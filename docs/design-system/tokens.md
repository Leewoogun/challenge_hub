# Design Tokens — 맹세(MAENGSE)

- **소스**: `challenge-design/oathbound-challenges/src/styles.css` (Tailwind v4 `@theme inline` + CSS 변수)
- **최종 스냅샷**: 2026-04-24
- **테마**: Dark-first 단일 테마 (라이트 보류 — 추후 ADR로 재논의)
- **목적**: Compose Multiplatform의 `:core:designsystem` 모듈이 동기화해야 할 의미 단위 토큰 카탈로그. 각 feature의 `design.md`는 값을 복붙하지 말고 이 문서를 링크로 참조.

---

## 1. 색상 (Colors)

> **컬러 토큰의 single source of truth는 [colors.md](./colors.md).** 본 섹션은 요약 + 링크.

- **Material3 darkColorScheme 매핑 표** (primary, background, surface, error 등 16슬롯) → [colors.md §1](./colors.md#1-의미-단위-색상-semantic--material3-colorscheme-슬롯)
- **ChallengeExtendedColors** (success / warning / chart 1~5 / gradient stops 등 Material3에 없는 토큰) → [colors.md §2](./colors.md#2-challengeextendedcolors--material3-외-확장-토큰)
- **ChallengeBrushes** (`fire` / `card` / `glow` Brush 헬퍼) → [colors.md §3](./colors.md#3-challengebrushes--compose-brush-헬퍼)
- **BrandColors** (Kakao 토큰화 완료) → [colors.md §4](./colors.md#4-brandcolors--외부-브랜드-kakao)
- **디자이너 시각 검증 필요 5건** → [colors.md §5](./colors.md#5-️-디자이너-시각-검증-필요)

2026-04-30 적용 결정 요약: Lovable 기준으로 모바일 통합 완료. Dark-first, Primary `#E97A3D`, 카카오 토큰화, ExtendedColors/Brushes 신설. 자세한 내용은 colors.md §0 참조.

---

## 2. 그라데이션 (Gradients)

| 의미 토큰 | CSS 변수 | 정의 | 용도 |
|---------|---------|------|------|
| Fire | `--gradient-fire` | `linear-gradient(135deg, oklch(0.72 0.19 45), oklch(0.65 0.22 30))` | 기본 버튼 배경, 로고 스탬프, 타이틀 텍스트 하이라이트 |
| Card | `--gradient-card` | `linear-gradient(135deg, oklch(0.25 0.02 270), oklch(0.22 0.015 270))` | 카드 배경(미묘한 depth) |
| Glow | `--gradient-glow` | `radial-gradient(circle at 50% 0%, oklch(0.72 0.19 45 / 15%), transparent 60%)` | 화면 상단 후광 (로그인/홈) |

Compose 매핑: `Brush.linearGradient(...)` / `Brush.radialGradient(...)`. `:core:designsystem`에 `ChallengeBrushes.fire`, `.card`, `.glow`로 고정.

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

Compose 매핑 제안: `:core:designsystem`에 `ChallengeShapes(small=8.dp, medium=12.dp, large=16.dp, extraLarge=24.dp)` → Material 3 `Shapes` 슬롯.

---

## 5. 타이포그래피 (Typography)

### 5.1 폰트 패밀리

| CSS 변수 | 값 | 모바일 대체 |
|---------|-----|-----------|
| `--font-family-display` | `'Pretendard', system-ui, -apple-system, sans-serif` | Android: Pretendard 번들 or Noto Sans KR fallback / iOS: Pretendard 번들 or `-apple-system` (SF Pro + SD Gothic) |

> Pretendard는 무료 상업 사용 가능. `:core:designsystem`의 `resources/font/` 에 번들하고 `FontFamily`로 노출할 것을 권장.

### 5.2 크기 / 굵기 (Lovable에서 관찰된 실사용 값만)

Tailwind 기본 사이즈를 그대로 사용 중. 아래는 로그인 화면에서 관찰된 값 기준.

| 역할 | Tailwind class | font-size | font-weight | line-height | Compose 매핑 제안 |
|------|---------------|----------|------------|------------|----------------|
| Hero Title | `text-5xl font-black leading-none tracking-tight` | 48px (3rem) | 900 | 1.0 | `displayMedium` (커스텀 weight 900) |
| Body (강조) | `text-sm font-bold` | 14px | 700 | 1.25 | `bodyMedium` + `SemiBold/Bold` |
| Body | `text-[13px]` | 13px | 400 | 1.5 | `bodySmall` |
| Badge / Caption | `text-[11px] font-semibold` | 11px | 600 | 1.4 | `labelSmall` |
| Fine print | `text-[10px]` (uppercase+tracking-widest) | 10px | 700 | 1.6 | 커스텀 `labelTiny` |

> 굵기 400/600/700/900 4종을 지원하는 Pretendard 웨이트 번들 필요.

---

## 6. 스페이싱 / 레이아웃

| 토큰 | 값 | 용도 |
|------|-----|------|
| App container max-width | `430px` | 모바일 최대 폭 (Lovable 웹에서 모바일 프리뷰용). 네이티브 모바일은 무시, 화면 꽉 채움. |
| 기본 수평 패딩 | `px-6` (24px) | 화면 좌우 gutter |
| 기본 수직 리듬 | `gap-8` (32px) / `gap-3` (12px) | 섹션 간격 / 컴포넌트 간격 |

Compose: `ChallengeSpacing(xs=4, sm=8, md=12, lg=16, xl=24, xxl=32)` 정의 후 사용.

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
3. **Pretendard 번들링**: iOS 앱 스토어 심사 / 라이선스 표기 처리 확인.
4. **Glow shadow**: CSS의 발광 효과를 Compose에서 Canvas로 흉내낼지, 생략할지 — 성능/비주얼 균형 결정 필요.
5. **차트 5색**: 현재 랭킹 기능 등에 쓰일지 불확실. 실제 사용처 확인 후 토큰 유지/제거.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-04-24 | 최초 정리 — styles.css 스냅샷 기반 전체 토큰 카탈로그, auth-kakao feature 작업 중 추출 | design-bridge |
| 2026-04-24 | 컬러 섹션을 colors.md 링크로 단순화. mobile-dev의 Lovable 기준 통합(2026-04-30) 반영 — Dark-first 통일, Primary `#E97A3D`, BrandColors/ExtendedColors/Brushes 신설. 컬러 외 토큰(그라데이션 정의/radius/typography/spacing/animation)은 그대로 유지. | design-bridge |
