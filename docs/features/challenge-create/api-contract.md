# API Contract — 챌린지 신청 (challenge-create)

- **feature-id**: challenge-create
- **상태**: confirmed
- **최종 수정**: 2026-07-28 by backend-dev (오픈 이슈 **5건 전부 해소** — 미결 항목 없음)
- **상위 spec**: [spec.md](./spec.md)

## 엔드포인트 요약

| # | Method | Path | 설명 | 인증 |
|---|--------|------|------|------|
| 1 | POST | `/api/v1/challenges` | 챌린지 신청 (PENDING 생성) | Bearer JWT |
| 2 | GET | `/api/v1/challenges/received` | 받은 도전장 목록 (PENDING, 마감 미경과) | Bearer JWT |
| 3 | POST | `/api/v1/challenges/{id}/accept` | 수락 + 내 미션 입력 → IN_PROGRESS | Bearer JWT |
| 4 | POST | `/api/v1/challenges/{id}/reject` | 거절 → REJECTED | Bearer JWT |
| 5 | DELETE | `/api/v1/challenges/{id}` | 챌린저가 보낸 PENDING 취소 (물리 삭제) | Bearer JWT |

공통:
- 모든 endpoint `Authorization: Bearer <access-token>` 필수.
- ADR-0002 BaseResponse 패턴 — 항상 HTTP 200 + body `code`로 성공/비즈니스 에러 구분.
- ADR-0009 refresh — 일반 API 401은 Ktor Auth 플러그인 자동 갱신, `/auth/refresh` 401은 강제 재로그인.
- 페이지네이션 없음 (받은 도전장은 소량 가정).
- ~~시간 필드 직렬화: **ISO-8601 UTC** (`2026-07-28T15:00:00Z`).~~ → 🔴 **2026-07-31 [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)으로 대체됨.** 현행은 **`yyyy-MM-dd HH:mm:ss` (KST)** 다 — `T`·`Z`·offset·밀리초 없음. 날짜 전용은 `yyyy-MM-dd`(변경 없음).
  > **아래 본문의 `"...T15:00:00Z"` 예시들은 이 문서가 확정된 시점(2026-07-28)의 표기이며 현재 서버 응답과 다르다.** 실제 값은 `deadline = "2026-08-01 00:00:00"` 형태다(같은 순간의 다른 표기 — 시각은 이동하지 않았다). 개정 근거·실측 대조는 [datetime-model-migration](../datetime-model-migration/summary.md) 참조. 이 문서는 **당시 합의 기록으로 보존**한다.
- ID 타입: 전부 `Long` (BIGSERIAL 기반).
- 기존 `GET /api/v1/challenges/active`(home-feed)와 경로 네임스페이스를 공유한다. **응답 shape 변경 없음** — 본 feature는 신규 경로만 추가.

### 🔴 공통 규약 — `message`는 그대로 사용자에게 보이는 UI 텍스트다

2026-07-28 mobile-dev 확인 사항. 모바일의 에러 채널은 **`code`를 버리고 `message`(String)만 ViewModel에 전달**한다:

- `remote/network/.../ApiResultConverterFactory.kt` — HTTP 200 + `body.code != 200` → `ApiResult.Failure.CustomError(code, message)`
- `remote/network/.../ApiResult.kt`의 `suspendOnFailureWithErrorHandling(onError: (String) -> Unit)` — `is CustomError -> onError(message)` 에서 **code 소실**
- 이 `onError: (String) -> Unit` 시그니처가 `FriendsRepository` / `ActiveChallengeRepository` / `UserInfoRepository` / `RecordRepository` 전체의 프로젝트 표준 (user-info feature "옵션 1", commit `faae2cd`)

따라서:

1. **서버의 `message`는 로그 문구가 아니라 완성된 한국어 UI 문장이어야 한다.** 영문 예외 메시지·스택·내부 식별자가 새어나가면 사용자 화면에 그대로 노출된다. 본 계약에 적힌 문구를 **글자 그대로** 응답에 싣는다.
2. **모바일은 `code`로 분기하지 않는다.** `accept` / `reject` / `cancel`이 **어떤 코드로든** 실패하면 → 스낵바로 `message` 노출 + 받은 도전장 목록 **무조건 재조회**. 초안이 705에 기대했던 "목록이 낡았다 → 재조회" 효과는 코드 분기 없이 "실패 시 항상 재조회"로 동일하게 달성된다. 기능 손실 없음.
3. **그럼에도 서버는 700/705 배분을 의미대로 유지한다** (아래 각 엔드포인트 표). 지금은 모바일이 무시하지만, 향후 error-channel을 `(Int, String)`으로 리팩터하면 서버 변경 없이 즉시 활용 가능하다. 그 리팩터는 기존 Repository 5개 + 테스트(FriendsViewModelTest 10건, FriendsSearchViewModelTest 12건, UserInfoRepositoryImplTest 5건 등) 전면 수정이라 본 feature 범위 밖이다.

## 공통 enum

### DeadlineType (요청 전용)
| 값 | 의미 | 서버 환산 |
|---|---|---|
| `TODAY` | 오늘 자정 마감 | `challenge_date` = KST 오늘, `deadline` = KST 익일 00:00 → UTC |
| `TOMORROW` | 내일 자정 마감 | `challenge_date` = KST 내일, `deadline` = KST 익익일 00:00 → UTC |

> **클라이언트는 timestamp를 보내지 않는다.** 기기 시계 조작·타임존 불일치를 차단하고 마감 기준을 서버로 일원화하기 위함. KST(UTC+9) 고정 — 해외 사용자 대응은 범위 밖.
>
> 예: KST 2026-07-28 14:00에 `TODAY`로 생성 → `challengeDate` = `2026-07-28`, `deadline` = `2026-07-28T15:00:00Z` (= KST 07-29 00:00).

### ChallengeStatus (응답)
| 값 | 의미 |
|---|---|
| `PENDING` | 신청됨, 상대 응답 대기 |
| `IN_PROGRESS` | 수락됨, 진행 중 |
| `REJECTED` | 거절됨 |

> `ACCEPTED` / `CONTRACT_SIGNING`은 본 feature에서 **사용하지 않는다** (spec 스코프 결정 5). 영혼의 맹세 feature 도입 시 재등장.
> `COMPLETED` / `EXPIRED`도 본 feature의 응답에 나타나지 않는다.

---

## 1. POST `/api/v1/challenges`

### 설명
친구에게 챌린지를 신청한다. `PENDING` 상태의 `challenges` row를 1건 생성한다.

### 인증
- 방식: `Bearer JWT`. 인증 주체가 `challenger`가 된다.

### Request Body (JSON)
```json
{
  "opponentId": 42,
  "myMission": "오늘 운동 1시간 하기",
  "betContent": "커피 사기",
  "deadlineType": "TODAY"
}
```

| 이름 | 타입 | 필수 | 검증 |
|------|------|-----|------|
| `opponentId` | Long | ✓ | 본인 아님 + `friendships`에 `ACCEPTED` 관계 존재 |
| `myMission` | String | ✓ | trim 후 1~100자 |
| `betContent` | String | ✓ | trim 후 1~100자 |
| `deadlineType` | enum | ✓ | `TODAY` \| `TOMORROW` |

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "challengeId": 7,
    "status": "PENDING",
    "challengeDate": "2026-07-28",
    "deadline": "2026-07-28T15:00:00Z"
  }
}
```

```kotlin
data class ChallengeCreateResponse(val data: ChallengeCreateData) : BaseResponse()

data class ChallengeCreateData(
    val challengeId: Long,
    val status: ChallengeStatus,
    // @JsonFormat(shape = STRING, pattern = "yyyy-MM-dd") — 반드시 "2026-07-28" 문자열
    val challengeDate: LocalDate,
    // @JsonFormat(shape = STRING) — 반드시 "2026-07-28T15:00:00Z"
    val deadline: Instant,
)
```

> **직렬화 고정 (2026-07-28 확정)** — 모바일은 `kotlinx-datetime`을 의존성에 넣지 않았다(home-feed에서 stdlib `kotlin.time.Instant`만 쓰기로 확정, `domain/model/build.gradle.kts`에 해당 의존성 없음). 서버는 `@JsonFormat`을 **명시적으로** 붙여 Jackson 설정 변화와 무관하게 `"2026-07-28"` 평문 ISO date를 보장하고, 컨트롤러 슬라이스 테스트가 실제 응답 JSON 문자열을 assert한다 (`[2026,7,28]` 배열 회귀 방지).
>
> **양측 수신 타입 대조** — 이 표가 어긋나면 파싱이 조용히 깨진다:
>
> | 필드 | 서버 타입 | JSON | **모바일 수신 타입** |
> |---|---|---|---|
> | `challengeDate` | `LocalDate` | `"2026-07-28"` | **`String`** (`= ""` 기본값) |
> | `deadline` | `Instant` | `"2026-07-28T15:00:00Z"` | `String` → `Instant.parse()` |
> | `createdAt` | `Instant` | `"2026-07-28T02:11:00Z"` | `String` → `Instant.parse()` |
> | `challengeId` / `challengerId` / `opponentId` | `Long` | `7` | `Long` (`= 0L` 기본값) |
> | `status` | `ChallengeStatus` | `"PENDING"` | enum (UPPER_SNAKE_CASE) |

### 에러 Response (HTTP 200, body의 code로 구분)

`message`는 **확정 문구**다 (위 공통 규약 참조 — 그대로 사용자에게 노출된다).

| code | 상황 | message (확정) |
|------|------|-----------|
| 700 | 친구가 아닌 상대 | `친구에게만 챌린지를 걸 수 있어요` |
| 700 | 본인에게 신청 | `자기 자신에게는 챌린지를 걸 수 없어요` |
| 700 | 중복 — **내가** 건 챌린지가 이미 있음 | `오늘은 이 친구와 이미 챌린지가 있어요` |
| 700 | 중복 — **상대가** 나에게 건 PENDING이 있음 | `이 친구가 이미 도전장을 보냈어요. 받은 도전장을 확인해보세요` |
| 700 | 미션 길이 위반 | `미션은 1자 이상 100자 이하로 입력해주세요` |
| 700 | 내기 길이 위반 | `내기 내용은 1자 이상 100자 이하로 입력해주세요` |
| 700 | 존재하지 않는 상대 | `상대를 찾을 수 없어요` |

> **중복 메시지를 2종으로 나눈 이유** (2026-07-28 mobile-dev 요청): 초안의 "이미 오늘 이 친구와 **진행 중인** 챌린지가 있어요"는 상대가 나에게 건 `PENDING` 때문에 막힌 경우 오히려 혼란을 준다. 사용자가 홈의 진행 중 목록을 봐도 아무것도 없기 때문이다(PENDING은 `/challenges/active`에 안 잡힌다). 역방향 PENDING일 때는 **어디를 봐야 하는지 알려주는** 문구로 분기한다.
>
> 판정 순서: 역방향 PENDING을 먼저 검사하고, 그 외 모든 중복(내가 건 PENDING / 양방향 IN_PROGRESS)은 첫 번째 문구로 묶는다.

### 모바일측 주의사항
- `deadline`은 표시 전용. 카운트다운은 기존 `Instant.toRelativeKoreanString`(`:core:utils`) 재사용.
- 성공 시 홈으로 복귀하며 진행 중 목록을 갱신할 필요는 없다 — 생성된 챌린지는 `PENDING`이라 `/challenges/active`에 안 잡힌다.

### 백엔드측 주의사항
- 중복 판정 쿼리: `WHERE ((challenger_id=me AND opponent_id=target) OR (challenger_id=target AND opponent_id=me)) AND challenge_date=? AND status IN ('PENDING','IN_PROGRESS')`. **양방향으로 검사** — 상대가 나에게 이미 건 경우도 중복 (2026-07-28 mobile-dev 동의).
- 동시 요청 race는 위 조건의 부분 유니크 인덱스가 없으므로 애플리케이션 레벨 검사 + `saveAndFlush` 후 재확인 패턴 권장 (friends 2차 `saveAndFlush` 선례).
- `opponent_mission`은 NULL로 insert (T-B1 / V5 마이그레이션 선행 필수).
- **길이 검증은 `trim()` 후 `1..100`, 카운팅 단위는 UTF-16 code unit** (JVM `String.length`). 한글은 1자=1이라 모바일과 자동 일치하고, BMP 밖 이모지만 2로 센다. 모바일이 `TextField maxLength=100` 하드캡 + 공백 전용 입력 시 버튼 비활성을 걸어 이 700은 실질적으로 도달 불가지만, 서버 검증은 최종 방어선으로 유지한다.

---

## 2. GET `/api/v1/challenges/received`

### 설명
인증 사용자가 `opponent`인 `PENDING` 챌린지 중 **마감이 지나지 않은 것**을 `created_at` 내림차순으로 반환. 없으면 빈 배열.

### 인증
- 방식: `Bearer JWT`

### Query Parameters
없음.

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "challenges": [
      {
        "challengeId": 7,
        "challengerId": 42,
        "challengerNickname": "민수",
        "challengerProfileImageUrl": "https://.../profile.jpg",
        "challengerMission": "오늘 운동 1시간 하기",
        "betContent": "커피 사기",
        "challengeDate": "2026-07-28",
        "deadline": "2026-07-28T15:00:00Z",
        "createdAt": "2026-07-28T02:11:00Z"
      }
    ]
  }
}
```

```kotlin
data class ReceivedChallengesResponse(val data: ReceivedChallengesData) : BaseResponse()

data class ReceivedChallengesData(val challenges: List<ReceivedChallengeItem>)

data class ReceivedChallengeItem(
    val challengeId: Long,
    val challengerId: Long,
    val challengerNickname: String,
    val challengerProfileImageUrl: String?,   // nullable — 카카오 프로필 미설정 가능
    val challengerMission: String,
    val betContent: String,
    val challengeDate: LocalDate,             // "2026-07-28"
    val deadline: Instant,                    // "2026-07-28T15:00:00Z"
    val createdAt: Instant,                   // "2026-07-28T02:11:00Z" — 초 단위로 절삭
)
```

> **nullable로 명시되지 않은 필드는 항상 존재한다.** 모바일 DTO는 전 필드에 기본값(`= 0L`, `= ""`)을 두는 방어적 패턴이라 필드가 누락되면 크래시 대신 조용히 빈 카드가 렌더된다 — 즉 필드 누락은 런타임에 드러나지 않는다. 서버는 `challengerProfileImageUrl` 외에는 절대 null/누락을 보내지 않는다.

### 에러 Response
비즈니스 에러 없음 (빈 목록은 `challenges: []`로 정상 응답).

### 모바일측 주의사항
- `challengerProfileImageUrl`은 **nullable**. 원격 이미지 로더가 아직 없으므로(backlog) 닉네임 이니셜 placeholder로 렌더 — `friends` 2차 `FriendListItem` 패턴 재사용.
- 마감 임박 표시는 `deadline` 기준 클라이언트 계산.
- `challengeDate`는 현재 UI에서 쓰지 않는다(카운트다운은 `deadline` 기준). 매퍼에서 버려도 무해 — 서버는 계속 내려준다.
- **`Instant.parse()` 실패 시 `Instant.DISTANT_PAST` 폴백**이라 파싱 에러가 조용히 "이미 마감된 카드"로 나타난다(home-feed 선례). 서버가 표기를 고정하는 이유.

### 백엔드측 주의사항
- `challenges` ↔ `users` JOIN 1쿼리. `challenger_id` 방향만 조인하면 된다.
- 마감 필터는 `deadline > now()`. status는 DB에서 `PENDING`인 채로 두고 **응답에서만 제외**(lazy expiry, spec 리스크 항목).
- **시간 표기 고정**: `Z` suffix 필수, 오프셋 표기(`+09:00`) 금지, **초 단위로 절삭**해 나노초 자릿수가 섞이지 않게 한다. `deadline`은 항상 KST 자정이라 나노초가 없지만 `createdAt`은 `LocalDateTime.now()` 유래라 나노초가 붙으므로 DTO 매핑 시 `truncatedTo(SECONDS)`를 적용한다.

---

## 3. POST `/api/v1/challenges/{id}/accept`

### 설명
받은 도전장을 수락하고 본인 미션을 입력한다. 상태가 `IN_PROGRESS`로 전환되고 `verifications` PENDING row 2건이 함께 생성된다.

### 인증
- 방식: `Bearer JWT`. 인증 주체가 해당 챌린지의 `opponent`여야 한다.

### Path Parameters
| 이름 | 타입 | 필수 | 설명 |
|------|------|-----|------|
| `id` | Long | ✓ | challengeId |

### Request Body (JSON)
```json
{ "myMission": "책 30페이지 읽기" }
```

| 이름 | 타입 | 필수 | 검증 |
|------|------|-----|------|
| `myMission` | String | ✓ | trim 후 1~100자. `opponent_mission`에 저장된다. |

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": { "challengeId": 7, "status": "IN_PROGRESS" }
}
```

### 에러 Response

| code | 상황 | message (확정) |
|------|------|-----------|
| 700 | 미션 길이 위반 | `미션은 1자 이상 100자 이하로 입력해주세요` |
| 705 | 이미 처리된 챌린지 (PENDING 아님) | `이미 처리된 챌린지예요` |
| 705 | 마감 경과 | `마감이 지난 챌린지예요` |
| 705 | 존재하지 않는 challengeId | `챌린지를 찾을 수 없어요` |
| 700 | 당사자 아님 (opponent 아님) | `내가 받은 도전장이 아니에요` |

> **705를 쓰는 이유(서버 의미론)**: 이 세 케이스는 **목록이 이미 낡았다**는 신호다. 다만 모바일은 현재 code를 못 받으므로(위 공통 규약) **실패 시 항상 목록을 재조회**해 동일한 효과를 낸다. 705 배분은 향후 error-channel 리팩터를 위한 서버측 의미 보존이다.
>
> **`권한이 없어요` → `내가 받은 도전장이 아니에요`로 변경** (2026-07-28 mobile-dev 요청): `message`가 그대로 사용자에게 보이는데 "권한이 없어요"는 사용자 입장에서 맥락이 없다.

### 백엔드측 주의사항
- **단일 트랜잭션**: `challenges` UPDATE(status, opponent_mission) + `verifications` INSERT 2건(challenger, opponent).
- **read-after-write 보장** (2026-07-28 mobile-dev 질의에 대한 확답): `@Transactional`은 **service 메서드**에 걸리므로 컨트롤러가 응답을 직렬화하기 전에 커밋이 끝난다. 리드 리플리카가 없고 단일 Postgres이므로, accept 성공 응답을 받은 직후 모바일이 `GET /challenges/received` + `GET /challenges/active`를 곧바로 호출하면 **방금 수락한 챌린지가 반드시 `/active`에 잡히고 `/received`에서는 반드시 사라진다.** 통합 테스트로 이 순서를 검증한다(spec 수용 기준 "수락된 챌린지가 `/challenges/active` 응답에 즉시 나타난다").
- `verifications`는 `uq_verifications_challenge_user` 유니크 제약이 있으므로 중복 수락 시도 시 제약 위반이 안전망 역할.
- `verifications` PENDING row 생성은 **V4(`home_feed_verification_status`)로 이미 가능하다** (2026-07-28 pm-lead 확인). V4가 `photo_url`·`verified_at`을 nullable로 완화하고 `status VARCHAR(20) NOT NULL DEFAULT 'PENDING'` + `created_at`을 추가해 뒀으며, V4 주석이 `created_at`을 "챌린지 IN_PROGRESS 전이 시점"으로 명시한다. 따라서 INSERT 시 `challenge_id` / `user_id`만 채우면 되고 **V5에 추가 완화는 불필요하다.**

### 모바일측 주의사항
- 성공 후 받은 도전장 목록과 진행 중 챌린지 목록을 **둘 다** 갱신해야 한다. 서버가 read-after-write를 보장하므로 지연/재시도 없이 즉시 호출해도 된다.
- **실패 시에도** 받은 도전장 목록을 재조회한다 (code 분기 없이 항상).

---

## 4. POST `/api/v1/challenges/{id}/reject`

### 설명
받은 도전장을 거절한다. 상태가 `REJECTED`로 전환된다.

### 인증
- 방식: `Bearer JWT`. 인증 주체가 `opponent`여야 한다.

### Request Body
없음.

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": { "challengeId": 7, "status": "REJECTED" }
}
```

### 에러 Response

| code | 상황 | message (확정) |
|------|------|-----------|
| 705 | 이미 처리된 챌린지 (PENDING 아님) | `이미 처리된 챌린지예요` |
| 705 | 마감 경과 | `마감이 지난 챌린지예요` |
| 705 | 존재하지 않는 challengeId | `챌린지를 찾을 수 없어요` |
| 700 | 당사자 아님 (opponent 아님) | `내가 받은 도전장이 아니에요` |

> 거절은 body가 없어 길이 검증이 없다는 점만 accept와 다르다.

---

## 5. DELETE `/api/v1/challenges/{id}`

### 설명
챌린저가 자신이 보낸 `PENDING` 챌린지를 취소한다. **물리 삭제**.

### 인증
- 방식: `Bearer JWT`. 인증 주체가 `challenger`여야 한다.

### Request Body
없음.

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": { "challengeId": 7 }
}
```
> **초안 변경 (2026-07-28)**: 초안은 `data` 없이 `{error, code, message}`만이었으나, friends의 동일 성격 엔드포인트 `DELETE /friends/requests/{id}`가 `data: { requestId }`를 반환한다(`CancelFriendRequestResponse`). 프로젝트 내 일관성을 위해 `data: { challengeId }`로 맞춘다. 삭제된 row의 id지만 모바일이 어떤 카드를 지울지 대조하는 데 쓸 수 있다.
>
> 204 No Content는 사용하지 않는다(프로젝트 규약).

### 에러 Response

| code | 상황 | message (확정) |
|------|------|-----------|
| 705 | PENDING이 아님 (이미 수락/거절됨) | `이미 처리된 챌린지예요` |
| 705 | 존재하지 않는 challengeId | `챌린지를 찾을 수 없어요` |
| 700 | 챌린저 아님 | `내가 보낸 도전장이 아니에요` |

### 백엔드측 주의사항
- `PENDING`은 `verifications` row가 아직 없으므로 FK 정리 불필요. 다만 방어적으로 `challenge_id` 참조 row 부재를 확인할 것.
- **⚠️ 이 엔드포인트는 도달 경로가 제한적이다 — 의도된 상태다 (오픈 이슈 5, 옵션 C 확정).** 챌린저가 자기가 보낸 PENDING 챌린지의 `challengeId`를 얻을 조회 API가 없다(`/received`는 내가 opponent인 것만, `/active`는 IN_PROGRESS만). 따라서 취소는 **생성 직후 같은 세션에서 create 응답의 `challengeId`를 들고 있을 때만** 가능하다.
- **모바일은 이번 feature에서 취소 호출부를 만들지 않는다.** 따라서 이 엔드포인트는 **서버 테스트(슬라이스 + 서비스 단위 + 통합)로만 검증**되며 모바일 연동 검증 대상이 아니다. 서버는 권한·상태·존재 검증을 전부 포함해 계약대로 구현한다 — 후속 feature가 보낸 도전장 목록 UI를 붙이면 그대로 살아난다.

---

## 오픈 이슈 — **전건 해소, 미결 없음**

### 해소됨

1. ~~**`verifications.photo_url` NOT NULL 여부**~~ — ✅ 2026-07-28 해소. V4가 이미 nullable 완화 + `status` DEFAULT `'PENDING'`을 마쳤다. V5는 `opponent_mission` 완화 1건만.
2. ~~**에러 코드 700 vs 705 배분**~~ — ✅ 2026-07-28 해소. **서버는 초안 배분을 유지**하되, 모바일이 `code`를 소비할 수 없다는 사실을 계약에 명시하고(위 공통 규약) 모바일 동작을 "실패 시 항상 목록 재조회"로 확정. 부수적으로 **모든 `message`를 사용자 노출 문구로 확정**했고 `권한이 없어요` → `내가 받은/보낸 도전장이 아니에요`로 교체.
3. ~~**중복 판정의 양방향 여부**~~ — ✅ 2026-07-28 해소. **양방향 유지**(mobile-dev 동의). 다만 역방향 PENDING 케이스는 별도 문구로 분기.
4. ~~**미션/내기 최대 길이 100자**~~ — ✅ 2026-07-28 해소. **100자 유지**. 카운팅은 UTF-16 code unit(양측 `String.length`로 자동 일치). 모바일이 `maxLength=100` 하드캡을 걸어 서버 700은 최종 방어선 역할만 한다.

5. ~~**보낸 도전장 조회 엔드포인트 부재**~~ — ✅ 2026-07-28 해소. **옵션 C 채택 (사용자 결정, pm-lead 전달).**

   - **`GET /api/v1/challenges/sent`는 도입하지 않는다.** 엔드포인트는 5건 그대로다.
   - **`DELETE /api/v1/challenges/{id}`는 계약대로 구현하고 서버 테스트도 작성한다.** 죽은 코드가 아니다 — 생성 직후(create 응답의 `challengeId` 보유 시) 도달 가능하고, 후속 feature가 목록 UI를 붙이면 그대로 살아난다. 권한·상태·존재 검증 전부 포함한다.
   - **모바일은 취소 호출부를 만들지 않는다.** 따라서 이 엔드포인트는 **서버 테스트로만 검증**되며 통합 검증(모바일 연동) 대상이 아니다.
   - 기각된 대안: **(A)** `GET /challenges/sent` 신규 — 서버 비용은 거의 0이나 실제 비용이 디자인(T-D2 +1 섹션)과 모바일(T-M5 +25%, 홈 `combine` 소스 4→5)에 쏠리고, 이미 등재된 "HomeViewModel 기존 테스트 10건 회귀 0" 리스크를 더 압박한다. 핵심 검증 목표(생성→PENDING→수락→IN_PROGRESS 홈 노출)는 C로 온전히 달성된다. **(B)** `/received`를 `/pending` + `direction`으로 통합 — mobile-dev 반대 근거 채택: 방향별로 표시 필드 자체가 다른데(RECEIVED는 `challengerNickname` + 상대 미션 + 수락/거절, SENT는 `opponentNickname` + 내 미션 + 취소) 한 DTO에 합치면 절반이 항상 무의미한 값이 되고, 모바일 DTO의 전 필드 기본값 방어 패턴 탓에 **잘못된 방향의 필드를 읽어도 컴파일·런타임 모두 조용히 통과**한다.
   - spec 정정 완료(스코프 결정 6 / 시나리오 4 취소선 / 취소 수용 기준을 "서버 테스트로만 검증"으로 한정 / 비범위에 "보낸 도전장 목록 + 모바일 취소 UI" 추가) + 백로그 등재 완료.

## 협의 이력

| 일시 | 작성자 | 변경 |
|------|-------|------|
| 2026-07-28 | pm-lead | 초안 — endpoint 5건, DeadlineType 서버 환산 규약, lazy expiry 방침 (상태: `draft`) |
| 2026-07-28 | backend-dev | 오픈 이슈 1~4에 대한 구체안 제시 + 이슈 5(보낸 도전장 조회 부재) 신규 제기. DELETE 응답에 `data.challengeId` 추가 제안, 중복 메시지 2종 분기 제안, 100자 UTF-16 카운팅 규약 제안 (상태: `draft` → `negotiating`) |
| 2026-07-28 | mobile-dev | 이슈 2·3·4 동의. 이슈 1은 **모바일 error-channel이 `code`를 버리고 `message`만 전달**하는 구조(`onError: (String) -> Unit`, user-info "옵션 1" 표준)임을 근거로 계약 문구 정정 요청 — 서버 배분은 유지하되 모바일은 코드 분기 대신 "실패 시 항상 재조회". `message`가 곧 UI 텍스트이므로 `권한이 없어요` 문구 교체 요구. `challengeDate`는 kotlinx-datetime 미도입으로 **평문 ISO date 문자열 필수**, `deadline`/`createdAt`은 `Z` suffix 고정 요구(파싱 실패 시 `Instant.DISTANT_PAST` 폴백으로 조용히 깨짐). DELETE `data` 추가에 동의. accept의 read-after-write 보장 여부 질의 |
| 2026-07-28 | backend-dev | 위 요구 전량 반영 — 공통 규약에 "`message`=UI 텍스트" 절 신설, 에러 메시지 전건 확정 문구화, 중복 메시지 2종 분기 확정, `@JsonFormat` 명시 + 슬라이스 테스트로 직렬화 고정, `createdAt` 초 단위 절삭, DELETE `data.challengeId` 채택, read-after-write 보장 확답(`@Transactional`이 service에 있어 응답 직렬화 전 커밋 완료). 이슈 5는 shape 무영향이라 별도 트랙으로 분리 (상태: `negotiating` → **`confirmed`**) |
| 2026-07-28 | mobile-dev | 재확인 회신 — 이슈 1은 "700으로 평탄화하지 말고 **배분 유지**" 명시(지금 평탄화하면 정보가 영영 소실되고, 모바일 관점에선 700/705 결과가 동일하므로 이득이 없다). 이슈 2 메시지 2종 분기 채택 동의(passthrough라 모바일 추가 비용 0). 이슈 3은 모바일도 `String.length`(UTF-16)로 카운트해 서버와 완전 동일 — 이모지 2 카운트는 미용 이슈로 수용. 이슈 4 a·b·c 전부 동의, `challengeDate` **모바일 수신 타입 = `String`** 명기 요청. 이슈 5는 **(A) 권고** + (B) 반대 근거 제시, 스코프 판단이라 pm-lead 결정 수용 |
| 2026-07-28 | pm-lead | **이슈 5 → 옵션 C 확정 (사용자 결정).** `GET /challenges/sent` 미도입, 엔드포인트 5건 유지. `DELETE /challenges/{id}`는 계약대로 구현 + 서버 테스트 작성하되 **모바일 호출부 없음 → 서버 테스트로만 검증**, 통합 검증 대상 제외. (A)는 실제 비용이 design·모바일에 쏠려 임계 경로를 늘리고 "HomeViewModel 테스트 10건 회귀 0" 리스크를 압박해 기각, (B)는 mobile-dev 근거로 기각. spec 정정(스코프 결정 6 / 시나리오 4 취소선 / 수용 기준 한정 / 비범위 추가) + 백로그 등재 완료. 나머지 1~4 합의안 전량 승인 |
| 2026-07-28 | backend-dev | 오픈 이슈 5 해소 처리 + 양측 수신 타입 대조표 추가 + §5에 "모바일 호출부 없음 / 서버 테스트 전용 검증" 명시. **미결 항목 0건 — 계약 최종 확정** |
