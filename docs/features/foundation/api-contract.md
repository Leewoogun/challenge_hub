# API Contract — Foundation (auth endpoints)

- **feature-id**: `foundation`
- **상태**: draft (pm-lead 초안, backend-dev 확정 예정)
- **최종 수정**: 2026-04-23 by pm-lead

## 엔드포인트 요약

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| POST | /api/v1/auth/kakao | 카카오 로그인 → JWT 발급 | ❌ (공개) |
| POST | /api/v1/auth/refresh | Access Token 재발급 | ❌ (Refresh Token 본문) |
| DELETE | /api/v1/auth/logout | 로그아웃 (Refresh 무효화, FCM 토큰 제거) | ✅ Bearer |

> 전부 HTTP 200 반환. 비즈니스 에러는 body `code` 필드로 구분 (ADR-0002, `api-contract` 스킬 참조).

---

## POST /api/v1/auth/kakao

### 설명
모바일이 카카오 SDK로 얻은 access_token과 (동의 시) phone_number를 받아 challenge 자체 JWT로 교환.

### 인증
공개 (토큰 발급 엔드포인트)

### Request Body
```json
{
  "kakaoAccessToken": "kakao_xxxx",
  "phoneNumber": "+821012345678"
}
```

- `kakaoAccessToken` (string, required): Kakao SDK가 반환한 OAuth access_token. 서버가 Kakao API로 유효성 검증.
- `phoneNumber` (string, nullable): Kakao `account_phone_number` scope 동의 시 국제 포맷 전화번호. 서버는 SHA-256 해시하여 `users.phone_number`에 저장.

> **Sprint 0 Foundation에서는 kakao 검증 stub** — 토큰 형식만 검사하고 임의 userId로 JWT 발급. Sprint 1 `auth-kakao`에서 Kakao /v2/user/me 실제 연동.

### 200 Response
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "accessToken": "eyJhbGciOi...",
    "refreshToken": "eyJhbGciOi...",
    "userId": 123,
    "isNewUser": true
  }
}
```

### 에러 (HTTP 200 + code)
| code | 상황 |
|------|------|
| 700 | 카카오 토큰 검증 실패 (스낵바) |
| 701 | 계정 탈퇴 상태 (다이얼로그) |

---

## POST /api/v1/auth/refresh

### 설명
Refresh Token으로 새 Access Token 발급. (Refresh Token 자체는 교체하지 않음 — 단순 재발급. 회전 정책은 향후 별도 결정)

### 인증
Refresh Token은 body로 전달 (Access Token과 별개)

### Request Body
```json
{
  "refreshToken": "eyJhbGciOi..."
}
```

### 200 Response
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "accessToken": "eyJhbGciOi..."
  }
}
```

### 에러 (HTTP 200 + code)
| code | 상황 |
|------|------|
| 401 | Refresh Token 만료 또는 무효 — 재로그인 유도 |

---

## DELETE /api/v1/auth/logout

### 설명
로그아웃 — 서버측에서 사용자의 Refresh Token 무효화, FCM 토큰 `users.fcm_token` null로 설정.

> Sprint 0에서는 로직 없이 200만 반환 (Refresh Token 무효화는 저장소가 아직 없음 — 향후 Redis blacklist 또는 DB 컬럼으로).

### 인증
Bearer Access Token

### Request Body
없음

### 200 Response
```json
{
  "error": false,
  "code": 200,
  "message": ""
}
```

### 에러
없음 (토큰 없으면 401 HTTP 수준 — Spring Security 기본 동작)

---

## 공통 에러 바디 shape

모든 엔드포인트에서 비즈니스 에러 발생 시:

```json
{
  "error": true,
  "code": 700,
  "message": "사용자에게 보여줄 메시지"
}
```

## JWT 규약

- Access Token: HS256, 만료 1시간, payload `{userId: Long, iat, exp}`
- Refresh Token: HS256, 만료 14일, payload `{userId: Long, tokenType: "refresh", iat, exp}`
- 시크릿: `application.yml`의 `jwt.secret` (환경변수 `JWT_SECRET`로 override)

## 모바일측 주의사항

- 응답 `data.accessToken`을 메모리(ViewModel 또는 TokenManager)에 보관, `data.refreshToken`은 Encrypted SharedPreferences(Android) / Keychain(iOS).
- `code=401` 수신 시 자동으로 `/auth/refresh` 호출 후 원 요청 재시도 (interceptor 레벨).
- `isNewUser=true`면 온보딩 화면으로 유도.

## 백엔드측 주의사항

- `POST /auth/kakao`는 현재 stub — 반드시 Sprint 1에서 Kakao `GET /v2/user/me` 연동 + 실제 사용자 조회/생성 로직 추가.
- `users` 테이블은 V1 마이그레이션에만 만들고, INSERT는 Sprint 1부터.
- Refresh Token 회전(rotation)은 현재 미구현 — 1회성 재발급만. 탈취 감지가 필요해지면 별도 ADR.

## 협의 이력

| 일시 | 작성자 | 변경 |
|------|-------|------|
| 2026-04-23 | pm-lead | 초안 — Sprint 0 foundation scope 한정 |
