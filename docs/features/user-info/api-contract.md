# API Contract — user-info

- **feature-id**: user-info
- **상태**: confirmed
- **최종 수정**: 2026-06-26

## 엔드포인트 요약

| Method | Path | 설명 | 인증 |
|---|---|---|---|
| GET | `/api/v1/users/me` | 본인 정보 조회 (id, kakaoId, nickname, profileImageUrl) | Bearer |

---

## GET `/api/v1/users/me`

### 설명
인증된 사용자의 본인 정보를 조회한다. JWT 토큰의 `principal=userId`로 식별. 모바일은 Home 진입 시 호출 + DataStore 캐시.

### 인증
- 방식: Bearer (`Authorization: Bearer <accessToken>`)
- userId 추출: 기존 `JwtAuthenticationFilter` (foundation 작업) — `@AuthenticationPrincipal userId: Long`

### Request
- Path / Query / Body 모두 없음

### 성공 Response (HTTP 200, code 200)

```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "id": 12,
    "kakaoId": 4883170475,
    "nickname": "이우건",
    "profileImageUrl": "http://img1.kakaocdn.net/..."
  }
}
```

### 서버 DTO (Kotlin)

```kotlin
data class UserInfoResponse(
    val data: UserInfoData,
) : BaseResponse()

data class UserInfoData(
    val id: Long,
    val kakaoId: Long,
    val nickname: String,
    val profileImageUrl: String?,
)
```

### 필드 명세

| 필드 | 타입 | nullable | 의미 |
|---|---|---|---|
| `id` | Long | NO | users.id (앱 내부 PK) |
| `kakaoId` | Long | NO | users.kakao_id (카카오 로그인 식별자) |
| `nickname` | String | NO | users.nickname (VARCHAR(50), UNIQUE 아님) |
| `profileImageUrl` | String? | YES | users.profile_image_url (카카오 프로필) |

### 에러 Response

| HTTP | code | 상황 | 모바일 처리 |
|---|---|---|---|
| 401 | 401 | Bearer 누락 / access 만료 / 사용자 부재 | Ktor Auth 자동 refresh → 실패 시 강제 재로그인 (ADR-0009) |
| 500 | 500 | 인프라 장애 (DB down 등) | 일반 에러 |

비즈니스 에러 (code 700/701/702/703/705)는 본 endpoint에서 사용 안 함.

### service 처리

- `UserService.getMe(me: Long): User`
- `userRepository.findById(me) ?: throw UnauthorizedException("user not found")`
- 토큰의 userId가 DB에 없으면 401 (회원탈퇴/삭제 케이스)

### 정렬 / 페이지네이션
해당 없음 (단일 row).

---

## 공통 에러 코드

| code | 의미 | 본 feature 사용 |
|---|---|---|
| 200 | 성공 | ✓ |
| 401 | 인증 만료 | ✓ |
| 500 | 인프라 장애 | ✓ |
| 700 | snackbar | 본 feature 사용 안 함 |
| 701 | dialog | 본 feature 사용 안 함 |

## 시간 포맷
ISO-8601 UTC. (본 endpoint 응답에 시간 필드 없음.)

## 협의 이력

| 일자 | 변경 | 비고 |
|---|---|---|
| 2026-06-26 | draft → confirmed | spec에서 mobile/backend 합의 완료 (필드 4개 + Bearer 인증). 추가 협의 불요. |
