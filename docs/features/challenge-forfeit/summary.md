# 챌린지 기권 (challenge-forfeit) — Summary

- **feature-id**: challenge-forfeit
- **완료일**: 2026-09-05
- **상태**: **implemented** — 전 범위 구현·검증 완료. 🔴 **양 레포 미커밋** + **실기 검증 0건**
- **선행**: [challenge-result](../challenge-result/summary.md)(`ChallengeVerdict`·자정 배치·전적 집계) · [soul-oath](../soul-oath/summary.md)(컨셉)
- **관계**: [ai-verification](../ai-verification/spec.md) 에서 **분할된 feature** — 의존 없음(§분할 근거)

## 구현 개요

챌린지를 **중간에 끝낼 수 있게** 했다. 이전에는 시작하면 마감을 기다리는 것 외에 끝내는 방법이
없었고, 못 하게 된 걸 이미 아는 사람도 자정까지 진행 중 카드를 들고 있어야 했다.

🔑 **사용자 결정으로 기권은 "미인증으로 친다" 가 아니라 "상대에게 승리를 준다" 는 선언이다.**
그래서 상대가 인증하지 않았어도 상대가 이긴다 — 기존 규칙이면 `BOTH_LOSE` 가 나올 자리다.
이 한 줄이 이 feature 의 전부이고, 나머지 설계는 **그 결정을 판정 규칙의 사본 없이 구현하는 방법**이다.

**마이그레이션 1건(컬럼 1개) · 새 엔드포인트 1건 · 판정 규칙 3종 변경 0.**

## 엔드포인트

| Method | Path | 내용 | 상태 |
|---|---|---|---|
| POST | `/api/v1/challenges/{id}/forfeit` | 기권 — 본문 없음, **즉시 확정** | implemented (미배포) |
| GET | `/api/v1/challenges/{id}` | 상세에 **`forfeitedBy: Long?`** 1필드 추가 | implemented (미배포) |

🔴 **`active`/`history` 에는 넣지 않았다** — [§근거 두 다리](#forfeitedby-를-상세에만-넣은-근거가-두-다리인-이유).

## 화면 / UI 변경

- **챌린지 상세** — 하단에 기권 진입점(`ForfeitText`, 텍스트 1줄, `error`) + `ConfirmDialog(destructive)`.
  노출 조건 `IN_PROGRESS` **AND 내 인증 없음**
- **챌린지 상세(결과)** — VS 헤더 결과 아래 한 줄로 *"내가 기권했어요" / "{닉}님이 기권했어요"*
- **알림 목록** — `CHALLENGE_FORFEITED` 아이콘(`Flag`)·색(`error`). 🔴 **탭 이동 없음**
- **푸시 트레이** — 탭하면 챌린지 상세. **목록과 목적지가 다른 것이 의도다**

## 테스트 결과

| | 숫자 |
|---|---|
| **백엔드** | **605/655 passed** (50 skipped = Docker 부재 상시 skip). 신규 31, **회귀 0** |
| **백엔드 실기동** | throwaway DB `challenge_forfeit_check`(18081) + 캡처용 재기동(18082) — **9항목** |
| **모바일** | **Android/JVM 478/478 · iOS 422/422** · failures 0 · errors 0 · skipped 0 |

🔴 **pm 독립 검증**: XML 직접 집계로 서버 `tests=655/failures=0/skipped=50`, 모바일 iOS 모듈별
(`detail 69` · `notification 43` · `core:push 28` · `remote:mapper 135`) **전부 일치**.
Android 가 pm 집계에서 2배로 나오는 것은 `testDebugUnitTest`·`testReleaseUnitTest` 가 같은 테스트를
두 벌 세기 때문이고 **variant 당 보고가 옳다**.

🔵 **`UP-TO-DATE` 3건은 stale 이 아니다** — 픽스처 교체 후 재검증에서 `:remote:mapper` 만 입력이
바뀌어 재실행(23:27)됐고 나머지는 입력 무변경이라 Gradle 이 스킵(23:21)했다. **timestamp 단독이면
정상 증분 빌드를 stale 로 오탐했을 자리다.**

### 🔴 단위 테스트가 원리적으로 못 잡는 것 2건을 실기동에서 잡았다

| 확인 | 결과 |
|---|---|
| **양쪽 미인증에서 기권 → 상대 승** | `CHALLENGER_WIN` (기존 규칙이면 `BOTH_LOSE`) ✅ |
| **동시 기권 2건** (curl 병렬) | 정확히 한쪽만 200, 다른 쪽 705, `forfeited_by` 단일 ✅ |
| **배치 재실행** (deadline 과거로 밀고 재기동) | `judged=0`, 전적 숫자 **완전 동일** ✅ |

앞의 것이 사용자 결정이 실제로 작동한다는 증거이고, 뒤의 둘은 **fake 에 트랜잭션도 행 잠금도 없어
단위 테스트로 불가능**하다.

---

## 결정 사항

### 사용자 결정 4건 (2026-09-05)

1. 🔴 **기권 = 상대 즉시 승** — *"미인증으로 친다"* 가 아니다. 상대가 인증 안 했어도 상대가 이긴다
2. **인증 전에만 기권 가능** — 인증해 놓고 기권은 논리 모순이고, 지울 사진도 안 생긴다
3. **전적·랭킹에서 일반 패배와 구분하지 않는다** — 마이그레이션·랭킹 정렬·마이페이지 계약 변경 0
4. **알림 목록 탭 이동 없음** — `notification-list` 2차 개정 규칙에 예외를 만들지 않는다

### 🔑 판정 규칙의 사본을 만들지 않았다 — 이 feature 의 1번 제약

`ChallengeVerdict` KDoc 이 *"이 프로젝트에서 판정 규칙이 존재하는 **유일한 곳**이다. 두 번째
호출부가 생기는 순간 두 벌의 규칙이 갈린다"* 라고 경계하는데, **기권이 정확히 그 두 번째 호출부**다.

- **규칙**: `decide()` 안에 `forfeit` 파라미터 1개를 추가하고 **최우선 분기**로 넣었다. 기존 3규칙 무변경
- **확정**: 기권은 판정을 계산하지 않는다. **자정 배치가 쓰는 `judge()` 를 그대로 호출**한다 —
  전적·연승·연패 집계 코드를 새로 쓰지 않았다

⚠️ **결정 1의 대가는 시그니처 파라미터 1개다.** 기권을 *"미인증으로 친다"* 로 정의했다면
`challengerVerified = false` 하나로 끝나 시그니처가 안 바뀌었다. 대가를 치르는 자리가 **규칙이 사는
그 한 곳**이라 사본은 안 생겼다.

🔴 **`Forfeit` 파라미터에 기본값을 주지 않았다** — 기본값이 있으면 새 호출부가 기권 판정을
**조용히 빠뜨린 채** 컴파일된다. `Challenge.forfeitedBy` 도 같은 이유로 기본값이 없다.

### 🔴 동시 기권 — 규칙을 늘리지 않고 닫았다

**pm spec §3.1 이 틀렸다.** *"첫 기권이 즉시 `COMPLETED` 라 두 번째는 `IN_PROGRESS` 게이트에 걸린다"*
는 **순차일 때만 참**이고, READ COMMITTED 에서 동시 요청 둘은 양쪽 다 통과한다. 전적이 두 번 오르고
`total_challenges` 는 소급 정정이 불가능하다.

해법: 트랜잭션 첫 문장에서 `@Lock(PESSIMISTIC_WRITE)` 단건 조회. 두 번째 요청이 첫 커밋 뒤 갱신된
row 를 다시 읽고, 그때 `COMPLETED` 라 **기존 게이트가 그대로 막는다.** 🔑 **동시성 전용 분기 0줄.**

🔑 **기권은 양쪽 당사자 모두가 부를 수 있는 이 프로젝트 유일의 상태 전이다** — 수락·거절은 opponent
만, 취소는 challenger 만, 배치는 단일 스레드. 잠금이 필요한 자리가 여기 하나뿐인 이유다.

### 🔑 T-M1 배타성을 테스트가 아니라 **타입**으로 고정했다

pm 지시는 *"'다시 찍기' 와 동시에 보이지 않게 하고 테스트로 고정하라"* 였다. 상세에 이미
`MyMissionSlot` 이라는 **단일 `when`** 이 있고 두 진입점이 그 `when` 의 다른 가지였다.

```kotlin
val canForfeit: Boolean get() = myMissionSlot == MyMissionSlot.VERIFY_CTA
```

한 `when` 의 값이 하나뿐이라 **"둘이 동시에 보이는 조합" 이 표현 불가능**해진다. 새 `if` 0개.
⚠️ 그래서 그 테스트는 **회귀 감시가 아니라 "이 파생이 실제로 그 뜻인지" 확인**하는 성격이고, 그
구분을 KDoc 에 적었다 — 안 적으면 나중에 독립 조건식으로 바꿔도 **테스트는 통과하는데 보증만 사라진다.**

### 🔑 실패도 성공과 같은 경로로 — 재조회

기권 요청은 **성공하든 실패하든 상세를 다시 조회**한다. 성공 body 를 안 읽는 이유는 상세를 세우는
경로가 두 벌이 되면 갈리는 날 아무도 못 잡기 때문이고, **실패에도 재조회하는 이유**는 서버 거부
사유 대부분이 *"화면 스냅샷이 낡았다"* 는 뜻이라서다 — 재조회하면 **사라졌어야 할 진입점이 그 자리에서
사라진다.**

🔵 이 설계가 부수적으로 **에러 코드 논쟁을 무의미하게 만들었다**(아래).

### 에러 코드 — 705×3 + 700×1 (pm 이 spec 이탈 승인)

spec 초안은 *"전부 700"* 이었으나 **폐기**했다. 승인 근거는 **하나뿐**이다 —
`"챌린지를 찾을 수 없어요"` 가 상세·취소·인증 제출에서 **이미 전부 705** 인데 기권만 700 이면
같은 문장이 화면마다 다르게 뜬다.

🔴 **backend 가 든 두 번째 근거는 기각했다** — *"705 는 확인을 강제해 새로고침 계기를 준다"* 는
**앱에 그 동작이 없어 거짓**이다(아래 §조용한 결함). ⚠️ 그렇다고 **700 으로 내리지도 않았다** —
앱 현실에 맞춰 서버 표기를 낮추면 정보를 **원천에서** 버리는 것이고, 앱이 나중에 고쳐도 전부 700 이라
아무것도 안 좋아진다. **버그가 계약에 박제된다.**

### <a id="forfeitedby-를-상세에만-넣은-근거가-두-다리인-이유"></a>🔑 `forfeitedBy` 를 상세에만 넣은 근거가 **두 다리**인 이유

- **ⓐ 아무도 안 그린다** — Lovable 정본에 기권 UI 0건이라 홈·보관함까지 그리면 디자인 근거 없는
  이탈분이 1건에서 3화면이 된다. ⚠️ **디자인이 바뀌면 무너지는 근거다**
- **ⓑ 🔴 넣어도 해석할 수 없다** — `ActiveChallengeDto`·`ChallengeHistoryDto` 는 **`userId` 를 하나도
  싣지 않는다.** 전부 *"내 시점"* 좌표(`myMission`·`myVerificationStatus`·`myResult`)다.
  `forfeitedBy` 는 userId 이므로 **비교 대상이 응답 안에 없는 외래 좌표 필드**가 홀로 앉는다

🔑 정확한 표현은 *"안 그린다"* 가 아니라 **"그릴 수 없다"** 다. **ⓑ 는 안 무너진다.**
⚠️ 뒤집으려면 `forfeitedBy` 가 아니라 **내 시점 필드**(`forfeitedByMe: Boolean` 등)가 필요하다 —
**결정이지 누락이 아니다.**

### `referencePending` = `null`

계약 §9.1 의 세 값 중 `null` = *"이 타입에는 그 개념이 없다"*. 기권 알림 수신자에게는 **응답할 것이
없다** — 이미 이긴 쪽이고 챌린지는 끝났다. `false` 는 *"한때 대기였는데 끝났다"* 로 읽히는데
**이 알림은 애초에 대기한 적이 없다.** 서버 코드 변경 0건(`else -> null` 로 자동).

🔵 앱은 이 값을 **아예 보지 않는다** — `isTappableInList` 가 타입에서 먼저 결론을 내고 «조건부» 인
타입만 `referencePending` 을 본다(기존 4종 중 3종이 그렇다). **값이 근거가 아니다.**

### 알림 발송 절차 — 문구를 일부러 늦게 넣었다

`NotificationMessages` 에서 **문구 한 줄이 곧 발송 스위치**다. backend 가 enum 만 열어 두고 문구를
비워 뒀다가, mobile 이 **딥링크 배선 완료를 숫자와 함께 회신한 뒤** 3줄을 넣었다
(`OPPONENT_VERIFIED` 가 2026-08-14 에 밟은 절차). 앱이 모르는 타입이 먼저 나가면 트레이에서
**눌러도 아무 데도 안 가는 조용한 실패**가 된다.

✅ **발송 ON 후 실기동으로 row 확인**:
```
type=CHALLENGE_FORFEITED · title=계약 파기. · body=테스터2님이 기권했습니다
reference_id=challengeId · 수신자 = 이긴 쪽 · 목록 응답 "referencePending":null
```

🔑 **목록에 `title` 이 안 실리는 것이 이번 문구 설계와 맞물린다** — `notification-list` 가 *"푸시용
헤드라인은 목록에서 홀로 서지 못한다"* 를 이유로 `title` 을 응답에서 뺐는데, `계약 파기.` 는 정확히
그런 문구다(트레이에서 본문과 **함께** 뜰 때 성립). **옛 결정과 새 문구가 정합한다.**

🔵 **문구가 사용자 미확정이라 앱 테스트에 문자열을 박지 않았다** — `기권했습니다` 는 프리뷰 픽스처
1곳뿐이고 단언 0건. 테스트는 타입·존재·비탭만 고정한다.

---

## 🔴 이 feature 의 수확 — *"문서가 코드보다 앞서 있는데 아무도 몰랐다"* **6건**

기권이 판정 결과와 인증 상태의 **일대일 대응을 깨자**, 그 대응을 근거로 삼은 문장들이 조용히
거짓이 됐다. **컴파일러도 테스트도 안 잡는다.**

| # | 위치 | 낡은 문장 | 무엇을 하던 근거였나 |
|---|---|---|---|
| 1 | `ChallengeHistoryService` KDoc | *"결과 4개가 양측 인증 상태를 **유일하게 결정**"* | verifications **조회 생략** |
| 2 | 🔴 `ChallengeHistoryResponse.myResult` KDoc | 위 + **대응표를 괄호 안에 나열** | 〃 |
| 3 | `ChallengeHistoryView` KDoc | 위 + *"정보량이 0인 필드 2개"* | 〃 |
| 4 | 앱 `ArchiveChallengeCard` KDoc | *"인증 pill 을 빼도 **정보가 줄지 않는다**"* | 🔴 **UI 요소 제거** |
| 5 | backend-report §결정 근거 | *"705 는 확인을 강제한다"* | 에러 코드 선택 |
| 6 | 🔴 **`confirmed` 계약 §3** | *"`referencePending = false`"* | 5줄 아래 소절이 그 값을 **기각** |

🔑 **2번이 가장 위험했다** — 대응표를 괄호 안에 그대로 나열해 **코드로 옮기기 가장 쉬운 형태**였다.
🔑 **4번이 성격이 가장 나빴다** — 나머지는 조회를 생략하는 근거였는데 이것은 **사용자가 볼 UI 요소를
빼는** 근거였다.
🔑 **6번은 실제 피해를 냈다** — mobile 의 child 지시서에 그 값이 실려 나갔고, **child 가 5줄 아래까지
읽고 계약을 근거로 이견을 내서** 잡혔다. *"판단 근거는 파일이지 메시지가 아니다"* 규율이 3단계
아래에서 작동한 사례다.

**전부 결론 유지 + 근거 교체 + "원문은 …였다" 과거형 기록.** 조용히 갈아끼우면 다음 사람이 무너진
논거를 다시 발명한다. ⚠️ **부분만 깨졌으면 부분만 적었다** — 기권은 **승·패만** 깨고 무·양패는 그대로다
(기권은 `CHALLENGER_WIN`/`OPPONENT_WIN` 만 만든다).

### 🔴 부수 — 캡처 픽스처 2개가 손도 안 댔는데 낡았다

앱 `ChallengeDetailWireFixtureTest` 의 4개 본문 중 2개(`wireResponse`·`pendingWireResponse`)에
**`result` 키가 없다.** 2026-08-03 캡처 당시 서버가 그 키를 안 보냈기 때문이다. 지금은 항상 보낸다
(`WireShapeContractTest.kt:85` 가 *"`@JsonInclude(NON_NULL)` 이 없어 항상 모든 키를 보낸다"* 를 계약으로
고정, `ChallengeDetailControllerTest.kt:242` 가 `"result":null` 원문 단언).

🔵 **삭제하지 않았다** — 키 부재 내성의 증명이라 `NON_NULL` 이 켜지는 날의 안전망이다. **시점 라벨만
달았다.** 🔑 **캡처는 손대지 않아도 서버가 바뀌면 낡는다.**

⚠️ **그 테스트 KDoc 이 *"서버가 shape 을 바꾸면 깨진다"* 고 단언하는데 이번엔 안 깨졌다** —
키가 **늘어난** 변경이라 `ignoreUnknownKeys` 가 흡수했다. **키가 줄 때만 깨진다.** 한계를 KDoc 에 적었다.

## 🔴 pm-lead 자기 정정 3건

1. **spec §3.1 동시성** — *"양쪽 기권은 저절로 닫힌다"* 를 **저절로 닫히는 것** 표에 넣었다.
   순차에서만 참이다. 더 나쁜 건 **§3 수용 기준이 처음부터 동시 요청 검증을 요구**하고 있어
   **spec 이 스스로 모순**이었다는 것 — 한쪽을 읽은 사람은 테스트를 쓰고 다른 쪽을 읽은 사람은 안 쓴다
2. **KDoc 초안 문장에 관점 한정 누락** — *"기권하면 `OPPONENT_WIN`"* 이라고 단정했는데
   `ChallengeResult` 는 **역할 기준**이라 내가 opponent 면 `CHALLENGER_WIN` 이다. 하필
   **역산이 틀린 답을 낸다고 경고하는 문장**에서 역할을 안 따졌다(mobile 의 child 가 적발)
3. **수용 기준의 `referencePending = false`** — 두 겹으로 틀렸다. ⓐ 확정값은 `null` ⓑ **값이 근거가
   아니다.** 🔴 **값만 고쳤으면 여전히 틀린 것을 검증했을 것이다** — 값을 단언하는 테스트는 서버가
   값을 바꾸는 날 깨지는데 정작 보장해야 할 것(타입 단계 비탭)은 그대로 참이다

## 주요 변경 파일

**백엔드** (35파일, 🔴 미커밋)
- `domain/model/.../challenge/ChallengeVerdict.kt` — `Forfeit` enum + `decide` 파라미터
- `domain/model/.../challenge/Challenge.kt` · `infra/entity/.../ChallengeEntity.kt` — `forfeitedBy`
- `service/.../challenge/ChallengeForfeitService.kt` (신규) · `ChallengeJudgementService.kt`
- `infra/jpa/.../ChallengeJpaRepository.kt` — `@Lock(PESSIMISTIC_WRITE)` 기권 전용 조회
- `app/src/main/resources/db/migration/V12__challenge_forfeit.sql` (신규)
- `domain/model/.../notification/NotificationType.kt` · `NotificationMessages.kt`

**모바일** (36파일 = 33 변경 + 3 신규, +962, 🔴 미커밋)
- `feature/challenge/detail/` — `ChallengeDetailState.kt`(`canForfeit`) · 다이얼로그 · ViewModel · Screen
- `core/push/PushEvent.kt` · `PushEventRoute.kt` — `ChallengeForfeited`
- `feature/notification/` — `NotificationState.kt`(비탭 고정) · `NotificationTypeVisual.kt`
- `remote/model/.../ForfeitChallengeResponse.kt` (신규) · `remote/api` · `datasource` · `mapper`
- `domain/model` · `domain/repository` · `data/repositoryImpl` + `FakeChallengeRepository` ×5

## 미해결 이슈

- [ ] 🔴 **양 레포 미커밋** — 서버 35파일 · 앱 36파일. 커밋은 사용자 판단
- [ ] 🔴 **실기 검증 0건** — 특히 ① 기권 → 상대 화면·푸시 도착 ② 동시 기권(실기기 2대)
      ③ 알림 목록에서 안 눌리는지 육안. 서버 실기동으로 ①의 서버측은 확인됐으나 **앱 왕복은 미확인**
- [ ] 🎨 **디자이너 확인 7건** — 진입점 위치(맨 아래)·형태(텍스트 1줄)·색(`error`) / 안내 문구 자리 /
      알림 아이콘(`Flag`)·색(`error`) / 홈·보관함 미표시. 🔴 **Lovable 정본에 기권 UI 0건**이라 전부 앱 관례에서 유도
- [ ] 🟡 **문구 4종 사용자 미확정** — spec §6 초안 그대로 구현(다이얼로그 제목·본문, 알림 제목·본문)
- [ ] 🔵 **배치와 기권이 정확히 겹치는 구간은 잠그지 않았다** — 노출 창이 하루 5분이고 기권 이전부터
      `judge()` 에 있던 성질이다(그래서 `judge()` 가 자기 트랜잭션에서 status 를 재확인한다).
      막으려면 배치 핫패스에 잠금을 넣는 구조 변경
- [ ] 🔵 **`:remote:datasource` · `:data:repositoryImpl` iOS 미컴파일** — **선존재**. 백로그 기존 항목 소관.
      🔑 이번에 **컴파일러 에러 원문 + 실패 태스크명**을 처음 확보했다(기존 근거는 *"iOS 디렉터리가
      없다"* 는 **간접** 증거였다). 백로그가 적어 둔 위반 수 **14 · 8 이 오늘도 유효**함을 컴파일러
      출력으로 독립 확인했고 **증감 0**이다. ✅ 이번 신규 테스트 2건은 백틱 이름의 `,`·`()` 를 피해
      **위반 수를 늘리지 않았다**(백로그 79행의 경고를 지켰다)

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md)(`confirmed`) · [change-log.md](./change-log.md)
- [backend-report.md](./backend-report.md) · [mobile-report.md](./mobile-report.md)
- **design.md 없음** — Lovable 정본에 기권 UI 0건(pm 실측: `grep -rniE "기권|포기|forfeit|surrender"` → 무관 히트 1건)이라 design-bridge 를 팀에서 제외했다
- 개정한 계약: [notification-list/api-contract.md](../notification-list/api-contract.md) §9(탭 규칙 승계) · [challenge-result/api-contract.md](../challenge-result/api-contract.md)(판정 규칙)
- [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)(시간) · [ADR-0002](../../decisions/0002-backend-foundation.md)(BaseResponse)
