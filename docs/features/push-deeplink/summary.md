# 푸시 알림 딥링크 (push-deeplink) — Summary

- **feature-id**: push-deeplink
- **완료일**: 2026-08-08
- **상태**: `implemented` — **`completed` 아니다.** 실기 검증(T-I1) 미실시 + **양 레포 미커밋**
- **선행**: [push-fcm](../push-fcm/summary.md) (`completed`, 2026-08-07)
- **범위**: Android. iOS 는 수신 자체가 미구현이라 자동 제외 — **단 `PushEvent`·`MainViewModel` 은 commonMain 이라 iOS 단위 테스트까지 초록이다**

## 구현 개요

**알림이 목적지를 갖게 됐다.** `push-fcm` 은 알림을 띄우는 데까지 갔고 누르면 홈이 전부였다.
그 문서가 남긴 미해결 *"🟢 딥링크 미구현 — `data.challengeId`는 이미 실려 있어 후속에서 라우팅만
붙이면 서버 변경 0"* 을 이번에 닫았다. **그 전제는 실제로 맞았다** — 서버 코드 변경은 `tag` 추가
한 건뿐이고 `notification`·`data` 블록은 무접촉이다.

입력은 mobile-dev 가 작성한 설계 문서([mobile-design.md](./mobile-design.md))였다.
**그대로 구현하지 않았다** — 검증 결과 결함 2건과 이미 해결된 요청 3건이 섞여 있었다(§1).

## 엔드포인트

**신규 0건. 변경 0건.** 요청·응답 shape 무변경이다. 유일한 서버 변경은 FCM 발송 페이로드에
`android` 블록이 **추가**된 것이고, 이는 [push-fcm/change-log.md](../push-fcm/change-log.md)에
등재했다(`confirmed` 이후 첫 계약 변경).

---

## §1 🔴 설계 문서를 검증했더니 5건 중 3건은 이미 끝나 있었고, 빠진 것이 2건 있었다

설계 문서는 백엔드에 5가지를 요청하며 *"2번(`challengeId` 키 이름 확인)이 가장 시급하다 …
실기기에서 알림을 한 번 받아 로그를 확인하면 바로 판별된다"* 고 적었다.
**그 항목은 실기기 없이 해소됐다.**

| # | 설계 문서의 요청 | 실측 | 근거 |
|---|---|---|---|
| 1 | `data.type` 신규 추가 | ✅ **이미 전송 중** | `FcmNotificationSender.send()` 의 `putData(DATA_KEY_TYPE, message.type.name)` |
| 2 | `challengeId` 키 이름 확인 (*가장 시급*) | ✅ **키 이름이 정확히 `challengeId`** | `DATA_KEY_CHALLENGE_ID` |
| 3 | `data` 동봉 보장 | ✅ 보장. **단 조건부 누락 규칙 있음** | `referenceId?.let { putData(...) }` |
| 4 | `android.notification.tag` | ❌ **미구현 → 이번 유일한 백엔드 작업** | — |
| 5 | 향후 이벤트 이름 합의 | ✅ **3종이 이미 enum 에 예약** | `NotificationType` |

작성자가 앱 코드만 보고 `push-fcm/api-contract.md`(`confirmed`)를 보지 않은 결과다.

### 🔴 결함 1 — `CHALLENGE_REQUEST` 를 통째로 빠뜨렸다

설계 문서는 대상을 *"수락/거절 2종"* 으로 적었다. **서버가 보내는 건 3종이고, 빠진 그 타입이
`push-fcm` 실기 검증에서 가장 많이 발화한 알림이다** — `CHALLENGE_REQUEST` 5회 /
`CHALLENGE_REJECTED` 2회 / `CHALLENGE_ACCEPTED` 1회.

설계대로 짰으면 **가장 흔한 알림에서 `PushEvent.from` 이 `null` 을 반환**해 딥링크가 안 먹는다.
크래시가 없어 **조용히 홈에만 머무는** 형태로 실패했을 것이다.

### 🔴 결함 2 — `challengeId` 가 항상 실린다는 전제가 틀렸다

서버는 `referenceId` 가 `null` 이면 **키를 통째로 뺀다.** 현재 3종은 전부 실리지만
**오늘의 사실이지 규약이 아니다** — `push-fcm` 결정사항 6번이 *"`reference_id` 를 `challenge_id`
로 못 박지 않는다"* 고 명시했고, `FRIEND_REQUEST` 가 붙는 순간 현실이 된다.

설계의 전역 `?: return null` 은 그 타입까지 조용히 버린다. **타입별 분기 안에서 판정**하도록 바꿨다.

---

## §2 PM 판정

| 타입 | 목적지 | 근거 |
|---|---|---|
| `CHALLENGE_REQUEST` | `Route.Home` | **수락/거절 액션이 홈 상단 "받은 도전장" 섹션에만 있다.** [challenge-create/design.md](../challenge-create/design.md)가 그 섹션을 위로 올린 이유로 든 진입점이다 |
| `CHALLENGE_ACCEPTED` | `Route.Challenge.Detail(challengeId)` | 수락 순간 `soul-oath` 가 수락과 서명을 원자로 묶어 **계약서가 성립한다.** 그걸 보러 누른 것이다 |
| `CHALLENGE_REJECTED` | `Route.Home` | 거절된 챌린지는 계약서가 없다. **빈 계약서를 보여주게 된다** |

**중복 정책은 덮어쓰기** — `tag = "challenge-{challengeId}"`. 포그라운드는 이미 `challengeId` 를
알림 id 로 써서 덮어쓰고 있었으므로 **백그라운드를 포그라운드에 맞추는 정합성 작업**이다.

**data-only 전환 보류 / 프로세스 사망 후 중복 소비 미방지**는 설계 문서 판단을 그대로 승인했다.

### 🔴 §2.1 pm-lead 가 근거를 틀렸고 정정했다

최초 판정문은 *"REJECTED 를 넣으면 Detail 이 Error 로 떨어질 가능성이 높다"* 를 근거로 삼고,
mobile-dev 에게 실측을 조건으로 걸었다. **그 근거가 틀렸다.**

```kotlin
// ChallengeDetailService.getDetail — 상태 필터가 없다
findById(challengeId) ?: throw OneButtonDialogException(MSG_NOT_FOUND)
if (me != challengerId && me != opponentId) throw SnackbarException(MSG_NOT_MINE)
val contract: Contract? = contractRepository.findByChallengeId(challengeId)   // nullable
```

검사하는 건 **존재 여부**와 **당사자 여부** 둘뿐이다. 어느 상태든 당사자면 200 이고,
`contract` 는 nullable 이며 모바일 `contract=null` 대응은 이미 들어가 있다(`a298125`).

**pm-lead 가 화면 이름(`ChallengeDetail…`)만 보고 "계약서 화면이니 계약서가 없으면 깨질 것"이라고
추측을 근거로 적었다.** `push-fcm` 계약서가 서버가 보내지 않는 `"data": null` 을 명시했던 것(#25 감사)과
같은 계열 — **확인하지 않은 것을 확인한 것처럼 적었다.**

`ACCEPTED → Detail` 은 안전이 확정됐고, `REJECTED → Home` 은 **결론만 유지하고 근거를 교체**했다
(안정성이 아니라 UX 판단). 상세는 [spec.md §1.1](./spec.md).

> **mobile-dev 가 pm-lead 실측보다 강한 논증을 하나 더 댔다**: `ChallengeCommandService.accept()` 는
> 한 트랜잭션에서 계약 저장 → 상태 전이 → verification 생성을 마친 **뒤에야** 알림을 발행한다.
> 즉 **알림의 존재 자체가 계약 성립 커밋의 증거**이므로 `ACCEPTED` 경로는 `contract` 가 null 일 수도 없다.

---

## 주요 변경

**백엔드** (미커밋, 2파일 +134/-0)
- `FcmNotificationSender` — `AndroidConfig` 추가. `tagFor(referenceId)` **순수 함수**로 분리
- 🔴 **`referenceId` 가 null 이면 `android.notification` 블록 자체를 뺀다** — `"challenge-null"` 로
  뭉치면 **무관한 알림들이 한 덩어리가 되어 서로를 덮어써 예외도 로그도 없이 사라진다**
- `priority = HIGH` — **오늘 기준 동작 변화 0.** FCM 은 `notification` 포함 메시지를 이미 high 로
  취급하므로(data-only 만 normal) **새 동작을 켜는 게 아니라 현재 실효 동작을 명시로 고정**하는 것
- 계약 §3.1 신설 + §0.6.1 신설 + `change-log.md` 등재

**모바일** (미커밋, 편집 7파일 +138/-23, 신규 8파일)
- **`:core:push`** — `PushEvent`(sealed, 3종) + `PushEventBus`(StateFlow) + `pushModule`
- **`:feature:main`** — `MainViewModel` 인증 게이트(`combine(pending, isAuthenticatedArea)`), `toRoute()`
- **`composeApp`** — `MainActivity` intent 파싱 + `onNewIntent` + `removeExtra`,
  `ChallengeFirebaseMessagingService` extras 키 통일(기존 `EXTRA_*` 상수 삭제)
- `buildNotificationId` KDoc — 서버 tag 와의 결합 명문화

## 테스트 결과

| 대상 | 결과 |
|---|---|
| **서버 전체** | **260/260 passed** (305 중 skip 45), failures 0 / errors 0. push-fcm 기준선 254 → 260, **회귀 0** |
| `FcmNotificationSenderTest` | **10/10 passed** (4 → 10) |
| `PushEventTest` (Android/iOS) | **9/9 passed** |
| `MainViewModelTest` (Android/iOS) | **9/9 passed** (8 → 9) |
| `ChallengeDetailViewModelTest` | **14/14 passed** |
| **모바일 전체** | **267/267 passed**, failures 0 |
| `:composeApp:compileDebugKotlinAndroid` | BUILD SUCCESSFUL |

> ⚠️ **숫자의 한계를 밝힌다.** 모바일 267 은 **한 번의 전체 실행에서 나온 수가 아니라 최신 모듈별
> XML 합산값**이다. 전 모듈 일괄 실행은 1회(266건)였고 이후 `:feature:main` 만 재실행해 9가 됐다.
> 서버 skip 45 는 컨테이너 런타임 부재로 인한 **누적 건**이다(백로그 🔴).
> **iOS 단위 테스트는 이 두 모듈에 한해 실행됐다** — `push-fcm` 이후 누적된 "iOS 미실행"이 부분 해소됐다.

## 🔴 검증되지 않은 것 — 이 feature 의 핵심이 여기 있다

**T-I1(실기 5케이스)을 하나도 실행하지 않았다.** 기기·에뮬레이터·기동 중인 백엔드가 없다.

- spec 이 *"이번 설계의 핵심"* 으로 지목한 **로그아웃 상태 탭 / 화면 회전** 두 케이스가 미검증분이다
- 단위 테스트가 게이트 로직과 `KEYS` 완전성은 고정하지만, **`intent.removeExtra` 가 실제 Activity
  재생성에서 먹는지는 단위 테스트 밖**이다
- 🔴 **tag 중복 제거는 자동 테스트로 증명 불가하다.** 증명된 건 *"올바른 tag 를 실었다"* 까지고,
  *"트레이에 하나만 남는다"* 는 Android 시스템의 몫이라 **배포 후 실기가 유일한 경로**다

**추정으로 통과 처리한 항목은 0건이다.**

## 결정 사항

1. **이벤트 기준 타입 체계** — 서버는 *"무슨 일이 일어났는가"* 만 보내고 목적지는 앱이 정한다.
   `toRoute()` 가 sealed 에 대한 exhaustive `when` 이라 **새 타입 추가 시 목적지 지정이 컴파일로 강제**된다.
   `else ->` 금지가 이 설계의 값어치다.
2. 🔴 **`challengeId` 필수 여부는 타입별로 판정** — §1 결함 2. 전역 필수는 확장 시 조용히 깨진다.
3. **`PushEvent` 를 `:core:push` 에** — UseCase/Repository 어디에도 안 나오는 푸시 계층 개념이고,
   새 모듈 간선이 `feature:main → core:push` 하나로 끝난다.
4. **`PushEvent → Route` 매핑을 `:feature:main` 에** — 소비처가 한 곳뿐. 알림 목록 화면이 생기면 승격.
5. **pending 을 ViewModel 이 아니라 Bus 가 보관** — `MainActivity`(androidMain)와
   `MainViewModel`(commonMain) 사이에 KMP 경계가 있다. `SharedFlow` 가 아니라 `StateFlow` 인 이유는
   `onCreate` 시점에 ViewModel 이 아직 구독 전일 수 있어서다.
6. **새 로그인 완료 신호를 만들지 않는다** — `MainRoute` 의 기존 `isAuthenticatedArea` 재사용.
   자동/수동 로그인이 같은 지점을 지나고 **로그아웃하면 자동으로 `false` 로 되돌아간다.**
7. **contentIntent extras 를 FCM 백그라운드 경로와 동일한 키·타입으로** — 파서가 한 벌로 끝나고,
   나중에 data-only 로 전환해도 앱 코드가 그대로다.
8. 🔴 **로그아웃 시 `pending` 소거** — 아래 §3.
9. 🔴 **새 타입 발송 개시 전 모바일 통지를 계약에 명문화**(§0.6.1) — 아래 §4.

### 🔴 §3 로그아웃 시 pending 소거 — 왜 "가정에 대한 방어"가 아닌가

mobile-dev 가 발견해 보고했고 pm-lead 가 승인했다. 로그아웃해도 `pending` 이 남아, **같은 기기에서
다음 사람이 로그인하면 앞사람의 딥링크로 이동**한다.

이 프로젝트는 *"관측되지 않은 가정에 방어 로직을 넣지 않는다"* 를 기준으로 삼는다. **이 건은 걸리지 않는다:**

1. **우리가 방금 만든 코드의 상태 누수다.** 새 방어물이 아니라, 세션 소유 상태가 세션 경계를 넘는 것을 막는 것
2. 🔴 **같은 구조의 선례가 현실이 됐다.** `push-fcm` 결정사항 2번(토큰 소유권 이전)이
   *"`dev-test-login` 계정 전환이 표준 검증 방식이라 방어가 없으면 개발 첫날 발생한다"* 로 도입돼
   **실사용에서 증명**됐다. 유발 조건이 이 프로젝트의 **표준 워크플로**다
3. 비용이 한 줄이고 위치가 특정돼 있다

⚠️ **증상 수위를 과장하지 않는다** — 데이터는 새지 않는다. 서버가 *"당사자만 볼 수 있다"* 로 막아
`SnackbarException` 이 뜬다. **실제 증상은 "로그인했더니 난데없는 화면 + 에러 스낵바"** 다.

> **테스트에 함정이 두 개 있었고 정면으로 다뤘다** — `loggedOut` 은 cold Flow 라 수집 없이
> `logout()` 만 부르면 `onEach` 가 안 돌아 **통과하는데 아무것도 검증하지 않는다.**
> `_logoutRequested` 는 replay 가 없어 구독 전 호출은 영영 오지 않는다. Turbine 으로 구독을 세운 뒤
> 호출하도록 짰다. 기존 `게이트가 닫힌다` 는 **별개 단언**이라 손대지 않았다.

### 🔴 §4 계약 §0.6.1 — 서버 파일 하나가 모바일을 조용히 깨뜨릴 수 있다

`NotificationMessages.of()` 가 나머지 5종에 `null` 을 반환해 **오늘 3종 외 도착은 구조적으로
불가능**하다. 위험은 **그 게이트가 풀리는 방식**이다 — 문구 한 벌을 추가하면 승인 단계 없이
즉시 실사용자에게 도달하고, **모바일은 알 방법이 없다.**

구버전 앱은 `else -> null` 로 버려 **크래시가 없어서** 문제다. 로그·크래시 리포트에 아무것도 안 남는
**무증상 실패**가 된다. 게이트를 푸는 사람과 라우팅을 붙이는 사람이 다른 레포에 있고 서버 변경만으로
완결되므로 **서버 안에 모바일을 멈춰 세울 지점이 없다.** 그래서 계약에 박았다.

🔵 **`FRIEND_REQUEST` 개시 순간 §1 결함 2(`challengeId` 키 누락)와 §3.1(`android.notification` 부재)이
처음으로 실제 발생한다.** 통지에 `referenceId` 가 무엇을 가리키는지 포함하도록 규약에 넣었다.

## 부수 성과 — `push-fcm` 계약서의 세 번째 드리프트를 잡았다

§0.6.1 근거를 실측하던 backend-dev 가 **계약과 서버 KDoc 의 충돌**을 발견했다.

| | 주장 |
|---|---|
| 계약 §3 | *"✅ **3종 전부 확정** (커밋 `e76c64c`)"* |
| `NotificationMessages` KDoc | *"`CHALLENGE_REQUEST` 만 ✅ 확정, 나머지 2종은 🟡 초안값"* |

🔴 **그 KDoc 은 사용자가 `e76c64c` 에서 직접 쓴 것이다.** 계약이 확정 근거로 인용한 바로 그 커밋이
같은 커밋 안에서 2종을 초안으로 표시했다(`git show` 확인).

**두 가지가 뒤섞여 있었다** — *"표가 코드와 일치한다"*(참)와 *"3종 전부 사용자 확정 문구다"*(거짓).
**문자열 교체와 문구 확정을 같은 사건으로 읽은 것이다.** §3 헤더를 `1종 확정 / 2종 초안` 으로
정정하고 세 번째 드리프트 사례로 등재했다.

부수로 **KDoc 자체의 오기도 잡혔다** — 2종을 *"반말"* 이라 적었으나 실제는 합니다체다.
정정 과정에서 **갈린 축이 존댓말/반말이 아니라 `title`** 이라는 더 정확한 진단이 나왔다
(`body` 는 셋 다 합니다체).

### 🔴 이 드리프트가 앞의 둘과 다른 점 — 그리고 정정이 한 번 더 필요했던 이유

**1·2번은 *"코드를 안 봐서"* 낡았는데, 3번은 문자열을 정확히 옮겼고 상태 표기만 틀렸다.**
즉 **문자열만 실측하면 확정 여부를 알 수 없다.** 재발 방지 지점이 *"코드를 봐라"* 가 아니라
**"어느 코드를 봐라"** 이므로, §3 에 **`NotificationMessages` KDoc 이 확정 상태의 정본**임을 명시했다.

계약 헤더의 `confirmed` 배지에도 단서를 달았다 — ***"`confirmed` 는 계약 shape 에 대한 것이고,
§3 문구 2종은 여전히 초안이다."*** 문구 변경은 shape 을 바꾸지 않는다(서버가 만들어 보내고 모바일은
그대로 표시). 이 구분이 없으면 다음 사람이 *"confirmed 인데 왜 초안이 있지"* 로 또 헷갈린다.

🔴 **그리고 1차 정정이 §3 헤더 한 곳만 고쳤다.** 같은 사실이 **오픈 이슈 표 1번 행**에도
*"✅ 해소 — 3종 전부 확정"* 으로 적혀 있었고, **취소선까지 쳐져 "닫힌 이슈"로 보이던 상태**라 더 나빴다.
pm-lead 가 잔존을 지적해 2차 정정으로 `🟡 부분 해소` + 취소선 해제까지 마쳤다.

> **교훈**: 같은 사실이 문서 안 두 곳에 있었고 한 곳만 고쳤다. **정정할 때는 `grep` 으로 전 사례를
> 훑어야 한다.** 최종 확인 결과 `"3종 전부 확정"` 잔존 4건은 **전부 정정 서술 안의 인용**이고
> 주장으로 남은 것은 0건이다.
>
> ⚠️ 오픈 이슈를 다시 열되 **"#32 영향"은 `❌ 없음` 으로 뒀다** — *상태를 정확히 적는 것*과
> *블로커로 취급하는 것*은 다르다. 문구 변경은 계약 shape 을 안 바꾸고 테스트도 문자열을 단언하지 않는다.

> **남은 2종 확정과 전역 톤 통일은 사용자 결정이라 백로그로 넘긴다.** KDoc 이
> *"임의로 통일하지 마라. 확정분을 초안에 맞추는 방향은 특히 안 된다"* 고 명시했고 그 지시는 유효하다.

## 미해결 이슈

- [x] ✅ **모바일 커밋됨** — `d25e394 feat: push noti 클릭 시 해당 화면으로 이동하는 기능 구현` + `b49f6d5`(README). working tree clean (2026-08-14 확인)
- [ ] 🔴 **서버 3파일 미커밋** — `FcmNotificationSender.kt` / `FcmNotificationSenderTest.kt` / `NotificationMessages.kt`. HEAD 여전히 `e76c64c`. ⚠️ **기능 파손은 없다** — 앱이 읽는 `data.type`·`challengeId` 는 `push-fcm` 때 이미 배포됐고, 미커밋분은 `android` 블록 추가 + 주석뿐이다. **다만 트레이 중복 제거가 안 켜져 있고, 최상위 블로커(T-I1)의 임계 경로 위에 있다**
- [ ] 🔴 **PM 문서 커밋** — 코드보다 급하다. 코드는 테스트로 재구성되지만 **판단 근거(tag null 가드 이유, priority 근거, 계약 §3 세 번째 드리프트 정정)는 이 파일들에만 있다**
- [ ] 🔴 **T-I1 실기 검증 미실시** — 위 절 전체. **수용 기준 중 실기로만 확인 가능한 항목이 남는다**
- [ ] 🔴 **tag 중복 제거 미배포·미실증** — 서버 배포 후에만 확인 가능
- [ ] 🟡 **알림 문구 2종 미확정 + 전역 톤 통일** — 사용자 결정 대기. `push-fcm` 미해결 🟢 와 같은 건
- [ ] 🟡 **`.setToken` deprecation** — `firebase-admin 9.10.0`. **기존 코드이고 이번 변경과 무관**(도입 `f01bd44`, 삭제 라인 0). ⚠️ **한 줄 교체가 아니다** — `setFid` 가 등록 토큰의 대체재라는 근거가 없고(FID 는 다른 식별자), 바꾸면 `users.fcm_token`·`confirmed` 계약 §1·모바일 `FcmTokenProvider` 를 함께 건드리는 **교차 레포 작업**이 된다. 착수 전 선결: *"`setFid` 가 대체재인지 별개 타겟팅 수단인지"* Firebase 문서 확정
- [ ] 🟢 **프로세스 사망 후 딥링크 중복 소비** — `removeExtra` 는 메모리상 `Intent` 만 고친다. 설계 판단대로 **의도적 미방지**(재이동이 오히려 자연스럽다). 필요해지면 `SavedStateHandle`
- [ ] 🟢 **`challengeId?.toInt()` Long→Int 절단** — `challenges.id` 가 21억을 넘으면 서로 다른 챌린지가 같은 알림 id 를 갖는다. **관측된 적 없고 현실적이지 않다.** 알림 id 체계를 다시 볼 때 함께
- [ ] 🟢 **통합 테스트 45건 skip** — 컨테이너 런타임 부재. 누적 건

## 🔴 프로세스 사고 — 에이전트 이름 충돌로 지시가 샜다

**pm-lead 가 spawn 한 팀원은 `backend-dev-3`/`mobile-dev-3` 인데, 이름을 `backend-dev`/`mobile-dev` 로
요청해 시스템이 접미사를 붙였다.** 그 사실을 확인하지 않고 이후 `SendMessage` 를 원래 이름으로 보내는
바람에 **지시가 이전 세션의 다른 인스턴스로 갔다.**

- 배정을 못 받은 인스턴스가 *"T-B1 담당자가 나는 아니다"* 라고 회신 — **그쪽 기준으로는 정확한 말**
- pm-lead 가 그 회신을 담당자의 상태로 착각해 **작성자 미상**으로 오판
- 같은 인스턴스가 diff 만 읽고 *"priority 근거가 없다"* 고 보고 — **틀렸다**(KDoc 에 섹션 통째로 존재).
  원인은 `grep -B3` 로 3줄만 봤는데 근거가 13줄 위에 있던 것. **도구의 창을 근거의 크기에 맞추지 않고,
  창에 안 들어온 것을 "없다"로 보고**했다

🔴 **더 위험했던 것**: `backend-dev-3` 이 `mobile-dev-2`(지휘 계통 밖)에게 **직접 작업을 요청**했다.
**`mobile-dev-2` 가 실행하지 않고 보고해 사고가 예방됐다** — 그 파일은 당시 `mobile-dev-3` 이
편집 중이었고, 실행됐으면 **같은 파일을 두 에이전트가 동시에 고치는 상황**이 됐다.
공교롭게도 `backend-dev-3` 자신이 직전에 경계한 구조다.

**교훈 2건:**
1. **작업 지시는 pm-lead 를 거친다.** 사실 확인 질의는 자유. peer 는 *"누가 무엇을 쥐고 있는지"* 를
   알 수 없고, 그것이 배정을 한 곳으로 모아야 하는 이유다
2. 🔴 **남의 레포는 행 번호로 가리키지 마라.** `backend-dev-3` 이 `:131` 로 지시했으나 실제 `:128` 이었고
   함수 시그니처까지 바뀌어 있었다. **양쪽 모두 심볼 기준 표기로 정정**했다
3. 🔴 **동시 편집 중에는 "확인했다"의 시점을 밝혀야 한다.** pm-lead 가 편집 직전 스냅샷을 근거로
   *"미반영"* 이라 지적한 일이 **3회**(KDoc / `consume()` / 계약 §3) 있었다. 매번 에이전트가
   파일 mtime·XML timestamp·`git diff` 원문으로 반박해 해소됐다.
   **행 번호가 단서였다** — pm-lead 가 인용한 `api-contract.md:298` 이 현재 `299` 인 것이
   *"헤더 위에 한 줄이 추가된 뒤"* 를 못 본 증거였다.
   ⚠️ **다만 이 왕복이 낭비만은 아니었다** — 3회 중 1회(계약 오픈 이슈 1번 행)는 **실제 누락**이었고,
   지적이 없었으면 *"닫힌 이슈"* 로 위장된 채 남았다. **stale read 가 무해한 게 아니라, 확인 자체는
   해야 하고 시점을 함께 말해야 한다는 뜻이다.**

## 참조

- [spec.md](./spec.md) (§0 실측 · §1 판정 · §1.1 정정) · [mobile-design.md](./mobile-design.md)(원본 설계, 판정 전 보존)
- [backend-report.md](./backend-report.md) · [mobile-report.md](./mobile-report.md)
- [push-fcm/api-contract.md](../push-fcm/api-contract.md) (`confirmed`, §3.1 · §0.6.1 추가) · [push-fcm/change-log.md](../push-fcm/change-log.md)
