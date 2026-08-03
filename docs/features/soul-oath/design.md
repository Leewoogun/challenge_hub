# Design — soul-oath (영혼의 맹세)

- **디자인 소스**: `/Users/hwamulman/woogunProject/challenge/challenge-design/oathbound-challenges`
- **참조 route**: `src/routes/challenge-new.tsx` step2 (수정), `src/routes/challenge-detail.tsx` (수정), `src/routes/oath.tsx` (**신규**)
- **전역 토큰**: [`tokens.md`](../../design-system/tokens.md), [`colors.md`](../../design-system/colors.md)
- **상위 spec**: [spec.md](./spec.md)
- **선행 design**: [`challenge-create/design.md`](../challenge-create/design.md) — `AcceptChallengeDialog` 결정 이력
- **스냅샷 일시**: 2026-08-03
- **신규 토큰**: **0건** (§6.1에 회피 근거 1건 기록)

## 착수 전 실측 (추측 아님)

지난 feature에서 플랫폼 제약을 추측했다가 결정을 두 번 뒤집었다. 이번엔 먼저 쟀다.

| 확인 | 명령 | 결과 |
|---|---|---|
| 드로잉 선례 | `grep -rln "pointerInput\|Canvas(\|drawPath\|detectDragGestures" feature core --include=*.kt` | **0건** — 앱 전체에 드로잉 코드가 없다 |
| `AcceptChallengeDialog` 실제 구조 | `AcceptChallengeDialog.kt:88` | **`Column(verticalScroll(rememberScrollState()))`** — 현재 최소 컨텐트(요약 3행 + 입력 1개)에서 **이미 스크롤이 필요하다** |
| 위저드 step | `ChallengeCreateStep` | `FRIEND_PICK` / `MISSION_INPUT` **2개** — progress 2칸 |
| `:feature:challenge:detail` | `settings.gradle.kts:69` | **없음** (`:feature:challenge:create`만) |
| `:core:ui` 입주자 | — | `StatusPillBadge`, `PlaceholderScreen`, `LabeledInputField` |

---

## 1. T-D1 — 상대방 맹세 화면: **전체 화면으로 승격**

### 1.1 결정

`AcceptChallengeDialog`(다이얼로그)를 **`OathScreen`(전체 화면)으로 교체**한다.

### 1.2 근거

**(a) 다이얼로그가 이미 한계다 — 측정된 사실.** 현재 다이얼로그는 요약 3행 + 입력 1개뿐인데 `verticalScroll`이 붙어 있다. 여기에 계약서 4행 + **서명 캔버스(168.dp)** + "다시 그리기" + CTA가 더 들어간다. 컨텐트가 대략 2배가 된다.

**(b) 스크롤 ↔ 드로잉 제스처 충돌 — 이게 결정적이다.** 서명 캔버스를 `verticalScroll` 컨테이너 안에 넣으면 캔버스 위의 드래그가 **"획을 긋는다" vs "부모를 스크롤한다"**로 모호해진다. 캔버스가 제스처를 완전 소비하게 만들 수는 있지만, 그러면 캔버스 영역에서 화면 스크롤이 죽어 IME가 올라왔을 때 CTA에 도달하지 못한다. **전체 화면에서는 캔버스를 스크롤 영역 밖 고정 슬롯에 둘 수 있어 충돌 자체가 사라진다.**

**(c) 되돌릴 수 없는 행위에 dismissible 컨테이너는 맞지 않다.** `is_finalized`가 되는 순간이고 제품 컨셉이 "무를 수 없는 약속"이다. 배경 탭 한 번에 공들여 그린 서명이 날아가는 건 이 화면에서 특히 나쁘다.

**(d) 대칭.** 챌린저는 위저드 **맹세 step(전체 화면)**에서 같은 계약서에 서명한다. 같은 행위를 한쪽은 전체 화면, 한쪽은 다이얼로그로 두면 무게가 달라 보인다.

### 1.3 이전 결정과의 관계 — 번복이 아니다

`challenge-create`에서 바텀시트를 기각하고 다이얼로그를 택한 근거는 **"입력 필드가 1개뿐이라 시트의 넓은 면적이 필요 없다"**였다. 그 전제가 이번에 바뀐다(계약서 + 캔버스 추가). **같은 기준을 적용해 다른 답이 나온 것**이지, 판단이 뒤집힌 게 아니다.

**바텀시트 기각 근거는 그대로 유효하다** — 시트 선례 0건 + CMP iOS IME 리스크. 전체 화면은 그 리스크를 우회하되 면적 문제도 푼다. **시트는 이번에도 후보가 아니다.**

> ⚠️ `AcceptChallengeDialog`는 **삭제되고 `OathScreen`으로 대체**된다. challenge-create가 만든 자산이라 mobile-dev가 교체분을 **회귀와 분리 보고**해야 한다(spec 리스크 §127과 동일 취급).

### 1.4 배치 권고

| 대상 | 위치 | 사유 |
|---|---|---|
| `SignaturePad`(입력) · `SignatureView`(렌더 전용) · `ContractCard` | **`:core:ui/components/`** | **소비 모듈 3곳** — `:feature:challenge:create`(맹세 step), 상대 맹세 화면, `:feature:challenge:detail`. `LabeledInputField`가 같은 이유로 `:core:ui`에 있는 선례. |
| `OathScreen`(상대) | **`:feature:challenge:oath` 신규** | 홈에서 진입하는 독립 라우트. `:feature:friends:list`/`:search` 중첩 패턴과 동일. |
| 챌린저 맹세 step | `:feature:challenge:create/component/OathStep.kt` | 위저드 step 상태기계 안이라 분리 불가. 내부는 `ContractCard` + `SignaturePad` 조합. |

> **대안**: `:feature:challenge:oath` 모듈 신설이 부담이면 `OathScreen`을 `:feature:challenge:create`에 두는 것도 가능하다(두 화면이 거의 같아 코드 재사용은 오히려 쉬움). 다만 "create" 모듈에 수락 경로가 들어가 이름이 어긋난다. **본안은 신설**, 최종 판단은 mobile-dev/pm-lead.

---

## 2. T-D2 — 서명 인터랙션 명세

### 2.1 캔버스 기하 — **종횡비 2:1 고정**

Lovable step2는 `h-24`(96px) dashed placeholder다. **손가락 서명에 96dp는 좁다** — 성인 손가락 접촉면이 8~10dp라 획이 뭉갠다.

| 항목 | 값 | 근거 |
|---|---|---|
| **종횡비** | **2 : 1 (가로:세로) 고정** | 좌표를 `[0,1]` 정규화해 저장하는데, 입력 캔버스와 상세 렌더의 비율이 다르면 서명이 찌그러진다. **비율을 고정해야 왕복 무손실이 성립한다.** |
| 입력 캔버스 | `fillMaxWidth()` + `aspectRatio(2f)` → 화면 좌우 20.dp 패딩 기준 **≈ 335 × 168.dp** | Lovable 96 → 168dp. 서명 가능 최소 높이 확보 |
| 상세 렌더 | `weight(1f)` + `aspectRatio(2f)` → 2-up에서 **≈ 158 × 79.dp** | §3 |
| shape / 배경 | `RoundedCornerShape(12.dp)` + `colorScheme.secondary` | 기존 입력 박스와 동일 |

> ⚠️ **비율 고정은 협상 대상이 아니다.** 2:1을 바꾸려면 입력·렌더 양쪽을 같이 바꿔야 한다. 한쪽만 바꾸면 저장된 서명이 왜곡된다.

> **v4 (2026-08-03) — 불변식이 컴포넌트로 들어갔다.** 초안은 `aspectRatio(2f)`와 획 굵기를 **호출부 책임**으로 뒀는데, mobile-dev가 `SignatureCanvas`/`SignatureView` **내부**에서 강제하도록 바꿨다(`SignatureCanvas.kt:69`, `SignatureView.kt:33`, 상수는 `internal`). **이쪽이 맞다** — 불변식을 호출부에 맡기면 호출부가 늘 때마다 깨질 기회가 생긴다. 실기에서 발견할 게 아니라 **애초에 불가능하게** 만드는 것이 옳다.
>
> 따라서 **호출부는 폭만 정하고 `aspectRatio`를 덧붙이지 않는다.** `strokeWidth` 파라미터도 제거됐고 `strokeColor`만 남았다(기본값 `primary` — 명세와 일치).
>
> ⚠️ spec 수용 기준의 *"모든 호출부가 `aspectRatio(2f)`를 적용한다 / 호출부 책임 / 현재 grep 0건"*은 **이 변경으로 낡았다.** 지금 기준대로 하면 호출부가 이미 강제된 비율을 한 번 더 붙인다. pm-lead에게 정정 요청했다.

### 2.2 획 (stroke)

| 항목 | 값 | 근거 |
|---|---|---|
| 색 | `colorScheme.primary` | Lovable 상세의 서명 표시가 `text-primary`. 잉크 = 브랜드 컬러 |
| **굵기** | **캔버스 폭의 0.9%** (`width * 0.009f`), 최소 `1.5.dp` | **고정 dp를 쓰면 안 된다.** 입력(335dp)에서 3dp인 획이 상세(158dp)에서도 3dp면 상대적으로 2배 굵어져 뭉갠다. 폭 비례로 두면 어느 크기에서도 같은 서명으로 보인다 |
| cap / join | `StrokeCap.Round` / `StrokeJoin.Round` | 손글씨 느낌. 각진 획은 서명으로 안 읽힌다 |
| 렌더 | 획 1개 = `Path` 1개. 점 2개 이상이면 선분 연결, **점 1개면 반지름 = 굵기/2인 원** | 점(dot)을 그리는 서명이 사라지지 않게 |

### 2.3 상태

| 상태 | 시각 |
|---|---|
| **빈 상태** | `secondary` 배경 + **dashed border** 1.5.dp `onSurfaceVariant.copy(alpha = 0.30f)` + 중앙 "여기에 서명하세요" `medium14` `onSurfaceVariant`. (Lovable `border-dashed border-muted-foreground/30` + 동일 문구 — **그대로 계승**) |
| **그리는 중** | 첫 `down` 즉시 dashed border와 안내 문구 **제거**(획을 가린다). 획이 실시간으로 따라 그려진다 |
| **서명 있음** | `secondary` 배경 + border 없음 + 획. 우측 아래 "다시 그리기" 노출 |
| **비활성 (제출 중)** | 전체 `alpha = 0.5f` + `pointerInput` 미수신 |
| 읽기 전용 (상세) | §3 — `SignatureView`. 터치 무반응 |

- **"다시 그리기"**: 캔버스 **아래 우측** `TextButton`, `medium12` `onSurfaceVariant`, 아이콘 `Icons.Filled.Refresh` 14.dp. **획이 0개면 미노출**(공간도 차지하지 않음 — 빈 상태에서 누를 게 없다). 탭 → 전체 획 삭제 → 빈 상태 복귀. **확인 다이얼로그 없음**(다시 그리면 되는 행위라 마찰 불필요).
- **되돌리기(Undo, 획 1개 취소)는 넣지 않는다.** 서명은 보통 1~3획이라 "다시 그리기" 하나로 충분하고, 버튼이 둘이면 캔버스 아래가 복잡해진다. 필요해지면 후속.

### 2.4 완료 판정

**유효 서명 = 획 ≥ 1개.** spec 수용 기준("빈 서명(획 0개)은 거부된다")과 정확히 일치시킨다.

- CTA "맹세한다! 🔥"는 **서명 유효 + (상대 화면인 경우) 미션 유효**일 때만 활성.
- ⚠️ **확인 필요**: 점 하나 톡 찍은 것도 "획 1개"라 통과한다. 더 엄격하게 하려면 *모든 점의 바운딩 박스가 캔버스의 5% 이상*을 추가할 수 있는데, **수용 기준보다 엄격한 규칙이라 임의로 넣지 않았다.** 필요 여부는 pm-lead 판단 (§7 #3).

### 2.5 좌표 · 직렬화 (T-M1 직결 — mobile-dev 즉시 필요)

```
strokes: List<Stroke>,  Stroke = List<Point>,  Point = (x, y)
x, y ∈ [0.0, 1.0]  — 캔버스 좌상단 원점, 폭/높이로 각각 나눈 정규화 값
```

> **v2 정정 (2026-08-03) — T-M1 구현을 확인하고 내 초안을 버렸다.** 아래 표는 **mobile-dev가 실제로 구현한 값**이며, 내 초안(float 소수 3자리 / 임계 0.005)보다 낫다. 근거는 표 아래.

| 항목 | 값 (구현 확정) | 출처 |
|---|---|---|
| 정규화 | 캔버스 폭·높이로 각각 나눠 **`0..GRID` 정수로 양자화** | `Signature.kt` `GRID = 1000` |
| 좌표 타입 | **`Int`** (float 아님) | `SignaturePoint(x: Int, y: Int)` |
| **점 솎아내기** | 직전 점과 거리 **< 3 그리드 단위**(= 0.003) | `MIN_POINT_DISTANCE = 3` |
| 범위 클램프 | `coerceIn(0, GRID)` | `quantize()` |
| 상한 | **총 점 2000 / 획 100.** 초과분은 예외 없이 **조용히 무시** | `MAX_POINTS` / `MAX_STROKES` |

**왜 내 초안(float 3자리)을 버렸나**: `GRID = 1000` 정수는 **정밀도가 소수 3자리와 정확히 같으면서**(1/1000), 직렬화·역직렬화에서 **부동소수 드리프트가 원천적으로 없다.** spec 수용 기준이 *"저장·조회 왕복에서 동일하게 렌더된다"*인데, float은 왕복 무손실을 "육안상"으로만 보장하고 정수는 **비트 단위로** 보장한다. 양자화 손실이 입력 시점 1회로 끝난다는 점도 명확하다.

**솎아내기 0.005 → 0.003**: 내가 "각져 보이면 낮춰라"라고 단 방향 그대로다. 더 촘촘해 곡선이 부드럽고, 상한 2000점 안에서 충분하다.

- 예상 크기: 서명 1개 ≈ 300~800점. 정수 좌표라 JSON에서 점당 ~10 byte → **3~8 KB**.
- 최악값(2000점)이라도 ~20KB로, 악의적 대용량은 상한이 막는다.

✅ **2:1 종횡비 강제 — v4에서 해결됐다.** v2 시점엔 `grep aspectRatio` → 0건이라 "호출부가 붙여야 한다"고 인계했는데, mobile-dev가 그걸 받아 **컴포넌트 내부로 옮겼다**(`SignatureCanvas.kt:69` / `SignatureView.kt:33`, 상수 `internal`). **호출부는 폭만 정하고 비율을 덧붙이지 않는다.** 자세한 경위는 §2.1 v4 노트.

⚠️ **`MAX_STROKES`는 100이다.** v2 문서에 64로 적었던 건 그 시점 코드를 읽은 것이고, mobile-dev가 내 첫 권고("짧은 획을 많이 쓰는 서명이 잘리면 안 된다")를 받아 100으로 올렸다. 실측 최악값 20,222자로 32KB 상한 여유 38% 유지된다. **이 값은 캡처 상한이라 모바일 소유** — 서버는 32KB 바이트 길이로만 막으므로 계약과 무관하다.

### 2.6 가장자리 클리핑 방지 — **인셋** (v3 신설)

**문제**: 좌표가 `0` / `GRID`면 획의 중심이 캔버스 경계에 정확히 놓여 **굵기의 절반이 잘린다.** 서명은 보통 가로로 길어 사용자가 실제로 가장자리까지 그린다. 입력·상세 **양쪽 다** 발생한다. (2026-08-03 pm-lead 지적. 내 Lovable 프리뷰에도 같은 버그가 있어 함께 고쳤다.)

**해법: 그릴 수 있는 영역(drawable rect)을 컴포넌트 경계에서 안쪽으로 들이고, 좌표 수집과 렌더가 그 사각형을 똑같이 쓴다.**

```
컴포넌트 박스        W × H           (2:1)
인셋            p = 실제 획 굵기 / 2   (4변 동일)
drawable rect   (p, p) ~ (W-p, H-p)
좌표 수집       손가락 위치를 drawable rect 기준으로 정규화 → 0..GRID
렌더            0..GRID 를 drawable rect 위에 매핑
```

- **입력 패딩만 하면 안 된다** — 손가락이 보이지 않는 벽에 눌려 획이 가장자리에서 납작해진다.
- **렌더 인셋만 하면 안 된다** — 그리는 위치와 보이는 위치가 어긋난다.
- **둘을 같은 `p`로 묶어야** 손가락 위치 = 획 위치가 유지되면서 잘리지도 않는다. pm-lead가 짚은 *"입력과 렌더가 같은 규칙을 써야 한다"*가 이 뜻이다.

| 항목 | 값 |
|---|---|
| 인셋 `p` | **실제 사용 중인 획 굵기 ÷ 2** |
| 왜 정확히 절반인가 | `StrokeCap.Round`가 끝점에서 모든 방향으로 굵기/2 만큼 번진다. 그 값이 곧 필요한 여백이고, **더 줄 이유도 없다** |
| 입력(W≈335) | 굵기 3.0dp → `p` = 1.5dp |
| 상세(W≈158) | 굵기 1.5dp(최소값 clamp) → `p` = 0.75dp |

> ⚠️ **`p`는 비율(0.9%)이 아니라 clamp까지 끝난 *실제* 굵기에서 뽑아라.** 상세 박스는 0.9%가 1.42dp라 최소값 1.5dp로 올라간다. 비율로 계산하면 인셋이 모자라 여전히 잘린다.

**부수 효과(허용)**: 4변을 균등하게 들이면 drawable rect가 정확한 2:1에서 살짝 벗어난다 — 입력 2.006, 상세 2.019. **최대 0.6% 세로 차이**로 지각 한계 아래이며, 두 화면 모두 같은 규칙을 쓰므로 왕복 시 서명이 어긋나 보이지 않는다. 정확한 2:1을 지키려고 축별로 다른 인셋을 주면 세로 여백이 부족해져 원래 문제로 돌아간다.

### 2.7 ⚠️ 구현 주의 (선례 0건 영역)

1. **스크롤 충돌** — §1.2(b). 캔버스는 **스크롤 영역 밖 고정 슬롯**에 둔다. 부득이 스크롤 안에 넣어야 하면 캔버스가 드래그를 완전 소비해야 하고, 그 경우 캔버스 영역에서 화면 스크롤이 죽는다는 걸 감수해야 한다.
2. **획 수집 중 리컴포지션** — 진행 중인 획을 `State`에 매 point마다 넣으면 프레임마다 전체 리컴포지션이 돈다. 진행 획은 `mutableStateListOf` 또는 별도 `Canvas` 레이어로 분리 권고.
3. **iOS 실기 검증** — spec 리스크 §129. 지연·좌표 정확도는 실기로만 확인된다. 시뮬레이터 마우스 드래그는 손가락과 다르다.

---

## 3. T-D3 — 상세 화면 서명 렌더

현재 Lovable `challenge-detail.tsx`는 `h-12` 박스 안에 **"나의 서명 ✓" 텍스트**다. 실제 벡터 렌더로 교체한다.

### 3.1 레이아웃

> **v7 (2026-08-03) — 상세도 공용 `ContractCard` + `footer`를 쓴다.** 아래 도식은 Lovable 원본 구조(`내기` + 구분선 + 서명 2-up)를 옮긴 것인데, `ContractCard`가 §5 공용 컴포넌트가 되기 전에 쓰인 문서다. mobile-dev 제안대로 **맹세 화면들과 같은 카드**를 쓰고 서명 2-up을 `footer` 슬롯에 넣는다.
>
> **왜**: 이 화면의 목적이 *"내가 서명한 그 계약서를 다시 본다"*인데 서명할 때 본 카드와 **다른 모양**이면 같은 문서로 안 읽힌다. 그리고 §4.6에서 확립한 원칙 — **계약서에 당사자의 의무가 빠지면 문서로서 성립하지 않는다** — 을 상세에도 일관되게 적용하면 미션 행이 있어야 한다. 원본 구조를 `ContractCard` 안에 그대로 넣으면 `내기`가 두 번 나오기도 한다.
>
> **§3.1 도식의 요소는 하나도 빠지지 않는다** — `내기` / 구분선 / `서명` 라벨 / 2-up / `spacedBy 12.dp` / 박스 아래 4.dp 라벨 / `secondary` bg + R12 전부 그대로고, **미션 2행과 마감이 더해질** 뿐이다.
>
> ⚠️ **v7.1 정정 — 미션 중복은 현재 존재하지 않는다. 아래는 조건부 항목이다.**
>
> v7 초안에 *"상세엔 이미 Missions 섹션이 있어 미션이 두 번 나온다"*고 적었는데 **사실이 아니었다.** 그건 **Lovable `challenge-detail.tsx`의 구조**고, 실제 `:feature:challenge:detail`에는 Missions 섹션이 없다(실측: `ChallengeDetailContract` + `SignatureColumn` + Loading/Error가 전부). 인증 뱃지·사진·"인증하기" CTA는 **카메라 인증 feature 몫**이고 spec이 비범위로 못박았다.
>
> **→ 지금 미션은 화면에 한 번만 나온다. 이번 회차 시각 검증 항목에서 제외한다** (확인할 중복이 없다).

#### 📌 Missions 섹션 도입 시 적용할 것 (카메라 인증 feature 인계)

Missions 섹션(미션 + 인증 상태 뱃지 + 인증 사진 + "인증하기" CTA)이 상세에 들어오면 **그때 미션이 화면에 두 번 나온다.** 그 시점의 판단을 미리 못박아 둔다.

- **중복을 그대로 둔다.** 두 블록의 **일이 다르다** — Missions는 *지금 무엇을 해야 하는가*(행동), 계약서는 *무엇을 걸고 맹세했는가*(기록). **계약서는 자기완결적이어야** 문서이고 실제 계약서도 조건을 다시 적는다.
- 🔴 **계약서에서 미션을 빼는 방향으로 고치지 마라.** 그건 §4.6에서 고친 결함(계약서에 당사자 의무가 없음)을 그대로 되살린다. 답답하면 **줄일 대상은 Missions 섹션의 라벨**이다.

> 이 항목을 "현재 상태 설명"이 아니라 **조건부 인계**로 둔 이유: 지금 상태로 적어두면 다음에 읽는 사람이 **없는 중복을 찾는다.** (mobile-dev 지적)

아래는 v7 이전 원본 구조 기록. Lovable의 "영혼의 맹세" 섹션 헤더(`FileText` 아이콘 + "영혼의 맹세")는 **보존**한다.

```
📄 영혼의 맹세                      ← bold14 + FileText 18.dp(primary)
┌──────────────────────────────┐
│ 내기                          │  ← medium10 / onSurfaceVariant
│ 진 사람이 커피 사기 ☕          │  ← bold14
│ ──────────────────────────── │  ← 1.dp outline, 위아래 12.dp
│ 서명                          │  ← medium10 / onSurfaceVariant
│ ┌──────────┐  ┌──────────┐   │  ← 2-up, spacedBy 12.dp
│ │ (벡터 획) │  │ (벡터 획) │   │  ← weight(1f) + aspectRatio(2f)
│ └──────────┘  └──────────┘   │
│      나          민수          │  ← medium12 / onSurfaceVariant, 중앙
└──────────────────────────────┘
```

| 항목 | 값 |
|---|---|
| 서명 박스 | `weight(1f)` + `aspectRatio(2f)` + `secondary` bg + `RoundedCornerShape(12.dp)` |
| 획 | §2.2와 동일 규칙 — **굵기 = 박스 폭의 0.9%**(≈1.4dp), `primary` |
| 라벨 | 박스 **아래** 4.dp, `medium12` `onSurfaceVariant`, 중앙 정렬. 문구는 §3.3 (관점 판정 결과에 따라 달라진다) |
| 두 박스 간격 | 12.dp |

> 라벨을 박스 **안**(Lovable)에서 **밖**으로 뺐다. 안에 두면 서명 획과 텍스트가 겹친다.

### 3.2 미서명 상태 — 새로 필요해진 상태

챌린저는 **생성 시** 서명하고 상대는 수락 시 서명하므로, `PENDING` 구간에는 **한쪽만 서명된 계약서**가 존재한다. Lovable에는 이 상태가 없다.

| 상태 | 조건 | 시각 |
|---|---|---|
| 서명됨 | 서명 데이터 있음 + 디코드 성공 | 벡터 획 렌더 |
| **미서명** | `signedAt == null` | dashed border 1.5.dp `onSurfaceVariant.copy(alpha=0.30f)` + 중앙 **"서명 대기 중"** `medium12` `onSurfaceVariant`. 배경은 동일 `secondary` |
| **디코드 실패** (v5 신설) | `signedAt`은 있는데 서명 문자열 파싱 실패 | 같은 dashed 시각 + 문구만 **"서명을 불러오지 못했어요"** |

> **디코드 실패를 "서명 대기 중"으로 그리면 거짓말이다.** 저 사람은 서명했다. 서버가 저장한 문자열을 그대로 돌려주는 한(`@JsonRawValue`) 나오지 않을 상태지만, **나오면 숨기지 않고 보이는 쪽이 맞다.**
>
> `datetime-model-migration`의 `Instant.DISTANT_PAST` 센티널이 **파싱 실패를 "이미 만료된 카드"로 위장**했던 것과 같은 계열이다. 실패를 정상 상태로 위장하면 발견이 늦는다. (mobile-dev 제기, 채택)
>
> **시각을 미서명과 같은 dashed로 두는 이유**: 둘 다 "여기 서명이 안 보인다"는 같은 사실을 말한다. 시각 언어를 나누면 사용자가 배울 게 하나 더 늘고, 정작 구분이 필요한 건 **문구**뿐이다.

- 빈 상태 시각을 **입력 캔버스의 빈 상태(§2.3)와 같은 언어**(dashed + 안내 문구)로 맞췄다. 사용자가 "여기 아직 안 채워졌다"를 한 번 배우면 두 화면에서 통한다.
- `SignatureView`는 **읽기 전용** — `pointerInput` 없음, 클릭 무반응.

---

### 3.3 관점을 모를 때 — 라벨을 실명으로 떨어뜨린다 (v7 신설)

API는 `challenger` / `opponent`를 **역할 그대로** 준다(계약서 화면이라 양쪽을 다 그리기 때문). 화면이 `"나"` / `"{상대}"`로 뒤집으려면 **내 `userId`로 어느 쪽이 나인지 판정**해야 하는데, 출처인 `UserInfoRepository`가 CACHE_FIRST라 **캐시가 비었고 네트워크가 실패하면 판정이 불가능하다.**

**그때 챌린저를 "나" 자리에 놓으면 계약서를 잘못 읽게 만든다** — 라벨은 "나"인데 실제로는 상대 서명이다. §3.2에서 합의한 *"`signedAt`이 있는데 '서명 대기 중'으로 그리면 거짓말"*과 **정확히 같은 종류의 거짓말**이다. 관점을 모를 땐 **역할 그대로 보여주는 게 정직하다** — 계약이 역할 기준으로 주는 것도 같은 이유다.

| 상황 | 왼쪽 라벨 | 오른쪽 라벨 |
|---|---|---|
| 내가 challenger | `"나"` | `{opponent 닉네임}` |
| 내가 opponent | `"나"` | `{challenger 닉네임}` |
| **판정 불가** | `{challenger 닉네임}` | `{opponent 닉네임}` |

- **배치는 challenger 왼쪽 고정.** 라벨만 바뀐다 — 위치까지 흔들면 같은 계약서가 진입할 때마다 달라 보인다.
- **스낵바 없음.** 사용자가 할 수 있는 게 없고 화면은 정상 동작한다. 조용히 정직한 표기로 떨어지면 된다.
- **계약서 행 라벨도 함께 떨어져야 한다.** 서명은 실명인데 행은 `"나의 미션"`이면 같은 카드 안에서 앞뒤가 안 맞는다 → `ContractCard(myMissionLabel: String = "나의 미션")`. 판정 불가일 때 `"{challenger 닉네임}의 미션"`. **기본값이 있어 다른 두 화면은 무변경**이다.

### 3.4 `isFinalized`는 그리지 않는다

**뱃지 등 별도 표시를 만들지 않는다.** 상대 서명은 수락+서명이 원자적으로 처리될 때만 채워지므로 **양측 서명이 다 그려진 것 ⟺ `isFinalized`**다. 같은 사실을 두 번 말하는 셈이라 중복이고, 명세에 없는 시각 요소를 발명할 이유가 없다.

---

## 4. 화면 명세 — `OathScreen` (상대) / `OathStep` (챌린저 맹세 step)

두 화면은 **미션 입력 유무만 다르다.** 공통 골격을 `mode`로 분기한다.

### 4.1 레이아웃 (위→아래)

```
← 영혼의 맹세                        ← TopBar 56.dp, bold18
[■■■]                               ← (챌린저만) progress 3칸
영혼의 맹세 📜                        ← bold20
서명하면 수정 불가! 진짜야?            ← medium14 / onSurfaceVariant
                                    ← 24.dp
┌────────── 계약서 카드 ──────────┐
│        영혼의 맹세               │  ← bold18 / primary, 중앙
│       SOUL CONTRACT             │  ← medium10 / onSurfaceVariant, 중앙
│ ───────────────────────────── │  ← 1.dp outline
│ 대결 상대            민수        │
│ 민수의 미션    아침 6시 기상하기   │  ← 상대 화면에만 (§4.6)
│ 나의 미션      책 30페이지 읽기   │  ← 상대 화면: 입력값 실시간 반영
│ 내기             커피 사기       │  ← primary
│ 마감             오늘 자정       │
│ ───────────────────────────── │  ← 1.dp outline
│ 도윤의 서명                      │  ← medium12 / onSurfaceVariant
│ ┌────────┐                     │  ← SignatureView, weight 0.5 + 2:1
│ │ (획)   │                     │     (상대 화면에만 — §4.4)
│ └────────┘                     │
└─────────────────────────────┘
                                    ← 16.dp
나의 미션                            ← (상대만) medium12
[ 예) 책 30페이지 읽기        ]      ← (상대만) 48.dp 입력
                            0/100
                                    ← 16.dp
서명란                               ← medium12 / onSurfaceVariant
┌─────────────────────────────┐
│                             │     ← 캔버스 335 × 168.dp
└─────────────────────────────┘
                    ↻ 다시 그리기     ← 획 ≥ 1일 때만
                                    ← 24.dp
[      ✓ 맹세한다! 🔥      ]         ← 52.dp full-width primary
```

### 4.2 계약서 카드 — Lovable step2 구조·문구 **보존**

| 요소 | Lovable | Compose |
|---|---|---|
| 카드 | `glass-card p-5 space-y-4` | `Surface(surface, 1.dp outline, RoundedCornerShape(16.dp))` + `padding(20.dp)` + `spacedBy(16.dp)` |
| 타이틀 | `text-lg font-extrabold text-gradient-fire` "영혼의 맹세" | `bold18` + **`colorScheme.primary`** — fire-gradient는 단색 primary 근사(colors.md §1.4 기존 정책) |
| 서브 | `text-[10px] text-muted-foreground` "SOUL CONTRACT" | `medium10` + `onSurfaceVariant` (§6.1 참조) |
| 구분선 | `border-b border-border pb-3` | `HorizontalDivider(1.dp, outline)` |
| 4행 | `flex justify-between text-sm` | `Row(SpaceBetween)` — 라벨 `medium14`/`onSurfaceVariant`, 값 `bold14`/`onBackground` |
| 내기 값 | `font-semibold text-primary` | `bold14` + **`primary`** |
| CTA | `size="full"` + `Check` 18 + "맹세한다! 🔥" | `IconTextButton(Filled)` 52.dp / radius 12.dp / `Icons.Filled.Check` 18.dp / `bold14` |

**문구 전부 Lovable 원문 유지**: "영혼의 맹세 📜" / "서명하면 수정 불가! 진짜야?" / "SOUL CONTRACT" / "여기에 서명하세요" / "맹세한다! 🔥".

### 4.3 상대 화면 고유 — 미션 입력이 계약서에 실시간 반영

입력 필드를 **계약서 카드 밖 아래**에 두고, 입력값이 **카드의 "나의 미션" 행에 실시간 반영**된다.

- **왜**: 계약서는 "확정된 내용"이고 입력은 "작성 행위"라 섞으면 안 된다. 대신 반영을 실시간으로 두면 **내가 서명할 문서가 눈앞에서 완성되는** 경험이 된다 — "무를 수 없는 약속"이라는 컨셉과 맞는다.
- 미입력 시 계약서 "나의 미션" 행은 `"—"` `onSurfaceVariant`.
- 입력 박스 명세는 [`challenge-create/design.md §1.3`](../challenge-create/design.md) **완전 동일** (48.dp / `secondary` / 12.dp radius / `medium14` / trim 기준 카운터 + 100자 하드캡).

### 4.4 챌린저 서명을 먼저 보여준다 (상대 화면 한정)

**채택.** pm-lead가 선택지로 전한 건이고, 검토 결과 넣는 게 맞다.

**왜**: 챌린저는 생성 시점에 이미 서명했으므로 `PENDING` 구간의 계약서는 **반쯤 채워진 문서**다. 빈 계약서에 혼자 서명하는 것과, **먼저 발을 들인 사람의 서명이 보이는 상태로** 서명하는 것은 무게가 다르다 — "무를 수 없는 약속"이라는 컨셉의 핵심이 여기다. `challenge-detail`의 양측 서명 표시와도 시각적으로 이어진다.

**T-D1 결정을 강화한다**: 이 정보는 다이얼로그였다면 절대 못 넣는다. 전체 화면 승격의 근거가 하나 늘었다.

**배치**: **계약서 카드 안, 맨 아래 구분선 뒤.** 챌린저 서명은 *계약 문서의 일부*이므로 카드 안이고, 내 서명 캔버스는 *작성 행위*이므로 카드 밖이다 — §4.3의 미션 입력과 같은 기준.

| 항목 | 값 |
|---|---|
| 라벨 | `"{챌린저닉네임}의 서명"` `medium12` `onSurfaceVariant` |
| 렌더 | `SignatureView` — `fillMaxWidth(0.5f)` + `aspectRatio(2f)` (≈158×79.dp, **상세 화면과 같은 크기**) |
| 정렬 | 좌측 정렬. 절반 폭이라 "이미 끝난 것"으로 읽히고 내 캔버스(전체 폭 168.dp)와 경쟁하지 않는다 |
| 미서명 케이스 | **없다.** 챌린저 서명은 이 화면의 진입 전제다 |

> **챌린저 맹세 step에는 넣지 않는다.** 그 시점엔 상대가 아직 서명할 수 없어 빈 칸만 생긴다.

#### 대가 — 진입 시 조회 1회 (v5 정정)

챌린저 서명은 **`/challenges/received` 목록 응답에 없다**(`ReceivedChallengeItem`에 서명 필드 없음). `GET /challenges/{id}`가 필요하다.

> **v5 (2026-08-03) — 내가 적었던 "부분 렌더" 완화책을 폐기한다.** 그 완화책은 *"미션·내기·마감은 홈에서 들고 온 목록 항목에 있으니 즉시 그리고 서명 자리만 로딩"*이었는데, **전제가 내 T-D1 결정으로 이미 죽어 있었다.** mobile-dev가 짚었다.
>
> **왜 죽었나**: 다이얼로그였을 땐 홈 위에 떠 있어 목록 항목을 그대로 넘겨받았다. 그런데 **전체 화면 별도 라우트로 승격**하면서 사정이 달라졌다 — 이 앱의 라우트는 `Route.Challenge.Detail(val challengeId: Long)`처럼 **id만 싣는 게 관례**다(실측: 나머지 라우트는 전부 payload 없는 `data object`). 목록 8필드를 라우트에 실어 백스택에 직렬화하면 **라우트가 도메인 모델에 묶인다.**
>
> **부분 렌더가 오히려 나빴던 지점** (mobile-dev 지적, 내가 못 본 것): 홈 목록 데이터는 낡을 수 있다. 그 사이 챌린저가 취소했거나 마감이 지났으면 **부분 렌더는 이미 없는 챌린지의 계약서를 멀쩡히 다 그려놓고** 서명 자리만 돈다. 사용자는 **서명을 다 그리고 나서야** 실패를 만난다. 이게 완화책의 진짜 대가였다.
>
> 덧붙여 `deadlineText`("5시간 32분")는 홈 매핑 시점에 1회 측정한 **상대시간**이라, 라우트로 실어 나르면 진입 시점에 이미 낡아 있다.

**확정: `GET /challenges/{id}` 한 번으로 전부 받고 진입 시 화면 로딩 1회를 감수한다.**

- 되돌리기 비용이 이 방향이 더 싸다 — 나중에 라우트에 필드를 실어 부분 렌더로 바꾸는 건 가능하고, 반대는 더 비싸다.
- **§4.4 본체(챌린저 서명 노출)는 그대로다.** 폐기한 건 완화책이지 결정이 아니다.

### 4.6 챌린저 미션 행 (v6 — 문서 누락 정정)

**계약서 카드에 `"{챌린저닉}의 미션"` 행이 있다.** 상대는 **자기가 무엇에 맞서 서명하는지** 알아야 한다. 계약서인데 한쪽 당사자의 의무가 빠져 있으면 문서로서 성립하지 않고, §4.4에서 챌린저 **서명**은 보여주기로 해놓고 그 서명이 보증하는 **내용**이 없으면 앞뒤가 안 맞는다.

| 화면 | `opponentMission` | 결과 |
|---|---|---|
| 위저드 맹세 step (챌린저) | `null` | **행 미노출** — Lovable step2와 동일. 상대가 아직 안 썼으니 맞다 |
| 상대 맹세 화면 | 챌린저 미션 | `"{챌린저닉}의 미션"` 행 노출 |
| 챌린지 상세 | 양쪽 다 | 둘 다 노출 |

- **위치**: "대결 상대" 바로 아래 — 상대 정보끼리 붙이고 그 아래 "나의 미션".
- **시각**: 나머지 행과 동일(라벨 `medium14`/`onSurfaceVariant`, 값 `bold14`/`onBackground`). 신규 토큰 0건.
- **라벨**: `AcceptChallengeDialog`의 `missionLabelText`("도윤의 미션")를 그대로 계승.

> **`null`일 때 `"—"`가 아니라 행을 통째로 빼는 이유** — 두 부재의 의미가 다르다.
> - `myMission`의 `"—"` = *"네가 지금 쓰는 중이라 아직 비었다"* → **자리를 지켜야** 곧 채워질 곳으로 읽힌다.
> - `opponentMission`의 부재 = *"이 시점엔 존재할 수 없다"* → 빈 자리를 남기면 **뭔가 빠진 것처럼** 보인다.

**경위 (기록)**: §4.2가 Lovable **step2 카드 구조를 보존**하기로 했는데 step2는 **챌린저 시점**이라 이 행이 없는 게 맞았다. 그 카드를 상대 화면에 재사용하면서 **비어 있어야 할 이유가 사라진 자리가 그대로 빈 채** 넘어왔다. Lovable `oath.tsx`에는 실제로 5행으로 구현해 뒀는데 **design.md §4.1 도식과 §5 props만 4행에 머물러** 있었다 — 프리뷰가 문서보다 정확했던 경우다. (mobile-dev 발견)

### 4.5 상태

| 상태 | 조건 | 화면 |
|---|---|---|
| **로딩** | 진입 직후 `GET /challenges/{id}` 대기 | 화면 전체 로딩. 계약서 내용이 없으면 그릴 것도 없다 |
| **조회 실패** | 조회 에러 | **재시도 버튼이 있는 에러 화면.** 반쯤 그려진 계약서에 서명하게 두는 것보다 정직하다 |
| 기본 | 조회 성공 | 계약서 렌더(챌린저 서명 포함), 캔버스 빈 상태, CTA **비활성** |
| 입력 중 | (상대) 미션 입력 | 계약서 행 실시간 갱신. IME 올라옴 |
| 서명 중 | 캔버스 드래그 | 안내 문구·dashed 제거, 획 실시간 |
| CTA 활성 | 서명 ≥ 1획 **AND** (상대면) 미션 trim 1~100자 | `primary` |
| 로딩 | 제출 in-flight | CTA 인디케이터 18.dp + 캔버스 `alpha 0.5f` 비활성 + 입력 `readOnly` + **뒤로가기 차단** |
| 실패 | 코드 무관 | 스낵바(서버 `message`) + **화면 유지, 서명·입력 보존.** ⚠️ challenge-create의 다이얼로그는 실패 시 닫았지만, **여기선 닫지 않는다** — 공들여 그린 서명을 버리는 건 비용이 너무 크다 |
| 성공 | `is_finalized = true` | 화면 pop → 홈 복귀 → 받은 도전장 + 진행 중 목록 갱신 → 스낵바 "맹세가 완료됐어요 🔥" |
| **이탈 (dirty)** | 미션 입력이 있거나 획 ≥ 1인 상태에서 뒤로가기 / 시스템 백 | **확인 다이얼로그** — 나가면 작성 중인 내용이 사라진다고 알리고 [나가기] / [계속 작성]. spec **T-M3a** |
| **이탈 (clean)** | 아무것도 입력·서명하지 않음 | **확인 없이 즉시 나감.** 들어왔다 그냥 나가는 경우까지 물으면 순수 마찰이다 |

---

## 5. Compose 컴포넌트 spec

```kotlin
// :core:ui — 저장 포맷. 3곳(create 맹세 step / oath / detail)이 공유한다.
@Serializable
data class SignatureStrokes(val strokes: List<List<SignaturePoint>>)

@Serializable
data class SignaturePoint(val x: Float, val y: Float)   // [0,1] 정규화, 소수 3자리
```

```kotlin
// :core:ui/components/ — 입력
@Composable
fun SignaturePad(
    strokes: SignatureStrokes,
    onStrokesChange: (SignatureStrokes) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    emptyHint: String = "여기에 서명하세요",
)
```
- 호출부는 **폭만** 정한다(`fillMaxWidth()` 등). `aspectRatio(2f)`·획 굵기·인셋은 **컴포넌트가 소유**하는 불변식이라 덧붙이지 않는다(§2.1 v4).
- 상태는 **호출부(ViewModel) 소유** — 내부 `remember` ❌ (`AcceptChallengeDialog`의 `myMission` hoisting과 같은 이유).
- 정규화·솎아내기·clamp는 **컴포넌트 내부 책임**. 호출부는 정규화된 결과만 받는다.
- `@Preview` 4종: 빈 상태 / 1획 / 3획 / `enabled = false`

```kotlin
// :core:ui/components/ — 렌더 전용
@Composable
fun SignatureView(
    strokes: SignatureStrokes?,      // null 또는 빈 목록 = 미서명
    modifier: Modifier = Modifier,
    emptyHint: String = "서명 대기 중",
)
```
- `aspectRatio(2f)`. `pointerInput` 없음.
- `@Preview` 2종: 서명됨 / 미서명

```kotlin
// :core:ui/components/
@Composable
fun ContractCard(
    opponentNickname: String,
    opponentMission: String?,        // null 이면 행 자체를 그리지 않는다 (§4.6)
    myMission: String?,              // null 이면 "—"
    betContent: String,
    deadlineText: String,
    modifier: Modifier = Modifier,
    myMissionLabel: String = "나의 미션",   // 관점 판정 불가 시 "{challenger}의 미션" (§3.3)
    footer: (@Composable ColumnScope.() -> Unit)? = null,  // 상세의 서명 2-up (§3.1)
)
```

- **세 화면이 이 카드 하나를 공유한다** — 챌린저 맹세 step / 상대 맹세 화면 / 챌린지 상세. `footer`와 `opponentMission`·`myMissionLabel` 기본값으로 차이를 흡수한다.

```kotlin
// :core:ui/components/ — 읽기 전용 서명 칸 껍데기 (v7)
@Composable
fun SignatureSlot(
    strokes: SignatureStrokes?,   // null 또는 빈 목록 = 미서명
    emptyHint: String,            // "서명 대기 중" / "서명을 불러오지 못했어요" (§3.2)
    modifier: Modifier = Modifier,
)
```

---

## 6. 사용 토큰

**신규 토큰 0건.** 색·타이포·radius·spacing 전부 기존 슬롯.

- **색**: `background` / `surface` / `outline` / `secondary` / `primary`(잉크·강조·CTA) / `onPrimary` / `onBackground` / `onSurfaceVariant`
- **alpha 변형**(호출부 책임, 슬롯화 ❌ — home-feed §5 정책): `onSurfaceVariant.copy(alpha = 0.30f)`(dashed border), `alpha = 0.5f`(비활성)
- **타이포**: `bold20`(화면 제목) / `bold18`(TopBar·계약서 타이틀) / `bold14`(계약 값·섹션 헤더·버튼) / `medium14`(서브·계약 라벨·입력·빈 캔버스 안내) / `medium12`(필드 라벨·서명 라벨·카운터·다시 그리기) / `medium10`(SOUL CONTRACT·상세 내기 라벨)
- **radius**: 카드 16.dp / 캔버스·서명 박스·버튼·입력 12.dp
- **spacing**: 화면 좌우 20.dp / TopBar 56.dp / 캔버스 168.dp(2:1) / CTA 52.dp / 블록 16.dp / 제목↔본문 24.dp / 서명 박스 간 12.dp
- **아이콘**: `Icons.AutoMirrored.Filled.ArrowBack` 20 / `Icons.Filled.Check` 18 / `Icons.Filled.Refresh` 14 / `Icons.Filled.Description` 18(상세 `FileText` 대응)

### 6.1 신규 토큰을 피한 지점 1건 (기록)

Lovable "SOUL CONTRACT"는 `text-[10px]` **weight 미지정** = `font-normal` → tokens.md §5.3 정책상 **Light 매핑**이므로 정확히는 `light10`이다. tokens.md §5.2는 *"`light10`/`bold10`은 첫 사용처가 생기면 추가한다"*고 적어 뒀지만, **"신규 토큰 0건 유지" 지시를 우선해 기존 `medium10`으로 근사**했다.

- 영향: 10sp에서 Light↔Medium 차이는 거의 안 보인다.
- `light10` 도입은 tokens.md에 이미 등재된 후속 항목이므로, 그때 이 사용처를 함께 옮기면 된다. **backlog 기존 항목에 흡수 — 신규 등재 불요.**

---

## 7. ⚠️ 확인 필요

| # | 항목 | 본안 | 결정 주체 |
|---|---|---|---|
| 1 | **서명 중 이탈 시 확인 다이얼로그** | ✅ **결정 완료 — dirty일 때만 확인** (spec T-M3a). 내 본안("확인 없이 나감")은 **채택되지 않았다.** pm-lead 근거 둘: (1) **손실이 서명만이 아니다** — 이 화면엔 미션 입력도 있어 타이핑한 텍스트가 함께 날아간다. 서명만이면 5초지만 둘이면 다르다. (2) 내가 근거로 든 *"오버레이를 하나로 줄인다"*의 원래 근거는 challenge-create에서 **705 다이얼로그가 code 분기 불가로 애초에 불필요**했던 것이지 "오버레이는 적을수록 좋다"가 아니다 — **근거를 뺀 채 형태만 옮기면 원칙이 미신이 된다.** 타당한 지적이라 수용한다. | 결정 완료 |
| 2 | `AcceptChallengeDialog` 삭제 | 삭제 + `OathScreen` 대체. 교체분 **분리 보고** | 결정 완료(§1.3) |
| 3 | 점 하나 = 유효 서명 | 수용 기준대로 **획 ≥ 1**만 검사. 바운딩 박스 하한은 넣지 않음 | pm-lead(§2.4) |
| 4 | `:feature:challenge:oath` 모듈 신설 | 신설 본안. `create`에 합치는 대안 있음(§1.4) | mobile-dev |
| 5 | 캔버스 높이 96 → 168.dp | 손가락 서명 최소 높이. 2:1 비율의 귀결 | 디자이너 |
| 6 | 획 굵기 = 폭의 0.9% | 고정 dp면 상세에서 뭉갠다(§2.2) | 디자이너 |
| 7 | 솎아내기 임계 0.005 | 제안값. 실기에서 각져 보이면 낮춘다 | mobile-dev 실기 후 회신 |
| 8 | 크기 상한 획 ≤100 / 점 ≤2000 | 디자인 권고. 확정은 api-contract | backend-dev |
| 9 | Undo(획 단위 취소) 미도입 | "다시 그리기"만 | 디자이너 |
| 10 | 실패 시 화면 유지(서명 보존) | challenge-create 다이얼로그(실패 시 닫음)와 다름. 서명 손실 비용이 커서 의도적 차별 | 결정 완료(§4.4) |

---

## 8. mobile-dev 강조 사항

1. **캔버스는 스크롤 영역 밖 고정 슬롯**(§1.2b, §2.6-1). 이게 전체 화면 승격의 핵심 이유다.
2. **종횡비 2:1은 입력·렌더 공통 불변식**(§2.1). 한쪽만 바꾸면 저장된 서명이 왜곡된다.
3. **획 굵기는 폭 비례(0.9%)**, 고정 dp ❌ (§2.2).
4. **`strokes`는 ViewModel 소유**, `SignaturePad` 내부 `remember` ❌ (§5).
5. **정규화·솎아내기·clamp는 컴포넌트 내부**에서 끝낸다 — 왕복 무손실 테스트(spec T-M1)의 대상이 여기다.
6. **실패 시 화면을 닫지 마라**(§4.4). challenge-create 다이얼로그와 의도적으로 다르다.
7. **`AcceptChallengeDialog` 삭제는 교체이지 회귀가 아니다** — 분리 보고(§1.3).
8. **progress 2칸 → 3칸.** challenge-create design.md §1.1에 *"영혼의 맹세 feature 진입 시 3칸으로 복귀"*라고 적어둔 그 시점이다. Lovable과 다시 일치한다.
9. **솎아내기 임계값이 시각에 영향**을 준다(§2.5). 실기에서 각져 보이면 낮추고 나에게 알려달라.

---

## 9. Lovable 변경

```
new:      src/lib/signature.ts            (저장 포맷 + 상수 — 모바일 :core:ui 모델에 대응)
new:      src/components/SignaturePad.tsx (SignaturePad 입력 + SignatureView 렌더 전용)
new:      src/routes/oath.tsx             (상대방 맹세 화면 — 전체 화면, T-D1)
modified: src/routes/challenge-new.tsx    (step2 서명란 placeholder → 실제 캔버스, CTA 활성 조건)
modified: src/routes/challenge-detail.tsx (서명 텍스트 → 벡터 렌더 + 미서명 상태)
modified: src/routeTree.gen.ts            (/oath 라우트 등록 — vite build 로 자동 재생성)
```

- `src/styles.css` **무변경** — 신규 토큰 0건.
- **검증**: `npx tsc --noEmit` **0 error** / `npx eslint`(변경 5파일) **0 problem** / `npx vite build` **성공**.
- 상수·타입을 `src/lib/signature.ts`로 분리한 이유: 직렬화 포맷은 컴포넌트가 아니라 **데이터 계약**이다. 모바일에서도 `:core:ui`의 `SignatureStrokes`(모델)와 `SignaturePad`(컴포넌트)가 같은 이유로 나뉜다.
- **`SignaturePad`와 `SignatureView`가 렌더 경로(`StrokePaths`)를 공유**한다 — 입력 화면과 상세 화면의 서명이 반드시 같아 보이도록 강제하는 장치다. 모바일도 같은 구조를 권한다.

> Lovable 프리뷰는 **실제로 그려진다.** 마우스/터치로 서명 → "다시 그리기" → CTA 활성까지 `/challenge-new`(step2)와 `/oath`에서 확인 가능. `/challenge-detail`은 목 서명이 벡터로 렌더된다.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-08-03 | **v1 최초 작성** — T-D1(상대 맹세 화면 **전체 화면 승격**, 근거 4건 + 이전 다이얼로그 결정과의 관계 정리) / T-D2(서명 인터랙션 — 2:1 비율 고정, 폭 비례 굵기, 정규화·솎아내기 직렬화, 빈/그리는 중/완료 상태) / T-D3(상세 벡터 렌더 + **미서명 상태 신설**) / T-D4(컴포넌트 3종 props, 토큰 종합). 착수 전 실측 5건 기록(드로잉 선례 0건, 다이얼로그 이미 `verticalScroll`). 신규 토큰 0건 — 회피 지점 1건(`light10`→`medium10`) §6.1 기록. ⚠️ 확인 필요 10건 §7. | design-bridge |
| 2026-08-03 (7차) | **v7.1 — 내 "미션 중복" 지적이 사실관계 오류였다** (mobile-dev 정정). v7에서 *"상세엔 이미 Missions 섹션이 있어 미션이 두 번 나온다"*고 적었는데, 그건 **Lovable `challenge-detail.tsx`의 구조**고 실제 `:feature:challenge:detail`엔 Missions 섹션이 **없다**(실측: `ChallengeDetailContract` + `SignatureColumn` + Loading/Error가 전부). 인증 뱃지·사진·CTA는 카메라 인증 feature 몫이고 spec이 비범위로 못박았다. **→ 현재 미션은 한 번만 나온다. 이번 회차 시각 검증 항목에서 제외.** 다만 **판단 자체는 유효**하므로 "Missions 섹션 도입 시 적용" **조건부 인계 항목**으로 재배치했다 — 중복은 그대로 두고, 🔴 **계약서에서 미션을 빼는 방향으로 고치지 마라**(§4.6 결함 재발). 현재 상태 설명으로 두면 **다음에 읽는 사람이 없는 중복을 찾는다**는 mobile-dev 지적을 반영. ⚠️ 원인: **Lovable 구조를 구현된 화면인 것처럼 서술했다** — 프리뷰와 모바일 구현이 갈릴 수 있다는 걸 확인 안 하고 적은 것. | design-bridge |
| 2026-08-03 (6차) | **v7 — 상세 화면 §3 조정 3건** (mobile-dev 제기, 3건 다 채택). (1) **상세의 맹세 블록을 공용 `ContractCard` + `footer`로 통일.** §3.1 도식은 `ContractCard`가 공용 컴포넌트가 되기 전 문서라 상세에만 별도 카드가 생기는 구조였다. 서명할 때 본 카드와 다르면 *"내가 서명한 그 계약서"*로 안 읽히고, §4.6 원칙(계약서에 당사자 의무가 빠지면 문서로 성립 안 함)을 상세에도 일관 적용하면 미션 행이 있어야 한다. ⚠️ **대가로 미션이 화면에 두 번 나온다**(별도 Missions 섹션과 중복) — 두 블록의 일이 다르고(행동 vs 기록) **계약서는 자기완결적이어야** 하므로 수용하되, 답답하면 줄일 대상은 **계약서가 아니라 Missions 섹션 라벨**이라고 명시. 시각 검증 항목으로 등재. (2) **§3.3 신설 — 관점 판정 불가 시 라벨을 실명으로.** `UserInfoRepository`가 CACHE_FIRST라 캐시 비었고 네트워크 실패면 "내가 누구인지" 판정이 안 되는데, 그때 챌린저를 "나" 자리에 놓으면 **계약서를 잘못 읽게 만든다** — §3.2의 "서명 대기 중 거짓말"과 같은 계열. 배치는 challenger 왼쪽 고정, **라벨만** 전환. 계약서 행도 함께 떨어지도록 `ContractCard(myMissionLabel)` 추가(기본값 있어 다른 화면 무변경). (3) **§3.4 — `isFinalized` 미표시 확정.** 상대 서명은 원자 처리라 **양측 서명 렌더 ⟺ `isFinalized`**로 동치, 뱃지는 중복. mobile-dev가 명세에 없는 시각 요소를 발명하지 않고 물어본 판단이 옳다. §5에 `footer`/`myMissionLabel`/`SignatureSlot` 반영. 신규 토큰 0건. | design-bridge |
| 2026-08-03 (5차) | **v6 — 계약서 카드의 챌린저 미션 행 누락 정정** (mobile-dev 발견). 상대 맹세 화면 계약서에 `"{챌린저닉}의 미션"` 행이 빠져 있었다 — **계약서인데 한쪽 당사자의 의무가 없고**, §4.4에서 챌린저 서명은 보여주면서 **그 서명이 보증하는 내용**은 안 보여주는 모순이었다. 삭제 대상인 `AcceptChallengeDialog`엔 있던 정보라 **교체가 정보를 줄이는** 결과이기도 했다. 원인: §4.2가 Lovable **step2 카드 구조를 보존**하기로 했는데 step2는 **챌린저 시점**이라 그 행이 없는 게 맞았고, 그 카드를 상대 화면에 재사용하면서 **비어 있어야 할 이유가 사라진 자리가 그대로 빈 채** 넘어왔다. → §4.6 신설 / §4.1 도식 5행 / §5 `ContractCard`에 `opponentMission: String?` 추가. `null`이면 **행 자체 미노출** — `myMission`의 `"—"`와 의미가 다르다(전자는 "지금 쓰는 중이라 빈 것"이라 자리를 지켜야 하고, 후자는 "이 시점엔 존재할 수 없는 것"이라 빈 자리가 결손으로 보인다). ⚠️ **Lovable `oath.tsx`엔 이미 5행으로 구현돼 있었고 design.md만 4행에 머물렀다** — 프리뷰가 문서보다 정확했던 경우. 신규 토큰 0건. | design-bridge |
| 2026-08-03 (4차) | **v5 — 내 §4.4 완화책 폐기 + 상세 디코드 실패 상태 신설** (mobile-dev 제기, 둘 다 채택). (1) **"부분 렌더" 완화책 폐기.** *"목록 데이터로 계약서를 즉시 그리고 서명 자리만 로딩"*이 성립하려면 화면이 목록 항목을 손에 들고 있어야 하는데, **내 T-D1 전체 화면 승격으로 그 전제가 이미 죽어 있었다** — 별도 라우트는 `Route.Challenge.Detail(challengeId: Long)`처럼 id만 싣는 게 이 앱 관례다(실측: 나머지 라우트 전부 payload 없는 `data object`). 게다가 부분 렌더는 **홈 목록이 낡았을 때 이미 없는 챌린지의 계약서를 다 그려놓고 사용자가 서명을 마친 뒤에야 실패시킨다** — 내가 못 본 대가다. → `GET /challenges/{id}` 한 번으로 받고 진입 시 로딩 1회 감수. §4.5의 "조회 중/실패" 2행을 **전체 로딩 / 재시도 에러 화면**으로 교체. **§4.4 본체(챌린저 서명 노출)는 유지** — 폐기한 건 완화책이지 결정이 아니다. (2) **§3.2에 "디코드 실패" 상태 신설** — `signedAt`은 있는데 파싱 실패한 경우를 "서명 대기 중"으로 그리면 **거짓말**이다(저 사람은 서명했다). 같은 dashed 시각 + 문구만 "서명을 불러오지 못했어요". `datetime-model-migration`의 `DISTANT_PAST` 센티널이 파싱 실패를 "만료된 카드"로 위장했던 것과 같은 계열. | design-bridge |
| 2026-08-03 (3차) | **v3 — 가장자리 클리핑 방지 §2.6 신설** (pm-lead 지적). 좌표 `0`/`GRID`가 캔버스 경계에 정확히 놓여 획 굵기의 절반이 잘리는 문제. **drawable rect를 실제 획 굵기의 절반만큼 4변 인셋하고, 좌표 수집과 렌더가 같은 인셋을 쓴다** — 입력 패딩만 하면 손가락이 보이지 않는 벽에 눌리고, 렌더 인셋만 하면 그리는 위치와 보이는 위치가 어긋난다. 인셋은 **clamp까지 끝난 실제 굵기**에서 뽑아야 한다(비율 0.9%로 계산하면 최소값 1.5dp로 올라가는 작은 박스에서 모자란다). 부수 효과로 drawable rect가 정확한 2:1에서 최대 0.6% 벗어나는 점 명시(지각 한계 아래, 두 화면 동일 규칙이라 왕복 시 어긋나지 않음). **Lovable 프리뷰도 같은 버그가 있어 함께 고쳤고, 그 과정에서 별도 렌더 버그 1건을 추가 발견·수정** — `y`가 `[0,1]`인데 SVG `viewBox` 높이가 `0.5`라 서명 아래쪽이 박스 밖으로 나가고 있었다(`y * 0.5` 누락). `StrokePaths`가 `<svg>`까지 소유하도록 정리해 입력·렌더가 viewBox·인셋·굵기를 **구조적으로 공유**하게 했다. | design-bridge |
| 2026-08-03 (2차) | **v2 — 설계 입력 반영 + T-M1 구현 대조 후 초안 정정.** (1) **§4.4 신설 — 상대 맹세 화면에 챌린저 서명을 먼저 보여준다**(pm-lead 선택지 제공 → 채택). 계약서 카드 **안** 맨 아래, 절반 폭 `SignatureView`. 근거: 먼저 발을 들인 사람의 서명이 보이는 상태로 서명하는 것과 빈 계약서에 혼자 서명하는 것은 무게가 다르다 — 컨셉의 핵심. **T-D1 전체 화면 결정을 강화**(다이얼로그였다면 못 넣는 정보). 대가로 `GET /challenges/{id}` 왕복 1회 + Loading 상태가 생기는 것을 명시하고, 부분 렌더 + 조회 실패 시 블록 생략(graceful degradation)으로 완화. (2) **§2.5 직렬화를 T-M1 구현값으로 교체** — 내 초안(float 소수 3자리 / 임계 0.005)을 버리고 `GRID = 1000` **정수 양자화** / `MIN_POINT_DISTANCE = 3` / `MAX_POINTS = 2000` / `MAX_STROKES = 64` 채택. 정수는 정밀도가 소수 3자리와 동일하면서 왕복 무손실을 **비트 단위로** 보장한다(수용 기준이 요구하는 바). (3) **⚠️ `aspectRatio` 강제가 코드에 0건**임을 확인 — `SignatureCanvas`가 의도적으로 호출부에 위임한 것이라 맹세·상세 화면이 `aspectRatio(2f)`를 반드시 붙여야 한다고 경고 추가. (4) step 번호 표기를 `step3` → **"맹세 step"**으로 통일 (Lovable/spec은 0-indexed `step2`, 내 문서는 3번째 의미의 `step3`이라 같은 화면을 두 이름으로 부르고 있었다). | design-bridge |
