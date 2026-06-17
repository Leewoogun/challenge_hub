# Mobile Report — home-feed

- **feature-id**: home-feed
- **작성자**: mobile-dev
- **작성일**: 2026-05-25
- **상태**: ✅ 코드 작업 종료. 백엔드 `GET /api/v1/home` 실연동 / 시각 검증은 사용자/QA 처리 영역.

---

## 구현 요약

home-feed/spec.md + api-contract.md(draft) + design.md(§1~3 + §4 props + §8 강조사항) 기준으로 Domain → Data → Feature → Navigation 전 레이어를 신규 구현.

핵심 결정 사항:
1. **빈 상태 분기는 ViewModel 책임** (design.md §8 #2 권고). `HomeUiState.Success(stats, challenges, emptyType)` 패턴으로 화면 코드는 분기 1줄로 끝남.
2. **시각 타입은 `kotlin.time.Instant`** 사용. Kotlin 2.2.20 부터 `kotlinx.datetime.Instant` 는 `kotlin.time.Instant` 의 typealias 라 stdlib 만으로 충분. (kotlinx-datetime 추가 의존성 회피)
3. **`ChallengeVerificationStatus` 는 designsystem 로컬 enum**. Clean Arch 단방향(designsystem → domain 금지)을 지키기 위해 도메인의 `VerificationStatus` 와는 분리. 호출부(feature)가 1:1 매핑.
4. **ADR-0003 잔여 해소** — 기존 `:feature:home` 의 placeholder ("Cooking" TopBar + "준비 중" 본문) 를 challenge 도메인 본 UI 로 교체. Movie 예제 코드는 점검 결과 이전에 이미 제거되어 별도 삭제 작업 불필요했음.

---

## 사용한 모바일 레포 스킬

- `full-feature/SKILL.md` (절차 참조) — Domain → Data → Feature → Navigation 전 레이어 신규 생성.
- `design-system/SKILL.md` (자동 적용) — `:core:designsystem` 에 `ChallengeCard`, `StatsBar`, `HomeEmptyState` 3개 신규 컴포넌트 추가.
- `test-viewmodel/SKILL.md` — `HomeViewModelTest` 6 케이스 작성.

---

## 변경된 파일

### 신규 — `:domain:model`
- `domain/model/src/commonMain/.../VerificationStatus.kt` — PENDING / VERIFIED / FAILED enum
- `domain/model/src/commonMain/.../UserStats.kt` — 4필드(win/lose/draw/currentStreak) + `isEmpty` 헬퍼 + `Empty` companion
- `domain/model/src/commonMain/.../ActiveChallenge.kt` — 7개 표시 필드 + challengeId. `deadline = kotlin.time.Instant`
- `domain/model/src/commonMain/.../HomeFeed.kt` — `UserStats` + `List<ActiveChallenge>`

### 신규 — `:domain:repository`
- `domain/repository/src/commonMain/.../HomeRepository.kt` — `suspend fun getHome(): HomeResult` 인터페이스 + `HomeResult { Success / Unauthorized / Error }` sealed

### 신규 — `:domain:usecase`
- `domain/usecase/src/commonMain/.../GetHomeFeedUseCase.kt` — `suspend operator fun invoke()` 단일 위임

### 신규 — `:remote:model`
- `remote/model/src/commonMain/.../home/HomeResponse.kt` — `HomeResponse` (BaseResponse 상속) / `HomeData` / `UserStatsDto` / `ActiveChallengeDto` (`deadline: String` ISO-8601) / `VerificationStatusDto`

### 신규 — `:remote:api`
- `remote/api/src/commonMain/.../HomeApi.kt` — Ktorfit `@GET("api/v1/home")` 인터페이스
- **수정** `remote/api/src/commonMain/.../di/ApiModule.kt` — `provideHomeApi(ktorfit)` `@Single` 추가

### 신규 — `:remote:mapper`
- `remote/mapper/src/commonMain/.../HomeResponseMapper.kt` — `HomeResponse.toHomeFeed()` + `deadline` 문자열 → `kotlin.time.Instant` 파싱(`runCatching`, 실패 시 `Instant.DISTANT_PAST` 폴백)

### 신규 — `:data:repositoryImpl`
- `data/repositoryImpl/src/commonMain/.../repository/HomeRepositoryImpl.kt` — `@Single(binds=[HomeRepository::class])` Ktorfit `ApiResult` → `HomeResult` 매핑(401 → Unauthorized, 그 외 실패 → Error)
- **수정** `data/repositoryImpl/src/commonMain/.../di/UseCaseModule.kt` — `provideGetHomeFeedUseCase(HomeRepository)` `@Factory` 추가

### 신규 — `:core:utils`
- `core/utils/src/commonMain/.../datetime/InstantFormat.kt` — `fun Instant.toRelativeKoreanString(now: Instant = Clock.System.now()): String` — "X시간 Y분"/"X분"/"곧 마감"/"마감" 분기. `now` 주입으로 테스트 시 Clock 고정 가능. 파일 단위 `@OptIn(ExperimentalTime::class)`.

### 신규 — `:core:designsystem`
- `core/designsystem/src/commonMain/.../components/challenge/ChallengeVerificationStatus.kt` — designsystem 전용 enum (도메인 미의존)
- `core/designsystem/src/commonMain/.../components/challenge/ChallengeCard.kt` — design.md §4.1 props 명세 그대로. 7개 표시 필드 + onClick + Modifier. 내부에서 `Instant.toRelativeKoreanString()` 호출. status pill 색/아이콘/라벨 3가지(`warning`/`success`/`error` + `Schedule`/`CheckCircle`/`Cancel`). 내기 띠는 `primary 5% bg + 10% border`.
- `core/designsystem/src/commonMain/.../components/challenge/StatsBar.kt` — design.md §4.2. 4분할 Row + 세로 구분선. 톤 분기 컴포넌트 내부 책임(4값 모두 0이면 muted 단일 톤). 연승 셀: value > 0 시 "{N}🔥".
- `core/designsystem/src/commonMain/.../components/challenge/HomeEmptyState.kt` — design.md §4.3. `HomeEmptyStateType` enum(FIRST_USER/NO_ACTIVE_CHALLENGE) + 2개 onClick. 64.dp Flame 일러스트 자리 + 헤드라인(bold16) + 서브라인(medium12 muted) + 가로 2버튼(`OutlinedButton`/`Button` weight(1f) 52.dp).
- `core/designsystem/src/commonMain/.../components/challenge/HomeEmptyStateType.kt` — enum (1줄짜리)

### 신규 — `:feature:home`
- `feature/home/src/commonMain/.../contract/HomeUiState.kt` — sealed `Loading / Success(stats, challenges, emptyType: HomeEmptyType) / Error(message)` + `HomeEmptyType { NONE / FIRST_USER / NO_ACTIVE_CHALLENGE }` enum
- `feature/home/src/commonMain/.../contract/HomeUiEffect.kt` — sealed `NavigateToLogin / ShowMessage(message)`
- `feature/home/src/commonTest/.../FakeHomeRepository.kt` — 미리 `result` 세팅 + `callCount` 노출
- `feature/home/src/commonTest/.../HomeViewModelTest.kt` — 6 케이스

### 수정 — `:feature:home`
- `feature/home/src/commonMain/.../HomeViewModel.kt` — placeholder 완전 교체. `@KoinViewModel(GetHomeFeedUseCase)`. init { refresh() }. `refresh()` 가 매번 Loading → API → Success/Error/effect 분기.
- `feature/home/src/commonMain/.../HomeRoute.kt` — placeholder 완전 교체. `koinViewModel()` + `collectAsStateWithLifecycle` + `LaunchedEffect { uiEffect.collect { ... } }`. 6개 콜백(retry/bell/fab/challenge/addFriend/createChallenge) 모두 `LocalNavigateAction` 으로 처리.
- `feature/home/src/commonMain/.../HomeScreen.kt` — design.md §1~3 그대로. ChallengeScaffold(statusBarColor=surface) + HomeTopBar + LazyColumn(StatsBar + 섹션 타이틀 + (카드 리스트 | HomeEmptyState)) + FAB.
- `feature/home/src/commonMain/.../component/HomeTopBar.kt` — placeholder ("Cooking" 텍스트) 완전 교체. Flame + "맹세" + Bell(미확인 dot) + `surface.copy(alpha=0.95f)` 배경.
- `feature/home/build.gradle.kts` — `compose.materialIconsExtended` + `kotlin.test`/`coroutines.test`/`turbine` 추가

### 수정 — `:core:navigation`
- `core/navigation/src/commonMain/.../Route.kt` — 3개 신규 Route sealed interface 추가:
  - `ChallengeDetailRoute.Main(challengeId: Long)` — `@Serializable data class`
  - `ChallengeCreateRoute.Main` — `@Serializable data object`
  - `NotificationsRoute.Main` — `@Serializable data object`
  - `routeSerializersModule` 에 3개 subclass 등록

### 수정 — `:feature:main`
- `feature/main/src/commonMain/.../MainScreen.kt` — `entryProvider` 에 3개 stub NavEntry 추가 (모두 `PlaceholderScreen` 으로 진입)
- `MainScreen` 의 BottomBar 가시 조건은 변경 없음 — 챌린지 상세/생성/알림은 BottomBar 가시 유지(스택 push 형태).

### 수정 — `:core:utils` 의 `build.gradle.kts`
- kotlinx-datetime 의존 추가하지 않음. stdlib 의 `kotlin.time.Clock` / `kotlin.time.Instant` (ExperimentalTime) 만 사용.

### 수정 — `:core:designsystem/build.gradle.kts`
- `compose.materialIconsExtended` (commonMain) — ChallengeCard / HomeEmptyState 가 직접 import 하기 위함
- `projects.core.utils` (commonMain) — `Instant.toRelativeKoreanString` 헬퍼 사용. utils → designsystem 의존 부재 확인(단방향).

### 수정 — `:domain:model/build.gradle.kts`
- kotlinx-datetime 의존 제거(stdlib `kotlin.time.Instant` 사용으로 불필요).

### 수정 — `:remote:mapper/build.gradle.kts`
- kotlinx-datetime 의존 추가하지 않음(동일 사유).

---

## 추가/변경 의존성 요약

| 모듈 | 추가 | 비고 |
|------|------|------|
| `:feature:home` | `compose.materialIconsExtended`, `kotlin.test`, `kotlinx.coroutines.test`, `turbine` | bottom-navigation feature 와 동일 패턴 |
| `:core:designsystem` | `compose.materialIconsExtended`, `projects.core.utils` | 신규 컴포넌트들이 직접 사용 |
| `:domain:model` | (없음) | kotlinx-datetime 도입하지 않음 — `kotlin.time.Instant` 사용 |
| `:remote:mapper` | (없음) | 동일 |
| `:core:utils` | (없음) | 동일 |

`kotlin.time.Instant`/`Clock` 은 Kotlin 2.2 부터 stdlib 포함이지만 `@ExperimentalTime` 마커 필요 — 사용처 파일마다 `@file:OptIn(ExperimentalTime::class)`.

---

## 빌드 결과 (모듈별)

| 모듈 | 명령 | 결과 |
|------|------|------|
| `:domain:model` | `:build` | ✅ BUILD SUCCESSFUL |
| `:domain:repository` | `:build` | ✅ BUILD SUCCESSFUL |
| `:domain:usecase` | `:build` | ✅ BUILD SUCCESSFUL |
| `:remote:model` | `:build` | ✅ BUILD SUCCESSFUL |
| `:remote:api` | `:build` | ✅ BUILD SUCCESSFUL |
| `:remote:mapper` | `:build` | ✅ BUILD SUCCESSFUL |
| `:data:repositoryImpl` | `:build` | ✅ BUILD SUCCESSFUL |
| `:core:utils` | `:build` | ✅ BUILD SUCCESSFUL |
| `:core:designsystem` | `:build` | ✅ BUILD SUCCESSFUL |
| `:core:navigation` | `:build` | ✅ BUILD SUCCESSFUL |
| `:feature:home` | `:compileDebugKotlinAndroid` + `:compileCommonMainKotlinMetadata` + `:iosSimulatorArm64Test` | ✅ BUILD SUCCESSFUL (detekt 는 프로젝트 공통 detekt.yml 부재로 스킵 — 본 feature 도입 이슈 아님) |
| `:feature:main` | `:build` | ✅ BUILD SUCCESSFUL |
| `:composeApp` | `:compileDebugKotlinAndroid` + `:compileCommonMainKotlinMetadata` + `:linkDebugFrameworkIosSimulatorArm64` | ✅ BUILD SUCCESSFUL |

detekt 태스크는 프로젝트 루트의 `config/detekt/detekt.yml` 파일 미존재로 모든 모듈에서 실패. 본 feature 의 코드 이슈는 아니며, 빌드 명령에서 `-x detekt` 로 제외해야 정상 통과(기존 hub backlog 후보).

---

## 테스트 결과

### `HomeViewModelTest` (commonTest)

| 케이스 | Android JVM (testDebugUnitTest) | iOS SimulatorArm64 (iosSimulatorArm64Test) |
|---|---|---|
| 초기 상태는 Loading 이며 init 진입과 동시에 1회 조회 | ✅ | ✅ |
| 신규 사용자 - 전적 0 챌린지 0 → Success(FIRST_USER) | ✅ | ✅ |
| 진행 중 챌린지 있는 응답 → Success(NONE) | ✅ | ✅ |
| Error 응답 → Error 상태 + ShowMessage UiEffect | ✅ | ✅ |
| Unauthorized 응답 → NavigateToLogin UiEffect (Loading 유지) | ✅ | ✅ |
| 기존 사용자 챌린지 0개 → Success(NO_ACTIVE_CHALLENGE) | ✅ | ✅ |
| **총** | **6/6 passed** | **6/6 passed** |

> 참고: 사용자가 요청한 4상태(로딩/성공/빈상태/에러)를 빈상태 2분기까지 분해해 6 케이스로 확장. 모두 통과.

### 회귀

- `feature:login:testDebugUnitTest` — **LoginViewModelTest 4/4 passed** (회귀 0)
- 다른 feature(splash/friends/ranking/mypage)는 단위 테스트가 스켈레톤만 있어 검증 대상에서 자동 제외.

### iOS 시뮬레이터 시각 검증

- Compose UI 자동 검증 불가. 사용자가 Android 에뮬레이터 / iOS Simulator 진입해 직접 확인 필요(현재 백엔드 미연동이므로 실제 진입은 mock/stub 응답 또는 backend feature 완료 이후).

---

## ADR-0003 잔여 확인

- `:feature:home` 의 사전 상태: `HomeViewModel` 은 빈 `ViewModel` 상속(파라미터 없음), `HomeRoute` 는 ChallengeScaffold + "준비 중" 텍스트, `HomeTopBar` 는 "Cooking" 텍스트. **Movie 예제 코드 잔재는 점검 결과 이미 0건** (이전 작업에서 정리된 것으로 보임).
- 본 feature 로 placeholder 잔재 완전 제거 + 챌린지 도메인 본 UI 로 교체 완료 → **ADR-0003 의 `:feature:home` 라인은 해소**.

repos.json `mobile.blockers` 의 다음 항목은 본 작업으로 해소 가능:
- `⚠️ :feature:home이 여전히 Movie 예제 — challenge 도메인으로 교체 필요 (Sprint 1~2).` → ✅ 교체 완료

---

## 미해결 이슈 / design.md §7 ⚠️ 항목 — 모바일 영향 정리

| # | 항목 | 본 feature 구현 | 결정 필요 |
|---|------|---------------|---------|
| 1 | 빈 상태(FIRST_USER) 에서 FAB 노출 여부 | **노출 유지** (design.md 본안 그대로) | pm-lead 결정 후 변경 시 1줄 수정 |
| 2 | NO_ACTIVE_CHALLENGE 에서 CTA 2버튼 vs 1버튼 | **2버튼 유지** | 디자이너 결정 후 props 변형 |
| 3 | 빈 상태 일러스트 자산 | **Flame 32.dp + primary 10% 배경 임시** | 디자이너 일러스트 합류 시 교체 |
| 4 | `Swords` lucide → `SportsKabaddi` 매핑 | 채택 — 코드상 `Icons.Filled.SportsKabaddi` 사용 | **시각 검토 필요** (Material 아이콘이 디자인 의도와 시각적으로 다를 수 있음 — 디자이너 확인) |
| 5 | `text-[11px]` → `medium12` 근사 | 채택 — `medium12` 슬롯 사용 | 후속 feature 에서 사용처 누적 시 `medium11` 슬롯 신설 재논의 |
| 6 | "무" 셀 색을 plain `onBackground` 로 둠 | 채택 그대로 | — |
| 7 | StatsBar 톤 분기 컴포넌트 책임 | 채택 — `win + lose + draw + currentStreak == 0` 일 때 4셀 muted | — |

추가 / 모바일 자체:
- **시계 의존 헬퍼**: `Instant.toRelativeKoreanString(now)` 은 `now` 매개변수 주입 가능하지만 현재 ChallengeCard 내부에서 기본값 호출. 시간 흐름에 따라 화면 텍스트가 자동 갱신되지 않음(매 composition 마다 재계산되긴 함). 분 단위 자동 갱신(`LaunchedEffect + delay(60s)`) 은 backlog 후보.
- **Material Icons Extended deprecation**: bottom-navigation feature 와 동일 — 1.7.3 핀 사용 시 경고. Material Symbols 마이그레이션 ADR 후보(기존 backlog 항목과 합쳐 추적).
- **pulse 애니메이션 미적용**: design.md §1 의 FAB pulse-fire 애니메이션은 1차 단순 처리(static FAB) — task 지시 그대로. 후속 작업 후보.
- **detekt 설정 누락**: `config/detekt/detekt.yml` 부재로 모든 모듈의 `:detekt` 태스크 실패. 본 feature 도입 이슈 아님. backlog 등재.

---

## backend-dev 에 API 계약 변경 요청 사항

**없음.** api-contract.md(draft) 의 응답 shape 을 그대로 사용해 DTO/매퍼/Repository 까지 빌드 성공. 백엔드 구현 결과 응답 shape 이 contract 와 달라지면 본 mobile-report 에 추가 기록 + 중재 라운드 요청 예정.

**참고 - 모바일 구현 결정으로 백엔드와 정합 확인 권장**:
1. `deadline` 필드 직렬화: 모바일 DTO 는 `String` 으로 받아 매퍼에서 `Instant.parse(value)` → 실패 시 `Instant.DISTANT_PAST` 폴백. 백엔드 응답이 정확한 ISO-8601 UTC(`2026-05-26T00:00:00Z`) 여야 함. (kotlinx.serialization 의 InstantIso8601Serializer 를 도입할 수도 있지만, DTO 가 String 이면 디시리얼라이즈 실패가 카드 1개를 0건으로 만드는 게 아니라 `DISTANT_PAST` 카드를 만들므로 방어적이 더 안전하다고 판단).
2. `code=401` 의 의미: 본 구현은 `401 → HomeResult.Unauthorized → NavigateToLogin` 로 처리. 토큰 만료 외에 권한 부족 등 다른 401 케이스가 있으면 분리 필요.
3. `activeChallenges` 의 빈 배열은 `null` 이 아닌 `[]` 로 응답(api-contract.md 명시) — DTO 기본값 `emptyList()` 로 방어.

---

## Working tree 상태

- 작업 브랜치: 사용자 체크아웃 브랜치 (mobile-dev 가 새 브랜치를 만들지 않음 — 메모리 규칙).
- 변경분: staged/unstaged 그대로 둠. 커밋 / 푸시 / PR 생성 안 함 — 사용자 처리 영역.
- 생성 파일 수: 18 (소스) + 1 (테스트 fake) + 1 (테스트 클래스) = 20 신규 파일.
- 수정 파일 수: 9 (모듈 빌드 스크립트 5, 코드 4).
