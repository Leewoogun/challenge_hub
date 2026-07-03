# Mobile Report — friends (2차 친구 추가)

- **feature-id**: friends
- **작성일**: 2026-07-02
- **담당**: mobile-dev (T4-T5 사용자 직접 커밋 / T6·T7a·T7b는 Agent Teams + 옵션 C)
- **상태**: implemented (모바일 working tree — 사용자 commit 대기)

## 구현 요약

friends 2차 spec(`spec-friend-add.md`) 모바일 트랙 전체 완료. T4(도메인/Data)와 T5(ViewModel/테스트)는 사용자가 직접 커밋(`81eccf0`), T6(designsystem), T7a(feature 화면/Navigation), T7b(`:core:invite` + KakaoLink 카톡 공유)는 pm-lead 오케스트레이션 하에 mobile-dev + Agent Teams(옵션 C — child claude 위임)로 진행. 카카오톡 초대는 spec §4.5 정정(2026-07-02)에 따라 **SDK Default `TextTemplate`** 방식으로 구현(콘솔 템플릿 등록 skip, `templateId` 발급 불필요).

## 변경된 모듈 & 파일 (누적 T4~T7b working tree)

### 신규 (~19)
| 모듈 | 파일 | 담당 task |
|---|---|---|
| `:core:designsystem` | `components/friend/FriendListItem.kt` (+ 3 Preview) | T6 |
| `:core:designsystem` | `components/friend/FriendRequestCard.kt` (+ 1 Preview) | T6 |
| `:core:invite` (신규 모듈) | `build.gradle.kts` | T7b |
| `:core:invite` | `commonMain/KakaoInviter.kt` (interface) | T7b |
| `:core:invite` | `commonMain/di/PlatformInviteModule.kt` (expect) | T7b |
| `:core:invite` | `androidMain/AndroidKakaoInviter.kt` | T7b |
| `:core:invite` | `androidMain/di/PlatformInviteModule.android.kt` | T7b |
| `:core:invite` | `iosMain/IosKakaoInviter.kt` (placeholder) | T7b |
| `:core:invite` | `iosMain/KakaoInviteBridge.kt` (handler injection) | T7b |
| `:core:invite` | `iosMain/di/PlatformInviteModule.ios.kt` | T7b |
| `:feature:friends` | `FriendsSearchScreen.kt` + `FriendsSearchRoute.kt` | T7a |
| `:feature:friends` | `component/FriendsSearchTopBar.kt` (+ Preview) | T7a |
| `:feature:friends` | `component/FriendSearchItem.kt` (+ 5 Preview: relation 5종) | T7a |
| `:feature:friends` | `component/FriendsActionRow.kt` (+ Preview) | T7a |
| `:feature:friends` | `component/ReceivedRequestsSection.kt` (+ Preview) | T7a |
| `:feature:friends` | `component/FriendsListSection.kt` (+ Preview) | T7a |
| `:feature:friends` | `commonTest/FakeUserInfoRepository.kt` | T7b |
| `:feature:friends` | `commonTest/FakeKakaoInviter.kt` | T7b |

### 수정 (~12)
- `settings.gradle.kts` — `:core:invite` 등록
- `composeApp/build.gradle.kts` — `:core:invite` 의존성
- `composeApp/App.kt` — Koin 초기화 확장
- `gradle/libs.versions.toml` — kakao-sdk-share dependency
- `:feature:friends/build.gradle.kts` — materialIconsExtended + `:core:invite` 의존
- `:core:navigation/Route.kt` — `FriendsRoute.Search` 추가
- `:feature:main/MainScreen.kt` — NavDisplay Search 분기
- `:feature:friends/FriendsRoute.kt` — koinViewModel + showMessage effect + onNavigateToSearch
- `:feature:friends/FriendsScreen.kt` — 받은 요청 인라인 + 친구 목록 + 액션 진입점 2개
- `:feature:friends/FriendsViewModel.kt` — `inviteFriend()` 추가 (T7b, `getUserInfo(CACHE_FIRST).firstOrNull()` + null 가드 + `KakaoInviter.sendInvite` 호출)
- `:feature:friends/commonTest/FriendsViewModelTest.kt` — 신규 invite 케이스 3건 추가
- `:core:designsystem/components/friend/FriendsEmptyState.kt` — `onClickInvite: (() -> Unit)? = null` prop 추가 (비파괴)

## 테스트 결과 (2026-07-02 실측)

### Android testDebugUnitTest
| 테스트 클래스 | 결과 | timestamp |
|---|---|---|
| `FriendsViewModelTest` | **10/10 PASS** (T7a 7 + 신규 invite 3) | 2026-07-02T02:07:28.317Z |
| `FriendsSearchViewModelTest` | **12/12 PASS** (회귀 0) | 2026-07-02T02:07:28.037Z |
| `HomeViewModelTest` | **10/10 PASS** (회귀 0) | 2026-07-02 |
| **종합** | **32/32 PASS, 회귀 0** | |

### 빌드
- Android + common: `:data:repositoryImpl` + `:core:invite` + `:feature:friends` + `:feature:home` + `:composeApp` — **BUILD SUCCESSFUL** (166 tasks, T7b 옵션 B 인터페이스 변경 후 전체 재컴파일)
- iOS: `:core:invite:compileKotlinIosSimulatorArm64` + `:feature:friends:compileKotlinIosSimulatorArm64` — **BUILD SUCCESSFUL**
- iOS 유닛테스트: **미실행** (Android 유닛 + iOS 컴파일까지가 검증 게이트, iOS 유닛은 backlog 후속)

## Working tree 상태

- 작업 브랜치: `main` 유지 (새 브랜치 없음)
- 변경분: 신규 ~19 + 수정 ~12, **새 커밋 0건** (모바일 dispatch git 금지 규칙 준수)
- 사용자가 T6·T7a·T7b 누적본을 직접 commit/push 결정

## 주요 결정 사항 (구현 중)

### T7b — SDK Default `TextTemplate` 방식 (spec §4.5 정정, 2026-07-02)

- **원안**: KakaoLink + 콘솔 커스텀 템플릿 (`templateId` 발급 + `KAKAO_INVITE_TEMPLATE_ID` 환경변수)
- **변경**: SDK Default `TextTemplate` — 앱 코드에서 직접 `TextTemplate(text, link, buttonTitle)` 정의
- **사유**: 사용자가 앱을 스토어 배포 안 하고 Firebase App Distribution으로 친구 4명 소규모 운용 결정. 카카오 콘솔 GUI 빌더에 텍스트형 미지원 (Feed/List/Commerce만). Default Template은 콘솔 등록 skip + `templateId` 불필요.

### T7b — HEAD 드리프트 대응 (옵션 B)

- 사용자 커밋(`8a5e725`)에서 `UserInfoRepository.observeUserInfoCache()` API가 인터페이스에서 제거된 상태 확인
- inviteFriend는 `observeUserInfoCache()` 재추가(A) 대신 **`getUserInfo(CACHE_FIRST).firstOrNull()`(B)** 로 처리 — HEAD 인터페이스 원복
- `.firstOrNull()` (mobile-dev 자체 판단): `.first()`는 cache=null일 때 무한 대기하는 flow 특성 회피

### T7a — 컴포넌트 분할 (design-system skill 정합)

- 메인 화면 sub-component 3개로 분할: `FriendsActionRow` / `ReceivedRequestsSection` / `FriendsListSection`
- 각 컴포넌트 `@Preview` 동반
- plan 명시 파일 수보다 많지만 design-system skill 규칙(단일 책임)에 정합

### T6 — 이미지 로더 부재 → 이니셜 placeholder

- 프로젝트에 Coil/Kamel/AsyncImage 없음
- `FriendListItem` / `FriendRequestCard`의 `profileImageUrl` 파라미터는 시그니처 그대로 받되 렌더는 닉네임 이니셜 + `secondary` bg
- 원격 이미지 로더 도입은 backlog

## 알려진 한계 / 후속 작업

- **iOS 카톡 공유 실제 연동**: 현재 iOS는 placeholder(`inviteHandler = null` → `Result.failure`). Xcode SPM에 `KakaoSDKShare` 추가 + Swift에서 `KakaoInviteBridge.inviteHandler`에 `ShareApi.shared.shareDefault(...)` 주입 필요 (사용자 Xcode 작업, `KakaoLoginHelper.swift` 패턴 참조).
- **iOS 유닛테스트 미실행**: T7b는 Android 유닛 + iOS 컴파일까지가 검증 게이트. iOS 유닛(`:feature:friends:iosSimulatorArm64Test`) 별도 실행 필요.
- **원격 이미지 로더 도입**: Coil3 KMP / Kamel / CMP Resources 검토. 친구 목록/검색 결과/내 프로필 화면 등에서 필요해질 것.
- **`IconTextButton iconSize` 파라미터화**: design.md는 액션 버튼 아이콘 14dp 명세, 공용 컴포넌트는 16dp 고정. 2dp 차이 정정 원하면 파라미터 추가 후속.
- **T4 (user-info HomeViewModel 통합) 사후 취소**: 사용자 결정으로 Home에 UserInfo 노출 안 함. inviteFriend는 초대 시점 fetch로 대체.

## 미해결 이슈

없음. iOS 실 연동은 사용자 Xcode 작업 대기.

## API 계약 대비 구현 차이

없음. `api-contract-friend-add.md` (status: confirmed) 7 endpoint와 모바일 API/Repository 1:1 정합. friends backend commit `bae8ab6` → `1d9d88d` push 완료.
