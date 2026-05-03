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
  - 중단 Hero: 중앙 정렬 컬럼, `gap-8`. 로고 스탬프(140×140) → 타이틀 뱃지 + h1 + 서브카피 → 통계 칩 2개.
  - 하단 스페이서: `flex-1 min-h-[40px]`.
  - 하단 CTA: `pb-8`, "한 번 서명하면 무를 수 없음" 구분선 → 카카오 버튼 → outline 버튼(그냥 구경) → 약관 풋터.
  - 전역: `max-width:430px` 컨테이너, `px-6` (좌우 24px), `overflow-hidden`.
- **배경 연출** (z-index 뒤):
  - 상단 중앙 `gradient-glow` 원형 후광 (500×500, opacity 30%).
  - 하단 중앙 `gradient-fire` blur 블롭 (400×300, opacity 20%, blur-3xl).
  - 전면에 floating ember 점 5개 (primary 1~2px, 부유 애니메이션).
- **상호작용**:
  - "카카오로 영혼 등록하기" 탭 → Kakao SDK 네이티브 로그인 (spec 참조).
  - "그냥 구경만 할게요" 탭 → 홈 라우팅. ⚠️ 모바일에서는 비로그인 탐색 UX 결정 필요 — spec에 언급 없음, 제거 유력.
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
  - Typo: Hero `text-5xl font-black`, sub `text-[13px]`/`text-sm font-bold`, badges `text-[11px] font-semibold`, 풋터 `text-[10px]`
- **상태**:
  - `default`: 위 설명 그대로.
  - `loading`: "카카오로 영혼 등록하기" 버튼 tap 이후 Kakao SDK 호출 및 서버 응답 대기. ⚠️ Lovable에는 loading 디자인 없음 — Compose에서는 버튼 내부에 CircularProgressIndicator(20dp, 검정) + 텍스트 숨김 제안.
  - `error (code=701)`: spec상 다이얼로그 — Material 3 `AlertDialog`로 처리. 이 화면은 그대로 유지.
  - `error (code=703)`: spec상 전체화면 에러 — 별도 ErrorScreen 라우트, 이 화면 밖.
  - `empty` / `offline`: 해당 없음(로그인 화면이라 데이터 없음). 네트워크 끊김은 버튼 탭 시점에서 code=703과 동일 처리.
- **모바일 대응**:
  - `max-width:430px`는 네이티브에서 의미 없음 — 화면 폭 그대로 사용(`fillMaxSize`).
  - `min-height:100dvh` → `Modifier.fillMaxHeight()` + `WindowInsets.safeDrawing` 적용해서 status bar/notch 회피.
  - 중앙 `flex-1` 스페이서는 Compose에서 `Spacer(Modifier.weight(1f))` 2개로. Hero 섹션이 화면 중앙 근처에 오도록 weight 밸런스.
  - 부유 입자 5개는 저사양 단말에서 프레임 드랍 우려 — 접근성 설정("애니메이션 줄이기") ON일 때 정적 렌더 또는 제거. ⚠️ 확인 필요.
  - 로그인 화면은 시스템 뒤로가기로 앱 종료시키는 편이 일반적 — Navigation에서 백스택 root로 두고 back press handling 필요(별도 spec 밖, mobile-dev 재량).

---

## 부가 요소 체크 (login.tsx에 있는 것 전부)

| 요소 | 위치 | 모바일 반영 여부 |
|------|------|----------------|
| 스탬프 로고 (외곽링 회전 + 내부 fire 스탬프 + Flame 아이콘 + Sparkles 2개) | Hero 최상단 | ✅ 반영. 단 `Flame` / `Sparkles`은 lucide-react 아이콘 — Compose에서는 `compose-icons` 대체하거나 SVG 리소스로 번들. |
| "SOUL CONTRACT" 뱃지 (점+텍스트 캡슐) | 타이틀 위 | ✅ 반영. `Row` + `Background(color=primary/10, shape=CircleShape) + Border(primary/20)`. |
| 타이틀 "영혼을 걸어라. 🔥" (gradient-fire 텍스트 + 일반 텍스트 + 흔들리는 이모지) | Hero 중앙 | ✅ 반영. `Brush`로 `drawWithContent { gradient }` 또는 `TextStyle(brush=...)` 사용. 이모지는 시스템 이모지 폰트. |
| 서브 카피 2줄 ("말만 번지르르한…"/"피할 수 없는 1:1 도전장") | 타이틀 아래 | ✅ 반영. |
| 통계 칩 "🤝 12,847건의 맹세" / "☕ 238잔의 벌칙 커피" | Hero 하단 | ⚠️ **하드코딩된 숫자** — 마케팅 목적 더미. spec에 API 없음. Sprint 0에서는 더미 유지 혹은 제거. pm-lead 확인 필요. |
| 구분선 + "한 번 서명하면 무를 수 없음" | CTA 위 | ✅ 반영. `Divider` 두 개 + 중앙 Text. |
| 카카오 로그인 버튼 | 메인 CTA | ✅ 반영 (§아래 "버튼 매핑"). |
| "그냥 구경만 할게요 👀" outline 버튼 | 카카오 버튼 아래 | ⚠️ spec에 게스트 모드 없음. mobile-dev가 **제거** 권장 — 로그인 필수 플로우와 충돌. pm-lead 확인 필요. |
| 약관/개인정보처리방침 동의 풋터 | 최하단 | ✅ 반영. 현재 비링크. 실제 링크는 별도 feature에서 연결. |
| 앱 버전 표시 | 없음 | — |

---

## 버튼 매핑 — "카카오로 영혼 등록하기"

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
| 아이콘 | 카카오 말풍선 SVG (inline, 20×20, currentColor) | SVG를 `:core:designsystem/resources/drawable/ic_kakao.svg`로 번들. `Icon(painterResource(...), tint = Color(0xFF191919), size = 20.dp)` |
| 아이콘-텍스트 간격 | `gap-3` (12px) | `Row { ... Spacer(12.dp) ... }` 또는 `Arrangement.spacedBy(12.dp)` |
| 그림자 | `shadow-lg` (Tailwind 기본) | `Modifier.shadow(8.dp, RoundedCornerShape(16.dp))` 근사치 |
| Pressed | `active:scale-[0.97]` (base 버튼 스타일) | Compose `InteractionSource`로 pressed 시 `scale=0.97` |
| Disabled | `disabled:opacity-50` | `alpha = 0.5f` |
| Ripple 색 | 미정(웹은 hover `#FDD835`) | `BrandColors.KakaoYellowPressed` (`#FDD835`)로 ripple 매핑 가능. ⚠️ Material 3 기본 ripple과 어떻게 결합할지 디자이너 확인 필요. |

**권장 구현 경로**: `:core:designsystem`에 재사용 컴포넌트 `KakaoSignInButton(onClick, enabled, loading)` 추가 — 브랜드 컬러가 하드코딩되므로 이 화면 전용이 아닌 **단일 진실 소스**로 관리. 다른 화면에서 카카오 로그인 버튼이 추가로 필요할 때 재사용.

### 카카오 브랜드 컴플라이언스 체크

- 배경 `BrandColors.KakaoYellow` (`#FEE500`) ✅ 공식값과 일치, 토큰화 완료.
- 텍스트 `BrandColors.KakaoLabel` (`#191919`) ✅ 공식 가이드 "블랙 텍스트"와 일치, 토큰화 완료.
- 아이콘: 카카오톡 말풍선 — Lovable은 inline SVG path 1개(단색 currentColor). 카카오 공식 리소스 SDK에서 제공하는 PNG/SVG로 교체 권장(상표 권리 이슈 예방). ⚠️ 확인 필요.
- 텍스트 "카카오로 영혼 등록하기": 공식 가이드는 "카카오 로그인", "카카오로 시작하기" 등 몇 가지 허용 문구 제시 — "영혼 등록"은 제품 톤앤매너상 채택했지만 **카카오 심사 시 거절 가능성** 있음. ⚠️ 공식 가이드 재확인 필요 (pm-lead가 카카오 디벨로퍼 문서 체크).

---

## 컴포넌트 매핑 표

| Lovable 소스 | Compose 제안 | 신규/기존 | 비고 |
|-------------|-------------|----------|------|
| `<Button variant="kakao" size="full">` | `KakaoSignInButton` (신규) | 신규 — `:core:designsystem` | 카카오 브랜드 고정 컴포넌트 |
| `<Button variant="outline" size="full">` | `ChallengeOutlineButton` or Material 3 `OutlinedButton` | 기존 디자인시스템 확장 | 외부 화면에서도 재사용 |
| Hero 스탬프 (원형 링 회전 + fire-gradient 배경 + Flame 아이콘) | `SoulStampLogo` (신규 composable) | 신규 — `:feature:auth` 또는 `:core:designsystem` | 회전 애니메이션 포함. 다른 화면에서도 쓸지 pm-lead 확인 |
| "SOUL CONTRACT" 뱃지 | `StatusPillBadge(text, iconColor)` | 신규 — `:core:designsystem` | 재사용 전망 높음(홈/상세에서도 유사 뱃지 예상) |
| 통계 칩 (stat chip) | `StatChip(emoji, label, value)` | ⚠️ 데이터 미정이라 보류 | 필요 시 신규 |
| 구분선+텍스트(divider with label) | `LabeledDivider(text)` | 신규 — `:core:designsystem` | Material 3에 없음 |
| 불꽃 입자 배경 (ember particles) | `EmberParticleBackground` (Canvas) | 신규 — `:feature:auth` 한정 | 성능 고려, 접근성 옵션 |
| `gradient-glow` / `gradient-fire` 블롭 | `Brush.radialGradient` / `Brush.linearGradient` + `blur()` | — | `:core:designsystem`의 `ChallengeBrushes`에 등록 |
| `text-gradient-fire` | `Text(style = TextStyle(brush = ChallengeBrushes.fire))` | — | Compose 1.6+ brush 지원 |
| `Flame` / `Sparkles` (lucide-react) | Material Icons Extended의 `LocalFireDepartment`, `AutoAwesome` 또는 커스텀 SVG | 기존/신규 | 아이콘 룩이 lucide와 다를 수 있음. ⚠️ 대조 확인. |

---

## ⚠️ 확인 필요 / pm-lead 질의 사항

1. **게스트 모드**: "그냥 구경만 할게요" 버튼 — spec에 해당 플로우 없음. 제거 or 추가 spec 필요.
2. **통계 칩 숫자(12,847 / 238)**: 하드코딩 더미인지, 실제 집계 API가 있을 예정인지 확인. 현재 스프린트 범위에서는 제거 또는 "N명과 함께" 수준의 정적 문구 권장.
3. **카카오 버튼 문구**: "카카오로 영혼 등록하기" 카카오 공식 가이드 준수 여부. 비준수 시 "카카오로 시작하기"로 대체.
4. **카카오 아이콘 리소스**: Lovable의 inline SVG path를 그대로 써도 되는지, 카카오 공식 아이콘 SDK/리소스를 받아야 하는지.
5. **로딩 상태 디자인**: Lovable에 없음 — Compose에서 임의 디자인(버튼 내부 spinner)해도 되는지, 아니면 디자이너 추가 시안 요청할지.
6. **접근성 "애니메이션 줄이기"**: 부유 입자/회전/맥동 애니메이션 비활성 옵션 제공 여부.
7. **라이트 모드**: 2026-04-30 dark-first 단일 테마로 통일 결정됨([colors.md §0](../../design-system/colors.md#0-적용된-결정-2026-04-30-lovable-기준-통합-완료)). 라이트 추가 필요 시 별도 ADR.
8. **SOUL CONTRACT 영문 뱃지**: 국문 제품명 "맹세"와 섞인 영문이 의도된 톤인지.
9. **디자이너 시각 검증 5건** (gradient end / card stops / chart4 / glow brush / 135deg 정확도): mobile-dev 통합 시 변환 추정값. 상세는 [colors.md §5](../../design-system/colors.md#5-️-디자이너-시각-검증-필요).

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-04-24 | 최초 작성 — login.tsx 스냅샷 기반. tokens.md 신규 생성과 동시 작업. auth-kakao feature의 UI 범위 전체 커버. | design-bridge |
| 2026-04-24 | mobile-dev의 Lovable 통합 결과 반영. 카카오 컬러 `BrandColors` 토큰화 완료, LoginScreen 컬러 매핑을 실제 적용 토큰명(`MaterialTheme.colorScheme.*`, `LocalChallengeBrushes.current.fire`, `BrandColors.KakaoYellow`)으로 갱신. 디자이너 검토 5건 colors.md §5 참조 링크 추가. | design-bridge |
