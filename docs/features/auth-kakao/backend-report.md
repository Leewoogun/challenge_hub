# Backend Report — auth-kakao

- **feature-id**: auth-kakao
- **작성**: 2026-04-24 by backend-dev
- **최종 갱신**: 2026-05-07 — contract drift 정정 (REST API → SDK 정렬). 자세한 내력은 [change-log.md](./change-log.md).
- **상태**: implemented (로컬), 배포 전
- **빌드 검증**: `:infra/:api/:app:compileKotlin` BUILD SUCCESSFUL / `AuthControllerTest` 5/5 passed / `AuthKakaoIntegrationTest` 5건 컴파일 통과 (Docker 미가용으로 skip)

## 구현 요약

Sprint 0 `foundation`에서 스텁으로 두었던 `POST /api/v1/auth/kakao`를 실제 Kakao OAuth 연동으로 교체했다. 핵심 흐름:

1. 모바일이 전달한 `kakaoAccessToken`을 Kakao `/v2/user/me`(WebClient)로 검증
2. 응답의 `kakao_account.phone_number`를 `PhoneHasher`로 정규화 + SHA-256 해시
3. `users` 테이블 upsert (kakao_id UNIQUE 기준) — 신규/기존 분기, `isNewUser` 플래그 반환
4. 기존 `JwtTokenProvider`로 access/refresh 토큰 발급

에러 분기:
- Kakao 401/403 → `DialogException` → HTTP 200 + code=701
- Kakao 5xx/타임아웃 → 1회 재시도 후 `FullScreenException` → HTTP 200 + code=703
- Kakao API 성공이지만 `phone_number_needs_agreement=true`이거나 phone 누락 → `phone_number=null`, `phone_verified=false`로 저장 (로그인은 성공)

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| POST | /api/v1/auth/kakao | 공개 | implemented (배포 전) |
| POST | /api/v1/auth/refresh | 공개 (refresh token이 인증) | foundation에서 구현됨 (변경 없음) |
| DELETE | /api/v1/auth/logout | Bearer | Sprint 0 stub 유지 (범위 밖) |

## 변경된 모듈 & 파일

### 새 파일

| 모듈 | 경로 |
|------|------|
| :core | `core/src/main/kotlin/com/lwg/challenge/core/hash/PhoneHasher.kt` |
| :core | `core/src/test/kotlin/com/lwg/challenge/core/hash/PhoneHasherTest.kt` |
| :domain | `domain/src/main/kotlin/com/lwg/challenge/domain/user/User.kt` (순수 도메인 모델 + UserStatus enum) |
| :infra | `infra/src/main/kotlin/com/lwg/challenge/infra/auth/UserEntity.kt` (JPA @Entity) |
| :infra | `infra/src/main/kotlin/com/lwg/challenge/infra/auth/UserJpaRepository.kt` |
| :infra | `infra/src/main/kotlin/com/lwg/challenge/infra/kakao/KakaoOAuthClient.kt` |
| :infra | `infra/src/main/kotlin/com/lwg/challenge/infra/kakao/KakaoUserResponse.kt` |
| :infra | `infra/src/main/kotlin/com/lwg/challenge/infra/kakao/KakaoOAuthExceptions.kt` |
| :api | `api/src/main/kotlin/com/lwg/challenge/api/auth/AuthService.kt` |
| :app (test) | `app/src/test/kotlin/com/lwg/challenge/auth/AuthKakaoIntegrationTest.kt` |

### 수정된 파일

| 파일 | 변경 |
|------|------|
| `api/src/main/kotlin/com/lwg/challenge/api/auth/AuthController.kt` | kakaoLogin 스텁 제거, AuthService 위임 |
| `api/src/main/kotlin/com/lwg/challenge/api/auth/dto/KakaoLoginRequest.kt` | `phoneNumber` 필드 제거 (서버가 Kakao에서 직접 받음, api-contract에 맞춤) |
| `app/src/main/kotlin/com/lwg/challenge/ChallengeServerApplication.kt` | `@EntityScan`/`@EnableJpaRepositories` 추가했다가 → 테스트 호환성 이슈로 기본 `@SpringBootApplication` 스캔에만 의존 |
| `app/src/main/resources/application.yml` | `kakao.base-url` + WebClient 타임아웃 프로퍼티 추가 |
| `api/build.gradle.kts` | `:infra` + `spring-boot-starter-data-jpa` + `spring-tx` 의존성 추가 |
| `infra/build.gradle.kts` | `spring-boot-starter-webflux` (WebClient용) 추가 |
| `app/build.gradle.kts` | test 의존성 (WireMock, Testcontainers Postgres) 추가 |
| `gradle/libs.versions.toml` | `spring-boot-starter-webflux`, `wiremock-standalone`, `testcontainers-*` 등록 |
| `build-logic/src/main/kotlin/KotlinLibraryConventionPlugin.kt` | `testRuntimeOnly(junit-platform-launcher)` 추가 (JUnit5 엔진 discover 실패 방지) |
| `app/src/test/kotlin/com/lwg/challenge/ChallengeServerApplicationTests.kt` | JpaRepositoriesAutoConfiguration 제외 + `UserJpaRepository` / `KakaoOAuthClient` `@MockitoBean` |
| `app/src/test/kotlin/com/lwg/challenge/api/auth/AuthControllerTest.kt` | `AuthService` mock 전환, 케이스 재구성 |

## DB 마이그레이션

- **추가/변경 없음**. Sprint 0 foundation의 `V1__init.sql`이 이미 `users` 테이블을 정의하고 있고 (ADR-0001), 이번 구현은 그 스키마에 JPA 엔티티를 매핑만 했다.
- `UserEntity.columnDefinition="TEXT"` 등 기존 SQL과 일치하도록 맞췄고, `ddl-auto=validate` 상태로 앱이 정상 기동함 (CI에서 확인 필요).

## 설정 변경 (application.yml)

```yaml
kakao:
  base-url: ${KAKAO_BASE_URL:https://kapi.kakao.com}
  webclient:
    connect-timeout-ms: 2000
    read-timeout-ms: 5000
```

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui/index.html
- 영향 받은 경로: `POST /api/v1/auth/kakao`
  - Request: `KakaoLoginRequest(kakaoAccessToken)` — `phoneNumber` 필드 제거
  - Response: `LoginResponse { data: LoginData { accessToken, refreshToken, userId, isNewUser } }` (변경 없음)

## 테스트 결과

```
./gradlew test        →  BUILD SUCCESSFUL
./gradlew :app:build  →  BUILD SUCCESSFUL
```

| 테스트 | 결과 |
|--------|------|
| PhoneHasherTest | 3/3 passed |
| GlobalExceptionHandlerTest | 5/5 passed |
| AuthControllerTest | 5/5 passed |
| ChallengeServerApplicationTests | 1/1 passed |
| **AuthKakaoIntegrationTest** | **4/4 skipped (Docker 필요)** |
| **합계** | **14/14 passed, 4 skipped** |

### AuthKakaoIntegrationTest skip 이유 (Docker 미가용)

현재 작업 환경에 `docker` CLI가 설치되어 있지 않아 Testcontainers Postgres를 기동할 수 없다. 이 경우 테스트 전체를 `@EnabledIf("isDockerAvailable")`로 스킵하도록 구성했다 — 로컬 Docker Desktop이 실행된 상태에서는 자동 활성화된다.

테스트 케이스 5종 (Docker 있을 때 실행, 2026-05-07 시점):
1. 신규 사용자 — Kakao 응답에서 phone 포함 → users INSERT, `isNewUser=true`, `phone_verified=true`, phone SHA-256 해시 저장
2. 기존 사용자 — 같은 `kakao_id` 재로그인 시 nickname/profile 업데이트, `isNewUser=false`, user_id 동일
3. phone 미동의 (`phone_number_needs_agreement=true`) → `phone_number=null`, `phone_verified=false`
4. Kakao `/v2/user/me` 401 → HTTP 200 + `code=701` + `users` 테이블 unchanged
5. Kakao `/v2/user/me` 5xx → 1회 재시도 후 HTTP 200 + `code=703` (호출 횟수 = 2 검증)

통합 테스트는 WireMock으로 `/v2/user/me` 스텁을 두고 Testcontainers Postgres에 실제 Flyway V1 마이그레이션이 적용된 상태에서 컨트롤러 → 서비스 → JPA → DB 전체 경로를 검증한다. `@DynamicPropertySource`로 `kakao.base-url`을 WireMock URL로 오버라이드.

## 설계 메모

### api-contract 준수
api-contract.md 요구사항에 맞춰 Request body에서 `phoneNumber` 필드를 제거했다. 전화번호는 서버가 직접 Kakao `/v2/user/me`에서 받아온다 (모바일이 중간에서 변조/누락시킬 여지를 없앰). 기존 Sprint 0 스텁 DTO에 남아있던 필드를 정리했다. 계약 자체는 변경하지 않았으므로 `협의 이력`에 기록 불필요.

### 모듈 경계
- `:domain.user.User`: 순수 Kotlin 데이터 클래스. JPA 무관.
- `:infra.auth.UserEntity`: JPA 매핑 담당. `toDomain()` 확장.
- `:infra.auth.UserJpaRepository`: Spring Data JPA. MVP 편의상 `:api`가 직접 참조 (Port/Adapter 분리는 현재 과잉 설계).
- `:core.hash.PhoneHasher`: 정규화 + SHA-256. 추후 `/friends/sync-contacts`에서 동일 유틸 사용해 해시 일치 보장.

### WebClient 단독 설치
`:infra`에 `spring-boot-starter-webflux`를 추가했지만 `:app`은 여전히 `spring-boot-starter-web`(Tomcat)이 우선 로드된다. WebFlux의 WebClient + Netty HttpClient만 사용하며, reactive 웹 서버로 기동되지 않는다.

### 에러 매핑
- `KakaoTokenInvalidException` → `DialogException(code=701)` "카카오 로그인이 만료되었습니다. 다시 시도해주세요"
- `KakaoServerException` → `FullScreenException(code=703)` "일시적인 장애로 로그인할 수 없습니다"
- 기존 `GlobalExceptionHandler`가 `BusinessException` → HTTP 200 + body.code로 변환 (ADR-0002 준수).

### phone 해시 정규화
`PhoneHasher.normalize`:
- 공백/하이픈/점/괄호 제거
- `+` 시작 → 그대로 (E.164 가정)
- `0` 시작 → `+82` prefix + 첫 `0` 제거 (한국)

모두 같은 결과:
- `+82 10-1234-5678` → `+821012345678`
- `010-1234-5678` → `+821012345678`
- `01012345678` → `+821012345678`

SHA-256 해시 → 64자 hex → `users.phone_number`.

## 2026-05-07 갱신 — Contract Drift 정정

이번 보고서 본문은 2026-04-24 시점 SDK 방식(`kakaoAccessToken` 페이로드 + `/v2/user/me`만 호출)을 정확히 기술하고 있다. 그러나 그 사이 어느 시점에 **백엔드 코드만 REST API Authorization Code Flow로 이탈**했다 (DTO 필드 `code`, `/oauth/token` 교환 추가, `KAKAO_REST_API_KEY`/`KAKAO_CLIENT_SECRET`/`KAKAO_REDIRECT_URI` 환경변수 도입). 2026-05-07 정렬 작업으로 contract와 보고서가 묘사하는 SDK 방식으로 코드를 되돌렸다.

**제거된 것** (drift 잔재 청소):
- `KakaoTokenResponse.kt` — 파일 삭제
- `KakaoOAuthClient`의 `exchangeCodeForToken`/`doExchangeCodeForToken`/`authWebClient`/`authBaseUrl`
- `application.yml`의 `kakao.auth-base-url`, `kakao.rest-api-key`, `kakao.client-secret`, `kakao.redirect-uri`
- `AuthService`의 `@Value("\${kakao.redirect-uri}")` 주입
- WireMock의 `/oauth/token` stub 5건

**현재 환경변수 상태**:
- 필요: `KAKAO_API_BASE_URL` (선택, default `https://kapi.kakao.com`), `JWT_SECRET`, DB/Redis 접속 정보
- 제거됨 (운영 secret manager에서 정리 권장): `KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET`, `KAKAO_REDIRECT_URI`, `KAKAO_AUTH_BASE_URL`

자세한 변경 파일 목록과 빌드 결과는 [change-log.md](./change-log.md) 참조.

## 미해결 이슈

1. **Docker 미가용 환경에서 통합 테스트 skip**: 현재 개발 셸에서 Docker가 없어 실제 Postgres + JPA 경로가 자동 테스트되지 않음. 로컬 Docker Desktop 실행 후 `./gradlew :app:test --tests "*AuthKakaoIntegrationTest"` 로 수동 검증 필요. CI에도 docker-in-docker 세팅 적용 요망.
2. **실제 Kakao 서버 호출 수동 검증 미수행**: Kakao 개발자 콘솔에서 `account_phone_number` scope 신청·승인이 완료되어야 실토큰으로 end-to-end 검증 가능 (ADR-0008, spec.md 리스크 섹션 참고). scope 승인 전에는 phone 필드가 비어서 오므로 `phone_verified=false` 케이스만 수동 검증 가능.
3. **동시성**: 같은 `kakao_id`로 두 요청이 거의 동시에 들어오면 UNIQUE 제약 위반으로 한 쪽이 `DataIntegrityViolationException`을 받고 500을 돌려준다 (서비스 코드에서 별도 재시도 없음). MVP 시점에는 실사용에서 거의 안 보일 시나리오지만, 향후 보강 필요 (현재 TODO).
4. **Refresh Token Rotation**: 기존 foundation 그대로 — 로그인 시마다 새 refresh 발급되고 옛 것은 무효화되지 않음. ADR-0009(예정)에서 결정.
5. **FCM 토큰 등록 경로 부재**: 현재 로그인에서는 `fcm_token`을 건드리지 않는다 (spec 비범위). 별도 feature `push-fcm`에서 처리 예정.
6. **User 도메인 모델이 지금 사용되지 않음**: `:domain.user.User`를 만들었지만 AuthService는 JPA 엔티티를 직접 다룬다. 추후 다른 도메인 로직이 도메인 모델을 필요로 할 때 `UserEntity.toDomain()` 으로 변환해 사용 (현재는 선제 작성). YAGNI 관점에서 과잉 설계일 수 있으나 지침(spec T-B1)에 따름.

## 참고 링크

- spec: `docs/features/auth-kakao/spec.md`
- contract: `docs/features/auth-kakao/api-contract.md`
- ADR-0002 (BaseResponse), ADR-0008 (Kakao account_phone_number scope)
- V1 스키마: `challenge-server/app/src/main/resources/db/migration/V1__init.sql`
