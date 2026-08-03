# 날짜·시간 모델 통일 (datetime-model-migration)

- **feature-id**: datetime-model-migration
- **owner**: pm-lead
- **상태**: draft
- **생성**: 2026-07-31
- **근거 ADR**: [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)

## 배경 / 문제

프로젝트는 지금까지 시간 필드를 **`Instant` + ISO-8601 UTC(`Z` suffix)** 로 다뤄 왔다. 그 결과:

- 서버와 모바일이 **같은 KST 환산 로직을 각자 구현**하고 있다 — `KstDeadlineCalculator`(서버) ↔ `KstDeadline`(모바일)이 사실상 중복이다.
- 모바일은 `kotlinx-datetime`을 배제하고 stdlib `kotlin.time.Instant`만 쓰기로 했는데(home-feed), KST 변환이 필요할 때마다 **직접 산술로 푸는 코드**가 늘고 있다. `challenge-create`에서는 `floorDiv` + `civil_from_days`를 손으로 구현하고 테스트 9건으로 못박아야 했다.
- 이 서비스는 **KST 단일 타임존**을 전제한다(해외 대응은 명시적 비범위). UTC 왕복이 실익 없이 양쪽에 환산 코드를 만든다.

## 결정 사항 (2026-07-31, 사용자 확정)

1. **DB는 KST로 저장한다.** 현재 모든 시간 컬럼이 `timestamp without time zone`이라 **컬럼 타입 변경은 없고 해석 기준만 UTC → KST로 바뀐다.**
2. **서버 → 모바일 응답은 `yyyy-MM-dd HH:mm:ss`.** `T` 구분자도 `Z` suffix도 없다.
3. **모바일 → 서버 요청도 같은 패턴.**
4. **모바일은 최종적으로 `LocalDateTime`과 `LocalDate`만 사용한다.** `Instant`를 도메인·UI 계층에서 제거하는 것이 목적이다.

> ⚠️ **이 포맷은 ISO-8601이 아니다.** ISO-8601은 날짜와 시간 사이에 `T`를 요구한다. CLAUDE.md의 "시간 포맷은 ISO-8601 UTC" 규칙을 명시적으로 대체하는 결정이므로, 규칙 문구를 함께 개정한다(T-P1).

## 🔴 실제 문제는 "UTC → KST 전환"이 아니라 **"이미 갈라진 두 기준의 통일"**이다

> **2026-07-31 정정.** 초안은 "서버가 UTC로 저장 중이니 KST로 바꾼다"를 전제했다. **틀렸다.** backend-dev가 착수 전 실측으로 잡았고 pm-lead가 재확인했다. 초안대로 V6에서 `+9h`를 쳤으면 **멀쩡한 데이터를 손상시킬 뻔했다.**

### 실측 (2026-07-31)

```
users 실데이터:
  created_at              = 2026-05-07 10:10:42
  updated_at              = 2026-07-28 11:01:23
  refresh_token_issued_at = 2026-07-31 08:55:05
DB now()  = 2026-07-31 09:26:25   (Postgres TimeZone = Asia/Seoul)
UTC now() = 2026-07-31 00:26:25
friendships=0  challenges=0  verifications=0  user_stats=0
```

**`users` 1행은 이미 KST다.** `refresh_token_issued_at`이 현재보다 28분 전 — 오늘 아침 로그인 시각과 정확히 맞는다. 이 값이 UTC였다면 KST로는 17:55, 즉 **미래**다. 리프레시 토큰이 미래에 발급될 수는 없다.

### 원인 — 서버 안에 시계가 두 갈래다

| 사용처 | 방식 | 지금 값 |
|---|---|---|
| `ChallengeCommandService` (challenge-create) | 주입된 `Clock.systemUTC()` (`app/config/ClockConfig.kt`) | **00:26 (UTC)** |
| `UserEntity` / `FriendshipEntity` / `ChallengeEntity` / `VerificationEntity` / `UserRecordEntity` 기본값 | `LocalDateTime.now()` | **09:26 (KST)** |
| `FriendService` / `AuthService` / `UserRecord` | `LocalDateTime.now()` | **09:26 (KST)** |

`LocalDateTime.now()`는 **JVM 기본 타임존**을 따르고 이 머신은 `Asia/Seoul`이다. 그래서 `foundation` 이래의 코드는 처음부터 KST로 기록해 왔다.

**즉 "DB TIMESTAMP를 UTC로 간주한다"는 문서상 규약을 레포의 나머지 코드가 한 번도 지키지 않았다.** `challenge-create`가 그 규약을 충실히 따라 `Clock.systemUTC()`를 도입하면서 **UTC 섬**이 생겼고, 같은 DB에 9시간 다른 두 기준이 공존하게 됐다. `challenges`/`verifications` row가 0이라 아직 실害가 없을 뿐이다. 실사용됐다면 `challenges.created_at`(UTC)과 `friendships.created_at`(KST)이 섞였을 것이다.

### 따라서 이 feature의 성격

- **데이터 보정이 아니다.** `users` 1행은 이미 맞고 나머지는 row 0이다.
- **서버 엔티티 계층은 이미 `LocalDateTime`이다.** 바꿀 대상은 `Instant`를 쓰는 곳 — DTO 직렬화, `ChallengeCommandService`, `KstDeadlineCalculator`다.
- **핵심 작업은 (1) 시계 기준 단일화 (2) 직렬화 포맷 통일 (3) 모바일 `Instant` 제거**다.

### 지금이 적기인 이유

`challenges`/`verifications`/`friendships`/`user_stats` 전부 row 0이다. **UTC 섬이 실데이터를 만들기 전에 닫는 마지막 시점**이다. 챌린지가 쌓인 뒤엔 섞인 기준을 사후 판별해야 한다.

## 마이그레이션 전 baseline (2026-07-31, `challenge-create` #7에서 실측)

실서버 + 실 Postgres에 실제 JWT로 5 endpoint를 호출한 **58/58 PASS** 결과에서 확보한 대조 기준이다.

```
deadline   = "2026-07-31T15:00:00Z"    (= KST 08-01 00:00)
createdAt  = "2026-07-31T00:31:01Z"    (밀리초 없음 — 초 절삭 동작)
DB 저장값   = 2026-07-31 15:00:00       (UTC 기준으로 기록됨 = challenge-create의 UTC 섬)
```

**마이그레이션 후 기대값**
```
deadline   = "2026-08-01 00:00:00"
DB 저장값   = 2026-08-01 00:00:00
```

> **같은 순간의 다른 표기**다. 실제 마감 시각은 변하지 않는다. 이 대조가 어긋나면 시각이 이동한 것이므로 즉시 중단할 것.

## 사용자 시나리오

이 feature는 사용자 대면 동작을 바꾸지 않는다. 검증은 **동작 보존**으로 한다.

1. (사용자) 홈 진입 → 진행 중 챌린지 카드의 남은 시간이 **마이그레이션 전과 동일하게** 표시된다
2. (사용자) 챌린지 생성 → `오늘 자정` 선택 → 마감이 **KST 당일 24:00**으로 잡힌다 (기존과 동일)
3. (사용자) 받은 도전장 목록 → 마감 임박(잔여 1시간) 강조가 기존과 동일하게 동작한다
4. (사용자) 친구 목록 → `since` 날짜가 기존과 동일하게 표시된다

## 수용 기준 (Acceptance Criteria)

### 계약 / 직렬화
- [ ] 서버의 모든 날짜+시간 응답 필드가 `yyyy-MM-dd HH:mm:ss` 문자열로 직렬화된다 (`T`·`Z`·offset·밀리초 없음)
- [ ] 서버의 날짜 전용 응답 필드(`challengeDate`)가 `yyyy-MM-dd`로 직렬화된다
- [ ] 서버가 요청 본문의 같은 패턴 문자열을 역직렬화한다 — ⚠️ **현재 요청 DTO에 시간 필드가 0건**이라(`CreateChallengeBody` / `AcceptChallengeBody` / `SendFriendRequestBody`) 이 기준은 그대로 두면 **공허하게 통과**한다. 전역 deserializer를 등록하고 **합성 DTO로 단위 테스트**해 "미래에 시간 필드가 추가돼도 동작"을 보장하는 것으로 대체한다 (2026-07-31 backend-dev 제기 → pm-lead 승인)
- [ ] 위 3건이 **컨트롤러 슬라이스 테스트에서 실제 JSON 문자열로 assert**된다 (Jackson 설정 변경에 대한 회귀 방지 — challenge-create 선례)
- [ ] `confirmed` 계약 3건(`challenge-create`, `home-feed`, `friends`)의 시간 필드 표기가 갱신되고 각 `change-log.md`에 기록된다

### 백엔드
- [ ] 서버가 시간 값을 **KST 기준으로 DB에 저장**한다
- [ ] **서버 전체가 단일 시계 기준을 쓴다** — `Clock.systemUTC()` 유래의 UTC 경로가 0건이 되고, 시각 취득 지점이 KST 하나로 통일된다 (JVM 기본 타임존에 의존하지 않는 방식으로)
- [ ] ~~기존 `users` 1행의 3개 시간 컬럼이 UTC → KST로 보정된다~~ → **삭제.** 이미 KST이므로 보정하면 **손상**이다. 대신: **`users` 1행이 변경되지 않고 그대로 유지된다** (마이그레이션이 데이터를 건드리지 않았음을 확인)
- [ ] `deadlineType=TODAY` 생성 시 `deadline`이 **KST 당일 24:00**으로 저장된다 (마이그레이션 전과 동일한 실제 시각)
- [ ] `challengeDate`가 KST 기준 날짜로 저장된다 (기존과 동일)
- [ ] 받은 도전장의 마감 필터(`deadline > now()`)가 KST 기준으로 올바르게 동작한다
- [ ] 서버 유닛·슬라이스 테스트 전건 통과, 회귀 0

### 모바일
- [ ] `:domain:model`의 시간 필드에 `Instant`가 **0건** 남는다 (`LocalDateTime` / `LocalDate`만 사용)
- [ ] `:core:utils`의 상대 시간 표기 함수가 `LocalDateTime` 기반으로 동작한다
- [ ] mapper가 `yyyy-MM-dd HH:mm:ss` / `yyyy-MM-dd`를 파싱한다
- [ ] **파싱 실패가 조용히 삼켜지지 않는다** — 현재 `Instant.DISTANT_PAST` 폴백은 파싱 에러를 "이미 마감된 카드"로 위장한다. 대체 전략을 정하고 테스트로 고정한다
- [ ] 모바일 유닛 테스트 전건 통과. 보고 형식: **"기존 87건 회귀 0 / 의도적 삭제 1건 / 신규 N건(그중 2건이 삭제분의 대체)"**
  > **회귀 카운트 정밀화 (2026-07-31, mobile-dev 제기 → pm-lead 승인, 2차 정정 반영)**
  > 삭제 대상은 `ChallengeRepositoryImplTest.kt:107`의 `getReceivedChallenges - 시간 파싱 실패 시 DISTANT_PAST 폴백` **단 1건**이다(88건 중 옛 동작을 고정하는 유일한 테스트). 이번 결정으로 폴백 자체가 사라지므로 이 테스트는 **정반대 동작을 고정한 테스트**가 된다. "88/88 그대로"는 오히려 실패 신호다.
  > **1:1 교체가 아니다.** 그 테스트는 한 케이스에서 `deadline`과 `createdAt`을 동시에 단언하는데, 새 정책은 두 필드를 **정반대로 가른다**(`deadline` 실패 → 항목 제외 + `onError` / `createdAt` 실패 → null 유지 + 항목 보존). 한 테스트로 담을 수 없으므로 **삭제 1건 → 신설 최소 2건**이다. 억지로 1:1을 맞추지 않는다 — 정책이 갈린 지금 두 단언을 묶으면 의도가 흐려진다.
- [ ] **센티넬 폴백이 mapper 3곳에서 모두 제거되고, 각각 테스트가 붙는다** — `ChallengeMappers:51` / `FriendMappers:66` / `ActiveChallengeResponseMapper:34`. ⚠️ **뒤 2곳은 현재 테스트가 없어서 센티넬을 걷어내도 회귀 카운트에 잡히지 않는다**(2026-07-31 mobile-dev 확인). 카운트에 안 잡힌다는 건 **검증되지 않는다는 뜻**이므로, 이번에 동작을 바꾸는 이상 테스트를 새로 붙인다.
- [ ] **임시 probe 파일이 남아 있지 않다** — `core/utils/.../DatetimeProbe.kt` + `DatetimeProbeTest.kt`는 #9(타입 실측) 산출물이다. T-M3/T-M4의 실제 구현으로 접어 넣고 **삭제**한다. `core/utils/build.gradle.kts`에서 제거된 "추가 의존성 불필요" 주석도 새 사실에 맞게 정리한다.
- [ ] Android·KMP common·iOS framework link 빌드 성공

### 문서
- [ ] CLAUDE.md의 "시간 포맷은 ISO-8601 UTC" 규칙이 새 규약으로 개정된다
- [ ] ADR-0010의 상태가 `accepted — 구현 대기` → `accepted — 구현 완료`로 갱신된다

## 비범위 (Out of Scope)

- **다중 타임존 지원** — KST 단일 고정. 해외 사용자 대응은 하지 않는다.
- **`contracts` / `notifications` / `taunt_messages` 테이블** — 아직 사용처가 없다. 컬럼 해석 기준만 KST로 문서화하고 코드는 건드리지 않는다.
- **`user_stats.updated_at`** — 응답에 노출되지 않는다. 저장 기준만 맞춘다.
- **Flyway `installed_on`** — Flyway 내부 컬럼. 건드리지 않는다.
- **UI/디자인 변경** — 표시 문구·레이아웃 변경 없음. design-bridge는 이 feature에 참여하지 않는다.
- **`challenge-create` #7 통합 검증** — 별개 태스크로 남아 있다. 이 feature와 순서 관계는 "의존 관계" 참조.

## 태스크 분해

### 백엔드 (backend-dev)

- [ ] **T-B1**: **시계 기준 단일화** — 이게 이 트랙의 핵심이다. `ClockConfig`의 `Clock.systemUTC()`가 만든 UTC 섬을 제거하고, 시각 취득을 KST 하나로 통일한다. **JVM 기본 타임존에 의존하지 않는 방식**이어야 한다(현재 이 머신이 우연히 `Asia/Seoul`이라 맞고 있을 뿐이며, ADR-0007의 AWS 배포에서 UTC면 조용히 깨진다). 흩어진 `LocalDateTime.now()` 호출부(엔티티 기본값 5곳 + 서비스 3곳)도 함께 정리. `Instant`를 쓰는 `ChallengeCommandService` / `KstDeadlineCalculator` → `LocalDateTime`. `KstDeadlineCalculator`는 UTC 환산이 사라져 대폭 단순화되거나 제거된다.
  > **서버 엔티티 계층은 이미 `LocalDateTime`이다.** 바꿀 대상은 `Instant`를 쓰는 DTO·서비스·계산기다.
- [ ] **T-B2**: ~~V6 데이터 보정~~ → **"보정 불필요 확인 + 근거 기록"으로 성격 변경** (2026-07-31). `users` 1행은 이미 KST이므로 **`+9h`를 치면 손상이다**(`refresh_token_issued_at`이 미래가 된다). 나머지 테이블은 row 0. **DML 없는 마이그레이션으로 근거를 주석에 남기거나, 마이그레이션 자체를 만들지 않는다 — backend-dev가 판단해 선택한다.** 어느 쪽이든 "왜 보정하지 않았는지"가 레포에 남아야 한다(다음 사람이 같은 오판을 반복하지 않도록).
- [ ] **T-B3**: DTO 직렬화·역직렬화 — 응답 DTO 전건에 `@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")`, 날짜 전용은 `"yyyy-MM-dd"`. 요청 DTO도 동일 패턴 역직렬화. 대상: `ChallengeCommandDtos`, `ActiveChallengeResponse`, `FriendListResponse`.
  - **🔴 `HttpMessageNotReadableException` 핸들러를 함께 추가한다** (2026-07-31 #7에서 backend-dev 발견 → pm-lead 승인). 현재 `GlobalExceptionHandler`가 이 예외를 처리하지 않아 `handleUncaught` → **HTTP 500 + code 500**이 나간다. ADR-0002상 비즈니스 에러는 HTTP 200 + 7xx여야 한다.
    ```
    {"opponentId":}                → HTTP 500 / code 500   (현재)
    {"deadlineType":"YESTERDAY"}   → HTTP 500 / code 500   (현재)
    ```
    지금은 정상 클라이언트가 well-formed JSON만 보내 영향이 낮지만, **이 feature가 요청 본문에 시간 문자열을 들이는 순간 포맷이 틀린 날짜가 정확히 이 경로로 500을 만든다.** 핸들러를 추가하면 "요청 역직렬화" 수용 기준이 **실제로 검증 가능해진다** — 잘못된 포맷을 보내 7xx가 나오는지 확인하는 경로가 생기기 때문이다. (공허한 기준 문제의 실질적 해법)
- [ ] **T-B4**: 테스트 갱신 — 컨트롤러 슬라이스가 **실제 JSON 문자열**을 assert하도록 유지(`[2026,7,28]` 배열 회귀 방지 선례). 서비스 단위 테스트의 시간 경계 케이스를 KST 기준으로 재작성. 전건 통과 + 회귀 0 확인.

### 모바일 (mobile-dev)

- [x] **T-M1**: ✅ **2026-07-31 완료.** `kotlinx-datetime` **도입 가능 확정. 자체 타입 불필요.** Android/JVM 6/6 + iOS SimulatorArm64 6/6 passed로 실측(문서 아님). iOS 네이티브 tzdb에서 `TimeZone.of("Asia/Seoul")` 동작 확인 — 이게 최대 리스크였는데 통과했다.
  > **🔴 `challenge-create`에서 깨진 진짜 원인은 API 비호환이 아니라 버전 스큐였다.** `libs.versions.toml`이 0.6.2를 선언했고 **JVM/Android 타깃은 그 0.6.2를 그대로 썼는데**, common metadata만 `compose.material3:1.9.0` 제약으로 0.7.1로 해석됐다. 0.6.2의 `kotlinx.datetime.Instant`는 `kotlin.time.Instant`와 **별개 클래스**라 확장이 안 걸린다. 0.7.1은 `typealias Instant = kotlin.time.Instant`이고 `TimeZone.kt`가 `kotlin.time.Instant`를 import해 확장이 직접 걸린다. **선언을 0.7.1로 맞추니 그대로 컴파일된다 — 라이브러리가 아니라 우리 버전 선언이 문제였다.**
  > **부수 소득**: `compose.material3`가 이미 kotlinx-datetime을 의존성 그래프에 끌어오고 있다. 도입은 **신규 서드파티 추가가 아니라 이미 있는 것을 선언하는 것**이다.
  > **확정 API** (양 플랫폼 통과): `TimeZone.of("Asia/Seoul")` / `LocalDateTime.Format { ... }` 커스텀 포맷 파싱·포맷 왕복 / `LocalDate.parse` / `Clock.System.now().toLocalDateTime(KST)` / `toInstant(KST)` 차이로 `Duration` / `plus(1, DateTimeUnit.DAY)`.
  > **`"2026-07-28T15:04:05"`(ISO `T` 구분자)가 파싱 실패하는 것도 테스트로 고정했다** — 서버가 실수로 `T`를 흘리면 조용히 통과하지 않는다.
  > **트랩**: `LocalDateTime`은 `monthNumber`/`day`를 멤버로 갖지만 `month.number`는 최상위 확장이라 `import kotlinx.datetime.number` 없이는 깨진다.
- [ ] ~~**T-M1(원안)**: `kotlinx-datetime` 도입 — **버전 충돌 선결.**~~ `libs.versions.toml` 선언은 0.6.2인데 실제 해석이 `strictly 0.7.1`이다. 0.7.x에서 `Instant`만 `kotlin.time`으로 이동했고 `LocalDateTime`/`LocalDate`는 `kotlinx.datetime`에 그대로 있으므로 도입 가능하다. **다만 실제 해석 버전과 API를 실측으로 확인하고 착수할 것** — challenge-create에서 문서 예시를 믿고 썼다가 컴파일이 깨진 선례가 있다. 자체 타입을 만드는 대안도 검토 대상.
- [ ] **T-M2**: `:domain:model` 시간 필드 타입 교체 — `ActiveChallenge`, `ReceivedChallenge`, `Friend`, `FriendRequest`. `Instant` 0건이 목표.
- [ ] **T-M3**: `:core:utils` 정리 — `InstantFormat.toRelativeKoreanString`을 `LocalDateTime` 기반으로 재작성(`"곧 마감"`/`"마감"` 반환 동작 보존). `KstDeadline`은 서버가 KST를 주므로 **대부분 불필요해진다** — 남길 부분만 남기고 정리. 기존 테스트 9건의 경계 의도(날짜 경계·월말·연말·윤년)를 새 구현에서도 유지.
- [ ] **T-M4**: `:remote:mapper` 파싱 — `yyyy-MM-dd HH:mm:ss` / `yyyy-MM-dd` 파서. **`Instant.DISTANT_PAST` 폴백 대체 전략을 정하고 테스트로 고정한다**(수용 기준 참조).
- [ ] **T-M5**: ItemState·화면·테스트 갱신 — `:feature:home`(`HomeUiState`, `ReceivedChallengeItemState`, `HomeScreen`), `:feature:friends:list`(`FriendItemStates`), `:feature:challenge:create`(`Screen`, `FriendPickStep`). 유닛 테스트 전건 + **기존 88건 회귀 0** 실측.

### PM (pm-lead)

- [ ] **T-P1**: CLAUDE.md 시간 포맷 규칙 개정 + `confirmed` 계약 3건 갱신 + 각 `change-log.md` 기록 + ADR-0010 상태 갱신.

## 의존 관계

- **`challenge-create` #7(통합 검증)을 이 feature보다 먼저 끝낸다.** 현재 서버가 새 코드로 떠 있고 5 endpoint가 등록된 상태라, **마이그레이션 전 baseline을 확보**하는 의미가 있다. 시간 포맷을 바꾼 뒤 문제가 생기면 원인 절연이 어려워진다.
- T-M2~T-M5, T-B1·T-B3·T-B4는 `api-contract.md` 상태가 `confirmed`가 된 뒤 착수.
- T-B2(V6 마이그레이션)는 계약과 독립 — 선행 착수 가능.
- T-M1(kotlinx-datetime 실측)은 계약과 독립 — **선행 착수 권장.** 여기서 자체 타입으로 가야 한다는 결론이 나오면 계약 협의에 영향을 준다.
- T-M2 → T-M3/T-M4 → T-M5.
- T-P1은 구현 완료 후.

## 리스크 / 오픈 이슈

- **🔴 `Z` suffix 제거가 조용히 깨진다** — 모바일이 `Instant.parse()` 실패 시 `Instant.DISTANT_PAST`로 폴백하는 구조라 **파싱 에러가 예외가 아니라 "이미 마감된 카드"로 화면에 나타난다**(home-feed 선례, challenge-create 계약 L222 명시). 서버·모바일이 동시에 바뀌지 않으면 이 방식으로 터진다. 이번 작업에서 **폴백 전략 자체를 손보는 것이 수용 기준에 포함된 이유**다.
- **🟡 `LocalDateTime`은 offset을 잃는다** — "이 값은 KST"라는 약속이 타입이 아니라 문서와 관행에만 존재하게 된다. 서버·모바일·DB 세 곳의 해석이 어긋나면 컴파일러가 잡아주지 못한다. 계약에 기준을 명문화하고 슬라이스 테스트로 고정하는 것으로 대응한다.
- **🟡 서버 `now()`의 기준** — Postgres 서버 타임존은 `Asia/Seoul`이지만 JVM 기본 타임존은 실행 환경에 따라 다르다. `LocalDateTime.now()`가 JVM 타임존을 따르므로 **명시적으로 KST를 지정할지 결정**해야 한다. 배포 환경(ADR-0007 local→AWS)에서 JVM 타임존이 UTC면 9시간 어긋난다.
- **🟡 `challenge-create`가 방금 끝났다** — 88/88(모바일) + 111/111(서버)로 검증된 코드를 바로 다시 건드린다. 회귀 확인이 특히 중요하다.
- **🟢 데이터 보정 비용은 지금이 최저** — `users` 1행뿐. 미루면 단조 증가한다.
