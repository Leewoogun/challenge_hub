# Mobile Report — challenge-create

- **feature-id**: challenge-create
- **작성**: 2026-07-28 by mobile-dev
- **상태**: implemented (working tree, **커밋 안 함**)
- **선행 입력**: [spec.md](./spec.md), [api-contract.md](./api-contract.md) (`confirmed`), [design.md](./design.md)
- **검증**: Android 유닛 **88/88 passed, 0 failed** / Android·KMP common 빌드 **BUILD SUCCESSFUL** / iOS framework link **BUILD SUCCESSFUL**
- **기준 문서**: design.md **v3** (v1 스냅샷으로 착수했다가 v2/v3 반영분을 사후 보정 — 아래 "design.md 개정 대응" 참조)

## 구현 요약

챌린지를 **생성하는 경로**와 **받아서 응답하는 경로**를 모바일에 열었다. 이전까지 홈은 `IN_PROGRESS` 챌린지를 읽어 그리기만 했고 생성 진입점이 없어 어떤 사용자도 빈 상태를 벗어날 수 없었다.

Domain → Remote/Data → Feature 전 레이어를 신규 구현하고, 기존 `:feature:home`을 확장했다. 계약(`confirmed`) 5 endpoint를 모두 구현했다.

세 가지가 이번 작업의 실질적 난점이었고 각각 대응했다:

1. **`combine` 이 홈 전체를 Loading 에 가두는 구조** — 프로젝트 표준 에러 패턴은 실패 시 `onError`만 부르고 **emit 하지 않는다.** `GetHomeDataUseCase`가 `combine`이라, 받은 도전장 소스를 그냥 4번째로 추가하면 **받은 도전장 조회 실패가 홈 화면 전체를 백지로 만든다.** 받은 도전장만 `.onEmpty { emit(emptyList()) }`로 격리했다(`userInfo`의 기존 선례 동일). 전적/진행중/유저정보는 의도적으로 그대로 뒀다 — 그 3개의 "실패 시 Loading 유지"는 기존 테스트 2건이 고정하고 있는 동작이다.
2. **`HomeViewModel` 에 refresh 메커니즘이 아예 없었다** — 콜드 Flow를 `stateIn` 한 게 전부라 수락/거절 후 목록을 다시 당길 방법이 없었다. `FriendsViewModel`의 `refreshTrigger + onStart + flatMapLatest` 패턴을 이식했다(신규 패턴 발명 없음).
3. **`message` 가 곧 UI 텍스트** — 모바일 에러 채널이 `code`를 버리고 `message`만 전달한다. 계약 협의에서 이 사실을 계약서에 명문화시키고 서버 문구를 확정 문구로 고정시켰다.

## 사용한 모바일 레포 스킬

- `/domain` — `:domain:model` / `:domain:repository` / `:domain:usecase` 신규 (T-M1)
- `/data-remote` — DTO / Ktorfit / mapper / RepositoryImpl / Koin 등록 (T-M2)
- `/feature` + `design-system` — 위저드 화면·컴포넌트, 홈 확장 (T-M4, T-M5)
- `/modify-feature` — `:feature:home` 기존 자산 확장 (T-M5)
- `/test-viewmodel` — `ChallengeCreateViewModelTest`, `HomeViewModelTest` 확장

## 화면 흐름

```
홈 FAB ──▶ 챌린지 생성 위저드
            step0 대결 상대 선택 (GET /friends)
              └─ 탭 ──▶ step1 미션·내기·마감
                        └─ "챌린지 걸기" ──▶ POST /challenges ──▶ pop ──▶ 홈
                        (TopBar ← 로 step0 복귀, 선택 유지)

홈 진입 ──▶ 받은 도전장 섹션 (GET /challenges/received)
              ├─ "수락" ──▶ 미션 입력 다이얼로그 ──▶ POST /{id}/accept
              │              └─ 성공 ──▶ 목록 재조회(받은+진행중 동시) + "챌린지가 시작됐어요"
              └─ "거절" ──▶ POST /{id}/reject ──▶ 목록 재조회
```

수락/거절이 **어떤 이유로 실패하든** 스낵바 + 받은 도전장 목록 재조회다(계약 §공통 규약 — code 분기 없음).

## 변경된 파일

### 신규 (41)

| 모듈 | 파일 |
|---|---|
| `:domain:model` | `challenge/DeadlineType.kt`, `challenge/ReceivedChallenge.kt`, `challenge/ChallengeCreateInput.kt` |
| `:domain:repository` | `ChallengeRepository.kt` |
| `:domain:usecase` | `CreateChallengeUseCase.kt` |
| `:remote:model` | `challenge/` 하위 7건 — `ChallengeCreateBody`(+`DeadlineTypeDto`), `ChallengeCreateResponse`, `ReceivedChallengesResponse`, `AcceptChallengeBody`, `AcceptChallengeResponse`, `RejectChallengeResponse`, `CancelChallengeResponse` |
| `:remote:api` | `ChallengeApi.kt` (5 endpoint) |
| `:remote:mapper` | `ChallengeMappers.kt` |
| `:data:repositoryImpl` | `repository/ChallengeRepositoryImpl.kt`, `commonTest/ChallengeRepositoryImplTest.kt` |
| `:core:ui` | `components/ProfilePlaceholder.kt` (승격 — 아래 참조) |
| `:core:utils` | `datetime/KstDeadline.kt` (KST 마감 시각 표시 헬퍼), `commonTest/datetime/KstDeadlineTest.kt` |
| `:feature:challenge:create` | `component/` 9건 (`FriendPickItem`, `DeadlineSelector`, `MissionInputField`, `SubmitButton`, `WizardProgressBar`, `ChallengeCreateTopBar`, `StepHeader`, `FriendPickStep`, `MissionInputStep`, `FriendPickPlaceholderCard`, `ChallengeCreateLoading`), `contract/FriendPickItemState.kt` |
| `:feature:challenge:create` (test) | `ChallengeCreateViewModelTest.kt`, `FakeFriendsRepository.kt`, `FakeChallengeRepository.kt` |
| `:feature:home` | `component/ReceivedChallengeCard.kt`, `component/ReceivedChallengesSection.kt`, `component/AcceptChallengeDialog.kt`, `component/BetStrip.kt`, `component/MissionInputField.kt`, `contract/ReceivedChallengeItemState.kt` |
| `:feature:home` (test) | `FakeChallengeRepository.kt` |

### 수정 (16)

| 파일 | 변경 |
|---|---|
| `:domain:model/HomeData.kt` | `receivedChallenges` 추가 |
| `:domain:usecase/GetHomeDataUseCase.kt` | `challengeRepository` 4번째 파라미터 + `combine` 4소스. 받은 도전장만 `.onEmpty { emit(emptyList()) }` |
| `:data:repositoryImpl/di/UseCaseModule.kt` | `provideCreateChallengeUseCase` 추가 + `provideGetHomeDataUseCase` 파라미터 추가 |
| `:remote:api/di/ApiModule.kt` | `provideChallengeApi` 추가 |
| `:feature:challenge:create/build.gradle.kts` | `materialIconsExtended` + commonTest 의존 |
| `:core:utils/build.gradle.kts` | commonTest 소스셋 신설 (`libs.kotlin.test`) — `KstDeadlineTest` 용 |
| `:feature:challenge:create/component/DeadlineSelector.kt` | 48.dp 1줄 → **60.dp 2줄 + 실제 마감 시각 부기** (design.md v2 §4.2) |
| `:feature:challenge:create/component/MissionInputStep.kt` | `DeadlineSelector` 에 힌트 2건 전달 |
| `:feature:challenge:create` 스텁 5파일 | `Route`/`Screen`/`ViewModel`/`contract` 2건 — "준비 중" 스텁 → 2-step 위저드 실물 |
| `:feature:home/HomeViewModel.kt` | `challengeRepository` 주입 + refreshTrigger + 수락/거절 갈래 |
| `:feature:home/contract/HomeUiState.kt` | `receivedChallenges`/`acceptTarget`/`acceptMission`/`isSubmittingAccept`/`inFlightIds` + `emptyType` 보정 |
| `:feature:home/HomeScreen.kt` | 받은 도전장 섹션 삽입 + 다이얼로그 + Preview 갱신·추가 |
| `:feature:home/HomeRoute.kt` | 콜백 5건 배선 |
| `:feature:home/component/ChallengeCard.kt` | 내기 띠를 `BetStrip`으로 추출(중복 제거) |
| `:feature:home/commonTest/HomeViewModelTest.kt` | 생성자 갱신 + 구독 추가 + 신규 11건 |
| `:feature:friends:list/component/FriendListItem.kt`, `FriendRequestCard.kt` | `ProfilePlaceholder` import 전환 |

### 삭제 (2)
`:feature:home` / `:feature:challenge:create` 의 로컬 `ProfilePlaceholder.kt` (→ `:core:ui` 승격)

## 테스트 결과

### Android 유닛 — **88/88 passed, 0 failed** (전건 XML 실측)

| 테스트 클래스 | 결과 | 성격 | XML timestamp |
|---|---|---|---|
| `ChallengeRepositoryImplTest` | **12/12** | 신규 | 2026-07-28T05:56:04Z |
| `ChallengeCreateViewModelTest` | **15/15** | 신규 | 2026-07-28T06:13:24Z |
| `HomeViewModelTest` | **21/21** (기존 10 + 신규 11) | 확장 | 2026-07-28T06:13:20Z |
| `KstDeadlineTest` | **9/9** | 신규 | 2026-07-28T06:11:38Z |
| `UserInfoRepositoryImplTest` | **5/5** | 회귀 0 | 2026-07-28T05:56:04Z |
| `FriendsViewModelTest` | **10/10** | 회귀 0 | 2026-07-28T05:56:22Z |
| `FriendsSearchViewModelTest` | **12/12** | 회귀 0 | 2026-07-28T05:56:12Z |
| `LoginViewModelTest` | **4/4** | 회귀 0 | 2026-07-28T05:56:14Z |

> **timestamp 가 두 그룹으로 갈리는 이유**: 05:56 그룹은 그 시점의 전체 실행분이고, 이후 변경(`:core:utils` 의 `KstDeadline` 신설 + `:feature:challenge:create` 의 `DeadlineSelector` 개정)이 해당 모듈들의 입력을 바꾸지 않아 Gradle 이 `UP-TO-DATE` 로 재실행을 건너뛴 것이다. **05:56 실행 자체가 그 모듈들에 영향을 주는 마지막 변경(`ProfilePlaceholder` 승격) 이후**이므로 결과는 유효하다. stale 아님.

### 🔴 수용 기준 — `HomeViewModel` 기존 10건 회귀 0

**충족.** 기존 10개 케이스의 **이름과 단언을 한 줄도 바꾸지 않았다.** 변경은 두 가지뿐이다:

1. `createViewModel()` 에 4번째 fake + `challengeRepository` 주입 (생성자 변경 대응)
2. **각 테스트에 `uiState` 구독 1줄 추가** — `uiState`가 `SharingStarted.WhileSubscribed(0)`이라 구독자가 없으면 `refreshTrigger.onStart{}.flatMapLatest{}` 파이프라인이 시작되지 않는다. `FriendsViewModelTest`의 `subscribeUiState` 헬퍼를 그대로 복제했다.

> 2번은 **단언 약화가 아니라 강화**다. 구독이 없으면 `record 실패 → Loading 유지` 같은 케이스가 "파이프라인이 안 돌아서 Loading"으로 공짜 통과한다. 구독을 넣어야 "파이프라인은 돌았는데 `combine`이 값을 못 내서 Loading"이라는 **원래 의도**가 실제로 검증된다.

### 빌드

| 대상 | 명령 | 결과 |
|---|---|---|
| Android | `:composeApp:compileDebugKotlinAndroid` (+ 전 모듈 전이) | ✅ BUILD SUCCESSFUL |
| KMP common | `:composeApp:compileCommonMainKotlinMetadata` | ✅ BUILD SUCCESSFUL |
| iOS framework | `:composeApp:linkDebugFrameworkIosSimulatorArm64` | ✅ BUILD SUCCESSFUL |

- `detekt`는 `config/detekt/detekt.yml` 부재로 전 모듈 실패 — home-feed 때부터의 기존 이슈이며 본 feature 도입 문제가 아니다. `-x detekt`로 제외했다. (backlog 기존 항목)
- **iOS 유닛 테스트(`iosSimulatorArm64Test`)는 미실행.** friends 2차와 동일하게 Android 유닛 + iOS 링크까지가 검증 게이트다.

## #7 준비 — iOS 로컬 네트워크 접근 (`Info.plist`)

`iosApp/iosApp/Info.plist`에 **`NSLocalNetworkUsageDescription` 1건 추가**. 문구는 권한 팝업에 그대로 노출된다: `"같은 네트워크의 개발 서버에 연결해 챌린지 정보를 주고받습니다."`

### ATS 키는 넣지 않았다 (조사 결과 no-op)

당초 지시는 ATS 예외(`NSAllowsLocalNetworking`) 추가였으나, **ATS는 이 요청을 막지 않는다.** Apple DTS(Quinn) 공식 답변:

> `NSAllowsLocalNetworking` ... **has no effect on IP address loads** (`http://192.168.1.39/`). **On iOS 10 and later such loads are always allowed.**

`http://172.30.1.63:8080/`은 숫자 IP라 ATS 대상이 아니다. `NSAllowsLocalNetworking` / `NSExceptionDomains` / `NSAllowsArbitraryLoads` 모두 **no-op**이며, 넣으면 "ATS를 처리했다"는 잘못된 인상만 남는다. (base URL이 `mac.local` 같은 **호스트명**이 되면 그때 의미가 생긴다.)

**실제 관문은 iOS 14+ Local Network Privacy(LNP)** — 사설 대역 IP로의 unicast 연결에 로컬 네트워크 권한이 필요하고, 키가 없으면 권한 안내를 못 띄워 연결이 실패한다(`Local network prohibited`). 카카오 SDK는 공인 HTTPS 도메인만 써서 지금까지 걸리지 않았고, 이번이 첫 로컬 네트워크 접근이다.

### 검증

| 항목 | 결과 |
|---|---|
| `plutil -lint` | OK |
| `xcodebuild -sdk iphonesimulator` (iPhone 16 Pro) | **`** BUILD SUCCEEDED **`** |
| 패키징된 `Challenge.app/Info.plist` 키 존재 | OK |
| 같은 plist에 ATS 키 부재 | OK (의도대로) |
| 카카오 `$(KAKAO_NATIVE_APP_KEY)` 변수 치환 | 정상 |
| 기존 키 5종 보존 | 전부 OK |

### ⚠️ 런타임 미검증 — 실기기 확인 필요

- 근거는 **Apple DTS 답변**이고 런타임 동작은 확인하지 못했다. `nscurl --ats-diagnostics`는 `http://`를 `https://`로 강제 승격해 답이 안 되고, Info.plist를 embed한 **macOS 바이너리/`.app` 실험은 ATS 키가 전혀 없는 대조군까지 통과해 무효**였다(macOS는 iOS처럼 ATS를 강제하지 않는다). 이 실험 결과는 근거로 쓰지 않았다.
- **iOS 시뮬레이터는 LNP를 강제하지 않는다.** 시뮬레이터 성공이 실기기 성공을 증명하지 않는다.
- 실기기에서는 첫 네트워크 호출 시 권한 팝업이 뜨고 **"허용"을 눌러야** 한다. Apple 인정 버그(r.131764908): 한 번 거부하면 재설치·허용해도 **기기 재시작 전까지 실패**가 캐시된다(iOS 18.6 beta 수정).
- 시뮬레이터만 쓸 거면 `local.properties`의 iOS 값을 `http://localhost:8080/`(buildkonfig 기본값)로 두는 편이 마찰이 가장 적다.

Android는 무변경 — `network_security_config.xml`의 `cleartextTrafficPermitted="true"`로 이미 통과한다.

### 출처 (재조사 방지)

- [ATS and local IP addresses — Apple Developer Forums](https://developer.apple.com/forums/thread/66417) — Quinn의 `NSAllowsLocalNetworking` 정의와 **"has no effect on IP address loads / on iOS 10 and later such loads are always allowed"** 원문
- ["Local network prohibited" 2025 edition — Apple Developer Forums](https://developer.apple.com/forums/thread/788044) — LNP 요구 조건 + 권한 거부 캐싱 버그(r.131764908)

> **결론 한 줄**: 이 앱의 로컬 서버 연결에서 **ATS는 무관하고 LNP가 전부다.** ATS 키를 추가하려는 시도가 다시 나오면 위 첫 번째 링크를 먼저 보라.

## Working tree 상태

- **작업 브랜치: `main`** (체크아웃돼 있던 브랜치. 새로 만들지 않음)
- 신규 41 + 수정 16 + 삭제 2, **새 커밋 0건**
- staged/unstaged 그대로 둠 — 커밋·푸시·PR 생성 안 함(사용자 처리 영역)

## API 계약 대비 구현 차이

**없음.** `confirmed` 계약의 5 endpoint를 요청/응답 shape 그대로 구현했다.

### ⚠️ `cancelChallenge` 는 **의도적으로 미사용 상태**다 (죽은 코드 아님)

`DELETE /challenges/{id}`는 **`:remote:api` / `:data:repositoryImpl` / `:domain:repository` 배관까지만 만들고 UseCase·ViewModel·UI 호출부를 만들지 않았다.** pm-lead 승인 조건 그대로다.

- **이유**: 오픈이슈 5가 **옵션 C**(보낸 도전장 조회 API 미도입)로 확정돼, 챌린저가 자기 PENDING 챌린지의 `challengeId`를 얻을 조회 경로가 없다. 호출부를 만들어도 도달할 수 없다.
- **지우지 마라.** `:remote:api`가 계약의 5 endpoint를 그대로 미러링하는 편이 일관되고, 후속 feature가 보낸 도전장 목록 UI만 붙이면 이 배관이 그대로 살아난다.
- `ChallengeRepository.createChallenge`의 `onSuccess`가 `challengeId`를 넘기도록 해 둔 것도 같은 맥락이다(생성 직후 언두의 유일한 handle).
- `ChallengeRepositoryImplTest`가 이 메서드를 성공/실패 2건으로 이미 덮고 있어 그대로 뒀다. 미사용 코드에 테스트를 **추가로** 붙이지는 않았다.

## design.md 개정 대응 (v1 스냅샷 착수 → v3 보정)

착수 시점에 읽은 design.md가 **편집 중 스냅샷**이었다. §0(문서 앞부분)은 v2였지만 §3 이후가 v1인 상태로 읽혀, 그 차이를 "문서 내부 모순"으로 판단하고 design-bridge에 정정 요청을 보낸 뒤 **v2/v3 방향으로 자체 판단해 구현했다.** 이후 파일을 다시 읽어 대조한 결과:

| # | 항목 | 내 판단 | v3 실제 | 결과 |
|---|---|---|---|---|
| 1 | 수락 UI | **다이얼로그** (시트 선례 0건 + CMP iOS IME + 입력 1개) | 다이얼로그 (v2에서 변경) | ✅ **일치** |
| 2 | `" 남음"` 접미사 | **붙이지 않음** (`"곧 마감 남음"` 방지) | 접미사 금지 (v2 정정) | ✅ **일치** |
| 3 | 705 전용 확인 다이얼로그 | **만들지 않음** (에러 채널이 code를 버림) | `ChallengeErrorDialog` v3에서 폐기 | ✅ **일치** |
| 4 | `DeadlineSelector` | v1대로 48.dp 1줄로 구현 | **60.dp 2줄 + 실제 마감 시각 부기** (v2 §4.2) | ❌ **누락 → 사후 보정 완료** |

4번이 실제 누락이었고 별도 작업으로 보정했다(`kstDeadlineHintText` 신설 + 컴포넌트 2줄화 + ViewModel 1회 계산 + 테스트 10건). 1~3번은 결과적으로 v3와 같은 결론이라 재작업이 없었다.

**교훈**: 다른 에이전트가 편집 중인 문서를 읽으면 일부만 갱신된 상태를 볼 수 있다. 모순이 보이면 "문서 오류"로 단정하지 말고 재-Read 후 대조하는 편이 안전하다.

### 남은 실제 차이 1건

| design.md | 구현 | 근거 |
|---|---|---|
| §2.4 "거절은 낙관적 갱신 ⭕ (friends 2차 정책 승계)" | **낙관적 갱신 안 함**, 성공 시 `reload()` | **실제 `FriendsViewModel.rejectRequest`는 낙관적 갱신을 하지 않는다** — `onSuccess = ::reload`가 전부다. design.md가 선례를 잘못 인용했다. 코드 선례를 따랐고 pm-lead에 보고했다 |

기타 사소한 차이:
- **CTA 아이콘 18.dp → 16.dp** — 공용 `IconTextButton`이 아이콘 크기를 16.dp로 고정하고 있다. friends 2차에서 이미 backlog로 등재된 항목(`IconTextButton iconSize 파라미터화`)이라 그대로 뒀다.
- **위저드 progress 2칸** (design.md §1.1 지시대로. Lovable 3칸은 step2가 범위 밖이라 도달 불가 칸이 생긴다)
- **`DeadlineSelector` 시그니처에 힌트 파라미터 2개 추가** — design.md §4.2 시그니처는 4개 파라미터지만, §8 #14가 "ViewModel 진입 시 1회 계산"을 요구하고 프로젝트 규칙이 "Composable에서 포맷팅 금지"라 컴포넌트가 힌트를 직접 만들 수 없다. `todayHintText` / `tomorrowHintText`를 파라미터로 받아 ViewModel이 공급한다.

### ⚠️ `kotlinx-datetime` 은 도입하지 않았다 (design.md §4.2 코드 예시와 다름)

design.md §4.2의 마감 시각 계산 예시는 `kotlinx.datetime`의 `TimeZone.of("Asia/Seoul")` / `toLocalDateTime` / `DateTimeUnit`을 쓴다. **그대로 시도했다가 컴파일이 깨졌다.**

- `libs.versions.toml`은 `kotlinx-datetime = "0.6.2"`를 적어두고 있으나 실제 해석 버전은 **0.7.1**이다(`strictly 0.7.1`로 강제됨). 0.7.x에서 `kotlinx.datetime.Instant` ↔ `kotlin.time.Instant` 관계가 바뀌어 `Instant.toLocalDateTime(TimeZone)` 확장이 매칭되지 않는다.
- **KST는 고정 UTC+9, DST 없음**이라 산술로 정확히 계산된다. 의존성을 추가하는 대신 stdlib만으로 구현했다 — home-feed의 "kotlinx-datetime 회피, stdlib `kotlin.time`만 사용" 결정도 그대로 유지된다.
- 구현: `floorDiv`(음수 epoch 대응) + **Howard Hinnant `civil_from_days`**(public domain, 검증된 알고리즘). `KstDeadlineTest` **9건**으로 못박았다 — KST 날짜 경계(`14:59:59Z` vs `15:00:00Z`), 월말·연말 넘김, **윤년(2028-02-28 +1 → 2/29)**, 평년(2027-02-28 +1 → 3/1), 1970 이전(절삭 나눗셈이면 틀리는 케이스).
- `libs.versions.toml`의 `kotlinx-datetime` 카탈로그 항목은 이제 **참조 모듈이 0개**다. 정리는 pm-lead 판단에 맡긴다.

## 미해결 이슈 / 후속

1. **시스템 백 버튼으로 step1 → step0 복귀 미구현** — 공용 `PlatformBackHandler`가 `:feature:main`에 expect/actual로 갇혀 있어 `:feature:challenge:create`에서 쓸 수 없다. 현재는 TopBar 뒤로가기만 단계를 전환하고, 시스템 백은 위저드 전체를 pop 한다. `PlatformBackHandler`를 `:core:ui`로 승격하면 해결된다 — **backlog 후보.**
2. **`SearchProfilePlaceholder` 4번째 사본** — `:feature:friends:search`의 `FriendSearchItem.kt`에 크기(44.dp)만 다른 동일 구현이 남아 있다. 이번에 `ProfilePlaceholder`에 `size` 파라미터를 넣었으므로 시각 변화 없이 흡수 가능하지만, **완료된 feature 영역이고 이번 feature가 만든 중복이 아니라 손대지 않았다.** backlog 후보.
3. **iOS 유닛 테스트 미실행** — Android 유닛 + iOS 링크까지가 검증 게이트. `:feature:home:iosSimulatorArm64Test` / `:feature:challenge:create:iosSimulatorArm64Test` 별도 실행 필요.
4. **실기기 시각 검증 미수행** — Compose UI 자동 검증 불가. 특히 **수락 다이얼로그의 iOS IME 동작**은 실기 확인이 필요하다(다이얼로그를 택한 이유가 시트의 IME 리스크였던 만큼, 다이얼로그 쪽도 확인은 받아야 한다).
5. **원격 이미지 로더 부재** — `challengerProfileImageUrl` / `profileImageUrl`은 시그니처로만 받고 닉네임 이니셜 placeholder로 렌더한다. friends 2차부터의 기존 backlog.
6. **백엔드 실연동 미검증** — 본 리포트는 모바일 단위 검증까지다. 실제 서버 연동은 태스크 #7. 백엔드도 통합 테스트 21건이 Docker 미가용으로 skip 상태라, **양측 모두 end-to-end 미검증**이다.
7. **base URL은 이미 challenge 서버 기준** — 2026-07-28 `repos.json` 갱신으로 확인됐다(TMDB 흔적 0건). `remote/network/build.gradle.kts`가 buildkonfig로 Android 기본 `http://10.0.2.2:8080/` / iOS 기본 `http://localhost:8080/`를 분리하고 `local.properties`의 `challenge_api_base_url_android` / `_ios`로 오버라이드한다. ⚠️ 다만 현재 `local.properties` 값이 **LAN IP 하드코딩**이라 네트워크가 바뀌면 재설정이 필요하다 — #7 실연동 시 확인할 것.

## 계약 협의 기여 (mobile-dev → 계약서 반영된 항목)

| 항목 | 근거 |
|---|---|
| 700/705 분기 불가 명문화 + 모바일 동작 "실패 시 항상 재조회" 확정 | `suspendOnFailureWithErrorHandling(onError: (String) -> Unit)`이 `CustomError.code`를 버림. 5개 Repository 공통 표준(`faae2cd`)이라 변경은 범위 밖 |
| 모든 에러 `message`를 사용자 노출 확정 문구화 | `message`가 가공 없이 스낵바에 뜬다 |
| `권한이 없어요` → `내가 받은/보낸 도전장이 아니에요` | 사용자 입장에서 맥락 없음 |
| 중복 메시지 2종 분기 (backend-dev 제안 채택) | 역방향 PENDING인데 "진행 중인 챌린지가 있어요"라고 하면 홈 진행중 목록이 비어 있어 버그로 오인 |
| `challengeDate` 평문 ISO date 문자열 강제 + `@JsonFormat` 명시 | 모바일 kotlinx-datetime 미도입 → `String`으로 수신. Jackson 기본 직렬화는 `[2026,7,28]` 배열 |
| `deadline`/`createdAt` `Z` suffix 고정 + 초 절삭 | 파싱 실패 시 `Instant.DISTANT_PAST` 폴백이라 **조용히 "마감된 카드"가 된다** |
| DELETE에 `data.challengeId` 추가 | friends `CancelFriendRequestResponse`와 shape 통일 |
| 옵션 (B) 기각 | 방향별 표시 필드가 달라, 전 필드 기본값 방어 패턴 탓에 잘못된 방향 필드를 읽어도 조용히 통과 |
