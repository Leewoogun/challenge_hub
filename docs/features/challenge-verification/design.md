# Design — challenge-verification (T-M4 챌린지 상세 재구성)

> 🔴 **폐기 경고 — 이 문서의 재제출·캐시 서술은 더 이상 사실이 아니다.**
>
> - **재제출 = 전면 거부(`code=700` `이미 인증을 완료했어요`)** → **폐기.** 현행은
>   **`last-write-wins`** — 마감 전까지 무제한 교체, 마지막 등록본이 최종이다.
> - **재제출 재시도 전 status 선행 조회(회복 절차)** → **소멸.** 그냥 다시 올린다.
> - **사진 캐시 `max-age=86400`** → **`no-cache` + ETag/304.**
>
> 개정: [verification-photo-replace](../verification-photo-replace/spec.md) (2026-09-02).
> 🔴 **정본은 [api-contract.md](./api-contract.md) 와 [change-log.md](./change-log.md) 다.**
> 아래 본문은 2026-08 시점 기록으로 보존하며, **계약으로 인용하지 마라.**


- **디자인 소스**: `challenge-design/oathbound-challenges` (`.claude/config/repos.json` → `design.export_dir`)
- **참조 route**: `src/routes/challenge-detail.tsx` (201줄, 전체가 이번 범위)
- **대조 route**: `src/routes/challenge-new.tsx` (§4.4 계약서 카드 이형 판정 근거)
- **토큰 원본**: `src/styles.css` → 카탈로그 [`docs/design-system/tokens.md`](../../design-system/tokens.md) · [`colors.md`](../../design-system/colors.md)
- **교체 대상 화면**: `feature/challenge/detail/src/commonMain/kotlin/com/lwg/challenge/feature/challenge/detail/screen/ChallengeDetailScreen.kt`
- **스냅샷 일시**: 2026-08-24 23:24:32
- **선행 문서**: [spec.md §4 T-M4](./spec.md) · [api-contract.md §4](./api-contract.md)

> 값을 이 문서에 복붙하지 않는다. 색·타이포·radius의 실제 값은 위 카탈로그가 단일 출처이고,
> 여기서는 **어떤 의미 토큰을 어디에 쓰는지**만 지정한다.

---

## §0 이 문서의 위치 — 왜 지금 design.md 가 생겼나

[spec.md §5](./spec.md) 는 *"디자인이 없다 — design-bridge 를 팀에서 제외한다"* 로 시작했다.
그 판단은 **촬영/인증 화면(Verify)에 대해서는 지금도 유효하다** — Lovable 에 카메라 route 가 0건이다.

**챌린지 상세는 다르다.** 2026-08-24 사용자 기획 판단 3건(① 양측 인증 사진을 상세에서 통합 확인
② 미션 나/상대 가독 분리 ③ 남은 시간 표기)이 **`challenge-detail.tsx` 에 이미 전부 들어 있음**이
확인돼 그 디자인을 정본으로 채택했다. 이 문서는 그 정본을 Compose 관점으로 옮긴 것이다.

🔴 **이 문서가 다루지 않는 것**: 촬영 화면(T-M1)은 여전히 디자인 대기다. mobile-dev 가
`:core:designsystem` 토큰과 기존 화면 패턴으로 구현하고, 디자인이 나오면 교체한다.

---

## §1 화면 구성 분해

### §1.0 골격

Lovable 은 `app-container`(max-width 430px) 안에 sticky header + `px-5 space-y-4` 본문을 둔다.
네이티브에서는 컨테이너 폭 제약이 무의미하므로 무시하고, **좌우 gutter 20dp(`px-5`) / 섹션 간격 16dp(`space-y-4`)**
두 값만 가져온다. 현행 화면이 이미 `padding(horizontal = 20.dp)` 라 gutter 변경은 없다.

```
ChallengeScaffold
├── topBar: ChallengeTopBar("챌린지 상세", onBack)   ← 변경 없음. Lovable sticky header 와 동치
└── content: Column(verticalScroll)                   ← 전체 스크롤
    ├── VsHeaderCard          §1.1
    ├── MissionCard(나)        §1.2
    ├── MissionCard(상대)      §1.3
    └── OathSummaryCard        §1.4
```

- 섹션 사이 `Arrangement.spacedBy(16.dp)`, 본문 상단 8dp(`mt-2`), 하단 32dp(`pb-8`).
- 🔴 **인증 CTA 가 스크롤 밖 하단 고정에서 "나의 미션" 카드 안으로 이동한다.** 현행
  `ChallengeDetailScreen.kt:97-108` 의 하단 고정 버튼은 **삭제**된다. 사유는 §1.2.
- 카드 4장 모두 Lovable `glass-card` = 배경 + 1dp 보더 + radius 16dp(`--radius-xl`) + card shadow.
  모바일은 기존 `ContractCard`/홈 `ChallengeCard` 선례를 따라 **`colorScheme.surface` 평면색**을 쓴다
  (§6.2 에 gradient 미적용 사유).

### §1.1 VS 헤더

- **참조**: `challenge-detail.tsx:85-108`
- **의도**: 이 화면이 *"누구 대 누구의, 언제까지인 대결"* 인지를 한 눈에 세운다. 현행 화면은 이 정보가
  계약서 카드의 `대결 상대` / `마감` **텍스트 행**에 묻혀 있었다.

레이아웃 — 카드 패딩 20dp(`p-5`), 내용 중앙 정렬.

```
Row(중앙 정렬, spacedBy 24dp)          ← gap-6
├── Column(spacedBy 8dp)   나 아바타 64dp + 라벨
├── Column                  Flame 28dp + "VS"
└── Column(spacedBy 8dp)   상대 아바타 64dp + 라벨
Row(중앙, spacedBy 6dp, top 16dp)      ← mt-4, gap-1.5
└── Clock 16dp + "남은 시간: N시간 M분"
```

| 요소 | 토큰 |
|---|---|
| 아바타 | 64dp 정사각, radius 20dp(`--radius-2xl`), 배경 `colorScheme.secondary` |
| 아바타 내용 | Lovable 은 이모지(😤/😏) — **도메인에 해당 필드가 없다.** §7-④ |
| 이름 라벨 | `typography.bold14` / `colorScheme.onBackground` |
| VS 불꽃 | `Icons.Filled.LocalFireDepartment` 28dp / `colorScheme.primary` |
| "VS" 텍스트 | `typography.bold12` / `colorScheme.primary`, 불꽃 아래 4dp |
| 남은 시간 | `Icons.Filled.Schedule` 16dp + `typography.medium14`, 둘 다 `colorScheme.warning` |

- **상호작용 없음.** 아바타 탭으로 프로필을 열지 않는다(프로필 화면 자체가 백로그).
- 홈 `ChallengeCard.HeaderRow` 가 이미 `Schedule` 아이콘 + `warning` 으로 남은 시간을 그린다
  (`ChallengeCard.kt:124-139`). **아이콘·색 선택이 두 화면에서 일치**하므로 그대로 간다.

### §1.2 나의 미션 카드

- **참조**: `challenge-detail.tsx:112-123`
- **의도**: 내가 **지금 해야 할 일**과 **그 자리에서 누르는 버튼**을 한 카드에 묶는다.

레이아웃 — 카드 패딩 16dp(`p-4`).

```
Row(SpaceBetween, 아래 8dp)
├── "나의 미션"  라벨
└── 상태 뱃지
Text  미션 본문
[상태에 따라] 인증 CTA  또는  내 인증 사진      ← top 16dp / 12dp
```

| 요소 | 토큰 |
|---|---|
| 라벨 | `typography.medium12` / `colorScheme.onSurfaceVariant` (Lovable `text-xs`) |
| 미션 본문 | `typography.bold16` / `colorScheme.onBackground` (Lovable `text-base font-bold`) |
| 상태 뱃지 | §2.1 |
| CTA | `IconTextButton(text="인증하기", icon=Icons.Filled.PhotoCamera)`, `fillMaxWidth`, 상단 16dp |
| 내 사진 | §1.3 사진 영역과 동일 규격, 상단 12dp |

🔴 **CTA 를 하단 고정에서 카드 안으로 옮기는 것이 이 카드의 핵심 변경이다.** 현행 주석은
*"계약서가 길어도 인증 액션이 스크롤에 밀려 사라지지 않도록 스크롤 밖에 고정한다"* 라고 그 반대를
근거로 적고 있다(`ChallengeDetailScreen.kt:96`). **그 우려는 재구성으로 해소된다** — 새 배치에서
"나의 미션" 카드는 VS 헤더 바로 다음이라 **진입 시 첫 화면에 들어온다.** 계약서는 아래로 내려갔다.
카드 안에 두면 *"어느 미션에 대한 인증인지"* 가 버튼과 붙어 있다는 이득도 함께 얻는다.

⚠️ **다만 검증 대상이다** — 미션 문구가 길거나 큰 폰트 스케일에서 CTA 가 첫 화면 밖으로 밀릴 수 있다.
mobile-dev 는 **긴 미션 + 큰 폰트 스케일 프리뷰**로 확인하고, 밀리면 리포트에 남긴다.

### §1.3 상대 미션 카드

- **참조**: `challenge-detail.tsx:125-136`
- **의도**: 상대가 **뭘 하기로 했고, 했는지, 증거가 뭔지**를 한 카드에 묶는다.
  구조는 §1.2 와 같고 **CTA 자리가 사진 영역**이라는 점만 다르다.

| 요소 | 토큰 |
|---|---|
| 라벨 | `"{상대 닉네임}의 미션"`, §1.2 라벨과 동일 |
| 사진 영역 | 높이 **160dp**(`h-40`), `fillMaxWidth`, radius 16dp(`--radius-xl`), 배경 `colorScheme.surfaceVariant` |
| 사진 자리 문구 | 중앙 정렬, `typography.medium14` / `colorScheme.onSurfaceVariant` |
| 사진 | `ContentScale.Crop` + 영역 radius 로 clip |

- Lovable 배경은 `bg-secondary/50`(secondary 50% 알파). 모바일은 **`surfaceVariant` 로 대체**한다 —
  surface 위에 secondary 50% 를 합성한 결과가 `surfaceVariant`(gray4)와 육안 구분이 안 되고,
  알파 합성을 도입하지 않는 쪽이 토큰이 깨끗하다. 계약서 내부 박스(`bg-secondary/30`)도 같은 대체를
  쓴다 — **두 박스는 서로 다른 카드에 있어 나란히 놓이는 일이 없으므로** 값이 같아도 무해하다.
- 🔴 **높이 160dp 고정.** 사진 종횡비에 따라 카드 높이가 들쭉날쭉하면 두 미션 카드의 리듬이 깨진다.
  로딩·에러·미인증 상태에서도 **같은 160dp 를 유지**해야 상태 전환 시 레이아웃이 튀지 않는다.
- **탭 상호작용은 정의되지 않았다.** §7-⑥.

### §1.4 영혼의 맹세 카드

- **참조**: `challenge-detail.tsx:140-170`
- **의도**: 서명까지 끝난 계약을 **참조용으로** 남긴다. 이제 화면의 주역이 아니다.

```
Row(spacedBy 8dp, 아래 12dp)
├── FileText 18dp (primary)
└── "영혼의 맹세"
Box(내부, 패딩 16dp, radius 16dp, 배경 surfaceVariant)
├── "내기" 라벨 + 내기 본문
├── "마감" 라벨 + 절대 마감 시각        ← 🔴 Lovable 에 없다. pm-lead 판정으로 존치 (§1.4.1)
├── Divider (1dp, outline) + 상단 12dp
└── "서명" 라벨 + Row(2열, spacedBy 12dp) { SignatureColumn × 2 }
```

| 요소 | 토큰 |
|---|---|
| 헤더 아이콘 | `Icons.Filled.Description` 18dp / `colorScheme.primary` |
| 헤더 텍스트 | `typography.bold14` / `colorScheme.onBackground` (Lovable `text-sm font-bold`) |
| 필드 라벨(내기·마감·서명) | `typography.medium10` / `colorScheme.onSurfaceVariant` (Lovable `text-[10px]`) |
| 내기 본문 | `typography.medium14` / `colorScheme.primary` |
| **마감 본문** | `typography.medium14` / `colorScheme.onBackground` — 내기와 달리 primary 강조를 주지 않는다. 이 카드에서 눈에 먼저 들어와야 하는 건 내기다 |
| 필드 간 간격 | 12dp (`space-y-3`) |
| 서명 하단 이름 | `typography.medium12` / `colorScheme.onSurfaceVariant`, 중앙 정렬, 상단 4dp |

🔴 **이 카드는 현행 `ContractCard` 를 그대로 쓸 수 없다.** 상세만 5행 중 3행을 잃는다:

| 현행 `ContractCard` 행 | 새 상세 화면에서의 행방 |
|---|---|
| 대결 상대 | VS 헤더의 아바타 + 이름으로 흡수 (§1.1) |
| 상대 미션 | 상대 미션 카드로 이동 (§1.3) |
| 나의 미션 | 나의 미션 카드로 이동 (§1.2) |
| **내기** | **남는다** |
| **마감** | **남는다** — ✅ pm-lead 판정 2026-08-24 (§1.4.1). Lovable 은 이 행을 없앴으나 되살린다 |

**`ContractCard` 를 고치면 안 된다.** 호출부가 3곳이고(`OathStep.kt:61` / `OathForm.kt:107` /
`ChallengeDetailScreen.kt:57`), 앞의 둘은 **서명하기 직전에 계약 전문을 검토하는 화면**이라 5행이
전부 필요하다. 파라미터 플래그로 행을 숨기는 방향도 아니다 — 화면별 분기가 공용 컴포넌트로 새어든다.
→ **상세 전용 컴포넌트를 새로 만든다** (§4.2).

✅ **이 이형은 디자이너 의도다 — 추측이 아니다.** `challenge-new.tsx:302-305` 는 여전히
`glass-card p-5` + **중앙 정렬 "영혼의 맹세" + "SOUL CONTRACT" 부제**(= 현행 `ContractCard`)를 쓰고,
`challenge-detail.tsx:141-144` 만 **좌측 정렬 아이콘 + 부제 없는 압축형**이다. 서명하는 순간은
격식을 갖추고, 그 뒤 참조는 가볍게 — 두 route 에서 일관되게 갈라져 있다.

#### §1.4.1 🔴 마감 행 존치 — Lovable 에서 의도적으로 벗어나는 유일한 지점

**pm-lead 판정 (2026-08-24)**: 절대 마감 시각을 이 카드에 **행으로 유지한다.**
VS 헤더는 상대 표기(`남은 시간: 5시간 32분`)를 전담하고, **절대 시각은 계약서 영역이 맡는다.**

근거: *"오늘 자정인지 내일인지"* 는 **계약 조건**이다. 상대 표기만으로는 그 조건을 복원할 수 없고
(`3시간`이 오늘 자정인지 내일 새벽인지 알 수 없다), 계약 조건을 보여주는 자리는 계약서 카드다.

🔴 **이 판정은 Lovable 디자인을 의도적으로 벗어난다.** `challenge-detail.tsx:145-149` 의 내부 박스는
`내기` 한 필드뿐이고 마감 행이 없다. **이 문서에서 정본을 따르지 않는 유일한 지점**이므로 명시해 둔다 —
디자이너가 나중에 이 화면을 다시 만들 때 *"왜 구현에 행이 하나 더 있나"* 로 되돌리지 않게 하기 위해서다.
확인 대상 표기는 유지하되(§7-⑤) **기본값은 존치**다.

##### 🔴 값 포맷 — 순진하게 그리면 **날짜가 하루 밀린다**

표기는 기존 `7/28 24:00` 관례를 따른다. **그런데 이 값을 만들 포맷터가 없다.** 실측 결과:

- `kstDeadlineHintText()`(`core/utils/.../KstDeadline.kt`)는 **`daysAhead: Int` 를 받는다** —
  사용자가 오늘/내일을 고르는 **생성 플로우 전용**이다. 기존 챌린지의 마감을 그리지 못한다.
- 상세 ViewModel 은 `deadline.toRelativeKoreanString(now)` 로 **상대 표기만** 만든다
  (`ChallengeDetailViewModel.kt:152`). 절대 표기 경로가 없다.

🔴 **그리고 `deadline` 을 그대로 월/일로 찍으면 하루 뒤가 나온다.** 계약 예시가
`challengeDate: "2026-08-03"` 에 `deadline: "2026-08-04 00:00:00"` 이다
([soul-oath/api-contract.md:95](../soul-oath/api-contract.md)) — 마감은 **익일 00:00(배타적 끝점)** 으로
온다. 순진하게 찍으면 `8/4` 가 되는데 **정답은 `8/3 24:00`** 이다. `KstDeadline.kt` KDoc 이 경고한
바로 그 혼란(*"'오늘'인데 왜 내일 날짜냐"*)이 이 경로에서 재발한다.

**권고**: `challengeDate`(응답에 이미 있다 — `ChallengeDetail.challengeDate: LocalDate?`)로 그린다.
`"{month}/{day} 24:00"` 이면 끝이고 **자정 롤오버 산술이 아예 없다.**
⚠️ **단 nullable 이다** — null 이면 `deadline` 에서 유도해야 하고, 그때 *"00:00 이면 전날 24:00"*
규칙이 필요하다. **mobile-dev 가 이 분기와 하루 밀림을 테스트로 고정하라** (§8).

---

## §2 상태 매트릭스

### §2.1 상태 뱃지 — 3종

Lovable `challenge-detail.tsx:115-117, 128-130` 에 PENDING·VERIFIED 2종이 있고, **FAILED 는 없다.**
그러나 [api-contract §4](./api-contract.md) 가 `status` 를 `PENDING`/`VERIFIED`/`FAILED` **3종**으로
내려주므로 UI 는 3종을 전부 그려야 한다.

✅ **셋 다 이미 구현돼 있다** — 홈 `ChallengeCard.statusVisualOf()`(`ChallengeCard.kt:216-232`):

| status | 색 | 라벨 | 아이콘 |
|---|---|---|---|
| `PENDING` | `colorScheme.warning` | 대기중 | `Icons.Filled.Schedule` |
| `VERIFIED` | `colorScheme.success` | 인증완료 | `Icons.Filled.CheckCircle` |
| `FAILED` | `colorScheme.error` | 실패 | `Icons.Filled.Cancel` |

**Lovable 과 완전 일치한다** — `bg-warning/10 text-warning` + `Clock` / `bg-success/10 text-success` +
`CheckCircle2`. 뱃지 규격(배경 accent 10% · 패딩 8×4 · `typography.medium10` · 아이콘 12dp · radius 10dp)도
Lovable(`px-2 py-1`, `text-[10px] font-semibold`, `rounded-lg`)과 맞는다.

> 미세 차이 2건, **둘 다 기존 값을 유지한다**: radius 는 Lovable 12dp(`rounded-lg`) ↔ 현행 10dp,
> 아이콘은 Lovable 10dp ↔ 현행 12dp. 홈에 이미 출시된 값이고, 컴포넌트를 공용화하면 두 화면이
> 자동으로 같아진다. 1~2dp 를 맞추자고 출시분을 건드릴 이유가 없다.

### §2.2 나의 미션 카드

CTA 노출 조건은 **두 값의 AND** 다 — 챌린지가 `IN_PROGRESS` 이고, **내 인증이 `PENDING`** 일 때만.

| 챌린지 status | 내 verification | 뱃지 | 카드 하단 |
|---|---|---|---|
| `IN_PROGRESS` | `PENDING` | 대기중 | **인증하기 CTA** |
| `IN_PROGRESS` | `VERIFIED` | 인증완료 | **내 인증 사진** (CTA 없음) 🔴 §2.4 |
| `IN_PROGRESS` | `FAILED` | 실패 | 없음 |
| 그 외(`COMPLETED` 등) | `VERIFIED` | 인증완료 | 내 인증 사진 |
| 그 외 | `PENDING`/`FAILED` | 각각 | 없음 |

🔴 **이것이 spec §4 T-M4-4 "버튼 게이트"의 해소다.** 현행 `ChallengeDetailUiState.Data.canVerify` 는
`status == IN_PROGRESS` 하나만 본다. KDoc 이 한계를 자백하고 있다 —
*"'내가 이미 인증했는지'는 아직 알 수 없어 항상 열어 두고, 중복 제출은 서버가 거부한다"*
(`ChallengeDetailState.kt:39-40`). §4 조회가 붙으면 그 정보가 생기므로 **알면서 여는 상태가 없어진다.**
[api-contract §3](./api-contract.md) 이 재제출을 **전면 거부**하는 이상, 눌러도 거부당할 버튼을
보여주는 것은 사용자를 실패로 안내하는 것이다.

### §2.3 상대 미션 카드

| 상대 verification | 뱃지 | 사진 영역(160dp 고정) |
|---|---|---|
| `PENDING` | 대기중 | `"아직 인증하지 않았어요"` — ⚠️ §7-② |
| `VERIFIED` | 인증완료 | 사진 (`photoUrl` non-null 보장 — 계약 §4) |
| `FAILED` | 실패 | `"인증하지 못했어요"` — ⚠️ §7-② |

사진 영역 자체의 하위 상태:

| | 표현 |
|---|---|
| 로딩 | 영역 유지 + `"불러오는 중..."` 또는 은은한 shimmer |
| 성공 | `ContentScale.Crop`, 영역 radius 로 clip |
| 실패(네트워크/404) | 영역 유지 + `"사진을 불러오지 못했어요"` + **재시도 가능** |

🔴 **실패 상태를 빈 박스로 두지 마라.** [mobile-report 16번](./mobile-report.md)이 지적한
`//` URL 조인 사고는 **정상 404 와 구분이 안 되게 조용히 실패**한다. 화면에 실패가 보여야 잡힌다.

### §2.4 🔴 내 인증 완료 상태 — Lovable 에 없다

**`challenge-detail.tsx` 는 "내가 아직 인증 안 함 + 상대는 인증함" 한 장면만 그린다.**
내가 인증을 마친 뒤 내 카드가 어떻게 보이는지는 **디자인이 존재하지 않는다.**

**제안 (상대 카드 패턴 미러링)** — 내 카드의 **CTA 자리를 상대 카드의 사진 영역과 동일한 규격으로
교체**하고, 뱃지를 `인증완료`(success)로 바꾼다. 규격·간격·문구를 §1.3 과 1:1로 맞춘다.

근거: ① 두 카드가 이미 같은 골격(라벨+뱃지+본문+하단 슬롯)을 공유한다 ② 양측 인증 사진을 **상세에서
통합 확인**하는 것이 이번 기획 판단 ①의 목적이므로, 내 사진만 다른 규격이면 비교가 어렵다
③ Compose 구현이 카드 1종의 슬롯 분기로 끝난다.

⚠️ **디자이너 확인 대상 (§7-①).** 채택 전까지는 제안 상태다.

### §2.5 🔴 부분 실패 — 이 화면은 더 이상 "부분 실패가 없는 화면"이 아니다

현행 `ChallengeDetailUiState` 는 이렇게 적고 있다 —
*"읽기 전용 화면이라 부분 실패가 없다 — 상세를 못 받으면 보여줄 계약서 자체가 없다"*
(`ChallengeDetailState.kt:28`). **`GET /challenges/{id}/verifications` 가 붙으면 이 전제가 깨진다.**
호출이 2개가 되고, 한쪽만 실패할 수 있다.

**제안**: 인증 조회만 실패하면 **화면 전체를 `Error` 로 떨어뜨리지 않는다.** VS 헤더·미션 본문·계약서는
상세 응답만으로 전부 그릴 수 있고, 그것만으로도 화면이 성립한다. **뱃지와 사진 영역만** 대체 상태
(`"인증 현황을 불러오지 못했어요"` + 재시도)로 낮춘다.

~~🔴 다만 그 경우 인증 CTA 는 숨긴다. 내 status 를 모르는 채로 버튼을 열면 §2.2 가 없애려던
"눌러도 거부당하는 버튼" 이 실패 경로로 되돌아온다. 재시도로 status 를 확인한 뒤에 연다.~~

🔴 **판정 전환 (2026-08-24, pm-lead — mobile-dev 반론 채택): 조회 실패 시 CTA 는 노출로 폴백한다.**
위 원안(숨김)은 구현 검토에서 뒤집혔다. 두 실패를 비교하면:

| 폴백 | 최악 시나리오 | 성격 |
|---|---|---|
| 숨김 (원안) | **아직 인증 안 한** 사용자가 일시적 네트워크 오류로 **인증 자체가 막힌다** | 주 액션 차단, 화면 안에서 회복 불가 |
| 노출 (채택) | **이미 인증한** 사용자가 다시 시도해 700(`이미 인증을 완료했어요`)을 받는다 | 서버가 정확히 답하는 기존 경로. 조회 실패 ∧ 기인증의 이중 조건이라 드물다 |

**막는 실패보다 중복 시도 실패가 낫다.** "눌러도 거부당하는 버튼"(§2.2)은 *정상 경로*에서 없애는
것이 목적이었고, *실패 경로*의 폴백까지 같은 규칙을 강요하면 더 나쁜 실패와 맞바꾸게 된다.
뱃지·사진 영역의 대체 상태(위 문단)는 원안 그대로 유지한다.

---

## §3 남은 시간 표기

- **참조**: `challenge-detail.tsx:104-107` — `Clock` 16px + `남은 시간: 5시간 32분`, warning 색.
- **형식**: `"남은 시간: "` + 상대 시간 문자열. 접두어는 **Lovable 문자열 그대로**다.

✅ **변환기가 이미 있다** — `core/utils/.../RelativeTimeFormat.kt` 의
`LocalDateTime.toRelativeKoreanString()` 이 정확히 이 표기를 만든다:

| 남은 시간 | 출력 |
|---|---|
| 1시간 이상 | `"5시간 32분"` (정각이면 `"2시간"`) |
| 1분~1시간 | `"32분"` |
| 1분 미만 | `"곧 마감"` |
| 이미 지남 | `"마감"` |

현행 상세 ViewModel 도 이미 이걸 써서 `deadlineText` 를 만든다(`ChallengeDetailViewModel.kt:105`).
**새로 만들 변환 로직이 없다.**

### §3.1 만료 후 표기 — Lovable 에 없다

`toRelativeKoreanString()` 은 마감이 지나면 `"마감"` 을 낸다. 그런데 **마감 직후~자정 배치 판정 전**
구간에서는 결과가 아직 없다 — [spec §1 제외](./spec.md)가 *"`FAILED` 전이는 시각 기준 배치이고
`:batch` 모듈은 `.kt` 파일 0개"* 라고 못박았다. 이 구간에 `"남은 시간: 마감"` 은 어색하다.

**제안**:

| 상황 | 표기 | 색 |
|---|---|---|
| 마감 전 | `남은 시간: 5시간 32분` | `warning` |
| 마감 후 · 결과 없음 | **`판정 대기 중`** (접두어 없이) | `onSurfaceVariant` |
| 결과 확정 | 이 자리에 결과 표시 — **판정 feature 소관, 이번 범위 밖** | — |

색을 `warning` 에서 내리는 이유: 마감 전 warning 은 *"서둘러라"* 는 행동 촉구인데, 마감 후에는
사용자가 할 수 있는 게 없다. 촉구색을 유지하면 없는 행동을 재촉하게 된다.

⚠️ **디자이너 확인 대상 (§7-③).**

### §3.2 🔴 분 단위 갱신 — 기존 주석과 정면으로 부딪힌다

spec §4 T-M4-1 이 **"분 단위 갱신"** 을 요구한다. 현행 ViewModel 은 정반대로 되어 있다:

> `// 시계는 매핑 시점 1회만 읽는다. Composable 에서 읽으면 recomposition 마다 값이 흔들린다.`
> (`ChallengeDetailViewModel.kt:78`)

**그 주석이 막으려던 것은 "갱신"이 아니라 "Composable 안에서의 시계 읽기"다.** 둘은 다르다 —
recomposition 마다 `nowKst()` 를 읽으면 갱신 주기가 렌더 사정에 좌우돼 값이 예측 불가능하게 흔들린다.

**따라서 갱신은 ViewModel 이 1분 주기로 state 를 새로 방출하는 방식이어야 한다.** Composable 은
받은 문자열을 그리기만 한다. 이러면 주석의 의도(시계 읽기 지점을 한 곳으로 고정)를 지키면서
분 단위 갱신을 얻는다. 🔴 **mobile-dev 는 이 주석을 새 동작에 맞게 갱신하라** — 고치지 않으면
다음 사람이 "1회만 읽는다"를 보고 티커를 버그로 오해한다.

---

## §4 Compose 매핑 가이드

### §4.1 그대로 쓰는 것 — 신규 제작 불필요

| 필요 | 기존 자산 | 위치 |
|---|---|---|
| 상단바 | `ChallengeTopBar("챌린지 상세")` | `:core:designsystem` — 변경 없음 |
| 화면 골격 | `ChallengeScaffold` | `:core:designsystem` |
| 인증 CTA | `IconTextButton(icon = Icons.Filled.PhotoCamera)` | `:core:designsystem` — 현행 호출 그대로, 위치만 이동 |
| 아바타 | `ProfilePlaceholder(size = 64.dp, shape = RoundedCornerShape(20.dp), textStyle = medium24)` | `:core:ui` — 파라미터로 전부 커버된다 |
| 서명 2열 | `SignatureColumn` | `feature/challenge/detail/component/` — 변경 없음 |
| 남은 시간 변환 | `toRelativeKoreanString()` | `:core:utils` |
| 뱃지 시각 규칙 | `statusVisualOf()` | 홈에 있음 → §4.3 으로 이전 |

### §4.2 신규 — `feature/challenge/detail/component/`

`component_placement_rule`(feature 전용 컴포넌트는 feature 모듈 `component/` 하위) 을 따른다.
이 넷은 **상세 화면 밖에서 쓸 데가 없다.**

| 컴포넌트 | 역할 |
|---|---|
| `VsHeaderCard` | §1.1. 아바타 2 + 불꽃 + 남은 시간 |
| `MissionCard` | §1.2/§1.3 **공용 1종.** 라벨 + 뱃지 + 미션 + **하단 슬롯**(`@Composable () -> Unit`) |
| `VerificationPhoto` | §1.3 사진 영역. 160dp 고정 + 로딩/실패/미인증 상태 포함 |
| `OathSummaryCard` | §1.4 압축 계약서. `ContractCard` 와 별개 |

🔴 **`MissionCard` 는 반드시 한 종류다.** 나/상대로 두 컴포넌트를 만들면 §2.4 미러링이 무너진다 —
내 카드에만 CTA→사진 전환이 있어서 갈라 놓고 싶어지지만, **그 차이는 하단 슬롯에 무엇을 넣느냐뿐**이다.
슬롯으로 처리하면 라벨·뱃지·타이포·간격이 구조적으로 같아진다.

### §4.3 신규 — `:core:ui` 로 승격

| 컴포넌트 | 사유 |
|---|---|
| `VerificationStatusPill` | 홈 `ChallengeCard.kt` 의 `private fun StatusPill` + `statusVisualOf()` 를 그대로 옮긴다. **홈과 상세 두 feature 가 쓰게 되는 순간 feature 전용이 아니다.** `ProfilePlaceholder`(4개 feature 사용)와 같은 선례 |

- 🔴 **이름 충돌 주의.** `:core:ui` 에 이미 `StatusPillBadge` 가 있다 — **점 + 텍스트 캡슐**이고
  로그인 화면의 `"SOUL CONTRACT"` 라벨용이다(`ChallengeSection.kt:51`). **전혀 다른 컴포넌트다.**
  같은 이름을 쓰거나 한쪽으로 통합하려 들면 로그인 화면이 깨진다.
- 상태 enum 은 **도메인 `VerificationStatus` 를 직접 받으면 된다** — `:core:ui` 는 이미
  `:domain:model` 에 의존한다(`core/ui/build.gradle.kts`, `SignatureView` 가 `Signature` 를 받는 선례).
  홈의 display 전용 `ChallengeVerificationStatus` 는 *":core:designsystem 이 도메인에 의존하지 않는다"* 가
  이유였는데, **`:core:ui` 에는 그 제약이 없다.** 승격하면서 홈의 내부 enum + 매핑 함수를 걷어낼 수 있다.
- ⚠️ 홈은 출시된 화면이다. 승격이 홈 회귀로 이어지지 않도록 **홈 프리뷰 2종을 확인**하고 리포트에 남겨라.
  회귀 위험이 크다고 판단되면 **홈은 두고 `:core:ui` 버전만 상세가 쓰는 것도 허용**한다 — 그 경우
  중복이 남으므로 백로그에 통합 항목을 등재한다.

### §4.4 원격 이미지 — Coil

✅ **실측 재확인 (2026-08-24)**: `AsyncImage` / `coil3` / `SingletonImageLoader` **사용처 0건**.
`gradle/libs.versions.toml:83-85` 카탈로그 등록만 있다. [spec §0.4](./spec.md) 그대로다 —
**인증 사진이 이 앱의 첫 원격 이미지다.**

디자인 관점에서 배선에 걸리는 요구는 둘뿐이고, 나머지(URL 조인·404 무캐시·인증 헤더)는
[spec §4 T-M4-5](./spec.md) 와 [mobile-report](./mobile-report.md) 소관이다:

1. **로딩·에러 상태가 눈에 보여야 한다** (§2.3). 빈 박스로 삼키지 않는다.
2. **영역 크기가 상태와 무관하게 160dp 로 고정**돼야 한다. 로드 완료 시 카드가 튀면 안 된다.

---

## §5 범위 밖 — 명시적으로 만들지 않는 것

| 항목 | 사유 |
|---|---|
| 🔥 **도발하기(Taunt) 섹션** | `challenge-detail.tsx:172-197` 에 **디자인이 있으나 별도 feature 다.** 빠른 문구 4종 + 직접 입력 + 전송 버튼. `taunt_messages` 엔티티는 있지만 이번 API 계약에 없다. **만들지 마라** |
| **아바타 실사진** | `profileImageUrl` 은 도메인·DTO·State 를 타고 화면까지 오지만 그리는 단계가 없다. 이번엔 **이니셜 placeholder 유지**. 활성화는 [백로그 "원격 이미지 로더 도입"](../../backlog.md) — Coil 배선이 끝나면 가능해지지만 [spec §0.4 범위 판정](./spec.md)이 *"세 화면을 동시에 바꾸면 회귀 표면이 넓어진다"* 로 미뤘다 |
| **아바타 이모지(😤/😏)** | Lovable 목데이터. 도메인에 필드가 없다. §7-④ |
| **결과 표시** | 승/패/무 — **판정 feature 소관** |
| **`FAILED` 전이** | 자정 배치. 이번 화면은 서버가 준 `FAILED` 를 **그리기만** 한다 |
| **사진 확대/저장/신고** | 디자인에 없다. §7-⑥ |
| **촬영 화면(T-M1)** | 디자인 자체가 없다. §0 |

---

## §6 신규 디자인 토큰 — **필요 없다**

기존 카탈로그와 전수 대조한 결과 **이번 화면이 요구하는 토큰이 전부 이미 있다.**

| 쓰임 | Lovable | 카탈로그 | 모바일 |
|---|---|---|---|
| 강조/불꽃/내기 | `--primary` | [colors.md §1.1](../../design-system/colors.md) | `colorScheme.primary` |
| 카드 표면 | `--card` | §1.2 | `colorScheme.surface` |
| 사진·계약 내부 박스 | `--secondary/50`, `/30` | §1.2 | `colorScheme.surfaceVariant` (§1.3 사유) |
| 아바타 배경 | `--secondary` | §1.3 | `colorScheme.secondary` |
| 보조 텍스트 | `--muted-foreground` | §1.2 | `colorScheme.onSurfaceVariant` |
| 보더/구분선 | `--border` | §1.4 | `colorScheme.outline` |
| 대기중/남은시간 | `--warning` | §1.5 | `colorScheme.warning` |
| 인증완료 | `--success` | §1.5 | `colorScheme.success` |
| 실패 | `--destructive` | §1.5 | `colorScheme.error` |
| radius 12/16/20 | `--radius-lg/xl/2xl` | [tokens.md §4](../../design-system/tokens.md) | `RoundedCornerShape(12/16/20.dp)` |
| 10/12/14/16sp | `text-[10px]`~`text-base` | tokens.md §5.2 | `medium10`/`medium12`/`bold14`/`bold16` 등 |

**타이포 슬롯도 신규 0건이다.** 이 화면이 쓰는 슬롯(`medium10`·`medium12`·`bold12`·`medium14`·
`bold14`·`bold16`·`medium24`)은 `Typography.kt` 에 전부 존재한다. tokens.md §5.2 가 사용처 발생 시
추가하라고 예약해 둔 `light10`/`bold10` 은 **이번에 필요하지 않다** — Lovable 의 `text-[10px]` 2건
(내기·서명 라벨)은 weight 미지정이라 §5.3 정책상 Light 매핑이 원칙이지만, **`ContractCard` 가 같은
라벨을 이미 `medium10` 으로 그리고 있어**(`ContractCard.kt:101`) 한 앱 안에서 같은 라벨이 두 굵기가
되는 쪽이 더 나쁘다. **`medium10` 으로 통일한다.**

⚠️ **미적용 상태로 남는 항목 2건** (이번 화면이 새로 만든 문제가 아니라 기존 미결):
- **`glass-card` 의 `--gradient-card`** — 카탈로그 tokens.md §2 에 `ChallengeTheme.brushes.card` 로
  매핑돼 있으나 **`ContractCard`·홈 `ChallengeCard` 둘 다 평면 `surface` 를 쓴다.** 이번 화면도
  그 선례를 따른다(§1.0). 그라데이션 카드로 갈지는 **전 화면 동시 결정 사안**이라 여기서 분기하지 않는다.
- **`--shadow-card`** — 동상. 기존 카드들이 shadow 없이 1dp 보더로 경계를 낸다.

---

## §7 ⚠️ 디자이너 확인 대상

| # | 항목 | 현재 처리 |
|---|---|---|
| ① | **내 인증 완료 후 카드 상태** — Lovable 에 장면이 없다 | 상대 카드 패턴 **미러링**으로 진행 (§2.4). 채택 여부 확인 필요 |
| ② | **상대 미인증(PENDING)/실패(FAILED) 시 사진 영역** — Lovable 은 VERIFIED 한 장면만 그린다 | 160dp 영역 유지 + 안내 문구로 진행 (§2.3). 영역을 아예 접을지 확인 필요 |
| ③ | **마감 후~판정 전 표기** — Lovable 에 없다 | `판정 대기 중` + `onSurfaceVariant` 제안 (§3.1) |
| ④ | **VS 헤더 아바타** — Lovable 이모지(😤/😏)는 목데이터이고 도메인에 필드가 없다 | **닉네임 이니셜 `ProfilePlaceholder`** 로 대체. 이모지를 실제 기능으로 도입할 계획이 있는지 확인 |
| ⑤ | **절대 마감 시각이 화면에서 사라진다** — 현행 계약서 `마감: 7/28 24:00` 행이 상대 표기로 대체된다 | ✅ **pm-lead 판정(2026-08-24)으로 해소** — `OathSummaryCard` 에 마감 행 존치 (§1.4.1). VS 헤더는 상대 표기 전담, 절대 시각은 계약서 영역 소관. Lovable 이 이 행을 없앤 것이 의도인지만 확인 |
| ⑥ | **인증 사진 탭 동작** — 확대/전체화면 여부가 정의되지 않았다 | **동작 없음**으로 진행 (범위 밖, §5) |
| ⑦ | **`FAILED` 뱃지** — Lovable 상세에 없다 | 홈 `ChallengeCard` 의 기존 표현(실패/`error`/`Cancel`)을 그대로 재사용 (§2.1) |

> ✅ **pm-lead 판정 (2026-08-24) — ①②③⑦ 은 위 제안값으로 진행 확정.** 판정/결과 feature 까지 미루지
> 않는다. **지금 이 화면을 만들려면 어차피 그 상태들을 그려야 하고**, 제안값이 전부 보수적이라
> 디자이너가 뒤집어도 교체 비용이 작다.
>
> 🔴 **표에서 지우지 마라.** 확인 대상 목록은 그대로 유지한다 — *"진행 확정"* 은 *"디자이너 확인이
> 끝났다"* 가 아니라 **확인을 기다리지 않고 구현한다**는 뜻이다. 목록을 지우면 나중에 이 값들이
> 디자이너가 승인한 값인지 우리가 정한 값인지 구분할 수 없게 된다.

---

## §8 mobile-dev 인계 체크리스트

- [ ] `ContractCard` 는 **건드리지 않는다** (§1.4). 상세 전용 `OathSummaryCard` 신설
- [ ] `OathSummaryCard` 는 **내기 + 마감 2행** (§1.4.1 pm-lead 판정). Lovable 은 마감 행이 없으니
      정본과 다르다는 점을 코드 주석에 남겨라 — 안 남기면 다음 사람이 "디자인에 없는 행"으로 지운다
- [ ] 🔴 **마감 절대 표기 포맷터 신설** — 기존 `kstDeadlineHintText()` 는 `daysAhead: Int` 를 받는
      생성 플로우 전용이라 **못 쓴다.** `deadline` 이 익일 00:00 으로 오므로 순진하게 찍으면 **하루 밀린다**.
      `challengeDate`(nullable) 우선 + null 시 유도 규칙, **하루 밀림을 테스트로 고정** (§1.4.1)
- [ ] 하단 고정 CTA 삭제 → `MissionCard` 하단 슬롯으로 이동 (§1.2). **긴 미션 + 큰 폰트 스케일 프리뷰 확인**
- [ ] `canVerify` 를 `IN_PROGRESS && myStatus == PENDING` 으로 좁히고 **`ChallengeDetailState.kt:39-40` KDoc 갱신** (§2.2)
- [ ] `ChallengeDetailState.kt:28` *"부분 실패가 없다"* 주석 갱신 (§2.5)
- [ ] `ChallengeDetailViewModel.kt:78` *"시계는 1회만 읽는다"* 주석 갱신 + 1분 티커는 **VM 방출** (§3.2)
- [ ] `MissionCard` 는 **1종 + 슬롯** (§4.2)
- [ ] `VerificationStatusPill` 승격 시 **`StatusPillBadge` 와 이름/역할 혼동 금지** (§4.3)
- [ ] 사진 영역 **160dp 고정**, 로딩·실패가 눈에 보일 것 (§2.3, §4.4)
- [ ] 프리뷰: 내 PENDING / 내 VERIFIED / 상대 PENDING / 상대 VERIFIED / 사진 로드 실패 / 인증조회 실패 / 마감 후
- [ ] 🔴 **이 문서와 코드가 갈라지면 그 자리에서 이 문서를 고친다** — soul-oath 에서 문서가 코드보다
      낡아 생긴 건이 3회다. 특히 §1 의 레이아웃 도식과 §4.2 의 슬롯 구조가 잘 낡는다

---

## 변경 이력

| 일시 | 변경 |
|------|------|
| 2026-08-24 23:24:32 | 최초 작성. `challenge-detail.tsx` 스냅샷 기준 T-M4 확장(상세 화면 재구성) 명세. 신규 토큰 0건 확인. 신규 컴포넌트 5종(feature 4 + `:core:ui` 승격 1). 디자이너 확인 대상 7건. |
| 2026-08-24 23:41:07 | **pm-lead 판정 반영.** (1) ⑤ 절대 마감 시각 → `OathSummaryCard` 에 **마감 행 존치** 확정. §1.4 도식·토큰표·행방표 갱신 + **§1.4.1 신설**(판정 근거 + Lovable 이탈 명시). (2) ①②③⑦ **제안값으로 진행 확정**, 확인 대상 목록은 존치(§7 각주 교체). (3) 🔴 **작성 시 오류 1건 자체 정정** — §1.4.1 초안이 *"기존 포맷터로 충분, 신규 불필요"* 라고 적었으나 실측 결과 `kstDeadlineHintText()` 는 `daysAhead: Int` 를 받는 생성 플로우 전용이라 **사용 불가**였고, `deadline` 이 익일 00:00 으로 와 **하루 밀림 위험**이 있음을 발견해 포맷터 신설 + 테스트 고정으로 정정. §8 체크리스트 3항 추가. |
