# Mobile Report — soul-oath

- **작성**: 2026-08-03 mobile-dev
- **범위**: T-M1 ~ T-M5 전량
- **상위**: [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [design.md](./design.md)

## 구현 요약

챌린지에 **영혼의 맹세(서명)** 를 넣었다. 서명은 손가락 획을 정규화·양자화한 **벡터 데이터**로 저장하고, 신청·수락 요청에 실려 나가며 상세에서 양측 서명이 실제로 그려진다.

화면 3개가 서명을 다룬다:

| 화면 | 모듈 | 성격 |
|---|---|---|
| 위저드 **맹세 step** (챌린저) | `:feature:challenge:create` | 신규 step (2칸 → **3칸**) |
| **맹세 화면** (상대) | **`:feature:challenge:oath`** 신규 | `AcceptChallengeDialog` **교체** |
| **챌린지 상세** | **`:feature:challenge:detail`** 신규 | `PlaceholderScreen` **교체** |

## 사용한 모바일 레포 스킬

- `full-feature` — 신규 모듈 2개(`oath` / `detail`)의 domain→data→feature→navigation 전 구간
- `domain` / `data-remote` — `ChallengeDetail` 모델, `GET /challenges/{id}` DTO·매퍼, 요청 body에 `signature` 추가
- `feature` / `viewmodel` — `OathViewModel` / `ChallengeDetailViewModel`, `MutableStateFlow` + `.update {}`
- `navigation` — `Route.Challenge.Oath` 신설, `Detail` 실화면 연결
- `test-usecase` / `test-viewmodel` — 신규 45건

---

## 테스트 결과

**230 / 230 passed, 0 failed** (`HEAD` 144 → **230**, +86)

```
BUILD SUCCESSFUL
./gradlew testDebugUnitTest jvmTest :composeApp:linkDebugFrameworkIosSimulatorArm64
```

> 최초 보고 **210** → 실서버 wire 픽스처 **+8**(218) → PENDING 픽스처 **+5**(223) → `ApiResult` 회귀 방지 **+7**(230). 아래 "실서버 wire 검증" / "실기에서 나온 버그 3건" 절 참조.

### 🔴 회귀 / 교체 / 신규 분해

| 구분 | 건수 | 내용 |
|---|---|---|
| **기존 회귀** | **0** | — |
| **의도적 삭제·교체** | **5** | 홈 수락 다이얼로그 전용 (아래) |
| **신규 (#21)** | **45** | |
| 신규 (#19 T-M1, 기보고) | 26 | `SignatureCodecTest` 18 / `SignatureTest` 4 / `SignatureCoordinateTest` 4 |

`144 + 26 + 45 − 5 = 210` — #21 종료 시점 산술. 이후 wire 픽스처 +8, PENDING 픽스처 +5 로 **223**.

**삭제한 5건** (`HomeViewModelTest`) — `AcceptChallengeDialog` 소멸에 따른 교체다:
1. `openAcceptDialog 는 대상을 세팅하고 dismissAcceptDialog 는 해제한다`
2. `updateAcceptMission 은 최대 길이로 잘린다`
3. `submitAccept 성공 시 trim 된 미션으로 요청하고 목록을 재조회한다`
4. `submitAccept 실패 시 ShowMessage 를 발행하고 제출 상태를 풀고 재조회한다`
5. `submitAccept 를 연속 호출해도 수락 요청은 1회만 나간다`

> **착수 전 추정이 실측과 일치했다** — "수락 다이얼로그 전용 5건"으로 예측했고 정확히 5건이었다. 다만 전체 건수를 24로 말했는데 **실제는 23**이었다(`@Test` 줄을 눈으로 세다 1건 중복). 유지 대상은 18건이다.
>
> **유지된 18건은 한 글자도 안 바뀌었다.** `git diff` 상 삭제 라인 89줄이 전부 위 5개 테스트 본문 안에 있고, 추가 21줄은 신규 1건 + KDoc이다.

### 신규 45건 내역

| 파일 | 건수 | 성격 |
|---|---|---|
| `OathViewModelTest` | 16 | 신규 모듈 |
| `ChallengeDetailViewModelTest` | 12 | 신규 모듈 |
| `ChallengeDetailMapperTest` | 8 | 신규 매퍼 |
| `ChallengeCreateViewModelTest` | +5 | 맹세 step 전이·서명 조건 |
| `ChallengeRepositoryImplTest` | +3 | `getChallengeDetail` |
| `HomeViewModelTest` | +1 | **재구독 갱신** (아래) |

### 빌드

- **Android** 유닛 — ok (230/230)
- **KMP common metadata** — ok
- **iOS 링크** (`linkDebugFrameworkIosSimulatorArm64`) — ok. 산출물 timestamp **08-03 14:31**, 최종 실행에서 갱신된 것이며 stale 아님
- iOS **유닛 테스트는 미실행** (기존 관행: Android 유닛 + iOS 링크까지가 게이트)

---

## 변경된 파일

### 신규 모듈 2개
- **`:feature:challenge:oath`** — 13 files. `OathRoute` / `OathScreen` / `OathViewModel` / `contract` 2 / `component` 4 / `di` / test 2
- **`:feature:challenge:detail`** — 13 files. 동일 구조

### `:core:ui` 신규 컴포넌트
- `ContractCard.kt` — 계약서 카드. **소비 모듈 3곳**
- `signature/SignatureField.kt` — 서명 **입력** 칸 (박스 + dashed 빈 상태 + "다시 그리기")
- `signature/SignatureSlot.kt` — 서명 **읽기 전용** 칸. dashed 스펙을 `SignatureField`와 한 벌 공유
- `signature/SignatureCanvas.kt` · `SignatureView.kt` · `SignatureDrawing.kt` (T-M1)

### 🔁 이동 2건 — **신규 코드 아님. 두 번째 소비자가 생겨서 옮겼다**
| 대상 | `from` → `to` | 사유 |
|---|---|---|
| `PlatformBackHandler` (expect/actual 3파일) | `:feature:main` → `:core:ui` | 맹세 화면이 **시스템 백을 가로채야** 한다. `ChallengeCreateRoute.kt`에 *"`:feature:main`에 있어 이 모듈에서 못 쓴다"*는 주석이 이미 있었다 |
| `SubmitButton` → `LoadingIconButton` | `:feature:challenge:create` → `:core:ui` | 맹세 화면 CTA가 같은 스펙(52.dp/R12/loading 대체 렌더). 복붙하면 두 벌이 갈라진다. `icon: ImageVector` 파라미터 추가 |

> 이동 결과 `:feature:main`에 androidMain/iosMain 소스가 하나도 안 남아 `androidMain.dependencies` 블록을 제거했다.

### 삭제
- `feature/home/.../component/AcceptChallengeDialog.kt` — **교체**
- `feature/main/.../PlatformBackHandler{,.android,.ios}.kt` — **이동**
- `feature/challenge/create/.../SubmitButton.kt` — **이동**

### 배선 (`:domain` / `:remote` / `:data`)
- `ChallengeCreateInput` + `signature: Signature`
- `ChallengeDetail` / `ContractParty` / `Contract` / `SignatureSlotState` 신규
- `ChallengeCreateBody` · `AcceptChallengeBody` + `signature: String`
- `ChallengeDetailResponse` DTO 신규, `ChallengeDetailMapper` 신규
- `ChallengeApi.getChallengeDetail`, `ChallengeRepository.getChallengeDetail` + `acceptChallenge(… signature …)`
- `Route.Challenge.Oath(challengeId)` 신설 + `routeSerializersModule` 등록
- `MainScreen` entry 2개(`Oath` 신규, `Detail`은 `PlaceholderScreen` → 실화면), `App.kt`에 Koin 모듈 2개

---

## 계약 대비 — 내가 제기해 바뀐 것

### 🔴 `signature`가 JSON **객체**로 바인딩되고 있었다 (서버 결함)

계약 §1/§2/§3 예시는 `{"v":1,"strokes":[[[0.12,0.34],…]]}` (객체 + Float 중첩), §4.1 확정 포맷은 `{"v":1,"g":1000,"s":[[123,456,…]]}` (평탄 Int)로 **한 문서 안에 두 포맷이 공존**했다.

타입을 §4.4의 **검증 순서**에서 역산했다:

> §4.4: **1. 문자열 길이 ≤ 32 KB → 2. 파싱 가능**. *"악의적 대용량은 파싱 전에 막는 게 맞다"*

**파싱 전에 길이를 재려면 그 필드가 문자열로 도착해야 한다.** 객체면 DTO 바인딩 시점에 Jackson이 이미 파싱을 끝낸다.

**실제로 서버가 `JsonNode?`였다** (`ChallengeCommandDtos.kt:61,132`). 즉 계약에 적히고 단위 테스트로까지 고정된 순서가 **프로덕션 엔드포인트에서는 무효**였고, 32KB 상한이 막으려던 대용량이 검증기에 닿기 전에 전부 파싱되고 있었다. backend-dev 진단: *"DTO 바인딩 층이 테스트 범위 밖이었다."*

부수 효과 하나 더 — `JsonNode.toString()`은 **재직렬화**라 보낸 바이트가 그대로 저장되지 않는다. 응답의 `@JsonRawValue`도 같은 이유로 제거됐다(raw로 오면 내 쪽이 `JsonElement` → 문자열 재인코딩을 타서 키 순서·공백이 바뀔 수 있고, 그게 정확히 §4.2 무손실을 깨는 지점이다). **지금은 서버·클라 어느 쪽에도 재직렬화 지점이 없다.**

→ 요청·응답 모두 `String` 확정. 서버 169/169 passed.

### `contract.content`는 도메인까지만 오고 화면에 안 그린다
계약서 카드를 `content` 문자열이 아니라 **구조화된 필드**로 조립한다(design 명세). 따라서 backend-dev의 문구 수정 3건(조사 병기 / 완결 시 재렌더 / `24:00`)은 현재 모바일 화면에 영향이 없다. **캐시도 하지 않는다** — 진입할 때마다 새로 조회하므로 수락 전후로 `content`가 달라져도 항상 최신이다.

---

## 스펙·디자인과 다르게 간 것 (전부 사전 보고 후 승인)

### 1. design §4.4 "부분 렌더" 완화책 제거 — **본체는 유지**
전체 화면 로딩 1회로 간다. **챌린저 서명을 계약서 카드 안에 먼저 보여준다는 §4.4 본체는 그대로 구현했다.**

부분 렌더는 **다이얼로그**(홈 위에 떠서 목록 항목을 그대로 넘겨받음)를 전제로 한 완화책인데, T-D1이 전체 화면 별도 라우트로 승격하면서 그 전제가 사라졌다. 이 앱 라우트는 `Detail(challengeId: Long)`처럼 **id만 싣는 게 관례**고, 목록 8필드를 백스택에 직렬화하면 라우트가 도메인 모델에 묶인다.

**완화책의 진짜 대가**: 홈 목록이 낡았으면(그 사이 취소·마감) 부분 렌더는 **이미 없는 챌린지의 계약서를 멀쩡히 다 그려놓고** 서명 자리만 돈다 → 사용자가 **획을 다 긋고 나서야** 실패한다. 서명은 5초 입력이 아니라 공들여 그리는 것이라 그걸 버리게 만드는 게 스피너 1회보다 훨씬 나쁘다. `deadlineText`도 홈 매핑 시점 상대시간이라 실어 나르면 이미 낡는다.

**graceful degradation은 오히려 강해졌다** — 계약서 자체를 못 그리므로 "서명 블록만 생략 + 스낵바"가 아니라 **재시도 있는 에러 화면**으로 정직하게 보인다.

### 2. 계약서 카드에 **챌린저 미션 행이 없었다** (내가 발견 → §4.6 신설)
§4.1 도식이 4행(대결 상대 / 나의 미션 / 내기 / 마감)이라 **챌린저가 무엇을 하기로 했는지가 어디에도 없었다.** 삭제 대상인 `AcceptChallengeDialog`에는 있던 정보라 **교체가 정보를 줄이는** 결과가 됐을 것이고, §4.4에서 **챌린저 서명은 보여주면서 그 서명이 보증하는 내용은 안 보여주는** 모순이었다.

원인: §4.2가 Lovable **step2 카드 보존**을 못박았는데 step2는 **챌린저 시점**이라 그 행이 없는 게 맞았고, 그 카드를 상대 화면에 재사용하면서 **비어 있어야 할 이유가 사라진 자리가 그대로 빈 채** 넘어왔다. (design-bridge 확인 결과 **Lovable `oath.tsx` 프리뷰엔 이미 5행으로 들어가 있었다** — 문서만 낡았던 것이다.)

**`null`의 의미가 필드마다 다르다**: `myMission`의 `"—"`는 *"지금 쓰는 중이라 아직 비었다"*라 **자리를 지켜야** 하고, `opponentMission`의 부재는 *"이 시점엔 존재할 수 없다"*라 **행 자체를 뺀다.** `"—"`로 통일하면 챌린저 step에 영원히 안 채워지는 빈 칸이 남는다.

### 3. 상세 화면을 `ContractCard` + `footer`로 만들었다 (§3.1 조정)
§3.1은 `내기` + 서명 2-up만 있는 **별도 카드**였다. 대신 맹세 화면들과 **같은 `ContractCard`**를 쓰고 서명 2-up을 §4.4와 같은 `footer` 슬롯에 넣었다.

§3.1의 요소는 하나도 안 빠졌고(내기 / 구분선 / `서명` 라벨 / 2-up / `spacedBy 12.dp` / 박스 아래 4.dp 라벨) **미션 2행과 마감이 더해졌다.** 이 화면의 목적이 *"내가 서명한 그 계약서를 다시 본다"*인데 서명할 때 본 카드와 모양이 다르면 같은 문서로 안 읽힌다. §3.1대로 `내기`만 있는 박스를 따로 두면 **내기가 두 번** 나오기도 한다.

### 4. 모듈 2개 신설 (design §7 #4가 내 결정으로 남긴 건)
`create`에 합치면 **"create" 모듈이 수락 경로를 소유**한다. 챌린저 맹세 step은 위저드 상태기계 안, 상대 맹세 화면은 홈에서 진입하는 독립 라우트 — **생애주기가 다르다.** 공유물(`ContractCard` / `SignatureField` / `SignatureSlot` / `LoadingIconButton`)을 `:core:ui`에 두면 합칠 이유가 남지 않는다.

---

## 설계 판단 기록

### 🔴 서명 캔버스는 **스크롤 영역 밖 고정 슬롯**
전체 화면 승격의 **존재 이유**다. `verticalScroll` 안에 두면 드래그가 "획 긋기 vs 부모 스크롤"로 모호해지고, 캔버스가 제스처를 완전 소비하게 하면 그 영역에서 화면 스크롤이 죽어 IME가 올라왔을 때 CTA에 도달 못 한다.

- 맹세 화면(입력) — 계약서·미션 입력은 `weight(1f).verticalScroll`, **서명란 + CTA는 고정**
- 상세 화면(읽기) — `SignatureView`에 `pointerInput`이 없어 전체를 `verticalScroll`로 감싸도 된다. **입력 화면과 의도적으로 다르다**

### 🔴 불변식은 파라미터로 열지 않는다
`SignatureCanvas` / `SignatureView`가 **종횡비 2:1 · 획 굵기(폭의 0.9%, 최소 1.5dp) · 가장자리 인셋**을 내부에서 강제한다. 상수는 `internal`이라 호출부가 손댈 수 없고, **호출부는 폭만 정한다.**

**인셋은 clamp까지 끝난 실제 굵기에서 뽑는다** — 상세 박스(158×79dp)에서 비율(0.9%) 기반이면 `1.422/2 = 0.711dp`인데 실제는 `0.75dp`로, **0.039dp 모자라 여전히 잘린다.** 수집과 렌더가 `signatureInsetPx` / `toOffset` / `toSignaturePoint` **한 벌**을 공유해서 한쪽만 고치는 게 구조적으로 불가능하다.

`SignatureCodecTest` **18/18이 무변경**인 것이 인셋 작업이 렌더 좌표계만 건드리고 **저장 좌표계는 안 건드렸다**는 증거다.

### 🔴 실패를 정상 상태로 위장하지 않는다 — `SignatureSlotState`
`signedAt`은 있는데 서명 디코드가 실패한 조합을 **"서명 대기 중"으로 그리면 거짓말이다 — 저 사람은 서명했다.**

```
signedAt == null                      → NOT_SIGNED   "서명 대기 중"
signature != null                     → SIGNED       획 렌더
signedAt != null && signature == null → UNREADABLE   "서명을 불러오지 못했어요"
```
플래그를 새로 두지 않고 **두 필드의 조합에서 파생**시켰다. 시각은 같은 dashed로 두고 **문구만** 가른다 — 사용자가 "여기 서명이 안 보인다"는 언어를 한 번 배우면 둘 다에 통하고, 정작 구분이 필요한 건 문구뿐이다.

`datetime-model-migration`의 `Instant.DISTANT_PAST` 센티널이 파싱 실패를 "이미 만료된 카드"로 위장했던 것과 **같은 계열**이라 같은 원칙을 적용했다. backend-dev 확인: 서명과 `signedAt`은 항상 같은 저장에서 함께 채워지므로 **이 조합이 나오면 서버 버그**다.

### 🔴 관점을 모를 때는 역할 그대로 보여준다
API는 `challenger`/`opponent`를 **역할 그대로** 준다. 상세 화면이 "나/상대"로 뒤집으려면 `UserInfoRepository`(CACHE_FIRST)의 `userId`가 필요한데, **캐시가 비었고 네트워크가 실패하면 판정이 불가능하다.**

| 상황 | 왼쪽 라벨 | 오른쪽 라벨 | 미션 행 라벨 |
|---|---|---|---|
| 내가 challenger | `나` | `{opponent}` | `나의 미션` |
| 내가 opponent | `나` | `{challenger}` | `나의 미션` |
| **판정 불가** | `{challenger}` | `{opponent}` | `{challenger}의 미션` |

**챌린저를 "나" 자리에 놓으면 계약서를 잘못 읽게 만든다** — 라벨은 "나"인데 실제로는 상대 서명이다. §3.2에서 합의한 "디코드 실패를 '대기 중'으로 그리면 거짓말"과 **같은 종류의 거짓말**이다.

`myLabel`과 `myMissionLabel`을 **같은 `if` 안에서 함께** 계산한다 — 따로 두면 나중에 한쪽만 고쳐 다시 어긋난다. 테스트도 **한 케이스에서 두 값을 함께 단언**한다. `userInfo` 조회 실패로 스낵바를 띄우지는 않는다(사용자가 할 수 있는 게 없고 화면은 정상 동작한다).

### 🔴 홈 갱신 — 새 장치를 만들지 않고 **테스트로 고정**했다
예전엔 수락이 홈 ViewModel 안이라 성공 후 `reload()`를 직접 불렀다. 이제 맹세는 별도 라우트라 그 호출이 사라진다.

**그래도 갱신된다** — `uiState`가 `SharingStarted.WhileSubscribed(0)`이고 맹세 화면이 push되면 홈 컴포지션이 dispose돼 구독자가 0이 된다. 돌아와 재구독하면 upstream이 재시작되고 `refreshTrigger.onStart { emit(Unit) }`가 다시 발화한다.

**맹세 성공 후 화면 반영이 통째로 이 동작 하나에 걸려 있는데 테스트가 없었다.** `구독이 끊겼다 다시 붙으면 목록을 재조회한다`를 추가하고, 왜 존재하는지를 KDoc과 `uiState` 선언부 주석에 남겼다 — *"이 동작이 깨지면 수락 후에도 받은 도전장이 그대로 남는다."*

### 이탈 확인은 **dirty일 때만**
미션 입력이 있거나 획 ≥ 1이면 확인, clean이면 즉시 나간다. **제출 중에는 이탈 자체를 막는다.**
**제출 실패 시 화면을 닫지 않고 미션·서명을 보존한다** — `AcceptChallengeDialog`는 실패 시 닫았지만 의도적으로 다르다. 공들여 그린 서명을 버리는 비용이 너무 크다.

### 유효 서명 = **획 ≥ 1개**
점 개수 하한이나 바운딩 박스 같은 추가 조건을 발명하지 않았다. 서버 검증(§4.5)과 **정확히 같은 규칙**이어야 클라 통과 → 서버 거부가 안 생긴다.

### 자정 경계 — 서명 화면은 이미 **서버 값**을 쓰고, 게다가 **날짜를 표시하지 않는다** (실측)

backend-dev가 제기한 건: 위저드 힌트가 **클라 시계**로 `"7/28 24:00"`을 만드는데 `challengeDate`는 **서버가 요청 도착 시점**에 정하므로, `23:59:5x`에 서명하면 계약서에 **틀린 날짜가 박제**될 수 있다.

**서명이 일어나는 두 화면은 이미 서버 값을 쓴다:**

| 위치 | 출처 | 표시 |
|---|---|---|
| `OathViewModel.kt:136` (상대 맹세) | `ChallengeDetail.deadline` ← `GET /challenges/{id}` | `toRelativeKoreanString` |
| `ChallengeDetailViewModel.kt:110` (상세) | 동일 | 동일 |
| `OathStep.kt:65` (챌린저 맹세 step) | `kstDeadlineHintText` (**클라 시계**) | `"7/28 24:00"` |

**날짜가 실제로 나오는 곳은 챌린저 step 하나뿐**이고, 그건 생성 **전**이라 서버 값이 존재하지 않는다 — pm-lead 분석대로 구조적으로 적용 불가다. 백로그 항목으로 남는다.

#### 앞의 두 화면이 날짜를 안 쓰는 이유 — **위험해서가 아니라 필요 없어서다**

> 2026-08-03 backend-dev 정정. 내 초안이 *"날짜를 넣으면 갈릴 대상이 생긴다"*로 읽히게 썼는데 **그 두 화면에는 해당하지 않는다.**

두 화면은 `GET /challenges/{id}`의 `deadline`을 쓰고, **그건 서버가 계약서 본문을 렌더할 때 쓴 값과 같은 출처**다. 거기서 날짜를 뽑으면 계약서와 어긋날 수가 없다 — **자정 경계와 무관하다.**

날짜를 안 쓰는 진짜 이유는 두 가지다:
1. 홈 카드·받은 도전장이 전부 상대시간이라 **날짜를 넣으면 앱 전체 일관성이 깨진다**
2. 서명 화면에서 알고 싶은 건 "언제까지냐"보다 **"얼마나 남았냐"**다

**즉 못 하는 게 아니라 안 하는 선택이다.** 나중에 상세에 마감 날짜를 넣자는 요구가 오면 **할 수 있다.**

#### 🔴 그때 밟을 함정 — `deadline`을 그대로 포맷하면 **항상** 하루 어긋난다

```
challengeDate = 7/28
deadline      = 7/29 00:00      ← 같은 순간, 다른 날짜
계약서 본문    = "2026년 7월 28일 24:00"
```

`deadline`의 날짜를 그냥 찍으면 **`"7/29"`** 가 나와 계약서와 하루 어긋난다 — backend-dev가 서버 템플릿에서 방금 없앤 바로 그 버그다(문구 수정 3번). 날짜가 필요하면 `deadline.date.minus(1, DAY)`로 뽑아 `"{그 날짜} 24:00"`이라야 계약서와 같아진다.

**자정 경계보다 훨씬 자주 밟는다** — 자정 경계는 초 단위 창인데 이건 **항상** 틀린다.

---

## 실서버 wire 검증 (2026-08-03, 서버 재기동 후)

backend-dev가 남긴 **`challengeId = 18`** (테스터3 → 테스터2, `IN_PROGRESS`, 양측 서명 완료)로 **실서버 응답을 직접 받아** 내 DTO·매퍼·코덱에 통과시켰다.

```
POST /api/v1/auth/test-login {"testUserNo":3}  →  200
GET  /api/v1/challenges/18                     →  200
```

**받은 응답이 계약과 정확히 일치했다:**

| 항목 | 실측 |
|---|---|
| `challengerSignature` / `opponentSignature` 타입 | **`str`** — 객체 아님 |
| 서명 포맷 | `{"v":1,"g":1000,"s":[[123,456,130,460],[700,200,705,210]]}` — 평탄 Int |
| `*SignedAt` | `"2026-08-03 13:37:12"` — `yyyy-MM-dd HH:mm:ss` |
| `challenger` / `opponent` | **역할 그대로** (뒤집히지 않음) |
| 미서명 필드 | `null` (`PENDING` 구간에서 확인) |

### 🔴 손으로 쓴 픽스처로는 못 잡는 층을 테스트로 고정했다

`ChallengeDetailMapperTest` 8건이 이미 있었지만 **전부 내가 쓴 픽스처**다 — **내가 믿는 형태를 검증하지, 서버가 실제로 보내는 형태를 검증하지 않는다.** 이 프로젝트는 방금 정확히 그 함정을 밟았다(서버가 요청 `signature`를 `JsonNode`로 바인딩하는데 **단위 테스트는 초록**이었다 — DTO 바인딩 층이 테스트 범위 밖).

→ **`ChallengeDetailWireFixtureTest` 8건 신규.** 실서버 응답 본문을 **한 글자도 안 바꾸고** 픽스처로 박았다. `Json` 설정은 `KtorfitModule.provideJson()`을 복제했다 — 파싱 조건이 어긋나면 테스트가 초록이어도 런타임을 보장하지 못한다.

**핵심 단언 — 바이트 왕복:**
```
SignatureCodec.encode(SignatureCodec.decode(서버가_돌려준_문자열)) == 서버가_돌려준_문자열
```
**서버가 저장·반환하는 문자열이 내 코덱 출력과 바이트 단위로 같다는 증명이다.** 다르면 앱이 다시 저장하는 순간 서버 데이터 표현이 바뀐다.

평탄 배열의 **홀짝이 밀리는지**도 좌표로 직접 고정했다 — 첫 획이 `(123,456) → (130,460)`, 둘째 획이 `(700,200)`.

### ✅ off-by-one 함정이 실측으로 확인됐다

```
deadline               = "2026-08-04 00:00:00"
contract.content 본문   = "· 마감: 2026년 8월 3일 24:00"
challengeDate          = "2026-08-03"
```
**`deadline`의 날짜(8/4)와 계약서 본문의 날짜(8/3)가 다르다.** 위 "자정 경계" 절에서 backend-dev가 경고한 그대로이고, `deadline.date.minus(1, DAY)`가 `challengeDate`와 일치하는 것도 확인됐다. **추정이 아니라 실 데이터로 굳었다.**

### 남은 것 — 실기 없이는 못 닫는다
wire 계층은 닫혔다. **화면 계층(종횡비·인셋 육안 / iOS `pointerInput`)은 여전히 실기가 필요하다.**

---

## 🔴 실기 검증 (#23) — **버그 1건 발견. 서명 캔버스가 동작하지 않는다**

**실기**: Galaxy S25 Ultra (SM-S948N) / Android 16 (API 36) / 1440×3120 @600dpi. 실서버(`172.30.1.63:8080`) 연동.

### 증상 — 획당 점이 **1개만** 기록된다

캔버스를 가로질러 스와이프해도 **시작점 하나짜리 점**만 남는다. 느리게(2.5초) 해도 같고, 3회 재현했다.

**나머지 상태 전이가 전부 정상이라 눈에 잘 안 띈다:**
dashed·안내 문구 제거 ✅ / "다시 그리기" 노출 ✅ / **CTA 활성화 ✅**

→ **점 1개도 "획 ≥ 1"이라 사용자가 점만 찍힌 계약서를 제출할 수 있다.**

### 원인 — `SignatureCanvas.kt:86-88`, consume 순서

```kotlin
change.consume()                    // 86
if (!change.pressed) break
if (change.positionChanged()) {     // 88  ← 항상 false
    activeStroke.extend(...)        //      ← 한 번도 실행되지 않는다
}
```

Compose의 `positionChange()`는 **이미 consume된 change에 `Offset.Zero`를 돌려준다.** 따라서 `consume()` 뒤의 `positionChanged()`는 **항상 `false`**고, 획에는 `begin()`이 넣은 DOWN 지점 1개만 남는다.

### 인젝션 artifact가 아니라는 판별

`adb input swipe`를 못 믿어서 대조 실험을 했다:
```
같은 방식으로 스크롤 영역 스와이프  →  변화 픽셀 58,777 → 정상 스크롤
```
**MOVE 이벤트는 Compose에 도달한다. 캔버스가 받고도 버린다.**

### 🔴 218건이 전부 초록인데 기능이 동작하지 않았다

- `SignatureCoordinateTest` 4건은 **좌표 변환 수학**만 본다
- `SignatureCodecTest` 18 / `SignatureTest` 4 / `ChallengeDetailMapperTest` 8 / `ChallengeDetailWireFixtureTest` 8 — 전부 **이미 만들어진 `Signature` 객체**에서 출발한다
- **제스처 루프를 구동하는 테스트가 0건**

**실서버 데이터도 반증이 못 됐다** — `challengeId=18`의 서명은 backend-dev가 API로 직접 만든 것이라 **앱을 거치지 않았다.** 위 절의 "바이트 왕복 통과"는 사실이지만 **앱이 만든 서명에 대한 검증은 아니었다.**

> **`JsonNode` 건과 정확히 같은 구조다** — 서버는 "검증기를 직접 부르니 DTO 바인딩 층이 빠졌고", 모바일은 "매퍼·코덱을 직접 부르니 **제스처 층**이 빠졌다". **둘 다 자기가 만든 입력으로 자기 코드를 검증했다.**

### 제안 (승인 대기)
```kotlin
val moved = change.positionChanged()   // consume 전에 판정
change.consume()
if (!change.pressed) break
if (moved) { activeStroke.extend(...) }
```
+ **회귀 테스트** — `runComposeUiTest` + `performTouchInput { swipe(...) }`로 *"스와이프하면 점이 2개 이상 쌓인다"* 고정. `:core:ui`에 Compose UI 테스트 선례 0건이라 의존성 추가가 따라온다.

### 실기에서 **정상 확인된** 항목

| 항목 | 결과 |
|---|---|
| 위저드 progress **3칸** | ✅ |
| step2 CTA `"다음"` (기존 `"챌린지 걸기"`) | ✅ |
| 맹세 step 계약서 **4행** (상대 미션 없음, §4.6) | ✅ |
| **캔버스 종횡비** | ✅ **정확히 2.0000** — 픽셀 실측 1278×639px = **340.8 × 170.4dp** |
| 빈 상태 dashed + `"여기에 서명하세요"` | ✅ |
| `"다시 그리기"` 획 0개일 때 미노출 | ✅ |
| 상세 양측 서명 렌더 + 관점 라벨 `"나"` / `"테스터3"` | ✅ |
| 상세 계약서 **5행** | ✅ |
| debug 계정 라벨(`테스터2`) 노출 | ✅ |

**인셋(가장자리 클리핑)은 확인 불가** — 획이 점 하나뿐이라 가장자리까지 그릴 수 없다. **버그 수정 후에만 검증된다.**

### 검증 중 만든 테스트 데이터
`테스터1 ↔ 테스터2` 친구 관계를 API로 생성(실사용 데이터 무관). `challengeId=18`은 **조회만** 했고 변경하지 않았다.

---

## 🔴 실기에서 나온 버그 3건 — 전부 수정·재검증 완료

### 버그 1. 서명 캔버스가 획당 점을 1개만 기록 (`SignatureCanvas.kt:86-88`)

`change.consume()` 뒤에 `change.positionChanged()`를 불렀다. Compose는 **consume된 change에 `Offset.Zero`를 돌려주므로** 판정이 항상 `false`가 되어 `extend()`가 한 번도 실행되지 않았다.

```
수정 전: 획 픽셀    97개 (점 하나)
수정 후: 획 픽셀 13,701개 (선)
```
수정: `val moved = change.positionChanged()`를 `consume()` **앞으로**.

**인젝션 artifact가 아님을 대조 실험으로 확인** — 같은 `adb input swipe`로 스크롤 영역은 정상 스크롤(변화 픽셀 58,777). MOVE는 도달하고 캔버스가 받고도 버렸다.

### 버그 2. 맹세 화면이 **100% 열리지 않음** — `ContractPartyDto.mission` 비-nullable

```
JsonDecodingException: Unexpected 'null' value ... at path: $.data.opponent.mission
```
`PENDING`은 상대 미션이 아직 없어 서버가 **명시적 `null`**을 보내는데 타입이 non-nullable이었다. **맹세 화면은 오직 `PENDING`만 연다** → 항상 실패.

> ⚠️ `kotlinx.serialization`의 기본값(`= ""`)은 **키 누락**만 덮는다. **명시적 `null`은 non-nullable 타입에서 그대로 예외다.**

수정: `ContractPartyDto.mission` / `ContractParty.mission` / detail State의 두 미션을 `String?`로. **`orEmpty()`로 뭉개지 않았다** — "없음"과 "빈 문자열"을 합치면 화면이 빈 행을 그린다.

### 버그 3. 🔴 역직렬화 실패가 **조용한 무한 로딩**이 된다 (프로젝트 전역) — ✅ 수정

`ApiResult.kt`에서 **`UnknownApiError`만 `onError`를 호출하지 않았다**(나머지 3개 분기는 호출). 그래서 버그 2가 에러가 아니라 **영원한 스피너**로 나타났다.

**내가 만든 게 아니라 이미 있던 결함이다.** 지금까지는 Flow 기반이라 `combine` 함정으로 나타났고, suspend+콜백인 `getChallengeDetail`에서 처음 "완전히 멈춤"으로 드러났다.

**수정**: 해당 분기에 `onError("요청을 처리하지 못했어요")` 한 줄 추가. 다른 3개 분기 무변경.

**문구 근거** — pm-lead가 `"일시적인 오류"`를 기각했고(역직렬화 실패는 일시적이지 않아 재시도를 오도한다), 제안된 `"화면을 불러오지 못했어요"`도 채택하지 않았다: **호출부 24곳 중 상당수가 조회가 아니라 mutation**(챌린지 신청/수락/거절/취소, 친구 요청/수락/거절/취소, 로그인)이라 "화면을 불러오지 못했어요"는 틀린 말이 된다. `"요청을 처리하지 못했어요"`는 **조회·변경 양쪽에 맞고 재시도를 오도하지도 않는다.**

**영향 범위**: `suspendOnFailureWithErrorHandling` 호출부 **24곳 / 6개 RepositoryImpl** (Challenge 7 · Friends 8 · Login 3 · ActiveChallenge/UserInfo/Record 각 2). 이 지점들이 이제 조용히 멈추는 대신 스낵바를 띄울 수 있게 된다.

**기존 동작을 고정한 테스트: 0건** — `UnknownApiError`를 참조하는 테스트가 repo 전체에 없었다. **교체분 없음.**

**회귀 방지**: `:remote:network`에 `commonTest` 신설(이 모듈 최초) + `ApiResultTest` **7건** — 4개 Failure 분기 각각 `onError` 호출 / `Success`는 미호출 / 최대 1회 호출 / `UnknownApiError` 문구 고정.

### 🔴 왜 223건이 전부 초록인데 두 버그가 살아 있었나

| 버그 | 왜 안 잡혔나 |
|---|---|
| 1 | **제스처 루프를 구동하는 테스트가 0건.** 모든 서명 테스트가 **이미 만들어진 `Signature` 객체**에서 출발한다 |
| 2 | wire fixture를 `challengeId=18`(**IN_PROGRESS**)에서 떴는데 그게 **유일하게 동작하는 상태**였다. 화면이 실제로 여는 `PENDING`은 한 번도 안 지나갔다 |

**버그 2는 내가 어제 "손으로 쓴 픽스처의 사각지대를 닫았다"고 보고한 그 테스트가 놓친 것이다.** 실서버에서 떴다는 사실이 **대표 응답을 떴다**는 뜻은 아니었다. → `ChallengeDetailWireFixtureTest`에 **PENDING 픽스처 5건 추가**(총 13건), 두 상태를 모두 고정했다.

---

## ✅ 실기 재검증 결과 (수정 후)

### 측정으로 확인한 것

| 항목 | 측정값 |
|---|---|
| **캔버스 종횡비** | **2.0000** (1290×645px = 344.0×172.0dp) |
| **상세/맹세 반폭 렌더 종횡비** | **2.0000** (570×285px = 152.0×76.0dp) |
| 🔴 **B4 입력↔렌더 동형성** | 정규화 잉크 bbox 차이 **≤ 0.0038** (2.26× 배율 차이에도) |
| 🔴 **B3 인셋** | 최상단 가장자리 획 **두께 12px** (예상 굵기 11.5px), **박스 밖 픽셀 0개**. 인셋 없으면 절반(≈6px)만 보여야 한다 |

**B4는 육안이 아니라 픽셀 스캔으로 쟀다.** 크롭 이미지 2장도 시각적으로 동일하다.

### 전체 흐름 왕복 (실서버)

```
테스터1 생성(서명 3획 164점) → 테스터2 수락(서명 1획 71점)
  → status = IN_PROGRESS,  isFinalized = true,  양측 서명 저장
  → 홈 자동 갱신: 받은 도전장 2건→1건, 진행 중 1개→2개
  → 상세: 「나」/「테스터1」 양측 서명 렌더, 관점 정확
```

**`is_finalized = true`가 된 시점에만 `IN_PROGRESS`로 전환**된다는 핵심 수용 기준이 실기+실서버로 확인됐다.

**홈 자동 갱신이 실기에서 확인됐다** — 명시적 reload 호출 없이 `WhileSubscribed(0)` 재구독만으로 목록이 갱신된다. `구독이 끊겼다 다시 붙으면 목록을 재조회한다` 테스트가 지키는 동작이 실제로 그것이다.

### 체크리스트 판정

| | 항목 | 결과 |
|---|---|---|
| A1~A7 | 서명 무관 전 항목 | ✅ |
| B1 | 선이 그어진다 | ✅ 13,701px |
| B3 | 획 끝이 잘리지 않는다 (인셋) | ✅ 12px / 박스 밖 0 |
| B4 | 입력↔렌더 같은 모양 | ✅ Δ ≤ 0.0038 |
| B7 | 챌린저 서명 선노출 (§4.4) | ✅ |
| B8 | dirty만 이탈 확인 (T-M3a) | ✅ clean 즉시 이탈 / dirty 다이얼로그 |
| B9 | 실패 시 화면 유지 + 서명 보존 | ✅ 중복 가드 실패로 우연히 확인 |
| **B2·B5·B6** | 지연 체감 / 각짐 / 높이 충분 | ⬜ **주관 판단 — 사용자·디자이너 몫** |
| **C** | iOS 실기 | ⬜ **기기 없음 — 미검증** |

**시뮬레이터로 대체하지 않았다.** iOS는 미검증으로 남긴다.

---

## Working tree 상태

- **작업 브랜치**: `main` (현재 체크아웃된 브랜치. 새로 만들지 않았다)
- **직전 커밋**: `6a3de0a refactor: button 디자인시스템 정리`
- **변경분 전량 unstaged/untracked 그대로** — 커밋·푸시·PR **없음**. 사용자 처리 영역
- `git status --short` 55 entries (M 37 / D 4 / ?? 14)

---

## 사용자 실기 체크리스트 (#23)

> ⚠️ **B 구간은 서명 캔버스 버그 수정 전에는 확인할 수 없다.** A 구간은 지금 그대로 확인 가능하다.
> 준비: `테스터1`↔`테스터2` 친구 관계 생성 완료. 로그인 화면 하단 **개발용** 버튼으로 계정 전환.

### A. 지금 확인 가능 (서명 무관)

| # | 화면 | 볼 것 | 잘못된 신호 |
|---|---|---|---|
| A1 | 로그인 | 하단 `개발용` 테스터1~3 버튼 | debug인데 안 보이면 게이트 오류 |
| A2 | 홈 | 상단 우측 **현재 계정 닉네임** | 계정을 바꿔도 그대로면 캐시 미갱신 |
| A3 | 새 챌린지 | 진행 바가 **3칸** | 2칸이면 맹세 step 미반영 |
| A4 | step2 | CTA 문구가 **`다음`** | `챌린지 걸기`면 옛 빌드 |
| A5 | 맹세 step | 계약서 **4행** (대결 상대/나의 미션/내기/마감) | **상대 미션 행이 있으면 오류** — 그 시점엔 존재할 수 없다 |
| A6 | 맹세 step | 캔버스 dashed + `여기에 서명하세요`, **`다시 그리기` 없음**, CTA **비활성** | 획 0인데 `다시 그리기`가 보이면 오류 |
| A7 | 상세 (`id=18`) | 계약서 **5행** + 서명 2칸 + 라벨 `나` / `테스터3` | 라벨이 뒤바뀌면 관점 판정 오류 |

### B. 🔴 서명 버그 수정 후에만 가능

| # | 볼 것 | 잘못된 신호 |
|---|---|---|
| B1 | 캔버스에 손가락으로 **선을 긋는다** | **점만 찍히면 이 버그가 안 고쳐진 것** |
| B2 | 획이 **손가락을 실시간으로 따라오는가** (지연 체감) | 끊기거나 뒤처지면 성능 이슈 |
| B3 | 가장자리까지 그었을 때 **획 끝이 둥근가** | **평평하게 잘리면 인셋 부족** |
| B4 | 🔴 **입력 캔버스(≈341dp) ↔ 상세 2-up(≈158dp)에서 같은 서명이 같은 모양인가** | **세로로 눌려 보이면** `y` 정규화/비율 어긋남 |
| B5 | 곡선이 **부드러운가, 각져 보이는가** | 각지면 솎아내기 임계(`MIN_POINT_DISTANCE=3`) 하향 필요 → design-bridge 회신 |
| B6 | 캔버스 높이 **170dp가 서명하기에 충분한가** | 좁으면 design 재조정 |
| B7 | 맹세 화면(수락)에 **챌린저 서명이 먼저 보이는가** (§4.4) | 안 보이면 조회 실패 또는 배선 누락 |
| B8 | 미션/획을 넣고 **뒤로가기 → 확인 다이얼로그**, 아무것도 안 하고 뒤로가기 → **바로 나감** (T-M3a) | clean인데 물으면 순수 마찰 |
| B9 | 제출 **실패 시 화면이 닫히지 않고 서명이 보존되는가** | 닫히면 `AcceptChallengeDialog` 동작이 남은 것 |

### C. iOS — **실기기 필요**
`pointerInput` 드로잉은 KMP 선례 0건이다. **시뮬레이터 마우스 드래그는 손가락과 다르므로 시뮬레이터 결과를 "검증 완료"로 적지 않는다.** B1~B6을 iOS 실기기에서 반복해야 닫힌다.

---

## 미해결 이슈

- [ ] **🔴 실서버 미검증** — 서버가 구버전으로 떠 있다. `soul-oath.sh` 하네스는 준비됨. 사용자 재기동 시 서버측 + 모바일 실연동을 함께 본다 (#22)
- [ ] **🔴 서명 캔버스 iOS 실기 미검증** — Compose `pointerInput` 드로잉은 KMP에서 **선례 0건**이다(design-bridge 실측). 지연·좌표 정확도는 실기로만 확인된다. **시뮬레이터 마우스 드래그는 손가락과 다르다.** 단위 레벨(좌표 변환 4건 / 왕복 무손실 18건)은 고정했으나 대체되지 않는다
- [ ] **🟡 종횡비·인셋은 눈으로 봐야 한다** — 좌표를 `x/width`·`y/height`로 **각각** 정규화하므로 비율이 어긋나도 **왕복 무손실 테스트는 통과하고 화면에서만 찌그러진다.** 입력 화면과 상세 화면에서 같은 서명이 같은 모양인지 실기 확인 필요
- [ ] **🟡 솎아내기 임계(`MIN_POINT_DISTANCE = 3`)의 시각 영향** — 실기에서 획이 각져 보이면 낮추고 design-bridge에 회신하기로 돼 있다
- [ ] **🟢 `ChallengeDetailUiState.Data.isFinalized`가 렌더되지 않는다** — 표시 위치 명세가 없어 배지를 임의로 만들지 않았다. 양측 서명이 다 그려진 것 자체가 완결의 시각적 증거라 중복이기도 하다
- [ ] **🟢 상세 화면 범위가 계약서까지다** — 인증 상태·사진 등은 카메라 인증 feature 몫(spec 비범위)
- [ ] iOS 유닛 테스트 미실행 (기존 관행)

## 참고 — 기존 문서의 숫자 불일치 1건

`dev-test-login/summary.md`가 모바일 **148/148**로 적었는데, 같은 방식(`@Test` 줄 수)으로 센 `HEAD` 값은 **144**다. `git status`상 삭제된 테스트 파일이 없고 tracked 테스트 파일 3개 중 삭제가 있는 건 `HomeViewModelTest`(의도적 교체 5건)뿐이라, **회귀가 아니라 이전 문서의 집계 방식 차이**로 보인다. 이번 보고의 `144 → 210` 산술은 **같은 방식으로 양끝을 재서** 내부적으로 일관된다.
