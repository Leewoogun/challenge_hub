# API Contract — 날짜·시간 모델 통일 (datetime-model-migration)

- **feature-id**: datetime-model-migration
- **상태**: confirmed
- **최종 수정**: 2026-07-31 by backend-dev (오픈 이슈 **7건 전부 해소** — 미결 항목 없음)
- **상위 spec**: [spec.md](./spec.md) · **근거 ADR**: [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)

## 성격

이 feature는 **신규 엔드포인트를 만들지 않는다.** 기존 `confirmed` 계약 3건의 **시간 필드 표기 규약만 개정**한다. 따라서 본 문서는 "전역 시간 규약"을 정의하고, 영향받는 필드를 열거하는 형태다.

---

## 1. 전역 시간 규약 (신규 — 기존 규약 대체)

### 1.1 표기

| 종류 | 패턴 | 예시 | 비고 |
|---|---|---|---|
| 날짜 + 시간 | `yyyy-MM-dd HH:mm:ss` | `2026-07-28 15:00:00` | 구분자는 **공백**. `T` 없음 |
| 날짜 전용 | `yyyy-MM-dd` | `2026-07-28` | |

- **offset·`Z` suffix·밀리초·나노초를 붙이지 않는다.**
- **모든 시간 값은 KST(UTC+9) 기준이다.** 표기에 타임존 정보가 없으므로 이 문서가 유일한 기준이다.
- **요청·응답 양방향에 동일 적용.**

> ⚠️ **ISO-8601이 아니다.** ISO-8601은 날짜와 시간 사이에 `T`를 요구한다(`2026-07-28T15:00:00`). CLAUDE.md의 "시간 포맷은 ISO-8601 UTC" 규칙을 이 규약이 대체한다.
>
> **관대하게 받지 않는다.** mobile-dev 실측 확인: `T` 구분자 문자열(`"2026-07-28T15:04:05"`)은 모바일 파서에서 **실패하며, 실패한다는 것 자체를 테스트로 고정**했다. 서버가 실수로 `T`를 흘리면 조용히 통과하지 않고 잡힌다.

### 1.2 계층별 타입 (확정)

| 계층 | 날짜+시간 | 날짜 전용 |
|---|---|---|
| DB (Postgres) | `timestamp without time zone` — **KST 기준으로 저장** | `date` |
| 서버 (Kotlin) | `java.time.LocalDateTime` | `java.time.LocalDate` |
| JSON | `"2026-07-28 15:00:00"` | `"2026-07-28"` |
| 모바일 (Kotlin) | **`kotlinx.datetime.LocalDateTime`** | **`kotlinx.datetime.LocalDate`** |

**모바일 도메인·UI 계층에 `Instant`를 남기지 않는다.**

> **모바일 타입 확정 근거 (2026-07-31 mobile-dev T-M1 실측)** — 자체 타입을 만들지 않고 `kotlinx-datetime`을 쓴다.
> - `:core:utils:testDebugUnitTest` **6/6 passed**, `:core:utils:iosSimulatorArm64Test` **6/6 passed**, 기존 `KstDeadlineTest` 9/9 양쪽 유지(회귀 0), Android·KMP common·iOS 컴파일 BUILD SUCCESSFUL
> - challenge-create에서 깨졌던 원인은 API 비호환이 아니라 **버전 스큐**였다 — `libs.versions.toml` 선언은 0.6.2인데 common metadata만 0.7.1로 해석됐고, JVM/Android는 0.6.2를 썼다. 0.6.2의 `kotlinx.datetime.Instant`는 **별개 클래스**라 `kotlin.time.Instant`와 매칭이 안 됐다. 0.7.1은 `typealias Instant = kotlin.time.Instant`라 그대로 컴파일된다. **선언을 0.7.1로 맞추는 것이 선결 조건.**
> - `compose.material3`가 이미 kotlinx-datetime을 의존성 그래프에 끌어오고 있다 — **신규 서드파티 추가가 아니라 이미 있는 것을 선언하는 것**이다.

#### 모바일 파서 (실측 확인된 형태)

`kotlinx.datetime`의 기본 `parse()`는 ISO(`T` 구분자)라 **공백 포맷을 읽지 못한다.** 커스텀 포맷이 필요하다:

```kotlin
val WIRE_DATETIME = LocalDateTime.Format {
    year(); char('-'); monthNumber(); char('-'); day()
    char(' ')
    hour(); char(':'); minute(); char(':'); second()
}
WIRE_DATETIME.parse("2026-07-28 15:04:05")   // OK (Android·iOS 양쪽 확인)
value.format(WIRE_DATETIME)                   // 왕복 일치 확인
LocalDate.parse("2026-07-28")                 // 날짜 전용은 기본 파서로 충분 (ISO date와 동일)
```

> 트랩: `LocalDateTime`은 `monthNumber`/`day`를 **직접 멤버**로 갖는다. `month.number`는 최상위 확장이라 `import kotlinx.datetime.number` 없이 쓰면 `Unresolved reference 'number'`로 깨진다 (mobile-dev가 실제로 겪음).

### 1.3 직렬화 고정 방식 (확정 — 명시가 정본 + 전역 안전망 병행)

- 응답 DTO 필드마다 `@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")`(날짜 전용은 `"yyyy-MM-dd"`)를 **명시적으로** 붙인다. challenge-create에서 `[2026,7,28]` 배열 직렬화 회귀를 막기 위해 세운 방침을 그대로 승계.
- **추가로 전역 `ObjectMapper`(`JavaTimeModule`) 설정도 같은 패턴으로 건다** — 새 DTO에서 어노테이션을 빠뜨려도 포맷이 맞도록. 명시가 정본이고 전역은 안전망이다(§1.4의 (c)와 같은 사고방식).
- **컨트롤러 슬라이스 테스트가 실제 JSON 문자열을 assert**한다.

### 1.4 서버 `now()` 기준 → **(c) 병행 확정**

> 🔴 **초안은 이걸 "배포 환경에서 어긋날 수 있다"는 미래형 리스크로 적었으나, 실측 결과 이미 현재형 버그였다** (2026-07-31 backend-dev 발견, pm-lead 재현).

| 사용처 | 방식 | 실측값 (동시각) |
|---|---|---|
| `ChallengeCommandService` | 주입된 `Clock.systemUTC()` (`app/config/ClockConfig.kt`) | **00:26 (UTC)** |
| 엔티티 5종 기본값 + `FriendService` / `AuthService` / `UserRecord` | `LocalDateTime.now()` | **09:26 (KST)** |

같은 DB에 9시간 다른 두 기준이 공존했다. `challenges`/`verifications` row가 0이라 실害가 없었을 뿐이다.

**확정 방식 (c) — 정본 + 안전망**:

1. `Clock` 빈을 **`Clock.system(ZoneId.of("Asia/Seoul"))`** 로 교체. 주입받는 서비스는 `LocalDateTime.now(clock)`.
2. 주입이 어려운 곳(**JPA 엔티티 필드 기본값**)을 위해 `:core`에 **KST 고정 헬퍼**를 두고 그것만 쓴다.
3. 앱 기동 시 JVM 기본 타임존도 KST로 고정 — **안전망**.

**(a) 단독을 채택하지 않은 이유**: 헬퍼는 *모든 호출부가 써야만* 동작하는데, 엔티티 기본값처럼 흩어진 자리를 **실제로 놓쳐 왔다**(위 표가 증거). 새 엔티티를 추가하는 사람이 습관적으로 `LocalDateTime.now()`를 쓰면 다시 갈라진다.
**(b) 단독을 채택하지 않은 이유**: 코드에 안 보여서 환경이 바뀌면 조용히 깨진다.

> 🔴 **pm-lead 조건**: JVM 기본 타임존에 의존하는 방식은 **금지**. 지금 맞고 있는 건 이 머신이 우연히 `Asia/Seoul`이기 때문이고 ADR-0007의 AWS 배포에서 UTC면 조용히 깨진다. (b)를 포함하더라도 **코드로 보장되는 경로(1·2)가 반드시 있어야 한다.**

---

## 2. 영향받는 필드 (기존 `confirmed` 계약 3건)

### 2.1 `challenge-create`

| 엔드포인트 | 필드 | 기존 (baseline 실측) | 신규 |
|---|---|---|---|
| `POST /api/v1/challenges` (응답) | `challengeDate` | `"2026-07-31"` | **변경 없음** (`LocalDate`) |
| | `deadline` | `"2026-07-31T15:00:00Z"` | `"2026-08-01 00:00:00"` |
| `GET /api/v1/challenges/received` | `challengeDate` | `"2026-07-31"` | **변경 없음** |
| | `deadline` | `"2026-07-31T15:00:00Z"` | `"2026-08-01 00:00:00"` |
| | `createdAt` | `"2026-07-31T00:31:01Z"` | `"2026-07-31 09:31:01"` |

> 위 "기존" 값은 추정이 아니라 **2026-07-31 #7 통합 검증에서 실서버로 받은 실측 baseline**이다. `deadline` 표기가 `15:00:00Z` → `00:00:00`으로 바뀌는 건 **같은 순간을 KST로 표기**한 것이다. 실제 마감 시각은 변하지 않는다.
> 요청 본문에는 시간 필드가 없다(`deadlineType` enum만 보낸다) — **이 설계가 이번 마이그레이션에서 유리하게 작동한다.**

### 2.2 `home-feed`

| 엔드포인트 | 필드 | 기존 | 신규 |
|---|---|---|---|
| `GET /api/v1/challenges/active` | `deadline` | `"...Z"` | `"yyyy-MM-dd HH:mm:ss"` |

### 2.3 `friends` — `since`는 **시각까지 유지** (날짜 전용으로 낮추지 않는다)

| 엔드포인트 | 필드 | 기존 | 신규 |
|---|---|---|---|
| `GET /api/v1/friends` | `since` | `"...Z"` | `"yyyy-MM-dd HH:mm:ss"` |
| `GET /api/v1/friends/requests/received` | `requestedAt` | `"...Z"` | `"yyyy-MM-dd HH:mm:ss"` |

> **날짜 전용으로 낮추지 않은 이유 (2026-07-31 확정)**: `FriendItemStates.formatSince`는 일 단위 버킷("오늘 친구가 됨" / "N일 전")이라 **시각을 화면에 표시하지는 않지만 계산에는 쓴다.** 날짜로 절삭하면 표시가 바뀐다 —
> - 현재: 어제 23:00에 친구 → `diff = 10시간` → **"오늘 친구가 됨"**
> - 날짜 전용: 어제 00:00으로 절삭 → `diff = 33시간` → **"1일 전 친구가 됨"**
>
> spec 수용 기준이 **동작 보존**이므로 표시가 바뀌면 안 된다. `friendships.accepted_at`은 이미 `TIMESTAMP`라 정보가 있고, **버린 정보는 계약을 다시 바꿔야 되찾는다.** 정밀도가 과하면 클라가 언제든 잘라 쓸 수 있다.

### 2.4 날짜 전용 필드는 `challengeDate` 하나뿐 — 확대하지 않는다

`createdAt` 류를 날짜로 낮추면 **같은 날 도착한 항목들의 정렬 근거가 사라진다.** 지금은 서버가 `created_at DESC`로 정렬해 주지만 클라가 재정렬하거나 "N분 전 도착" 표시를 넣으면 즉시 부족해진다. `challengeDate`만 날짜 전용을 유지한다 — DB도 `DATE` 컬럼이고 개념 자체가 날짜다.

> 참고: `createdAt`은 현재 `ReceivedChallengeItemState`에 **노출되지 않는다**(정렬 근거로만 쓰인다). 지금 안 쓴다는 사실이 정보를 버릴 근거는 아니라는 데 양측이 합의했다.

---

## 3. 모바일 파싱 실패 정책 → **필드 중요도로 분기 확정**

현행 `Instant.DISTANT_PAST` 센티넬 폴백은 파싱 에러를 **"이미 마감된 카드"로 위장**한다. 이번 포맷 변경이 정확히 그 경로이므로 함께 손본다.

| 필드 | 정책 | 근거 |
|---|---|---|
| `deadline` | **(a) 해당 항목을 목록에서 제외 + `onError` 발화** | 카드 UI 전체(`deadlineText`·`isUrgent`)가 이 필드 하나에 걸려 있다. 없으면 카드가 거짓말을 한다 |
| `createdAt`, `since`, `requestedAt` | **(b) nullable + UI가 "-" 표시** | 없어도 카드는 온전히 기능한다. `sinceText` 한 줄만 비면 된다 |

**(c) 현행 유지는 기각.** 마이그레이션 회귀가 나면 화면상 정상으로 보여 발견이 늦는다.

### 구현 통로 (mobile-dev 설계 — mapper는 `onError`에 접근할 수 없다)

mapper는 순수 함수(`Response.toDomain()`)이고 `onError`는 repository가 들고 있다. 그래서:

1. 파서가 `LocalDateTime?`을 반환 → `deadline` 파싱 실패 시 해당 item mapper가 `null` 반환
2. repository가 `mapNotNull`로 거르고, **거른 개수가 있으면** `onError("일부 항목을 불러오지 못했어요")` **1회** 발화 후 나머지를 emit
3. `createdAt`/`since`는 `null`을 그대로 도메인에 실어 보내고 ItemState가 `-` 처리

이러면 (a)와 (b)가 한 파이프라인에서 공존하고 **"몇 건이 걸러졌는가"를 테스트로 고정**할 수 있다.

- `ChallengeRepositoryImplTest`의 기존 `시간 파싱 실패 시 DISTANT_PAST 폴백` 테스트는 **정반대 동작을 고정한 테스트라 폐기**하고 "파싱 실패 항목은 제외되고 `onError`가 1회 발화한다"로 교체한다.
- **전체 응답 실패(카드 0건 + 스낵바)는 기각** — 5건 중 1건이 깨졌다고 나머지 4건을 못 보게 하는 건 과하다. `onError`가 뜨니 조용하지도 않다.

---

## 4. 잘못된 요청 본문의 에러 코드 (신규 — #7에서 발견)

현재 `GlobalExceptionHandler`가 `HttpMessageNotReadableException`을 처리하지 않아 `handleUncaught` → **HTTP 500 + code 500**이 나간다. ADR-0002상 비즈니스 에러는 HTTP 200 + code 7xx여야 한다.

2026-07-31 #7 통합 검증 실측:
```
{"opponentId":}                → HTTP 500 / code 500
{"deadlineType":"YESTERDAY"}   → HTTP 500 / code 500
```

지금은 정상 클라이언트가 well-formed JSON만 보내 영향이 낮다. **그러나 이번 feature에서 요청 본문에 시간 문자열이 들어오기 시작하면, 포맷이 틀린 날짜가 정확히 이 경로로 500을 만든다.**

**확정**: T-B3(요청 역직렬화)에서 `HttpMessageNotReadableException` 핸들러를 함께 추가해 **HTTP 200 + code 700**으로 변환한다. 이로써 §5의 "요청 역직렬화" 검증도 실제로 의미를 갖는다.

---

## 5. 요청 역직렬화의 검증 범위 (한계 명시)

spec 수용 기준의 "서버가 요청 본문의 같은 패턴 문자열을 역직렬화한다"는 **현재 요청 DTO에 시간 필드가 0건**이라(`CreateChallengeBody` / `AcceptChallengeBody` / `SendFriendRequestBody`) 그대로 두면 공허하게 통과한다.

**확정 (가)**: 전역 deserializer를 등록하고 **합성 DTO로 단위 테스트**해 "미래에 시간 필드가 추가돼도 동작"을 보장한다.

> ⚠️ **이 테스트가 검증하는 것과 아닌 것** (mobile-dev 지적, 계약에 명시):
> - ✅ 검증함: **전역 설정이 `yyyy-MM-dd HH:mm:ss` 패턴을 읽는다**
> - ❌ 검증 못 함: **실제 엔드포인트가 그 형식을 받는다**
>
> 시간 필드를 가진 요청 DTO가 실제로 생기는 시점에 **그 엔드포인트의 슬라이스 테스트가 따로 필요하다.** "이미 검증됨"으로 오해하지 말 것.

---

## 오픈 이슈 — **전건 해소, 미결 없음**

1. ~~**서버 `now()` 기준**~~ — ✅ **(c) 병행 확정.** 미래형 리스크가 아니라 **이미 9시간 갈라져 있던 현재형 버그**임이 실측으로 드러났고(§1.4), 그것이 (a) 단독을 기각한 근거다. JVM 타임존 의존 방식은 pm-lead가 명시 금지.
2. ~~**모바일 파싱 실패 정책**~~ — ✅ **필드 중요도로 분기 확정** (§3). `deadline`=(a) 제외+`onError`, 나머지=(b) nullable. 구현 통로는 mobile-dev 설계 채택.
3. ~~**`friends.since` 정밀도**~~ — ✅ **시각까지 유지** (§2.3). 날짜로 낮추면 `formatSince` 표시가 바뀌어 "동작 보존" 기준 위반.
4. ~~**모바일 시간 타입**~~ — ✅ **`kotlinx.datetime.LocalDateTime`/`LocalDate` 확정** (§1.2). T-M1 실측 6/6+6/6 passed. 버전 선언을 **0.7.1로 맞추는 것이 선결 조건**.
5. ~~**`@JsonFormat` 명시 vs 전역**~~ — ✅ **명시가 정본 + 전역 안전망 병행** (§1.3).
6. ~~**날짜 전용 필드 확대**~~ — ✅ **확대 안 함.** `challengeDate` 하나만 날짜 전용 (§2.4).
7. ~~**요청 역직렬화 수용 기준이 공허**~~ — ✅ **(가) 전역 deserializer + 합성 DTO 테스트.** 검증 범위의 한계를 §5에 명시. 더불어 §4(잘못된 본문 → 500) 수정을 T-B3에 포함.

## 협의 이력

| 일시 | 작성자 | 변경 |
|------|-------|------|
| 2026-07-31 | pm-lead | 초안 — 전역 시간 규약 정의, 영향 필드 3계약 열거, 오픈 이슈 6건 (상태: `draft`) |
| 2026-07-31 | backend-dev | 서버 코드·DB 실측 후 6건 구체안 + **신규 이슈 7건째** 제기. 🔴 **초안 전제 2건이 사실과 다름을 발견** — (1) `users` 1행은 이미 KST라 `+9h` 보정 시 **데이터 손상**(`refresh_token_issued_at`이 미래가 됨), (2) 서버 `now()`는 미래형 리스크가 아니라 **이미 9시간 갈라진 현재형 버그**(`Clock.systemUTC()` vs `LocalDateTime.now()`). 이슈 3은 `formatSince` 동작 변화를 근거로 **시각 유지** 역제안 (상태: `draft` → `negotiating`) |
| 2026-07-31 | pm-lead | 실측 재현 후 **발견 3건 전부 승인.** spec 전면 정정(feature 성격을 "UTC→KST 전환" → "**이미 갈라진 두 기준의 통일**"), 수용 기준에서 "`users` 보정" 삭제 → "**변경되지 않고 유지**"로 교체, T-B2를 "보정 불필요 확인 + 근거 기록"으로 재정의. **조건**: JVM 기본 타임존 의존 방식 금지 — 코드로 보장되는 경로 필수 |
| 2026-07-31 | mobile-dev | **T-M1 실측 완료** — `kotlinx.datetime` 확정(6/6+6/6 passed, 회귀 0). challenge-create에서 깨진 원인이 API 비호환이 아니라 **버전 스큐(0.6.2 vs 0.7.1)**였음을 규명. 공백 구분자용 커스텀 포맷 실측 + **`T` 구분자가 실패하는 것도 테스트로 고정**. 이슈 2는 필드 중요도 분기에 동의하되 **mapper가 `onError`에 접근 불가**하다는 구현 제약을 짚고 통로 설계 제시. 이슈 3·5·6 동의, 7은 **검증 범위 한계 명시** 요청 |
| 2026-07-31 | backend-dev | 위 결정 전량 반영 — §1.2에 모바일 타입·파서 실측 결과, §1.4에 (c) 확정 + 실측 표, §2.1 기존값을 **#7 실측 baseline**으로 교체, §2.3 `since` 유지 근거, §3 구현 통로, **§4 신규(잘못된 본문 → 500, T-B3에서 수정)**, §5 검증 범위 한계 명시. **오픈 이슈 7건 전부 해소 — 미결 0건, 상태 `negotiating` → `confirmed`** |
