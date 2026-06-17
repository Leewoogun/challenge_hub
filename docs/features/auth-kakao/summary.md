# 카카오 로그인 (auth-kakao) — Summary

- **feature-id**: auth-kakao
- **최초 완료일**: 2026-04-24
- **최종 갱신**: 2026-05-11 (LoginScreen 디자인 2차 반영 완료 — [change-log.md](./change-log.md))
- **상태**: completed

> 서버·모바일(Android+iOS)·계약 모두 SDK 방식으로 정렬·통합 완료(2026-05-07). LoginScreen 디자인 2차 반영도 완료(2026-05-11). **본 feature 범위 내 코드 작업 종료.** 운영성 잔여 항목(Docker 통합 테스트 수동 실행, 실 단말 E2E smoke, Android keyhash 등록, iOS Keychain 실기기 smoke, 시각 검증, 시각 fidelity 보완 4건)은 [backlog.md](../../backlog.md)에서 추적.

## 구현 개요

Sprint 0 `foundation`의 스텁(`userId=1L` 고정)을 실제 Kakao OAuth 연동으로 교체하고, 모바일 측에 전체 로그인 플로우(스플래시 → 토큰 확인 → 자동 로그인 또는 로그인 화면 → 홈)를 구축했다. 백엔드는 WebClient로 `/v2/user/me`를 호출해 토큰을 검증하고 users upsert + phone SHA-256 해시 저장 + JWT 발급을 단일 트랜잭션으로 수행한다 (SDK 방식 — 모바일이 SDK로 받은 access_token을 그대로 전달). 모바일은 DTO/API/UseCase/Repository/SecureTokenStorage(Android Keystore + iOS Keychain) + LoginScreen/SplashScreen + Navigation을 스킬 절차대로 구현했다.

**2026-05-07 갱신**: ① 백엔드 코드가 한때 REST API Authorization Code Flow로 이탈했던 것을 SDK 흐름으로 다시 정렬(contract drift 정정). ② Android는 `com.kakao.sdk:v2-user:2.20.6`으로 실연동 완료(`loginWithKakaoTalk` → 미설치 시 `loginWithKakaoAccount` fallback). ③ iOS는 SPM `kakao-ios-sdk`로 SDK 통합 완료 — `iOSApp.swift`에 `KakaoSDK.initSDK` + `onOpenURL` URL handler, `KakaoLoginHelper.swift`(Swift→Kotlin bridge), `KakaoAuthClient.ios.kt` placeholder→실 구현, Info.plist `kakao$(KAKAO_NATIVE_APP_KEY)` xcconfig 변수 주입. 자세한 내력은 [change-log.md](./change-log.md).

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| POST | /api/v1/auth/kakao | 공개 | implemented (배포 전) |
| POST | /api/v1/auth/refresh | 공개 (refresh가 인증) | foundation에서 완성, 변경 없음 |
| DELETE | /api/v1/auth/logout | Bearer | Sprint 0 스텁 유지 (범위 밖) |

## 화면 / UI 변경

- **SplashScreen (신규)**: 앱 진입점. `:feature:splash`. 저장된 refresh 토큰 확인 → 자동 로그인 시도 → 성공 시 `HomeRoute.Main`, 실패/부재 시 `LoginRoute`으로 분기.
- **LoginScreen (신규 + 2차 반영 완료 2026-05-11)**: `:feature:login`. 다크 베이스 + 글로우/fire 블롭 배경, Hero(SoulStampLogo 140dp + SOUL CONTRACT 뱃지 + "영혼을 걸어라. 🔥" brush 텍스트 + 서브 카피) + CTA(LabeledDivider + 카카오 버튼 "카카오로 시작하기" 텍스트 only + 약관 풋터). slide-up/fadeIn 진입 애니메이션. code별 분기(700 스낵바 / 701 재로그인 다이얼로그 / 703 서버 에러 다이얼로그). 로딩 시 검정 30% 오버레이 + CircularProgressIndicator.
- **MainScreen**: 시작점 `HomeRoute.Main` → `SplashRoute.Main`으로 교체. Splash/Login에서는 BottomBar 숨김.

## 주요 변경 파일

**백엔드** (challenge-server):
- `core/src/main/.../hash/PhoneHasher.kt` (+ test) — SHA-256 해시 유틸
- `domain/src/main/.../domain/user/User.kt` — 순수 도메인 모델
- `infra/src/main/.../infra/auth/UserEntity.kt`, `UserJpaRepository.kt` — JPA 매핑
- `infra/src/main/.../infra/kakao/KakaoOAuthClient.kt`, `KakaoUserResponse.kt`, `KakaoOAuthExceptions.kt` — WebClient 기반 Kakao 연동
- `api/src/main/.../api/auth/AuthService.kt` — 로그인 서비스 (업서트 + JWT)
- `api/src/main/.../api/auth/AuthController.kt` — 스텁 제거, 서비스 위임
- `app/src/main/resources/application.yml` — `kakao.base-url`, WebClient 타임아웃
- `app/src/test/kotlin/.../auth/AuthKakaoIntegrationTest.kt` — WireMock + Testcontainers 통합 테스트 4케이스
- `build-logic/src/main/kotlin/KotlinLibraryConventionPlugin.kt` — `junit-platform-launcher` 추가 (JUnit5 discover 이슈 수정)

**모바일** (challenge-app):
- `remote/model/.../base/BaseResponse.kt` + `auth/*.kt` DTO 5종 — BaseResponse 패턴(ADR-0002) 준수
- `remote/api/.../AuthApi.kt` — Ktorfit 인터페이스
- `domain/model/.../{AuthTokens, UserProfile, LoginResult}.kt`
- `domain/repository/.../AuthRepository.kt`
- `domain/usecase/.../{LoginWithKakao, RefreshAccessToken, GetStoredTokens}UseCase.kt`
- `data/repositoryImpl/.../AuthRepositoryImpl.kt`
- `data/repositoryImpl/.../storage/SecureTokenStorage.kt` + `.android.kt` (EncryptedSharedPreferences) + `.ios.kt` (Keychain)
- `feature/login/` 신규 모듈 — LoginScreen/ViewModel + `KakaoAuthClient` expect/actual (Android `com.kakao.sdk:v2-user`, iOS SPM bridge)
- `feature/splash/` 신규 모듈 — SplashViewModel 자동 로그인 분기
- `core/navigation/.../Route.kt` — `LoginRoute`, `SplashRoute.Main` 추가
- `feature/main/.../MainScreen.kt` — 시작점 Splash로 교체, BottomBar 노출 분기
- `local.properties` / `remote/network/build.gradle.kts` — TMDB 제거, `challenge_api_base_url_{android,ios}` buildkonfig로 교체
- `gradle/libs.versions.toml` — `androidx-security-crypto`, `turbine`, `kotlinx-coroutines-test`, `kakao-sdk-user` 추가
- **2026-05-11 디자인 2차 반영 추가분**:
  - `core/designsystem/.../components/{StatusPillBadge, LabeledDivider, Divider, Spacer}.kt` — 신규 재사용 컴포넌트 4종
  - `feature/login/.../component/{SoulStampLogo, BackgroundDecor, ChallengeSection, ChallengeTitle, FooterAgreementText, LoginButtonSection}.kt` — Hero/CTA 분할 composable 6종
  - `feature/login/.../LoginScreen.kt` 교체 — placeholder → 풀세트 디자인
  - `feature/login/build.gradle.kts` — `compose.materialIconsExtended` 추가

**PM 레포**:
- `docs/features/auth-kakao/{spec.md, api-contract.md, design.md, backend-report.md, mobile-report.md, summary.md}`
- `docs/design-system/tokens.md` (신규) — Lovable styles.css 전역 토큰 카탈로그

## 테스트 결과

**백엔드** (2026-05-07 SDK 정렬 후, `:infra/:api/:app:compileKotlin` BUILD SUCCESSFUL):
- PhoneHasherTest: 3/3 passed
- GlobalExceptionHandlerTest: 5/5 passed
- AuthControllerTest: 5/5 passed (`code` → `kakaoAccessToken` 페이로드 정렬 반영)
- ChallengeServerApplicationTests: 1/1 passed (`kakao.rest-api-key`/`redirect-uri` env 제거 후에도 context 로드 OK)
- **AuthKakaoIntegrationTest: 0/5 실행, 5 skipped** (Docker 미가용 — `@EnabledIf("isDockerAvailable")`로 자동 skip). 시나리오 5건: 신규 / 기존 / phone미동의 / `/v2/user/me` 401(701) / `/v2/user/me` 5xx 1회 재시도 후 703.
- **합계: 14/14 passed, 5 skipped**

**모바일** (2026-05-11 디자인 2차 반영 후):
- LoginViewModelTest (commonTest): **4/4 passed** (Android Unit + iOS SimulatorArm64) — OAuth Success+서버 Success / OAuth Cancelled / OAuth Failure / OAuth Success+서버 Error. UI 변경에도 회귀 0.
- Android 빌드(`:feature:login:compileDebugKotlinAndroid`, `:composeApp:compileDebugKotlinAndroid`): BUILD SUCCESSFUL
- iOS 빌드(`:composeApp:linkDebugFrameworkIosSimulatorArm64`): BUILD SUCCESSFUL (28s)
- commonMain metadata: `:remote:*`, `:domain:*`, `:data:repositoryImpl`, `:feature:login`, `:feature:splash`, `:feature:main`, `:core:designsystem` 전부 BUILD SUCCESSFUL
- **시각 검증 미수행** — Compose UI 자동 검증 불가. 사용자가 Android 에뮬레이터/iOS Simulator에서 직접 확인 필요(backlog 등재).

## 결정 사항

1. **`KakaoLoginRequest`에서 `phoneNumber` 제거**: 서버가 Kakao API에서 직접 phone을 받으므로 모바일이 body에 실어 보낼 필요 없음. 모바일 변조/누락 가능성 제거. (api-contract 협의 이력 기록)
2. **`:api` → `:infra`(JpaRepository) 직접 참조**: MVP 단순성 위해 Port/Adapter 분리 생략. 향후 도메인 로직이 많아지면 `:domain`에 `UserRepository` 인터페이스 도입 검토.
3. **WebFlux를 `:infra`에만 추가**: Tomcat은 `:app`에서 유지. WebClient(+Netty HttpClient)만 사용, reactive 서버로 기동되지 않음.
4. **Kakao SDK 네이티브 연동 — 2026-05-07 Android+iOS 모두 완료**: Android는 `com.kakao.sdk:v2-user:2.20.6` 실연동(`KakaoAuthClient.android.kt` — `loginWithKakaoTalk` → fallback `loginWithKakaoAccount`, `AuthCodeHandlerActivity` Manifest, `KakaoSdk.init`, buildkonfig `KAKAO_NATIVE_APP_KEY`). iOS는 SPM `kakao-ios-sdk` 통합(`iOSApp.swift` `KakaoSDK.initSDK` + `onOpenURL` URL handler, `KakaoLoginHelper.swift` Swift→Kotlin bridge, `KakaoAuthClient.ios.kt` 실 구현, Info.plist `kakao$(KAKAO_NATIVE_APP_KEY)` xcconfig 변수). CocoaPods 미사용 — SPM 단일 채택.
5. **phone 해시 정규화 규칙**: `+82 10-1234-5678` / `010-1234-5678` / `01012345678` 모두 `+821012345678`로 정규화 후 SHA-256(64자 hex). 추후 `/friends/sync-contacts`가 동일 유틸(`PhoneHasher`) 재사용해 해시 일치 보장.
6. **에러 콜백 시그니처**: `AuthRepository.loginWithKakao/refreshAccessToken`이 `onError: (code: Int, message: String) -> Unit`을 받음 → ViewModel에서 code 분기(700/701/703)로 UI 처리. ADR-0002의 code 기반 에러 모델을 Domain 레이어까지 보존.
7. **앱 시작점 교체**: `HomeRoute.Main` → `SplashRoute.Main`. 자동 로그인 체크가 모든 진입에 선행.

## 디자인 결정 항목 (2026-05-08 pm-lead 확정)

`design.md` ⚠️ 9건 → ✅ 결정 완료. 상세는 `design.md`의 "✅ pm-lead 결정 사항" 표 참조. 요약:

1. **"그냥 구경만 할게요" 게스트 모드** — ❌ **제거**. Lovable에서도 삭제됨.
2. **통계 칩 숫자(12,847 / 238)** — ❌ **제거**. Lovable에서도 삭제됨.
3. **카카오 버튼 문구** — ✅ **"카카오로 시작하기"** (공식 가이드 준수).
4. **카카오 inline SVG 아이콘** — ❌ **제거** (텍스트 only, 상표 권리 회피).
5. **라이트 테마** — ✅ **dark-first 단일 테마 확정** (이미 colors.md §0).
6. **로딩 상태 디자인** — ✅ **현재 placeholder 유지** (검정 30% 오버레이 + `CircularProgressIndicator`). 정식 시안은 추후.
7. **부유 입자 / 외곽 회전 링** — ❌ **제거**. Lovable에서도 삭제됨. 불꽃 관련 애니메이션(`pulse-fire`/`wiggle`/`slide-up`)은 유지.
8. **"SOUL CONTRACT" 영문 뱃지** — ✅ 현재 디자인 유지.
9. **디자이너 시각 검증 6건** (colors.md §5) — ✅ mobile-dev 추정값 그대로 채택. 추후 미세 조정 시 별도 ADR.

> **모바일 LoginScreen.kt 반영 완료 (2026-05-11, 커밋 `fb68069` + `d7529cc`).** Lovable과 모바일 화면이 본 결정 표대로 동기화된 상태.

## 미해결 이슈

- [ ] **Android keyhash 카카오 콘솔 등록 여부 확인** (사용자 action). NATIVE APP KEY는 ✅ 발급+기입 완료. `debug.keystore` SHA1을 카카오 개발자 콘솔에 등록했는지 확인 필요.
- [ ] **Kakao 개발자 콘솔 `account_phone_number` scope 승인** (사용자 action, ADR-0008). 승인 전에는 `phone_verified=false` 케이스만 end-to-end 검증 가능.
- [ ] **Docker 기반 통합 테스트 수동 실행**: Docker Desktop 실행 후 `./gradlew :app:test --tests "*AuthKakaoIntegrationTest"`로 WireMock+Testcontainers 5케이스 검증.
- [ ] **실 단말 E2E smoke (Android+iOS)**: NATIVE APP KEY 기입 완료. 서버 8080에 띄우고 Android 에뮬레이터/실기기 + iOS Simulator/Device에서 카카오 로그인 → JWT 발급 end-to-end. 카카오톡 앱-간 인증 + 웹 fallback 둘 다.
- [ ] **LoginScreen 시각 검증** (2026-05-11 디자인 반영 후 신규): Android 에뮬레이터 + iOS Simulator에서 직접 확인. 특히 "영혼" brush 텍스트 / 🔥 wiggle / 스탬프 pulse-fire / 글로우·블롭 톤 / 노치 safeDrawing.
- [ ] **iOS SPM 카카오 SDK 버전 pin 적정성 확인**: `XCRemoteSwiftPackageReference`의 `requirement` 설정(`upToNextMajor` 등) 명시 여부 점검.
- [ ] **iOS Keychain 실기기 smoke**: `SecItemAdd/Copy` roundtrip 수동 확인.
- [ ] **LoginScreen Blur 미적용** (2026-05-11 신규): Lovable의 `blur-3xl`(48px) 등가가 Compose에 없어 alpha만으로 근사. 시각 차이 크면 `graphicsLayer { renderEffect = BlurEffect(...) }` 도입(Android API 31+ / KMP 호환성 검증 필요).
- [ ] **Material Icons Extended deprecation** (2026-05-11 신규): `compose.materialIconsExtended` 1.7.3 핀에 deprecation 경고. Material Symbols(vector resources) 마이그레이션 ADR 후보.
- [ ] **Glow shadow / 외광 효과** (2026-05-11 신규): tokens.md §3 `--shadow-glow`(0 0 30px primary 20%)는 Compose 기본 `shadow()`로 표현 어려움. Canvas glow 별도 작업 후보.
- [ ] **카카오 버튼 ripple 색** (2026-05-11 신규): 현재 Surface 기본 ripple 사용. design.md의 `BrandColors.KakaoYellowPressed` ripple 매핑은 디자이너 확인 후 별도 작업.
- [ ] **동시성 보호**: 같은 `kakao_id` 동시 로그인 시 UNIQUE 위반 재시도 로직 없음 (MVP 현실성 낮음, 향후 TODO).
- [x] **Refresh Token Rotation** ✅ 2026-05-28 해소 — [ADR-0009](../../decisions/0009-refresh-token-rotation.md) accepted, [auth-refresh-rotation](../auth-refresh-rotation/summary.md) 구현 완료.
- [ ] **별건: `application.yml:60` Swagger UI path 한글자음 'ㅠ' 오타** — Swagger UI 접근 안 될 가능성. 별도 정정.
- [ ] **별건: `:feature:login:check` detekt config 부재** (`/config/detekt/detekt.yml` 없음) — 인프라 티켓에서 처리.

## 참조

- [spec.md](./spec.md)
- [api-contract.md](./api-contract.md) (상태: confirmed — SDK 방식, `kakaoAccessToken` 페이로드)
- [change-log.md](./change-log.md) — 2026-05-07 contract drift 정정 + Android SDK 실연동 이력
- [design.md](./design.md)
- [backend-report.md](./backend-report.md)
- [mobile-report.md](./mobile-report.md)
- [tokens.md](../../design-system/tokens.md)
- ADR-0001 (Flyway), ADR-0002 (BaseResponse), ADR-0007 (환경 분리), ADR-0008 (Kakao scope), [ADR-0009](../../decisions/0009-refresh-token-rotation.md) (Refresh Token Rotation — 본 summary의 "Refresh Token Rotation" 미해결 이슈 해소)
