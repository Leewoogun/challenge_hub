# Design — home-feed

- **디자인 소스**: `/Users/hwamulman/woogunProject/challenge/challenge-design/oathbound-challenges`
- **참조 route**: `src/routes/index.tsx` (수정됨 — 빈 상태 분기 + 신규 stats 톤 추가)
- **참조 컴포넌트**: `src/components/ChallengeCard.tsx`, `src/components/BottomNav.tsx`
- **전역 토큰**: [`docs/design-system/tokens.md`](../../design-system/tokens.md), [`colors.md`](../../design-system/colors.md)
- **스냅샷 일시**: 2026-05-25
- **대상 화면 수**: 1 화면(HomeScreen) × 3 상태 (default / first_user / no_active_challenge)
- **신규 컴포넌트**: `ChallengeCard`, `StatsBar`, `HomeEmptyState` — 모두 `:core:designsystem`에 추가 제안

---

## 0. 변경 요약 (Lovable index.tsx)

기존 `src/routes/index.tsx`는 챌린지 3건 + stats `7/3/2/3🔥`가 하드코딩된 default 상태만 표현. 본 작업으로 다음을 반영:

1. `mockChallenges` 배열 길이를 보는 `isEmptyChallenges` 플래그 + stats 전부 0 여부로 `isFirstUser` 플래그를 노출 → Lovable에서 빈 상태를 시각적으로 검토 가능.
2. 빈 상태일 때 `HomeEmptyState` (신규 sub-component) 표시. `variant: "first_user" | "no_active_challenge"` 분기로 헤드라인/서브라인 차이.
3. Stats bar를 `StatCell` 헬퍼로 분리 — 신규 사용자(전부 0)일 땐 `tone="muted"`로 모든 숫자를 `muted-foreground` 색으로 표시(빈 칸 금지 원칙).
4. 연승 셀의 `🔥` 이모지는 `currentStreak > 0`일 때만 노출. 0이면 단순 `0`.
5. FAB는 빈 상태에서도 그대로 표시(상시 노출). 빈 상태 카드의 primary CTA "챌린지 만들기"와 라우팅이 겹치지만, 화면 외부의 영구 액션이라 유지.

> Lovable의 `mockChallenges` / `mockStats` 상수는 디자인 검토 토글용. 실제 데이터 연동 후엔 GET /api/v1/home 응답으로 교체된다.

---

## 1. HomeScreen — default (챌린지 있음, 기존 사용자)

- **참조**: `src/routes/index.tsx` (수정 후)
- **의도**: 사용자가 책임지고 있는 약속들을 한눈에 보여주고 누적 전적으로 동기 부여.
- **레이아웃** (위→아래):
  1. **Sticky Header** (`bg-background/80 backdrop-blur-xl`, 좌우 20.dp 패딩 + safe-top inset)
     - 좌측: `Flame` 24.dp(primary) + "맹세" 라벨 (text-xl extrabold)
     - 우측: `Bell` 아이콘 + 우상단 2.dp dot (destructive) — 미확인 알림 표시
  2. **Stats bar** (`glass-card`, 수평 4분할)
     - 각 셀: 숫자(text-lg bold) + 라벨(10sp muted) 세로 정렬
     - 셀 구분: 8.dp 높이 세로 보더(`bg-border`)
     - 연승 셀만 `value > 0`일 때 `🔥` 접미
  3. **Section title row**: "진행 중인 챌린지" (text-base bold) + N개 카운트 (10sp muted)
  4. **ChallengeCard list** (deadline asc 정렬, `space-y-3` = 12.dp 간격)
  5. **FAB** (우하단, `bottom-24 + safe-bottom`): primary `Plus` 56×56.dp 라운드 16.dp + pulse-fire 애니메이션
  6. **BottomNav** (이미 구현됨, bottom-navigation feature 참조)
- **상호작용**:
  - 카드 탭 → 챌린지 상세 화면(이번 feature 범위 밖, navigation stub)
  - FAB 탭 → 챌린지 생성 화면(stub)
  - Bell 탭 → /notifications (stub)
- **토큰**: `colorScheme.background` / `colorScheme.surface` (glass-card) / `colorScheme.primary` / `colorScheme.warning`(연승) / `colorScheme.destructive`(패) / `colorScheme.outline`(구분 보더) / `typography.bold18`(섹션 타이틀) / `typography.bold18` 또는 `bold20`(헤더 "맹세") / `typography.medium10`(stats 라벨) — tokens.md §5.2
- **상태**: default (이 절)
- **모바일 대응**:
  - `app-container max-w-[430px]` 무시 → 화면 full-width.
  - `sticky` 헤더 + `backdrop-blur-xl` → Compose는 alpha 80% + 1.dp 보더 근사(bottom-navigation 결정과 동일). 본 feature는 헤더의 시각 우선순위가 BottomBar보다 낮아 alpha만으로 충분.
  - FAB의 `right-[max(1rem,calc(50%-215px+1rem))]`은 430px 컨테이너 보정값 — 모바일은 단순 `Modifier.padding(end=16.dp, bottom=24.dp + bottomBarHeight)`로 대체.

---

## 2. HomeScreen — empty / first_user (신규 사용자)

- **트리거**: `stats.win + lose + draw + currentStreak == 0 && activeChallenges.isEmpty()`
- **의도**: 가입 직후 사용자가 첫 행동(친구 등록 → 첫 챌린지)을 명확히 인지하도록 유도. "데이터 없음"이 아니라 "이제 시작" 톤.
- **레이아웃 변경점** (default 대비):
  - **Stats bar**: 4개 셀 모두 노출하되 색은 `muted-foreground` 단일. 숫자 값은 `0` 그대로. 빈 칸/대시 표시 ❌.
  - **챌린지 영역**: 카드 리스트 자리에 `HomeEmptyState(variant = "first_user")` 1개 카드.
    - 일러스트 자리: 64×64.dp 라운드 16.dp, `primary/10%` 배경 + Flame 32.dp(primary). 추후 일러스트 자산 합류 시 교체.
    - 헤드라인: "아직 진행 중인 챌린지가 없어요" (text-base bold)
    - 서브라인: "친구를 등록하고 첫 약속을 걸어보세요" (12sp muted)
    - CTA 2버튼 가로 배치 (`gap-2`, `flex-1`):
      - 좌측: `outline` variant + `UserPlus` 아이콘 + "친구 등록" → /friends
      - 우측: `default` (primary) variant + `Swords` 아이콘 + "챌린지 만들기" → /challenge-new
    - 두 버튼 모두 `size="full"` (h-13, 약 52.dp 높이)
  - 섹션 타이틀 "진행 중인 챌린지" + N개 카운트(0개)는 유지 — 컨텍스트 제공.
- **상호작용**:
  - "친구 등록" 탭 → /friends (BottomNav의 친구 탭 진입과 동일 동작)
  - "챌린지 만들기" 탭 → /challenge-new (FAB와 동일 라우팅)
- **토큰**: 위 default + `colorScheme.primary.copy(alpha=0.10f)` (일러스트 배경)
- **모바일 대응**: 위 default와 동일.
- ⚠️ **확인 필요**:
  - **신규 사용자에게 FAB도 노출할지** — 본안은 노출. 빈 상태 카드의 "챌린지 만들기" 버튼과 라우팅 중복이라 시각/인지 부담. pm-lead 판단으로 빈 상태일 때 FAB 숨김 옵션 가능.
  - **일러스트 자산 의도** — 1차안은 Flame 아이콘 단순 사용. 디자이너가 별도 일러스트 제공 시 교체. backlog 후보.

---

## 3. HomeScreen — empty / no_active_challenge (기존 사용자, 챌린지 0개)

- **트리거**: `activeChallenges.isEmpty() && (stats.win + lose + draw + currentStreak) > 0`
- **의도**: 누적 전적은 유지(자존감) + 챌린지 영역만 부드럽게 "다시 시작" 유도.
- **레이아웃 변경점** (first_user 대비):
  - **Stats bar**: default와 동일 톤(primary/destructive/foreground/warning) 색 유지. 숫자도 실제 누적값.
  - **챌린지 영역**: `HomeEmptyState(variant = "no_active_challenge")` 1개 카드.
    - 헤드라인: "진행 중인 챌린지가 없어요"
    - 서브라인: "새 챌린지를 시작해 다시 불을 붙여보세요"
    - CTA 2버튼은 first_user와 동일 (친구 등록 + 챌린지 만들기) — 친구가 이미 있는 사용자라도 신규 친구 등록 경로는 항상 유효하므로 단순화.
  - 섹션 타이틀 + 0개 카운트 유지.
- **상호작용 / 토큰**: first_user와 동일.
- ⚠️ **확인 필요**:
  - 기존 사용자에겐 "친구 등록" CTA가 불필요할 수 있음. 1차안은 first_user와 동일 2버튼 유지(단순화). 디자이너 판단으로 "챌린지 만들기" 단일 버튼(`size="full"`)으로 축소 가능 — backlog 후보.

---

## 4. 컴포넌트 매핑

| Lovable 소스 | Compose 제안 | 신규/기존 | 비고 |
|---|---|---|---|
| `<ChallengeCard {...} />` (`src/components/ChallengeCard.tsx`) | `ChallengeCard` (`:core:designsystem`) | **신규** | 7개 props (§4.1). 카드 자체는 `glass-card` 룩 — `colorScheme.surface` + `colorScheme.outline` 1dp + `RoundedCornerShape(16.dp)`. |
| Stats bar 인라인 (`src/routes/index.tsx` 70~91행) | `StatsBar` (`:core:designsystem`) | **신규** | 4개 숫자 props (§4.2). 4분할 + 세로 보더 구조 고정. 톤 분기는 컴포넌트 내부가 아닌 호출부가 결정한 토큰을 받게(권고). |
| Empty state block (`HomeEmptyState` sub-component) | `HomeEmptyState` (`:core:designsystem`) | **신규** | variant 분기 1 props (§4.3). 추후 friends/ranking 빈 상태에도 재사용 가능. |
| Header (`<header>` Lovable) | `:feature:home` 내부 인라인 (`HomeTopBar`) | 기존 영역 | 다른 화면(친구/랭킹/MY) 헤더와 패턴 유사하지만 본 feature 범위는 home 한정. 추출은 후속 feature에서. |
| FAB (`<Link>` + `<Button>` icon) | `:feature:home` 내부 인라인 | 기존 영역 | `:core:designsystem`의 `Button` 활용. 위치 보정만 home 화면이 책임. |
| `BottomNav` | 기존 `ChallengeBottomBar` (`:feature:main`) | 기존 — bottom-navigation feature 완료분 | 변경 없음. |
| lucide `Bell` / `Flame` / `Plus` / `UserPlus` / `Swords` / `Clock` / `CheckCircle2` / `XCircle` | `Icons.Filled.{Notifications, LocalFireDepartment, Add, PersonAdd, SportsKabaddi, Schedule, CheckCircle, Cancel}` | 기존 — `materialIconsExtended` | bottom-navigation에서 채택한 옵션 A(Material Icons Extended) 일관 적용. ⚠️ `Swords` ↔ `SportsKabaddi` 의미는 유사하나 비주얼이 다름 — 디자이너 검토 필요. 대안: `Icons.Filled.LocalFireDepartment` 재사용 또는 lucide SVG 번들. |

### 4.1 `ChallengeCard` (Compose, 신규) — props 명세

Lovable 소스의 7개 표시 필드를 그대로 매핑. 단, **navigation은 호출부 책임**(카드 자체는 `onClick: () -> Unit` 1개만 받음 — `Link` 래핑 안 함).

```kotlin
@Composable
fun ChallengeCard(
    challengeId: Long,                      // 카드 식별 / 클릭 시 호출부가 사용
    myMission: String,                      // "오늘 운동 1시간 하기"
    opponentNickname: String,               // "민수"
    opponentMission: String,                // "책 30페이지 읽기"
    deadline: Instant,                      // ISO-8601 UTC, 표시는 "5시간 32분" 같은 상대 시간
    myVerificationStatus: VerificationStatus,
    opponentVerificationStatus: VerificationStatus,
    bet: String,                            // "커피 사기 ☕"
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
)
```

- **표시 변환**:
  - `deadline` → 모바일에서 상대 시간 텍스트 변환(`Clock.System.now()` 차이 계산). "X시간 Y분" / "X분" / "지났음". `:core:utils`에 헬퍼 두기 권장. ⚠️ Lovable의 "완료" 케이스(deadline 지난 IN_PROGRESS)는 1차 API 응답에서 제외되므로 본 컴포넌트는 미래 deadline만 가정.
  - `myVerificationStatus` / `opponentVerificationStatus` → 우측 상단 status pill (10sp semibold). 3종 매핑:
    - `PENDING` → `Clock` 아이콘 + "대기중" / `colorScheme.warning` text + `warning.copy(alpha=0.10f)` bg
    - `VERIFIED` → `CheckCircle` 아이콘 + "인증완료" / `colorScheme.success` text + `success.copy(alpha=0.10f)` bg
    - `FAILED` → `Cancel` 아이콘 + "실패" / `colorScheme.error` text + `error.copy(alpha=0.10f)` bg
  - `bet` → 카드 하단 띠 (8.dp 패딩, `primary/5%` bg, `primary/10%` 1dp 보더, `radius-lg = 12.dp`): `🔥` + "내기: {bet}" (12sp medium, color = primary)
- **레이아웃** (위→아래, 16.dp 내부 패딩):
  1. 헤더 row: 좌측 `Flame` 18.dp(primary) + "vs {opponent}" 12sp medium muted / 우측 `Clock` 14.dp + 상대시간 12sp medium warning
  2. 미션 row × 2 (`space-y-2` ≈ 8.dp 간격):
     - "나의 미션" 11sp muted + myMission 14sp semibold (강조)
     - "{opponent}의 미션" 11sp muted + opponentMission 14sp medium muted (상대 미션은 약간 톤 다운)
     - 각 row 우측에 status pill
  3. 내기 띠
- **모바일 주의**:
  - Lovable의 `space-y-2` / `gap-3` 등은 §토큰(spacing) 단위로 환산.
  - lucide 아이콘 크기 18/14는 Compose `Modifier.size(18.dp)` / `size(14.dp)`.
  - status pill의 `text-[10px]` → `typography.medium10` (tokens.md §5.2 슬롯 사용. ⚠️ semibold→Medium 정책 §5.3).
  - 카드 진입 애니메이션(`animate-slide-up`) → `AnimatedVisibility` + `slideInVertically` 선택 적용. 리스트 아이템마다 동일 애니메이션이면 성능 영향 미미.

### 4.2 `StatsBar` (Compose, 신규) — props 명세

```kotlin
@Composable
fun StatsBar(
    win: Int,
    lose: Int,
    draw: Int,
    currentStreak: Int,
    modifier: Modifier = Modifier,
)
```

- **레이아웃**: 가로 4분할 Row + 사이에 8.dp 높이 1.dp 세로 보더(`colorScheme.outline`). 컨테이너는 `glass-card` 룩(`colorScheme.surface` + 12.dp radius + 24.dp 카드 shadow 또는 생략).
- **각 셀**:
  - 숫자: `typography.bold18` (Lovable `text-lg font-bold` = 18sp/28). 색은 셀별 의미 색.
  - 라벨: `typography.medium10` (10sp medium muted)
- **셀별 색 매핑** (호출부에서 결정 vs 컴포넌트 내부에서 결정):
  - **권고**: 컴포넌트 내부가 결정. 4개 값이 **모두 0**이면 신규 사용자로 간주하고 4개 셀 전부 `onSurfaceVariant` 단일 톤. 하나라도 0이 아니면 의미 색(win=primary, lose=error, draw=onBackground, currentStreak=warning).
  - 호출부에 노출 안 함(API 응답 그대로 받고 컴포넌트가 처리) — 화면 코드 단순화.
- **연승 셀**:
  - `currentStreak == 0` → "0" 만 표시(이모지 ❌)
  - `currentStreak > 0` → "{N}🔥" — 🔥는 라벨 옆이 아니라 숫자에 붙임. 이모지 폰트 렌더는 시스템에 의존.
  - ⚠️ Compose에서 🔥 이모지는 fontFamily에 따라 렌더가 갈림(GmarketSans 미지원). `Text("$value🔥")`로 시스템 폰트 fallback에 맡김 — Android/iOS 모두 무난.
- ⚠️ **확인 필요**:
  - "무" 셀 색을 plain `onBackground`로 둘지, 별도 의미 색을 줄지 — Lovable은 색 미지정(검정 텍스트 = `foreground`). 본안 유지.

### 4.3 `HomeEmptyState` (Compose, 신규) — props 명세

```kotlin
@Composable
fun HomeEmptyState(
    type: HomeEmptyStateType,               // FIRST_USER | NO_ACTIVE_CHALLENGE
    onClickAddFriend: () -> Unit,
    onClickCreateChallenge: () -> Unit,
    modifier: Modifier = Modifier,
)

enum class HomeEmptyStateType { FIRST_USER, NO_ACTIVE_CHALLENGE }
```

- **레이아웃** (24.dp 내부 패딩, 컨테이너는 `glass-card` 룩):
  1. 일러스트 자리: 64×64.dp + 16.dp radius + `primary.copy(alpha=0.10f)` bg + Flame 32.dp(primary). 중앙 정렬.
  2. 16.dp gap
  3. 헤드라인 (`typography.bold18` 또는 `bold16` — Lovable `text-base font-bold` 기준 **bold16 권고**)
  4. 4.dp gap
  5. 서브라인 (`typography.medium12`, `onSurfaceVariant`)
  6. 20.dp gap
  7. CTA 2버튼 Row (`Arrangement.spacedBy(8.dp)`):
     - 좌측 `OutlinedButton` (둘 다 `weight(1f)`): `PersonAdd` 16.dp + "친구 등록"
     - 우측 `Button` (primary): `SportsKabaddi` 16.dp + "챌린지 만들기"
     - 버튼 높이 52.dp(`size="full"` 매핑), radius 12.dp
- **type별 텍스트**:
  - `FIRST_USER`: "아직 진행 중인 챌린지가 없어요" / "친구를 등록하고 첫 약속을 걸어보세요"
  - `NO_ACTIVE_CHALLENGE`: "진행 중인 챌린지가 없어요" / "새 챌린지를 시작해 다시 불을 붙여보세요"
- ⚠️ **확인 필요**:
  - 1차안은 type별로 CTA 동일(2버튼). 디자이너가 `NO_ACTIVE_CHALLENGE` 케이스에 단일 "챌린지 만들기"만 표시하기로 결정하면 props를 `cta: SingleCta | DoubleCta` 형태로 변형 가능. backlog 후보.

---

## 5. 전역 토큰 (참조)

본 feature 도입으로 신규 추가되는 토큰 없음. 모두 기존 `ChallengeColorScheme` 슬롯으로 커버 가능.

- `colorScheme.background` / `surface` / `outline` / `primary` / `onPrimary` / `error` / `success` / `warning` / `onBackground` / `onSurfaceVariant`
- `colorScheme.primary.copy(alpha=0.10f)` — 일러스트 배경, status pill 배경, 내기 띠 배경. **신규 슬롯화 ❌** (alpha 적용은 호출부 책임).
- `typography.bold18` / `bold16` / `medium14` / `medium12` / `medium10` / `bold18` — 전부 기존 슬롯.

> tokens.md §5.2의 `text-[11px]` (Lovable이 "나의 미션" 라벨에 사용)은 비표준 슬롯. 본안은 `medium12` (12sp)로 근사하고 backlog에 미세 정합 후보 등재. — bottom-navigation의 `medium10` 슬롯 신설 같은 추가는 미정.

---

## 6. ChallengeCard 시각 토큰 매핑 표

| 항목 | Lovable | Compose 매핑 | 비고 |
|---|---|---|---|
| 카드 배경 | `glass-card` = `var(--gradient-card)` + 1px 보더 + shadow | `Modifier.background(brushes.card)` or `colorScheme.surface` + `Modifier.border(1.dp, colorScheme.outline, RoundedCornerShape(16.dp))` | 1차안은 단순 surface 사용. brushes.card 사용은 시각 검토 후. |
| 카드 radius | `--radius-xl` (16px) | `RoundedCornerShape(16.dp)` | tokens.md §4 |
| 내부 패딩 | `p-4` (16px) | `Modifier.padding(16.dp)` | |
| 헤더 "vs {opponent}" | `text-xs font-medium text-muted-foreground` | `typography.medium12` + `onSurfaceVariant` | |
| 헤더 timeLeft | `text-xs text-warning font-medium` | `typography.medium12` + `colorScheme.warning` | |
| 미션 라벨 ("나의 미션") | `text-[11px] text-muted-foreground` | `typography.medium12` + `onSurfaceVariant` | ⚠️ 11px → 12sp 근사 |
| 미션 본문 (내) | `text-sm font-semibold` | `typography.medium14` + `onBackground` | §5.3 semibold→Medium |
| 미션 본문 (상대) | `text-sm font-medium text-muted-foreground` | `typography.medium14` + `onSurfaceVariant` | |
| status pill 텍스트 | `text-[10px] font-semibold` | `typography.medium10` + 의미 색 | medium10 슬롯(tokens.md §5.2) |
| status pill 패딩 | `px-2 py-1` (8px / 4px) | `PaddingValues(horizontal = 8.dp, vertical = 4.dp)` | |
| status pill radius | `rounded-lg` (10px) | `RoundedCornerShape(10.dp)` | |
| 내기 띠 텍스트 | `text-xs font-medium text-primary` | `typography.medium12` + `colorScheme.primary` | |
| 내기 띠 배경 | `bg-primary/5 border border-primary/10` | `colorScheme.primary.copy(alpha=0.05f)` + 1.dp border `primary.copy(alpha=0.10f)` | |
| 내기 띠 radius | `rounded-lg` (10px) | `RoundedCornerShape(10.dp)` | |

---

## 7. ⚠️ 확인 필요 / 디자이너 협의 항목 (집약)

| # | 항목 | 본안 | 결정 필요 시점 |
|---|---|---|---|
| 1 | 빈 상태(`first_user`)에서 FAB 노출 여부 | 노출 유지 | 모바일 구현 전 |
| 2 | `no_active_challenge`에서 CTA 2버튼 vs 1버튼 | 2버튼 유지(first_user와 동일) | 모바일 구현 전 |
| 3 | 빈 상태 일러스트 자산 | Flame 32.dp + primary 10% 배경 임시 | 디자이너 별도 일러스트 합류 시 교체 (backlog) |
| 4 | `Swords` lucide → Material `SportsKabaddi` 매핑 | 채택, 시각 검토 필요 | 모바일 구현 직후 |
| 5 | `text-[11px]` 슬롯(`medium11`) 신설 vs `medium12` 근사 | 근사 채택 | 후속 feature에서 사용처 누적 시 재논의 |
| 6 | "무" 셀 색을 plain foreground로 둘지 | Lovable과 동일 plain | — |
| 7 | StatsBar 톤 분기를 컴포넌트가 결정 vs 호출부 | 컴포넌트가 결정(4값 모두 0이면 muted) | 모바일 구현 전 |

---

## 8. mobile-dev 강조 사항 (인계 시 주의)

본 feature 인계 시 다음을 반드시 강조:

1. **`deadline: Instant` → 상대 시간 변환은 화면 진입 시점 기준**. ViewModel이 상태 보존을 하지 않고 매 composition마다 재계산해도 무방(StateFlow 1회 갱신만으로 충분). `:core:utils`에 `Instant.toRelativeKoreanString()` 헬퍼 두기 권장. ⚠️ 시계 의존 — 테스트에서는 Clock 주입.
2. **빈 상태 분기는 ViewModel이 책임**: `HomeUiState`는 `Loading / Success(stats, challenges, emptyType: FIRST_USER | NO_ACTIVE_CHALLENGE | NONE) / Error` 패턴 권고. 화면 코드에서 `if/else` 분기 최소화. API 응답을 받자마자 `(stats == zero && challenges.isEmpty) -> FIRST_USER`, `(challenges.isEmpty) -> NO_ACTIVE_CHALLENGE`, `else -> NONE` 매핑 (api-contract.md §모바일측 주의사항 그대로 따름).
3. **`materialIconsExtended` 의존성을 `:feature:home`에 추가**: bottom-navigation feature와 동일 패턴. `Bell` → `Icons.Filled.Notifications`, `Flame` → `Icons.Filled.LocalFireDepartment`, `Plus` → `Icons.Filled.Add`, `UserPlus` → `Icons.Filled.PersonAdd`, `Swords` → `Icons.Filled.SportsKabaddi`, `Clock` → `Icons.Filled.Schedule`, `CheckCircle2` → `Icons.Filled.CheckCircle`, `XCircle` → `Icons.Filled.Cancel`.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-05-25 | 최초 작성 — Lovable `index.tsx` 빈 상태 분기 + stats 톤 정합 반영. 3개 화면 상태(default/first_user/no_active_challenge) 명세. `ChallengeCard`/`StatsBar`/`HomeEmptyState` 3개 컴포넌트 props·토큰 매핑 1차안 작성. ⚠️ 확인 필요 7건 §7 등재. | design-bridge |
