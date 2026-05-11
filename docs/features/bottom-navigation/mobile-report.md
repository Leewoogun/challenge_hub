# Mobile Report — bottom-navigation

- **작성일**: 2026-05-08
- **작성자**: mobile-dev
- **대상 레포**: `/Users/hwamulman/woogunProject/challenge/challenge-app`
- **대상 브랜치**: `main` (체크아웃된 그대로, 신규 브랜치 미생성)

## 구현 요약

challenge 메인 셸 BottomBar 를 CmpSystem 잔재(HOME/Ex1/Ex2/Ex3) 4탭 → challenge 도메인 4탭(홈/친구/랭킹/MY) 으로 전면 재구성. design.md ✅ 결정 7건 그대로 채택.

- `:core:navigation`의 `Route` sealed interface 에 `FriendsRoute`/`RankingRoute`/`MyPageRoute` 3 개 추가, `Ex1Route`/`Ex2Route`/`Ex3Route` 제거. `routeSerializersModule` 동시 갱신.
- 신규 feature 모듈 3 개(`:feature:friends`, `:feature:ranking`, `:feature:mypage`) skeleton 생성. 각 모듈은 State/Effect/ViewModel/Route/Screen/Module 6 파일로 ex1 패턴과 동일하지만 ViewModel 초기 상태를 `Data()`로 둬서 진입 즉시 placeholder 노출.
- Placeholder 는 `:core:designsystem`의 신규 공통 컴포저블 `PlaceholderScreen(title, subtitle="준비 중")`으로 추상화. 다크 배경 + bold18 화면명 + medium14 보조 한 줄. 후속 feature(`home-feed`, `friends-register` 등) 진입 전에도 재사용 가능.
- `ChallengeBottomBar` 를 `NavigationBar` → `Surface + Column + Row` 커스텀 구현으로 교체. Material 컴포넌트의 12.sp 라벨 / 56.dp 패딩 강제를 우회하여 디자인의 10.sp 라벨 / py-1.5 / `surface.copy(alpha=0.95f)` 카드 색을 정확히 매핑. Active(`primary`) vs Inactive(`onSurfaceVariant`) 는 색 분기만(`strokeWidth` 분기 없음 — Compose 한계).
- `MainScreen.kt` 의 `NavDisplay.entryProvider` 에서 Ex1/Ex2/Ex3 NavEntry 제거하고 Friends/Ranking/MyPage NavEntry 추가. BottomBar 노출 분기 `currentRoute !is SplashRoute && currentRoute !is LoginRoute` 는 그대로 두면 신규 4 라우트 자동 노출되므로 변경 없음.
- `:feature:ex1/ex2/ex3` 디렉토리 `rm -rf` 로 삭제, `settings.gradle.kts` / `:composeApp/build.gradle.kts` / `:feature:main/build.gradle.kts` / `:composeApp/.../App.kt` (Koin 모듈 등록) 4 곳에서 ex1~3 참조 제거 + friends/ranking/mypage 추가.

### 빌드 중 발견된 이슈 1 건 (대응 완료)

- 1차안에서 `Modifier.clickable(indication = rememberRipple(...))` 사용 → Material `rememberRipple` 이 deprecation 을 넘어 error 처리되어 컴파일 실패. `Modifier.clickable(onClick = ...)` 로 단순화(Material3 테마 컨텍스트의 `LocalIndication`이 자동 ripple 처리).

## 사용한 모바일 레포 스킬

- `modify-feature` — 기존 `ChallengeBottomBar` / `BottomNavItem` / `MainScreen` 교체 절차(영향 레이어 분석 → 변경 계획 → 레이어별 수정 → 빌드 검증).
- `navigation` — `Route.kt` sealed 갱신, `MainScreen.kt` NavDisplay 등록, `:feature:main/build.gradle.kts` 의존성 갱신 4 곳 체크리스트.
- `feature` — 신규 3 모듈(friends/ranking/mypage)의 contract/ViewModel/Route/Screen/di 6 파일 패턴.
- `design-system` (자동) — `ChallengeTheme.colorScheme` / `typography` 슬롯 매핑 규칙 준수.

`./scripts/generate-feature.sh` 는 사용하지 않음. 스크립트가 `com/lwg/base/feature/...` 경로(잘못된 베이스 패키지)에 파일을 생성하는 버그가 있어 ex1 패턴을 참고하여 수동으로 정확한 `com/lwg/challenge/feature/{name}` 경로로 작성. → 별건 발견 항목 참조.

## 변경된 파일

### 신규 (12 파일)

- `core/designsystem/src/commonMain/kotlin/com/lwg/challenge/designsystem/components/PlaceholderScreen.kt`
- `feature/friends/build.gradle.kts`
- `feature/friends/.gitignore`
- `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsRoute.kt`
- `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsScreen.kt`
- `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsViewModel.kt`
- `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/contract/FriendsState.kt`
- `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/contract/FriendsEffect.kt`
- `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/di/FriendsModule.kt`
- `feature/ranking/` (위와 동일 6 파일 패턴, Ranking 명)
- `feature/mypage/` (위와 동일 6 파일 패턴, MyPage 명)

> 신규 feature 3 개 × 6 파일 + .gitignore 1 + build.gradle.kts 1 = 8 파일 × 3 = 24 파일, PlaceholderScreen 1 파일 ⇒ 총 신규 25 파일.

### 수정 (7 파일)

- `core/navigation/src/commonMain/kotlin/com/lwg/challenge/navigation/Route.kt` — Ex1~3 sealed object 제거, FriendsRoute/RankingRoute/MyPageRoute 추가. `routeSerializersModule` 동시 갱신.
- `feature/main/src/commonMain/kotlin/com/lwg/challenge/feature/main/MainScreen.kt` — import 갱신 + NavDisplay entryProvider 4 분기 갱신.
- `feature/main/src/commonMain/kotlin/com/lwg/challenge/feature/main/component/BottomNavItem.kt` — 4 항목 갱신(HOME/FRIENDS/RANKING/MYPAGE + Material 아이콘 + 한글 라벨).
- `feature/main/src/commonMain/kotlin/com/lwg/challenge/feature/main/component/ChallengeBottomBar.kt` — `NavigationBar` → `Surface+Row` 커스텀 전면 교체.
- `feature/main/build.gradle.kts` — ex1~3 의존성 제거, friends/ranking/mypage 추가. `compose.materialIconsExtended` 는 기존부터 존재.
- `composeApp/build.gradle.kts` — 동상 의존성 교체.
- `composeApp/src/commonMain/kotlin/com/lwg/challenge/App.kt` — Koin Ex1Module/Ex2Module/Ex3Module 제거, FriendsModule/RankingModule/MyPageModule 추가.
- `settings.gradle.kts` — `include(":feature:ex1/ex2/ex3")` 줄 제거, `include(":feature:friends/ranking/mypage")` 추가.

### 삭제

- `feature/ex1/` 디렉토리 통째 (build.gradle.kts + 6 kt 파일 + .gitignore)
- `feature/ex2/` 디렉토리 통째 (동상)
- `feature/ex3/` 디렉토리 통째 (동상)
- `Route.kt` 의 `Ex1Route`/`Ex2Route`/`Ex3Route` sealed object 3 건
- `Route.kt` 의 `routeSerializersModule` SerializersModule 등록 3 건
- `settings.gradle.kts` 의 `include(":feature:ex1/ex2/ex3")` 3 줄
- `App.kt` 의 `Ex1Module/Ex2Module/Ex3Module` import + Koin modules 등록 6 줄
- `feature/main/build.gradle.kts` 의 `implementation(projects.feature.ex1/ex2/ex3)` 3 줄
- `composeApp/build.gradle.kts` 의 동상 3 줄

## 빌드 결과

| 명령 | 결과 | 소요 |
|---|---|---|
| `:core:navigation:compileCommonMainKotlinMetadata` | BUILD SUCCESSFUL | 2m 47s (configuration cache cold start 포함) |
| `:feature:main:compileCommonMainKotlinMetadata` | BUILD SUCCESSFUL | 3s (warm) |
| `:feature:friends:compileCommonMainKotlinMetadata` | BUILD SUCCESSFUL | 3s (warm) |
| `:feature:ranking:compileCommonMainKotlinMetadata` | BUILD SUCCESSFUL | 3s (warm) |
| `:feature:mypage:compileCommonMainKotlinMetadata` | BUILD SUCCESSFUL | 3s (warm) |
| `:composeApp:compileDebugKotlinAndroid` | BUILD SUCCESSFUL | 1m 13s |
| `:composeApp:linkDebugFrameworkIosSimulatorArm64` | BUILD SUCCESSFUL | 1m 26s |

> 빌드 경고: `materialIconsExtended` deprecation(`:feature:login` 도 동일 백로그), `rememberRipple` deprecation은 본 작업에서 제거됨, `Preview` annotation 경고는 기존 `:feature:login` 잔존(별건). 본 feature 신규 코드에서는 모두 정리됨.

## 테스트 결과

- `:feature:login:allTests` — **4/4 passed** (회귀 0). `LoginViewModelTest` 의 카카오 OAuth 4 시나리오(성공/Failure/Cancelled/서버 실패) 모두 그대로 통과.

```
<testsuite name="com.lwg.challenge.feature.login.LoginViewModelTest"
           tests="4" skipped="0" failures="0" errors="0" time="0.091"/>
```

- 신규 3 feature(friends/ranking/mypage)는 placeholder 수준이라 ViewModel 테스트는 미작성. 후속 feature(`friends-register` 등)에서 도메인 도입 시 함께 추가 예정.

## 시각 검증

**미수행**. 사용자가 Android 에뮬레이터 / iOS Simulator 에서 직접 확인 필요.

권장 체크포인트:

- 4 탭 라벨/아이콘 시각 균형 — 10.sp 라벨 가독성, 22.dp 아이콘과 라벨 사이 2.dp 간격.
- Active(`primary` = `#E97A3D`) ↔ Inactive(`onSurfaceVariant` = `#9596A0`) 색 대비.
- alpha 95% `surface`(`#2F303A` 95%) 가 다크 배경(`#26272F`) 위에서 충분히 구분되는지 — blur 미적용이라 디자이너 사후 검토 권장.
- iOS safe-area inset (홈 인디케이터) 침범 없는지 — `WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom)` 적용.
- 탭 전환 시 BottomBar active 갱신 정확도(Home → Friends → Ranking → MyPage 순환).
- Splash/Login 화면 진입 시 BottomBar 숨김 유지(기존 분기 보전).

## Working tree 상태

- 작업 브랜치: `main` (기존 체크아웃, 새로 안 만듦)
- 변경 파일 수: 7 modified + 25 new + 16 deleted (디렉토리 3 개 통째)
- staged/unstaged 그대로 둠 — git add/commit/push/PR 모두 미수행. 사용자 처리 영역.

## 미해결 이슈

- **`materialIconsExtended` deprecation**: `Icons.Filled.Home/Group/EmojiEvents/Person` 사용은 design.md 결정대로지만, 이 artifact 는 1.7.3 핀고정 + 업데이트 중단. `:feature:login`이 같은 문제로 백로그 등재되어 있으며, 본 feature 도 동일 처리 권장 — Material Symbols(vector resources) 마이그레이션 ADR 후보.
- **`backdrop-blur` 미적용**: design.md ✅ #5 결정으로 alpha 95%만 근사. iOS `UIVisualEffectView` + Android `Modifier.blur` platform-specific actual 구현은 backlog.
- **10.sp 라벨 inline `TextStyle`**: design.md ✅ #6 결정으로 typography 슬롯 신설 안 함. 다른 사용처가 누적되면 `medium10` 슬롯 추가 검토 필요(backlog).
- **placeholder 3 화면 ViewModel 무의미**: `FriendsViewModel`/`RankingViewModel`/`MyPageViewModel`은 의존성 없이 `Data()` state 만 발행. 후속 feature(`friends-register`, `ranking-view`, `mypage-view`)에서 도메인 로직과 함께 교체될 임시 코드. 점검 시 제거/교체 필요.

## API 계약 대비 구현 차이

해당 없음. 본 feature 는 UI/Navigation 전용으로 백엔드 API 호출 없음.

## 별건 발견

- **`./scripts/generate-feature.sh` 버그**: 스크립트가 `SRC_DIR="$FEATURE_MODULE_DIR/src/commonMain/kotlin/com/lwg/base/feature/$LOWER_FEATURE_NAME"`로 잘못된 베이스 패키지(`com.lwg.base`)에 디렉토리를 생성. 실제 프로젝트는 `com.lwg.challenge`. 스크립트 내부의 `BASE_PACKAGE="com.lwg.challenge"` 변수와 `SRC_DIR` 경로의 `com/lwg/base/` 가 불일치. 본 작업에선 스크립트 우회하여 수동 생성. 스크립트 수정은 별도 backlog 등재 권장. (위치: `/Users/hwamulman/woogunProject/challenge/challenge-app/scripts/generate-feature.sh` 39 행)
- **`Preview` annotation deprecation 경고 다수**: `:feature:login` 의 컴포넌트들이 `org.jetbrains.compose.ui.tooling.preview.Preview` 가 아닌 deprecated 경로 사용. 본 feature 범위 외이나 후속 정리 필요.
