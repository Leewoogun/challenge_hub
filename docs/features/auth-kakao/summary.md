# 카카오 로그인 (auth-kakao) — Summary

- **feature-id**: auth-kakao
- **최초 완료일**: 2026-04-24
- **최종 갱신**: 2026-05-07 (Android+iOS Kakao SDK 통합 완료 + 백엔드 SDK 정렬 — [change-log.md](./change-log.md))
- **상태**: partially-completed

> 서버·모바일(Android+iOS)·계약 모두 SDK 방식으로 정렬·통합 완료(2026-05-07). **Android+iOS 모두 Kakao SDK 실연동 완료** — Android `com.kakao.sdk:v2-user`, iOS SPM `kakao-ios-sdk`. 잔여: ① 디자인 2차 반영, ② Docker 기반 통합 테스트 수동 실행, ③ 실 단말 E2E smoke (Android+iOS 카카오톡 핸드오프 + 웹 fallback), ④ Android keyhash 카카오 콘솔 등록 여부 확인.

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

- **SplashScreen (신규)**: 앱 진입점. `:feature:splash`. 저장된 refresh 토큰 확인 → 자동 로그인 시도 → 성공 시 `HomeRoute.Main`, 실패/부재 시 `AuthRoute.Login`으로 분기.
- **LoginScreen (신규)**: `:feature:auth`. 카카오 옐로우(#FEE500) 버튼 + 그라데이션 배경 placeholder. code별 분기(700 스낵바 / 701 재로그인 다이얼로그 / 703 서버 에러 다이얼로그). Lovable 디자인 2차 반영은 후속 PR.
- **MainScreen**: 시작점 `HomeRoute.Main` → `SplashRoute.Main`으로 교체. Splash/Auth에서는 BottomBar 숨김.

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
- `feature/auth/` 신규 모듈 — LoginScreen/ViewModel + `KakaoLoginProvider` expect/actual stub
- `feature/splash/` 신규 모듈 — SplashViewModel 자동 로그인 분기
- `core/navigation/.../Route.kt` — `AuthRoute.Login`, `SplashRoute.Main` 추가
- `feature/main/.../MainScreen.kt` — 시작점 Splash로 교체, BottomBar 노출 분기
- `local.properties` / `remote/network/build.gradle.kts` — TMDB 제거, `challenge_api_base_url_{android,ios}` buildkonfig로 교체
- `gradle/libs.versions.toml` — `androidx-security-crypto`, `turbine`, `kotlinx-coroutines-test` 추가

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

**모바일** (2026-05-07 Android SDK 실연동 후):
- LoginViewModelTest (commonTest): **4/4 passed** (Android Unit + iOS SimulatorArm64) — OAuth Success+서버 Success / OAuth Cancelled / OAuth Failure / OAuth Success+서버 Error
- Android 빌드(`:feature:login:compileDebugKotlinAndroid`, `:composeApp:compileDebugKotlinAndroid`): ok
- iOS 빌드(`:composeApp:linkDebugFrameworkIosSimulatorArm64`): ok (Kotlin 측. Pod/SPM Swift 통합은 별도)
- commonMain metadata: `:remote:*`, `:domain:*`, `:data:repositoryImpl`, `:feature:login`, `:feature:splash`, `:feature:main` 전부 ok

## 결정 사항

1. **`KakaoLoginRequest`에서 `phoneNumber` 제거**: 서버가 Kakao API에서 직접 phone을 받으므로 모바일이 body에 실어 보낼 필요 없음. 모바일 변조/누락 가능성 제거. (api-contract 협의 이력 기록)
2. **`:api` → `:infra`(JpaRepository) 직접 참조**: MVP 단순성 위해 Port/Adapter 분리 생략. 향후 도메인 로직이 많아지면 `:domain`에 `UserRepository` 인터페이스 도입 검토.
3. **WebFlux를 `:infra`에만 추가**: Tomcat은 `:app`에서 유지. WebClient(+Netty HttpClient)만 사용, reactive 서버로 기동되지 않음.
4. **Kakao SDK 네이티브 연동 — 2026-05-07 Android+iOS 모두 완료**: Android는 `com.kakao.sdk:v2-user:2.20.6` 실연동(`KakaoAuthClient.android.kt` — `loginWithKakaoTalk` → fallback `loginWithKakaoAccount`, `AuthCodeHandlerActivity` Manifest, `KakaoSdk.init`, buildkonfig `KAKAO_NATIVE_APP_KEY`). iOS는 SPM `kakao-ios-sdk` 통합(`iOSApp.swift` `KakaoSDK.initSDK` + `onOpenURL` URL handler, `KakaoLoginHelper.swift` Swift→Kotlin bridge, `KakaoAuthClient.ios.kt` 실 구현, Info.plist `kakao$(KAKAO_NATIVE_APP_KEY)` xcconfig 변수). CocoaPods 미사용 — SPM 단일 채택.
5. **phone 해시 정규화 규칙**: `+82 10-1234-5678` / `010-1234-5678` / `01012345678` 모두 `+821012345678`로 정규화 후 SHA-256(64자 hex). 추후 `/friends/sync-contacts`가 동일 유틸(`PhoneHasher`) 재사용해 해시 일치 보장.
6. **에러 콜백 시그니처**: `AuthRepository.loginWithKakao/refreshAccessToken`이 `onError: (code: Int, message: String) -> Unit`을 받음 → ViewModel에서 code 분기(700/701/703)로 UI 처리. ADR-0002의 code 기반 에러 모델을 Domain 레이어까지 보존.
7. **앱 시작점 교체**: `HomeRoute.Main` → `SplashRoute.Main`. 자동 로그인 체크가 모든 진입에 선행.

## 디자인 확인 필요 항목 (design-bridge 플래그)

`design.md`에서 ⚠️ 로 플래그된 6개 — pm-lead가 사용자와 확정 필요:

1. **"그냥 구경만 할게요" 게스트 모드** — Lovable login.tsx에 존재하나 spec에 없음. 제거 유력.
2. **통계 칩 숫자(12,847 / 238)** — 하드코딩 더미인지 API 제공인지 불명.
3. **"카카오로 영혼 등록하기" 버튼 문구** — 카카오 브랜드 가이드 공식 문구("카카오로 시작하기" 등)와 맞는지 검토.
4. **카카오 inline SVG 아이콘** — 공식 Kakao 리소스로 교체 필요 여부.
5. **라이트 테마** — 다크 전용 확정인지 추후 ADR 필요.
6. **로딩 상태 디자인** — login.tsx에 로딩 UI 부재. LoginScreen의 `LoadingIndicator` placeholder 유지.

## 미해결 이슈

- [ ] **Android keyhash 카카오 콘솔 등록 여부 확인** (사용자 action). NATIVE APP KEY는 ✅ 발급+기입 완료. `debug.keystore` SHA1을 카카오 개발자 콘솔에 등록했는지 확인 필요.
- [ ] **Kakao 개발자 콘솔 `account_phone_number` scope 승인** (사용자 action, ADR-0008). 승인 전에는 `phone_verified=false` 케이스만 end-to-end 검증 가능.
- [ ] **Docker 기반 통합 테스트 수동 실행**: Docker Desktop 실행 후 `./gradlew :app:test --tests "*AuthKakaoIntegrationTest"`로 WireMock+Testcontainers 5케이스 검증.
- [ ] **실 단말 E2E smoke (Android+iOS)**: NATIVE APP KEY 기입 완료. 서버 8080에 띄우고 Android 에뮬레이터/실기기 + iOS Simulator/Device에서 카카오 로그인 → JWT 발급 end-to-end. 카카오톡 앱-간 인증 + 웹 fallback 둘 다.
- [ ] **iOS SPM 카카오 SDK 버전 pin 적정성 확인**: `XCRemoteSwiftPackageReference`의 `requirement` 설정(`upToNextMajor` 등) 명시 여부 점검.
- [ ] **design.md 2차 반영**: LoginScreen placeholder를 Lovable 토큰/로고/그라데이션으로 교체 — 별도 PR.
- [ ] **iOS Keychain 실기기 smoke**: `SecItemAdd/Copy` roundtrip 수동 확인.
- [ ] **동시성 보호**: 같은 `kakao_id` 동시 로그인 시 UNIQUE 위반 재시도 로직 없음 (MVP 현실성 낮음, 향후 TODO).
- [ ] **Refresh Token Rotation**: 로그인 시마다 새 refresh 발급되지만 옛 것 무효화 없음 — ADR-0009(예정)에서 결정.
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
- ADR-0001 (Flyway), ADR-0002 (BaseResponse), ADR-0007 (환경 분리), ADR-0008 (Kakao scope)
