# user-info — Summary

- **feature-id**: user-info
- **완료일**: 2026-06-29
- **T4 취소 반영일**: 2026-07-02
- **상태**: completed (T4 HomeViewModel 통합 사용자 결정으로 사후 취소)

## 구현 개요

인증된 사용자의 본인 정보(id, kakaoId, nickname, profileImageUrl)를 백엔드 신규 endpoint(`GET /api/v1/users/me`)로 조회하고, 모바일이 DataStore에 캐시 + Home 화면에서 표시. CarOwnerRenew `UserInfoRepositoryImpl` 패턴을 우리 모바일 표준(`faae2cd` 이후 `onError: (String)` + Ktor Auth 전담)에 맞춰 구현. 부수 정리로 `UserProfile`(`userId, isNewUser` 보유) 모델을 `LoginResult`에 평탄화하여 의미 정합화.

진행 방식: **Agent Teams 첫 정식 사용**. backend-dev / mobile-dev 두 팀원 spawn → SendMessage 협업. mobile-dev는 옵션 C(child claude 위임)로 컨벤션 강제 발화.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|---|---|---|---|
| GET | `/api/v1/users/me` | Bearer JWT | implemented (challenge-server `ef784b1` push 완료) |

응답 data: `{ id: Long, kakaoId: Long, nickname: String, profileImageUrl: String? }`

## 화면 / UI 변경

> ⚠️ **2026-07-02 T4 사후 취소**: 아래 HomeViewModel 통합은 구현 완료됐으나 사용자가 커밋(`8a5e725`) 시점에 의도적으로 제외. HEAD에는 T4 통합 없음. `UserInfoRepository.observeUserInfoCache()` API도 인터페이스에서 제거됨. UserInfo 활용은 친구 T7b `FriendsViewModel.inviteFriend`(초대 시점 `getUserInfo(CACHE_FIRST).firstOrNull()`)로 이동. Home에서 닉네임/프사 노출은 후속 작업(내 프로필 화면)에서 결정.

- ~~**HomeViewModel** 확장~~ (사후 취소): `UserInfoRepository` 주입 + `init`에서 `getUserInfo(CACHE_FIRST)` 단발 트리거 + `observeUserInfoCache()` collect → `_userInfo` 갱신 → `combine(getHomeData, _userInfo)` 결합
- ~~**HomeUiState.Data** 확장~~ (사후 취소): `userInfo: UserInfo? = null` 필드 추가
- **HomeScreen.kt 미수정** — 유지

## 주요 변경 파일

### 백엔드 (challenge-server, commit `ef784b1`)

- `controller/user/UserController.kt` 신규 (`@GetMapping("/me")`)
- `controller/user/dto/UserInfoResponse.kt` 신규
- `service/user/UserService.kt` 신규 (`getMe(me): User` — `UserRepository.findById` 활용)
- `app/src/test/.../controller/user/UserControllerTest.kt` 신규
- `app/src/test/.../integration/UserIntegrationTest.kt` 신규

기존 `UserRepository.findById`(auth-refresh-rotation 작업) + `JwtAuthenticationFilter` 그대로 활용. V1 스키마 그대로 — **DB 마이그레이션 0건**. SecurityConfig 변경 불필요 (`.anyRequest().authenticated()` 자동 적용).

### 모바일 (challenge-app, working tree)

신규 12 + 수정 10 + 삭제 1. mobile-report.md 참조.

핵심:
- 도메인: `UserInfo`, `CacheStrategy`, `UserInfoRepository`
- Remote: `UserApi` (Ktorfit), `UserInfoResponse`, `UserInfoMapper`
- Local: `UserInfoPrefs` (`hasValue` sentinel), `UserInfoLocalDataSource` (interface) + `Impl`
- Data: `UserInfoRepositoryImpl` (옵션 1 패턴 — `flow { suspendOnSuccess + suspendOnFailureWithErrorHandling(onError: String) }`)
- Feature: `HomeViewModel` 통합 + `HomeUiState.Data.userInfo` + 신규 테스트 3건
- 부수: `LoginResult` 평탄화 + `UserProfile.kt` 삭제 + `LoginViewModel.kt:53` 정정
- 캐시 클리어: `TokenProviderImpl.clearTokens` + `LoginRepositoryImpl.clearTokens` 두 진입점에 `userInfoLocalDataSource.clear()`

### PM hub

- `docs/features/user-info/spec.md` (`33ffe88`) + 옵션 1 정정 노트
- `docs/features/user-info/plan.md` (`e70e013`) + 옵션 1 정정 노트
- `docs/features/user-info/api-contract.md` (`b4e666a`, status: confirmed)
- `docs/features/user-info/backend-report.md` (`5c8ef8f`)
- `docs/features/user-info/mobile-report.md` (T5 — 본 commit)
- `docs/features/user-info/summary.md` (T5 — 본 파일)
- `docs/features/INDEX.md` 갱신
- `docs/backlog.md` 후속 작업 등재

## 테스트 결과

### 백엔드
- 슬라이스 `UserControllerTest` **2/2 PASS** (정상 4필드 / UnauthorizedException → 401)
- 통합 `UserIntegrationTest` 4건 작성 + Docker 미가용 **4 skipped** (기존 패턴 일치 — `AuthKakaoIntegrationTest`, `FriendIntegrationTest` 동일)
- `./gradlew build`: **BUILD SUCCESSFUL**
- 기존 회귀 0

### 모바일
- `UserInfoRepositoryImplTest` (신규) **5/5 PASS** (CACHE_FIRST+캐시O/X, NETWORK_ONLY, API 실패 → onError, clear)
- `LoginViewModelTest` (회귀) **4/4 PASS** (LoginResult 평탄화 영향 없음 — `tokens: AuthTokens` 유지)
- `HomeViewModelTest` (확장) **10/10 PASS** (기존 7 + 신규 3, 회귀 0)
- **종합 19/19 PASS, 회귀 0**
- 9 모듈 `compileCommonMainKotlinMetadata` + `compileDebugKotlinAndroid` SUCCESS
- iOS 단위 테스트 / iOS framework link: 미수행 (backlog 등재)

## 결정 사항

### 핵심 결정 (브레인스토밍)

- **fetch 트리거 위치**: `HomeViewModel.init` (옵션 A). 신규 로그인 / 자동 로그인 둘 다 Home 진입 시 동일 흐름. Splash는 토큰 존재만 확인 후 직행 (기존 ADR-0009 흐름 유지).
- **캐시 만료**: 없음 (무조건 캐시). 명시적 갱신(networkOnly)은 1차에서 호출 지점 없음 (YAGNI).
- **로그아웃/세션만료 시 캐시 클리어**: `TokenProviderImpl` + `LoginRepositoryImpl`의 `clearTokens()` 두 진입점에 통합.
- **`observeUserInfoCache()` 패턴 도입**: 캐시 변경 자동 반영 + Home 외 다른 화면 확장성.
- **DTO/도메인 명명**: `UserInfo` (도메인), `UserInfoResponse` / `UserInfoData` (DTO), `UserApi` (Ktorfit). CarOwnerRenew 정합.
- **`UserProfile` 평탄화**: `LoginResult`에 `userId, isNewUser` 직접 보유 + `UserProfile.kt` 삭제. `tokens: AuthTokens`는 유지 (영향 범위 축소).

### 옵션 1 (현재 repo 표준) 적용 (T3 분석 단계 정정)

spec/plan 작성 시점에 `feedback_mobile_repository_pattern.md`가 옛 패턴(Throwable + SilentAuthExpired + AuthEventBus repository 내부)으로 stale 상태였음. mobile-dev가 T3 분석 단계에서 `challenge-app` 실제 코드(`faae2cd` 사용자 본인 commit) 확인 + 메모리 자체 갱신 + pm-lead 에스컬레이션. 사용자 승인 후 **옵션 1**(현재 표준 — `onError: (String)`, Ktor Auth 전담, 도메인 에러 클래스 없음) 진행:

- `UserInfoRepository.getUserInfo(onError: (String) -> Unit, cacheStrategy)` 시그니처
- `UserInfoError.kt` 생성 X (도메인 에러 클래스 없음)
- `SilentAuthExpired` sentinel 미사용
- `AuthEventBus` repository 미주입 — 401은 `KtorfitModule`의 Ktor Auth(bearer) 플러그인이 자동 refresh + 실패 시 `emitSessionExpired()`까지 전담

spec/plan의 옛 표현은 본 summary와 mobile-report에서 정정 노트로 남김.

### Agent Teams 첫 사용 — 학습 사항

- Agent tool의 `name` parameter로 spawn (PM hub `.claude/agents/{name}.md` 자동 적용). `subagent_type: "general-purpose"` + `name: "mobile-dev"` 형태.
- `SendMessage`로 팀원 간 직접 통신. 작업 지시/완료 보고/에스컬레이션 자연스러움.
- 팀원 `idle_notification`은 단순 mailbox 폴링 결과 — 작업 완료 신호 아님.
- mobile-dev의 child claude(`cd challenge-app && claude -p`) 위임 흐름이 옵션 C로 정상 작동: KMP 모듈 발견 + skill 적용 + 8 모듈 빌드 + 5 테스트 모두 발화.
- mobile-dev의 자체 메모리 갱신(`feedback_mobile_repository_pattern.md`) — `faae2cd` 기반 합리적 갱신. 권한 laundering 아님 (사용자 commit에 정확히 기반).

## 미해결 이슈

없음.

## 후속 작업 (`backlog.md` 등재)

- iOS 단위 테스트 (`:feature:home:iosSimulatorArm64Test`) + iOS framework link 검증
- UserInfo 활용 UI — 내 프로필 화면 (닉네임 / 프사 + 친구 초대 시 사용 등)
- 명시적 갱신 UX — pull-to-refresh / 카카오 프로필 변경 감지
- `SilentAuthExpired` 공통 위치 이동 (`:domain:model/auth/`) 검토 — 본 작업에서 사용 안 함이지만 친구 작업에서도 `faae2cd`로 삭제됨. 둘 다 후속 spec/plan에서 결정.
- `TokenLocalDataSource` / `AppSettingsLocalDataSource` interface 분리 (테스트 추가 시)

## 참조

- [spec.md](./spec.md) — 본 작업 spec
- [api-contract.md](./api-contract.md) — confirmed
- [plan.md](./plan.md) — 5 task 분해
- [backend-report.md](./backend-report.md) — T2
- [mobile-report.md](./mobile-report.md) — T3 + T4
- 관련 ADR: 0002 (BaseResponse), 0008 (Kakao scope), 0009 (Refresh Token Rotation)
- 참고 패턴: `/Users/hwamulman/hwamulman-workspace/CarOwnerRenew/data/repositoryImpl/.../UserInfoRepositoryImpl.kt`

## 후속 작업 (사용자 액션)

1. **모바일 commit/push** — 신규 12 + 수정 10 + 삭제 1 (`UserProfile.kt`). 한 commit으로 묶을지 분리할지 사용자 결정.
2. **PM hub push** — user-info commit 6건 (T1 spec, T1 contract, T1 plan, T2 backend-report, T3+T4 mobile-report, T5 summary)
3. **manual smoke** — 신규 가입 / 자동 로그인 / 로그아웃 시 캐시 클리어 검증 (디바이스)
4. **iOS 빌드 검증** (선택) — `xcodebuild compile` 또는 `:composeApp:linkDebugFrameworkIosSimulatorArm64`
