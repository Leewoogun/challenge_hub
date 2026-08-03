# Mobile Report — dev-test-login

- **feature-id**: dev-test-login
- **작성**: 2026-07-31 by mobile-dev
- **상태**: implemented (working tree, **커밋 안 함**)
- **선행 입력**: [spec.md](./spec.md), [api-contract.md](./api-contract.md) (`confirmed`)
- **담당 태스크**: #16 (T-M1~T-M4) · #13 계약 co-assignee
- **검증**: Android 유닛 **148/148 passed, 0 failed** / Android·KMP common 빌드 **BUILD SUCCESSFUL** / iOS framework link **BUILD SUCCESSFUL**

## 구현 요약

가짜 계정 3개로 즉시 로그인하는 debug 전용 경로를 열었다. 목적은 **혼자서 친구 요청·수락, 챌린지 신청·수락을 왕복 검증**하는 것이다 — 지금까지 "실기기 시각 검증", "manual smoke"가 미해결로 쌓인 병목이 계정이 하나뿐이라는 것이었다.

인증 우회 경로라 **격리가 기능과 동등한 수용 기준**이다. 모바일 쪽 격리는 `isDebug` 런타임 게이트이고, **실질 방어선은 서버의 fail-closed**(운영에서는 엔드포인트가 존재하지 않아 404)다.

## T-M1 — 새로 만든 것이 없다

`:core:utils`에 **`expect val isDebug: Boolean`이 이미 구현돼 있었고 사용처가 0건**이었다(androidMain → `BuildConfig.DEBUG`, iosMain → `Platform.isDebugBinary`). `ChallengeFeaturePlugin`이 모든 feature 모듈에 `:core:utils`를 자동 주입하므로 의존성 추가도 불필요했다.

→ **BuildKonfig 플래그 신설 없이 코드 0줄로 완료.** 같은 일을 하는 장치를 둘로 늘리지 않았다.

### 격리 강도 — 런타임 게이트다 (정확히)

`isDebug`는 코드가 release APK에 **들어가되 렌더되지 않는** 수준이다. 컴파일 제외가 아니다. spec §3이 두 수준("컴파일되지 않거나, 최소한 렌더되지 않아야")을 허용하므로 기준은 충족한다. 컴파일 제외는 KMP common/iOS에서 Android `debug` 소스셋처럼 깔끔하지 않아 비용이 크고, **운영에서는 서버 엔드포인트 자체가 없어 404**이므로 모바일 게이트는 defense-in-depth이지 유일한 방어가 아니다.

## T-M3 — 배선 (`:remote` / `:domain` / `:data`)

- `TestLoginRequest(testUserNo: Int)` 신규. **응답은 `LoginResponse`/`LoginData`(4필드)를 그대로 재사용** — 계약 1순위 제약(shape 파리티)이다.
- `LoginApi.testLogin()` 추가 (새 인터페이스 만들지 않음 — 같은 auth 네임스페이스)
- `LoginRepository.loginWithTestAccount(testUserNo, onError, onUnsupported)`

### 🔴 성공 후처리를 공통 함수로 추출했다

계약의 핵심 요구가 **"테스트 로그인이 카카오와 완전히 동일한 후처리를 탄다"**이다. 복사-붙여넣기하면 나중에 한쪽만 바뀌어 갈라지고, 그러면 *"테스트 로그인으로 검증한 것이 실제 로그인을 보증한다"*는 전제가 무너진다.

```kotlin
private suspend fun FlowCollector<LoginResult>.handleLoginSuccess(response: LoginResponse)
// 매핑 → updateTokens → authTokenCacheInvalidator.invalidate() → emit
```
카카오·테스트 두 경로가 **같은 함수**를 호출한다. 테스트로도 고정했다(케이스 5).

### 404 / 401 → `onUnsupported` 분기

```kotlin
if (result is ApiResult.Failure.HttpError && (result.code == 404 || result.code == 401)) {
    onUnsupported(); return@flow
}
```
- **`onError`로 보내지 않는 이유**: `HttpError.message`는 Ktor가 넣은 `response.status.description` — 영문 `"Not Found"` / `"Unauthorized"`다. 그대로 스낵바에 뜬다. **서버가 통제할 수 없는 문자열**이다.
- **401도 포함하는 이유**: 서버 격리(T-B1a/T-B1b) 배포 전에는 404가 아니라 401이 온다. 두 경우 모두 "이 서버는 미지원"이 사용자에게 맞는 설명이다.
- ⚠️ 비즈니스 에러(`code 700`, 범위 밖 `testUserNo`)는 HTTP 200 + BaseResponse라 `CustomError`로 오고 **기존대로 `onError`**로 간다. 500 경계 케이스도 `onError`로 가는 것을 테스트로 고정했다.

### `LoginWithTestAccountUseCase` — 계정 전환 정리를 강제한다

```kotlin
operator fun invoke(...): Flow<LoginResult> = flow {
    logoutUseCase()          // 토큰 + UserInfo 캐시 정리
    emitAll(loginRepository.loginWithTestAccount(...))
}
```
ViewModel이 잊을 수 없도록 UseCase 안에 넣었다. 이유는 아래 "계약 정정" 참조.

## T-M2 — 로그인 화면

- `TestLoginUiState(isVisible, isUnavailable)` + `TestAccount` enum. 파생값(`isEnabled` / `caption`)은 전부 `get()` — Composable에서 조건 판별 금지(프로젝트 규칙).
- **라벨은 `테스터1/2/3`** — 서버가 만드는 닉네임과 **글자 단위로 동일**. T-M4로 홈에 실제 닉네임이 뜨므로 같은 문자열이어야 한다.
- `TestLoginSection`은 `isVisible == false`면 **early return**으로 아무것도 렌더하지 않는다. release에서 사라지는 지점이 여기다.
- 🔴 성공 시 **카카오와 동일한 `LoginUiEffect.NavigateToHome(isNewUser)`**를 발행한다. 별도 effect를 만들지 않았다.

### 404 처리 — 반응형 비활성 (사전 probe 없음)

| 시점 | 동작 |
|---|---|
| 로그인 화면 진입 | **probe 하지 않는다.** debug면 버튼 노출 |
| 첫 404/401 | 한국어 안내 + **그 세션 동안 버튼 비활성** + 사유 캡션 |
| 이후 | 눌리지 않아 같은 실패가 반복되지 않는다 |

**사전 probe를 기각한 이유**: 로그인은 앱의 첫 화면이라 진입마다 네트워크 왕복을 얹고 싶지 않고, **probe 자체가 실패하면 무슨 문구를 띄울지 문제가 재귀**한다. 반응형 비활성은 사전 비용 0이면서 한 번 눌러본 뒤 UI가 현실을 반영한다.

## T-M4 — debug 빌드에서만 홈에 계정 표시

`HomeUiState.Data.debugAccountLabel: String? get() = if (isDebug) userInfo?.nickname else null` + `HomeTopBar(debugAccountLabel = ...)`.

**왜 필요했나** — 실측 결과 **현재 앱에는 "내가 누구로 로그인했는지" 보이는 화면이 한 곳도 없었다.** `userInfo`는 fetch·캐시까지 되지만 렌더되는 곳이 0건이고, 홈의 유일한 닉네임 렌더는 `ReceivedChallengeCard`의 **상대방** 것이다. 스낵바는 몇 초 뒤 사라지는데 실제 검증 흐름은 로그인 → 친구 요청 → 챌린지 신청 → 수락으로 몇 분간 이어져서, 중간에 헷갈리면 **손 테스트 결과 자체를 신뢰할 수 없다.**

**`user-info`의 "Home에 노출 안 함" 사용자 결정과 충돌하지 않는다** — `isDebug` 게이트라 운영 UI는 그대로다. 데이터도 이미 상태에 있어 렌더만 붙였다(fetch 추가 없음).

## 변경된 파일 — **전부 이 feature 소속이다**

> 2026-07-31 사용자가 `challenge-create`(`d1a441f`)와 `datetime-model-migration`(`b7dd2d9`)을 커밋했다. **working tree에는 이제 이 feature의 변경분만 남아 있어 커밋 분리가 필요 없다.**

### 신규 (7)
| 모듈 | 파일 |
|---|---|
| `:remote:model` | `auth/TestLoginRequest.kt` |
| `:domain:usecase` | `LoginWithTestAccountUseCase.kt` |
| `:local:datastore` | `datasource/TokenLocalDataSourceImpl.kt` |
| `:data:repositoryImpl` | `commonTest/LoginRepositoryImplTest.kt` |
| `:feature:login` | `contract/TestLoginState.kt`, `component/TestLoginSection.kt`, `commonTest/FakeUserInfoRepository.kt` |

### 수정 (15)
`:remote:api/LoginApi.kt` · `:domain:repository/LoginRepository.kt` · `:data:repositoryImpl`(`LoginRepositoryImpl`, `di/UseCaseModule`, `build.gradle.kts`) · `:local:datastore/TokenLocalDataSource.kt` · `:feature:login`(`LoginViewModel`, `LoginScreen`, `LoginRoute`, `commonTest/FakeLoginRepository`, `commonTest/LoginViewModelTest`) · `:feature:home`(`contract/HomeUiState`, `component/HomeTopBar`, `HomeScreen`, `commonTest/HomeViewModelTest`)

### ⚠️ 범위 밖 구조 변경 1건 — `TokenLocalDataSource` interface 분리

`TokenLocalDataSource`가 **final concrete 클래스이고 생성자에서 `createDataStore`를 즉시 실행**해(Android는 Koin `Context` 주입) fake도 실물 사용도 불가능했다. 그래서 `LoginRepositoryImpl` 테스트를 **한 건도** 쓸 수 없었다.

→ 레포에 이미 있는 `UserInfoLocalDataSource`(interface) + `UserInfoLocalDataSourceImpl`(`@Single(binds=...)`) 패턴을 그대로 따라 분리했다. 사용처 2곳(`LoginRepositoryImpl`, `TokenProviderImpl`)은 **타입명이 유지돼 무변경**이다.

**이건 backlog에 이미 등재돼 있던 항목이다** — `user-info/mobile-report.md` 출처의 *"`TokenLocalDataSource` / `AppSettingsLocalDataSource` interface 분리 (테스트 추가 시)"*. "테스트 추가 시"라는 조건이 지금 충족됐다. `AppSettingsLocalDataSource`는 손대지 않았다.

## 테스트 결과 — **148/148 passed, 0 failed**

집계 전 `build/test-results`를 삭제해 stale XML을 배제했다.

| 모듈 | 클래스 | 건수 | 성격 |
|---|---|---|---|
| `:data:repositoryImpl` | `LoginRepositoryImplTest` | **6** | 신규 |
| `:feature:login` | `LoginViewModelTest` | **10** | 기존 4 + 신규 6 |
| `:feature:home` | `HomeViewModelTest` | **23** | 기존 21 + 신규 2 |
| `:data:repositoryImpl` | `ChallengeRepositoryImplTest` / `UserInfoRepositoryImplTest` | 13 / 5 | 회귀 0 |
| `:core:utils` | `KstDeadline` / `RelativeTimeFormat` / `ChallengeDateTimeFormats` / `WireFormatBaseline` | 9 / 9 / 6 / 4 | 회귀 0 |
| `:remote:mapper` | `ChallengeMappers` / `ActiveChallengeResponseMapper` / `FriendMappers` | 6 / 3 / 5 | 회귀 0 |
| `:feature:*` | `FriendsViewModel` / `FriendsSearchViewModel` / `ChallengeCreateViewModel` | 11 / 12 / 15 | 회귀 0 |

### 회귀 카운트

> **기존 134건 회귀 0 / 의도적 삭제 0건 / 신규 14건**

- baseline **134** = 직전 feature 종료 시 123 + `LoginViewModelTest` 4 + `HomeViewModelTest` 21 − … *(실측: 148 − 신규 14 = 134)*
- **신규 14** = `LoginRepositoryImplTest` 6 + `LoginViewModelTest` +6 + `HomeViewModelTest` +2
- **삭제·교체 0건.** 기존 테스트의 이름·단언을 하나도 바꾸지 않았다. `LoginViewModelTest`/`HomeViewModelTest`의 변경은 **생성자 조립과 fake 추가뿐**이다.

### 신규 테스트가 고정하는 것

- **두 로그인 경로가 같은 후처리를 탄다** (`LoginRepositoryImplTest` 케이스 5)
- **404 / 401 → `onUnsupported`, 500·비즈니스 에러 → `onError`** — 분기가 과도하게 넓지 않음을 500 경계 케이스로 고정
- **`isNewUser`가 카카오와 동일하게 전달** (true/false 둘 다)
- **미지원(`isUnavailable`)과 일반 실패를 구분** — 일반 실패는 `isUnavailable`을 건드리지 않는다
- **테스트 로그인 전에 `LogoutUseCase`가 먼저 실행** — `callLog == ["clearTokens", "loginWithTestAccount"]` + `clearUserInfoCache` 1회
- 로그인 진행 중 재호출 시 **중복 요청 없음**

### 환경 의존 단언을 피했다

`isDebug`는 테스트 실행 타깃의 빌드 타입에 따라 값이 달라진다. 그래서:
- `TestLoginUiState.isVisible` 자체는 단언하지 않았다 (`isEnabled=false`는 `isUnavailable=true`만으로 성립)
- `debugAccountLabel`은 `if (isDebug) assertEquals(...) else assertNull(...)`로 **양쪽 분기를 모두 고정** — 플랫폼과 무관하게 성립한다

### 빌드

| 대상 | 결과 |
|---|---|
| Android (`:composeApp:compileDebugKotlinAndroid`) | ✅ BUILD SUCCESSFUL |
| KMP common (`compileCommonMainKotlinMetadata`) | ✅ BUILD SUCCESSFUL |
| iOS framework (`linkDebugFrameworkIosSimulatorArm64`) | ✅ BUILD SUCCESSFUL |

## 계약 정정 2건 (내가 제기 → 반영됨)

### 1. 🔴 `clearTokens()`는 `UserInfo` 캐시를 비우지 않는다 — **내가 준 정보가 틀렸다**

계약에 *"`LoginRepository.clearTokens()`가 이미 `userInfoLocalDataSource.clear()`까지 수행한다"*고 적혀 있었는데 **사실이 아니다.**

```kotlin
override suspend fun clearTokens() {
    tokenLocalDataSource.clearTokens()
    authTokenCacheInvalidator.invalidate()   // UserInfo 캐시는 건드리지 않음
}
```
`userInfoLocalDataSource.clear()`는 `UserInfoRepositoryImpl.clearUserInfoCache()`에서만 호출된다.

`user-info/mobile-report.md`에 "추가했다"고 적혀 있어 그걸 근거로 말했는데 **현재 코드엔 없다.** 리포트를 믿고 코드를 확인하지 않은 게 원인이다.

→ 토큰과 캐시를 **함께** 비우는 건 **`LogoutUseCase`**(`clearTokens()` + `clearUserInfoCache()`)다. 그걸 호출하도록 구현했다. **결론(전환 전 정리 필요)은 그대로**이고 호출 대상만 바뀐다. **로그아웃 경로 자체는 정상**이라 기존 버그는 없다.

### 2. `nickname` 필드 부재 / "홈에서 닉네임이 보인다"

- 계약 초안의 `nickname` 필드는 **실재하지 않는다**(양측 `LoginData` 4필드). 내가 초안을 실물로 읽고 그 위에 스낵바 안을 세웠다 — 모바일 코드는 내 영역이라 확인이 어렵지도 않았는데 하지 않았다.
- 그 대안으로 제시된 "홈에서 `UserInfo`로 본다"도 **사실이 아니었다**(렌더 0건). 이건 grep으로 잡았고 T-M4가 그 대응으로 신설됐다.

> 이번 feature에서 **문서를 근거로 판단했다가 실제와 다른 게 3건**이었다. 모바일 코드에 관한 진술은 **리포트가 아니라 현재 코드**를 보고 말하는 것으로 습관을 바꿨다.

## Working tree 상태

- **작업 브랜치 `main`**, **새 커밋 0건**
- 신규 7 + 수정 15 = **22 파일, 전부 이 feature 소속**
- 직전 두 feature는 사용자가 커밋 완료(`d1a441f`, `b7dd2d9`) — **커밋 분리 부담 없음**

## 미해결 / 후속

1. **🔴 실서버 연동 미검증** — 서버 T-B2/T-B3(엔드포인트 구현)이 아직이다. 현재 모바일은 **단위 테스트 기준으로만** 완결돼 있다. 서버가 뜨면 실제로 눌러봐야 한다.
2. **404 경로 실기 확인 필요** — 서버 격리 설정이 꺼진 상태에서 실제로 404가 오는지, 그때 반응형 비활성이 도는지. **T-B1a/T-B1b가 없으면 401이 오고**, 그 경우 Ktor Auth 플러그인이 repository보다 먼저 `emitSessionExpired()`를 쏠 수 있다 — **모바일 방어로는 못 막는다.** 서버 404가 근본 해결이다.
3. **iOS 유닛 테스트 미실행** — Android 유닛 + iOS framework link까지가 검증 게이트(기존 관행).
4. **`AppSettingsLocalDataSource` interface 분리 미수행** — backlog 항목 중 `TokenLocalDataSource`만 처리했다. 테스트가 필요해질 때 같은 패턴으로.
5. **계정 전환 시 홈 데이터 갱신** — `LogoutUseCase`로 캐시를 비우므로 홈 재진입 시 새로 fetch된다. 다만 **전환 직후 홈이 이미 떠 있는 경우**의 갱신 타이밍은 실기에서 확인할 것.
