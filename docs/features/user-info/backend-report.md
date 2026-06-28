# Backend Report — user-info

- **feature-id**: user-info
- **작성일**: 2026-06-29
- **담당**: backend-dev
- **상태**: implemented (deploy 전)

## 구현 요약

인증된 사용자의 본인 정보(id, kakaoId, nickname, profileImageUrl)를 반환하는 `GET /api/v1/users/me` 신규. 기존 `UserRepository.findById`(auth-refresh-rotation 작업, ADR-0009) 그대로 활용. V1 스키마 그대로 — **마이그레이션 0건**. TDD로 통합 테스트 + 슬라이스 테스트 작성.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| GET | `/api/v1/users/me` | Bearer JWT | implemented |

- 인증: SecurityFilterChain `.anyRequest().authenticated()` + `JwtAuthenticationFilter` (별도 SecurityConfig 변경 불필요 — `/api/v1/users/me`는 permitAll 목록에 없어 자동 인증 대상).
- principal=userId(Long) 추출은 `FriendController.currentUserId()` 동일 패턴 재사용.

### 성공 응답 (HTTP 200, code 200)

```json
{ "error": false, "code": 200, "message": "",
  "data": { "id": 12, "kakaoId": 4883170475, "nickname": "이우건", "profileImageUrl": "http://img1.kakaocdn.net/..." } }
```

`profileImageUrl`이 null인 사용자는 Jackson NON_NULL 설정으로 응답에서 **필드 자체가 생략**된다(FriendController `pendingRequestId` 와 동일 동작). 모바일은 missing → null 로 역직렬화.

### 에러

| HTTP | code | 상황 |
|---|---|---|
| 401 | 401 | Bearer 누락/만료 (SecurityFilterChain) 또는 토큰 userId가 DB에 없음 (`UnauthorizedException`) |
| 500 | 500 | 인프라 장애 |

## 변경된 모듈 & 파일

| 모듈 | 파일 | 신규/변경 |
|---|---|---|
| `:controller` | `controller/user/UserController.kt` | 신규 |
| `:controller` | `controller/user/dto/UserInfoResponse.kt` (`UserInfoResponse` + `UserInfoData`) | 신규 |
| `:service` | `service/user/UserService.kt` | 신규 |
| `:app` (test) | `controller/user/UserControllerTest.kt` | 신규 |
| `:app` (test) | `integration/UserIntegrationTest.kt` | 신규 |

`UserService.getMe(me: Long): User = userRepository.findById(me) ?: throw UnauthorizedException("user not found")` — `@Transactional(readOnly = true)`.

## DB 마이그레이션

없음. V1 users 스키마(id, kakao_id, nickname, profile_image_url) 그대로 사용.

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui.html
- 반영 경로: `GET /api/v1/users/me` (`@Tag(name="User")`, `@Operation`, `@SecurityRequirement(name="bearerAuth")`)

## 테스트 결과

- 슬라이스 (`UserControllerTest`): **2/2 passed**
  1. 정상 응답 4 필드 (id, kakaoId, nickname, profileImageUrl)
  2. 사용자 부재 → `UnauthorizedException` → HTTP 401 + code 401
- 통합 (`UserIntegrationTest`): **4건 작성, 현재 환경 Docker 미가용으로 4 skipped** (`@EnabledIf` isDockerAvailable — 기존 FriendIntegrationTest 동일 패턴). 컴파일은 성공(스키마/픽스처 정합 검증됨).
  1. 정상 응답 4 필드
  2. 미인증(토큰 없음) → 401
  3. 토큰의 userId가 DB에 없음 → 401
  4. profile_image_url null 사용자 → 응답에서 profileImageUrl 생략
- `./gradlew build`: **SUCCESS**

## 미해결 이슈 / 알려진 한계

- 통합 테스트 4건은 Docker(Testcontainers Postgres) 가용 환경에서 재검증 필요. 현재 CI/로컬 Docker 미가용으로 skip 상태.
- `profileImageUrl` null 시 JSON 필드 생략(NON_NULL) — 명시적 `null` 이 아님. 모바일 역직렬화 기본값 null 가정과 정합. api-contract 예시는 non-null 케이스만 표기.
