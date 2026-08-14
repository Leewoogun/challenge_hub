# Mobile Report — push-deeplink

- **feature-id**: push-deeplink
- **작성일**: 2026-08-08
- **범위**: Android (iOS 는 수신 자체가 미구현 — [push-fcm 미해결](../push-fcm/summary.md) 🔵). **단 `PushEvent`·`MainViewModel` 은 commonMain 이라 iOS 단위 테스트까지 초록이다.**
- **기준 문서**: [spec.md](./spec.md) §0~§1 (원본 [mobile-design.md](./mobile-design.md) 는 결함 3건이 있어 spec 이 이긴다)

## 구현 요약

알림을 누르면 **알림 종류에 맞는 화면으로 이동**한다. 로그인이 안 돼 있으면 딥링크를 버리지 않고
들고 있다가 **로그인 완료 시점에 원래 목적지로** 보낸다.

파이프라인은 한 방향이다:

```
알림 탭 → MainActivity(onCreate | onNewIntent) → PushEvent.from(intent.extras)
       → PushEventBus(:core:push, StateFlow) → MainViewModel(인증 게이트)
       → MainRoute → MainNavigator(switchTab | navigateTo)
```

## 사용한 모바일 레포 스킬

- `test-viewmodel`: `MainViewModelTest` 를 그 규약대로 작성 — `Dispatchers.setMain(UnconfinedTestDispatcher())` / `@BeforeTest`·`@AfterTest resetMain()` / Turbine `test { }` / `runTest`. 구독이 먼저 서도록 `setAuthenticatedArea`·`emit` 을 전부 `pushNavigation.test { }` 블록 **안에서** 호출했다.
- `viewmodel`: `MutableStateFlow` + `.update { }` (`.value =` 미사용), 일회성 이동은 `MutableSharedFlow(extraBufferCapacity = 1)`.
- 코드 편집은 전부 `cd challenge-app && claude -p` child 위임 (`.claude/agents/mobile-dev.md` "코드 편집 흐름"). 분석·API 확인·빌드/테스트는 본체.

## 🔴 spec 이 지적한 설계 결함 3건을 어떻게 반영했나

### 결함 1 — `CHALLENGE_REQUEST` 누락 (spec §0.2)

`PushEvent` 를 **3종 전부**로 정의했다: `ChallengeRequest` / `ChallengeAccepted` / `ChallengeRejected`.
원본 설계대로 2종만 만들었으면 **실기 발화 8회 중 5회를 차지한 `CHALLENGE_REQUEST` 에서
`from` 이 null 을 반환**해, 크래시 없이 조용히 홈에만 머무는 형태로 실패했을 것이다.

`PushEventTest` 가 3종을 각각 고정하고, `MainViewModelTest` 가 3종의 목적지를 각각 고정한다.

### 결함 2 — `challengeId` 를 전역 필수로 두면 확장 시 조용히 깨진다 (spec §0.1)

전역 `?: return null` 을 **쓰지 않았다.** 조회는 한 번 하되 **필수 판정은 타입별 분기 안**에 있다:

```kotlin
fun from(data: Map<String, String>): PushEvent? {
    val challengeId = data[KEY_CHALLENGE_ID]?.toLongOrNull()

    return when (data[KEY_TYPE]) {
        TYPE_CHALLENGE_REQUEST -> challengeId?.let(::ChallengeRequest)
        TYPE_CHALLENGE_ACCEPTED -> challengeId?.let(::ChallengeAccepted)
        TYPE_CHALLENGE_REJECTED -> challengeId?.let(::ChallengeRejected)
        else -> null
    }
}
```

`challengeId` 없는 타입(친구 요청 계열 등)이 붙으면 **그 분기만 `challengeId` 를 안 보면 된다** —
다른 분기를 건드리지 않는다. 서버가 `referenceId == null` 일 때 `challengeId` 키를 통째로 빼는
규약(`FcmNotificationSender.send()` 의 `message.referenceId?.let { putData(...) }`)과 정확히 맞물린다.

> `else -> null` 은 **파싱 실패 처리**이지 목적지 매핑이 아니다. 금지된 것은
> `toRoute()` 의 `else` 이고, 거기엔 없다 (아래 참조).

### 결함 3 — 백엔드 요청 1·2·3번은 이미 확정 (spec §0)

실기기 로그로 키 이름을 판별하는 작업은 **하지 않았다.** `data.type` = `NotificationType.name`,
`data.challengeId` = `referenceId.toString()` 를 확정 전제로 파서를 작성했다.
근거는 `FcmNotificationSender.send()` / `DATA_KEY_TYPE` / `DATA_KEY_CHALLENGE_ID` 실측 +
[push-fcm/api-contract.md §3](../push-fcm/api-contract.md)
(`confirmed`). backend-dev 에게는 이번 T-B1 에서 이 두 키를 건드리지 않는지 통지만 요청했다.

## 🔴 `CHALLENGE_ACCEPTED → Detail` — **판정 그대로 유지한다**

spec §1 판정 1 이 걸었던 실측 조건은 **[spec §1.1](./spec.md) 에서 pm-lead 가 직접 해소했다**
(2026-08-08). 조건의 전제였던 *"Error 로 떨어질 가능성이 높다"* 가 틀렸다는 정정이고,
**mobile-dev 가 별도로 확인할 필요가 없다**는 것이 그 결론이다.

아래는 내가 독립적으로 확인한 것으로, §1.1 과 같은 결론에 도달했고 근거가 하나 더 있다.
**Detail 로 보내도 Error 로 떨어지지 않는다.**

**근거 1 — 서버 경로에 status 게이트가 없다.** (§1.1 과 같은 발견) `ChallengeDetailService.getDetail()` 의 거절 조건은
두 개뿐이다: 챌린지 부재(`MSG_NOT_FOUND`), 당사자 아님(`MSG_NOT_MINE`). `ChallengeStatus` 를 보지
않는다. `CHALLENGE_ACCEPTED` 의 수신자는 **신청자(challenger)** 이고 당연히 당사자이므로 통과한다.

**근거 2 — 알림이 나가는 그 시점에 계약서가 이미 완결돼 있다.** `ChallengeCommandService.accept()` 는
한 트랜잭션 안에서 ① `contract.copy(isFinalized = true, opponentSignatureData = …)` 저장 →
② `status = IN_PROGRESS` + `opponentMission` 채움 → ③ verification 2건 → ④ **그 다음에야**
`publishNotification(CHALLENGE_ACCEPTED)` 를 부른다. 즉 알림이 존재한다는 것 자체가
**양측 서명 + `isFinalized = true` + `opponentMission` non-null 이 이미 커밋됐다는 뜻**이다.

**근거 3 — 그 상태의 매핑이 이미 테스트로 고정돼 있다.** `ChallengeDetailViewModelTest` 의 기본
픽스처가 정확히 이 상태(양측 서명 + `isFinalized = true`)이고, `양측 서명이 완료되면 두 서명이
모두 있고 계약이 완결로 온다` / `계약서가 있으면 서명 묶음이 채워진다` 가 `Data` 전이를 단언한다.
이번 실행에서 **14/14 passed** (아래 테스트 결과).

**근거 4 (§1.1 이 추가로 지목) — `contract` 가 nullable 이고 모바일 대응이 이미 있다.**
`ChallengeDetailResponse.contract: ContractDto?` 이고, 모바일 `ChallengeDetailViewModel` 은
`contract?.toSignatureSection(...)` 로 **없으면 서명 묶음만 비운다**(커밋 `a298125`).
`ACCEPTED` 경로에서는 애초에 null 이 아니지만, **null 이어도 Error 가 아니다.**

⚠️ **한계를 명시한다**: 위 4건은 **코드 경로 + 단위 테스트 수준의 실측**이다. **실기기에서 실제로
알림을 눌러 Detail 이 뜨는 것을 본 것은 아니다** (T-I1 미실시, 아래 참조). 다만 Error 로 떨어질
경로가 서버·모바일 양쪽에 존재하지 않는다는 것까지는 확인했다.

### 최종 목적지 매핑 (구현된 것)

| 타입 | 목적지 | 비고 |
|---|---|---|
| `CHALLENGE_REQUEST` | `Route.Home` | 수락/거절 액션이 홈 상단 "받은 도전장" 섹션에만 있다 |
| `CHALLENGE_ACCEPTED` | `Route.Challenge.Detail(challengeId)` | **판정 유지** (위 실측) |
| `CHALLENGE_REJECTED` | `Route.Home` | 계약서가 없어 **빈 계약서를 보여주게 된다.** ⚠️ *"Error 로 떨어진다"* 가 아니다 — [spec §1.1](./spec.md) 정정 |

> ⚠️ **`CHALLENGE_REJECTED` 의 근거를 정정해 옮겼다.** spec 최초 판정문의 *"Error 상태로 떨어질
> 가능성이 높다"* 는 §1.1 에서 **틀린 것으로 확인됐다.** 서버가 상태를 보지 않으므로 REJECTED 도
> 200 이 나온다. 결론(Home)은 유지하되 판단 축은 **안정성이 아니라 UX** 다.

`toRoute()` 는 sealed 에 대한 exhaustive `when` 이고 **`else ->` 가 없다.** 새 타입을 `PushEvent` 에
추가하면 이 지점이 컴파일 에러를 내 목적지 지정을 강제한다 (spec 판정 2 수용 기준).

## 변경된 파일

**신규 (8)**

| 경로 | 역할 |
|---|---|
| `core/push/src/commonMain/kotlin/com/lwg/challenge/push/PushEvent.kt` | sealed interface 3종 + `from(Map)` 파서 + `KEY_TYPE`/`KEY_CHALLENGE_ID`/`KEYS` |
| `core/push/src/commonMain/kotlin/com/lwg/challenge/push/PushEventBus.kt` | pending 딥링크 보관 (`StateFlow`) |
| `core/push/src/commonMain/kotlin/com/lwg/challenge/push/di/PushModule.kt` | `pushModule` — Koin 수동 등록 |
| `core/push/src/commonTest/kotlin/com/lwg/challenge/push/PushEventTest.kt` | 파싱 9건 |
| `feature/main/src/commonTest/kotlin/com/lwg/challenge/feature/main/MainViewModelTest.kt` | 인증 게이트 + 목적지 + pending 소거 **9건** |
| `feature/main/src/commonTest/.../FakeLoginRepository.kt` | `LogoutUseCase` 조립용 |
| `feature/main/src/commonTest/.../FakeUserInfoRepository.kt` | 〃 |
| `feature/main/src/commonTest/.../FakePermissionManager.kt` | `PermissionManager` 스텁 (`@Composable Bind()` 빈 구현) |

**편집 (7)**

| 경로 | 변경 |
|---|---|
| `core/push/build.gradle.kts` | `commonTest.dependencies { kotlin.test }` (이 모듈 첫 테스트 소스셋) |
| `feature/main/build.gradle.kts` | `implementation(projects.core.push)` + commonTest 3종(kotlin.test / coroutines.test / turbine) |
| `feature/main/.../MainViewModel.kt` | `pushEventBus` 주입, `combine(pending, _isAuthenticatedArea)` 게이트, `pushNavigation`, `setAuthenticatedArea`, 파일 하단 `toRoute()`, `loggedOut` 에 `consume()` |
| `feature/main/.../MainScreen.kt` | `setAuthenticatedArea(isAuthenticatedArea)` 전달 + `pushNavigation` 수집(탭 루트면 `switchTab`, 아니면 `navigateTo`) |
| `composeApp/.../commonMain/App.kt` | `pushModule` 등록 |
| `composeApp/.../androidMain/MainActivity.kt` | `onCreate`/`onNewIntent` intent 파싱 → 버스, `removeExtra` |
| `composeApp/.../androidMain/push/ChallengeFirebaseMessagingService.kt` | `contentIntent` extras 키·타입 통일, `EXTRA_*` 상수 삭제, `buildNotificationId` KDoc |

`git diff --stat`: 편집 7파일. 신규 8파일은 untracked.

### T-M3 — `onNewIntent` 와 `removeExtra`

spec 이 🔴로 지목한 두 지점을 모두 넣었다.

- `onNewIntent` **있다.** `MainActivity` 가 매니페스트에서 `android:launchMode="singleTask"` 라 앱 생존 중 알림 탭은
  `onCreate` 가 아니라 여기로 온다. 없으면 **그 경로가 통째로 무반응**이 된다.
- `PushEvent.KEYS.forEach(intent::removeExtra)` 로 소비 즉시 extras 를 지운다. 화면 회전으로
  Activity 가 재생성되면 같은 intent 를 다시 읽어 재이동하기 때문이다.
- `by inject()` 는 **koin-android 가 아니라 `org.koin.core.component.KoinComponent`** 를 썼다.
  composeApp androidMain 에 koin-android 의존이 없고, `ChallengeFirebaseMessagingService` 가 이미
  같은 방식을 쓰는 선례가 있다. **build.gradle.kts 에 새 의존을 추가하지 않았다.**

### T-M4 — 파서를 한 벌로 유지하는 지점

`contentIntent` 가 `data.forEach { (key, value) -> putExtra(key, value) }` 로 **원본 키·String 값
그대로** 싣는다. FCM 이 백그라운드에서 만드는 런처 인텐트와 extras 모양이 같아져 `MainActivity` 는
포그라운드/백그라운드 구분 없이 파서를 한 벌만 유지한다. **나중에 data-only 페이로드로 전환해도
앱 코드가 그대로**라는 근거가 이 지점이다 (spec 판정 4 — 보류이지 폐기 아님).

`EXTRA_NOTIFICATION_TYPE` / `EXTRA_CHALLENGE_ID` 는 삭제했다. **레포 전체 grep 결과 다른 참조 0건**
(선언 2줄 + 같은 파일 내 사용 2줄이 전부였다). 키 문자열의 단일 출처는 이제 `:core:push` 의
`PushEvent.KEY_CHALLENGE_ID` 하나다 — 서비스도 알림 id 를 만들 때 그것을 쓴다.

### T-M4 추가 — `buildNotificationId` KDoc (pm-lead 추가 배정, 2026-08-08)

같은 파일의 `buildNotificationId` 에 **포그라운드/백그라운드 묶음 키가 왜 같아야 하는지**를 KDoc 으로
남겼다. 서버는 `android.notification.tag = "challenge-{referenceId}"` 로 백그라운드 트레이 묶음을
정하고 앱은 이 함수의 Int id 로 포그라운드 묶음을 정하는데, **전달 경로도 값 타입도 다르지만 논리
키가 `challengeId` 로 같아서** 지금 동작이 일치한다. null 처리 방향까지 일치한다 — 서버는
`android.notification` 블록을 빼고 앱은 `currentTimeMillis` 를 쓴다. 둘 다 *"묶지 않고 각각 쌓는다"* 다.
🔴 **이 키를 바꾸면 묶음 단위가 갈라지고 크래시도 로그도 없이 조용히 어긋난다** — 이것이 KDoc 을
남긴 이유다. 본문 코드는 무변경, 컴파일 재확인 완료(`BUILD SUCCESSFUL`, `EXIT=0`).

## 테스트 결과

**신규 — Android `testDebugUnitTest`**

| 스위트 | 결과 | XML timestamp (KST) |
|---|---|---|
| `PushEventTest` (`:core:push`) | **9/9 passed** (failures 0, errors 0, skipped 0) | 2026-08-08 18:22:44 |
| `MainViewModelTest` (`:feature:main`) | **9/9 passed** (failures 0, errors 0, skipped 0) | 2026-08-08 18:38:32 |

> `MainViewModelTest` 는 pending 소거 케이스 추가로 **8 → 9** 가 됐다. XML 의 `testcase` 목록에
> `로그아웃하면 대기 중이던 pending 이 소거되어 다음 인증에서 재방출되지 않는다` 가 **실제로 실려
> 있는 것을 확인**했다 — 추가만 하고 안 돌린 것이 아니다.
> `PushEventTest` 는 `:core:push` 입력이 안 바뀌어 `UP-TO-DATE` 였고 **이번 실행에서 다시 돌지
> 않았다**(timestamp 18:22:44 유지). 그대로 적는다.

**신규 — iOS `iosSimulatorArm64Test`** (commonMain 코드라 iOS 타깃에서도 돈다)

| 스위트 | 결과 | XML timestamp (KST) |
|---|---|---|
| `PushEventTest` | **9/9 passed** | 2026-08-08 18:24:03 |
| `MainViewModelTest` | **9/9 passed** | 2026-08-08 18:39:30 |

> ⚠️ **stale 여부를 확인했다.** `PushEventTest` iOS XML 은 mtime 18:24 로 첫 실행 구간(18:23~18:25)
> 안이고, `MainViewModelTest` iOS XML 은 pending 소거 반영 후 재실행분(mtime 18:39)이며 새 테스트
> 이름이 XML 안에 실려 있다. 과거 실행 결과를 재보고한 것이 아니다.
> `push-fcm` 이후 누적돼 있던 **"iOS 단위 테스트 미실행" 항목이 이 두 모듈에 한해 해소**됐다.

**전체 회귀 — Android `testDebugUnitTest` (전 모듈)**

- **267/267 passed, failures 0, errors 0, skipped 0**
- 🔴 **이 숫자가 어떻게 나왔는지 정확히 적는다.** 전 모듈 일괄 실행은 **18:25 에 1회**(266건, main 8)
  했고, 그 뒤 pending 소거 반영으로 **`:feature:main` 만 재실행**해 9건이 됐다(18:38). 즉
  **267 은 한 번의 전체 실행에서 나온 수가 아니라 최신 모듈별 XML 을 합산한 값**이다.
  전 모듈을 한 번에 다시 돌리지는 않았다.
- 18:25 회차에서 **실제로 실행된 것은 131건**(composeApp 1 / core:push 9 / core:ui 4 /
  challenge:create 20 / challenge:detail 14 / challenge:oath 17 / friends:list 11 / friends:search 12 /
  home 20 / login 15 / main 8), 나머지 **135건은 `UP-TO-DATE`** — 입력이 안 바뀐 모듈
  (core:utils 28 / data:repositoryImpl 14 / remote:datasource 22 / remote:mapper 58 /
  remote:model 6 / remote:network 7)이라 gradle 이 건너뛰었고 XML timestamp 가 2026-08-07 이다.
  **이번에 돌지 않았다는 뜻이므로 그대로 적는다.**
- pending 소거 변경의 영향 범위는 `:feature:main` commonMain/commonTest 뿐이고,
  `:composeApp:compileDebugKotlinAndroid` 로 하위 소비처 컴파일까지 확인했다.
- `ChallengeDetailViewModelTest` **14/14 passed** — 위 "Detail 실측" 근거 3.

**빌드 검증**

| 태스크 | 결과 |
|---|---|
| `:core:push:compileCommonMainKotlinMetadata` | ok |
| `:feature:main:compileCommonMainKotlinMetadata` | ok |
| `:composeApp:compileDebugKotlinAndroid` | ok |
| `BUILD SUCCESSFUL` / `GRADLE_EXIT_CODE=0` | 1m 29s |

경고는 전부 기존 것(`materialIconsExtended` deprecation, `@Preview` deprecation)이고 **신규 경고 0건**.

## 🔴 실기기 검증 (T-I1) — **하지 않았다**

- **실기기 5케이스(포그라운드 / 백그라운드 앱 생존 / 앱 종료 / 로그아웃 상태 탭 / 화면 회전)를
  단 하나도 실행하지 않았다.** 이 세션에 기기·에뮬레이터도, 기동 중인 백엔드·FCM 자격증명도 없다.
- 위 표의 결과는 **전부 단위 테스트와 컴파일**이다. 추정으로 통과 처리한 항목은 없다.
- spec 이 "이번 설계의 핵심"으로 지목한 **로그아웃 상태 탭 / 화면 회전** 두 케이스가 미검증분에
  포함된다. 단위 테스트가 게이트 로직(`로그아웃으로 인증 영역을 벗어나면 게이트가 닫힌다`)과
  `KEYS` 완전성은 고정하지만, **`intent.removeExtra` 가 실제 Activity 재생성에서 먹는지**는
  단위 테스트 밖이다.
- tag 중복 제거는 backend-dev 의 T-B1 배포 후에만 볼 수 있다. 계약서 §3.1 에는 이미
  `tag = "challenge-{referenceId}"`(referenceId null 이면 `android.notification` 블록 자체 생략)로
  등재돼 있으나, **모바일은 tag 를 읽지 않으므로 코드 영향 0**이다.

## Working tree 상태

- **작업 브랜치: `main`** (현재 체크아웃돼 있던 브랜치. 새로 만들지 않았다)
- 변경분은 **staged/unstaged 그대로** 두었다. **커밋·푸시·PR 생성 안 함** — 사용자 처리 영역.
- 편집 7파일 `M`, 신규 8파일 `??` (`core/push/src/commonTest/`, `feature/main/src/commonTest/` 디렉터리 포함).

## 미해결 이슈

- [ ] 🔴 **T-I1 실기 검증 미실시** — 위 절 전체. 이 feature 의 수용 기준 7개 중 실기로만 확인
      가능한 것(3경로 동일 동작 / 회전 재소비 / 트레이 1건)이 **전부 미확인**이다.
- [ ] 🟡 **프로세스 사망 후 딥링크 중복 소비** — spec 판정 4 에서 **승인된 미방지**다.
      `intent.removeExtra` 는 메모리상의 `Intent` 객체만 고치므로, 프로세스가 죽고 시스템이 저장한
      원본 intent 가 복원되면 extras 가 살아 있다. 필요해지면 `SavedStateHandle` 에 소비 여부를 남긴다.
- [x] ✅ **로그아웃 시 pending 이 남는다 — 고쳤다** (pm-lead 승인, 2026-08-08). 아래 절 참조.
- [ ] 🟢 **iOS 는 여전히 알림을 못 받는다** — 파서·버스·게이트는 commonMain 이라 iOS 에서도 컴파일·
      테스트가 돌지만(위 결과), **`PushEvent` 를 iOS 에서 버스에 넣어 주는 진입점이 없다.**
      APNs 인증키가 유료 Apple Developer 계정에서만 나오는 [push-fcm 🔵](../push-fcm/summary.md)이
      풀리기 전까지는 만들 근거가 없다. iOS 진입점 하나만 붙이면 나머지는 그대로 쓴다.
- [ ] 🟢 **알림 여러 개 연속 탭 시 마지막 것만 남는다** — `StateFlow` 라 의도된 동작이다
      (설계 문서 5절). 기록만.

## T-M2 추가 — 로그아웃 시 pending 소거 (pm-lead 승인, 2026-08-08)

내가 미해결로 올린 🟡 항목을 pm-lead 가 **"고쳐라"로 판정**해 반영했다.

`PushEventBus.pending` 은 **세션 소유물인데 로그아웃 때 비워지지 않았다.** 게이트가 닫혀 이동은
막히지만 값이 남아, **그 기기에서 다음 사람이 로그인하는 순간 앞사람의 딥링크로 이동**한다.

```kotlin
val loggedOut: Flow<Unit> = merge(authEventBus.sessionExpired, _logoutRequested)
    .onEach {
        logoutUseCase()
        // 대기 중인 딥링크는 세션 소유물이라 함께 버린다. …
        pushEventBus.consume()
    }
```

`pushEventBus` 를 `private val` 로 승격한 것 외에 다른 변경은 없다 — `init` 의 combine 게이트,
`toRoute()`, `setAuthenticatedArea()`, `requestNotificationPermission()` 전부 무변경.

**"가정에 방어 로직을 넣지 않는다"에 걸리지 않는 이유** (pm-lead 판정 근거):
새 방어물을 덧대는 게 아니라 **방금 만든 코드의 상태 누수**를 막는 것이고, 유발 조건인
`dev-test-login` 계정 전환이 **이 프로젝트의 표준 검증 방식**이라 가정이 아니라 일상이다.
`push-fcm` 결정사항 2번(토큰 소유권 이전)이 같은 구조로 도입돼 실기에서 *"실사용 증명됨"* 으로
닫힌 선례가 있다.

⚠️ **증상 수위를 정확히 적는다 — 데이터 유출이 아니다.** 다음 사람이 앞사람의
`Detail(challengeId)` 로 가더라도 서버 `ChallengeDetailService` 가 *"당사자만 볼 수 있다"* 로 막아
`SnackbarException` 이 뜬다. 실제 증상은 **"로그인했더니 난데없는 화면 + 에러 스낵바"** 이고,
유출이 아니라 혼란이다. 그래도 고칠 값어치가 있다는 것이 판정이다.

**테스트 1건 추가** — `로그아웃하면 대기 중이던 pending 이 소거되어 다음 인증에서 재방출되지 않는다`.
기존 `로그아웃으로 인증 영역을 벗어나면 게이트가 닫힌다` 는 **게이트**를 고정하는 별개 단언이므로
그대로 뒀다. 🔴 이 테스트는 `loggedOut` 이 **cold Flow** 라는 함정을 정면으로 다룬다 — 수집하지
않으면 `onEach` 가 아예 돌지 않아 테스트가 조용히 무의미해지고, `_logoutRequested` 는 replay 가
없어 구독 전에 부른 `logout()` 은 영영 오지 않는다. Turbine 이 구독을 세운 뒤 `logout()` 을 부른다.

## backend-dev 실측 회신 (2026-08-08) — 파서 전제 3건 확정

내가 보낸 확인 요청에 backend-dev 가 **파일 실측으로** 답했다. 세 건 다 내 전제와 일치한다.

| 확인 항목 | 회신 |
|---|---|
| tag 형식 | `tagFor(referenceId) = referenceId?.let { "challenge-$it" }`. `null` 이면 `AndroidNotification` 자체를 안 붙인다. `AndroidConfig`(`priority = HIGH`)는 항상 붙고 **tag 만 조건부** |
| `data.type` | `putData("type", message.type.name)` — 무변경 |
| `data.challengeId` | `message.referenceId?.let { putData("challengeId", it.toString()) }` — `null` 이면 키 자체 없음. **내 타입별 분기 판정(spec §0.1)이 이 코드와 정확히 맞물린다** |

### 🔴 backend-dev 가 알려준 추가 사실 — 지금은 3종 외 도착이 **구조적으로 불가능**하다

나머지 5종(`REMIND` / `OPPONENT_VERIFIED` / `RESULT` / `TAUNT` / `FRIEND_REQUEST`)은
**`NotificationMessages.of()` 가 `null` 을 반환해 `NotificationDispatcher` 가 row 저장도 발송도
건너뛴다.** 즉 오늘 기준 모르는 type 이 앱에 도달할 경로가 없다.

**그래도 `else -> null` 방어는 유지한다.** 문구가 추가되는 순간 즉시 도달 가능해지고,
**그 변경은 서버 파일 하나(`NotificationMessages`)를 고치는 것으로 일어난다.**
모바일이 모르는 사이에 전제가 바뀔 수 있는 구조라는 뜻이다.

### 🟡 pm-lead 에 올리는 제안 — "새 타입 발송 개시 전 모바일 통지" 를 계약에 명문화

backend-dev 가 *"나에게만 의존하지 마라 — 그 파일을 고치는 사람이 내가 아닐 수 있다.
계약에 명문화하는 게 사람 기억보다 안전하다"* 고 직접 짚었다. **동의한다.**
자리는 [push-fcm/api-contract.md §0.6](../push-fcm/api-contract.md)(알림 타입 재정의)이 맞다고 본다.
🔴 **다만 계약서는 backend-dev 소유이고 배정은 pm-lead 경로이므로, 내가 고치지 않고 제안만 남긴다.**

### 참고 — 알림 문구 톤이 3종 사이에 갈려 있다 (버그 아님)

`CHALLENGE_REQUEST` 는 2026-08-07 사용자 확정본(`"영혼의 맹세"` / `"{닉네임}님이 당신과 계약하고
싶습니다"`, 격식)이고 `ACCEPTED` / `REJECTED` 는 초안(반말)이 그대로다.
실기 검증 스크린샷에 그대로 찍힐 것이므로 **결함으로 보고하지 않는다.**
[push-fcm summary 의 🟢 "알림 문구 톤 불균일"](../push-fcm/summary.md) 과 같은 항목이다.

## API 계약 대비 구현 차이

**없다.** 요청/응답 shape 변경 0, 페이로드 규약도 [push-fcm/api-contract.md §3](../push-fcm/api-contract.md)
그대로다. 모바일이 읽는 것은 `data.type` / `data.challengeId` 두 키뿐이고,
backend-dev 가 이번에 추가한 `android` 블록(`priority` / `notification.tag`)은
**시스템 트레이가 소비하고 앱에 전달되지 않으므로 모바일 파서는 무접촉**이다 (§3.1 문구와 일치).
