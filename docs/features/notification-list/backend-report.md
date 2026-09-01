# Backend Report — notification-list

- **작성**: 2026-09-01 backend-dev (noti-backend)
- **계약**: [api-contract.md](./api-contract.md) — ✅ `confirmed`
- **상태**: implemented (**미배포·미커밋**)

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

### 🟢 4. 페이지네이션 규약이 나머지 4종에 적용되지 않았다

이 계약이 프로젝트 최초 페이지네이션이고 방식(커서)을 열었다. **친구 목록·받은 요청·랭킹은
지금 따라 고치지 않았다** — 백로그가 말한 *"수백 건 도달"* 신호가 없다(보관함은 월이 이미
경계라 대상이 아니다). 다음에 도입하는 쪽이 이 shape 을 따르면 된다:
`?cursor=&size=` + `data.nextCursor: <키>?`, 정렬·커서 키 동일, 불리언 금지.
**ADR 승격 여부는 pm 판단.**

### ⚠️ 5. 미커밋

🚫 지시대로 **커밋·staging 하지 않았다.** 변경 **12개**(신규 6 / 수정 6)가 working tree 에 있다.
서버 레포 HEAD 는 `0c06589` 그대로다. 코드 레포 커밋은 사용자 몫이다.
