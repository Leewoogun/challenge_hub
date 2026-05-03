# Mobile Report — auth-kakao

- **feature-id**: auth-kakao
- **작성자**: mobile-dev
- **작성일**: 2026-04-24
- **상태**: 스켈레톤 완료, Kakao SDK 실연동 및 디자인 반영 대기

## 구현 요약

카카오 로그인 플로우를 위한 모바일 레이어를 Domain → Data → Feature → Navigation 순서로 구축했다.
- API base URL 을 TMDB 에서 로컬 challenge 서버로 교체하고 buildkonfig 을 플랫폼별로 분기 (Android 에뮬레이터: `10.0.2.2:8080`, iOS 시뮬레이터: `localhost:8080`).
- `:remote:model` 에 `BaseResponse` 패턴 (ADR-0002) 및 `KakaoLoginRequest`/`LoginResponse`/`LoginData`/`RefreshRequest`/`RefreshResponse`/`RefreshData` DTO 추가.
- `:remote:api` 에 `AuthApi` (Ktorfit interface) 추가 — `POST /api/v1/auth/kakao`, `POST /api/v1/auth/refresh`. 반환 타입은 공통 `ApiResult<T>`.
- `:domain:model` 에 `AuthTokens`, `UserProfile`, `LoginResult` 추가.
- `:domain:repository` 에 `AuthRepository` 인터페이스 정의. 에러 콜백 시그니처 `(code: Int, message: String) -> Unit` 로 ADR-0002 의 code 기반 에러를 그대로 전달.
- `:domain:usecase` 에 `LoginWithKakaoUseCase`, `RefreshAccessTokenUseCase`, `GetStoredTokensUseCase` 추가. (Domain 모듈은 pure Kotlin 이므로 Koin annotation 불가 → `:data:repositoryImpl/di/UseCaseModule.kt` 에서 `@Factory` 로 등록)
- `:data:repositoryImpl` 에 `AuthRepositoryImpl` (`@Single(binds = [AuthRepository::class])`) 추가. code=200 성공 → 토큰 저장, code=401 refresh 만료 → null 반환 + 저장소 정리, 그 외 → onError 콜백.
- `SecureTokenStorage` (interface) + `expect class SecureTokenStorageImpl` 를 `:data:repositoryImpl` commonMain 에, Android actual 은 `EncryptedSharedPreferences` (AES-256-GCM + AndroidKeyStore), iOS actual 은 Keychain (`kSecClassGenericPassword`, `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`) 로 구현.
- `:feature:auth` 모듈 신규 생성. `LoginScreen` (그라데이션 배경 + 카카오 옐로우 버튼 placeholder), `LoginViewModel` (StateFlow `.update { }` + code 분기 다이얼로그/스낵바 처리), expect/actual `KakaoLoginProvider` (Android/iOS 모두 stub 구현체가 `"TEST_TOKEN_DO_NOT_USE"` 반환).
- `:feature:splash` 모듈 신규 생성. `SplashViewModel` 이 저장된 refresh 확인 → `/auth/refresh` 시도 → 성공 시 홈, 실패/부재 시 로그인 화면으로 분기.
- `:core:navigation/Route.kt` 에 `AuthRoute.Login`, `SplashRoute.Main` 추가. `SerializersModule` 에도 등록.
- `:feature:main/MainScreen.kt` 의 NavDisplay 가 splash/auth/home 을 모두 라우팅하도록 업데이트. 앱 시작점을 `HomeRoute.Main` 에서 `SplashRoute.Main` 으로 교체. Splash/Auth 에서는 BottomBar 숨김.
- `composeApp/App.kt` 의 Koin `startKoin` 에 `AuthModule`, `SplashModule` 등록.

## 사용한 모바일 레포 스킬

- `full-feature/SKILL.md` (전체 플로우 가이드): Domain → Data → Feature → Navigation 순서로 진행.
- `data-remote/SKILL.md`: DTO (`:remote:model`), Ktorfit API (`:remote:api`), RepositoryImpl (`:data:repositoryImpl`) 생성 규칙 준수. Ktorfit `createAuthApi` 확장함수 + `ApiResult<T>` 반환 타입 패턴을 기존 MovieApi 와 동일하게.
- `feature/SKILL.md`: State/Effect sealed interface, `{Name}Route` / `private {Name}Content` / `internal {Name}Screen` 3단 구조, `@KoinViewModel` + `@Module @ComponentScan`.
- `navigation/SKILL.md`: Route.kt → MainScreen.kt NavDisplay → feature:main build.gradle.kts → settings.gradle.kts 4곳 모두 수정.
- `test-viewmodel/SKILL.md`: `@BeforeTest`/`@AfterTest` 에서 Dispatchers.setMain/resetMain, Fake Repository + Turbine `.test { }` + runTest, 한글 백틱 네이밍.

## 변경된 파일

### 신규 파일

**Remote (DTO / API)**
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/base/BaseResponse.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/auth/KakaoLoginRequest.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/auth/LoginResponse.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/auth/RefreshRequest.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/auth/RefreshResponse.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/api/src/commonMain/kotlin/com/lwg/challenge/remote/api/AuthApi.kt`

**Domain**
- `/Users/hwamulman/woogunProject/challenge/challenge-app/domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/AuthTokens.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/UserProfile.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/LoginResult.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/domain/repository/src/commonMain/kotlin/com/lwg/challenge/domain/repository/AuthRepository.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/domain/usecase/src/commonMain/kotlin/com/lwg/challenge/domain/usecase/LoginWithKakaoUseCase.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/domain/usecase/src/commonMain/kotlin/com/lwg/challenge/domain/usecase/RefreshAccessTokenUseCase.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/domain/usecase/src/commonMain/kotlin/com/lwg/challenge/domain/usecase/GetStoredTokensUseCase.kt`

**Data**
- `/Users/hwamulman/woogunProject/challenge/challenge-app/data/repositoryImpl/src/commonMain/kotlin/com/lwg/challenge/data/repository/AuthRepositoryImpl.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/data/repositoryImpl/src/commonMain/kotlin/com/lwg/challenge/data/storage/SecureTokenStorage.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/data/repositoryImpl/src/androidMain/kotlin/com/lwg/challenge/data/storage/SecureTokenStorage.android.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/data/repositoryImpl/src/iosMain/kotlin/com/lwg/challenge/data/storage/SecureTokenStorage.ios.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/data/repositoryImpl/src/commonMain/kotlin/com/lwg/challenge/data/di/UseCaseModule.kt`

**Feature — Auth**
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/build.gradle.kts`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonMain/kotlin/com/lwg/challenge/feature/auth/contract/AuthState.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonMain/kotlin/com/lwg/challenge/feature/auth/contract/AuthEffect.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonMain/kotlin/com/lwg/challenge/feature/auth/kakao/KakaoLoginProvider.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/androidMain/kotlin/com/lwg/challenge/feature/auth/kakao/KakaoLoginProvider.android.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/iosMain/kotlin/com/lwg/challenge/feature/auth/kakao/KakaoLoginProvider.ios.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonMain/kotlin/com/lwg/challenge/feature/auth/LoginViewModel.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonMain/kotlin/com/lwg/challenge/feature/auth/LoginRoute.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonMain/kotlin/com/lwg/challenge/feature/auth/LoginScreen.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonMain/kotlin/com/lwg/challenge/feature/auth/di/AuthModule.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonTest/kotlin/com/lwg/challenge/feature/auth/FakeAuthRepository.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/src/commonTest/kotlin/com/lwg/challenge/feature/auth/LoginViewModelTest.kt`

**Feature — Splash**
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/splash/build.gradle.kts`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/splash/src/commonMain/kotlin/com/lwg/challenge/feature/splash/contract/SplashState.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/splash/src/commonMain/kotlin/com/lwg/challenge/feature/splash/contract/SplashEffect.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/splash/src/commonMain/kotlin/com/lwg/challenge/feature/splash/SplashViewModel.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/splash/src/commonMain/kotlin/com/lwg/challenge/feature/splash/SplashRoute.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/splash/src/commonMain/kotlin/com/lwg/challenge/feature/splash/SplashScreen.kt`
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/splash/src/commonMain/kotlin/com/lwg/challenge/feature/splash/di/SplashModule.kt`

### 수정 파일

- `/Users/hwamulman/woogunProject/challenge/challenge-app/settings.gradle.kts` — `:feature:auth`, `:feature:splash` include 추가.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/local.properties` — `tmdb_token` 제거, `challenge_api_base_url_android`, `challenge_api_base_url_ios` 추가.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/network/build.gradle.kts` — buildkonfig 가 TMDB_TOKEN/BASE_URL 대신 BASE_URL 만 제공하고 iOS target 에서 오버라이드.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/network/src/commonMain/kotlin/com/lwg/challenge/remote/network/di/KtorfitModule.kt` — TMDB Authorization 헤더 제거.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/remote/api/src/commonMain/kotlin/com/lwg/challenge/remote/api/di/ApiModule.kt` — `provideAuthApi` 추가.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/gradle/libs.versions.toml` — `androidx-security-crypto`, `turbine`, `kotlinx-coroutines-test` 라이브러리 추가.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/data/repositoryImpl/build.gradle.kts` — `:domain:usecase`, `:local:datastore` 의존성 + androidMain 의 `androidx.security.crypto`.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/data/repositoryImpl/src/commonMain/kotlin/com/lwg/challenge/data/di/DataModule.kt` — `UseCaseModule::class` 을 `includes` 에 추가.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/core/navigation/src/commonMain/kotlin/com/lwg/challenge/navigation/Route.kt` — `AuthRoute.Login`, `SplashRoute.Main` 추가 + SerializersModule 등록.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/main/build.gradle.kts` — `:feature:auth`, `:feature:splash` 의존성 추가.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/main/src/commonMain/kotlin/com/lwg/challenge/feature/main/MainScreen.kt` — SplashRoute 를 시작점으로, Auth/Splash 에서 BottomBar 숨김, NavDisplay entryProvider 에 Splash/Auth 분기 추가.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/composeApp/build.gradle.kts` — `:feature:auth`, `:feature:splash` 의존성 추가.
- `/Users/hwamulman/woogunProject/challenge/challenge-app/composeApp/src/commonMain/kotlin/com/lwg/challenge/App.kt` — `AuthModule`, `SplashModule` 을 Koin 시작 시 등록.

## 테스트 결과

- **LoginViewModelTest (commonTest)** — 2/2 passed (Android debug/release 및 iOS SimulatorArm64 모두 통과)
  - `카카오 로그인 성공 시 NavigateToHome UiEffect 를 발행하고 Idle 로 복귀한다`
  - `카카오 토큰 만료 code=701 응답 시 ReLogin 모달 effect 로 전환된다`
- 테스트 결과 XML: `/Users/hwamulman/woogunProject/challenge/challenge-app/feature/auth/build/test-results/`

### iOS 빌드
- **ok**: `:composeApp:linkDebugFrameworkIosSimulatorArm64` 성공. Kotlin/Native 가 `Map<Any?, Any?>` → `NSDictionary` → `CFDictionaryRef` toll-free bridge 로 Keychain API 호출 가능.

### Android 빌드
- **ok**: `:composeApp:compileDebugKotlinAndroid` 성공. `:data:repositoryImpl:compileDebugKotlinAndroid` 도 통과 — `EncryptedSharedPreferences` (`androidx.security:security-crypto:1.1.0-alpha06`) 사용.

### 레이어별 검증
- `:remote:model:compileCommonMainKotlinMetadata` ok
- `:remote:network:compileCommonMainKotlinMetadata` ok
- `:remote:api:compileCommonMainKotlinMetadata` ok
- `:domain:model`, `:domain:repository`, `:domain:usecase` compileCommonMainKotlinMetadata ok
- `:data:repositoryImpl:compileCommonMainKotlinMetadata` ok
- `:feature:auth:compileCommonMainKotlinMetadata` ok
- `:feature:splash:compileCommonMainKotlinMetadata` ok
- `:feature:main:compileCommonMainKotlinMetadata` ok

## 미해결 이슈

### 1. Kakao SDK 실연동 (T-M9 범위 축소)
현재 `KakaoLoginProviderImpl` (Android/iOS 공통) 은 `"TEST_TOKEN_DO_NOT_USE"` 고정 토큰을 반환하는 **placeholder stub**. 실연동 시 다음 작업 필요:
- **Android**:
  1. `composeApp/build.gradle.kts` Android 의존성에 `implementation("com.kakao.sdk:v2-user:2.20.6")` 추가.
  2. `AndroidManifest.xml` 에 `AuthCodeHandlerActivity` + intent-filter 등록 (`android:scheme="kakao{NATIVE_APP_KEY}"`).
  3. `ChallengeApplication.onCreate` 에서 `KakaoSdk.init(this, "{NATIVE_APP_KEY}")`.
  4. `KakaoLoginProviderImpl.requestKakaoAccessToken` 구현체 교체 — `UserApiClient.instance.loginWithKakaoTalk` → fallback `loginWithKakaoAccount`.
- **iOS**:
  1. `iosApp/Podfile` 또는 Swift Package Manager 로 `KakaoSDKUser ~> 2.22.0` 추가.
  2. `iosApp/iosApp/Info.plist` 에 URL Scheme (`kakao{NATIVE_APP_KEY}`) + `LSApplicationQueriesSchemes` (`kakaokompassauth`, `kakaolink`) 등록.
  3. AppDelegate 에서 `KakaoSDK.initSDK(appKey:)` 호출.
  4. Swift ↔ Kotlin bridge 로 `loginWithKakaoTalk` 결과 전달 (`suspendCancellableCoroutine` + callback).
- **Kakao 개발자 콘솔**: `account_phone_number` scope 사용 권한 신청·승인 (사용자 action, 승인 전에는 phone_verified=false 케이스만 검증 가능).

### 2. design.md 반영 필요
`docs/features/auth-kakao/design.md` 가 아직 작성되지 않음. `LoginScreen` 은 현재 디자인 시스템 기본 토큰 (Orange 그라데이션 배경 + 카카오 옐로우 `#FEE500` 버튼) 으로 placeholder UI 작성. design-bridge 가 Lovable `src/routes/login.tsx` 분석 결과를 `design.md` 에 정리하면:
- 로고 이미지/SVG 경로 반영
- 실제 배경 그라데이션 토큰 (다크 테마) 교체
- 버튼 스타일 (radius, padding, icon) 최종 결정
- 타이포 스케일 보정 (현재 `bold48` 사용)

이 2차 수정은 별도 PR. 현재 placeholder 에는 `// TODO(design):` 주석 명시.

### 3. iOS Keychain 구현체 세부 점검 필요
`SecureTokenStorage.ios.kt` 는 `Map<Any?, Any?>` → `NSDictionary` → `CFDictionaryRef` toll-free bridge 에 의존. 컴파일 및 링크는 통과했으나, 실제 iOS 시뮬레이터/디바이스에서 SecItemAdd/Copy/Update 의 상태 코드를 **수동 smoke test** 로 확인 필요. 특히:
- `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` 설정이 CFDictionary key 로 제대로 전달되는지.
- `SecItemCopyMatching` 결과 (`CFTypeRef`) → `NSData` 변환이 정상 동작하는지.
- 실연동 전 간단한 integration test 로 write-read roundtrip 검증 권장 (별도 commonTest 는 Dispatchers 와 Keychain 접근 제한으로 iOS 실기기 테스트 필요).

### 4. `:remote:mapper` 의 HomeViewModel → MovieRepository 예제 코드 잔존
TMDB 예제 (`HomeViewModel`/`HomeScreen`/`MovieApi`/`MovieRepository`/`Movie`) 는 그대로 유지. BottomBar 홈 탭에서 TMDB 서버로 호출 시도하므로 backend-dev 의 foundation API 로 교체되기 전에는 에러 스낵바가 노출됨 (spec 의 "비범위"에 해당하나 표면상 이슈). `HomeRoute` 가 실제 데이터를 쓰지 않도록 임시 placeholder 로 교체하는 것도 고려 가능하나, 이번 범위 밖으로 둠.

### 5. feature:ex1/ex2/ex3 예제 모듈
repos.json 의 blocker 로 "제거 권장" 명시되어 있으나 이번 스프린트 범위 아님. 그대로 유지.

### 6. 실행 검증의 한계
- **실 서버 연동 smoke test 미수행**: backend-dev 의 foundation 스텁이 로컬 8080 에서 뜨면 `POST /api/v1/auth/kakao` 에 `"TEST_TOKEN_DO_NOT_USE"` 를 보내 스텁의 userId=1 고정 동작을 확인할 수 있음 — 별도 수동 확인 필요.
- **iOS 실기기 Keychain smoke test 미수행**: 앱 재시작 시 토큰이 보존되는지 등은 실기기/시뮬레이터 smoke 로 확인 필요.

## API 계약 대비 구현 차이

현 시점에서는 **차이 없음**. 계약 (`api-contract.md`) 상 필드명/타입/에러 코드 모두 그대로 매핑.

참고 확인 지점:
- `LoginData.userId: Long` — 계약의 `"userId": 12` 가 Int 일 수도 있으나 안전하게 Long 으로 (서버 Long → JSON number → Kotlin Long 매핑).
- `isNewUser: Boolean` — 기본값 false (null 방어).
- `RefreshResponse.data.accessToken: String` — 기본값 `""`.
- 에러 code 처리:
  - 700: 스낵바 (`AuthUiEffect.ShowMessage`).
  - 701: `AuthModalEffect.ReLogin` 다이얼로그 (재로그인 버튼).
  - 703: `AuthModalEffect.ServerError` 다이얼로그 (재시도 버튼).
  - 401 (refresh): `SecureTokenStorage.clear()` 후 null 반환 — 로그인 화면으로 유도.

## 다음 단계 제안

1. design-bridge 가 `design.md` 를 작성하면 `LoginScreen` 2차 수정 (로고, 색상 토큰, 다크 배경 등).
2. backend-dev 의 `/api/v1/auth/kakao` 실 구현 완료 후, 로컬 서버 기동 상태에서 수동 통합 테스트.
3. Kakao SDK 실 연동 별도 PR (sprint 1 후반 또는 별도 티켓).
4. ADR-0007 phased 환경 분리: staging/production URL 은 buildkonfig 의 flavor/buildType 별 오버라이드로 추가 예정.
