# Mobile Report — loser-ranking

- **작성**: 2026-08-26 mobile-dev(rank-mobile)
- **상위 spec**: [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [design.md](./design.md)
- **상태**: ✅ **구현 완료 · 계약 `confirmed` 대조 완료 · 실서버 원문 픽스처 반영 완료**

## 구현 요약

4탭 중 마지막 placeholder 였던 랭킹 탭을 실화면으로 교체했다. `PlaceholderScreen("랭킹")` 한 줄에서
**도메인~remote 계층 신설 + Top3 포디움 + "수치의 명단" + 빈 상태**까지 전 계층을 세웠다.

**네비게이션 작업은 0이었다.** 랭킹은 원래 탭이라 3곳이 전부 배선돼 있었다 — `Route.kt:26`
(`data object Ranking` + `:74` 다형성 등록), `MainScreen.kt:208`(`entry<Route.Ranking> { RankingRoute() }`),
`BottomNavItem.kt:28`. 순수 화면 교체였다.

## 사용한 모바일 레포 스킬

- `data-remote` + `domain`: 랭킹 API 계층 신설 (DTO → Api → Mapper → RemoteDataSource → RepositoryImpl).
  `record` 체인(단일 소스 GET 표준형)을 미러링했다.
- `feature`: `:feature:ranking` UiState/ItemState/ViewModel/Screen/Route + component 8종.
- `test-viewmodel`: ViewModel + ItemState 테스트. wire 픽스처는 `ActiveChallengeWireFixtureTest` 형식 승계.

코드 편집은 전부 **cwd=challenge-app 의 child claude 위임**으로 했다(4회). 빌드·테스트는 본체 background.

## 변경된 파일

### 신규 (24)

**도메인·데이터 (8)**
- `domain/model/.../domain/model/ranking/LoserRankingEntry.kt` — 랭킹 1행. 파생 프로퍼티 없음
- `domain/repository/.../RankingRepository.kt` — `getLoserRanking(onError): Flow<List<LoserRankingEntry>>`
- `remote/model/.../remote/model/ranking/LoserRankingResponse.kt` — envelope + `LoserRankingDto`, **전 필드 기본값**
- `remote/api/.../RankingApi.kt` — `@GET("api/v1/rankings/losers")`
- `remote/mapper/.../LoserRankingResponseMapper.kt` — 순서 보존 1:1
- `remote/datasource/.../RankingRemoteDataSourceImpl.kt` — `@Single(binds=[...])`
- `data/datasource/.../remote/RankingRemoteDataSource.kt`
- `data/repositoryImpl/.../RankingRepositoryImpl.kt` — 얇은 위임체

**공용 승격 (2)** — design.md §4.4
- `core/designsystem/.../designsystem/modifier/Wiggle.kt` — `Modifier.wiggle()` 신설.
  `ChallengeTitle.kt` 인라인 구현 추출, 값(±8f / 1500ms / Reverse) 그대로 승계
- `core/ui/.../ui/components/EmptyStateCard.kt` — `FriendsEmptyState` 승격. **렌더 코드 무변경**

**화면 (10)**
- `feature/ranking/.../contract/LoserRankingItemState.kt` — 표시 파생값 전부(캡션 조립 포함)
- `feature/ranking/.../component/` 8종 — `RankingTopBar` / `PodiumCard` / `PodiumColumn` / `PodiumAvatar` /
  `LoserRankRow` / `RankingEmptyState` / `RankingSectionTitle` / `RankingSubtitle`
- `feature/ranking/.../RankingPreviewFixtures.kt` — **실서버 5행**을 프리뷰 단일 출처로.
  3개 파일에 복붙하면 다음 실측 때 갈라지므로 한 곳에 뒀다

**테스트 (3 + Fake 1)**
- `feature/ranking/src/commonTest/.../contract/LoserRankingItemStateTest.kt` (17)
- `feature/ranking/src/commonTest/.../RankingViewModelTest.kt` (11)
- `feature/ranking/src/commonTest/.../FakeRankingRepository.kt`
- `remote/mapper/src/commonTest/.../LoserRankingResponseMapperTest.kt` (10)

### 변경 (9) + 삭제 (1)

- `feature/ranking/build.gradle.kts` — `compose.materialIconsExtended` + commonTest 3종
- `feature/ranking/.../RankingScreen.kt` · `RankingRoute.kt` · `RankingViewModel.kt` · `contract/RankingState.kt`
  — placeholder/TODO 제거하고 실제 구현
- `remote/api/.../di/ApiModule.kt` — `provideRankingApi` 추가
- `feature/login/.../component/ChallengeTitle.kt` — 인라인 애니메이션 → `Modifier.wiggle()`
- `feature/friends/list/.../FriendsScreen.kt` — `EmptyStateCard` 로 import 교체 (**인자 무변경**)
- `feature/challenge/create/.../FriendPickPlaceholderCard.kt` — 낡은 주석 1줄만 정정 (코드 무변경).
  `internal` 이라 재사용 못 한다는 사유가 승격으로 사라져 그대로 두면 거짓이 된다
- `remote/model/.../LoserRankingResponse.kt` — KDoc 예시 JSON 을 실서버 원문으로 갱신 (2차)
- `feature/ranking/.../contract/LoserRankingItemState.kt` — 조건부 캡션 주석에 실측 근거 추가 (2차)
- `core/ui/.../EmptyStateCard.kt` — `ctaIcon`·`inviteIcon` 파라미터 개방 (2차, design §4.4.1)
- 삭제: `feature/friends/list/.../component/FriendsEmptyState.kt` (`:core:ui` 로 이관)

🔴 **안 건드린 것 (design.md §9 지시)**: `ProfilePlaceholder`(diff 0) · `ChallengeTopBarDefaults.Height`
공용 56dp(diff 0) · `feature/home` 전체(diff 0, `HomeEmptyState` 통합은 별건 백로그).

## 테스트 결과

**계약 `confirmed` + 실서버 원문 픽스처 반영 후 최종 수치.**

| | 결과 |
|---|---|
| **Android 전체** | **460 / 460 passed**, failures 0, errors 0 (baseline 416 → **신규 44**) |
| **iOS (`:feature:ranking` + `:remote:mapper` + `:core:ui`)** | **148 / 148 passed**, failures 0, errors 0 |
| **신규 44건** | **양 플랫폼 전부 통과** (Android 44 / iOS 44) |

- 신규 내역: `LoserRankingItemStateTest` **17** · `RankingViewModelTest` **11** ·
  `LoserRankingResponseMapperTest` **16**(계약 기준 10 + **실서버 원문 6**)
- 모듈별 iOS: `:feature:ranking` 28 · `:remote:mapper` 116 · `:core:ui` 4
- **Android 빌드**: ok (`BUILD SUCCESSFUL in 31s`)
- **iOS 빌드**: ok (`BUILD SUCCESSFUL in 39s`, `linkDebugTestIosSimulatorArm64` 통과)

### 🔴 iOS XML stale 아님 — 실측

| XML (iOS) | tests / failures | timestamp |
|---|---|---|
| `LoserRankingItemStateTest` | 17 / **0** | **14:46:30** |
| `RankingViewModelTest` | 11 / **0** | **14:46:30** |
| `LoserRankingResponseMapperTest` | 16 / **0** | **14:46:40** |

확인 시각이 `14:46:58` 이었으므로 **실행 직후의 파일**이다. 과거 feature 에서 iOS XML stale 오탐이
있었어서 timestamp 를 명시한다.

### ⚠️ iOS 는 **모듈 한정**으로 돌렸다 — 의도적 배치

`./gradlew iosSimulatorArm64Test`(전체 집계 태스크)는 **지금 레포에서 실패한다.** 실측:

```
> Task :core:utils:compileTestKotlinIosSimulatorArm64 FAILED
e: .../core/utils/src/commonTest/.../WireFormatBaselineTest.kt:32:9
   Name contains illegal characters: "()".
```

백로그의 *"3개 모듈 iOS 테스트가 한 번도 돈 적 없다"* 항목이 **여전히 살아 있다**(실측 위반 정확히
22건 — `:remote:datasource` 13 / `:data:repositoryImpl` 8 / `:core:utils` 1). Gradle 이 fail-fast 라
내 모듈에 도달하기 전에 중단된다.

🔴 **그래서 랭킹 테스트를 `:feature:ranking` 과 `:remote:mapper` 에만 두었다. 누락이 아니라 배치 결정이다.**
이 두 모듈은 iOS 테스트가 정상 동작하는 쪽이고(대조: iOS XML 존재 모듈은 `remote/mapper`·`feature/*`·
`core/camera`·`core/push`, 부재 모듈은 위반 3개와 정확히 일치), 모듈 한정 실행으로 양 플랫폼 숫자를 얻었다.

**`:remote:datasource` / `:data:repositoryImpl` 에 랭킹 테스트가 없는 것은 의도다** — 거기 두면
Android 에서만 검증된다. 두 곳의 랭킹 구현은 `record` 체인과 동일한 얇은 위임체라 자체 로직이 없다.
22건 rename 은 별건 백로그 항목이라 이번에 침범하지 않았다.

## Working tree 상태

- **작업 브랜치**: `main` (현재 체크아웃된 것. 새로 만들지 않았다)
- **변경분**: staged/unstaged 그대로 둠. **커밋·푸시·PR 생성 안 함** — 사용자 처리 영역
- 마지막 커밋은 `a776ed2 feat: 챌린지 결과 처리 기능 구현` 그대로
- 규모: **신규 24 · 변경 9 · 삭제 1** (`git status` 실측)

## 미해결 이슈

### 1. ✅ (해소) `totalChallenges` — 계약 `confirmed` + 실측 픽스처로 닫혔다

원래 미해결 1번이었다. 지금은 세 겹으로 닫혀 있다:

- **계약 문면**: `api-contract.md` 가 `confirmed` 이고 `totalChallenges | Int | ❌ non-null |
  row 없으면 0 | 🔴 정렬 키가 아니다 — 표시 분기 전용` 으로 등재. 내 DTO·도메인·매퍼를
  **9필드 필드별로 대조 완료** — 이름·타입·nullable·순서 전부 일치.
- **서버측 고정**: backend 의 `WireShapeContractTest` 가 **9필드 키 세트**를 고정한다. 서버가
  DTO 에서 필드를 지우면 서버 테스트가 먼저 빨개진다.
- **앱측 고정**: 실서버 원문 픽스처에 `totalChallenges == 0` 행이 실려 있고,
  *"키가 없으면 0 으로 읽혀 전원이 기록 없음 캡션으로 보인다"* 테스트도 **남겨 뒀다**(정상 경로와
  누락 경로를 둘 다 덮는다).

🔴 **재계산 금지 규약이 이 필드로 확장된 것도 준수 확인했다** — `totalChallenges` 는 앱에서
**`== 0` 비교에만** 쓰이고 분모로 쓰인 곳이 **0건**이다(grep 실측). `lossRate` 는 문자열 보간
표시에만 쓴다. 서버가 그 정수를 정렬 3차 키로도 쓰므로 앱이 다시 나누면 표시와 정렬이 갈린다.

### 2. ✅ (해소) 실서버 원문 픽스처 반영 완료

backend 가 넘긴 실서버 원문(테스터1 = user 14 시점, 5행)을 `LoserRankingResponseMapperTest` 에
추가했다 — 계약 기준 픽스처는 **지우지 않고 병존**(미지 키 `tier` 등 실원문에 없는 조합을 덮는다).
신규 6건이 이 원문 기반이다.

한 응답이 표시 분기를 전부 덮는다:

| rank | 걸리는 분기 |
|---|---|
| 1 (테스터1) | `isMe` 정확히 1건 + **`currentLossStreak == 0` 인 1위**(연패 절 생략) + "나" 치환이 **포디움에서** 걸림 |
| 2·4 | `currentLossStreak > 0` → 🐷 뱃지 |
| 3 (이우건) | `profileImageUrl` **non-null 실 URL** 파싱 |
| 5 (테스터4) | 🔴 **`totalChallenges == 0`** → `아직 기록 없음` |

🔴 **rank 5 는 픽스처에서 절대 빼면 안 된다.** backend 가 이 실측을 위해 `users` row 만 있고
`user_stats` row 가 없는 계정을 일부러 심었다가 지웠고, **native query 의 `LEFT JOIN` + `COALESCE 0`
폴백이 실제 SQL 에서 탄 유일한 증거**다(슬라이스 테스트가 원리적으로 못 덮는 경로). 파일 KDoc 에 명시.

**재정렬 회귀 방지선도 이 데이터가 만들어 줬다** — rank 2·4 는 패율 **100%** 인데 rank 1 은 **80%** 다.
`losses DESC` 가 1차 키라는 게 실데이터로 증명되므로, 앱이 `lossRate` 로 재정렬하면 반드시 깨지는
단언(`패배율 내림차순이 아니다`)을 넣었다.

### 3. `triggerStateIn` 의 `restart()` 미사용 (나이트)

`RankingViewModel.uiState` 를 `TriggerStateFlow` 로 만들었으나 `restart()` 호출부가 없다.
design.md §3.1 이 *"재시도는 탭 재진입"* 으로 정해 `WhileSubscribed(0)` 재구독이 갱신을 담당하므로
**동작에는 문제 없다.** 당겨서 새로고침이 붙으면 그대로 쓰이는 자리라 두었다. `stateIn` 으로
낮추는 것도 선택지다.

### 4. 프리뷰만 확인, 실기 미확인

Compose `@Preview` 로만 검증했다(정상 6명 / N=3 / N=2 / N=1 / N=0 / 연패 0 인 1위 / 내가 1위 /
긴 닉네임 / 큰 폰트 스케일 / Loading — 10종). 디바이스 실기 확인은 사용자 몫.

### 5. design.md §7 디자이너 확인 대상은 그대로 열려 있다

§7-①(1위 받침대 `fire-gradient/20` 렌더 안 되는 건에 대한 의도 구현), ②("나" 행 강조),
③(2위만 rank 색 강조 빠짐), ⑤(`MilitaryTech` 아이콘 대체), ⑥(참가자 3명 미만 분기),
⑦·⑪(빈 상태·"아직 기록 없음" 문구), ⑩(🐷 의미 통일). 전부 **design.md 기본값대로 구현**했고
디자이너 확인이 오면 바뀔 수 있다.

### 6. 🔴 실데이터에서 처음 드러난 표시 조합 — 디자인 확인 필요

실서버 데이터를 프리뷰에 넣고 나서 보인 것이다. **1위 캡션이 `4패 · 패배율 80%` 인데 바로 아래
2위가 `3패 · 패배율 100%`** 다.

정렬(`losses DESC` 1차)상 **완전히 정상 동작**이고 backend·design·mobile 3자가 합의한 규칙 그대로다.
다만 화면에서는 *"패배 랭킹인데 1위의 패배율이 2위보다 낮다"* 로 읽힌다 — 명단 캡션이 **패배율을
같이 보여주기 때문에** 순위와 어긋나 보이는 숫자가 나란히 놓인다.

가정이 아니라 **개발 DB 로 처음 띄우면 바로 보이는 화면**이다(실서버 rank 1·2 가 그 케이스).

### ✅ 판정: **① 그대로 간다** (2026-08-26 pm-lead)

- **③(정렬 기준을 화면에 밝힌다)은 이미 충족돼 있다** — 헤더 부제 *"패배의 왕좌 — 많이 진 놈이 대장"*
  이 정렬 기준(총 패배 우선)을 사용자 언어로 이미 말하고 있다. 별도 설명 줄을 더할 필요가 없다.
- **②(명단 캡션에서 패배율 제거)는 정본 이탈이다** — Lovable `ranking.tsx:101` 이 캡션에 패배율을
  포함한다. 읽히는 방식이 문제라면 문구가 아니라 디자인이 판단할 사안이다.
- **실화면에서 어떻게 읽히는지는 디자이너 확인 대상으로 등재**됐다(pm-lead → rank-design).

🔴 **재정렬로 "고치면" 안 된다** — 계약 위반이고 서버 정렬 3차 키와 표시가 갈린다.
`서버 순서가 보존되며 패배율 내림차순이 아니다` 단언이 **이 판정의 안전판**이다 —
①로 두는 한, 누군가 "보기 이상하다"는 이유로 앱에서 재정렬하려 하면 그 테스트가 막는다.

## API 계약 대비 구현 차이

**없다.** `confirmed` 계약의 **9필드를 필드별로 대조 완료**했다 — 이름·타입·nullable·선언 순서가
DTO(`LoserRankingDto`)·도메인(`LoserRankingEntry`) 양쪽에서 계약 문면과 일치한다.

`totalChallenges` 는 design.md 가 정본이라 **계약 확정보다 앞서 구현**했었고, 확정된 문면과
대조한 결과 **차이 0**이었다(non-null `Int`, 맨 마지막 필드, row 없으면 0).

### 계약 확정 후 반영한 것 (2026-08-26 2차)

- **실서버 원문 픽스처 6건 추가** (§미해결 2번)
- **DTO KDoc 예시 JSON 갱신** — 확정 전 가짜 데이터(`준혁`/userId 3, `totalChallenges` 누락)라
  실서버 원문 2행(rank 1 / rank 5)으로 교체. 코드가 아니라 문서 문자열이었지만, 낡은 wire 예시는
  다음 사람을 오도한다.
- **조건부 캡션 주석 강화** — *"실서버 1위(테스터1)가 `losses=4, currentLossStreak=0` 이라
  개발 DB 로 처음 띄우면 바로 이 분기를 밟는다"* 를 KDoc 에 추가. 정본에 없는 분기라
  **"일어나지 않는 상황에 대한 방어 코드"로 오해받아 삭제되는 것**을 막는 게 목적이다.
- **`EmptyStateCard` 에 `ctaIcon`·`inviteIcon` 개방** (design.md §4.4.1) — 두 사본이 서로 **반대되는
  것**을 파라미터화해 놨다는 지적을 받았다(`FriendsEmptyState` 는 일러스트 아이콘이 파라미터·CTA
  아이콘이 하드코딩, `FriendPickPlaceholderCard` 는 정반대). 기본값이 기존 하드코딩 값과 같아
  **친구 화면 호출부 인자는 한 글자도 안 바뀌었다**(diff 실측: import·이름 3줄뿐).
- ⚠️ 아이콘 박스 shape 은 **16dp 유지**. Lovable 정본은 20dp 이고 앱 3사본이 16/16/`CircleShape`
  으로 이미 갈려 있으나, 승격의 장점이 *"렌더 무변경"* 이라 이번에 안 맞췄다 — 백로그.

### 🔴 `profileImageUrl` — 되돌릴 것이 없었다

backend 가 실측으로 *"카카오 실계정은 URL 이 들어온다"* 를 알리며 한때 *"이미지 로드 두 갈래를
구현하라"* 고 했다가 **스코프 월권이라며 철회**했고, design 도 같은 결론(§1.2.3.1)에 도달했다.

**앱은 처음부터 이미지 로드를 배선하지 않았다** — `feature/ranking` 내 Coil/`AsyncImage` 사용
**0건**(grep 실측). 되돌릴 작업이 없었다. **키는 받되 그리지 않는다.**

부수로 확인된 사실: 이 레포는 이미 Coil 이 배선돼 있고(`App.kt` `setSingletonImageLoaderFactory`,
`VerificationPhoto.kt` 가 `SubcomposeAsyncImage` 실사용) URL 도 실제로 온다. 그럼에도 안 켜는 이유는
**URL 이 평문 `http://`** 라 Android 는 `cleartextTrafficPermitted=true` 로 통과하지만 **iOS 는 ATS 로
차단**되기 때문이다 — 도메인명(`img1.kakaocdn.net`)이라 "숫자 IP 예외"에 안 걸린다.
**한쪽만 깨지는 실패라 Android 확인으로는 안 잡힌다.** 서버 https 정규화가 선결 조건이고
`ProfilePlaceholder` 가 4개 feature 공용이라 랭킹 단독으로 못 켠다. 별건 백로그.

계약 협의에서 모바일이 관철한 것:
- **`isMe` 채택** — `amIChallenger` 기각 논거가 여기 적용되지 않는 이유를 실패 모드로 구분했다.
  `amIChallenger` 는 두 값이 정반대 시점이라 키 누락 시 승리를 패배로 그리지만, `isMe` 는 `false` 가
  중립·다수값(N행 중 N-1행)이라 키 누락 시 하이라이트가 안 그려질 뿐이다. userId 대조를 기각한 근거는
  `ChallengeDetailViewModel.kt:186` KDoc 의 실측(*"내 userId. 실패하면 null"*).
- **`rank` 는 중복 없는 1..N 순증** — 포디움이 배열 앞 3개를 1/2/3 자리에 꽂는 구조라 공동 순위가 오면
  앱이 동률 표시 규칙을 새로 만들어야 하고, 그게 정렬 규칙의 두 번째 사본이 된다.
- **`lossRate` 서버 계산 정수 non-null** — 앱 재계산 금지(정렬 키와 표시가 갈린다).
- **`myRank` 미포함** — 목록이 같은 응답에 있어 `find { it.isMe }?.rank` 가 조회로 끝난다.

### ⚠️ 협의 중 내가 낸 오류 2건 (자진 기록)

1. *"`isMe` 를 기본값 없는 필수 필드로 받겠다"* 라고 backend 에 말했는데 **레포 관행을 틀리게 말한 것**
   이다. `ActiveChallengeDto`·`RecordData` 는 전 필드에 기본값이 있고(`MissingFieldException` 회피),
   계약 회귀는 wire 픽스처가 잡는 구조다. 즉시 정정했고 결론은 안 바뀌었다.
2. **작성 중이던 design.md 를 다 쓰인 것으로 착각**해 *"`totalChallenges` 불필요, `confirmed` 가라"* 고
   회신했다. 내가 읽은 시점은 44,977 바이트였고 §1.3.3 이 아직 없었다(현재 53,978). §1.3.3 을 보고
   **즉시 철회 메시지를 보내 `confirmed` 를 막고** 추가 요청으로 되돌렸다.
   → 교훈: **작성 중일 수 있는 문서를 근거로 계약을 닫지 않는다.**
