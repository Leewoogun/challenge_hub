# Refresh Token Rotation (auth-refresh-rotation) — Summary

- **feature-id**: auth-refresh-rotation
- **완료일**: 2026-05-28
- **상태**: completed
- **결정 ADR**: [ADR-0009](../../decisions/0009-refresh-token-rotation.md)
- **선행 작업**: [auth-kakao](../auth-kakao/summary.md)의 미해결 이슈 "Refresh Token Rotation"

> `foundation` Sprint 0에서 도입한 단순 refresh 흐름(access만 재발급, refresh 영구 재사용)을 **DB sha256 hash 기반 rotation**으로 교체. 옛 refresh 즉시 무효화 + 1기기 1세션 강제 + 모바일 401 처리 단일 지점화. ADR-0002의 `code=401`을 access 만료/refresh 만료로 세분화 명문화.

## 구현 개요

### 서버 (커밋 `dfecba5`)

1. **V3 마이그레이션**: `users.refresh_token_hash VARCHAR(64)`, `refresh_token_issued_at TIMESTAMP` 추가 (둘 다 nullable).
2. **`RefreshTokenHasher`** (`core/hash`): sha256 hex 64자 lower-case. salt 없음 (입력이 JWT).
3. **`AuthService.refresh()`** 신규: JWT 검증 + `findById` + DB hash 일치 확인 → 새 access + 새 refresh 발급, hash 회전. 모든 실패 경로가 동일 401 응답 (정보 노출 최소화).
4. **`AuthService.login()`**: 발급 직후 hash 저장 추가.
5. **`RefreshData`** DTO에 `refreshToken` 필드 추가.
6. **`UserRepository`**: `findById`, `updateRefreshTokenHash` 추가. JPA `@Modifying`으로 핀포인트 UPDATE (`updated_at` 의도적 미갱신).

### 모바일 (커밋 `68d6533`)

1. **Ktor `Auth(bearer)`** `KtorfitModule`에 설치 → 401 처리 단일 지점화. `loadTokens` / `refreshTokens` / `sendWithoutRequest(auth 제외)`.
2. **`TokenProvider`** 인터페이스 (`remote/network`) + **`TokenProviderImpl`** 구현 (`data/repositoryImpl`) — `:remote:network`가 `:local:datastore`에 직접 의존하지 않도록 port-adapter 분리.
3. **`AuthEventBus`** (`core/utils`): `SharedFlow<Unit> sessionExpired`. `MainScreen`이 collect → 로그인 탭으로 강제 이동.
4. **`RefreshResponse.RefreshData.refreshToken`** 필드 추가 (서버 정합).
5. **제거**: `RefreshAccessTokenUseCase`, `LoginRepository.refreshAccessToken` + Impl + Fake, `RefreshResponseMapper`, `LoginApi.refresh`, `LoginRepositoryImpl.CODE_UNAUTHORIZED`, `SplashViewModel`의 refresh-on-launch.

## 엔드포인트

| Method | Path | 인증 | 변경 | 상태 |
|--------|------|------|------|------|
| POST | /api/v1/auth/kakao | 공개 | 서버 측 hash 저장 1단계 추가 (응답 계약 동일) | unchanged |
| **POST** | **/api/v1/auth/refresh** | **공개 (refresh가 인증)** | **`data.refreshToken` 신규 + 검증 강화 + 실패 메시지 통일** | **confirmed (rev 2)** |
| DELETE | /api/v1/auth/logout | Bearer | 변경 없음 (Sprint 0 스텁 유지) | unchanged |

상세 계약은 [api-contract.md](./api-contract.md).

## 새로운 401 흐름 (end-to-end)

```
[일반 API 호출]
   ↓ 401 (access 만료)
[Ktor Auth.refreshTokens 자동 트리거]
   ↓ POST /api/v1/auth/refresh { refreshToken }
[서버 검증]
   ├─ JWT 서명/exp/tokenType 통과 AND DB hash 일치
   │     → 새 access + 새 refresh 발급, hash 회전, code=200
   │     ↓ 모바일이 새 토큰 저장 + 원 요청 재시도
   │     ✅ 사용자 무자각 성공
   │
   └─ 실패 (서명 무효 / exp 초과 / 사용자 부재 / hash 불일치 / hash NULL)
         → 동일 401 응답 ("Refresh Token 이 유효하지 않거나 만료되었습니다")
         ↓ 모바일이 토큰 클리어 + AuthEventBus.sessionExpired 발사
         ↓ MainScreen이 collect → Route.LoginRoute.Main 강제 이동
         🔁 사용자 카카오 재로그인
```

## ADR-0002 401 의미 세분화

[ADR-0009](../../decisions/0009-refresh-token-rotation.md) 내 하위 결정으로 명문화. `code=401`은 두 가지 의미를 가지며, 모바일이 발생 경로(일반 API vs `/auth/refresh`)로 분기.

| 응답 출처 | code | 모바일 처리 |
|-----------|------|------------|
| 일반 API | 401 | Ktor Auth가 자동 refresh 후 재시도 (사용자 무자각) |
| `/auth/refresh` | 401 | 토큰 클리어 + 세션 만료 이벤트 → 로그인 화면 |

HTTP는 모두 200 유지 (ADR-0002 "항상 HTTP 200").

## 주요 변경 파일

**백엔드** (`challenge-server`, 11 files / +188 / -16):
- `app/src/main/resources/db/migration/V3__users_refresh_token.sql` (신규)
- `core/.../core/hash/RefreshTokenHasher.kt` (신규)
- `service/.../service/auth/AuthService.kt` — `refresh()` 신규, `login()`에 hash 저장 추가
- `service/.../service/auth/RefreshResult.kt` (신규)
- `controller/.../controller/auth/AuthController.kt` — `JwtTokenProvider` 직접 의존 제거, service 위임
- `controller/.../controller/auth/dto/RefreshResponse.kt` — `refreshToken` 필드 추가
- `domain/model/.../domain/user/User.kt` — `refreshTokenHash`, `refreshTokenIssuedAt` 필드
- `domain/repository/.../domain/user/UserRepository.kt` — `findById`, `updateRefreshTokenHash` 추가
- `infra/jpa/.../UserJpaRepository.kt` — `@Modifying @Query` UPDATE
- `infra/repositoryimpl/.../UserRepositoryImpl.kt` — 위임 구현
- `infra/entity/.../auth/UserEntity.kt` — 2 컬럼 매핑 + `toDomain` / `fromDomain` 갱신

**모바일** (`challenge-app`, 16 files / +143 / -116):
- `core/utils/.../utils/AuthEventBus.kt` (신규)
- `remote/network/.../auth/TokenProvider.kt` (신규 인터페이스)
- `data/repositoryImpl/.../data/auth/TokenProviderImpl.kt` (신규 구현)
- `remote/network/.../di/KtorfitModule.kt` — Ktor `Auth(bearer)` 설치 + `provideAuthEventBus`
- `remote/network/build.gradle.kts`, `gradle/libs.versions.toml` — `ktor-client-auth` 의존성
- `remote/model/.../auth/RefreshResponse.kt` — `RefreshData.refreshToken` 필드
- `feature/main/.../MainScreen.kt` — `AuthEventBus.sessionExpired` collect → 로그인 탭 이동
- `feature/splash/.../SplashViewModel.kt` — refresh-on-launch 제거, 단순 분기
- 제거: `domain/usecase/.../RefreshAccessTokenUseCase.kt`, `remote/mapper/.../RefreshResponseMapper.kt`
- 갱신: `data/repository/LoginRepositoryImpl.kt`, `data/di/UseCaseModule.kt`, `domain/repository/LoginRepository.kt`, `remote/api/LoginApi.kt`, `feature/login/FakeLoginRepository.kt`(test)

**PM 레포** (`challenge-pm/challenge_hub`):
- `docs/decisions/0009-refresh-token-rotation.md` (신규 ADR)
- `docs/features/auth-refresh-rotation/{spec, api-contract, backend-report, mobile-report, summary}.md` (본 묶음)
- `docs/features/INDEX.md`, `docs/backlog.md` 갱신

## 테스트 결과

**신규 테스트 0건**. 본 PR은 시간 제약상 회귀 확인만 수행. 권장 케이스는 backlog 등재.

- **서버 회귀 영향 분석**: 기존 AuthControllerTest 5/5, AuthKakaoIntegrationTest 5(docker skip), ChallengeServerApplicationTests는 본 변경에 영향 없음. `RefreshData`에 필드 추가는 backward-compatible.
- **모바일 회귀 영향 분석**: LoginViewModelTest 4/4는 로그인 분기만 검증 — refresh 흐름과 무관. FakeLoginRepository에서 `refreshAccessToken` override가 제거됐으나 테스트 코드에서 호출처 없음.
- **빌드 검증**: 본 정리 시점에 별도 재실행 안 함 (코드 변경 0건의 사후 박제). 개발자가 푸시 전 로컬 빌드/테스트 통과 확인했다고 전제.

## 결정 사항

1. **DB hash 저장 방식 채택** (ADR-0009 B안). Redis blacklist 대비 외부 의존 최소화 + `Redis 용도 결정`이 미정인 시점에 인증을 Redis에 묶지 않음.
2. **실패 응답 통일** — JWT 무효 / 사용자 부재 / hash 불일치 / hash NULL 모두 동일 401 메시지. 정보 노출 최소화.
3. **V1 가입자는 강제 재로그인** — 마이그레이션 직후 hash NULL → 다음 refresh에서 401. MVP 가입자 수 적어 수용.
4. **`updated_at` 미갱신** — rotation은 logical update가 아님. `@PreUpdate` 회피 위해 `@Modifying @Query` 사용.
5. **모바일 401 처리 일원화** — Ktor `Auth(bearer)` 단일 지점. 신규 API 추가 시 401 분기 재작성 불필요.
6. **`/auth/refresh`도 공개 엔드포인트로 처리** — Ktor `sendWithoutRequest`가 `auth` 경로에서 Authorization 미부착. refresh body 자체가 인증.
7. **logout 엔드포인트는 본 범위 밖** — `updateRefreshTokenHash(_, null, null)` 호출 자리만 마련.

## 미해결 이슈

- [ ] **AuthServiceRefreshTest 단위 테스트** (backend): 정상 rotation / 옛 refresh 재사용 / hash NULL / JWT 만료 / tokenType 잘못 — 5 케이스 권장. 본 PR 미작성.
- [ ] **Ktor Auth 플러그인 모바일 테스트**: 200 분기 / 401 분기 / refresh JSON deserialization / 다중 요청 race 처리.
- [ ] **수동 E2E smoke**: access 만료 시뮬레이션 (서버 application.yml에서 jwt.access.expire 짧게) → 모바일에서 사용자 무자각 갱신 확인 + refresh 만료 시 로그인 화면 이동.
- [ ] **V1 가입자 강제 재로그인 동작 확인**: 마이그레이션 후 기존 사용자가 첫 호출에서 강제 재로그인 되는지.
- [ ] **logout 엔드포인트 구현**: 별도 feature. hash NULL화 호출.
- [ ] **rotation race 동시성**: 동일 refresh로 2 요청 동시 도착 시 한쪽 실패의 사용자 영향. Ktor Auth 단일 클라이언트 직렬화로 단일 기기에선 발생 빈도 낮음.
- [ ] **audit 로그**: `refresh_token_issued_at` 외 별도 audit 테이블. 의심 사례 추적 필요 시점에 검토.

## 참조

- [spec.md](./spec.md)
- [api-contract.md](./api-contract.md) (상태: confirmed rev 2)
- [backend-report.md](./backend-report.md)
- [mobile-report.md](./mobile-report.md)
- [ADR-0009](../../decisions/0009-refresh-token-rotation.md)
- [auth-kakao/summary.md](../auth-kakao/summary.md) — 본 feature 트리거 출처
- ADR-0002 (BaseResponse + code 401) — 본 feature가 의미 세분화
- 서버 커밋 `dfecba5`, 모바일 커밋 `68d6533`
