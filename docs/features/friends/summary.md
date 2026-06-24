# 친구 화면 (friends) — Summary (1차 1단계)

- **feature-id**: friends
- **완료일**: 2026-06-24
- **상태**: partially-completed (1차 1단계 빈 상태 UI만 — 백엔드/친구 목록/추가 흐름은 1차 2단계로 이연)

## 구현 개요

`:feature:friends` 모듈의 `PlaceholderScreen`을 친구가 없는 신규 사용자용 빈 상태 화면으로 교체. 백엔드 호출 0건, 진입과 동시에 `FriendsUiState.Data` 상태로 빈 상태 컴포넌트 노출.

핵심 결정 4건:
1. **스코프 좁힘** — 1차 1단계는 빈 상태 화면만. 친구 목록 / 추가 흐름 / 카드 탭 라우팅 / 백엔드 모델 / API 모두 1차 2단계로 이연. spec.md / plan.md 모두 이 분리를 명시.
2. **단일 출처 = design.md** — plan.md 헤드라인 폰트 `bold18`은 오기로 정정, design.md `bold16` 사용. design.md §3.1/§5/§6에서 강한 어조로 명시.
3. **stub CTA** — "친구 추가하기" 버튼의 onClick은 `viewModel.showMessage("준비 중입니다")`. Route에서 `LocalMainAction.current.showSnackBar`로 스낵바 표시. 1차 2단계 친구 추가 feature 진입 시 라우팅 연결.
4. **컴포넌트 위치 결정** — `FriendsEmptyState`는 `:core:designsystem`, `FriendsTopBar`는 `:feature:friends/component/`(home 패턴 답습). spec.md는 `FriendsTopBar`도 `:core:designsystem`이라 적었으나 plan.md 단계에서 home 패턴 답습으로 변경 — spec drift 1건.

## 화면 / UI 변경

- **FriendsScreen (Data, default)** — `ChallengeScaffold(topBar = FriendsTopBar) { FriendsEmptyState(...) }` 구조. 빈 상태 카드 1개:
  - 일러스트 영역: 64dp 박스 + 16dp radius + `primary.copy(alpha = 0.10f)` 배경 + `Icons.Filled.Group` 32dp(primary tint)
  - 헤드라인: "아직 친구가 없어요" / `typography.bold16` / `onBackground`
  - 서브 텍스트: "친구를 추가하고 함께 챌린지를 시작해보세요" / `typography.medium12` / `onSurfaceVariant`
  - CTA 버튼: "친구 추가하기" + `Icons.Filled.PersonAdd` 16dp / `primary` 배경 / 12dp radius / 52dp 높이 / `typography.bold14`
- **FriendsScreen (Loading)** — 중앙 `CircularProgressIndicator`. 1차 1단계엔 실제 진입 케이스 없음(진입과 동시에 Data) — 1차 2단계 API 호출 시 활용.
- **FriendsTopBar** — Surface + 56dp 높이 + 제목 "친구" + `typography.bold18`. 액션 슬롯 미노출. 1차 2단계 진입 시 `actions: (@Composable RowScope.() -> Unit)? = null` 추가 예상.
- **Lovable `src/routes/friends.tsx`** — `isEmpty = mockFriends.length === 0` 플래그 도입, mockFriends 5개 주석 처리(1차 1단계 빈 상태 노출용). `FriendsTopBar` sub-component + `FriendsEmptyState` sub-component 분리. Compose와 추상화 단위 정합.

## 주요 변경 파일

**모바일** (5 modify / 3 신규):
- `:feature:friends`
  - 신규 `component/FriendsTopBar.kt`
  - 신규 `commonTest/FriendsViewModelTest.kt`
  - 수정 `FriendsScreen.kt` (PlaceholderScreen → 빈 상태 + Loading 분기)
  - 수정 `FriendsRoute.kt` (`LocalMainAction.current` + `LaunchedEffect { uiEffect.collect }` + CTA stub → `viewModel.showMessage("준비 중입니다")`)
  - 수정 `FriendsViewModel.kt` (`// TODO: 의존성을 주입하세요.` 제거, `showMessage`를 `private` → `internal`로 전환, KDoc 1차 2단계 확장 경로 명시)
  - 수정 `contract/FriendsState.kt` (`Data(placeholder: Unit)` → `data object Data`)
  - 수정 `build.gradle.kts` (`commonMain.dependencies { compose.materialIconsExtended }` + `commonTest.dependencies { kotlin.test / kotlinx.coroutines.test / turbine }`)
- `:core:designsystem`
  - 신규 `components/friend/FriendsEmptyState.kt`

**디자인** (Lovable + PM hub):
- `oathbound-challenges/src/routes/friends.tsx` — 빈 상태 분기 추가, `FriendsTopBar` + `FriendsEmptyState` sub-component 분리
- `docs/features/friends/design.md` — 화면 구조 / 토큰 매핑 / Compose props 시그니처 / 모바일 강조 사항 / ⚠️ 확인 필요 6건 / 변경 이력

**PM hub** (4 신규 / 1 수정):
- 신규 `docs/features/friends/spec.md` (1차 1단계 스코프 명시, 후속 계획 별도)
- 신규 `docs/features/friends/plan.md` (Tasks 1-9 분해, 모바일 git 금지 메모리 규칙 반영)
- 신규 `docs/features/friends/design.md` (디자인 산출물)
- 신규 `docs/features/friends/summary.md` (본 문서)
- 수정 `docs/features/INDEX.md` (friends 상태 갱신 draft → partially-completed)

## 테스트 결과

- **모바일** (Android JVM, `:feature:{home,login,friends}:testDebugUnitTest`):
  - `feature:home` — **7/7 passed** (회귀 0)
  - `feature:login` — **4/4 passed** (회귀 0)
  - `feature:friends` — **2/2 passed** (신규 — init 시 Data 진입 / showMessage 호출 시 ShowMessage effect)
- **전체 모듈 컴파일** — `./gradlew compileDebugKotlinAndroid` BUILD SUCCESSFUL
- **시각 검증** — 사용자 영역(Android 에뮬레이터 + iOS Simulator). 디자이너 산출물(Lovable friends.tsx) ↔ 모바일 컴포넌트 시각 일치 확인 권장.

## 결정 사항

- **API 계약 변경 0건** — 본 1차 1단계엔 API 자체가 없음. 1차 2단계에서 `GET /api/v1/friends` 신규 협의.
- **빈 상태 컴포넌트 위치** — `:core:designsystem/components/friend/FriendsEmptyState.kt`. 향후 `HomeEmptyState`처럼 enum variant로 통합 가능성은 1차 2단계 진입 시 디자이너 점검.
- **TopBar 액션 슬롯** — 1차 1단계 미노출. 1차 2단계 진입 시 검색/알림 추가 검토.
- **single source of truth — design.md 우선** — plan.md `bold18` 오기를 design.md `bold16`이 단일 출처로 정정. mobile-dev 강조 사항(§5 #1)에 명시.
- **`showMessage` 가시성 = `internal`** — 코드 리뷰 피드백으로 `public` 금지, 모듈 외부 노출 안 함. test와 같은 모듈이라 호출 가능.
- **시각 타입 / 디자인 토큰** — 모두 `ChallengeTheme.colorScheme/typography/shape` 경유. 인라인 색·간격 0건.

## 미해결 이슈

- [ ] **1차 2단계 (별도 작업)**:
  - 백엔드 — `friendships(user_a_id, user_b_id, since)` 테이블 (V5) + `GET /api/v1/friends` + `FriendService` / `FriendshipRepository` + 통합 테스트 (Testcontainers Postgres, friends 0명 / N명 정렬 / 401)
  - 모바일 — `Friend` 도메인 모델, `FriendRepository`(Flow + onError + AuthEventBus 표준 패턴), `GetFriendsUseCase`, `FriendApi` / `FriendsResponse` DTO / `FriendsResponseMapper`, `FriendRepositoryImpl`, `:core:designsystem`에 `FriendCard`, `FriendsUiState`에 `friends: List<Friend>` 필드 + `Data.isEmpty` derived, `FriendsViewModelTest` 시나리오 확장(빈/N건/에러), `FriendsTopBar` `actions` slot 추가.
- [ ] **친구 추가 feature** (별도 — `friends-add` 등 후속 작업) — 닉네임 검색, 연락처 매칭(ADR-0008 — 카카오 scope 승인 외부 의존), 친구 요청 받기/보내기.
- [ ] **카드 탭 라우팅** — 친구 프로필 or 챌린지 생성 진입. 본 1차 2단계 이후 결정.
- [ ] **빈 상태 CTA 라우팅** — 1차 1단계엔 stub. 친구 추가 feature 진입 시 연결.
- [ ] **시각 검증** — Android 에뮬레이터 + iOS Simulator + Lovable 프리뷰 3방향 정합 확인.
- [ ] **모바일 working tree 사용자 커밋 대기** — 메모리 규칙(`feedback_mobile_dispatch_no_git.md`)에 따라 모바일 git 작업은 사용자 직접.
- [ ] **Lovable working tree 사용자 커밋 대기** — `oathbound-challenges/src/routes/friends.tsx` 변경.

## Spec drift

- **`FriendsTopBar` 위치** — spec.md(2026-06-24)는 `:core:designsystem/components/friend/FriendsTopBar.kt`로 적었으나, plan.md 단계에서 home 패턴(`HomeTopBar`가 `:feature:home/component/`) 답습으로 `:feature:friends/component/FriendsTopBar.kt`로 변경. topBar는 feature-specific 추상화라 feature 내부 위치가 자연스러움.

## 참조

- [spec.md](./spec.md)
- [plan.md](./plan.md)
- [design.md](./design.md)
