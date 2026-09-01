# Mobile Report — notification-list

- **작성**: 2026-09-01 mobile-dev (noti-mobile)
- **계약**: [api-contract.md](./api-contract.md) `confirmed` (파일로 확인 후 착수)
- **디자인**: [design.md](./design.md) 개정본(2026-09-01 13:41 — §4.5·§4.5.2·§6.3 반영)

## 구현 요약

**알림이 오는데 볼 곳이 없던 상태를 메웠다.** `MainScreen.kt:228` 의 `PlaceholderScreen("알림")` 이
실화면으로 교체됐고, 홈 벨의 붉은 점이 처음으로 켜진다.

1. **목적지 규칙을 한 벌로 승격** — 푸시와 목록이 같은 `toRoute()` 를 탄다 (T-M2)
2. **과거 경과 시간 포맷터 신설** — 기존 함수는 방향이 반대라 쓸 수 없었다 (T-M3)
3. **알림 목록 화면** — 커서 무한 스크롤 + 빈 상태 + 실패 상태 (T-M1)
4. **홈 벨 뱃지 점등** — `unreadCount > 0` (T-M4)
5. **테스트** (T-M5)

## 사용한 모바일 레포 스킬

- `full-feature` 계열 절차(`domain` → `data-remote` → `feature` → `navigation`)를 단계별로 적용.
  코드 편집은 전부 `cd challenge-app && claude -p` 로 위임해 레포 자체 하네스(SessionStart 훅 ·
  skills 자동 발견 · 누적 메모리)가 발화하도록 했다. 빌드·테스트는 본체에서 background 실행.
- `generate-feature.sh notification` 으로 모듈 생성 후 채움.

## 변경된 파일 (34 경로)

### 신규 모듈 `:feature:notification` (14 파일)
`NotificationRoute` / `NotificationScreen` / `NotificationViewModel` / `NotificationPreviewFixtures` /
`contract/{NotificationState, NotificationEffect}` / `component/{NotificationCard, NotificationEmptyState,
NotificationListFooter, NotificationTypeVisual}` / `di/NotificationModule` + 테스트 3.

### 데이터 계층 (신규)
`remote/model/notification/{NotificationListResponse, UnreadCountResponse}` · `remote/api/NotificationApi` ·
`remote/mapper/NotificationResponseMapper` · `remote/datasource/NotificationRemoteDataSourceImpl` ·
`data/datasource/remote/NotificationRemoteDataSource` · `data/repository/NotificationRepositoryImpl` ·
`domain/repository/NotificationRepository` · `domain/model/notification/{Notification, NotificationPage}`

### 공유 규칙 승격
- `core/push/PushEventRoute.kt` **(신규)** — `toRoute()` 를 `:feature:main` private 에서 승격·public 화
- `core/push/PushEvent.kt` — `of(type, referenceId)` 신설, `from(Map)` 이 위임. `TYPE_*` 4개 public 화
- `core/push/build.gradle.kts` — `:core:navigation` + navigation3 의존 추가

### 경과 시간
- `core/utils/datetime/ElapsedTimeFormat.kt` **(신규)** — `toElapsedKoreanString`
- `core/utils/.../WireFormatBaselineTest.kt` — 함수명 1건 rename (아래 §부수 효과)

### 홈 뱃지
`domain/model/HomeData.kt` · `domain/usecase/GetHomeDataUseCase.kt` · `data/di/UseCaseModule.kt` ·
`feature/home/{HomeScreen, HomeViewModel, contract/HomeUiState}` + 테스트 2

### 배선
`feature/main/{MainScreen, MainViewModel, build.gradle.kts}` · `composeApp/{App.kt, build.gradle.kts}` ·
`remote/api/di/ApiModule.kt` · `core/navigation/Route.kt`(KDoc) · `settings.gradle.kts`

## 테스트 결과

`BUILD SUCCESSFUL` · XML timestamp 로 stale 배제 확인.

| 모듈 | Android | iOS |
|---|---|---|
| `:feature:notification` **(신규)** | **23/23** | **23/23** |
| `:remote:model` | **21/21** | **21/21** |
| `:core:push` | **24/24** | **24/24** |
| `:feature:home` | **27/27** | **27/27** |
| `:feature:main` | **17/17** | **17/17** |
| `:core:utils` | **50/50** | **50/50** |
| **합계** | **162/162** | **162/162** |

`failures=0 errors=0`. `:composeApp:compileDebugKotlinAndroid` 통과.
이번 세션 신규 약 **57건**.

- **Android 빌드**: ok
- **iOS 빌드**: ok (`iosSimulatorArm64`)
- ⚠️ **실기 검증 없음** — 시뮬레이터/단위 테스트까지다.

### 검증이 약한 지점 (숨기지 않고 적는다)

**기준 시각 공유가 간접 검증이다.** *"쪽이 추가돼도 전 항목이 같은 `now` 를 쓴다"* 를 직접 단언하지
못했다 — `now` 는 `NotificationItemState` 의 private 이고 `nowKst()` 에 주입점이 없다. 쪽을 건너
같은 `createdAt` 이 같은 `elapsedText` 를 내는 것으로 관측했다. 직접 판별하려면 ViewModel 에 clock
주입점을 여는 별도 작업이 필요하다.

## Working tree 상태

- **작업 브랜치**: `main` (현재 체크아웃된 브랜치. 새로 만들지 않았다)
- **변경분**: unstaged 그대로. **커밋·푸시·PR 생성 없음** — 사용자 처리 영역
- 34 경로 (수정 19 · 신규 15)

## 주요 판단

### 1. `toRoute()` 승격 — 사본 금지의 실질

`toRoute()` 는 `MainViewModel.kt:106` 의 **파일 private** 이었고 모듈이 `:feature:main` 이다.
`:feature:main` 이 모든 feature 를 의존하므로 `:feature:notification` 이 역으로 의존할 수 없다 —
**구조가 사본을 강제하고 있었다.** 규칙을 지우는 게 아니라 **사본이 필요 없게** 만들었다.

- 방향은 `:core:push` → `:core:navigation`. 순환 없음. 반대 방향은 기각했다 — 모든 feature 모듈이
  `:core:navigation` 을 받으므로 거기에 푸시 인프라를 매달면 전 모듈이 끌려온다.
- `PushEvent.of(type, referenceId)` 신설 + `from(Map)` 위임으로 **타입 어휘와 "모르는 타입 → null"
  규칙이 한 곳에만** 있다. 수용 기준 *"모르는 타입이 와도 목록이 깨지지 않는다"* 가 이 함수 하나로
  떨어진다 — null → 목적지 없음 → 비탭.
- **기존 `MainViewModelTest` 4건이 무수정 통과**한 것이 동작 보존의 증거다.

### 2. `toElapsedKoreanString` 신설 — 가지 순서가 이 함수의 전부다

기존 `toRelativeKoreanString` 은 **재사용 불가**다. 마감까지 **남은** 시간을 세는 미래 카운트다운이라
지난 시각에 `"마감"` 을 반환하고(`RelativeTimeFormat.kt:27` `if (remaining <= 0.seconds)`), 알림
`createdAt` 은 전부 과거라 **목록 전 행이 "마감" 으로 찍힌다.** 오버로드로 만들지 않고 별도 이름을
썼다 — 방향이 반대인 두 함수가 같은 이름이면 호출부에서 어느 쪽인지 안 보인다(design §3.4).

**5가지를 순서대로 평가한다**: ①<1분(음수 포함) `"방금 전"` ②<60분 `"{N}분 전"` ③<24시간
`"{N}시간 전"` ④달력일 차 1 `"어제"` ⑤그 외 `"{M}월 {d}일"`.

🔴 **③이 ④보다 먼저인 것이 핵심이다.** `"어제"` 는 **달력 단어**고 `"N시간 전"` 은 **산술 단어**라
한 축으로 계산하면 반드시 거짓이 난다:

- 시간 가지를 달력일로 제한하면 → 어제 23:00 을 오늘 01:00 에 보며 `"어제"` (**정보 손실**)
- `"어제"` 를 24~48시간으로 잡으면 → 그저께 23:00 을 오늘 01:00 에 `"어제"` (**거짓** — 달력상 그저께)

**순서를 지키는 것만으로는 부족해서 계산 축 자체를 분리했다** — 경과는 `toInstant(KST)` 차(산술),
어제 판정은 `date.daysUntil(date)`(달력). 절차를 구조로 바꾼 것이라 다음 사람이 순서를 건드려도
두 축이 섞이지 않는다.

**반례 2개를 테스트로 고정**했다(잘못 구현했을 때만 값이 갈리는 지점이다):
어제 23:00 → 오늘 01:00 = `"2시간 전"` / 그저께 23:00 → 오늘 01:00 = `"8월 3일"`.
음수 경과 흡수도 고정 — `createdAt` 은 서버가, `now` 는 기기가 만들어 두 시계가 어긋나는 것은
분산 시스템의 상수다(기존 함수도 같은 자리를 `"마감"` 으로 흡수한다). 흡수 안 하면 `"-3분 전"` 이 나온다.

### 3. 🔴 미지 타입 폴백의 근거 — 잘못 적었다가 고쳤다

**폴백이 필요한 이유는 서버가 원문을 보장해서가 아니다.**

서버 `NotificationEntity.toDomain()` 은 enum **밖** 문자열을 `CHALLENGE_REQUEST` 로 강등하며
**그 동작은 지금도 살아 있다**(우회 시도가 있었으나 도메인 `Notification.type` 이 enum 이라 실행
불가로 철회 — [backlog #140](../../backlog.md)).

진짜 근거는 이것이다: 서버 `NotificationType` enum **8종 중 발송은 4종**이고, 남은
`RESULT`·`TAUNT`·`REMIND`·`FRIEND_REQUEST` 는 **이미 enum 안이라 강등을 거치지 않고 원문 그대로
round-trip** 한다. 그 타입의 발송이 열리는 날 구버전 앱을 막아 주는 것은 이 폴백뿐이다.

🔴 **강등이 나중에 고쳐지더라도 이 폴백을 같이 걷어내지 마라.** 강등은 폴백의 근거가 아니라 폴백을
*일부 구간에서 무력화하던 쪽*이고, 고쳐지면 폴백이 닿는 범위가 **오히려 넓어진다.**

⚠️ **경위**: 나는 pm 지시가 있었다는 사실에서 "수행됐다"로 건너뛰어 backend 에게 *"우회로 바꾼 것까지
포함해서"* 라고 적었고, **그 잘못된 근거가 `NotificationTypeVisual.kt` 폴백 KDoc 에 박혔다.** backend
가 메시지를 정정했고, pm-lead 의 *"볼 수 없는 자리에 같은 종류가 더 있는지는 별개 질문"* 지적으로
코드를 전수 확인해 찾아 고쳤다(추가 0건). PM 문서에는 번지지 않았다.

### 4. 타입 리터럴 0건 — 보장 방식

`feature/notification` 안에 알림 타입 문자열 리터럴이 **0건**이다. 아이콘·색 매핑과 목적지 매핑이
전부 `PushEvent.TYPE_*` 상수를 참조한다.

⚠️ **스켈레톤 1차에서 이 사본이 실제로 났다** — `NotificationTypeVisual.kt` 하단에 같은 문자열 4개가
따로 선언됐다. 사본을 경계하는 feature 인데 내 손에서 났다. `PushEvent` 의 상수를 public 으로 올려
참조하게 바꿔 걷어냈다(T-M2 와 같은 형태 — 사본을 지우는 게 아니라 **사본이 필요 없게** 만든다).

**보장 방식**: *"사본이 0건이다"* 를 검증하면 소스를 읽는 테스트가 되어 이상해진다. 대신
🔴 **`PushEvent.TYPE_*` 4개의 값이 서버 wire 문자열과 같은지를 리터럴로 단언**한다
(`PushEventTest`, 4건). **사본이 없으니 이 한 벌만 맞으면 아이콘·색·목적지가 전부 맞는다.**
상수가 조용히 바뀌면 화면은 폴백으로 떨어질 뿐 아무것도 실패하지 않는 자리라 여기서 잡는다.
단언은 상수끼리가 아니라 **리터럴 문자열로** 한다 — 상수끼리 비교하면 값이 틀려도 통과한다.

### 5. 커서를 앱이 만들지 않는다

`nextCursor` 를 그대로 되돌려 보낸다. ViewModel 에 커서 변수가 하나뿐이고 대입 지점이 서버 응답 2곳
+ `retry()` 의 null 리셋뿐 — `items.last().notificationId` 같은 계산식이 코드에 없다.

**테스트가 이걸 실제로 잡는다**: 픽스처의 `nextCursor`(42·31)를 직전 쪽 마지막 항목 id(7·5)와
**일부러 다르게** 심어서, 앱이 커서를 계산하면 `[null, 7, 5]` 가 되어 단언이 깨진다.

### 6. 읽음 처리 — 진입 1회

`markAllAsRead()` 는 `private` 이고 **호출부가 `init` 한 줄뿐**이라 `loadMore()` 경로에서 도달 불가다.
서버 §8 실측(*`GET /notifications` 이 읽음 처리를 하지 않는다* · 멱등 · 타 사용자 미영향)에 기대어
앱에 가드를 두지 않았다. 실패해도 목록을 막지 않는다 — 뱃지가 안 꺼질 뿐이다.

**뱃지는 서버가 준 `unreadCount` 하나만 본다.** *"read-all 을 불렀으니 0"* 이라는 규칙을 앱에 두지
않았다(계약 §4.3 요구).

### 7. 홈 뱃지 — 고친 곳은 **한 곳뿐이다**

`GetHomeDataUseCase` 의 5번째 `combine` 소스로 붙이고 **`.onEmpty { emit(0) }`** 으로 흘린다 —
뱃지 조회 실패가 홈 전체를 Loading 에 가두면 안 된다(받은 도전장 선례와 같은 등급).
**전용 엔드포인트라서 이 격리가 가능하다** — `/challenges/active` 에 필드로 얹혔으면 뱃지 실패가
홈 필수 데이터 실패가 된다.

🔴 **`HomeScreen.kt:61` 만 바꿨다. `:125` 는 `false` 로 뒀다** — 거긴 `HomeLoadingScreen` 이고
파라미터가 콜백 둘뿐이라 데이터가 없다. 아직 모르는 시점에 점을 켜면 값을 지어내는 것이고, 응답이
0 이면 깜빡 켜졌다 꺼진다. design 이 이 지적을 받아 **§4.5.2 를 신설**했다(뱃지는 모를 때 켜지지
않고, 알고 난 뒤엔 늦게 꺼지지 않는다).

**§4.5.1(돌아온 홈에 점 없을 것)은 기존 구조로 충족된다** — `HomeViewModel` 이
`SharingStarted.WhileSubscribed(0)` 이라 목록으로 나가면 구독이 끊기고 돌아오면 upstream 이 재시작해
`unread-count` 를 다시 부른다. 신호 발행·공유 상태를 새로 만들지 않았고, **구조에 기댄 결론이라
테스트로 고정**했다(이름에 `WhileSubscribed` 를 넣지 않았다 — 구현 세부로 읽히면 지워진다).

### 8. 매퍼가 행을 버리는 유일한 경우

**모르는 `type` 은 절대 안 버린다.** 버리는 건 `createdAt` 파싱 실패뿐이다 — 열린 집합이 아니라
wire 포맷 위반(ADR-0010)이고 카드가 그리는 두 값 중 하나라 그릴 자리가 정해지지 않는다.
보관함 `ChallengeHistoryResponseMapper.kt:37-39` 의 판단을 승계했다.

그 아래 계층은 이미 안전하다 — `WireLocalDateTimeSerializer` 가 파싱 실패를 예외가 아니라 null 로
흡수해서 **시간 문자열 하나가 응답 전체 디코딩을 깨뜨리지 않는다.**

## 부수 효과 — `:core:utils` iOS 테스트가 처음 돌았다

design §8.4 가 경과 포맷터를 `:core:utils` 에 두라고 못박았는데, 그 모듈은 **백틱 함수명 위반으로
iOS 테스트가 컴파일조차 안 되던** 3모듈 중 하나였다. 회피가 불가능해 고쳤다.

🔴 **비용은 함수명 1개였다.** `WireFormatBaselineTest.kt:32` 의 `옛 방식(Instant 차)` 하나가 모듈
전체를 막고 있었다(`e: ... Name contains illegal characters: "()"`). 로직·단언 무변경.

결과: `iosSimulatorArm64Test` 디렉터리가 **처음 생겼고** 50/50 통과. 그중 **35건은 여태 Android
에서만 돌던 기존 테스트**다.

⚠️ **백로그 숫자는 틀리지 않았다.** 내가 *"백로그가 `:core:utils` 를 위반 35건으로 셌다"* 고 정정
요청했으나 **반려됐고 그게 맞다** — 백로그는 22(rename 비용)와 89(손실 커버리지)를 이미 나눠
적고 있었고, 내 측정(14·8·1=23)은 22를 **확증**했다. 요약을 근거로 문서를 반박한 내 실수다.
남은 두 모듈은 `:remote:datasource` 14건 · `:data:repositoryImpl` 8건.

## 🔵 `PlaceholderScreen` 소비처 0건

`MainScreen.kt:228` 교체로 **앱에 placeholder 화면이 하나도 남지 않았다.** 이 feature 가 *"기획서 §4
IA 의 진입 경로가 빈 화면으로 끝난다"* 를 해소하러 시작했는데, 그 완결이다. 컴포넌트 자체는
`:core:ui` 에 남겼다(삭제는 범위 밖 — pm-lead 백로그 정리 묶음).

## 미해결 이슈

1. **실기 검증 없음** — 시뮬레이터·단위 테스트까지. 특히 무한 스크롤 트리거(마지막 항목 도달)와
   뱃지 점등은 실제 스크롤·화면 전환에서 확인해야 한다.
2. ⚠️ **뱃지 위치 육안 검증 대기** — 정본은 버튼 기준 6px, 구현은 10dp. 출시된 화면이라 이번에
   안 고쳤다(design §4.5). **점이 켜진 실물을 처음 보게 되므로** 그때 어색하면 판단한다.
3. **기준 시각 공유가 간접 검증** — 위 §검증이 약한 지점.
4. **`:remote:datasource`(14) · `:data:repositoryImpl`(8) 백틱 위반 잔존** — iOS 테스트 54건이 아직
   Android 에서만 돈다. 이번 범위 밖.
5. **서버 강등이 살아 있다** — enum 밖 문자열이 `CHALLENGE_REQUEST` 로 오분류된다(오늘 도달 경로
   없음). backend 미해결 1번 · [backlog #140](../../backlog.md).
6. **`"민수과"` 조사 결함** — `CHALLENGE_REQUEST` 문구가 받침 없는 닉네임에서 어긋난다.
   🔴 **앱에서 고치지 않았다** — 서버 박제값이라 고치면 푸시와 목록이 갈린다. 서버
   `NotificationMessages` 한 곳이 고칠 자리이고 design §10-② 확인 대상이다.

## API 계약 대비 구현 차이 — **0건**

`NotificationDto` 필드가 계약 §1 필드 표와 **정확히 일치**한다(`notificationId` · `type` · `body` ·
`referenceId` · `createdAt`). `title`·`isRead` 부재도 반영돼 있다.

🔵 **DTO 를 backend 의 예시 JSON 이 아니라 계약 파일의 필드 표에서 만든 것**이 진행 중 `title` 제거를
자동으로 흡수했다. 예시는 작성 시점 스냅샷이고 필드 표는 계약 본문이라, shape 이 바뀌면 표는
고쳐지지만 남의 메시지에 붙은 예시는 안 고쳐진다.

**계약 §8 실측에 기대어 앱에서 방어하지 않은 것**: `GET` 이 읽음 처리를 하지 않음(20번) ·
`read-all` 멱등(18번) · 타 사용자 미영향(17번) · 없는 커서가 에러 아님 · `referenceId: null` 도 키가
실림. 서버가 이 정도로 고정해 주면 앱에 조건 분기가 안 생긴다.
