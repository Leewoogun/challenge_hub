# API Contract — 알림 목록 (notification-list)

- **feature-id**: notification-list
- **상태**: 🟡 **`negotiating`** — §2(shape)·§3(페이지네이션)·§5(모르는 타입)는 백엔드 결정으로 확정.
  **§4 읽음 처리만 소비자(noti-mobile·noti-design) 판정 대기.**
- **소유**: backend-dev (noti-backend)
- **작성**: 2026-09-01 backend-dev
- **상위 spec**: [spec.md](./spec.md)
- **선행 계약**: [push-fcm/api-contract.md](../push-fcm/api-contract.md) — `notifications` row 저장·`reference_id` 규약·타입 어휘

## 요약 — 신규 1건

| # | Method | Path | 인증 | 설명 | 상태 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/notifications` | Bearer | 알림 목록 — 최신순, **커서 페이지네이션** | 🟡 negotiating |
| 2 | — | (읽음 처리) | — | §4 — **도입 여부 미정** | ⏸ 판정 대기 |

공통:
- ADR-0002 BaseResponse — 성공·비즈니스 에러는 HTTP 200 + body `code`. 인증 실패만 bare HTTP 401.
- ADR-0010 시간 규약 — `yyyy-MM-dd HH:mm:ss` (KST). `T`·`Z`·offset·밀리초 없음.
- 인증은 `SecurityFilterChain` 의 `.anyRequest().authenticated()` 가 이미 덮는다 —
  **`SecurityConfig` 변경 0건.** `/api/v1/notifications` 는 permitAll 목록에 없다.

---

## 1. GET `/api/v1/notifications` — 알림 목록

### 요청

```
GET /api/v1/notifications                      # 🔴 첫 호출은 파라미터 없이
GET /api/v1/notifications?cursor=57&size=20    # 다음 페이지
Authorization: Bearer {accessToken}
```

| 이름 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `cursor` | long | ✗ | 없음(= 맨 앞) | **직전 응답의 `nextCursor` 를 그대로 되돌려 보낸다.** 이 값보다 `id` 가 작은 것부터 |
| `size` | int | ✗ | **20** | 한 번에 받을 개수. `1..50` |

🔴 **첫 호출이 파라미터 없이 성립하는 것이 설계다.** 앱은 커서를 **만들지 않는다** — 서버가 준
값을 되돌려 보내기만 한다. 보관함 `?month=` 가 optional 인 것과 같은 판단이며
([mypage §1](../mypage/api-contract.md)), 클라이언트가 경계값을 스스로 계산하지 않게 하는 것이
이 프로젝트의 반복 규약이다.

`?cursor=` / `?size=` 가 **빈 문자열**이면 미지정과 같이 다룬다 (보관함 `?month=` 와 동일).

### 응답 — 성공

```json
{
  "error": false, "code": 200, "message": "",
  "data": {
    "notifications": [
      {
        "notificationId": 57,
        "type": "CHALLENGE_ACCEPTED",
        "title": "계약 완료.",
        "body": "민수님이 수락했습니다",
        "referenceId": 1001,
        "createdAt": "2026-09-01 13:42:07"
      }
    ],
    "nextCursor": 38
  }
}
```

| 필드 | 타입 | null | 설명 |
|---|---|---|---|
| `notifications` | array | non-null (**빌 수 있다**) | `id` 내림차순 = 최신순 |
| `nextCursor` | long | 🔴 **nullable** | 다음 페이지의 `cursor`. **`null` 이면 끝이다** |

#### `notifications[]` 항목

| 필드 | 타입 | null | 설명 |
|---|---|---|---|
| `notificationId` | long | non-null | 알림 row id |
| `type` | **string** | non-null | §5 — 🔴 **열린 집합이다. enum 으로 받지 마라** |
| `title` | string | non-null | 발송 시점 문구 **박제값** |
| `body` | string | non-null | 발송 시점 문구 **박제값** |
| `referenceId` | long | 🔴 **nullable** | 목적지 id. 타입에 따라 참조 대상이 다르다 — §6 |
| `createdAt` | string | non-null | `yyyy-MM-dd HH:mm:ss` KST. 앱이 상대 시각으로 변환 |

⚠️ **`nextCursor` / `referenceId` 가 `null` 이어도 키는 항상 실린다** — 이 프로젝트 Jackson 에
`@JsonInclude(NON_NULL)` 설정이 없다(mypage `WireShapeContractTest` 실측분). 모바일은 키 존재를
전제해도 된다.

### 🔴 `title` 과 `body` 를 **둘 다** 내린다

Lovable `notifications.tsx` mock 은 메시지 **1줄**만 그린다. 그런데 이 화면의 존재 이유가
*"푸시를 놓치면 그걸로 끝"* 을 메우는 것이고(spec 배경), **푸시는 title + body 두 줄을 보여준다**
(push-fcm §0.5 혼합 페이로드). 목록이 `body` 만 그리면 **같은 사건을 푸시보다 적은 정보로**
복구하게 된다 — 복구 경로가 원본보다 손실이 있으면 화면의 목적이 절반만 달성된다.

두 값 다 **이미 DB 에 박제돼 있다**(push-fcm 오픈이슈 2 해소분 — `notifications.title`/`body` 에
발송 시점 문구를 그대로 저장). 서버가 만들 것이 없다.

> 🟡 **design(T-D1) 이 `title` 을 안 그리기로 하면 알려 달라.** 그때 필드를 빼는 것이 맞다 —
> 안 그리는 필드를 내리는 것은 spec 이 금지한 *"앱이 그리는 것만"* 위반이다. 다만
> **뺄 때 breaking 이므로 T-D1 확정 전까지는 내려 두는 쪽**이 안전하다(나중에 넣는 것은 추가,
> 내리다 빼는 것은 파괴).

### 에러

| code | HTTP | 상황 | message |
|---|---|---|---|
| 700 | 200 | `size` 가 정수가 아니거나 `1..50` 밖 | `한 번에 받을 개수가 올바르지 않아요` |
| 700 | 200 | `cursor` 가 정수가 아님 | `목록 위치가 올바르지 않아요` |
| 401 | **401** | access 만료 | ADR-0009 — Ktor Auth 가 자동 갱신 후 재시도 |

🔴 **`size` 범위를 벗어나면 clamp 하지 않고 거부한다.** 조용히 50 으로 깎으면 앱은 100 개를
받았다고 믿고 커서를 잘못 이어 붙인다. 보관함이 미래 달을 clamp 하지 않고 code 700 으로 끊는
것과 같은 판단이다(*"조용히 clamp 하면 응답의 에코가 요청과 달라져 화면에서 어긋난다"*).

⚠️ **`cursor` 가 존재하지 않는 id 여도 에러가 아니다.** `id < cursor` 조건이라 그냥 그보다
작은 것들이 나온다. 삭제된 알림을 커서로 들고 있어도 목록이 이어진다 — 이게 커서를
`id` 로 잡은 부수 효과다.

---

## 2. 🔴 페이지네이션 도입 — **이 프로젝트 최초다. 근거를 남긴다**

### 왜 여기서 도입하나

백로그 *"페이지네이션 일괄 도입 시점 결정"* 은 2026-08-28 에 우선순위가 내려갔다. 내려간
근거가 이것이다:

> ~~"계약서 보관함이 프로젝트 최초의 무한히 자라는 목록"~~ — **보관함이 월 단위 조회로
> 개정되면서 한 응답 상한이 한 달치로 고정**돼 그 전제가 소멸했다(1순위 트리거였다).

🔴 **알림이 그 자리를 그대로 물려받는다.** 보관함은 *월* 이라는 축이 페이지 경계 역할을 했는데
**알림에는 그런 축이 없다**:

| | 보관함 | 알림 |
|---|---|---|
| 자연 경계 | ✅ 월 (`?month=`) | ❌ **없다** |
| 증가 속도 | 챌린지 1건당 1행 | **챌린지 1건당 2~4행** (신청·수락/거절·인증) |
| 상한 | 한 달치 | **없음 — 계정 수명 내내 append** |

백로그가 기다리던 *"만기 신호"* 가 이 feature 다. **여기서 안 하면 첫 응답이 사용자 수명 전체를
싣게 되고, 그건 나중에 고칠 때 breaking change 다.**

### 🔴 커서를 고른다 — offset 은 알림에 한해 **상시 깨진다**

| | offset (`?page=&size=`) | **커서 (채택)** |
|---|---|---|
| 머리에 새 행이 들어오는 동안 | 🔴 페이지가 밀려 **2페이지에 1페이지 항목이 다시 나온다** | ✅ 영향 없음 |
| 총 개수 | 제공 가능 | 제공 안 함 (필요 없다 — "1/N 페이지" 를 그리지 않는다) |
| Spring 지원 | `Pageable` 기성품 | JPQL 직접 |

**알림은 정의상 새 행이 목록 머리에 꽂히는 유일한 화면**이다. offset 의 shift 문제가 다른
목록에서는 드문 경합이지만 **여기서는 상시 조건**이다 — 사용자가 목록을 스크롤하는 동안
상대가 인증 한 번만 해도 발생한다. 이 하나로 결정된다.

### 정렬·커서 키가 **둘 다 `id`** 인 이유 — `created_at` 이 아니다

```sql
WHERE user_id = :me AND (:cursor IS NULL OR id < :cursor)
ORDER BY id DESC
LIMIT :size + 1
```

🔴 **`created_at` 은 DB 가 아니라 서버 Kotlin 이 만든다** — `NotificationEntity.createdAt` 의
기본값이 `KstTime.now()` 다(컬럼 DEFAULT 는 있지만 엔티티가 항상 값을 채워 보내므로 쓰이지
않는다). 즉 **NTP 보정으로 시계가 뒤로 밀리면 `created_at` 순서와 삽입 순서가 어긋난다.**
커서가 그 위에 서 있으면 **어긋난 구간의 행이 통째로 건너뛰어진다 — 예외도 로그도 없이.**

`id` 는 `BIGSERIAL` 이라 삽입 순서와 정확히 일치하고, append-only 테이블이라 **`id` 순서 = 최신순**
이다. 그래서:

- **표시는 `createdAt`, 순서는 `id`** 로 분리한다. 두 값이 어긋나도 목록이 빠지지 않는다.
- **동률이 없다.** `created_at` 정렬은 같은 배치에서 나간 알림 2건이 같은 값을 가질 수 있어
  복합 커서(`(createdAt, id)`)가 필요해지는데, `id` 단독은 그 표면이 아예 없다.
- 보관함이 `ORDER BY challengeDate DESC, c.id DESC` 로 `id` 를 tiebreak 에 쓰는 것과 같은 결이다.

### `nextCursor: Long?` — 불리언 `hasNext` 를 쓰지 않는다

[mypage §1](../mypage/api-contract.md) 이 `hasPrevious`/`hasNext` 를 기각하고 절대값
(`firstArchivedMonth`)으로 간 선례를 그대로 따른다. 여기서는 그 논거가 더 직접적이다 —
**`nextCursor` 는 앱이 다음 요청에 그대로 실어야 하는 값 자체**다. 불리언을 주면 앱이
*"마지막 항목의 `notificationId` 를 커서로 쓴다"* 는 **규칙의 사본**을 갖게 되고, 나중에 서버가
커서 표현을 바꾸면 그 사본이 조용히 틀린다. 절대값은 앱에 규칙을 두지 않는다.

`null` 하나가 *"끝"* 을 뜻하므로 경쟁하는 신호도 없다.

> **서버 구현**: `size + 1` 건을 읽어 초과분이 있으면 잘라 내고 마지막 항목의 `id` 를
> `nextCursor` 로, 없으면 `null`. **`COUNT` 쿼리를 걸지 않는다.**

### 🔴 이 shape 이 프로젝트 페이지네이션 규약이 된다

CLAUDE.md: *"페이지네이션은 프로젝트 전체에서 한 방식으로 통일."* 이 계약이 그 방식을 연다.

**나머지 4종(친구 목록·받은 요청·랭킹·보관함)을 지금 따라 고치지 않는다** — 보관함은 월이 이미
경계이고, 나머지 3종은 백로그가 말한 *"수백 건 도달"* 신호가 아직 없다. 다만 **다음에 도입하는
쪽은 이 shape 을 따른다**: `?cursor=&size=` + `data.nextCursor: <키>?`, 정렬·커서 키 동일, 불리언
금지. ADR 승격 여부는 pm 판단.

### 인덱스는 **추가하지 않는다** — 판단 근거를 남긴다

V1 의 `idx_notifications_user_read_created (user_id, is_read, created_at DESC)` 는
**안 읽은 개수용**이지 이 쿼리용이 아니다. `WHERE user_id=? ORDER BY id DESC` 에는 선두 컬럼
(`user_id`)만 쓰이고 정렬은 별도로 일어난다.

그럼에도 지금 인덱스를 만들지 않는 이유:

- **페이지네이션과 인덱스는 되돌리는 비용이 다르다.** 페이지네이션은 **계약**이라 나중에 바꾸면
  breaking 이고, 인덱스는 **1줄 마이그레이션**이라 계약 영향 0으로 아무 때나 붙는다. 지금
  정해야 하는 것은 앞의 것뿐이다.
- 한 사용자의 행 수는 계정 수명 내내 쌓여도 수천 단위이고, 그 정도 정렬은 측정 가능한 비용이
  아니다. **"목록이 무한히 자란다"는 앱이 받아 그려야 하는 payload 얘기이지 DB 정렬 비용 얘기가
  아니다** — 둘을 같은 근거로 묶으면 안 된다.
- 🔴 **붙일 트리거**: 이 쿼리가 느려진 것이 **관측되면** `(user_id, id DESC)` 를 추가한다.
  관측 전에 만들지 않는 것은 이 프로젝트 방침이다.

---

## 3. 🔴 모르는 타입 — `type` 은 **열린 집합**이다 (§5 로 이동, 아래 참조)

---

## 4. ⏸ 읽음 처리 — **도입 여부 판정 대기** (spec 오픈이슈 1)

`notifications.is_read` 는 **V1 부터 있다.** API 자체는 싸다. 문제는 그게 아니다.

### 백엔드 의견: **1차에서 뺀다 (A안)**

**읽음 표시는 그것을 *보여주는 것*이 있어야 값이 생기는데, 그 둘이 다 spec 비범위다.**

| 보여주는 곳 | spec 상태 |
|---|---|
| 목록 행의 읽음/안읽음 시각 구분 | 범위 안 (design 판단) |
| 홈 벨 **안 읽은 개수 뱃지** | 🔴 **명시적 비범위** |

뱃지 없이 행 구분만 넣으면 사용자가 얻는 것은 *"굵은 글씨가 안 굵어진다"* 하나다. 대가로
**"언제 읽음인가" 라는 제품 결정**이 딸려온다 — 목록을 열면 전부? 탭한 것만? 화면에 보이면?
**그건 기술 판단이 아니라 기획 판단이고, 답에 따라 API 모양이 통째로 갈린다.**

🔴 **그래서 응답에 `isRead` 필드도 내리지 않는다.** 항상 `false` 인 필드를 내리면 앱이 그걸로
뭔가를 그리게 되고, 그리는 순간 *"왜 영원히 안 읽음이냐"* 가 된다. 안 내리다 나중에 넣는 것은
**필드 추가라 non-breaking** 이고, 거짓말을 내리다 고치는 것보다 훨씬 싸다.

### 선택지

| 안 | 내용 | 딸려오는 것 |
|---|---|---|
| **A (백엔드 권장)** | 전부 미룸. `isRead` 필드 없음 | 없음 |
| **B** | `POST /notifications/read-all` + 응답에 `unreadCount` | 홈 벨 뱃지가 **성립한다.** "언제 읽음인가" 가 *"목록을 열면"* 하나로 고정돼 제품 결정이 사라진다 |
| **C** | 행 단위 읽음 (`POST /notifications/{id}/read` + 항목의 `isRead`) | 🔴 "언제 읽음인가" 기획 결정 + 앱 낙관적 상태 + 뱃지 재계산 |

🔵 **B 가 중간이 아니라 별개 설계다.** 행 단위를 버리는 대신 엔드포인트 1 + 필드 1 로 뱃지까지
연다. **뱃지를 1차에 원하면 B, 원치 않으면 A.** C 는 뱃지 없이는 값이 거의 없다.

> **어느 쪽으로 가도 §1 은 되돌아가지 않는다.** B/C 는 §1 에 **필드·엔드포인트 추가**이지
> 변경이 아니다. 그래서 이 판정을 기다리지 않고 §1 을 구현한다.

**→ noti-mobile · noti-design 회신 요망.**

---

## 5. 🔴 모르는 타입 방어 — `type` 은 **string 이고 열린 집합이다**

### 사실관계

`NotificationType` 은 **8종을 선언**하는데 **오늘 발송 가능한 것은 4종**이다. 나머지 4종
(`REMIND`/`RESULT`/`TAUNT`/`FRIEND_REQUEST`)은 `NotificationMessages.of()` 가 `null` 을 반환해
발송이 막혀 있다 — push-fcm §0.6.1 이 *"의도된 게이트지 미완성이 아니"* 라고 적은 그 구조다.

🔴 **즉 "서버가 타입을 추가하는 사건"은 가정이 아니라 예정이다.** 해당 feature 가 붙으면
`NotificationMessages` 에 문구 한 벌이 추가되고 **그 순간부터 새 타입 row 가 이 목록에 섞인다.**

### 서버가 하는 것

**응답 DTO 의 `type` 을 enum 이 아니라 `String` 으로 낸다.**

wire 바이트는 어느 쪽이든 같다(Jackson 이 enum 을 name 문자열로 낸다). **달라지는 것은 SpringDoc
이 내는 OpenAPI 스키마**다:

- enum → `type: string, enum: [CHALLENGE_REQUEST, ...]` — **닫힌 집합을 광고한다.**
- String → `type: string` — 열린 집합.

모바일이 OpenAPI 를 source of truth 로 읽는 구조라(backend-dev 규약), 닫힌 집합을 광고하면
**typed enum 을 만들도록 유도하게 된다.** 그게 정확히 아래 실패다.

### 🔴 모바일이 해야 하는 것 — **`type` 을 String 으로 받아라**

모바일 레포에 **이미 같은 결론이 적혀 있다.** `ActiveChallengeResponse.kt` 의
`VerificationStatusDto` KDoc:

> *"typed enum 은 서버가 값을 하나 추가하면 **응답 전체의 역직렬화를 깨뜨리므로**, 신규 필드는
> 같은 실수를 반복하지 않으려 String 으로 받고 매퍼가 흡수한다."*

같은 파일의 `status`/`myResult` 가 그 결론을 적용해 String 으로 받고 있다.

🔴 **알림 타입은 그 KDoc 이 말한 위험이 가장 크게 걸리는 필드다** — 8종 중 4종이 대기 중이라
확장이 예정돼 있고, 목록이라 **한 행이 아니라 응답 전체가 깨진다.** 새 타입 알림 하나가 섞이면
사용자의 알림 화면이 **통째로 빈다.**

매퍼의 `else` 가 무엇을 하든(행을 버리든 기본 아이콘으로 그리든) **나머지 행이 살아야 한다** —
그게 spec 수용 기준 *"모르는 타입이 와도 목록이 깨지지 않아야 한다"* 의 내용이다.

### 서버 쪽 알려진 한계 — 숨기지 않고 적는다

`NotificationEntity.toDomain()` 은 enum 에 없는 `type` 문자열을 **`CHALLENGE_REQUEST` 로
떨어뜨린다**(폐기된 `SIGN_REQUEST` row 를 읽다 조회가 깨지는 것을 막으려고 push-fcm 때 넣은
방어). 목록 조회에서는 이게 **오분류**로 나타날 수 있다 — 모르는 타입이 챌린지 신청으로 보인다.

**오늘 이게 발생하는 경로는 없다**: `type` 에 들어갈 수 있는 값은 enum 8종의 name 뿐이고
(`fromDomain` 이 `type.name` 을 쓴다) 8종은 전부 round-trip 된다. 실제로 걸리려면 **수동 DB
삽입**이거나 **구버전 인스턴스가 신버전이 쓴 row 를 읽는 롤링 배포**여야 하는데, 후자는
ADR-0007 배포 시점 소관이고 지금은 단일 인스턴스다.

🔴 **고치지 않고 기록만 하는 이유**: 지금 고치려면 도메인 모델의 `type` 을 String 으로
바꾸거나 `UNKNOWN` 을 추가해야 하는데, 그건 발송부(`NotificationDispatcher`·
`NotificationMessages`)까지 번지는 변경이고 **오늘 관측되지 않는 경로**를 위한 것이다.
**배포가 다중 인스턴스가 되는 시점에 다시 봐야 한다** — backend-report 미해결에 올린다.

---

## 6. `referenceId` — 목적지 id. **타입에 따라 대상이 다르다**

push-fcm 오픈이슈 3 의 결정을 그대로 승계한다:

> **`challenge_id` 로 못 박지 않는다.** 이름은 중립으로 두고, 참조 대상이 타입에 따라 다르다는
> 사실을 `COMMENT ON COLUMN` 에 적는다.

**오늘 발송되는 4종은 전부 `challenges.id` 다.** 🔴 **그건 오늘의 사실이지 규약이 아니다** —
`FRIEND_REQUEST` 가 개시되면 `users.id` 를 가리킨다(`NotificationType.FRIEND_REQUEST` KDoc:
*"`reference_id` 가 challenge 가 아닌 유일한 타입이 될 예정"*).

🔴 **그래서 `referenceId` 는 nullable 이고, 모바일은 타입별로 필수 여부를 판정해야 한다.**
`PushEvent.from` 이 이미 그렇게 짜여 있다 — *"challengeId 필수 여부는 타입별로 판정한다 —
참조 대상 없는 타입이 붙어도 버리지 않도록"*. **목록도 같은 규칙을 쓴다.**

### 탭 → 목적지는 **push-deeplink 의 매핑을 재사용한다** (spec T-M2)

서버는 목적지를 **계산해서 내려보내지 않는다.** `type` + `referenceId` 만 준다.
push-deeplink 가 `PushEvent → Route` 매핑을 `:feature:main` 의 `toRoute()` 에 두었고,
그 summary 가 이미 예고했다:

> *"`PushEvent → Route` 매핑을 `:feature:main` 에 — 소비처가 한 곳뿐. **알림 목록 화면이 생기면
> 승격.**"*

🔴 **이번이 그 승격 시점이다.** 서버가 목적지를 내려보내면 매핑이 서버·앱 양쪽에 생겨
**푸시와 목록이 서로 다른 곳으로 가는 날**이 온다 — spec T-M2 가 금지한 그 사본이 서버에 생기는
것과 같다.

### spec 오픈이슈 3 (탭했는데 대상이 사라짐) — **서버 작업 없음**

목록 탭이 푸시와 같은 목적지(`Route.Challenge.Detail`)로 가고, 그 화면이 부르는
`GET /challenges/{id}` 가 이미 `findById ?: throw OneButtonDialogException` 으로 **code 705** 를
낸다(push-deeplink 실측분). **목록에서 와도 같은 엔드포인트라 처리가 자동으로 같다.**
새 코드도 새 코드값도 필요 없다.

---

## 7. 범위 밖 — 명시

- **알림 삭제 · 전체 삭제 · 보관 기간 정책** (spec 비범위). row 는 계정 수명 내내 남는다.
  탈퇴 시에만 물리 삭제된다 (`NotificationRepository.deleteAllByUserId`, mypage T-B4).
- **알림 설정 on/off**.
- **새 타입 발송 개시** — 각 feature 소관이며 push-fcm §0.6.1 의 **모바일 선통지 규약**이 그대로
  적용된다. 🔴 이 계약이 그 규약에 **한 줄을 더한다**: 새 타입은 푸시뿐 아니라 **이 목록에도
  섞이므로**, 통지 대상에 *"목록 렌더링(아이콘·색·탭 목적지)"* 이 포함된다.

---

## 협의 이력

### 2026-09-01 — backend-dev 초안 + 결정 3건

| # | 항목 | 결정 | 상태 |
|---|---|---|---|
| 1 | 페이지네이션 도입 여부·방식 | **도입. 커서(`id` 기준).** §2 | 백엔드 결정 (근거 등재) |
| 2 | `type` 의 wire 타입 | **String (열린 집합).** §5 | 백엔드 결정 (통지) |
| 3 | 읽음 처리 | **A안(미룸) 권장.** §4 | ⏸ 소비자 판정 대기 |
