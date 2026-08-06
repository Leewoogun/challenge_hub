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
    "createdAt": "2026-04-23 19:00:00"
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
    val createdAt: LocalDateTime,  // @JsonFormat(pattern = WIRE_DATETIME) → "2026-04-23 19:00:00" (KST)
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
| 2026-04-23 | backend-dev | createdAt 을 `yyyy-MM-dd HH:mm:ss` (KST) 로 고정 제안 |
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

- 🔴 **시간 포맷은 `yyyy-MM-dd HH:mm:ss` (KST 벽시계) 고정** — [ADR-0010](../../../docs/decisions/0010-datetime-model-localdatetime.md). **ISO-8601 이 아니다** — `T` 구분자·`Z`·offset·밀리초를 **쓰지 않는다.** 날짜 전용은 `yyyy-MM-dd`. 타입은 서버 `java.time.LocalDateTime`/`LocalDate`, 모바일 `kotlinx.datetime.LocalDateTime`/`LocalDate`.
  > ~~2026-07-31 이전: "ISO-8601 UTC 고정, 서버가 KST 로 보내지 않는다"~~ — **정반대로 뒤집혔다.** 양쪽이 `T`·`Z` 를 **거부하고 그 거부를 테스트로 고정**하고 있다.
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
- 🔴 **날짜 직렬화**: 서버 `LocalDateTime` + `@JsonFormat(pattern = WIRE_DATETIME)` → `"2026-08-04 00:00:00"`. 모바일은 `WireLocalDateTimeSerializer` 로 받는다. **`Instant`/`OffsetDateTime` 을 쓰지 않는다**(ADR-0010).
  > ⚠️ 모바일 직렬화기는 **파싱 실패도 `null` 로 흡수**한다. 그래서 서버의 non-null 보증만 믿고 클라의 `null` 방어를 지우면 안 된다 — **보증은 "서버가 안 보낸다"이지 "클라가 항상 파싱한다"가 아니다.**

## 🔴 작성·수정 후 필수 — 시간 표기 린트

**계약 문서를 만들거나 고친 뒤 반드시 실행한다.**

```bash
python3 .claude/scripts/contract-lint.py
```

- **🔴 ERROR 0 이 통과 조건이다.** json 예시의 시간 리터럴이 ADR-0010 포맷(`yyyy-MM-dd HH:mm:ss`)을 어기면 에러다.
- **🟡 WARN 은 전수를 아래 4가지로 분류하고, ④ 가 0건이어야 넘어간다.**

  | | 분류 | 처리 |
  |---|---|---|
  | ① | ADR/문서 참조 — 현행 규칙을 서술 | 정상 |
  | ② | 협의 이력 행 | 정상 |
  | ③ | 취소선 사료 (`~~옛 규칙~~ → 현행`) | 정상 |
  | ④ | **그 외 — 규범 문장인데 옛 규칙을 말한다** | **정정 대상** |

  > 🔴 **"눈으로 확인했다"로 적지 마라.** 그건 검증 가능한 진술이 아니다. **"④ 0건"은 검증 가능하다.**
  >
  > **이 문구가 이렇게 바뀐 이유**: 2026-08-06 첫 사용에서 경고 21건을 "확인했다"고 보고했는데 **2건이 ④였다.** `user-info:98` 의 *"ISO-8601 UTC. (본 endpoint 응답에 시간 필드 없음.)"* — **괄호가 구해주지 못한다.** 시간 필드가 없다는 사실이 *문서가 프로젝트 규칙을 틀리게 말한다*는 것을 바꾸지 않고, 이건 **복사되는 종류의 문장**이다. 나머지 1건은 `challenge-create:119` 의 *"모바일은 kotlinx-datetime 을 의존성에 넣지 않았다"* — 지금은 사실이 아니다(`domain/model/build.gradle.kts:9` 실측).
  >
  > **린트는 정상 동작했다. 새어나간 건 그 다음 단계인 사람의 점검이다.** 20건이 넘으면 "훑어봤다"가 실제로는 표본 확인이 된다.
  >
  > ⚠️ **경고 건수를 줄이는 것을 목표로 삼지 마라.** 위 2건을 정정하자 경고가 **21 → 23 으로 늘었다** — 제대로 된 정정은 *무엇이 틀렸었는지*를 취소선·인용으로 남기고, 그 인용이 다시 토큰에 걸리기 때문이다. **건수가 아니라 ④ 가 지표다.** 건수를 지표로 삼으면 사람이 근거를 지운다.
  >
  > 분류를 스크립트로 자동화하려 하지 마라 — 2026-08-06 에 휴리스틱 분류기를 시도했더니 **6건을 ④ 로 오탐**했다(사료 인용·규칙 서술을 구별 못 한다). **분류는 판단이지 패턴 매칭이 아니다.**

### 왜 이 단계가 필요한가

ADR-0010(2026-07-31)이 시간 포맷을 뒤집었는데 **계약 갱신이 일부만 됐다.** 2026-08-06 감사에서 나온 것:

| 문서 | 낡은 표기 |
|---|---|
| `friends` | 6곳 — ADR-0010 반영 **0건** |
| `challenge-create` | 14곳 — 헤더 취소선만 있고 본문은 그대로 |
| `home-feed` | 2곳 — 서버 타입 주석만 갱신됨 |
| **이 스킬 파일** | **4곳 — 규칙 자체가 옛 내용이었다** |

**마지막 줄이 핵심이다.** 스킬이 *"시간 포맷은 ISO-8601 UTC 고정"* 을 규칙으로 적고 있었으므로, **이 스킬로 쓰는 새 계약은 전부 같은 오류를 갖고 태어났다.** 계약만 고치고 발원지를 두면 재발한다.

> **계약이 서버가 보내지 않는 것을 보낸다고 말하는 것은 누락이 아니라 능동적 오류다.** 그리고 nullable 표를 아무리 잘 만들어도 이 축은 안 잡힌다 — 키는 같고 **포맷만** 다르기 때문이다.

### 이 린트가 덮지 않는 것

- **시간 축만 본다.** enum 값·필드 존재·타입 일치는 안 본다. 응답 shape(키 제거·개명)은 서버 `WireShapeContractTest` 가 덮는다.
- **산문에 숨은 것은 경고까지만.** `→ UTC` 같은 표현은 토큰으로 잡지만 판정은 사람이 한다.
- **PM 레포 문서 대상이라 자동으로 돌 게 없다.** `gradle test` 가 돌려주지 않는다. **이 체크리스트가 우리가 가진 유일한 구동 지점이다** — 안 돌리면 없느니만 못하다.

## 상충 해결

- mobile ↔ backend가 30분 내 합의 실패: pm-lead에게 중재 요청.
- 양쪽 안을 `A안`/`B안`으로 병기 후 pm-lead가 결정 또는 사용자에게 에스컬레이션.
- 결정 후 채택되지 않은 안도 "협의 이력"에 근거와 함께 남긴다 (향후 재논의 시 참조).
