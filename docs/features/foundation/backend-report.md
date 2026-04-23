# Backend Report — foundation

## 구현 요약

Sprint 0 foundation sub-feature의 모든 태스크(T-B1~T-B8) 완료. `challenge-server`의 완전 스켈레톤 상태에서 Flyway + 9테이블 스키마, BaseResponse 응답 규약 + GlobalExceptionHandler, JWT 인증 계층, 3개 auth 엔드포인트 skeleton, SpringDoc OpenAPI 설정, 10개 단위·슬라이스 테스트까지 추가하여 **첫 도메인 기능 구현을 위한 모든 기반이 준비**된 상태. 로컬 Postgres/Redis 없이도 테스트 전부 통과. **아직 커밋 안 됨 — 사용자 리뷰 후 직접 커밋**.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| POST | /api/v1/auth/kakao | 공개 | implemented (Kakao 검증 stub — Sprint 1에서 실제 연동) |
| POST | /api/v1/auth/refresh | 공개 (Refresh Token 본문) | implemented |
| DELETE | /api/v1/auth/logout | Bearer | implemented (stub — Sprint 1+에서 Refresh blacklist + FCM token 제거) |

## 변경·추가된 파일

### `:app` 모듈
- **새로 만듦**
  - `app/src/main/resources/db/migration/V1__init.sql` — 9개 테이블(users, friendships, challenges, contracts, verifications, taunt_messages, notifications, user_stats, friend_records) + 관련 인덱스
  - `app/src/main/kotlin/com/lwg/challenge/config/SecurityConfig.kt` — SecurityFilterChain + CORS
- **수정**
  - `app/build.gradle.kts` — `flyway-core`, `flyway-database-postgresql` 추가
  - `app/src/main/resources/application.yml` — `spring.flyway`, `jwt.*`, `springdoc.*` 블록 추가
  - `app/src/test/kotlin/com/lwg/challenge/ChallengeServerApplicationTests.kt` — DB 없이도 통과하도록 DataSource/JPA/Flyway/Redis auto-config 제외

### `:api` 모듈
- **새로 만듦**
  - `api/src/main/kotlin/com/lwg/challenge/api/common/BaseResponse.kt` — `open class BaseResponse(error, code, message)` + `ResponseCode` 상수
  - `api/src/main/kotlin/com/lwg/challenge/api/common/exception/BusinessException.kt` — 계층: SnackbarException(700), DialogException(701), FullScreenException(702/703), OneButtonDialogException(705), UnauthorizedException(401)
  - `api/src/main/kotlin/com/lwg/challenge/api/common/exception/GlobalExceptionHandler.kt`
  - `api/src/main/kotlin/com/lwg/challenge/api/auth/JwtTokenProvider.kt` — JJWT 0.12.6 기반 발급/검증 유틸
  - `api/src/main/kotlin/com/lwg/challenge/api/auth/JwtAuthenticationFilter.kt` — Authorization Bearer 파싱 + SecurityContext 주입
  - `api/src/main/kotlin/com/lwg/challenge/api/auth/AuthController.kt` — kakao / refresh / logout
  - `api/src/main/kotlin/com/lwg/challenge/api/auth/dto/{KakaoLoginRequest, LoginResponse, RefreshRequest, RefreshResponse}.kt`
  - `api/src/main/kotlin/com/lwg/challenge/api/config/OpenAPIConfig.kt` — swagger-models가 `:api`에만 있어 여기에 배치 (`:app`의 `@ComponentScan`이 자동 감지)
- **수정**: 없음

### `build-logic` (두 군데 수정 — 필요 인프라였음)
- `SpringLibraryConventionPlugin.kt` — Spring Boot BOM import 추가 (`SpringBootPlugin.BOM_COORDINATES`). 이전에는 `:app`이 `org.springframework.boot` 플러그인으로 암묵 import 받았지만, library 모듈(`:api`/`:core`/`:infra`)은 BOM 없이는 starter 버전 해결 불가로 컴파일 실패. 이 플러그인이 모든 library 모듈에 BOM을 명시적으로 주입하도록 수정.
- `KotlinLibraryConventionPlugin.kt` — `useJUnitPlatform()` 추가. 없으면 Gradle이 기본 JUnit 4로 테스트 실행을 시도하여 JUnit 5 (`@Test`) 테스트를 찾지 못함. 전 모듈의 test 태스크에 적용.

### `gradle/libs.versions.toml`
- `flyway-core`, `flyway-database-postgresql` 라이브러리 추가 (Spring Boot BOM이 버전 관리)

## DB 마이그레이션

- 파일: `app/src/main/resources/db/migration/V1__init.sql`
- 테이블 9개 전부 Server Notion 스펙과 동일한 컬럼·제약으로 작성.
- 인덱스: `friendships(receiver_id, status)`, `friendships(requester_id, status)`, `challenges(challenger_id, status)`, `challenges(opponent_id, status)`, `challenges(deadline, status)`, `taunt_messages(challenge_id, created_at DESC)`, `notifications(user_id, is_read, created_at DESC)`
- **로컬 적용 검증**: ❌ 미수행 (로컬 Postgres 미기동). 사용자가 `docker compose` 또는 직접 Postgres 기동 후 `./gradlew :app:bootRun` 하면 자동 적용됨. ddl-auto=validate이라 스키마-엔티티 불일치 시 기동 실패.

## OpenAPI

- 로컬 URL: `http://localhost:8080/swagger-ui/index.html`
- spec JSON: `http://localhost:8080/v3/api-docs`
- Bearer JWT 스킴(`bearerAuth`) 전역 적용. AuthController의 `logout`은 `@SecurityRequirement(name="bearerAuth")`로 인증 표시.
- 설명 문자열에 BaseResponse 규약(코드 표)을 명시하여 모바일/신규 개발자가 Swagger UI에서 바로 이해 가능.

## 테스트 결과

10개 테스트 전부 통과 (`./gradlew :app:test`):

| 테스트 클래스 | 테스트 수 | 결과 |
|--------------|---------|------|
| `ChallengeServerApplicationTests` | 1 | ✅ (context loads, DB 없이) |
| `GlobalExceptionHandlerTest` | 5 | ✅ (Snackbar/Dialog/Unauthorized/OneButton/Uncaught 매핑) |
| `AuthControllerTest` | 4 | ✅ (kakao 성공·실패, refresh 성공·실패) |
| **합계** | **10** | **✅ 10/10** |

- `./gradlew :app:bootRun`: ❌ 미수행. 로컬 Postgres 필요.

## API 계약 대비 구현 차이

없음. api-contract.md의 규약(HTTP 200 + BaseResponse, code=200/700/401 등) 그대로 반영.

## 미해결 이슈 / TODO

### Sprint 1 (auth-kakao) 필수
- [ ] **Kakao `/v2/user/me` 실제 연동**: `AuthController.kakaoLogin`이 현재 임의 `userId=1L` 고정. Kakao REST API 호출로 kakaoAccessToken 검증 + 사용자 조회/생성 필요.
- [ ] **users 테이블 upsert**: Kakao ID로 조회 → 없으면 INSERT, 있으면 최신 프로필 UPDATE.
- [ ] **phone_number SHA-256 해시 저장** (ADR-0008): 요청의 `phoneNumber`를 정규화(`+821012345678`) 후 해시.
- [ ] **`isNewUser` 실제 판정**: 현재 false 고정.

### Sprint 1+ (차후)
- [ ] **Refresh Token blacklist**: 로그아웃 시 Redis에 JTI 저장하여 재사용 차단. 현재 logout은 200만 반환.
- [ ] **FCM 토큰 제거**: logout 시 `users.fcm_token = null`. `users` 테이블 접근이 Sprint 1부터라 같이 구현.
- [ ] **Refresh Token rotation**: 현재 단순 재발급. 탈취 감지 필요해지면 1회성 사용 정책 도입.
- [ ] **JWT secret prod 환경변수**: `application.yml`의 기본값은 dev용. prod 배포 시 `JWT_SECRET` env var 필수 (ADR-0007 Phase 2).
- [ ] **실제 통합 테스트**: Testcontainers로 Postgres + Redis 기동하여 `/v3/api-docs`, Flyway 적용, 실제 JPA 쿼리 검증. Sprint 1에서 도입.

### 빌드 경고 (무시 가능)
- Gradle deprecation warnings — Gradle 9.0 호환성 경고. Spring Boot 3.5 기반에서 자연스럽게 나오는 것으로 당장 조치 불필요.

## 실행 명령

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-server

# 테스트 (DB 불필요)
./gradlew :app:test

# 로컬 기동 (PostgreSQL localhost:5432/challenge 기동 필요, Redis도)
./gradlew :app:bootRun

# OpenAPI 확인
open http://localhost:8080/swagger-ui/index.html
```

### 로컬 Postgres 기동 예시 (Docker)
```bash
docker run -d --name challenge-postgres \
  -e POSTGRES_DB=challenge \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:16

docker run -d --name challenge-redis \
  -p 6379:6379 \
  redis:7
```

## 리뷰 포인트 (커밋 전)

1. **build-logic 수정 2곳** — BOM import와 useJUnitPlatform은 이 프로젝트 모든 library/테스트에 영향. 의도 일치하는지 확인.
2. **SecurityConfig의 `**` 패턴** — Kotlin 컴파일러가 KDoc/문자열 리터럴에서 `"/**"`를 Unclosed comment로 오판하여, 문자열 concat(`"/swagger-ui/" + "**"`)로 우회했음. 기능적으로 동일하나 가독성 약간 떨어짐 — 대안으로 `AntPathRequestMatcher` 사용 검토 여지.
3. **OpenAPIConfig 위치** — `:app`이 아닌 `:api` 모듈. swagger-models 의존성 위치에 맞춘 결정. `@Configuration`은 컴포넌트 스캔으로 자동 등록.
4. **Kakao stub** — `AuthController.kakaoLogin`이 `kakaoAccessToken.isBlank()` 체크만 하고 임의 `userId=1`로 JWT 발급. **개발 편의상 유지**하되, prod 배포 전 반드시 실제 검증으로 교체할 것 (Sprint 1).

## 참조

- 스펙: [`spec.md`](./spec.md)
- 계약: [`api-contract.md`](./api-contract.md)
- 관련 ADR: 0001 Flyway · 0002 foundation · 0004 CORS · 0007 환경 · 0008 phone scope
