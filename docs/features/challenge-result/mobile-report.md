# Mobile Report — challenge-result

- **작성**: 2026-08-25, result-mobile
- **상태**: **T-M1 · T-M2 · T-M3 · T-M4 전부 완료**
- **작업 브랜치**: `main` (새로 만들지 않음)

## 구현 요약

판정 결과를 **상세와 홈 두 화면 모두**에 개통했다.

**상세** — VS 헤더의 한 자리가 시간 순으로 주인을 넘겨받는 구조가 됐다: `남은 시간: 5시간 32분`(마감 전)
→ `판정 대기 중`(마감 후·판정 전) → `승리`/`패배`/`무승부`/`양측 패배`(판정 후). 앞의 두 구간은
challenge-verification 에서 이미 만들어져 있었고, 이번에 세 번째가 붙으면서 그 자리의 이름과 타입을
결과까지 담도록 넓혔다.

**홈** — 판정 후 7일 이내의 챌린지가 `/challenges/active` 에 섞여 오므로, 목록을 `status` 로 갈라
`진행 중인 챌린지` 구획과 `최근 결과` 구획으로 나눠 그린다. 결과 카드는 남은 시간 자리에 결과 pill 을 단다.

**관점 뒤집기의 주체가 엔드포인트마다 다르다 — 의도한 것이다.**

| | 좌표계 | 뒤집는 주체 |
|---|---|---|
| `GET /challenges/{id}` (상세) | 역할 기준 `result` | **앱** (계약 §1, soul-oath §3) |
| `GET /challenges/active` (홈) | 내 시점 `myResult` | **서버** |

상세는 계약서 화면이라 양측 서명을 실명·역할로 나란히 세워야 해서 역할 기준이 맞다. 홈 응답은
`myMission`/`myVerificationStatus` 등 **전 필드가 이미 내 시점**이라 거기에 역할 기준 값을 하나 끼워
넣는 쪽이 이물질이다. 각 엔드포인트가 자기 좌표계를 일관되게 지키는 편을 택했다.

## 사용한 모바일 레포 스킬

- `modify-feature`: 기존 상세·홈 화면에 필드와 표시 상태를 얹는 작업이라 신규 feature 가 아닌 수정
  절차를 따랐다. 코드 편집은 전부 `cd challenge-app && claude -p` child 위임(**6회** — 데이터 레이어 2,
  상세 UI 2, 홈 UI 2), 빌드·테스트는 본체 background 실행.
  ⚠️ 상세 UI 패스 1회가 Bash 10분 캡에 걸려 SIGTERM 됐으나 **편집은 전부 반영된 뒤**였다(파일 상태로
  확인 후 컴파일로 검증). 이후 패스는 범위를 더 잘게 쪼갰다.

## 설계 판단

### 1. `deadline*` → `headline*` 개명 — 이름이 거짓말을 하게 됐다

그 자리가 더 이상 마감만 그리지 않으므로 `DeadlineDisplay.kt` → `HeadlineDisplay.kt`,
`deadlineText`/`deadlineTone` → `headlineText`/`headlineTone`, `DeadlineTone` → `HeadlineTone` 으로
옮겼다. 🔴 **`deadlineAbsoluteText` 는 이름 그대로 뒀다** — `OathSummaryCard` 의 절대 마감 표기는
진짜 마감이고 결과와 무관하다.

### 2. 문자열과 톤을 한 함수가 함께 돌려준다

기존 `deadlineDisplayText()` / `deadlineDisplayTone()` 두 함수를 `headlineDisplay()` 하나로 합쳐
`HeadlineDisplay(text, tone)` 를 통째로 반환한다. 기존 KDoc 이 *"문자열과 tone 이 서로 다른 순간의
시계를 보면 '판정 대기 중' 이 촉구색으로 나올 수 있다"* 고 **걱정만 하고 호출 규약으로 막고 있던
위험**을, 반환을 묶어 구조적으로 없앴다. 결과가 붙으면서 어긋날 수 있는 축이 시계 하나에서
시계+관점 둘로 늘어나 합치는 편이 더 필요해졌다.

### 3. 🔴 서버 불변식이 깨져도 결과를 날조하지 않는다 — 방어 코드 없이

`headlineDisplay()` 의 분기 순서가 `result != null` → `deadline <= now` → `else` 다. 이 순서 덕에
`status == COMPLETED` 인데 `result == null` 인 조합(서버 불변식 위반)이 **별도 방어 분기 없이**
`판정 대기 중` 으로 떨어진다. 백엔드가 `status == COMPLETED ⟺ result != null` 을 불변식으로
보장한다고 계약에 적었으므로 전용 분기를 두지 않았고, 그래도 깨졌을 때의 낙하 지점이 안전하다.
테스트로 고정했다 (`COMPLETED 인데 result 가 null 이면 판정 대기 중으로 남는다`).

### 4. 관점을 모를 때 승패를 내 것으로 말하지 않는다

`userInfo` 조회 실패 등으로 내가 어느 쪽인지 모르면 `승리` 대신 **`우건 승리`** 처럼 역할 실명으로
낮춘다. 기존 코드가 같은 상황에서 서명 라벨을 `나` 대신 실명으로 낮추던 폴백과 같은 판단이다.
`ResultView` sealed interface 로 `Mine(outcome)` / `ByRole(result, 두 닉네임)` 을 갈랐다.

### 5. 승패무 색은 새로 정하지 않았다 — 홈 `StatsBar` 의 색 언어를 따랐다

디자인 산출물이 없어 **신규 토큰 0건**으로 갔다. 승=`primary` / 패=`error` / 무=`onBackground` 는
홈 전적 카드가 이미 쓰던 매핑이고, 상세만 다른 색을 쓰면 같은 사실이 두 화면에서 다른 색이 된다.
패배 아이콘 `Icons.Filled.Cancel` 도 홈 `VerificationStatusPill` 의 실패 표현과 같은 아이콘이다.

### 6. 🔴 홈 — "진행 중" 의 의미를 지키면 문구를 하나도 안 바꿔도 된다

COMPLETED 가 같은 배열에 섞여 오면 홈에서 **두 곳이 거짓말을 한다**:

1. 섹션 제목이 리터럴 `"진행 중인 챌린지"` + `challenges.size` 라, 진행 중 0건인데 **"진행 중인 챌린지
   2개"** 가 뜬다
2. `emptyType` 이 `challenges.isEmpty()` 라, 진행 중이 0인데도 결과 카드 때문에 빈 상태가 **영영 안 뜬다**.
   그런데 빈 상태 문구 2종이 **둘 다 "진행 중인 챌린지가 없어요"** 다

`inProgressChallenges` / `completedChallenges` 로 안정 분할하고 **진행 중만 세도록** 고쳤다. 그러면
문구를 한 글자도 바꿀 필요가 없다 — 그래서 `HomeEmptyState` 는 손대지 않았다. 재정렬은 하지 않는다
(서버가 정렬 책임이고, `filter` 는 안정 분할이라 두 구획 각각의 내부 순서가 서버가 준 그대로 남는다).

`FIRST_USER` 조건도 보강했다 — **최근 결과가 있으면 신규 사용자가 아니다.** 판정된 결과가 이미 있는
사람에게 "친구를 등록하고 첫 약속을 걸어보세요" 는 틀린 말이다.

### 7. 🔴 승패무 표현을 `:core:ui` 로 승격 — 두 화면이 한 출처를 쓴다

문구(`승리`/`패배`/…)는 상세의 `HeadlineDisplay.kt` 상수에, 색·아이콘은 `VsHeaderCard` 안에 있어서
홈에서 쓸 수 없었다. 복사했으면 **"승리가 무슨 색인가" 가 두 곳에 생겨 갈라진다.**
`core/ui/.../ChallengeOutcomePill.kt` 를 신설해 문구 상수 + `challengeOutcomeVisualOf()` + 카드용
`ChallengeOutcomePill` 을 모으고, 상세의 두 지점이 이걸 쓰도록 고쳤다. `VerificationStatusPill` 과
같은 자리·같은 규격이고, **상세 테스트 41개가 그대로 통과**해 겉보기 동작 무변경이 확인됐다.

`HeadlineTone.LOSE` 가 `LOSE`·`BOTH_LOSE` 를 함께 받아 outcome 과 1:1 이 아닌데, **상세는 문구를 이미
state 에 확정해 들고 오므로 위임 시 label 을 버리면 차이가 새지 않는다**는 불변식으로 정리하고 양쪽에
주석으로 박았다.

### 8. 🔴 구현 중 자체 발견·수정한 결함 2건

**(a) 승리 문구에 카운트다운 시계가 붙었다.** 관점 미상의 결과에 `NEUTRAL` 톤을 주도록 처음
설계했는데, `NEUTRAL` 은 `판정 대기 중` 과 공유하는 값이라 **아이콘이 시계**였다. 결과적으로
`우건 승리` 옆에 시계가 붙었다 — 하필 `headlineVisualOf()` 의 KDoc 이 *"색만 따로 고르면 '승리' 에
시계 아이콘이 남는 조합이 생긴다"* 고 경계하던 바로 그 조합이다. 색은 안 기울이되 아이콘은 갈라야
해서 `DECIDED_NEUTRAL`(`onSurfaceVariant` + 트로피)을 신설했다. **두 톤이 다시 합쳐지는 것을 막는
회귀 테스트**를 넣었다 (`관점 미상 결과와 판정 대기 중은 서로 다른 톤이다`).

**(b) 결과를 모르는 판정 완료 카드에 시계가 남았다.** 홈 카드의 `remainingText` 기본값이 `""` 라,
`status == COMPLETED` 인데 `outcome == null` 인 카드가 **빈 문자열 + 시계**로 그려졌다.
🔴 **이건 도달 불가능한 예외가 아니라 우리가 의도적으로 만든 경로다** — 매퍼가 모르는 `myResult` 를
null 로 흡수하고 항목은 살리므로, 서버가 결과 종류를 하나 추가하면 그날부터 실제로 내려온다. tolerant
매핑을 고르고 렌더 경로를 깨진 채 두면 그 선택의 의미가 없다. `remainingText` 를 `String?` 로 바꿔
3분기(결과 pill / 시계+텍스트 / **아무것도 안 그림**)로 정리하고 프리뷰로 고정했다. 빈 자리가 틀린
자리보다 낫다.

### 9. 🔴 실서버 원문 픽스처 — `/challenges/active` 에만 없던 구멍

`GET /challenges/{id}` 와 `/verifications` 에는 실서버 원문 픽스처 테스트가 있는데
**`/challenges/active` 에만 없었다.** 기존 `ActiveChallengeResponseMapperTest` 는 DTO 를 코드로
조립해 매퍼만 검증하므로 **DTO 바인딩 층(JSON 키 이름·날짜 포맷·enum 문자열)이 통째로 사각지대**였다.
backend 가 실서버 응답 원문을 넘기며 *"손으로 쓴 픽스처 말고 이걸 박아라"* 고 요청해 신설했다
(`ActiveChallengeWireFixtureTest`, 9 tests). 근거는 이미 상세 쪽 파일 KDoc 에 적혀 있던 사건이다 —
*"실서버에서 떴다는 사실이 대표 응답을 떴다는 뜻은 아니다."*

원문 바이트 → 도메인까지 한 번에 통과시켜 고정한 것:
- **IN_PROGRESS 와 COMPLETED 를 한 응답에** (이 목록은 정의상 두 상태가 섞여 오므로 한쪽만 덮으면 절반이 사각지대)
- 🔴 **역할 기준 `result` 키를 앱이 모르는데도 파싱이 안 깨진다** — `ActiveChallengeDto` 에 그 필드가
  없고 `ignoreUnknownKeys` 가 흡수한다. **끄면 홈이 통째로 죽는다**는 것을 `ignoreUnknownKeys = false`
  로 `SerializationException` 을 실패 고정해 증명했다. 항목 하나 드롭이 아니라 전면 장애다
- `myVerificationStatus = FAILED` 가 도메인까지 도달 — 이번 판정 feature 로 **처음 실제로 흐르기 시작한 값**
- `IN_PROGRESS` 항목에도 `result`/`myResult` **키가 존재하고 값만 null**
- 서버가 준 **순서 보존**, `droppedCount == 0`
- 픽스처 2개 — backend 가 `myResult` 를 3값으로 접던 시점의 **원문 그대로**(하위호환 증거, `LOSE` 로
  읽힘) + 4값 확정 후의 **현행 대표 응답**(`BOTH_LOSE`)

## 변경된 파일

**신설 5**
- `remote/mapper/src/commonTest/.../ActiveChallengeWireFixtureTest.kt` — **실서버 원문** 픽스처 (아래 §9)
- `domain/model/.../challenge/ChallengeResult.kt` — `ChallengeResult`(역할 기준 4종) + `ChallengeOutcome`(내 시점 4종) + `outcomeFor(isMeOpponent)`
- `domain/model/.../ActiveChallengeStatus.kt` — `IN_PROGRESS`/`COMPLETED` (홈 목록 전용 부분집합)
- `feature/challenge/detail/.../contract/HeadlineDisplay.kt` — `HeadlineTone`, `HeadlineDisplay`, `ResultView`, `headlineDisplay()`
- `core/ui/.../components/ChallengeOutcomePill.kt` — 승패무 문구 상수 + `challengeOutcomeVisualOf()` + 카드용 pill

**삭제 1**
- `feature/challenge/detail/.../contract/DeadlineDisplay.kt` — `HeadlineDisplay.kt` 로 대체(개명)

**수정 16**
- `domain/model/.../challenge/ChallengeDetail.kt` — `result: ChallengeResult?`
- `domain/model/.../ActiveChallenge.kt` — `status`, `outcome`
- `remote/model/.../ChallengeDetailResponse.kt` · `ActiveChallengeResponse.kt` — `result` / `status`·`myResult` (전부 `String`, typed enum 금지 근거 KDoc)
- `remote/mapper/.../ChallengeDetailMapper.kt` · `ActiveChallengeResponseMapper.kt` — tolerant 변환
- `remote/mapper/.../MappedList.kt` — `droppedCount` 사유가 늘어 KDoc 갱신
- `feature/challenge/detail/` — `ChallengeDetailViewModel.kt`, `contract/ChallengeDetailState.kt`, `component/VsHeaderCard.kt`, `screen/ChallengeDetailScreen.kt`
- `feature/home/` — `contract/HomeUiState.kt`, `HomeScreen.kt`, `component/ChallengeCard.kt`
- 테스트 5: `ChallengeDetailMapperTest`, `ChallengeDetailWireFixtureTest`, `ActiveChallengeResponseMapperTest`, `ChallengeDetailViewModelTest`, `HomeViewModelTest`
- `feature/challenge/oath/.../OathViewModelTest.kt` — fixture 한 줄 (컴파일 유지용)

`20 files changed, +1270 −150`

## 테스트 결과 (실측 XML)

**Android** (`testDebugUnitTest`) — **186 tests / 0 failures**

| 모듈 | tests | failures | timestamp (UTC) |
|---|---|---|---|
| `:remote:mapper` | **100** | 0 | 07:28:45Z |
| `:feature:challenge:detail` | **41** | 0 | 07:17:24Z |
| `:feature:home` | **24** | 0 | 07:19:51Z |
| `:feature:challenge:oath` | 17 | 0 | 07:19:42Z |
| `:core:ui` | 4 | 0 | 07:17:18Z |

**iOS** (`iosSimulatorArm64Test`) — **165 tests / 0 failures**

| 모듈 | tests | failures | timestamp (UTC) |
|---|---|---|---|
| `:remote:mapper` | **100** | 0 | 07:28:47Z |
| `:feature:challenge:detail` | **41** | 0 | 07:20:12Z |
| `:feature:home` | **24** | 0 | 07:20:05Z |

- Android 빌드: **ok** / iOS 빌드: **ok**
- 신규 테스트 **+39** (베이스라인 mapper 75 → 100, detail 31 → 41, home 20 → 24)
- 🔴 **상세 41개가 T-M3 후에도 그대로** — `:core:ui` 승격이 겉보기 동작을 안 바꿨다는 증거다

🔴 **iOS stale 오탐을 두 번 배제했다.** 이 레포는 iOS XML 이 오래 남아 있어 그냥 읽으면 통과로 오판한다.

1. **T-M2 후**: 실행 전 detail iOS XML 이 `tests="31"` / `00:57:33Z`(변경 전 베이스라인)였다. 실행 후
   `41` / `06:52:10Z` — **개수와 timestamp 가 모두 전진**해 확인.
2. **T-M3 후**: detail 은 이번에 테스트가 늘지 않아 **개수(41)가 그대로**라, 개수만 보면 stale 과
   구분되지 않았다. 실행 전 `06:52:10Z` → 실행 후 `07:20:12Z` 로 **timestamp 만으로** 판별했다.
   `:feature:home` 은 iOS 결과 디렉터리 자체가 없다가 이번에 생성됐다.

## 새로 덮은 케이스

**상세**
- 관점 뒤집기 **양방향** — challenger 가 본 `CHALLENGER_WIN`(승리) / opponent 가 본 같은 값(패배),
  `OPPONENT_WIN` 도 양방향
- `DRAW` → 무승부 / `BOTH_LOSE` → 양측 패배(톤 LOSE)
- 관점 미상 → 실명 표기 + `DECIDED_NEUTRAL`, 그리고 **`판정 대기 중` 과 톤이 다르다**(회귀 방지)
- `COMPLETED` + `result == null` → 판정 대기 중
- 마감 전인데 결과가 있으면 **결과가 이긴다**(분기 순서 고정)
- 모르는 `result` 문자열("CANCELLED") → null 이고 **나머지 필드는 정상 매핑**
- wire fixture 에 `result` 키 있음/없음/값 있음 3종

**홈**
- 진행 중 + 판정 완료 혼합 응답이 두 구획으로 **정확히 갈린다**, 각 구획 내부 **순서 보존**
- 🔴 진행 중 0건 + 판정 완료 N건 → `emptyType` 이 `NO_ACTIVE_CHALLENGE`(빈 상태가 사라지지 않는다)
- 🔴 전적 0 + 진행 중 0 + 받은 도전장 0 인데 최근 결과가 있으면 **`FIRST_USER` 가 아니다**
- `myResult` 4값 각각 → 대응 `ChallengeOutcome`, 모르는 값 → null 이고 **항목은 살아남는다**
- 🔴 모르는 `status`("ARCHIVED"/"CANCELLED") → 항목 드롭 + `droppedCount` 증가
- 🔴 `status` 키가 **없는** 구버전 wire 원문 → 드롭 0, 전부 `IN_PROGRESS`

## Working tree 상태

- 작업 브랜치: `main` — 새로 만들지 않았다
- 변경분은 staged/unstaged 그대로 뒀다. **커밋·푸시·PR 생성 안 함** (사용자 처리 영역)
- 신설 4 / 삭제 1 / 수정 16, `20 files changed, +1270 −150`
- ⚠️ `DeadlineDisplay.kt` 의 삭제만 **staged** 상태다 (child 가 파일 개명을 `git mv` 로 처리). 나머지는 unstaged

## 미해결 이슈

### ⚠️ `"최근 결과"` 는 시안에 없는 새 문구다

홈의 판정 완료 구획 제목을 `"최근 결과"` 로 새로 지었다. Lovable 에 결과 목록 화면이 0건이라 참조할
디자인이 없고, 진행 중 구획과 **같은 규격**(`SectionTitleRow`)을 재사용했다. 디자이너 확인 대상이며
교체 비용은 문자열 하나다.

### ⚠️ 미답 확인 1건 — 판정과 `FAILED` 전이의 트랜잭션 경계

상세는 `GET /challenges/{id}` + `GET /challenges/{id}/verifications` **두 번** 호출한다. 배치가
`challenges` 와 `verifications` 를 따로 커밋하면 그 사이에 조회한 사용자는 **"승리" + 상대 뱃지
"대기중"** 을 본다. 한 트랜잭션이면 이 창이 없다. backend 회신 대기 중이며, 갈라진다면 앱이 방어할
방법이 없어 표시 규칙을 따로 만들어야 한다.

### 처리하지 않기로 한 것 — `EXPIRED` 상세 표기 (근거 있는 미처리)

이번에 서버가 새로 만드는 상태지만 **상세 화면에 도달할 경로가 없다.** 네비게이션 진입점을 전수
확인했다 — 홈 카드 탭(`HomeRoute.kt:28`)과 푸시 딥링크 2종(`MainViewModel.kt:93` `ChallengeAccepted`,
`:97` `OpponentVerified`)뿐이고, `EXPIRED` 는 `PENDING` 에서만 발생하는데 그 셋 중 어느 것도
`PENDING` 챌린지를 상세로 보내지 않는다(받은 도전장은 홈에서 인라인 수락/거절). 관측되지 않는
상태에 분기를 넣지 않는다는 레포 규칙에 따라 미처리하고 근거만 남긴다. **홈에 `EXPIRED` 를 노출하게
되면 이 판단이 뒤집힌다** — 계약이 `EXPIRED` 미노출로 가고 있어 현재는 유효하다.

### 참고 — 기존 잠재 위험 1건 (이번 범위 밖, 확인 요청함)

`ActiveChallengeDto.myVerificationStatus` 는 typed `@Serializable enum VerificationStatusDto` 라
서버가 인증 상태를 하나 추가하면 **홈 목록 전체의 역직렬화가 깨진다**. 상세 쪽
`PartyVerificationDto.status` 는 `String` 인데 여기만 typed 다. 현재 3종을 모두 처리하고 있어
관측된 버그는 아니므로 손대지 않았고(안 일어날 일에 방어 코드를 넣지 않는다), backend 에 "인증 상태
추가 계획이 있는지" 물어 뒀다. 있다면 그때 `String` 으로 낮춘다. **이번에 추가한 `status`·`myResult`
는 같은 실수를 반복하지 않으려 처음부터 `String`** 이고, 그 대비를 해당 파일 주석에 남겼다.

## API 계약 대비 구현 차이

없다.

- §1 `GET /challenges/{id}` 의 `result` — nullable / 키 항상 존재 / **역할 기준** / 모르는 값은 앱이 흡수
- §2 `GET /challenges/active` 의 `status`·`myResult` — 단일 배열 / **내 시점** `myResult` 4값
  (`BOTH_LOSE` 포함) / 서버 정렬 / `EXPIRED` 미노출 / 판정 후 **7일**

🔴 **계약에 없어 앱이 자체 결정한 것 1건**: `status` 키가 **누락/빈 문자열**이면 항목을 드롭하지 않고
`IN_PROGRESS` 로 간주한다. 이 필드가 생기기 전 이 목록은 정의상 전부 진행 중이었으므로 **구버전 서버
응답의 의미를 정확히 복원**하는 것이다. 이렇게 하지 않으면 서버 배포 전에 앱을 돌릴 때 모든 항목이
드롭되어 **진행 중인 챌린지가 있는데도 홈이 통째로 비는** 조용한 전면 장애가 난다. 값은 있는데 모르는
값(예: `"ARCHIVED"`)은 복원할 의미가 없으므로 기존 방침대로 항목 드롭이다. 두 경우를 갈라 테스트로
고정했다 (`status 키가 없는 구버전 응답 - 목록이 비지 않고 전부 IN_PROGRESS`).

## 계약 협의 기여 (기록)

- **streak 오픈 이슈가 stale 임을 발견** — home-feed api-contract(`confirmed` v2)가 집계 규칙을 이미
  확정해 뒀고 앱이 그 위에 출시돼 있다(`UserRecord.kt:9` KDoc, 홈 `StatsBar` "연승" 라벨). 새로 정할
  게 아니라 이행할 것이었다. spec 정정됨
- **결과 도달 경로에 기한이 생기는 문제 제기** — 히스토리 화면이 없어 노출 창이 닫히면 그 결과는 앱
  어디에서도 도달 불가. N=3 → **7일** 로 확정되고 "결과 히스토리 화면 부재" 백로그 등재
- **홈 카드 관점 좌표계** — active 응답은 이미 전부 내 시점(`myMission`/`myVerificationStatus`)이라
  역할 기준 `result` 가 이물질이라는 점, 그리고 `amIChallenger: Boolean` 은 키 누락 시 기본값 `false`
  로 **승패를 반대로 그리는** 실패 모드라는 점을 근거로 `myResult` 안을 요청
