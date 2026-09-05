# Mobile Report — challenge-forfeit

- **작성**: 2026-09-05, mobile-dev(forfeit-mobile)
- **입력**: [spec.md](./spec.md) §4 T-M1~T-M4 · [api-contract.md](./api-contract.md) (`confirmed` 2026-09-05)
- **디자인**: 없음 — Lovable 정본에 기권 UI **0건**(pm 실측). 기존 토큰·패턴으로 구현하고 이탈분 전부를 §디자이너 확인 목록에 등재

## 구현 요약

기권 진입점·확인 다이얼로그·결과 표시·알림 배선을 넣었다. 33개 파일 변경 + 3개 신규(962 insertions).

**T-M1 기권 진입점 + 확인 다이얼로그** — 상세 하단에 `ForfeitText`(텍스트 1줄, `error`), 탭하면 `ConfirmDialog(destructive = true)`. 확인 없이는 요청이 나가지 않는다.

**T-M2 기권 표시** — `forfeitedBy` 를 상세에 받아 VS 헤더 결과 문구 아래 한 줄("내가 기권했어요" / "우건님이 기권했어요")로 구분. 관점 판정은 ViewModel 이 끝내고 화면은 그린다.

**T-M3 알림 배선** — `PushEvent.ChallengeForfeited` + 트레이 딥링크(상세) + **목록 탭 이동 없음** + 목록 아이콘·색.

**T-M4 테스트** — 아래 숫자.

### 🔑 T-M1 의 핵심 설계 — 배타성을 테스트가 아니라 **타입**으로 고정했다

pm 지시는 *"'다시 찍기' 와 동시에 보이지 않게 하고 테스트로 고정하라"* 였다. 실측해 보니 상세에 이미
`MyMissionSlot` 이라는 **단일 `when`** 이 있고 두 진입점이 그 `when` 의 **서로 다른 가지**였다.

```kotlin
// ChallengeDetailState.kt
val canForfeit: Boolean get() = myMissionSlot == MyMissionSlot.VERIFY_CTA
```

한 `when` 의 값이 하나뿐이므로 **"둘이 동시에 보이는 조합" 이 표현 불가능**해진다. 새 `if` 0개,
새 조건식 0개 — spec §3.1 *"별도 가드를 추가하지 마라"* 와도 정합한다. pm-lead 승인
(*"테스트는 틀린 조합이 났을 때 알려 주는 장치고, 네 안은 그 조합이 표현 불가능하다"*).

⚠️ **그래서 그 테스트의 성격이 다르다** — 회귀 감시가 아니라 *"이 파생이 실제로 그 뜻인지"* 를
상태공간 전수로 확인하는 것이다. 테스트 KDoc 에 그 구분을 적었다. 안 적으면 나중에 `canForfeit` 를
독립 조건식으로 바꿔도 **테스트는 통과하는데 보증만 사라진다.**

### 🔑 실패도 성공과 같은 경로로 — 재조회

기권 요청은 **성공하든 실패하든 상세를 다시 조회**한다.

- 성공 응답 body 를 안 읽는 이유: 상세 화면을 세우는 경로가 두 벌이 되면 갈리는 날 컴파일러도
  테스트도 못 잡는다(spec §0.1 과 같은 축). `forfeitedBy` 도 어차피 재조회로만 온다.
- 실패에도 재조회하는 이유: 서버 거부 사유 대부분(*이미 끝났다 / 이미 인증했다*)이 **화면 스냅샷이
  낡았다**는 뜻이다. 재조회하면 사라졌어야 할 진입점이 **그 자리에서 사라진다** — 다이얼로그 없이.

## 사용한 모바일 레포 스킬

- `modify-feature`: 기존 상세 화면에 액션·필드 추가. 영향 레이어 분석 → 레이어별 수정 순서를 따랐다
- `design-system`(자동): Compose UI 작성 시 토큰·Preview 필수 규칙 적용
- 코드 편집은 전부 `cd challenge-app && claude -p` **child 위임**(4회). 분석·협의·빌드는 본체

## 변경된 파일 (33 변경 + 3 신규)

**신규**
- `remote/model/.../challenge/ForfeitChallengeResponse.kt`
- `feature/challenge/detail/.../contract/ChallengeDetailEffect.kt`
- `feature/challenge/detail/.../component/ForfeitText.kt`

**레이어별 변경**
- `:remote:model` `ChallengeDetailResponse.kt`(`forfeitedBy`)
- `:remote:api` `ChallengeApi.kt`(`forfeitChallenge`)
- `:remote:mapper` `ChallengeDetailMapper.kt`
- `:remote:datasource` `ChallengeRemoteDataSourceImpl.kt`
- `:data:datasource` `ChallengeRemoteDataSource.kt` / `:data:repositoryImpl` `ChallengeRepositoryImpl.kt`
- `:domain:model` `ChallengeDetail.kt`(`forfeitedBy`) · `ChallengeResult.kt`(KDoc)
- `:domain:repository` `ChallengeRepository.kt`
- `:core:push` `PushEvent.kt` · `PushEventRoute.kt`
- `:feature:notification` `NotificationState.kt` · `NotificationTypeVisual.kt` · `NotificationPreviewFixtures.kt`
- `:feature:challenge:detail` `ChallengeDetailState.kt` · `ChallengeDetailViewModel.kt` · `ChallengeDetailRoute.kt` · `ChallengeDetailScreen.kt` · `VsHeaderCard.kt`
- `:feature:mypage` `ArchiveChallengeCard.kt`(KDoc — 아래 §낡은 근거)
- 테스트 8개 파일 + Fake 5개(`ChallengeRepository` 에 메서드가 늘어 구현체 전부)

## 테스트 결과

🔴 **XML 직접 확인. `UP-TO-DATE` 여부를 timestamp 와 함께 적는다**(둘 중 하나만 보면 정상 증분 빌드를 stale 로 오탐한다).

| 모듈 | Android/JVM | iOS | XML 시각 | 실행 여부 |
|---|---|---|---|---|
| `:domain:model` | 4/4 | 4/4 | 23:20 | 실행 |
| `:remote:model` | 22/22 | 22/22 | 23:20 | 실행 |
| `:remote:mapper` | **135/135** | **135/135** | **23:27** | **실행**(픽스처 교체로 재실행) |
| `:remote:datasource` | 41/41 | ⚠️ 미실행 | 23:21 | 실행(Android) |
| `:core:push` | 28/28 | 28/28 | 23:21 | 실행 → 재실행 시 `UP-TO-DATE` |
| `:feature:notification` | 43/43 | 43/43 | 23:21 | 실행 → 재실행 시 `UP-TO-DATE` |
| `:feature:challenge:detail` | **69/69** | **69/69** | 23:21 | 실행 → 재실행 시 `UP-TO-DATE` |
| `:feature:challenge:oath` | 17/17 | 17/17 | 23:21 | 실행 |
| `:feature:challenge:create` | 20/20 | 20/20 | 23:21 | 실행 |
| `:feature:home` | 27/27 | 27/27 | 23:22 | 실행 |
| `:feature:mypage` | 57/57 | 57/57 | 23:22 | 실행 |
| `:data:repositoryImpl` | 15/15 | ⚠️ 미실행 | 23:22 | 실행(Android) |

- **단위 합계: Android/JVM 478/478 passed · iOS 422/422 passed. failures 0 · errors 0 · skipped 0**
- **Android 빌드: ok** (`BUILD SUCCESSFUL`)
- **iOS 빌드: ok** — 단 아래 2개 모듈의 iOS **테스트 컴파일**은 선존재 결함으로 미실행

⚠️ **`UP-TO-DATE` 4건은 stale 이 아니다.** 픽스처 교체 후 재검증에서 `:remote:mapper` 만 입력이
바뀌어 재실행됐고(23:27), 나머지는 입력 무변경이라 Gradle 이 스킵했다. timestamp 만 보면 이걸
stale 로 오탐한다 — **두 값을 같이 봐야 한다.**

### 🔴 iOS 미실행 2건 — **선존재 결함이며 내 변경과 무관**

`:remote:datasource` · `:data:repositoryImpl` 의 `compileTestKotlinIosSimulatorArm64` 가 실패한다:

```
e: LoginRemoteDataSourceImplTest.kt:37:9   Name contains illegal characters: ","
e: LoginRemoteDataSourceImplTest.kt:96:9   Name contains illegal characters: ",()"
e: UserInfoRepositoryImplTest.kt:34:9      Name contains illegal characters: ","
```

Kotlin/Native 가 **백틱 테스트 이름의 `,` · `(` · `)`** 를 심볼명으로 쓰지 못한다.

**선존재 근거 (실측 2단)**
1. **착수 전 베이스라인**에서 이미 동일하게 실패했다. 그 시점 working tree 는 주석 2파일뿐이었고
   실패한 파일들은 **무변경**이었다.
2. 실패 지점이 전부 **기존 테스트**다(`getReceivedChallenges 실패 - onError 1회, emit 0건` 등).
   이번에 추가한 `forfeitChallenge 성공 - onSuccess 호출`(485행) ·
   `forfeitChallenge 실패 - …`(509행)는 **실패 목록에 없다** — 쉼표·괄호를 피해 지었다.

🔑 **그래서 이 두 모듈의 iOS 테스트는 여태 한 번도 돈 적이 없다.** Android 만 돌리면 안 드러나고,
실패해도 아무도 보지 않는다. **고치지 않았다** — 기존 테스트 이름 다수를 바꾸는 일이라 이 feature
범위 밖이다. §미해결에 백로그 후보로 등재.

## Working tree 상태

- **작업 브랜치: `main`** (현재 체크아웃된 브랜치. 새로 만들지 않았다)
- 변경분 **staged/unstaged 그대로** 둠. **커밋·푸시·PR 생성 안 함** — 사용자 처리 영역
- 총 36개 파일(33 변경 + 3 신규)

## 🔴 디자이너 확인 목록 — 정본 이탈분 전부

Lovable 정본에 기권 UI 가 0건이라 아래는 전부 **내가 기존 토큰·패턴으로 정한 것**이다.

| # | 자리 | 정한 값 | 근거 | 대안 |
|---|---|---|---|---|
| 1 | 기권 진입점 위치 | 상세 본문 **맨 아래** | 되돌릴 수 없는 행위를 주 액션(인증하기) 옆에 두면 오탭 거리가 0. mypage 가 회원 탈퇴를 맨 아래 둔 것과 같은 판단 | 미션 카드 하단 |
| 2 | 진입점 형태 | 버튼 아님, **텍스트 1줄** | 우발적 탭을 줄이려 시각 위계를 낮춤. 경고는 다이얼로그가 맡는다(`WithdrawText` 선례) | Outlined 버튼 |
| 3 | 진입점 색 | `error` | 이 화면에서 `error` 를 쓰는 건 "패배" 헤드라인뿐인데 **둘은 같은 화면에 못 나온다**(기권 진입점은 `IN_PROGRESS`, 패배는 판정 후). 색이 비어 있고, 가장 위험한 행위가 그 색을 갖는다 | `onSurfaceVariant`(mypage 선례) |
| 4 | 기권 안내 문구 자리 | VS 헤더 결과 **아래 한 줄** | 결과가 아니라 *"어떻게 끝났는지"* 에 붙는 주석이라 헤드라인 톤 색을 쓰지 않고 `onSurfaceVariant` `medium12` 로 낮춤 | 별도 카드 |
| 5 | 알림 아이콘 | `Icons.Filled.Flag` | 기존 4종과 안 겹치고 백기(기권)를 직접 가리킴 | `HeartBroken` 등 |
| 6 | 알림 색 | `error` | 받는 사람에겐 이긴 사건이지만 **제목이 `계약 파기.`** 다. 성격이 가장 가까운 `CHALLENGE_REJECTED`(관계가 성립하지 못하고 끝남)와 맞춤 | `success`(수신자 = 승자) |
| 7 | 홈·보관함 기권 표시 | **하지 않음** | §미해결 1번 참조 |

🟡 **문구 4종은 spec §6 초안 그대로 썼다(사용자 미확정)** — 다이얼로그 제목/본문, 진입점·확인 라벨.

## 미해결 이슈

1. 🔴 **홈·보관함에 기권을 표시하지 않는다 — 결정이지 누락이 아니다.** 뒤집으면 **서버까지 되돌아간다**
   (`active`/`history` 응답에 필드 추가). ⚠️ 그리고 `forfeitedBy` 를 **그대로 추가하면 안 된다** —
   두 DTO 는 `my*`/`opponent*` **내 시점 좌표**만 쓰고 `userId` 를 하나도 싣지 않아(실측 0건)
   userId 형태는 해석이 불가능하다. `forfeitedByMe: Boolean` 같은 시점 필드가 필요하다.
2. 🔴 **`:remote:datasource` · `:data:repositoryImpl` 의 iOS 테스트가 컴파일되지 않는다**(선존재).
   백틱 이름의 쉼표·괄호. **이 두 모듈 iOS 테스트는 실행된 적이 없다.** 백로그 후보.
3. 🔴 **앱이 `ResponseCode` 의 표시 위계를 구현하지 않는다** — `onError: (String) -> Unit` 이
   레포 전체 **206곳 단일 종**이라 `code` 를 나를 통로가 없다. 서버가 기권 실패에 **705 를 3건**
   보내지만 **앱은 전부 스낵바로 그린다. 정상이고 결함이 아니다** — 백로그 등재(`9c3bf19`).
   이 feature 에서는 재조회 설계로 실질 문제가 없다.
4. 🟡 **`wireResponse` · `pendingWireResponse` 픽스처가 낡았다**(2026-08-03 캡처, `result` 키 이전 서버).
   라벨을 달았으나 **재캡처는 안 했다** — `IN_PROGRESS`·`PENDING` 두 상태로 서버 왕복 2회가 필요해
   범위 밖. 🔵 삭제하지 않은 이유: **키 부재 내성**의 증명이라 전역 `NON_NULL` 이 켜지는 날의 안전망이다.
5. 🟡 **spec §3 수용 기준의 `referencePending = false` 가 계약(`null`)과 어긋난다** — pm-lead 소관.
   계약 §3 은 정정 완료.
6. 🟡 **알림 발송은 아직 꺼져 있다** — backend 가 `NotificationMessages` 문구를 넣으면 켜진다.
   배선 완료를 회신했다(`OPPONENT_VERIFIED` 선례 절차). 기권 자체는 정상 동작한다.

## 🔴 기권이 깨뜨린 "낡은 근거" — 스윕 결과

pm 지시로 *"result 하나면 인증 상태 둘을 안다"* 류 서술을 훑었다.

- **코드 역산: 0건** — `ChallengeOutcome`/`ChallengeResult` 를 읽는 프로덕션 지점 **전수**
  (`outcomeFor` · `challengeOutcomeVisualOf` · `toHeadline`×2 · `headlineVisualOf` · 매퍼 2)가
  전부 `result → 표시` 단방향이다. **훑었고 0건**이다(안 훑은 것과 구분해 적는다).
- **주석 1건 발견·수정** — `ArchiveChallengeCard.kt` 가 *"인증 pill 을 빼도 정보가 줄지 않는다 —
  결과 4종이 양측 인증 상태를 유일하게 결정하므로"* 를 근거로 pill 을 빼고 있었다. 기권이 그
  일대일을 **승·패에서** 깬다(무·양패는 기권에서 나오지 않아 유지). **결론(pill 안 넣음)은 유지하고
  근거만 교체**했고, **무너졌다는 사실 자체를 주석에 남겼다** — 지우면 다음 사람이 옛 논거를 재발명한다.
- **`ChallengeOutcome` KDoc 1건 보강** — 역산 경고가 여전히 참이지만 기권 이후 **더 강해졌다**
  (사본일 뿐 아니라 **틀린 답**을 낸다). 한 절 덧붙였다.

## API 계약 대비 구현 차이

**없다.** 확정 계약대로 구현했다. 참고로 앱이 **소비하지 않는** 계약 항목:

- `POST /forfeit` 성공 응답의 `challengeId`·`status`·`result`·`myResult`·`completedAt` — 앱은
  성공 여부만 보고 **상세를 재조회**한다. DTO 는 계약 shape 그대로 두되 읽지 않는다
  (`RejectChallengeData` 와 같은 선례)
- `referencePending` — 앱이 `CHALLENGE_FORFEITED` 를 **타입 단계**에서 비탭으로 고정하므로 값을
  보지 않는다. `true`/`false`/`null` **3값 전부**로 비탭을 검증했다
- 실패 `code`(705×3 + 700×1) — 위 미해결 3번. 사유별 분기 없이 서버 `message` 를 그대로 띄운다
