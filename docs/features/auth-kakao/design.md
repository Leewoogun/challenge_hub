# Design — auth-kakao

- **디자인 소스**: `/Users/hwamulman/woogunProject/challenge/challenge-design/oathbound-challenges`
- **참조 route**: `src/routes/login.tsx`
- **참조 컴포넌트**: `src/components/ui/button.tsx` (variant=`kakao`, `outline`; size=`full`)
- **전역 토큰**: [`docs/design-system/tokens.md`](../../design-system/tokens.md) — 색상·그라데이션·타이포 값은 모두 여기 참조
- **스냅샷 일시**: 2026-04-24
- **대상 화면 수**: 1 (Login)

## 화면 목록

### Login — 카카오 로그인 진입점

- **참조**: `src/routes/login.tsx`
- **의도**: "영혼의 맹세"라는 제품 컨셉을 첫 화면에서 각인시키면서, 카카오 한 번 눌러 바로 진입하도록 마찰 최소화. 불꽃(primary) 톤의 다크 화면, 중앙의 스탬프/인장 비주얼, 하단 CTA 고정.
- **레이아웃** (세로 3분할, `flex-col`):
  - 상단 스페이서: `flex-1 min-h-[60px]` — safe area 이후 최소 60px 여백, 남는 공간은 상단이 더 먹음.
  - 중단 Hero: 중앙 정렬 컬럼, `gap-8`. 로고 스탬프(140×140) → 타이틀 뱃지 + h1 + 서브카피.
  - 하단 스페이서: `flex-1 min-h-[40px]`.
  - 하단 CTA: `pb-8`, "한 번 서명하면 무를 수 없음" 구분선 → 카카오 버튼 → 약관 풋터.
  - 전역: `max-width:430px` 컨테이너, `px-6` (좌우 24px), `overflow-hidden`.
- **배경 연출** (z-index 뒤):
  - 상단 중앙 `gradient-glow` 원형 후광 (500×500, opacity 30%).
  - 하단 중앙 `gradient-fire` blur 블롭 (400×300, opacity 20%, blur-3xl).
- **상호작용**:
  - "카카오로 시작하기" 탭 → Kakao SDK 네이티브 로그인 (spec 참조).
  - 약관 텍스트는 현재 비링크(그냥 강조 텍스트). 실제 링크 연결은 별도 feature.
  - 화면 진입 시 Hero + CTA가 `slide-up` 애니메이션(0.4s, CTA는 0.2s delay).
- **토큰 참조** (값은 [colors.md](../../design-system/colors.md) / [tokens.md](../../design-system/tokens.md)):
  - 배경: `MaterialTheme.colorScheme.background` (`#26272F`)
  - 전경: `colorScheme.onBackground` (`#F2F2F4`) / `colorScheme.onSurfaceVariant` (`#9596A0`, 캡션)
  - 브랜드 Primary(스탬프, 입자, 뱃지 액센트): `colorScheme.primary` (`#E97A3D`)
  - 로고 배경: `LocalChallengeBrushes.current.fire` (135deg 오렌지 → 짙은 주홍)
  - 후광: `LocalChallengeBrushes.current.glow` (radial 오렌지 글로우)
  - 카드 칩: `colorScheme.surface` (`#2F303A`) + `colorScheme.outline` (`#43444E`)
  - 카카오 버튼: `BrandColors.KakaoYellow` / `BrandColors.KakaoLabel` ✅ 토큰화 완료
  - Radius: `radius.xl` (16dp, 버튼 full) / `radius.full` (스탬프, 뱃지)
  - Typo: Hero `text-5xl font-black` (→ `bold48`), sub `text-[13px]`/`text-sm font-bold` (→ `bold14`), badges `text-[11px] font-semibold` (→ `medium12` 근사), **LabeledDivider "한 번 서명하면 무를 수 없음" `text-[10px] font-bold` (→ `bold10` 슬롯, 2026-05-12 tokens.md §5.2 추가 후보)**, **풋터 약관 텍스트 `text-[10px]` weight-미지정 (→ `light10` 슬롯, 2026-05-12 tokens.md §5.2 추가 후보)**. ⚠️ 현재 모바일 LoginScreen은 LabeledDivider 기본 `bold12` / FooterAgreementText `light12`로 12sp 사용 — Lovable 10sp와 불일치. tokens.md §5.2 정책에 따라 `bold10`/`light10` 슬롯 신설 + 호출부 정합 권고 (backlog.md mobile 항목).
- **상태**:
  - `default`: 위 설명 그대로.
  - `loading`: "카카오로 시작하기" 버튼 tap 이후 Kakao SDK 호출 및 서버 응답 대기. **결정 (2026-05-08)**: 정식 시안 없이 화면 중앙 검정 30% 오버레이 + `CircularProgressIndicator` placeholder 유지. 추후 디자이너 시안 나오면 재검토.
  - `error (code=701)`: spec상 다이얼로그 — Material 3 `AlertDialog`로 처리. 이 화면은 그대로 유지.
  - `error (code=703)`: spec상 전체화면 에러 — 별도 ErrorScreen 라우트, 이 화면 밖.
  - `empty` / `offline`: 해당 없음(로그인 화면이라 데이터 없음). 네트워크 끊김은 버튼 탭 시점에서 code=703과 동일 처리.
- **모바일 대응**:
  - `max-width:430px`는 네이티브에서 의미 없음 — 화면 폭 그대로 사용(`fillMaxSize`).
  - `min-height:100dvh` → `Modifier.fillMaxHeight()` + `WindowInsets.safeDrawing` 적용해서 status bar/notch 회피.
  - 중앙 `flex-1` 스페이서는 Compose에서 `Spacer(Modifier.weight(1f))` 2개로. Hero 섹션이 화면 중앙 근처에 오도록 weight 밸런스.
  - 로그인 화면은 시스템 뒤로가기로 앱 종료시키는 편이 일반적 — Navigation에서 백스택 root로 두고 back press handling 필요(별도 spec 밖, mobile-dev 재량).

---

## 부가 요소 체크 (login.tsx에 있는 것 전부)

| 요소 | 위치 | 모바일 반영 여부 |
|------|------|----------------|
| 스탬프 로고 (내부 fire 스탬프 + Flame 아이콘 + Sparkles 2개) | Hero 최상단 | ✅ 반영. 단 `Flame` / `Sparkles`은 lucide-react 아이콘 — Compose에서는 `compose-icons` 대체하거나 SVG 리소스로 번들. **외곽 링 회전은 제거 결정 (2026-05-08)**. |
| "SOUL CONTRACT" 뱃지 (점+텍스트 캡슐) | 타이틀 위 | ✅ 반영. `Row` + `Background(color=primary/10, shape=CircleShape) + Border(primary/20)`. |
| 타이틀 "영혼을 걸어라. 🔥" (gradient-fire 텍스트 + 일반 텍스트 + 흔들리는 이모지) | Hero 중앙 | ✅ 반영. `Brush`로 `drawWithContent { gradient }` 또는 `TextStyle(brush=...)` 사용. 이모지는 시스템 이모지 폰트. |
| 서브 카피 2줄 ("말만 번지르르한…"/"피할 수 없는 1:1 도전장") | 타이틀 아래 | ✅ 반영. |
| 통계 칩 "🤝 12,847건의 맹세" / "☕ 238잔의 벌칙 커피" | ~~Hero 하단~~ | ❌ **제거 결정 (2026-05-08)** — Lovable에서도 삭제됨. |
| 구분선 + "한 번 서명하면 무를 수 없음" | CTA 위 | ✅ 반영. `Divider` 두 개 + 중앙 Text. |
| 카카오 로그인 버튼 | 메인 CTA | ✅ 반영 (§아래 "버튼 매핑"). |
| "그냥 구경만 할게요 👀" outline 버튼 | ~~카카오 버튼 아래~~ | ❌ **제거 결정 (2026-05-08)** — Lovable에서도 삭제됨. |
| 약관/개인정보처리방침 동의 풋터 | 최하단 | ✅ 반영. 현재 비링크. 실제 링크는 별도 feature에서 연결. |
| 앱 버전 표시 | 없음 | — |

---

## 버튼 매핑 — "카카오로 시작하기"

Lovable 정의 (`button.tsx` variant=`kakao`, size=`full`):

```
bg-[#FEE500] text-[#191919] font-bold hover:bg-[#FDD835]
h-13 w-full rounded-xl px-8 text-base   ← size=full
```

| 속성 | Lovable 값 | Compose 매핑 |
|------|-----------|-------------|
| 배경색 | `#FEE500` | `BrandColors.KakaoYellow` ✅ 토큰화 완료 (`:core:designsystem` `BrandColors.kt`) |
| 텍스트 색 | `#191919` | `BrandColors.KakaoLabel` ✅ 토큰화 완료 |
| 폰트 굵기 | `font-bold` (700) | `FontWeight.Bold` |
| 폰트 크기 | `text-base` (16px) | 16.sp |
| 높이 | `h-13` (52px) | `52.dp` (Material 기본 버튼 48dp보다 약간 크다) |
| 가로 | `w-full` | `Modifier.fillMaxWidth()` |
| 모서리 | `rounded-xl` (16px) | `RoundedCornerShape(16.dp)` |
| 좌우 패딩 | `px-8` (32px) | `PaddingValues(horizontal = 32.dp)` |
| 아이콘 | ~~카카오 말풍선 SVG~~ — **제거 결정 (2026-05-08)** | 텍스트 only |
| 아이콘-텍스트 간격 | — (아이콘 없음) | — |
| 그림자 | `shadow-lg` (Tailwind 기본) | `Modifier.shadow(8.dp, RoundedCornerShape(16.dp))` 근사치 |
| Pressed | `active:scale-[0.97]` (base 버튼 스타일) | Compose `InteractionSource`로 pressed 시 `scale=0.97` |
| Disabled | `disabled:opacity-50` | `alpha = 0.5f` |
| Ripple 색 | 미정(웹은 hover `#FDD835`) | `BrandColors.KakaoYellowPressed` (`#FDD835`)로 ripple 매핑 가능. ⚠️ Material 3 기본 ripple과 어떻게 결합할지 디자이너 확인 필요. |

**권장 구현 경로**: `:core:designsystem`에 재사용 컴포넌트 `KakaoSignInButton(onClick, enabled, loading)` 추가 — 브랜드 컬러가 하드코딩되므로 이 화면 전용이 아닌 **단일 진실 소스**로 관리. 다른 화면에서 카카오 로그인 버튼이 추가로 필요할 때 재사용.

### 카카오 브랜드 컴플라이언스 체크

- 배경 `BrandColors.KakaoYellow` (`#FEE500`) ✅ 공식값과 일치, 토큰화 완료.
- 텍스트 `BrandColors.KakaoLabel` (`#191919`) ✅ 공식 가이드 "블랙 텍스트"와 일치, 토큰화 완료.
- 아이콘: **제거 결정 (2026-05-08)** — 텍스트 only로 처리. 카카오 상표 권리 이슈 회피.
- 텍스트 **"카카오로 시작하기"** ✅ 카카오 공식 가이드 허용 문구. 결정 (2026-05-08).

---

## 컴포넌트 매핑 표

| Lovable 소스 | Compose 제안 | 신규/기존 | 비고 |
|-------------|-------------|----------|------|
| `<Button variant="kakao" size="full">` | `KakaoSignInButton` (신규) | 신규 — `:core:designsystem` | 카카오 브랜드 고정 컴포넌트. 아이콘 없는 텍스트 only. |
| ~~`<Button variant="outline" size="full">`~~ | — | ❌ 제거 결정 (2026-05-08) | "그냥 구경만 할게요" 버튼 삭제 |
| Hero 스탬프 (fire-gradient 배경 + Flame 아이콘) | `SoulStampLogo` (신규 composable) | 신규 — `:feature:login` 또는 `:core:designsystem` | **외곽 회전 링은 제거 결정 (2026-05-08)**. `pulse-fire` 맥동만 유지. |
| "SOUL CONTRACT" 뱃지 | `StatusPillBadge(text, iconColor)` | 신규 — `:core:designsystem` | 재사용 전망 높음(홈/상세에서도 유사 뱃지 예상) |
| ~~통계 칩 (stat chip)~~ | — | ❌ 제거 결정 (2026-05-08) | Lovable 및 모바일 양쪽 미반영 |
| 구분선+텍스트(divider with label) | `LabeledDivider(text)` | 신규 — `:core:designsystem` | Material 3에 없음 |
| ~~불꽃 입자 배경 (ember particles)~~ | — | ❌ 제거 결정 (2026-05-08) | Lovable에서도 삭제됨 |
| `gradient-glow` / `gradient-fire` 블롭 | `Brush.radialGradient` / `Brush.linearGradient` + `blur()` | — | `:core:designsystem`의 `ChallengeBrushes`에 등록 |
| `text-gradient-fire` | `Text(style = TextStyle(brush = ChallengeBrushes.fire))` | — | Compose 1.6+ brush 지원 |
| `Flame` / `Sparkles` (lucide-react) | Material Icons Extended의 `LocalFireDepartment`, `AutoAwesome` 또는 커스텀 SVG | 기존/신규 | 아이콘 룩이 lucide와 다를 수 있음. ⚠️ 대조 확인. |

---

## ✅ pm-lead 결정 사항 (2026-05-08)

| # | 항목 | 결정 | 적용 위치 |
|---|------|------|----------|
| 1 | "그냥 구경만 할게요" 버튼 (게스트 모드) | **제거** | Lovable `login.tsx` ✅ 반영 / 모바일 `LoginScreen.kt` 2차 PR에서 반영 |
| 2 | 통계 칩 (`12,847건의 맹세` / `238잔의 벌칙 커피`) | **제거** | Lovable ✅ 반영 / 모바일 미반영(원래 placeholder라 무관) |
| 3 | 카카오 버튼 문구 | **카카오 공식 가이드 준수** → "카카오로 시작하기" | Lovable ✅ 반영 / 모바일은 이미 "카카오로 시작하기" |
| 4 | 카카오 버튼 말풍선 SVG 아이콘 | **제거** (텍스트 only) | Lovable ✅ 반영 / 모바일은 원래 없음 |
| 5 | 로딩 상태 디자인 | **현재 placeholder 유지** — 화면 중앙 `CircularProgressIndicator` (검정 30% 오버레이). 정식 시안은 추후. | 모바일 현 구현 그대로 |
| 6 | 애니메이션 — 부유 입자(ember 5개) | **제거** | Lovable ✅ 반영 / 모바일은 원래 없음 |
| 6 | 애니메이션 — 외곽 링 회전(`animate-spin-slow`) | **제거** (불꽃 모양 아님) | Lovable ✅ 반영 / 모바일은 원래 없음 |
| 6 | 애니메이션 — 불꽃 관련(스탬프 fire-gradient + `pulse-fire`, 🔥 `wiggle`, `slide-up`) | **유지** | Lovable 유지 / 모바일 2차 PR에서 반영 |
| 7 | 라이트 모드 | **추가 안 함**, dark-first 단일 테마 확정 (colors.md §0) | — |
| 8 | "SOUL CONTRACT" 영문 뱃지 | **현재 디자인 유지** | Lovable 유지 / 모바일 2차 PR에서 반영 |
| 9 | 디자이너 시각 검증 6건 (colors.md §5) | **현 추정값 그대로 채택**. 디자이너 부재로 별도 검증 생략. 추후 미세 조정 시 별도 ADR. | colors.md §5 그대로 보존 |

> 동기화 원칙: Lovable과 모바일 화면은 항상 동일한 결정을 반영해야 한다. 이 표가 양쪽 진실 소스.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-04-24 | 최초 작성 — login.tsx 스냅샷 기반. tokens.md 신규 생성과 동시 작업. auth-kakao feature의 UI 범위 전체 커버. | design-bridge |
| 2026-04-24 | mobile-dev의 Lovable 통합 결과 반영. 카카오 컬러 `BrandColors` 토큰화 완료, LoginScreen 컬러 매핑을 실제 적용 토큰명(`MaterialTheme.colorScheme.*`, `LocalChallengeBrushes.current.fire`, `BrandColors.KakaoYellow`)으로 갱신. 디자이너 검토 5건 colors.md §5 참조 링크 추가. | design-bridge |
| 2026-05-08 | pm-lead 9건 결정 반영. "그냥 구경만 할게요"·통계 칩·카카오 SVG 아이콘·외곽 링 회전·부유 입자 5개 모두 **제거**. 카카오 버튼 문구 "카카오로 시작하기"로 통일(공식 가이드 준수). Lovable `login.tsx` 동기 갱신. 모바일 `LoginScreen.kt` 2차 PR에서 본 결정 반영 예정. 디자이너 시각 검증 6건은 추정값 그대로 채택. | pm-lead |
| 2026-05-12 | tokens.md §5.2 `medium10` 슬롯 신설 후속 — "토큰 참조"의 10sp 라벨 매핑을 정리. LabeledDivider "한 번 서명하면 무를 수 없음" `text-[10px] font-bold` → `bold10` 슬롯 후보, FooterAgreementText 약관 풋터 `text-[10px]` weight-미지정 → `light10` 슬롯 후보로 명시. 현재 모바일 호출부는 `bold12`/`light12`로 12sp 사용 중이라 10sp 정합 작업이 별도 후속(backlog.md mobile 항목 등재). | design-bridge |
