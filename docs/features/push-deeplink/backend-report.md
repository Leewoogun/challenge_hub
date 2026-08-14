# Backend Report — push-deeplink

- **작성일**: 2026-08-08 / **작성자**: backend-dev
- **범위**: **T-B1 한 건** (`AndroidConfig.notification.tag` 추가). REST 엔드포인트 변경 0건.
- **상태**: implemented (**미배포**)

## 구현 요약

`FcmNotificationSender.send()`의 `Message.builder()`에 **`AndroidConfig` 블록을 추가**했다.
이전에는 `AndroidConfig` 자체가 없었다.

🔴 **`notification`·`data` 블록은 손대지 않았다.** shape이 바뀌면 모바일 파서와 `push-fcm`의
`confirmed` 계약이 동시에 깨진다. 이번 변경은 `android` 블록 **추가**뿐이고, **모바일 코드 변경은
불필요하다** — `android.notification.tag`는 시스템 트레이가 소비하고 앱에 전달되지 않는다.

## 🔵 mobile-dev 에게 통지할 `tag` 문자열 형식

```
challenge-{referenceId}      예: challenge-7
```

- **접두사는 `"challenge-"` (하이픈 포함), 뒤에 `referenceId` 10진수 문자열.** 상수:
  `FcmNotificationSender.TAG_PREFIX`.
- 🔴 **`referenceId`가 `null`이면 tag를 붙이지 않는다** — `android.notification` 블록 자체가
  페이로드에서 빠진다. `"challenge-null"`은 보내지 않는다.
- 🔵 **모바일이 이 값을 파싱할 일은 없다.** tag는 Android 시스템 트레이 전용 키이고 앱에
  전달되지 않는다. **모바일 조치 사항 없음** — `notification`/`data` 무변경이라 기존 파서도
  그대로다. (mobile-dev 확인 완료: `data.type`/`data.challengeId`를 읽는 코드가 `android` 블록을
  보지 않는다.)

### 🔴 `buildNotificationId` 와의 결합 — 우연이 아니라 결정이다

`ChallengeFirebaseMessagingService`의 `buildNotificationId` (2026-08-08 backend-dev 직접 실측):

```kotlin
private fun buildNotificationId(challengeId: Long?): Int =
    challengeId?.toInt() ?: (System.currentTimeMillis() and Int.MAX_VALUE.toLong()).toInt()
```

**서버 tag와 앱의 포그라운드 알림 id가 같은 논리 키(`challengeId`)로 묶는다. `null` 케이스까지
방향이 일치한다:**

| | `referenceId`/`challengeId` 있음 | 없음 |
|---|---|---|
| 서버 (트레이) | `tag = "challenge-7"` → 덮어씀 | **`android.notification` 블록을 통째로 뺌** → 각각 쌓임 |
| 앱 (포그라운드) | `notificationId = 7` → 덮어씀 | `System.currentTimeMillis()` → 각각 쌓임 |

표현이 다르고(문자열 tag vs Int id) 전달 경로도 달라 **값이 같을 필요는 없다.** 일치해야 하는 것은
**묶는 키**다.

⚠️ **그런데 이 결정이 서버·앱 어느 쪽 주석에도 없었다.** `buildNotificationId`의 키를 바꾸면
포그라운드와 백그라운드의 덮어쓰기 단위가 갈라져, 같은 도전장 알림이 한쪽에선 합쳐지고 다른 쪽에선
따로 쌓인다 — **양쪽 모두 크래시 없이 조용히** 어긋난다. 서버 쪽은 `androidConfigFor` KDoc과
계약 §3.1에 적었다. **앱 쪽 KDoc 은 pm-lead 가 파일 소유자에게 배정한다** (backend-dev 는 모바일
레포를 편집하지 않고 peer 에게 작업을 지시하지도 않는다).

> 🔴 **인용 방식 정정** — 이 절이 처음에 `ChallengeFirebaseMessagingService.kt:131`이라고 적었다.
> **틀렸다.** 실제는 128행이고, 그 사이 `showNotification` 시그니처가 `(title, body, type,
> challengeId)` → `(title, body, data: Map<String,String>)`로, 키 상수가
> `PushEvent.KEY_CHALLENGE_ID`로 옮겨졌다. 그 파일은 지금도 **미커밋 편집 중**이다.
>
> 원인은 두 가지가 겹쳤다: **(1)** peer 가 준 행 번호를 받아 적고 대상 레포에서 직접 확인하지
> 않았다. **(2)** 남의 레포 파일은 이 문서보다 빨리 움직인다. 이후로는 **함수 이름으로 가리키고
> 행 번호를 쓰지 않는다.**

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| — | **변경 없음** | — | — |

REST 계약은 요청·응답 shape이 전혀 바뀌지 않았다. 변경된 것은 **FCM 페이로드 규약**
(`push-fcm/api-contract.md` §3)뿐이다.

## 변경된 모듈 & 파일

| 모듈 | 파일 | 변경 |
|---|---|---|
| `:infra:external` | `infra/external/src/main/kotlin/com/lwg/challenge/infra/external/firebase/FcmNotificationSender.kt` | `setAndroidConfig(...)` 1행 + `TAG_PREFIX` / `tagFor` / `androidConfigFor` 신설 |
| `:infra:external` (test) | `infra/external/src/test/kotlin/com/lwg/challenge/infra/external/firebase/FcmNotificationSenderTest.kt` | 테스트 4 → **10** |

DB 마이그레이션 **없음**. 의존성 추가 **없음**.

## tag 규칙

```kotlin
fun tagFor(referenceId: Long?): String? = referenceId?.let { "$TAG_PREFIX$it" }
```

`resultFor`와 **같은 이유로 순수 함수**다 — `AndroidConfig`/`FirebaseMessagingException` 같은
Firebase 타입 없이 전수 검증할 수 있다.

🔴 **`null` 분기가 이 태스크의 핵심이다.** `"challenge-null"`로 뭉치면 **서로 무관한 알림들이 한
덩어리가 되어 서로를 덮어쓴다** — 예외도 로그도 없이 알림이 사라지는 사고다. 같은 파일이 이미
`putData(DATA_KEY_CHALLENGE_ID, ...)`를 조건부로 넣고 있으며 **같은 이유·같은 판단**이다.

⚠️ 현재 3종은 전부 `challenges.id`를 참조하므로 실제로는 항상 붙는다. 그러나 그건 **오늘의 사실이지
규약이 아니다** — `push-fcm` 결정사항 6번(*`reference_id`를 `challenge_id`로 못 박지 않는다*)이
현실이 되는 순간 이 분기가 유일한 방어가 된다.

## priority 판단 — **`high`로 설정. 근거는 아래.**

**결론부터: 오늘 기준으로 동작이 바뀌지 않는다.**

FCM은 **`notification`을 포함한 메시지를 이미 high로 취급**한다 — 기본값이 normal인 것은 data-only
메시지다. 우리 페이로드는 `notification` + `data` 혼합이므로(계약 §0.5) **명시 전에도 실효 priority는
이미 high였다.** 따라서 이 설정은 **새 동작을 켜는 것이 아니라 현재의 실효 동작을 고정하는 것**이다.

그래서 "붙인다 / 안 붙인다"의 실질 차이는 딱 하나다:

| | 오늘 | 페이로드가 data-only로 바뀔 때 |
|---|---|---|
| 미설정 | high (암묵) | **normal로 조용히 강등** |
| `high` 명시 | high | high 유지 |

`push-deeplink` 판정 4가 data-only 전환을 **폐기가 아니라 보류**(*"알림함 기능 착수 시 재검토"*)로
남겼으므로, 그 전환이 실제로 오면 **명시가 없는 쪽이 즉시성을 소리 없이 잃는다.** 명시 쪽은 오늘
비용이 0이고 그때 이득이 있다.

**배터리 정책 역효과는 현재 해당하지 않는다.** high 남용이 문제가 되는 것은 **주기·배치·마케팅
발송**인데, 현재 3종(`CHALLENGE_REQUEST`/`ACCEPTED`/`REJECTED`)은 전부 **사용자 행동이 즉시 유발한
1:1 알림**이고 그런 경로가 없다. 도전장이 늦게 도착하면 알림 자체가 무의미해진다.

🔴 **단, `RESULT`(자정 판정 배치)·`REMIND`(마감 1시간 전 배치)가 붙을 때 이 판단을 재검토해야 한다.**
자정 배치가 전 사용자 기기를 한꺼번에 Doze에서 깨우는 것은 위에서 말한 남용 패턴 그 자체다.
**타입별 priority 분기를 지금 만들지는 않았다** — 해당 타입이 존재하지 않아 근거를 정할 수 없고,
spec 판정 2가 같은 이유로 미래 타입 매핑을 금지하고 있다. 재검토 시점은 프로덕션 KDoc과
계약 §3.1 양쪽에 명시해 뒀다.

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui.html
- **반영된 경로 없음.** FCM 페이로드는 REST 엔드포인트가 아니라 서버 ↔ 모바일 간 메시지 규약이라
  OpenAPI 대상이 아니다. 정본은 `push-fcm/api-contract.md` §3.

## 테스트 결과

- **전체: 260/260 passed** (총 305건 중 skip 45). 이전 baseline 254 → **신규 6, 회귀 0**
- `FcmNotificationSenderTest`: **10/10 passed** (기존 4건 전부 유지 + 신규 6건)
- 통합 테스트 45건은 여전히 **컨테이너 런타임 부재로 skip** (누적 건, 이번 변경과 무관)

### 신규 6건이 고정하는 것

| # | 테스트 | 잠그는 실패 |
|---|---|---|
| 1 | `referenceId 가 있으면 challenge- 접두사 tag 가 붙는다` | 접두사·형식 드리프트 |
| 2 | `referenceId 가 null 이면 tag 를 만들지 않는다` | 🔴 `"challenge-null"` 덩어리 |
| 3 | `tag 가 android notification 에 실린다` | tag가 엉뚱한 자리(`android.data` 등)에 실림 |
| 4 | `referenceId 가 null 이면 android notification 블록이 아예 없다` | 빈 tag 전송 |
| 5 | `android notification 은 tag 외에 아무 필드도 싣지 않는다` | 🔴 **아래 참조** |
| 6 | `priority 는 referenceId 유무와 무관하게 high` | 한쪽 분기에만 priority가 붙음 |

🔴 **5번이 "shape 무변경" 주장을 실제로 지탱하는 테스트다.** FCM은 `android.notification`의
**설정된 필드만** 공통 `notification`을 덮어쓴다. 여기에 빈 title/body가 실리면 **트레이에 제목 없는
알림이 뜨고 계약 §3 문구 3종이 통째로 무력화된다.** 말로 "안 건드렸다"고 적는 대신 나가는 JSON
원문으로 고정했다.

### 검증 방식에 대한 메모

`AndroidConfig`에는 **공개 getter가 없다.** 그래서 firebase-admin이 **실제 전송에 쓰는 직렬화
경로**(`@Key` + `JsonFactory`)를 그대로 태워 JSON 원문을 단언했다:

```
androidConfigFor(7L)   → {"notification":{"tag":"challenge-7"},"priority":"high"}
androidConfigFor(null) → {"priority":"high"}
```

**술어를 Kotlin으로 다시 쓰지 않고 나가는 바이트를 본다** — `push-fcm` 계약 §0.2가 *"fake가 SQL
술어를 다시 쓴 것이라 실제 SQL을 검증하지 못한다"*고 경고한 문제의 반대편에 서 있다.

부수 효과로 **`send()`의 메시지 빌드부에 처음으로 테스트가 닿았다.** `push-fcm` summary가
*"`send()`의 메시지 빌드·호출·catch는 어떤 테스트도 태우지 않는다"*고 적어 둔 공백의 일부가 메워졌다
(호출·catch 경로는 여전히 미커버).

## 계약 문서 반영

메모리 규약(*api-contract.md 소유자는 backend-dev — 묻지 말고 고치고 협의 이력에 등재*)에 따라 직접 반영했다.

- `docs/features/push-fcm/api-contract.md` — §3 페이로드 예시에 `android` 블록 + 키 표 2행 추가,
  **§3.1 신설**(tag 규칙 / null 분기 / priority 근거 / 회귀 장치), 헤더 "최종 수정" 갱신
- `docs/features/push-fcm/change-log.md` — **`2026-08-08` 절 신설.** `confirmed` 이후 첫 계약 변경이라
  유발자(push-deeplink T-B1)와 등재 주체를 명시했다

## 미해결 이슈

- [ ] 🔴 **tag 중복 제거는 자동 테스트로 검증할 수 없다** — 트레이 묶음 동작은 Android 시스템의
  몫이다. 서버가 증명할 수 있는 것은 *"올바른 tag를 실었다"*까지고, *"트레이에 하나만 남는다"*는
  **배포 후 실기 검증**(T-I1)이 유일한 확인 경로다.
- [ ] 🟡 **미배포.** 로컬 구현·테스트만 끝났다. T-I1의 tag 검증은 배포 후에만 가능하다.
- [ ] 🟢 **`RESULT`/`REMIND` 도입 시 priority 재검토** — 위 "priority 판단" 참조. 자정 배치의
  blanket high는 Doze 일괄 기상이라 남용 패턴에 해당한다.
- [ ] 🟢 **`send()`의 호출·catch 경로는 여전히 미커버** — 이번에 메시지 빌드부만 닿았다.
  `push-fcm`의 누적 항목이 부분적으로만 해소됐다.
- [ ] 🟡 **`Message.Builder.setToken` deprecation 경고 (`FcmNotificationSender.kt:36`)** — **이번
  변경이 유발한 것이 아니다.** 아래 "deprecation 경고" 참조. **이번 범위에서 조치하지 않았다.**

## deprecation 경고 — 출처와 판단

```
w: FcmNotificationSender.kt:36:14 'fun setToken(p0: String!): Message.Builder!' is deprecated. Deprecated in Java.
```

### 출처: **기존 코드다. 이번 변경과 무관하다.**

| 확인 | 결과 |
|---|---|
| 프로덕션 diff의 삭제 라인 수 | **0** — 순수 추가만 했고 `.setToken` 라인은 무접촉 |
| `.setToken(fcmToken)` 도입 커밋 | **`f01bd44`** (push-fcm T-B4) |
| `firebase-admin` 버전 변경 이력 | **`f01bd44`가 유일** — 9.10.0으로 도입된 이래 무변경 |

즉 **push-fcm 시점부터 계속 나오던 경고**이고, 이번엔 파일이 재컴파일되면서 다시 표면화됐을 뿐이다.

### 조치 필요 여부: **지금은 아니다. 그러나 한 줄 교체가 아니다.**

firebase-admin 9.10.0 바이트코드 실측 — `Message.Builder.setToken`에 `@Deprecated`가 달려 있고,
형제 setter `setFid`/`setTopic`/`setCondition`에는 없다. 다만 **`forRemoval`·`since` 요소가 비어
있어 제거 시한이 신호되지 않았다** (Kotlin이 *"Deprecated in Java"*라고만 말하는 이유 — Java의
`@Deprecated`는 설명 텍스트를 바이트코드에 남기지 않는다).

⚠️ **`setFid`를 대체재로 단정할 근거는 아직 없다.** 확인된 것은 *"deprecated가 아니다"*까지다.
FID(Firebase Installation ID)와 등록 토큰은 **다른 식별자**이고, 이 프로젝트의 스택 전체가 등록
토큰 위에 서 있다 — `users.fcm_token` 컬럼, `PUT /api/v1/users/me/fcm-token` (`confirmed` 계약 §1),
모바일 `FcmTokenProvider`·`onNewToken`. 바꾼다면 **서버 단독 변경이 아니라 DB·계약·모바일을 함께
건드리는 교차 레포 작업**이다.

**따라서 T-B1 범위에서 손대지 않았다.** 컴파일 경고 하나를 지우려고 `confirmed` 계약과 스키마를
건드리는 것은 비용 방향이 반대다. **백로그 항목으로 pm-lead에게 넘긴다** — 착수 전 선결 과제는
*"`setFid`가 등록 토큰의 대체재가 맞는지, 아니면 별개 타겟팅 수단인지"*를 Firebase 문서로 확정하는
것이다.
