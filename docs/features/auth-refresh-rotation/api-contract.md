# API Contract — auth-refresh-rotation

- **상태**: confirmed (2026-05-28)
- **변경 ADR**: [ADR-0009](../../decisions/0009-refresh-token-rotation.md)
- **prior contract**: [auth-kakao/api-contract.md](../auth-kakao/api-contract.md) — `/auth/refresh`는 access만 재발급, refresh 재사용.
- **변경 endpoint 수**: 1 (`POST /api/v1/auth/refresh` 응답 body)

## 변경 요약

| Method | Path | 변경 항목 | 상태 |
|--------|------|----------|------|
| POST | /api/v1/auth/kakao | 변경 없음 (서버 측에서 refresh hash DB 저장은 신규지만 응답 계약은 동일) | confirmed (불변) |
| **POST** | **/api/v1/auth/refresh** | **응답 `data.refreshToken` 필드 추가 + 검증 흐름 강화** | **confirmed (rev 2)** |
| DELETE | /api/v1/auth/logout | 변경 없음 (Sprint 0 스텁 유지, 본 feature 범위 밖) | unchanged |

## POST /api/v1/auth/refresh (revision 2)

### 요청

```http
POST /api/v1/auth/refresh
Content-Type: application/json; charset=utf-8

{ "refreshToken": "eyJhbGciOi..." }
```

- Authorization 헤더 **미사용** (refresh 자체가 인증).
- 모바일 Ktor `Auth(bearer)`의 `sendWithoutRequest`가 `auth` 경로에서 Authorization 헤더를 제외함.

### 성공 응답 (rotation 성공)

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "accessToken": "eyJhbGciOi...(new)",
    "refreshToken": "eyJhbGciOi...(new, rotated)"
  }
}
```

- **`data.refreshToken`이 신규 필드.** 모바일은 받은 즉시 로컬 저장소를 이 값으로 덮어써야 한다 (이전 refresh는 동시에 서버에서 무효화됨).
- 서버 hash 갱신은 응답 발신 전에 commit되므로, 클라이언트가 응답을 못 받았더라도 옛 refresh는 이미 죽은 상태일 수 있음 — 이 경우 다음 호출 시 401을 받아 재로그인 경로로 진입.

### 실패 응답 — 모든 케이스 동일

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "error": true,
  "code": 401,
  "message": "Refresh Token 이 유효하지 않거나 만료되었습니다",
  "data": null
}
```

**401을 반환하는 케이스 (서버 내부 분기 — 클라이언트엔 노출하지 않음)**:

| 케이스 | 의미 |
|---|---|
| JWT 서명 무효 | 변조된 토큰 |
| JWT exp 초과 | refresh 만료 |
| JWT tokenType ≠ refresh | access 토큰을 refresh로 보낸 경우 |
| `findById(userId)` 부재 | 사용자가 삭제됨 / 토큰 위조 |
| `user.refreshTokenHash` NULL | V1 가입자 (마이그레이션 직후) / 로그아웃 후 |
| `user.refreshTokenHash` ≠ sha256(incoming) | 옛 refresh 재사용 (이미 rotation됨) — **핵심 탈취 차단 경로** |

> 정보 노출 최소화를 위해 메시지와 code 모두 동일. 분기는 서버 로그에서만 확인.

### 모바일 처리 규칙

| 응답 | 처리 |
|------|------|
| `code=200` | `data.accessToken`, `data.refreshToken` 둘 다 `TokenProvider.updateTokens()`로 저장. 원 요청을 새 access로 재시도. |
| `code=401` | `TokenProvider.clearTokens()` + `AuthEventBus.emitSessionExpired()` → `MainScreen`이 받아 로그인 탭으로 강제 이동. |
| 기타 code | 로그만 남기고 refresh 실패로 처리 (원 요청 실패). |

## ADR-0002 401 의미 세분화 (하위 명문화)

| 응답 출처 | code | 의미 | 모바일 |
|----------|------|------|--------|
| 일반 API | 401 | access 만료/무효 | Ktor `Auth.refreshTokens` 자동 트리거 → `/auth/refresh` 후 원 요청 재시도 |
| `/auth/refresh` | 401 | refresh 만료/hash 불일치/사용자 부재 | 토큰 클리어 + 세션 만료 이벤트 → 로그인 화면 |

HTTP는 모두 200 (ADR-0002 "항상 HTTP 200" 원칙 보존).

## 마이그레이션 비고

- **V1 시기 가입자**는 이번 V3 마이그레이션 시점에 `refresh_token_hash IS NULL`. 다음 refresh 호출에서 401을 받게 되어 강제 재로그인. 의도된 동작이며, 가입자 수가 적은 MVP 단계 가정.
- **모바일 앱 버전 호환**: 본 ADR 이전 모바일 빌드(`refresh` 응답에서 `refreshToken` 필드 무시)도 forward-compatible — kotlinx.serialization은 모르는 필드 무시. 다만 옛 빌드는 옛 refresh를 계속 사용하다 hash 불일치로 401을 받아 재로그인하게 됨.
