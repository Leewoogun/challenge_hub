# Design — notification-list (알림 목록)

- **디자인 소스**: `challenge-design/oathbound-challenges`
- **참조 route**: `src/routes/notifications.tsx` (51줄, 전체)
- **정본 마지막 수정**: `634e170` **2026-04-16 03:40:56** — 🔴 이 날짜가 §0.1 의 근거다
- **스냅샷 일시**: 2026-09-01 13:12:19
- **선행 문서**: [spec.md](./spec.md) · [push-fcm](../push-fcm/summary.md) · [push-deeplink](../push-deeplink/summary.md)
- **토큰 카탈로그**: [tokens.md](../../design-system/tokens.md) · [colors.md](../../design-system/colors.md) — 값은 여기 복붙하지 않는다

---

## §0 이 문서의 위치 — 정본이 4개월 반 낡았다

이 화면은 앞선 feature 들과 조건이 다르다. **정본이 현행 서버와 어긋나 있고, 어긋난 이유가 확인된다.**

`notifications.tsx` 는 `634e170`(**2026-04-16**) 이후 한 번도 손대지 않았다. 그런데 알림 타입 체계는
그 뒤에 두 번 바뀌었다:

| 일시 | 무슨 일 | 정본 반영 |
|---|---|---|
| 2026-08-06 | 기획서 전면 개정 — `SIGN_REQUEST` 폐기(수락=서명 원자화), `CHALLENGE_ACCEPTED`/`CHALLENGE_REJECTED` 신규 2종 | ❌ 안 됨 |
| 2026-08-14 | `OPPONENT_VERIFIED` 발송 개시 (challenge-verification T-B4) | ❌ 안 됨 |

**그래서 정본 mock 6종과 실제 발송 4종은 "일부 미구현" 관계가 아니라 서로 다른 목록이다.**
§2.1 의 대조표가 이 문서의 핵심이고, 여기서 정본을 그대로 옮기면 **서버가 만들지 않는 알림 4종을
그리고, 실제로 오는 알림 2종은 자리가 없는** 화면이 나온다.

🔴 **정본에 없다는 이유로 `CHALLENGE_ACCEPTED`·`CHALLENGE_REJECTED` 를 빼지 마라.** 둘은 지금
**운용 중**이다. 반대로 mock 의 `taunt`·`reminder`·`result`·`lost` 는 **그리지 마라.** 서버가 만들지
않는다.

### §0.1 그럼 디자이너에게 다시 export 를 받아야 하나 — 아니다

정본이 낡은 것은 **타입 목록**이지 **카드 형태**가 아니다. 카드 골격(아이콘 박스 + 메시지 + 상대
시각), 간격, 토큰은 그대로 유효하고 앱의 다른 화면과도 정합한다. **형태는 정본을 따르고, 타입
목록만 서버 실측으로 대체한다.** 재-export 요청은 §10-① 로 pm-lead 에게 올린다(차단 사유 아님).

---

## §1 골격

Lovable 은 `app-container`(max-width 430px) 안에 sticky header + 목록 + `<BottomNav />` 를 둔다.
네이티브에서는:

- **컨테이너 폭 제약 무시** ([tokens.md §6](../../design-system/tokens.md) — 웹 프리뷰용).
- 🔴 **`<BottomNav />` 와 `pb-24` 를 옮기지 않는다.** `Route.Notifications` 는 `BottomNavItem` 에
  **없다**(`BottomNavItem.kt:17-36` — HOME·FRIENDS·RANKING·MYPAGE 4개뿐). `MainScreen.kt:163` 이
  `BottomNavItem.find(currentRoute) != null` 로 판별하므로 이 화면엔 바가 애초에 안 그려진다.
  화면이 직접 그리면 탭 4개짜리 바에 활성 탭이 없는 상태가 된다.
- 좌우 gutter `px-5` = **20dp**. 홈·친구·랭킹·마이페이지와 같은 값.

```
ChallengeScaffold(statusBarColor = surface)
├── topBar: ChallengeTopBar("알림", onBack = popBackStack)      §2
└── content: LazyColumn(contentPadding = vertical 16dp)
    └── items { NotificationCard }                              §3
        (0건이면 NotificationEmptyState)                        §5
```

🔴 **`LazyColumn` 을 쓴다.** 마이페이지가 `Column(verticalScroll)` 을 쓴 근거(*"항목이 고정 5개
이하"*, [mypage §1.0](../mypage/design.md))가 여기엔 없다 — **알림은 상한 없이 쌓이는 유일한
목록**이다(spec 오픈이슈 2 가 페이지네이션을 다시 연 이유와 같은 사실). 보관함(`ArchiveScreen.kt`)이
`LazyColumn` 을 쓴 것과 같다.

- 항목 간격 `space-y-2` = **8dp**, 목록 상단 `mt-4` = **16dp**.
- 🔴 **좌우 gutter 는 `contentPadding` 이 아니라 카드마다 넣는다.** `ArchiveChallengeList`
  (`ArchiveScreen.kt:145-160`)의 판단을 승계한다 — 카드가 스크롤 인디케이터와 겹치지 않게 카드
  자신이 여백을 낸다.

### §1.1 진입 애니메이션 — **넣지 않는다**

정본은 카드마다 `animate-slide-up` + `animationDelay: i * 0.05s` 스태거를 건다(`notifications.tsx:35`).
**앱에 이식하지 않는다.**

- 실측: 앱 전체에서 `AnimatedVisibility`/`slideInVertically` 를 쓰는 파일은 **`:feature:login` 2개
  뿐**이다. 홈·친구·랭킹·보관함 네 목록 화면이 전부 애니메이션 없이 출시됐다 — 앞선 design.md 들이
  *"선택 구현"* 으로 넘긴 결과가 일관되게 **미구현**이었다.
- 그리고 이 목록은 다르다. 스태거는 **한 번 그려지는 목록**의 어휘다. 알림 목록은 진입할 때마다
  최신 상태를 다시 받는 화면이고, 갱신마다 6개 카드가 순차로 밀려 올라오면 **읽던 자리를 잃는다.**

→ 🔴 **"선택 구현" 으로 넘기지 않고 미구현으로 확정한다.** 되살리려면 네 목록 화면을 함께 판단한다.

---

## §2 헤더

- **참조**: `notifications.tsx:27-29`
- **의도**: 라벨만. 액션 없음.

| 요소 | Lovable | 토큰 |
|---|---|---|
| 제목 | `text-xl font-extrabold` "알림" | `typography.bold18` / `colorScheme.onBackground` — 🔴 아래 |
| 배경 | `bg-background/80 backdrop-blur-xl` | `colorScheme.surface` (`ChallengeTopBar` 기본값). 블러 재현 안 함 |
| 뒤로가기 | **정본에 없다** | 🔴 `onBack = navigator::popBackStack` — 아래 |

### §2.1 🔴 `titleStyle` 은 **기본값(`bold18`)** 이다 — 마이페이지와 반대 결론이다

[mypage §1.1](../mypage/design.md) 은 `bold20` 을 **명시로 넘기라**고 했다. 여기서는 넘기지 않는다.
모순이 아니라 **같은 규칙의 다른 항**이다:

| | 마이페이지 | 알림 |
|---|---|---|
| 화면 성격 | 하단 4탭 중 하나 | 벨에서 push 된 **하위 화면** |
| 정본 헤더 | `text-xl font-extrabold` (20px) | `text-xl font-extrabold` (20px) — **같다** |
| 앱 관례 | 4탭 헤더는 `bold20`(홈·랭킹) | 하위 화면은 `bold18` (상세·생성·친구검색·보관함) |
| 판정 | `bold20` 명시 | **`bold18` 기본값** |

`ArchiveRoute.kt:62` 가 이미 같은 판단을 코드 주석으로 남겼다 — *"탭이 아니라 하위 화면이라
titleStyle 은 기본값(bold18)을 쓴다 — 상세·생성·친구검색과 같다."* **정본이 20px 인 것은 Lovable
에서 이 페이지가 `<BottomNav />` 를 달고 있어 탭처럼 취급됐기 때문**이고(§1), 앱에서는 탭이 아니다.

### §2.2 🔴 뒤로가기 버튼은 **정본에 없는 것을 추가하는 것이다**

정본 헤더에는 뒤로가기가 없다. **웹에서는 브라우저 뒤로가기가 있고, `<BottomNav />` 로도 나갈 수
있기 때문**이다. 앱에는 둘 다 없다 — 바가 안 그려지고(§1), iOS 에는 시스템 뒤로가기 제스처가 있지만
Android 는 하드웨어 백뿐이다. **버튼 없이 내보내면 화면에 갇힌다.**

`ChallengeTopBar(title, onBack)` 의 기본 제공 버튼을 쓴다 — `Icons.AutoMirrored.Filled.ArrowBack`
20dp / `onBackground` / 40dp 터치 타깃(`TopBar.kt:102` `ChallengeTopBarBackButton`). 신규 제작 없음.

---

## §3 알림 카드 (`NotificationCard`)

- **참조**: `notifications.tsx:35-43`

```
Surface(radius 16dp, surface + 1dp outline)   ← clickable (§7)
└── Row(Alignment.Top, spacedBy 12dp, 패딩 16dp)
    ├── Box(36dp, radius 16dp, secondary) { Icon 18dp, tint = 타입색 }   §3.2
    └── Column(weight 1f)
        ├── 메시지        medium14 / onBackground      §3.3
        ├── VerticalSpacer(4dp)
        └── 상대 시각      medium10 / onSurfaceVariant  §3.4
```

| 요소 | Lovable | 토큰 | 근거 |
|---|---|---|---|
| 카드 | `glass-card p-4` | `Surface(RoundedCornerShape(16.dp), colorScheme.surface, BorderStroke(1.dp, colorScheme.outline))` + 패딩 16dp | [mypage §1.4.4](../mypage/design.md) 와 동일 |
| Row 정렬 | `items-start` | `Alignment.Top` — 🔴 메시지가 2줄이 되면 아이콘 박스가 **위에 붙는다**. `CenterVertically` 아님 | 정본 |
| Row 간격 | `gap-3` | `Arrangement.spacedBy(12.dp)` | 정본 |
| 아이콘 박스 | `w-9 h-9 rounded-xl bg-secondary` | **36dp**, `RoundedCornerShape(16.dp)`, `colorScheme.secondary` | [mypage §1.4.4](../mypage/design.md) 아이콘 박스와 **markup 이 글자 단위로 같다** |
| 아이콘 | lucide 18px, `text-*` 로 tint | **18dp**, tint = §3.2 타입색 | 정본 |
| 메시지 | `text-sm font-medium` | `typography.medium14` / `colorScheme.onBackground` | tokens.md §5.2·§5.3 |
| 시각 | `text-[10px] text-muted-foreground mt-1` | `typography.medium10` / `colorScheme.onSurfaceVariant`, 상단 4dp | tokens.md §5.2 |

- `bg-secondary` 는 알파 없는 평면색이라 그대로 `colorScheme.secondary`. (랭킹의 `bg-secondary/50`
  → `surfaceVariant` 대체와 다른 경우 — 여기엔 `/50` 이 없다.)
- `text-[10px]` weight 미지정 → tokens.md §5.3 정책상 Light 지만
  [challenge-verification §6](../challenge-verification/design.md) 의 **`medium10` 통일**을 승계한다
  ([mypage §1.4.4](../mypage/design.md) 와 같은 처리).
- `shrink-0` / `min-w-0` 은 Compose 의 `Row` + `weight(1f)` 가 구조적으로 처리한다. 옮길 것 없음.

### §3.1 메시지 줄 수 — **상한을 두지 않는다**

정본은 상한을 안 건다(`min-w-0` 만 있고 `line-clamp` 없음). 그대로 간다.

근거: 메시지는 서버가 만든 고정 문형 + 닉네임뿐이라(§3.3) 길이가 튀는 원인이 **닉네임 하나**다.
카카오 닉네임이 길면 2줄이 되는데, **잘라내면 잘리는 부분이 하필 닉네임**이다 — 누가 한 일인지
모르는 알림이 된다. 2줄을 허용하는 쪽이 싸다. `Alignment.Top`(§3) 이 그 경우의 정렬을 이미 맞춰 뒀다.

### §3.2 🔴 타입 → 아이콘·색 — **발송 4종만**

**정본 mock 6종 대조표.** 왼쪽이 정본, 오른쪽이 서버 실측(`NotificationType.kt` + `NotificationMessages.kt`):

| 정본 mock `type` | 정본 아이콘·색 | 서버 대응 | 처리 |
|---|---|---|---|
| `challenge` | `Swords` / `text-primary` | `CHALLENGE_REQUEST` ✅ 발송 중 | **매핑** |
| `verified` | `CheckCircle2` / `text-success` | `OPPONENT_VERIFIED` ✅ 발송 중 | **매핑** |
| `taunt` | `Flame` / `text-warning` | `TAUNT` — 트리거 없음 | 🔴 **그리지 않는다** |
| `reminder` | `Clock` / `text-warning` | `REMIND` — 트리거 없음 | 🔴 **그리지 않는다** |
| `result` | `CheckCircle2` / `text-success` | `RESULT` — 트리거 없음 | 🔴 **그리지 않는다** |
| `lost` | `XCircle` / `text-destructive` | `RESULT` 의 패배 케이스 — 트리거 없음 | 🔴 **그리지 않는다** |
| — (정본에 없음) | — | `CHALLENGE_ACCEPTED` ✅ 발송 중 | 🔴 **신규 매핑 필요** |
| — (정본에 없음) | — | `CHALLENGE_REJECTED` ✅ 발송 중 | 🔴 **신규 매핑 필요** |

"트리거 없음" 의 실측 근거: `NotificationMessages.of()` 가 `REMIND`/`RESULT`/`TAUNT`/`FRIEND_REQUEST`
에 대해 **`null` 을 반환**하고(`NotificationMessages.kt:91-95`), dispatcher 가 null 이면 건너뛴다.
같은 파일 KDoc 이 *"이 한 줄이 발송 스위치다"* 라고 명시한다.

#### 확정 매핑 — 4종

| 서버 타입 | 아이콘 | 색 | 근거 |
|---|---|---|---|
| `CHALLENGE_REQUEST` | `Icons.Filled.SportsKabaddi` | `colorScheme.primary` | 색은 정본 그대로. 아이콘은 lucide `Swords` 대응 — **앱이 이미 "챌린지"에 쓰는 기호**다(`ArchiveScreen.kt:177` CTA 아이콘) |
| `CHALLENGE_ACCEPTED` | `Icons.Filled.Description` | `colorScheme.success` | 🔴 정본에 없다 — 아래 |
| `CHALLENGE_REJECTED` | `Icons.Filled.Cancel` | `colorScheme.error` | 🔴 정본에 없다 — 아래 |
| `OPPONENT_VERIFIED` | `Icons.Filled.CheckCircle` | `colorScheme.success` | 정본 `CheckCircle2` / `text-success` 그대로 |
| **그 외 전부** | `Icons.Filled.Notifications` | `colorScheme.onSurfaceVariant` | §3.2.2 |

##### 🔴 `CHALLENGE_ACCEPTED` — 왜 `Description` + `success` 인가

- **아이콘**: 이 사건은 *"상대가 수락했다"* 가 아니라 **"계약이 성립했다"** 다 — 2026-08-06 개정이
  수락과 서명을 원자로 묶었기 때문에, 이 알림이 도착한 시점에 **계약서가 존재한다.**
  앱은 계약서를 `Icons.Filled.Description` 로 그린다([mypage §1.4.4](../mypage/design.md) "계약서
  보관함"). 서버 문구도 `title = "계약 완료."` 다. 세 축이 같은 곳을 가리킨다.
  - ⚠️ `CheckCircle` 를 쓰면 안 된다 — `OPPONENT_VERIFIED` 와 같은 아이콘이 된다. 이 둘은 **한
    챌린지에서 연달아 도착**하므로(수락 → 인증) 목록에서 나란히 놓인다. 아이콘이 같으면 구분이
    시각에만 남는다.
- **색**: `success`. 신청(`primary`)과 색까지 같으면 신청→수락 두 줄이 통째로 닮는다.
  🔴 [mypage §5.1](../mypage/design.md) 이 *"`success` 를 쓰는 자리가 사실상 사라졌다"* 고 적었는데,
  **여기가 그 자리다** — 같은 절이 예고한 *"인증 축에서 쓰일 여지"* 가 실현된 셈이다. §9 에 기록.

##### 🔴 `CHALLENGE_REJECTED` — `lost` 를 빌려오되 사건을 바꾸지 않는다

정본에서 가장 가까운 것은 `lost`(`XCircle` / `text-destructive`)인데 **패배와 거절은 다른 사건**이다.
그럼에도 형태를 빌리는 이유는 **부정 결과 축**이 같아서다. `XCircle` 대응은
`Icons.Filled.Cancel`(원 안의 X — lucide `XCircle` 과 형태가 같다). 대안 `Icons.Filled.Close`(원 없음).

⚠️ **`error` 색이 "앱이 고장났다"로 읽히지 않는가** — 읽히지 않는다. 정본이 이미 부정 **사건**에
`text-destructive` 를 쓰고 있고(`lost`), 이 화면에는 시스템 오류를 그리는 자리가 따로 있다(§6).
🔴 다만 [mypage §1.5.2](../mypage/design.md) 가 회원탈퇴에 `error` 를 **쓰지 않기로** 한 것과
헷갈리지 마라 — 거긴 위계 문제(로그아웃이 이미 그 색)였고, 여기는 위계 경쟁자가 없다.

#### §3.2.1 🔴 이 매핑의 사본을 만들지 마라

`NotificationCard` 는 **타입을 받아 아이콘·색을 고르지 않는다.** 화면 계층에서 `when(type)` 을 돌리면
타입이 늘 때마다 화면을 고치게 되고, 그 `when` 이 §3.2.2 의 폴백을 반드시 빠뜨린다.

→ **타입 → (아이콘, 색) 은 UiState 계산 프로퍼티 한 곳에서 끝내고**, `NotificationCard` 는 이미
결정된 `ImageVector` + `Color` 를 받는다. `ChallengeOutcomePill.kt:98` 의 `challengeOutcomeVisualOf`
(`:core:ui`, 승패무 표현의 단일 출처 — [mypage §1.2.4](../mypage/design.md))와 같은 형태다.
위치·이름은 mobile-dev 판단.

#### §3.2.2 🔴 모르는 타입이 와도 목록이 깨지지 않아야 한다 — 이건 가정이 아니다

**서버 enum 에 8종이 이미 선언돼 있고**(`NotificationType.kt`), `NotificationMessages.of()` 에 문구
한 줄이 추가되는 순간 그 타입의 발송이 시작된다. 같은 파일 KDoc:

> **"여기 먼저 쓰면 구버전 앱에서 '눌러도 아무 데도 안 가는' 조용한 실패가 난다."**

즉 **구버전 앱이 모르는 타입을 받는 것은 이 프로젝트가 이미 문서화한 운용 방식**이다. 폴백은 방어적
가정이 아니라 관측된 요구사항이다.

> ✅ **2026-09-01 — 가정에서 계약으로 확정됐다.** backend 가 목록 응답의 `type` 을 **정규화하지 않은
> DB 원문 String** 으로 내리기로 확정했다. 계기는 `NotificationEntity.kt:61-62` 실측 —
> `runCatching { NotificationType.valueOf(type) }.getOrDefault(NotificationType.CHALLENGE_REQUEST)`
> 가 **모르는 type 을 조용히 `CHALLENGE_REQUEST` 로 강등**한다(같은 파일 KDoc 이 옛 row 로 목록
> 조회가 깨지는 것을 막으려는 의도라고 밝힌다). 그대로 두면 폐기된 `SIGN_REQUEST` 가 화면에
> **"도전장 도착"** 으로 찍힌다 — 🔴 **모르는 타입보다 나쁘다. 아는 척하는 오답이기 때문이다.**
> backend 가 읽기 경로에서 그 매퍼를 안 밟게 바꾸므로 **원문이 보존되고, 앱은 실제로 모르는 값을
> 받게 된다.** 두 결정이 서로를 성립시킨다 — 서버가 원문을 주는 것은 앱에 폴백이 있을 때만 안전하고,
> 폴백이 값을 갖는 것은 원문이 올 때뿐이다.

| | 폴백 |
|---|---|
| 아이콘 | `Icons.Filled.Notifications` — 홈 벨과 같은 기호. "알림 일반"을 앱이 이미 그 모양으로 쓴다 |
| 색 | `colorScheme.onSurfaceVariant` — 🔴 **무채색.** 의미를 모르는데 `warning`·`success` 같은 의미색을 주면 없는 뜻을 지어낸다 |
| 메시지·시각 | **그대로 그린다.** 서버가 `body` 를 채워 보내므로 사람은 읽을 수 있다 |
| 탭 | **비활성** — §7.2 |

🔴 **모르는 타입을 목록에서 숨기지 마라.** 숨기면 ① 푸시로 본 알림이 목록에 없고 ② 홈 뱃지 개수와
목록 길이가 어긋난다. **읽을 수 있게 그리되 못 가는 곳으로 보내지 않는 것**이 폴백의 전부다.

### §3.3 🔴 메시지는 서버의 `body` 다 — `title` 은 그리지 않는다

서버는 알림 1건에 **`title` 과 `body` 를 둘 다 박제**한다(`Notification.kt`, `NotificationMessages.kt`).
정본 카드는 메시지가 **한 줄**이다(`notifications.tsx:40`). 무엇을 그릴지 정해야 한다.

실측 4종:

| 타입 | `title` | `body` |
|---|---|---|
| `CHALLENGE_REQUEST` | `영혼의 맹세` | `{닉}과 계약을 하시렵니까?` |
| `CHALLENGE_ACCEPTED` | `계약 완료.` | `{닉}님이 수락했습니다` |
| `CHALLENGE_REJECTED` | `ㅠㅠ` | `{닉}님이 도망쳤습니다` |
| `OPPONENT_VERIFIED` | `증거 도착` | `{닉}님이 인증 사진을 올렸습니다` |

**판정: `body` 단독 1행.**

- 정본 mock 메시지(`"민수님이 챌린지를 신청했습니다!"`)와 **같은 문형**이 `body` 다 — 누가·무엇을.
  `title` 넷은 푸시 알림의 헤드라인으로 설계된 것이라 목록에서 홀로 서지 못한다. `ㅠㅠ` 한 줄짜리
  알림이 생긴다.
- 2행(title 볼드 + body)도 기각한다. 카드 높이가 1.5배가 되는데 얻는 정보는 `ㅠㅠ` 다. 정본이 1행인
  것을 뒤집을 근거가 안 된다.

🔴 **이건 "응답에서 `title` 을 빼라"는 뜻이 아니다.** 계약 필드 결정은 T-B1 소관이고, 화면 근거로는
**필요 없다**는 것만 확정한다. spec T-B1 이 *"앱이 그리는 것만"* 이라고 했으므로 backend 는 이 절을
근거로 빼도 된다.

#### §3.3.1 ⚠️ `CHALLENGE_REQUEST` 문구의 조사 — 목록이 이 결함을 오래 노출한다

`"${actorNickname}과 계약을 하시렵니까?"` — **받침 없는 닉네임이면 "민수과"** 가 된다. 정본 mock 이
쓰는 이름이 정확히 "민수" 다. 4종 중 이 한 종만 `님` 도 빠져 있다(나머지 셋은 `{닉}님이`).

**이 문구는 사용자 확정(2026-08-07)이라 내가 바꾸지 않는다.** 다만 확정 당시엔 **푸시밖에 없었다** —
푸시는 스쳐 지나가지만 **목록은 남고, 스크롤하면 다시 보인다.** 노출 조건이 달라졌으므로 §10-② 로
올린다. 🔴 **mobile 이 앱에서 문자열을 고쳐 덮지 마라** — 서버가 박제한 값이라 푸시와 목록이 갈린다.

### §3.4 🔴 상대 시각 — `toRelativeKoreanString` 은 **쓸 수 없다**. 실측 결과다

spec T-D1 이 재사용 가능성을 물었다. **불가능하다.**

`core/utils/.../RelativeTimeFormat.kt:23-39` 를 읽으면:

```
val remaining = this.toInstant(KST) - now.toInstant(KST)
if (remaining <= 0.seconds) return "마감"
```

**이 함수는 마감까지 남은 시간(미래)을 세는 카운트다운**이다. KDoc 도 *"챌린지 마감 시각(deadline)을
… 카드 UI 의 우상단 '5시간 32분'"* 이라고 못 박는다. 알림의 `createdAt` 은 **항상 과거**라
`remaining <= 0` 이 무조건 참이고 — **목록의 모든 행이 "마감" 으로 표시된다.**

앱 전체에 과거 경과 시간을 만드는 함수는 **없다**(`"방금"`·`"분 전"`·`"시간 전"`·`"어제"` 전수 검색
0건). **신규 함수가 필요하다.**

#### 확정 — 경과 시간 포맷

`:core:utils` 의 `RelativeTimeFormat.kt` **옆에** 둔다(같은 파일이든 형제 파일이든 mobile-dev 판단).
🔴 **이름을 `toRelativeKoreanString` 의 오버로드로 만들지 마라** — 방향이 반대인 두 함수가 같은
이름이면 호출부에서 어느 쪽인지 안 보인다. `toElapsedKoreanString` 류의 다른 이름을 쓴다.

**규칙은 순서대로 평가한다. 각 가지는 참인 것만 말한다.**

| # | 조건 | 출력 | 정본 대응 |
|---|---|---|---|
| 1 | 경과 < 1분 (**음수 포함**) | `"방금 전"` | `"방금 전"` ✅ |
| 2 | 경과 < 60분 | `"{N}분 전"` | `"10분 전"` ✅ |
| 3 | 경과 < 24시간 | `"{N}시간 전"` | `"1시간 전"` · `"2시간 전"` ✅ |
| 4 | 달력일 차이 == 1 | `"어제"` | `"어제"` ✅ |
| 5 | 그 외 | `"{M}월 {d}일"` | ⚠️ 정본에 없다 — §10-③ |

##### 🔴 3번과 4번의 순서가 이 표에서 제일 중요하다

`"어제"` 는 **달력 단어**고 `"N시간 전"` 은 **산술 단어**다. 둘을 한 축으로 계산하면 반드시 거짓말이
나온다:

- 시간 가지를 달력일로 제한하면 → **어제 23:00 알림을 오늘 01:00 에 보면 "2시간 전" 대신 "어제"**.
  정보 손실.
- `"어제"` 를 24~48시간으로 잡으면 → **그저께 23:00 알림을 오늘 01:00 에 보면 26시간 경과라
  "어제"** 인데 달력상 그저께다. **거짓**.

위 순서면 둘 다 안 난다. 어제 10:00 → 오늘 01:00 은 15시간이라 `"15시간 전"`(참), 어제 10:00 →
오늘 20:00 은 34시간이라 가지 3 탈락 후 달력일 차 1 → `"어제"`(참), 그저께 23:00 → 오늘 01:00 은
가지 3·4 모두 탈락 → `"8월 30일"`(참).

##### 5번을 `"{N}일 전"` 으로 하지 않는 이유

`"8일 전"` 은 세어봐야 언제인지 안다. 그리고 앱엔 이미 날짜 어휘가 있다 —
[mypage §2.4.3](../mypage/design.md) 이 보관함 카드에 `{M}월 {d}일` 을 확정했다. **두 번째 날짜
방언을 만들지 않는다.** ⚠️ 정본이 `"어제"` 까지만 보여줘서 이 가지는 근거가 앱 관례뿐이다 — §10-③.

##### 1번이 음수를 흡수하는 것은 방어적 가정이 아니다

`createdAt` 은 **서버가 만들고**, `now` 는 **기기가 만든다.** 두 시계가 다른 것은 가정이 아니라
분산 시스템의 상수다. 기존 `toRelativeKoreanString` 도 같은 자리를 `"마감"` 으로 흡수하고 있고
(`remaining <= 0.seconds`), `WireFormatBaselineTest` 가 그 경계를 고정한다. **같은 처리를 승계하는
것이지 새 방어를 넣는 게 아니다.** 흡수 안 하면 `"-3분 전"` 이 나온다.

##### 🔴 화면에 시계를 두지 마라

`now` 를 **UiState 가 한 번 받아 전 항목에 같은 값을 쓴다.** 항목마다 `nowKst()` 를 부르면 같은
목록 안에서 기준 시각이 어긋난다. [home-feed 의 `HomeUiState.now`](../home-feed/design.md) ·
`ReceivedChallengeItemState.now` 가 이미 그 형태다(`HomeUiState.kt:67`).

⚠️ **초 단위로 갱신하지 않는다.** 화면이 살아 있는 동안 `"3분 전"` 이 `"4분 전"` 으로 바뀌지 않아도
된다 — 카운트다운(마감)과 달리 경과 시간은 긴박하지 않다. 진입 시각 기준 1회로 충분하다.

---

## §4 🔴 읽음 여부 시각 표현 — **확정 (2026-09-01, pm 판정)**

> ✅ **결론: 읽음 처리를 넣는다. 단 "목록을 열면 전부 읽음" 형태로.**
> `POST /notifications/read-all` + 응답 `unreadCount`. 🔴 **행 단위 `isRead` 는 서버가 내리지 않는다** —
> 즉 **목록에 읽음/안읽음 시각 구분이 없다.** 카드는 1상태다.
> 아래 §4.1~§4.3 이 이 판정의 근거이고, **§4.5 가 이번에 범위로 들어온 홈 벨 뱃지의 표현 판정**이다.
> (spec 오픈이슈 1 해소. 본 문서 초판의 권고안이 그대로 채택됐다.)

### §4.1 실측 — 붉은 점은 **이미 만들어져 있고 영구히 꺼져 있다**

| 실측 | |
|---|---|
| `HomeTopBar.kt:27` | `hasUnreadNotification: Boolean` 파라미터 존재 |
| `HomeTopBar.kt:76-88` | 8dp 붉은 점(`colorScheme.error`, `CircleShape`) 렌더 코드 존재 |
| `HomeTopBar.kt:101,131` | 뱃지 켜진 `@Preview` 2개 존재 |
| **`HomeScreen.kt:61` · `HomeScreen.kt:125`** | 🔴 **`hasUnreadNotification = false` 하드코딩. 호출부 전부** |
| [home-feed/design.md:34](../home-feed/design.md) | *"우측: `Bell` 아이콘 + 우상단 dot (destructive) — **미확인 알림 표시**"* |

**즉 이 UI 는 설계·구현·프리뷰까지 끝났고 데이터만 안 들어온다.** 읽음 처리를 1차에서 빼면 그 상태가
유지된다 — spec 비범위가 *"홈 뱃지는 읽음 처리에 종속"* 이라고 적은 것의 실제 모습이 이것이다.

### §4.2 읽음 구분이 **없을 때** 목록이 어떻게 읽히나

알림 4종은 **전부 한 챌린지의 생애주기**다(신청 → 수락/거절 → 상대 인증). 챌린지 1건이 목록에
**최대 3줄**을 만들고, 세 줄이 같은 닉네임을 달고 **연속으로** 놓인다:

```
민수님이 인증 사진을 올렸습니다      2시간 전
민수님이 수락했습니다               5시간 전
민수과 계약을 하시렵니까?           6시간 전
```

여기서 사용자가 답해야 하는 질문은 *"새로 온 게 뭐지"* 인데, **답을 주는 것이 시각 한 줄뿐**이다.
그리고 그 시각은 `medium10` / `onSurfaceVariant` — **화면에서 가장 약한 요소**다(정본이 그렇게
정했고 §3 이 그대로 따랐다). 🔴 **가장 중요한 질문의 답이 가장 약한 자리에 있다.**

### §4.3 확정 — **"목록 진입 시 전체 읽음"**. 카드 2상태를 만들지 않는다

| | 값 |
|---|---|
| 읽음 처리 시점 | **목록 화면 진입 시 1회 일괄** (`POST /notifications/read-all`) |
| 카드의 읽음 시각 표현 | 🔴 **없음.** 카드는 1상태 그대로 |
| 홈 뱃지 | `unreadCount > 0` 이면 점 — 표현 판정은 **§4.5** |
| 딸려오는 API | **1개** (전체 읽음) + 응답 `unreadCount` |

**왜 카드에 2상태를 안 만드나 — 만들 수가 없다.** 진입하는 순간 전부 읽음이 되므로 **읽은 카드와 안
읽은 카드가 한 화면에 공존하는 시간이 0이다.** 그릴 대상이 없다.

**그리고 그게 이 안의 가장 큰 이득이다.** 정본에는 읽음 표현이 **없다**(6종 전부 같은 카드). 카드별
읽음을 도입하면 배경을 `surface`→`tertiary` 로 올리거나 좌측에 primary 바를 넣는 식으로 **정본에
없는 것을 발명**해야 한다. 발명한 표현은 디자이너 확인 대상이 되고, 이 feature 를 확인 대기로 만든다.

**대가**: 목록에 들어갔다가 아무것도 안 읽고 나가도 점이 꺼진다.
→ 🔴 **이건 결함이 아니라 뱃지의 정의다.** 붉은 점이 답하는 질문은 *"이 줄을 봤나"* 가 아니라
*"안 본 게 있나"* 이고, home-feed/design.md 가 쓴 단어가 정확히 **"미확인 알림 표시"** 다.
목록을 연 순간 그 질문은 답해졌다.

### §4.4 ~~만약 1차에서 빼기로 하면~~ — **무효 (2026-09-01 pm 판정으로 소멸).** 지우지 않고 남긴다

초판이 "읽음을 빼는 결정도 수용 가능하다"며 그 경우의 요구사항(하드코딩된 `false` 를 죽은 UI 로
백로그 등재)을 적어 뒀다. **(B) 채택으로 이 분기가 사라졌다** — 뱃지가 이번에 점등되므로 등재할
죽은 UI 가 없다(§11-① 도 함께 소멸).

🔴 **다만 §4.2 는 무효가 아니다.** 거기 적은 *"같은 닉네임 세 줄이 연속으로 쌓이고 구분자가 가장
약한 시각 한 줄뿐"* 은 **읽음을 넣어도 목록 안에서는 그대로 참**이다 — (B)는 행 단위 구분을 만들지
않기 때문이다. (B)가 해결하는 것은 **목록에 들어오기 전** 질문(*"볼 게 있나"*)이지 **들어온 뒤**
질문(*"어디까지 봤나"*)이 아니다. 후자가 실사용에서 문제로 올라오면 그때 행 단위 읽음(C안)을
재론한다 — **지금 미리 그리지 않는다.**

### §4.5 🔴 홈 벨 뱃지 — **점을 유지한다. 숫자로 바꾸지 않는다**

pm 판정으로 홈 벨 뱃지가 이번 범위에 들어왔고(spec 비범위 → 범위) 표현이 내 판정 대상이 됐다.
서버가 `unreadCount`(**숫자**)를 주는데 정본과 구현은 둘 다 **점**이다. 어긋난 지점이라 결정이 필요하다.

**판정: `unreadCount > 0` 을 boolean 으로 접어 기존 점에 넣는다. 신규 UI 0건.**

| 축 | 값 | 출처 |
|---|---|---|
| 형태 | **점** (숫자 아님) | 정본 `index.tsx:130` `w-2 h-2 rounded-full` |
| 크기 | **8dp** | 정본 `w-2`(=8px) · 구현 `HomeTopBar.kt:81` `.size(8.dp)` — **이미 일치** |
| 색 | `colorScheme.error` | 정본 `bg-destructive` · 구현 `HomeTopBar.kt:83` — **이미 일치** |
| 위치 | 벨 아이콘 우상단 | 구현 현행(`padding(top = 10.dp, end = 10.dp)`) 유지 — 아래 ⚠️ |
| 99+ 규칙 | **만들지 않는다** | 숫자를 안 쓰므로 발생하지 않는다 |

#### 왜 숫자가 아닌가 — 근거 3개

1. 🔴 **(B) 안에서 숫자는 사용자의 행동을 바꾸지 못한다.** 목록을 열면 **전부** 읽음이 된다. 그래서
   개수는 *"열기 전에 쌓인 수"* 이고, 그 수를 본 사용자가 할 수 있는 일은 **"연다" 하나뿐**이다.
   3이든 17이든 같은 행동을 한다. **숫자는 선택지를 바꿀 때만 값이 있다** — 여기엔 선택지가 없다.
2. **정본이 점이다.** 숫자로 가는 것은 정본 이탈이고, 이탈하려면 근거가 필요한데 1번이 그 반대다.
3. **구현이 이미 점이다.** 이 feature 는 벨 뱃지를 **점등**시키러 온 것이지 다시 그리러 온 게 아니다.
   숫자로 바꾸면 출시된 `HomeTopBar` 의 레이아웃을 뜯게 되고, 그 순간 **숫자 폭에 따른 뱃지 크기
   가변 · 벨 아이콘과의 겹침 · 99+ 절단 규칙**이 전부 새 문제로 딸려온다. 점은 그 중 하나도 안 만든다.

⚠️ **`unreadCount` 를 boolean 으로 바꿔 달라고 backend 에 요구하지 않는다.** 접는 것은 앱이 한 줄로
한다(`unreadCount > 0`). 계약을 좁히면 나중에 숫자로 갈 때 계약을 다시 열어야 하고, **화면이 그걸
요구할 근거가 없다.**

⚠️ **뱃지 위치는 육안 검증 대상이다** — 정본은 버튼 기준 6px 오프셋(`top-1.5 right-1.5`)인데 구현은
10dp 다. 40dp `IconButton` 안에 24dp 아이콘이 들어가 여백이 다르기 때문으로 보인다. 🔴 **이번에
고치지 않는다** — 출시된 화면이고 이 feature 는 점등만 한다. 점이 켜진 실물을 처음 보게 되므로,
그때 어색하면 그때 판단한다.

#### §4.5.1 🔴 목록에서 돌아온 홈에 점이 남아 있으면 안 된다

**(B) 안이 화면에 만드는 유일한 리스크가 이것이다.** 목록 진입 → 전부 읽음 → 뒤로 → **홈의 점이
그대로**면 사용자는 *"읽었는데 왜 아직 있지"* 를 본다. 뱃지를 점등시킨 것이 오히려 신뢰를 깎는다.

→ **요구사항: 목록에서 돌아온 홈은 뱃지를 갱신한다.** 수단(홈 재진입 시 재조회 / 목록이 읽음 처리
후 신호 발행 / 공유 상태)은 mobile-dev 판단이다. 화면이 요구하는 것은 **결과 하나** — 돌아온
홈에 점이 없을 것.

⚠️ **반대 방향은 요구하지 않는다.** 홈에 머무는 중 푸시가 도착했을 때 점이 **즉시** 켜질 필요는
없다 — 푸시 자체가 이미 알렸다. 다음 홈 진입/새로고침에 반영되면 충분하다. 실시간 점등을 요구하면
홈이 알림을 구독해야 하고, 그건 이 feature 가 살 이유가 없는 비용이다.

---

## §5 빈 상태 — `EmptyStateCard` 를 **쓰지 않는다.** 검토했고 기각했다

spec T-D1 이 명시로 요구한 검토 항목이다. **결론: 신규 `NotificationEmptyState`.**

### §5.1 기각 사유

🔴 **`EmptyStateCard` 는 CTA 가 필수 파라미터다** — `ctaLabel: String` · `onClickCta: () -> Unit` ·
`icon: ImageVector` 셋 다 non-null 이고 빠질 경로가 없다(`EmptyStateCard.kt:44-56`).
그런데 **빈 알림함에 놓을 CTA 가 없다**:

| 후보 CTA | 기각 사유 |
|---|---|
| `"챌린지 만들기"` | 🔴 **홈이 이미 갖고 있다.** `HomeEmptyState` 가 `"챌린지 만들기"`·`"친구 등록"` 두 CTA 를 제공한다(`HomeEmptyState.kt:44-47`). 그리고 이 사용자는 **방금 그 홈에서 벨을 눌러 왔다** — 같은 버튼을 한 화면 뒤에서 다시 보여주는 셈 |
| `"친구 추가하기"` | 동상. 그리고 알림함에서 친구 목록으로 내보내면 **확인하러 온 사람을 밖으로 내보낸다** |
| CTA 없음 | ✅ 맞는 답 — **그런데 컴포넌트가 허용하지 않는다** |

`EmptyStateCard` 에 `onClickCta: (() -> Unit)?` 를 여는 것도 **하지 않는다** —
[mypage §2.5.1a](../mypage/design.md) 가 같은 자리에서 내린 판단을 그대로 승계한다:
*"출시된 공용 컴포넌트를 두 번째 사용처 때문에 일반화하지 않고, 3번째가 나올 때 통합을 판단한다."*
🔴 **이번이 그 두 번째다.** 세 번째가 나오면 그때 `EmptyStateCard` 의 CTA optional 화를 판단한다 —
§11-② 로 pm-lead 백로그에 올린다.

**형태도 안 맞는다.** `EmptyStateCard` 는 카드 크롬(16dp radius + `surface` + 1dp `outline` + 24dp
패딩 + 전폭 버튼)을 가진 **종착지의 어휘**다. 빈 알림함은 *"아직 아무 일도 안 일어났다"* 는 담담한
사실이지 사건이 아니다.

### §5.2 확정 — `NotificationEmptyState`

**카드 크롬만 벗고, 일러스트 문법은 `EmptyStateCard`·`ArchiveEmptyMonth` 와 픽셀 단위로 같게 간다.**
새 방언이 아니라 **같은 어휘의 가벼운 판**이다. [mypage §2.5.1a](../mypage/design.md) 의 `ArchiveEmptyMonth`
와 골격이 동일하다.

```
Column(fillMaxWidth, CenterHorizontally, 상단 64dp)
├── Box(64dp, radius 16dp, primary.copy(alpha = 0.10f)) { Icon 32dp, primary }
├── VerticalSpacer(16dp)
├── "아직 알림이 없어요"                    bold16   / onBackground
├── VerticalSpacer(4dp)
└── "챌린지가 오가면 여기에 쌓여요"          medium12 / onSurfaceVariant
```

| | 값 | 사유 |
|---|---|---|
| 아이콘 | `Icons.Filled.NotificationsNone` | 🔴 **outline 벨.** 홈의 filled `Notifications`(§3.2.2 폴백도 그것)와 **달라야 한다** — 하나는 "알림", 하나는 "알림 없음" 이다. 대안 `NotificationsOff` 는 **끄지 않았는데 꺼진 것처럼 보여** 기각 |
| 제목 | `"아직 알림이 없어요"` | 앱의 빈 상태 문구는 전부 말 거는 `-어요` 체([mypage §6-②](../mypage/design.md)) |
| 부제 | `"챌린지가 오가면 여기에 쌓여요"` | 🔴 *"알림을 켜세요"* 같은 설정 유도를 **넣지 않는다** — 알림 권한과 알림 목록은 다른 축이고, row 는 권한 없이도 쌓인다(`Notification.kt` KDoc) |
| CTA | **없음** | §5.1 |
| 카드 크롬 | **없음** | §5.1 |

⚠️ 문구 2줄 모두 **정본에 없다**(빈 상태 자체가 mock 에 없다). §10-④.

---

## §6 상태 매트릭스

| 상태 | 조건 | 화면 |
|---|---|---|
| **Loading** | 첫 조회 중 | 중앙 `CircularProgressIndicator`. 보관함(`ArchiveLoadingScreen`)과 같은 형태 |
| **Data** | 1건 이상 | §1 목록 |
| **Empty** | 0건, 조회 성공 | §5 `NotificationEmptyState` |
| **Failure** | 첫 조회 실패 | 🔴 **빈 상태로 그리지 않는다** — §6.1 |
| **다음 쪽 로딩** | 커서로 추가 조회 중 | 🔴 **목록 하단 인디케이터.** 화면을 덮지 않는다 — §6.3 |
| **다음 쪽 실패** | 커서 추가 조회 실패 | 🔴 **목록 유지** + 스낵바 + 하단에 `"다시 시도"` — §6.3 |
| **끝 도달** | 커서 소진 | **아무 표시도 하지 않는다.** 인디케이터가 사라지고 목록이 끝난다 — §6.3 |

### §6.1 🔴 0건과 실패를 뭉개지 않는다

[mypage §2.5.4](../mypage/design.md) 가 확정한 규칙을 승계한다 — *"0건과 실패는 다른 사실"*.
알림함에서 특히 그렇다: **"알림이 없다"** 와 **"알림을 못 불러왔다"** 는 사용자가 취할 행동이 정반대다
(전자는 나가면 되고, 후자는 다시 시도해야 한다).

실패 화면은 `ArchiveFailureScreen`(`ArchiveScreen.kt:193-210`)의 형태를 따른다 — 같은 일러스트 문법 +
`Icons.Filled.CloudOff`(`ArchiveScreen.kt:205`) + `"다시 시도"`.
🔴 **아이콘까지 빈 상태와 달라야 한다**(mypage 의 근거:
*"둘 다 '목록이 없는 화면' 이라 문구만 다르면 0건인지 못 불러온 건지 한눈에 갈리지 않는다"*).

### §6.2 페이지네이션 — **커서 무한 스크롤로 확정** (2026-09-01 backend 판정)

초판이 낸 화면 관점 우선순위는 **① 최근 N건 고정 > ② 무한 스크롤 > ③ "더 보기" 버튼** 이었다.
**backend 가 ②(커서)를 채택했다.** 초판의 우선순위를 지우지 않고 무효 사유와 함께 남긴다:

- ~~① 최근 N건 고정~~ — **무효.** 화면에 추가 상태가 하나도 안 생긴다는 것이 ①의 유일한 근거였고,
  그건 **화면의 편의**지 제품의 근거가 아니다. 알림은 상한 없이 쌓이는 유일한 목록이라(§1) 상한을
  두면 **언젠가 조용히 잘린다** — 잘린 사실을 사용자도 앱도 모른다. 커서가 그 문제를 안 만든다.
- 🔴 **③ `"더 보기"` 버튼 기각은 그대로 유효하다.** 카드 사이에 버튼이 끼면 §3 의 균일한 리듬이
  깨지고, 알림은 버튼을 눌러가며 파고들 대상이 아니다.

②를 받으면 화면에 상태가 3개 생긴다. 그 명세가 §6.3 이다.

### §6.3 🔴 무한 스크롤이 만드는 상태 3개 — 보관함이 배운 것을 그대로 승계한다

#### ① 다음 쪽 로딩 — **필요하다.** 목록 하단 인디케이터

무한 스크롤은 **스크롤을 끝까지 내렸을 때 아무 일도 안 일어나는 것처럼 보이는 순간**이 있다.
그 순간이 *"로딩 중"* 인지 *"끝"* 인지 구분되지 않으면 사용자는 끝인 줄 알고 나간다.

- 목록의 **마지막 item** 으로 `CircularProgressIndicator`(20dp) + 상하 16dp 패딩, 가운데 정렬.
- 🔴 **전체 화면 로딩으로 덮지 마라.** [mypage §2.5.4.3](../mypage/design.md) 이 월 전환에서 배운
  것과 같다 — 읽고 있던 목록이 사라지고 스크롤 위치를 잃는다.

#### ② 끝 도달 — **아무 표시도 하지 않는다**

초판 §6.2 의 판단을 커서 방식에서도 유지한다: *"여기까지"* 같은 문구는 **사용자가 안 찾던 경계를
알려준다.** 커서가 소진되면 **인디케이터가 사라지고 목록이 그냥 끝난다.** 그게 자연스러운 끝이다.

⚠️ 목록이 짧아 스크롤이 아예 안 생기는 경우도 같다 — 그냥 짧은 목록이고 표시할 것이 없다.

#### ③ 다음 쪽 실패 — 🔴 **목록을 비우지 마라**

[mypage §2.5.4.2](../mypage/design.md) 가 되살린 신호를 그대로 쓴다 — **부분 실패는 스낵바다.**
화면 전체를 실패로 바꾸면 이미 읽고 있던 알림까지 사라진다.

- **스낵바** + **하단 인디케이터 자리를 `"다시 시도"` 로 교체.** 스크롤 위치를 유지한 채 그 자리에서
  다시 시도한다.
- 🔴 **스낵바만 띄우고 끝내지 마라.** 스낵바는 사라지고, 그 뒤에 사용자가 더 볼 수단이 없어진다.
  §6.1 의 전체 화면 실패가 `"다시 시도"` 를 유일한 복구 수단으로 갖는 것과 같은 이유다.
- 첫 조회 실패(§6.1)는 그대로 전체 화면 실패다 — 목록이 아예 없으니 **비울 것이 없다.**

---

## §7 진입·이탈

| | |
|---|---|
| 진입 | 홈 상단 벨 (`HomeRoute.kt:25` — 이미 연결됨) |
| 이탈 (뒤로) | `ChallengeTopBar` 뒤로가기(§2.2) · 시스템 백 |
| 이탈 (탭) | 알림이 가리키는 화면 — §7.1 |

### §7.1 🔴 목적지 규칙의 사본을 만들지 마라 — 그런데 지금 그대로는 못 쓴다

spec T-M2 가 *"`MainViewModel.toRoute()` 의 매핑을 재사용하라"* 고 했다. **실측 결과 그대로는
불가능하다:**

- `toRoute()` 는 `MainViewModel.kt:106` 의 **파일 private top-level 함수**이고 모듈은 `:feature:main`
  이다. 다른 모듈에서 호출할 수 없다.
- 입력 타입도 다르다. `toRoute()` 는 `PushEvent` 를 받는데, `PushEvent` 는 **FCM data map 전용**
  모델이다(`PushEvent.from(Map<String, String>)`). 목록 행은 **API 응답**에서 온다.
- ⚠️ 다만 **두 입구의 재료는 같다** — FCM 은 `type` + `challengeId`, API 는 `type` + `referenceId`.
  같은 두 값이다.

**화면 관점 요구사항은 하나다: 규칙이 한 곳에만 있을 것.** 어디에 두고 무엇을 승격할지는 mobile-dev
설계 판단이다(`:core:push` 에 `:core:navigation` 의존이 현재 없다는 점만 덧붙인다 —
`core/push/build.gradle.kts` 실측).

🔴 **사본을 만들면 푸시와 목록이 서로 다른 곳으로 가는 날이 온다.** 특히 `CHALLENGE_REQUEST` 가
`Route.Home` 인 것(상세가 아니라 홈 — 수락/거절 액션이 홈 '받은 도전장' 섹션에만 있어서)과
`CHALLENGE_REJECTED` 가 `Route.Home` 인 것(거절된 챌린지는 계약서가 없어 상세에 볼 것이 없어서)은
**주석으로만 남아 있는 판단**이라, 사본을 쓰는 사람이 "당연히 상세겠지" 하고 틀리기 쉽다.

### §7.2 탭 불가 상태

| 경우 | 처리 |
|---|---|
| 모르는 타입 (§3.2.2) | 🔴 **`clickable` 을 붙이지 않는다.** 목적지를 모르는데 누르게 하면 아무 일도 안 일어나거나 엉뚱한 데로 간다 |
| `referenceId == null` | 동상 — 목적지를 특정할 수 없다. `PushEvent.from()` 이 이미 같은 판단을 한다(`challengeId?.let(::…)`, null 이면 이벤트 자체를 안 만든다) |

⚠️ **누를 수 없다는 것을 시각으로 표시하지 않는다** — 흐리게 처리하면 "고장난 알림"으로 보인다.
그냥 리플이 안 뜰 뿐이다. (모르는 타입은 §3.2.2 대로 무채색 아이콘이라 이미 톤이 낮다.)

### §7.3 대상이 사라진 경우 (spec 오픈이슈 3) — **새로 처리하지 않는다**

challenge-result 에서 실측된 `code 705` 경로가 이미 있다. **목록 탭도 같은 `Route` 로 보내므로 같은
처리가 난다** — 목적지 화면이 705 를 받아 처리하는 것이고, 목록은 그 사실을 알 필요가 없다.
🔴 **목록에 "삭제된 챌린지입니다" 같은 사전 판정을 넣지 마라.** 넣으려면 목록 조회가 대상의 생사를
확인해야 하고, 확인해도 탭하는 사이에 바뀔 수 있다.

**이것이 §7.1 "사본 금지"의 실질적 이득이다** — 규칙이 하나면 예외 처리도 하나다.

---

## §8 Compose 매핑 · 컴포넌트 배치

### §8.1 그대로 쓰는 것 — 신규 제작 불필요

| 컴포넌트 | 위치 | 용도 |
|---|---|---|
| `ChallengeScaffold` | `:core:designsystem` | 화면 골격 (§1) |
| `ChallengeTopBar` | `:core:designsystem` | 헤더 + 뒤로가기, `titleStyle` 기본값 (§2) |
| `VerticalSpacer` | `:core:designsystem` | 간격 |
| `CircularProgressIndicator` | Material 3 | 로딩 (§6) |

### §8.2 신규 — feature 모듈 `component/` 하위

| 컴포넌트 | 내용 |
|---|---|
| `NotificationCard` | §3. 아이콘 박스 + 메시지 + 상대 시각. **아이콘·색을 스스로 고르지 않는다**(§3.2.1) |
| `NotificationEmptyState` | §5. CTA·카드 크롬 없음 |

🔴 **`:core:designsystem` 이나 `:core:ui` 에 올리지 마라.** repos.json 의 `component_placement_rule`
(커밋 `72d9d9c`): *"feature 전용 컴포넌트는 해당 feature 모듈의 `component/` 하위에 둔다.
`:core:designsystem` 은 도메인 무관 프리미티브 + theme 만 보유."* 둘 다 알림 도메인 전용이다.

실패 화면(§6.1)은 보관함이 `ArchiveScreen.kt` 안에 private 컴포저블로 뒀다 — 같은 형태를 권한다
(`component/` 로 뺄 만큼 재사용되지 않는다).

### §8.3 모듈 배치 — 신규 `:feature:notification` 권고

현재 `Route.Notifications` 는 `MainScreen.kt:228` 에서 `PlaceholderScreen` 으로 끝난다.
화면·ViewModel·컴포넌트를 새 feature 모듈에 두는 것이 `component_placement_rule` 과 정합한다.
🔴 **최종 판단은 mobile-dev.** `:feature:main` 안에 두면 §7.1 의 `toRoute()` 접근 문제가 사라지는
대신 `:feature:main` 이 데이터 계층 의존을 갖게 된다 — 그 트레이드오프는 모바일 아키텍처 사안이다.

### §8.4 `:core:utils` 에 함수 1개 추가

§3.4 의 경과 시간 포맷. 🔴 **feature 모듈에 두지 마라** — `toRelativeKoreanString` 이 `:core:utils`
에 있고, 방향만 다른 형제 함수가 다른 모듈에 있으면 다음 사람이 못 찾아서 또 만든다.

### §8.5 아이콘 — `materialIconsExtended` 는 이미 전 모듈에 있다

⚠️ [mypage §3.4](../mypage/design.md) 가 *"`materialIconsExtended` 의존이 없다"* 고 적었으나 **지금은
아니다** — 실측 결과 **13개 모듈**(`:core:designsystem`·`:core:ui` + feature 11개)이 전부
`implementation(compose.materialIconsExtended)` 을 갖고 있다. `feature/mypage/build.gradle.kts:16`
도 그중 하나다 — mypage 작업 중에 추가된 것으로 보인다. **새 모듈에도 같은 줄이 필요하다.**

이 문서가 지정한 아이콘 6종: `SportsKabaddi`(사용 중) · `Description`(사용 중) · `CheckCircle` ·
`Cancel` · `Notifications`(사용 중) · `NotificationsNone` · `CloudOff`(사용 중).
⚠️ `Cancel`·`NotificationsNone` 은 앱에서 첫 사용이다 — **컴파일로 확인**하고, 없으면 §3.2 ·§5.2 의
대안(`Close` / `NotificationImportant`)을 쓴 뒤 회신하라.

---

## §9 신규 디자인 토큰 — **0건**

전수 대조. 이 화면이 쓰는 토큰은 전부 [colors.md](../../design-system/colors.md) ·
[tokens.md](../../design-system/tokens.md) 에 이미 있다.

| 자리 | 토큰 | 카탈로그 |
|---|---|---|
| 화면 배경 | `background` | colors.md §1.2 |
| 카드 배경 / 상단바 | `surface` | colors.md §1.2 |
| 카드 보더 | `outline` 1dp | colors.md §1.4 |
| 아이콘 박스 배경 | `secondary` | colors.md §1.3 |
| 메시지 · 제목 | `onBackground` | colors.md §1.2 |
| 상대 시각 · 부제 · 미지 타입 아이콘 | `onSurfaceVariant` | colors.md §1.2 |
| `CHALLENGE_REQUEST` · 빈 상태 일러스트 | `primary` (+ `alpha 0.10f`) | colors.md §1.1 |
| `CHALLENGE_ACCEPTED` · `OPPONENT_VERIFIED` | `success` | colors.md §1.5 |
| `CHALLENGE_REJECTED` · 홈 뱃지 점 | `error` | colors.md §1.5 |
| radius 16dp | `--radius-xl` | tokens.md §4 |
| 10 / 12 / 14 / 16 / 18sp | `text-[10px]`~`text-lg` | tokens.md §5.2 → `medium10`·`medium12`·`medium14`·`bold16`·`bold18` |

**타이포 슬롯도 신규 0건이다.**

### §9.1 🔴 카탈로그 갱신 — `success` 의 첫 실사용처가 여기다

[mypage §5.1](../mypage/design.md) 이 남긴 관찰:

> *"캘린더가 빠지면 앱에서 `success` 를 쓰는 자리가 사실상 사라진다. … 다만 `success` 는
> `VerificationStatusPill` 등 인증 축에서 쓰일 여지가 있어 chart 5색처럼 닫을 수 없다."*

**그 여지가 실현됐다.** 이 화면의 `CHALLENGE_ACCEPTED`·`OPPONENT_VERIFIED` 두 타입이 `success` 를
쓴다(§3.2). 🔴 **tokens.md §8 을 지금 고치지는 않는다** — `success` 는 §8 확인 항목이 아니었고(닫힌
항목은 chart 5색), mypage §5.1 은 확인 대상이 아니라 관찰 기록이다. **이 절이 그 관찰에 대한 회신**이다.

> ✅ **2026-09-01 — mypage §5.1 에 해소 블록이 들어갔다**(pm-lead, `0bd8b13`). 관찰문 자체는
> **지우지 않고 남겼다** — mypage 시점엔 참이었다.
>
> 🔴 **함께 확정된 경계를 여기에도 적는다: 이건 "해소"지 "무효"가 아니다.**
> 내가 찾은 `success` 실사용처는 **긍정 이벤트 축**이고, mypage §1.2.4 의 승/패/무 `primary` 매핑과
> §6-①("승 = success" 정본 어긋남)은 **경쟁 축**이다. **서로 다른 자리라 하나가 채워졌다고 다른
> 하나가 닫히지 않는다.** 이 문단이 없으면 다음 사람이 §9.1 만 읽고 §6-① 을 해결된 걸로 오독한다 —
> 경계를 한쪽 문서에만 두면 반대쪽에서 읽는 사람이 못 본다.

### §9.2 ⚠️ 미적용으로 남는 항목 2건 (기존 미결, 이 화면이 만든 문제 아님)

- **`glass-card` 의 `--gradient-card`** — tokens.md §2 에 `brushes.card` 로 매핑돼 있으나
  `FriendListItem`·`HomeEmptyState`·홈 `ChallengeCard`·`EmptyStateCard`·보관함 카드가 **전부 평면
  `surface`** 다. 이 화면도 선례를 따른다. 전 화면 동시 결정 사안.
- **`--shadow-card`** — 동상. 기존 카드들이 shadow 없이 1dp 보더로 경계를 낸다.

---

## §10 ⚠️ 디자이너 확인 대상

> **①·⑤ 는 2026-09-01 백로그에 🔵 로 등재됐다**(pm-lead, `0bd8b13`). 🔴 **둘 다 차단 사유가 아니다** —
> 이 문서의 판정대로 구현을 진행하고, 디자이너 회신이 오면 그때 조정한다. 나머지 행은 회신 대기 없이
> 확정으로 간다(정본에 근거가 없다는 사실을 기록해 둔 것이지 승인을 기다리는 것이 아니다).

| # | 항목 | 현재 처리 |
|---|---|---|
| ① | 🔴 **정본이 4개월 반 낡았다** — `notifications.tsx` 는 2026-04-16 이후 미수정이고, mock 6종은 2026-08-06 타입 재정의 **이전** 목록이다 | **재-export 없이 진행**(§0.1). 형태는 정본, 타입 목록은 서버 실측. 디자이너가 알림 화면을 다시 그릴 계획이 있는지만 확인 |
| ② | 🔴 **`CHALLENGE_REQUEST` 문구 조사** — `"{닉}과 계약을 하시렵니까?"` 는 받침 없는 닉네임에서 **"민수과"**. 4종 중 이 종만 `님` 도 없다 | **고치지 않고 진행**(§3.3.1). 사용자 확정(2026-08-07) 문구다. 다만 **확정 당시엔 푸시뿐이었고 이제 목록에 남는다** — 노출 조건이 달라졌으므로 재확인 요청 |
| ③ | **어제보다 오래된 알림의 시각 표기** — 정본이 `"어제"` 까지만 보여준다 | `"{M}월 {d}일"` 제안(§3.4). 근거는 앱 관례([mypage §2.4.3](../mypage/design.md))뿐. `"{N}일 전"` 대안 있음 |
| ④ | **빈 상태 문구·아이콘** — 정본에 빈 상태 자체가 없다 | `"아직 알림이 없어요"` / `"챌린지가 오가면 여기에 쌓여요"` / `NotificationsNone`, **CTA 없음**(§5.2) |
| ⑤ | 🔴 **`CHALLENGE_ACCEPTED`·`CHALLENGE_REJECTED` 아이콘·색** — 정본에 두 타입이 **없다** | `Description`+`success` / `Cancel`+`error` (§3.2). 앱 관례와 정본 인접 사건에서 유도했으나 **정본 근거가 아니다** |
| ⑥ | **뒤로가기 버튼** — 정본에 없다 | 추가(§2.2). 앱엔 브라우저 뒤로가기도 `<BottomNav />` 도 없다 |
| ⑦ | **진입 애니메이션 미구현** — 정본은 스태거 `slide-up` | 미구현 확정(§1.1). 네 목록 화면이 이미 전부 미구현 |
| ⑧ | **홈 벨 뱃지 = 점 유지** — 서버가 `unreadCount`(숫자)를 주는데 정본·구현은 둘 다 점이다 | **점 유지**(§4.5). 정본 `index.tsx:130` 이 `w-2 h-2`(점)이고, (B) 안에서 숫자는 사용자의 행동을 바꾸지 못한다. **디자이너 이탈 없음** — 확인이 아니라 기록 목적의 행이다 |

---

## §11 pm-lead 백로그 요청 — ✅ **전부 처리됨 (2026-09-01, `0bd8b13`)**

> 🔴 **이 표는 열린 요청이 아니다.** 5건 전부 pm-lead 가 처리했고, 아래는 **무엇을 어떻게 처리했는지의
> 기록**이다. 남은 작업으로 읽지 마라.

| # | 항목 | 처리 결과 |
|---|---|---|
| ① | ~~**`hasUnreadNotification = false` 하드코딩**~~ | ✅ **소멸.** 읽음 처리 (B) 채택으로 뱃지가 이번에 점등된다(§4.5). 등재할 죽은 UI 가 없다 |
| ①' | ⚠️ **뱃지 위치 육안 검증** — 정본은 버튼 기준 6px(`top-1.5 right-1.5`), 구현은 10dp(`HomeTopBar.kt:80`). 40dp 버튼에 24dp 아이콘이라 여백이 다르다 | ✅ 🟢 **백로그 등재.** **이번 feature 에서 점이 처음 켜지므로** 실물을 보고 판단한다 — 켜진 걸 본 적 없이 좌표만 옮기지 않는다. 지금은 안 고친다 |
| ② | **`EmptyStateCard` 의 CTA 필수 제약** — CTA 없는 빈 상태의 **두 번째** 사례([mypage §2.5.1a](../mypage/design.md) 가 첫 번째) | ✅ 🟢 **백로그 등재.** 지금 통합하지 않는다 — pm-lead 판단: **통합에 필요한 건 `onClickCta` optional 여부가 아니라 세 사례의 공통 형태**다 |
| ③ | **[mypage §5.1](../mypage/design.md) 에 역참조** | ✅ **해소 블록 삽입.** 관찰문은 지우지 않고 존치. 🔴 **경계 함께 확정** — "해소"지 "무효"가 아니다(§9.1 인용 블록) |
| ④ | **repos.json `mobile.modules` 가 낡았다** — `:core:push` · `:core:permission` 누락 | ✅ **정정.** `settings.gradle.kts` 와 **양방향 차집합 0**(32개 일치). 🔴 **두 번째 사고라**(1회 없는 모듈 추가, 2회 있는 모듈 누락) 대조 명령을 `_modules_comment` 에 박았다 — 이 목록은 **틀려도 아무것도 실패하지 않아** 조용히 낡는다 |
| ⑤ | ⚠️ **[home-feed/design.md:34](../home-feed/design.md) 의 `"2.dp dot"`** | ✅ **8.dp 로 정정** + `destructive` → `error` 토큰명. 🔴 **같은 줄에 "코드를 이 문서에 맞추지 마라"를 박았다** — 방향을 명시하지 않은 정정은 절반만 고친 것이다. 오독 원인(`w-2` = `0.5rem` = 8px 인데 숫자만 옮겨 적음)도 남겨 다른 `w-N` 에서 재발하지 않게 했다 |

---

## 변경 이력

| 일시 | 변경 | 작성자 |
|------|------|-------|
| 2026-09-01 13:12:19 | 최초 작성 (T-D1). `notifications.tsx` 스냅샷 기준. 주요 판정 7건 — ① 정본이 2026-04-16 이후 미수정이라 mock 6종과 발송 4종이 서로 다른 목록임을 §0 에 근거로 등재, 재-export 없이 진행 ② 타입 매핑 4종 확정 + `ACCEPTED`/`REJECTED` 2종은 정본 부재로 신규 유도(§3.2), 미지 타입 폴백은 `NotificationMessages` KDoc 의 "구버전 앱" 운용 근거로 **가정이 아님**을 명시 ③ 🔴 **`toRelativeKoreanString` 재사용 불가 실측** — 미래 카운트다운 함수라 과거 시각에 전부 `"마감"` 출력. 신규 경과 포맷 5가지 확정(§3.4) ④ 읽음 처리 — 홈 벨 뱃지가 이미 구현됐고 `false` 하드코딩된 실측을 근거로 **"진입 시 전체 읽음, 카드 2상태 없음"** 권고(§4) ⑤ `EmptyStateCard` 기각 + `NotificationEmptyState` 신설(§5) ⑥ `titleStyle` 은 마이페이지와 **반대로** 기본값 `bold18`(하위 화면, `ArchiveRoute` 선례) ⑦ 진입 애니메이션 미구현 확정. 신규 토큰 0건. | design-bridge (noti-design) |
| 2026-09-01 13:41:00 | **pm 판정 반영 개정 (2건 수신).** ① **읽음 처리 = (B) 확정** — 초판 §4.3 권고안이 그대로 채택됐다(`read-all` + `unreadCount`, 행 단위 `isRead` 없음). §4 머리에 확정 블록, §4.4("빼기로 하면")를 **무효 표기 후 존치**. 🔴 단 §4.2 는 무효가 아님을 명시 — (B)는 *"들어오기 전"* 질문만 답하고 *"어디까지 봤나"* 는 그대로 남는다(C안 재론 조건 기록). ② 🔴 **홈 벨 뱃지가 범위로 들어와 §4.5 신설** — **점 유지, 숫자로 안 간다.** 근거 3개(정본 `index.tsx:130` 이 점 / (B) 안에서 개수는 사용자의 행동을 못 바꾼다 / 구현이 이미 점이라 숫자는 폭 가변·겹침·99+ 를 새로 만든다). 크기 8dp·색 `error` 는 정본과 구현이 **이미 일치**해 신규 UI 0건. §4.5.1 에 (B)의 유일한 화면 리스크 등재 — **목록에서 돌아온 홈에 점이 남으면 안 된다**(수단은 mobile 판단, 결과만 요구). 실시간 점등은 요구하지 않음. ③ **페이지네이션 = 커서 무한 스크롤 확정** — 초판 우선순위 ①(최근 N건)이 기각됐고 **무효 사유를 남긴 채 존치**(상한은 언젠가 조용히 잘리고 그걸 아무도 모른다). §6.3 신설 — 하단 인디케이터 / **끝 도달 무표시** / 부분 실패는 목록 유지 + 스낵바 + 하단 `"다시 시도"`. 상태 매트릭스 3행 추가. §11-① 소멸(뱃지 점등으로 해소), §11-①' 신설(뱃지 위치 육안 검증), §10-⑧ 신설. | design-bridge (noti-design) |
| 2026-09-01 13:55:00 | **§3.2.2 폴백 근거 갱신 (T-D1 승인 후, 문서 구조 변경 없음).** backend 가 `type` 을 **정규화하지 않은 DB 원문 String** 으로 내리기로 확정해, 초판이 "관측된 운용 방식"으로 논증했던 폴백의 전제가 **계약으로 확정**됐다. 계기가 된 서버 실측을 직접 재확인하고 인용을 붙였다 — `NotificationEntity.kt:61-62` 의 `getOrDefault(NotificationType.CHALLENGE_REQUEST)` 가 모르는 type 을 조용히 강등해, 그대로 두면 폐기된 `SIGN_REQUEST` 가 **"도전장 도착"** 으로 찍힌다. 🔴 **모르는 타입보다 나쁘다 — 아는 척하는 오답이라서다.** 두 결정(서버가 원문 보존 / 앱이 폴백 표시)이 서로를 성립시킨다는 점을 명시. **판정 변경 0건** — §3.2.2 의 폴백 규격(무채색 아이콘·탭 비활성·숨기지 않음)은 초판 그대로다. | design-bridge (noti-design) |
| 2026-09-01 14:05:00 | **백로그 5건 처리 결과 반영 (pm-lead `0bd8b13`). 판정 변경 0건.** ① **§11 을 "요청"에서 "처리 기록"으로 전환** — 5건 전부 처리됐는데 표가 열린 요청처럼 읽히면 다음 사람이 이미 끝난 일을 다시 한다. 각 행에 처리 결과를 붙이고 머리에 🔴 *"열린 요청이 아니다"* 를 박았다. 처리 3건은 파일로 직접 확인했다(`repos.json` `:core:push`·`:core:permission` 추가 / `home-feed/design.md:34` `8.dp`+`error` 정정 / `mypage §5.1` 해소 블록). ② **§10 머리에 ①·⑤ 백로그 등재 + 🔴 차단 사유 아님** 명시 — 확인 대상 표가 "회신 대기"로 오독되면 구현이 멈춘다. ③ 🔴 **§9.1 에 축 구분 경계 추가** — pm-lead 가 mypage 쪽에 박은 *"해소지 무효가 아니다"*(알림의 `success` = **긍정 이벤트 축** vs 승/패/무 = **경쟁 축**)를 이쪽에도 옮겼다. **경계를 한쪽 문서에만 두면 반대쪽에서 읽는 사람이 못 본다** — §9.1 만 읽고 mypage §6-① 을 해결된 걸로 오독하는 경로를 막는다. | design-bridge (noti-design) |
