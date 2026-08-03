# Design — challenge-create (챌린지 신청)

- **디자인 소스**: `/Users/hwamulman/woogunProject/challenge/challenge-design/oathbound-challenges`
- **참조 route**: `src/routes/challenge-new.tsx` (수정), `src/routes/index.tsx` (수정), `src/routes/friends.tsx` (패턴 참조 — 무변경)
- **참조 컴포넌트**: `src/components/ChallengeCard.tsx`, `src/components/ui/button.tsx`, `src/components/ui/drawer.tsx`
- **전역 토큰**: [`docs/design-system/tokens.md`](../../design-system/tokens.md), [`colors.md`](../../design-system/colors.md)
- **상위 spec**: [spec.md](./spec.md) / [api-contract.md](./api-contract.md)
- **스냅샷 일시**: 2026-07-28 14:10
- **대상 화면**: 2 화면 + 1 오버레이
  1. 챌린지 생성 위저드 (신규 화면, 2 step)
  2. 홈 — 받은 도전장 섹션 (기존 `HomeScreen` 확장)
  3. 수락 시 미션 입력 (신규 **다이얼로그** — Lovable 대응 화면 없음, 본 문서에서 신규 설계)
- **신규 토큰**: **없음.** 전부 기존 `ChallengeColorScheme` / `ChallengeTypoGraphy` 슬롯으로 커버.

> **2026-07-28 14:40 개정 (v2)**: mobile-dev의 플랫폼 제약 지적 3건을 반영했다. (1) **수락 UI를 바텀시트 → 다이얼로그로 변경** (§3.1 재작성), (2) `DeadlineSelector`에 실제 마감 시각 부기 (§4.2), (3) 남은 시간 텍스트의 `" 남음"` 접미사 제거 — `toRelativeKoreanString()`이 `"곧 마감"`/`"마감"`도 반환해 문장이 깨졌다. 추가로 step1 입력 글자 수 카운터와 마감 임박 강조 규칙을 명세했다. 모듈 배치(§7)는 spec.md T-M3이 이미 정정돼 합의 완료.
>
> **2026-07-28 15:10 개정 (v3)**: api-contract `confirmed` 반영 — **모바일은 `code`(700/705)로 분기하지 않는다**(§공통 규약 2). 수락/거절 실패는 코드 무관 **스낵바 + 목록 무조건 재조회**. 이에 따라 (1) **`ChallengeErrorDialog`(§4.6) 폐기 — 만들지 않는다**, (2) §3.1의 v2 결정 근거 중 "705 다이얼로그가 어차피 필요"를 **무효 처리**(결론인 다이얼로그 채택은 나머지 근거로 유지), (3) §3.3 / §6 / §5.6의 700·705 분기 서술을 코드 무관 단일 경로로 정정.
>
> ⚠️ **v2와 v3은 §3 이후 본문까지 전부 반영돼 있다.** v2 직후 이 문서를 읽었다면 §3~§9가 v1로 보였을 수 있는데(편집 중 스냅샷), 현재 파일은 일관된 v3다.

---

## 0. 변경 요약 (Lovable working tree)

### 0.1 `src/routes/challenge-new.tsx` — T-D1

1. `DeadlineType` 타입 + `DEADLINE_OPTIONS` 상수 신설 (`TODAY` / `TOMORROW`). api-contract.md §DeadlineType 과 값 일치.
2. `deadlineType` state 추가 (기본값 `TODAY`).
3. **step1에 `DeadlineSelector` sub-component 신규** — 내기 입력 아래, "다음" 버튼 위. 2-up 토글 + **실제 마감 시각 부기**(`deadlineHint()`).
4. step2의 마감 행이 `"오늘 자정"` 하드코딩이었던 것을 `deadlineType` 바인딩으로 교체 (1줄).
5. **`MAX_LEN = 100` + `CharCounter` sub-component 신규** — 미션·내기 입력 아래 우측 `{n}/100`. `maxLength` 하드캡 동반.
6. "다음" 버튼 disabled 조건을 `!myMission || !bet` → **`trim()` 후 1~100자 검사**(`canProceed`)로 교체. 공백만 입력해도 통과하던 구멍을 막고 서버 검증(api-contract §1)과 규칙을 일치시켰다.

> ⚠️ **step2(영혼의 맹세)는 구조·문구·서명란 전부 그대로 보존했다.** 삭제·축소 없음. 위 4번은 step1 선택값이 계약서 요약에 반영되지 않으면 프리뷰가 자기모순이 되기 때문에 넣은 **표시 바인딩 1줄**이며, step2의 어떤 요소도 제거하지 않았다. 문제가 되면 되돌리기는 1줄이다.

### 0.2 `src/routes/index.tsx` — T-D2 / T-D3

1. `ReceivedChallenge` 타입 + `mockReceivedChallenges` 목데이터 신설. (빈 상태 프리뷰: 배열을 `[]`로 — `friends.tsx` 받은 요청 섹션과 동일 정책)
2. **`ReceivedChallengesSection` + `ReceivedChallengeCard` sub-component 신규** — StatsBar 아래, "진행 중인 챌린지" 위. 0건이면 섹션 자체 미노출.
3. **`AcceptChallengeDialog` sub-component 신규** — shadcn `dialog`(Radix) 기반. 수락 버튼 → 다이얼로그 오픈 → 내 미션 입력 → 확정. (v1의 `drawer`(vaul) 시트에서 변경 — §3.1)
4. `isFirstUser` 판정에 `receivedEmpty`를 AND 조건으로 추가. 받은 도전장이 1건이라도 있으면 빈 상태 문구를 `no_active_challenge` 톤으로 낮춘다 (§2.5 근거).
5. 진행 중 챌린지 블록 상단 여백을 조건부(`receivedEmpty ? mt-2 : mt-5`)로 — 섹션이 붙었을 때만 20px 간격.
6. `ReceivedChallenge.timeLeft`에서 `" 남음"` 접미사 제거 + `urgent: boolean` 필드 추가 (마감 임박 강조 — §2.3).

**검증**: `npx tsc --noEmit` 0 error. `npx eslint` — 본 작업 라인 0 error (남은 4건은 손대지 않은 기존 라인의 prettier 위반, HEAD에서도 동일).

---

## 1. 챌린지 생성 위저드 (`:feature:challenge:create`)

- **참조**: `src/routes/challenge-new.tsx`
- **의도**: "누구에게 → 무엇을 걸고" 두 판단만 순서대로 묻는다. 한 화면에 다 넣으면 친구 목록과 입력 폼이 뒤섞여 스크롤이 길어진다.
- **진입**: 홈 FAB(`Icons.Filled.Add`) 탭. (홈 빈 상태 카드의 "챌린지 만들기" CTA도 동일 목적지 — home-feed §2 기존 자산)

### 1.1 공통 골격

| 영역 | Lovable | Compose |
|---|---|---|
| TopBar | `sticky ... px-5 pt-safe pb-3`, `ArrowLeft` 20 + "새 챌린지" `text-lg font-bold` | `Surface(color = colorScheme.surface)` + `Row(height 56.dp, padding horizontal 20.dp)`. `IconButton(40.dp)` + `Icons.AutoMirrored.Filled.ArrowBack` 20.dp(`onBackground`) + `Text("새 챌린지", bold18, onBackground)`. 간격 `spacedBy(8.dp)` |
| Progress bar | `flex gap-1.5 mt-3`, 각 칸 `h-1 flex-1 rounded-full`, `i <= step ? bg-primary : bg-secondary` | `Row(spacedBy(6.dp), padding(horizontal 20.dp, top 12.dp))` + 칸마다 `Box(Modifier.weight(1f).height(4.dp).clip(CircleShape).background(...))`. 색: 도달 `primary` / 미도달 `secondary` |
| 본문 | `px-5 mt-4` | `Modifier.padding(horizontal = 20.dp)` + 상단 16.dp |
| 진입 애니메이션 | `animate-slide-up` | `AnimatedContent` 또는 `AnimatedVisibility + slideInVertically`. 선택 구현 |

> ⚠️ **Progress 칸 수: Lovable 3칸 / 모바일 2칸.** Lovable은 `[0,1,2]`로 step2(영혼의 맹세)까지 그린다. 이번 feature의 모바일 범위는 step0/step1뿐이므로 **모바일은 2칸**으로 렌더한다. 영혼의 맹세 feature 진입 시 3칸으로 복귀 — 그때 Lovable과 다시 일치한다.

### 1.2 step0 — 대결 상대 선택

- **레이아웃** (위→아래):
  1. 제목 "누구에게 걸래? 🔥" — `bold20` + `onBackground` (Lovable `text-xl font-extrabold`)
  2. 4.dp gap
  3. 서브 "대결 상대를 선택하세요" — `medium14` + `onSurfaceVariant`
  4. 24.dp gap
  5. `LazyColumn` — `FriendPickItem` × N, `verticalArrangement = spacedBy(8.dp)`
- **상호작용**: 항목 탭 → `selectedFriendId` 저장 + 즉시 step1 전환. 뒤로가기(TopBar ← 또는 시스템 백)로 step0 복귀 시 **이전 선택이 `selected = true`로 유지**된다.
- **상태**:

  | 상태 | 조건 | 화면 |
  |---|---|---|
  | `Loading` | `GET /api/v1/friends` 응답 대기 | 리스트 자리에 `CircularProgressIndicator`(primary) 중앙 |
  | `Data` | 친구 ≥ 1명 | 위 레이아웃 |
  | `Empty` | 친구 0명 | 카드 1개: `Icons.Filled.Group` 32.dp(primary) + `primary` 10% 배경 64.dp 원형자리 / "아직 친구가 없어요" `bold16` / "친구를 추가하고 챌린지를 걸어보세요" `medium12` `onSurfaceVariant` / CTA "친구 추가하기"(friends 검색 화면으로) — **`FriendsEmptyState` 재사용 불가**(`:feature:friends:list` internal). §7 참조 |
  | `Error` | 친구 목록 로드 실패 | 스낵바 + `Empty`와 동일 카드 (문구만 "친구 목록을 불러오지 못했어요" / CTA "다시 시도") |

- ⚠️ **전적("3승 2패")은 모바일에서 노출하지 않는다.** Lovable `mockFriends`에는 `record`가 있지만 `GET /api/v1/friends` 응답은 `{id, nickname, profileImageUrl, since}`뿐이다(friends 2차 api-contract §6). Lovable의 record는 `friend_records` 테이블이 실제로 붙는 후속 feature의 선행 비전이므로 **Lovable에서 지우지 않고 그대로 두되, 모바일 `FriendPickItem`은 전적 행을 렌더하지 않는다.**

### 1.3 step1 — 미션 · 내기 · 마감

- **레이아웃** (위→아래):
  1. 제목 "미션을 입력해 ✍️" — `bold20` + `onBackground`
  2. 4.dp gap
  3. 서브 "오늘 반드시 해낼 것을 적어" — `medium14` + `onSurfaceVariant`
  4. 24.dp gap
  5. 필드 `Column(verticalArrangement = spacedBy(16.dp))`:
     - **나의 미션** — 라벨 `medium12` `onSurfaceVariant` + 6.dp gap + 입력 박스
     - **내기 (진 사람이 해야 할 것)** — 동일 구조
     - **`DeadlineSelector`** (§4.2)
     - CTA "챌린지 걸기"
- **입력 박스 공통** (Lovable `bg-secondary rounded-xl px-4 py-3.5 text-sm`):

  | 항목 | 값 |
  |---|---|
  | 구현 | `BasicTextField` + `decorationBox` (Material3 `TextField`의 고정 높이·indicator 회피 — `FriendsSearchTopBar` 선례) |
  | 배경 / shape | `colorScheme.secondary` + `RoundedCornerShape(12.dp)` |
  | 높이 / 내부 패딩 | 48.dp / `horizontal = 16.dp` |
  | 입력 텍스트 | `medium14` + `onBackground` |
  | placeholder | `medium14` + `onSurfaceVariant` — 미션 "예) 오늘 운동 1시간 하기" / 내기 "예) 커피 사기" |
  | 커서 | `SolidColor(colorScheme.primary)` |
  | 포커스 | 2.dp `primary` border (Lovable `focus:ring-2 ring-primary`) |
  | 제약 | `singleLine = true`, 100자 하드캡, `imeAction = Next`(미션) / `Done`(내기) |

- **글자 수 카운터** (미션 / 내기 / 수락 다이얼로그 **공통 규칙**):

  | 항목 | 값 |
  |---|---|
  | 위치 | 입력 박스 **아래 우측 정렬**, 입력과 6.dp |
  | 포맷 | `"{trim된 길이}/100"` — 서버 검증이 trim 기준(api-contract §1)이라 카운터도 trim 기준으로 센다 |
  | 타이포 | `medium12` |
  | 색 (기본) | `onSurfaceVariant` |
  | 색 (100자 도달) | `warning` |
  | 초과 | **발생하지 않는다.** `maxLength = 100` 하드캡으로 입력 자체를 막는다 → `error` 색 미사용 |

- **CTA "챌린지 걸기"**:

  | 상태 | 시각 |
  |---|---|
  | 기본(활성) | `IconTextButton(Filled)` — `fillMaxWidth`, height 52.dp, radius 12.dp, `primary` bg / `onPrimary` content, 라벨 `bold14`, 아이콘 `Icons.Filled.SportsKabaddi` 18.dp |
  | 비활성 | `enabled = false`. 조건: `myMission.trim()` 또는 `bet.trim()`이 1~100자를 벗어남. Material3 기본 disabled alpha 사용(38%) |
  | 로딩 | `enabled = false` + 라벨 자리에 `CircularProgressIndicator(18.dp, color = onPrimary, strokeWidth = 2.dp)`. 중복 제출 차단 |

- **성공/실패 처리**:
  - 성공(`code = 200`) → 위저드 pop → 홈 복귀. 홈의 진행 중 목록은 갱신 불필요(생성물은 `PENDING`이라 `/challenges/active`에 안 잡힘 — api-contract §1).
  - 실패(코드 무관 — 친구 아님 / 본인 / 중복 / 길이 / 상대 없음) → **스낵바**(서버 `message` 그대로). 화면 유지, 입력값 보존. 모바일은 `code`를 구분하지 않는다(api-contract §공통 규약 2).
- ⚠️ **STT 마이크 버튼은 모바일에서 렌더하지 않는다.** Lovable step1의 입력 우측 마이크 버튼과 "마이크 버튼 누르고 말로 입력해도 돼" 힌트는 ADR-0006(클라이언트 STT SDK) 실행 후 붙는다. spec.md 비범위. **Lovable에서는 제거하지 않고 그대로 둔다.**

---

## 2. 홈 — 받은 도전장 섹션 (`:feature:home` 확장)

- **참조**: `src/routes/index.tsx` (수정 후), 패턴 원본 `src/routes/friends.tsx` `ReceivedRequestsSection`
- **의도**: FCM이 없어(spec 비범위) 사용자가 홈에 들어와야 도전장을 인지한다. 따라서 **액션이 필요한 항목을 진행 중 목록보다 위**에 둔다.

### 2.1 배치

```
HomeTopBar (기존)
StatsBar (기존)
▸ 받은 도전장 섹션        ← 신규. 0건이면 섹션 통째 미노출
  "진행 중인 챌린지" 섹션 (기존)
FAB (기존) / BottomBar (기존)
```

- 섹션 상단 여백 8.dp, 받은 도전장 섹션 ↔ 진행 중 섹션 사이 20.dp (`friends` 2차 `space-y-5`와 동일 리듬).
- 화면 가로 패딩 20.dp (기존 홈과 동일).

### 2.2 섹션 헤더

- "받은 도전장 " (`bold14`, `onBackground`) + "{N}건" (`bold14`, **`primary`**) — `friends` 2차 "받은 요청 N건"과 동일 패턴.
- 헤더 ↔ 리스트 gap 8.dp, 헤더 좌우 인셋 4.dp(`px-1`).

### 2.3 `ReceivedChallengeCard` 레이아웃

컨테이너: `Surface(color = surface, border = 1.dp outline, shape = RoundedCornerShape(16.dp))` + `Modifier.padding(12.dp)` — `FriendRequestCard`와 동일(컴팩트 12.dp).

```
┌──────────────────────────────────────────┐
│ [프사48] 도윤의 도전장                    │   ← Row, spacedBy 12.dp
│         🕐 42분                          │   ← 접미사 없음. 잔여 1시간 이하라 error 색
│                                          │   ← 12.dp
│ 도윤의 미션                               │   ← medium12 / onSurfaceVariant
│ 아침 6시 기상하기                          │   ← bold14 / onBackground, maxLines 2
│                                          │   ← 10.dp
│ 🔥 내기: 치킨 사기 🍗                      │   ← BetStrip (ChallengeCard와 동일)
│                                          │   ← 12.dp
│ [ ✓ 수락 ]        [ ✕ 거절 ]              │   ← 균등 2-up, spacedBy 8.dp
└──────────────────────────────────────────┘
```

| 요소 | Lovable | Compose |
|---|---|---|
| 프로필 자리 | `w-12 h-12 rounded-xl bg-secondary` + emoji | 48.dp + `RoundedCornerShape(12.dp)` + `secondary` bg + **닉네임 첫 글자 이니셜** `medium20` `onSurface` (friends 2차 `ProfilePlaceholder` 동일 규칙 — emoji는 Lovable 프리뷰 전용) |
| 타이틀 | `text-sm font-bold truncate` | `bold14` + `onBackground`, `maxLines = 1`, `TextOverflow.Ellipsis` — 문구 `"{닉네임}의 도전장"` |
| 남은 시간 | `text-xs font-medium` + `Clock` 12 | `Icons.Filled.Schedule` 12.dp + `medium12`, `spacedBy(4.dp)`. 색은 아래 임박 규칙. 값은 `deadline.toRelativeKoreanString()` **원문 그대로 — 접미사 없음** |
| 미션 라벨 | `text-[11px] text-muted-foreground` | `medium12` + `onSurfaceVariant` (11px → 12sp 근사, home-feed §7 #5 정책) |
| 미션 본문 | `text-sm font-semibold` | `bold14` + `onBackground`, `maxLines = 2`, `Ellipsis` — `ChallengeCard`의 강조 미션 구현 선례와 동일 |
| 내기 띠 | `bg-primary/5 border-primary/10 rounded-lg px-3 py-2` | `ChallengeCard.BetStrip`과 **완전 동일**: `primary.copy(alpha=0.05f)` bg + 1.dp `primary.copy(alpha=0.10f)` border + `RoundedCornerShape(10.dp)` + `padding(h=12.dp, v=8.dp)` + `LocalFireDepartment` 14.dp + `medium12`(`primary`) |
| 수락 버튼 | `Button size="sm"` + `Check` 14 | `IconTextButton(Filled)` — `weight(1f)`, height 36.dp, radius 12.dp, `Icons.Filled.Check` 14.dp, `bold14` |
| 거절 버튼 | `Button variant="outline" size="sm"` + `X` 14 | `IconTextButton(Outlined)` — 동일 크기, `Icons.Filled.Close` 14.dp, border `outline` |

> **액션 배치가 `FriendRequestCard`와 다른 이유**: 친구 요청 카드는 1행짜리라 버튼을 우측 인라인에 넣을 수 있었지만, 도전장 카드는 미션 + 내기 띠로 세로가 길어 우측 인라인이면 버튼이 카드 상단에 붕 뜬다. **카드 내부 하단 균등 2-up**으로 바꾼다(카드 밖 분리 ❌ — 카드 1장 = 도전장 1건이라는 경계가 흐려진다). 버튼 크기(36.dp / radius 12.dp / `bold14`)는 그대로 승계.

#### 남은 시간 표기 · 마감 임박 강조 규칙

값은 `:core:utils`의 `Instant.toRelativeKoreanString()` **출력 그대로**. 반환값은 4종이다:

| 잔여 | 반환 |
|---|---|
| 1시간 이상 | `"X시간 Y분"` / `"X시간"` |
| 1분 ~ 1시간 | `"X분"` |
| 1분 미만 (양수) | `"곧 마감"` |
| 0 이하 | `"마감"` |

> ⚠️ **`" 남음"` 같은 접미사를 붙이지 마라.** `"곧 마감 남음"` / `"마감 남음"`이 된다. (v1 명세의 오류를 정정한 항목 — Lovable 목데이터도 함께 수정했다.)

강조 색 규칙 — **잔여 1시간이 경계**:

| 조건 | 색 |
|---|---|
| 잔여 > 1시간 | `warning` (기존 `ChallengeCard`와 동일 톤) |
| 잔여 ≤ 1시간 (`"X분"` / `"곧 마감"` / `"마감"`) | `error` |

- 경계를 1시간으로 잡은 이유: 마감이 `TODAY`면 최대 24시간, `TOMORROW`면 최대 48시간이라 3시간 같은 넉넉한 경계는 목록 대부분이 강조돼 강조가 죽는다. "지금 안 누르면 놓친다"가 실제로 성립하는 구간이 1시간이다.
- 판정은 `deadline - now <= 1.hours`로 **컴포넌트가 직접** 한다. 문자열 파싱 ❌.
- 목록은 서버가 `deadline > now()`로 필터하므로(api-contract §2) `"마감"`은 화면을 켜둔 채 시각이 넘어갈 때만 나타난다. 그래도 렌더는 깨지지 않아야 한다.

### 2.4 상태

| 상태 | 조건 | 화면 |
|---|---|---|
| 미노출 | `received.isEmpty()` | 섹션 전체 렌더 안 함. **전용 빈 상태 카드 만들지 않는다** — 홈에 빈 상태 카드가 둘이 되면 시각 소음. `friends.tsx` 정책 동일 |
| 기본 | `received.isNotEmpty()` | §2.3 카드 × N (`createdAt` 내림차순 — api-contract §2 서버 정렬 그대로) |
| 로딩 | 최초 진입 fetch 중 | 섹션 미노출(깜빡임 방지). 홈 전체 `Loading` 슬롯이 이미 있으므로 별도 skeleton 없음 |
| 처리 중 | 특정 카드 수락/거절 in-flight | 해당 카드의 두 버튼 `enabled = false`. 다른 카드는 영향 없음 |
| 에러 | 목록 로드 실패 | 섹션 미노출 + 스낵바 1회. 홈의 나머지는 정상 렌더 |

- **낙관적 갱신**: 거절은 즉시 카드 제거 → 실패 시 롤백 + 스낵바 (friends 2차 정책 승계). **수락은 낙관적 갱신하지 않는다** — 미션 입력이 함께 가고 성공 시 진행 중 목록에도 삽입돼야 해서, 서버 응답 후 두 목록을 함께 갱신한다(api-contract §3 모바일 주의사항).

### 2.5 빈 상태 문구 톤 조정 (신규 결정)

`isFirstUser` 판정에 **`received.isEmpty()`를 AND 조건으로 추가**한다.

- **이유**: 받은 도전장이 있는데 바로 아래에서 "친구를 등록하고 첫 약속을 걸어보세요"라고 하면 안내가 사실과 어긋난다. 이미 걸 상대가 있고, 화면 위쪽에 수락 버튼이 떠 있다.
- **적용 후**: 받은 도전장 ≥ 1건이면 `HomeEmptyStateType.NO_ACTIVE_CHALLENGE` ("진행 중인 챌린지가 없어요" / "새 챌린지를 시작해 다시 불을 붙여보세요").
- **모바일 영향**: `HomeViewModel`의 `emptyType` 매핑 1줄. `HomeEmptyState` 컴포넌트 자체는 무변경. ⚠️ 기존 테스트 10건 중 `FIRST_USER` 케이스가 있으면 받은 도전장 0건 전제를 명시적으로 넣어야 한다.

---

## 3. 수락 시 미션 입력 — `AcceptChallengeDialog` (신규 설계)

Lovable에 대응 화면이 없다. 기존 토큰만으로 신규 설계했고, Lovable `src/routes/index.tsx`에도 shadcn `dialog`(Radix)로 프리뷰를 구현해 두었다.

### 3.1 다이얼로그 채택 근거 (바텀시트에서 변경 — v2)

**v1은 바텀시트였다. mobile-dev의 플랫폼 제약 지적을 받아 다이얼로그로 바꾼다.** 근거를 남긴다.

**v1이 틀렸던 지점** — 내 1순위 근거가 "시트가 IME 처리가 쉽다"였는데, 검증해 보니 반대였다:

- **바텀시트 선례 0건.** `challenge-app` 전체에 `ModalBottomSheet` 사용처가 없다(`grep` 확인). CMP 1.10.3의 `ModalBottomSheet` + `TextField` 조합은 iOS IME에서 시트가 가려지거나 밀리는 동작이 플랫폼별로 갈리는 구간이고, 이번 feature가 그 리스크를 처음 떠안게 된다. mobile-dev가 iOS 실기 검증 시간을 별도로 잡아야 한다고 명시했다.
- **`MainScreen.kt:142`에 `imePadding()`이 이미 있다.** 앱이 Scaffold 레벨에서 IME를 잡고 있어 기존 인셋 처리와 충돌이 적은 쪽은 다이얼로그다.

**나머지 v1 근거는 다이얼로그로 충족되거나 무효다:**

- *정보량* — 요약 3행 + 입력 1개 + CTA는 다이얼로그에 충분히 들어간다. 입력 필드가 **1개**뿐이라 시트의 넓은 면적이 필요 없다.
- *취소 안전성* — 배경 탭 / 시스템 백으로 동일하게 확보된다.
- *무게감* — CTA 문구("수락하고 시작")와 요약 카드가 담당한다. 오히려 다이얼로그가 "결단" 톤에 가깝다.
- *역할 분리(v1의 3번)* — **v3에서 전제가 무너져 폐기.** 아래 참조.

> **v3 정정 (2026-07-28 15:10)**: v2는 "`705` 확인 다이얼로그가 어차피 필요하니, 시트까지 넣으면 선례 0건 오버레이를 2개 들이게 된다"를 결정적 근거로 삼았다. **이 전제가 계약 확정으로 무효가 됐다.**
>
> api-contract가 `confirmed`되면서 **모바일은 `code`로 분기하지 않는다**가 명문화됐다(§공통 규약 2 — `suspendOnFailureWithErrorHandling(onError: (String) -> Unit)` 시그니처가 `CustomError`에서 code를 버리고 message만 넘기는 프로젝트 표준). 수락/거절 실패는 **코드와 무관하게 스낵바 + 목록 무조건 재조회**로 통일된다. 따라서 **`705` 전용 확인 다이얼로그는 만들지 않는다.**
>
> **그래도 결론은 다이얼로그로 유지한다.** 근거가 하나 줄었을 뿐, 애초에 mobile-dev가 다이얼로그를 권한 1순위 이유(시트 선례 0건 + CMP iOS IME 리스크 + 기존 `imePadding()`)가 그대로 살아 있고, 입력 필드 1개에 시트의 면적이 필요 없다는 점도 그대로다. 오히려 이제 **이번 feature가 새로 들이는 오버레이 프리미티브는 `AcceptChallengeDialog` 하나뿐**이라 더 단순해졌다.
>
> v2에 있던 "705 에러 다이얼로그가 연달아 뜨는 트레이드오프"도 함께 소멸했다.

### 3.2 레이아웃

```
┌──────────────────────────────────────┐
│ 받아친다 🔥                      [✕] │  ← bold18 / onBackground
│ 수락하면 바로 시작돼. 네가 해낼        │  ← medium14 / onSurfaceVariant
│ 미션을 적어.                          │
│                                      │  ← 16.dp
│ ┌──────────────────────────────────┐ │
│ │ 도윤의 미션      아침 6시 기상하기 │ │  ← surface 카드, padding 12.dp
│ │ 내기            치킨 사기 🍗      │ │  ← 행 간 8.dp
│ │ 마감            42분              │ │
│ └──────────────────────────────────┘ │
│                                      │  ← 16.dp
│ 나의 미션                             │  ← medium12 / onSurfaceVariant
│ ┌──────────────────────────────────┐ │
│ │ 예) 책 30페이지 읽기              │ │  ← secondary bg, 48.dp
│ └──────────────────────────────────┘ │
│                            0/100     │  ← medium12, 우측 정렬
│                                      │  ← 16.dp
│ [       ✓ 수락하고 시작        ]      │  ← 52.dp full-width primary
└──────────────────────────────────────┘
```

| 항목 | 값 |
|---|---|
| 구현 | `BasicAlertDialog`(Material3) + 커스텀 `Surface` 컨텐트. `AlertDialog`의 고정 `title`/`text`/`confirmButton` 슬롯은 요약 카드 + 입력 + 카운터를 담기 어렵다 |
| 컨테이너 | `Surface(color = colorScheme.background, shape = RoundedCornerShape(16.dp))` — **`background`**. 내부 요약 카드가 `surface`라 대비가 필요하다 (Lovable `DialogContent bg-background` + 내부 `glass-card` 동일 구조) |
| 폭 | `Modifier.fillMaxWidth().padding(horizontal = 20.dp)` — 화면 좌우 20.dp 여백. `usePlatformDefaultWidth = false` |
| 내부 패딩 | 20.dp |
| 타이틀 | "받아친다 🔥" `bold18` `onBackground` |
| 서브 | "수락하면 바로 시작돼. 네가 해낼 미션을 적어." `medium14` `onSurfaceVariant`, 타이틀과 4.dp |
| 블록 간격 | `spacedBy(16.dp)` |
| 요약 카드 | `Surface(surface, 1.dp outline, RoundedCornerShape(16.dp))` + `padding(12.dp)` + 행 간 `spacedBy(8.dp)` |
| 요약 라벨 | `medium14` + `onSurfaceVariant` (좌측 고정, `shrink` 금지) |
| 요약 값 | `bold14` + `onBackground` (우측 정렬, 길면 wrap). **내기 행만 `primary`** — Lovable step2 계약서 요약과 동일 강조 |
| 요약 "마감" 값 | `toRelativeKoreanString()` **원문** (§2.3 규칙 동일, 접미사 ❌) |
| 입력 라벨 | "나의 미션" `medium12` + `onSurfaceVariant`, 입력과 6.dp |
| 입력 박스 | §1.3 입력 박스 공통 명세와 **완전 동일** (48.dp / `secondary` / 12.dp radius / `medium14` / 포커스 시 2.dp `primary` border) |
| 글자 수 | §1.3 카운터 공통 규칙과 **완전 동일** |
| CTA | `IconTextButton(Filled)` — `fillMaxWidth`, 52.dp, radius 12.dp, `Icons.Filled.Check` 18.dp + "수락하고 시작", `bold14` |
| 닫기 | 우상단 `IconButton` 없이 **배경 탭 / 시스템 백**으로 일원화 (Lovable `DialogContent`는 X 버튼이 기본 포함이지만, 모바일은 시스템 백이 있어 불필요) |

> **버튼이 단일 CTA인 이유**: "취소" 버튼을 나란히 두면 2-up이 되어 primary CTA의 시각 비중이 절반으로 준다. 취소는 배경 탭/시스템 백이라는 무비용 경로가 이미 있고, 이 화면은 "수락"이 유일한 전진 동작이다.

### 3.3 상태

| 상태 | 조건 | 시각 / 동작 |
|---|---|---|
| 기본 | 다이얼로그 오픈 직후 | 입력 비어 있음, 입력에 자동 포커스(`FocusRequester`) + IME 오픈. CTA **비활성** |
| 입력 유효 | `myMission.trim().length in 1..100` | CTA 활성 (`primary` / `onPrimary`) |
| 비활성 | 미입력 / 공백만 | CTA `enabled = false`, Material3 기본 disabled alpha |
| 100자 도달 | `trim().length == 100` | 카운터 `warning`. 입력은 하드캡으로 더 안 들어감 |
| 로딩 | 제출 in-flight | CTA `enabled = false` + 라벨 자리 `CircularProgressIndicator(18.dp, onPrimary, stroke 2.dp)`. **입력 `readOnly = true`**, 배경 탭·시스템 백 dismiss 차단 (`DialogProperties(dismissOnBackPress = false, dismissOnClickOutside = false)`) |
| 성공 | `code = 200` | 다이얼로그 닫기 → 받은 도전장 목록 + 진행 중 목록 **둘 다** 갱신 → 스낵바 "챌린지가 시작됐어요" |
| **실패 (코드 무관)** | 서버가 성공이 아닌 응답 | **다이얼로그 닫기 → 스낵바(서버 `message` 그대로) → 받은 도전장 목록 무조건 재조회.** api-contract §공통 규약 2 — 모바일 error-channel이 `code`를 버리므로 700/705를 구분하지 않는다. "목록이 낡았다 → 재조회" 효과는 "실패 시 항상 재조회"로 동일하게 달성된다 |
| 취소 | 배경 탭 / 시스템 백 | 입력값 폐기하고 닫기. 별도 확인 없음 |

- 다이얼로그는 화면당 1개 인스턴스. `acceptTarget: ReceivedChallenge?` 상태 하나로 열림/닫힘과 대상 데이터를 함께 표현한다(Lovable 프리뷰와 동일).
- IME가 올라와 컨텐트가 화면을 넘치면 내부를 `verticalScroll`로 감싼다.

> **실패 시 다이얼로그를 닫는 이유**: 목록을 재조회하는 동안 다이얼로그가 떠 있으면 그 아래에서 대상 카드가 사라질 수 있어(이미 처리된 도전장) 상태가 어긋난다. 닫고 재조회하는 편이 일관된다.
>
> 대가로 입력한 미션이 사라진다. 다만 **길이 위반(700)은 클라이언트 검증(trim 1~100자 + 100자 하드캡)으로 이미 막혀 도달 불가**하고, 남는 건 네트워크 오류나 낡은 목록뿐이라 손실 빈도가 낮다. 재입력 부담이 문제로 드러나면 실패 시 입력값을 ViewModel에 남겨 재오픈 시 복원하는 방식으로 후속 조정 가능하다(`myMission`이 이미 ViewModel 소유라 비용이 작다).

---

## 4. Compose 컴포넌트 spec (props 시그니처 — 모바일 단일 출처)

### 4.1 `FriendPickItem`

```kotlin
@Composable
internal fun FriendPickItem(
    profileImageUrl: String?,   // 이미지 로더 부재 — 시그니처만. 이니셜 placeholder 렌더
    nickname: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
)
```

- 컨테이너: `Surface(surface, RoundedCornerShape(16.dp))` + `Modifier.fillMaxWidth().clickable(onClick)` + `Modifier.padding(16.dp)` + `spacedBy(12.dp)`
- **border 분기 (선택 상태)** — Lovable `ring-2 ring-primary` 매핑:

  | 상태 | border |
  |---|---|
  | 기본 | `BorderStroke(1.dp, colorScheme.outline)` |
  | 선택 | `BorderStroke(2.dp, colorScheme.primary)` |

- 좌: 프로필 48.dp / 12.dp radius / `secondary` bg / 닉네임 첫 글자 `medium20` `onSurface`
- 중: 닉네임 `bold14` `onBackground`, `weight(1f)`, `maxLines = 1` Ellipsis. **전적 행 없음** (§1.2 ⚠️)
- 우: `Icons.AutoMirrored.Filled.KeyboardArrowRight` 18.dp `onSurfaceVariant`
- `@Preview` 3종 권고: 기본 / 선택 / 긴 닉네임

### 4.2 `DeadlineSelector`

```kotlin
@Composable
internal fun DeadlineSelector(
    value: DeadlineType,             // :domain:model 의 enum 을 그대로 받는다
    onValueChange: (DeadlineType) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
)
```

> `:feature:challenge:create`에 두므로 **`:domain:model`의 `DeadlineType`을 그대로 받는다.** 미러 enum 불필요 (spec.md T-M3 정정 반영 — §7).

- **세그먼트 컨트롤이 아니라 카드 2장(2-up).** 옵션마다 2줄(라벨 + 실제 시각)이 들어가는데, 세그먼트는 붙어 있는 단일 라인 컨트롤이라 2줄을 담으면 형태가 무너진다.
- 라벨 "마감" `medium12` `onSurfaceVariant` + 6.dp gap
- `Row(horizontalArrangement = spacedBy(8.dp))` — 두 옵션 각각 `Modifier.weight(1f)`
- 옵션 버튼: height **60.dp**, `RoundedCornerShape(12.dp)`, 세로 가운데 정렬, 2줄 사이 2.dp
  - 1행: `Icons.Filled.Schedule` 14.dp + 라벨("오늘 자정" / "내일 자정") `medium14`, 아이콘↔라벨 6.dp
  - 2행: **실제 마감 시각** `medium12`

  | 상태 | 배경 | border | 1행 색 | 2행 색 |
  |---|---|---|---|---|
  | 선택 | `primary.copy(alpha = 0.10f)` | 1.dp `primary` | `primary` | `primary.copy(alpha = 0.80f)` |
  | 미선택 | `secondary` | 없음 (`Color.Transparent`) | `onSurfaceVariant` | `onSurfaceVariant.copy(alpha = 0.70f)` |
  | 비활성 (`enabled = false`) | 위와 동일 + 컴포넌트 전체 `alpha = 0.5f` | — | — | — |

- 캡션 "선택한 자정까지가 챌린지 기간이야" `medium12` `onSurfaceVariant`, 6.dp top
- 접근성: 각 버튼 `Modifier.semantics { role = Role.RadioButton; selected = ... }`. 2지선다이므로 라디오 시맨틱이 맞다.

#### 실제 마감 시각 부기 (mobile-dev 제안 채택)

spec 결정 3의 취지가 "심야 생성 시 몇 분짜리 챌린지가 되는 걸 막는다"인데, `"오늘 자정"`만 보여주면 그게 정확히 몇 시인지 안 보여 취지가 죽는다. 실제 시각을 부기한다.

| 옵션 | 표기 예 |
|---|---|
| `TODAY` | `"7/28 24:00"` |
| `TOMORROW` | `"7/29 24:00"` |

- **`24:00` 표기를 쓰는 이유**: "오늘 자정"의 실제 순간은 익일 `00:00`이라 `"7/29 00:00"`으로 적으면 "오늘"인데 왜 내일 날짜냐는 혼란이 생긴다. `24:00`은 "7/28이 끝나는 순간"으로 한 번에 읽힌다.
- **계산** (KST 고정):
  ```kotlin
  val kst = TimeZone.of("Asia/Seoul")
  val today = Clock.System.now().toLocalDateTime(kst).date
  val date = if (option == DeadlineType.TOMORROW) today.plus(1, DateTimeUnit.DAY) else today
  val hint = "${date.monthNumber}/${date.dayOfMonth} 24:00"
  ```
- ⚠️ **표시 전용.** 마감 환산의 authority는 서버다(api-contract §DeadlineType — 클라이언트는 timestamp를 보내지 않는다). 기기 시계가 틀리면 이 표시도 틀리지만, 전송값은 enum이라 **실제 저장되는 마감은 영향받지 않는다.**
- 날짜 자정을 넘겨 화면을 켜둔 경우 값이 낡는다. `ChallengeCreateViewModel` 진입 시 1회 계산으로 충분하다 — 실시간 갱신은 과하다.

### 4.3 `ReceivedChallengeCard`

```kotlin
@Composable
internal fun ReceivedChallengeCard(
    challengeId: Long,
    challengerNickname: String,
    challengerProfileImageUrl: String?,
    challengerMission: String,
    bet: String,
    deadline: Instant,          // 내부에서 toRelativeKoreanString() — 접미사 없음
    onAccept: () -> Unit,       // 다이얼로그 오픈 — 호출부 책임
    onReject: () -> Unit,
    actionsEnabled: Boolean = true,   // in-flight 동안 false
    modifier: Modifier = Modifier,
)
```

- 시각은 §2.3 표 + 남은 시간 표기/임박 강조 규칙 그대로. `@OptIn(ExperimentalTime::class)` — `ChallengeCard`와 동일.
- 임박 판정(`deadline - now <= 1.hours`)은 컴포넌트 내부에서. `now`는 `Clock.System.now()` 기본값 파라미터로 빼면 `@Preview`/테스트에서 고정 가능하다.
- `@Preview` 4종 권고: 기본 / **임박(잔여 1시간 이하 — `error` 색)** / 긴 미션(2줄 ellipsis) / `actionsEnabled = false`

### 4.4 `ReceivedChallengesSection`

```kotlin
@Composable
internal fun ReceivedChallengesSection(
    challenges: List<ReceivedChallenge>,
    onAccept: (ReceivedChallenge) -> Unit,
    onReject: (Long) -> Unit,
    inFlightIds: Set<Long> = emptySet(),
    modifier: Modifier = Modifier,
)
```

- **호출부가 `challenges.isEmpty()`일 때 아예 호출하지 않는다** — 컴포넌트 내부에 빈 상태 분기를 넣지 않는다.
- 헤더(§2.2) + `Column(spacedBy(8.dp))`. 홈 전체가 이미 `LazyColumn`이면 `item`/`items`로 펼치는 편이 낫다 — 중첩 `LazyColumn` 금지.

### 4.5 `AcceptChallengeDialog`

```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun AcceptChallengeDialog(
    challenge: ReceivedChallenge?,   // null이면 닫힘 — 호출부에서 null 체크 후 렌더
    myMission: String,
    onMyMissionChange: (String) -> Unit,
    isSubmitting: Boolean,
    onSubmit: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
)
```

- 시각·상태는 §3.2 / §3.3 그대로. `BasicAlertDialog` + 커스텀 `Surface` 컨텐트.
- **입력 상태는 ViewModel 소유**(`myMission` hoisting). 다이얼로그 내부 `remember`로 두면 회전·프로세스 사망 시 유실되고, 제출 검증을 ViewModel이 못 한다.
- `isSubmitting = true`면 `DialogProperties(dismissOnBackPress = false, dismissOnClickOutside = false)`로 dismiss 차단.
- `DialogProperties(usePlatformDefaultWidth = false)` + `Modifier.fillMaxWidth().padding(horizontal = 20.dp)`로 폭 제어.
- `@Preview` 4종 권고: 기본(빈 입력) / 유효 입력 / 100자 도달 / 로딩

### 4.6 ~~`ChallengeErrorDialog` (705 공통)~~ — **v3에서 폐기**

**만들지 않는다.** api-contract가 `confirmed`되면서 **모바일이 `code`로 분기하지 않는다**가 확정됐다(§공통 규약 2). 수락/거절 실패는 코드와 무관하게 **스낵바(서버 `message`) + 목록 무조건 재조회**로 처리한다 — 별도 확인 다이얼로그가 필요 없다.

→ 본 feature가 새로 만드는 오버레이는 **`AcceptChallengeDialog` 하나뿐**이다.

---

## 5. 사용 토큰 종합

**신규 토큰 0건.** 전부 기존 슬롯.

### 5.1 색상 (`ChallengeTheme.colorScheme.*`)

| 의미 | 슬롯 |
|---|---|
| 화면 배경 / 다이얼로그 컨테이너 | `background` |
| 카드 (glass-card) / TopBar | `surface` |
| 카드 border / 미선택 옵션 아웃라인 | `outline` |
| 입력 박스 bg / 프로필 자리 bg / 미선택 마감 옵션 bg | `secondary` |
| 본문·타이틀·닉네임·미션 본문 | `onBackground` |
| 라벨·캡션·placeholder·전적성 보조 | `onSurfaceVariant` |
| 프로필 이니셜 | `onSurface` |
| CTA bg / "N건" 강조 / 선택된 마감 옵션 / 내기 텍스트 / progress 도달 칸 | `primary` |
| CTA content | `onPrimary` |
| 선택 옵션 bg / 내기 띠 bg | `primary.copy(alpha = 0.10f)` / `primary.copy(alpha = 0.05f)` — **슬롯화 ❌, 호출부 책임** (home-feed §5 정책) |
| 선택 옵션 2행 / 미선택 옵션 2행 | `primary.copy(alpha = 0.80f)` / `onSurfaceVariant.copy(alpha = 0.70f)` — 동상 |
| 남은 시간(잔여 > 1시간) / 글자 수 100자 도달 | `warning` |
| **남은 시간(잔여 ≤ 1시간, 마감 임박)** | `error` |
| progress 미도달 칸 | `secondary` |

### 5.2 Typography (`ChallengeTheme.typography.*`)

| 위치 | 슬롯 |
|---|---|
| 위저드 step 제목 ("누구에게 걸래? 🔥") | `bold20` |
| 위저드 TopBar "새 챌린지" / 다이얼로그 타이틀 "받아친다 🔥" | `bold18` |
| 홈 빈 상태 헤드라인 (기존 재사용) | `bold16` |
| 섹션 헤더 / 카드 타이틀 / 미션 본문 / 요약 값 / 모든 버튼 라벨 | `bold14` |
| step 서브 문구 / 입력 텍스트 / placeholder / 마감 옵션 1행 라벨 / 요약 라벨 / 다이얼로그 서브 / 에러 다이얼로그 본문 | `medium14` |
| 필드 라벨 / 미션 라벨 / 캡션 / 남은 시간 / 글자 수 / **마감 옵션 2행(실제 시각)** | `medium12` |
| 프로필 이니셜 | `medium20` |

> `text-[11px]`(미션 라벨) → `medium12` 근사. home-feed §7 #5 결정 승계 — 신규 슬롯 만들지 않는다.

### 5.3 Radius

| 위치 | dp |
|---|---|
| 카드 컨테이너 (`FriendPickItem` / `ReceivedChallengeCard` / 요약 카드) | 16 |
| **다이얼로그 컨테이너** (`AcceptChallengeDialog`) | 16 |
| 버튼 / 입력 박스 / 마감 옵션 / 프로필 자리 | 12 |
| 내기 띠 | 10 |
| progress 칸 | `CircleShape` |

### 5.4 Spacing (dp)

| 위치 | 값 |
|---|---|
| 화면 가로 패딩 | 20 |
| TopBar 높이 | 56 |
| progress 칸 높이 / 칸 간격 / TopBar와 간격 | 4 / 6 / 12 |
| 본문 상단 여백 | 16 |
| step 제목 ↔ 서브 | 4 |
| step 서브 ↔ 첫 요소 | 24 |
| step1 필드 블록 간격 | 16 |
| 필드 라벨 ↔ 입력 / 입력 ↔ 캡션·카운터 | 6 |
| 입력 박스 높이 / 가로 패딩 | 48 / 16 |
| 마감 옵션 높이 / 두 옵션 간격 / 아이콘↔라벨 / 2줄 사이 | 60 / 8 / 6 / 2 |
| CTA 버튼 높이 | 52 |
| 카드 리스트 간격 | 8 |
| 섹션 헤더 ↔ 리스트 | 8 |
| 섹션 간 간격 | 20 |
| 받은 도전장 섹션 상단 여백 | 8 |
| `ReceivedChallengeCard` 패딩 / 내부 요소 간격 | 12 / 12 |
| 카드 미션 블록 ↔ 내기 띠 | 10 |
| 내기 띠 패딩 | h 12 / v 8 |
| 카드 액션 버튼 높이 / 간격 | 36 / 8 |
| `FriendPickItem` 패딩 | 16 |
| 다이얼로그 내부 패딩 / 화면 좌우 여백 | 20 / 20 |
| 다이얼로그 블록 간격 / 요약 카드 패딩 / 요약 행 간격 | 16 / 12 / 8 |

### 5.5 아이콘 (Material Icons Extended)

| 위치 | 아이콘 | dp |
|---|---|---|
| 위저드 뒤로가기 | `Icons.AutoMirrored.Filled.ArrowBack` | 20 |
| `FriendPickItem` 우측 chevron | `Icons.AutoMirrored.Filled.KeyboardArrowRight` | 18 |
| 마감 옵션 / 카드 남은 시간 | `Icons.Filled.Schedule` | 14 / 12 |
| "챌린지 걸기" CTA | `Icons.Filled.SportsKabaddi` | 18 |
| 카드 [수락] / 다이얼로그 CTA | `Icons.Filled.Check` | 14 / 18 |
| 카드 [거절] | `Icons.Filled.Close` | 14 |
| 내기 띠 🔥 | `Icons.Filled.LocalFireDepartment` | 14 |
| step0 빈 상태 | `Icons.Filled.Group` | 32 |
| 홈 FAB (기존) | `Icons.Filled.Add` | 28 |

> Lovable lucide → Material 매핑은 bottom-navigation 옵션 A 일관. `ChevronRight`만 본 feature에서 신규 도입.

### 5.6 문구 (단일 출처, 전부 한국어)

| 위치 | 문구 |
|---|---|
| 위저드 TopBar | "새 챌린지" |
| step0 제목 / 서브 | "누구에게 걸래? 🔥" / "대결 상대를 선택하세요" |
| step0 빈 상태 | "아직 친구가 없어요" / "친구를 추가하고 챌린지를 걸어보세요" / CTA "친구 추가하기" |
| step1 제목 / 서브 | "미션을 입력해 ✍️" / "오늘 반드시 해낼 것을 적어" |
| step1 미션 라벨 / placeholder | "나의 미션" / "예) 오늘 운동 1시간 하기" |
| step1 내기 라벨 / placeholder | "내기 (진 사람이 해야 할 것)" / "예) 커피 사기" |
| 마감 라벨 / 옵션 / 캡션 | "마감" / "오늘 자정" · "내일 자정" / "선택한 자정까지가 챌린지 기간이야" |
| 마감 옵션 부기 | "{M}/{D} 24:00" (§4.2) |
| 글자 수 카운터 | "{n}/100" |
| step1 CTA | "챌린지 걸기" |
| 홈 섹션 헤더 | "받은 도전장 {N}건" — "{N}건"만 `primary` |
| 도전장 카드 타이틀 / 미션 라벨 / 남은 시간 | "{닉네임}의 도전장" / "{닉네임}의 미션" / `toRelativeKoreanString()` 원문 (**접미사 ❌**) |
| 도전장 카드 내기 띠 | "내기: {bet}" |
| 도전장 카드 액션 | "수락" / "거절" |
| 다이얼로그 타이틀 / 서브 | "받아친다 🔥" / "수락하면 바로 시작돼. 네가 해낼 미션을 적어." |
| 다이얼로그 요약 라벨 | "{닉네임}의 미션" / "내기" / "마감" |
| 다이얼로그 입력 라벨 / placeholder | "나의 미션" / "예) 책 30페이지 읽기" |
| 다이얼로그 CTA | "수락하고 시작" |
| 성공 스낵바 (수락) | "챌린지가 시작됐어요" |
| **모든 실패 스낵바** | **서버 `message` 그대로.** 클라이언트가 문구를 만들지 않는다 — api-contract가 모든 `message`를 사용자 노출 문구로 확정했다 |
| a11y | 뒤로가기 `"뒤로 가기"`, 수락 `"도전장 수락"`, 거절 `"도전장 거절"` |

> 반말 톤(`"걸래?"`, `"적어"`, `"받아친다"`)은 Lovable 원본의 제품 보이스다. 신규 문구도 같은 톤으로 맞췄다. `friends` feature의 존댓말 안내문(`"닉네임을 2자 이상 입력해주세요"`)과 톤이 갈리는데, **원본이 이미 그렇게 갈려 있어** 본 feature는 화면별 원본 톤을 따랐다. 통일이 필요하면 §9 #8.

---

## 6. 상태 매트릭스 (전 화면 집약)

| 화면 / 요소 | 기본 | 선택 | 비활성 | 로딩 | 빈 상태 | 에러 |
|---|---|---|---|---|---|---|
| step0 친구 리스트 | 카드 N개 | `FriendPickItem` 2.dp `primary` border | — | 중앙 `CircularProgressIndicator` | 카드 1개 + "친구 추가하기" CTA | 스낵바 + 빈 상태 카드(문구/CTA 교체) |
| step1 입력 박스 | `secondary` bg | 포커스 시 2.dp `primary` border | 제출 중 `readOnly` | — | — | 실패 → 스낵바, 값 보존 |
| `DeadlineSelector` | 미선택 `secondary`/`onSurfaceVariant` | `primary` 10% bg + 1.dp `primary` border + `primary` content | 전체 `alpha 0.5f` | — | — | — |
| 글자 수 카운터 | `onSurfaceVariant` | — | — | — | `0/100` | 100자 도달 시 `warning` (초과는 하드캡으로 불가) |
| step1 CTA | `primary` | — | trim 후 1~100자 미충족 시 disabled alpha | 인디케이터 18.dp | — | 실패 → 스낵바 |
| 받은 도전장 섹션 | 카드 N개 | — | in-flight 카드 버튼 disabled | 섹션 미노출 | **섹션 통째 미노출** | 섹션 미노출 + 스낵바 |
| 카드 남은 시간 | `warning` (잔여 > 1시간) | — | — | — | — | 잔여 ≤ 1시간 → `error` |
| `AcceptChallengeDialog` | 빈 입력, CTA disabled | — | 미입력/공백 | CTA 인디케이터 + 입력 readOnly + dismiss 차단 | — | **코드 무관** — 닫고 스낵바 + 목록 재조회 |
| 홈 빈 상태 카드 | 기존 자산 | — | — | — | 받은 도전장 유무로 `FIRST_USER` ↔ `NO_ACTIVE_CHALLENGE` 분기 | — |

---

## 7. 모듈 배치 — ✅ 합의 완료 (2026-07-28)

> **결론: feature 모듈.** spec.md T-M3이 정정됐고, mobile-dev와 design-bridge가 **독립적으로 같은 결론**에 도달했다. 아래는 근거 기록.

spec.md **T-M3 초안**은 `FriendPickItem` / `ReceivedChallengeCard` / `DeadlineSelector`를 `:core:designsystem`에 두라고 적혀 있었다. 그런데 모바일 레포의 실제 선례는 다르다.

| 컴포넌트 | 실제 위치 |
|---|---|
| `ChallengeCard` / `StatsBar` / `HomeEmptyState` / `HomeTopBar` | `:feature:home/component/` (home-feed 산출물) |
| `FriendListItem` / `FriendRequestCard` / `ProfilePlaceholder` | `:feature:friends:list/component/` (friends 2차 산출물) |
| `:core:designsystem/components/` | `Button` / `IconTextButton` / `Label` / `Divider` / `Scaffold` / `Spacer` — **도메인 무관 프리미티브만** |

`:core:designsystem`은 `:core:utils` + `materialIconsExtended`만 의존한다(`:domain:model` 미의존).

**확정 배치**:

- `ReceivedChallengeCard` / `ReceivedChallengesSection` / `AcceptChallengeDialog` → **`:feature:home/component/`** (`ChallengeCard` 옆)
- `FriendPickItem` / `DeadlineSelector` → **`:feature:challenge:create/component/`**

**이유**:

1. 전부 화면 1곳에서만 쓰이는 도메인 컴포넌트다.
2. `:core:designsystem`에 넣으면 `DeadlineType` 도메인 enum을 못 받아 미러 enum + 매퍼가 추가로 필요하다.
3. **커밋 `72d9d9c` "fix: feature component가 디자인시스템 모듈에 있던 문제 수정"에서 사용자가 feature 전용 컴포넌트를 designsystem에서 직접 걷어냈다.** 초안대로 하면 그 수정을 되돌린다.

> 이 배치에서 T-M3은 사실상 T-M4/T-M5에 흡수된다. `:core:designsystem`은 **건드리지 않는다** — 토큰(`ChallengeTheme.colorScheme` / `.typography`)만 읽는다.

부수 이슈: `ProfilePlaceholder`(닉네임 이니셜 자리)가 `:feature:friends:list`에 `internal`이라 홈/위저드에서 재사용할 수 없다. 선택지는 (a) `:core:ui`로 승격(현재 `StatusPillBadge`/`PlaceholderScreen` 2개가 있는 모듈), (b) 각 feature에 복제. **(a) 권고** — 이번 feature에서 2곳이 더 쓰므로 총 4곳이 된다.

---

## 8. mobile-dev 강조 사항

1. **`toRelativeKoreanString()` 출력에 접미사를 붙이지 마라** (§2.3). `"곧 마감"` / `"마감"`도 반환하므로 `" 남음"`을 붙이면 문장이 깨진다. **v1 명세의 오류를 정정한 항목이니 특히 주의.**
2. **마감 임박 강조는 잔여 1시간 경계** (§2.3). `deadline - now <= 1.hours` → `error`, 그 외 `warning`. **문자열 파싱 ❌**, `Instant`로 직접 판정.
3. **수락 UI는 다이얼로그** (§3). `BasicAlertDialog` + 커스텀 `Surface` 컨텐트. `AcceptChallengeDialog`의 `myMission`은 **ViewModel hoisting**, 내부 `remember` ❌.
4. **`ChallengeErrorDialog`는 만들지 않는다** (§4.6 — v3에서 폐기). 모바일이 `code`로 분기하지 않으므로(api-contract §공통 규약 2) 수락/거절 실패는 **코드 무관 스낵바 + 목록 무조건 재조회**. **본 feature가 새로 만드는 오버레이는 `AcceptChallengeDialog` 하나뿐.**
5. **글자 수 카운터는 trim 기준** (§1.3). 서버 검증이 trim 기준이라 `"  a  "`는 `1/100`이어야 한다. `maxLength = 100` 하드캡 동반.
6. **step1 CTA disabled 조건도 trim 기준** — 공백만 입력하고 통과하면 서버 검증에서 걸린다.
7. **모듈 배치는 feature 모듈 확정** (§7). `:core:designsystem`은 건드리지 않는다 — 토큰만 읽는다.
8. **`ProfilePlaceholder`는 `:core:ui` 승격 권고** (§7). 복제하면 이니셜 규칙(`nickname.trim().firstOrNull()?.uppercase()`)이 3벌이 된다.
9. **내기 띠는 `ChallengeCard.BetStrip`과 픽셀 동일** — 값이 전부 같으니 사설 구현 말고 공통화 검토(`:core:ui` 후보).
10. **수락은 낙관적 갱신 ❌, 거절은 낙관적 갱신 ⭕** (§2.4). 수락 성공 시 받은 도전장 + 진행 중 목록 **둘 다** 갱신.
11. **`isFirstUser` 판정에 받은 도전장 조건 추가** (§2.5). `HomeViewModel` 기존 테스트 10건 중 `FIRST_USER` 케이스는 "받은 도전장 0건" 전제를 명시해야 회귀가 안 난다.
12. **progress 칸은 2칸** (§1.1). Lovable 3칸을 그대로 옮기면 도달 불가능한 칸이 생긴다.
13. **STT 마이크 버튼 / 친구 전적 행은 모바일에서 렌더하지 않는다** (§1.2, §1.3). Lovable에는 남아 있는 게 정상이다 — 지우러 가지 말 것.
14. **마감 옵션의 실제 시각 부기는 KST 고정 + 표시 전용** (§4.2). 전송값은 enum이라 기기 시계가 틀려도 저장되는 마감은 영향 없다. ViewModel 진입 시 1회 계산.
15. **`materialIconsExtended` 의존성**을 `:feature:challenge:create`에 추가. `:feature:home`엔 이미 있다.
16. **`Instant` 사용부는 `@OptIn(kotlin.time.ExperimentalTime::class)`** — `ChallengeCard` 선례 동일.

---

## 9. ⚠️ 확인 필요 / 협의 항목

| # | 항목 | 본안 | 결정 주체 / 시점 |
|---|---|---|---|
| 1 | 컴포넌트 모듈 배치 (spec T-M3 초안 `:core:designsystem` vs feature 모듈) | **feature 모듈 — ✅ 합의 완료** (§7). spec.md T-M3 정정됨 | 결정 완료 |
| 2 | **수락 UI — 바텀시트 vs 다이얼로그** | **다이얼로그 — v1(바텀시트)에서 변경** (§3.1). CMP 시트 선례 0건 + iOS IME 리스크 + 입력 1개. *(v2의 "705 다이얼로그가 어차피 필요" 근거는 v3에서 폐기 — 계약 확정으로 모바일이 code를 안 쓴다. 결론은 유지)* | 결정 완료 — 디자이너 사후 검토 |
| 3 | `ProfilePlaceholder` `:core:ui` 승격 | 승격 권고 | mobile-dev 재량 |
| 4 | Lovable step2 마감 표시 바인딩 1줄 | 넣었음 (§0.1). 되돌리기 1줄 | pm-lead 확인 |
| 5 | 미션/내기 100자 제한 (api-contract 오픈이슈 #4) | **100자 유지.** 카드 미션 2줄 ellipsis, 다이얼로그 요약 우측 정렬 wrap으로 렌더 검증됨 | 결정 완료 |
| 6 | 친구 전적 행 미노출 | `GET /api/v1/friends`에 전적 없음 → 미노출. `friend_records` 붙는 후속 feature에서 복귀 | 결정 완료 |
| 7 | 마감 옵션 실제 시각 부기 (`"7/28 24:00"`) | **부기함** — mobile-dev 제안 채택. spec 결정 3(심야 생성 방지)의 취지 보존 (§4.2) | 디자이너 시각 검토 |
| 8 | `24:00` 표기 vs `00:00` 표기 | `24:00` — "오늘 자정"의 실제 순간은 익일 `00:00`이라 날짜가 어긋나 보인다 | 디자이너 검토 |
| 9 | 마감 임박 강조 경계 | **잔여 1시간** (§2.3). 3시간이면 목록 대부분이 강조돼 강조가 죽는다 | 디자이너 검토 |
| 10 | 수락 다이얼로그 단일 CTA (취소 버튼 없음) | 단일 CTA — 배경 탭/시스템 백이 취소 경로 (§3.2) | 디자이너 검토 |
| 11 | 문구 톤 — 반말(챌린지 화면) vs 존댓말(친구 화면) | 화면별 원본 톤 유지 | 디자이너 — 별건으로 전체 톤 정리 필요 시 backlog |
| 12 | 마감 캡션 문구 "선택한 자정까지가 챌린지 기간이야" | 신규 작성. "자정이 지나면 판정" 같은 표현은 판정이 비범위라 피했다 | 디자이너 검토 |
| 13 | 도전장 카드 액션 카드 내부 하단 2-up (친구 요청 카드는 우측 인라인) | 카드 내부 하단 2-up (§2.3 근거) | 결정 완료 |
| 14 | 도전장 0건 시 전용 빈 상태 카드 | 만들지 않음 — 섹션 미노출 (§2.4) | 결정 완료 |
| 15 | 홈 일러스트 자산 | 기존과 동일 — Material 아이콘 임시. 일러스트 합류 시 교체 | backlog |

---

## 10. Lovable working tree 변경 요약

```
modified:   src/routes/challenge-new.tsx   (DeadlineType/DEADLINE_OPTIONS/deadlineHint + MAX_LEN
                                            + deadlineType state + canProceed(trim 검증)
                                            + DeadlineSelector / CharCounter sub-component
                                            + step2 마감 표시 바인딩)
modified:   src/routes/index.tsx           (ReceivedChallenge 타입 + 목데이터
                                            + ReceivedChallengesSection / ReceivedChallengeCard
                                            + AcceptChallengeDialog(Radix dialog)
                                            + isFirstUser 판정 보정 + 여백 조건부
                                            + timeLeft 접미사 제거 + urgent 강조)
```

- **미변경**: `src/routes/friends.tsx` (패턴 참조만), `src/components/**`, `src/styles.css` (**신규 토큰 0건**).
- 메모리 규칙(`feedback_lovable_mobile_sync.md`)에 따라 Lovable working tree로만 두고 자체 git 커밋·push는 하지 않는다. PM hub 컨트롤러가 일괄 처리.

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-07-28 14:10 | **v1 최초 작성** — T-D1(`challenge-new.tsx` 마감 2지선다 UI, step2 보존) / T-D2(홈 받은 도전장 섹션 + 카드) / T-D3(수락 미션 입력 **바텀시트** 신규 설계 + 근거 4건). Compose 컴포넌트 5종 props·토큰·상태 단일 출처. 신규 토큰 0건. 모듈 배치 불일치(spec T-M3 vs 실제 선례) §7 제기. ⚠️ 확인 필요 12건 §9. | design-bridge |
| 2026-07-28 14:40 | **v2 — mobile-dev 플랫폼 제약 지적 3건 반영.** (1) **수락 UI 바텀시트 → 다이얼로그 변경** — §3 전면 재작성. `challenge-app`에 `ModalBottomSheet` 선례 0건(grep 확인) + CMP 1.10.3 iOS IME 리스크 + `MainScreen.kt:142`의 기존 `imePadding()`, 그리고 **705 에러 다이얼로그가 어차피 필요**하므로 시트를 추가하면 선례 0건 오버레이 프리미티브를 2개 들이게 된다는 점이 결정적. v1의 1순위 근거("시트가 IME에 유리")가 반대였음을 기록. 컴포넌트명 `AcceptChallengeSheet` → `AcceptChallengeDialog`. `ChallengeErrorDialog`(§4.6) 신규 추가. (2) **`DeadlineSelector`에 실제 마감 시각 부기** — `"7/28 24:00"`, 옵션 높이 48 → 60.dp, 2줄 구성. spec 결정 3(심야 생성 방지) 취지 보존. (3) **`" 남음"` 접미사 제거** — `toRelativeKoreanString()`이 `"곧 마감"`/`"마감"`도 반환해 문장이 깨지는 v1 명세 오류 정정. 추가: 마감 임박 강조 규칙(잔여 1시간 경계 → `error`) 신설, step1 글자 수 카운터 명세(trim 기준 + 하드캡), step1 CTA disabled 조건을 trim 기준으로 정정. §7 모듈 배치는 spec.md T-M3 정정으로 합의 완료 처리. ⚠️ 확인 필요 15건 §9. | design-bridge |
| 2026-07-28 15:10 | **v3 — api-contract `confirmed` 반영 (mobile-dev 지적).** 계약 §공통 규약 2로 **모바일이 `code`를 소비하지 않음**이 확정(`suspendOnFailureWithErrorHandling(onError: (String) -> Unit)`이 `CustomError`의 code를 버리는 프로젝트 표준). (1) **`ChallengeErrorDialog`(§4.6) 폐기** — 705 전용 확인 다이얼로그 불필요. 본 feature가 새로 만드는 오버레이는 `AcceptChallengeDialog` 하나뿐. (2) **§3.1의 v2 결정 근거 중 "705 다이얼로그가 어차피 필요 → 시트까지 넣으면 프리미티브 2개"를 무효 처리.** 전제가 무너졌음을 명시하고, 다이얼로그 채택 결론은 나머지 근거(시트 선례 0건 + CMP iOS IME 리스크 + 기존 `imePadding()` + 입력 1개)로 유지. (3) §3.3 상태표의 700/705 2행을 **"실패(코드 무관)" 1행**으로 통합 + 실패 시 다이얼로그를 닫는 이유와 입력값 손실 트레이드오프 명시. (4) §1.3 / §5.6 / §6 / §8 #4의 700·705 서술 정정. 모든 실패 문구는 **서버 `message` 그대로** — 클라이언트가 문구를 만들지 않는다. | design-bridge |
