# Design — bottom-navigation

- **디자인 소스**: `/Users/hwamulman/woogunProject/challenge/challenge-design/oathbound-challenges`
- **참조 컴포넌트**: `src/components/BottomNav.tsx`
- **참조 route** (placeholder 톤 가늠용): `src/routes/{index,friends,ranking,mypage}.tsx`
- **전역 토큰**: [`docs/design-system/tokens.md`](../../design-system/tokens.md), [`colors.md`](../../design-system/colors.md)
- **스냅샷 일시**: 2026-05-08
- **대상 화면 수**: 1 컴포넌트 (ChallengeBottomBar) + 3 placeholder Screen (Friends / Ranking / MyPage)

---

## 컴포넌트 — ChallengeBottomBar

- **참조**: `src/components/BottomNav.tsx`
- **의도**: 메인 셸의 4탭(홈/친구/랭킹/MY) 영구 navigation. 화면 하단 고정, 다크 카드 위 active 탭만 fiery primary로 강조.
- **위치**: `Scaffold(bottomBar = { ChallengeBottomBar(...) })`. Splash/Login 진입 화면에선 숨김(MainScreen에 기존 분기 유지).
- **레이아웃**:
  - 컨테이너: 화면 폭 전체 (`fillMaxWidth`), 4탭을 `Row` + `Arrangement.SpaceAround`로 균등 배치.
  - 각 탭: 세로 컬럼 — 아이콘 1개 + 라벨(`gap-0.5` ≈ 2.dp).
  - 탭 패딩: 좌우 12.dp, 위 6.dp / 아래 6.dp (Lovable `px-3 py-1.5` 정확 매핑).
  - Bar 컨테이너 패딩: 위 8.dp + 아래 safe-area inset (`max(8.dp, safeBottom)`).
- **상호작용**:
  - 탭 클릭 → 해당 `Route.{...}.Main`으로 navigate. 이미 active 탭 재클릭 시 무동작(또는 스크롤 top — 본 feature 범위 외).
  - Pressed 시 ripple. Material 기본 ripple 사용. ⚠️ Lovable엔 ripple/hover 명시 없음(`transition-colors`만) → 디자이너 검토 없이 Material 기본값 채택.
  - 진입/탭 전환 애니메이션 없음 (Lovable이 `transition-colors`만 사용).

### 시각 토큰 매핑 표

| 항목 | Lovable | Compose 매핑 | 비고 |
|---|---|---|---|
| Bar 배경 | `bg-card/95` | `ChallengeTheme.colorScheme.surface.copy(alpha = 0.95f)` | `#2F303A` 95% alpha |
| Bar blur | `backdrop-blur-xl` | ⚠️ **Compose Multiplatform에 직접 등가 없음** — 근사안: 배경 alpha 95% + 1.dp 상단 보더만 유지. iOS는 `UIVisualEffectView` 인터롭, Android API 31+는 `Modifier.blur(20.dp)` 가능하나 KMP 공통 API 미지원 → 본 feature는 **alpha 95%로 단순 근사**, blur 미적용. |
| Bar 상단 보더 | `border-t border-border` | `Modifier.drawBehind { drawLine(color = colorScheme.outline, start = (0,0), end = (width,0), strokeWidth = 1.dp.toPx()) }` 또는 `HorizontalDivider(color = outline)` 를 Bar 상단에 배치 | `#43444E` 1dp |
| 화면 부착 | `fixed bottom-0 z-50` | `Scaffold(bottomBar = ...)` 기본 동작 | Compose에선 별도 z-index 불필요 |
| 최대 폭 | `max-w-[430px] left-1/2 -translate-x-1/2` | 무시. `fillMaxWidth()` 사용 | 네이티브에서 의미 없음 (tokens.md §6과 동일) |
| 탭 라벨 active | `text-primary` | `ChallengeTheme.colorScheme.primary` (`#E97A3D`) | |
| 탭 라벨 inactive | `text-muted-foreground` | `ChallengeTheme.colorScheme.onSurfaceVariant` (`#9596A0`) | |
| 탭 아이콘 active 색 | `text-primary` (= 라벨과 동일) | 동상 | |
| 탭 아이콘 inactive 색 | `text-muted-foreground` (= 라벨과 동일) | 동상 | |
| 탭 컨테이너 모서리 | `rounded-xl` | 시각 영향 없음(배경 색이 없으니 모서리 불가시) → 생략 가능. ripple 클리핑만 `RoundedCornerShape(16.dp)`로 정리. | |
| Safe area (하단) | `pb-[max(0.5rem,env(safe-area-inset-bottom))]` | `Modifier.windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom))` 또는 `NavigationBar`의 기본 인셋 처리 | iOS notch/홈 인디케이터 보호 |

### 사이즈

| 항목 | Lovable | Compose |
|---|---|---|
| 아이콘 사이즈 | `size={22}` | `Modifier.size(22.dp)` |
| 아이콘 strokeWidth (active) | `2.5` | ⚠️ Compose `Icon`/`ImageVector`는 strokeWidth 런타임 제어 불가 → **무시**. 굵기 차이는 색(primary vs muted)만으로 표현. 또는 lucide의 두 굵기 variant SVG를 둘 다 번들(옵션 B 시). |
| 아이콘 strokeWidth (inactive) | `1.8` | 동상 |
| 라벨 폰트 사이즈 | `text-[10px]` | 10.sp. 가장 가까운 슬롯은 `medium12` — ⚠️ 정확히 10.sp는 `ChallengeTypoGraphy`에 없음. **권고: inline `TextStyle(fontSize = 10.sp, fontWeight = Medium, lineHeight = 14.sp)` 직접 지정 + tokens.md에 `medium10` 슬롯 신설 후보 등재.** |
| 라벨 폰트 굵기 | `font-medium` (500) | `FontWeight.Medium` → GmarketSans Medium (tokens.md §5.3) |
| 아이콘-라벨 간격 | `gap-0.5` (2px) | `Modifier.padding(top = 2.dp)` 또는 `Arrangement.spacedBy(2.dp)` |
| 탭 좌우 패딩 | `px-3` (12px) | `PaddingValues(horizontal = 12.dp)` |
| 탭 위/아래 패딩 | `py-1.5` (6px) | `PaddingValues(vertical = 6.dp)` |
| Bar 자체 상하 패딩 | `py-2` (8px, 아래는 safe-area로 확장) | 위 8.dp + 아래 `max(8.dp, safeBottom)` |

### Active / Inactive 상태

- **Active**: 색 `primary` + (디자인) 굵은 stroke 2.5. 모바일은 색만으로 active 표시. ⚠️ stroke 차이 미반영 사실 명시.
- **Inactive**: 색 `onSurfaceVariant` + (디자인) 얇은 stroke 1.8.
- **Pressed**: Material 기본 ripple (primary 계열 자동). 별도 색 없음.
- **Disabled**: 사용 안 함(4탭 모두 항상 enabled).

### 모바일 대응 (Compose Multiplatform 특이사항)

1. **`backdrop-blur-xl` 미지원**: 위 표 참조. 단순 alpha 95% 카드 색 + 1dp 상단 보더로 근사. ⚠️ 디자이너가 blur가 시각 핵심이라 판단하면 platform-specific actual 구현(Android `Modifier.blur`, iOS `UIVisualEffectView` interop) 검토 필요 — backlog 후보.
2. **lucide vs Material Icons 룩 차이**:
   - lucide: 모서리 둥근 24×24 그리드, stroke 기반(strokeWidth 1.8~2.5).
   - Material Icons Filled: 24×24 그리드, fill 기반(stroke 개념 없음).
   - 결과: lucide의 가벼운 stroke 룩과 Material filled의 굵은 fill 룩이 시각적으로 다름. 본 feature는 색 강조(primary)로 active를 분기하므로 stroke 굵기 차이는 시각상 큰 손실은 아님. ⚠️ 그러나 매니아 사용자에겐 차이가 보일 수 있어 §아이콘 매핑에서 결정 플래그.
3. **`Scaffold(bottomBar)` vs `Modifier.align(BottomCenter)`**: 본 프로젝트는 NavDisplay + Scaffold 패턴이 이미 `MainScreen.kt`에 존재 — Scaffold 슬롯 활용 권고. NavigationBar 컴포넌트가 인셋·표면 색을 기본으로 처리하나, 디자인 충실도(`backdrop-blur` 근사·라벨 10sp)를 위해 **NavigationBar 채택 ❌, 커스텀 Row 구현 ✅**.

---

## 아이콘 매핑 표 ⚠️ 핵심 결정 항목

Lovable lucide 4종 → Compose 후보 비교.

| Lovable lucide | 라벨 | 후보 A: Material Icons Extended (filled) | 후보 B: 커스텀 SVG (lucide 원본) | 후보 C: Material 빌트인 (`Icons.Default.*`) |
|---|---|---|---|---|
| `Home` | 홈 | `Icons.Filled.Home` | `home.svg` (24px, stroke 1.8/2.5 2종) | `Icons.Default.Home` ✅ |
| `Users` | 친구 | `Icons.Filled.Group` 또는 `Icons.Filled.People` | `users.svg` | ❌ 빌트인 없음 — A로 fallback |
| `Trophy` | 랭킹 | `Icons.Filled.EmojiEvents` | `trophy.svg` | ❌ 빌트인 없음 — A로 fallback |
| `User` | MY | `Icons.Filled.Person` | `user.svg` | `Icons.Default.Person` ✅ |

### 권고

⚠️ **옵션 A (Material Icons Extended)** 추천. 사유:
1. 모바일 레포 `:feature:login`이 이미 `materialIconsExtended`를 사용 중(`Icons.Filled.LocalFireDepartment` 등). 일관성 우선.
2. lucide 4개 SVG 번들도 비용 작지만, 색만 다른 active/inactive 처리 시 stroke 굵기 분기 SVG 2종 필요 → 자산 8개로 늘어남.
3. Material Icons filled는 stroke가 아닌 fill이라 lucide의 가벼운 라인 룩과 차이가 있으나, BottomBar는 22.dp 작은 크기 + 다크 배경 위라 차이 체감 적음.
4. `materialIconsExtended` deprecation은 별도 ADR 후보로 이미 등재(spec.md "사용자 결정 권한 §1") — 본 feature 범위에서 옵션 B로 전환할 만한 충분한 이유 없음.

**옵션 B 대안 권고 조건**: 디자이너가 lucide 라인 룩이 브랜드 정체성에 필수라고 판단할 경우. 이 경우 `:core:designsystem/src/commonMain/composeResources/drawable/`에 4개 SVG 번들 + active/inactive를 색으로만 분기(굵기 동일).

**최종 1차안**: 옵션 A로 mobile-dev 인계, 시각 검토 후 미세 조정.

---

## 컴포넌트 — Placeholder Screens (Friends / Ranking / MyPage)

- **참조**: 동명 route(`src/routes/{friends,ranking,mypage}.tsx`)는 본 feature 범위에선 **콘텐츠 미반영**(후속 feature에서 채움). 톤·헤더 패턴만 가늠.
- **의도**: BottomBar 라우팅 검증용 빈 컨테이너. 사용자가 탭 전환 시 "준비 중"을 명확히 인지하도록.
- **레이아웃** (3개 모두 동일 패턴):
  - 다크 배경(`background` = `#26272F`) 풀스크린.
  - 중앙 컬럼 정렬: 아이콘 1개(옵션) + 화면명 + "준비 중" 한 줄.
  - `WindowInsets.safeDrawing` 적용 — Top safe-area 포함.
- **토큰 매핑**:
  - 배경: `ChallengeTheme.colorScheme.background`
  - 화면명: `ChallengeTheme.typography.bold18` + `colorScheme.onBackground`
  - "준비 중" 보조: `ChallengeTheme.typography.medium14` + `colorScheme.onSurfaceVariant`
  - 아이콘 (옵션): `Icons.Outlined.HourglassEmpty` 또는 각 탭의 메인 아이콘 60% alpha — `onSurfaceVariant` 색 / 40~48.dp.

### 디테일 수준 옵션 (사용자 결정)

| 옵션 | 구성 | 권고 |
|---|---|---|
| **(가) 최소** | 화면명("친구"/"랭킹"/"MY") + "준비 중" 두 줄만 | ✅ 권고 — 후속 feature가 곧 채울 예정이라 디자인 비용 최소화 |
| (나) 아이콘 추가 | + 위 아이콘(각 탭 메인 아이콘 48.dp, `onSurfaceVariant`) | 시각적 완성도 ↑, 후속 feature와 충돌 없음 |
| (다) Empty illustration | + 일러스트(불꽃 모티프, 회색톤) | 자산 작성 비용 발생, 본 feature 범위 초과 |

**1차 권고**: (가). 사용자가 "조금 더 정돈된 느낌" 요구하면 (나)로 승격. (다)는 별도 feature.

### Placeholder 톤 통일

3개 화면 동일 컴포넌트 추상화 권고: `PlaceholderScreen(title: String, modifier: Modifier)` — `:core:designsystem`에 두면 후속 feature(`friends-register` 등) 진입 전에도 다른 곳에서 재사용 가능. 또는 각 `:feature:{friends,ranking,mypage}` 내부에 내용만 다른 동일 코드 3벌 — 가장 단순. mobile-dev 재량.

---

## 컴포넌트 매핑 표

| Lovable 소스 | Compose 제안 | 신규/기존 | 비고 |
|---|---|---|---|
| `<nav className="fixed bottom-0 ...">` (BottomNav 전체) | `ChallengeBottomBar` (기존 파일 갱신) | 기존 — `:feature:main/component/ChallengeBottomBar.kt` | 현재 `NavigationBar` 사용 중 → **커스텀 Row 기반으로 교체** (10.sp 라벨·alpha 카드 색 직접 제어) |
| `<Link>` 각 탭 | `Modifier.clickable + Modifier.padding` Row 항목 | 신규 인라인 | NavigationBarItem은 라벨 폰트 강제 + 패딩 강제라 부적합 |
| lucide 아이콘 4종 | `Icons.Filled.{Home, Group, EmojiEvents, Person}` | 기존 — `materialIconsExtended` 의존 (이미 `:feature:login`에 추가됨) | ⚠️ 옵션 A 채택 시. ⚠️ 결정 필요 |
| BottomBar 색·blur 근사 | `ChallengeTheme.colorScheme.surface.copy(alpha=0.95f)` + `HorizontalDivider` | — | `backdrop-blur` 미적용 (위 §모바일 대응) |
| Friends/Ranking/MyPage placeholder | `PlaceholderScreen` (신규) 또는 각 feature 내 ad-hoc | 신규 | `:core:designsystem` vs `:feature:*` 인라인 — mobile-dev 재량 |
| `Route.FriendsRoute.Main` 등 | `:core:navigation/Route.kt`에 3건 신설 + SerializersModule 등록 | 기존 파일 갱신 | spec.md T-M2 |

---

## BottomBar 토큰화 위치 — 권고

⚠️ 결정 필요 항목.

- **(A) `:feature:main` 인라인 유지** (현재 위치): `ChallengeBottomBar.kt` + `BottomNavItem.kt` 그대로 갱신.
  - 장점: 변경 범위 최소. main 모듈만 손대면 끝.
  - 단점: BottomBar가 다른 feature/화면에서 재사용될 일은 없으므로 손해 없음.
- **(B) `:core:designsystem`로 추출**: 일반화된 `BottomNavBar(items, selectedRoute, onSelect)` 컴포넌트.
  - 장점: 디자인시스템 일관성.
  - 단점: 본 feature는 4탭 고정·앱 단일 사용 — 추상화 비용 vs 재사용 기회 0에 가까움.

**권고**: **(A) 인라인 유지**. BottomNav는 앱 셸 전용이라 추출 이득 미미. `:feature:main`이 적정.

---

## ✅ pm-lead 결정 사항 (2026-05-11)

design-bridge 1차 권고 7건 전부 채택. mobile-dev는 본 표대로 구현.

| # | 항목 | 결정 | 비고 |
|---|---|---|---|
| 1 | **아이콘 출처** | **A: `materialIconsExtended` filled** (`Icons.Filled.Home/Group/EmojiEvents/Person`) | 22.dp 작은 크기 + 다크 배경에서 lucide stroke 룩 손실 미미. `:feature:login`에 이미 의존성 존재 |
| 2 | **"MY" 라벨** | **"MY" 유지** | 10.sp에서 가독성 우위 |
| 3 | **Placeholder 디테일** | **(가) 텍스트만** ("준비 중" + 화면명) | 후속 feature가 곧 채움 |
| 4 | **BottomBar 토큰화 위치** | **A: `:feature:main` 인라인 유지** | 재사용 0, 추상화 비용 절약 |
| 5 | **`backdrop-blur` 근사** | **(i) alpha 95%만** | KMP 공통 API 한계. platform actual blur는 백로그 등재 |
| 6 | **10.sp 라벨 처리** | **(i) inline `TextStyle`** | `medium10` 슬롯 신설은 백로그(다른 사용처 누적 시) |
| 7 | **Active stroke 굵기** | **(i) 색 분기만** (`primary` vs `onSurfaceVariant`) | Compose `Icon` strokeWidth 런타임 제어 불가 |

> **모바일과 Lovable 동기화 원칙(메모리 룰)에 따라**, 본 결정으로 Lovable `BottomNav.tsx` 변경은 발생하지 않음(이미 Lovable이 진실 소스이고, 모바일이 그를 따라가는 방향). Lovable에 stroke 굵기 2.5는 그대로 유지(Compose 한계로 모바일만 색 분기). 디자이너 검토 후 lucide 변환이 필요해지면 별도 ADR.

---

## mobile-dev 질의

본 feature 인계 시 다음을 강조:

1. **`NavigationBar`/`NavigationBarItem` 사용 ❌**: Material 컴포넌트는 라벨 폰트(`labelMedium`, 12.sp) 강제 + 좌우 패딩 강제(56.dp 최소 높이). 본 디자인의 10.sp 라벨·py-1.5 패딩·alpha 95% surface 색을 정확히 맞추려면 **`Row` 기반 커스텀 구현** 필요.
2. **현재 `ChallengeBottomBar.kt`의 `when (currentRoute)` 분기 전면 교체**: `Route.HomeRoute`/`FriendsRoute`/`RankingRoute`/`MyPageRoute` 4분기로. `Ex1Route`/`Ex2Route`/`Ex3Route` 분기 완전 제거(spec.md T-M2, T-M5와 정합).
3. **safe-area inset 처리**: `Modifier.windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom))`을 Bar 컨테이너에 적용. `Scaffold` 자체가 `contentWindowInsets`를 처리하더라도 customized Row 구현 시 명시적으로 한 번 더 확인 권장.
4. **아이콘 매핑 1차안은 옵션 A**: `Icons.Filled.{Home, Group, EmojiEvents, Person}`. import는 `androidx.compose.material.icons.filled.*`. `materialIconsExtended` 의존성이 `:feature:main`에 추가되어야 함(`:feature:login`에 이미 있음 — 컨벤션 플러그인이 자동 추가하는지 build.gradle.kts 확인).
5. **`PlaceholderScreen` 추상화 여부**: mobile-dev 재량. (가) 디테일 옵션을 적용한다면 코드 3벌이 동일해 추상화 가성비 ↑. (나)/(다)로 승격되면 더 명확해짐.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-05-08 | 최초 작성 — Lovable `BottomNav.tsx` 분석 + 4 placeholder 화면 톤 결정. spec.md "사용자 결정 권한" 4항목을 7건으로 구체화. 아이콘 매핑 1차안 옵션 A(`materialIconsExtended`) 권고. BottomBar 토큰화는 `:feature:main` 인라인 권고. | design-bridge |
