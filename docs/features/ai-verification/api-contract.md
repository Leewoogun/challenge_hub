# ai-verification — API 계약

- **상태**: ✅ **`confirmed`** (2026-09-22, backend-dev) — 미결 2건 확정, 협의 종료
- **소유자**: **backend-dev** — 확정·개정 권한은 backend-dev 에게 있다. 🔵 pm 초안은 *협의의 출발점*이지 결정이 아니다
- **협의**: backend-dev ↔ mobile-dev (`aiverify-backend` ↔ `aiverify-mobile`, 2026-09-22 종료)
- **정본**: 🔴 **[challenge-verification/api-contract.md](../challenge-verification/api-contract.md) §4·§4.1 이다.**
  이 문서는 그 개정의 **근거와 경위**만 보관한다 — 값을 여기서 읽지 마라 (§1 참조)
- **관련**: [ADR-0013](../../decisions/0013-ai-verification-provider.md) · [spec.md](./spec.md) §5 · [plan.md](./plan.md) Task 7·9

---

## §0 이 feature 의 계약 표면은 **얇다**

**새 엔드포인트 0개. 새 마이그레이션은 있으나(판정 로그 4컬럼) 앱에 보이는 것은 아니다.**
앱이 보는 변화는 **기존 `confirmed` 계약에 필드 1개가 붙는 것**뿐이다.

🔴 **그러므로 이 문서는 [challenge-verification/api-contract.md](../challenge-verification/api-contract.md)
의 개정 제안서다.** 확정되면 **그쪽 계약 본문을 고치고 그쪽 `change-log.md` 에 등재**한다 —
이 파일에 사본을 남기지 마라. 값이 두 곳에 살면 언젠가 갈린다.

---

## §1 ✅ **이관 완료** — 정본은 challenge-verification 계약이다

**2026-09-22 개정 완료.** `aiReason` 의 shape · nullable · 게이트 조건 · 필드 표는 전부
**[challenge-verification/api-contract.md](../challenge-verification/api-contract.md) §4 본문과
§4.1** 로 옮겼고, 같은 feature 의 [change-log.md](../challenge-verification/change-log.md) 에
**2건**으로 등재했다(`aiReason` 추가 / `photoDeleted` 누락 보정 — 섞지 않았다).

🔴 **여기에 사본을 남기지 않는다.** 값이 두 곳에 살면 언젠가 갈린다. 아래 §1.1~§3 은
**그 개정에 이른 경위와 근거**이고, *"지금 wire 가 어떤 모양인가"* 의 답은 **정본에만 있다.**

🔵 함께 정정한 것: 그쪽 §4 의 **낡은 문장 4건**(`status` 로 사진 유무를 역산하던 서술)과
**`photoDeleted` 누락**(2026-08-26 부터 실재했는데 표·예시에 없었다).

---

## ✅ §1.1 확정 — **wire 게이트는 계약이다** (컬럼을 그대로 내리지 마라)

```
wire 의 aiReason 은 verdict.rejectsVerification() 이 참일 때에만 non-null 이다.
그 외 (PASS / UNCERTAIN / UNVERIFIABLE / ERROR) 는 컬럼에 값이 있어도 wire 는 null.
```

🔑 **컬럼과 wire 는 다른 것이다.** `ai_reason` **컬럼**은 rubric 튜닝 근거라 **전건 저장이
설계대로**다(spec T-B2). **wire 는 사용자 화면**이라 미인증 확정 건만 실어야 한다.

### ✅ **해소됨 (2026-09-22, backend-dev 구현)** — 아래는 적발 당시의 실측 기록이다

> 🔴 **이 절의 *"게이트가 없다"* 는 더 이상 참이 아니다.** `VerificationService.view()` 에
> `aiReason = verification?.takeIf { it.rejectedByAi() }?.aiReason` 로 구현됐고,
> 판정은 `Verification.rejectedByAi()` **한 곳**에서 `MissionVerdict.rejectsVerification()` 에
> **위임**한다(조건식 사본 0). `VerificationServiceTest` **6건**이 각 `ai_verdict` 의 비노출을
> 단언한다. 아래 표는 **적발 당시 기록**이며 되돌림 방지용으로 남긴다.

#### (적발 당시) 게이트가 코드에 **없었다** — `aiverify-mobile` 적발, pm 독립 확인

| # | 위치 | 상태 |
|---|---|---|
| 1 | `MissionVerdictRecorder.kt:57` `status = if (verdict.rejectsVerification())` | ✅ 게이트 **있음** |
| 2 | 같은 `copy()` 4줄 아래 `:64` `aiReason = verdict.reason` | ✅ **이게 맞다** — 컬럼은 전건 저장이 설계 |
| 3 | 🔴 **`VerificationService.kt:336` `aiReason = verification?.aiReason`** | 🔴 **조건 0개 — 여기가 결함이다** |

**고칠 곳은 3번 하나다.** 도메인에 `MissionVerdict.rejectsVerification()` 이 이미 **한 곳으로**
존재하므로(KDoc: *"미인증 처리는 rejectsVerification 한 곳에서만 판단한다"*) **조건식을
`view()` 에 새로 적지 말고 그 헬퍼를 불러라** — 새로 적으면 판정 규칙의 사본이 생긴다.

### 이 게이트가 없을 때 실제로 나가는 것

| `ai_verdict` | 게이트 없으면 사용자가 보는 것 |
|---|---|
| `PASS` | 🔴 **이겼는데** *"인정되지 않았어요: {통과 사유}"* |
| `UNVERIFIABLE` | *"인정되지 않았어요: AI 검증이 비활성 상태입니다 (API 키 미설정)"* — **무키 상태에서 제출 전건** |
| 🔴 `ERROR` | *"인정되지 않았어요: 검증 중 예외: {e.message}"* — **예외 메시지가 사용자 화면에** (`MissionVerificationRunner.kt:115`) |
| `UNCERTAIN` | 통과인데 부정적 문구 |
| `REJECT` + conf ≥ 0.80 | ✅ **이것만 나가야 한다** |

### 🔴 KDoc 이 없는 계약을 있다고 적고 있다 — 이 프로젝트 7번째다

`NoOpMissionVerifier.kt:36` KDoc (실측 인용):

> *"이 문자열은 `ai_reason` 컬럼에 저장되지만 **사용자에게는 보이지 않는다** — 통과한 건의
> `aiReason` 은 wire 에 내려가지 않기 때문이다(계약)."*

**그 계약은 코드 어디에도 없다.** 컴파일되고 테스트도 초록이라 **조용하다** — 다음 사람이 이 줄을
읽고 *"게이트 있구나"* 하고 넘어간다. 🔵 **다만 backend 가 게이트를 의도했다는 증거**이기도 하므로
**설계 이견이 아니라 누락 1건**이다.

⚠️ challenge-forfeit 이 *"문서가 코드보다 앞서 있는데 아무도 몰랐다"* 를 **6건** 수확했다.
이번이 **7번째**이고, 앞의 6건과 달리 **사용자 화면에 직접 새는 건**이다.

### ✅ 테스트로 고정했다 — 🔴 **단 요청받은 위치가 아니다 (의도된 이탈)**

요청은 *"`WireShapeContractTest` 에 추가하라"* 였으나 **`VerificationServiceTest` 에 넣었다.**

🔴 **`WireShapeContractTest` 에서는 이 단언이 성립하지 않는다.** 그 테스트는 `PartyVerificationDto`
를 **손으로 만들어** 직렬화 결과를 보는데, 게이트는 그 **위 계층**(`view()` 가 `Verification` row →
`PartyVerificationView`)에 있다. 즉 거기서 `aiReason = null` 인 DTO 를 만들어 *"null 이 나온다"* 를
단언하면 **Jackson 이 null 을 직렬화한다는 것만 증명**하고 게이트가 사라져도 **초록으로 남는다.**
그건 있으나 마나 한 테스트이고, 오히려 *"잠갔다"* 는 착각을 만들어 더 나쁘다.

**실제로 넣은 것** (`VerificationServiceTest`, 6건 — `Verification` row 를 심고 `view()` 를 통과시킨다):

| 심은 `ai_verdict` | 단언 |
|---|---|
| `PASS` + 사유 | wire `aiReason == null` |
| `UNVERIFIABLE` + *"AI 검증이 비활성 상태입니다…"* | 〃 |
| `ERROR` + *"검증 중 예외: …"* | 〃 |
| `UNCERTAIN` + 사유 | 〃 |
| `REJECT` + **conf 0.79** | 〃 — 🔑 게이트를 `outcome == REJECT` 만으로 쓴 구현과 갈라 준다 |
| `REJECT` + conf 0.93 | wire `aiReason` **non-null** (게이트가 전부 막지 않았음) |

⚠️ `WireShapeContractTest` 의 기존 `PENDING` 케이스에는 **`"aiReason":null` 이 원문에 남는지**를
추가했다 — 그건 그 테스트가 할 수 있는 일(키 보존)이고 게이트와는 별개 명제다.

---

🔵 **`aiVerdict` / `aiConfidence` 는 내리지 않는다.** 앱이 쓸 데가 없고, **신뢰도 숫자를 노출하면
사용자가 그 값을 두고 다툰다.** 서버 컬럼으로만 남긴다(rubric 튜닝 근거 — spec T-B2).

---

## ✅ §2 확정 — **A 안: 반려된 인증은 `status = FAILED` 로 전이한다**

**이 feature 의 유일한 실질 계약 쟁점이다.** 앱이 *"반려됐다"* 를 아는 경로가 여기서 갈린다.

| 안 | 내용 | 걸리는 것 |
|---|---|---|
| **A. `status` 를 `FAILED` 로 전이** | 판정 시 row 의 status 자체를 바꾼다 | 앱이 기존 `status` 분기만으로 읽는다. 🔴 단 **`FAILED` 를 소비하는 기존 앱 코드의 의미가 바뀐다** — 현재 `FAILED` 는 *"미제출로 마감"* 이다 |
| **B. `status` 는 `VERIFIED` 유지 + `aiReason` non-null 로 판별** | 사진은 냈고 AI 가 안 쳐줬다는 사실을 분리 | 🔴 **앱이 "`aiReason` 이 있으면 반려" 라는 규칙의 사본을 갖는다** — ADR-0013 §근거 2 가 경계한 그 형태 |
| **C. 별도 필드** (`aiRejected: Boolean`) | 명시적 | 🔴 **절대값이 아니라 파생 불리언**이다. ADR-0012 §근거 3 이 기각한 형태 |

> ✅ **확정 (2026-09-22, backend-dev). A 안이다.** `aiverify-mobile` 이 앱 소비처 전수 grep 으로
> A 를 권고하고, pm-lead 가 지지 의견을 냈으며, backend-dev 가 서버측 실측 후 확정했다.
>
> 🔑 **결정적 근거는 B 안의 치명상이다** — `VerificationStatusPill` 이 `status` 만 보므로 B 면
> 같은 카드에 초록 *"인증완료"* 뱃지와 *"인정되지 않았습니다"* 가 **동시에** 뜬다. 막으려면 앱이
> *"`aiReason` 이 있으면 뱃지를 실패로 바꾼다"* 를 갖게 되고 **그게 ADR-0013 §근거 2 가 경계한
> 규칙의 사본**이다. C 는 ADR-0012 §근거 3(파생 불리언) 기각 형태라 검토에서 제외했다.
>
> 아래 표와 §의 *"A 안에서 깨지는 것"* 들은 **전부 이행됐다** — 서버 3곳 수정 + 순서 테스트 1건
> (앱 3곳은 mobile-dev T-M2).

🔑 **pm 관점(당시, 결정 아님)**: A 가 ADR-0013 §근거 2 와 가장 정합해 보인다 — 판정 결과가 **서버가
확정한 상태 하나**로 표현되고 앱은 그걸 그릴 뿐이다. 다만 **`FAILED` 의미 확장이 기존 소비처를
건드리므로 mobile-dev 실측이 필요하다.**

> 🔴 **초안 정정 (2026-09-22, `aiverify-mobile` 실측).** 이 자리에 *"A 안이면
> `MissionCardMineFailedPreview` 가 되살아난다"* 고 적었는데 **틀렸다.** 그 Preview 는
> `FAILED` + **"다시 인증하기" CTA** 를 그리는데, 판정 시점이 **자정 = 마감**이라 재시도 창이
> 구조적으로 존재하지 않고 `myMissionSlot` 이 `FAILED` 에서 CTA 를 낼 수 없다.
> **어느 안이든 죽은 화면이고, 백로그 판단(*"현재 코드가 옳고 Preview 가 낡았다"*)이 맞다.**
> A 안이 실제로 만드는 화면(`FAILED` + 사진 + 사유)에 맞춰 이번에 고쳐 닫는다.

🔴 **A 안의 실제 비용은 Preview 가 아니라 "FAILED 면 사진이 없다" 는 암묵 전제다**
(`aiverify-mobile` 전수 grep):

| # | 위치 | 현재 동작 | A 안에서 깨지는 것 |
|---|---|---|---|
| 1 | `core/ui/.../VerificationStatusPill.kt:83` | error 색 + Cancel + "실패" | 라벨 의미만 확장 (감당 가능) |
| 2 | `feature/challenge/detail/.../VerificationPhoto.kt:84` | "인증하지 못했어요" | 🔴 이 분기가 `photoUrl` 분기보다 **먼저** 걸려 **사진을 안 그린다** |
| 3 | `.../contract/ChallengeDetailState.kt:155` | `myMissionSlot = NONE` | 🔴 **내 카드 하단 슬롯 통째 제거 — 사유를 그릴 자리가 없다** |

🔑 즉 A 안을 그냥 켜면 **사용자가 올린 사진이 사라지고 반려 사유를 띄울 자리조차 없다.**

### 🔴 그리고 서버에도 같은 함정이 3곳 있다 (2026-09-22 pm 실측)

**앱만 고치면 안 된다.** `service/.../verification/VerificationService.kt` 가 `VERIFIED` 를
**사진의 존재 조건**으로 쓴다:

> ✅ **서버 3곳 수정 완료 (2026-09-22).** 판정을 `status` → **사진 key 유무**로 옮겼고,
> `photoDeleted` 는 `verifiedAt != null && key == null && owner DELETED` 로 바꿨다
> (*"이 사람이 사진을 낸 적이 있는가"* 가 필요한 명제이고, `verifiedAt` 은 제출만이 쓴다).
> ⚠️ **기존 데이터에서는 세 조건 모두 동작이 완전히 동일하다** — 새로 생기는 조합만 갈린다.
> `VerificationServiceTest` 4건으로 고정했다.

| 행 | 코드 (수정 전) | A 안에서 깨졌을 것 |
|---|---|---|
| `:260` | `if (status != VERIFIED) return PhotoReadResult.NotFound` | 🔴 **반려 건 사진이 404** |
| `:301` | `hasPhoto = status == VERIFIED && key != null` | 🔴 **`photoUrl` 이 null 로 내려간다** |
| `:307` | `photoDeleted = status == VERIFIED && …` | 탈퇴 표시가 반려 건에서 사라진다 |

⚠️ **앱을 고쳐도 서버가 `photoUrl: null` 을 주면 *"사진을 불러오지 못했어요"* 가 뜬다.**
`hasPhoto` 의 조건을 **`status` 가 아니라 photo key 유무**로 옮겨야 한다.

🔑 **양쪽이 각자 계층에서 같은 함정을 독립 발견했다** — verification-photo-replace 의 Coil 캐시
건과 같은 모양이다. *"`VERIFIED` = 사진이 있다"* 라는 등식이 두 레포에 퍼져 있었고,
**A 안은 그 등식을 깬다**(사진이 있는데 `FAILED`).

### 🔴 순서 제약 — 판정보다 **먼저** 반려가 찍혀야 한다

`ChallengeJudgementService.kt:91-92` 가 승패를 이렇게 읽는다:

```kotlin
val challengerVerified = verifications[challenge.challengerId]?.status == VERIFIED
val opponentVerified   = verifications[challenge.opponentId]?.status == VERIFIED
```

🔵 **A 안이 이 코드와 정합하는 이유가 여기 있다** — AI 반려를 `FAILED` 로 찍으면
**판정 로직을 한 줄도 안 고치고** 그 인증이 승패 계산에서 빠진다(ADR-0013 §결정 2:
*"AI 는 승패를 결정하지 않는다"* 가 코드 수준에서 성립). B·C 안이면 이 두 줄에
`aiReason`/`aiRejected` 조건을 더해야 하고 **그게 판정 규칙의 사본이다.**

🔴 **단 순서가 전제다.** AI 검증 단계가 `judge()` 가 위 두 줄을 읽기 **전에** 완료돼야 한다.
spec T-B4 의 *"판정 배치 **앞단**"* 이 이 제약이다 — 순서가 뒤집히면 **반려가 판정에 반영되지
않고 그 사실이 조용하다**(예외도 로그도 없이 그냥 옛 규칙대로 이긴다).
> ✅ **고정했다 (2026-09-22).** `ChallengeJudgementRunnerTest` 의
> *"AI 가 양측을 반려하면 판정이 BOTH_LOSE 다 — 검증이 판정보다 먼저 돈다"*.
>
> 🔑 **순서를 직접 관찰하지 않고 결과로 가른다** — 양측 제출 + 양측 반려면 순서가 맞으면
> `BOTH_LOSE`, 뒤집히면 `DRAW` 다. **두 기대값이 갈라지므로 순서가 실제로 검증된다**
> (ADR-0012 §차등 검증과 같은 원리). 🔴 **테스트에 이가 있는지도 확인했다** — 구현의 검증
> 호출을 판정 루프 **뒤로 일부러 옮겨** 그 테스트 1건만 빨개지는 것을 보고 되돌렸다.
> 대조군(*"AI 반려가 없으면 DRAW"*)도 함께 넣었다.

**이것이 A 안의 실제 비용이다 — 앱 3곳 + 서버 3곳 + 순서 테스트 1건.**

### ✅ 감사 완결성 — 서버에 **숨은 게이트는 없다** (2026-09-22 pm 실측)

`aiverify-mobile` 이 앱에서 *"`grep "== VERIFIED"` 로는 **소거 형태**가 안 잡힌다"* 를 발견했다
(`VerificationPhoto.kt:84` 가 `VERIFIED` 를 **묻지 않고** `PENDING`·`FAILED` 를 먼저 걸러낸 뒤
남은 것을 사진으로 본다). **서버에 같은 형태가 있는지는 아무도 안 봤으므로** 내가 확인했다.

`VerificationStatus.PENDING|FAILED` 를 서버 프로덕션 전수 grep → **사진 게이트로 쓰인 곳 0건**
(전부 기본값 대입이거나 판정 전이다). 즉 **서버의 사진 게이트 3곳은 모두 `VERIFIED` 를 명시**하며
backend 의 감사 범위가 **완전하다.**

### 🔵 `FAILED` 를 쓰는 주체가 둘이 된다 — 그런데 겹치지 않는다

| 쓰는 곳 | 대상 | 의미 |
|---|---|---|
| **AI 검증 단계** (신규) | `VERIFIED` → `FAILED` | 사진은 냈는데 **미션 증거로 인정 안 됨** |
| `ChallengeJudgementService.kt:105-106` (기존) | `PENDING` → `FAILED` | **마감까지 미제출** |

✅ **대상 집합이 서로소라 경합하지 않는다.** 그리고 재실행에서도 안전하다 — 반려된 row 는
`FAILED` 가 되어 *"`VERIFIED` row 를 모은다"* 는 AI 단계 대상 쿼리에 **다시 안 걸린다**(멱등
가드가 `ai_checked_at` 과 **두 겹**). ⚠️ **AI 단계의 대상은 반드시 `VERIFIED` row 여야 한다** —
*"`FAILED` 를 재검증"* 으로 넓히면 이 두 겹이 동시에 무너진다.

🔑 **`FAILED` 의 의미가 둘로 늘어나는 것은 맞다.** 다만 앱이 구분할 필요가 없다 —
`aiReason` 유무가 *(표시용으로)* 갈라 주고, **판정은 둘 다 "미인증" 으로 같게 대한다.**
이것이 §2 표의 A 안 항목이 *"`FAILED` 의미 확장"* 을 감당 가능한 비용으로 본 이유다.

🔵 **서버측 전제는 실측 확인됨** — `ChallengeJudgementService.kt:104-107` 이 `PENDING` 인 row 만
`FAILED` 로 전이시키고 `VERIFIED` 는 건드리지 않는다. 즉 *"현재 `FAILED` = 미제출로 마감"* 이 맞다.

## ✅ §3 확정 — **앱은 `aiReason: null` 의 세 의미를 구분하지 않는다**

```
null = ⓐ AI 가 통과시켰다
     = ⓑ AI 를 아예 안 불렀다 (fail-open — 키 없음/429/타임아웃/파싱실패)
     = ⓒ 미제출이라 판정 대상이 아니었다
```

⚠️ **앱이 셋을 구분해야 하는가?** pm 판단으로는 **구분할 필요가 없다** — 셋 다 화면에 *"반려
사유 없음"* = 아무것도 안 그린다로 귀결된다.

🔴 **그러나 운영에서는 ⓑ 를 반드시 구분해야 한다**(ADR-0013 §결정 4 대가 — 선불 잔액이 마르면
fail-open 이 조용히 켜진다). **그 구분은 wire 가 아니라 서버 배치 요약이 진다.**
*"앱에 안 보인다"* 와 *"아무도 모른다"* 는 다르다 — 이 줄을 근거로 배치 로깅을 빼지 마라.

---

## §4 확정 시 해야 할 일 (backend-dev)

1. [challenge-verification/api-contract.md](../challenge-verification/api-contract.md) **본문 개정** — `confirmed` 계약이다
2. 같은 feature 의 `change-log.md` **등재 필수**
3. 이 파일 상태를 `confirmed` 로 전환하고 **§1 을 "그쪽으로 이관됨" 으로 축약** (사본 방지)
4. 🔴 **`WireShapeContractTest` 에 `aiReason` 행 추가** — 이 프로젝트는 wire shape 을 테스트로 고정한다

## §5 이 feature 가 **건드리지 않는 것**

- **기권 건** — `COMPLETED` 라 배치 대상에서 빠진다. AI 호출 0회, `aiReason` 항상 `null`
  (근거: [challenge-forfeit/spec.md](../challenge-forfeit/spec.md) §3.1)
- **재제출 / 재촬영 UI** — ✅ 이미 개통됨 (verification-photo-replace, 2026-09-02)
- **승패 판정 규칙** — `ChallengeVerdict` 무변경. AI 는 인증 1건의 pass/fail 만 낸다 (ADR-0013 §결정 2)
- **페이지네이션** — 인증은 챌린지당 2건이다. 커서 없음 (ADR-0012 §적용 범위)
