# Backend Report — notification-list

- **작성**: 2026-09-01 backend-dev (noti-backend). 🔴 **v2 개정분 반영** (아래 §v2)
- **계약**: [api-contract.md](./api-contract.md) — ✅ `confirmed` (**v2** 가 현행) · [change-log.md](./change-log.md)
- **상태**: implemented (**미배포**). v1 은 사용자가 커밋(`e8b1460`), **v2 는 미커밋 14파일**

---

## 🔴 v2 (2026-09-01) — `referencePending` 추가

사용자 피드백(*"이미 지난 챌린지도 이동이 되어서 어색하다"*)으로 목록 탭 규칙이 **타입 → 상태**로
바뀌었다. 응답에 **필드 1개 추가**, 기존 5필드·3엔드포인트·커서 규약은 **전부 그대로**다.

### 🔴 이 개정의 핵심 — 원시 상태값 안이 실측으로 기각됐다

`referenceStatus: "PENDING"` 을 내리는 안이 더 «사실»처럼 보였고 먼저 검토했다. **기각 근거**:

```sql
-- 홈 '받은 도전장' 실측 (findReceivedPending)
WHERE c.opponent_id = :me AND c.status = 'PENDING' AND c.deadline > :now
```

`ChallengeCommandService` KDoc — ***"마감 지난 row 는 DB 에서 `PENDING` 인 채로 남고 응답에서만
빠진다 (lazy expiry)"*.** 🔴 **«PENDING 이면서 만료된» 챌린지가 정상적으로 존재**하므로, 상태값을
내렸다면 앱이 *"PENDING = 탭 가능"* 으로 읽어 **만료된 신청을 빈 '받은 도전장'으로 보낸다** —
**사용자가 신고한 증상의 재발**이다. 상세는 계약 §9.3.

### 변경 파일 (16, 전부 미커밋)

| 모듈 | 파일 | 변경 |
|---|---|---|
| `:domain:repository` | `challenge/ChallengeRepository.kt` | 포트 `findPendingReceivedIdsIn(opponentId, ids, now)` |
| `:infra:jpa` | `challenge/ChallengeJpaRepository.kt` | JPQL — 술어 3조건(`opponent_id`·`PENDING`·`deadline > now`) |
| `:infra:repositoryimpl` | `challenge/ChallengeRepositoryImpl.kt` | 빈 `IN` 가드 + `toSet()` |
| `:service` | `notification/NotificationQueryService.kt` | `ChallengeRepository`+`Clock` 주입, 배치 조회 1회 |
| `:controller` | `notification/dto/NotificationListResponse.kt` · `NotificationController.kt` | 필드 + 매핑 |
| 테스트 (8) | Query/Controller +12건, 기존 fake `ChallengeRepository` **6곳** 채움 | |

**마이그레이션 0건** — 스키마 변경이 없다.

### 성능 — join 을 쓰지 않는다

**타입으로 거른 뒤 `IN` 절 배치 1회.** 페이지 크기와 무관하게 **총 2쿼리**, COUNT 없음.
🔴 **join 이 위험한 이유는 성능이 아니라 정합성이다** — `reference_id` 는 FK 가 아니고 타입마다
참조 대상이 다르므로, `FRIEND_REQUEST` 가 열리면 `users.id` 를 `challenges.id` 에 조인하게 되어
**조용히 틀린다**(계약 §9.5). N+1 회귀 장치로 *"배치 조회는 페이지당 1회"* 와 *"fake 의 단건
`findById` 는 `error()`"* 를 테스트에 박았다.

### 테스트

```
v1 기준선  total 589 / passed 540 / skipped 49 / failures 0
v2 최종    total 605 / passed 555 / skipped 50 / failures 0
```
**+16 전부 신규, 회귀 0.** ⚠️ **skip +1 은 회귀가 아니다** — 새 통합 테스트가 기존 49건과 같은
이유(Docker 부재 `@EnabledIf` 가드)로 건너뛴 것이다.

### 🔴 술어 복제 방지 (pm 지적 반영)

`findReceivedPending`(홈, native)과 `findPendingReceivedIdsIn`(알림, JPQL)이 **같은 도메인 규칙의
두 번째 구현**이다. ⚠️ **합치지 않았다**(native/JPQL 이라 표기·SELECT·JOIN·정렬이 다 다르다).
대신 **갈라지면 깨지는 장치 3개**: 양방향 교차 참조 KDoc / `ChallengeReceivedPredicateBindingTest`
(**항상 실행** — 두 `@Query` 를 리플렉션으로 읽어 세 조건 존재를 단언) / 통합 테스트(Docker 필요,
**한 테스트 안에서** *"홈 집합 == `referencePending=true` 집합"*).

🔵 **구조 테스트가 실제로 잡는지 확인했다** — JPQL 을 `>=` 로 바꿔 실패시켜 보고 되돌렸다.
⚠️ 정규화에서 **대소문자를 접으면 안 된다** — `status = 'pending'` 이 통과하는데 DB 엔 대문자
enum name 이 들어가므로 **조용히 빈 결과가 되는 실제 버그**다. 만료 경계는 `now-1s`=false / `now`(정각)=false / `now+1s`=true 로
`>` 를 고정했다 — `findReceivedPending` 과 같은 규칙.

### 🔴 실구동 (계약 §8.1) — 10항목 전부 통과

throwaway DB `challenge_noti_verify` + 포트 8088, 공용 DB·`:8080` 불가침, 정리까지 확인.
핵심 2건:

1. 🔴 **`PENDING` 인데 마감 지난 챌린지 → `false`.** 이 케이스가 없었으면 개정이 실패했다.
2. 🔴 **홈 '받은 도전장' 과 직접 대조** — 같은 계정으로 `GET /challenges/received` 를 부르니
   **정확히 같은 1건**만 왔다(만료분은 양쪽 모두에서 빠짐). §9.4 의 *"홈과 같은 술어"* 가
   **추론이 아니라 실측으로 확인**됐다.

### spec 오픈 이슈 3 — **부분 해소**

신청은 사전 차단돼 **705 에 도달하지 않는다.** 증거 도착은 **여전히 705**(*"항상 탭"*).

---

## v1 (아래는 최초 구현분 — 사용자 커밋 `e8b1460`)

## 구현 요약

알림 목록 조회 + 읽음 처리. **스키마 변경 0건** — `notifications` 테이블은 V1 그대로이고
`is_read` 컬럼과 `idx_notifications_user_read_created` 인덱스도 V1 부터 있다. **마이그레이션
파일을 추가하지 않았다.**

결정 4건과 그 근거는 전부 계약 문서에 있다:

| # | 결정 | 계약 |
|---|---|---|
| 1 | **페이지네이션 도입 — 커서(`id` 기준).** 프로젝트 최초이며 통일 규약을 연다 | §2 |
| 2 | **`type` 은 열린 집합(String)** — enum 으로 내지 않는다 | §5 |
| 3 | **읽음 처리 (B)** — `read-all` + `unreadCount`. 행 단위 `isRead` 없음 | §4 |
| 4 | **`title` 을 응답에서 제거** — design §3.3 판정 반영, 초안 뒤집음 | §1.1 |

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| GET | `/api/v1/notifications?cursor=&size=` | Bearer | implemented (미배포) |
| GET | `/api/v1/notifications/unread-count` | Bearer | implemented (미배포) |
| POST | `/api/v1/notifications/read-all` | Bearer | implemented (미배포) |

**`SecurityConfig` 변경 0건** — `.anyRequest().authenticated()` 가 이미 덮는다. 세 경로 전부
무인증 시 HTTP 401 을 실측했다. 🔵 permitAll 목록에 명시하지 **않은** 것이 의도다 — 명시하면
인증 규칙이 두 곳에 생긴다.

## 변경된 모듈 & 파일

**신규 (6)**

| 모듈 | 파일 |
|---|---|
| `:service` | `notification/NotificationQueryService.kt` (`NotificationPage`/`NotificationView` 포함) |
| `:service` | `notification/NotificationCommandService.kt` |
| `:controller` | `notification/NotificationController.kt` |
| `:controller` | `notification/dto/NotificationListResponse.kt` (`UnreadCountResponse` 포함) |
| `:service` (test) | `notification/NotificationQueryServiceTest.kt` · `notification/NotificationCommandServiceTest.kt` |
| `:app` (test) | `controller/notification/NotificationControllerTest.kt` |

**수정 (5)**

| 모듈 | 파일 | 변경 |
|---|---|---|
| `:domain:repository` | `notification/NotificationRepository.kt` | 포트 3개 추가(`findPageByUserId` / `countUnreadByUserId` / `markAllAsReadByUserId`). 낡은 *"조회는 아직 없다"* KDoc 교체 |
| `:infra:jpa` | `notification/NotificationJpaRepository.kt` | 쿼리 4개 추가 |
| `:infra:repositoryimpl` | `notification/NotificationRepositoryImpl.kt` | 위임 3개 |
| `:infra:entity` | `notification/NotificationEntity.kt` | 🔴 **`toDomain()` KDoc 정정** (주석만, 로직 무변경) — 아래 |
| `:service` (test) | `notification/NotificationDispatcherTest.kt` · `user/WithdrawalServiceTest.kt` | 포트가 늘어 기존 fake 2곳에 새 메서드 채움 (해당 경로에서 호출되면 `error(...)`) |

### 🔴 `NotificationEntity.toDomain()` KDoc 정정 — pm-lead 요청분

⚠️ **초판 report 에서 이 항목을 빠뜨렸다.** pm-lead 가 report 요청 시 명시한 4항목 중 하나였는데
누락했고, 지적받아 처리했다.

그 KDoc 이 *"(현재 `notifications` 는 0행이라 실제로 그런 row 는 없다.)"* 로 끝나고 있었다.
**낡았다** — push-fcm 이 4종을 발송하며 row 를 쌓고 있고, 실측 dev DB **14행**이다
(`CHALLENGE_REQUEST` 7 / `ACCEPTED` 3 / `REJECTED` 2 / `OPPONENT_VERIFIED` 2).

⚠️ **문구 오류가 아니라 위험도 오독을 부르는 문장이었다** — 그 괄호가 **강등 로직을 "이론상
안전"으로 보이게 하는 유일한 근거**인데, 근거가 사라졌는데 문장만 남으면 다음 사람이 위험도를
낮게 읽는다.

**"0행이라 안전"을 진짜 이유로 교체했다**: 오늘 강등이 안 터지는 것은 행이 없어서가 아니라
**쓰기가 제약돼서**다(`fromDomain` 이 `type.name` 만 쓰므로 DB 값은 enum 8종 name 뿐, 8종은 전부
round-trip). 함께 적은 것 — 읽기 경로가 생기며 **결과가 화면에 렌더되고 탭 목적지가 된다**는
성격 변화, `VerificationEntity` 와 **같은 것은 코드 모양까지고 위험 등급은 다르다**는 대비
(거긴 내부 분기용이라 눈에 띄게 깨지고 여긴 렌더되는 값이라 조용히 틀린다), 안 고치는 이유와
트리거 2개.

🔵 **실측 14행이라는 숫자는 KDoc 에 넣지 않았다** — 그 숫자도 똑같이 낡아 **이번과 같은 오독을
다시 만든다.** *"행이 쌓이고 있다 + 행 수는 근거가 아니다"* 로 적고 근거를 쓰기 제약으로 옮겼다.

로직·시그니처 무변경이라 테스트 숫자는 **589/540/49/0 그대로**다.

## DB 마이그레이션

**없다.** 이 feature 가 쓰는 것은 전부 V1 자산이다.

🔵 **V1 인덱스가 처음으로 제 용도로 쓰인다** — `idx_notifications_user_read_created
(user_id, is_read, created_at DESC)` 는 애초에 *안 읽은 개수 집계용*으로 만들어진 것이고,
`COUNT(*) WHERE user_id=? AND is_read=false` 의 선두 두 컬럼과 정확히 맞는다.

⚠️ **반대로 목록 조회 쿼리는 이 인덱스를 정렬에 쓰지 못한다** (`ORDER BY id DESC` 인데 인덱스
3번째 컬럼이 `created_at`). **그래도 인덱스를 추가하지 않았다** — 근거는 계약 §2 마지막 절:
페이지네이션은 **계약**이라 나중에 바꾸면 breaking 이지만 인덱스는 **1줄 마이그레이션**이라
계약 영향 0으로 아무 때나 붙는다. 붙일 트리거는 *"이 쿼리가 느려진 것이 관측되면"* 이고,
그때 `(user_id, id DESC)` 를 추가한다.

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui.html · `/v3/api-docs`
- 등록된 경로 3개: `/api/v1/notifications` (get) · `/notifications/read-all` (post) ·
  `/notifications/unread-count` (get) — **실측 확인**

🔴 **`type` 이 닫힌 집합으로 광고되지 않는 것을 스펙 원문으로 확인했다** (이게 String 을
고른 이유 자체다):

```json
"type": { "type": "string",
          "description": "알림 종류. **열린 집합** — … typed enum 으로 만들지 마라.",
          "example": "CHALLENGE_ACCEPTED" }
```

`enum: [...]` 배열이 **없다.** enum 타입으로 선언했다면 여기 8종이 박혀 나가고, 모바일이 그걸
source of truth 로 읽어 typed enum 을 만들었을 것이다.

**nullable 표현도 확인** — OpenAPI 3.1 이라 `required` 배열에서 빠지는 것으로 표현된다
(mypage 선례와 동일):
- `NotificationDto.required = [body, createdAt, notificationId, type]` → **`referenceId` 만 빠짐** ✅
- `NotificationListData.required = [notifications]` → **`nextCursor` 빠짐** ✅

⚠️ **`createdAt` 의 `"format": "date-time"` 은 스펙이 흘리는 거짓 신호다.** SpringDoc 이
`LocalDateTime` 을 보고 자동으로 붙이는데, 실제 wire 는 `@JsonFormat` 이 정한
`yyyy-MM-dd HH:mm:ss`(ADR-0010, **ISO 아님**)다. `example`·`description` 은 실제 형식을 적고
있다. 🔵 **이번에 생긴 것이 아니라 `deadline` 등 기존 `LocalDateTime` 필드 전부가 같다** —
프로젝트 전역 사안이라 여기서 고치지 않았다. **codegen 을 쓴다면 `format` 이 아니라
`description` 을 믿어야 한다.**

## 테스트 결과

```
기준선 (작업 전)  total 535 / passed 486 / skipped 49 / failures 0
최종             total 589 / passed 540 / skipped 49 / failures 0
```

🔴 **회귀 0.** 증가분 **+54 는 전부 신규**다.

| 테스트 | 건수 |
|---|---|
| `NotificationControllerTest` (신규) | 29 |
| `NotificationQueryServiceTest` (신규) | 17 |
| `NotificationCommandServiceTest` (신규) | 8 |

skipped 49 는 **기존 블로커** — Testcontainers 통합 테스트가 컨테이너 런타임(Docker) 부재로
전부 비활성이다. 이번 작업이 늘린 것이 아니다.

### 회귀 장치로 고정한 "의도적 부재" 2건

단언이 **값이 아니라 키의 부재**를 본다. 나중에 누가 무심코 되살리면 실패한다.

```kotlin
jsonPath("$.data.notifications[0].isRead").doesNotExist()   // §4 — 행 단위 읽음 미채택
jsonPath("$.data.notifications[0].title").doesNotExist()    // §1.1 — design §3.3 판정
```

## 🔴 실구동 검증 — 단위 테스트가 못 덮는 축

**이 레포의 단위 테스트는 JPA 를 auto-configuration 에서 제외하고 repository 를 mock 으로
세운다. 즉 통과한 540건 중 어느 것도 새 JPQL 4개를 실제 DB 에 대고 실행하지 않는다.**
통합 테스트 49건은 상시 skip 이다.

그래서 **throwaway DB `challenge_noti_verify` + 포트 8088** 로 21항목을 확인했다.
🔴 **공용 `challenge` DB 와 `:8080` 은 건드리지 않았고** 끝난 뒤 전부 정리했다
(정리 확인: DB drop / 프로세스 종료 / 공용 DB `notifications` 14행 그대로 / `:8080` 401 응답).

전체 표는 [api-contract.md §8](./api-contract.md). 핵심 3건만:

1. 🔴 **정렬 축이 `id` 임을 갈라서 증명했다.** 시드에서 `created_at` 을 일부러 `id` 순서와
   어긋나게 넣었다 — id=3 에 가장 오래된 `2026-08-01` 을 줬다. `created_at` 정렬이었다면
   `7,6,5,4,2,1,3` 이 나왔어야 하는데 **실제 응답은 `7,6,5,4,3,2,1`** 이었다.
2. **커서 페이징 중복 0 / 누락 0** — `size=3` 으로 7건을 `[7,6,5]→[4,3,2]→[1]` 로 완주,
   마지막에 `nextCursor: null`.
3. **`read-all` 이 남의 알림을 건드리지 않는다** — user1 7건이 read 로 바뀌는 동안
   user2 의 2건은 unread 유지.

⚠️ **2회 돌렸다.** 1회차는 `title` 제거 **전** 빌드였고 §1.1 로 shape 이 바뀌어 **최종 빌드로
전량 재실행**했다. 낡은 shape 에 대한 검증을 근거로 남기지 않기 위해서다.

## 미해결 이슈

### 🔴 1. enum 밖 `type` 문자열이 `CHALLENGE_REQUEST` 로 오분류된다 — **실측 재현됨**

`NotificationEntity.toDomain()` 이 enum 에 없는 `type` 을 `CHALLENGE_REQUEST` 로 떨어뜨린다
(폐기된 `SIGN_REQUEST` row 방어용으로 push-fcm 때 넣은 것). DB 에 `type='SOME_FUTURE_TYPE'` 을
넣고 조회하니 wire 에 **`"type":"CHALLENGE_REQUEST"`** 로 나왔다.

⚠️ **나쁜 종류의 fallback 이다** — `CHALLENGE_REQUEST` 는 **실재하고 탭되는 타입**이라 모르는
알림이 *"챌린지 신청"* 으로 보이고 탭하면 챌린지 상세로 간다. 앱이 준비한 방어(*"모르는 타입
→ null → 비탭"*)는 **모르는 값이 앱까지 가야 작동하는데 서버가 그 전에 아는 값으로 바꾼다.**

🔵 **오늘 도달 경로는 없다.** `fromDomain` 이 `type.name` 을 쓰므로 DB 에 들어가는 값은 enum
8종뿐이고, **8종은 전부 round-trip 한다**(같은 검증에서 `FRIEND_REQUEST` 정상 확인). 실제로
걸리려면 **수동 DB 삽입**(= 검증에서 한 것)이나 **롤링 배포**여야 한다.

**고치지 않은 이유**: 도메인 `Notification.type` 을 String 으로 바꾸거나 `UNKNOWN` 을 추가해야
하는데 발송부(`NotificationDispatcher`·`NotificationMessages.of`)와 그 테스트까지 번진다.
관측되지 않은 경로를 위한 리팩터링은 이 프로젝트 방침이 아니다.
**트리거**: (1) 다중 인스턴스 배포(ADR-0007), (2) enum 밖 타입이 DB 에 들어가는 경로 발생.

> 🔴 **pm-lead 의 최초 지시는 실행 불가능했고 그 사실을 남긴다** — *"목록 조회는 `toDomain()` 을
> 밟지 말고 **컬럼에서 바로 프로젝션**해 원문 String 을 내려라."* `NotificationRepositoryImpl
> .findPageByUserId` 가 **`List<Notification>`(도메인)을 반환**하고 `Notification.type` 이 enum
> 이라 **거기가 병목이라 "컬럼에서 바로"라는 길이 없다.** 하려면 도메인 모델을 String 으로
> 바꾸거나(위 번짐) 계층을 우회하는 별도 읽기 경로를 만들어야 하는데, 후자는 이 레포의 DIP
> 규약(`.claude/skills/dip-architecture`)을 정면으로 어긴다. pm-lead 가 *"엔티티에 값이 있는
> 것과 그 값이 응답까지 갈 길이 있는 것은 다른 문제인데 후자를 안 봤다"* 로 정정했고,
> **지시를 그대로 따르지 않고 실측해 미해결로 올린 처리가 승인**됐다.

**계약 쪽 처리 (2026-09-01, [change-log.md](./change-log.md))**: 이 사실이 report 에만 있으면
**계약을 읽는 사람은 report 를 안 읽는다.** §5 의 논증 **바로 다음 줄에 인라인 경고**를 넣었다
(접기·별도 절로 분리했다가 안 읽혀 사고 난 것이 이 프로젝트에 3회). 경고의 마지막 문장이
핵심 — *"앱의 폴백을 «쓸모없는 방어»로 읽지 마라."* 없으면 누군가 *"어차피 서버가 아는 값만
주는데"* 라며 design §3.2 폴백을 걷어내고, 트리거가 왔을 때 막을 것이 없어진다.

**KDoc 도 같은 사실을 담도록 고쳤다** — 위 "변경된 모듈 & 파일" 절 참조.

### 🟡 2. `CHALLENGE_REQUEST` 문구의 조사 결함 — `"민수과 계약을 하시렵니까?"`

`NotificationMessages` 의 `"{actorNickname}과 계약을 하시렵니까?"` 가 **받침 없는 닉네임에서
`"민수과"`** 가 된다. 4종 중 이 한 종만 `님` 도 빠져 있다(나머지는 `{닉}님이`).

🔴 **사용자 확정 문구(2026-08-07)라 임의로 바꾸지 않았다.** 다만 **확정 당시엔 푸시밖에
없었다** — 푸시는 스쳐 지나가지만 **목록은 남고 스크롤하면 다시 보인다.** noti-design 이
§3.3.1 로 올린 것을 백엔드가 승계한다(고칠 자리가 서버 `NotificationMessages` 한 곳이므로).
**사용자 결정 대기.** 앱 변경은 불필요하고, mobile 에는 *"앱에서 문자열을 덮지 마라"* 를 통지했다.

### 🟢 3. 목록 조회용 인덱스 `(user_id, id DESC)` 미생성

위 "DB 마이그레이션" 절 참조. **관측 후 추가**가 방침이고, 1줄 마이그레이션이라 계약 영향 0.

### 🟢 4. 페이지네이션 규약이 기존 목록에 적용되지 않았다

이 계약이 프로젝트 최초 페이지네이션이고 방식(커서)을 열었다.
✅ **[ADR-0012](../../decisions/0012-list-pagination-cursor.md) 로 승격됐다**(accepted, 2026-09-01)
— 초판의 *"ADR 승격 여부는 pm 판단"* 은 해소됐다. **적용 범위와 미적용 사유는 ADR §적용 범위가
정본**이다.

**기존 6종을 지금 따라 고치지 않았다** — 보관함은 월이 이미 경계, 홈 진행중·받은 도전장은
설계상 한정, 친구·받은 요청·랭킹은 백로그가 말한 *"수백 건 도달"* 신호가 없다.

> 🔴 **2026-09-01 정정 — 이 항목이 "나머지 4종"이라고 적고 있었다.** `GET /challenges/active` 와
> `GET /challenges/received` 를 빠뜨린 오답이고, **같은 오류가 계약 §2 에도 있어 CLAUDE.md 규칙
> 줄과 백로그로 번졌다**(경위는 [change-log.md](./change-log.md) 5번). 계약·ADR·CLAUDE.md·백로그는
> `f72d0b4` 까지 정정됐는데 **이 report 만 남아 있었다** — 같은 숫자가 5개 문서에 흩어져 있었고
> **마지막 하나는 전수 grep 으로만 찾혔다.**

### ✅ 5. ~~미커밋~~ → **v1 은 커밋됨, v2 가 미커밋**

🚫 지시대로 **내가 커밋·staging 하지 않았다.** 코드 레포 커밋은 사용자 몫이다.

- **v1** (신규 6 / 수정 6) — ✅ **사용자가 커밋했다**: `e8b1460 feat: 알림 히스토리 조회 기능 구현`
  (13파일 +2014줄). ⚠️ 초판 report 가 *"HEAD 는 `0c06589` 그대로"* 라고 적고 있었는데 **낡았다** —
  그 사이 사용자가 커밋했다.
- **v2** (`referencePending`) — **미커밋 14파일.** 위 §v2 참조.
