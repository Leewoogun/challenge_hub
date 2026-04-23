---
name: api-contract
description: "challenge 프로젝트의 모바일-백엔드 API 계약을 표준 형식으로 작성/갱신한다. 엔드포인트 스펙, 요청/응답 shape, 에러 코드, 인증 요구, 페이지네이션을 정의. 'API 계약', 'API 스펙', 'endpoint 정의', '요청/응답 shape' 작업이나 mobile-dev ↔ backend-dev가 계약을 협의할 때 반드시 이 스킬을 사용한다."
---

# API Contract — 모바일-백엔드 API 계약 포맷

mobile-dev와 backend-dev가 합의하는 API 계약의 표준 포맷. `docs/features/{feature-id}/api-contract.md`에 작성·갱신한다.

## 언제 사용하나
- pm-lead: feature-spec 단계에서 **초안**(draft) 작성
- backend-dev: 초안 리뷰 후 구현 가능한 형태로 제안 (상태 `negotiating`)
- mobile-dev: 백엔드 제안을 리뷰하고 소비 관점에서 수정 요구 (상태 `negotiating`)
- 양쪽 합의 시: 상태 `confirmed`. 이후 변경은 change-log.md 기록 + 이 파일의 "협의 이력"에 append

## 템플릿

````markdown
# API Contract — {Feature Title}

- **feature-id**: {kebab-case}
- **상태**: draft | negotiating | confirmed
- **최종 수정**: {YYYY-MM-DD} by {agent-name}

## 엔드포인트 요약
| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| GET | /api/users/{id} | 사용자 프로필 조회 | Bearer JWT |

---

## {Method} {Path}

### 설명
한 문장.

### 인증
- 방식: `Bearer JWT` | `공개` | `API Key`
- 스코프/권한: (필요 시)

### Path Parameters
| 이름 | 타입 | 필수 | 설명 |
|------|------|-----|------|
| id | string(UUID) | ✓ | 사용자 ID |

### Query Parameters
| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|

### Request Body (JSON)
```json
{
  "name": "string, 1..50",
  "email": "string, email 형식"
}
```

### 성공 Response (HTTP 200)

`BaseResponse`를 상속한 응답 data class. 예:

```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "id": 123,
    "name": "string",
    "email": "string | null",
    "createdAt": "2026-04-23T10:00:00Z"
  }
}
```

서버 쪽 타입:
```kotlin
data class UserProfileResponse(
    val data: UserProfileData,
) : BaseResponse()

data class UserProfileData(
    val id: Long,
    val name: String,
    val email: String?,
    val createdAt: Instant,  // ISO-8601 UTC 직렬화
)
```

### 에러 Response (**HTTP 200**, body의 code로 구분)

| code | 상황 | 예시 메시지 |
|------|------|-----------|
| 700 | 비즈니스 — 스낵바 | "이미 가입된 사용자입니다" |
| 701 | 비즈니스 — 다이얼로그 | "카카오 계정 연결이 만료되었습니다. 재로그인하세요" |
| 702~703 | 비즈니스 — 전체화면 | "서비스 점검 중입니다" |
| 705 | 비즈니스 — 단일 버튼 | "계약서가 이미 확정되었습니다" |
| 401 | 토큰 만료 | "토큰 만료 — Refresh" |

에러 바디 shape (BaseResponse 그대로):
```json
{ "error": true, "code": 700, "message": "이미 가입된 사용자입니다" }
```

> **HTTP 4xx는 사용하지 않음.** 이 엔드포인트 계약서에 HTTP status는 "항상 200 (인프라 장애 제외)"로 기재하면 충분.

### 페이지네이션 (목록 엔드포인트만)
- 방식: `cursor` | `offset` — 프로젝트 내에서 통일.
- 요청 파라미터, 응답 메타 구조 명시.

### 모바일측 주의사항
- nullable 필드, 포맷 변환 필요 필드, 캐시 정책.

### 백엔드측 주의사항
- 트랜잭션 경계, 이벤트 발행, 영향 테이블.

---

## 협의 이력
| 일시 | 작성자 | 변경 |
|------|-------|------|
| 2026-04-23 | pm-lead | 초안 |
| 2026-04-23 | backend-dev | createdAt을 ISO-8601 UTC로 고정 제안 |
| 2026-04-23 | mobile-dev | name 최대 길이 50 요구 |
````

## 협상 프로토콜

1. **초안(pm-lead):** Method / Path / 대략적 요청·응답 shape.
2. **백엔드 리뷰(backend-dev):** 구현 가능성 검토, 타입 구체화, 에러 코드 정의, DB 제약 반영.
3. **모바일 리뷰(mobile-dev):** 소비자 관점에서 nullable, 포맷, 페이지네이션 방식 요구.
4. **확정:** 양쪽 합의 시 상단 상태를 `confirmed`로 변경. 이후 변경은 change-log.md + "협의 이력"에 append.

## 응답 규약 — BaseResponse 패턴 (ADR-0002 accepted)

**모든 응답은 `BaseResponse`를 상속하거나 그 자체를 반환한다. HTTP status는 성공/실패 무관하게 200 (비즈니스 에러 포함). 인프라 장애(DB down 등)만 HTTP 5xx.**

```kotlin
// 공통 베이스 클래스 (서버 :api 모듈 / 모바일 :remote:model)
open class BaseResponse(
    val error: Boolean = false,
    val code: Int = 200,
    val message: String = "",
)

// 데이터 응답은 data class가 상속, data 필드에 실제 페이로드
data class LoginResponse(
    val data: LoginData,
) : BaseResponse()
```

### 코드 규약 (CarOwnerRenew ApiCode와 일치)

| code | 의미 | HTTP | 모바일 처리 |
|------|------|------|------------|
| 200 | 성공 (`error=false`) | 200 | 정상 |
| 401 | 토큰 만료 | 200 | Refresh Token 재시도 후 재요청 |
| 500 | 인프라 장애 | 500 | 재시도/장애 안내 |
| 700 | 비즈니스 에러 — 스낵바 | **200** | 토스트/스낵바 |
| 701 | 비즈니스 에러 — 다이얼로그 | **200** | 확인 다이얼로그 |
| 702, 703 | 비즈니스 에러 — 전체화면 | **200** | 전체화면 에러 |
| 705 | 비즈니스 에러 — 단일 버튼 | **200** | 단일 버튼 다이얼로그 |

> **HTTP 4xx는 거의 쓰지 않는다.** 입력 검증 실패도 `HTTP 200 + code=700`. 이유: 모바일 `ApiResultCall`이 `body.code == 200`만 Success로 간주하므로 서버가 4xx를 반환하면 HTTP 예외 경로와 비즈니스 에러 경로가 섞여 처리가 지저분해진다.

## 합의 원칙 (프로젝트 공통)

- **시간 포맷은 ISO-8601 UTC 고정.** 서버가 KST 등 로컬 타임존으로 보내지 않는다.
- **nullable 여부를 반드시 명시.** "없을 수 있음"을 적지 않으면 양쪽이 다르게 가정한다.
- **모든 응답은 BaseResponse 상속 또는 자체**. 에러도 `{error: true, code: 7xx, message}`로 HTTP 200에 담김.
- **페이지네이션 방식을 섞지 않는다.** 프로젝트 내 cursor 또는 offset 중 하나로 통일.
- **ID 타입(UUID vs Long vs String)을 초기 계약에서 확정.** 참고: Server 스펙은 `BIGSERIAL` 기반 `Long`.
- **버전 관리:** breaking change는 `/api/v2/...` 새 경로로. 기존 엔드포인트 응답 shape의 의미 변경 금지.

## 프로젝트 스택 특이 사항

- **백엔드 source of truth: SpringDoc OpenAPI**. `challenge-server`는 SpringDoc 2.8.6이 설치되어 있어, 컨트롤러·DTO에 붙인 Swagger 어노테이션이 자동으로 OpenAPI spec(JSON)을 생성한다. 이 spec이 배포된 후에는 api-contract.md를 수동 동기화보다 spec 링크와 해시로 참조하는 편이 안전.
- **백엔드 응답 DTO**: `:api` 모듈에 `data class Xxx(val data: XxxData) : BaseResponse()` 패턴. `BaseResponse`는 ADR-0002 참조.
- **백엔드 DTO 필드명**: camelCase, JSON도 camelCase(Jackson 기본). 의도적으로 snake_case가 필요하면 `@JsonProperty`.
- **모바일 DTO**: `:remote:model`에 `@Serializable open class BaseResponse(...)` + 상속 data class들. kotlinx.serialization이 JSON ↔ Kotlin 자동 매핑. CarOwnerRenew의 `BaseResponse.kt` 참조.
- **모바일 `ApiResultCall`**: `body.code == 200`만 Success. 그 외는 `ApiResult.Failure.CustomError(code, message)` → UI에서 code별 분기 처리(700 스낵바, 701 다이얼로그 등).
- **모바일 API 인터페이스**: `:remote:api`에 Ktorfit `@GET`/`@POST`. 서버 path와 1:1 매핑.
- **enum 값**: 양쪽 다 대문자 `UPPER_SNAKE_CASE` 문자열로 통일 (`CHALLENGER_WIN`, `PENDING` 등 Server 스펙 일치).
- **빈 응답**: 204 No Content 사용 금지. 성공 시에도 항상 BaseResponse(`{error:false, code:200, message:""}`)를 반환 — 필요 시 `data` 필드를 null 허용 또는 생략.
- **날짜 직렬화**: `Instant` / `OffsetDateTime` → ISO-8601 UTC 문자열. Jackson/kotlinx.serialization 모두 JavaTimeModule / kotlinx-serialization-datetime 설정 필수.

## 상충 해결

- mobile ↔ backend가 30분 내 합의 실패: pm-lead에게 중재 요청.
- 양쪽 안을 `A안`/`B안`으로 병기 후 pm-lead가 결정 또는 사용자에게 에스컬레이션.
- 결정 후 채택되지 않은 안도 "협의 이력"에 근거와 함께 남긴다 (향후 재논의 시 참조).
