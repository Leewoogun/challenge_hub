# API Contract — 챌린지 기권 (challenge-forfeit)

- **feature-id**: challenge-forfeit
- **상태**: 🟡 **`draft`** — pm-lead 초안. **backend-dev 가 소유권을 넘겨받아 확정한다**
  (`confirmed` 전까지 모바일 착수 금지 — spec §5)
- **소유**: backend-dev (착수 시 지정)
- **작성**: 2026-09-05 pm-lead
- **상위 spec**: [spec.md](./spec.md)
- **선행 계약**: [challenge-result/api-contract.md](../challenge-result/api-contract.md) — 판정 규칙·`result`·`myResult`·전적 집계 규약
- **선행 계약**: [push-fcm/api-contract.md](../push-fcm/api-contract.md) — `notifications` row·`reference_id` 규약·타입 어휘

## 요약 — 신규 1건 + 기존 1건 확장

| # | Method | Path | 인증 | 설명 | 상태 |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/challenges/{id}/forfeit` | Bearer | 기권 — **즉시 확정** | 🟡 draft |
| 2 | GET | `/api/v1/challenges/{id}` | Bearer | 상세에 **`forfeitedBy` 1필드 추가** (기존 계약 확장) | 🟡 draft |

공통:
- ADR-0002 BaseResponse — 성공·비즈니스 에러는 HTTP 200 + body `code`. 인증 실패만 bare HTTP 401.
- ADR-0010 시간 규약 — `yyyy-MM-dd HH:mm:ss` (KST). `T`·`Z`·offset·밀리초 없음.
- 🔑 **`code` 는 의미가 아니라 표시 방식이다** — `700=스낵바`, `701=다이얼로그`, `705=단일버튼 다이얼로그`
  (`ResponseCode.kt` 실측). 기권 실패는 전부 **`700`** 을 쓰고 사유는 `message` 로 구분한다.

---

## 1. POST `/api/v1/challenges/{id}/forfeit` — 기권

### 요청

**본문 없음.** 기권자는 JWT 의 주체다 — body 로 받지 않는다.

🔴 **`userId` 를 body 나 쿼리로 받지 마라.** 남의 챌린지를 기권시킬 수 있는 문을 여는 것이고,
서버는 이미 토큰으로 요청자를 안다. `isMe` 를 서버가 부여한 `loser-ranking` 선례와 같은 축이다.

### 응답 — 성공

```json
{
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
| `completedAt` | String | ❌ | `yyyy-MM-dd HH:mm:ss` KST |

#### 🟡 협의 항목 — `myResult` 를 넣을 것인가

**pm 초안은 넣는 쪽이다.** 근거: `challenge-result` 가 *"앱이 `result` 를 역할로 뒤집어 계산하면
판정 규칙 사본이 앱에 생긴다"* 는 이유로 `myResult` 를 신설한 선례가 있다(계약 §3.1).

⚠️ **반론도 유효하다** — 이 응답에서 `myResult` 는 **항상 `LOSE` 로 고정**이라 정보량이 0이다.
상수를 필드로 내보내는 셈이다. **backend-dev 가 판단한다.**

### 에러

| 조건 | code | message 초안 |
|---|---|---|
| `IN_PROGRESS` 가 아님 (`PENDING`·`COMPLETED`·`EXPIRED`·`REJECTED`) | 700 | `이미 끝났거나 아직 시작되지 않은 챌린지예요` |
| 요청자가 당사자가 아님 | 700 | `참여자만 기권할 수 있어요` |
| 🔴 **요청자가 이미 인증함** | 700 | `이미 인증했어요. 기권할 수 없어요` |
| 존재하지 않는 챌린지 | 700 | `챌린지를 찾을 수 없어요` |

🔴 **멱등이 아니다.** 두 번째 기권 요청은 `COMPLETED` 라 **첫 줄에 걸려 실패**한다.
`read-all` 이 멱등 200 인 것과 다르다 — 저건 상태를 수렴시키는 연산이고 이건 **일회성 전이**다.

### 🔴 서버 내부 순서 (계약 아님, 검증 대상)

```
1. 검증 3종 (IN_PROGRESS / 당사자 / 내 인증 없음)
2. challenges.forfeited_by = 요청자 userId
3. ChallengeJudgementService.judge(challengeId)  ← 배치와 같은 함수
4. CHALLENGE_FORFEITED 알림 발송 (AFTER_COMMIT)
```

🔴 **3번에서 전적 집계를 새로 쓰지 마라.** `judge()` 가 판정·`COMPLETED`·`UserRecord`·
`FriendRecord` 를 한 트랜잭션에 이미 한다. 새로 쓰면 **자정 배치 경로와 갈린다**
(spec §0.1 — `ChallengeVerdict` KDoc 이 그것을 경계한다).

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

#### 🔴 `Boolean` 이 아니라 `userId` 인 이유

`forfeited: Boolean` 으로 주면 앱은 *"누가 기권했나"* 를 알기 위해
`forfeited && result == OPPONENT_WIN → challenger 가 기권`  으로 **역산**해야 한다.
그건 판정 규칙의 사본을 앱에 심는 것이고, `myResult` 를 신설했던 것과 정확히 같은 이유로 안 된다.

`userId` 를 주면 앱은 `challenger.userId` / `opponent.userId` 와 **비교만** 하면 된다.

#### 🟡 협의 항목 — `active` · `history` 응답에도 넣을 것인가

- `GET /challenges/active` — 홈이 **COMPLETED 를 7일간 노출**하므로(challenge-result 결정)
  기권 건이 홈 카드로 뜬다. 카드에서 기권을 구분해 보여줄 것인지가 갈림길
- `GET /challenges/history` — 보관함에서 기권 표시 여부

**둘 다 pm 이 정하지 않는다.** 앱이 그 화면에서 기권을 그릴 것인지가 먼저이고,
그건 T-M2 와 T-D1(디자인 실측) 결과에 달렸다. **mobile-dev ↔ backend-dev 협의 항목.**

---

## 3. 알림 — `CHALLENGE_FORFEITED` 신설

| | 값 |
|---|---|
| `type` | `CHALLENGE_FORFEITED` |
| 받는 사람 | **기권당한 쪽**(= 이긴 쪽) |
| `reference_id` | `challengeId` |
| 제목 (초안) | `계약 파기.` |
| 본문 (초안) | `{actorNickname}님이 기권했습니다` |

🔴 **문구 한 줄이 곧 발송 스위치다.** `NotificationMessages` 에서 문구가 `null` 인 타입은
dispatcher 가 건너뛴다(선언 8종 중 4종이 그 상태). **문구를 적는 순간 발송이 켜진다.**

### 탭 목적지 — 🔴 두 경로가 다르다. 의도다

| 어디서 탭 | 목적지 |
|---|---|
| **푸시 트레이** | 챌린지 상세 (`PushEventRoute` 에 `Route.Challenge.Detail` 배선) |
| **알림 목록 화면** | 🔴 **이동하지 않는다** |

목록에서 이동하지 않는 것은 `notification-list` 2차 개정 규칙(*"아직 수락 전인 알림만 이동"*)이
그대로 적용된 결과다 — 기권 알림이 가리키는 챌린지는 `COMPLETED` 이므로 `referencePending = false`.

🔑 **예외를 만들지 않는 것이 사용자 결정(2026-09-05)이다.** 원래 불만이 *"알림 화면에서
이미 지난 챌린지로 이동돼서 어색하다"* 였고, 기권 알림도 그 부류다.

---

## 4. 협의 이력

| 날짜 | 주체 | 내용 |
|---|---|---|
| 2026-09-05 | pm-lead | 초안 작성. 사용자 결정 4건 반영 — ① 기권=상대 즉시 승(미인증 취급 아님) ② 인증 전에만 가능 ③ 전적·랭킹 구분 없음 ④ 알림 목록 탭 이동 없음 |
