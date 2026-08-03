# 날짜·시간 모델 통일 (datetime-model-migration) — Summary

- **feature-id**: datetime-model-migration
- **완료일**: 2026-07-31
- **상태**: completed
- **근거 ADR**: [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)

## 구현 개요

프로젝트 전체의 시간 표현을 **`Instant` + ISO-8601 UTC(`Z`)** 에서 **`LocalDateTime` + KST + `yyyy-MM-dd HH:mm:ss`** 로 통일했다. 신규 엔드포인트는 없고 기존 `confirmed` 계약 3건의 시간 필드 표기만 개정한 **횡단 변경**이다.

**착수 후 문제 정의가 뒤집혔다.** 초안은 "서버가 UTC로 저장 중이니 KST로 바꾼다"였으나, 실측 결과 **서버는 이미 KST로 저장하고 있었고 진짜 문제는 시계가 두 갈래로 갈라져 있던 것**이었다 — `ChallengeCommandService`만 `Clock.systemUTC()`(UTC), 나머지 엔티티·서비스는 `LocalDateTime.now()`(JVM 기본 = KST). 같은 DB에 9시간 다른 두 기준이 공존했고, `challenges`/`verifications` row가 0이라 실害가 없었을 뿐이다.

즉 이 feature의 실제 성과는 **"UTC → KST 전환"이 아니라 "이미 갈라진 두 기준의 통일"** 이다.

## 엔드포인트

신규 없음. 기존 3계약의 시간 필드 표기만 변경.

| 계약 | 필드 | 이전 | 이후 |
|---|---|---|---|
| challenge-create | `deadline` · `createdAt` | `"2026-07-31T15:00:00Z"` | `"2026-08-01 00:00:00"` |
| challenge-create | `challengeDate` | `"2026-07-31"` | 변경 없음 |
| home-feed | `deadline` | `"...Z"` | `"yyyy-MM-dd HH:mm:ss"` |
| friends | `since` · `requestedAt` | `"...Z"` | `"yyyy-MM-dd HH:mm:ss"` |

## 주요 변경 파일

**백엔드**
- `core/.../time/KstTime.kt` (신규) — 주입 불가 지점(엔티티 기본값)용 KST 고정 헬퍼
- `app/.../config/ClockConfig.kt` — `Clock.systemUTC()` → `Clock.system(Asia/Seoul)`
- `controller/.../common/WireDateTimeFormat.kt` (신규) — `WIRE_DATETIME` / `WIRE_DATE` 상수
- `controller/.../config/JacksonDateTimeConfig.kt` (신규) — 전역 직렬화·역직렬화 안전망
- `controller/.../challenge/dto/ChallengeCommandDtos.kt` · `ActiveChallengeResponse.kt` · `friend/dto/FriendListResponse.kt`
- `app/.../db/migration/V6__datetime_kst_convention.sql` (신규) — **DML 0건**, `COMMENT ON COLUMN` 17건

**모바일**
- `gradle/libs.versions.toml` — `kotlinx-datetime` 0.6.2 → **0.7.1**
- `core/utils/.../datetime/{RelativeTimeFormat, KstDeadline}.kt` — 손으로 짠 날짜 산술 제거
- `domain/model/.../{ActiveChallenge, ReceivedChallenge, Friend, FriendRequest}.kt`
- `remote/mapper/` 3종 + **`commonTest` 소스셋 신설**
- `feature/{home, friends:list, challenge:create}` ItemState·화면

## 테스트 결과

**백엔드 — 123/123 passed, 0 failed** (이전 111, 순증 +12, 회귀 0)
- 신규: `KstTimeTest` 4 · `WireDateTimeSerdeTest` 7 · `GlobalExceptionHandlerTest` +2
- `KstDeadlineCalculatorTest` 17 → **16 (의도적 감소)** — UTC↔KST 경계 6건이 **검증 대상 자체를 잃어** 삭제되고, 자정 경계·윤년·타임존 무관성 5건으로 재구성
- **`TZ=UTC ./gradlew --stop && clean test --no-daemon` → 123/123 통과**

**백엔드 실서버 end-to-end — 65/65 PASS, 0 FAIL**
```
응답 deadline  "2026-07-31T15:00:00Z"  →  "2026-08-01 00:00:00"
DB  deadline   2026-07-31 15:00:00     →  2026-08-01 00:00:00
```

**모바일 — 123/123 passed, 0 failed**
- **기존 87건 회귀 0 / 의도적 삭제 1건 / 신규 36건**(그중 2건이 삭제분의 대체)
- 삭제 1건은 `DISTANT_PAST 폴백` 테스트 — 이번 결정으로 **정반대 동작을 고정한 테스트**가 되어 폐기
- Android · KMP common · iOS `linkDebugFrameworkIosSimulatorArm64` 전부 SUCCESS

**🔴 백엔드 통합 테스트 45건은 여전히 skip** — 컨테이너 런타임 부재.

## 결정 사항

1. **표기는 `yyyy-MM-dd HH:mm:ss` — ISO-8601이 아니다.** ISO는 `T`를 요구한다. CLAUDE.md의 "시간 포맷은 ISO-8601 UTC" 규칙을 이 규약이 대체한다. **관대하게 받지 않는다** — `T` 구분자·`Z` suffix는 양쪽에서 **거부되며 거부된다는 사실 자체가 테스트로 고정**돼 있다.
2. **서버 `now()`는 (c) 병행** — `Clock.system(Asia/Seoul)` 주입(정본) + `:core`의 `KstTime`(엔티티 기본값용, 정본) + JVM 타임존 고정(안전망). (a) 헬퍼 단독을 기각한 근거는 "**엔티티 기본값처럼 흩어진 자리를 실제로 놓쳐 왔다**"는 실측이다. 안전망을 빼도 서는지는 `TZ=UTC` 전체 실행으로 증명했다.
3. **모바일은 `kotlinx-datetime` 채택** — challenge-create에서 깨진 원인이 API 비호환이 아니라 **버전 스큐**(선언 0.6.2 / common 해석 0.7.1)였음이 규명됐다. 0.7.1로 맞추면 그대로 컴파일된다. `compose.material3`가 이미 그래프에 끌어오고 있어 **신규 서드파티 추가가 아니라 이미 있는 것을 선언하는 것**이다.
4. **파싱 실패는 필드 중요도로 분기** — `deadline` = 항목 제외 + `onError` 1회 / `createdAt`·`since`·`requestedAt` = nullable + UI `-`. 기존 `Instant.DISTANT_PAST` 센티넬은 **파싱 에러를 "이미 마감된 카드"로 위장**해 폐기했다.
5. **`friends.since`는 시각까지 유지** — 날짜로 낮추면 `formatSince`가 "어제 23:00 → 오늘 친구가 됨"을 "1일 전"으로 바꾼다. 동작 보존 기준 위반.
6. **`@JsonFormat` 명시가 정본 + 전역 설정은 안전망** — 어노테이션은 컴파일 타임 상수만 받으므로 `WIRE_DATETIME` 상수를 단일 출처로 두었다. DTO마다 문자열을 손으로 적으면 **오타가 나도 컴파일이 통과**한다.
7. **V6는 데이터를 보정하지 않는다** — `users` 1행은 **이미 KST였고 `+9h`를 쳤으면 손상**이었다(`refresh_token_issued_at`이 미래가 된다). 대신 `COMMENT ON COLUMN` 17건으로 KST 기준을 DB 메타데이터에 박았다. `LocalDateTime`이 offset을 잃어 "이 값은 KST"가 문서 약속에만 남는 리스크에 대한 직접 대응이다.

## 미해결 이슈

- [ ] **🔴 백엔드 통합 테스트 45건 미실행** — 컨테이너 런타임 부재. 실서버 65단언이 같은 층을 수동으로 덮었으나 **CI에서 반복되지 않는다.**
- [ ] **모바일↔서버 실연동 미검증** — 서버측은 65/65로 실증됐고 모바일은 단위 + `WireFormatBaselineTest` 등가성까지 확인됐으나, 앱을 띄워 맞물리는 확인은 남았다. `dev-test-login` 완료 후 손 검증에서 함께 수행한다.
- [ ] **iOS 유닛 테스트 미실행** — Android 유닛 + iOS 링크까지가 검증 게이트였다.
- [ ] **🟡 `challengeKotlinMultiplatformPure` 모듈의 `api()` 전이 실패** — `:domain:model`이 `api(kotlinx-datetime)`을 선언해도 android 타깃이 없어 간선이 유실된다. feature 3곳 `implementation` 명시 선언으로 우회. 근본 해결은 build-logic.
- [ ] **🟢 `/actuator/health` 500** — actuator 의존성 부재. `dev-test-login`의 404 핸들러로 해소 예정.
- [ ] **커밋 0건** — PM 허브 / 백엔드 / 모바일 3개 레포 working tree에 `challenge-create`와 누적.

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [change-log.md](./change-log.md)
- [mobile-report.md](./mobile-report.md) · [backend-report.md](./backend-report.md)
- [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)
