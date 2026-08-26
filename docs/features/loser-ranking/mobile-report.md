# Mobile Report — loser-ranking

- **작성**: 2026-08-26 mobile-dev(rank-mobile)
- **상위 spec**: [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [design.md](./design.md)
- **상태**: 구현 완료 · 🔴 **계약 1건 미확정**(`totalChallenges`) — §미해결 1번

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

### 신규 (23)

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

**테스트 (3 + Fake 1)**
- `feature/ranking/src/commonTest/.../contract/LoserRankingItemStateTest.kt` (17)
- `feature/ranking/src/commonTest/.../RankingViewModelTest.kt` (11)
- `feature/ranking/src/commonTest/.../FakeRankingRepository.kt`
- `remote/mapper/src/commonTest/.../LoserRankingResponseMapperTest.kt` (10)

### 변경 (10)

- `feature/ranking/build.gradle.kts` — `compose.materialIconsExtended` + commonTest 3종
- `feature/ranking/.../RankingScreen.kt` · `RankingRoute.kt` · `RankingViewModel.kt` · `contract/RankingState.kt`
  — placeholder/TODO 제거하고 실제 구현
- `remote/api/.../di/ApiModule.kt` — `provideRankingApi` 추가
- `feature/login/.../component/ChallengeTitle.kt` — 인라인 애니메이션 → `Modifier.wiggle()`
- `feature/friends/list/.../FriendsScreen.kt` — `EmptyStateCard` 로 import 교체 (**인자 무변경**)
- `feature/challenge/create/.../FriendPickPlaceholderCard.kt` — 낡은 주석 1줄만 정정 (코드 무변경)
- 삭제: `feature/friends/list/.../component/FriendsEmptyState.kt` (`:core:ui` 로 이관)

🔴 **안 건드린 것 (design.md §9 지시)**: `ProfilePlaceholder`(diff 0) · `ChallengeTopBarDefaults.Height`
공용 56dp(diff 0) · `feature/home` 전체(diff 0, `HomeEmptyState` 통합은 별건 백로그).

## 테스트 결과

| | 결과 |
|---|---|
| **Android 전체** | **454 / 454 passed**, failures 0, errors 0 (baseline 416 → **신규 38**) |
| **iOS (`:feature:ranking` + `:remote:mapper`)** | **138 / 138 passed**, failures 0, errors 0 |
| **신규 38건** | **양 플랫폼 전부 통과** (Android 38 / iOS 38) |

- 신규 내역: `LoserRankingItemStateTest` 17 · `RankingViewModelTest` 11 · `LoserRankingResponseMapperTest` 10
- **Android 빌드**: ok (`BUILD SUCCESSFUL in 1m 20s`)
- **iOS 빌드**: ok (`BUILD SUCCESSFUL in 46s`, `linkDebugTestIosSimulatorArm64` 통과)

### 🔴 iOS XML stale 아님 — 실측

| XML | tests | timestamp |
|---|---|---|
| `LoserRankingItemStateTest` (iOS) | 17 / 실패 0 | **2026-08-26 14:29:37** |
| `RankingViewModelTest` (iOS) | 11 / 실패 0 | **2026-08-26 14:29:37** |
| `LoserRankingResponseMapperTest` (iOS) | 10 / 실패 0 | **2026-08-26 14:29:50** |

확인 시각이 `14:30:02` 였으므로 **실행 직후의 파일**이다. 과거 feature 에서 iOS XML stale 오탐이
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

## 미해결 이슈

### 1. 🔴 `totalChallenges` 계약 미확정 — 조용한 실패 노출

design.md §1.3.3 이 캡션을 `totalChallenges == 0` → `"아직 기록 없음"` 으로 분기하도록 확정했고
그대로 구현했다. **그런데 이 필드가 아직 계약에 없다.** rank-backend 에 추가 요청을 보냈고
(§8-⑤ 논거 인용) 회신 대기 중이다.

**서버가 이 키를 안 내려주면**: DTO 기본값이 `0` 이라 역직렬화는 **성공한 채로** 전원이 0 이 되고,
명단 캡션이 **전원 "아직 기록 없음"** 이 된다. 25패 78% 인 개돼지왕까지 그렇게 보인다.
예외도 로그도 없다.

- 방어 로직을 넣지 않은 이유: 계약이 협의 중인 필드지 가정이 아니고, backend 가 *"추가는 비파괴적"*
  이라고 확인했다. 대신 **테스트로 박아 뒀다** — `totalChallenges 키가 없으면 0 으로 읽혀 전원이
  기록 없음 캡션으로 보인다` 가 그 위험을 명시적으로 고정한다.
- 확정되면 반영 비용은 **0**이다 (DTO·도메인·매퍼에 이미 필드가 들어가 있다).

### 2. 실서버 원문 픽스처 없음

`LoserRankingResponseMapperTest` 는 **계약 기준 대표 응답**으로 만들었다. backend 가 구현 후 실측
원문을 넘겨주기로 했고, 그때 교체·추가한다(파일 KDoc 에 그 자리를 명시). 요청한 원문 구성 4요소:
친구 여럿 + 나 포함 / `currentLossStreak > 0` / **`currentLossStreak == 0` 인 1위** / `totalChallenges == 0` 유저.

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

## API 계약 대비 구현 차이

**없다** — 확정된 8필드를 그대로 구현했다. 단 위 §미해결 1번의 `totalChallenges` 는
**계약보다 앞서 구현**한 상태다(design.md 가 정본이라 선반영, backend 확정 대기).

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
