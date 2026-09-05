# 챌린지 기권 (challenge-forfeit) — Spec

- **feature-id**: challenge-forfeit
- **owner**: pm-lead
- **상태**: `draft` — 브레인스토밍 승인 완료(2026-09-05). 착수 전 `run-feature` 로 API 계약 협의 필요
- **생성**: 2026-09-05
- **선행**: [challenge-result](../challenge-result/summary.md)(`ChallengeVerdict` · 자정 판정 배치 · 전적 집계) · [soul-oath](../soul-oath/summary.md)(컨셉)
- **관계**: [ai-verification](../ai-verification/spec.md) 과 **의존 없음** — §0.2 참조

## 배경 / 문제

지금은 챌린지를 시작하면 **끝내는 방법이 마감을 기다리는 것뿐이다.** 못 하게 됐다는 걸
이미 아는 사람도 자정까지 진행 중 카드를 들고 있어야 하고, 상대는 *"쟤가 할 건가 안 할 건가"* 를
마감까지 모른다.

기권은 그 상태를 **명시적으로 닫는 수단**이다. 사용자 결정(2026-09-05)으로 기권은
*"나는 인증 안 한 것으로 친다"* 가 아니라 **"상대에게 승리를 준다"** 는 선언이다.

---

## §0 사전 실측 (2026-09-05, pm-lead 서버 코드 직접 확인)

> 🔴 **이 표는 실측만 적는다. 판정·승인·계획은 적지 않는다.**
> (`ai-verification` 에서 pm 이 자기 승인을 완료로 적은 사고의 재발 방지 규칙)

| | 상태 |
|---|---|
| `ChallengeVerdict` — 판정 규칙 순수 객체 (`:domain:model` `domain/challenge/`) | ✅ **존재.** `decide(challengerVerified, opponentVerified)` + `outcomeFor(result, isChallenger)` |
| `ChallengeJudgementService.judge(challengeId)` — `@Transactional`, 판정→인증 FAILED→챌린지 COMPLETED→UserRecord→FriendRecord 를 **한 트랜잭션** | ✅ 존재 (150행) |
| `ChallengeJudgementScheduler` — 00:05 KST cron + `ApplicationReadyEvent` 소급 | ✅ 존재 (`:batch`) |
| `ChallengeStatus` | ✅ `PENDING · ACCEPTED · REJECTED · CONTRACT_SIGNING · IN_PROGRESS · COMPLETED · EXPIRED` |
| `ChallengeResult` | ✅ `CHALLENGER_WIN · OPPONENT_WIN · DRAW · BOTH_LOSE` |
| `Outcome` (내 시점) | ✅ `WIN · LOSE · DRAW · BOTH_LOSE` |
| `challenges` 에 기권 컬럼 | ❌ **없다 — 마이그레이션 1건 필요** |
| `NotificationType` | ✅ 8종 선언. 기권 타입 ❌ **없다** |
| `ResponseCode` | ✅ 🔑 **의미 코드가 아니라 표시 방식 코드다** — `700=SNACKBAR_ERROR`, `701=DIALOG_ERROR`, `702/703=FULL_SCREEN`, `705=ONE_BUTTON_DIALOG` |
| 인증 제출의 `IN_PROGRESS` 게이트 | ✅ 존재 (verification-photo-replace 수용 기준 *"`IN_PROGRESS` 가 아니면 여전히 거부"*) |
| `VerificationParty { CHALLENGER, OPPONENT }` | ⚠️ 존재하나 **`:service` 안**(`VerificationService.kt:499`)이다. `ChallengeVerdict` 는 `:domain:model` 이라 **이걸 못 쓴다** — §1.1 참조 |

### §0.1 🔴 `ChallengeVerdict` 의 KDoc 이 이 feature 의 설계를 이미 규정하고 있다

```
🔴 이 프로젝트에서 판정 규칙이 존재하는 유일한 곳이다.
규칙을 서비스 안 when 절로 흩뿌리면, 나중에 재판정·수동 정정·랭킹 재계산 같은
두 번째 호출부가 생기는 순간 두 벌의 규칙이 갈린다. 배치가 매긴 결과와 화면이
계산한 결과가 다르면 그건 컴파일러도 테스트도 잡아주지 못하는 종류의 버그다.
```

**기권은 정확히 그 "두 번째 호출부"다.** 그래서 이 spec 의 1번 제약은
**기권 판정을 `ChallengeVerdict` 밖에서 계산하지 않는 것**이다.

### §0.2 🔴 `ai-verification` 에 넣지 않고 분리한 이유

사용자 최초 요청은 *"AI 판별 자정 배치에 기권도 추가"* 였다. 분리한 근거:

- **의존이 없다.** 기권은 사진도 AI 도 보지 않는다. `ChallengeVerdict` + 컬럼 1 + 엔드포인트 1 이다
- **무게가 다르다.** `ai-verification` 은 외부 API 키·타임아웃·프롬프트 인젝션 방어·**ADR 작성**이 통째로 붙는다. 묶으면 기권이 그 무게를 같이 진다
- **선례가 있다.** [verification-photo-replace](../verification-photo-replace/summary.md) 가 같은 이유로 `ai-verification` 에서 떨어져 나와 **먼저 개통**됐고 성공했다

⚠️ **착수 순서에 제약이 없다** — AI 보다 먼저 쳐도, 병렬로 가도, 나중에 해도 된다.

---

## §1 범위

### 포함

1. **기권 엔드포인트** 1건 — `POST /challenges/{id}/forfeit`
2. **마이그레이션** — `challenges.forfeited_by` 1컬럼
3. **`ChallengeVerdict.decide` 확장** — 기권을 최우선 규칙으로 (§1.1)
4. **즉시 확정** — 기권 시점에 기존 `judge()` 를 그대로 호출
5. **알림 1종 신설** — `CHALLENGE_FORFEITED`
6. **앱** — 기권 진입점 + 확인 다이얼로그 + 결과 표시

### 🔴 제외 — 명시적으로 안 만든다

- **기권 취소** — `soul-oath` 의 *"무를 수 없는 약속"* 컨셉과 정면 충돌한다. 오조작은 확인 다이얼로그로 막는다
- **`PENDING`(수락 전) 기권** — 이미 **거절**이 그 자리에 있다. 두 개를 두면 둘이 갈린다
- **전적·랭킹에서 기권을 따로 세기** — 🔴 **사용자 결정(2026-09-05): 구분하지 않는다.** 기권자 `losses+1` · 연패 잇기 · 상대 `wins+1`. 마이그레이션·랭킹 정렬·마이페이지 계약 **변경 0**
- **기권 알림의 목록 탭 이동** — 🔴 **사용자 결정(2026-09-05): 이동하지 않는다.** `notification-list` 2차 개정 규칙(*"수락 전 알림만 이동"*)에 **예외를 만들지 않는다**
- **판정 규칙 3종 변경** — 기획 §2.6(양측 인증=무승부 / 한쪽만=그쪽 승 / 양측 미인증=양패)은 한 글자도 안 바뀐다. 기권은 그 **앞에 붙는 별도 규칙**이다

### §1.1 🔴 `ChallengeVerdict` 확장 — 파라미터 1개가 이 설계의 유일한 대가

```kotlin
// :domain:model  domain/challenge/  — ChallengeVerdict.kt 와 같은 파일
enum class Forfeit { CHALLENGER, OPPONENT }

fun decide(
    challengerVerified: Boolean,
    opponentVerified: Boolean,
    forfeit: Forfeit?,                 // ← 신설
): ChallengeResult = when {
    forfeit == Forfeit.CHALLENGER -> ChallengeResult.OPPONENT_WIN    // 인증 여부를 보지 않는다
    forfeit == Forfeit.OPPONENT   -> ChallengeResult.CHALLENGER_WIN
    challengerVerified && opponentVerified -> ChallengeResult.DRAW   // ↓ 기존 3규칙 무변경
    challengerVerified -> ChallengeResult.CHALLENGER_WIN
    opponentVerified -> ChallengeResult.OPPONENT_WIN
    else -> ChallengeResult.BOTH_LOSE
}
```

🔑 **이 파라미터 추가가 *"상대 즉시 승"* 을 고른 대가다.** 기권을 *"미인증으로 친다"* 로 정의했다면
`challengerVerified = false` 하나로 끝나 **시그니처가 안 바뀌었다.** 사용자가 2026-09-05 에
전자를 골랐으므로 대가를 치른다. **다만 대가를 치르는 자리가 규칙이 사는 그 한 곳이라 사본은 안 생긴다.**

🔴 **`VerificationParty` 를 재사용하지 마라.** 그건 `:service` 에 있고 `ChallengeVerdict` 는
`:domain:model` 이다. 도메인이 서비스를 참조하면 의존 방향이 뒤집힌다. **`Forfeit` 을 도메인에 새로 만든다.**

🔑 **`userId` 가 아니라 역할 enum 을 받는 이유**는 KDoc 이 이미 답해 뒀다 —
*"row 부재는 enum 으로 표현할 수 없으므로 **환산 책임을 호출부에 두고** 이 함수는 이미 환산된
값만 본다."* `userId → CHALLENGER/OPPONENT` 환산도 같은 이유로 호출부 몫이다.

---

## §2 사용자 시나리오

1. `IN_PROGRESS` 챌린지 상세에서, **아직 내가 인증을 안 올린 상태**면 기권 진입점이 보인다.
2. 누르면 확인 다이얼로그가 뜬다 — **되돌릴 수 없다는 것**을 명시한다.
3. 확정하면 챌린지가 **즉시 끝난다**. 나는 패, 상대는 승. 전적·연패가 그 자리에서 갱신된다.
4. 상대에게 **푸시가 간다.** 상대가 트레이에서 누르면 챌린지 상세로 간다.
   🔴 **알림 목록에서 누르면 이동하지 않는다** (사용자 결정 — `notification-list` 규칙 그대로).
5. 홈에서 그 챌린지는 진행 중 카드가 아니라 **결과 카드**가 된다 (challenge-result 의 COMPLETED 7일 노출).

---

## §3 수용 기준

- [ ] `IN_PROGRESS` + 당사자 + **내 인증 없음** 셋이 다 참일 때만 기권이 성공한다
- [ ] 🔴 **기권 즉시 `status = COMPLETED` 이고 `result` 가 확정된다** — 자정을 기다리지 않는다
- [ ] 🔴 **결과가 기권자 `LOSE` / 상대 `WIN` 이다** — 상대의 인증 여부와 **무관**함을 두 케이스로 각각 검증:
      상대 인증함 → 상대 `WIN` / **상대도 미인증** → 그래도 상대 `WIN`
      (🔑 뒤쪽이 이 feature 의 핵심 단언이다. 기존 규칙이면 `BOTH_LOSE` 가 나올 자리다)
- [ ] 🔴 **전적이 기권 경로에서도 갱신된다** — 기권자 `losses+1` · `current_loss_streak+1` ·
      `current_streak=0`, 상대 `wins+1` · `current_streak+1` · `current_loss_streak=0`. **숫자로 검증**
- [ ] 🔴 **`FriendRecord` 도 양방향 갱신된다** — 배치 경로와 같은 함수를 탔음의 증거
- [ ] 🔴 **판정 규칙이 `ChallengeVerdict` 밖에 복제되지 않았다** — `ChallengeResult` 를 `when`/`if` 로
      결정하는 코드가 `ChallengeVerdict.kt` 외에 **0곳**임을 grep 으로 검증
- [ ] 이미 인증한 사람은 기권할 수 없다 (거부, `code=700`)
- [ ] `IN_PROGRESS` 가 아니면 기권할 수 없다 — `PENDING` · `COMPLETED` · `EXPIRED` 각각 거부
- [ ] 당사자가 아니면 기권할 수 없다 (거부)
- [ ] 🔴 **양쪽이 동시에 기권 요청을 보내도 한쪽만 성공한다** — 두 번째는 `IN_PROGRESS` 가 아니라 거부.
      **동시 요청으로 검증**하고, `forfeited_by` 가 덮어써지지 않음을 확인
- [ ] 🔴 **기권 후 상대가 인증을 제출하면 거부된다** — 기존 `IN_PROGRESS` 게이트로 막히는지 실제 확인
- [ ] 🔴 **자정 배치가 기권 건을 다시 판정하지 않는다** — `COMPLETED` 라 대상 쿼리에 안 들어옴을 확인.
      배치를 돌려도 전적이 **두 번 오르지 않는다**(숫자 동일)
- [ ] 상대에게 `CHALLENGE_FORFEITED` 알림이 **정확히 1건** 생긴다 (`notifications` row 증가 1)
- [ ] 🔴 **알림 목록에서 기권 알림이 탭되지 않는다** — `referencePending = false` (챌린지가 `COMPLETED`)
- [ ] 앱: `IN_PROGRESS` + 내 인증 없음일 때만 기권 진입점이 보인다. 인증 후에는 **사라진다**
- [ ] 앱: 확인 다이얼로그 없이는 기권이 발생하지 않는다
- [ ] 시간 값은 전부 `yyyy-MM-dd HH:mm:ss` KST (ADR-0010)
- [ ] 백엔드 전체 테스트 회귀 0, 모바일 빌드 성공. 결과는 **숫자로** (CLAUDE.md)

### §3.1 🔵 저절로 닫히는 것들 — 따로 막지 않는다

설계가 이 형태면 방어 코드를 쓸 필요가 없어지는 항목이다.
🔴 **[가정에 방어 로직을 넣지 않는다] 규칙에 따라, 아래에 별도 가드를 추가하지 마라.**

⚠️ **그런데 이 표의 첫 칸이 실제로 틀렸다** — 아래 정정 참조. *"저절로 닫힌다"* 는 주장은 매력적이라서 **검증 없이 쓰기 쉽다.** 이 표를 늘릴 때는 각 칸이 **순차에서만 참인지 동시성에서도 참인지**를 갈라서 확인해라. *"가드를 넣지 마라"* 는 **관측되지 않은 위험**에 대한 규칙이지, 관측된 구조적 결함까지 덮으라는 뜻이 아니다.

| 걱정 | 왜 안 막아도 되나 |
|---|---|
| 양쪽이 다 기권 | 🔴 **이 칸은 틀렸다 (2026-09-05 정정).** 원문은 *"첫 기권이 즉시 `COMPLETED` 로 끝내므로 두 번째는 `IN_PROGRESS` 게이트에 걸린다"* 였는데, 그건 **순차일 때만** 참이다. READ COMMITTED 에서 동시 요청 둘은 **양쪽 다 `IN_PROGRESS` 를 읽고 양쪽 다 통과**한다. backend-dev 가 `@Lock(PESSIMISTIC_WRITE)` 단건 조회(`SELECT … FOR UPDATE`, 기권 전용)로 해결했다 — 🔑 **동시성 전용 규칙을 새로 만들지 않고**, 두 번째 호출자가 `COMPLETED` 가 된 행을 **다시 읽게** 만들어 *기존* 게이트가 거부하게 했다. 내 §3 수용 기준은 처음부터 동시 요청 검증을 요구하고 있었으므로, **이 표와 그 기준이 서로 모순이었다.** |
| 기권 후 상대가 인증 | 인증 제출이 **이미** `IN_PROGRESS` 를 요구한다 (verification-photo-replace) |
| 기권자 사진 삭제 | 기권 조건이 *"인증 전"* 이라 **지울 사진이 존재하지 않는다** |
| 기권 건의 AI 호출(후속 feature) | 즉시 `COMPLETED` → 자정 배치 대상에서 빠짐 → AI 호출 **0회** |

⚠️ 마지막 항목의 부작용: **상대가 올린 사진은 AI 판별을 받지 않는다.** 미션과 무관한 사진이어도
이긴다. 🔑 **이건 의도다** — 그 승리는 인증이 아니라 **기권에서 나온 것**이라 사진을 볼 이유가 없다.
`ai-verification` 착수 시 이 문장을 근거로 삼고, 기권 건을 AI 대상에 넣지 마라.

---

## §4 태스크 분해

### 백엔드 (backend-dev)

**T-B1. `ChallengeVerdict` 확장** — `Forfeit` enum 신설 + `decide` 파라미터 1개 추가.
🔴 **KDoc 도 함께 고친다** — 현재 KDoc 의 판정 표가 4행이고 기권이 없어 **낡은 문장이 된다.**
표 위에 기권 우선 규칙을 넣고, *"`Forfeit` 을 `:service` 의 `VerificationParty` 로 대체하지 마라"* 를 명시.

**T-B2. 마이그레이션** — `challenges` 에 `forfeited_by BIGINT NULL` (user_id) 1컬럼 + `COMMENT ON COLUMN`.

🔴 **`forfeited_at` 을 만들지 마라.** 기권 즉시 `COMPLETED` 가 되므로 **기존 `completed_at` 이 그 시각**이다.
값이 같은 컬럼을 둘 두면 언젠가 갈린다.

**T-B3. 기권 서비스 + 엔드포인트** — `POST /challenges/{id}/forfeit`, 본문 없음.

- 검증 3종(§3) → `forfeited_by` 기록 → **`ChallengeJudgementService.judge(challengeId)` 를 그대로 호출**
- 🔴 **전적 집계 코드를 새로 쓰지 마라.** `judge()` 가 이미 판정·`COMPLETED`·`UserRecord`·`FriendRecord` 를
  한 트랜잭션에 한다. 새로 쓰면 **배치 경로와 갈린다** (§0.1)
- `judge()` 는 `forfeited_by` 를 읽어 `Forfeit` 으로 환산해 `decide` 에 넘긴다 — 배치가 소급 판정할 때도
  같은 코드를 타므로 두 경로가 갈릴 수 없다
- 실패 응답은 `code=700`(스낵바). 🔑 이 프로젝트 코드는 **의미가 아니라 표시 방식**이다(§0)

**T-B4. 알림** — `NotificationType.CHALLENGE_FORFEITED` + `NotificationMessages` 문구.

🔴 **문구 한 줄이 곧 발송 스위치다** — 문구가 `null` 이면 dispatcher 가 건너뛴다(선언 8종 중 4종이
그 상태). 적는 순간 발송된다. 문구 초안은 §6.
🔴 `reference_id` 는 `challengeId`. 앱 딥링크(`PushEventRoute`)에 `Route.Challenge.Detail` 로 배선.

**T-B5. 테스트** — 🔴 결과는 **숫자로**. §3 의 🔴 항목은 전부 테스트로 고정한다.
특히 *"상대도 미인증인데 상대 WIN"* 과 *"배치를 돌려도 전적이 두 번 안 오른다"* 두 건.

### 모바일 (mobile-dev)

> 🔴 코드 편집은 `cd challenge-app && claude -p` child 위임 (`.claude/agents/mobile-dev.md`)

**T-M1. 기권 진입점 + 확인 다이얼로그** — 챌린지 상세(`:feature:challenge:detail`).
노출 조건은 `IN_PROGRESS` **AND 내 인증 없음**. 🔑 이 조건은 **"다시 찍기" 진입점의 정확한 반대**다
(그쪽은 인증 **있을** 때 보인다 — verification-photo-replace T-M1). 둘이 동시에 보이는 일이 없어야 한다.

**T-M2. 결과 표시** — 기권으로 끝난 챌린지임을 상세·결과에서 구분해 보여준다.
**디자인 없음** — 기존 토큰·패턴으로, 디자이너 확인 대상에 등재.

**T-M3. 알림 배선** — `CHALLENGE_FORFEITED` 를 목록 아이콘·색에 추가.
🔴 **탭 이동은 넣지 않는다** (사용자 결정). 트레이 딥링크는 상세로 간다 — **두 경로가 다르다는 것이 의도다.**

**T-M4. 테스트** — 🔴 결과는 **숫자로**.

### 디자인 — 🔴 **팀에서 제외** (T-D1 실측 완료, 2026-09-05 pm-lead)

**T-D1 은 끝났다.** Lovable 정본에 기권 UI 가 **0건**임을 실측했다:
`grep -rniE "기권|포기|forfeit|surrender|give.?up|resign" src/` → 히트 1건뿐이고 그것은
`challenge-detail.tsx:176` 의 **도발 문구** `"포기는 배추 셀 때나"` 로 이 기능과 무관하다.

따라서 **design-bridge 를 팀에 넣지 않는다** — `verification-photo-replace` 와 같은 상황이다
(그때도 인증·카메라 화면이 0건이라 제외했다). 🔴 **T-M1·T-M2 는 기존 토큰·패턴으로 구현하고,
정본 이탈분 전부를 디자이너 확인 목록에 등재한다.**

---

## §5 의존 관계

```
T-B1 → T-B3
T-B2 → T-B3
T-B4 (독립 착수 가능)
T-B3 ─(api-contract confirmed)→ T-M1 · T-M3
T-M2 는 T-M1 이후
T-D1 은 즉시 착수 가능 (실측뿐)
```

🔴 **`api-contract.md` 가 `confirmed` 가 되기 전에 T-M1·T-M3 을 착수하지 마라.**
🔴 **`confirmed` 근거는 파일 본문이다** — pm 의 판정 메시지나 팀 통신이 아니다.

---

## §6 문구 (초안 — 🟡 사용자 확정 필요)

| 자리 | 초안 |
|---|---|
| 확인 다이얼로그 제목 | `정말 기권하시겠어요?` |
| 확인 다이얼로그 본문 | `기권하면 이 챌린지는 바로 끝나고, 상대가 승리합니다. 되돌릴 수 없어요.` |
| 알림 제목 | `계약 파기.` |
| 알림 본문 | `{actorNickname}님이 기권했습니다` |

🔑 **알림 제목이 `계약 파기.` 인 이유**: 기존 4종이 `영혼의 맹세` / `계약 완료.` / `ㅠㅠ` / `증거 도착`
으로 **계약 은유 + 짧은 단정** 톤을 쓴다. 기권은 그 은유에서 계약을 깨는 행위다.

⚠️ **본문에 `{actorNickname}님이` 형태를 쓴 것은 의도다** — 4종 중 `CHALLENGE_REQUEST` 하나만
`님` 이 빠져 `"민수과"` 조사 결함이 나 있고 백로그에 올라 있다. **그 실수를 새 문구에 복제하지 않는다.**

---

## §7 리스크 / 오픈 이슈

- 🔴 **`ChallengeVerdict.decide` 는 호출부가 여럿일 수 있다.** 파라미터를 늘리면 전부 컴파일 에러가
  나므로 **놓칠 수는 없지만**, 기권과 무관한 호출부가 `null` 을 넘기게 된다. 착수 시 호출부를 전수
  확인하고, `null` 이 *"기권 없음"* 을 뜻한다는 것을 KDoc 에 박아라
- 🟡 **기권이 컨셉을 흔든다.** `soul-oath` 는 *"무를 수 없는 약속"* 이 제품의 핵심 차별점이다.
  기권 버튼은 그 반대말이다. 취소 불가 + 확인 다이얼로그로 완화하지만, **컨셉 훼손 자체는 남는다** —
  사용자가 그 비용을 알고 고른 것으로 기록한다(2026-09-05)
- 🟡 **기권 남용을 막는 장치가 없다.** 전적에서 구분하지 않기로 했으므로(§1 제외), 기권을 반복해도
  일반 패배와 똑같이 보인다. 🔵 **지금은 문제가 아니다** — 기권도 패배라 개돼지 랭킹이 이미 센다.
  실사용자 유입 후 재검토 대상
- 🟡 **`ai-verification` spec 이 이 feature 를 아직 모른다.** 착수 확정 시 그쪽 §1 제외 목록에
  *"기권 건은 AI 대상이 아니다"* 를 넣어야 한다 (§3.1 마지막 항목이 근거)
- 🔵 **Lovable 정본 부재 가능성** — T-D1 실측 결과에 따라 디자이너 확인 항목이 늘어난다
