# API Contract — 챌린지 기권 (challenge-forfeit)

- **feature-id**: challenge-forfeit
- **상태**: ✅ **`confirmed`** (2026-09-05) — 미결 0건. **T-M1·T-M3 착수 가능.**
  확정 경로: backend-dev 개정 4건 + forfeit-mobile 회신 + pm-lead 판정. 전문은 §4
- **소유**: **backend-dev** (2026-09-05 인계 완료)
- **작성**: 2026-09-05 pm-lead 초안 → 2026-09-05 backend-dev 개정
- **상위 spec**: [spec.md](./spec.md)
- **선행 계약**: [challenge-result/api-contract.md](../challenge-result/api-contract.md) — 판정 규칙·`result`·`myResult`·전적 집계 규약
- **선행 계약**: [push-fcm/api-contract.md](../push-fcm/api-contract.md) — `notifications` row·`reference_id` 규약·타입 어휘

## 요약 — 신규 1건 + 기존 1건 확장

| # | Method | Path | 인증 | 설명 | 상태 |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/challenges/{id}/forfeit` | Bearer | 기권 — **즉시 확정** | ✅ confirmed · 구현 완료 |
| 2 | GET | `/api/v1/challenges/{id}` | Bearer | 상세에 **`forfeitedBy` 1필드 추가** (기존 계약 확장) | ✅ confirmed · 구현 완료 |

공통:
- ADR-0002 BaseResponse — 성공·비즈니스 에러는 HTTP 200 + body `code`. 인증 실패만 bare HTTP 401.
- ADR-0010 시간 규약 — `yyyy-MM-dd HH:mm:ss` (KST). `T`·`Z`·offset·밀리초 없음.
- 🔑 **`code` 는 의미가 아니라 표시 방식이다** — `700=스낵바`, `701=다이얼로그`, `705=단일버튼 다이얼로그`
  (`ResponseCode.kt` 실측).

  🔴 **초안의 *"기권 실패는 전부 700"* 은 폐기됐다.** 사유와 확정 배분은 §1 에러 표 · §4 협의 이력 1번.

---

## 1. POST `/api/v1/challenges/{id}/forfeit` — 기권

### 요청

**본문 없음.** 기권자는 JWT 의 주체다 — body 로 받지 않는다.

🔴 **`userId` 를 body 나 쿼리로 받지 마라.** 남의 챌린지를 기권시킬 수 있는 문을 여는 것이고,
서버는 이미 토큰으로 요청자를 안다. `isMe` 를 서버가 부여한 `loser-ranking` 선례와 같은 축이다.

### 응답 — 성공

```json
{
  "error": false,
  "code": 200,
  "message": "성공",
  "data": {
    "challengeId": 1001,
    "status": "COMPLETED",
    "result": "OPPONENT_WIN",
    "myResult": "LOSE",
    "completedAt": "2026-09-05 14:23:11"
  }
}
```

| 필드 | 타입 | null | 설명 |
|---|---|---|---|
| `challengeId` | Long | ❌ | |
| `status` | String enum | ❌ | 항상 `COMPLETED` — 기권은 즉시 확정이다 |
| `result` | String enum | ❌ | **역할 기준.** 기권자가 challenger 면 `OPPONENT_WIN`, opponent 면 `CHALLENGER_WIN` |
| `myResult` | String enum | ❌ | **요청자 시점.** 기권자가 부르는 API 이므로 **항상 `LOSE`** |
| `completedAt` | String | ❌ | `yyyy-MM-dd HH:mm:ss` KST. **기권 시각이기도 하다** (§3.2) |

#### ✅ 해소 — `myResult` 를 **넣는다** (backend-dev 판단, 2026-09-05)

pm 초안의 반론(*"항상 `LOSE` 로 고정이라 정보량이 0, 상수를 필드로 내보내는 셈"*)은 유효했지만
**전제가 틀렸다.** 서버가 `LOSE` 를 박아 넣는 것이 아니라
`ChallengeVerdict.outcomeFor(result, isChallenger)` 를 **실제로 태운 결과**를 싣는다 —
판정 규칙 함수를 통과한 값이라 `result` 와 어긋날 수 없고, 오늘 항상 `LOSE` 인 것은
**하드코딩이 아니라 결과**다.

빼면 앱이 ① `result` 를 역할로 뒤집거나 ② *"기권했으니 졌다"* 를 앱 안에 심어야 한다.
`challenge-result` 가 `myResult` 를 신설하며 막았던 것이 정확히 그 사본이다(계약 §3.1).

⚠️ **앱이 이 필드에 의존할 필요는 없다** — 기권 성공 = 내 패배가 자명하므로 화면 전환에 안 써도 된다.

### 에러 — 🔴 **초안(전부 700)에서 개정됐다**

| 조건 | 초안 | **확정** | message |
|---|---|---|---|
| 존재하지 않는 챌린지 | 700 | **705** | `챌린지를 찾을 수 없어요` |
| 요청자가 당사자가 아님 | 700 | **700** | `내 챌린지가 아니에요` |
| `IN_PROGRESS` 가 아님 (`PENDING`·`ACCEPTED`·`CONTRACT_SIGNING`·`REJECTED`·`COMPLETED`·`EXPIRED`) | 700 | **705** | `진행 중인 챌린지만 기권할 수 있어요` |
| 🔴 요청자가 이미 인증함 | 700 | **705** | `이미 인증해서 기권할 수 없어요` |

**개정 근거** (레포 실측 — `ChallengeCommandService` / `VerificationService` KDoc 에 명문화된 배분):

- **700 스낵바** = 권한 위반 + 사용자가 행동을 고치면 되는 것
- **705 단일버튼 다이얼로그** = *"네 화면이 이미 낡았다"* (없음 / 상태가 다름 / 이미 처리됨)

🔴 초안대로면 **`"챌린지를 찾을 수 없어요"` 라는 같은 문장이 화면마다 다른 UI 로 뜬다** —
상세·취소·인증 제출은 전부 705 로 내보내고 있는데 기권만 700 이 된다.

🔴 *"이미 인증함"* 이 705 인 이유: **사용자가 고칠 수 있는 것이 아니다.** 인증은 무를 수 없으므로,
이 응답이 나갔다는 건 **화면이 낡았다**는 뜻이다(다른 기기에서 인증했거나 진입점이 안 사라졌거나).
`700` 은 *"입력을 고쳐 다시 해봐라"* 를 뜻하는 자리라 이 오류의 성격과 맞지 않는다.

### 🔴 이 코드로 앱 동작이 달라지지는 **않는다** — 그래도 705 를 쓴다

⚠️ **초안 개정 때 내가 적었던 *"705 는 확인을 강제해 새로고침 계기를 준다"* 는 삭제됐다. 사실이 아니다.**
forfeit-mobile 실측 + pm-lead 재확인: `ApiResult.kt` 의 `suspendOnFailureWithErrorHandling` 이
`onError(message)` 로 **문자열만** 넘기고 `code` 는 로그 한 줄에서 죽는다.
`onError: (String) -> Unit` 시그니처가 레포 전체 **206곳 단일 종**이라 code 를 나를 통로 자체가 없다 —
**앱은 700 이든 705 든 전부 스낵바로 그린다.** 기존 705 두 건(`이미 처리된 챌린지예요` /
`마감이 지난 챌린지예요`)도 그렇게 나가고 있다.

🔴 **그래도 705 를 700 으로 내리지 않는다.** 앱이 code 를 버리는 것은 **앱의 미구현이고 백로그
항목**이다(pm-lead 등재, 커밋 `9c3bf19`). 서버가 거기 맞춰 표기를 낮추면 **정보를 원천에서 버리는
것**이고, 나중에 앱이 그 결함을 고쳐도 전부 700 이라 아무것도 좋아지지 않는다 —
**버그가 계약에 박제된다.** 705 는 *"이 오류의 성격"* 을 표기한 것이지 앱의 현재 동작에 대한
서술이 아니다.

🔑 **그러므로 이 표를 지지하는 유효한 근거는 첫 번째 것 하나다** — *"같은 문장이 엔드포인트마다
다른 UI 처리를 받으면 안 된다."* 그거면 충분하다.

⚠️ **spec §3 은 이 항목을 `code=700` 으로 적었다.** 의도적 이탈이며 pm-lead 에게 보고했다.

🔴 **멱등이 아니다.** 두 번째 기권 요청은 `COMPLETED` 라 **세 번째 줄에 걸려 실패**한다.
`read-all` 이 멱등 200 인 것과 다르다 — 저건 상태를 수렴시키는 연산이고 이건 **일회성 전이**다.

### 🔴 서버 내부 순서 (계약 아님, 검증 대상)

```
0. SELECT ... FOR UPDATE  ← 신설. 사유는 아래
1. 검증 3종 (당사자 / IN_PROGRESS / 내 인증 없음)
2. challenges.forfeited_by = 요청자 userId
3. ChallengeJudgementService.judge(challengeId)  ← 배치와 같은 함수
4. CHALLENGE_FORFEITED 알림 발송 (AFTER_COMMIT)
```

🔴 **3번에서 전적 집계를 새로 쓰지 않았다.** `judge()` 가 판정·`COMPLETED`·`UserRecord`·
`FriendRecord` 를 한 트랜잭션에 이미 한다. `judge()` 가 `forfeited_by` 를 읽어 스스로
`Forfeit` 으로 환산하므로 **기권 경로와 자정 배치 경로가 같은 코드**다.

#### 🔴 0번(행 잠금)이 추가된 이유 — 초안에 없던 항목이다

기권은 **양쪽 당사자 모두가 부를 수 있는 유일한 상태 전이**다(수락·거절은 opponent 만, 취소는
challenger 만 부른다). 잠금이 없으면 READ COMMITTED 에서 동시에 누른 두 요청이 **둘 다**
`IN_PROGRESS` 를 읽고 통과해, 나중 것이 앞 것의 `forfeited_by`·`result` 를 덮어쓰고
**전적을 한 번 더 올린다.** `total_challenges` 는 소급 정정이 불가능하다.

`FOR UPDATE` 로 잠그면 두 번째 트랜잭션이 첫 커밋을 기다렸다가 갱신된 row 를 다시 읽고,
그때 `COMPLETED` 라 **위 검증 3종의 평범한 `IN_PROGRESS` 게이트가 그대로 막는다** —
동시성 전용 규칙을 새로 만들지 않았다는 것이 이 설계의 핵심이다.

⚠️ **앱에는 영향이 없다.** 두 번째 요청이 받는 응답은 위 에러 표의 세 번째 줄 그대로다.

---

## 2. GET `/api/v1/challenges/{id}` — 상세에 `forfeitedBy` 추가

### 변경

`ChallengeDetailData` 에 **필드 1개 추가.** 나머지 shape 무변경.

```json
{
  "challengeId": 1001,
  "status": "COMPLETED",
  "result": "OPPONENT_WIN",
  "forfeitedBy": 42,
  "...": "나머지 기존 그대로"
}
```

| 필드 | 타입 | null | 설명 |
|---|---|---|---|
| `forfeitedBy` | Long | ✅ | 기권한 사람의 `userId`. **`null` = 기권 없이 끝났거나 아직 안 끝났다** |

🔴 **`null` 이어도 키는 항상 나간다** (`@JsonInclude(NON_NULL)` 미설정 — #24 선례).
`WireShapeContractTest` 가 키 존재를, `ChallengeDetailControllerTest` 가 원문 `"forfeitedBy":null` 을 고정한다.

🔴 값이 있으면 `status` 는 반드시 `COMPLETED` 이고 `result` 는 기권자의 **반대편 승리**다.

#### 🔴 `Boolean` 이 아니라 `userId` 인 이유

`forfeited: Boolean` 으로 주면 앱은 *"누가 기권했나"* 를 알기 위해
`forfeited && result == OPPONENT_WIN → challenger 가 기권`  으로 **역산**해야 한다.
그건 판정 규칙의 사본을 앱에 심는 것이고, `myResult` 를 신설했던 것과 정확히 같은 이유로 안 된다.

`userId` 를 주면 앱은 `challenger.userId` / `opponent.userId` 와 **비교만** 하면 된다.

#### ✅ 확정 — `active` · `history` 에는 **넣지 않는다** (2026-09-05)

pm-lead 판정 + forfeit-mobile 안 채택. 판단 기준이 *"그 화면이 기권을 구분해 그리는가"* 였고
**답이 "안 그린다"** 였다.

근거:
- Lovable 정본에 기권 UI 가 **0건**(pm 실측). 홈 카드·보관함까지 그리면 **디자인 근거 없는
  이탈분이 1건에서 3화면으로** 늘어난다
- 홈·보관함이 말하는 승/패는 기권이든 아니든 **이미 정확하다** — *전적에서 기권을 구분하지 않는다*
  는 사용자 결정(spec §1 제외)과 같은 방향이다
- *"왜 이렇게 끝났나"* 는 **상세가 답할 자리**다

실측: `ActiveChallengeResponse.kt` / `ChallengeHistoryResponse.kt` 둘 다 forfeit 참조 **0건** —
구현이 이미 이 결정대로다.

🔴 **뒤집히면 서버 필드 추가가 따라온다.** 디자이너가 홈 카드 기권 표시를 요구하면 두 응답에
`forfeitedBy` 를 넣는 서버 작업이 돌아온다. **결정이지 누락이 아니다** — 나중에 읽는 사람이
그 둘을 구분할 수 있어야 해서 명시한다.

⚠️ 초안이 남겼던 *"`active`/`history` DTO 에 `challenger.userId` 가 있는지 확인하라"* 는 **소멸했다.**
비교할 일 자체가 없다.

---

## 3. 알림 — `CHALLENGE_FORFEITED` 신설

| | 값 |
|---|---|
| `type` | `CHALLENGE_FORFEITED` |
| 받는 사람 | **기권당한 쪽**(= 이긴 쪽) |
| `reference_id` | `challengeId` |
| 제목 (초안) | `계약 파기.` |
| 본문 (초안) | `{actorNickname}님이 기권했습니다` |

### 🟡 현재 상태 — **타입은 열렸고 문구는 아직 비어 있다** (의도)

🔴 **문구 한 줄이 곧 발송 스위치다.** `NotificationMessages` 에서 문구가 `null` 인 타입은
dispatcher 가 건너뛴다. 레포 규약(`NotificationMessagesTest` KDoc)이
*"여기에 타입을 추가하기 전에 모바일 통지·회신이 선행해야 한다"* 로 못박고 있어,
**forfeit-mobile 이 `PushEvent` + 딥링크 배선 완료를 회신한 뒤에 문구를 넣는다.**
`OPPONENT_VERIFIED` 가 2026-08-14 에 밟은 절차와 같다.

앱이 모르는 타입이 먼저 나가면 트레이에서 **눌러도 아무 데도 안 가는 조용한 실패**가 된다.

⚠️ **그 전까지도 기권 자체는 완전히 동작한다** — 판정·전적·응답 전부 정상이고
알림만 0건이다(`notifications` row 도 안 쌓인다). **블로커가 아니다.**

### 탭 목적지 — 🔴 두 경로가 다르다. 의도다

| 어디서 탭 | 목적지 |
|---|---|
| **푸시 트레이** | 챌린지 상세 (`PushEventRoute` 에 `Route.Challenge.Detail` 배선) |
| **알림 목록 화면** | 🔴 **이동하지 않는다** |

목록에서 이동하지 않는 것은 `notification-list` 2차 개정 규칙(*"아직 수락 전인 알림만 이동"*)이
그대로 적용된 결과다 — 기권 알림이 가리키는 챌린지는 `COMPLETED` 이므로 `referencePending = false`.

🔑 **예외를 만들지 않는 것이 사용자 결정(2026-09-05)이다.** 원래 불만이 *"알림 화면에서
이미 지난 챌린지로 이동돼서 어색하다"* 였고, 기권 알림도 그 부류다.

### 🔴 `referencePending` = **`null`** (확정. 근거를 남긴다)

`notification-list` 계약 §9.1 이 세 값에 각각 의미를 부여해 뒀다:
`true` = 참조 대상이 **아직 응답 대기 중** / `false` = 이미 처리됐거나 종료됐다 /
`null` = **이 타입에는 그 개념이 없다.**

**기권 알림에는 그 개념이 없다.** 이 알림의 수신자는 *"응답할 것"* 이 없다 — 이미 이긴 쪽이고
챌린지는 끝났다. `false` 를 쓰면 *"한때 대기였는데 이제 끝났다"* 로 읽히는데, 이 알림은
**애초에 대기한 적이 없다.** `CHALLENGE_ACCEPTED` · `OPPONENT_VERIFIED` 가 `null` 인 것과 같은 부류다
(§9.2 가 그 둘을 `null` 행으로 명시).

구현상으로도 서버 작업이 **0건**이다 — `NotificationQueryService` 가
`when (type) { CHALLENGE_REQUEST -> …; else -> null }` 이라 새 타입은 자동으로 `null` 이 된다.

⚠️ **앱은 이 값을 보지 않는다.** forfeit-mobile 이 `CHALLENGE_FORFEITED` 를 **타입 단계에서**
비탭으로 고정하기로 했고(`isTappableInList`), 그게 사용자 결정을 더 강하게 고정한다.
🔴 **그렇다고 서버가 아무 값이나 보내도 되는 것은 아니다** — 앱 규칙이 언젠가 «조건부» 로 바뀌면
이 값이 **조용히 작동하기 시작한다.** 그 순간 근거 없이 들어간 값이 정책이 된다. 그래서 위에 근거를 남긴다.

---

## 3.2 시간 — 🔴 `forfeitedAt` 은 **없다**

기권은 즉시 `COMPLETED` 이므로 **`completedAt` 이 곧 기권 시각**이다. 마이그레이션에도
`forfeited_at` 컬럼을 만들지 않았다(V12 주석에 근거 박제). 값이 같은 필드를 둘 두면 언젠가 갈린다.

👉 **앱은 기권 시각이 필요하면 `completedAt` 을 읽어라.**

---

## 4. 협의 이력

| 날짜 | 주체 | 내용 |
|---|---|---|
| 2026-09-05 | pm-lead | 초안 작성. 사용자 결정 4건 반영 — ① 기권=상대 즉시 승(미인증 취급 아님) ② 인증 전에만 가능 ③ 전적·랭킹 구분 없음 ④ 알림 목록 탭 이동 없음 |
| 2026-09-05 | backend-dev | **소유권 인계.** 초안 개정 4건 (아래) |
| 2026-09-05 | forfeit-mobile | 개정 4건 **전부 수용, 이견 0**. ① `active`/`history` **둘 다 넣지 마라**(앱이 그 두 화면에서 기권을 안 그린다) ② 🔴 **705 근거 1줄이 실측과 다르다** — 앱은 `code` 를 소비하지 않는다(`onError: (String) -> Unit`, 206곳). **결론은 유지하되 근거를 바꿔라** ③ `myResult` 수용(앱은 안 읽지만 계약에 있는 게 맞다) ④ 알림 배선 3줄 설계 완료, 착수는 `confirmed` 이후 |
| 2026-09-05 | pm-lead | **판정 3건.** ① `active`/`history` **미포함 확정**(mobile 안 채택) ② `referencePending` 은 값과 **근거를 계약에 명시할 것** ③ 🔴 705 를 700 으로 내리지 마라 — 앱 미구현에 서버 표기를 맞추면 **버그가 계약에 박제된다.** 앱 결함은 백로그 등재(`9c3bf19`) |
| 2026-09-05 | backend-dev | **`confirmed` 로 확정.** 미결 0건. 반영: `active`/`history` 미포함(§2) · `referencePending = null` + 근거(§3) · 🔴 **705 근거에서 *"확인을 강제해 새로고침 계기를 준다"* 삭제**(실재하지 않는 앱 동작이었다 — §1) |

### 개정 1 — 🔴 에러 코드를 전부 700 → **705 3건 + 700 1건** (§1)

초안이 4가지 실패를 전부 700 으로 적었다. 그대로 두면 **같은 문장이 엔드포인트마다 다른 UI 로**
뜬다(`"챌린지를 찾을 수 없어요"` 는 상세·취소·인증에서 이미 705). 레포에 명문화된 배분
(700=권한/사용자가 고칠 것, 705=화면이 낡음)을 그대로 따랐다.

⚠️ **spec §3 의 *"이미 인증한 사람은 기권할 수 없다 (거부, `code=700`)"* 와 어긋난다.**
의도적 이탈이며 pm-lead 에게 보고했다. 근거는 §1 에러 표 아래.

### 개정 2 — ✅ `myResult` 를 **넣는다** (초안의 🟡 협의 항목 해소)

초안의 반론이 *"항상 LOSE 인 상수"* 였으나, 서버는 상수를 박는 것이 아니라
`ChallengeVerdict.outcomeFor` 를 태운 값을 싣는다. 근거 전문은 §1.

### 개정 3 — 🔴 서버 내부 순서에 **0번(행 잠금)** 추가

초안 순서에 없던 항목이다. 없으면 spec §3 의 수용 기준
*"양쪽이 동시에 기권 요청을 보내도 한쪽만 성공한다 — `forfeited_by` 가 덮어써지지 않음을 확인"* 이
**실제로 성립하지 않는다.** 근거 전문은 §1.

⚠️ **앱 영향 0** — 두 번째 요청이 받는 응답은 에러 표 그대로다.

### 개정 4 — 🟡 §3 에 *"문구는 모바일 회신 후에 넣는다"* 명시

레포 규약(`NotificationMessagesTest` KDoc)이 요구하는 절차인데 초안에 없었다.
`OPPONENT_VERIFIED` 선례와 같다.

### ✅ 미결 0건 — `confirmed`

초안의 🟡 협의 항목 2건(`myResult` / `active`·`history` 확장)이 둘 다 결론에 도달했고,
개정 과정에서 새로 생긴 쟁점(에러 코드 근거 · `referencePending`)도 닫혔다.

🔴 **`confirmed` 이후의 변경은 `change-log.md` 에 기록한다** (CLAUDE.md 규칙).

### ⚠️ 계약 밖으로 넘긴 것 1건 — 앱이 `code` 를 소비하지 않는 문제

`ResponseCode` 가 정의한 표시 방식(700=스낵바 / 705=단일버튼 다이얼로그)을 **앱이 구현하지 않고
있다.** 이 feature 에서 고칠 크기가 아니다(`ApiResult` 채널 + 호출부 206곳). pm-lead 가
백로그에 등재했다(`9c3bf19`). 🔑 **이 건의 교훈은 따로 있다** — 앱의 조용한 미구현이
**서버 쪽 판단까지 왜곡했다.** 계약 문서가 앱 동작보다 앞서 있다는 걸 아무도 모르고 있었다.
