# Refresh Token Rotation — Spec

- **feature-id**: auth-refresh-rotation
- **상태**: completed (2026-05-28)
- **출발점**: [auth-kakao/summary.md](../auth-kakao/summary.md) 미해결 이슈 "Refresh Token Rotation: 로그인 시마다 새 refresh 발급되지만 옛 것 무효화 없음 — ADR-0009(예정)에서 결정"
- **결정 ADR**: [ADR-0009](../../decisions/0009-refresh-token-rotation.md)

## 목적

`foundation` Sprint 0에서 도입한 단순 refresh 흐름(서명+exp만 검증, refresh는 영구 재사용)을 **Rotation + DB sha256 hash** 기반으로 교체하여:

1. 옛 refresh 토큰을 즉시 무효화할 수 있는 경로를 만든다 (탈취 대응).
2. 1기기 1세션 정책을 서버 측 진실로 강제한다.
3. 모바일의 401 처리를 Ktor `Auth(bearer)` 플러그인으로 일원화한다 (산재된 `CODE_UNAUTHORIZED=401` 분기 제거).
4. ADR-0002의 `code=401` 의미를 access 만료 / refresh 만료로 세분화·명문화한다.

## 비-목표 (Out of scope)

- **logout 엔드포인트 구현**: hash NULL화 자리만 마련(`updateRefreshTokenHash(_, null, null)` 가능). 실제 logout feature는 별도.
- **다른 기기 강제 로그아웃 UX**: 1기기 1세션은 서버 측에서 자연스럽게 강제되나, 다른 기기에서 로그인했을 때 기존 기기에 알림을 띄우는 UX는 별도.
- **감사 로그(audit)**: `refresh_token_issued_at` 컬럼 외 별도 audit 테이블은 미작성.
- **신규 단위 테스트**: 시간 제약상 본 PR에는 회귀 확인만. 권장 테스트 케이스는 backlog 등재.

## 요구사항

### 서버

- [x] `users` 테이블에 `refresh_token_hash VARCHAR(64)`, `refresh_token_issued_at TIMESTAMP` 컬럼 추가 (둘 다 nullable).
- [x] Flyway 마이그레이션 V3 작성. V1 시기 가입자(hash NULL)는 다음 refresh 호출에서 401 → 재로그인 경로 진입.
- [x] `RefreshTokenHasher` 유틸 — SHA-256 hex (64자, lower-case). salt 없음 (입력이 JWT 고엔트로피).
- [x] 카카오 로그인 성공 시 발급된 refresh의 hash를 DB에 저장.
- [x] `POST /api/v1/auth/refresh` 흐름 교체:
  - JWT 서명+exp+tokenType 검증
  - `userId`로 사용자 조회 실패 → 401
  - DB hash와 incoming hash 불일치 → 401
  - 통과 시 새 access + 새 refresh 발급, hash 회전
- [x] 모든 실패 경로의 응답 메시지·코드 통일 (`code=401`, "Refresh Token 이 유효하지 않거나 만료되었습니다") — 정보 노출 최소화.
- [x] `RefreshData` DTO에 `refreshToken: String` 필드 추가.

### 모바일

- [x] `TokenProvider` 인터페이스 (remote/network) — get/update/clear 4메서드. 구현은 data 레이어 `TokenProviderImpl`이 `TokenLocalDataSource` 위임.
- [x] `KtorfitModule`에 Ktor `Auth(bearer)` 설치:
  - `loadTokens` — TokenProvider에서 읽기
  - `refreshTokens` — `/api/v1/auth/refresh` POST → `body.code` 분기 (200/401/기타)
  - `sendWithoutRequest` — `auth` 경로는 Authorization 미부착
- [x] `AuthEventBus` (core/utils) — `SharedFlow<Unit> sessionExpired`.
- [x] `MainScreen`에서 `AuthEventBus.sessionExpired` collect → `Route.LoginRoute.Main` 강제 이동.
- [x] `RefreshResponse.RefreshData`에 `refreshToken` 필드 추가 (서버 변경과 정합).
- [x] 제거: `LoginRepository.refreshAccessToken` + Impl, `RefreshAccessTokenUseCase`, `RefreshResponseMapper`, `LoginApi.refresh`, `LoginRepositoryImpl.CODE_UNAUTHORIZED`, `SplashViewModel`의 refresh-on-launch.

### 계약

- [x] [api-contract.md](./api-contract.md) confirmed (변경 1건: `refresh` 응답 body에 `refreshToken` 추가).
- [x] [ADR-0009](../../decisions/0009-refresh-token-rotation.md) accepted.
- [x] ADR-0002의 401 의미 세분화 (ADR-0009 내 하위 결정으로 명문화).

## 영향받는 사용자 시나리오

| 시나리오 | 동작 |
|---|---|
| 첫 카카오 로그인 | access + refresh 발급. 서버 DB에 hash 저장. |
| access 만료 후 일반 API 호출 | Ktor Auth가 401 감지 → `/auth/refresh` 호출 → 새 토큰 쌍 받아 원 요청 자동 재시도. 사용자 무자각. |
| refresh 만료 / 옛 refresh 사용 | `/auth/refresh`가 `code=401` 반환 → 모바일이 토큰 클리어 + 로그인 화면으로 강제 이동. |
| V1 시기 가입자 (hash 부재) | 첫 refresh 호출 시 hash 불일치로 401 → 로그인 화면 → 카카오 재로그인 → 그때부터 정상 rotation. |
| 다른 기기에서 재로그인 | 새 기기에서 발급된 refresh로 DB hash 덮임. 기존 기기는 다음 refresh 호출 시 hash 불일치 401 → 강제 로그아웃 (1기기 1세션). |

## 참조

- [api-contract.md](./api-contract.md)
- [backend-report.md](./backend-report.md)
- [mobile-report.md](./mobile-report.md)
- [summary.md](./summary.md)
- [ADR-0009](../../decisions/0009-refresh-token-rotation.md)
- ADR-0002 (BaseResponse + code 401)
- 서버 커밋 `dfecba5`, 모바일 커밋 `68d6533`
