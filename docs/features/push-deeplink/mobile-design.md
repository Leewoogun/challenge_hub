# FCM 푸시 알림 딥링크 설계

> ⚠️ **이 문서는 mobile-dev 가 작성한 원본 설계이며, PM 판정 전 상태로 보존한다.**
> "1. 협의 필요 항목" 의 5건 중 3건은 이미 확정된 사안이고, 대상 알림 종류에 누락이 있다.
> **구현 시 실제 기준은 [spec.md](./spec.md) §0~§1 이다.** 두 문서가 어긋나면 spec.md 가 이긴다.

- 작성일: 2026-08-08
- 범위: Android (iOS 는 동일 구조로 확장 가능하게 설계)
- 현재 대상 알림: 챌린지 신청 수락 / 거절
- 향후 확장: 친구 요청 수락 / 거절

## 요약

푸시 알림을 누르면 알림 종류에 맞는 화면으로 이동한다. 로그인이 되어 있지 않으면
로그인 프로세스를 먼저 마친 뒤 원래 목적지로 이동한다.

알림 종류는 **"무슨 일이 일어났는가"(이벤트) 기준**으로 정의하고, 어느 화면으로 갈지는
앱이 결정한다. 서버는 목적지를 알 필요가 없다.

---

## 1. 협의 필요 항목

> 이 절만 PM / 백엔드에 전달해도 됩니다. 나머지는 앱 구현 상세입니다.

### 1-1. 백엔드 요청

최종 페이로드 형태 (FCM HTTP v1):

```json
{
  "message": {
    "token": "<device-token>",
    "notification": {
      "title": "도전장이 수락되었어요",
      "body": "홍길동님이 도전장을 수락했습니다"
    },
    "data": {
      "type": "CHALLENGE_ACCEPTED",
      "challengeId": "7"
    },
    "android": {
      "priority": "high",
      "notification": { "tag": "challenge-7" }
    }
  }
}
```

| # | 항목 | 내용 | 우선순위 |
|---|---|---|---|
| 1 | `data.type` **신규 추가** | `CHALLENGE_ACCEPTED` / `CHALLENGE_REJECTED`. 백엔드 enum 이름과 동일한 문자열로 합의 | 필수 |
| 2 | `data.challengeId` **키 이름 확인** | 앱 코드가 이 키를 가정하고 있으나 검증된 바 없음. 실제 전송 키 확인 필요 | 필수 |
| 3 | `data` 동봉 보장 | `notification` 만 있고 `data` 가 빠지면 딥링크가 동작하지 않음 | 필수 |
| 4 | `android.notification.tag` 추가 | `"challenge-{challengeId}"`. 없으면 백그라운드에서 같은 도전장 알림이 계속 쌓임 | 권장 |
| 5 | 향후 이벤트 이름 사전 합의 | 친구 요청/수락/거절 타입 문자열 | 참고 |

**2번이 가장 시급하다.** 키 이름이 실제와 다르면 현재도 알림 중복 제거가 동작하지 않고 있을
것이고, 딥링크를 붙여도 그대로 동작하지 않는다. 실기기에서 알림을 한 번 받아 로그를 확인하면
바로 판별된다 (`ChallengeFirebaseMessagingService` 가 `data` 를 통째로 로깅 중).

`data.type` 은 정수가 아니라 **문자열**로 요청한다. 정수를 쓰면 백엔드가 `11` 과 `12` 를
바꿔 보내도 양쪽 모두 알아채지 못한다. 문자열이면 Firebase 콘솔 테스트 발송과 로그에서
바로 읽힌다.

### 1-2. PM 확인

1. **각 알림의 목적지** — 현재 설계는 수락/거절 모두 홈이다. 다만 `Route.Challenge.Detail(challengeId)`
   가 이미 존재하므로, "수락되었어요" 알림은 해당 도전장 상세로 바로 보내는 편이 자연스러울 수 있다.
   홈이 맞는지 확인 필요.
2. **이벤트 목록 확정** — 현재 수락/거절 두 종류뿐인지, "도전장이 도착했어요" 같은 알림도 있는지.
3. **같은 도전장 알림 중복 정책** — 하나로 덮어쓸지, 각각 쌓을지. 1-1 의 4번 항목이 여기서 갈린다.

### 1-3. 이번 범위에서 제외한 것

- **data-only 페이로드 전환** — 현행 `notification` + `data` 동시 발송을 유지한다. data-only 로
  가면 포그라운드/백그라운드 동작이 완전히 일치하고 알림함 저장·푸시 설정 존중 같은 후속 기능이
  자연히 따라오지만, 사용자가 앱을 강제 종료한 상태에서 알림이 도달하지 않는 대가가 있다.
  이번 범위는 딥링크뿐이므로 유지하고, 알림함 기능을 붙일 때 재검토한다.
  앱 코드는 어느 쪽이든 파서 하나만 유지되므로 나중에 전환해도 손해가 없다.
- **프로세스 사망 후 재복원 시 딥링크 중복 소비 방지** — 아래 5절 참조.

---

## 2. 배경

### 2-1. Android FCM 의 전경/배경 동작 차이

| 페이로드 | 포그라운드 | 백그라운드 / 앱 종료 |
|---|---|---|
| `notification` 포함 | `onMessageReceived` 호출 → 앱이 직접 알림 표시 | **`onMessageReceived` 호출되지 않음.** FCM SDK 가 시스템 트레이에 직접 표시 |
| `data` 만 | 호출됨 | 호출됨 (앱 강제 종료 상태 제외) |

현재 앱은 `notification` 페이로드를 전제로 하므로 백그라운드에서는 앱 코드가 실행되지 않는다.
매니페스트에 채널 id 와 아이콘 meta-data 가 설정되어 있어 **알림 겉모습은 양쪽이 사실상 동일**하다
(FCM SDK 도 body 에 `BigTextStyle` 을 적용한다).

실제로 갈리는 지점은 두 개다.

**알림 중복 처리** — 앱이 그릴 때는 `challengeId` 를 알림 id 로 써서 같은 도전장 알림이 덮어쓰이지만,
FCM 이 그릴 때는 `gcm.n.tag` 가 없으면 `"FCM-Notification:" + SystemClock.uptimeMillis()` 를
tag 로 써서 매번 새 알림이 쌓인다.

**클릭 시 전달되는 데이터** — FCM 은 런처 인텐트에 `paramsWithReservedKeysRemoved()` 결과를
넣으므로 **`data` 의 원래 키가 그대로, 값은 전부 String** 으로 들어온다. 앱이 만드는 `contentIntent`
가 다른 키·타입을 쓰면 경로별로 파서를 두 벌 유지해야 한다.

### 2-2. 해결 방침

앱이 만드는 `contentIntent` 의 extras 키·타입을 **FCM 이 백그라운드에서 넣는 것과 동일하게** 맞춘다.
그러면 파서가 하나로 끝나고, 나중에 data-only 로 전환해도 앱 코드가 그대로 유지된다.

---

## 3. 아키텍처

```
[알림 탭]
   │
   ▼
MainActivity (composeApp/androidMain)
   onCreate / onNewIntent  →  intent.extras 를 Map<String, String> 으로
   PushEvent.from(data)    →  파싱 실패(모르는 type)면 여기서 버림
   intent.removeExtra(...) →  회전·재생성 시 재소비 방지
   │
   ▼
PushEventBus (:core:push, Koin 싱글톤)
   _pending: MutableStateFlow<PushEvent?>
   │
   ▼
MainViewModel (:feature:main, commonMain)
   combine(pushEventBus.pending, isAuthenticatedArea)
       둘 다 준비되면 → consume() → Route 로 매핑해 방출
   │
   ▼
MainRoute → MainNavigator (탭 루트면 switchTab, 아니면 navigateTo)
```

### 3-1. 파일 배치

| 파일 | 모듈 | 역할 |
|---|---|---|
| `PushEvent.kt` | `:core:push` | sealed interface + `from(Map)` 파서 |
| `PushEventBus.kt` | `:core:push` | pending 딥링크 보관 |
| `PushModule.kt` | `:core:push` | `PushEventBus` Koin 등록 |
| `MainViewModel.kt` | `:feature:main` | 인증 게이트 + `PushEvent → Route` 매핑 |
| `MainScreen.kt` | `:feature:main` | 이동 수집 및 실행 |
| `MainActivity.kt` | `composeApp/androidMain` | intent 파싱 → 버스 |
| `ChallengeFirebaseMessagingService.kt` | `composeApp/androidMain` | `contentIntent` extras 키 통일 |
| `App.kt` | `composeApp/commonMain` | `pushModule` 등록 |
| `build.gradle.kts` | `:feature:main` | `implementation(projects.core.push)` 추가 |

`composeApp` 은 `platformPushModule` 을 이미 쓰고 있어 `:core:push` 의존이 있다.
새로 추가되는 것은 `:feature:main → :core:push` 하나뿐이다.

`PushEvent` 를 `:domain:model` 이 아니라 `:core:push` 에 두는 이유는, UseCase / Repository 어디에도
등장하지 않는 푸시 전송 계층의 개념이고, `:core:push` 가 이미 푸시 관심사를 소유하고 있어
새로 생기는 모듈 의존 간선이 `feature:main → core:push` 하나로 끝나기 때문이다.

`PushEvent → Route` 매핑을 `:core:navigation` 이 아니라 `:feature:main` 에 두는 이유는 현재
소비처가 한 곳뿐이기 때문이다. 알림 목록 화면에서도 같은 매핑이 필요해지면 그때 승격한다.

### 3-2. 차주앱(CarOwnerRenew) 대비 차이

기본 골격은 차주앱 `MainViewModel` 의 `combine(_pendingFcmType, _isLoginComplete)` 패턴과 같다.
두 지점이 다르다.

**pending 을 ViewModel 이 아니라 Bus 가 보관한다.** 차주앱은 `MainActivity` 가 `feature:main`
안에 있어 ViewModel 을 직접 참조하지만, 이 프로젝트는 `MainActivity`(androidMain) 와
`MainViewModel`(commonMain) 사이에 KMP 경계가 있다. `:core:utils` 의 `AuthEventBus` 와 같은
패턴으로 버스를 둔다. `SharedFlow` 가 아니라 `StateFlow` 인 이유는 `onCreate` 시점에 ViewModel 이
아직 구독 전일 수 있어서다.

**`checkLoginComplete()` 에 해당하는 신호를 새로 만들지 않는다.** `MainRoute` 에 이미
같은 의미의 `isAuthenticatedArea` 가 있다.

```kotlin
// MainScreen.kt — 기존 코드
val isAuthenticatedArea = backStack.lastOrNull().let {
    it != null && it !is Route.Splash && it !is Route.Login
}
```

자동 로그인과 수동 로그인이 같은 지점을 지나고, **로그아웃하면 자동으로 `false` 로 되돌아간다.**
차주앱은 이 되돌리기가 없어 로그아웃 후에도 `_isLoginComplete` 가 `true` 로 남는다.

---

## 4. 구현

### 4-1. PushEvent

```kotlin
// :core:push commonMain
sealed interface PushEvent {

    data class ChallengeAccepted(val challengeId: Long) : PushEvent
    data class ChallengeRejected(val challengeId: Long) : PushEvent

    companion object {
        private const val KEY_TYPE = "type"
        private const val KEY_CHALLENGE_ID = "challengeId"

        val KEYS = listOf(KEY_TYPE, KEY_CHALLENGE_ID)

        // FCM data 는 값이 전부 문자열로 도착한다. 서버가 숫자로 보내도 여기선 "7" 이다.
        fun from(data: Map<String, String>): PushEvent? {
            val challengeId = data[KEY_CHALLENGE_ID]?.toLongOrNull() ?: return null
            return when (data[KEY_TYPE]) {
                "CHALLENGE_ACCEPTED" -> ChallengeAccepted(challengeId)
                "CHALLENGE_REJECTED" -> ChallengeRejected(challengeId)
                else -> null
            }
        }
    }
}
```

`challengeId` 를 필수로 두고 없으면 파싱을 실패시킨다. 알림 클릭 자체가 앱을 실행시키므로
파싱이 실패해도 앱은 열려 홈까지는 도달한다. 딥링크 분기만 타지 않을 뿐이다.

### 4-2. PushEventBus

```kotlin
// :core:push commonMain
class PushEventBus {
    private val _pending = MutableStateFlow<PushEvent?>(null)
    val pending: StateFlow<PushEvent?> = _pending.asStateFlow()

    fun emit(event: PushEvent) = _pending.update { event }
    fun consume() = _pending.update { null }
}

// AppModule 의 @ComponentScan 은 composeApp 패키지만 훑어 다른 모듈까지 닿지 않는다.
// platformPushModule 과 같은 방식으로 수동 등록한다.
val pushModule: Module = module {
    single { PushEventBus() }
}
```

`App.kt` 의 `challengeAppDeclaration` 에 `pushModule` 을 추가한다.

### 4-3. MainViewModel

```kotlin
@KoinViewModel
class MainViewModel(
    authEventBus: AuthEventBus,
    private val pushEventBus: PushEventBus,
    private val logoutUseCase: LogoutUseCase,
    private val permissionManager: PermissionManager,
) : ViewModel() {

    private val _isAuthenticatedArea = MutableStateFlow(false)

    private val _pushNavigation = MutableSharedFlow<Route>(extraBufferCapacity = 1)
    val pushNavigation: SharedFlow<Route> = _pushNavigation.asSharedFlow()

    init {
        viewModelScope.launch {
            // 알림이 먼저 와서 기다리든, 인증이 먼저 끝나 있든 상관없이 둘 다 준비된 시점에 이동한다.
            combine(pushEventBus.pending, _isAuthenticatedArea) { event, isReady ->
                event.takeIf { isReady }
            }.collect { event ->
                if (event == null) return@collect

                pushEventBus.consume()
                _pushNavigation.emit(event.toRoute())
            }
        }
    }

    fun setAuthenticatedArea(isAuthenticatedArea: Boolean) {
        _isAuthenticatedArea.update { isAuthenticatedArea }
    }
}

private fun PushEvent.toRoute(): Route = when (this) {
    is PushEvent.ChallengeAccepted -> Route.Home
    is PushEvent.ChallengeRejected -> Route.Home
}
```

`toRoute` 가 `sealed` 에 대한 `when` 이므로 새 이벤트를 추가하면 컴파일 에러로 목적지 지정이
강제된다. 이벤트 기준 타입 체계를 택한 실질적 이득이다.

### 4-4. MainRoute

```kotlin
LaunchedEffect(isAuthenticatedArea) {
    viewModel.setAuthenticatedArea(isAuthenticatedArea)
    if (isAuthenticatedArea) viewModel.requestNotificationPermission()
}

LaunchedEffect(viewModel) {
    viewModel.pushNavigation.collect { route ->
        if (backStack.lastOrNull() == route) return@collect

        // 탭 루트가 목적지면 백스택을 정리한다. 알림으로 홈에 왔는데 뒤로가기가
        // 이전에 보던 화면으로 돌아가면 어디서 온 건지 알 수 없다.
        if (BottomNavItem.find(route) != null) navigator.switchTab(route)
        else navigator.navigateTo(route)
    }
}
```

### 4-5. MainActivity

```kotlin
// org.koin.android.ext.android.inject
private val pushEventBus: PushEventBus by inject()

override fun onCreate(savedInstanceState: Bundle?) {
    // ... 기존 코드
    handlePushIntent(intent)
}

// launchMode=singleTask 라 앱이 살아 있을 때 알림을 누르면 onCreate 가 아니라 여기로 온다.
override fun onNewIntent(intent: Intent) {
    super.onNewIntent(intent)
    setIntent(intent)
    handlePushIntent(intent)
}

private fun handlePushIntent(intent: Intent?) {
    val extras = intent?.extras ?: return
    val data = extras.keySet()
        .mapNotNull { key -> extras.getString(key)?.let { key to it } }
        .toMap()

    val event = PushEvent.from(data) ?: return
    // 화면 회전으로 Activity 가 재생성되면 같은 intent 를 다시 읽어 재이동한다. 즉시 제거한다.
    PushEvent.KEYS.forEach(intent::removeExtra)

    pushEventBus.emit(event)
}
```

`onNewIntent` 가 없으면 **앱이 살아 있는 상태에서 알림을 눌렀을 때 아무 일도 일어나지 않는다.**

### 4-6. ChallengeFirebaseMessagingService

`contentIntent` 의 extras 를 FCM 백그라운드 경로와 동일한 키·타입으로 맞춘다.

```kotlin
private fun contentIntent(notificationId: Int, data: Map<String, String>): PendingIntent {
    val intent = Intent(this, MainActivity::class.java).apply {
        flags = Intent.FLAG_ACTIVITY_CLEAR_TOP
        // 백그라운드에서 FCM 이 넣어주는 extras 와 키·타입을 맞춘다.
        // 어긋나면 MainActivity 가 경로별로 파서를 두 벌 들고 있어야 한다.
        data.forEach { (key, value) -> putExtra(key, value) }
    }

    return PendingIntent.getActivity(
        this,
        notificationId,
        intent,
        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
    )
}
```

기존 `EXTRA_NOTIFICATION_TYPE` / `EXTRA_CHALLENGE_ID` 상수는 삭제한다.

---

## 5. 엣지 케이스

| 상황 | 동작 |
|---|---|
| 알림 여러 개 연속 탭 | `StateFlow` 이므로 마지막 것만 남아 마지막에 누른 알림으로 이동 |
| 로그인 전에 알림 탭 | pending 유지 → 로그인 완료 시점에 이동 |
| 로그아웃 | `isAuthenticatedArea` 가 `false` 로 떨어져 게이트가 자동으로 닫힘 |
| 앱이 살아 있을 때 알림 탭 | `onNewIntent` 경유, `isAuthenticatedArea` 가 이미 `true` 이므로 즉시 이동 |
| 모르는 `type` (구버전 앱) | `PushEvent.from` 이 `null` → 버스에 들어가지 않음. 앱은 정상적으로 열림 |
| 화면 회전 | `removeExtra` 로 재소비 방지 |
| 프로세스 사망 후 복원 | **같은 알림으로 한 번 더 이동할 수 있음** (아래 참조) |

`intent.removeExtra` 는 메모리상의 `Intent` 객체를 수정하므로, 프로세스가 죽고 시스템이 저장한
원본 intent 가 복원되면 extras 가 살아 있다. "알림으로 들어왔다가 앱이 죽어 재실행되는" 상황이라
다시 이동하는 편이 오히려 자연스러워 이번 범위에서는 방지하지 않는다. 필요해지면
`SavedStateHandle` 에 소비 여부를 남긴다.

---

## 6. 검증

### 6-1. 단위 테스트

**`PushEventTest`** (commonTest)
- 정상 파싱
- 모르는 `type` → `null`
- `challengeId` 누락 → `null`
- 숫자가 아닌 `challengeId` → `null`

**`MainViewModelTest`** (commonTest, Turbine) — `/test-viewmodel` 스킬 규약을 따른다
- 인증 완료 상태에서 알림 도착 → 즉시 `Route` 방출
- 알림 도착 후 인증 완료 → 인증 시점에 방출
- 방출 후 pending 이 소비되어 재방출 없음
- 미인증 상태에서는 방출 없음

### 6-2. 수동 검증 (실기기 필수)

Firebase 콘솔 테스트 메시지 또는 백엔드 스테이징으로 확인한다.

| 케이스 | 기대 |
|---|---|
| 포그라운드에서 알림 탭 | 즉시 홈으로 (이미 홈이면 변화 없음) |
| 백그라운드(앱 살아있음)에서 탭 | `onNewIntent` 경유, 즉시 홈으로 |
| 앱 종료 상태에서 탭 | 스플래시 → 자동 로그인 → 홈 |
| 로그아웃 상태에서 탭 | 스플래시 → 로그인 화면 → 로그인 완료 → 홈 |
| 화면 회전 후 | 같은 알림으로 재이동하지 않음 |

마지막 두 케이스가 이번 설계의 핵심이므로 반드시 실기기로 확인한다.

### 6-3. 빌드 검증

```bash
./gradlew :core:push:compileCommonMainKotlinMetadata
./gradlew :feature:main:compileCommonMainKotlinMetadata
./gradlew :composeApp:compileDebugKotlinAndroid
```
