# Mobile Report — ai-verification

- **담당**: mobile-dev (`aiverify-mobile`)
- **범위**: spec §4 **T-M2**(반려 사유 표시) · **T-M3**(테스트) = plan **Task 9 Step 1**
- **작성**: 2026-09-22
- **선행 계약**: [challenge-verification/api-contract.md](../challenge-verification/api-contract.md) §4·§4.1 (`confirmed`, PM 허브 커밋 `54c4bec`)

> 🔴 **plan Task 8(재촬영·교체 UI)은 실행하지 않았다** — 폐기된 태스크다(verification-photo-replace 가 2026-09-02 에 개통, app `2a650ba`).
>
> 🔵 **plan Task 9 Step 2(재제출 전 선행 조회 제거)도 실행할 것이 없었다 — 이미 끝나 있다.**
> `feature/challenge/verify/.../VerifyViewModel.kt` 의 `submit()` 이 선행 조회 없이 곧바로
> `verificationRepository.submitVerification` 을 부른다(실측). verification-photo-replace 가
> 소유권을 가져간 몫이고, plan 머리 배너도 그렇게 적고 있다.

---

## 구현 요약

앱이 보는 변화는 **필드 1개**(`aiReason`)지만, 실제 작업의 대부분은 그게 아니었다.

🔴 **A안(반려 → `status = FAILED`) 이 이 프로젝트에 처음으로 `status == FAILED` 인데 사진이 있는 row 를 만든다.** 지금까지 `FAILED` 는 100% *"마감까지 미제출"* 이었고 `photoUrl` 이 항상 null 이었다. 앱 코드 세 곳이 그 낡은 전제를 굳혀 두고 있었고, 그대로 두면 **사용자가 올린 사진이 화면에서 사라진 채 "인증하지 못했어요" 만 뜬다** — 사진을 냈는데 "못 했다" 고 하면서 그 사진을 감추는, 두 번 거짓말하는 화면이다.

그래서 작업은 두 덩이였다:
1. **`aiReason` 배관 + 렌더링** — 계약이 요구하는 규칙은 한 줄(*"non-null 이면 그린다"*)
2. 🔴 **`FAILED` 게이트 3곳 해제** — 이쪽이 더 컸다

### §2 계약 미결 2건 — 실측으로 A안을 권고하고 확정에 도달

`api-contract.md` 가 `draft` 인 상태로 시작해 backend-dev(`aiverify-backend`)와 SendMessage 로 협의했다.

**§2 반려된 인증의 `status`** → **A안 확정** (양쪽이 독립적으로 같은 결론).

`FAILED` 소비처를 전수 grep 해 근거를 댔다:

| # | 위치 | 현재 동작 | A안에서 |
|---|---|---|---|
| 1 | `core/ui/.../VerificationStatusPill.kt:83` | error 색 + `Icons.Filled.Cancel` + "실패" | 🔵 **변경 없음** — 라벨이 미제출·반려 둘 다에 참 |
| 2 | `feature/challenge/detail/.../component/VerificationPhoto.kt:84` | `status == FAILED` → "인증하지 못했어요" | 🔴 이 분기가 `photoUrl` 분기보다 **먼저** 걸려 **사진을 안 그린다** |
| 3 | `.../contract/ChallengeDetailState.kt:155` | `FAILED` → `MyMissionSlot.NONE` | 🔴 **내 카드 하단 슬롯 통째 제거 — 사유를 그릴 자리조차 없다** |

🔴 **B안을 기각한 근거가 화면에 있었다.** B안(`VERIFIED` 유지 + `aiReason` 으로 판별)은 **같은 카드 안에 초록 "인증완료" 뱃지와 "인증이 인정되지 않았어요" 를 동시에 띄운다** — `VerificationStatusPill` 이 `status` 만 보기 때문이다. 막으려면 앱이 *"`aiReason` 있으면 뱃지를 실패로 바꾼다"* 를 해야 하고, 그게 [ADR-0013](../../decisions/0013-ai-verification-provider.md) §근거 2 가 경계한 **규칙의 사본** 그 자체다. C안(파생 불리언)은 [ADR-0012](../../decisions/0012-list-pagination-cursor.md) §근거 3 기각 형태라 검토에서 제외했다.

A안이면 `FAILED` 의 의미가 둘로 늘어나는 게 아니라 ***"이 인증은 인정되지 않았다"* 하나로 통일**된다 — 서버 `ChallengeVerdict` KDoc 의 *"`VERIFIED` 가 아닌 모든 것이 미인증"* 과 정합한다.

**§3 `aiReason: null` 의 세 의미** → **앱은 구분하지 않는다.** `null` 에서 어떤 결론도 파생하지 않는다.

### 🔴 협의 중 적발 — wire 게이트가 서버 코드에 없었다

`aiReason` 이 확정된 뒤, **backend 의 "필드 넣었으니 시작해도 된다" 를 메시지로 받아들이지 않고 서버 코드를 직접 읽어** 구멍을 찾았다. 세 줄이 이어져 있었다:

1. `MissionVerdictRecorder.kt:64` — `aiReason = verdict.reason` 을 **판정 종류를 안 가리고** 저장 (설계대로다 — 컬럼은 rubric 튜닝 근거)
2. 🔴 `VerificationService.kt:336` — `aiReason = verification?.aiReason`, **조건 0개로 wire 통과**
3. `NoOpMissionVerifier` 가 `unverifiable("AI 검증이 비활성 상태입니다 (API 키 미설정)")` 를 돌려주고 `MissionVerificationRunner` 가 **그것도 기록**

→ 무키 상태에서 배치가 한 번 돌면 제출 전건의 `ai_reason` 이 저 문자열이 되고, 합의된 앱 규칙대로 그리면 **이긴 사람 화면에** *"인증이 인정되지 않았어요: AI 검증이 비활성 상태입니다 (API 키 미설정)"* 가 뜬다. `ERROR` verdict 는 `"검증 중 예외: ${e.message}"` 라 **예외 메시지가 사용자 화면에** 간다.

🔴 **더 나쁜 것은 `NoOpMissionVerifier.kt:36` KDoc 이 *"통과한 건의 `aiReason` 은 wire 에 내려가지 않기 때문이다(계약)"* 라고 없는 계약을 있다고 단정하고 있었다는 점이다.** 컴파일도 테스트도 초록이라 조용했다. 🔵 동시에 backend 가 게이트를 **의도했다는 증거**이기도 해서 설계 이견이 아니라 누락 1건이었다.

backend 가 `Verification.rejectedByAi()` 를 두고 `MissionVerdict.rejectsVerification()` 에 위임하는 형태로 닫았고(조건식 사본 없음), 계약 §4.1 에 조항으로 박혔다:

```
wire 의 aiReason 이 non-null  ⟺  그 인증이 AI 판별로 미인증 처리됐다
```

🔑 **이 조항이 없으면 A안 안에서 B안의 사본이 되살아난다** — 서버가 언제 사유를 싣는지 계약이 말해주지 않으면 앱이 `status` 와 `aiReason` 을 **둘 다** 봐야 한다. 조항 덕에 앱 규칙이 한 줄로 끝났다.

### 계약 초안 오류 2건 적발 (pm 이 정정)

- **§1 예시 JSON 이 `data.verifications[]` 배열**이었다. 실재 shape 은 `data.challengeId` + `data.challenger{}` / `data.opponent{}` 다 (confirmed 계약 L548~572, 앱 `ChallengeVerificationsData` 일치). 🔴 **그 예시가 그대로 본문으로 이관됐으면 `confirmed` 계약에 거짓 shape 이 들어갔다.**
- 실재 필드 **`photoDeleted` 누락** — 부수로 **기존 계약의 구멍**이 드러났다(mypage 가 필드를 추가하고 challenge-verification 본문 예시를 안 고쳤다). backend 가 별도 change-log 항목으로 갈라 등재했다.
- **§2 의 *"A안이면 `MissionCardMineFailedPreview` 가 되살아난다"* 도 틀렸다** — 아래 참조.

---

## 사용한 모바일 레포 스킬

코드 편집은 전부 `cd challenge-app && claude -p` **child claude 위임**으로 했다(cwd 가 PM 허브라 SessionStart 훅 · skill 자동 발견 · 누적 메모리가 본체에서는 발화하지 않는다).

- **`modify-feature`**: 1차 참조. 기존 기능에 필드 1개 추가 + 기존 분기 수정이라는 형태가 이 스킬의 대상이다
- **`feature`**: 컴포넌트 배치 규칙 — 반려 사유 composable 을 `:core:designsystem` 이 아니라 `:feature:challenge:detail` 의 `component/` 에 뒀다(`:core:designsystem` 은 도메인 무관 프리미티브만)
- **`viewmodel`**: State 파이프라인 규칙 — **Composable 에서 문자열 포맷팅 금지**를 지켜 접두어 결합을 State 파생(`myAiReasonText`)에서 끝냈다

---

## 변경된 파일

challenge-app, **12 파일 수정 + 1 신규**, `+536 / -35`.

### 배관 — `aiReason: String?` (remote DTO → 도메인 → 매퍼 → State)

| 파일 | 변경 |
|---|---|
| `remote/model/.../verification/ChallengeVerificationsResponse.kt` | `PartyVerificationDto.aiReason: String? = null` |
| `domain/model/.../verification/ChallengeVerifications.kt` | `PartyVerification.aiReason: String?` |
| `remote/mapper/.../VerificationMappers.kt` | 통과 |
| `feature/challenge/detail/.../contract/ChallengeDetailState.kt` | `VerificationSection.myAiReason` / `opponentAiReason` + `Data` 파생 |
| `feature/challenge/detail/.../ChallengeDetailViewModel.kt` | `toVerificationSection()` 에서 양측 채움 |

🔴 **DTO 기본값 `= null` 이 필수다** — kotlinx.serialization 에서 기본값이 없으면 키 누락이 곧 `MissingFieldException` 이고 **인증 현황 조회가 통째로 죽는다**. `photoDeleted` 가 같은 KDoc 으로 이미 경고하고 있던 함정이다.

### 🔴 `FAILED` 게이트 해제 — "FAILED 면 사진이 없다" 전제 제거

**`VerificationPhoto.kt` — `when` 체인 재배열**

```
isLoading                              -> 불러오는 중...
status == null                          -> 인증 현황을 불러오지 못했어요 (재시도)
status == PENDING                       -> 아직 인증하지 않았어요
photoDeleted                            -> 탈퇴한 사용자의 사진은 삭제됐어요      ← FAILED 위로 올라갔다
status == FAILED && photoUrl == null    -> 인증하지 못했어요                      ← 조건이 붙었다
photoUrl == null                        -> 사진을 불러오지 못했어요
else                                    -> RemotePhoto(photoUrl)                 ← 반려 건이 여기 도달
```

- `photoDeleted` 를 올린 이유: 탈퇴는 `status` 와 무관한 사실이고, 서버의 새 판정식(`verifiedAt != null && key 없음 && owner DELETED`)이 **반려 후 탈퇴** 조합에서 참이 된다. 그 칸에서 할 말은 *"인증하지 못했어요"* 가 아니라 사진이 지워졌다는 사실이다. 🔵 **미제출 건은 `verifiedAt` 이 null 이라 `photoDeleted` 가 false** — 이 재배열이 미제출 경로를 건드리지 않는 근거다.
- 🔵 **`status == VERIFIED` 를 긍정 조건으로 세우지 않았다.** 이 체인은 *"무엇이 없는지"* 를 차례로 걷어내는 소거형이고, `VERIFIED` 를 문턱으로 세우는 순간 반려 `FAILED` 가 다시 사진을 잃는다.
- 🔵 **기존 데이터에서 동작 변화 0** — 여태 `FAILED` 는 `photoUrl == null` 뿐이라 그 경로는 지금도 같은 분기에서 끝난다.

**`ChallengeDetailState.kt` — `myMissionSlot`**

`FAILED -> NONE` → `FAILED -> if (myPhotoUrl != null) MY_PHOTO else NONE`.

`MY_PHOTO_WITH_RETAKE` 가 아닌 이유: 반려는 자정 판정이 내리는 결론이고 그 시점이 곧 마감이라, `FAILED` 를 보는 순간 챌린지는 이미 `COMPLETED` 이고 `canVerify` 가 false 다. **다시 찍을 창이 구조적으로 존재하지 않는다.**

🔵 **`canForfeit` 은 손대지 않았다.** `myMissionSlot == VERIFY_CTA` 파생이고 `FAILED` 는 그 가지로 가지 않아 값이 그대로다. 그 파생 KDoc 이 *"조건식을 새로 적으면 같은 규칙이 두 벌이 된다"* 고 경계하고 있어 새 조건을 넣지 않았다.

**`VerificationStatus.kt`** — 코드 변경 없이 `FAILED` KDoc 을 확장했다. 두 사건(미제출 / AI 반려)을 한 값으로 두는 이유(결과가 같다)와 **사진 유무가 둘을 가른다**는 것, 그리고 *"이 상태만 보고 사진이 없다고 단정하면 반려 건에서 사용자가 올린 사진을 지운다"* 를 남겼다.

### 반려 사유 렌더링

**신규** `feature/challenge/detail/.../component/RejectionReasonText.kt`

- 문구: **`"인증이 인정되지 않았어요: {aiReason}"`**
  🔵 spec 원문은 합쇼체(*"인정되지 않았습니다"*)인데 **해요체로 낮췄다** — 이 화면의 사용자 노출 문구가 전부 해요체라(*"아직 인증하지 않았어요"* · *"인증하지 못했어요"* · *"사진을 불러오지 못했어요"* · *"탈퇴한 사용자의 사진은 삭제됐어요"*) 한 줄만 합쇼체면 그 자리가 튄다. 근거를 상수 KDoc 에 남겼다.
- 스타일: `typography.medium12` + `colorScheme.onSurfaceVariant`
  🔴 **`error` 색을 쓰지 않았다** — 같은 카드의 `VerificationStatusPill` 이 이미 error 색으로 "실패" 를 말하고 있어 사유까지 같은 색이면 **한 카드 안에서 둘이 경쟁**한다. 사유는 판정이 아니라 판정에 붙는 설명이라 위계가 한 단계 아래다. `VsHeaderCard` 의 기권 안내 한 줄이 헤드라인 톤 색을 버린 것과 **같은 판단**이고, 그 선례를 따른 것이 이 스타일의 근거 전부다.
- 🔴 **`maxLines` 로 자르지 않았다** — 이의제기 절차가 없는(spec §1 제외) 이 앱에서 이 문구는 사용자가 왜 졌는지 알 수 있는 **유일한 설명**이다. 잘라서 감출 수 없다.
- 조립은 State 파생(`myAiReasonText` / `opponentAiReasonText`)이 끝낸다 — Composable 에서 포맷팅 금지 규칙 + 두 카드가 같은 문장을 그려야 하는데 호출부에 맡기면 한쪽만 고쳐져 갈린다.

**배선 2곳** (`ChallengeDetailScreen.kt`) — 내 카드는 `MyMissionSlot.MY_PHOTO` 가지의 사진 아래, 상대 카드는 footer 의 사진 아래. `aiReason` 이 `null` 이면 **간격째 통째로 빠진다**(`forfeitText` 와 같은 형태).

🔴 **`MY_PHOTO_WITH_RETAKE` 가지에는 넣지 않았다.** 그 가지는 `canVerify`(= `IN_PROGRESS`)일 때만 나오고 반려는 `COMPLETED` 이후라 **두 조건이 동시에 참일 수 없다.** 일어날 수 없는 조합에 코드를 두는 것은 이 레포가 금지하는 *"가정에 대한 방어 로직"* 이다.

🔵 **앱은 `status` 와 `aiReason` 을 둘 다 보지 않는다.** `aiReason != null` 하나만 본다 — 계약 §4.1 이 그 등가를 보장하고, `status` 를 함께 보면 판정 사본이 생긴다.

### 🔴 `MissionCardMineFailedPreview` 정리 — 백로그 🟡 항목 종결

**A안이어도 되살아나지 않는다.** api-contract 초안 §2 는 *"A안이면 그 Preview 가 되살아난다"* 고 적었는데 **실측상 틀렸다** — 그 Preview 는 `FAILED` + *"다시 인증하기" CTA* 를 그리는데 판정 시점이 자정 = 마감이라 재시도 창이 구조적으로 없고 `myMissionSlot` 은 `FAILED` 에서 CTA 를 낼 수 없다. **어느 안이든 죽은 화면**이었고, 백로그 판단(*"현재 코드가 옳고 Preview 가 낡았다"*)이 맞았다. pm 이 그 문장을 본문에서 철회했다.

A안이 실제로 만드는 화면(**실패 뱃지 + 사진 + 사유**)으로 고쳐 닫았다. `isLoading` 대신 더미 URL 을 쓴 이유는 로딩 문구가 어느 분기에서 끝나든 같아서, 실패 문구가 사진 자리를 가로채도 프리뷰가 같아 보이기 때문이다.

**프리뷰 추가 4개** — `FAILED` 가 이제 전혀 다른 두 화면을 만들므로 나란히 둬야 읽힌다:
`VerificationPhotoFailedWithPhotoPreview` / `ChallengeDetailScreenMyVerificationRejectedPreview` / `ChallengeDetailScreenOpponentVerificationRejectedPreview` / `RejectionReasonText` 프리뷰 2개(짧은 사유 · **긴 사유가 잘리지 않고 흐르는지**).

### 🔴 규칙 변경으로 거짓이 된 문장 정정 — 코드는 안 깨지고 문장만 틀어진 것들

| 문장 | 왜 거짓이 됐나 |
|---|---|
| `PartyVerification.verifiedAt` — *"인증 확정 시각. 미인증이면 null"* | 🔴 **진짜 의미는 "제출 확정 시각"**. `submit()` 만이 쓰고 판정·탈퇴가 안 건드린다. *"인증 확정"* 으로 읽으면 **두 곳이 잘못 이해된다** — ① 앱의 사진 캐시 키가 이 값을 쓴다 ② 서버 `photoDeleted` 판정식이 *"verifiedAt 있으면 낸 적 있다"* 에 선다 |
| `photoUrl` — *"미인증이면 null"* (도메인·DTO·State 3곳) | 반려 건은 미인증 처리인데 사진이 있다 → *"제출한 적이 없으면 null"* |
| `opponentPhotoDeleted` — *"`VERIFIED` + photoUrl null 조합이 정상인 **유일한** 경우"* | 반려 `FAILED` + 사진 삭제 조합이 하나 더 생겼다. 🔵 요지(*"이 값이 없으면 데이터 이상과 구분되지 않는다"*)는 여전히 참이고 **오히려 강해진다** |
| DTO 파일 머리 예시 JSON | `aiReason` 누락 — 파일이 선언하는 shape 을 스스로 불완전하게 예시하고 있었다 |
| 1단계가 써 넣은 *"아직 화면에 그리지 않는다"* 3곳 | 계약이 닫히며 거짓이 됐다. 지우지 않고 **계약 조항**(*"non-null ⟺ 미인증 확정이므로 앱은 status 를 함께 보지 않는다"*)으로 바꿨다 — 다음 사람이 *"aiReason 있는데 status 가 VERIFIED 면?"* 을 걱정해 방어 조건을 넣는 것을 막는 문장이다 |
| `ChallengeDetailViewModelTest` 의 *"FAILED 는 보여줄 것이 없는 조합"* | 절반만 참이 됐다(사진이 있으면 보여줄 것이 있다). 지우지 않고 **미제출 케이스로 의미를 좁히고** 반려 케이스를 별도 테스트로 추가했다 |

🔵 **backend 경고에 대한 실측 답** — 낡은 계약 문장(*"`photoUrl` 은 `status` 와 `userId` 만으로 결정된다 — 앱이 조립해도 같은 결과"*)을 두고 backend 가 *"앱에 조립 코드 있으면 확인해라"* 고 했다. **없다.** `grep -rn "photos/" --include="*.kt"` 결과 프로덕션 위치는 프리뷰 하드코딩 URL 과 문서 예시뿐이고, 실제 경로는 서버가 준 `photoUrl` 을 `joinPhotoUrl(baseUrl, path)` 로 **baseUrl 에만** 붙인다. 그 함수 KDoc 의 *"조인이 한 곳뿐이라 이 함수가 유일한 방지선"* 이라는 설계가 이번 변경을 무해하게 만들었다.

---

## 테스트 결과

실측 기준: `./gradlew` 로그의 **`BUILD SUCCESSFUL in 1m 53s`**, 요청한 8개 태스크 **전부 `UP-TO-DATE` 없이 실행**, 결과 XML 을 직접 읽어 집계(2026-09-22 09:35~09:36).

| 모듈 | Android (`testDebugUnitTest`) | iOS (`iosSimulatorArm64Test`) | 비고 |
|---|---|---|---|
| `:remote:mapper` | **140 / 140** | **140 / 140** | 베이스라인 135 → **+5** |
| `:feature:challenge:detail` | **75 / 75** | **75 / 75** | 베이스라인 69 → **+6** |
| `:remote:datasource` | **41 / 41** | 🔴 **XML 디렉터리 자체가 없음** | 기존 백로그 항목 — 내 변경과 무관 |
| `:feature:home` | **27 / 27** | **27 / 27** | 회귀 확인용(`VerificationStatus` 소비처) |
| **합계** | **283 / 283** | **242 / 242** | **failures 0 / errors 0 / skipped 0** |

**추가한 테스트 11건** (베이스라인 대비): 매퍼 2(반려 건 통과 · `null` 유지) / wire 픽스처 3(`"aiReason":null` 명시 키 · `FAILED`+사진+사유 원문 · **`aiReason` 키가 아예 없는 원문** — 기본값이 키 누락을 덮는지) / VM 6(반려·미제출 슬롯 분기 · `aiReason` State 도달 · 문구 조립).

- **Android 빌드**: ✅ **ok** — `:composeApp:assembleDebug` 성공, `composeApp-debug.apk` 09:36:38 생성 확인
- **iOS 빌드**: ✅ **내 변경 범위는 ok** — 바꾼 두 모듈이 `iosSimulatorArm64` 로 컴파일·테스트 통과. ⚠️ 단 **framework 링크는 기존 결함으로 막혀 있다**(바로 아래 미해결 참조)

> 🔵 **베이스라인을 먼저 떠 놓고 비교했다** — 착수 전 같은 방식으로 `:remote:mapper` 135/135 · `:feature:challenge:detail` 69/69 (Android·iOS 각각, failures 0)을 측정했다. 증감이 전부 내가 추가한 테스트 수와 일치하고 **기존 테스트 회귀 0**이다.

---

## Working tree 상태

- **작업 브랜치: `main`** (현재 체크아웃된 것. 새로 만들지 않았다)
- 변경분은 **unstaged 그대로** 뒀다 — 🔴 **커밋·푸시·PR 생성 안 함** (사용자 처리 영역)
- 시작 시 HEAD `1ff4ef4` (챌린지 기권), working tree clean 에서 출발

---

## 미해결 이슈

### 🔴 1. 반려 화면을 **실제로 본 적이 없다** — 실기 미확인

AI 판별이 현재 **비활성**이다(Gemini 키 미설정 → `NoOpMissionVerifier`). 게이트가 `UNVERIFIABLE` 을 막으므로 **`aiReason` 은 실제로 항상 `null` 로 온다.** 즉 지금 서버를 붙여도 **이번 작업의 결과물이 화면에 한 번도 나오지 않는다.**

확인하려면 DB 에 네 값을 직접 넣어야 한다 (backend 안내 — **셋이 다 있어야 게이트를 통과**한다):

```sql
status = 'FAILED', ai_verdict = 'REJECT', ai_confidence = 0.93, ai_reason = '...'
```

⚠️ **프리뷰로는 절반만 확인된다** — Compose UI 테스트 인프라가 이 레포에 없고(단위 테스트만), 프리뷰는 네트워크를 못 타 Coil 의 로딩 슬롯까지만 보인다. **"실패 문구가 사진 자리를 가로채지 않는다" 는 프리뷰로 드러나지만, 실제 사진 위에 사유가 어떻게 앉는지는 기기에서 봐야 한다.**

### 🔴 2. 접두어와 AI 사유의 **경어체가 섞인다** — 내가 고칠 수 없는 자리

앱 접두어는 **해요체**다(이 화면 전체 문구와 맞춘 것):

> **인증이 인정되지 않았어요:** {aiReason}

그런데 계약 §4 의 `aiReason` 예시가 **합쇼체**다:

> 인증이 인정되지 않았어요: 책상 위 커피잔 사진으로, 미션(주 3회 운동) 수행 증거로 **보기 어렵습니다.**

🔴 **한 문장 안에서 해요체 + 합쇼체가 섞인다.** 그리고 이건 앱이 정할 수 없다 — **AI 사유의 톤은 서버 프롬프트가 정한다.** 접두어를 합쇼체로 올리면 이 화면의 다른 문구 전부와 어긋나므로(그게 해요체를 고른 이유다) 앱 쪽 해법이 없다.

🔵 **[ADR-0013](../../decisions/0013-ai-verification-provider.md) §미해결의 *"`reason` 한국어 톤 실측"* 항목이 정확히 이것이고, 이번 구현으로 그 항목이 추상에서 구체로 내려왔다.** 프롬프트에 **해요체**를 지정하면 해소된다 — backend / pm 소관. **백로그 항목의 조치 내용으로 "프롬프트에 해요체 지정" 을 적어 둘 것을 제안한다.**

### 🎨 3. 디자이너 확인 대상 — 반려 사유 표시 **전체**

**디자인 산출물이 0건이다**(Lovable 에 반려 사유 화면 없음 — challenge-verification 때 실측). 기존 토큰과 `VsHeaderCard` 의 기권 안내 선례만으로 만들었고, 그 선례가 근거의 전부다. 확인 필요:

1. 사유가 **사진 아래**에 붙는 자리 (간격 8dp)
2. 위계 — `medium12` + `onSurfaceVariant`. 🔴 **`error` 색을 쓰지 않은 판단**(Pill 과 경쟁)
3. **긴 사유가 잘리지 않고 여러 줄로 흐르는 것** (`maxLines` 없음). 사유 길이가 카드 높이를 밀어낸다
4. 반려 카드의 완성 조합 — **실패 뱃지 + 사진 + 사유**
5. **상대 카드에도 같은 문구가 붙는 것** (상대 인증이 반려된 경우)

### 🔵 4. root-level `iosSimulatorArm64Test` 가 실패한다 — 기존·무해, 그러나 백로그 대상

```
Execution failed for task ':local:database:kspKotlinIosSimulatorArm64'
e: [ksp] local/database/.../AppDatabase.kt:18:
   The @Database class must be annotated with @ConstructedBy
   since the source is targeting non-Android platforms.
```

**내 변경과 무관하다** — `git status local/database/` 빈 결과(미변경), 마지막 커밋 `2b73444`.

🔵 **범위를 실측으로 좁혔다 — 처음 보고한 것보다 좁다:**

| 확인한 것 | 결과 |
|---|---|
| `:composeApp:linkDebugFrameworkIosSimulatorArm64` | ✅ **`BUILD SUCCESSFUL in 1m 13s`** — 로그에 `:local:database` 태스크가 **한 개도 안 나온다** |
| `:local:database` 를 의존하는 모듈 | 🔑 **0개** (`grep -rn "local:database" --include=build.gradle.kts` → 자기 namespace 줄 하나뿐) |

→ **`:local:database` 는 아직 아무도 쓰지 않는 미배선 모듈이다.** 그래서 ⓐ iOS 프레임워크는 영향 없고 ⓑ 앱 동작에도 무해하며 ⓒ 막히는 것은 **root-level 로 전 모듈 iOS 테스트를 한 번에 돌리는 경로 하나**뿐이다.

⚠️ **그래서 지금까지 안 드러났다** — 이 프로젝트의 iOS 수치는 **항상 모듈별 실행**으로 나왔고(이번 검증도 그 방식), 그 경로는 이 모듈을 타지 않는다.

🔴 **조치는 `@ConstructedBy` 추가가 아니라 모듈 삭제다** (pm-lead 지적 → 내가 실측 확인). 이 모듈은 **TMDB 템플릿 잔재**다:

| 실측 | 결과 |
|---|---|
| `AppDatabase` 의 엔티티 | **`SearchHistoryEntity`(검색 기록) · `FavoriteEntity`(찜)** — 챌린지 도메인이 아니다 |
| 모듈 밖 소비처 | **0건** — `AppDatabase`/두 엔티티/DAO 참조가 전부 `local/database/` 안에만 있다 |
| 🔑 가시성 | **모든 선언이 `internal`** (`AppDatabase` · 엔티티 2 · DAO 2 · DataSource 2 · DI) → **외부 모듈이 쓸 수조차 없다.** 미사용이 아니라 *구조적으로 사용 불가*다 |

🔑 **애노테이션을 붙이면 죽은 코드를 되살려 유지 비용만 남기고 iOS KSP 가 계속 그 모듈을 컴파일한다.** 삭제하면 빌드 실패가 **부수적으로 사라진다.** ⚠️ 모듈 삭제는 별건이고 T-M2/T-M3 범위가 아니라 **이번 feature 에서 손대지 않았다** — 백로그에 등재됐다.

🔵 **부수 — `repos.json` 의 거짓 주장 1건이 드러났다**: blockers 에 *"TMDB 흔적 코드·설정 전부 0건 (68d6533 시점에 정리됨)"* 이라고 박혀 있었는데 **모듈이 통째로 살아 있다.** 그 문장 때문에 아무도 다시 안 봤다(pm-lead 가 정정). **root-level 로 한 번 돌린 것이 이걸 드러냈다.**

### 🔵 5. `:remote:datasource` iOS 테스트 미컴파일 — 기존 백로그 항목 **존치 확인**

이번 검증에서도 `remote/datasource/build/test-results/iosSimulatorArm64Test/` **디렉터리 자체가 없다**. verification-photo-replace 때 적발된 그 항목(백틱 이름의 `,()` — Kotlin/Native 금지)이 그대로다. 🔵 위 4번과 **원인은 다르지만 결과가 같은 계열**이다(iOS 커버리지 구멍이 조용히 있는 것).

### 🔵 6. 기록만 — "반려 후 탈퇴" 조합에서 내 카드는 사유가 안 뜬다

`myMissionSlot` 이 `myPhotoUrl != null` 만 보므로, 사진이 삭제되면 `NONE` 이 되어 사유도 함께 빠진다. **내 사진이 삭제되는 것은 내 탈퇴이므로 내가 그 화면을 볼 수 없어 실질적으로 도달 불가**하다. 상대 카드는 사진 영역이 항상 렌더되므로 정상이다.

🔵 **방어 로직을 넣지 않았다** — 도달 불가능한 조합에 코드를 두는 것은 이 레포가 금지하는 *"가정에 대한 방어"* 다. 기록만 남긴다.

---

## API 계약 대비 구현 차이

**없다.** 계약 §4·§4.1 그대로 구현했다.

- `aiReason` 은 `GET /challenges/{id}/verifications` 에서만 받는다. `SubmitVerificationResponse` · `ActiveChallengeResponse` 에는 필드가 없고 앱도 요구하지 않는다(내 Q3 실측으로 계약 범위가 안 커졌다)
- `aiVerdict` / `aiConfidence` 는 받지 않는다 — 신뢰도 숫자를 노출하면 사용자가 그 값을 두고 다툰다(계약)
- 앱 규칙은 계약이 요구한 한 줄 그대로: **`aiReason != null` 이면 그린다**. `status` 를 함께 보지 않는다
