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

---

# 2차 — 친구 추가

> 본 섹션은 **친구 추가 feature(spec-friend-add.md)** 디자인 명세. 1차 1단계 섹션(위)은 historical artifact로 그대로 보존하고, 본 섹션이 현재 친구 화면 동작 디자인의 권위(authority).

- **디자인 소스**: `/Users/hwamulman/woogunProject/challenge/challenge-design/oathbound-challenges`
- **참조 route**: `src/routes/friends.tsx` (수정), `src/routes/friends-search.tsx` (신규)
- **스냅샷 일시**: 2026-06-25
- **본 단계 신규/변경 컴포넌트 (Compose 매핑 대상)**:
  - `FriendListItem` *(:core:designsystem)* — 친구 1행 (기존 1차 2단계 입력안 `FriendCard`의 단순 버전 — 본 spec은 전적/대결 버튼 제외, 프로필+닉네임만)
  - `FriendRequestCard` *(:core:designsystem)* — 받은 요청 카드 (수락/거절)
  - `FriendSearchItem` *(:feature:friends)* — 검색 결과 1행 (relation 5종 분기)
  - `FriendsSearchTopBar` *(:feature:friends)* — 검색 화면 전용 상단 (← 뒤로 + 닉네임 입력)
  - `FriendsActionRow` *(:feature:friends 또는 화면 인라인)* — [친구 추가]/[친구 초대] 2-up 액션
  - `FriendsTopBar` *(:feature:friends)* — 1차 1단계 자산 유지 (props 0개)
  - `FriendsEmptyState` *(:core:designsystem)* — 1차 1단계 자산 재사용 + **2차에서 보조 CTA "카카오톡으로 초대하기" 추가**

> **1차 1단계 default 섹션(§2의 `FriendCard`)와의 관계**: §2는 전적/대결 버튼 포함 `FriendCard`(1차 2단계 입력만)였다. 본 2차에서는 친구 목록 1행이 **프로필 + 닉네임 + 대결 버튼**만 노출하는 단순화 — 전적 시각은 친구 추가 feature 범위 밖. 모바일 구현 단일 출처는 본 2차 섹션을 따른다. (`FriendListItem` 신규, `FriendCard`는 1차 2단계 입력만으로 사장.)

---

## A. FriendsScreen — Main (친구 목록 + 받은 요청)

### A.1 의도

친구 탭에 진입한 사용자가 **받은 요청을 즉시 인지**하고(FCM 없음 — 메모리 §5 위험 #5), **친구 추가/초대 진입점 2개**가 한눈에 보이도록.

### A.2 레이아웃 (위 → 아래)

1. **Sticky Header** — `FriendsTopBar` (1차 1단계 자산 유지)
   - `bg-background/80 backdrop-blur-xl`, `px-5`, top safe-area inset
   - 좌측: "친구" — `text-xl extrabold`
   - 우측: **액션 슬롯 없음** (액션은 본문 ActionRow로 분리 — 위치 일관성 + TopBar 단순성)
2. **본문 영역** — `px-5 mt-4 space-y-5`
   1. **`FriendsActionRow`** (2-up grid, `grid-cols-2 gap-2`)
      - 좌: `[친구 추가]` — `Button variant="default" size="full"` + `UserPlus` 16 + "친구 추가"
      - 우: `[친구 초대]` — `Button variant="outline" size="full"` + `Send` 16 + "친구 초대"
      - 조건부 노출: 친구 0건 + 요청 0건이면 미노출(빈 상태 카드 CTA로 일원화)
   2. **`ReceivedRequestsSection`** (받은 요청 ≥ 1건일 때)
      - 섹션 헤더: `text-sm font-bold` "받은 요청 " + `text-primary` "N건"
      - 카드 리스트: `FriendRequestCard` × N (`space-y-2` ≈ 8.dp)
   3. **친구 목록 섹션** (친구 ≥ 1건일 때)
      - 섹션 헤더: `text-sm font-bold` "친구 N명"
      - 리스트: `FriendListItem` × N (`space-y-2`)
3. **빈 상태 분기** — 친구 0건 **AND** 요청 0건일 때만 `FriendsEmptyState` 카드(1차 1단계 자산 재사용, 2차에서 보조 CTA "카카오톡으로 초대하기" 추가)
4. **BottomNav** (기존)

### A.3 상호작용

- `[친구 추가]` 탭 → `Route.FriendsRoute.Search` push (낙관적 진입, 뒤로가기 시 메인 자동 refresh — spec.md §6.4 명시)
- `[친구 초대]` 탭 → KakaoLink 공유 시트 (`KakaoInviter.sendInvite({ inviterNickname })`)
- `FriendRequestCard.[수락]` 탭 → `repository.acceptRequest(id)` (낙관적 갱신 — 해당 카드 즉시 제거 + 친구 목록 prepend)
- `FriendRequestCard.[거절]` 탭 → `repository.rejectRequest(id)` (낙관적 갱신 — 해당 카드 즉시 제거)
- 빈 상태 카드 `[친구 추가하기]` 탭 → `Route.FriendsRoute.Search`
- 빈 상태 카드 `[카카오톡으로 초대하기]` 탭 → KakaoLink

### A.4 토큰

| 위치 | Lovable (Tailwind v4) | Compose / `ChallengeTheme` |
|---|---|---|
| TopBar 라벨 "친구" | `text-xl font-extrabold` | `typography.bold18` + `colorScheme.onBackground` |
| 섹션 헤더 ("받은 요청 N건", "친구 N명") | `text-sm font-bold` | `typography.bold14` + `colorScheme.onBackground` |
| "N건" 강조 | `text-primary` | `colorScheme.primary` |
| ActionRow 컨테이너 | `grid grid-cols-2 gap-2` | `Row(Arrangement.spacedBy(8.dp))` 또는 `Row` + 두 Button `Modifier.weight(1f)` |
| 받은 요청 카드 | `glass-card p-3 flex items-center gap-3` | `colorScheme.surface` + `border 1.dp colorScheme.outline` + `RoundedCornerShape(16.dp)` + `Modifier.padding(12.dp)` + `Arrangement.spacedBy(12.dp)` |
| 친구 카드 (`FriendListItem`) | `glass-card p-4 flex items-center gap-3` | 동일 surface, padding 16.dp |
| 카드 닉네임 | `text-sm font-bold` | `typography.bold14` + `onBackground` |
| 프로필 자리(emoji placeholder) | `w-12 h-12 rounded-xl bg-secondary text-xl` (요청 카드는 동일, 검색은 `w-11 h-11`) | 48.dp/44.dp(검색) × 48.dp/44.dp + `RoundedCornerShape(12.dp)` + `colorScheme.secondary` bg + `typography.medium20` emoji (`AsyncImage(profileImageUrl)` fallback) |
| `[친구 추가]` / `[친구 요청]` (primary) | `Button` default + `size="full"` (메인) / `size="sm"` (검색) | `Button(colors = colorScheme.primary on onPrimary)` + `typography.bold14` |
| `[친구 초대]` / `[다시 요청]` (secondary) | `Button variant="outline"`/`"secondary"` | 메인은 `OutlinedButton` (border = `colorScheme.outline`), 검색 [다시 요청]은 `Button(colors = colorScheme.secondary on onSurface)` |
| 카드 내부 간격 | `gap-3` (12px) | `Arrangement.spacedBy(12.dp)` |
| 라디우스 (카드) | `--radius-xl` = 16px | `RoundedCornerShape(16.dp)` |
| 라디우스 (버튼 sm) | `rounded-lg` = 12px | `RoundedCornerShape(12.dp)` |
| 라디우스 (프로필 placeholder) | `rounded-xl` = 16px | `RoundedCornerShape(12.dp)` ⚠️ Lovable `rounded-xl`(16) vs 기존 §2 매핑(12.dp) — **본 2차는 12.dp 채택**(시각 확인 결과 12.dp가 더 정합) |
| 받은 요청 카드 액션 간격 | `gap-1.5` (6px) | `Arrangement.spacedBy(6.dp)` |
| 화면 가로 패딩 | `px-5` (20px) | `Modifier.padding(horizontal = 20.dp)` |
| 본문 첫 섹션 상단 여백 | `mt-4` (16px) | `Modifier.padding(top = 16.dp)` |
| 섹션 간 간격 | `space-y-5` (20px) | `Arrangement.spacedBy(20.dp)` |
| 카드 리스트 간 간격 | `space-y-2` (8px) | `Arrangement.spacedBy(8.dp)` |
| BottomNav 여백 | `pb-24` (96px) | bottomBar slot 사용 — 별도 padding 불요 |

### A.5 상태

- `Loading` — 친구/받은 요청 동시 fetch 전. 화면 전체 skeleton 또는 ProgressIndicator. 본 spec은 시각 명세 없음 (mobile-dev 재량).
- `Data(friends, requests)` — A.2 레이아웃. 각 섹션의 0/1+건은 조건부 렌더.
- `Empty` — friends.isEmpty() && requests.isEmpty(). `FriendsEmptyState`만 노출.

---

## B. FriendsSearchScreen — 검색 화면 (신규)

### B.1 의도

닉네임으로 회원가입된 사용자를 찾아 **relation별 적절한 액션**을 1탭으로 수행. 동명이인 다수에 대응하기 위해 프로필 사진 + 닉네임 시각 식별 보장.

### B.2 레이아웃 (위 → 아래)

1. **Sticky `FriendsSearchTopBar`** — `bg-background/80 backdrop-blur-xl`, `px-5`, top safe-area inset
   - 좌: `← 뒤로가기` (`ArrowLeft` 20, `h-10 w-10` 탭 영역, 시각 `-ml-2`로 컨테이너 패딩 흡수)
   - 우(나머지 폭): 닉네임 입력 — `bg-secondary rounded-xl pl-10 pr-9 py-2.5 text-sm`, 좌측 `Search` 16 아이콘 absolute, 우측 입력값 있을 때 `X` 14 clear 버튼, `autoFocus`
2. **본문**
   - **Idle 상태** (`query.trim().length < 2`): 화면 중앙 상단(`mt-16`)에 회색 안내 텍스트 — "닉네임을 2자 이상 입력해주세요"
   - **Empty 상태** (검색 결과 0건): 동일 위치에 "검색 결과가 없어요. 닉네임을 더 정확히 입력해보세요."
   - **Result 상태**: `px-5 mt-3 space-y-2` 리스트 — `FriendSearchItem` × N (LIMIT 20)

### B.3 `FriendSearchItem` 레이아웃

`glass-card p-3 flex items-center gap-3`:
1. 프로필 (44 × 44.dp, `rounded-xl bg-secondary`, emoji or `AsyncImage`)
2. 닉네임 (`text-sm font-bold` + `truncate` + `flex-1 min-w-0`)
3. `RelationAction` — relation 5종 분기 (§B.5)

### B.4 상호작용

- 입력값 변경 → debounce 300ms(모바일) → `searchUsersByNickname(trimmed)` 호출
- `[친구 요청]` 탭 → `sendRequest(targetId)` 낙관적 갱신 → 해당 행 relation을 `REQUEST_SENT`로 즉시 전환 → 실패 시 롤백 + 스낵바
- `[요청 보냄 X]`의 `X` 탭 → `cancelRequest(pendingRequestId)` 낙관적 갱신 → relation `NONE` 전환
- `[수락]` 탭 → `acceptRequest(pendingRequestId)` 낙관적 갱신 → relation `FRIEND` 전환
- `[다시 요청]` 탭 → `sendRequest(targetId)` (서버는 REJECTED row를 PENDING으로 UPDATE — spec.md §5.3) → relation `REQUEST_SENT` 전환
- `이미 친구` 뱃지: 비활성 (탭 무동작)
- 뒤로가기 → 메인 진입 시 자동 refresh (spec.md §6.4)

### B.5 relation 5종 시각 명세 (단일 출처)

| relation | UI | 컴포넌트 | 시각 토큰 | 동작 |
|---|---|---|---|---|
| `NONE` | `[친구 요청]` (primary, fill) | `Button(default, size=sm)` + `UserPlus` 14 + "친구 요청" | `colorScheme.primary` bg + `onPrimary` text + `typography.bold14` (Lovable `fire-gradient`은 모바일 단색 `primary`로 근사 — 홈 첫 진입 CTA와 동일 정책 §1.4) | `onClickAction()` → sendRequest |
| `REQUEST_SENT` | `[요청 보냄] [X]` 2-up | `Button(secondary, disabled, opacity-100)` "요청 보냄" + 옆에 `Button(ghost, h-9 w-9)` `X` 14 | `colorScheme.secondary` bg + `secondaryForeground` text + `disabled = true` (시각만 — 실제 disabled 처리는 X 버튼이 별도). `X`는 `colorScheme.onSurfaceVariant` | `onClickCancel()` → cancelRequest. "요청 보냄" 라벨 자체는 무동작 (시각 상태만). |
| `REQUEST_RECEIVED` | `[수락]` (primary, fill) | `Button(default, size=sm)` + `Check` 14 + "수락" | `colorScheme.primary` bg + `onPrimary` text | `onClickAction()` → acceptRequest |
| `FRIEND` | `이미 친구` (disabled badge) | `<span>` (Lovable) → Compose `Surface(color = colorScheme.secondary, shape = RoundedCornerShape(12.dp))` + `Modifier.height(36.dp).padding(horizontal = 12.dp)` | `colorScheme.secondary` bg + `colorScheme.onSurfaceVariant` text + 1.dp `outline` border + `typography.bold12` | 비활성 — 클릭 무동작 |
| `REJECTED` | `[다시 요청]` (secondary, fill) | `Button(secondary, size=sm)` + `RotateCw` 14 + "다시 요청" | `colorScheme.secondary` bg + `secondaryForeground` text + `typography.bold14` | `onClickAction()` → sendRequest (서버 측 REJECTED→PENDING UPDATE) |

> **버튼 크기 통일**: 모두 `Button size="sm"` = Lovable `h-9 rounded-lg px-3 text-xs` = Compose `height = 36.dp` + `RoundedCornerShape(12.dp)` + `Modifier.padding(horizontal = 12.dp)` + 텍스트 `typography.bold14` (12sp 미사용 — 14sp 통일, 버튼 가독성 우선).

> **`REQUEST_SENT`의 disabled 시각**: Lovable에서 `disabled className="opacity-100 cursor-default"`로 opacity 변화 제거. **모바일에서도 동일** — `Button(enabled = false)`는 alpha 변화가 자동 적용되므로, **`Surface` 위에 텍스트 + `Modifier.clickable`을 주지 않는 정적 컴포넌트**로 구현하는 것을 권장 (Disabled Button의 자동 alpha 0.38 회피).

### B.6 토큰

| 위치 | Lovable | Compose |
|---|---|---|
| TopBar 컨테이너 | `bg-background/80 backdrop-blur-xl` | `Surface(color = colorScheme.background.copy(alpha = 0.80f))` (1차 1단계 §1과 동일 정책 — alpha 근사) |
| TopBar 높이 | `h-10` 버튼 + `py-2.5` input + safe-area | 56.dp 권장 (`FriendsTopBar`와 동일) |
| 뒤로가기 버튼 | `h-10 w-10 -ml-2 rounded-xl text-foreground hover:bg-accent` | `IconButton(modifier = Modifier.size(40.dp).offset(x = -8.dp))` + `Icons.AutoMirrored.Filled.ArrowBack` 20.dp + `colorScheme.onBackground` |
| 입력 박스 | `bg-secondary rounded-xl pl-10 pr-9 py-2.5 text-sm` + focus `ring-2 ring-primary` | `TextField` 또는 `BasicTextField` + `colorScheme.secondary` bg + `RoundedCornerShape(12.dp)` + `Modifier.height(40.dp)` + leading icon padding 36.dp + trailing icon padding 36.dp + `typography.medium14` 입력 텍스트 + `colorScheme.onSurfaceVariant` placeholder + focus indicator (border 2.dp `primary`) |
| 입력 placeholder | `placeholder:text-muted-foreground` | `colorScheme.onSurfaceVariant` |
| 안내 텍스트 (Idle/Empty) | `mt-16 text-center text-sm text-muted-foreground` | `Modifier.padding(top = 64.dp)` + `Arrangement.Center` + `typography.medium14` + `colorScheme.onSurfaceVariant` |
| 결과 리스트 컨테이너 | `px-5 mt-3 space-y-2` | `LazyColumn` + `contentPadding = PaddingValues(horizontal = 20.dp, vertical = 12.dp)` + `verticalArrangement = Arrangement.spacedBy(8.dp)` |

### B.7 상태

| State | 트리거 | 화면 |
|---|---|---|
| `Idle` | `query.trim().length < 2` | TopBar + Idle 안내 "닉네임을 2자 이상 입력해주세요" |
| `Searching` | 입력 ≥ 2자 + 서버 응답 대기 | TopBar + (로딩 인디케이터 — 모바일 재량, Lovable 미구현) |
| `Result(items)` | 응답 도착, items ≥ 1건 | TopBar + 리스트 |
| `Empty` | 응답 도착, items = 0건 | TopBar + Empty 안내 "검색 결과가 없어요. 닉네임을 더 정확히 입력해보세요." |

---

## C. Compose 컴포넌트 spec (props 시그니처 — 모바일 단일 출처)

```kotlin
@Composable
fun FriendListItem(
    profileImageUrl: String?,
    nickname: String,
    modifier: Modifier = Modifier,
)
```
- 친구 목록 1행. 프로필 + 닉네임만. 본 spec(친구 추가 feature) 범위는 전적/대결 버튼 미포함.
- 카드 컨테이너: `Surface(color = colorScheme.surface, border = BorderStroke(1.dp, colorScheme.outline), shape = RoundedCornerShape(16.dp))` + `Modifier.padding(16.dp)`.
- 프로필 placeholder: `profileImageUrl == null`이면 emoji 또는 닉네임 이니셜(닉네임 1글자) — **본 spec은 닉네임 첫 1글자 + `colorScheme.secondary` bg 채택** (emoji는 Lovable preview용 — 실 데이터 모델에 emoji 필드 없음, spec.md §6 derived 모델). 1차 1단계 §2.99의 ⚠️ 확인 필요 #4에서 본 spec으로 **닉네임 이니셜 확정**.

```kotlin
@Composable
fun FriendRequestCard(
    profileImageUrl: String?,
    nickname: String,
    onAccept: () -> Unit,
    onReject: () -> Unit,
    modifier: Modifier = Modifier,
)
```
- 카드 컨테이너: `Surface(... shape = RoundedCornerShape(16.dp))` + `Modifier.padding(12.dp)` (요청 카드는 친구 카드보다 1단계 작은 padding으로 컴팩트 — Lovable `p-3`).
- 액션 2버튼: `Row(horizontalArrangement = Arrangement.spacedBy(6.dp))`
  - 좌: `Button(size = sm, colors = primary)` + `Icons.Filled.Check` 14.dp + "수락"
  - 우: `OutlinedButton(size = sm)` + `Icons.Filled.Close` 14.dp + "거절"
- `onAccept` / `onReject`는 ViewModel로 위임. 낙관적 갱신은 ViewModel 책임.

```kotlin
enum class Relation { NONE, REQUEST_SENT, REQUEST_RECEIVED, FRIEND, REJECTED }

@Composable
fun FriendSearchItem(
    profileImageUrl: String?,
    nickname: String,
    relation: Relation,
    onClickAction: () -> Unit,
    onClickCancel: (() -> Unit)?,           // REQUEST_SENT 일 때만 non-null
    modifier: Modifier = Modifier,
)
```
- 컨테이너: `Surface(... padding = 12.dp)`. 프로필 placeholder 44.dp.
- relation 분기는 §B.5 시각 명세 그대로. 내부 when으로 5종 분기.
- `onClickCancel`은 `relation == REQUEST_SENT`일 때만 호출됨. 다른 케이스에선 `null` 허용.

```kotlin
@Composable
fun FriendsSearchTopBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
)
```
- Row (`fillMaxWidth().height(56.dp).padding(horizontal = 20.dp)`, `verticalAlignment = CenterVertically`, `horizontalArrangement = Arrangement.spacedBy(8.dp)`)
- 좌측 `IconButton(onClick = onBack)` + `Icons.AutoMirrored.Filled.ArrowBack` 20.dp
- 우측 `TextField` (or `BasicTextField` + 커스텀 decoration) — `Modifier.weight(1f)` + leading `Search` 16 + trailing clear `X` (query 비어있지 않을 때만)
- placeholder: "닉네임 검색"
- 자동 포커스 (`LaunchedEffect + FocusRequester`)

---

## D. 사용 토큰 종합 (color / typography / spacing / radius)

본 단계 도입으로 신규 토큰 추가 없음. 기존 `ChallengeColorScheme` + `ChallengeTypoGraphy` 슬롯으로 전부 커버.

- **Colors**: `background` / `surface` / `secondary` / `secondaryForeground` / `outline` / `primary` / `onPrimary` / `onBackground` / `onSurfaceVariant`
- **Alpha 변형**: `background.copy(alpha = 0.80f)` (TopBar backdrop-blur 근사). 신규 슬롯화 ❌ — 호출부 책임 (1차 1단계 §4와 동일 정책).
- **Typography**: `bold18` (메인 TopBar "친구" — 1차 1단계 §1과 동일 홈 패턴), `bold16` (빈 상태 헤드라인 — 1차 1단계 §3.1과 동일), `bold14` (섹션 헤더 / 카드 닉네임 / 버튼 라벨), `bold12` (FRIEND 뱃지), `medium14` (검색 입력 / 안내 텍스트), `medium20` (프로필 emoji placeholder), `medium12` (빈 상태 서브라인 — 1차 1단계 §3.1과 동일).
- **Radius**:
  - 카드: `RoundedCornerShape(16.dp)` — radius-xl
  - 버튼 / 프로필 placeholder / 입력 박스 / FRIEND 뱃지 / 뒤로가기 IconButton: `RoundedCornerShape(12.dp)` — radius-lg
- **Spacing**:
  - 화면 가로 패딩: 20.dp
  - 카드 가로 패딩: 12.dp (요청·검색) / 16.dp (친구)
  - 카드 내부 요소 간격: 12.dp (프로필 ↔ 닉네임 ↔ 액션)
  - 받은 요청 액션 2버튼 간격: 6.dp
  - ActionRow 간격: 8.dp
  - 카드 리스트 간격: 8.dp
  - 섹션 간격: 20.dp
  - TopBar 높이: 56.dp
  - 검색 입력 높이: 40.dp
  - 프로필 placeholder size: 48.dp (요청/친구), 44.dp (검색)
  - 아이콘: 액션 버튼 14.dp / TopBar 아이콘 20.dp / 입력 leading Search 16.dp / clear X 14.dp / 친구 카드 대결 아이콘 14.dp

---

## E. 컴포넌트 매핑 (2차)

| Lovable 소스 | Compose 제안 | 신규/기존 | 비고 |
|---|---|---|---|
| `FriendsTopBar` (`src/routes/friends.tsx`) | `FriendsTopBar` (`:feature:friends/component/`) | 1차 1단계 자산 유지 | 2차 시점 props 0개 그대로. 액션 슬롯은 ActionRow로 외주화. |
| `FriendsActionRow` 인라인 (`src/routes/friends.tsx`) | `FriendsActionRow` (`:feature:friends/component/`) 또는 화면 인라인 | **신규** | 단일 호출처라 별도 컴포넌트 분리 선택. 친구 추가/초대 2-up 버튼만. |
| `ReceivedRequestsSection` 인라인 | `ReceivedRequestsSection` 또는 화면 인라인 + `FriendRequestCard` × N | **신규** | 섹션 헤더 + LazyColumn. 카드는 `:core:designsystem`. |
| `FriendRequestCard` 인라인 (Lovable) | `FriendRequestCard` (`:core:designsystem/components/friend/`) | **신규** | C 섹션 props 시그니처. |
| `FriendListItem` 인라인 (Lovable) | `FriendListItem` (`:core:designsystem/components/friend/`) | **신규** | 1차 2단계 입력안 `FriendCard`(전적/대결 포함)와 별개 — 본 spec은 단순 1행. 1차 2단계 §2 `FriendCard`는 **사장**(친구 추가 feature 범위 외, 후속 spec 진입 시 재검토). |
| `FriendsEmptyState` (Lovable, `src/routes/friends.tsx`) | `FriendsEmptyState` (`:core:designsystem/components/friend/`) | 1차 1단계 자산 + **CTA 2개로 확장** | 메인 CTA "친구 추가하기" → 검색 화면 / 보조 CTA "카카오톡으로 초대하기" → KakaoLink. props에 `onClickInvite: (() -> Unit)? = null` 추가 권고 (null이면 1차 1단계처럼 단일 CTA만). |
| `FriendsSearchTopBar` (Lovable, `src/routes/friends-search.tsx`) | `FriendsSearchTopBar` (`:feature:friends/component/`) | **신규** | C 섹션 props 시그니처. |
| `FriendSearchItem` (Lovable, `src/routes/friends-search.tsx`) | `FriendSearchItem` (`:feature:friends/component/`) | **신규** | C 섹션 props 시그니처. 내부 `RelationAction` private composable로 5종 분기. |
| `SearchHintMessage` (Lovable) | (화면 인라인) `Text` + `Modifier.padding(top = 64.dp)` | — | 별도 컴포넌트 불요. 두 안내 문구만 다른 인자로 호출. |
| lucide `ArrowLeft` / `Search` / `UserPlus` / `Send` / `Check` / `X` / `RotateCw` | `Icons.AutoMirrored.Filled.ArrowBack` / `Icons.Filled.Search` / `Icons.Filled.PersonAdd` / `Icons.AutoMirrored.Filled.Send` / `Icons.Filled.Check` / `Icons.Filled.Close` / `Icons.Filled.Refresh` | 기존 — `materialIconsExtended` | bottom-navigation / home-feed 옵션 A 일관. 메인의 친구 초대 `Send`와 검색의 다시 요청 `Refresh`는 본 단계 신규 도입. |

---

## F. 모바일 측 정확한 토큰 / 문구 / 아이콘 식별자 (단일 출처)

### F.1 문구 (모두 한국어, 단일 출처)

| 위치 | 문구 |
|---|---|
| 메인 TopBar | "친구" |
| 메인 ActionRow primary | "친구 추가" |
| 메인 ActionRow secondary | "친구 초대" |
| 받은 요청 섹션 헤더 | "받은 요청 {N}건" — "N건"은 `colorScheme.primary` |
| 받은 요청 카드 수락 | "수락" |
| 받은 요청 카드 거절 | "거절" |
| 친구 섹션 헤더 | "친구 {N}명" |
| 빈 상태 헤드라인 | "아직 친구가 없어요" |
| 빈 상태 서브라인 | "친구를 추가하고 함께 챌린지를 시작해보세요" |
| 빈 상태 primary CTA | "친구 추가하기" |
| 빈 상태 secondary CTA (2차 신규) | "카카오톡으로 초대하기" |
| 검색 입력 placeholder | "닉네임 검색" |
| 검색 Idle 안내 | "닉네임을 2자 이상 입력해주세요" |
| 검색 Empty 안내 | "검색 결과가 없어요. 닉네임을 더 정확히 입력해보세요." |
| relation NONE 액션 | "친구 요청" |
| relation REQUEST_SENT 라벨 | "요청 보냄" |
| relation REQUEST_SENT 취소 버튼 | (아이콘만 — `X` 14.dp + `contentDescription = "요청 취소"`) |
| relation REQUEST_RECEIVED 액션 | "수락" |
| relation FRIEND 뱃지 | "이미 친구" |
| relation REJECTED 액션 | "다시 요청" |
| 뒤로가기 버튼 a11y | `contentDescription = "뒤로 가기"` |
| 검색 clear X 버튼 a11y | `contentDescription = "검색어 지우기"` |

### F.2 아이콘 (Material Icons Extended)

| 위치 | 아이콘 | sp/dp |
|---|---|---|
| 메인 ActionRow [친구 추가] | `Icons.Filled.PersonAdd` | 16.dp |
| 메인 ActionRow [친구 초대] | `Icons.AutoMirrored.Filled.Send` | 16.dp |
| 받은 요청 [수락] | `Icons.Filled.Check` | 14.dp |
| 받은 요청 [거절] | `Icons.Filled.Close` | 14.dp |
| 검색 TopBar 뒤로가기 | `Icons.AutoMirrored.Filled.ArrowBack` | 20.dp |
| 검색 입력 leading | `Icons.Filled.Search` | 16.dp |
| 검색 입력 clear | `Icons.Filled.Close` | 14.dp |
| relation NONE / 빈 상태 primary CTA | `Icons.Filled.PersonAdd` | 14.dp (검색 행) / 16.dp (빈 상태 CTA) |
| relation REQUEST_SENT 취소 | `Icons.Filled.Close` | 14.dp |
| relation REQUEST_RECEIVED [수락] | `Icons.Filled.Check` | 14.dp |
| relation REJECTED [다시 요청] | `Icons.Filled.Refresh` | 14.dp |
| 빈 상태 보조 CTA | `Icons.AutoMirrored.Filled.Send` | 16.dp |
| 친구 카드 [대결] (참고 — 본 spec 범위 외) | `Icons.Filled.SportsKabaddi` | 14.dp |

### F.3 색상 슬롯 매핑 (위 §D 재집약)

| 의미 | `ChallengeTheme.colorScheme.*` |
|---|---|
| 메인 / 검색 화면 배경 | `background` |
| 카드 (glass-card) bg | `surface` |
| 카드 border | `outline` (1.dp) |
| 프로필 placeholder bg / FRIEND 뱃지 bg / 검색 입력 bg / 거절·다시 요청 버튼 bg | `secondary` |
| primary 버튼 bg / 받은 요청 N건 강조 / [친구 요청] / [수락] | `primary` |
| primary 버튼 text | `onPrimary` |
| 본문 텍스트 / TopBar 라벨 / 카드 닉네임 | `onBackground` |
| 보조 텍스트 / placeholder / 검색 안내 / FRIEND 뱃지 텍스트 | `onSurfaceVariant` |
| destructive (현 단계 미사용 — 거절은 outline) | `error` (참고만) |

### F.4 Typography 슬롯 매핑

| 위치 | 슬롯 |
|---|---|
| 메인 TopBar "친구" | `bold18` |
| 빈 상태 헤드라인 | `bold16` |
| 빈 상태 서브라인 | `medium12` |
| 빈 상태 CTA 라벨 | `bold14` |
| 섹션 헤더 ("받은 요청 N건", "친구 N명") | `bold14` |
| 카드 닉네임 | `bold14` |
| 모든 버튼 라벨 (sm/full) | `bold14` |
| FRIEND 뱃지 "이미 친구" | `bold12` |
| 검색 입력 텍스트 | `medium14` |
| 검색 placeholder | `medium14` |
| 검색 안내 (Idle/Empty) | `medium14` |
| 프로필 emoji placeholder | `medium20` (preview 한정 — 실 데이터 모델은 닉네임 이니셜) |

### F.5 Radius / Shape

| 위치 | dp |
|---|---|
| 카드 컨테이너 | 16.dp |
| 모든 버튼 (sm / full) | 12.dp |
| 검색 입력 박스 | 12.dp |
| 프로필 placeholder | 12.dp |
| FRIEND 뱃지 | 12.dp |
| 뒤로가기 IconButton | 12.dp (또는 `CircleShape` — 모바일 재량) |

### F.6 Spacing (전부 dp)

| 위치 | 값 |
|---|---|
| 화면 가로 padding | 20 |
| TopBar 높이 | 56 |
| 검색 입력 높이 | 40 |
| 친구 카드 padding | 16 |
| 받은 요청 카드 padding | 12 |
| 검색 결과 카드 padding | 12 |
| 카드 내부 spacedBy | 12 |
| ActionRow 2버튼 spacedBy | 8 |
| 받은 요청 [수락]/[거절] spacedBy | 6 |
| 카드 리스트 spacedBy | 8 |
| 섹션 간 spacedBy | 20 |
| 본문 첫 섹션 top padding | 16 |
| 프로필 placeholder (요청/친구) | 48 × 48 |
| 프로필 placeholder (검색) | 44 × 44 |
| 검색 안내 텍스트 top padding | 64 |
| 빈 상태 카드 내부 padding | 24 (1차 1단계 §4와 동일) |

---

## G. mobile-dev 강조 사항 (T-M1~M6 인계 시)

1. **친구 목록 1행은 `FriendListItem` 신규** — 1차 1단계 §2 입력안 `FriendCard`(전적+대결)는 본 spec 범위 밖. `FriendListItem(profileImageUrl, nickname)` 단순 시그니처만 구현.
2. **`FriendsEmptyState` 확장**: 1차 1단계 단일 CTA → 2차 보조 CTA 추가. 기존 props에 `onClickInvite: (() -> Unit)? = null` 추가하고, null일 때는 1차 1단계 동일 시각. **1차 1단계 호출처는 영향 없음** (default null). **주의**: Lovable preview (`src/routes/friends.tsx` 빈 상태 카드)는 2차 모드(보조 CTA 노출)만 표현하며 props 없이 inline으로 그려졌으므로 비파괴 보장은 Compose 측 의무. Lovable에서 1차 fallback 시각을 보려면 별도 mock 화면 필요.
3. **`FriendsTopBar`는 props 0개 그대로** — 메인 화면 액션은 본문 ActionRow로 외주화. spec.md §6.4 흐름 일치.
4. **검색 입력 debounce**는 ViewModel 책임 — `FriendsSearchTopBar`는 onQueryChange만 즉시 호출. 모바일 ViewModel에서 `flow { ... }.debounce(300.milliseconds).filter { it.length >= 2 }` 처리.
5. **relation 5종 시각은 §B.5 표가 단일 출처** — Lovable과 본 design.md 둘 다 동일. 모바일에서 다른 시각 채택 시 Lovable + design.md 모두 갱신 (Lovable ↔ 모바일 동기 메모리 규칙).
6. **`REQUEST_SENT` 취소 버튼은 별도 클릭 영역** — "요청 보냄" 라벨 자체는 클릭 무동작이고, 옆의 `X` 아이콘 버튼만 `onClickCancel` 호출. Compose에서 둘을 `Row` 안에 별도 `Surface`/`IconButton`으로 배치.
7. **낙관적 갱신** — repository 호출 전에 즉시 UI 전환, 실패 시 롤백 + 스낵바. ViewModel에서 처리.
8. **`materialIconsExtended` 의존성**: 이미 `:feature:home` / `:feature:main`에 있으면 `:feature:friends`도 동일 패턴 추가. `Icons.AutoMirrored.Filled.{ArrowBack, Send}`는 RTL 자동 대응을 위해 AutoMirrored 사용.

---

## H. ⚠️ 확인 필요 / 디자이너 협의 항목 (2차)

| # | 항목 | 본안 | 결정 필요 시점 |
|---|---|---|---|
| 1 | 프로필 placeholder — 닉네임 이니셜 vs emoji vs 이미지 fallback | **닉네임 첫 1글자 + `colorScheme.secondary` bg** (Lovable preview는 emoji지만 실 데이터 모델은 nickname + profileImageUrl 두 필드만 — spec.md §5.1 응답 DTO 기준) | 결정 완료 — 단, 디자이너 별도 아이콘/일러스트 합류 시 교체 (backlog) |
| 2 | `REQUEST_SENT`의 disabled "요청 보냄" 라벨 시각 — Button(disabled) vs Surface 정적 | **Surface 정적** (Button(enabled = false)의 자동 alpha 0.38 회피, opacity 100% 유지) | 결정 완료 |
| 3 | 검색 안내 텍스트 노출 위치 — 화면 중앙 vs TopBar 직후 | **TopBar 직후 64.dp top padding** (Lovable `mt-16` 매핑) — 입력 컨텍스트 가깝게 | 결정 완료 |
| 4 | 메인 화면 ActionRow 위치 — TopBar 액션 슬롯 vs 본문 상단 | **본문 상단** (TopBar는 라벨만, 액션은 본문 첫 줄) | 결정 완료 |
| 5 | 친구 카드 [대결] 버튼 노출 여부 (본 spec 범위) | **본 spec은 미노출** — `FriendListItem`은 프로필+닉네임만. 친구별 1:1 대결 신청은 후속 spec에서 별도 정의 | 후속 spec 진입 시 |
| 6 | 카카오 초대 진입점 위치 — ActionRow vs FAB | **ActionRow** (메인 진입점 2개를 평등하게 노출, FAB는 홈 챌린지 생성과 시각 중복 회피) | 결정 완료 |
| 7 | 일러스트 자산 | 1차 1단계와 동일 — `Icons.Filled.Group` 임시. 추후 일러스트 자산 합류 시 교체 (backlog) | backlog |

---

## I. Lovable working tree 변경 요약 (2차)

```
modified:   src/routes/friends.tsx       (받은 요청 인라인 섹션 + ActionRow + FriendListItem 단순화 + 빈 상태 보조 CTA)
new file:   src/routes/friends-search.tsx (신규 검색 화면 — 5 relation × 3 상태)
modified:   src/routeTree.gen.ts         (friends-search 라우트 등록)
```

**Lovable git**: `0b65b6c` (`친구 추가 화면 신규 + 친구 목록 메인 받은 요청/액션 섹션 추가`) — main에 push 완료.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-06-24 | 최초 작성 — Lovable `friends.tsx` 빈 상태 분기 + `FriendsEmptyState` sub-component 반영. 2개 화면 상태(empty 본 단계 / default 1차 2단계 입력) 명세. `FriendsEmptyState`/`FriendsTopBar` 2개 컴포넌트 props·토큰 매핑 1차안. 친구 카드(1차 2단계) 시각 토큰 매핑 표 + props 권고 등재. ⚠️ 확인 필요 6건 §6. | design-bridge |
| 2026-06-25 | **2차 — 친구 추가 섹션 추가**. Lovable `friends.tsx` 받은 요청 인라인 + ActionRow 추가, `friends-search.tsx` 신규 (relation 5종 × Idle/Result/Empty 3상태). Compose 컴포넌트 spec 4종 (`FriendListItem`, `FriendRequestCard`, `FriendSearchItem`, `FriendsSearchTopBar`) props 시그니처. relation 5종 시각 명세 단일 출처. 1차 1단계 §2 `FriendCard`(전적+대결)는 사장 — 본 spec은 `FriendListItem` 단순 1행. ⚠️ 확인 필요 7건 §H. Lovable commit `0b65b6c`. | design-bridge |
