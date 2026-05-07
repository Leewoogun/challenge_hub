# Color Tokens — challenge 프로젝트 (맹세 / MAENGSE)

> 본 문서는 challenge 사이드 프로젝트(맹세 / MAENGSE)에서 **현재 실제로 사용 중인 모든 색상**을 단일 카탈로그로 정리한다. 이 문서가 컬러 토큰의 **single source of truth**이다.
> Lovable 디자인 레포(`challenge-design/oathbound-challenges`)를 기준으로 모바일 `:core:designsystem`이 통합·유지된다.
>
> 정밀 토큰 카탈로그(라디우스/타이포 등)는 [tokens.md](./tokens.md) 참조.

- **마지막 갱신**: 2026-05-04
- **소스**:
  - Lovable 디자인 (참조 기준 / ADR-0004 A안): `challenge-design/oathbound-challenges/src/styles.css`
  - 모바일 (구현체): `challenge-app/core/designsystem/src/commonMain/kotlin/com/lwg/challenge/designsystem/theme/`
    - `Color.kt` (raw 토큰), `ChallengeColorScheme.kt` (시멘틱 단일 진입점), `Theme.kt`, `ChallengeBrushes.kt`, `BrandColors.kt`
  - 카카오 브랜드 가이드 (외부)
- **테마**: **Dark-first 단일 테마**로 통일. 라이트 테마 미지원 (추후 ADR로 재논의).

---

## 0. 결정 이력

### 0.1 (2026-04-30) Lovable 기준 통합 — 1차

이전(2026-04-24) 모바일 라이트 팔레트 잔존 vs Lovable 다크 팔레트 갭 5건 도출 → mobile-dev 통합 작업 적용.

| # | 이전 불일치 | 적용된 결정 |
|---|------------|-------------|
| 1 | 베이스 테마 톤 (Light vs Dark) | Dark-first로 통일. Lovable 다크 팔레트 채택. |
| 2 | Primary 오렌지 (`#FF7033` vs `#E97A3D`) | Lovable `#E97A3D` 채택. |
| 3 | 카카오 hex 직접 박힘 | `BrandColors` object로 토큰화. |
| 4 | success/warning/muted/accent/border/chart 누락 | 신설. |
| 5 | 그라데이션 방향/색 불일치 | 135deg, 오렌지→짙은 주홍 채택. |

### 0.2 (2026-05-04) ColorScheme 단일화 — 2차

1차 통합 시점에 도입했던 `ChallengeExtendedColors` 분리 구조를 폐지하고 **모든 시멘틱 색상을 `ChallengeColorScheme` 한 데이터 클래스에 통합**. 접근 경로도 단일화.

| 항목 | 결정 |
|---|---|
| 시멘틱 색 진입점 | `ChallengeTheme.colorScheme.<name>` **단일**. Material3 `MaterialTheme.colorScheme.X` 직접 호출 **금지** (내부 호환용으로만 생성). |
| `ChallengeExtendedColors` 데이터 클래스 | 폐지. success/warning/border/accent/muted/chart/gradient stops 모두 `ChallengeColorScheme` 슬롯으로 흡수. |
| Raw 토큰 명명 | 의미(primary/background)가 아닌 **색 자체**를 가리키는 이름으로 정리: `orange1`, `black2`, `gray3` 등. 시멘틱 매핑은 `DefaultChallengeColorScheme`에서 단일로 정의. |
| Material3 호환 | `ChallengeColorScheme.toMaterialColorScheme()` 내부 변환으로 `darkColorScheme()` 생성 → Surface/Scaffold/AlertDialog 등 머터리얼 컴포넌트가 동일 색을 자동 사용. Feature 코드는 이걸 **읽지 않는다**. |

**빌드 검증**: commonMain metadata / Android designsystem / Android composeApp 3건 BUILD SUCCESSFUL.

---

## 1. ChallengeColorScheme — 단일 시멘틱 진입점

`ChallengeTheme.colorScheme.<name>` 으로만 접근. **이 표가 컬러 결정의 source of truth.**

### 1.1 CTA / 강조

| 슬롯 | hex | raw 토큰 | Lovable 변수 | 사용 가이드 |
|---|---|---|---|---|
| `primary` | `#E97A3D` | `orange1` | `--primary` | 메인 CTA, 포인트, 스탬프 |
| `onPrimary` | `#1A1B22` | `black1` | `--primary-foreground` | primary 위 전경 |

### 1.2 배경 / 표면

| 슬롯 | hex | raw 토큰 | Lovable 변수 | 사용 가이드 |
|---|---|---|---|---|
| `background` | `#26272F` | `black2` | `--background` | 화면 베이스 |
| `onBackground` | `#F2F2F4` | `white1` | `--foreground` | 본문 텍스트 |
| `surface` | `#2F303A` | `black3` | `--card` | 카드 / 다이얼로그 |
| `onSurface` | `#F2F2F4` | `white1` | `--card-foreground` | surface 위 텍스트 |
| `surfaceVariant` | `#383942` | `gray4` | `--muted` | 비활성 / 보조 표면 |
| `onSurfaceVariant` | `#9596A0` | `gray5` | `--muted-foreground` | 캡션 / 서브 텍스트 |

### 1.3 보조 톤

| 슬롯 | hex | raw 토큰 | Lovable 변수 | 사용 가이드 |
|---|---|---|---|---|
| `secondary` | `#3D3E48` | `gray1` | `--secondary` | 다크 보조 톤 |
| `onSecondary` | `#D2D2D6` | `gray6` | `--secondary-foreground` | secondary 위 전경 |
| `tertiary` | `#43444F` | `gray2` | `--accent` | hover/상호작용 강조 |
| `onTertiary` | `#F2F2F4` | `white1` | `--accent-foreground` | tertiary 위 전경 |

### 1.4 보더 / 구분선

| 슬롯 | hex | raw 토큰 | Lovable 변수 | 사용 가이드 |
|---|---|---|---|---|
| `outline` | `#43444E` | `gray3` | `--border` | 1px 구분선 / Material3 outline |
| `border` | `#43444E` | `gray3` | `--border` | 의미적 별칭 (실제 Material3 outline과 동일값) |

### 1.5 상태 색

| 슬롯 | hex | raw 토큰 | Lovable 변수 | 사용 가이드 |
|---|---|---|---|---|
| `error` | `#D75C4A` | `red1` | `--destructive` | 에러 상태 |
| `onError` | `#F2F2F4` | `white1` | `--destructive-foreground` | error 위 전경 |
| `success` | `#3CAB7A` | `green1` | `--success` | 챌린지 성공 / 완료 |
| `onSuccess` | `#1A1B22` | `black1` | `--success-foreground` | success 위 전경 |
| `warning` | `#D7AF45` | `yellow1` | `--warning` | 데드라인 임박 등 |
| `onWarning` | `#1A1B22` | `black1` | `--warning-foreground` | warning 위 전경 |

### 1.6 차트 (랭킹 / 통계)

| 슬롯 | hex | raw 토큰 | Lovable 변수 | 비고 |
|---|---|---|---|---|
| `chart1` | `#E97A3D` | `orange1` | `--chart-1` | primary와 동일 |
| `chart2` | `#3CAB7A` | `green1` | `--chart-2` | success와 동일 |
| `chart3` | `#D75C4A` | `red1` | `--chart-3` | error와 동일 |
| `chart4` | `#5E91C9` | `blue1` | `--chart-4` | 시안 계열 |
| `chart5` | `#D7AF45` | `yellow1` | `--chart-5` | warning과 동일 |

### 1.7 그라데이션 stops & 글로우

`ChallengeBrushes` 헬퍼의 재료. 직접 컬러로도 접근 가능.

| 슬롯 | hex | raw 토큰 | Lovable 변수 | 비고 |
|---|---|---|---|---|
| `gradientPrimaryStart` | `#E97A3D` | `orange1` | `--gradient-fire` start | primary와 동일 |
| `gradientPrimaryEnd` | `#D75C3A` | `orange2` | `--gradient-fire` end | ⚠️ oklch→hex 변환 추정 |
| `gradientCardStart` | `#31323D` | `black4` | `--gradient-card` start | ⚠️ 추정값 |
| `gradientCardEnd` | `#2B2C36` | `black5` | `--gradient-card` end | ⚠️ 추정값 |
| `glowPrimary` | primary 15% alpha | `orange1.copy(alpha=0.15f)` | `--gradient-glow` 중심 | radial 글로우 중심색 |

> 사용 규약: 화면 코드는 `ChallengeTheme.colorScheme.<slot>` 만 참조. 직접 hex 사용 금지(카카오 브랜드는 `BrandColors` 토큰 경유). `MaterialTheme.colorScheme.X` 도 사용 금지.

---

## 2. Raw 토큰 카탈로그 (`Color.kt`)

화면/시멘틱 슬롯에서 직접 사용하지 **않는다**. 1장 표의 매핑 출처일 뿐.

| raw 토큰 | hex | 어느 슬롯에 매핑되나 |
|---|---|---|
| `orange1` | `#E97A3D` | primary, chart1, gradientPrimaryStart |
| `orange2` | `#D75C3A` | gradientPrimaryEnd |
| `red1` | `#D75C4A` | error, chart3 |
| `yellow1` | `#D7AF45` | warning, chart5 |
| `green1` | `#3CAB7A` | success, chart2 |
| `blue1` | `#5E91C9` | chart4 |
| `black1` | `#1A1B22` | onPrimary, onSuccess, onWarning |
| `black2` | `#26272F` | background |
| `black3` | `#2F303A` | surface |
| `black4` | `#31323D` | gradientCardStart |
| `black5` | `#2B2C36` | gradientCardEnd |
| `gray1` | `#3D3E48` | secondary |
| `gray2` | `#43444F` | tertiary |
| `gray3` | `#43444E` | outline, border |
| `gray4` | `#383942` | surfaceVariant |
| `gray5` | `#9596A0` | onSurfaceVariant |
| `gray6` | `#D2D2D6` | onSecondary |
| `white1` | `#F2F2F4` | onBackground, onSurface, onTertiary, onError |

---

## 3. ChallengeBrushes — Compose Brush 헬퍼

`ChallengeTheme.brushes.<name>` 으로 접근.

| 토큰 | 정의 | 용도 / 사용 위치 |
|---|---|---|
| `brushes.fire` | `linearGradient(135deg, gradientPrimaryStart → gradientPrimaryEnd)` | 메인 CTA 배경, 로고 스탬프, 타이틀 텍스트 하이라이트 (`LoginScreen.kt`, `SplashScreen.kt`) |
| `brushes.card` | `linearGradient(135deg, gradientCardStart → gradientCardEnd)` | 카드 표면 미묘한 depth |
| `brushes.glow` | `radialGradient(glowPrimary → transparent)` | 화면 상단 후광 (Login/Home) — Compose 기본값 근사 |

---

## 4. BrandColors — 외부 브랜드 (Kakao)

`BrandColors` object — Material3 ColorScheme/`ChallengeColorScheme` 외부의 별도 고정값. 테마와 분리.

| 토큰 | hex | 출처 | 사용 위치 |
|---|---|---|---|
| `BrandColors.KakaoYellow` | `#FEE500` | 카카오 공식 가이드 | `LoginScreen.kt` 카카오 로그인 버튼 containerColor |
| `BrandColors.KakaoYellowPressed` | `#FDD835` | Lovable hover (비공식) | 모바일 ripple 색 또는 pressed state |
| `BrandColors.KakaoLabel` | `#191919` | 카카오 공식 가이드 | 옐로우 위 텍스트/아이콘 색 |

```kotlin
Button(colors = ButtonDefaults.buttonColors(containerColor = BrandColors.KakaoYellow))
```

---

## 5. ⚠️ 디자이너 시각 검증 필요

mobile-dev 통합 작업 중 **변환/근사**가 필요했던 케이스. 코드 적용은 완료, 디자이너 시각 검토 후 미세 조정 가능.

| # | 항목 | 적용된 값 | 사유 |
|---|---|---|---|
| 1 | `gradientPrimaryEnd` (`orange2`) | `#D75C3A` | Lovable `oklch(0.65 0.22 30)` → hex 변환 추정 |
| 2 | `gradientCardStart` (`black4`) | `#31323D` | Lovable `oklch(0.25 0.02 270)` 추정 |
| 3 | `gradientCardEnd` (`black5`) | `#2B2C36` | Lovable `oklch(0.22 0.015 270)` 추정 |
| 4 | `chart4` (`blue1`) | `#5E91C9` | Lovable `oklch(0.70 0.15 250)` 변환 |
| 5 | Glow brush 재현도 | Compose `Brush.radialGradient` 기본값 근사 | Lovable `radial-gradient(circle at 50% 0%, ..., transparent 60%)`을 명시적 center/radius 없이 근사 |
| 6 | 135deg linearGradient 방향 | `start = Offset.Zero`, `end = Offset.Infinite` | 정사각 영역에서만 정확히 135deg. 직사각 화면에선 각도 어긋남 가능 |

→ pm-lead가 디자이너에게 묶어 검토 요청. 결과에 따라 raw 토큰 hex 또는 brush 정의 미세 조정.

---

## 6. 작업 가이드

### 6.1 새 색상 추가 시

1. 시멘틱 의미가 1장 표의 어느 슬롯에 들어가는지 결정.
   - 기존 슬롯에 들어가면 hex만 정해 매핑 추가 — 슬롯 자체를 늘리지 말 것.
   - 새 의미가 필요하면 `ChallengeColorScheme` 슬롯 신설 + `Color.kt`에 raw 토큰 추가 + `DefaultChallengeColorScheme` 매핑 + 본 문서 1·2장 갱신.
2. Lovable에 같은 의미 변수가 있다면 `--<변수명>` 컬럼 채워 일치 확인.
3. 외부 브랜드는 `BrandColors` object에 추가 (테마와 분리).

### 6.2 화면 코드 작성 시

- ❌ `Color(0xFF...)` 직접 사용 금지
- ❌ `MaterialTheme.colorScheme.X` 직접 사용 금지 (내부 호환용)
- ✅ 시멘틱 색 → `ChallengeTheme.colorScheme.<slot>`
- ✅ 카카오 브랜드 → `BrandColors.<name>`
- ✅ 그라데이션 → `ChallengeTheme.brushes.<name>`

### 6.3 라이트 테마 요구 시

현재는 dark-first 단일 테마. 라이트가 필요하면 ADR 작성 후 `ChallengeColorScheme`의 라이트 variant 추가 + `Theme.kt`에서 시스템 모드에 따라 분기.

---

## 7. 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-04-24 | 최초 작성 — Lovable styles.css 전체, 모바일 `:core:designsystem` Color.kt + 사용처 grep 결과 통합. 5건 불일치 도출. | design-bridge |
| 2026-04-30 | 1차 통합. dark-first 통일, primary `#E97A3D` 채택, `BrandColors`/`ChallengeExtendedColors`/`ChallengeBrushes` 신설. ⚠️ 검증 필요 5건 5장에 보존. | design-bridge |
| 2026-05-04 | 모바일 `:core:designsystem` 실제 코드 갭 정리 (옛 라이트 팔레트 잔존분 제거) + 같은 날 ColorScheme 단일화 2차 리팩터. `ChallengeExtendedColors` 폐지 → `ChallengeColorScheme` 단일 데이터 클래스로 통합. raw 토큰 명명을 색 자체 기반(`orange1`/`black2`/`gray3`)으로 정리. 시멘틱 진입점 `ChallengeTheme.colorScheme.<name>` **단일**. 호출부(Button/Label/Scaffold/HomeRoute/HomeTopBar/SplashScreen/LoginScreen) 정리. | mobile-dev + design-bridge |
