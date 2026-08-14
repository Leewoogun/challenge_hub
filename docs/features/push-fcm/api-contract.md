# API Contract — 푸시 알림 (push-fcm)

- **feature-id**: push-fcm
- **상태**: ✅ **`confirmed`** (2026-08-07) — 오픈 이슈 4건 전부 해소. 이후 변경은 `change-log.md`에 기록.
  - ⚠️ **`confirmed`는 계약 shape에 대한 것이다.** §3 문구 3종 중 2종은 여전히 **초안**이며, 문구 변경은 계약 shape을 바꾸지 않는다(서버가 `title`/`body`를 만들어 보내고 모바일은 그대로 표시한다).
- **최종 수정**: 2026-08-08 by backend-dev (§3에 `android` 블록 추가 + **§0.6.1 신설**(새 타입 발송 개시 전 모바일 통지) — [push-deeplink](../push-deeplink/spec.md). `notification`·`data` 무변경, `change-log.md` 등재됨)
- **상위 spec**: [spec.md](./spec.md)

## 엔드포인트 요약

| # | Method | Path | 설명 | 인증 | 변경 |
|---|--------|------|------|------|------|
| 1 | PUT | `/api/v1/users/me/fcm-token` | FCM 토큰 등록·갱신 | Bearer JWT | **신규** |
| 2 | DELETE | `/api/v1/auth/logout` | 로그아웃 — refresh 무효화 **+ FCM 토큰 제거** | Bearer JWT | **스텁 → 실구현** (계약 shape 무변경) |

공통:
- ADR-0002 BaseResponse — 성공·비즈니스 에러는 HTTP 200 + body `code`.
- ADR-0010 시간 규약 — `yyyy-MM-dd HH:mm:ss` (KST). `T`·`Z`·offset·밀리초 없음. **본 계약에는 시간 필드가 없다.**
- `POST /challenges` · `/accept` · `/reject` 는 **요청·응답 shape이 바뀌지 않는다.** 알림 발송은 부수 효과로만 붙는다.

---

## 0. 핵심 결정 (초안 — Phase 4에서 확정)

### 0.1 토큰 등록은 **로그인 body가 아니라 독립 엔드포인트**다

로그인 요청에 `fcmToken`을 실으면 안 된다. **FCM 토큰의 수명주기가 로그인 수명주기와 다르기 때문이다** — 앱 재설치, 앱 데이터 삭제, 토큰 만료, 복원 시 FCM은 언제든 `onNewToken`을 부른다. 그 시점에 사용자는 이미 로그인 상태이고 로그인 요청을 다시 보낼 이유가 없다. 로그인에만 실으면 **갱신된 토큰을 보낼 곳이 없어진다.**

부수 효과로 `auth-kakao`의 `confirmed` 계약을 건드리지 않는다.

### 0.2 🔴 토큰 소유권은 **한 계정에만** 있다 — 등록 시 이전 소유자를 밀어낸다

`users.fcm_token`에는 UNIQUE 제약이 없다. 그래서 **같은 기기에서 A 로그아웃 → B 로그인** 시 A의 `fcm_token`이 남아 있으면 **한 기기가 두 계정의 알림을 받는다.**

🔴 **2026-08-06 근거 정정 — 이것은 "혹시 모를 경우"에 대한 방어가 아니라 유일한 방어다.**

초안은 *"logout의 `NULL` 처리(§2)가 대부분을 막고, 앱 삭제·강제 종료로 logout이 안 불린 경로만 남는다"*고 적었다. **틀렸다.** mobile-dev 실측에 따르면 **모바일 `LogoutUseCase`는 서버를 호출하지 않는다 — 로컬 토큰 정리만 한다.** 즉 §2의 `fcm_token = NULL`은 **앱에서 한 번도 발생하지 않는다.**

따라서 §0.2는 보조 방어가 아니라 **현재 유일한 방어**다. 그리고 이 실패는 가정이 아니라 **관측 가능한 확정 경로**다 — `dev-test-login`으로 테스트 계정 3개를 한 기기에서 오가는 것이 이 프로젝트의 **표준 검증 방식**이므로, 방어가 없으면 개발 첫날 발생한다.

> ⚠️ **`LogoutUseCase`가 서버를 호출하지 않는 것 자체가 별개 결함이다.** 지금은 무해하지만 **`push-fcm`이 들어가는 순간 실제로 깨진다** — 로그아웃해도 서버 `fcm_token`이 남아 그 기기로 알림이 계속 간다. **가정이 아니라 미구현 기능**이므로 §0.2와 별도로 처리해야 한다(아래 오픈 이슈 4).

두 UPDATE는 순서가 중요하다:

```
UPDATE users SET fcm_token = NULL WHERE fcm_token = :token AND id <> :me;
UPDATE users SET fcm_token = :token WHERE id = :me;
```

> ⚠️ 이건 이론적 위험이 아니다. `dev-test-login`으로 **테스트 계정 3개를 한 기기에서 오가는 것이 이 프로젝트의 표준 검증 방식**이다. 방어하지 않으면 개발 중에 즉시 발생한다.

> 🔴 **검증 상태 주의 (2026-08-06 backend-dev 검토) — "§0.2가 테스트로 덮였다"고 읽으면 안 된다.**
>
> `UserServiceFcmTokenTest`는 **fake를 쓴다.** fake 구현이 `store.values.filter { it.fcmToken == fcmToken && it.id != exceptUserId }` 인데, 이건 **Kotlin으로 다시 쓴 술어를 검증하는 것이지 실제 SQL의 `AND u.id <> :exceptUserId`를 검증하는 게 아니다.** fake와 SQL이 갈라져도 테스트는 초록이다.
>
> fake를 쓴 것 자체는 레포 선례이고 서비스 로직 검증엔 맞다. 다만 **실제 SQL을 태우는 건 통합 테스트뿐이고 그 45건이 컨테이너 런타임 부재로 skip 중**이라, 런타임이 생기기 전까지 **§0.2의 SQL은 무검증 상태**다. 소유권 이전은 이 feature의 핵심 방어이므로 이 사실을 알고 가야 한다.

### 0.3 🔴 발송은 **트랜잭션 밖**에서 — `AFTER_COMMIT`

FCM 호출 실패가 챌린지 생성·수락·거절을 롤백시키면 안 된다. *"알림이 안 갔다"*는 불편이지만 *"챌린지가 안 걸렸다"*는 기능 실패다. 둘을 한 트랜잭션에 묶으면 후자가 전자에 인질로 잡힌다.

```
ChallengeCommandService  ──publish──>  ChallengeNotificationEvent
                                              │ @TransactionalEventListener(AFTER_COMMIT)
                                              ↓
                                    notifications row 저장 + FCM 발송
```

> ⚠️ **`AFTER_COMMIT` 리스너는 원 트랜잭션이 이미 끝난 뒤 실행된다.** row를 저장하려면 `@Transactional(propagation = REQUIRES_NEW)`가 필요하고, 빠뜨리면 **저장이 예외 없이 조용히 사라진다.** 이 프로젝트가 반복해서 겪은 *"테스트는 초록인데 실제로는 안 됨"* 계열이라 테스트로 고정한다.

### 0.4 🔴 서비스 계정 키가 없어도 **서버는 정상 기동한다** — no-op 격리

`NotificationSender` 인터페이스 + `FcmNotificationSender`(firebase-admin) + `NoOpNotificationSender`. 키가 없거나 초기화에 실패하면 **no-op으로 떨어지고 `notifications` row 저장은 그대로 수행**한다.

두 가지를 동시에 달성한다:
1. **Firebase 프로젝트 생성을 기다리지 않고 백엔드 전체를 완성·테스트할 수 있다.** (spec 의존 관계 참조)
2. 운영에서 Firebase 장애가 앱 전체를 멈추지 않는다.

> ⚠️ `dev-test-login`의 교훈을 그대로 적용한다 — **fail-safe는 "안 열린다"여야지 "터진다"가 아니다.** 그 feature에서 `getProperty(Boolean::class)`가 오타에 `ConversionFailedException`을 던져 서버를 죽였다. 여기서도 **잘못된 키 경로·손상된 JSON이 기동을 막으면 안 된다.**

### 0.5 페이로드는 `notification` + `data` **혼합**

| 방식 | 백그라운드 | 포그라운드 | 판단 |
|---|---|---|---|
| `notification`만 | 시스템이 자동 표시 | 앱이 직접 표시해야 함 | 라우팅 정보를 못 실음 |
| `data`만 | **앱이 살아 있어야 수신** (Doze/제조사 제약) | 앱이 직접 표시 | 배달 신뢰도 낮음 |
| **혼합 (채택)** | 시스템이 자동 표시 | 앱이 `data` 보고 표시 | 표시 보장 + 라우팅 정보 확보 |

`data`에는 `type`과 `challengeId`를 싣는다. **딥링크는 이번 범위 밖이지만 페이로드는 미리 실어 둔다** — 후속에서 라우팅만 붙이면 서버 변경이 0이 된다.

### 0.6 알림 타입 재정의

V1 `notifications.type` 주석의 7종을 다음으로 대체한다.

| type | 수신자 | 트리거 | 이번 범위 |
|---|---|---|---|
| `CHALLENGE_REQUEST` | 상대 | `POST /challenges` | ✅ |
| `CHALLENGE_ACCEPTED` | 신청자 | `POST /challenges/{id}/accept` | ✅ **신규** |
| `CHALLENGE_REJECTED` | 신청자 | `POST /challenges/{id}/reject` | ✅ **신규** |
| ~~`SIGN_REQUEST`~~ | — | — | ⛔ **폐기** |
| `REMIND` | 양측 | 마감 1시간 전 배치 | ❌ 인증 feature |
| `OPPONENT_VERIFIED` | 상대 | 인증 제출 | ❌ 인증 feature |
| `RESULT` | 양측 | 자정 판정 배치 | ❌ 판정 feature |
| `TAUNT` | 상대 | 도발 전송 | ❌ 도발 feature |
| `FRIEND_REQUEST` | 수신자 | 친구 요청 | ❌ 후속 |

> **`SIGN_REQUEST` 폐기 사유**: `soul-oath`에서 수락과 서명을 원자 요청으로 묶었으므로 *"수락은 했고 서명은 안 한"* 상태가 존재하지 않는다. 부를 대상이 없는 알림이다.
>
> DB는 `VARCHAR(30)`이라 **마이그레이션은 불필요**하나, V1 주석이 낡았으므로 `COMMENT ON COLUMN`으로 정정한다 (ADR-0010의 17건 선례).

### 0.6.1 🔴 새 타입의 **발송 개시**는 모바일 통지가 선행한다 — 2026-08-08 추가

**규약: 서버는 새 `NotificationType`의 발송을 시작하기 전에 모바일에 통지한다.**

⚠️ **enum에 값을 추가하는 것과 실제로 발송이 시작되는 것은 다른 사건이다.** 이 규약이 거는 것은
**후자**다. `NotificationType`은 그 자체로 *"어휘이지 구현 목록이 아니"*며(같은 이름의 enum KDoc),
8종이 이미 선언돼 있지만 **오늘 발송 가능한 것은 3종뿐**이다.

#### 오늘의 게이트 — `NotificationMessages.of()`

나머지 5종(`REMIND`/`OPPONENT_VERIFIED`/`RESULT`/`TAUNT`/`FRIEND_REQUEST`)은 `of()`가 **`null`을
반환**해 발송 자체가 막혀 있다. 그 함수 KDoc이 근거를 적어 뒀다 — *"빈 문자열이나 임시 문구를
만들어 내보내면 사용자에게 깨진 알림이 가므로, 문구가 없으면 아예 보내지 않는 쪽이 맞다."*

🔵 **이건 의도된 게이트지 미완성이 아니다.** 3종 외 도착은 오늘 **구조적으로 불가능**하다.

#### 🔴 그런데 게이트가 풀리는 방식이 위험하다

**`NotificationMessages`에 문구 한 벌을 추가하는 것만으로 새 타입이 즉시 실사용자에게 도달한다.**
서버 파일 하나를 고치는 일이고, 배관(`NotificationDispatcher` → `NotificationSender`)은 이미 전부
깔려 있어 **다른 어떤 승인 단계도 거치지 않는다.** 그리고 **모바일은 그 사실을 알 방법이 없다.**

**그래서 이 계약은 "문구 추가 = 발송 개시"로 간주한다.** 통지 시점의 기준선은 enum 값 추가가 아니라
`NotificationMessages.of()`에 해당 타입의 `Message`가 생기는 시점이다.

#### 통지 없이 개시하면 무슨 일이 나는가

구버전 앱의 `PushEvent.from`이 모르는 `type`을 `null`로 버린다. **크래시는 없다** — 그래서 문제다.
사용자에게는 **알림을 눌렀는데 아무 데도 가지 않는** 형태로 보이고, 앱은 열리므로 로그에도
크래시 리포트에도 아무것도 남지 않는다. `push-deeplink` spec §0.2가 *"조용히 홈에만 머무는"*
실패라고 부른 것과 같은 모양이다.

> **왜 코드 방어가 아니라 계약인가.** 게이트를 푸는 사람과 라우팅을 붙이는 사람이 서로 다른 레포에
> 있고, 서버 쪽 변경만으로 완결되기 때문에 **서버 안에는 모바일을 멈춰 세울 지점이 없다.**
> 사람 기억보다 계약이 안전하다.

#### 🔵 `FRIEND_REQUEST`는 통지 내용이 하나 더 있다

`NotificationType.FRIEND_REQUEST` KDoc이 *"`reference_id`가 challenge가 아닌 유일한 타입이 될
예정"*이라고 적어 뒀다. 이 타입이 개시되면 §0.1(`challengeId` 키 조건부 누락)과
§3.1(`android.notification` 블록 조건부 부재)이 **처음으로 실제 발생**한다. 통지에 **`referenceId`가
무엇을 가리키는지**를 함께 넣어야 한다 — 오픈 이슈 3이 `reference_id`를 `challenge_id`로 못 박지
않은 대가를 치르는 지점이다.

---

## 1. PUT `/api/v1/users/me/fcm-token` — FCM 토큰 등록·갱신 (신규)

### Request Body
```json
{ "fcmToken": "dGhpcyBpcyBhIGZha2UgdG9rZW4..." }
```

| 필드 | 타입 | 필수 | 비고 |
|---|---|---|---|
| `fcmToken` | string | ✅ | FCM 등록 토큰. blank 불가. **최대 4096자** |

> ⚠️ **2026-08-06 backend-dev 수정 — 초안의 "길이 상한 없음"을 4096자로 바꿨다.**
>
> `users.fcm_token`이 `TEXT`인 건 맞지만 **DB 상한 부재를 API 상한 부재로 옮긴 것이 오류였다.** 무제한 문자열을 받아 그대로 저장하면 요청 하나로 임의 크기를 밀어넣을 수 있다. 실제 FCM 등록 토큰은 150~250자 수준이라 4096은 20배 가까운 여유이며, **정상 토큰이 이 상한에 닿는 경로는 없다.** 초과 시 code 700.
>
> 선례: `KakaoLoginRequest`도 같은 이유로 `@Size(max = 2048)`을 갖고 있다.

### 성공 Response
```json
{ "error": false, "code": 200, "message": "" }
```

> 🔴 **`data` 키 자체가 없다. `null`이 오는 게 아니다.**
>
> `BaseResponse`는 `error`/`code`/`message` **3필드뿐**이고 `data`는 상속한 하위 클래스가 추가하는 것이다. 이 엔드포인트는 `BaseResponse()`를 그대로 반환하므로 **`data`가 직렬화되지 않는다.**
>
> **모바일에서 "키 없음"과 "키가 null"은 다른 예외를 낸다** (#25 감사 정리분):
> - 키 자체가 없음 → 기본값이 없으면 `MissingFieldException`
> - 키가 있고 값이 `null` → 필드가 non-nullable이면 `JsonConvertException`
>
> 즉 `data`를 nullable로 선언해도 **기본값이 없으면 여전히 깨진다.** 아예 선언하지 않는 것이 맞다.
>
> ⚠️ **2026-08-06 정정** — 최초 초안은 `"data": null`로 적었다. **서버가 보내지 않는 키를 보낸다고 말한 능동적 오류**로, `friends` 계약이 서버가 쓰지 않는 ISO-8601을 명시했던 것과 같은 계열이다(#25 감사). backend-dev가 모바일 T-M2 착수 전에 발견해 정정했다.

### 동작
1. `UPDATE users SET fcm_token = NULL WHERE fcm_token = :token AND id <> :me` (§0.2 소유권 이전)
2. `UPDATE users SET fcm_token = :token WHERE id = :me`

**멱등하다.** 같은 토큰을 여러 번 보내도 결과가 같다 — 모바일이 로그인 직후·`onNewToken` 양쪽에서 부르므로 중복 호출이 정상 경로다.

### 에러
| code | HTTP | 상황 | message |
|---|---|---|---|
| 700 | 200 | `fcmToken`이 blank (빈 문자열·공백만) | `FCM 토큰이 비어 있어요` |
| 700 | 200 | `fcmToken`이 4096자 초과 | `FCM 토큰 길이가 비정상입니다` |
| 401 | 401 | access 만료 | ADR-0009 — Ktor Auth가 자동 갱신 후 재시도 |
| 401 | 401 | 토큰의 `userId`가 DB에 없음 (탈퇴·삭제 후 access token이 아직 유효) | `user not found` |

> **🔴 blank는 "토큰 제거"가 아니라 거부다.** 빈 문자열을 제거로 해석하면 **모바일이 FCM 토큰 획득에 실패해 빈 값을 보냈을 때 조용히 알림이 꺼진다** — 사용자에게도 서버 로그에도 아무 신호가 없다. 제거는 `DELETE /auth/logout`(§2)만 한다.
>
> ⚠️ **401 두 줄은 HTTP status도 401이다.** ADR-0002가 "항상 HTTP 200"이라고 말하는 대상은 **700번대 UI 분류 코드**이고, 401은 HTTP status를 그대로 쓴다(`GlobalExceptionHandler`: `code in 400..599`면 그 status). 모바일 Ktor Auth(bearer)가 HTTP 401을 트리거로 refresh에 진입하기 때문이다. 이 프로젝트에 이미 깔린 규약이며 `GET /users/me`도 동일하다.

---

## 2. DELETE `/api/v1/auth/logout` — 로그아웃 (스텁 → 실구현)

### 계약 shape — **변경 없음**

요청 body 없음, header 인증. 응답:
```json
{ "error": false, "code": 200, "message": "" }
```

> 🔴 **§1과 동일 — `data` 키 자체가 없다.** `BaseResponse()`를 그대로 반환한다. (2026-08-06 정정, 최초 초안의 `"data": null`은 오류였다)

[foundation/api-contract.md](../foundation/api-contract.md)에 이미 *"Refresh 무효화, FCM 토큰 제거"*로 명문화돼 있었으나 [backend-report.md:86](../foundation/backend-report.md)에 미구현 TODO로 남아 있던 것을 **이번에 채운다.**

### 동작 (신규)
1. `users.refresh_token_hash = NULL` — ADR-0009 rotation 무효화
2. `users.fcm_token = NULL` — **그 기기로 이 계정 알림이 더는 가지 않는다**

**멱등하다.** 이미 로그아웃된 상태에서 다시 불러도 200.

> ⚠️ **logout만으로는 §0.2 문제가 안 막힌다.** 앱 삭제·강제 종료 시 호출되지 않기 때문이다. 등록 시점 방어(§0.2)와 **둘 다** 필요하다.

---

## 3. FCM 메시지 페이로드 규약 (REST 아님 — 서버 ↔ 모바일 계약)

```json
{
  "notification": { "title": "영혼의 맹세",
                    "body": "지연님이 당신과 계약하고 싶습니다" },
  "data": { "type": "CHALLENGE_REQUEST",
            "challengeId": "7" },
  "android": { "priority": "high",
               "notification": { "tag": "challenge-7" } }
}
```

| 키 | 타입 | 비고 |
|---|---|---|
| `data.type` | string | §0.6 타입 문자열 |
| `data.challengeId` | string | ⚠️ **FCM `data`는 값이 전부 문자열이다.** 숫자로 보내도 문자열로 도착하므로 모바일은 파싱해야 한다 |
| `android.priority` | string | 항상 `"high"`. §3.1 |
| `android.notification.tag` | string | `challenge-{referenceId}`. **`referenceId`가 없으면 `android.notification` 블록 자체가 빠진다.** §3.1 |

### 3.1 `android` 블록 — 2026-08-08 추가 (push-deeplink T-B1)

> ⚠️ **`notification`·`data` 블록은 무변경이다.** 이 절은 `android` 블록 **추가**만 다룬다.
> 모바일 파서는 손댈 것이 없다 — `android.notification.tag`는 **시스템 트레이가 소비하고 앱에
> 전달되지 않는다.**

**`tag = "challenge-{referenceId}"`** — 같은 도전장에 대한 알림을 트레이에서 **하나로 덮어쓴다**
([push-deeplink 판정 3](../push-deeplink/spec.md)). *"도전장이 왔다"* 뒤에 *"수락됐다"*가 따로
쌓이면 트레이만 지저분해지고, 사용자가 알아야 할 것은 **최신 상태 하나**다. 앱이 직접 그리는
포그라운드 경로는 이미 `challengeId`를 알림 id로 써서 덮어쓰고 있으므로 **백그라운드를
포그라운드에 맞추는 정합성 작업**이다 (`ChallengeFirebaseMessagingService`의
`buildNotificationId`. `null`이면 `currentTimeMillis()`로 갈라놓는 것까지 서버와 방향이 같다).

> ⚠️ **행 번호를 적지 않는다.** 이 문서가 한 번 `:131`로 적었다가 틀렸다 — 실제로는 128행이고,
> 그 사이 `showNotification` 시그니처가 `(title, body, type, challengeId)` → `(title, body, data:
> Map<String,String>)`로, 키 상수가 `PushEvent.KEY_CHALLENGE_ID`로 바뀌었다. **남의 레포 파일은
> 이 문서보다 빨리 움직인다.** 함수 이름으로 가리키면 낡지 않는다.

⚠️ **두 경로가 같은 논리 키로 묶는 것은 우연이 아니라 결정이다.** 값이 같을 필요는 없지만
(문자열 tag vs Int id, 전달 경로도 다르다) **키가 갈라지면 같은 도전장 알림이 포그라운드에선
합쳐지고 백그라운드에선 따로 쌓인다** — 크래시 없이 조용히 어긋난다.

🔴 **`referenceId`가 `null`이면 tag를 붙이지 않는다.** `"challenge-null"`로 뭉치면 서로 무관한
알림들이 한 덩어리가 되어 서로를 덮어쓴다 — **예외도 로그도 없이 알림이 사라진다.** `putData`가
`challengeId` 키를 조건부로 넣는 것과 **같은 이유·같은 판단**이며, 오픈 이슈 3(*`reference_id`를
`challenge_id`로 못 박지 않는다*)이 현실이 되는 순간 이 분기가 유일한 방어다.

**`priority = "high"`** — **오늘 기준으로 동작이 바뀌지 않는다.** FCM은 `notification`을 포함한
메시지를 이미 high로 취급하고(data-only만 normal이 기본) 우리 페이로드는 혼합이다(§0.5). 즉
새 동작을 켜는 게 아니라 **현재의 실효 동작을 명시로 고정**하는 것이고, 나중에 페이로드가
data-only로 바뀌어도([push-deeplink 판정 4](../push-deeplink/spec.md)에서 **보류**, 폐기 아님)
즉시성이 조용히 normal로 떨어지지 않는다.

⚠️ **`RESULT`(자정 판정 배치)·`REMIND`(마감 1시간 전 배치)가 붙을 때 재검토할 것.** 자정 배치가
전 사용자 기기를 한꺼번에 Doze에서 깨우는 것은 high 남용 패턴 그 자체다. 현재 3종은 전부
**사용자 행동이 즉시 유발한 1:1 알림**이라 해당하지 않는다. 타입별 분기는 **미리 만들지 않았다** —
해당 타입이 없어 근거를 정할 수 없다.

**회귀 장치**: `FcmNotificationSenderTest` +6건. `AndroidConfig`는 공개 getter가 없어
firebase-admin이 실제 전송에 쓰는 직렬화 경로(`@Key` + `JsonFactory`)를 그대로 태워 **JSON 원문**
으로 단언한다 — 술어를 Kotlin으로 다시 쓰지 않고 나가는 바이트를 본다(§0.2 fake 문제의 반대편).
그중 1건은 **`android.notification`에 `tag` 외 필드가 새어 들어가지 않는지**를 고정한다. FCM은
`android.notification`의 설정된 필드만 공통 `notification`을 덮어쓰므로, 빈 title/body가 실리면
**§3 문구 3종이 통째로 무력화되고 제목 없는 알림이 뜬다.**

### 문구 — 🟡 **1종 확정 / 2종 초안** (2026-08-07 사용자, 커밋 `e76c64c`)

⚠️ **아래는 `NotificationMessages` 실측값이다.** 이 표는 코드를 따라간다 — 서버 코드가 정본이다.

| type | title | body | 확정 상태 |
|---|---|---|---|
| `CHALLENGE_REQUEST` | `영혼의 맹세` | `{actorNickname}과 계약을 하시렵니까?` | ✅ **사용자 확정** |
| `CHALLENGE_ACCEPTED` | `계약 완료.` | `{actorNickname}님이 수락했습니다` | 🟡 **초안** — 디자인 확인 후 바뀔 수 있다 |
| `CHALLENGE_REJECTED` | `ㅠㅠ` | `{actorNickname}님이 도망쳤습니다` | 🟡 **초안** — 디자인 확인 후 바뀔 수 있다 |

> 🔵 **문자열이 최신인 것과 문구가 확정된 것은 다르다.** 세 값 모두 코드 실측값이 맞지만,
> **확정된 것은 `CHALLENGE_REQUEST` 하나**다. 나머지 둘은 초안이 교체된 것이지 확정된 것이 아니다.

닉네임 부재 시 `UNKNOWN_NICKNAME = "(알 수 없음)"`.

> ⚠️ **이 표가 세 번 낡았다.**
> 1. 최초 계약 초안: `새 도전장이 왔어!` / `도전이 성사됐어!` / `도전이 거절됐어` (전부 반말)
> 2. 중간 기재: `CHALLENGE_REQUEST` 를 `{닉}님이 당신과 계약하고 싶습니다` 로 적었으나 **실제 코드는 `{닉}과 계약을 하시렵니까?`** 였고, 나머지 2종은 "초안 반말"로 남아 있었으나 **코드는 이미 교체돼 있었다**
> 3. 🔴 **2026-08-08 backend-dev 정정 — 앞의 정정이 반대편으로 넘어갔다.** 2026-08-07 에 이 절을 *"3종 전부 확정"* 으로 적으면서 근거로 커밋 `e76c64c` 를 들었는데, **`git show e76c64c` 를 보면 그 커밋은 정반대다** — `"## 🟡 문구 미확정"` → `"1종 확정 / 2종 초안"` 으로 바꾼 커밋이고, *"나머지 둘은 아직 초안이다"* 를 사용자가 그 커밋에서 직접 써 넣었다. **문자열이 바뀐 것을 확정으로 읽은 오독**이다.
>
> `soul-oath` 에서 *"프리뷰를 고치면 design.md를 그 자리에서 맞춘다"* 로 정리한 것과 같은 계열의 드리프트다. **문구는 `NotificationMessages` 한 곳에만 있으므로 코드에서 실측해 이 표를 갱신하는 것이 유일한 정본 유지 방법이다.**
>
> 🔵 **다만 3번은 "코드를 안 봐서" 생긴 게 아니다.** 문자열은 정확히 옮겼고 **상태 표기만 틀렸다.** 같은 파일의 **KDoc 이 확정 상태의 정본**이라는 점을 이번에 추가로 명시한다 — 문자열만 보면 확정 여부를 알 수 없다.
>
> ⚠️ **세 종의 톤이 균일하지 않다. 단 갈린 축은 `title` 이지 존댓말/반말이 아니다** — `body` 는 **셋 다 합니다체**이고(`~하시렵니까?` / `~수락했습니다` / `~도망쳤습니다`), 갈리는 것은 제목이다: `영혼의 맹세`(제품 개념명) / `계약 완료.`(평서 단정) / `ㅠㅠ`(구어). [challenge-create/design.md §9](../challenge-create/design.md)가 지적한 **Lovable 화면별 톤 불일치**와 같은 축이다.
>
> 🔴 **`NotificationMessages` KDoc 도 한때 2종을 "반말" 이라고 적었다 — 사실이 아니었고 2026-08-08 에 정정했다.** `e76c64c` 가 문자열을 존댓말로 교체하면서 상태 표기를 함께 고치지 못한 흔적이다. **톤을 확정할 사람이 그 표를 보고 판단하므로, 표가 현재 톤을 잘못 말하면 판단 자체가 틀어진다.**
>
> 🔴 **남은 2종 확정·전역 톤 통일은 push-deeplink 범위 밖이다. 임의로 통일하지 마라** — 특히 **확정분(`CHALLENGE_REQUEST`)을 초안에 맞추는 방향은 안 된다**(`NotificationMessages` KDoc 의 지시). 백로그 / push-fcm summary 미해결 🟢 *"알림 문구 톤 불균일"* 항목에서 다룬다.
>
> ✅ **문구 변경에 모바일 코드 수정은 불필요하다** — 서버가 `title`/`body`를 만들어 보내고 모바일은 그대로 표시한다(§0.5 혼합 페이로드). 테스트도 **문자열을 단언하지 않아** 문구 교체로 깨지지 않는다.

### 수신자에게 `fcm_token`이 없을 때
발송을 **건너뛰되 `notifications` row는 저장한다.** 요청은 정상 성공(200)이다. 알림 권한 거부·로그아웃 상태가 챌린지 기능을 막으면 안 된다.

### 발송 실패 처리
FCM이 `UNREGISTERED` / `INVALID_ARGUMENT`를 반환하면 **해당 `fcm_token`을 `NULL`로 정리한다.** 죽은 토큰을 남겨두면 이후 모든 발송이 실패한다.

---

## 오픈 이슈

### ✅ 3. `reference_id` 의미 — **해소 (2026-08-06, backend-dev 제안 채택)**

**`challenge_id`로 못 박지 않는다.** 이름은 중립으로 두고, 참조 대상이 타입에 따라 다르다는 사실을 **`COMMENT ON COLUMN`에 적는다.**

> `soul-oath`의 `_signature_url` → `_signature_data` 와 같은 판단이다. *"`_url`이 문제였던 이유는 **저장 표현을 컬럼 이름에 박았다**는 것"* — `reference_id`를 지금 "= `challenge_id`"로 규정하면 `FRIEND_REQUEST`가 붙는 순간 **이름이 거짓이 되거나 컬럼을 새로 파야 한다.**
>
> **현재 3종이 전부 challenge라는 건 오늘의 사실이지 규약이 아니다.** 이름은 중립적으로, 형식·의미는 검색 가능한 곳에 — ADR-0010의 주석 17건, V7의 6건과 같은 선례다.

주석 문안(대략): *"알림 타입에 따라 참조 대상이 다르다. 현재 `CHALLENGE_REQUEST`/`CHALLENGE_ACCEPTED`/`CHALLENGE_REJECTED` 3종은 전부 `challenges.id`. 타입 추가 시 이 주석을 갱신할 것."*

**T-B3가 어차피 `COMMENT ON COLUMN`을 손대는 태스크이므로 여기서 함께 닫는다.**

### 미해소 — **단, T-B1~T-B3(#32)를 막지 않는다**

| # | 이슈 | #32 영향 | 귀속 |
|---|---|---|---|
| 4 | 🔴 **`LogoutUseCase`가 서버를 호출하지 않는다** — 로컬 토큰 정리만 한다(mobile-dev 실측). 그래서 §2의 `fcm_token = NULL`이 앱에서 한 번도 발생하지 않는다. **지금은 무해하지만 `push-fcm`이 들어가는 순간 로그아웃 후에도 그 기기로 알림이 계속 간다.** ⚠️ 이건 **가정이 아니라 미구현 기능**이다 — 기능이 들어가면 확정적으로 깨진다. §0.2 소유권 이전이 계정 전환은 덮지만 **"로그아웃하고 아무도 로그인하지 않은 기기"** 는 못 덮는다.<br>🔴 **한 줄 추가로 끝나지 않는다. 함정 2개가 있다** (mobile-dev 발견, pm-lead 실측 확인):<br>**(1) Bearer 토큰이 안 붙는다.** `KtorfitModule.kt:103`이 `sendWithoutRequest { request.url.pathSegments.none { it == "auth" } }` 다 — **경로에 `auth` 세그먼트가 있으면 토큰을 선제 전송하지 않는다.** `/auth/kakao`(로그인)·`/auth/refresh`(갱신)가 토큰 없이 나가야 해서 만든 규칙인데, **`/auth/logout`이 같은 경로 밑에 있다는 이유로 함께 걸린다.** 그런데 §2는 Bearer 필수다 — `SecurityConfig`의 permitAll은 `POST /auth/kakao`·`/auth/refresh`·`/auth/test-login` 뿐이고 logout은 `anyRequest().authenticated()`에 걸린다.<br>⚠️ **그래서 첫 요청은 반드시 401을 맞는다. 그 다음이 검증되지 않았다** — Ktor Auth의 401 재시도는 응답의 `WWW-Authenticate` challenge를 보고 동작하는데, **`UnauthorizedEntryPoint`는 HTTP 401 + JSON body만 주고 그 헤더를 보내지 않는다.** 재시도가 돌면 불필요한 토큰 rotation 1회를 거쳐 성공하고, 안 돌면 **서버 `fcm_token`이 안 지워진 채 로컬만 정리돼 겉보기엔 로그아웃이 성공한 것처럼 보인다.** 🔴 **어느 쪽인지는 실측 전까지 단정할 수 없다.** 이 불확실성 자체가 401 경로에 기대지 말아야 할 이유다.<br>→ 해법은 `sendWithoutRequest`를 **경로 전체가 아니라 엔드포인트 단위**(`kakao`/`refresh`/`test-login`만 제외)로 좁히는 것인데, **이미 동작 중인 인증 경로를 건드리는 변경**이라 회귀 위험이 있다. `auth-refresh-rotation`이 401 처리를 여기 한 곳으로 모아둔 구조라 영향 범위가 넓다.<br>**(2) 테스트 계정 전환마다 서버 호출이 나간다.** `LogoutUseCase`는 `LoginWithTestAccountUseCase` 안에서도 호출된다(계정 전환 시 캐시 정리). §0.2가 서버에서 소유권을 정리하므로 아마 무해한 중복이지만, `dev-test-login`이 표준 검증 방식인 만큼 그 경로가 매번 서버를 때리는 게 의도인지 확인이 필요하다 | 🔴 **있음** | **사용자 결정 대기** — T-M2 편입 vs 백로그 |
| 1 | 🟡 **부분 해소 (2026-08-07 사용자, 커밋 `e76c64c`)** — **`CHALLENGE_REQUEST` 1종만 확정이고 나머지 2종은 여전히 초안값**이다. §3 표는 `NotificationMessages` 실측값으로 갱신돼 있다.<br>🔴 **2026-08-08 backend-dev 정정** — 이 행이 *"✅ 해소 — 3종 전부 확정"*이라고 적고 있었다. §3 헤더와 **같은 오독**이며(문자열 교체 = 문구 확정으로 읽음), `e76c64c` 의 KDoc 은 오히려 2종을 🟡 초안으로 표시한다. §3 의 "세 번째 드리프트" 항목과 같은 건이다.<br>**남은 2종 확정·전역 톤 통일은 사용자 결정**이고 백로그 / summary 미해결 🟢 *"알림 문구 톤 불균일"* 로 열려 있다 | ❌ 없음 — **아무것도 막지 않는다.** 문구 변경은 계약 shape 을 바꾸지 않고(서버가 `title`/`body` 를 만들어 보내고 모바일은 그대로 표시), 테스트도 문자열을 단언하지 않는다 | **사용자 결정 대기** (백로그) |
| ~~2~~ | ✅ **해소 (2026-08-06 pm-lead)** — **박제한다.** 발송 시점의 `title`/`body`를 그대로 저장한다. **스키마가 이미 그렇게 정해져 있다** — V1의 `notifications.title VARCHAR(100) NOT NULL` / `body TEXT NOT NULL`은 렌더된 문구를 담는 모양이다. 재조립 방식이면 이 두 컬럼이 놀거나 템플릿 키가 들어가야 하는데, 그건 스키마 변경이고 이번 범위가 아니다. 부수 효과로 **문구를 나중에 바꿔도 과거 알림이 그대로 남는다** — 알림은 *"그때 이렇게 통지했다"*는 기록이므로 이게 오히려 맞다. ⚠️ 대가: 문구 오타를 고쳐도 기존 row는 안 바뀐다. row가 0건인 지금은 무해하다 | ❌ 없음 | — |

> 🔴 **따라서 `draft` 상태이지만 T-B1(토큰 등록)·T-B2(logout)·T-B3(타입 재정의)는 착수 가능하다.** §0.1/§0.2/§0.6이 이미 확정이고, 남은 두 이슈는 **발송부(#33)에만 걸린다.** 계약 전체의 `confirmed` 전환은 #33 착수 전에 한다.

---

## 협의 이력

### 2026-08-06 — backend-dev, T-B1~T-B3 구현 중 발견분 (`draft` 단계 직접 수정)

`draft` 상태이고 이 문서의 소유자가 backend-dev이므로 **묻지 않고 고친 뒤 여기에 등재한다.** 셋 다 **초안이 서버 실구현·기존 규약과 어긋난 지점**이지 설계 변경이 아니다.

| # | 위치 | 초안 | 수정 | 왜 |
|---|---|---|---|---|
| 1 | §1 Request | `fcmToken` **길이 상한 없음** | **최대 4096자** (초과 시 code 700) | `users.fcm_token`이 `TEXT`인 건 맞지만 **DB 상한 부재를 API 상한 부재로 옮긴 것이 오류**였다. 무제한 문자열을 받아 그대로 저장하면 요청 하나로 임의 크기를 밀어넣을 수 있다. 실제 토큰은 150~250자라 20배 여유 — **정상 토큰이 상한에 닿는 경로가 없다.** `KakaoLoginRequest`의 `@Size(max = 2048)` 선례. |
| 2 | §1 에러 표 | 700(blank) / 401(access 만료) 2행 | **4행** — 700(길이 초과), 401(토큰의 `userId`가 DB에 없음) 추가 + HTTP status 열 추가 | 탈퇴·삭제 계정의 access token이 아직 유효한 경우가 빠져 있었다. `GET /users/me`와 같은 처리(401)로 맞췄다. **조용히 200을 주면 모바일은 등록됐다고 믿는다.** HTTP status 열은 "401은 HTTP도 401"이라는 기존 규약(ADR-0002의 항상-200은 **700번대**에만 적용)을 명시하려고 추가했다. |
| 3 | §1/§2 성공 Response | `"data": null` | `data` 키 **없음** | pm-lead가 먼저 정정 완료 — backend-dev도 독립적으로 같은 결론에 도달했고 **실구현이 그 정정과 일치한다**(`BaseResponse()` 그대로 반환). 서버 회귀 장치로 `jsonPath("$.data").doesNotExist()`를 슬라이스 테스트 2곳에 박았다. |

**뒤집지 않은 것**: §0.2 소유권 이전, §0.3 AFTER_COMMIT. 근거가 명확해 그대로 구현했다.

### 구현 상태 (2026-08-06, working tree — 커밋 전)

| 엔드포인트 | 상태 | 회귀 장치 |
|---|---|---|
| PUT `/api/v1/users/me/fcm-token` | ✅ implemented (미배포) | `UserServiceFcmTokenTest` 6건, `UserControllerTest` +5건 |
| DELETE `/api/v1/auth/logout` | ✅ implemented (미배포) — 스텁 대체 | `AuthServiceLogoutTest` 4건, `AuthControllerTest` +3건 |
| `NotificationType` enum + `V8` 컬럼 주석 | ✅ implemented (V8 **미적용** — dev DB는 V7) | `NotificationTypeTest` 3건 |
| §0.4 no-op 격리 (`NotificationSender` + Fcm/NoOp) | ✅ implemented — **서비스 계정 키 없이 동작 중** | `FirebaseCredentialsLoaderTest` 8건, `NotificationSenderConfigTest` 4건, `FcmNotificationSenderTest` 4건 |
| §0.3 이벤트 배관 (`AFTER_COMMIT` + `REQUIRES_NEW`) | ✅ implemented | `NotificationDispatcherTest` 12건, `NotificationDispatcherWiringTest` 2건, `ChallengeCommandServiceTest` +5건 |
| §3 문구 3종 | ✅ `CHALLENGE_REQUEST` 확정 / 🟡 나머지 2종 초안 | `NotificationMessagesTest` 4건 (문자열은 단언하지 않는다) |

> **§3 문구는 `NotificationMessages` 한 곳에만 있다.** 확정되면 그 파일만 고치면 되고, 코드 곳곳에 흩어진 문자열을 찾아다닐 일이 없다. 테스트도 **문자열을 단언하지 않는다** — 지금 박아 두면 문구를 바꿀 때마다 테스트가 깨지는데 그 깨짐이 아무것도 알려주지 않는다. 대신 "3종은 문구가 있다 / 트리거 없는 타입은 null이라 발송하지 않는다"만 고정했다.
>
> ⚠️ **`AFTER_COMMIT` + `REQUIRES_NEW`는 어노테이션 존재만 검증된다.** `NotificationDispatcherWiringTest`는 *"정말 커밋 후에 도는가 / 정말 새 트랜잭션에서 커밋되는가"*를 증명하지 못한다 — 실제 트랜잭션 매니저와 DB가 필요하고 그건 skip 중인 통합 테스트뿐이다. 막으려는 실패 모드가 **"누가 어노테이션을 지운다"**라서 그 지점만 정확히 겨눈 구조적 단언이다.
>
> ⚠️ **실제 FCM 발송은 한 번도 실행된 적이 없다.** 서비스 계정 키가 없어 전 구간이 `NoOpNotificationSender`로 흐른다. `send()`의 메시지 빌드·호출·catch는 어떤 테스트도 태우지 않으며, 검증된 것은 **에러 코드 분류(`resultFor`)뿐**이다. 실발송은 T-U3(키 발급) 후 실기 검증 대상이다.

> ⚠️ **§0.2 소유권 이전 SQL의 `AND id <> :me`는 실행 중인 테스트가 검증하지 못한다.** 서비스 단위 테스트는 fake가 그 조건을 재현하는 것이고, 실제 JPQL은 Testcontainers 통합 테스트(컨테이너 런타임 부재로 45건 skip 중)에서만 실행된다. 2026-08-06에 로컬 Postgres로 **1회 수동 검증**했다(JPQL 파싱·실행 확인, 영향 0행). 상시 자동 검증은 통합 테스트 skip이 풀려야 생긴다.
| 2026-08-07 | backend-dev | ✅ **`CHALLENGE_REQUEST` 문구 사용자 확정** — `새 도전장이 왔어! / {닉}님이 도전장을 보냈어` → **`영혼의 맹세` / `{닉}님이 당신과 계약하고 싶습니다`**. 제품 개념명을 제목으로 쓰고 본문이 계약 제안이라 **격식체**이며, `soul-oath` 계약서 본문이 격식체인 것과 같은 결이다. ⚠️ **나머지 2종은 초안(반말) 그대로라 지금 톤이 갈려 있다** — 확정분을 초안에 맞춰 되돌리지 말고, 나머지를 확정할 때 함께 정한다. 코드는 `NotificationMessages` 한 곳만 변경, 테스트는 문자열을 단언하지 않아 무변경(254/254 passed) |
