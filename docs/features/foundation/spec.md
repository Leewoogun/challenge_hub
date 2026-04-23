# Foundation — 백엔드 기반 인프라

- **feature-id**: `foundation`
- **owner**: pm-lead → backend-dev (구현)
- **상태**: in-progress
- **생성**: 2026-04-23
- **타입**: sub-feature (모든 도메인 기능의 선행 조건)

## 배경 / 문제

`challenge-server`는 `ChallengeServerApplication.kt` + smoke test만 있는 완전 스켈레톤. 어떠한 도메인 기능도 구현하기 전에 공통 기반을 정리해야 feature별 일관성이 보장되고, 반복되는 부트스트랩 비용이 사라진다.

ADR-0002 accepted. 이 sub-feature는 ADR-0001·0002·0004·0008 결정의 코드 반영.

## 사용자 시나리오

이 sub-feature 자체는 사용자 기능이 아님. 다만 **다음 시나리오가 동작하도록 기반만 구축**:

1. 모바일이 `POST /api/v1/auth/kakao`에 Kakao access_token + phone_number 보냄 → 서버가 (Kakao SDK 검증은 Sprint 1, 지금은 stub) JWT Access + Refresh 반환
2. 모바일이 `POST /api/v1/auth/refresh`로 Access Token 재발급
3. 모바일이 `DELETE /api/v1/auth/logout`으로 서버측 Refresh Token 무효화 + FCM 토큰 제거
4. 비즈니스 예외(`SnackbarException` 등) 발생 시 HTTP 200 + `{error:true, code:700, message}` 응답
5. 인프라 장애(DB down) 발생 시 HTTP 500 + 표준 에러 body

## 수용 기준 (Acceptance Criteria)

### DB 마이그레이션
- [ ] Flyway 의존성 추가 (`spring-boot-starter-flyway` + `flyway-database-postgresql`)
- [ ] `app/src/main/resources/db/migration/V1__init.sql` 작성 — Server Notion 스펙의 9개 테이블 전부 포함:
  - `users`, `friendships`, `challenges`, `contracts`, `verifications`, `taunt_messages`, `notifications`, `user_stats`, `friend_records`
- [ ] `application.yml`에 `spring.flyway.enabled=true`, baseline 설정
- [ ] `./gradlew :app:bootRun` 시 Flyway가 V1 적용하고 앱 기동 성공 (로컬 Postgres 전제)

### 응답 DTO (BaseResponse 패턴)
- [ ] `:api` 모듈에 `BaseResponse` open class (`error: Boolean`, `code: Int=200`, `message: String=""`)
- [ ] `BusinessException` abstract class + `SnackbarException(700)`, `DialogException(701)`, `FullScreenException(702)`, `OneButtonException(705)` 하위 클래스
- [ ] `GlobalExceptionHandler` (`@RestControllerAdvice`) — `BusinessException` + `MethodArgumentNotValidException` 처리, 전부 `ResponseEntity.ok(BaseResponse(error=true, code=7xx, message))` 반환
- [ ] 인프라 예외 fallback (`Exception::class` 핸들러) → HTTP 500 + `BaseResponse(error=true, code=500, ...)`

### 보안
- [ ] `SecurityConfig` — `SecurityFilterChain` bean, CSRF 비활성, 세션 STATELESS
- [ ] `JwtTokenProvider` — `generateAccessToken(userId): String`, `generateRefreshToken(userId): String`, `verify(token): Long?`. JJWT 0.12.6 사용. 시크릿은 `application.yml`의 `jwt.secret` (env var 주입 가능)
- [ ] `JwtAuthenticationFilter` — `OncePerRequestFilter` 상속, Authorization 헤더에서 Bearer 추출 후 검증, SecurityContextHolder에 Authentication 설정
- [ ] SecurityFilterChain 규칙:
  - 공개: `/api/v1/auth/kakao`, `/api/v1/auth/refresh`, `/swagger-ui/**`, `/v3/api-docs/**`, `/actuator/health`
  - 인증 필요: 그 외 `/api/v1/**`
- [ ] CORS config — 모바일 origin(`*` for dev, prod에선 별도 결정) 허용, credentials=true

### 인증 엔드포인트 (skeleton)
- [ ] `POST /api/v1/auth/kakao` — 요청: `KakaoLoginRequest(accessToken, phoneNumber?)`. **Kakao 검증은 stub** (TODO 주석, Sprint 1에서 실제 연동). 응답: `LoginResponse(data=LoginData(accessToken, refreshToken, userId))`. 현재는 임의 userId로 JWT 발급만.
- [ ] `POST /api/v1/auth/refresh` — 요청: `RefreshRequest(refreshToken)`, 응답: `RefreshResponse(data=RefreshData(accessToken))`. Refresh Token 검증 후 새 Access Token 발급.
- [ ] `DELETE /api/v1/auth/logout` — 요청: header 인증, body 없음. 응답: `BaseResponse()` 성공. 현재는 FCM 토큰 제거 정도만 TODO로 둠 (Redis/DB 아직 사용 안 함).

### OpenAPI 문서
- [ ] SpringDoc `OpenAPIConfig` — JWT Bearer security scheme, `securityRequirements`로 글로벌 적용, 서버 정보(`http://localhost:8080`) 기재
- [ ] `/swagger-ui/index.html` 접속 시 3개 엔드포인트 표시 확인

### 테스트
- [ ] `AuthControllerTest` (`@SpringBootTest(webEnvironment=RANDOM_PORT)` 또는 `@WebMvcTest`) — 각 엔드포인트에 대한 smoke 테스트 (성공 1건, 401/700 에러 1건씩)
- [ ] `GlobalExceptionHandlerTest` — `SnackbarException` 발생 시 HTTP 200 + code=700 확인

## 비범위 (Out of Scope)

- Kakao SDK 실제 토큰 검증 (Sprint 1 `auth-kakao` feature에서 구현)
- `users` 테이블 실제 INSERT/UPSERT (Sprint 1)
- `phone_number` 해시 저장 로직 (ADR-0008, Sprint 1)
- Redis 연동 (Sprint 2+: 랭킹·Rate Limit 도입 시)
- WebSocket 구성 (Sprint 3: 도발 기능)
- 실제 도메인 로직 (모든 `:domain`/`:core` 모듈의 서비스)
- S3/Presigned URL 구성 (Sprint 2: 인증 사진)

## 태스크 분해

### 백엔드 (backend-dev)
- [ ] **T-B1**: Gradle 의존성 추가 — Flyway, (이미 설치된 것 확인: JJWT, SpringDoc, Spring Security, Redis, JPA)
- [ ] **T-B2**: `V1__init.sql` 작성 — 9개 테이블 DDL (Server Notion 스펙 그대로, 제약조건 포함)
- [ ] **T-B3**: `:api` 모듈에 `BaseResponse` + `BusinessException` 계층 + 에러 코드 상수
- [ ] **T-B4**: `GlobalExceptionHandler` 구현
- [ ] **T-B5**: `JwtTokenProvider` + `JwtAuthenticationFilter` + `SecurityConfig`
- [ ] **T-B6**: `AuthController` + 3개 엔드포인트 skeleton + DTOs (`KakaoLoginRequest`, `LoginResponse`/`LoginData`, `RefreshRequest`/`RefreshResponse`/`RefreshData`)
- [ ] **T-B7**: `OpenAPIConfig` + CORS config
- [ ] **T-B8**: 테스트 (AuthController smoke + GlobalExceptionHandler 1건)
- [ ] **T-B9**: `backend-report.md` 작성 (PM 레포에)

### 모바일 (mobile-dev) — 이번 sub-feature에서는 건드리지 않음
foundation 완료 후 Sprint 1 `auth-kakao` feature에서 모바일측 구현.

## 의존 관계

- ADR-0001 (Flyway), ADR-0002 (foundation), ADR-0008 (phone scope) 결정 선행 — **완료**
- 이 sub-feature 완료가 **모든 다른 feature의 선행 조건**

## 리스크 / 오픈 이슈

1. **로컬 Postgres 미기동**: backend-dev가 `bootRun` 검증하려면 로컬에 PostgreSQL + `challenge` DB가 있어야 함. 없으면 테스트만 돌리고 bootRun은 스킵(리포트에 명시).
2. **Redis**: 이번 sub-feature에서는 Redis를 사용하지 않으나 `application.yml`에 호스트가 지정되어 있어 연결 시도할 수 있음. 비활성화 또는 `@Profile` 분리 필요 여부 판단.
3. **JWT secret**: `application.yml`에 기본값을 두되 `JWT_SECRET` 환경변수로 오버라이드 가능하게. 기본값은 개발용 임시 문자열.
4. **Kakao stub**: `POST /api/v1/auth/kakao`가 검증 없이 JWT를 발급하면 보안상 위험 — 개발 프로필에서만 동작하도록 `@Profile("local")` 조건 또는 명확한 TODO 주석.
