# Backend Report — challenge-result

- **작성**: 2026-08-25 backend-dev
- **커밋**: 🔴 **0건** (working tree 변경만. 커밋·브랜치·푸시 금지 지시 준수)
- **계약**: [api-contract.md](./api-contract.md) — `confirmed`

## 구현 요약

핵심 플로우의 마지막 미개통 구간인 **자정 직후 배치 판정**을 개통했다. 이 프로젝트의 **첫 스케줄러**이자
`:batch` 모듈의 **첫 `.kt` 파일**이다.

🔴 **스키마는 처음부터 다 있었다. 없던 것은 판정하는 코드였다.** `challenges.result`·`ChallengeResult`
4종·`COMPLETED`/`EXPIRED`·`user_stats`·`friend_records` 전부 V1 부터 존재했고 **쓰는 코드가 0건**이었다.
판정·집계 자체는 **스키마 변경 0건**이며, 이번 작업은 스키마가 이미 약속한 것을 이행한 쪽에 가깝다.

마이그레이션은 **V10 한 건**뿐인데 그것도 판정 때문이 아니라 **개돼지 랭킹 선결 데이터**(연패 2컬럼)다 —
pm-lead 승인으로 범위에 추가됐다. 아래 "DB 마이그레이션" 절 참조.

같은 성격의 발견이 하나 더 있다 — spec 이 오픈 이슈로 올린 *"DRAW/BOTH_LOSE 의 streak 의미"* 는
**협의할 것이 없었다.** `home-feed` 의 **`confirmed` 계약**이 2026-05-25 부터
*"`currentStreak` = win 만 연속, lose/draw/both_lose 시 0"* 을 갖고 있었고 모바일 `UserRecord` KDoc 도
같은 문장이었다. **집계(생산) 규칙이 그 값을 *읽는* 엔드포인트의 계약에 살고 있었다.**

## 엔드포인트

| Method | Path | 인증 | 변경 | 상태 |
|--------|------|------|------|------|
| GET | `/api/v1/challenges/{id}` | Bearer | `result` **필드 추가** | implemented (실측) |
| GET | `/api/v1/challenges/active` | Bearer | `status`·`result`·`myResult` 추가 + **COMPLETED 7일 노출** | implemented (실측) |
| GET | `/api/v1/record` | Bearer | **무변경.** 값만 실데이터가 됨 | implemented (실측) |

**신규 엔드포인트 0건.** 판정은 서버 내부 배치라 wire 가 없다.
🔴 두 변경 모두 `confirmed` 계약이라 change-log 등재를 마쳤다 —
[soul-oath](../soul-oath/change-log.md) · [home-feed](../home-feed/change-log.md).

## 아키텍처 결정

### 1. `@Scheduled` — Spring Batch·Quartz 기각

| 후보 | 기각 사유 |
|---|---|
| Spring Batch | chunk·재시작·JobRepository 6테이블이 따라온다. *"행 몇 개 읽고 상태 바꾸기"* 가 그 기계장치 값을 못 한다 |
| Quartz(DB 잡스토어) | 존재 이유가 다중 인스턴스 중복 방지인데 지금은 단일 인스턴스다(ADR-0007). 필요해지는 시점에 갈아끼울 지점이 한 곳뿐이다 |
| **`@Scheduled`** | **채택.** 의존 0, `zone` 으로 KST 명시 가능 |

### 2. 🔴 소급 판정은 스케줄러가 아니라 **쿼리**가 보장한다

cron 은 *"언제 볼까"* 만 정한다. 대상은 `deadline <= now` 로 뽑으므로 **서버가 며칠 죽어 있어도
밀린 분이 전부 대상에 들어온다.** 여기에 `ApplicationReadyEvent` 기동 시 1회를 더해
*"자정에 죽어 있다가 아침에 올라온"* 경우 다음 자정까지 기다리지 않는다.

> 그래서 **놓친 실행을 보상하는 로직을 추가하면 안 된다** — 이미 쿼리가 하고 있고,
> 두 번째 보상 로직은 두 번 도는 원인이 될 뿐이다. 코드 KDoc 에 박제했다.

### 3. 빈을 **두 개**로 쪼갰다 — self-invocation

`ChallengeJudgementRunner`(대상 선정 루프, 트랜잭션 없음) / `ChallengeJudgementService`(1건 판정,
`@Transactional`). 한 빈에 두면 루프의 `this.judge(id)` 가 **프록시를 타지 않아 `@Transactional` 이
무효**가 된다 — 어노테이션은 붙어 있고 컴파일도 되고 테스트도 초록인데 운영에서만 부분 커밋이 남는다.
`AopContext.currentProxy()` 류는 *"잊으면 조용히 깨지는"* 쪽이라 **빈 분리**를 택했다.

Runner 에 `@Transactional` 을 얹지 않은 것도 의도다 — 얹으면 **한 건 실패에 그날 판정 전부가 롤백**된다.

### 4. 판정 규칙은 `:domain:model` 의 순수 함수 **한 곳**에만

`ChallengeVerdict.decide()` / `.outcomeFor()`, 집계는 `UserRecord.applying()` / `FriendRecord.applying()`.
Spring 도 DB 도 모르는 순수 함수라 단위 테스트로 전부 고정된다. 재판정·수동 정정·랭킹 재계산 같은
두 번째 호출부가 생겨도 규칙이 갈리지 않는다.

- `Outcome { WIN, LOSE, DRAW, BOTH_LOSE }` 신설 — 홈 카드의 `myResult` 축이자 집계 입력.
  🔴 초안은 3값(`BOTH_LOSE` → `LOSE` 로 접기)이었는데 **result-mobile 이 기각했고 논거가 맞았다**:
  접어서 보내면 앱이 `myVerificationStatus == FAILED && opponentVerificationStatus == FAILED` 로
  **역산**해야 복원되고, **그건 판정 규칙의 두 번째 사본을 앱에 심는 것**이다 — spec T-B2 가
  *"판정 규칙은 한 곳에만"* 이라며 경계한 지점이라 서버가 그걸 강제하는 shape 을 내리는 건 자기모순이었다.
  `BOTH_LOSE` 는 **관점 중립**(양쪽에서 뜻이 같다)이라 "내 시점" 좌표계를 깨뜨리지 않는다
- 서비스는 이 함수들을 **호출만** 한다

### 5. 🔴 `EXPIRED` 는 판정이 아니다

`result` `NULL`, `completed_at` `NULL`, **전적·`friend_records` 집계 없음.** 계약서가 체결된 적이 없어
승부가 성립하지 않았다. `BOTH_LOSE` 로 집계하면 *"도전장을 받고 무시한 쪽"* 이 아니라
**도전장을 보내고 무시당한 쪽**의 패배 수가 올라간다 — 본인은 아무것도 하지 않았는데.
`status == COMPLETED ⟺ result != null` 불변식도 이 선택이 지킨다.

### 6. 🔴 알림 미발송은 **구조로 보장**했다

`ChallengeJudgementService` 생성자에 **`ApplicationEventPublisher` 가 없다.** 넣지 않는 한 발송이
불가능하다. `NotificationMessages`·`NotificationType` 파일은 한 줄도 건드리지 않았다.

## 변경된 모듈 & 파일

전부 `/Users/hwamulman/woogunProject/challenge/challenge-server/` 기준.

> 아래 목록은 `git status` 실측이다 (신규 **17** / 수정 **20**). 손으로 센 숫자가 아니다.

### 신규 (17)

**마이그레이션 (1)**
- `app/src/main/resources/db/migration/V10__user_stats_loss_streak.sql`

**`:batch` — 모듈의 첫 `.kt` (2)**
- `batch/src/main/kotlin/com/lwg/challenge/batch/challenge/ChallengeJudgementScheduler.kt`
- `batch/src/main/kotlin/com/lwg/challenge/batch/config/BatchSchedulingConfig.kt`

**`:domain:model` (2)** — `domain/model/src/main/kotlin/com/lwg/challenge/domain/`
- `challenge/ChallengeVerdict.kt` (+ `Outcome`)
- `friendrecord/FriendRecord.kt`

**`:domain:repository` (1)**
- `domain/repository/src/main/kotlin/com/lwg/challenge/domain/friendrecord/FriendRecordRepository.kt`

**`:infra` (3)** — `friend_records` 배선
- `infra/entity/src/main/kotlin/com/lwg/challenge/infra/entity/friendrecord/FriendRecordEntity.kt`
- `infra/jpa/src/main/kotlin/com/lwg/challenge/infra/jpa/friendrecord/FriendRecordJpaRepository.kt`
- `infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/friendrecord/FriendRecordRepositoryImpl.kt`

**`:service` (2)** — `service/src/main/kotlin/com/lwg/challenge/service/challenge/`
- `ChallengeJudgementService.kt` · `ChallengeJudgementRunner.kt`

**테스트 (6)**
- `domain/model/src/test/.../challenge/ChallengeVerdictTest.kt` (9)
- `domain/model/src/test/.../userrecord/UserRecordApplyingTest.kt` (20 — 연패 6 포함)
- `service/src/test/.../challenge/ChallengeJudgementServiceTest.kt` (19)
- `service/src/test/.../challenge/ChallengeJudgementRunnerTest.kt` (13)
- `service/src/test/.../challenge/ActiveChallengeServiceTest.kt` (9)
- `service/src/test/.../challenge/JudgementFakes.kt` (공용 fake)

### 수정 (20)

**본체 (9)**
- `domain/model/.../userrecord/UserRecord.kt` — `applying()` 확장 + 연패 2필드
- `domain/repository/.../challenge/ChallengeRepository.kt` — `findDueByStatus` / `findRecentlyCompletedByUser`
- `infra/jpa/.../challenge/ChallengeJpaRepository.kt` · `infra/repositoryimpl/.../challenge/ChallengeRepositoryImpl.kt`
- `infra/entity/.../userrecord/UserRecordEntity.kt` — 연패 2컬럼 매핑
- `service/.../challenge/ChallengeDetailService.kt` — `result` 매핑
- `service/.../challenge/ActiveChallengeService.kt` — COMPLETED 병합 + `myResult`
- `controller/.../dto/ChallengeDetailResponse.kt` · `controller/.../dto/ActiveChallengeResponse.kt`

**컨트롤러 (2)** — `ChallengeCommandController.kt` · `ActiveChallengeController.kt` (매핑 각 1~3줄)

**설정 (3)** — `app/src/main/resources/application.yml` · `batch/build.gradle.kts` · `gradle/libs.versions.toml`

**테스트 (6)** — `ChallengeServerApplicationTests` · `WireShapeContractTest` ·
`ChallengeDetailControllerTest` · `ActiveChallengeApiIntegrationTest` ·
`ChallengeCommandServiceTest` · `VerificationServiceTest` (뒤 둘은 포트에 메서드가 늘어난 fake 대응)

⚠️ **`ActiveChallengeResponse.kt` / `ActiveChallengeService.kt` 의 마지막 수정은 KDoc·주석만이다** —
`Outcome` 이 4값이 되면서 *"BOTH_LOSE 는 나에게 LOSE 다"* 라는 문장이 **거짓**이 됐기 때문이다.
필드·타입·`@Schema` 구조는 무변경. *"바뀐 결정은 옛 근거를 지우고 새 근거로 교체한다"* 규칙 적용 —
낡은 주석이 남아 정반대를 주장하는 것이 이 레포가 반복해 겪은 실패다.

### 설정 신규

```yaml
challenge:
  result:
    batch:
      cron: ${CHALLENGE_JUDGEMENT_CRON:0 5 0 * * *}     # 00:05 KST (zone 은 코드에서 명시)
      enabled: ${CHALLENGE_JUDGEMENT_ENABLED:true}       # 다중 인스턴스 시 한 대만 true
    completed-retention-days: ${CHALLENGE_COMPLETED_RETENTION_DAYS:7}
```

### 버전 카탈로그 2줄 추가 (설계 이탈 1건)

`challenge.spring.library` 컨벤션은 `spring-context` 까지만 준다. `ApplicationReadyEvent` 는
`spring-boot`, `@ConditionalOnProperty` 는 `spring-boot-autoconfigure` 소관이라 **starter 통째가 아니라
필요한 조각만** `:batch` 에 들였다. (`TestLoginEnabledCondition` 이 *":service 에 그 의존성이 없어서"*
손수 `Condition` 을 쓴 그 상황이며, 계약 §3.2 가 `ApplicationReadyEvent` 를 명시하므로 회피하지 않았다.)

## DB 마이그레이션 — **V10 1건**

판정·집계 자체는 **스키마 변경 0건**이었다. 필요한 컬럼·테이블이 V1 부터 전부 존재했고
`idx_challenges_deadline_status`(V1)가 배치 대상 조회를 그대로 받는다.

**V10 은 개돼지 랭킹 선결 데이터다** (pm-lead 승인으로 범위에 추가):

```sql
-- V10__user_stats_loss_streak.sql
ALTER TABLE user_stats ADD COLUMN current_loss_streak INT NOT NULL DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN max_loss_streak     INT NOT NULL DEFAULT 0;
```

🔴 **왜 랭킹 feature 가 아니라 지금인가 — 비용의 *크기* 가 아니라 *종류* 가 바뀐다.**
지금은 집계 로직을 처음 쓰는 시점이라 컬럼 추가 + 규칙 2줄이면 끝난다. 나중에 하면
**이미 쌓인 결과를 `completed_at` 순으로 되짚는 백필**이 필요하다 — *"총 몇 번 졌나"* 는 합계에서
나오지만 *"연속 몇 번 졌나"* 는 **사건의 순서**를 알아야 나온다. 스키마 변경이 데이터 복구 작업이 된다.

⚠️ `current_streak` 에 음수를 넣어 연패를 표현하는 절약안은 **기각**했다 — 홈 StatsBar 가 그 값을
**"연승"** 라벨로 그리고 `HomeUiState` 가 `> 0` 일 때 `"N🔥"` 로 표기한다. 음수가 들어가면 화면이
조용히 거짓말을 하고 `max_streak`("최대 연승")의 의미도 무너진다.
컬럼 하나를 아끼는 값보다 **"한 컬럼이 두 가지를 뜻한다"** 의 비용이 크다.

**집계 규칙 — 연승의 정확한 거울상**: `LOSE`·`BOTH_LOSE` → `+1`, `WIN`·**`DRAW`** → `0`.
무승부는 패배가 아니므로 연속 패배가 이어질 근거가 없다. 두 규칙이 같은 모양이라야 다음 사람이
한쪽만 보고 나머지를 맞게 추측한다. **결과적으로 연승과 연패는 동시에 0 보다 클 수 없다.**

`BOTH_LOSE` 가 연패를 잇는 것은 **그것이 패배이기 때문**이다 — home-feed 정본이
*"BOTH_LOSE → 양쪽 lose+1"* 로 이미 패배로 세고 있어, `losses` 와 `current_loss_streak` 이 서로 다른
사건 집합을 세면 랭킹의 두 정렬 축(총 패배 수 · 연패)이 어긋난다.

🔴 **wire 노출 없음** — `RecordData`/`GET /record` 무변경. 읽는 화면이 아직 없다.
컬럼 주석으로 `current_streak`/`max_streak` 이 **연승 전용**이라는 것도 함께 못박았다.

## OpenAPI

- SpringDoc (로컬): http://localhost:8080/swagger-ui/index.html · spec: `/v3/api-docs`
- 반영: `GET /challenges/{id}` 의 `result`, `GET /challenges/active` 의 `status`/`result`/`myResult`
  (`@field:Schema` 로 `nullable`·example 표기)

## 테스트 결과

`build/test-results` XML 직접 집계 (숫자를 리포트 산문이 아니라 결과 파일에서 읽었다):

| 모듈 | tests | passed | skipped | failed |
|---|---|---|---|---|
| `:app` | 164 | 119 | 45 | 0 |
| `:core` | 23 | 23 | 0 | 0 |
| `:domain:model` | 51 | 51 | 0 | 0 |
| `:infra:external` | 33 | 33 | 0 | 0 |
| `:service` | 166 | 166 | 0 | 0 |
| **합계** | **437** | **392** | **45** | **0** |

- **기준선**: `365 tests / 320 passed / 45 skipped` → **신규 72건 전부 통과, 회귀 0**
- 45 skip 은 Docker 부재로 늘 건너뛰는 Testcontainers 통합 테스트다 (기존과 동일)
- 신규 내역: `ChallengeVerdictTest` 9 · `UserRecordApplyingTest` **20**(연패 6 포함) ·
  `ChallengeJudgementServiceTest` 19 · `ChallengeJudgementRunnerTest` 13 · `ActiveChallengeServiceTest` 9 ·
  `WireShapeContractTest` +1 · `ChallengeDetailControllerTest` +1
- `./gradlew build` → **BUILD SUCCESSFUL**

> ⚠️ **child 세션의 보고 숫자를 그대로 쓰지 않았다.** 1차 보고가 *"420/420 passed"* 였는데
> 실제로는 `420 tests / 375 passed / 45 skipped` 였다 — **skip 을 pass 로 셌다.** XML 을 직접
> 집계해 정정했다.

## 🔴 실서버 실측 (2026-08-25) — 소급 판정을 실데이터로 증명했다

사용자 로컬 DB 에 **마감이 최대 21일 지난 챌린지가 그대로 남아 있었다.** 시드를 만들 필요 없이
소급 판정을 실데이터로 확인할 수 있는 상태였다. 사용자 서버(`:8080`)는 건드리지 않고 **`:8081` 별도 기동**.

```
ChallengeJudgementRunner : 판정 배치 완료 (now=2026-08-25T15:56:08):
                           JudgementRunResult(judged=6, expired=2, failed=0, skipped=0)
```

| 항목 | 결과 |
|---|---|
| 🔴 **소급** | 마감 `08-04`~`08-19` 6건이 **08-25 기동 시점에** 전부 판정. 자정을 21번 놓쳐도 한 번에 따라잡는다 |
| 판정 규칙 | 양측 미인증 6건 → 전부 `BOTH_LOSE` |
| **마감 전은 무변경** | `deadline=08-26` 1건 `IN_PROGRESS` 유지 + 그 `VERIFIED` 2건 그대로 |
| `FAILED` 전이 | `verifications` `PENDING` 12 → `FAILED` 12. `VERIFIED` 2건 무변경 |
| `EXPIRED` | 마감 지난 `PENDING` 2건 → `EXPIRED`, `result`/`completed_at` **`NULL` 유지** |
| `user_stats` | 4명 `total = 3/4/3/2` (합 12 = 6건 × 2). 전부 `losses`, `current_streak=0` |
| `friend_records` | **방향 8행**. 같은 상대와 2패한 쌍은 `losses=2` 누적 |
| 🔴 **알림** | `notifications` **14 → 14**. **증가 0** (수용 기준 충족) |
| 🔴 **멱등** | 재기동 2회차 `judged=0, expired=0`. `user_stats` **md5 해시 동일**, `friend_records` 8행 유지 |

wire (`:8081` + dev test-login, 테스터1 = user 14):

| 항목 | 결과 |
|---|---|
| `/challenges/active` 정렬 | `IN_PROGRESS`(30) → `COMPLETED`(29, 26, 21, 11) — `completed_at` DESC 정확 |
| `myResult` | `BOTH_LOSE` 카드에 `"myResult": "BOTH_LOSE"` (4값 확정 후 재실측 — §2차 실측) |
| 🔴 **null 키 잔존** | `IN_PROGRESS` 카드에 `"result": null, "myResult": null` — **키가 나간다**(#24) |
| `myVerificationStatus` | `COMPLETED` 카드에서 `FAILED` (예고대로) |
| `EXPIRED` 미노출 | 24·28 목록에 **없음** |
| `GET /challenges/{id}` | `COMPLETED`→`"BOTH_LOSE"` / `IN_PROGRESS`→`null`(키 존재) / `EXPIRED`→`null` |
| `GET /record` | `{"win":0,"lose":4,"draw":0,"currentStreak":0}` — **처음으로 0 이 아닌 실데이터** |

### 이 실측이 아니면 검증할 수단이 없던 것 3가지

통합 테스트 45건이 Docker 부재로 전부 skip 되므로, 아래는 **단위 테스트로 덮이지 않는다**:

1. `@Value` 프로퍼티 주입 (`completed-retention-days`) — YAML 키 경로가 실제로 잡히는가
2. JPQL 의 `status = 'COMPLETED'` **문자열 리터럴 비교** (엔티티가 `String` 이라 성립)
3. `ApplicationReadyEvent` → 컴포넌트 스캔 → `@EnableScheduling` → 배치 실행 **전 경로**

### 2차 실측 — V10 + `myResult` 4값

| 항목 | 결과 |
|---|---|
| 🔴 **V10 적용** | `Migrating schema "public" to version "10"` → `Successfully applied 1 migration` |
| 🔴 **`ddl-auto=validate` 통과** | **서버가 기동됐다.** 엔티티 2컬럼과 SQL 2컬럼이 실제로 맞는다는 **유일한 증거** — 어긋나면 기동 자체가 실패한다. child 세션이 *"V10 이 실제 DB 에 적용된 적 없다"* 며 남긴 리스크가 여기서 닫혔다 |
| 연패 누적 | `current_loss_streak = 3/4/3/2` — **각자 연속 패배 횟수와 정확히 일치**(user 14 는 `BOTH_LOSE` 4연패 → 4) |
| `max_loss_streak` | 동일 3/4/3/2 |
| **연승 0** | `current_streak`/`max_streak` 전원 0 — **연승과 연패가 동시에 살아 있지 않다** |
| `myResult` 4값 | `COMPLETED` 카드 전부 **`myResult="BOTH_LOSE"`** (접히지 않는다) |
| 🔴 **`GET /record` 무변경** | `{"win":0,"lose":4,"draw":0,"currentStreak":0}` — **연패 필드가 새지 않는다** |

⚠️ **실데이터가 `BOTH_LOSE` 일색이라 실측이 못 덮은 분기가 하나 있다** — *"승리·무승부가 연패를 0 으로
끊는다"*. `UserRecordApplyingTest` 단위 테스트로만 고정돼 있다.

### DB 원복

**전량 원복 완료** — `challenges` 상태/`result`/`completed_at`, `verifications` 상태,
`user_stats`(0행), `friend_records`(0행), `notifications`(14) 전부 실측 전과 동일함을 재조회로 확인.
사용자 서버(:8080, PID 54114)는 실측 내내 **무중단**.

원복 SQL 생성 방식 (실측 **전에** 스냅샷해 두었다):

```sql
BEGIN;
-- challenges: id 별 status/result/completed_at 을 UPDATE 로 복원 (13행)
-- verifications: (challenge_id, user_id) 별 status/verified_at 복원 (14행)
DELETE FROM user_stats;      -- 실측 전 0행
DELETE FROM friend_records;  -- 실측 전 0행
COMMIT;
```

> 스냅샷을 **코드 실행 전에** 떠 둔 것이 핵심이다. 배치가 돈 뒤에 원복 SQL 을 만들려 했다면
> 원본 `status` 를 이미 잃은 뒤다.

## 미해결 이슈

- [x] ~~`current_loss_streak` / `max_loss_streak` 컬럼 미추가~~ — **해소.** pm-lead 승인으로 V10 에 포함했다.
  `docs/backlog.md` 32행(*"판정 feature 스코프"*)과 `spec.md` 비범위가 어긋났던 건인데, **backlog 가 맞고
  spec 초판이 틀린 것**으로 정리됐다(pm-lead 가 spec 정정). 위 "DB 마이그레이션" 절 참조.
- [ ] 🔵 **연패 규칙의 "끊김" 분기는 단위 테스트로만 고정** — 실측 데이터가 `BOTH_LOSE` 일색이라
  *"승리·무승부가 연패를 0 으로 끊는다"* 를 실서버에서 관측하지 못했다. 승부가 갈리는 챌린지가
  실제로 쌓이면 자연히 확인된다.
- [ ] 🔵 **다중 인스턴스 중복 실행** — 가드가 `AtomicBoolean`(in-process)이라 단일 인스턴스 전제다.
  뚫려도 멱등 가드가 이중 집계는 막으므로 **헛일이지 데이터 손상은 아니다.** DB 락/Quartz 는
  ADR-0007 소관. 임시 방편은 `CHALLENGE_JUDGEMENT_ENABLED=false` 로 한 대만 남기기.
- [ ] 🔵 **cron 이 정말 00:05 KST 에 도는지는 미검증** — cron 파싱·`zone` 적용은 Spring 소관이라
  단위 테스트로 고정할 수 없다. 실측이 덮은 것은 **startup 경로까지**다. 실패 모드(`zone` 을 지우면
  AWS(UTC)에서 조용히 09:05 KST 에 돈다)를 KDoc 에 박제하는 것으로 갈음했다.
- [ ] 🔵 **`friend_records` 는 읽는 wire 가 0건** — 이번 feature 는 채우기만 한다. 소비는 랭킹 feature.
  따라서 **집계 정확성은 실측 8행 대조로만 확인**됐고 API 회귀 테스트가 없다.
- [ ] 🔵 **통합 테스트 45건 여전히 skip** — Docker 부재. 기존과 동일한 상태이며 이번에 늘지 않았다.
- [ ] 🔵 **`ActiveChallengeApiIntegrationTest` 의 "COMPLETED 제외" 케이스 의미 변경** —
  기존 픽스처가 `completedAt = now` 라 7일 창에 걸려 **노출되는 게 정상**이 됐다. 케이스를 지우지 않고
  픽스처를 1년 전으로 밀어 *"보관기간 지난 COMPLETED 는 제외"* 로 정정했다. 의도한 검증은 살아 있으나
  **Docker 환경에서 한 번 실행해 볼 것**.

## 참고 — repos.json 의 백엔드 정보가 낡았다

`modules` 가 `[":app", ":api", ":core", ":domain", ":infra", ":batch"]` 로 적혀 있으나
**실제는** `:app :core :batch :domain:model :domain:repository :controller :service :infra:entity
:infra:jpa :infra:repositoryimpl :infra:external` 이다. `blockers` 의 *"완전 스켈레톤 — 컨트롤러/서비스
전무"*, *"마이그레이션 도구 미결정"* 도 전부 해소된 지 오래다. 이 feature 범위 밖이라 고치지 않았다.
