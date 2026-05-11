# Change Log — auth-kakao

각 항목은 spec/api-contract/구현 코드 중 어디서 변경이 일어났는지 명시한다. `api-contract.md`(status: confirmed) 자체는 변경된 적 없음 — 코드/문서가 contract를 따라가도록 정렬한 이력만 기록.

## 2026-05-08 — pm-lead 디자인 결정 9건 정리 + Lovable 동기 갱신

`design.md` ⚠️ 미결정 9건을 pm-lead가 일괄 결정하고, **Lovable 디자인 소스(`challenge-design/oathbound-challenges/src/routes/login.tsx`)를 동기 갱신**. 모바일 `LoginScreen.kt`는 placeholder 상태 그대로이며 본 결정은 **추후 2차 PR에서 반영 예정**.

### 결정 사항 → Lovable 적용

- ❌ 게스트 모드 outline 버튼 "그냥 구경만 할게요 👀" — 제거
- ❌ 통계 칩 2개 (12,847건의 맹세 / 238잔의 벌칙 커피) — 제거
- ❌ 카카오 버튼 말풍선 SVG 아이콘 — 제거 (텍스트 only)
- ❌ 외곽 회전 링 (`animate-spin-slow`) — 제거 ("불꽃 모양" 아니라는 판단)
- ❌ 부유 입자(ember 5개, `animate-float-*`) — 제거
- ✏️ 카카오 버튼 문구 "카카오로 영혼 등록하기" → **"카카오로 시작하기"** (카카오 공식 가이드 준수)

### 유지

- 스탬프 fire-gradient 배경 + Flame 아이콘 + Sparkles 2개 (`animate-pulse-fire`, `animate-pulse`)
- "SOUL CONTRACT" 영문 캡슐 뱃지
- 타이틀 "영혼을 걸어라. 🔥" (gradient-fire 텍스트 + `animate-wiggle` 이모지)
- `slide-up` 진입 애니메이션 (Hero / CTA 0.2s delay)
- `gradient-glow` / `gradient-fire` blur 블롭 배경
- 약관 풋터, 구분선 + "한 번 서명하면 무를 수 없음"

### 보류 / 별도 처리

- **로딩 상태 디자인**: 정식 시안 없이 현재 placeholder(전체 검정 30% 오버레이 + `CircularProgressIndicator`) 유지. 추후 디자이너 시안 나오면 재검토.
- **디자이너 시각 검증 6건**(`docs/design-system/colors.md` §5: gradientPrimaryEnd / gradientCardStart/End / chart4 / glow brush / 135deg): 디자이너 부재로 mobile-dev 추정값 그대로 채택. 향후 미세 조정 시 별도 ADR.

### 변경 파일

- ✏️ `challenge-design/oathbound-challenges/src/routes/login.tsx` — ember 5개 / 외곽 회전 링 / 통계 칩 / outline 버튼 / 카카오 SVG 아이콘 제거. 카카오 문구 변경.
- ✏️ `challenge-pm/challenge_hub/docs/features/auth-kakao/design.md` — ⚠️ 9건 → ✅ 결정 표로 교체. 본문 표(부가 요소/카카오 매핑/컴포넌트 매핑) 결정 반영.
- ✏️ `challenge-pm/challenge_hub/docs/features/auth-kakao/change-log.md` — 본 항목.

### 후속 (별도 PR)

- 모바일 `LoginScreen.kt` 디자인 통합 2차 PR — 본 결정에 맞춰 Hero(스탬프 + 뱃지 + 타이틀 + 서브카피) + CTA(구분선 + 카카오 버튼 + 약관 풋터) + 배경 블롭/슬라이드업 모두 구현. 현재 placeholder("맹세" 텍스트 + 슬로건 + 카카오 버튼) 교체. 사용자 결정에 따라 일정은 미정.

---

## 2026-05-07 — iOS Kakao SDK 실연동 완료 (T-M9 잔여 해소)

직전(같은 날) Android SDK 실연동 항목에서 placeholder로 남았던 iOS 통합이 완전히 채워졌다. **Android+iOS 모두 SDK 통합 완료** — 다음 sprint부터 카카오 로그인이 실제 단말 양쪽에서 동작.

### 변경 (`challenge-app`)

#### iOS SPM 의존성
- `iosApp/iosApp.xcodeproj/project.pbxproj` — `XCRemoteSwiftPackageReference "kakao-ios-sdk"` 추가 (`https://github.com/kakao/kakao-ios-sdk`). Frameworks에 `KakaoSDKAuth` / `KakaoSDKCommon` / `KakaoSDKUser` 모두 링크. **CocoaPods 미사용** (Podfile/`Pods/`/`xcworkspace` 없음 — SPM 단일 채택).

#### Kotlin actual 구현 (placeholder → 실 구현)
- `feature/login/src/iosMain/.../kakao/KakaoAuthClient.ios.kt` — `KakaoLoginBridge.loginHandler`를 `suspendCancellableCoroutine`으로 감싸 Success/Failure/Cancelled로 매핑. placeholder 메시지 전체 제거.
- `feature/login/src/iosMain/.../kakao/KakaoLoginBridge.kt` — `object KakaoLoginBridge { var loginHandler }` (Kotlin/Native ↔ Swift 통신 entry).
- `composeApp/src/iosMain/.../KakaoLoginSetup.kt` — `interface KakaoLoginHandler` + `fun registerKakaoLoginHandler(handler)` (Kotlin이 Swift 구현체를 받는 경로).

#### Swift 측 bridge 구현
- `iosApp/iosApp/KakaoLoginHelper.swift` — `KakaoLoginHelperImpl: KakaoLoginHandler`. `UserApi.shared.loginWithKakaoTalk` 우선, 실패 시 `loginWithKakaoAccount` fallback. 취소 식별(`SdkError.getClientError().reason == .Cancelled`)까지 처리하여 `KakaoAuthResult.Cancelled`로 매핑.
- `iosApp/iosApp/iOSApp.swift` — `init()`에서 `KakaoSDK.initSDK(appKey:)` (Info.plist의 `KAKAO_NATIVE_APP_KEY` 읽음, 비어있으면 경고 후 skip). `WindowGroup.onOpenURL`에서 `AuthApi.isKakaoTalkLoginUrl(url)` 체크 후 `AuthController.handleOpenUrl(url:)` 처리. `registerKakaoLoginHandler(handler: KakaoLoginHelperImpl())`로 bridge 등록.

#### Info.plist + secret 주입
- `iosApp/iosApp/Info.plist` — `kakao{KAKAO_NATIVE_APP_KEY}` literal → `kakao$(KAKAO_NATIVE_APP_KEY)` Xcode 빌드 변수로 교체.
- `iosApp/Configuration/Config.xcconfig` — 기본 설정.
- `iosApp/Configuration/Secrets.xcconfig` — gitignored. 사용자가 실 NATIVE APP KEY 기입.
- `iosApp/Configuration/Secrets.xcconfig.template` — 템플릿 커밋, 신규 개발자 가이드.
- `.gitignore` — `Secrets.xcconfig` 추가.

### 빌드/테스트
- `:composeApp:linkDebugFrameworkIosSimulatorArm64` BUILD SUCCESSFUL (24s)
- `:feature:login:iosSimulatorArm64Test` BUILD SUCCESSFUL (UP-TO-DATE — 기존 4 케이스 그대로, KMP commonTest가 iOS Simulator에서도 실행되므로 별도 iOS 테스트 추가 불필요)
- Xcode SPM resolve / 시뮬레이터 실행 검증은 사용자 측에서 수행

### 사용자 액션 상태
- ✅ NATIVE APP KEY 발급 + `Secrets.xcconfig` 기입 완료
- ✅ Android `local.properties.kakao_native_app_key` 동일 값 채움
- ⚠️ Android keyhash 카카오 콘솔 등록 여부 미확인 — 백로그 등재
- ⚠️ 실 단말 E2E (Android 카카오톡 앱-간 인증 + 웹 fallback / iOS 동일) 수동 검증 미수행 — 백로그 등재

### 잔여 / 후속
- iOS SPM `XCRemoteSwiftPackageReference`의 `requirement` 설정(`upToNextMajor` 등) 적정성 확인 — 백로그 등재
- iOS Simulator + 실 디바이스 카카오톡 핸드오프 E2E 수동 테스트 — 백로그 등재
- iOS Keychain 실기기 smoke (별건, 직전부터 백로그 잔존)

---

## 2026-05-07 — 백엔드 contract drift 정정 (REST API → SDK 정렬)

### 발견
조사 중 모바일과 백엔드가 **서로 다른 카카오 로그인 방식**으로 구현되어 있어 통신이 불가능한 상태로 확인됨:

| | 모바일 | 백엔드 (drift) | api-contract.md |
|---|---|---|---|
| 페이로드 | `{ "kakaoAccessToken": "..." }` | `{ "code": "..." }` | `kakaoAccessToken` |
| 카카오 호출 | (SDK 내부) | `/oauth/token` + `/v2/user/me` | `/v2/user/me`만 |
| client_secret | 불필요 | 필요 (`KAKAO_REST_API_KEY` + `KAKAO_CLIENT_SECRET` + `KAKAO_REDIRECT_URI`) | 불필요 |

`api-contract.md`(2026-04-24 confirmed)와 `backend-report.md`(2026-04-24)는 처음부터 SDK 방식(`kakaoAccessToken`)으로 명세 — 그러나 **백엔드 코드만 그 사이 어느 시점에 REST API Authorization Code Flow로 이탈**한 상태였음. 모바일은 contract를 그대로 따른 상태.

### 사용자 결정
"SDK 방식으로 통일" — 모바일이 이미 그렇게 구현돼 있고 contract도 SDK 명세이므로 백엔드를 contract에 맞춰 정렬.

### 백엔드 변경 (`challenge-server`)
- `api/.../auth/dto/KakaoLoginRequest.kt` — `code: String` → `kakaoAccessToken: String`. `@NotBlank` 메시지 contract 정렬, `@Size` 한도 1024 → 2048
- `api/.../auth/AuthController.kt` — `request.code` → `request.kakaoAccessToken`
- `api/.../auth/AuthService.kt` — `loginWithKakao(code)` → `loginWithKakao(kakaoAccessToken)`. `kakaoOAuthClient.exchangeCodeForToken(...)` 호출 단계 제거, `getUserInfo(kakaoAccessToken)`만 호출. `@Value("\${kakao.redirect-uri}")` 주입 제거
- `infra/.../kakao/KakaoOAuthClient.kt` — `exchangeCodeForToken`/`doExchangeCodeForToken`/`authWebClient`/`authBaseUrl` 등 `/oauth/token` 관련 코드 전면 제거. `@Value` 3종(`auth-base-url`, `rest-api-key`, `client-secret`) 제거. 401/403 → `KakaoTokenInvalidException`(701), 5xx/네트워크 → 1회 재시도 후 `KakaoServerException`(703) 매핑은 유지
- `infra/.../kakao/KakaoTokenResponse.kt` — **삭제** (참조처 없음)
- `app/src/main/resources/application.yml` — `kakao.auth-base-url`, `kakao.rest-api-key`, `kakao.client-secret`, `kakao.redirect-uri` 키 4종 제거. `kakao.api-base-url` + `kakao.webclient.*`만 잔존
- `app/src/test/.../api/auth/AuthControllerTest.kt` — 페이로드/mock stub `code` → `kakaoAccessToken`
- `app/src/test/.../auth/AuthKakaoIntegrationTest.kt` — WireMock `/oauth/token` stub 5건 제거. 시나리오 5건 재정렬: 신규/기존/phone미동의/`/v2/user/me` 401(701)/`/v2/user/me` 5xx 1회 재시도 후 703. 페이로드 `{"kakaoAccessToken": "..."}`로 변경
- `app/src/test/.../ChallengeServerApplicationTests.kt` — `@SpringBootTest` properties에서 `kakao.rest-api-key`/`kakao.redirect-uri` 제거

### 빌드/테스트
- `:infra` / `:api` / `:app` `compileKotlin` BUILD SUCCESSFUL
- `AuthControllerTest` 5/5 passed
- `AuthKakaoIntegrationTest` 컴파일 통과, 5/5 skipped (Docker 미가용 — `@EnabledIf` 자동 skip). Docker 환경에서 재실행 필요
- `ChallengeServerApplicationTests` 1/1 passed (env var 제거 후에도 context 로드 OK)

### 운영 영향
- 더 이상 필요 없는 환경변수: `KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET`, `KAKAO_REDIRECT_URI`, `KAKAO_AUTH_BASE_URL` — 운영 secret manager / k8s Secret / `.env`에서 제거 권장
- 여전히 필요: `KAKAO_API_BASE_URL` (선택, default `https://kapi.kakao.com`), `JWT_SECRET`, DB/Redis 접속 정보

### 별건 발견 (스코프 밖, 후속 처리 필요)
- `app/src/main/resources/application.yml:60` — `swagger-ui.path: /swagger-ui/index.htmlㅠ` 한글 자음 'ㅠ' 오타. Swagger UI 접근 안 될 가능성 → 백로그 등재.

---

## 2026-05-07 — 모바일 Android Kakao SDK 실연동 완료 (T-M9 부분 해소)

### 변경 (`challenge-app`)
- `feature/login/.../kakao/KakaoAuthClient.kt` (commonMain) — interface + `KakaoAuthResult` sealed (Success/Cancelled/Failure)
- `feature/login/.../kakao/KakaoAuthClient.android.kt` — `UserApiClient.loginWithKakaoTalk()` → 미설치/실패 시 `loginWithKakaoAccount()` fallback. `suspendCancellableCoroutine`로 콜백→코루틴 변환
- `feature/login/.../kakao/KakaoAuthClient.ios.kt` — **placeholder**. 무조건 `Failure(message="iOS 카카오 로그인은 아직 통합되지 않았습니다...")` 반환. CocoaPods/SPM 의존성, AppDelegate URL handler, Swift bridge 모두 미구현 (단계는 docstring에 명시)
- `feature/login/.../di/PlatformLoginModule.{android,ios}.kt` — `expect val platformLoginModule: Module` + 플랫폼별 actual
- `feature/login/build.gradle.kts` — `androidMain`에 `libs.kakao.sdk.user`
- `composeApp/build.gradle.kts` — buildkonfig 플러그인, `KAKAO_NATIVE_APP_KEY` BuildKonfig 필드, Android `manifestPlaceholders["kakaoNativeAppKey"]`
- `composeApp/src/androidMain/AndroidManifest.xml` — `com.kakao.sdk.auth.AuthCodeHandlerActivity` + `kakao${kakaoNativeAppKey}://oauth` intent-filter
- `composeApp/src/androidMain/.../ChallengeApplication.kt` — `KakaoSdk.init(this, BuildKonfig.KAKAO_NATIVE_APP_KEY)` (key 비어있으면 경고만 남기고 skip)
- `iosApp/iosApp/Info.plist` — `CFBundleURLTypes` (scheme `kakao{KAKAO_NATIVE_APP_KEY}` placeholder) + `LSApplicationQueriesSchemes` (`kakaokompassauth`, `kakaolink`, `kakaoplus`)
- `gradle/libs.versions.toml` — `kakao-sdk = "2.20.6"` + `kakao-sdk-user = { module = "com.kakao.sdk:v2-user" }`
- `settings.gradle.kts` — 카카오 Maven 저장소 추가 (`https://devrepo.kakao.com/nexus/content/groups/public/`)
- `local.properties` — `kakao_native_app_key = ""` placeholder (사용자 기입 필요)
- `feature/login/src/commonMain/.../LoginViewModel.kt` — `STUB_KAKAO_TOKEN` 제거, `KakaoAuthClient.requestAccessToken()` 결과별 분기 (Success/Cancelled/Failure)
- `feature/login/src/commonTest/.../LoginViewModelTest.kt` — 2 케이스 → **4 케이스**로 확장 (OAuth Success+서버 Success / OAuth Cancelled / OAuth Failure / OAuth Success+서버 Error)

### 빌드/테스트
- `:feature:login:compileCommonMainKotlinMetadata` / `:feature:login:compileDebugKotlinAndroid` / `:composeApp:compileDebugKotlinAndroid` / `:composeApp:linkDebugFrameworkIosSimulatorArm64` 4건 BUILD SUCCESSFUL
- `LoginViewModelTest` 4/4 passed (Android Unit + iOS SimulatorArm64)

### 사용자 액션 필요
1. Kakao 개발자 콘솔에서 **NATIVE APP KEY** 발급 → `local.properties.kakao_native_app_key` 기입
2. Android keyhash 등록 (`debug.keystore` SHA1)
3. iOS Info.plist의 `kakao{KAKAO_NATIVE_APP_KEY}` literal을 실제 키로 치환

### 잔여 (별도 PR)
- iOS Kakao SDK 정식 통합 — Pod/SPM 추가, `iOSApp.swift` AppDelegate에서 `KakaoSDK.initSDK(appKey:)` + `application(_:open:options:)`에서 `AuthApi.handleOpenUrl` 처리, Swift→Kotlin bridge로 `AuthApi.shared.loginWithKakaoTalk`/`loginWithKakaoAccount` 콜백 매핑.

### 별건 발견 (스코프 밖)
- `:feature:login:check`가 detekt config 부재(`/config/detekt/detekt.yml` 없음)로 BUILD FAILED — 이번 변경과 무관한 사전 인프라 이슈. 컴파일/테스트 자체는 모두 성공.
