# 푸시 알림 딥링크 (push-deeplink) — Spec

- **feature-id**: push-deeplink
- **작성일**: 2026-08-08
- **상태**: `in-progress`
- **선행**: [push-fcm](../push-fcm/summary.md) (`completed`, 2026-08-07)
- **범위**: Android. iOS 는 수신 자체가 미구현이므로 자동 제외 ([push-fcm 미해결](../push-fcm/summary.md) 🔵)

## 배경

`push-fcm` summary 의 미해결 항목 **"🟢 딥링크 미구현 — 알림 탭 → 홈까지만"** 을 닫는다.
같은 문서가 *"`data.challengeId`는 이미 실려 있어 후속에서 라우팅만 붙이면 서버 변경 0"* 이라고
적어 뒀고, **이번에 그 전제가 실제로 맞는지 코드로 확인했다** (§0).

입력은 모바일이 작성한 설계 문서 [mobile-design.md](./mobile-design.md) 다. 그 문서의
"1. 협의 필요 항목" 절에 대한 **PM 판정이 §1** 이고, 구현은 그 판정을 반영한 뒤 착수한다.

---

## §0 사실 확인 — 설계 문서의 "협의 필요" 5건 중 3건은 이미 확정돼 있다

설계 문서는 백엔드에 5가지를 요청했다. **실측 결과 1·2·3번은 `push-fcm` 시점에 이미 구현·계약
완료 상태다.** 설계 문서 작성자가 `push-fcm`의 계약서를 보지 않고 앱 코드만 보고 쓴 결과다.

| # | 설계 문서의 요청 | 실측 결과 | 근거 |
|---|---|---|---|
| 1 | `data.type` **신규 추가** 필요 | ✅ **이미 전송 중**. `NotificationType` enum 이름이 그대로 문자열로 실린다 | `FcmNotificationSender.kt:38` `putData(DATA_KEY_TYPE, message.type.name)` |
| 2 | `data.challengeId` 키 이름 **확인 필요** (가장 시급) | ✅ **키 이름이 정확히 `challengeId`**. 실기기 로그 확인 불필요 | `FcmNotificationSender.kt:72` `DATA_KEY_CHALLENGE_ID = "challengeId"` / [api-contract §3](../push-fcm/api-contract.md) |
| 3 | `data` 동봉 보장 | ✅ 보장. 단 **조건부 누락 규칙이 있다** — §0.1 참조 | `FcmNotificationSender.kt:42` |
| 4 | `android.notification.tag` 추가 | ❌ **미구현.** 이번 범위의 유일한 백엔드 작업 | `Message.builder()` 에 `AndroidConfig` 자체가 없음 |
| 5 | 향후 이벤트 이름 사전 합의 | ✅ **3종이 이미 enum 에 예약돼 있다** — `REMIND` / `OPPONENT_VERIFIED` / `RESULT`. 친구 요청 계열은 아직 없음 | `NotificationType.kt:25-30` |

> 설계 문서가 **"2번이 가장 시급하다 … 실기기에서 알림을 한 번 받아 로그를 확인하면 바로 판별된다"**
> 라고 적은 항목은 **실기기 없이 해소됐다.** `push-fcm` 이 이미 계약서에 못 박고 실기 검증까지
> 마친 사안이다 (해당 summary 의 "🔴 실기 검증" 절, 알림 3종 8회 발화 확인).

### §0.1 🔴 `challengeId` 는 "항상 실린다"가 아니다 — 설계 문서의 전제가 틀렸다

```kotlin
// FcmNotificationSender.kt:40-42
// ⚠️ putData 는 null 값을 허용하지 않는다. referenceId 가 없으면 키를 아예 넣지 않는다 —
// 빈 문자열을 넣으면 모바일이 "" 를 파싱하려다 실패한다.
message.referenceId?.let { putData(DATA_KEY_CHALLENGE_ID, it.toString()) }
```

`referenceId` 가 `null` 이면 **`challengeId` 키가 통째로 빠진다.** 현재 3종은 전부 challenge 를
참조하므로 실제로는 항상 실리지만, 이건 **오늘의 사실이지 규약이 아니다** —
`push-fcm` 결정사항 6번이 *"`reference_id` 를 `challenge_id` 로 못 박지 않는다"* 고 명시했고,
친구 요청 알림이 붙는 순간 `challengeId` 없는 타입이 나온다.

**따라서 `PushEvent.from` 이 `challengeId` 를 전역 필수로 두는 설계는 지금은 동작하지만
확장 시 조용히 깨진다.** 필수 여부는 **타입별로** 갈라야 한다 — T-M1 참조.

### §0.2 🔴 설계 문서가 `CHALLENGE_REQUEST` 를 통째로 빠뜨렸다

설계 문서는 대상 알림을 *"챌린지 신청 수락 / 거절"* 두 종류로 적었다. **서버가 보내는 타입은 3종이고,
빠진 `CHALLENGE_REQUEST`(도전장이 도착했다)가 실기 검증에서 가장 많이 발화한 타입이다** —
`push-fcm` summary 의 발화 집계에서 `CHALLENGE_REQUEST` 5회 / `CHALLENGE_REJECTED` 2회 /
`CHALLENGE_ACCEPTED` 1회.

설계대로 구현하면 **가장 흔한 알림에서 `PushEvent.from` 이 `null` 을 반환**해 딥링크가 동작하지
않는다. 앱은 열리므로 크래시는 없고, **조용히 홈에만 머무는** 형태로 실패한다. 3종 전부 다룬다.

---

## §1 PM 판정 — 설계 문서 "1-2. PM 확인" 에 대한 답

### 판정 1. 목적지 매핑

| 타입 | 목적지 | 근거 |
|---|---|---|
| `CHALLENGE_ACCEPTED` | **`Route.Challenge.Detail(challengeId)`** | 수락 순간 `soul-oath` 가 수락과 서명을 원자로 묶어 **계약서가 성립한다.** 사용자가 그 알림을 누르는 이유는 성립한 계약서를 보려는 것이다. 홈으로 보내면 *"방금 무슨 일이 있었는지 네가 다시 찾아라"* 가 된다 |
| `CHALLENGE_REJECTED` | **`Route.Home`** | 거절된 챌린지는 **계약서가 없다.** 상세로 보내면 빈 계약서를 보여주게 된다. 볼 것이 없는 화면으로 보내지 않는다 (⚠️ 최초 근거는 *"Error 로 떨어질 가능성이 높다"* 였으나 **그건 틀렸다** — §1.1 참조. 결론만 유지한다) |
| `CHALLENGE_REQUEST` | **`Route.Home`** | **수락/거절 액션이 홈 상단 "받은 도전장" 섹션에만 있고 Detail 에는 없다.** `challenge-create/design.md` 가 *"받은 도전장 섹션을 진행 중 목록보다 위에 올린 이유"* 로 바로 이 진입점을 든다. 액션이 있는 곳으로 보낸다 |

> 설계 문서는 수락/거절 **둘 다 홈**을 제안하면서 *"`Route.Challenge.Detail` 이 이미 존재하므로
> 수락 알림은 상세로 바로 보내는 편이 자연스러울 수 있다"* 고 스스로 단서를 달았다. **그 단서를 채택한다.**

### §1.1 🔴 판정 1 의 근거 정정 — pm-lead 실측 (2026-08-08)

최초 판정문은 mobile-dev 에게 *"`Detail` 로 보내기 전에 ACCEPTED 상태에서 정상 렌더되는지 실측하고,
Error 로 떨어지면 Home 으로 내려라"* 를 조건으로 걸었다. **그 조건의 전제가 틀렸다.**
pm-lead 가 서버 코드를 직접 확인한 결과:

```kotlin
// ChallengeDetailService.getDetail — 상태 필터가 없다
val challenge = challengeRepository.findById(challengeId) ?: throw OneButtonDialogException(MSG_NOT_FOUND)
if (me != challenge.challengerId && me != challenge.opponentId) throw SnackbarException(MSG_NOT_MINE)
val contract: Contract? = contractRepository.findByChallengeId(challengeId)   // nullable
```

- **상태로 거르지 않는다.** 검사하는 것은 **존재 여부**와 **당사자 여부** 둘뿐이다.
  `ACCEPTED`·`REJECTED`·`PENDING` 어느 상태든 당사자면 200 이 나온다.
- **`contract` 는 nullable 이다** (`ChallengeDetailResponse.contract: ContractDto?`). 계약서가 없는
  챌린지도 응답이 성립하며, 모바일은 `contract=null` 대응이 이미 들어가 있다 (커밋 `a298125`).

**따라서 `CHALLENGE_ACCEPTED → Detail` 은 안전하다** — 실측 조건은 해소됐고 mobile-dev 가 별도로
확인할 필요가 없다.

**`CHALLENGE_REJECTED → Home` 판정은 유지하되 근거를 바꾼다.** *"Error 로 떨어진다"* 가 아니라
**"빈 계약서를 보여주게 된다"** 가 옳은 근거다. 화면이 깨지는 문제가 아니라 **보여줄 내용이 없는
문제**이므로, 판단 축은 안정성이 아니라 UX 다.

> ⚠️ **이 정정의 교훈**: pm-lead 가 화면 이름(`ChallengeDetail…`)만 보고 *"계약서 화면이니 계약서가
> 없으면 깨질 것"* 이라고 **추측을 근거로 적었다.** 실제 서버는 상태를 아예 보지 않는다.
> `push-fcm` 계약서가 서버가 보내지 않는 `"data": null` 을 명시했던 것(#25 감사)과 같은 계열이다 —
> **확인하지 않은 것을 확인한 것처럼 적었다.**

### 판정 2. 이벤트 목록

**현재 3종 전부가 이번 범위다** — `CHALLENGE_REQUEST` / `CHALLENGE_ACCEPTED` / `CHALLENGE_REJECTED`.
`REMIND` / `OPPONENT_VERIFIED` / `RESULT` 는 enum 에 예약돼 있으나 **인증·판정 feature 미착수라
서버가 보내지 않는다.** 지금 매핑을 만들지 않는다 — 목적지를 정할 근거가 없다.

친구 요청 계열 타입은 **아직 존재하지 않는다. 이번에 만들지 않는다.**
설계 문서의 "향후 확장: 친구 요청 수락 / 거절" 은 해당 feature 착수 시점의 일이다.

> 새 타입이 생길 때 `PushEvent.toRoute()` 의 `when` 이 컴파일 에러를 내 목적지 지정을 강제한다.
> 설계 문서가 sealed 를 택한 실질적 이득이고, **이 성질을 유지하는 것이 T-M1 의 수용 기준이다**
> (`else ->` 로 뭉개지 말 것).

### 판정 3. 같은 도전장 알림 중복 정책

**하나로 덮어쓴다.** → `android.notification.tag = "challenge-{challengeId}"` (T-B1 채택).

같은 도전장에 대해 사용자가 알아야 할 것은 **최신 상태 하나**다. "도전장이 왔다" 뒤에 "수락됐다"가
따로 쌓여 있으면 트레이만 지저분해진다. 앱이 그릴 때(포그라운드)는 이미 `challengeId` 를 알림 id 로
써서 덮어쓰고 있으므로, **tag 추가는 백그라운드 동작을 포그라운드에 맞추는 정합성 작업**이다.

### 판정 4. 설계 문서의 "1-3. 이번 범위에서 제외한 것" — 그대로 승인

- **data-only 페이로드 전환 보류** — 승인. 앱 강제 종료 시 미도달 대가가 딥링크 하나 때문에 치를
  값이 아니다. **알림함 기능 착수 시 재검토**하고, 그때까지 파서는 한 벌로 유지한다.
- **프로세스 사망 후 딥링크 중복 소비 미방지** — 승인. 설계 문서의 근거(*"알림으로 들어왔다가 앱이
  죽어 재실행되는 상황이라 다시 이동하는 편이 자연스럽다"*)가 타당하다. **미해결로 기록만 남긴다.**

---

## 사용자 시나리오

1. 사용자가 앱을 쓰지 않는 동안 친구가 도전장을 보낸다 → 알림이 뜬다 → 누르면 **앱이 열리고 홈의
   "받은 도전장" 섹션까지 도달**한다. 지금까지는 알림을 눌러도 홈에서 직접 찾아야 했다.
2. 내가 보낸 도전장을 친구가 수락한다 → 알림을 누르면 **성립한 계약서(상세)가 바로 열린다.**
3. **로그아웃 상태에서 알림을 누른다** → 로그인 화면 → 로그인 완료 → **원래 목적지로 이동**한다.
   딥링크가 로그인 때문에 버려지지 않는다.
4. 같은 도전장에 대한 알림이 연달아 와도 **트레이에 하나만 남는다.**

## 수용 기준

- [ ] 3종(`CHALLENGE_REQUEST`/`ACCEPTED`/`REJECTED`) 전부 딥링크가 동작한다
- [ ] 포그라운드 / 백그라운드(앱 생존) / 앱 종료 **세 경로 모두** 동일하게 동작한다
- [ ] 미인증 상태에서 알림을 누르면 **로그인 완료 후 목적지로 이동**한다 (딥링크 유실 없음)
- [ ] 로그아웃하면 대기 중이던 딥링크가 **자동으로 게이트에 막힌다**
- [ ] 모르는 `type`(구버전 앱 ↔ 신규 서버)에서 **크래시 없이 앱이 정상 개통**된다
- [ ] 화면 회전으로 **같은 알림이 재소비되지 않는다**
- [ ] 같은 `challengeId` 알림이 트레이에 **하나만 남는다**
- [ ] 서버: 기존 알림 발송 회귀 **0건** (`data`/`notification` shape 무변경)

---

## 태스크 분해

### 백엔드 (backend-dev) — 1건

**T-B1. `AndroidConfig.notification.tag` 추가**
- `FcmNotificationSender.send()` 의 `Message.builder()` 에 `AndroidConfig` 를 붙인다.
- `tag = "challenge-{referenceId}"`. 🔴 **`referenceId` 가 `null` 이면 tag 를 붙이지 않는다** —
  `"challenge-null"` 은 서로 무관한 알림들을 한 덩어리로 덮어쓴다. §0.1 과 같은 종류의 함정이다.
- `priority = high` 는 설계 문서 페이로드 예시에 있으나 **현재 미설정이다.** 붙일지 판단해 결정을
  리포트에 남긴다 (도전장 알림은 즉시성이 있으나, high 남용은 Android 배터리 정책상 역효과가 있다).
- **계약 영향**: `push-fcm/api-contract.md` 는 `confirmed` 다. 페이로드 §3 에 `android` 블록이
  추가되므로 **`push-fcm/change-log.md` 에 변경을 등재**한다 (CLAUDE.md 규칙).
- 테스트: 기존 `FcmNotificationSenderTest` 회귀 유지 + tag 생성 규칙(`null` 케이스 포함) 고정.

### 모바일 (mobile-dev) — 5건

> 🔴 **코드 편집은 반드시 `cd challenge-app && claude -p` child 위임** (`.claude/agents/mobile-dev.md`
> "코드 편집 흐름"). 분석·협의만 본체에서 한다.

**T-M1. `PushEvent` + `PushEventBus` (`:core:push`)**
- 설계 문서 §4-1 / §4-2 기반. **단 아래 두 가지를 반영한다:**
  - 🔴 `CHALLENGE_REQUEST` 추가 (§0.2)
  - 🔴 `challengeId` 필수 판정을 **타입별로** 분리 (§0.1). 전역 `?: return null` 금지.
- `toRoute()` 는 sealed 에 대한 exhaustive `when` 유지. **`else ->` 금지** (판정 2).
- `pushModule` Koin 수동 등록 + `App.kt` 배선.

**T-M2. `MainViewModel` 인증 게이트**
- 설계 문서 §4-3. `combine(pending, isAuthenticatedArea)`.
- 기존 `isAuthenticatedArea` 재사용 — 새 로그인 완료 신호를 만들지 않는다.

**T-M3. `MainRoute` 이동 수집 + `MainActivity` intent 파싱**
- 설계 문서 §4-4 / §4-5. 탭 루트면 `switchTab`, 아니면 `navigateTo`.
- 🔴 **`onNewIntent` 누락 금지** — 없으면 앱 생존 중 알림 탭이 무반응이 된다.
- `removeExtra` 로 회전 시 재소비 방지.

**T-M4. `ChallengeFirebaseMessagingService` extras 키 통일**
- 설계 문서 §4-6. `contentIntent` extras 를 FCM 백그라운드 경로와 동일한 키·타입(전부 String)으로.
- 기존 `EXTRA_NOTIFICATION_TYPE` / `EXTRA_CHALLENGE_ID` 상수 삭제.
- **이것이 파서를 한 벌로 유지하는 근거이자, 나중에 data-only 전환 시 앱 무변경을 보장하는 지점이다.**

**T-M5. 테스트 + 빌드 검증**
- `PushEventTest` (commonTest): 3종 정상 파싱 / 모르는 type / `challengeId` 누락 / 비숫자 `challengeId`.
- `MainViewModelTest` (commonTest, Turbine) — `/test-viewmodel` 스킬 규약: 인증 후 도착 / 도착 후 인증 /
  소비 후 재방출 없음 / 미인증 시 무방출.
- 빌드: `:core:push` · `:feature:main` · `:composeApp:compileDebugKotlinAndroid`.
- 🔴 **결과는 숫자로 보고** (CLAUDE.md).

### 통합 (mobile-dev, 백엔드 배포 후)

**T-I1. 실기기 수동 검증** — 설계 문서 §6-2 표 5케이스.
🔴 **로그아웃 상태 탭 / 화면 회전 두 케이스가 이번 설계의 핵심**이므로 반드시 실기로 확인한다.
tag 중복 제거는 **T-B1 배포 후에만** 검증 가능하다.

---

## 의존성

```
T-B1 (독립, 병렬 가능)
T-M1 → T-M2 → T-M3
   └→ T-M4 (T-M1 의 KEYS 상수에만 의존)
T-M1..T-M4 → T-M5
T-B1 + T-M5 → T-I1
```

**API 계약 협의는 사실상 불필요하다** — 요청/응답 shape 변경이 0이고, 페이로드 규약은 §0 에서
실측으로 확정됐다. backend-dev 는 T-B1 만 수행하고 **`tag` 문자열 형식만 mobile-dev 에 통지**한다.

## 참조

- [mobile-design.md](./mobile-design.md) — 모바일 작성 원본 설계 (이 스펙의 입력)
- [push-fcm/summary.md](../push-fcm/summary.md) · [push-fcm/api-contract.md](../push-fcm/api-contract.md) (`confirmed`)
- [soul-oath/spec.md](../soul-oath/spec.md) — 수락=서명 원자화 (판정 1 의 근거)
