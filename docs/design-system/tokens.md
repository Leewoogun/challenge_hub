# Design Tokens — 맹세(MAENGSE)

- **소스**: `challenge-design/oathbound-challenges/src/styles.css` (Tailwind v4 `@theme inline` + CSS 변수) + 모바일 `:core:designsystem`
- **최종 스냅샷**: 2026-05-04
- **테마**: Dark-first 단일 테마 (라이트 보류 — 추후 ADR로 재논의)
- **목적**: Compose Multiplatform의 `:core:designsystem` 모듈이 동기화해야 할 의미 단위 토큰 카탈로그. 각 feature의 `design.md`는 값을 복붙하지 말고 이 문서를 링크로 참조.

---

## 1. 색상 (Colors)

> **컬러 토큰의 single source of truth는 [colors.md](./colors.md).** 본 섹션은 요약 + 링크.

- **`ChallengeColorScheme` 단일 진입점** (primary/background/surface/error/success/warning/chart 1~5/gradient stops 등 시멘틱 28슬롯) → [colors.md §1](./colors.md#1-challengecolorscheme--단일-시멘틱-진입점)
- **Raw 토큰 카탈로그** (orange1/black2/gray3 등 색 자체 기반 명명) → [colors.md §2](./colors.md#2-raw-토큰-카탈로그-colorkt)
- **ChallengeBrushes** (`fire` / `card` / `glow` Brush 헬퍼) → [colors.md §3](./colors.md#3-challengebrushes--compose-brush-헬퍼)
- **BrandColors** (Kakao 토큰화 완료) → [colors.md §4](./colors.md#4-brandcolors--외부-브랜드-kakao)
- **디자이너 시각 검증 필요 6건** → [colors.md §5](./colors.md#5-️-디자이너-시각-검증-필요)

2026-05-04 적용 결정 요약: ColorScheme 단일화. `ChallengeExtendedColors` 폐지 → `ChallengeColorScheme` 한 데이터 클래스로 통합. 접근은 `ChallengeTheme.colorScheme.<name>` **단일** (Material3 `MaterialTheme.colorScheme.X` 직접 호출 금지). 자세한 내용은 colors.md §0 참조.

---

## 2. 그라데이션 (Gradients)

| 의미 토큰 | CSS 변수 | 정의 | 용도 |
|---------|---------|------|------|
| Fire | `--gradient-fire` | `linear-gradient(135deg, oklch(0.72 0.19 45), oklch(0.65 0.22 30))` | 기본 버튼 배경, 로고 스탬프, 타이틀 텍스트 하이라이트 |
| Card | `--gradient-card` | `linear-gradient(135deg, oklch(0.25 0.02 270), oklch(0.22 0.015 270))` | 카드 배경(미묘한 depth) |
| Glow | `--gradient-glow` | `radial-gradient(circle at 50% 0%, oklch(0.72 0.19 45 / 15%), transparent 60%)` | 화면 상단 후광 (로그인/홈) |

Compose 매핑: `ChallengeTheme.brushes.fire / .card / .glow` 헬퍼로 고정.

---

## 3. 그림자 (Shadows)

| 의미 토큰 | CSS 변수 | 정의 | Compose 매핑 |
|---------|---------|------|-------------|
| Card | `--shadow-card` | `0 4px 24px oklch(0 0 0 / 30%)` | `Modifier.shadow(4.dp, ...)` + ambient 30% |
| Glow | `--shadow-glow` | `0 0 30px oklch(0.72 0.19 45 / 20%)` | Compose 기본 shadow로 표현 어려움 — Canvas로 blur glow 그리거나 생략. ⚠️ 모바일 성능 고려. |

---

## 4. Radius

| 의미 토큰 | CSS 변수 | 값 | Compose dp |
|---------|---------|-----|-----------|
| base | `--radius` | `0.75rem` (12px) | 12.dp |
| sm | `--radius-sm` | `calc(base - 4px)` (8px) | 8.dp |
| md | `--radius-md` | `calc(base - 2px)` (10px) | 10.dp |
| lg | `--radius-lg` | `base` (12px) | 12.dp |
| xl | `--radius-xl` | `calc(base + 4px)` (16px) | 16.dp |
| 2xl | `--radius-2xl` | `calc(base + 8px)` (20px) | 20.dp |
| 3xl | `--radius-3xl` | `calc(base + 12px)` (24px) | 24.dp |
| 4xl | `--radius-4xl` | `calc(base + 16px)` (28px) | 28.dp |
| full | — | `9999px` (Tailwind `rounded-full`) | `CircleShape` |

Compose 매핑 제안: `:core:designsystem`에 `ChallengeShapes(small=8.dp, medium=12.dp, large=16.dp, extraLarge=24.dp)` → Material 3 `Shapes` 슬롯. (현재 미적용 — 도입 결정 필요)

---

## 5. 타이포그래피 (Typography)

> **2026-05-04 통합 완료.** 모바일 `Typography.kt`의 `ChallengeTypoGraphy`는 Lovable에서 실사용된 사이즈 스케일을 그대로 반영한다 (text-xs/sm/base/lg/xl/2xl/3xl/5xl). 접근은 `ChallengeTheme.typography.<slot>`.

### 5.1 폰트 패밀리

| 출처 | 디자인 (Lovable) | 모바일 실제 |
|---|---|---|
| 패밀리 | Pretendard, system-ui, -apple-system, sans-serif (`--font-family-display`) | **GmarketSansTTF** (Light/Medium/Bold 3종 자산) |
| 자산 위치 | (웹 CSS 변수) | `core/designsystem/src/commonMain/composeResources/font/` |
| 라이선스 | Pretendard 무료 상업 사용 가능 | GmarketSans 무료 상업 사용 가능 |

> ⚠️ **폰트 패밀리 자체는 디자인(Pretendard) ↔ 모바일(GmarketSans) 불일치.** 사용자 요청 시 size/lineHeight/fontWeight만 정합 — 패밀리 교체는 별도 결정. ADR 후보.

### 5.2 사이즈 / lineHeight 매핑 (Lovable Tailwind 기본 → 모바일 슬롯)

| Lovable 클래스 | px | lineHeight | 모바일 슬롯 (light/medium/bold) | 비고 |
|---|---|---|---|---|
| `text-xs` | 12 | 16 | `light12` / `medium12` / `bold12` | Tailwind 기본 |
| `text-sm` | 14 | 20 | `light14` / `medium14` / `bold14` | Tailwind 기본. 이전 22 → 20 정합 |
| `text-base` | 16 | 24 | `light16` / `medium16` / `bold16` | Tailwind 기본 |
| `text-lg` | 18 | 28 | `light18` / `medium18` / `bold18` | Tailwind 기본. 이전 26 → 28 정합 |
| `text-xl` | 20 | 28 | `light20` / `medium20` / `bold20` | Tailwind 기본 |
| (디자인 미사용) | 22 | 30 | `light22` / `medium22` / `bold22` | ⚠️ 디자인엔 없는 슬롯. 호출부 보호 위해 유지, 점진적 제거 후보 |
| `text-2xl` | 24 | 32 | `light24` / `medium24` / `bold24` | Tailwind 기본 |
| `text-3xl` | 30 | 36 | `light30` / `medium30` / `bold30` | Tailwind 기본 |
| `text-5xl` | 48 | 48 | `bold48` | Lovable `leading-none` 의도 반영 (size=lineHeight) |

### 5.3 fontWeight 매핑 정책

GmarketSans 자산이 Light(300) / Medium(500) / Bold(700) 3종뿐이라 디자인의 6단계 weight를 다음과 같이 매핑한다. 폰트 자산 추가는 별도 결정.

| Lovable 클래스 | 무게 | 모바일 사용 슬롯 | 사유 |
|---|---|---|---|
| `font-light` | 300 | Light | — |
| `font-normal` | 400 | Light | Regular 자산 부재 → Light 근사 |
| `font-medium` | 500 | Medium | — |
| `font-semibold` | 600 | Medium | Semi 자산 부재 → Bold보다 Medium이 시각적 무게차 작음 (디자인 의도 보존) |
| `font-bold` | 700 | Bold | — |
| `font-extrabold` | 800 | Bold | Heavy 자산 부재 → Bold가 최대치 |
| `font-black` | 900 | Bold | 동상 |

### 5.4 사용 가이드

```kotlin
Text(
    text = "...",
    style = ChallengeTheme.typography.medium16,
    color = ChallengeTheme.colorScheme.onBackground,
)
```

- 폰트 스케일 적용 무관하게 표시되어야 하는 텍스트는 `style.nonScaledSp` 확장 사용.
- `lineHeightStyle` (Center alignment + Trim None)이 모든 슬롯에 공통 적용.

---

## 6. 스페이싱 / 레이아웃

| 토큰 | 값 | 용도 |
|------|-----|------|
| App container max-width | `430px` | 모바일 최대 폭 (Lovable 웹에서 모바일 프리뷰용). 네이티브 모바일은 무시, 화면 꽉 채움. |
| 기본 수평 패딩 | `px-6` (24px) | 화면 좌우 gutter |
| 기본 수직 리듬 | `gap-8` (32px) / `gap-3` (12px) | 섹션 간격 / 컴포넌트 간격 |

Compose 매핑 제안: `ChallengeSpacing(xs=4, sm=8, md=12, lg=16, xl=24, xxl=32)` 정의 후 사용. (현재 미적용 — 도입 결정 필요)

---

## 7. 애니메이션 (참고)

`@keyframes`로 정의된 인터랙션. 모바일에서는 선택 구현.

| 이름 | duration / timing | 용도 | Compose 이식 난이도 |
|------|-------------------|------|-------------------|
| `slide-up` | 0.4s ease-out | 화면 진입 시 하위 요소 20px 위로 슬라이드 + opacity | 쉬움 (`AnimatedVisibility` + `slideInVertically`) |
| `pulse-fire` | 2s ease-in-out infinite | 로고 스탬프의 불꽃 발광 | 중간 (shadow는 `InfiniteTransition` + Canvas) |
| `spin-slow` | 20s linear infinite | 로고 외곽 링 회전 | 쉬움 (`rotate`) |
| `wiggle` | 1.5s ease-in-out infinite | 🔥 이모지 흔들림 | 쉬움 |
| `float-slow/medium/fast` | 3~6s infinite | 배경 불꽃 입자 부유 | 중간 — 성능 주의, 5개 이상이면 60fps 보장 어려움. ⚠️ 저사양 단말에서 생략 옵션 권장. |
| `pulse` (tailwind 기본) | 2s | 뱃지 점 깜빡임 | 내장 사용 |

---

## 8. ⚠️ 확인 필요 / 디자이너 협의 항목

1. **라이트 테마**: styles.css에 dark 값만 존재하고 `@custom-variant dark (&:is(.dark *))` 정의만 있음. 라이트는 제공 안 하는 것이 확정인가? (ADR 필요 수준)
2. **Kakao hover 값 `#FDD835`**: 카카오 공식 가이드에는 hover 스펙이 없음. 모바일에서는 ripple로 대체할지, pressed 색을 맞출지 확인.
3. **폰트 패밀리 불일치 (Pretendard ↔ GmarketSans)**: 디자인 의도는 Pretendard. 모바일은 현재 GmarketSans 번들. 어느 쪽으로 통일할지 결정. iOS 앱 스토어 심사 / 라이선스 표기는 Pretendard 채택 시 함께 처리.
4. **Glow shadow**: CSS의 발광 효과를 Compose에서 Canvas로 흉내낼지, 생략할지 — 성능/비주얼 균형 결정 필요.
5. **차트 5색**: 현재 랭킹 기능 등에 쓰일지 불확실. 실제 사용처 확인 후 토큰 유지/제거.
6. **Typography 22sp 슬롯**: 디자인엔 없으나 모바일 호출부 보호로 유지 중. 호출부 정리 후 제거 검토.
7. **bold48 lineHeight 60→48 변경**: Lovable `leading-none` 의도 반영. LoginScreen / SplashScreen 대제목 멀티라인 케이스에서 시각 검증 필요.
8. **NormalButton (medium14, lineHeight 22→20)**: 멀티라인 라벨 시 미세 변화 가능. 단일 라인이 일반적이라 영향은 미미할 것으로 예상.
9. **font-semibold/extrabold/black 매핑**: GmarketSans 자산 한계로 각각 Medium/Bold/Bold로 매핑. 디자인 의도 보존도 확인 필요.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-04-24 | 최초 정리 — styles.css 스냅샷 기반 전체 토큰 카탈로그, auth-kakao feature 작업 중 추출 | design-bridge |
| 2026-04-30 | 컬러 섹션을 colors.md 링크로 단순화. Lovable 기준 통합 1차 반영. | design-bridge |
| 2026-05-04 | (1) 컬러 섹션 — `ChallengeExtendedColors` 폐지 + `ChallengeColorScheme` 단일 진입점 반영. (2) 타이포그래피 섹션 5 — Tailwind 기본 스케일과 모바일 `ChallengeTypoGraphy` 슬롯(light/medium/bold × 12/14/16/18/20/22/24/30, bold48) 매핑 표 신설. fontWeight 매핑 정책 명시(GmarketSans 3종 자산 한계). lineHeight 변경 4건(14: 22→20, 18: 26→28, 48: 60→48) 기록. 폰트 패밀리 Pretendard↔GmarketSans 불일치 §8에 ADR 후보로 등재. | design-bridge + mobile-dev |
