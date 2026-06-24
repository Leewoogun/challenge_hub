# Design — friends (1차 1단계)

- **디자인 소스**: `/Users/hwamulman/woogunProject/challenge/challenge-design/oathbound-challenges`
- **참조 route**: `src/routes/friends.tsx` (수정됨 — 빈 상태 분기 + `FriendsEmptyState` sub-component 신규)
- **참조 컴포넌트**: `src/components/BottomNav.tsx`, `src/routes/index.tsx` (`HomeEmptyState` 톤 정합 기준)
- **전역 토큰**: [`docs/design-system/tokens.md`](../../design-system/tokens.md), [`colors.md`](../../design-system/colors.md)
- **스냅샷 일시**: 2026-06-24
- **대상 화면 수**: 1 화면(FriendsScreen) × 2 상태 (empty / default)
- **본 단계 신규 컴포넌트**: `FriendsEmptyState`, `FriendsTopBar` — 모두 `:core:designsystem` 또는 `:feature:friends/component` 추가 제안
- **본 단계 범위 제한**: 1차 1단계는 **친구 0명 빈 상태**만. 친구 N명 default 상태(친구 카드 LazyColumn)는 §4에 디자인 정합 가이드만 기록(1차 2단계 입력).

---

## 0. 변경 요약 (Lovable friends.tsx)

기존 `src/routes/friends.tsx`는 친구 5명이 하드코딩된 default 상태만 표현. 본 작업으로 다음을 반영:

1. `mockFriends` 배열을 빈 배열로 두고 주석 처리(`isEmpty = mockFriends.length === 0`). 빈 상태가 default 프리뷰가 되도록.
2. 빈 상태일 때 `FriendsEmptyState` (신규 sub-component) 표시. variant 분기 ❌ — 친구 빈 상태는 한 종류(친구 0명)뿐.
3. **TopBar 액션 슬롯(UserPlus / Search input)을 빈 상태일 때 미노출**. 친구 0명에서 검색·신규 추가 진입점은 빈 상태 카드의 CTA로 일원화한다. 1차 2단계 진입 시 복귀.
4. 빈 상태 카드의 stub CTA "친구 추가하기"는 onClick 무동작(모바일은 "준비 중입니다" 스낵바). 1차 2단계 친구 추가 feature 진입 시 라우팅 연결.

> Lovable의 `mockFriends` 상수는 비어있는 default + 주석 처리된 샘플 데이터 — `mockFriends` 배열에 항목을 살리면 친구 카드 default 상태를 다시 프리뷰할 수 있음. 1차 2단계 진입 시 GET /api/v1/friends 응답으로 교체된다.

---

## 1. FriendsScreen — empty (친구 0명, 1차 1단계 본 단계 범위)

- **트리거**: `friends.isEmpty()` — 1차 1단계 모든 사용자(백엔드 미구현이라 항상 충족)
- **의도**: 친구 탭 첫 진입 사용자가 "친구 추가" 액션 1개로 자연스럽게 다음 단계 인지하도록 유도. 홈의 `HomeEmptyState(first_user)`와 결을 맞춰 "데이터 없음"이 아닌 "이제 시작" 톤.
- **레이아웃** (위→아래):
  1. **Sticky Header** (`bg-background/80 backdrop-blur-xl`, 좌우 20.dp 패딩 + safe-top inset)
     - 좌측: "친구" 라벨 (text-xl extrabold) — 홈 `HomeTopBar`와 동일 패턴(아이콘 미사용)
     - 우측: **(빈 상태) 미노출** — 1차 2단계 진입 시 UserPlus 액션 + 검색 input 복귀
  2. **본문 영역**: 화면 가로 패딩 `px-5` (20.dp) + 상단 `mt-6` (24.dp)
  3. **FriendsEmptyState 카드** (`glass-card`, 내부 24.dp 패딩, 세로 중앙 정렬)
     - 일러스트 자리: 64×64.dp 라운드 16.dp, `primary/10%` 배경 + `Users` 32.dp(primary). 추후 일러스트 자산 합류 시 교체(backlog).
     - 헤드라인: "아직 친구가 없어요" (text-base bold)
     - 서브라인: "친구를 추가하고 함께 챌린지를 시작해보세요" (12sp muted)
     - CTA 1버튼 `size="full"` (전체 폭, h-13 ≈ 52.dp 높이): `default` (primary) variant + `UserPlus` 아이콘 + "친구 추가하기"
  4. **BottomNav** (이미 구현됨, bottom-navigation feature 참조 — `:feature:main`의 `ChallengeBottomBar`)
- **상호작용**:
  - "친구 추가하기" 탭 → 1차 1단계 stub (모바일은 `showSnackBar("준비 중입니다")`). 1차 2단계 친구 추가 feature 도입 시 라우팅 연결.
- **토큰**: `colorScheme.background` / `colorScheme.surface` (glass-card) / `colorScheme.primary` / `colorScheme.onPrimary` / `colorScheme.onBackground` / `colorScheme.onSurfaceVariant` / `colorScheme.primary.copy(alpha=0.10f)` (일러스트 배경) / `typography.bold18` (TopBar "친구" — 홈 패턴) / `typography.bold16`(헤드라인) / `typography.medium12`(서브라인) / `typography.bold14`(CTA 라벨)
- **상태**: empty (이 절)
- **모바일 대응**:
  - `app-container max-w-[430px]` 무시 → 화면 full-width.
  - `sticky` 헤더 + `backdrop-blur-xl` → Compose는 alpha 80% + 1.dp 보더 근사(home-feed와 동일 결정).
  - `animate-slide-up` 진입 애니메이션 → Compose `AnimatedVisibility` + `slideInVertically` 선택 적용(빈 상태 카드 1개라 성능 영향 없음).

---

## 2. FriendsScreen — default (친구 N명, 1차 2단계 입력만)

> **본 절은 1차 1단계 구현 범위 밖.** 1차 2단계 친구 목록 feature 진입 시 본 절을 spec.md / 모바일 트랙 입력으로 활용. 1차 1단계 모바일은 `Loading / Data` 두 슬롯만 사용하며 `Data` 진입 시 항상 `FriendsEmptyState` 표시.

- **트리거**: `friends.isNotEmpty()`
- **의도**: 친구별 누적 전적(승/패/무/연승) + 1:1 대결 신청 진입점 제공.
- **레이아웃** (위→아래):
  1. Sticky Header — TopBar 액션 슬롯 노출(UserPlus 단일 아이콘 버튼) + 본문 첫 줄에 검색 input (`bg-secondary rounded-xl`, 좌측 Search 아이콘 16.dp).
  2. 친구 카드 LazyColumn (`px-5 space-y-2` ≈ 8.dp 간격).
- **친구 카드 시각 토큰 매핑** (1차 2단계 mobile-dev 인계용):

  | 항목 | Lovable | Compose 매핑 | 비고 |
  |---|---|---|---|
  | 카드 컨테이너 | `glass-card p-4 flex items-center gap-3` | `colorScheme.surface` + 1.dp `outline` border + `RoundedCornerShape(16.dp)` + `Modifier.padding(16.dp)` + `Arrangement.spacedBy(12.dp)` | tokens.md §4 (radius-xl = 16) |
  | 프로필 placeholder | `w-12 h-12 rounded-xl bg-secondary` + emoji `text-xl` | 48.dp × 48.dp + `RoundedCornerShape(12.dp)` + `colorScheme.secondary` bg + `typography.medium20` emoji (또는 `AsyncImage(profileImageUrl)`) | 1차 2단계 모델: emoji or profile image URL 양자 택일 결정 필요(spec.md "후속 계획" 참조). 본안은 image fallback → emoji. |
  | 닉네임 | `text-sm font-bold` | `typography.bold14` + `onBackground` | |
  | 전적 라벨 | `text-[11px] text-muted-foreground` | `typography.medium12` + `onSurfaceVariant` | ⚠️ 11px → 12sp 근사(home-feed §7 동일 정책) |
  | 승 색 | `text-success` | `colorScheme.success` | |
  | 패 색 | `text-destructive` | `colorScheme.error` | |
  | 무 색 | 미지정(= foreground) | `colorScheme.onSurfaceVariant` | 홈 StatsBar "무" 셀과 동일 톤 |
  | 연승 색 + 🔥 | `text-warning` + "🔥{streak}연승" | `colorScheme.warning` | `streak > 0`일 때만 노출 |
  | 대결 버튼 | `<Button variant="outline" size="sm">` + `Swords` 14.dp + "대결" | `OutlinedButton` (height = 32.dp) + `Icons.Filled.SportsKabaddi` 14.dp + "대결" | home-feed §4와 동일 매핑 정책 |

- **1차 2단계 props 시그니처 권고** (1차 2단계 진입 시 mobile-dev 입력):

  ```kotlin
  @Composable
  fun FriendCard(
      friendId: Long,
      nickname: String,
      profileImageUrl: String?,        // null이면 emoji placeholder
      emojiFallback: String,           // "🙂" 기본
      wins: Int,
      losses: Int,
      draws: Int,
      currentStreak: Int,
      onClickChallenge: () -> Unit,    // "대결" 버튼 탭 → 챌린지 생성 진입
      onClick: () -> Unit,             // 카드 자체 탭 → 친구 프로필 진입(후속의 후속)
      modifier: Modifier = Modifier,
  )
  ```

- **상호작용** (1차 2단계 진입 시):
  - 카드 탭 → 친구 프로필 화면(후속의 후속, 본 spec 범위 외)
  - "대결" 버튼 탭 → 챌린지 생성 화면 (`/challenge-new`, 후속의 후속)
- ⚠️ **1차 2단계 진입 시 확인 필요**:
  - 프로필 placeholder를 emoji vs 닉네임 이니셜 vs 일관 색상 dot 어느 톤으로 갈지 — 본안은 emoji + image URL fallback. spec.md "후속 계획"의 `Friend(friendId, nickname, profileImageUrl)` view에는 emoji 필드 없음 → emoji는 임의 placeholder 풀에서 닉네임 hash로 선택 vs 닉네임 이니셜 단일 톤 중 디자이너 결정 필요.

---

## 3. 컴포넌트 매핑

| Lovable 소스 | Compose 제안 | 신규/기존 | 비고 |
|---|---|---|---|
| `FriendsEmptyState` sub-component (`src/routes/friends.tsx`) | `FriendsEmptyState` (`:core:designsystem/components/friend/`) | **신규 (본 단계)** | 5개 props (§3.1). 홈의 `HomeEmptyState`와 시각 패턴 일치하나, 친구 빈 상태는 variant 분기 없는 단일 형태 → 별도 컴포넌트로 분리. |
| Header (`<header>` Lovable, 친구) | `FriendsTopBar` (`:feature:friends/component/`) | **신규 (본 단계)** | 1개 props (§3.2). 홈 `HomeTopBar` 패턴 답습. 본 단계엔 액션 슬롯 미노출, 1차 2단계 진입 시 `actions: @Composable RowScope.() -> Unit` slot 추가 후보. |
| 친구 카드 인라인 (`src/routes/friends.tsx` 47~68행) | `FriendCard` (`:core:designsystem/components/friend/`) | **신규 (1차 2단계 — 본 단계 범위 밖)** | §2 참조. |
| 검색 input + UserPlus 액션 | (1차 2단계 진입 시 `FriendsTopBar`에 slot 추가) | 1차 2단계 | 본 단계 미구현. |
| `BottomNav` | 기존 `ChallengeBottomBar` (`:feature:main`) | 기존 — bottom-navigation feature 완료분 | 변경 없음. |
| lucide `Users` / `UserPlus` / `Search` / `Swords` | `Icons.Filled.{Group, PersonAdd, Search, SportsKabaddi}` | 기존 — `materialIconsExtended` | bottom-navigation/home-feed에서 채택한 옵션 A(Material Icons Extended) 일관 적용. 본 단계는 `Group` + `PersonAdd` 2종만 사용. |

### 3.1 `FriendsEmptyState` (Compose, 신규) — props 명세

```kotlin
@Composable
fun FriendsEmptyState(
    title: String,
    subtitle: String,
    ctaLabel: String,
    icon: ImageVector,
    onClickCta: () -> Unit,
    modifier: Modifier = Modifier,
)
```

- **호출 인자 (1차 1단계 mobile-dev 사용값 — 그대로 복사 가능)**:

  | 인자 | 값 |
  |---|---|
  | `title` | `"아직 친구가 없어요"` |
  | `subtitle` | `"친구를 추가하고 함께 챌린지를 시작해보세요"` |
  | `ctaLabel` | `"친구 추가하기"` |
  | `icon` | `Icons.Filled.Group` (Material Icons Extended — `androidx.compose.material.icons.filled.Group`) |
  | `onClickCta` | `{ viewModel.showMessage("준비 중입니다") }` (Route에서 wiring) |

- **레이아웃** (24.dp 내부 패딩, 컨테이너는 `glass-card` 룩):
  1. 일러스트 자리: 64×64.dp + 16.dp radius + `primary.copy(alpha=0.10f)` bg + `icon` 32.dp(primary). 중앙 정렬.
  2. 16.dp gap
  3. `title` (`typography.bold16` 또는 `bold18` — Lovable `text-base font-bold` 기준 **bold16 권고**, 홈 `HomeEmptyState`와 정합)
  4. 4.dp gap
  5. `subtitle` (`typography.medium12`, `onSurfaceVariant`)
  6. 20.dp gap
  7. CTA 1버튼 `Button` (primary) full-width: `Icons.Filled.PersonAdd` 16.dp + `ctaLabel`
     - 버튼 높이 52.dp(`size="full"` 매핑), radius 12.dp, `colorScheme.primary` bg + `onPrimary` content + `typography.bold14`
- **컴포넌트 컨테이너**: `:core:designsystem`의 `glass-card` 룩이 별도 헬퍼(`ChallengeTheme.brushes.card`)로 추출돼 있으면 사용, 없으면 `colorScheme.surface` + `colorScheme.outline` 1dp 보더 + `RoundedCornerShape(16.dp)`로 근사. home-feed §6과 동일 정책.
- ⚠️ **단일 출처 결정 (mobile-dev 필독)**:
  - **헤드라인 폰트 크기**: **plan.md Step 4의 `bold18`은 무시하고 본 design.md의 `bold16`을 사용한다.** 사유: Lovable `text-base font-bold` = 16sp이며 홈 `HomeEmptyState`도 16sp로 시각 정합. plan.md 기재값은 초안 단계 오기이며, **모바일 단일 출처는 본 design.md**다. 본 항목은 §5 #1, §6 #3에서도 동일 톤으로 반복 명시.
  - **1차 2단계 일러스트 자산**: 1차 1단계는 `Icons.Filled.Group` 임시. backlog 후보 — 친구 추가 feature 진입 시점에 일러스트 합류 검토.

### 3.2 `FriendsTopBar` (Compose, 신규) — props 명세

```kotlin
@Composable
internal fun FriendsTopBar(
    modifier: Modifier = Modifier,
)
```

- **본 단계는 props 0개.** 1차 2단계 진입 시 `actions: (@Composable RowScope.() -> Unit)? = null` 슬롯 추가하여 UserPlus 버튼 + 검색 input 영역을 외부에서 주입하도록 확장.
- **레이아웃**:
  - Row (`fillMaxWidth` + `height(56.dp)` + `padding(horizontal = 20.dp)` + `verticalAlignment = CenterVertically` + `horizontalArrangement = Arrangement.Start`)
  - 단일 Text "친구" — `typography.bold18` + `colorScheme.onBackground`
  - 컨테이너는 `Surface(color = colorScheme.surface)` — 홈 `HomeTopBar` 패턴 답습. backdrop-blur 근사는 surface alpha 80% 옵션이 있으면 적용, 없으면 단색.
- **본 단계 액션 슬롯 결정**: **미노출**. 사유:
  - 친구 0명 상태에서 UserPlus 액션은 빈 상태 카드 CTA "친구 추가하기"와 라우팅 중복(시각/인지 부담).
  - 검색 input은 친구 0명일 때 검색 대상이 없으므로 의미 없음.
  - spec.md §29 / §97 의 본 단계 default(액션 미노출) 채택.
- **1차 2단계 진입 시 변경 예상**:
  - `actions` slot 추가 → 외부에서 `IconButton(Icons.Filled.PersonAdd)` 주입.
  - TopBar 하단에 검색 input row 추가(별도 sub-component 또는 prop으로 받는 slot).
  - 본 단계 컴포넌트 시그니처 변경이 1차 2단계에 1번만 발생하도록 prop default를 nullable로 명시.

---

## 4. 전역 토큰 (참조)

본 feature 도입으로 신규 추가되는 토큰 없음. 모두 기존 `ChallengeColorScheme` 슬롯으로 커버 가능. home-feed 도입 시 정리된 토큰 그대로 재사용.

- **Colors**: `colorScheme.background` / `surface` / `outline` / `primary` / `onPrimary` / `onBackground` / `onSurfaceVariant`
- **Alpha 변형**: `colorScheme.primary.copy(alpha=0.10f)` — 일러스트 배경. **신규 슬롯화 ❌** (alpha 적용은 호출부 책임 — home-feed §5 동일 정책).
- **Typography**: `typography.bold18` (TopBar) / `bold16` (헤드라인) / `medium12` (서브라인) / `bold14` (CTA 라벨) — 전부 기존 슬롯. tokens.md §5.2 매핑 그대로.
- **Radius**: `RoundedCornerShape(16.dp)` (카드 컨테이너 — radius-xl) / `RoundedCornerShape(12.dp)` (CTA 버튼 — radius-lg) / `RoundedCornerShape(16.dp)` (일러스트 자리). tokens.md §4.
- **Spacing**:
  - 일러스트 자리 size: 64.dp × 64.dp
  - 일러스트 아이콘 size: 32.dp
  - 일러스트 ↔ 헤드라인 gap: 16.dp
  - 헤드라인 ↔ 서브라인 gap: 4.dp
  - 서브라인 ↔ CTA gap: 20.dp
  - 카드 내부 패딩: 24.dp
  - CTA 버튼 높이: 52.dp
  - CTA 버튼 내부 icon ↔ 텍스트 간격: 6.dp (`gap-1.5` 매핑)

---

## 5. mobile-dev 강조 사항 (T-M1~M3 인계 시 주의)

본 feature mobile 트랙(T-M1~M6) 인계 시 다음을 반드시 강조:

1. **`FriendsEmptyState`의 props 시그니처는 §3.1 그대로**. plan.md Step 4의 코드 예시와 prop 순서/타입 일치. **헤드라인 폰트는 plan.md의 `bold18`을 무시하고 본 design.md의 `bold16`을 그대로 사용한다** — 모바일 단일 출처는 본 design.md이며, plan.md `bold18`은 초안 단계 오기. 사유는 홈 `HomeEmptyState`(16sp)와 시각 정합. mobile-dev는 본 항목에 한해 plan.md를 따르지 말 것.
2. **`materialIconsExtended` 의존성을 `:feature:friends` 또는 `:core:designsystem`에 추가**: home-feed/bottom-navigation feature와 동일 패턴. `Icons.Filled.Group` + `Icons.Filled.PersonAdd` 2종 사용.
3. **stub CTA 콜백은 `viewModel.showMessage("준비 중입니다")`** — plan.md Task 7 그대로. ShowMessage effect는 Route에서 `LocalMainAction.current.showSnackBar(message)`로 수집.
4. **빈 상태 카드는 화면 세로 중앙에 배치하지 않고 TopBar 아래 `mt-6` (24.dp)에서 시작**. Lovable과 동일. `Modifier.fillMaxSize()` + `Arrangement.Center`는 ❌ — TopBar 직후 상단 정렬.
5. **`FriendsTopBar`는 본 단계 props 0개**. 액션 슬롯이 필요해지면 본 컴포넌트 시그니처를 1번만 확장(1차 2단계 진입 시).
6. **빈 상태 컴포넌트 위치는 `:core:designsystem/components/friend/FriendsEmptyState.kt`** (spec.md §26, plan.md File Structure). `HomeEmptyState`와 같은 패키지 패턴 답습.

---

## 6. ⚠️ 확인 필요 / 디자이너 협의 항목 (집약)

| # | 항목 | 본안 | 결정 필요 시점 |
|---|---|---|---|
| 1 | TopBar 액션 슬롯 노출(UserPlus / Search) | 빈 상태 미노출 | 1차 2단계 진입 전 (목록 등장과 동시에 복귀) |
| 2 | 빈 상태 일러스트 자산 | `Icons.Filled.Group` 32.dp + primary 10% 배경 임시 | 디자이너 별도 일러스트 합류 시 교체 (backlog) |
| 3 | 헤드라인 폰트 크기 — plan.md `bold18` vs design.md `bold16` | **`bold16` 확정. plan.md `bold18`은 무시.** 모바일 단일 출처 = 본 design.md. 홈 `HomeEmptyState`(16sp) 시각 정합 사유. | 결정 완료 — 추가 협의 불요 |
| 4 | 친구 카드 프로필 placeholder — emoji vs 이니셜 vs 단일 톤 dot | emoji + image URL fallback(1차 2단계 입력만) | 1차 2단계 진입 전 |
| 5 | 친구 카드 "대결" 버튼 라우팅 (`Swords` → `SportsKabaddi`) | home-feed §7 #4와 동일 정책 채택 | 1차 2단계 진입 시 |
| 6 | 1차 2단계 진입 시 빈 상태 컴포넌트 재사용 | `FriendsEmptyState`를 그대로 활용 + ViewModel이 `friends.isEmpty()` 분기 | 1차 2단계 진입 시 |

---

## 7. Lovable working tree 변경 요약

```
modified:   src/routes/friends.tsx
```

변경 한 줄 요약: `mockFriends` 빈 배열 + `isEmpty` 플래그 + `FriendsEmptyState` sub-component 신규(글로벌 미사용, 본 라우트 내부) + TopBar 액션/검색 input의 `!isEmpty` 조건부 노출.

> 메모리 규칙(`feedback_lovable_mobile_sync.md`)에 따라 Lovable과 모바일 양쪽 동기. Lovable의 본 변경은 working tree로만 두고(자체 git 커밋·push 안 함), PM hub 컨트롤러가 일괄 처리.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-06-24 | 최초 작성 — Lovable `friends.tsx` 빈 상태 분기 + `FriendsEmptyState` sub-component 반영. 2개 화면 상태(empty 본 단계 / default 1차 2단계 입력) 명세. `FriendsEmptyState`/`FriendsTopBar` 2개 컴포넌트 props·토큰 매핑 1차안. 친구 카드(1차 2단계) 시각 토큰 매핑 표 + props 권고 등재. ⚠️ 확인 필요 6건 §6. | design-bridge |
