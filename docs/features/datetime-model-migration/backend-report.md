# Backend Report — datetime-model-migration

- **feature-id**: datetime-model-migration
- **작성**: 2026-07-31 by backend-dev
- **상태**: implemented + **실서버 검증 완료** (재기동 후 65/65 PASS), 커밋 안 함
- **선행 입력**: [spec.md](./spec.md), [api-contract.md](./api-contract.md) (status: `confirmed`), [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)
- **빌드 검증**: `./gradlew clean build` → **BUILD SUCCESSFUL** / 실행 테스트 **123/123 passed, 0 failed** / 통합 45건 Docker 미가용 skip

## 구현 요약

이 feature의 성격은 착수 전 실측으로 **재정의됐다**. 초안 전제("서버가 UTC로 저장 중이니 KST로 바꾼다")가 사실과 달랐다.

**실제 문제는 "UTC → KST 전환"이 아니라 "이미 갈라진 두 시계의 통일"이었다.**

| 사용처 | 방식 | 실측값 (동시각) |
|---|---|---|
| `ChallengeCommandService` | 주입된 `Clock.systemUTC()` | **00:26 (UTC)** |
| 엔티티 5종 기본값 + `FriendService`/`AuthService`/`UserRecord` | `LocalDateTime.now()` (JVM 기본) | **09:26 (KST)** |

같은 DB에 9시간 다른 두 기준이 공존했다. `challenges`/`verifications` row가 0이라 실害가 없었을 뿐이다. 이 발견으로 **V6의 `+9h` 데이터 보정이 취소**됐다(그대로 실행했으면 `users` 1행이 손상됐다 — 상세는 T-B2).

## T-B1 — 시계 기준 단일화

### 신설: `KstTime` (`:core`)

`LocalDateTime.now(ZoneId.of("Asia/Seoul"))` 을 감싼 헬퍼. **JPA 엔티티 필드 기본값처럼 `Clock` 주입이 불가능한 자리** 전용이다.

### `Clock` 빈: `Clock.systemUTC()` → `Clock.system(KstTime.ZONE)`

Spring 빈은 전부 `LocalDateTime.now(clock)` 을 쓴다. 테스트가 `Clock.fixed(..., KstTime.ZONE)` 으로 시각을 고정할 수 있다.

### 시각 취득 지점 — 두 갈래로 수렴, 둘 다 KST

| 경로 | 개소 |
|---|---|
| `KstTime.now()` (주입 불가) | 엔티티 9곳 (`UserEntity` 4 / `FriendshipEntity` 1 / `VerificationEntity` 1 / `ChallengeEntity` 1 / `UserRecordEntity` 2) + `UserRecord` 1 |
| `LocalDateTime.now(clock)` (Spring 빈) | `FriendService` 2 / `AuthService` 3 / `ChallengeCommandService` 1 |

### 감사 결과 — UTC 섬 제거를 기계적으로 확인

| 항목 | production 코드 잔존 |
|---|---|
| `java.time.Instant` | **0건** |
| `Clock.systemUTC()` / `ZoneOffset.UTC` | **0건** |
| 인자 없는 `LocalDateTime.now()` | **0건** |

(위 grep 결과에 남는 매칭은 전부 "예전엔 이랬다"를 설명하는 주석이다.)

### 🔴 안전망 없이 정본만으로 서는가 — **실증했다**

pm-lead 조건: *"(c)의 1·2번이 정본이다. 3번(JVM 고정)을 빼도 동작해야 한다. AWS에서 UTC로 떠도 시각이 안 밀리는지 스스로 확인할 방법을 만들어라."*

**전체 테스트를 JVM 타임존 UTC 강제 상태에서 실행했다:**

```
$ TZ=UTC java -e 'TimeZone.getDefault()'  →  default=UTC     (강제가 실제로 먹었는지 확인)
$ ./gradlew --stop && TZ=UTC ./gradlew clean test --no-daemon
  → BUILD SUCCESSFUL,  실행 123 / 실패 0 / 에러 0
```

**안전망(`main()`의 `TimeZone.setDefault`)은 테스트 경로에 적용되지 않는다.** 즉 이 결과는 `Clock` 빈 + `KstTime` 만으로 전 코드베이스가 KST를 유지한다는 증거다. AWS에서 JVM이 UTC로 떠도 값이 밀리지 않는다.

추가로 단위 테스트에서도 못박았다:
- `KstTimeTest` — JVM 기본을 UTC / `America/New_York` 으로 **실제로 바꿔가며** `KstTime.now()` 결과가 이동하지 않음 확인 (`finally` 원복)
- `KstDeadlineCalculatorTest` — JVM 기본이 UTC 여도 `calculate`/`isExpired` 결과 동일

### `KstDeadlineCalculator` 대폭 단순화

`Instant`(UTC) → KST 날짜 → UTC 되돌리기 **왕복 환산이 통째로 사라졌다.** 입출력이 전부 KST `LocalDateTime`. 남은 책임은 하나 — **"오늘 자정"은 오늘의 *끝*(익일 00:00)이지 시작이 아니다.** `endOfKstDayInUtc` → `endOfDay` 로 개명.

## T-B2 — V6 마이그레이션 (데이터 보정 **안 함**)

`V6__datetime_kst_convention.sql`. **DML 0건**이 핵심이다.

### 보정하지 않은 근거 (파일 주석에 전문 수록)

```
refresh_token_issued_at = 2026-07-31 08:55:05
DB now()                = 2026-07-31 09:23:49   ← 28분 전
```

이 값이 UTC였다면 KST로 17:55 = **미래**다. 리프레시 토큰이 미래에 발급될 수 없으므로 저장값은 **이미 KST**다. 나머지 테이블은 row 0.

> `created_at`(5월) / `updated_at`(7월)만 봤다면 UTC인지 KST인지 구별할 근거가 없다. **"방금 발급됐다"는 의미를 가진 컬럼이라야 반증이 가능하다.** 이 추론 과정을 주석에 남겼다 — 결론만 남기면 다음 사람이 결론을 의심할 때 재현할 방법이 없다.

### DML 대신 `COMMENT ON COLUMN` 17건

spec 리스크 항목을 직접 닫는다:

> "`LocalDateTime`은 offset을 잃는다 — '이 값은 KST'라는 약속이 타입이 아니라 문서와 관행에만 존재하게 된다"

`\d+ challenges` 한 번이면 운영·분석·다음 담당자가 서버 코드를 안 읽고도 기준을 안다. 순수 메타데이터라 동작 영향 0.

비범위인 `contracts`/`notifications`/`taunt_messages`에도 **주석만** 달았다 — "코드는 건드리지 않되 해석 기준은 문서화한다"는 비범위 문구 그대로.

### 검증

- 일회용 DB에 V1→V3→V4→V5→**V6** 순차 적용 **5건 전부 OK**, 주석 17건 기록 확인 후 DROP
- **기계적 확인**: `INSERT|UPDATE|DELETE|ALTER|DROP|TRUNCATE` 매칭 **0**, `COMMENT ON COLUMN` **17**
- **실 DB 미적용** — flyway 최신 V5 유지, `users` 1행 타임스탬프 3개 전부 #7 이전과 동일. **다음 재기동 시 Flyway가 자동 적용한다.**

## T-B3 — 직렬화 / 역직렬화

### `WIRE_DATETIME` / `WIRE_DATE` 상수 (`:controller:common`)

`@JsonFormat(pattern=...)` 은 컴파일 타임 상수만 받는데, 문자열을 DTO마다 손으로 적으면 **오타가 나도 컴파일이 통과한다.** 한 곳을 참조하게 해서 그 실패 모드를 없앴다.

### 변경 대상

| 파일 | 변경 |
|---|---|
| `ChallengeCommandDtos` | `deadline`/`createdAt` `Instant` → `LocalDateTime` + `@JsonFormat(WIRE_DATETIME)`, `challengeDate` → `WIRE_DATE` |
| `ActiveChallengeResponse` | `deadline` 동일 |
| `FriendListResponse` | `since` / `requestedAt` 동일 (`requestedAt`은 계약 초안에 없던 필드 — 누락 보완) |
| `ChallengeCommandController` / `ActiveChallengeController` / `FriendController` | `toInstant(ZoneOffset.UTC)` **전부 제거** — 변환 없이 그대로 직렬화 |
| `JacksonDateTimeConfig` (신규) | 전역 `LocalDateTime`/`LocalDate` serializer + **deserializer** (안전망) |
| `GlobalExceptionHandler` | **`HttpMessageNotReadableException` 핸들러 신규** (§4) |

### §4 — 잘못된 요청 본문이 HTTP 500 을 반환하던 문제

`challenge-create` #7 실서버 검증에서 발견했다:
```
{"opponentId":}              → HTTP 500 / code 500
{"deadlineType":"YESTERDAY"} → HTTP 500 / code 500
```
핸들러 부재로 `handleUncaught` 로 떨어지던 것을 **HTTP 200 + code 700** 으로 바꿨다. **ADR-0010 에서 특히 중요해졌다** — 요청 본문에 날짜 문자열이 들어오면 포맷 오류가 정확히 이 경로를 탄다.

Jackson 내부 영문 문구(`Cannot deserialize value of type java.time.LocalDateTime`)를 그대로 노출하지 않고 고정 문구(`"요청 형식이 올바르지 않습니다"`)로 바꿨다 — 모바일이 `message` 를 가공 없이 화면에 띄우기 때문이며, **그 사실 자체를 테스트로 박았다.**

## T-B4 — 테스트

### 결과: 실행 **123 / 실패 0 / 에러 0** (이전 111)

| 테스트 | 이전 | 지금 | 비고 |
|---|---|---|---|
| `KstDeadlineCalculatorTest` | 17 | **16** | **의도적 -1** (아래) |
| `KstTimeTest` | — | **4** | 신규 |
| `WireDateTimeSerdeTest` | — | **7** | 신규 (§5 합성 DTO) |
| `GlobalExceptionHandlerTest` | 5 | **7** | +2 (§4) |
| `ChallengeCommandServiceTest` | 39 | 39 | 회귀 0 |
| `ChallengeCommandControllerTest` | 18 | 18 | 회귀 0 |
| `FriendControllerTest` | 15 | 15 | 회귀 0 |
| `AuthControllerTest` / `UserControllerTest` / `PhoneHasherTest` / `FriendServiceEscapeForLikeTest` / smoke | 5/2/3/6/1 | 동일 | 회귀 0 |

### `KstDeadlineCalculatorTest` 17 → 16 은 의도적 감소다

기존 17건 중 **6건이 `15:00Z` 전후 UTC↔KST 날짜 경계**를 확인하던 것인데, 변환 자체가 사라져 **검증 대상이 없어졌다.** 그 자리에 5건을 새로 넣었다 — 자정 1초 전 / 자정 정각 / 2월 28일 TODAY / `endOfDay` / **타임존 무관성**. 억지로 17을 맞추지 않았다.

**남긴 의도**: "날짜가 하루 어긋나면 안 된다"는 원래 목적은 월말·연말·윤년 경계와 "자정은 하루의 끝" 회귀 방지로 그대로 유지된다.

### §5 — 요청 역직렬화의 검증 범위

`WireDateTimeSerdeTest` 가 **합성 DTO**(`SyntheticTimeBody`)로 역직렬화를 검증한다. 프로덕션 요청 DTO에 시간 필드가 0건이라 그냥 두면 수용 기준이 공허하게 통과하기 때문이다.

- ✅ 증명함: 전역 설정이 `yyyy-MM-dd HH:mm:ss` 를 **읽고 쓴다**, `T` 구분자·`Z` suffix 를 **거부한다**, 나노초가 잘린다, 왕복이 값을 보존한다
- ❌ **증명 못 함: 실제 엔드포인트가 그 형식을 받는다** — 시간 필드를 가진 요청 DTO가 생기는 시점에 그 엔드포인트의 슬라이스 테스트가 따로 필요하다

이 한계를 계약 §5와 테스트 KDoc 양쪽에 명시했다. "이미 검증됨"으로 오해할 자리를 막기 위함이다.

## ✅ 실서버 baseline 대조 — 완료 (2026-07-31 재기동 후, **65/65 PASS, 0 FAIL**)

사용자가 서버를 재기동한 뒤 하네스(65 단언)를 실행했다.

### baseline 대조 — **시각이 이동하지 않았다**

| | 마이그레이션 전 (#7 실측) | 마이그레이션 후 (실측) |
|---|---|---|
| 응답 `deadline` | `"2026-07-31T15:00:00Z"` | **`"2026-08-01 00:00:00"`** |
| DB `challenges.deadline` | `2026-07-31 15:00:00` | **`2026-08-01 00:00:00`** |
| 응답 `createdAt` | `"2026-07-31T00:31:01Z"` | **`"2026-07-31 14:09:23"`** |

`2026-07-31T15:00:00Z` == `2026-08-01 00:00:00 KST` — **같은 순간의 다른 표기**다. 실제 마감 시각은 변하지 않았다.

핵심 단언 4건이 이를 기계적으로 확인했다:
- `deadline` 형태가 `^yyyy-MM-dd HH:mm:ss$` ✅
- `deadline`에 `T` 구분자 없음 / `Z` suffix 없음 ✅
- `deadline == KST 익일 00:00` (DB에서 계산한 값과 직접 대조) ✅
- **`DB deadline == 응답 deadline`** ✅ ← 직렬화 단계에서 시각이 이동하지 않았다는 직접 증거

`createdAt`도 `14:09:23`으로 DB `now()`(14:09)와 일치 — KST 벽시계가 그대로 저장·직렬화된다.

### V6 실 DB 적용 확인

```
Flyway  V1 → V3 → V4 → V5 → V6   전부 success
ADR-0010 컬럼 주석                17건 실 DB 반영 ✅
users created_at                 2026-05-07 10:10:42.443862  (불변)
users updated_at                 2026-07-28 11:01:23.650844  (불변)
```

**V6가 데이터를 건드리지 않았다는 것이 실 DB에서 확인됐다.** DML 0건 주장이 그대로 성립한다.

> `refresh_token_issued_at`이 `08:55:05` → `13:19:55`로 바뀌었으나 **마이그레이션 때문이 아니다.** V6에 DML이 없고, `+9h` 이동이었다면 `17:55`(당시 기준 미래)여야 하는데 실제 값은 현재 시각보다 49분 전이다. **재기동 과정의 정상 재로그인**이다.

### 구간별 결과

| 구간 | 결과 |
|---|---|
| 0-A. V6 적용 + 주석 17건 + `users` 불변 | 3/3 |
| 1. 생성 (새 포맷 4단언 + DB 대조 포함) | 10/10 |
| 2. 검증 규칙 (코드 + 확정 문구 전건) | 12/12 |
| 3. 받은 도전장 (JOIN + `createdAt` 형태) | 9/9 |
| 4. 수락 + read-after-write | 17/17 |
| 5. 거절 | 6/6 |
| 6. 취소 | 8/8 |
| 7. 미인증 401 | 2/2 |
| **합계** | **65/65 PASS, 0 FAIL** |

**challenge-create의 58건이 새 시간 포맷에서도 전부 통과했다** — 시간 규약 변경이 기존 기능을 깨지 않았다는 뜻이다(동작 보존).

### DB 조작 내역 (전량 원복)

- 삽입: `users` 2행(`kakao_id 999000001/2`), `friendships` 1행, `challenges` 3행, `verifications` 2행
- **삭제 범위를 `kakao_id 999000001~999000999`로 넓혀 정리** — `dev-test-login`이 같은 대역(`999000001~3`)을 쓰기로 확정돼 잔여가 섞이면 안 되기 때문이다
- **정리 후**: `users=1 friendships=0 challenges=0 verifications=0 user_stats=0`, **999000xxx 대역 잔존 0** ✅
- 실사용자(id=1) `created_at`/`updated_at` 검증 전후 동일

## 변경 파일 (절대 경로)

### 신규
```
core/src/main/kotlin/com/lwg/challenge/core/time/KstTime.kt
controller/src/main/kotlin/com/lwg/challenge/controller/common/WireDateTimeFormat.kt
controller/src/main/kotlin/com/lwg/challenge/controller/config/JacksonDateTimeConfig.kt
app/src/main/resources/db/migration/V6__datetime_kst_convention.sql
core/src/test/kotlin/com/lwg/challenge/core/time/KstTimeTest.kt
app/src/test/kotlin/com/lwg/challenge/controller/config/WireDateTimeSerdeTest.kt
```
(전부 `/Users/hwamulman/woogunProject/challenge/challenge-server/` 하위)

### 수정
- `core/.../challenge/KstDeadlineCalculator.kt` (UTC 환산 제거)
- `app/.../config/ClockConfig.kt` (UTC → KST)
- `app/.../ChallengeServerApplication.kt` (JVM tz 안전망)
- 엔티티 5종 + `domain/model/.../userrecord/UserRecord.kt`
- `service/.../friend/FriendService.kt` · `auth/AuthService.kt` · `challenge/ChallengeCommandService.kt` (Clock 주입)
- DTO 3종 + 컨트롤러 3종 + `GlobalExceptionHandler`
- 도메인 KDoc 4곳 (UTC → KST 기준 정정)
- 테스트 5종

## 미해결 이슈

1. ~~**실서버 baseline 대조 미완**~~ — ✅ **2026-07-31 해소. 65/65 PASS, 시각 이동 없음 확인.**
2. **🔴 통합 테스트 45건 여전히 skip** — 컨테이너 런타임 부재(백로그 등재). 이번 변경도 `ChallengeCreateIntegrationTest` 21건이 검증하지 못한다. 다만 위 실서버 65단언이 같은 층(JPA 매핑·Flyway 적용·Security 필터·직렬화)을 수동으로 덮었다 — **CI에서 반복되지 않는다는 한계는 그대로다.**
3. **🟢 `/actuator/health` 500** — actuator 의존성 부재. #7에서 발견, 사용처 없음.
4. **🟢 `Clock` 주입 미적용 잔여 없음** — 엔티티 기본값은 구조상 주입이 불가능해 `KstTime` 을 쓴다. 이는 설계 선택이지 부채가 아니다.
