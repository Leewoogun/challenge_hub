# Mobile Report — mypage

- **작성**: 2026-08-26 mypage-mobile · 🔴 **후속 개정 2026-08-28 archive-month-mobile** (아래 §후속 개정)
- **상위**: [spec.md](./spec.md) · [api-contract.md](./api-contract.md) (§1 `negotiating`, §2·§3 `confirmed`) ·
  [design.md](./design.md) · [change-log.md](./change-log.md)

---

# 🔴 후속 개정 — 계약서 보관함 월 이동 (2026-08-28)

1차의 **"전체 최신순 + 월 섹션 헤더"** 를 폐기하고 **월 단위 조회 + 월 이동 UI** 로 바꾸는 작업.
사용자 확정: 월 1칸씩 순차 이동, **빈 달도 건너뛰지 않는다**, 첫 진입은 항상 이번 달, 미래 달 없음.

## 진행 상태

| 태스크 | 상태 |
|---|---|
| 월 이동 경계 규칙 (`ArchiveMonthCursor`) | ✅ 완료·검증 |
| 월 이동 바 / 빈 달 화면 컴포넌트 | ✅ 완료·검증 |
| wire (`?month=` · 응답 신규 필드 2개 · 매퍼 · `yyyy-MM` 직렬화기) | ✅ 완료·검증 |
| 화면 골격 재구성 (`ArchiveScreen` · 상태 reshape) | ✅ 완료·검증 |
| ViewModel 월 전환 파이프라인 | ✅ 완료·검증 |
| 테스트 | ✅ 아래 표 (`failures=0`) |

⚠️ 계약 §1 이 `negotiating` 인 동안에는 **wire 를 착수하지 않고** 상태관리·화면 골격만 진행했다.
계약 v3 확정(내 회신으로 마감) 후에 배선했다.

## 🔴 계약 협의 — 내 원안 2건을 철회했고, 1건은 아직 반대 중이다

### 철회 — 앱이 기기 시계로 "이번 달" 을 만들면 안 된다

내 초안은 `?month=` 를 **required** 로 하고 앱이 `nowKst()` 로 이번 달을 계산해 보내는 것이었다.
design §2.1.2 가 이를 기각했고 **그쪽이 맞다**:

> 🔴 **기기 타임존이 KST 가 아니면 상한이 서버와 한 달 어긋난다.** ADR-0010 이 프로젝트 전체를
> KST 로 고정했지만 **사용자 기기 시계는 그 규약 밖**이다. 하필 어긋나는 순간이 월말·월초 자정
> 근처고, 증상이 **`>` 가 잠긴 채 이번 달 기록이 안 보이는** 형태다.

→ `month` 는 **optional**(미지정 = 서버 KST 이번 달)이고, 응답의 `month` **에코**가 곧 상한이다.
backend 가 같은 결론에 `DeadlineType`/`KstDeadlineCalculator` 선례를 근거로 독립 도달했다.
**결과적으로 앱은 이 화면에서 시계를 한 번도 읽지 않는다.** 초안이 요구했던 `nowKst()` 호출은 사라졌다.

에코는 두 번째 일도 한다 — **연타로 겹친 요청 중 늦게 온 옛 응답을 버리는 판별자**다.

### 🔴 관철됨 — `hasPrevious`/`hasNext` boolean 을 절대값으로 뒤집었다 (계약 v2 → v3)

계약 v2 가 경계를 boolean 2개로 내렸다. **절대값 `firstArchivedMonth: String?` 로 바꿔 달라고
요청했고, 이건 구현 쪽에서 실제로 깨지는 순서가 있어서 제기한 것이다.**
design(§2.1.2)이 같은 결론에 독립적으로 도달해 있었고, **backend 가 v3 에서 채택했다**
(boolean 2개 삭제). 아래는 그 반례다.

전제 2개가 모두 확정 사항이다 — ① 빈 달을 건너뛰지 않으므로 **연타가 정상 사용**이다
② design §2.5.4.3-① 이 *"월 라벨은 탭 즉시 바뀌고 **화살표는 계속 눌린다**"* 를 요구한다
(응답마다 입력을 잠그면 *"빈 달을 하나씩 지나간다"* 가 왕복 지연만큼 느려져 사실상 불가능해진다).

하한이 `2026-03` 인 사용자:

```
① 4월 표시 중 (hasPrevious=true)
② `<` 탭 → 라벨 3월. 3월의 hasPrevious 는 아직 모른다 → 잠글 수 없으니 true 로 둘 수밖에 없다
③ 응답 전에 `<` 또 탭 → 2월. 🔴 하한 아래로 걸어 들어갔다
```

🔴 **boolean 은 하한에 도착해야 하한을 알려주는데, 연타에서는 그게 한 탭 늦다.** 계약서에는 벽이
있지만 손이 빠르면 통과한다 — 그리고 그 벽을 세운 목적이 backend 자신의 문면으로
*"확정적으로 빈 달의 사막으로 걸어 들어가지 않게 한다"* 였다.

**위쪽은 에러까지 난다.** 이번 달 직전에서 `>` 를 두 번 빠르게 누르면 미래 달 요청이 나가고
계약상 `code 700` 이 온다 — **정상 조작이 오류 화면을 만든다.**

절대값이면 앱이 **아무 달에서나 왕복 0회로** 두 화살표를 확정하므로 두 방향 모두 사라진다.
빈 상태 2종 구분(`firstArchivedMonth == null` ⟺ 기록 전무)도 3필드 조합보다 오조합 여지가 없다.
⚠️ **앱에서 우회 불가능한 항목이었다** — 모르는 값을 앱이 만들어낼 수 없다.

backend 가 v3 에서 자신의 초안을 정정하며 남긴 정식화가 내 것보다 낫다 — 불리언은 *"신호가 더
적은 것"* 이 아니라 **절대값의 손실 있는 투영**이고, 절대값 하나만 내리면 경쟁하는 신호도 안 생긴다.
(내가 처음에 제시했던 `earliestMonth` 별도 필드 추가안은 design 이 기각했다 — `firstArchivedMonth`
가 곧 그 값이라 필드를 둘로 만들 이유가 없다. 옳다.)

### 확정된 계약 v3 (§1)

```
GET /api/v1/challenges/history            → 이번 달 (파라미터 생략)
GET /api/v1/challenges/history?month=2026-05
```
```json
"data": { "month": "2026-08", "firstArchivedMonth": "2026-03", "histories": [ ...7개 필드... ] }
```
- `month`: non-null 에코. 🔴 **파라미터 없이 부른 첫 응답의 에코가 곧 상한(이번 달)** 이고, 동시에
  **stale 응답 폐기의 판별자**다. 한 필드가 두 일을 한다
- `firstArchivedMonth`: nullable 절대값. 🔴 **`null` 은 결측이 아니라 "종료 챌린지가 0건"** 이다.
  이 값 하나가 (a) 이전 이동 가능 여부 (b) 빈 달 vs 기록 전무 화면 선택을 **둘 다** 결정한다
- 🔴 **`null` 이어도 키는 항상 실린다**(backend 실측, 서버 테스트로 고정). 전역 `NON_NULL` 이 켜지면
  키가 조용히 사라지고 앱은 **기록 전무로 오판**하는데 목록은 멀쩡히 `[]` 라 다른 단언이 못 잡는다
- 카드 7필드·`challengeDate` 축·`EXPIRED` 제외·`myResult` 뒤집기 **전부 무변경**

## 🔴 1차 코드 중 무엇을 지우는가 (pm-lead 태스크 3)

| 1차 코드 | 판정 | 근거 |
|---|---|---|
| `toArchiveMonths()` 의 **클라 월 그룹핑** | 🔴 **삭제** | 화면에 달이 하나뿐이라 그룹이 하나다. 더 결정적으로 **1차는 월 라벨을 `histories.first().challengeDate` 에서 뽑았는데, 빈 달에는 뽑아낼 데이터가 없다** — 라벨의 출처가 데이터에서 **선택된 달**로 옮겨가야 한다 |
| 같은 함수의 **방어적 `sortedByDescending`** | 🔴 **삭제** | 1차에 이걸 넣은 사유는 *"순서가 어긋나면 같은 월 헤더가 두 번 나오는 **형태로 깨진다**"* 였다. 헤더가 하나뿐이니 **그 구조적 파손이 발생할 수 없고**, 남는 건 카드 순서뿐이라 레포 관례(*"정렬은 서버 책임"*)로 돌아간다. 계약 v2 가 `challengeDate DESC` + `id DESC` 2차 키까지 고정했다 |
| `ArchiveMonthState` (key·label·countText) | 🔴 **삭제** | 역할이 둘로 갈라졌다 — `label` 은 `ArchiveMonthCursor` 로(선택된 달에서 파생), `countText` 는 본문 상태로 |
| `ArchiveMonthHeader.kt` + `stickyHeader` | 🔴 **삭제** | design §2.3.2 폐지 판정. 월 이동 바가 같은 문자열을 두 줄 간격으로 두 번 말하게 된다. 1차가 sticky 를 채택한 사유(*"월 이동 UI 를 뺀 대가를 이게 갚는다"*)가 **명시적으로 소멸**했다 |
| `ArchiveChallengeItemState` · `ArchiveChallengeCard` · `dateText`("8월 14일") | ✅ **유지 — 손대지 않는다** | design §2.4.3 이 명시적으로 고정했다. 월 이동 바가 고정이라 월 중복은 남지만, 카드는 상세 진입 전 마지막 요약이라 자립해야 하고 **출시·테스트된 컴포넌트를 중복 두 글자 때문에 건드리면 회귀 표면만 는다** |
| 전체/부분 실패 2경로 분리 | ✅ **유지 — 월 단위에서도 성립한다** | 아래 |

### 실패 2경로가 월 단위에서 그대로 성립하는지 (pm-lead 태스크 2)

성립한다. 판별자가 *"emit 이 뒤따르는가"* 였고 그건 응답 범위와 무관하다 —
전체 실패는 그 달 본문 전체가 실패 영역이라 **인라인 카드**, 부분 실패는 그 달 목록이 나오고 몇
건만 드롭이라 **목록 + 스낵바 병행**. 범위만 "전체"에서 "그 달"로 좁아진다.

🔴 **다만 실패의 귀속이 달라져서 요구가 하나 늘었다.** 실패가 이제 **특정 달에 귀속**되므로,
실패 화면이 월 이동 바까지 덮으면 사용자가 **그 달에 갇혀 "다시 시도" 말고 탈출구가 없다** —
옆 달로 넘어가는 것도 유효한 복구인데 그 수단이 사라진다. design §2.3.3 이 월 이동 바를
**고정 크롬**으로 못박은 근거 중 하나가 이것이고, 골격도 그렇게 짰다(바는 항상 살아 있고
본문 영역만 5중 하나로 교체).

⚠️ **예외 1건 — 첫 로딩 실패.** 이번 달을 서버 에코로 알게 되므로 첫 응답이 실패하면 **어떤 달의
실패인지도 모른다.** 바를 그릴 수 없고 월 이동도 불가능하다(어디서 ±1 을 셀지 모른다) → 그
상태만은 실패 카드 + "다시 시도" 뿐이다. design 에 질의했고, 받아들일 만하다고 본다(첫 조회
실패는 대개 네트워크라 옆 달도 실패한다).

## 🔴 월 전환 누수를 구조로 막은 방식 (pm-lead 태스크 1)

pm-lead 가 *"이전 달 데이터가 잠깐 보이거나 실패 상태가 새는 경로"* 를 지목했다. 1차의 보류 상태
누수와 같은 계열이라, **같은 처방 — 수명이 다른 값을 다른 곳에 둔다 — 을 적용했다.**

| 값 | 수명 | 어디에 |
|---|---|---|
| 부분 실패 보류 메시지 | **그 달 1회 수집** | `flow { }` 람다 안 지역 변수 (1차와 동일) |
| `firstArchivedMonth` / 이번 달(상한) | **사용자·세션 전역** (요청 월과 무관하게 매 응답 동일값) | ViewModel 프로퍼티 — 달을 넘어 들고 있는 것이 **옳다** |

🔴 **헤더와 본문을 한 값으로 묶어 emit 한다.** `combine` 으로 따로 흘리면 화살표를 누른 순간
헤더만 새 달로 바뀌고 본문은 아직 옛 달 카드인 **찢어진 중간 상태**가 한 프레임 보인다.
`flatMapLatest` 안쪽 flow 의 `onStart` 가 `(새 달, 비움)` 을 **정지 없이 먼저** 내보내므로
짝이 원자적으로만 바뀐다 — 타이밍 방어가 아니라 구조적으로 불가능해진다.

⚠️ `onStart`·`onEmpty` 는 반드시 `flatMapLatest` **안쪽**이어야 한다. 바깥이면 (a) 두 번째 달
전환에서 로딩을 안 거쳐 **이전 달 데이터가 그대로 남고** (b) 상류가 무한 `StateFlow` 라
`onEmpty` 가 영원히 안 불려 **실패 화면이 나오지 않는다.**

🔴 **스낵바 이펙트도 새는 경로였다.** 1차는 `viewModelScope.launch { emit }` 로 분리했는데(구독자가
붙기 전 emit 이 파이프라인을 막지 않게), 그 코루틴은 **`flatMapLatest` 취소를 타지 않는다** —
8월의 부분 실패 스낵바가 9월 화면 위에 뜰 수 있다. `extraBufferCapacity = 1` + `tryEmit` 으로
바꾸면 비정지라 분리할 이유가 사라지고, 나중에 발화할 **보류된 emit 자체가 없어진다.**
(replay 는 0 유지 — 1차 테스트가 *"collector 붙기 전 이펙트는 버려진다"* 에 의존한다.)

**응답 경합 2차 방어**: `flatMapLatest` 로 구독을 끊고, 그래도 도착한 응답은 `month` **에코와
표시 중인 달이 다르면 버린다.** design §2.5.4.3-④ 와 같은 판단이며, 🔴 *"가정에 방어 로직을
넣지 않는다"* 와 어긋나지 않는다 — **경합은 이 화면의 정상 동작(연타)에서 직접 나오는 관측 가능한
조건**이지 "혹시 몰라서" 가 아니다.

## 변경된 파일

### wire — `:remote:*` · `:data:*` · `:domain:*`

- `core/utils/.../datetime/ChallengeDateTimeFormats.kt` — `parseWireYearMonth` 추가
- `remote/model/.../serializer/WireDateTimeSerializers.kt` — **`WireYearMonthSerializer`** 추가
  (기존 `NullTolerantStringSerializer` 를 그대로 상속 — 새 패턴 0)
- `remote/model/.../challenge/ChallengeHistoryResponse.kt` — `month`·`firstArchivedMonth` 2필드
  (둘 다 기본값 `null` — 서버가 안 내리는 환경의 `MissingFieldException` 을 막는 레포 관례)
- `domain/model/.../challenge/ChallengeArchive.kt` (신규) — `month` + `firstArchivedMonth` + `histories`
- `remote/mapper/.../ChallengeHistoryResponseMapper.kt` — `toChallengeHistories()` → `toChallengeArchive()`
- `remote/mapper/.../MappedList.kt` — `MappedArchive` 추가 (`MappedList` 무수정)
- `remote/api/.../ChallengeApi.kt` — `@Query("month") month: String?`
- `remote/datasource/.../ChallengeRemoteDataSourceImpl.kt` · `data/datasource/...` ·
  `domain/repository/...` · `data/repositoryImpl/...` — `getChallengeArchive(month, onError)` 체인
- `domain/usecase/.../GetChallengeArchiveUseCase.kt` (신규, 옛 `GetChallengeHistoriesUseCase` 삭제)
- `data/repositoryImpl/.../di/UseCaseModule.kt` — 등록 갱신
- 테스트 fake 5곳(`:feature:home`, `:feature:challenge:{detail,oath,create}`, `:remote:datasource` 의
  `FakeChallengeApi`) — 🔴 1차에서 **이걸 빠뜨려 뒤쪽 모듈의 컴파일 에러가 가려진 적이 있어**
  먼저 전수 grep 으로 6곳을 확정하고 들어갔다

### `:feature:mypage`

- `contract/ArchiveMonthCursor.kt` (신규) — 경계 규칙의 단일 소유자
- `contract/ArchiveState.kt` — `sealed interface` → **`data class ArchiveUiState(month, content)`**
  + `ArchiveContent{Blank,Loading,Failure,Data}`. `ArchiveMonthState`·`toArchiveMonths()` **삭제**
- `ArchiveViewModel.kt` — `flatMapLatest` 월 전환 파이프라인
- `ArchiveScreen.kt` — `Column` + 고정 바 + `Box(weight(1f))` 본문 4중. `stickyHeader`·월 그룹 루프 삭제
- `ArchiveRoute.kt` — 월 이동 콜백 배선. 🔴 1차의 private composable `ArchiveContent` 가 상태
  sealed interface 와 이름이 겹쳐 **`ArchiveBody` 로 개명**
- `component/ArchiveMonthNavBar.kt` (신규) · `component/ArchiveEmptyMonth.kt` (신규)
- `component/ArchiveMonthHeader.kt` — 🔴 **파일 삭제**
- `ArchivePreviewFixtures.kt` — 3개월치 → 한 달치
- `component/ArchiveChallengeCard.kt` · `ArchiveChallengeItemState` — ✅ **한 글자도 안 바꿨다**

### 테스트

- `contract/ArchiveMonthCursorTest.kt` (신규) · `ArchiveViewModelTest.kt` (전면 재작성) ·
  `FakeChallengeRepository.kt` (월별 응답·에코 조작·응답 보류 지원) ·
  `remote/mapper/.../ChallengeHistoryResponseMapperTest.kt` (신규) ·
  `remote/model/.../serializer/WireYearMonthSerializerTest.kt` (신규) ·
  `remote/datasource/.../ChallengeRemoteDataSourceImplTest.kt` (보관함 케이스 추가)

## 만든 것의 요지

### `contract/ArchiveMonthCursor.kt` (신규) — 경계 규칙의 단일 소유자

`selected` / `latest`(이번 달) / `earliest`(하한, **`null` = 기록 0건**) 세 값과
`canGoPrevious`·`canGoNext`·`previous()`·`next()`·`label`·`emptyMonthTitle`.

- 🔴 **경계에서 예외 대신 `this` 를 반환한다** — 비활성 버튼을 눌러도 아무 일이 없어야 하고,
  던지면 호출부가 경계 검사를 한 번 더 하게 되어 **같은 규칙의 사본이 두 곳에 생긴다.**
- 🔴 **이 타입은 그 달에 데이터가 있는지를 아예 모른다.** 빈 달을 건너뛰지 않는 것이 사용자 확정
  사항이라, 데이터 유무로 이동 폭이 달라지면 달력의 시간 흐름과 어긋난다. 테스트로 고정했다.
- 시계를 읽지 않아 **고정값만으로 전부 단위 테스트된다**(연말·연초 넘김 포함).
- `kotlinx.datetime.YearMonth`(0.7.1)를 쓴다. ⚠️ `YearMonth.monthNumber` 는 **internal** 이라
  `month.number` 확장을 써야 한다. Android·iOS 양 타깃 컴파일·테스트 통과를 먼저 확인했다.

### `component/ArchiveMonthNavBar.kt` (신규) — `ArchiveMonthHeader` 대체

### `component/ArchiveEmptyMonth.kt` (신규) — 빈 달 전용 화면

🔴 **`EmptyStateCard` 를 쓰지 않는다.** CTA 가 필수 파라미터인데 빈 달에 놓을 CTA 가 없다 —
"챌린지 만들기" 는 **동선이 반대**(이 사용자는 기록을 찾는 중이다)고, "이전 달 보기" 는 월 이동
바의 `<` 를 카드 안에 복제한다. 카드 크롬만 벗고 일러스트 문법은 `EmptyStateCard` 와 동일하게
두어 **새 방언이 아니라 같은 어휘의 가벼운 판**으로 만들었다 — 빈 달은 종착지가 아니라 **경유지**라,
무거운 카드가 월마다 나타났다 사라지면 정상적인 경유가 매번 사건처럼 보인다.

### design 판정 2건을 내 제안 대신 채택했다

1. **건수 줄을 감추지 않는다** — 나는 0건인 달의 `"0건"` 이 빈 상태 문구와 중복이라 숨기자고
   했으나, 감추면 **바 높이가 줄어 화살표가 위로 올라간다.** 연타가 정상 사용인 화면에서
   **중복 한 단어보다 움직이는 버튼이 나쁘다.**
2. **비활성 화살표 색** — 내가 만든 `onSurfaceVariant.copy(alpha = 0.38f)` 대신 앱 관례인
   `onBackground.copy(alpha = 0.4f)`(`Button.kt:30` 의 `disabledContentColor`). 새 값을 만들지 않는다.

## 🔴 이번 작업에서 발견한 것 — **3개 모듈의 iOS 테스트가 원래부터 컴파일되지 않고 있다**

작업 전 전체 기준선을 뜨다가 발견했다. **내 변경과 무관한 선재 상태**다(변경 전 실행에서 동일).

```
e: .../core/utils/.../WireFormatBaselineTest.kt:32:9        Name contains illegal characters: "()".
e: .../data/repositoryImpl/.../FcmTokenRepositoryImplTest.kt:11:9   Name contains illegal characters: ",".
e: .../remote/datasource/.../ChallengeRemoteDataSourceImplTest.kt:128:9  Name contains illegal characters: ",".
```

🔴 **Kotlin/Native 는 백틱 함수명에 `,` `(` `)` 를 허용하지 않는다.** pm-lead 가 이번 태스크에서
*"백틱 이름 제약 유지"* 로 경고한 바로 그 제약인데, **이미 어기고 있는 파일이 3개 모듈에 있다.**
결과로 `:core:utils` · `:data:repositoryImpl` · `:remote:datasource` 의
`compileTestKotlinIosSimulatorArm64` 가 실패하고 **그 모듈의 iOS 테스트가 한 건도 실행되지 않는다.**
(별건으로 `:local:database:kspKotlinIosSimulatorArm64` 도 `PROCESSING_ERROR` 로 실패한다.)

⚠️ **1차 리포트가 이걸 "iOS —" 로 적었다.** 그때 나는 *"그 모듈은 iOS 타깃 테스트가 없다"* 로 읽었는데
사실은 **있는데 컴파일이 안 되고 있었다.** 조용히 빠진 것이라 숫자만 보면 알 수 없다 —
`:remote:datasource` 39건, `:data:repositoryImpl` 15건, `:core:utils` 35건이 **Android 에서만** 돈다.

- 이번에 내가 **새로 만든 테스트 파일 4개는 전부 이 제약을 지킨다**(백틱 이름에 한글·공백·숫자만).
  실측으로 확인했다.
- 🔴 **고치지 않았다** — 이름 15개가량을 바꾸는 기계적 작업이지만 **다른 feature 의 테스트 파일**이라
  이번 개정의 범위 밖이다. 백로그/별도 작업으로 올리는 것을 권한다. 고치면 iOS 커버리지가
  3개 모듈만큼 늘어난다.

⚠️ **검증 방법에 대한 교훈 하나 더.** `./gradlew ... ; echo "EXIT=$?"` 로 돌리면 **셸의 종료 코드는
`echo` 의 것**이라 상위 도구가 항상 "성공"으로 보고한다. 1차에서 `| tail -80` 이 exit code 를
삼켰던 것과 **같은 계열의 함정**이다. 로그의 `BUILD SUCCESSFUL` 문자열과 `GRADLE_EXIT=` 출력을
**둘 다** 확인해야 한다 — 이번에도 그 대조로 기준선 실패를 잡았다.

## 테스트 결과 — 실측 XML

**전체 합계: Android 563 / iOS 478. `failures=0 errors=0` (전 모듈 XML 전수 확인).**
XML 전부 `2026-08-28` 자로, 이번 세션 실행분이다 — 08-26 이전 stale 은 **0건**.

| 모듈 | Android | iOS | 비고 |
|---|---|---|---|
| `:feature:mypage` | **49** | **49** | 1차 30 → 49. 커서 11 + ArchiveViewModel 19 + MyPage 19 |
| `:remote:mapper` | **130** | **130** | 120 → 130 (보관함 매퍼 테스트 신규 10) |
| `:remote:model` | **15** | **15** | 6 → 15 (`WireYearMonthSerializerTest` 9) |
| `:remote:datasource` | **39** | — | 32 → 39. iOS 는 아래 선재 이슈로 미실행 |
| `:core:utils` | 35 | — | 변동 없음. iOS 는 아래 선재 이슈 |
| `:data:repositoryImpl` | 15 | — | 변동 없음. iOS 는 아래 선재 이슈 |
| 그 외 전 모듈 | 변동 없음 | 변동 없음 | 회귀 0 |
| **합계** | **563** | **478** | 기준선 529 / 451 → **+34 / +27** |

`:composeApp:compileDebugKotlinAndroid` 성공.

⚠️ **전체 실행의 gradle 종료 코드는 1이다.** 실패 4건은 **전부 위 §선재 이슈**(`:local:database`
KSP + iOS 테스트 컴파일 3개)이고, **작업 전 기준선 실행의 실패 집합과 정확히 동일**하다 —
내 변경으로 새로 깨진 것은 **0건**이며 **테스트 실패는 전 모듈 XML에 한 건도 없다.**

### 신규 테스트가 고정한 것

- `ArchiveMonthCursorTest` 11 — 경계 규칙(이번 달 상한 / 하한 / 기록 0건 / **빈 달을 건너뛰지 않음** /
  연말·연초 넘김 / 경계에서 `this` 반환)
- `ArchiveViewModelTest` 19 — 🔴 그중 **누수·경합 방어 6건**: 월 전환 시 이전 달 카드 잔존 /
  이전 달 실패 잔존 / **에코 어긋난 응답 폐기** / **부분 실패 스낵바가 다음 달로 샘** /
  **재수집 시 직전 실패 메시지가 샘**(1차 계승) / 재시도 중 바 소실
- `WireYearMonthSerializerTest` 9 — `2026-8`·`2026-08-14`·깨진 문자열·JSON null·숫자·필드 누락이
  전부 null 로 떨어지고, `YearMonth(2026, 3)` → `"2026-03"` **zero-padding 왕복**
- `ChallengeHistoryResponseMapperTest` 10 — 🔴 **`month` 를 못 읽으면 응답 전체를 버린다**,
  `firstArchivedMonth` null 보존, 항목 드롭이 두 필드에 영향 없음
- `ChallengeRemoteDataSourceImplTest` +7 — 🔴 **`month` 결측은 emit 없이 전체 실패**(부분 실패와
  갈리는 판별자 고정), `month=null` 로 나가는 첫 요청

## 실기 검증 없음

월 이동·빈 달·경계 비활성은 **단위 테스트와 프리뷰까지만** 확인했다. 실제 서버 응답으로 도는 것,
연타 시 체감(300ms 지연 스피너가 실제로 명멸을 없애는지)은 **실기로만 확인 가능**하다.

## Working tree 상태

- **작업 브랜치**: `main` (현재 체크아웃된 브랜치. 새로 만들지 않았다)
- **변경분**: 수정 25 · 신규 8 · 삭제 2, 전부 staged/unstaged 그대로.
  **커밋·푸시·PR 생성 안 함** — 사용자 처리 영역

## 미해결 / 인계

1. 🔴 **`:core:utils`·`:data:repositoryImpl`·`:remote:datasource` 의 iOS 테스트 컴파일 실패**
   (위 §발견). 백틱 이름의 `,`·`()` 제거로 해소되며 iOS 커버리지가 3개 모듈만큼 는다.
   `:local:database` KSP 실패는 별건
2. **첫 로딩 실패는 "다시 시도" 만 남는다** — 이번 달을 서버 에코로 알아서 어느 달의 실패인지도
   모른다. design 이 §2.5.4.1 에 예외로 인라인했고 수용 판정
3. **상한(이번 달)은 세션 중 고정** — 첫 응답 에코를 들고 있으므로, 앱을 열어 둔 채 자정을 넘겨
   달이 바뀌면 새 달로 못 간다. 재진입하면 해소된다(ViewModel 재생성). 방어 코드를 넣지 않았다
4. **문구 미확정 승계** — 1차의 §6 디자이너 확인 대상에 §6-⑰(월 이동 바 형태·건수 이관·라벨
   타이포)이 추가됐다. 전부 "제안" 상태로 구현돼 있다

## API 계약 대비 구현 차이

**없음.** 계약 v3 §1 을 그대로 따랐다. 협의 과정에서 **내가 철회한 것 2건**(`month` required /
에코 불필요)과 **관철한 것 1건**(경계 절대값)은 위 §계약 협의에 기록했다.

---

# (이하 1차 기록 — 2026-08-26)

## 구현 요약

| 태스크 | 상태 |
|---|---|
| T-M1 프로필 카드 + 마이페이지 골격 | ✅ 완료·검증 |
| T-M2 로그아웃 실구현 | ✅ 완료·검증 |
| T-M3 계약서 보관함 화면 | ✅ 완료·검증 |
| T-M4 회원탈퇴 플로우 (+ `photoDeleted`) | ✅ 완료·검증 |
| T-M5 테스트 | ✅ failures=0 (아래 표) |

마이페이지가 `PlaceholderScreen` 에서 실제 화면이 됐고, **로그아웃이 처음으로 서버에 도달**한다.
계약서 보관함이 신설되어 **홈 7일 노출이 지난 결과에도 도달**할 수 있다(백로그 "결과 히스토리 화면
부재" 해소 조건).

## 사용한 모바일 레포 스킬

- `/viewmodel` — `MyPageViewModel` StateFlow 파이프라인(`triggerStateIn` + `combine`)
- `/domain` — `GetMyPageDataUseCase` · `WithdrawUseCase` · `LogoutReason`
- `/data-remote` — `logout` · `withdraw` 배선(Api → RemoteDataSource → Repository)
- `/feature` — 마이페이지 화면·컴포넌트
- `design-system` (자동 적용) — 토큰·프리뷰 규칙

## 🔴 이 작업의 핵심 발견 — `WWW-Authenticate` 없이도 Ktor 자동 갱신이 돈다

계약 §3 이 *"Ktor 자동 갱신이 이 헤더를 필요로 한다는 결론이 나오면 `UnauthorizedEntryPoint` 에
추가한다 — **모든 401 의 전역 변경**이라 mobile 확인 전에는 넣지 않는다"* 로 mobile 회신을 대기하고
있었다. **실측으로 답했다: 필요 없다. 서버 변경 0건.**

프로덕션 인증 설정을 `MockEngine` 에 그대로 태우는 특성화 테스트를 신설해 확인했다.

| 테스트 | 결과 |
|---|---|
| 401 + `WWW-Authenticate: Bearer` → 갱신 후 원 요청 재시도 | ✅ pass |
| 🔴 401 에 헤더 **없어도** 갱신이 시도된다 | ✅ **pass** |

코드 근거도 일치한다 — `ktor-client-auth 3.3.1` `Auth.kt` `findProvider` 에
`authHeaders.isEmpty() && candidateProviders.size == 1 -> candidateProviders.first() to null` 분기가
있고, 이 앱은 프로바이더가 `bearer` 하나뿐이라 이 경로를 탄다. **우연이 아니라 후보가 하나인 한
구조적으로 돈다.** ⚠️ 그 전제(프로바이더 1개)가 깨지면 헤더가 필요해지며, 위 테스트 2건이 그 순간
빨갛게 터지도록 박제해 뒀다.

RFC 9110 §15.5.2 위반은 남지만 **동작을 위해 전역 401 을 건드릴 이유는 사라졌다.** 규격 정합은
별건으로 백로그 대상.

## 변경된 파일

### T-M1 — 프로필 카드 + 골격

- `domain/model/.../MyPageData.kt` (신규) — `record: UserRecord?` + `userInfo: UserInfo?`
- `domain/usecase/.../GetMyPageDataUseCase.kt` (신규) — `combine`. 🔴 **두 소스 모두 `onEmpty` 폴백** —
  없으면 한쪽 실패가 화면 전체를 `Loading` 에 영구히 가둔다
- `feature/mypage/.../contract/MyPageState.kt` — `Data(record, userInfo, isWithdrawing)` + `recordSummary`
- `feature/mypage/.../MyPageViewModel.kt` — `triggerStateIn(WhileSubscribed(0))` (탭 복귀 시 전적 재조회)
- `feature/mypage/.../MyPageRoute.kt` — `ChallengeScaffold` + `ChallengeTopBar(titleStyle = bold20)`
- `feature/mypage/.../MyPageScreen.kt` — `Column(verticalScroll)` 골격
- `feature/mypage/.../component/ProfileCard.kt` (신규) — 아바타 64dp/**radius 20dp**, 승=`primary`
- `feature/mypage/.../component/MyPageMenuCard.kt` (신규) — 목록 전제로 파라미터화
- `data/repositoryImpl/.../di/UseCaseModule.kt` — UseCase 등록
- `feature/mypage/build.gradle.kts` — `compose.materialIconsExtended` + commonTest 의존

### T-M2 — 로그아웃

- `remote/network/.../auth/ChallengeAuth.kt` (신규) — `install(Auth)` 블록을 추출(동작 무변경).
  🔴 `sendWithoutRequest` 술어를 **공개 3경로 allowlist** 로 교체
- `remote/network/.../di/KtorfitModule.kt` — 한 줄 호출로 축약
- `remote/model/.../auth/LogoutResponse.kt` (신규) — `data` 키 없음
- `remote/api/.../LoginApi.kt` — `@DELETE("api/v1/auth/logout")` + *"공개 엔드포인트"* KDoc 정정
- `remote/datasource/.../LoginRemoteDataSourceImpl.kt` · `data/datasource/.../LoginRemoteDataSource.kt` ·
  `domain/repository/.../LoginRepository.kt` · `data/repositoryImpl/.../LoginRepositoryImpl.kt` — 배선
- `domain/model/.../LogoutReason.kt` (신규) — `USER` / `SESSION_EXPIRED` / `WITHDRAWN`
- `domain/usecase/.../LogoutUseCase.kt` — `invoke(reason)`
- `domain/usecase/.../LoginWithTestAccountUseCase.kt` — `LogoutReason.USER` 전달
- `feature/main/.../MainViewModel.kt` — `merge` 에 이유를 실어 보냄

### T-M4 — 회원탈퇴

- `core/ui/.../ConfirmDialog.kt` (신규) — `destructive: Boolean` 하나로 색 판정
- `feature/mypage/.../component/WithdrawText.kt` (신규) — `onSurfaceVariant`, 세로 패딩으로 48dp 터치 타깃
- `remote/model/.../user/WithdrawResponse.kt` · `remote/api/.../UserApi.kt` (`@DELETE api/v1/users/me`)
- `data/datasource/.../WithdrawRemoteDataSource.kt` · `remote/datasource/.../WithdrawRemoteDataSourceImpl.kt` ·
  `domain/repository/.../WithdrawRepository.kt` · `data/repositoryImpl/.../WithdrawRepositoryImpl.kt` (전부 신규)
- `domain/usecase/.../WithdrawUseCase.kt` (신규)
- `core/navigation/.../MainAction.kt` — `fun withdrawn()`
- `feature/main/.../MainScreen.kt` · `MainViewModel.kt` — `withdrawn` 배선

### T-M3 — 계약서 보관함

- `domain/model/.../challenge/ChallengeHistory.kt` (신규) — `myResult: ChallengeOutcome` non-null
  (기존 `Outcome` 타입 재사용, 새 매핑 만들지 않음)
- `remote/model/.../challenge/ChallengeHistoryResponse.kt` · `remote/mapper/.../ChallengeHistoryResponseMapper.kt` (신규)
- `remote/api/.../ChallengeApi.kt` — `@GET("api/v1/challenges/history")`
- `remote/datasource` · `data/datasource` · `domain/repository` · `data/repositoryImpl` — `getChallengeHistories` 배선
- `domain/usecase/.../GetChallengeHistoriesUseCase.kt` (신규)
- `feature/mypage/.../ArchiveRoute.kt` · `ArchiveScreen.kt` · `ArchiveViewModel.kt` ·
  `contract/ArchiveState.kt` · `contract/ArchiveEffect.kt` · `ArchivePreviewFixtures.kt` (전부 신규)
- `feature/mypage/.../component/ArchiveMonthHeader.kt` · `ArchiveChallengeCard.kt` (신규)
- 🔴 `feature/home/.../component/BetStrip.kt` → **`core/ui/.../components/BetStrip.kt`** (`git mv`).
  `internal` → `public`, **렌더 코드 무변경**. KDoc 의 *"홈 카드 2곳이 공유한다"* 문장도 함께 정정 —
  안 고치면 다음 사람이 또 사본을 뜬다
- `core/navigation/.../Route.kt` — `Route.Archive` + `routeSerializersModule` 등재
- `feature/main/.../MainScreen.kt` — `entry<Route.Archive>` 등록
  (`feature/main/build.gradle.kts` 는 `:feature:mypage` 가 이미 의존성에 있어 변경 없음)
- `feature/{home,challenge/detail,challenge/oath,challenge/create}` 의 `FakeChallengeRepository` +
  `remote/datasource` 의 `FakeChallengeApi` — 신규 인터페이스 멤버 스텁

## 🔴 T-M2 의 세 가지 계약 — 테스트로 고정했다

1. **서버 호출은 `clearTokens()` 앞.** 뒤에 두면 토큰이 없어 401 → refresh 실패로 **정상적인 계정
   전환이 "세션 만료"로 반응**한다. → `listOf("logout", "clearTokens")` 순서를 단언
2. **서버 실패를 삼키고 로컬 정리는 반드시 수행.** 서버가 죽었다고 사용자를 로그인 상태에 가둘 수
   없다(계약의 *"멱등 성공"* 철학). 단 `CancellationException` 은 재던진다 —
   `PhotoCompressor.android.kt:52` 의 레포 관례
3. **`SESSION_EXPIRED` 는 서버를 부르지 않는다.** `MainViewModel` 이 자동/수동 로그아웃을 한 흐름에
   합쳐 놔서, 만료 경로에서 서버를 부르면 401 → refresh 실패 → `emitSessionExpired()` → **같은
   merge 흐름에 재진입**한다

### `sendWithoutRequest` 술어를 왜 allowlist 로 바꿨나

기존 `pathSegments.none { it == "auth" }` 는 `/auth/logout`(Bearer **필수**)까지 걸러 토큰을 안 붙였다.
그리고 이건 "토큰이 안 붙는다"에서 끝나지 않는다 — `ktor-client-auth` 의 `refreshTokenIfNeeded` 는
**토큰이 선제 부착된 요청만** 갱신 대상으로 삼으므로, 401 을 받아도 **자동 갱신조차 돌지 않았다.**

allowlist 방향을 고른 이유는 **실패 방향이 안전**하기 때문이다 — 새 공개 엔드포인트를 빠뜨리면 공개
API 에 토큰이 붙을 뿐(무해)이지만, 차단목록 방식은 보호된 API 에서 토큰이 빠져 **조용히 401** 이 된다.
`/auth/refresh` 가 목록에 남아야 하는 것도 고정했다(만료 토큰으로 갱신을 시도하면 재귀).

## 테스트 결과 — 실측 XML (최종, `GRADLE_EXIT=0` · BUILD SUCCESSFUL)

| 모듈 | Android | iOS | XML timestamp (UTC) |
|---|---|---|---|
| `:remote:network` | 23 | 23 | 07:55:31 / 07:58:39 |
| `:remote:mapper` | **120** | **120** | 08:10:10 / 08:10:12 |
| `:remote:datasource` | 32 | — | 07:58:37 |
| `:data:repositoryImpl` | 15 | — | 07:58:40 |
| `:core:ui` | 4 | 4 | 07:54:03 / 07:54:35 |
| `:feature:main` | 17 | 17 | 07:55:04 / 07:55:19 |
| `:feature:login` | 15 | — | 07:55:27 |
| `:feature:home` | 24 | 24 | 07:54:32 / 07:54:34 |
| `:feature:mypage` | **30** | **30** | 08:30:30 / 08:30:32 |
| `:feature:challenge:detail` | **45** | **45** | 08:09:52 / 08:09:54 |
| `:feature:challenge:verify` | 25 | (미실행) | 08:10:09 |
| **합계** | **346** | **259** | 전부 `2026-08-26` |

`photoDeleted` 반영 후 재측정: `:feature:challenge:detail` **41 → 45**(신규 4, 회귀 0, Android·iOS 동일),
`:remote:mapper` **116 → 120**. pm-lead 가 건 조건(*"기존 41건 전량 회귀 확인"*) 충족.

`failures=0 errors=0 skipped=0`. `:composeApp:compileDebugKotlinAndroid` 성공.

⚠️ **stale 1건 — 숫자에서 제외했다.** `:feature:challenge:verify` 의 **iOS** XML 은 `2026-08-18` 자로
이번 실행분이 아니다(태스크 목록에 넣지 않았다). 그 모듈은 이번에 **테스트 fixture 2줄만** 바뀌었고
Android 25건은 fresh 하게 통과했다.

⚠️ `:feature:main` 의 iOS XML 은 작업 **시작 시점에 `2026-08-08` 자 stale** 이었다 — 이번 작업으로
갱신됐음을 확인했다. 원래 stale 이던 것을 되살린 사례다.

🔴 **검증 과정에서 오탐 2건을 잡았다.**
1. `./gradlew ... | tail -80` 로 돌렸더니 셸이 **`tail` 의 exit code** 를 반환해 **실패한 빌드가
   성공으로 보였다.** XML timestamp 가 실행 시각보다 과거인 것으로 발각했다(실제로는
   `ChallengeAuth.kt:94 Unresolved reference 'encodedPath'` — Ktor 3.3.1 `URLBuilder` 에 없는 프로퍼티).
   **gradle 을 파이프에 물리지 말 것.**
2. 첫 T-M3 실행이 `:feature:mypage` 에서 먼저 실패해 **뒤쪽 모듈의 컴파일 에러가 가려졌다**
   (`FakeChallengeApi` 가 신규 `getChallengeHistories` 미구현). 모듈 하나가 실패하면 나머지는
   검증되지 않은 것으로 취급해야 한다.

### 🔴 `kotlin.math.round` 는 은행가 반올림이다 — 테스트가 design 의 서술 오류를 잡았다

design.md §1.2.5.2 가 요구한 반올림 회귀 테스트(`5승 3패` → 5/8 = 62.5% → **63%**)가 **실패**했다.
원인은 같은 절의 서술이 사실과 달랐던 것 —

> ⚠️ Kotlin `round()` 는 `.5` 를 가장 가까운 짝수가 아니라 위로 보내므로 `Math.round` 와 같다

`kotlin.math.round` 는 **ties-to-even** 이라 `round(62.5) == 62.0` 이다. 서버가 쓰는
`java.lang.Math.round(double)` 은 **`floor(x + 0.5)`** 로 정의돼 `63` 이다. **둘이 다르다.**

→ 구현을 `floor(win * 100.0 / total + 0.5).toInt()` 로 고쳤다. **테스트가 옳았고 문서가 틀렸다** —
design.md §1.2.5.2 의 해당 ⚠️ 문장은 정정 대상이다.

## Working tree 상태

- **작업 브랜치**: `main` (현재 체크아웃된 브랜치. 새로 만들지 않았다)
- **변경분**: staged/unstaged 그대로. **커밋·푸시·PR 생성 안 함** — 사용자 처리 영역

## `photoDeleted` — 탈퇴자 인증 사진 (pm-lead 판정으로 T-M4 범위 확정, 완료)

`photoDeleted: Boolean`(additive·non-null·기본 `false`)을 DTO → 도메인 → 매퍼 → 화면까지 배선하고,
`VerificationPhoto` 의 `when` 에 분기를 **하나 추가**했다.

```kotlin
photoDeleted -> PhotoMessage(PHOTO_DELETED_TEXT)      // 신규 — "탈퇴한 사용자의 사진은 삭제됐어요"
photoUrl == null -> PhotoMessage(LOAD_FAILED_TEXT)    // 🔴 유지
```

🔴 **`photoUrl == null` 분기를 지우지 않은 것이 이 작업의 핵심이다.** 그 자리는 *"인증은 됐는데 URL 이
없는 비정상"* 을 잡으려고 일부러 만든 **감지기**다. 두 신호를 한 문구로 합치면 **URL 유실 버그가
탈퇴자 뒤에 영영 숨는다.** `photoDeleted == false` 인데 URL 이 null 이면 여전히 기존 문구가 나온다.

- **`PhotoRetryMessage` 가 아니라 `PhotoMessage`** — 삭제는 영구 상태라 재시도할 대상이 없다.
- `FAILED` 분기가 새 분기보다 **위**라, 서버 실측의 `FAILED + photoDeleted` 조합도 기존 문구를 유지한다.
- DTO 필드에 **기본값 `false`** 를 줬다 — 서버가 아직 안 내리는 환경에서 `MissingFieldException` 이 난다.
- 프리뷰 4종(사진 / 삭제됨 / **URL 유실** / 미인증)으로 ②와 ③이 다른 문구인지 눈으로 고정했다.

## 보관함 조회 실패 — 인라인 실패 카드 + 두 실패 경로 분리 (design §2.5.4.1, 완료)

초판 §2.5.4 의 *"스낵바 + 로딩 직전 상태 유지"* 는 첫 진입에서 **유지할 상태가 없어 무한 스피너**가
됐다(§1.7.2 가 마이페이지에서 기각한 바로 그 상태). design 이 판정을 뒤집어 **인라인 실패 카드 +
"다시 시도"** 로 확정했고 그대로 구현했다.

`EmptyStateCard` 골격 재사용, 값만 교체 — `CloudOff` / `"보관함을 불러오지 못했어요"` /
`"잠시 후 다시 시도해주세요"` / `"다시 시도"` + `Refresh` → `uiState.restart()`.
🔴 **재시도 버튼이 여기엔 필수다** — 마이페이지에서 뺀 사유(*"탭이라 재진입이 재시도"*)가 **push 하위
화면엔 성립하지 않는다.** 뒤로 가는 순간 실패했다는 사실도 화면과 함께 사라진다.
🔴 **아이콘을 `Description` 으로 두지 않았다** — 빈 상태와 구분이 안 된다.

**실패를 상태로 만든 방식**: `onEmpty { emit(Failure) }` + 그 **바깥**의 `onStart { emit(Loading) }`.
⚠️ `onStart` 가 `onEmpty` **안쪽**이면 `Loading` emit 이 "비어있지 않음"으로 세어져 `Failure` 가
영원히 안 나온다 — 바깥에 둔 것이 핵심이다.

### 🔴 두 실패를 갈랐다 — `onError` 하나가 서로 다른 두 사건을 나른다

`ChallengeRemoteDataSourceImpl.getChallengeHistories` 실측(40~51행):

```kotlin
if (mapped.droppedCount > 0) onError("일부 항목을 불러오지 못했어요")  // 부분 실패: onError 후 emit 이 온다
this@flow.emit(mapped.items)
.suspendOnFailureWithErrorHandling(onError)                          // 전체 실패: emit 이 없다
```

**`onError` 자체로는 구분되지 않는다. 판별자는 "emit 이 뒤따르는가" 다.**

| 사건 | 표현 |
|---|---|
| 전체 실패 (emit 없음) | 실패 카드, **스낵바 없음** |
| 부분 실패 (목록은 오고 몇 건 드롭) | **목록 + 스낵바 병행** |

design 이 세운 규칙(*"실패 표시가 주 내용을 차지하면 생략, **부분 표시면 병행**"*)을 그대로 적용한
것이다 — 규칙을 바꾼 게 아니다. pm-lead 승인.

이 구분이 필요한 이유는 T-M3 의 드롭 정책과 맞물린다 — 보관함 매퍼는 `challengeDate`·`myResult` 를
못 읽으면 **항목을 버린다**(홈과 반대). **드롭을 정당화한 논리가 곧 드롭이 실제로 일어난다는 뜻**인데,
알림이 없으면 목록은 정상으로 보이면서 몇 건이 조용히 빠진다. §2.5.2.1 의 신호 분리와 같은 결이다.

구현: `flow { }` 빌더 **람다 안 지역 변수**에 메시지를 보류하고, `collect` 람다(= emit 이 일어나는
지점)에서 flush → 부분 실패. `onEmpty` 는 보류분을 버리고 `Failure` 만 낸다 → 전체 실패.
🔴 **보류 상태가 수집 단위여야 한다** — ViewModel 프로퍼티면 `retry()` 재수집 때 **이전 실패
메시지가 새어 나온다.** `flow { }` 지역 변수라 재수집이 블록을 처음부터 다시 실행해 살아남을 경로가
구조적으로 없다. 그 누수를 막는 회귀 테스트를 넣었다.

🔴 **`ArchiveRoute` 에 `uiEffect` 수집이 아예 없었다** — 이펙트를 흘려도 스낵바가 뜨지 않는 상태였다.
`LocalMainAction.showSnackBar` 로 연결했다(`RankingRoute`·`MyPageRoute` 와 동일 패턴).

## 미해결 이슈

1. **로컬 정리가 두 번 탄다** — `WithdrawUseCase` 가 `logoutUseCase(WITHDRAWN)` 을 부르고,
   `MainViewModel.withdrawn()` 도 같은 정리를 탄다. 멱등이라 무해하지만 소유자가 둘이다
4. **실기 검증 없음** — 로그아웃이 서버 `fcm_token` 을 실제로 NULL 로 만들어 *"그 기기로 푸시가 더
   안 온다"* 는 수용 기준은 **실기로만 확인 가능**하다. 탈퇴·보관함 플로우도 동일
5. **문구 미확정** — design §6 의 디자이너 확인 대상(승/패/무 색, 빈 상태 문구, 탈퇴 문구·색·배치,
   탈퇴 다이얼로그 본문 등)이 전부 "제안" 상태로 구현돼 있다

## T-M3 구현 시 내린 판단 (design.md 반영 필요)

1. **신규 route 이름 = `Route.Archive`** (평탄한 `data object`). `:feature:mypage` 가 하위 모듈로
   나뉘지 않은 단일 모듈이라 `Route.kt` 주석의 *"중첩은 하위 모듈로 나뉜 feature 만"* 규칙을 적용
2. **`stickyHeader` 를 썼다** (일반 `item` 으로 내리지 않음)
3. **월 헤더의 좌우 gutter 를 `contentPadding` 이 아니라 컴포넌트가 직접 낸다.** §2.3 도식대로
   `contentPadding(horizontal = 20.dp)` 을 주면 **sticky 헤더 배경이 gutter 만큼 좁아져 좌우로
   카드가 비친다** (§2.3.2 가 Lovable 의 `-mx-5 px-6` 로 지적한 것과 같은 문제)
4. **매퍼 드롭 정책이 홈과 반대다.** 홈은 모르는 `myResult` 를 null 로 흡수하고 카드를 살리지만,
   보관함은 `challengeDate`·`myResult` 중 하나라도 못 읽으면 항목을 드롭한다 — §2.4.2 가
   "결과 pill 항상 non-null" 을 전제하고 날짜가 월 그룹 키라 둘 다 없으면 그릴 자리가 없다
5. **`toArchiveMonths` 가 `challengeDate` 내림차순 정렬을 한 번 더 한다.** 레포 관례는
   *"정렬은 서버 책임"* 이지만, 그룹핑은 순서가 어긋난 응답에서 **같은 월 헤더가 두 번 나오는
   형태로 깨진다** — 목록 순서가 바뀌는 것과 다른 급이라 방어했다

## API 계약 대비 구현 차이

**없음.** 계약 `confirmed` 3종을 그대로 따랐다. 다만 계약 협의 과정에서 mobile 이 요구했다가
**철회한 것 1건**: `GET /record` 에 `winRate`·`totalChallenges` 추가. design 이 *"loser-ranking 에서
재계산을 막은 이유는 서버가 그 정수를 정렬 3차 키로도 쓰기 때문이고 여기엔 정렬이 없다"* 로
반박했고 타당해 철회했다 — **`GET /record` 계약 변경 0 유지.**

## design.md 에 반영이 필요한 것 (구현이 문서를 앞선 지점)

1. **§3.2 `ProfileCard` 시그니처** — 문서는 "개별 `Int` 3개"(원래 mobile 제안)인데, §1.7.3 의
   *"전적 실패를 0 과 구분"* 요구를 타입으로 강제하려고 **`record: UserRecord?` 하나**로 바꿨다.
   `Int` 3개면 `win = 0` 을 넘기는 경로가 컴파일된다. CLAUDE.md *"파생값이 없으면 도메인 모델을
   그대로 UiState 에 담는다"* 와도 이쪽이 맞는다
2. **탈퇴 다이얼로그를 별도 컴포넌트로 만들지 않았다** — §3.2 신규 목록에 없어
   `MyPageRoute` 에서 `ConfirmDialog` 를 직접 호출하고 문구는 같은 파일 `private const` 로 뒀다
