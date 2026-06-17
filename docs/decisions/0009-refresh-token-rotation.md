# ADR-0009: Refresh Token Rotation (1기기 1세션, DB hash 기반)

- **상태**: accepted (2026-05-28)
- **생성**: 2026-05-28
- **영향 범위**: `users` 스키마 (V3 마이그레이션), `POST /api/v1/auth/refresh` 응답 계약, 모바일 토큰 처리 전반, ADR-0002 401 정의

## 맥락

`foundation`(Sprint 0)에서 도입한 refresh 흐름은 다음과 같았다.

- 로그인 시 access + refresh 발급 → 모바일 저장소에 둘 다 저장.
- `POST /api/v1/auth/refresh` 호출 시 서버는 JWT 서명/exp만 검증하고 **access만 재발급**. refresh는 그대로 재사용.
- 모바일은 splash 진입 시 `RefreshAccessTokenUseCase`를 직접 호출, 일반 API의 401 처리는 각 Repository가 산발적으로 분기 (`LoginRepositoryImpl.CODE_UNAUTHORIZED=401` → `clearTokens()` 후 silently fail).

이 구조에는 다음 문제가 누적되어 있었다.

1. **토큰 탈취 시 무효화 불가**. refresh JWT의 exp까지(현 정책 14일) 무한 재사용 가능. 사용자가 다른 기기에서 재로그인해도 옛 refresh는 살아 있음. [auth-kakao/summary.md](../features/auth-kakao/summary.md) 미해결 이슈로 기록되어 있었음.
2. **1기기 1세션 정책 부재**. 서버는 한 사용자에 대해 동시에 여러 refresh를 인정. 향후 강제 로그아웃·세션 만료 UX(다른 기기에서 로그인 시 기존 기기 강제 로그아웃) 구현 시 hook이 없음.
3. **401 처리 산재**. Splash, Repository, ViewModel이 각자 401을 해석 → 화면 분기까지 책임. Ktor `Auth(bearer)` 같은 일원화 지점이 없어 신규 API 추가할 때마다 401 분기를 다시 적어야 함.
4. **계약상 명문화 부재**. ADR-0002의 "code=401 = 토큰 만료" 정의는 access/refresh를 구분하지 않음. refresh 만료 시점에 서버가 어떻게 응답할지가 명세에 없음.

## 선택지

### A. JWT exp만 사용 (현재 구조 유지)

- refresh JWT 서명/exp만 검증. DB 저장 없음.
- **장점**: 구현 변경 0. stateless.
- **단점**: 위 문제 1~3 그대로. 탈취 시 무효화 경로 없음.

### B. Rotation + DB sha256 hash (권장)

- refresh 호출마다 새 access + 새 refresh 발급. `users.refresh_token_hash`에 sha256(rawRefresh) 저장.
- 다음 refresh는 DB hash 일치 여부도 확인 → 옛 refresh 자동 무효화 (rotation).
- **장점**:
  - 옛 refresh를 신규로 덮어 즉시 무효화 (탈취 후 정상 사용자가 한 번 갱신만 하면 탈취본 차단).
  - 1기기 1세션 자연스럽게 강제 (다른 기기 로그인 시 기존 hash 덮임).
  - logout/관리자 강제 무효화 시 hash NULL로 갱신만 하면 됨.
  - hash 저장이라 raw refresh 유출 시에도 DB 자체로는 토큰 발급 불가.
- **단점**:
  - users 테이블에 2 컬럼 추가 (마이그레이션 V3 필요).
  - refresh API가 read-only가 아니라 write 트랜잭션 (UPDATE 1건/요청).

### C. Redis blacklist

- refresh 사용 시 jti(또는 hash)를 Redis에 blacklist 등록 → 다음 사용 시 차단.
- **장점**: DB 스키마 변경 없음, TTL 자동 만료.
- **단점**:
  - Redis 가용성에 인증 흐름 직접 의존 (Redis down = 모든 refresh 실패).
  - blacklist는 "쓴 적 있는가"는 알아도 "이 사용자의 현재 유효 토큰이 뭔가"는 모름 → 1기기 1세션 강제는 별도 키 필요.
  - `repos.json` backend.blockers의 "Redis 용도 미정"이 아직 결정 안 됨 — 인증을 Redis에 묶기엔 시점이 이름.

### D. Rotation + Redis hash

- B와 C 혼합. 저장소만 Redis.
- **장점**: TTL 자동.
- **단점**: C와 동일한 가용성 결합. + 사용자 핵심 식별 정보(`users` row)와 분리되어 회복/감사 추적이 까다로움.

## 트레이드오프

| 축 | A | **B (DB hash + rotation)** | C (Redis blacklist) | D (Redis hash + rotation) |
|----|---|----|----|----|
| 탈취 무효화 | ❌ | ✅ 즉시 (1회 정상 갱신) | ✅ 사용 시점 | ✅ |
| 1기기 1세션 | ❌ | ✅ 자연스럽게 | △ (별도 키 필요) | △ |
| 외부 의존 | 없음 | DB만 | Redis 필수 | Redis 필수 |
| 마이그레이션 | 없음 | V3 1건 (컬럼 2개) | 없음 | 없음 |
| 감사 추적 | ❌ | ✅ `refresh_token_issued_at` | △ | △ |
| 구현 복잡도 | 0 | 낮음 | 중 (Redis 모듈 + TTL) | 중 |
| MVP 적합성 | 낮음 (보안 우려) | **높음** | 시기 이름 | 시기 이름 |

## 결정

**B 채택 (accepted, 2026-05-28).**

근거:
- MVP 단계에서 가장 단순하면서 (1) 탈취 무효화, (2) 1기기 1세션, (3) 감사 추적을 모두 만족.
- Redis 용도 결정([backlog.md](../backlog.md) 🟢 항목)이 아직 안 됐고, 인증을 Redis 가용성에 묶는 결정을 그 결정보다 먼저 내릴 이유 없음.
- hash 저장이므로 DB 덤프 유출 시에도 raw refresh가 노출되지 않음 (반대로 jti만 저장하면 토큰 식별·관리는 가능하나 raw 일치 검증은 불가). sha256 hex는 64자 고정 → 컬럼 길이 산정 단순.
- rotation 자체가 OWASP Refresh Token Rotation 권장 패턴 [^owasp].

## 구현 (이번 PR로 확정)

상세는 [features/auth-refresh-rotation/summary.md](../features/auth-refresh-rotation/summary.md) — 핵심만:

### 스키마 (V3)

```sql
ALTER TABLE users ADD COLUMN refresh_token_hash VARCHAR(64);
ALTER TABLE users ADD COLUMN refresh_token_issued_at TIMESTAMP;
```

- 둘 다 nullable. V1 시기 가입자(`refresh_token_hash IS NULL`)는 다음 refresh 호출에서 401 → 모바일이 카카오 재로그인 → 그때부터 정상 rotation 진입.
- logout/강제 무효화 시 NULL로 갱신.

### 서버 API

| 변경 | before | after |
|------|--------|-------|
| `POST /api/v1/auth/refresh` 응답 | `data: { accessToken }` | `data: { accessToken, refreshToken }` |
| `RefreshData.refreshToken` | 부재 | **신규 필수 필드** (새 회전된 refresh) |
| 인증 흐름 | JWT 서명+exp만 | JWT 서명+exp **AND** DB hash 일치 |

실패 응답은 모두 동일 메시지(`"Refresh Token 이 유효하지 않거나 만료되었습니다"`) + `code=401`로 통일 → 정보 노출 최소화.

### 모바일 흐름

- 401 처리는 Ktor `Auth(bearer)` 플러그인이 일원화. `loadTokens` / `refreshTokens` / `sendWithoutRequest`(auth 경로 제외) 3개 hook.
- refresh 성공 → 새 토큰 둘 다 로컬 저장소에 저장, 원 요청 재시도.
- refresh가 `code=401` 반환 → 토큰 클리어 + `AuthEventBus.sessionExpired` 발사 → `MainScreen`이 받아 로그인 탭으로 강제 이동.
- `RefreshAccessTokenUseCase` / `LoginRepository.refreshAccessToken` / `RefreshResponseMapper` / `LoginApi.refresh` 4개 제거 (Ktor Auth가 흡수). SplashViewModel의 refresh-on-launch 로직도 제거 — 만료 판정은 첫 API 호출 시점에서.

## ADR-0002 명문화 (하위 결정)

ADR-0002의 `code=401`을 다음과 같이 분리·명문화한다.

| 응답 | 의미 | 모바일 처리 |
|------|------|-------------|
| 일반 API `code=401` | access 만료 (또는 무효) | Ktor Auth `refreshTokens` 트리거 → `/auth/refresh` 호출 후 원 요청 재시도 |
| `/auth/refresh` `code=401` | refresh 만료 / hash 불일치 / 옛 refresh 재사용 / 사용자 부재 — 모두 동일 응답 | 토큰 클리어 + `AuthEventBus.sessionExpired` → 로그인 화면 |

서버는 두 경우 모두 BaseResponse code=401, HTTP 200을 유지 (ADR-0002의 "항상 HTTP 200" 원칙 보존).

## 잔여·후속

- **logout 엔드포인트의 hash NULL화**: `updateRefreshTokenHash(userId, null, null)` 호출처가 본 PR 범위 밖. logout feature 진입 시 합류.
- **rotation race**: 동일 refresh로 두 요청이 동시 도착할 경우 한쪽은 hash 불일치로 실패. 모바일 Ktor Auth는 401 발생 시 한 번에 하나의 refresh만 수행하도록 동기화하므로 단일 클라이언트 환경에선 발생 빈도 낮음. 다중 기기에서 동시 갱신은 의도된 1기기 1세션 정책의 자연스런 귀결.
- **감사 로그**: `refresh_token_issued_at` 컬럼만 두고 별도 audit 테이블은 미작성. 의심 사례 추적 필요 시점에 별도 ADR.
- **신규 단위 테스트 미작성** (본 PR). `AuthServiceRefreshTest`(서명 OK/hash 불일치/사용자 부재/만료 4 케이스) + 모바일 `KtorfitModule` Auth 플러그인 테스트는 backlog 등재.

## 참조

- [features/auth-refresh-rotation/summary.md](../features/auth-refresh-rotation/summary.md)
- [features/auth-refresh-rotation/api-contract.md](../features/auth-refresh-rotation/api-contract.md)
- ADR-0002 (BaseResponse + code 기반 에러) — 본 ADR이 401 의미를 세분화
- [auth-kakao/summary.md](../features/auth-kakao/summary.md) 미해결 이슈 "Refresh Token Rotation" — 본 ADR로 해소
- 서버 커밋 `dfecba5` / 모바일 커밋 `68d6533`

[^owasp]: OWASP Cheat Sheet — JSON Web Token for Java § Token Sidejacking, Refresh Token rotation 권장 패턴.
