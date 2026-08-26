# Design — loser-ranking (개돼지 랭킹)

- **디자인 소스**: `challenge-design/oathbound-challenges` (`.claude/config/repos.json` → `design.export_dir`)
- **참조 route**: `src/routes/ranking.tsx` (116줄, **전체가 이번 범위**)
- **대조 route**: `src/routes/friends.tsx` · `mypage.tsx` · `notifications.tsx` (§1.1 헤더 이형 판정 근거)
- **토큰 원본**: `src/styles.css` → 카탈로그 [`docs/design-system/tokens.md`](../../design-system/tokens.md) · [`colors.md`](../../design-system/colors.md)
- **교체 대상 화면**: `feature/ranking/src/commonMain/kotlin/com/lwg/challenge/feature/ranking/RankingScreen.kt`
  (현재 `PlaceholderScreen(title = "랭킹")` **한 줄**)
- **스냅샷 일시**: 2026-08-26 13:46:29
- **선행 문서**: [spec.md T-D1](./spec.md) · [api-contract.md](./api-contract.md)(draft)
- **형식 선례**: [challenge-verification/design.md](../challenge-verification/design.md)

> 값을 이 문서에 복붙하지 않는다. 색·타이포·radius 의 실제 값은 위 카탈로그가 단일 출처이고,
> 여기서는 **어떤 의미 토큰을 어디에 쓰는지**만 지정한다.

---

## §0 이 문서의 위치

랭킹은 **4탭 중 마지막 남은 placeholder** 다. 도메인~remote 계층이 전부 신설이고 화면도 전부 신설이라
"기존 화면을 고친다"가 아니라 **빈 화면을 채운다**. 그만큼 이 문서가 정하지 않으면 정해지는 곳이 없다.

Lovable `ranking.tsx` 는 **완성본**이다 — 헤더·포디움·명단이 전부 그려져 있다. 이 문서는 그것을
Compose 관점으로 옮긴 것이고, **정본에서 벗어나는 지점 4곳**(§1.2.4 받침대 · §1.2.5 1위 캡션 ·
§2 애니메이션 · §3.2 참가자 3명 미만)은 전부 사유와 함께 명시했다.

🔴 **정본이 답하지 않는 것이 하나 있다 — 참가자가 3명 미만일 때.** `ranking.tsx:25` 는
`const [first, second, third] = rankings` 로 목데이터 6건을 구조분해한다. **친구가 0~1명이면
`second`/`third` 가 `undefined` 가 되어 정본은 그대로는 성립하지 않는다.** 그리고 그게 신규 사용자의
기본 상태다. §3.2 가 이 분기를 정의한다.

---

## §1 화면 구성 분해

### §1.0 골격

Lovable 은 `app-container`(max-width 430px) 안에 sticky header + 본문 + `<BottomNav />` 를 둔다.
네이티브에서는:

- **컨테이너 폭 제약은 무시**한다 (tokens.md §6 — 웹 프리뷰용).
- 🔴 **`<BottomNav />` 와 `pb-24` 를 옮기지 않는다.** 바텀바는 `MainScreen` 이 Scaffold 의 `bottomBar`
  로 이미 그리고 있고(`MainScreen.kt:174-181`), 하단 인셋도 `consumeWindowInsets(innerPadding)` 으로
  이미 처리된다(`MainScreen.kt:196-201`). 화면이 또 그리면 바가 두 개가 되고 인셋이 이중 적용된다.
- 좌우 gutter는 `px-5` = **20dp**. 친구/홈과 같은 값이라 변경 없음.

```
ChallengeScaffold
├── topBar: RankingTopBar (제목 + 부제)        §1.1
└── content: LazyColumn                          ← 명단이 길어질 수 있다
    ├── item  PodiumCard        §1.2   (참가자 3명 이상일 때만 — §3.2)
    ├── item  "수치의 명단" 섹션 제목  §1.3.0
    ├── items LoserRankRow × N   §1.3
    └── item  RankingEmptyState  §3.2  (참가자 2명 이하일 때)
```

- `LazyColumn` 을 쓰는 이유: 명단이 **나 + accepted 친구 전원**이라 상한이 없다. 지금 규모에선
  `Column(verticalScroll)` 로도 되지만, 친구 목록 화면이 이미 `LazyColumn` 이라 같은 쪽에 맞춘다
  (`FriendsScreen.kt:43`).
- `contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp)` — 친구 화면과 동일.
- 카드 2종(포디움·명단 행) 모두 Lovable `glass-card` = 배경 + 1dp 보더 + radius 16dp(`--radius-xl`)
  + card shadow. 모바일은 기존 `FriendListItem`/`HomeEmptyState` 선례를 따라
  **`colorScheme.surface` 평면색 + 1dp `outline` 보더**를 쓴다 (§6 에 gradient·shadow 미적용 사유).

### §1.1 헤더 — 이 앱에서 **부제가 있는 유일한 탭 헤더**

- **참조**: `ranking.tsx:29-32`
- **의도**: 이 탭이 *"승자 랭킹이 아니라 패자 랭킹"* 임을 진입 즉시 못박는다. 부제가 그 일을 한다.

```
제목   "개돼지 랭킹 🐷"
부제   "패배의 왕좌 — 많이 진 놈이 대장"      ← 상단 2dp
```

| 요소 | Lovable | 토큰 |
|---|---|---|
| 제목 | `text-xl font-extrabold` | `typography.bold20` / `colorScheme.onBackground` |
| 부제 | `text-[11px] text-muted-foreground mt-0.5` | `typography.medium12` / `colorScheme.onSurfaceVariant`, 상단 2dp |

✅ **`text-[11px]` → `medium12` 근사는 이미 확정된 관례다.** `ChallengeCard.kt:182` 가
`// design.md: text-[11px] → medium12 근사 (tokens.md §5.2)` 주석과 함께 그렇게 쓰고 있다.
**새로 판단하지 않고 그대로 승계한다.** (11px 는 Tailwind 비표준이고 카탈로그에 없다 — §6.1)

🔴 **다른 세 탭은 부제가 없다.** `friends.tsx:104-108` / `mypage.tsx:32-34` /
`notifications.tsx:27-29` 는 전부 `<h1>` 한 줄뿐이고, 그래서 모바일도
`ChallengeTopBar(title = "친구")` 한 줄로 끝냈다(`FriendsRoute.kt:53`). **랭킹만 2줄이다.**

⚠️ **그래서 `ChallengeTopBar` 를 그대로 쓸 수 없다** — `title: String` 한 줄만 받는다.
`ChallengeBaseTopBar` 의 `title` 슬롯에 `Column(제목 + 부제)` 를 넣는다.

🔴 **높이 검증이 필요하다.** `ChallengeBaseTopBar` 는 `.height(56.dp)` **고정**이다
(`TopBar.kt:55`, `ChallengeTopBarDefaults.Height`). 기본 스케일에서는
`bold20`(lineHeight 28) + 2dp + `medium12`(lineHeight 16) = **46dp** 로 들어가지만,
**폰트 스케일 1.3x 면 약 59dp 로 넘쳐 잘린다.** mobile-dev 는 **큰 폰트 스케일 프리뷰로 확인**하고,
잘리면 **부제를 본문 최상단으로 내린다**(제목만 상단바). 공용 56dp 를 랭킹 사정으로 바꾸지 마라 —
전 화면이 따라 움직인다.

- 상단바 색은 `ChallengeTopBar` 기본값(`colorScheme.surface`)을 따른다. Lovable 의
  `bg-background/80 backdrop-blur-xl` 은 **블러를 재현하지 않는다** — 친구 화면이 이미 불투명
  `surface` 로 출시돼 있고, 두 탭이 달라지는 쪽이 나쁘다.

### §1.2 Top3 포디움

- **참조**: `ranking.tsx:34-74`
- **의도**: 명단을 읽기 전에 **개돼지왕이 누구인지**를 한 눈에 세운다. 1위만 규격·색·모션이 전부 다르다.

카드 — `glass-card p-6` = 패딩 **24dp**, 상단 16dp(`mt-4`).

```
Row(verticalAlignment = Alignment.Bottom, 중앙 정렬, spacedBy 16dp)   ← items-end, gap-4
├── Column(center)  2위
├── Column(center)  1위 (개돼지왕)
└── Column(center)  3위
```

🔴 **`items-end`(하단 정렬)가 포디움의 전부다.** 받침대 높이가 **64 / 96 / 48dp**(2·1·3위)로 달라서
바닥을 맞추면 자동으로 단이 생긴다. Compose `Row(verticalAlignment = Alignment.Bottom)` 이 그대로 같은 일을 한다.
1위 Column 의 `-mt-4` 는 **옮기지 않는다** — 하단 정렬 상태에서 음수 top margin 은 요소를 위로
더 뻗게 할 뿐이고, Compose 에서는 키 큰 Column 이 이미 위로 뻗는다. 옮기면 오히려 16dp 가 이중으로 붙는다.

#### §1.2.1 2위 / 3위 (동일 규격, 받침대 높이만 다름)

| 요소 | Lovable | 토큰 |
|---|---|---|
| 아바타 | `w-14 h-14 rounded-xl bg-secondary` + 이모지 `text-xl` | `ProfilePlaceholder(size = 56.dp, shape = RoundedCornerShape(16.dp), textStyle = medium20)` — 배경은 기본값 `colorScheme.secondary` |
| 이름 | `text-xs font-bold mt-2` | `typography.bold12` / `colorScheme.onBackground`, 상단 8dp |
| 캡션 | `text-[10px] font-medium text-destructive` — `🐷{losses}패` | `typography.medium10` / `colorScheme.error` — 🔴 **🐷 를 뗀다**, `{losses}패`. §1.2.6 |
| 받침대 | `w-16` × (`h-16` 2위 / `h-12` 3위) `bg-secondary/50 rounded-t-lg mt-2` | **64dp × (64dp / 48dp)**, 상단 8dp, `RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp)`, 배경 `colorScheme.surfaceVariant` |
| 받침대 아이콘 | `Medal` (20px 2위 / 18px 3위) `text-muted-foreground` | `Icons.Filled.MilitaryTech` 20dp / 18dp, `colorScheme.onSurfaceVariant` — ⚠️ §7-⑤ |

- `bg-secondary/50` → **`surfaceVariant` 로 대체**한다. [challenge-verification/design.md §1.3](../challenge-verification/design.md)
  이 같은 대체를 이미 결정했다 — surface 위에 secondary 50% 를 합성한 결과가 `surfaceVariant`(gray4)와
  육안 구분이 안 되고, 알파 합성을 도입하지 않는 쪽이 토큰이 깨끗하다.
- `rounded-t-lg` = `--radius-lg` = **12dp**, **상단 두 모서리만**. 아바타의 `rounded-xl`(16dp)과 다르다.

#### §1.2.2 1위 (개돼지왕)

| 요소 | Lovable | 토큰 |
|---|---|---|
| 🐷 왕관 | `text-2xl mb-1 animate-wiggle` | `typography.bold24`, 하단 4dp, **wiggle 적용** — §2.1 |
| 아바타 | `w-16 h-16 rounded-xl fire-gradient` + 이모지 `text-2xl` + `animate-pulse-fire` | `ProfilePlaceholder(size = 64.dp, shape = RoundedCornerShape(16.dp), backgroundColor = ...)` — 🔴 배경이 **Brush** 라 파라미터로 안 된다, §4.2. **pulse-fire 는 미적용** — §2.2 |
| 이름 | `text-sm font-extrabold mt-2` | `typography.bold14` / `colorScheme.onBackground`, 상단 8dp |
| 캡션 | `text-[10px] font-medium text-destructive` — `🐷{lossStreak}연패 · {losses}패` | `typography.medium10` / `colorScheme.error` — 🔴 조건부, §1.2.5 |
| 받침대 | `w-20 h-24 fire-gradient/20 rounded-t-lg mt-2 opacity-40` | **80dp × 96dp**, 상단 8dp, radius top 12dp — 🔴 §1.2.4 |
| 받침대 아이콘 | `Flame` 24px `text-primary` | `Icons.Filled.LocalFireDepartment` 24dp, `colorScheme.primary` |

- 1위 아바타의 `fire-gradient` = `--gradient-fire` = **`ChallengeTheme.brushes.fire`**.
  카탈로그에 이미 매핑돼 있다([tokens.md §2](../../design-system/tokens.md) · [colors.md §3](../../design-system/colors.md)).
  로그인 스탬프가 쓰는 것과 같은 Brush 다(`SoulStampLogo.kt:66,74`). **신규 토큰 아님.**
- **1위만 fire, 2·3위는 secondary 평면색.** 이 대비가 "개돼지왕"의 시각적 근거 전부다 —
  모션을 뺀 뒤에도(§2.2) 이 대비는 남는다.

#### §1.2.3 이모지 아바타 → 이니셜 placeholder

Lovable 은 인당 이모지(🤓😊🤗😤😏😎)를 아바타로 쓴다(`ranking.tsx:16-21`). **목데이터다 —
도메인에 이모지 필드가 없다.**

→ **닉네임 첫 글자 `ProfilePlaceholder` 로 대체**한다. VS 헤더가 같은 판단을 이미 내렸고
([challenge-verification/design.md §7-④](../challenge-verification/design.md)), 친구 목록도
같은 컴포넌트를 쓴다(`FriendListItem.kt:48`).

`profileImageUrl` 은 계약에 있지만 **이번에도 렌더하지 않는다.** 🔴 **다만 그 사유가 2026-08-26 에
통째로 바뀌었다** — 이 문서 초판이 적었던 두 전제가 **둘 다 사실이 아니다**. §1.2.3.1 참조.

##### §1.2.3.1 🔴 초판의 전제 2개가 무너졌다 — 결론은 유지, 사유는 교체

| 초판이 적은 전제 | 실측 (2026-08-26) |
|---|---|
| *"원격 이미지 로더(Coil) 배선이 아직 0건"* | ❌ **배선돼 있다.** `App.kt:77` `setSingletonImageLoaderFactory` + `KtorNetworkFetcherFactory`, `VerificationPhoto.kt:95` 가 `SubcomposeAsyncImage` 로 실사용 중. challenge-verification 이 인증 사진 때문에 깔았다 |
| *"URL 은 사실상 항상 null"* (rank-backend 초기 진술) | ❌ **실제로 들어온다.** 실서버 응답의 rank 3 이 `"http://img1.kakaocdn.net/..."` — 실사용자 계정의 카카오 CDN URL |

**두 사유가 다 죽었는데도 placeholder 를 유지하는 이유는 따로 있다:**

🔴 **URL 이 `http://` 평문이라, 지금 그리면 iOS 에서만 깨진다.**

| 플랫폼 | 평문 HTTP 로드 | 근거 |
|---|---|---|
| **Android** | ✅ **된다** | `network_security_config.xml:10` 이 `<base-config cleartextTrafficPermitted="true" />` — 전 호스트 허용 |
| **iOS** | ❌ **차단된다** | `Info.plist` 에 ATS 키가 **의도적으로 없다.** 주석이 이유를 적어 뒀다 — *"iOS 10+ 는 **숫자 IP** 로의 평문 로드를 ATS 로 막지 않는다"*. 그건 로컬 개발 서버(사설 IP) 얘기고, **`img1.kakaocdn.net` 은 도메인명이라 ATS 가 그대로 막는다** |

**이게 최악의 실패 형태다** — 한쪽 플랫폼에서만 깨진다. Android 로 확인하면 통과하고, iOS 에서만
아바타가 비어 보인다. 게다가 `Info.plist` 주석이 *"운영은 HTTPS 도메인을 쓰므로"* 를 전제로 깔고 있는데,
**카카오 CDN 의 http URL 이 그 전제를 깬다.**

**선결 조건**: 🔴 **서버가 `profileImageUrl` 을 `https` 로 정규화해서 내려주는 것**
(⚠️ **이 feature 의 계약 요구가 아니다** — 백로그 "아바타 활성화" 항목의 선결 조건이다. §8.1).
그게 되면 앱은 cleartext 예외를 **한 줄도 열 필요가 없다.** 반대로 앱에서 ATS 예외를 여는 방향은
**전 호스트 평문을 iOS 에도 여는 것**이라 훨씬 나쁘고, 스토어 심사 축까지 딸려온다.

**그 뒤에도 랭킹이 단독으로 켜지지는 않는다** — `ProfilePlaceholder` 는 **4개 feature 가 쓰는 공용
컴포넌트**라 여기에 이미지 로드를 얹으면 홈·친구·친구검색·랭킹이 동시에 바뀐다.
[challenge-verification spec §0.4](../challenge-verification/spec.md)가 *"세 화면을 동시에 바꾸면
회귀 표면이 넓어진다"* 로 미룬 그 작업이고, **랭킹 PR 에 묶을 크기가 아니다.**
→ ✅ **2026-08-26 [백로그 "`profileImageUrl` 화면 적용"](../../backlog.md) 항목에 반영 완료** (pm-lead).
차단 사유가 *"Coil 배선 0건"* 에서 위 두 줄(**서버 https 정규화** → **`ProfilePlaceholder` 공용 변경**)로
전면 갱신됐고, **랭킹 화면도 활성화 대상에 포함**됐다.

⚠️ **옛 백로그 항목 "원격 이미지 로더 도입" 을 찾지 마라 — 2026-08-25 challenge-verification 이 해소하며
닫혔다.** 살아 있는 항목은 위 이름이다.

🔴 **구현 세부(https 동일 서빙 실측 · 유입 1곳 · `fname=` 이중 `http` 함정)는 그 백로그 항목이 갖는다.
여기에 옮겨 적지 않는다** — 두 벌이 되면 갈린다. 이 문서가 그 사실들에 대해 할 일은 *"이번에 아바타를
켜지 않는다"* 까지고, *"어떻게 켜느냐"* 는 그 항목 소관이다.

⚠️ 이모지를 실제 기능(프로필 이모지 선택)으로 도입할 계획이 있는지는 확인 대상 — §7-④.
[spec.md 비범위](./spec.md)는 *"프로필 이모지 선택 기능 — 도메인에 필드 없음"* 으로 이미 접었다.

#### §1.2.4 🔴 1위 받침대 — 정본의 클래스가 **렌더되지 않는다**

`ranking.tsx:58` 은 `className="w-20 h-24 fire-gradient/20 rounded-t-lg mt-2 ... opacity-40"` 이다.
**`fire-gradient/20` 은 Tailwind 가 생성하지 않는 클래스다.**

근거 (실측):
- `.fire-gradient` 는 `styles.css:134,153` 에서 **`@layer utilities` 안의 평범한 CSS 클래스**로 정의돼 있다.
  Tailwind 의 색상 유틸리티가 아니므로 **`/20` 투명도 수식자가 붙지 않는다.**
- 디자인 레포 전체에서 `fire-gradient/` 형태를 쓰는 곳은 **이 한 줄뿐이다** (`grep -rn "fire-gradient/" src/` → 1건).
  나머지는 전부 수식자 없는 `fire-gradient`.

**렌더 결과**: 1위 받침대는 **배경이 없고**, `opacity-40` 이 걸린 Flame 아이콘만 80×96 공간에 떠 있다.
2·3위에는 받침대가 보이는데 **1위 자리만 비어 보인다.**

**판정 — 의도를 구현한다**: 받침대 배경을 **`brushes.fire` 20% 알파**로 그린다.
사유: ① 클래스 이름이 의도를 명시한다(`fire-gradient` + `/20`) ② 셋 중 1위 받침대만 사라진 포디움은
디자인 의도로 볼 수 없다 ③ 1위만 fire 계열이라는 §1.2.2 의 대비와 일관된다.
`opacity-40` 은 **아이콘에만** 적용한다(`LocalFireDepartment` tint = `primary.copy(alpha = 0.40f)`) —
받침대 전체에 걸면 20% 배경이 8% 가 되어 다시 안 보인다.

⚠️ **디자이너 확인 대상 (§7-①).** 이건 추측이 아니라 *"쓰여 있는 대로 하면 안 보인다"* 는 실측이고,
확인이 오기 전까지 위 기본값으로 진행한다.

#### §1.2.5 🔴 1위 캡션 — `0연패` 가 나오는 구멍

정본 `ranking.tsx:55-57` 은 1위 캡션을 **무조건** `🐷{lossStreak}연패 · {losses}패` 로 그린다.
목데이터의 1위는 항상 `lossStreak: 7` 이라 이 구멍이 드러나지 않는다.

**연패 0 인 사람이 1위가 될 수 있다** — 많이 졌지만 최근에 이긴 사람이 1위다.
그러면 `🐷0연패 · 25패` 가 찍힌다.

✅ **가정이 아니라 확정이고, 실데이터에 이미 있다 (2026-08-26).** 이 문단은 원래 *"총 패배가 1차
정렬 키라면"* 이라는 조건부로 썼는데, rank-backend 가 정렬을 **`losses DESC` 1차 키**로 확정했다.
**연패 0 인 1위는 정상 발생한다** — 계약 §1 에도 *"`currentLossStreak == 0` 인 1위는 정상적으로
발생한다"* 로 명시됐다(나중에 버그로 오해받지 않게).

🔴 **개발 DB 실측 응답의 1위가 정확히 그 케이스다**:

```
rank 1  테스터1  losses=4  lossRate=80   currentLossStreak=0   ← 연패 절 생략 대상
rank 2  테스터2  losses=3  lossRate=100  currentLossStreak=3
```

**조건부를 안 넣었으면 첫 실행에서 바로 `🐷0연패 · 4패` 를 밟는다.** 아래 조건부 캡션은 방어 코드가
아니라 **지금 당장 발동하는 분기**다 — 이 문단이 그 증거이니 코드 주석에도 같이 남겨라(§9).

**판정**: `lossStreak > 0` 일 때만 연패 절을 붙인다.

| lossStreak | 1위 캡션 |
|---|---|
| `> 0` | `🐷{lossStreak}연패 · {losses}패` |
| `0` | `{losses}패` |

**정본과 어긋나지 않는다** — 같은 화면의 명단 행이 이미 `r.lossStreak > 0 &&` 조건부다
(`ranking.tsx:106`). 포디움에만 그 조건이 빠진 것이고, **같은 규칙을 같은 화면에 일관되게 적용**하는 것이다.

#### §1.2.6 🔴 🐷 이모지가 두 뜻으로 쓰인다 — **연패 쪽으로 통일**

rank-mobile 실측 지적(2026-08-26). 정본에서 🐷 뒤의 숫자가 자리마다 다른 것을 가리킨다:

| 자리 | 정본 | 🐷 뒤의 수 |
|---|---|---|
| 포디움 1위 | `🐷{lossStreak}연패 · {losses}패` | **연패** |
| 포디움 2·3위 | `🐷{losses}패` | **패배 수** |
| 명단 뱃지 | `🐷{lossStreak}` (`lossStreak > 0` 일 때만) | **연패** |

**판정: 🐷 뒤에 오는 수는 언제나 연패다.** → **포디움 2·3위 캡션에서 🐷 를 뗀다** (`{losses}패`).

근거: ① 3자리 중 2자리가 연패 축이다 ② **명단 뱃지가 `lossStreak > 0` 조건부라는 사실이 🐷 의 의미를
이미 규정한다** — "연패 중인 사람에게만 붙는 표식"이다. 조건부가 아니었다면 단순 장식으로 볼 수 있었다
③ 패배 수는 `패` 라는 단위 글자를 이미 갖고 있어 🐷 없이도 읽힌다.

✅ **§1.2.5 와 맞물려 캡션 형식이 하나로 수렴한다.** 연패가 0 이면 🐷 절이 통째로 사라지므로:

| | 캡션 |
|---|---|
| 1위, `lossStreak > 0` | `🐷{lossStreak}연패 · {losses}패` |
| 1위, `lossStreak == 0` | `{losses}패` |
| 2·3위 | `{losses}패` |

즉 **연패 중이 아니면 세 자리의 캡션 형식이 완전히 같아진다.**

🔴 **2·3위에 연패를 "추가"하지는 않는다.** 목데이터는 2위 `lossStreak: 4` · 3위 `lossStreak: 2` 를
**갖고 있으면서도 화면에 쓰지 않는다**(`ranking.tsx:17-18, 66`). 데이터가 없어서가 아니라 안 쓴 것이므로
**포디움에서 연패 표기는 개돼지왕의 것**이라는 의도로 읽는다. 여기서 건드리는 건 🐷 의 의미 통일뿐이다.

⚠️ **디자이너 확인 대상 (§7-⑩).**

### §1.3 수치의 명단

- **참조**: `ranking.tsx:76-111`
- **의도**: 포디움이 못 담는 **전원**을, 내가 몇 위인지까지 포함해 줄 세운다.

🔴 **명단은 1위부터 전원을 포함한다 — 포디움과 중복된다.** `ranking.tsx:79` 는 `rankings.map` 으로
**슬라이스 없이** 전부 그린다. 포디움의 1·2·3위가 명단에도 다시 나온다. **이건 정본이다 —
`drop(3)` 으로 "고치지" 마라.** 포디움은 요약이고 명단은 전체다.

#### §1.3.0 섹션 제목

| 요소 | Lovable | 토큰 |
|---|---|---|
| "수치의 명단" | `text-sm font-bold text-muted-foreground mb-3` | `typography.bold14` / `colorScheme.onSurfaceVariant`, 상단 24dp(`mt-6`), 아래 12dp |

#### §1.3.1 행 (`LoserRankRow`)

카드 — `glass-card p-3.5` = 패딩 **14dp**, 행 간격 8dp(`space-y-2`).

```
Row(verticalAlignment = CenterVertically, spacedBy 12dp)
├── rank 숫자   (28dp 폭, 중앙)
├── 아바타      (40dp)
├── Column(weight 1f)  { 닉네임 / 캡션 }
└── 연패 뱃지   (조건부)
```

| 요소 | Lovable | 토큰 |
|---|---|---|
| 카드 보더 | `border-destructive/20` (rank ≤ 3) / 기본 | rank ≤ 3 → `BorderStroke(1.dp, colorScheme.error.copy(alpha = 0.20f))`, 그 외 → `colorScheme.outline` |
| rank 숫자 | `w-7 text-center text-sm font-extrabold` | 28dp 폭, 중앙 정렬, `typography.bold14`, 색은 아래 분기 |
| 아바타 | `w-10 h-10 rounded-xl bg-secondary` + 이모지 `text-lg` | `ProfilePlaceholder(size = 40.dp, shape = RoundedCornerShape(16.dp), textStyle = medium16)` |
| 닉네임 | `text-sm font-bold` | `typography.bold14` / `colorScheme.onBackground`, `weight(1f)`, 1줄 `Ellipsis` |
| 캡션 | `text-[10px] text-muted-foreground` — `{losses}패 · 패배율 {lossRate}%` | `typography.medium10` / `colorScheme.onSurfaceVariant` — 🔴 기록 없음 분기, §1.3.3 |
| 연패 뱃지 | `text-xs font-semibold text-destructive` — `🐷{lossStreak}`, **`lossStreak > 0` 일 때만** | `typography.medium12` / `colorScheme.error` |

**rank 숫자 색 분기** (`ranking.tsx:85-93`):

| rank | Lovable | 모바일 |
|---|---|---|
| 1 | `text-destructive` | `colorScheme.error` |
| 2 | `text-muted-foreground` | `colorScheme.onSurfaceVariant` |
| 3 | `text-warning` | `colorScheme.warning` |
| 4+ | `text-muted-foreground` | `colorScheme.onSurfaceVariant` |

⚠️ **2위와 4위 이하가 같은 색이다** — 결과적으로 강조되는 건 1위(error)와 3위(warning)뿐이고
**2위만 강조가 빠진다.** 카드 보더는 `rank <= 3` 로 셋을 묶는데 숫자 색은 2위를 안 묶는 셈이라
불일치로 보인다. **정본 그대로 구현하되** 의도인지 확인 대상 — §7-③.

- 알파 보더(`error.copy(alpha = 0.20f)`)는 **앱에 선례가 있다** —
  `FriendsEmptyState.kt:68` / `HomeEmptyState.kt:69` 가 `primary.copy(alpha = 0.10f)` 를 배경에 쓴다.
  §1.2.1 에서 배경 알파 합성을 피한 것과 모순되지 않는다: 거기는 **대체할 의미 토큰이 있었고**(`surfaceVariant`),
  여기는 "error 계열의 옅은 보더"에 대응하는 토큰이 없다.
- **캡션의 `%` 는 앱이 붙인다.** 계약 초안이 `lossRate: 78` (정수)이므로 화면이 `"패배율 ${lossRate}%"`.
  🔴 **앱이 `losses / total` 를 다시 계산하지 않는다** — 정렬 키를 서버가 쥐고 있는데 표시값만
  따로 계산하면 정렬과 표시가 갈린다. §8-② 참조.

#### §1.3.2 "나" 행

Lovable 목데이터의 rank 4 는 `name: "나"` 다(`ranking.tsx:19`). **별도 강조 스타일이 없다 —
닉네임 자리에 `"나"` 가 들어 있는 것이 강조의 전부다.**

✅ **이건 앱의 기존 관례와 정확히 같다.** 챌린지 상세가 `MY_LABEL = "나"`
(`ChallengeDetailState.kt:9`)로 **닉네임을 "나" 로 치환**한다.

**판정 (2종)**:

1. **닉네임을 `"나"` 로 치환**한다 — 명단 행과 **포디움 양쪽 모두**.
2. **명단 행 배경을 `colorScheme.surfaceVariant` 로** 올린다 (다른 행은 `surface`).

🔴 **2번은 판정 전환이다 (2026-08-26, rank-mobile 반론 채택).** 초안은 *"닉네임 치환만, 배경·보더
추가 강조 없음"* 이었다. rank-mobile 이 [spec.md 사용자 시나리오 2](./spec.md)(*"내가 몇 위인지 본다"*)를
근거로 그것만으로 부족하다고 지적했고, 채택한다. 배경은 **보더 규칙(`rank <= 3` → `error` 20%)과
축이 겹치지 않는 유일한 강조**라 내가 top3 여도 두 규칙이 충돌하지 않는다.

🔴 **다만 닉네임 치환이 주(主)고 배경은 보조다.** 치환을 뺄 수 없는 이유:
**포디움에도 내가 있을 수 있는데, 배경 강조는 포디움 열에 적용할 자리가 없다.** 1·2위 자리는 이미
fire/secondary 로 색이 정해져 있다. **닉네임 치환은 명단과 포디움 두 영역에 공통으로 먹는 유일한 축**이다.

⚠️ rank-mobile 이 *"실제로는 내 닉네임이 나오니 못 찾는다"* 고 본 것은 **전제가 다르다** — 이 문서는
`isMe` 행의 표시 이름 자체를 `"나"` 로 바꾼다. 목데이터의 `name: "나"` 는 우연이 아니라 그 동작의 표현이고,
앱에도 같은 관례가 이미 있다(`MY_LABEL`). 아바타 이니셜도 함께 `"나"` 가 된다.

확인 대상 — §7-②.

🔴 **치환은 `isMe` 를 필요로 한다.** `ChallengeDetailViewModel.kt:208` 의 주석이 이유를 적어 뒀다 —
*"관점을 모르면 챌린저를 '나' 라고 부르지 않는다."* 앱이 `userId` 를 대조하려면 내 `userInfo` 가
먼저 로드돼 있어야 하고, 실패하면 **아무도 "나" 가 아닌 목록**이 나온다. §8-① 참조.

#### §1.3.3 🔴 "0전 0패" ≠ "전승 0패" — 화면은 **구분해야 한다**

rank-mobile 실측 지적(2026-08-26). [spec.md 수용 기준](./spec.md)이 *"`user_stats` row 가 없는
유저(챌린지 0회)도 목록에서 빠지지 않는다"* 를 요구하므로 **챌린지를 한 번도 안 한 사람**이 명단에 들어온다.
그런데 지금 캡션은 `{losses}패 · 패배율 {lossRate}%` 한 줄이라:

| | 캡션 |
|---|---|
| 챌린지 0회 | `0패 · 패배율 0%` |
| **12전 전승** | `0패 · 패배율 0%` |

**두 사람이 글자 하나까지 같다. 정반대 상태인데.**

**판정: 구분한다.** 근거:
1. 명단 하단에는 **0패가 여럿 몰린다**(신규 사용자 + 안 지는 사람). 그 구간에서 캡션의 정보량이 0 이 된다.
2. `user_stats` row 부재 유저를 **굳이 목록에 남기기로 한 이유**가 *"친구인데 왜 없지"* 를 막는 것이었다면
   (계약 쟁점 ④), 들어와서 무의미한 행이 되면 목적을 절반만 달성한다.
3. 개돼지 랭킹에서 *"아직 안 해봤음"* 과 *"다 이겼음"* 은 놀림의 대상이 서로 다르다.

**표기**:

| 조건 | 캡션 | 토큰 |
|---|---|---|
| `totalChallenges == 0` | **`아직 기록 없음`** (캡션 전체 대체) | `medium10` / `onSurfaceVariant` — 동일 |
| `totalChallenges > 0` | `{losses}패 · 패배율 {lossRate}%` | 변경 없음 |

🔴 **전승자에게 별도 표기를 주지 않는다.** `12전 무패` 같은 표기는 개돼지 랭킹에서 **무패를 자랑거리로
세우는 것**이라 화면의 축이 뒤집힌다. 그냥 `0패 · 패배율 0%` 로 두고, 명단 최하단이 그 사람의 자리다.

🔴 **이건 계약을 blocking 한다** — 앱이 현재 shape(`losses`/`lossRate`/`currentLossStreak`)으로는
두 상태를 **도출할 수 없다.** `totalChallenges` 를 계약에 추가해야 한다. §8-⑤ 참조.

⚠️ **디자이너 확인 대상 (§7-⑪)** — 문구 `"아직 기록 없음"` 은 제안이다.

---

## §2 🔴 애니메이션 판정

정본은 1위에 두 개를 건다: 🐷 왕관에 `animate-wiggle`, 아바타에 `animate-pulse-fire`.
백로그의 *"FAB `pulse-fire` 애니메이션 미구현 (HomeScreen)"* 과 같은 축이므로 **일관된 선**을 먼저 세운다.

### §2.0 판정 기준 — 이 앱에는 이미 선이 그어져 있다

| | 실측 |
|---|---|
| `spin-slow`·`wiggle` (transform) | ✅ **구현돼 있다** — `ChallengeTitle.kt:44-53` 이 🔥 이모지를 `Modifier.rotate()` 로 흔든다 |
| `pulse-fire` (box-shadow glow) | ⚠️ **glow 를 그린 곳이 0건이다** — `SoulStampLogo.kt:35-43` 이 glow 대신 **alpha 호흡**(0.85↔1.0, 2000ms)으로 우회했다. 홈 FAB 는 아예 미구현(백로그) |

**선은 "애니메이션이냐 아니냐"가 아니라 "transform/alpha 냐 box-shadow glow 냐"에 그어져 있다.**
그리고 그 선은 카탈로그가 이미 근거까지 적어 뒀다:

- [tokens.md §3](../../design-system/tokens.md): Glow shadow — *"Compose 기본 shadow 로 표현 어려움 —
  Canvas 로 blur glow 를 그리거나 생략. ⚠️ 모바일 성능 고려."*
- [tokens.md §7](../../design-system/tokens.md): `wiggle` 이식 난이도 **쉬움**, `pulse-fire` **중간**.
- [colors.md §5-5](../../design-system/colors.md): glow 재현도가 이미 "근사" 로 flag 돼 있다.

→ **판정: transform/alpha 로 표현되는 모션은 구현하고, box-shadow glow 는 보류한다.**

### §2.1 `animate-wiggle` → ✅ **구현.** 새로 만들 것도 거의 없다

CSS: `wiggle 1.5s ease-in-out infinite` — `0%/100% rotate(0) scale(1)`, `25% rotate(-15deg) scale(1.1)`,
`75% rotate(15deg) scale(1.1)` (`styles.css:181-185, 214-217`).

✅ **앱에 이미 번역본이 있다** — `ChallengeTitle.kt:44-53`, 로그인 화면의 🔥 이모지:

| | 앱 기존값 | CSS 원값 |
|---|---|---|
| 주기 | `tween(1_500)` + `RepeatMode.Reverse` | `1.5s` |
| 진폭 | `-8f ..= 8f` | `±15deg` |
| scale | 없음 | `1.1` |
| 적용 | `Modifier.rotate(rotation)` (이모지 `Text`) | 이모지 `<span>` |

**판정: 기존값(±8도, 1500ms, scale 없음)을 그대로 쓴다.** CSS 원값으로 맞추지 않는다 —
로그인과 랭킹이 **같은 "이모지 흔들림"** 인데 진폭이 다르면 한 앱에 방언이 둘 생기고, 원값에
맞추려면 **출시된 로그인 화면을 함께 바꿔야** 한다. 랭킹 작업이 건드릴 범위가 아니다.

**배치**: 기존 구현은 `ChallengeTitle` 안에 인라인돼 있어 재사용이 안 된다.
→ `:core:designsystem` 에 **`Modifier.wiggle()`** 로 추출한다(§4.3). 도메인 의존이 없는 순수 모션이라
`:core:ui` 가 아니라 `:core:designsystem` 이 맞는 자리다.

⚠️ **로그인은 출시 화면이다.** 추출하면서 `ChallengeTitle` 도 새 Modifier 를 쓰게 바꾸되
**로그인 프리뷰를 확인하고 리포트에 남겨라.** 회귀 위험이 크다고 판단되면 **랭킹만 새 Modifier 를
쓰고 로그인은 두는 것도 허용**한다 — 그 경우 사본이 남으므로 백로그에 통합 항목을 등재한다.
([challenge-verification/design.md §4.3](../challenge-verification/design.md) 과 같은 처리)

### §2.2 `animate-pulse-fire` → ❌ **보류. 정적 대체**

CSS: `0%/100% box-shadow 0 0 20px oklch(0.72 0.19 45 / 20%)`, `50% box-shadow 0 0 40px ... / 40%`
(`styles.css:166-169`). **transform 이 아니라 box-shadow 다.**

**판정: 구현하지 않는다.** 근거 4가지:

1. **Compose 에 대응물이 없다.** `Modifier.shadow` 는 elevation 그림자지 발광이 아니다.
   재현하려면 Canvas 로 blur glow 를 직접 그려야 하고, tokens.md §3 이 그걸 이미 *"성능 고려"* 로 유보했다.
2. **같은 CSS 클래스에 대한 선례가 이미 "보류"다.** 백로그 *"FAB `pulse-fire` 애니메이션 미구현
   (HomeScreen)"* — 홈에서 내린 판정을 랭킹에서 뒤집을 이유가 없다.
3. **로그인이 이미 glow 를 안 그리는 쪽으로 번역했다.** `SoulStampLogo.kt` 는 `animate-pulse-fire`
   자리에 alpha 호흡을 넣었다. 앱에는 *"pulse-fire = glow 를 그리지 않는다"* 는 방언이 이미 있다.
4. **뺐을 때 잃는 것이 적다.** 1위를 구분하는 건 fire-gradient 배경·더 큰 아바타·🐷 왕관·wiggle
   **네 가지**다. 발광 하나가 빠져도 개돼지왕은 충분히 튄다.

**정적 대체안 (채택)**: 1위 아바타는 **`brushes.fire` 배경**만으로 간다. 추가 발광 없음.

**모션이 필요하다고 판단될 경우의 대체 (2순위)**: `SoulStampLogo.kt:35-43` 의 **alpha 호흡**
(`0.85f ..= 1.0f`, `tween(2_000)`, `Reverse`)을 1위 아바타에 그대로 적용한다 — 주기가 CSS 와 같은 2s 다.
🔴 **어느 경우에도 Canvas blur glow 는 만들지 않는다.**

**기각 — `brushes.glow` 를 1위 아바타 뒤에 정적 후광으로 깔기** (rank-mobile 제안, 2026-08-26):
아이디어는 타당하지만 두 가지로 기각한다. ① `brushes.glow` 는 `Brush.radialGradient(colors)` 를
**center·radius 없이** 만든다(`ChallengeBrushes.kt:29-32`) — 화면 상단 전폭 후광용으로 잡힌 것이고,
[colors.md §5-5](../../design-system/colors.md)가 그 근사를 이미 flag 해 뒀다. 64dp 아바타 뒤에 깔면
CSS 의 `transparent 60%` 와 전혀 다른 그림이 나오고, 맞추려면 결국 center/radius 를 새로 찍어야 한다 —
그건 "정적 대체"가 아니라 새 튜닝이다. ② §2.2 판정의 전제가 *"1위 구분 요소가 이미 넷"* 이라
후광이 주는 증분이 작다. **후광이 꼭 필요하다는 판단이 서면 2순위(alpha 호흡)가 더 싸고 검증돼 있다.**

### §2.3 백로그 FAB 항목에 대한 함의

백로그 항목이 *"Compose에서 LoginScreen pulse-fire 패턴 재사용 후보"* 라고 적혀 있는데,
**LoginScreen 패턴은 glow 가 아니라 alpha 호흡이다.** 항목의 문구가 "미구현"으로 남아 있으면
다음 사람이 Canvas glow 를 만들러 간다. → pm-lead 에 **문구 재정의**를 요청한다(§9 보고 항목).

---

## §3 상태 매트릭스

`RankingUiState` 는 현재 `Loading` / `Data(placeholder)` 뿐이다(`RankingState.kt`). 실패는 홈·친구와
같이 **스낵바**로 낸다 — `HomeViewModel.kt:70,81` → `HomeRoute.kt:39-41` → `mainAction.showSnackBar`.
스캐폴딩에 `RankingUiEffect.ShowMessage` 와 `showMessage()` 가 이미 있다(`RankingViewModel.kt:34-38`).
**Error 화면 상태를 새로 만들지 않는다** — 앱에 그 선례가 없다.

### §3.1 화면 상태 3종

| 상태 | 표현 |
|---|---|
| 로딩 | 중앙 `CircularProgressIndicator(color = colorScheme.primary)` — `FriendsScreen.kt:74-81` 과 동일 |
| 정상 | 포디움(조건부, §3.2) + 수치의 명단 |
| 실패 | 스낵바 + 화면은 로딩 직전 상태 유지. **재시도는 탭 재진입** |

### §3.2 🔴 참가자 수 분기 — 정본에 없고, **신규 사용자의 기본 상태다**

`ranking.tsx:25` 의 `const [first, second, third] = rankings` 는 목데이터 6건을 전제한다.
실제 범위는 **나 + accepted 친구**라 **친구 0명이면 1건, 1명이면 2건**이다.

| 참가자 N | 포디움 | 수치의 명단 | 빈 상태 카드 |
|---|---|---|---|
| **0** (서버가 `[]`) | ❌ | ❌ | ✅ |
| **1** (나 혼자) | ❌ | ✅ 1행 | ✅ 명단 **아래** |
| **2** | ❌ | ✅ 2행 | ✅ 명단 **아래** |
| **3 이상** | ✅ 정본 그대로 | ✅ 전원 | ❌ |

**포디움을 N ≥ 3 에서만 그리는 이유**: 포디움은 **1·2·3위라는 서열의 시각화**다. 자리가 비면
빈 칸이 생겨 고장난 화면으로 보이고, 참가자 1명짜리 "개돼지왕"은 농담이 성립하지 않는다
(자기 자신을 왕으로 세우는 화면이 된다).

**기각한 대안**: *"채워진 자리만 그린다"* — N=2 면 1·2위만, N=1 이면 1위만. 기각 사유: 받침대
높이차(96/64/48)가 만드는 단이 두 칸에서는 그냥 "높이가 다른 상자 둘"로 읽히고, 한 칸에서는
아무 의미가 없다. 포디움을 생략하는 쪽이 화면이 더 정직하다.

⚠️ **디자이너 확인 대상 (§7-⑥).** 정본에 없는 분기이므로 위 기본값으로 진행한다.

### §3.3 빈 상태 카드 문구 (제안)

`FriendsEmptyState` 와 **같은 골격**(64dp 아이콘 박스 + 제목 + 부제 + CTA)을 쓴다.

| | 값 |
|---|---|
| 아이콘 | `Icons.Filled.Group`, 32dp, `primary` (배경 `primary.copy(alpha = 0.10f)`) |
| 제목 | `"아직 줄 세울 친구가 없어요"` — `typography.bold16` / `onBackground` |
| 부제 | `"친구를 등록하면 누가 개돼지왕인지 가려져요"` — `typography.medium12` / `onSurfaceVariant` |
| CTA | `"친구 추가하기"` + `Icons.Filled.PersonAdd` → `Route.Friends.Search` (`LocalNavigateAction`) |
| 보조 CTA | 없음 (`onClickInvite = null`) |

⚠️ **문구는 제안이다** — §7-⑦. 톤은 정본 부제(*"패배의 왕좌 — 많이 진 놈이 대장"*)의 반말·도발조를 따랐다.

---

## §4 Compose 매핑 가이드

### §4.1 그대로 쓰는 것 — 신규 제작 불필요

| 필요 | 기존 자산 | 위치 |
|---|---|---|
| 화면 골격 | `ChallengeScaffold` | `:core:designsystem` |
| 상단바 뼈대 | `ChallengeBaseTopBar` (title 슬롯) | `:core:designsystem` — §1.1 |
| 아바타 | `ProfilePlaceholder(size, shape, textStyle)` | `:core:ui` — 파라미터로 커버, 단 1위 예외 §4.2 |
| 1위 배경 Brush | `ChallengeTheme.brushes.fire` | `:core:designsystem` |
| 불꽃 아이콘 | `Icons.Filled.LocalFireDepartment` | 홈·상세가 이미 쓴다 |
| 로딩 | `CircularProgressIndicator(color = primary)` | `FriendsScreen.kt:74` 패턴 |
| 실패 알림 | `RankingUiEffect.ShowMessage` → `mainAction.showSnackBar` | 스캐폴딩에 이미 있음 |
| 바텀바 | **화면이 그리지 않는다** | `MainScreen` 소관 — §1.0 |

### §4.2 🔴 `ProfilePlaceholder` 는 1위 아바타를 그리지 못한다

`ProfilePlaceholder` 의 배경 파라미터는 **`backgroundColor: Color`** 다(`ProfilePlaceholder.kt:31`).
1위 아바타는 **Brush**(`brushes.fire`) 배경이라 넘길 수 없다.

**권고 — `:core:ui` 의 `ProfilePlaceholder` 를 건드리지 않는다.** 호출부가 4개 feature 라
`Brush?` 파라미터를 추가하면 안 쓰는 화면까지 시그니처가 넓어진다.
→ 랭킹 feature 안에서 **Brush 배경 Box + 이니셜 `Text`** 를 직접 그린다(§4.3 `PodiumAvatar`).
2·3위·명단 행은 `ProfilePlaceholder` 를 그대로 쓴다.

⚠️ 이니셜 렌더 규칙(`nickname.trim().firstOrNull()?.uppercase() ?: ""`)은 **원본과 동일하게** 맞춰라 —
공백 닉네임 처리가 갈리면 1위만 다르게 보인다.

### §4.3 신규 — `feature/ranking/component/`

`component_placement_rule`(feature 전용 컴포넌트는 feature 모듈 `component/` 하위)을 따른다.
아래는 랭킹 화면 밖에서 쓸 데가 없다.

| 컴포넌트 | 역할 |
|---|---|
| `RankingTopBar` | §1.1. `ChallengeBaseTopBar` + Column(제목·부제) |
| `PodiumCard` | §1.2. 하단 정렬 Row + 3열. **N ≥ 3 에서만 호출** |
| `PodiumColumn` | §1.2.1/§1.2.2 **공용 1종.** 순위별 규격을 파라미터로(아바타 크기·받침대 크기·이름 슬롯·왕관 노출) |
| `PodiumAvatar` | §4.2. Brush 배경 지원 아바타 (1위 전용 분기 포함) |
| `LoserRankRow` | §1.3.1. rank 색 분기 + 조건부 연패 뱃지 |
| `RankingEmptyState` | §3.3. `:core:ui` 승격본(§4.4) 호출 래퍼 |

🔴 **`PodiumColumn` 은 반드시 한 종류다.** 1위/나머지로 갈라 놓으면 이름·캡션·받침대의 타이포와
간격이 조용히 갈린다. 1위의 차이는 **① 왕관 유무 ② 아바타 크기·배경 ③ 받침대 크기·색 ④ 캡션 문구**
넷뿐이고 전부 파라미터로 표현된다. (`MissionCard` 1종 + 슬롯과 같은 판단 —
[challenge-verification/design.md §4.2](../challenge-verification/design.md))

### §4.4 신규 — 공용 모듈로 올리는 것 2건

| 대상 | 이동 | 사유 |
|---|---|---|
| **`Modifier.wiggle()`** | 신설 → `:core:designsystem` | §2.1. `ChallengeTitle.kt:44-53` 의 인라인 구현을 추출. 도메인 의존 없는 순수 모션 |
| **`EmptyStateCard`** | `FriendsEmptyState` 를 `:core:ui` 로 이동 + 개명 | §3.3. **랭킹이 4번째 사본이 되는 것을 막는다** — §4.4.1 |

**`EmptyStateCard` 승격이 안전한 이유**: `FriendsEmptyState` 는 이미 완전히 파라미터화돼 있다
(`title`/`subtitle`/`ctaLabel`/`icon`/`onClickCta`/`onClickInvite`). **렌더 코드를 한 줄도 바꾸지 않고
파일만 옮기고 `internal` → `public` 으로 여는 것**이라 친구 화면의 픽셀이 변하지 않는다.
바뀌는 건 import 한 줄뿐이다.
⚠️ 단 보조 CTA 라벨 `"카카오톡으로 초대하기"` 가 하드코딩돼 있다(`FriendsEmptyState.kt:108`) —
승격하면서 **파라미터로 뺀다**. 친구가 같은 문자열을 넘기면 여전히 무변화다.

🔴 **홈의 `HomeEmptyState` 는 이번에 건드리지 않는다.** CTA 가 2개 Row 라 형태가 다르고,
출시된 화면이다. `HomeEmptyState` 의 KDoc 이 *"친구/랭킹 등 다른 화면의 빈 상태에도 재사용 가능하도록
컴포넌트 단위로 분리"* 라고 적어 놓고 실제로는 친구가 사본을 떠 간 상태인데, **그 통합은 별건**이다.
→ pm-lead 가 **백로그에 등재**한다(§9).

#### §4.4.1 🔴 사본은 2개가 아니라 **3개**였고, 이미 갈라졌다

rank-mobile 실측 제보(2026-08-26)를 확인했다. `FriendPickPlaceholderCard.kt:33` 의 KDoc:

> *"`:feature:friends:list` 의 `FriendsEmptyState` 는 internal 이라 재사용할 수 없어 별도로 둔다."*

**세 번째 사본이 이미 있었다.** 랭킹은 4번째가 될 뻔했다. 그리고 셋은 **이미 값이 갈렸다** —
일러스트 아이콘 박스(64dp, `primary` 10% 배경, 아이콘 32dp)까지 똑같은데 **모서리만 다르다**:

| 구현 | 아이콘 박스 shape |
|---|---|
| Lovable 정본 (`friends.tsx:219` · `index.tsx:453`) | `rounded-2xl` = **20dp** |
| `FriendsEmptyState.kt:67` | `RoundedCornerShape(16.dp)` |
| `HomeEmptyState.kt:68` | `RoundedCornerShape(16.dp)` |
| `FriendPickPlaceholderCard.kt:39` | **`CircleShape`** |

**셋 다 정본과 다르고, 셋끼리도 다르다.** 백로그의 `flowUtil` 항목이 적은
*"한 곳이 바뀌면 나머지가 조용히 갈린다"* 가 여기서 이미 일어난 것이다.

🔴 **그렇다고 이번에 20dp 로 맞추지 마라.** 승격의 성격이 *"렌더 코드 무변경 + 파일 이동"* 이라
회귀 위험이 0 인 것이 장점인데, 여기서 shape 을 건드리면 **출시된 친구·홈 화면의 픽셀이 움직인다.**
→ 승격본은 **`FriendsEmptyState` 의 현행 16dp 를 그대로** 들고 가고, 랭킹도 16dp 를 쓴다.
**정본(20dp) 정합은 백로그**로 넘긴다 — 지금 맞추려면 3곳을 고쳐야 하지만, 통합이 끝나면 **1곳**이다.
(이것 자체가 통합의 근거다.)

##### 🔴 승격 시그니처 — `ctaIcon` 도 파라미터로 빼라

두 사본이 **서로 반대되는 것을 파라미터화**해 놨다:

| | 일러스트 아이콘 | CTA 아이콘 |
|---|---|---|
| `FriendsEmptyState` | `icon: ImageVector` **파라미터** | `Icons.Filled.PersonAdd` **하드코딩** |
| `FriendPickPlaceholderCard` | `Icons.Filled.Group` **하드코딩** | `ctaIcon: ImageVector` **파라미터** (*"빈 상태는 친구 추가, 실패는 재시도"*) |

`FriendsEmptyState` 를 **그대로** 올리면 CTA 아이콘이 `PersonAdd` 로 굳는다. 나중에
`FriendPickPlaceholderCard` 를 이관할 때 **시그니처를 또 바꿔야 하고**, 그때는 호출부가 늘어나 있다.

→ 승격하면서 **`icon` · `ctaIcon` · 보조 CTA 라벨 셋 다 파라미터**로 연다.
친구·랭킹이 각각 기존 값을 넘기면 **여전히 렌더 무변경**이다.

### §4.5 🔴 `materialIconsExtended` 의존이 없다

`feature/ranking/build.gradle.kts` 는 **6줄짜리 빈 껍데기**다 — `compose.materialIconsExtended` 가 없다.
`:core:designsystem` 이 갖고 있지만 **`implementation` 이라 전이되지 않는다.** 홈 모듈이 그 사실을
주석으로 적어 두고 자기 `build.gradle.kts:15` 에 직접 선언했다.

→ `MilitaryTech` / `LocalFireDepartment` / `Group` / `PersonAdd` 를 쓰려면 **랭킹 모듈에도 선언해야 한다.**

---

## §5 범위 밖 — 명시적으로 만들지 않는 것

| 항목 | 사유 |
|---|---|
| **프로필 이모지** | Lovable 목데이터. 도메인에 필드 없음. [spec.md 비범위](./spec.md) 확정 — §1.2.3 |
| **아바타 실사진** (`profileImageUrl`) | 🔴 **사유 교체됨(2026-08-26)** — Coil 은 **이미 배선돼 있고** URL 도 **실제로 들어온다**(§1.2.3.1). 지금 안 그리는 이유는 ① URL 이 `http://` 평문이라 **iOS 에서만 차단**된다 ② `ProfilePlaceholder` 는 4개 feature 공용이라 단독으로 못 켠다. **아바타 활성화는 "기존 화면 일괄" 백로그 건**(pm-lead 판정) — 선결 조건은 서버 https 정규화 (§1.2.3.1 · §8.1) |
| **`box-shadow` glow / `pulse-fire`** | §2.2 판정 |
| **`glass-card` 그라데이션 · `--shadow-card`** | §6.2 — 전 화면 동시 결정 사안 |
| **행 탭 상호작용** | 정본에 없다. 프로필 화면 자체가 백로그. **탭하면 아무 일도 없다** — §7-⑧ |
| **Pull-to-refresh** | 정본에 없고 앱에 선례도 없다 |
| **기간별(주간·월간) 랭킹 · 전체 유저 랭킹** | [spec.md 비범위](./spec.md) — 기획에 없음 |
| **랭킹 변동 알림** | [spec.md 비범위](./spec.md) |
| **결과 히스토리 화면** | 백로그 별건. 랭킹 탭과 화면 축이 다르다 |
| **`bottom nav` / `pb-24`** | `MainScreen` 소관 — §1.0 |

---

## §6 신규 디자인 토큰 — **필요 없다**

기존 카탈로그와 전수 대조한 결과 **이번 화면이 요구하는 토큰이 전부 이미 있다.**

| 쓰임 | Lovable | 카탈로그 | 모바일 |
|---|---|---|---|
| 1위 아바타·받침대 | `fire-gradient` = `--gradient-fire` | [tokens.md §2](../../design-system/tokens.md) · [colors.md §3](../../design-system/colors.md) | **`brushes.fire`** ✅ **이미 있다** |
| 받침대 불꽃 | `--primary` | colors.md §1.1 | `colorScheme.primary` |
| 카드 표면 | `--card` | colors.md §1.2 | `colorScheme.surface` |
| 아바타 배경(2·3위·명단) | `--secondary` | colors.md §1.3 | `colorScheme.secondary` |
| 받침대(2·3위) | `--secondary/50` | colors.md §1.3 | `colorScheme.surfaceVariant` (§1.2.1 사유) |
| 패수·연패·1위 rank | `--destructive` | colors.md §1.5 | `colorScheme.error` |
| 3위 rank | `--warning` | colors.md §1.5 | `colorScheme.warning` |
| 부제·캡션·2/4+위 rank·메달 | `--muted-foreground` | colors.md §1.2 | `colorScheme.onSurfaceVariant` |
| 보더 | `--border` | colors.md §1.4 | `colorScheme.outline` |
| radius 12 / 16 | `--radius-lg` / `--radius-xl` | tokens.md §4 | `RoundedCornerShape(12.dp / 16.dp)` |
| 10 / 12 / 14 / 16 / 20 / 24sp | `text-[10px]`~`text-2xl` | tokens.md §5.2 | `medium10`·`medium12`·`bold12`·`bold14`·`medium16`·`bold16`·`medium20`·`bold20`·`bold24` |

**타이포 슬롯도 신규 0건이다.** 위 슬롯은 전부 `Typography.kt` 에 존재한다.
tokens.md §5.2 가 예약해 둔 `light10`/`bold10` 은 **이번에도 필요하지 않다** — 이 화면의
`text-[10px]` 2건(포디움 캡션 `font-medium`, 명단 캡션 weight 미지정)은 §5.3 정책상 각각
Medium/Light 지만, [challenge-verification/design.md §6](../challenge-verification/design.md) 이
*"한 앱 안에서 같은 성격의 캡션이 두 굵기가 되는 쪽이 더 나쁘다"* 로 **`medium10` 통일**을 결정했다.
그 결정을 승계한다.

### §6.0 실측 확인 2건 (rank-mobile 질의, 2026-08-26)

**① `text-destructive` → `colorScheme.error` 가 맞다.** `ChallengeColorScheme` 에 `destructive`
라는 이름의 슬롯은 **없다** — [colors.md §1.5](../../design-system/colors.md)가 Lovable 변수
`--destructive` 를 `error`(`red1` `#D75C4A`)에 매핑해 뒀다. 이름이 달라진 것뿐이고 값이 그 값이다.
`text-warning` → `warning`(`yellow1` `#D7AF45`) 도 동상. **이 화면에서 `chart1~5` 는 쓰지 않는다**
(tokens.md §8-5 가 *"랭킹 기능에 쓰일지 불확실"* 로 남겨 둔 항목인데, **랭킹에는 차트가 없다** —
pm-lead 가 그 확인 항목을 닫아도 된다).

**② Brush 슬롯 이름은 `fire` 다 — `primary` 가 아니다.** rank-mobile 실측 보고가
*"`ChallengeBrushes.primary`"* 라고 적었는데 **실제 필드명은 `fire`** 다:

```
ChallengeBrushes.kt:13-20  →  data class ChallengeBrushes(fire, card, glow)
```

`gradientPrimaryStart/End` 는 그 Brush 의 **재료가 되는 ColorScheme 슬롯 이름**이고, Brush 슬롯 자체는
`fire` 다(KDoc *"메인 CTA / 히어로"* 가 `val fire` 위에 붙어 있어 혼동하기 쉽다).
실사용처 6곳이 전부 `ChallengeTheme.brushes.fire` 다 — `SplashScreen.kt:24` ·
`SoulStampLogo.kt:66` · `ChallengeTitle.kt:30` · `BackgroundDecor.kt:21` · `Label.kt:83`.
→ **카탈로그가 옳고 갱신할 것이 없다.** 코드에 쓸 이름은 `ChallengeTheme.brushes.fire`.

> ✅ **색 명세를 hex 가 아니라 토큰 이름으로 달라는 요청은 이 문서가 이미 그렇게 돼 있다.**
> 문서 서두가 *"값을 이 문서에 복붙하지 않는다"* 이고, §1 의 모든 표가 `colorScheme.<slot>` 이름만 쓴다.

### §6.1 ⚠️ 카탈로그 갱신 대상 — `text-[11px]` 이 카탈로그에 없다

`text-[11px]` 은 Tailwind 비표준이고 [tokens.md §5.2](../../design-system/tokens.md) 표에 **행이 없다**.
그런데 실측하면 **9개 파일에 15회** 쓰인다:

```
challenge-new 5 · index 2 · ChallengeCard 2 · friends 1 · login 1
mypage 1 · oath 1 · ranking 1 · SignaturePad 1
```

`text-[10px]` 은 §5.2 가 21개 사용처까지 전수 등재해 뒀는데 **11px 만 빠져 있다.**
모바일은 이미 `medium12` 근사로 처리하고 있고(`ChallengeCard.kt:182`) 이 문서도 그걸 따르지만
(§1.1), **카탈로그에 근거가 없어서 매번 코드 주석에서 재발견되는 상태**다.

✅ **2026-08-26 등재 완료** — [tokens.md §5.2](../../design-system/tokens.md) 에 `text-[11px]` 행 신설
(15개 사용처 + weight 분포 `font-bold` 1 / `font-medium` 1 / 미지정 13).
**11sp 슬롯은 신설하지 않았다** — 이미 `medium12` 근사로 출시돼 있고, 1px 을 위해 슬롯을 늘리면
10/11/12sp 가 육안 구분 없이 셋 공존한다. 그 행은 "슬롯"이 아니라 **근사 규약의 기록**이다.

### §6.2 ⚠️ 미적용으로 남는 항목 2건 (기존 미결, 이 화면이 만든 문제 아님)

- **`glass-card` 의 `--gradient-card`** — tokens.md §2 에 `brushes.card` 로 매핑돼 있으나
  `FriendListItem`·`HomeEmptyState`·홈 `ChallengeCard` 가 **전부 평면 `surface`** 를 쓴다.
  이번 화면도 선례를 따른다. 그라데이션 카드로 갈지는 **전 화면 동시 결정 사안**이라 여기서 분기하지 않는다.
- **`--shadow-card`** — 동상. 기존 카드들이 shadow 없이 1dp 보더로 경계를 낸다.

---

## §7 ⚠️ 디자이너 확인 대상

| # | 항목 | 현재 처리 |
|---|---|---|
| ① | **1위 받침대 `fire-gradient/20`** — Tailwind 가 생성하지 않는 클래스라 **웹에서도 배경이 안 나온다**(실측, 레포 유일 사용) | **의도대로** `brushes.fire` 20% 배경 + 아이콘만 40% 알파로 진행 (§1.2.4) |
| ② | **"나" 행 강조** — 정본은 닉네임이 `"나"` 인 것 외에 강조가 없다 | **닉네임 치환(명단+포디움) + 명단 행 배경 `surfaceVariant`** (§1.3.2). 🔴 초안의 "치환만"에서 **전환** — rank-mobile 반론 채택 |
| ③ | **rank 숫자 색** — 2위가 4위 이하와 같은 `muted` 라 **2위만 강조가 빠진다**. 카드 보더는 `rank ≤ 3` 로 셋을 묶는데 숫자 색은 안 묶는다 | **정본 그대로** 구현 (§1.3.1) |
| ④ | **이모지 아바타(🤓😊🤗😤😏😎)** — 목데이터이고 도메인에 필드가 없다 | **닉네임 이니셜 `ProfilePlaceholder`** 로 대체. 프로필 이모지를 실제 기능으로 도입할 계획이 있는지 확인 (§1.2.3) |
| ⑤ | **받침대 메달 아이콘** — lucide `Medal` 에 1:1 대응하는 Material 아이콘이 없다 | `Icons.Filled.MilitaryTech` 로 진행. `EmojiEvents`(트로피)가 대안 |
| ⑥ | **참가자 3명 미만** — 정본이 답하지 않는다. **신규 사용자의 기본 상태** | N < 3 이면 **포디움 생략**, 명단 + 빈 상태 카드 (§3.2) |
| ⑦ | **빈 상태 문구** — 정본에 없다 | `"아직 줄 세울 친구가 없어요"` / `"친구를 등록하면 누가 개돼지왕인지 가려져요"` 제안 (§3.3) |
| ⑧ | **행 탭 동작** — 정의되지 않았다 | **동작 없음**으로 진행 (범위 밖, §5) |
| ⑨ | **1위 캡션의 `0연패`** — 정본이 무조건 연패를 찍는다 | `lossStreak > 0` 조건부로 교정 (§1.2.5). 같은 화면 명단 행이 이미 그 조건이다 |
| ⑩ | **🐷 가 두 뜻으로 쓰인다** — 포디움 1위·명단 뱃지는 **연패**, 포디움 2·3위는 **패배 수** | **연패로 통일** — 포디움 2·3위 캡션에서 🐷 를 뗀다 (§1.2.6). 2·3위에 연패를 추가하지는 않는다 |
| ⑪ | **"0전 0패" 와 "전승 0패" 가 같은 캡션** — 정반대 상태인데 글자가 같다 | `totalChallenges == 0` 이면 **`아직 기록 없음`** (§1.3.3). 🔴 **계약에 `totalChallenges` 추가 필요** |

> ✅ **①③④⑤⑥⑦⑧⑨⑩⑪ 는 위 제안값으로 진행 확정.** 디자이너 확인을 기다리지 않는다 —
> **지금 이 화면을 만들려면 어차피 그 값들이 필요하고**, 제안값이 전부 보수적이라 뒤집혀도 교체 비용이 작다.
> ②는 정본과 앱 관례가 일치하므로 이견이 없는 한 그대로 간다.
>
> 🔴 **표에서 지우지 마라.** *"진행 확정"* 은 *"디자이너가 승인했다"* 가 아니라 **확인을 기다리지 않고
> 구현한다**는 뜻이다. 목록을 지우면 나중에 이 값들이 디자이너가 정한 값인지 우리가 정한 값인지 구분할 수 없다.

---

## §8 계약(api-contract)에 대한 디자인 측 요구

[api-contract.md](./api-contract.md) 의 쟁점 5개 중 **3개가 화면 표현을 직접 좌우**한다.
backend-dev(rank-backend) 가 참고할 디자인 측 입장:

| 계약 쟁점 | 디자인 측 요구 | 사유 |
|---|---|---|
| **③ "나" 식별** | 🔴 **`isMe` 를 서버가 내려 달라** | §1.3.2 의 닉네임 치환이 여기 걸린다. 앱이 `userId` 를 대조하려면 내 `userInfo` 가 먼저 로드돼야 하고, 실패하면 **아무도 "나" 가 아닌 목록**이 나온다. `ChallengeDetailViewModel.kt:208` 이 같은 함정을 주석으로 남겨 뒀다 |
| ✅ **② `lossRate` 계산 주체 / 0-0 — 확정** | **서버 계산 + 정수 %**, `total = 0` 이면 **`0`**(`null` 금지) | 캡션이 `"패배율 ${lossRate}%"` 한 줄이다. `null` 이면 화면에 분기가 하나 생기고 그 분기의 문구를 디자인이 정한 적이 없다. 🔴 **앱은 `losses / totalChallenges` 를 재계산하지 않는다.** 사유가 계약 회신으로 더 강해졌다 — 서버는 그 몫을 **반올림한 정수**로 만들고 **그 정수를 정렬 3차 키로도 쓴다.** 앱이 다시 나누면 반올림이 조금만 달라도 **표시값이 서버 정렬과 어긋난다**(4위가 5위보다 높은 패배율로 보이는 식). `totalChallenges` 가 응답에 생겼다고 해서 분모로 쓰라는 뜻이 아니다 — 그건 §1.3.3 의 `== 0` 판정 전용이다 |
| **⑤ 친구 0명일 때 배열** | **`[{나}]` 로 내려 달라** (`[]` 아님) | §3.2 의 N=0 행이 통째로 사라진다. 나 혼자여도 "명단"은 성립하고, 앱의 분기가 하나 줄어든다 |
| ① 정렬·동률 | (디자인 무관) | 다만 §1.2.5 — **연패 0 인 사람이 1위가 될 수 있는지**가 정렬 규칙에 달렸다. 될 수 있다면 §1.2.5 의 조건부 캡션이 반드시 필요하다 |
| ④ row 부재 = 전부 0 | **찬성 — 단 ⑤가 함께 와야 목적이 달성된다** | 명단에서 빠지면 "친구인데 왜 없지" 가 된다. 0패로 맨 아래. 다만 **들어와서 무의미한 행이 되면 안 된다** → ⑤ |
| ~~⑥ `profileImageUrl` https 정규화~~ | 🔴 **철회 — 이 feature 의 계약 요구가 아니다** | §8.1 |
| ✅ **⑤ `totalChallenges` 추가 — 반영 완료** | `totalChallenges: Int` non-null, row 없으면 `0` (2026-08-26 `confirmed`) | §1.3.3. 챌린지 0회인 사람과 **전승한 사람**이 지금 shape 으로는 둘 다 `0패 · 패배율 0%` 라 **글자 하나까지 같다.** 앱이 현재 필드로는 도출할 수 없다. `hasRecord` 같은 파생 플래그보다 `totalChallenges` 를 선호한다 — **서버가 이미 `lossRate` 계산에 쓰는 값**이라 추가 비용이 사실상 0 이고, 파생 플래그는 서버가 규칙을 하나 더 소유하게 된다. 앱은 `== 0` 만 본다 |

### §8.1 🔴 ⑥ https 정규화 요구 철회 — **내 월권이었다**

**철회 (2026-08-26, design-bridge 자체 정정).** `profileImageUrl` 을 https 로 정규화해 달라는 요구를
§8 표에 **계약 요구로 올린 것이 범위를 벗어났다.**

**사유**: §8 은 *"이 feature 를 그리는 데 계약이 무엇을 줘야 하나"* 의 표다.
**이 feature 는 `profileImageUrl` 을 그리지 않는다**(§1.2.3.1 — 이니셜 placeholder 확정).
안 그리는 값의 형식을 이 feature 의 계약 요구로 올리면, **계약이 화면과 무관한 조건을 지게 된다.**

✅ **pm-lead 스코프 판정(2026-08-26)과도 같은 결론이다** — 아바타 활성화는 *"기존 화면 일괄"* 백로그
건이고, 랭킹 화면 하나에 얹을 범위가 아니다. `http://` 평문의 ATS/cleartext 축은 **화면 명세가 아니라
앱 전역 설정 사안**이며, 아바타는 홈·친구·친구검색에도 똑같이 걸려 있다. 켤 거면 일괄로 켠다.

🔴 **다만 실측 자체는 버리지 않는다.** 기술적 발견(Android 통과 / iOS ATS 차단의 **플랫폼 분기 실패**)은
**§1.2.3.1 에 그대로 남는다.** 그것이 이 문서에서 하는 일은 *"계약에 요구하는 것"* 이 아니라
**"이번에 아바타를 켜지 않는 이유"** 이고, 그 자리에서는 정당하다.

→ https 정규화는 **백로그 "아바타 활성화(기존 화면 일괄)" 항목의 선결 조건**으로 옮긴다(pm-lead 소관).
그 항목을 여는 사람이 **가장 먼저 확인해야 할 것**이다 — 안 보고 켜면 iOS 에서만 깨진다.

⚠️ **계약은 `profileImageUrl` 키를 그대로 내린다.** 값이 실제로 있을 수 있는 정상 nullable 이고,
나중에 아바타를 켤 때 **계약 변경 없이** 되게 하려는 것이다. **앱은 받되 안 그린다.**

---

## §9 mobile-dev(rank-mobile) 인계 체크리스트

- [ ] 🔴 **`<BottomNav />` 와 `pb-24` 를 옮기지 마라** — `MainScreen` 이 이미 그린다 (§1.0)
- [ ] 상단바는 `ChallengeBaseTopBar` + Column(제목·부제). **56dp 고정 높이 × 큰 폰트 스케일 프리뷰로
      클리핑 확인**, 잘리면 부제를 본문 최상단으로 (§1.1). 공용 56dp 는 건드리지 마라
- [ ] 포디움은 `Row(verticalAlignment = Alignment.Bottom)`. **`-mt-4` 를 옮기지 마라** (§1.2)
- [ ] 🔴 **1위 받침대는 `brushes.fire` 20% 배경**, `opacity-40` 은 **아이콘 tint 에만** (§1.2.4)
- [ ] 🔴 **1위 캡션은 `lossStreak > 0` 조건부** — 정본에 없는 조건이니 **코드 주석에 사유를 남겨라**.
      안 남기면 다음 사람이 "정본에 없는 분기"로 지운다 (§1.2.5)
- [ ] 🔴 **명단은 1위부터 전원.** 포디움과 중복되는 게 정본이다. `drop(3)` 금지 (§1.3)
- [ ] 🔴 **🐷 뒤의 수는 언제나 연패.** 포디움 2·3위 캡션에서 🐷 를 떼고 `{losses}패` (§1.2.6)
- [ ] 🔴 **`totalChallenges == 0` 이면 캡션을 `"아직 기록 없음"` 으로 대체** (§1.3.3).
      계약에 `totalChallenges` 가 들어오는지 확인하고, 없으면 rank-backend 에 요구하라 (§8-⑤)
- [ ] `lossRate` **재계산 금지.** 서버 값에 `%` 만 붙인다 (§1.3.1, §8-②)
- [ ] `isMe` 행은 닉네임을 `"나"` 로 치환(**명단+포디움**) + **명단 행 배경 `surfaceVariant`** (§1.3.2)
- [ ] **`Modifier.wiggle()` 은 `:core:designsystem` 신설**, 값은 `ChallengeTitle.kt:44-53` 기존값
      (±8f / 1500ms / Reverse) 승계. 로그인도 교체하면 **로그인 프리뷰 확인 후 리포트에 기록**,
      위험하면 랭킹만 쓰고 백로그 등재 (§2.1)
- [ ] 🔴 **`pulse-fire` 는 구현하지 않는다.** Canvas glow 를 만들지 마라 (§2.2)
- [ ] **N < 3 이면 포디움을 그리지 않는다** — N=1(나 혼자)이 신규 사용자의 기본 상태다 (§3.2).
      프리뷰에 **N=0/1/2/3/6** 을 전부 넣어라
- [ ] `FriendsEmptyState` → `:core:ui` **`EmptyStateCard`** 이동. **홈 `HomeEmptyState` 는 건드리지 마라** (§4.4)
  - [ ] 🔴 **`icon` · `ctaIcon` · 보조 CTA 라벨 셋 다 파라미터로 열어라** (§4.4.1). `FriendsEmptyState` 를
        그대로 올리면 CTA 아이콘이 `PersonAdd` 로 굳어서, 나중에 `FriendPickPlaceholderCard` 이관 때
        **시그니처를 또 바꿔야 한다.** 기존 호출부가 기존 값을 넘기면 렌더는 여전히 무변경이다
  - [ ] 🔴 **아이콘 박스 shape 은 현행 16dp 유지.** 정본은 `rounded-2xl`(20dp)이고 세 사본이
        16/16/`CircleShape` 로 갈라져 있지만, **이번에 맞추면 출시된 친구·홈 픽셀이 움직인다.**
        20dp 정합은 백로그 (§4.4.1)
- [ ] `ProfilePlaceholder` 를 **고치지 마라** — 1위 Brush 배경은 랭킹 안에서 별도 구현 (§4.2).
      이니셜 규칙(`trim().firstOrNull()?.uppercase()`)은 원본과 동일하게
- [ ] 🔴 **아바타 radius 는 12dp 가 아니라 16dp 다.** `rounded-xl` = `--radius-xl` = **16px**
      (tokens.md §4). 12dp 는 `--radius-lg`(`rounded-lg`)이고, 이 화면에서 12dp 가 쓰이는 곳은
      **받침대 상단 모서리(`rounded-t-lg`)뿐**이다. 아바타 규격 총정리:

      | 자리 | size | shape | textStyle |
      |---|---|---|---|
      | 포디움 1위 | 64dp | `RoundedCornerShape(16.dp)` | `medium24` — 🔴 `ProfilePlaceholder` 불가, Brush 배경 (§4.2) |
      | 포디움 2·3위 | 56dp | `RoundedCornerShape(16.dp)` | `medium20` |
      | 명단 행 | 40dp | `RoundedCornerShape(16.dp)` | `medium16` |
- [ ] 🔴 **`feature/ranking/build.gradle.kts` 에 `compose.materialIconsExtended` 선언 추가** (§4.5)
- [ ] 실패는 **스낵바** (`RankingUiEffect.ShowMessage`). Error 화면 상태를 새로 만들지 마라 (§3)
- [ ] `RankingViewModel` / `RankingState` 의 `TODO` · `placeholder: Unit` 를 실제 필드로 교체
- [ ] 🔴 **`ProfilePlaceholder` 를 `AsyncImage` 로 바꾸지 마라** (§1.2.3.1). Coil 이 배선돼 있고
      URL 도 실제로 들어와서 *"이제 되네"* 로 보이지만, **URL 이 `http://` 평문이라 iOS 에서만 차단된다.**
      Android 로 확인하면 통과한다 — **한쪽만 깨지는 실패**다. 아바타 활성화는 **"기존 화면 일괄"
      백로그 건**이고(pm-lead 판정), 선결 조건은 서버 https 정규화다 (§1.2.3.1 · §8.1)
- [ ] **프리뷰 픽스처는 실서버 실측 응답을 그대로 써라** — 표시 분기가 한 응답에 다 들어 있다:

      | rank | nickname | isMe | losses | lossRate | currentLossStreak | totalChallenges | 걸리는 분기 |
      |---|---|---|---|---|---|---|---|
      | 1 | 테스터1 | ✅ | 4 | 80 | **0** | 5 | §1.2.5 연패 절 생략 + §1.3.2 "나" 치환 + **내가 1위** |
      | 2 | 테스터2 | | 3 | 100 | 3 | 3 | 연패 뱃지 노출 · 패배율 100% |
      | 3 | 이우건 | | 3 | 75 | 0 | 4 | `profileImageUrl` **non-null**(카카오 CDN) — placeholder 유지 확인 |
      | 4 | 테스터3 | | 2 | 100 | 2 | 2 | 4위 이하 rank 색 |
      | 5 | 테스터4 | | 0 | 0 | 0 | **0** | §1.3.3 **`아직 기록 없음`** |

- [ ] 프리뷰: 위 5명 실측 + N=3 / N=2 / N=1 / N=0 / 긴 닉네임 / 큰 폰트 스케일
- [ ] 🔴 **이 문서와 코드가 갈라지면 그 자리에서 이 문서를 고친다** — soul-oath 에서 문서가 코드보다
      낡아 생긴 건이 3회다. 특히 §1 의 레이아웃 도식과 §4.3 의 컴포넌트 목록이 잘 낡는다

### pm-lead 보고 항목 (이번 feature 산출물 아님)

- ~~**백로그 문구 재정의** — *"FAB `pulse-fire` 미구현"* 의 "LoginScreen 패턴 재사용"이 Canvas glow 로
  오독되는 경로~~ ✅ **2026-08-26 pm-lead 처리 완료** (§2.3)
- ~~**tokens.md §5.2 에 `text-[11px]` 행 추가**~~ ✅ **2026-08-26 design-bridge 직접 등재 완료** (§6.1)
- ~~**`HomeEmptyState` ↔ `EmptyStateCard` 통합** 백로그 등재~~ ✅ **2026-08-26 pm-lead 처리 완료** (§4.4)
- ~~**tokens.md §8-5 "차트 5색" 을 닫아도 된다**~~ ✅ **2026-08-26 design-bridge 마감 완료** (§6.0-①)
- ~~**백로그 아바타 항목의 차단 사유 갱신**~~ ✅ **2026-08-26 pm-lead 처리 완료** — 항목명은
  **"`profileImageUrl` 화면 적용"** 이다(옛 "원격 이미지 로더 도입" 은 2026-08-25 해소되며 닫혔다).
  차단 사유가 전면 갱신됐고 rank-backend 의 실측 3종(https 동일 서빙 · 유입 1곳 · `fname=` 이중 `http`
  함정)까지 등재됐다. **design.md 는 그 내용을 복제하지 않는다** (§1.2.3.1)

---

## 변경 이력

| 일시 | 변경 |
|------|------|
| 2026-08-26 16:02:55 | **끊긴 백로그 참조 2곳 정정.** 문서가 [백로그 "원격 이미지 로더 도입"](../../backlog.md) 을 가리키고 있었는데 **그 항목은 2026-08-25 challenge-verification 이 해소하며 닫혔다.** 살아 있는 항목명은 **"`profileImageUrl` 화면 적용"** 이고, pm-lead 가 차단 사유를 이미 전면 갱신해 뒀다(rank-backend 실측 3종 포함). §1.2.3.1 과 pm 보고 항목의 *"갱신해야 한다"* 를 **완료 표시 + 정확한 항목명**으로 교체. 🔴 **rank-backend 가 제안한 "실측 3종을 §1.2.3.1 에 보태라" 는 채택하지 않았다** — 백로그 항목이 이미 그 셋을 갖고 있어 **두 벌이 되면 갈린다.** 이 문서의 몫은 *"이번에 안 켠다"* 까지고 *"어떻게 켜느냐"* 는 그 항목 소관임을 §1.2.3.1 에 명시. |
| 2026-08-26 15:41:07 | 🔴 **§8-⑥(https 정규화) 계약 요구 철회 — §8.1 신설.** rank-backend 가 자기 제안(*"이미지 로드 갈래를 design.md 에 추가해라"*)을 pm-lead 스코프 판정에 따라 철회했고, **그 판정에 비추면 내 §8-⑥ 도 월권이었다** — §8 은 *"이 feature 를 그리는 데 계약이 무엇을 줘야 하나"* 의 표인데 **이 feature 는 `profileImageUrl` 을 그리지 않는다.** 안 그리는 값의 형식을 계약 요구로 올리면 계약이 화면과 무관한 조건을 진다. **실측(Android 통과 / iOS ATS 차단의 플랫폼 분기 실패)은 §1.2.3.1 에 그대로 남긴다** — 거기서는 "계약 요구"가 아니라 **"이번에 아바타를 켜지 않는 이유"** 라 정당하다. https 정규화는 백로그 "아바타 활성화(기존 화면 일괄)" 의 **선결 조건**으로 이관. §5·§9·§1.2.3.1 의 `§8-⑥` 참조 3곳도 함께 정정. **이니셜 placeholder 유지는 변경 없음**(원래 그렇게 쓰여 있었고, 이미지 로드 갈래를 추가한 적이 없다). |
| 2026-08-26 15:18:44 | **rank-backend 계약 `confirmed` + 실서버 실측 반영.** 🔴 **§1.2.3.1 신설 — 이 문서 초판의 전제 2개가 무너졌다.** ① *"Coil 배선 0건"* → **이미 배선돼 있다**(`App.kt:77` `setSingletonImageLoaderFactory`, `VerificationPhoto.kt:95` `SubcomposeAsyncImage` — challenge-verification 이 깔았다). ② *"URL 은 사실상 항상 null"* → **실제로 들어온다**(실측 rank 3 이 카카오 CDN URL). **결론(placeholder 유지)은 그대로지만 사유가 통째로 교체됐다** — 새 사유는 URL 이 `http://` 평문이라 **iOS 에서만 차단**된다는 것(Android 는 `network_security_config.xml:10` 전 호스트 평문 허용, iOS 는 ATS 키 부재 + `img1.kakaocdn.net` 이 도메인명이라 차단). **한쪽 플랫폼만 깨지는 실패**라 §9 에 "`AsyncImage` 로 바꾸지 마라" 를 명시. §8-⑥ 신설(서버 https 정규화 요구). §5 아바타 행 갱신. 백로그 "원격 이미지 로더 도입"의 차단 사유 갱신을 pm-lead 보고에 등재. (2) **§1.2.5 에 실데이터 증거 추가** — 개발 DB 1위가 `losses=4, currentLossStreak=0` 으로 **조건부 캡션이 첫 실행에서 발동**한다. (3) **§8-② 강화** — `lossRate` 정수가 **정렬 3차 키**이기도 해서 앱 재계산 시 표시와 정렬이 어긋난다(`totalChallenges` 는 §1.3.3 `== 0` 판정 전용이지 분모가 아님). (4) **§8-⑤ 반영 완료 표시** — `totalChallenges: Int` non-null 확정. (5) **§9 프리뷰 픽스처를 실측 응답 5행 표로 교체** — 표시 분기가 한 응답에 다 들어 있다. |
| 2026-08-26 14:51:33 | **rank-mobile 실측 제보 2건 반영.** (1) 🔴 **§4.4.1 신설** — EmptyState 사본이 2개가 아니라 **3개**였다(`FriendPickPlaceholderCard.kt:33` KDoc 이 *"`FriendsEmptyState` 는 internal 이라 별도로 둔다"* 라고 자백). 랭킹은 4번째가 될 뻔했다. 확인 결과 **셋이 이미 갈라져 있다** — 일러스트 아이콘 박스 shape 이 Lovable 정본 `rounded-2xl`(20dp) ↔ `FriendsEmptyState`/`HomeEmptyState` 16dp ↔ `FriendPickPlaceholderCard` `CircleShape`. **셋 다 정본과 다르고 셋끼리도 다르다.** 이번엔 16dp 유지(승격의 무회귀 성격 보존), 20dp 정합은 백로그 — 지금은 3곳이지만 통합 후엔 1곳이라는 것이 통합의 근거. 🔴 **승격 시그니처 요구 추가**: 두 사본이 서로 반대되는 것을 파라미터화해 놔서(`FriendsEmptyState` 는 `icon` 만, `FriendPickPlaceholderCard` 는 `ctaIcon` 만), 그대로 올리면 나중 이관 때 시그니처를 또 바꿔야 한다 → `icon`·`ctaIcon`·보조 CTA 라벨 셋 다 열도록 §9 체크리스트 갱신. (2) **§1.2.5 조건 확정** — 원래 *"총 패배가 1차 키라면"* 조건부로 쓴 문단을, rank-backend 가 `losses DESC` 1차 키로 확정함에 따라 **"실제로 발동하는 분기"** 로 승격. 방어 코드가 아님을 명시. |
| 2026-08-26 14:22:10 | **rank-mobile 질의 6건 반영.** (1) 🔴 **§1.3.3 신설** — *"0전 0패"* 와 *"전승 0패"* 가 지금 shape 으로는 캡션이 글자까지 같다는 지적 채택. `totalChallenges == 0` → `"아직 기록 없음"`, **계약에 `totalChallenges` 추가 요구**(§8-⑤ 신설, 계약 blocking). (2) 🔴 **§1.2.6 신설** — 🐷 가 연패/패배수 두 뜻으로 쓰이는 것을 **연패로 통일**(포디움 2·3위 캡션에서 🐷 제거). §1.2.5 와 맞물려 캡션 형식이 수렴함을 기록. (3) 🔴 **§1.3.2 판정 전환** — "나" 강조를 닉네임 치환 **단독**에서 **치환 + 명단 행 배경 `surfaceVariant`** 로 상향(rank-mobile 시나리오 2 반론 채택). 치환이 주인 이유(포디움에는 배경 강조를 걸 자리가 없다)를 명시. (4) **§6.0 신설** — 실측 확인 2건: `text-destructive` → `error` 확정 / 🔴 **Brush 슬롯명은 `primary` 가 아니라 `fire`** (rank-mobile 실측 보고 정정, 실사용처 6곳 대조). 랭킹에 차트가 없으므로 tokens.md §8-5 를 닫을 수 있음도 등재. (5) **§2.2 기각 사유 추가** — `brushes.glow` 정적 후광 제안은 center/radius 미지정 근사라 새 튜닝이 되므로 기각. (6) **§9 아바타 규격표 추가** — rank-mobile 이 `rounded-xl` 을 12dp 로 읽었으나 **16dp** 임을 정정(12dp 는 받침대 상단 모서리뿐). §7 확인 대상 ⑩⑪ 추가, ② 갱신. |
| 2026-08-26 13:46:29 | 최초 작성. `ranking.tsx` 스냅샷 기준 T-D1 명세. **애니메이션 판정**: `wiggle` 구현(기존 `ChallengeTitle` 값 승계 + `:core:designsystem` 추출) / `pulse-fire` 보류(정적 `brushes.fire` 대체) — 판정선은 "transform·alpha 는 구현, box-shadow glow 는 보류". **정본 이탈 4건**: 1위 받침대(`fire-gradient/20` 이 Tailwind 미생성 클래스임을 실측) / 1위 캡션 `0연패` 조건부 / N<3 포디움 생략 / bottom nav 미이식. 신규 토큰 **0건**(`brushes.fire` 이미 존재). 신규 컴포넌트 8종(feature 6 + 공용 2). 디자이너 확인 대상 9건. 계약 쟁점 3건에 디자인 측 요구 회신(§8). |
</content>
</invoke>
