# API Contract — 카카오 로그인 (auth-kakao)

- **feature-id**: auth-kakao
- **상태**: confirmed
- **최종 수정**: 2026-04-24 by pm-lead (양쪽 구현 완료 후 확정)

## 엔드포인트 요약

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| POST | /api/v1/auth/kakao | 카카오 access_token으로 로그인/가입 + JWT 발급 | 공개 |
| POST | /api/v1/auth/refresh | Refresh Token으로 Access Token 재발급 | 공개 (refresh 토큰이 인증 역할) |

> `/api/v1/auth/logout`은 Sprint 0 스텁 그대로 유지 (이번 범위 밖). `/api/v1/auth/kakao`와 `/refresh`는 이미 foundation에서 기본 구조는 있으나, 이번에 **kakao 엔드포인트만 실구현으로 교체**한다. refresh는 foundation에서 이미 완성되어 있어 변경 없음.

---

## POST /api/v1/auth/kakao

### 설명
모바일이 Kakao SDK로 획득한 access_token을 서버에 전달 → 서버가 `/v2/user/me`로 검증 → users upsert → 자체 JWT 발급.

### 인증
- 방식: 공개 (Authorization 헤더 없음)

### Request Body (JSON)
```json
{
  "kakaoAccessToken": "string, not blank"
}
```

서버 DTO:
```kotlin
data class KakaoLoginRequest(
    @field:NotBlank
    @field:Size(max = 2048)
    val kakaoAccessToken: String,
)
```

### 성공 Response (HTTP 200)

```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "accessToken": "eyJhbGciOi...",
    "refreshToken": "eyJhbGciOi...",
    "userId": 12,
    "isNewUser": true
  }
}
```

서버 타입:
```kotlin
data class LoginResponse(
    val data: LoginData,
) : BaseResponse()

data class LoginData(
    val accessToken: String,
    val refreshToken: String,
    val userId: Long,
    val isNewUser: Boolean,
)
```

### 에러 Response (**HTTP 200**, body의 code로 구분)

| code | 상황 | 예시 메시지 |
|------|------|-----------|
| 700 | `kakaoAccessToken` 공백/누락 (@Valid 실패) | "카카오 토큰이 누락되었습니다" |
| 701 | Kakao 토큰 검증 실패 (Kakao가 401/403) | "카카오 로그인이 만료되었습니다. 다시 시도해주세요" |
| 703 | Kakao 서버 장애 / 타임아웃 (1회 재시도 후 실패) | "일시적인 장애로 로그인할 수 없습니다" |

> 인프라 장애(DB down 등)만 HTTP 500 + code=500.

### Kakao 응답 shape (참고, 서버 내부 처리용)

서버가 `GET https://kapi.kakao.com/v2/user/me` (Authorization: `Bearer {kakaoAccessToken}`)을 호출하여 받는 응답의 핵심 필드:

```json
{
  "id": 123456789,
  "kakao_account": {
    "phone_number_needs_agreement": false,
    "phone_number": "+82 10-1234-5678",
    "profile_needs_agreement": false,
    "profile": {
      "nickname": "홍길동",
      "profile_image_url": "https://..."
    }
  }
}
```

처리 규칙:
- `id` → `users.kakao_id`
- `kakao_account.profile.nickname` → `users.nickname` (없으면 `"사용자{id}"` 기본값)
- `kakao_account.profile.profile_image_url` → `users.profile_image_url` (nullable)
- `kakao_account.phone_number` 존재 AND `phone_number_needs_agreement=false`:
  - 정규화: 공백/하이픈 제거, `+82` 그대로 유지 → `+821012345678`
  - SHA-256 해시 → hex → `users.phone_number` (64자)
  - `users.phone_verified=true`
- 그 외 → `phone_number=NULL`, `phone_verified=false`

### 모바일측 주의사항
- `isNewUser=true`면 추후 온보딩 화면으로, `false`면 홈으로 (이번 범위에서는 둘 다 홈으로 임시 이동).
- `accessToken` / `refreshToken`은 즉시 secure storage(Android Keystore / iOS Keychain)에 저장. 평문 SharedPreferences 금지.
- `code=701`은 "재로그인 필요" 다이얼로그. 사용자가 버튼 누르면 Kakao SDK 재호출.
- `code=703`은 "재시도" 버튼 제공.

### 백엔드측 주의사항
- Kakao 호출에 `WebClient` 사용. 타임아웃: connect 2s, read 5s. 1회 재시도 후 실패면 `code=703`.
- users upsert는 단일 트랜잭션. kakao_id UNIQUE 제약으로 동시성 보호.
- phone 해시는 `MessageDigest.getInstance("SHA-256")` 표준 — 프로젝트 내 해시 방식 고정 (모바일 `/friends/sync-contacts`가 같은 방식 사용 예정, 이번 범위 밖).
- Kakao 응답에서 `kakao_account`가 null이면 profile_needs_agreement로 간주하고 nickname 기본값 사용. 로그인은 진행.
- JWT 발급은 foundation의 `JwtTokenProvider.generateAccessToken(userId)` / `generateRefreshToken(userId)` 재사용.
- 테스트: Kakao 실서버 대신 WireMock으로 `/v2/user/me` 스텁. `application-test.yml`의 `kakao.base-url`을 WireMock 서버로 교체.

---

## POST /api/v1/auth/refresh

**변경 없음** (foundation에서 완성, 재협의 불필요).

### 설명
Refresh Token 검증 후 새 Access Token 발급. Refresh Token 자체는 재발급하지 않는다.

### Request Body
```json
{ "refreshToken": "string, not blank" }
```

### 성공 Response
```json
{
  "error": false, "code": 200, "message": "",
  "data": { "accessToken": "eyJ..." }
}
```

### 에러
- `code=401` — Refresh Token invalid/expired → 모바일은 로그인 화면으로 강제 이동.

---

## 협의 이력

| 일시 | 작성자 | 변경 |
|------|-------|------|
| 2026-04-24 | pm-lead | 초안 — foundation 스텁을 실제 Kakao 연동으로 교체. Kakao 응답 매핑 규칙, 에러 코드 3종(700/701/703), phone SHA-256 정규화 규칙 정의. |
| 2026-04-24 | backend-dev | 구현 중 `KakaoLoginRequest`에서 `phoneNumber` 필드 제거 (서버가 Kakao에서 직접 수신, 계약 원안 그대로). |
| 2026-04-24 | mobile-dev | 구현 완료. 필드명/타입/에러 코드 모두 계약과 일치. 차이 없음. |
| 2026-04-24 | pm-lead | 양쪽 구현 완료 — 상태 `confirmed`. |
