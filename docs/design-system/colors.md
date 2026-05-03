# Color Tokens — challenge 프로젝트 (맹세 / MAENGSE)

> 본 문서는 challenge 사이드 프로젝트(맹세 / MAENGSE)에서 **현재 실제로 사용 중인 모든 색상**을 단일 카탈로그로 정리한다. 이 문서가 컬러 토큰의 **single source of truth**이다.
> Lovable 디자인 레포(`challenge-design/oathbound-challenges`) 기준으로 모바일 `:core:designsystem`이 통합 완료 (2026-04-30).
>
> 정밀 토큰 카탈로그(라디우스/타이포 등)는 [tokens.md](./tokens.md) 참조.

- **마지막 갱신**: 2026-05-04
- **소스**:
  - Lovable 디자인 (참조 기준 / ADR-0004 A안): `challenge-design/oathbound-challenges/src/styles.css`
  - 모바일 (구현체): `challenge-app/core/designsystem/src/commonMain/kotlin/com/lwg/challenge/designsystem/theme/`
    - `Color.kt`, `Theme.kt`, `ChallengeColors.kt` (= `challengeDarkColorScheme()`), `BrandColors.kt`, `ChallengeExtendedColors.kt`, `ChallengeBrushes.kt`
  - 카카오 브랜드 가이드 (외부)
- **테마**: **Dark-first 단일 테마**로 통일. (라이트 테마는 보류 — 추후 ADR로 재논의)

---

## 0. 적용된 결정 (2026-04-30, Lovable 기준 통합 완료)

이전(2026-04-24) 본 문서가 5건 불일치를 도출했고, mobile-dev가 Lovable 토큰을 기준으로 `:core:designsystem`을 재구축하여 모두 해결되었다.

| # | 이전 불일치 | 적용된 결정 | 결과 |
|---|------------|-------------|------|
| 1 | 베이스 테마 톤 (Light vs Dark) | **Dark-first로 통일.** Lovable 다크 팔레트 채택. 라이트는 보류. | `Theme.kt`가 Material3 `darkColorScheme`만 정의. 이전 라이트 토큰(`ivory1/2`, `gray50`, `fontBlack`, `brown1/2`, `orange3`) 제거됨. |
| 2 | Primary 오렌지 값 (`#FF7033` vs `#E97A3D`) | **Lovable `#E97A3D` 채택.** | `Color.kt`의 `colorScheme.primary` = `#E97A3D`. |
| 3 | 카카오 hex 화면 코드 직접 박힘 | **`BrandColors` object로 토큰화.** | `BrandColors.KakaoYellow`, `BrandColors.KakaoYellowPressed`, `BrandColors.KakaoLabel` |
| 4 | success / warning / muted / accent / border / chart 누락 | **`ChallengeExtendedColors` 신설.** Material3에 없는 슬롯을 확장 컬러 데이터 클래스로 정의. | `LocalChallengeExtendedColors` CompositionLocal로 `ChallengeTheme` 내부에서 접근. |
| 5 | 그라데이션 방향/색 불일치 (수평 vs 135deg) | **`ChallengeBrushes.fire` (135deg, 오렌지 → 짙은 주홍) 채택.** 모바일 수평 그라데이션 폐기. | `ChallengeBrushes.kt`에 `fire` / `card` / `glow` 헬퍼. |

**빌드 검증**: Android / iOS / commonMain compile + LoginViewModelTest BUILD SUCCESSFUL.

---

## 1. 의미 단위 색상 (Semantic) — Material3 ColorScheme 슬롯

`ChallengeTheme` 내에서 `MaterialTheme.colorScheme.<slot>`으로 참조. 모든 값은 Lovable 다크 팔레트와 일치. **이 표가 컬러 결정의 source of truth.**

| Material3 슬롯 | Lovable 변수 | hex | 모바일 사용 위치 |
|---|---|---|---|
| `primary` / `primaryContainer` | `--primary` | `#E97A3D` | `Theme.kt` darkColorScheme.primary, `LoginScreen.kt` 스탬프/포인트 |
| `onPrimary` / `onPrimaryContainer` | `--primary-foreground` | `#1A1B22` | `Theme.kt` darkColorScheme.onPrimary |
| `secondary` / `secondaryContainer` | `--secondary` | `#3D3E48` | `Theme.kt` darkColorScheme.secondary |
| `onSecondary` / `onSecondaryContainer` | `--secondary-foreground` | `#D2D2D6` | `Theme.kt` darkColorScheme.onSecondary |
| `tertiary` / `tertiaryContainer` | `--accent` | `#43444F` | `Theme.kt` darkColorScheme.tertiary |
| `onTertiary` / `onTertiaryContainer` | `--accent-foreground` | `#F2F2F4` | `Theme.kt` darkColorScheme.onTertiary |
| `background` | `--background` | `#26272F` | `Theme.kt` darkColorScheme.background, `Scaffold.kt`, `LoginScreen.kt` 배경 |
| `onBackground` | `--foreground` | `#F2F2F4` | `Theme.kt` darkColorScheme.onBackground, 본문 텍스트 |
| `surface` | `--card` | `#2F303A` | `Theme.kt` darkColorScheme.surface, 카드 컴포넌트 |
| `onSurface` | `--card-foreground` | `#F2F2F4` | `Theme.kt` darkColorScheme.onSurface |
| `surfaceVariant` | `--muted` | `#383942` | `Theme.kt` darkColorScheme.surfaceVariant |
| `onSurfaceVariant` | `--muted-foreground` | `#9596A0` | `Theme.kt` darkColorScheme.onSurfaceVariant, 캡션/서브 |
| `outline` / `outlineVariant` | `--border` | `#43444E` | `Theme.kt` darkColorScheme.outline, 1px 구분선 |
| `error` / `errorContainer` | `--destructive` | `#D75C4A` | `Theme.kt` darkColorScheme.error |
| `onError` / `onErrorContainer` | `--destructive-foreground` | `#F2F2F4` | `Theme.kt` darkColorScheme.onError |

> 사용 규약: 화면 코드는 `MaterialTheme.colorScheme.<slot>`만 참조. 직접 hex 사용 금지(카카오 브랜드는 BrandColors 토큰 경유).

---

## 2. ChallengeExtendedColors — Material3 외 확장 토큰

Material3 `ColorScheme`에 success/warning/chart 등이 없어, 별도 데이터 클래스로 정의했다. `ChallengeTheme` 내에서 `LocalChallengeExtendedColors.current.<name>` 으로 접근.

### 2.1 Semantic 확장

| 항목 | hex | Lovable | 비고 |
|---|---|---|---|
| `success` | `#3CAB7A` | `--success` | 챌린지 성공/완료 표시 |
| `onSuccess` | `#1A1B22` | `--success-foreground` | success 위 전경 |
| `warning` | `#D7AF45` | `--warning` | 데드라인 임박 등 |
| `onWarning` | `#1A1B22` | `--warning-foreground` | warning 위 전경 |

### 2.2 중립 보조 (Material3 슬롯과 의도적으로 동일/중복 노출)

| 항목 | hex | Lovable | 비고 |
|---|---|---|---|
| `border` | `#43444E` | `--border` | `outline`과 동일값. 의미적 명시 위해 별도 노출. |
| `accent` | `#43444F` | `--accent` | `tertiary`와 동일. hover/상호작용 강조 의미로 사용. |
| `onAccent` | `#F2F2F4` | `--accent-foreground` | |
| `muted` | `#383942` | `--muted` | `surfaceVariant`와 동일값. 의미적 별칭. |
| `onMuted` | `#9596A0` | `--muted-foreground` | |

### 2.3 Chart 5색 (랭킹/통계)

| 항목 | hex | Lovable | 비고 |
|---|---|---|---|
| `chart1` | `#E97A3D` | `--chart-1` | primary와 동일 |
| `chart2` | `#3CAB7A` | `--chart-2` | success와 동일 |
| `chart3` | `#D75C4A` | `--chart-3` | destructive와 동일 |
| `chart4` | `#5E91C9` | `--chart-4` | 시안 계열 |
| `chart5` | `#D7AF45` | `--chart-5` | warning과 동일 |

### 2.4 그라데이션 / 글로우 컬러 stops

`ChallengeBrushes` 정의를 위해 stop들을 토큰화. Compose에서 직접 색상으로도 접근 가능.

| 항목 | hex | Lovable | 비고 |
|---|---|---|---|
| `gradientPrimaryStart` | `#E97A3D` | `--gradient-fire` start (`oklch(0.72 0.19 45)`) | primary와 동일 |
| `gradientPrimaryEnd` | `#D75C3A` | `--gradient-fire` end (`oklch(0.65 0.22 30)`) | ⚠️ 변환 추정 — 디자이너 확인 |
| `gradientCardStart` | `#31323D` | `--gradient-card` start (`oklch(0.25 0.02 270)`) | ⚠️ 추정값 |
| `gradientCardEnd` | `#2B2C36` | `--gradient-card` end (`oklch(0.22 0.015 270)`) | ⚠️ 추정값 |
| `glowPrimary` | primary 15% alpha | `--gradient-glow` center (`oklch(0.72 0.19 45 / 15%)`) | radial 글로우 중심색 |

---

## 3. ChallengeBrushes — Compose Brush 헬퍼

그라데이션을 Compose `Brush`로 사전 계산해 둔 헬퍼. `LocalChallengeBrushes.current.<name>` 으로 접근.

| 토큰 | 정의 | 용도 / 사용 위치 |
|---|---|---|
| `brushes.fire` | `Brush.linearGradient(135deg, gradientPrimaryStart → gradientPrimaryEnd)` | 메인 CTA 배경, 로고 스탬프, 타이틀 텍스트 하이라이트 (`LoginScreen.kt`, `SplashScreen.kt`) |
| `brushes.card` | `Brush.linearGradient(135deg, gradientCardStart → gradientCardEnd)` | 카드 표면 미묘한 depth |
| `brushes.glow` | `Brush.radialGradient(glowPrimary → transparent)` | 화면 상단 후광 (Login/Home) — Compose 기본 radialGradient로 근사 |

> 모바일에서 이전에 사용하던 `gradientColor` (수평 `#FF7033` → `#F49D25`)는 폐기됨.

---

## 4. BrandColors — 외부 브랜드 (Kakao)

이전에는 화면 코드에 hex가 직접 박혀 있었으나, **`BrandColors` object로 토큰화 완료.**

| 토큰 | hex | 출처 | 사용 위치 |
|---|---|---|---|
| `BrandColors.KakaoYellow` | `#FEE500` | 카카오 공식 가이드 | `LoginScreen.kt` 카카오 로그인 버튼 containerColor |
| `BrandColors.KakaoYellowPressed` | `#FDD835` | Lovable hover 값 (비공식) | 모바일 ripple 색 또는 pressed state |
| `BrandColors.KakaoLabel` | `#191919` | 카카오 공식 가이드 | 옐로우 위 텍스트/아이콘 색 (검정) |

사용 예시:
```kotlin
Button(colors = ButtonDefaults.buttonColors(containerColor = BrandColors.KakaoYellow))
```

> Material3 `ColorScheme`에 들어가는 토큰이 아니라 `:core:designsystem`의 별도 `object BrandColors`. 외부 브랜드는 테마와 분리하여 명시적으로 hex 고정값 유지.

---

## 5. ⚠️ 디자이너 시각 검증 필요

mobile-dev 통합 작업 중 **변환/근사**가 필요했던 5건. 모두 코드는 적용되었으나 디자이너 시각 검토 후 미세 조정 가능.

| # | 항목 | 적용된 값 | 사유 |
|---|---|---|---|
| 1 | `gradientPrimaryEnd` | `#D75C3A` | Lovable `oklch(0.65 0.22 30)` 자체 변환 추정값. 디자이너 시각 확인 필요. |
| 2 | `gradientCardStart` | `#31323D` | Lovable `oklch(0.25 0.02 270)` 추정값. |
| 2 | `gradientCardEnd` | `#2B2C36` | Lovable `oklch(0.22 0.015 270)` 추정값. |
| 3 | `chart4` | `#5E91C9` | Lovable `oklch(0.70 0.15 250)` 변환값 — 본 문서 값 그대로 사용. 사용처(랭킹) 확정 시 디자이너 재확인. |
| 4 | Glow brush 재현도 | Compose `Brush.radialGradient` 기본값 근사 | Lovable `radial-gradient(circle at 50% 0%, ...)` 정확 재현은 size 계산 + 명시적 center/radius 필요. 현재는 기본값으로 근사. |
| 5 | 135deg 그라데이션 방향 | Compose `Brush.linearGradient(start = (0,0), end = (size.x, size.y))` | 정사각 영역에서만 정확히 135deg. 직사각(가로/세로 비율 큰 화면)에서는 각도 어긋남 가능. |

→ pm-lead가 디자이너에게 위 5건을 묶어 검토 요청. 결과에 따라 `Color.kt` / `ChallengeBrushes.kt` 미세 조정.

---

## 6. 작업 가이드

### 6.1 새 색상 추가 시

1. Material3 슬롯으로 매핑 가능한가? → `Color.kt` + `Theme.kt` darkColorScheme에 정의. 1장 표에 행 추가.
2. Material3에 없는 의미(success/warning/chart 등)인가? → `ChallengeExtendedColors.kt`에 추가. 2장 표에 행 추가.
3. 외부 브랜드인가? → `BrandColors.kt` object에 추가. 4장 표에 행 추가.
4. Lovable에 같은 의미가 있다면 `--<변수명>` 컬럼 채워 일치 확인.

### 6.2 화면 코드 작성 시

- ❌ `Color(0xFF...)` 직접 사용 금지
- ✅ `MaterialTheme.colorScheme.<slot>` 우선
- ✅ 확장 색은 `LocalChallengeExtendedColors.current.<name>`
- ✅ 카카오 브랜드는 `BrandColors.<name>`
- ✅ 그라데이션은 `LocalChallengeBrushes.current.<name>`

### 6.3 새 화면이 라이트 테마를 요구할 경우

현재는 dark-first 단일 테마. 라이트 추가가 필요하면 ADR 작성 후 `Theme.kt`에 lightColorScheme 정의 + `ChallengeExtendedColors`도 light variant 추가.

---

## 7. 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-04-24 | 최초 작성 — Lovable styles.css 전체, 모바일 `:core:designsystem` Color.kt + 사용처 grep 결과 통합. 5.1~5.7 일관성 점검 5건 도출. | design-bridge |
| 2026-04-24 | mobile-dev의 Lovable 기준 통합 작업 반영. 5건 불일치 모두 해결: dark-first 통일, primary `#E97A3D` 채택, `BrandColors`/`ChallengeExtendedColors`/`ChallengeBrushes` 신설. Material3 darkColorScheme 매핑 표가 source of truth. ⚠️ 디자이너 시각 검증 필요 5건은 5장에 보존. | design-bridge |
| 2026-05-04 | 모바일 `:core:designsystem` 실제 코드를 1~4장 카탈로그와 일치시킴 (이전엔 옛 라이트 팔레트 코드가 잔존). `ChallengeColors` data class + `LocalChallengeColors` CompositionLocal 제거, Material3 `darkColorScheme()` 직접 노출 (`challengeDarkColorScheme()`). `ChallengeExtendedColors.kt` 신설, `ChallengeTheme.extendedColors` 접근자 추가. `ChallengeBrushes`는 fire/card/glow 3종으로 확장. 호출부(Button/Label/Scaffold/HomeRoute/HomeTopBar/SplashScreen/LoginScreen) 옛 토큰 제거. 모바일 자체 `design-system` SKILL.md 가이드도 갱신. 빌드: commonMain metadata / Android designsystem / Android composeApp 3건 BUILD SUCCESSFUL. | mobile-dev |
