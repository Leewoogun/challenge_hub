# 하단 네비게이션 (bottom-navigation) — Summary

- **feature-id**: bottom-navigation
- **완료일**: 2026-05-11
- **상태**: completed
- **범위**: UI / Navigation 전용 (백엔드·API 없음)

> CmpSystem 템플릿 잔재(`:feature:ex1/ex2/ex3` + HOME 4탭)를 challenge 도메인 4탭(홈/친구/랭킹/MY)으로 전면 재구성. 신규 placeholder 모듈 3종(`:feature:friends/ranking/mypage`) 생성, ex1~3 모듈 통째 삭제, `ChallengeBottomBar` Material `NavigationBar` → `Surface + Row` 커스텀 구현으로 교체. ADR-0003 잔여 중 "ex1~3 제거" 해소.

## 구현 개요

Lovable `BottomNav.tsx` (4탭 / lucide 아이콘 / `bg-card/95 backdrop-blur-xl border-t`)를 Compose Multiplatform으로 옮기되, Material 컴포넌트(`NavigationBar`/`NavigationBarItem`)는 라벨 폰트(12.sp) / 좌우 패딩(56.dp) 강제로 디자인의 10.sp 라벨·py-1.5 패딩·alpha 95% surface를 정확히 맞출 수 없어 **`Surface + Row` 기반 커스텀 구현**으로 전환. `:core:navigation`의 sealed `Route`에 Friends/Ranking/MyPage 추가하고 Ex1~3은 SerializersModule까지 통째 제거. 각 placeholder 화면은 `:core:designsystem`에 신설한 `PlaceholderScreen(title, subtitle)` 재사용 컴포넌트로 통일.

## 엔드포인트

해당 없음 — UI / Navigation 전용 feature. `api-contract.md` 생성하지 않음.

## 화면 / UI 변경

- **ChallengeBottomBar (교체)**: `:feature:main/component/`. Material `NavigationBar` 폐기, `Surface(alpha 0.95) + HorizontalDivider + Row` 커스텀. 4탭: 홈 / 친구 / 랭킹 / MY. 아이콘 22.dp Material Filled, 라벨 10.sp inline `TextStyle`, gap 2.dp. Active=`primary`(#E97A3D) / Inactive=`onSurfaceVariant`(#9596A0). `WindowInsets.safeDrawing.only(Bottom)`로 iOS 홈 인디케이터 회피.
- **FriendsScreen / RankingScreen / MyPageScreen (신규, placeholder)**: 각 `:feature:friends/ranking/mypage`. 다크 배경 + 중앙 정렬 "준비 중" 텍스트 + 화면명. 모두 `PlaceholderScreen(title, subtitle)` 재사용. 향후 후속 feature(`friends-register` / `ranking-view` / `mypage-view`)에서 도메인 채울 예정.
- **MainScreen (수정)**: NavDisplay entryProvider에 Friends/Ranking/MyPage 추가, Ex1/Ex2/Ex3 제거. BottomBar 노출 분기는 Splash/Login에서 계속 숨김.
- **HomeScreen**: 변경 없음 (Movie 예제 그대로 — 후속 `home-feed` feature 범위).

## 주요 변경 파일

**모바일 (challenge-app):**

신규:
- `core/designsystem/.../components/PlaceholderScreen.kt` — 재사용 placeholder UI
- `feature/friends/` 모듈 통째 (build.gradle.kts + 6 kt: Route/Screen/ViewModel/State/Effect/Module)
- `feature/ranking/` 모듈 통째
- `feature/mypage/` 모듈 통째

수정:
- `core/navigation/.../Route.kt` — Ex1/Ex2/Ex3 sealed object 제거 + FriendsRoute.Main / RankingRoute.Main / MyPageRoute.Main 추가, SerializersModule 갱신
- `feature/main/.../MainScreen.kt` — NavDisplay entryProvider 갱신
- `feature/main/.../component/BottomNavItem.kt` — 4탭 enum (HOME/FRIENDS/RANKING/MYPAGE + Material 아이콘 + 한글 라벨 + "MY")
- `feature/main/.../component/ChallengeBottomBar.kt` — Surface+Row 커스텀 전면 교체
- `feature/main/build.gradle.kts` / `composeApp/build.gradle.kts` — 의존성 교체
- `composeApp/.../App.kt` — Koin module 등록 교체
- `settings.gradle.kts` — include 교체

삭제:
- `feature/ex1/`, `feature/ex2/`, `feature/ex3/` 디렉토리 통째 (16 파일)

## 테스트 결과

- **빌드 (7건 BUILD SUCCESSFUL)**:
  - `:core:navigation:compileCommonMainKotlinMetadata` (2m 47s cold)
  - `:feature:main:compileCommonMainKotlinMetadata` (3s)
  - `:feature:friends:compileCommonMainKotlinMetadata` (3s)
  - `:feature:ranking:compileCommonMainKotlinMetadata` (3s)
  - `:feature:mypage:compileCommonMainKotlinMetadata` (3s)
  - `:composeApp:compileDebugKotlinAndroid` (1m 13s)
  - `:composeApp:linkDebugFrameworkIosSimulatorArm64` (1m 26s)
- **단위 테스트**: `LoginViewModelTest` 4/4 passed (Android Unit + iOS SimulatorArm64). 회귀 0. JUnit XML 검증: `tests="4" skipped="0" failures="0" errors="0"`.
- **신규 ViewModel 테스트**: 없음 — placeholder ViewModel skeleton이라 의미 있는 테스트 대상 없음. 후속 도메인 feature에서 추가.
- **시각 검증**: 미수행 (Compose UI 자동 검증 불가, backlog 등재).

## 결정 사항

본 feature는 design-bridge가 권고한 7건을 그대로 채택 + 구현 중 발견된 1건 추가:

| # | 항목 | 결정 |
|---|------|------|
| 1 | 아이콘 출처 | **`materialIconsExtended`** (`Icons.Filled.{Home, Group, EmojiEvents, Person}`). 22.dp 작은 크기 + 다크 배경에서 lucide stroke 룩 손실 미미. |
| 2 | 라벨 표기 | **"홈" / "친구" / "랭킹" / "MY"** (한글 + "MY"만 영문). 10.sp 가독성 우위. |
| 3 | Placeholder 디테일 | **텍스트만** — `PlaceholderScreen(title, subtitle)` 재사용. |
| 4 | BottomBar 토큰화 | **`:feature:main` 인라인 유지** — 재사용 0, 추상화 비용 절약. |
| 5 | backdrop-blur 근사 | **alpha 95%만** — KMP 공통 API 한계. blur 자체 미적용. |
| 6 | 10.sp 라벨 | **inline `TextStyle`** — typography 슬롯 신설 안 함. |
| 7 | Active stroke | **색 분기만** — Compose `Icon` strokeWidth 런타임 제어 불가. |
| 8 | (구현 중 결정) ripple 처리 | **`rememberRipple(...)` 폐기** → `Modifier.clickable` + Material3 `LocalIndication` 자동 ripple. `rememberRipple` deprecation→error 회피. 디자인 영향 없음. |

**Material `NavigationBar`/`NavigationBarItem` 사용 금지 결정**: 라벨 폰트 / 좌우 패딩 강제로 디자인 토큰 정확 매핑 불가 → `Surface + Row` 커스텀 구현. design-bridge 1차 권고이며 mobile-dev가 채택.

> 본 결정 표가 모바일과 Lovable 사이의 진실 소스. Lovable `BottomNav.tsx` 변경은 발생하지 않음 — Lovable이 이미 진실 소스이고 모바일이 그를 따라간 방향. 디자이너 검토 후 lucide stroke 룩 차이가 시각 핵심이면 별도 ADR.

## 디자인 결정 항목 상세

`design.md`의 "✅ pm-lead 결정 사항 (2026-05-11)" 표 참조. design-bridge가 분석한 시각 토큰 매핑 / 아이콘 매핑 / 컴포넌트 매핑 / mobile-dev 질의 5건은 design.md 본문에 보존.

## 미해결 이슈

- [ ] **bottom-navigation 시각 검증** — 사용자 액션. Android 에뮬레이터 + iOS Simulator에서 다음 직접 확인:
  - 4탭 라벨/아이콘 시각 균형 (10.sp / 22.dp / gap 2.dp)
  - Active(`primary` #E97A3D) ↔ Inactive(`onSurfaceVariant` #9596A0) 색 대비
  - alpha 95% surface가 다크 배경(#26272F) 위에서 충분히 구분되는지 (blur 미적용)
  - iOS safe-area inset(홈 인디케이터) 침범 없음
  - 탭 전환 시 BottomBar active 갱신 정확도
  - Splash/Login 진입 시 BottomBar 숨김 유지
- [ ] **backdrop-blur 미적용** (design.md ✅ #5 결정의 후속) — 디자이너 검토 후 시각 핵심이면 platform actual blur(Android `Modifier.blur` API 31+ / iOS `UIVisualEffectView` interop) 도입 별건. LoginScreen Blur 미적용과 동일 카테고리 — 같이 묶어 처리 권장.
- [ ] **`./scripts/generate-feature.sh` 패키지 경로 버그** (별건 발견) — 39행 `SRC_DIR`이 `com/lwg/base/feature/...`로 잘못 설정됨(실제는 `com.lwg.challenge`). 본 작업은 스크립트 우회하여 ex1 패턴 따라 수동 생성. 향후 신규 feature 생성 시 차단되므로 별도 정정 필요.
- [ ] **`:feature:home` Movie 예제 잔존** — 본 feature 범위 외. 후속 `home-feed` feature에서 challenge 홈으로 교체.
- [ ] **`:feature:login` Preview annotation deprecation 경고 다수** (별건 발견) — 본 작업 빌드 중 발견. 정리 후보, 별도 위생 작업.
- [ ] **CLAUDE.md 모듈 구조 정정** (ADR-0003 잔여) — `:core:domain/network/data` → `:domain:*/:remote:*/:data:*`. 본 feature 범위 외, 즉시 가능한 위생 작업.

## 후속 feature 예고

- **`home-feed`** — `:feature:home`의 Movie 예제 → challenge 홈 화면 본격 교체
- **`friends-register`** — 친구 등록 (Kakao `account_phone_number` scope 승인 대기)
- **`ranking-view`** / **`mypage-view`** — 각 placeholder 채우기
- **`challenge-create-entry`** — 챌린지 생성 진입 결정 (FAB 등). Lovable BottomNav에 없는 항목.
- **`notifications`** — 알림 화면 + 진입

## 참조

- [spec.md](./spec.md)
- [design.md](./design.md) — design-bridge 분석 + ✅ pm-lead 결정 7건
- [mobile-report.md](./mobile-report.md)
- ADR-0003 (모바일 템플릿 초기화) — 본 feature가 잔여의 ex1~3 제거 해소
