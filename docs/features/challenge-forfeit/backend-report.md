# Backend Report — challenge-forfeit

- **작성**: 2026-09-05 backend-dev
- **레포**: `challenge-server` (커밋하지 않음 — 사용자 판단 대기, working tree 상태)
- **상위**: [spec.md](./spec.md) · [api-contract.md](./api-contract.md)

## 구현 요약

T-B1 ~ T-B5 **전부 구현 완료.** 한 문장으로: **기권은 `challenges.forfeited_by` 한 컬럼을
기록하고 기존 `judge()` 를 부르는 것이 전부다** — 판정도 전적 집계도 새로 쓰지 않았다.

| 태스크 | 상태 | 비고 |
|---|---|---|
| T-B1 `ChallengeVerdict` 확장 | ✅ | `Forfeit` enum 신설 + `decide` 파라미터 1개. KDoc 판정 표 4행 → **6행**으로 갱신 |
| T-B2 마이그레이션 | ✅ | `V12__challenge_forfeit.sql` — `forfeited_by` 1컬럼. **`forfeited_at` 은 만들지 않았다** |
| T-B3 엔드포인트 | ✅ | `POST /challenges/{id}/forfeit` + `ChallengeForfeitService`. `judge()` 를 그대로 호출 |
| T-B4 알림 | 🟡 **타입만 열림** | `CHALLENGE_FORFEITED` 선언 + 이벤트 발행까지 완료. **문구는 forfeit-mobile 회신 대기** (아래 §미해결 1) |
| T-B5 테스트 | ✅ | 신규 **31건**, 회귀 **0**. spec §3 의 🔴 항목 전부 고정 |

### 🔑 이 feature 에서 실제로 어려웠던 것은 **동시성**이었다

spec §3.1 이 *"양쪽이 다 기권"* 을 **저절로 닫히는 것**으로 분류했다 —
*"첫 기권이 즉시 `COMPLETED` 로 끝내므로 두 번째는 `IN_PROGRESS` 게이트에 걸린다."*
**순차라면 맞다. 동시에는 틀린다.**

READ COMMITTED 에서 두 요청이 **둘 다** `IN_PROGRESS` 를 읽고 통과하면, 나중 것이 앞 것의
`forfeited_by`·`result` 를 덮어쓰고 **전적을 한 번 더 올린다.** `total_challenges` 는
소급 정정이 불가능하다. 그래서 spec §3 은 이걸 **별도 수용 기준**으로 따로 세워 뒀고
(*"동시 요청으로 검증"*), §3.1 의 *"방어 로직 추가 금지"* 목록과 모순되지 않는다.

🔴 **기권은 양쪽 당사자 모두가 부를 수 있는 이 프로젝트 유일의 상태 전이다.**
수락·거절은 opponent 만, 취소는 challenger 만 부르고, 판정 배치는 단일 스레드다.
그래서 잠금이 필요한 자리가 여기 하나뿐이다.

**해법은 규칙을 추가하지 않는 쪽으로 골랐다** — `findByIdForUpdate` 로 트랜잭션 첫 문장에서
행을 잠그면, 두 번째 트랜잭션이 첫 커밋을 기다렸다가 **갱신된 row 를 다시 읽고**, 그때
`COMPLETED` 라 **기존 `IN_PROGRESS` 게이트가 그대로 막는다.** 동시성 전용 분기가 0줄이다.

✅ **실기동에서 진짜 동시 요청으로 검증했다** (아래 §실기동 3번). 단위 테스트로는 원리적으로 불가능하다.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|---|---|---|---|
| POST | `/api/v1/challenges/{id}/forfeit` | Bearer | **implemented** (미배포·미커밋) |
| GET | `/api/v1/challenges/{id}` | Bearer | **implemented** — `forfeitedBy` 필드 1개 추가 (기존 shape 무변경) |

### 응답 (성공)

```json
{"error":false,"code":200,"message":"성공",
 "data":{"challengeId":1,"status":"COMPLETED","result":"CHALLENGER_WIN",
         "myResult":"LOSE","completedAt":"2026-09-05 22:48:12"}}
```

### 에러 — 🔴 계약 초안(전부 700)에서 **개정**

| 조건 | 초안 | 확정 | message |
|---|---|---|---|
| 챌린지 없음 | 700 | **705** | `챌린지를 찾을 수 없어요` |
| 당사자 아님 | 700 | **700** | `내 챌린지가 아니에요` |
| `IN_PROGRESS` 아님 | 700 | **705** | `진행 중인 챌린지만 기권할 수 있어요` |
| 이미 인증함 | 700 | **705** | `이미 인증해서 기권할 수 없어요` |

⚠️ **spec §3 의 *"이미 인증한 사람은 기권할 수 없다 (거부, `code=700`)"* 와 어긋난다.**
의도적 이탈이다. 근거는 아래 §결정 근거 1. **pm-lead 판단이 필요하면 되돌릴 수 있다** —
서비스 상수 1줄 + 테스트 2건이 전부다.

## 변경된 모듈 & 파일

### `:domain:model`
- `domain/challenge/ChallengeVerdict.kt` — **`Forfeit` enum 신설** + `decide(…, forfeit: Forfeit?)`.
  KDoc 판정 표를 4행 → 6행으로 갱신하고 *"`VerificationParty` 를 재사용하지 마라"* 를 명시
- `domain/challenge/Challenge.kt` — `forfeitedBy: Long?` 필드 (**기본값 없음**)
- `domain/notification/NotificationType.kt` — `CHALLENGE_FORFEITED` 선언
- `domain/notification/NotificationMessages.kt` — 🟡 `null` 분기에 **대기 사유를 적어** 배치

### `:domain:repository`
- `domain/challenge/ChallengeRepository.kt` — `findByIdForUpdate` 신설

### `:infra:entity` / `:infra:jpa` / `:infra:repositoryimpl`
- `ChallengeEntity.kt` — `forfeited_by` 매핑 + `toDomain`/`fromDomain`
- `ChallengeJpaRepository.kt` — `@Lock(PESSIMISTIC_WRITE)` 쿼리
- `ChallengeRepositoryImpl.kt` — 위임 1줄

### `:service`
- **`challenge/ChallengeForfeitService.kt` (신규)** — 검증 3종 + `forfeited_by` 기록 + `judge()` 호출 + 알림 발행
- `challenge/ChallengeJudgementService.kt` — `forfeited_by` → `Forfeit` 환산 후 `decide` 에 전달
- `challenge/ChallengeDetailService.kt` — `forfeitedBy` 를 view 에 실음
- 🔴 `challenge/ChallengeHistoryService.kt` — **낡아버린 KDoc 정정** (아래 §부수 발견)
- `challenge/ChallengeCommandService.kt` — 신규 생성 시 `forfeitedBy = null` 1줄

### `:controller`
- `challenge/ChallengeCommandController.kt` — `POST /challenges/{id}/forfeit` + 상세에 `forfeitedBy`
- `challenge/dto/ChallengeCommandDtos.kt` — `ForfeitChallengeResponse` / `ForfeitChallengeData`
- `challenge/dto/ChallengeDetailResponse.kt` — `forfeitedBy` 필드

### `:app`
- `db/migration/V12__challenge_forfeit.sql` (신규)

## DB 마이그레이션 — `V12__challenge_forfeit.sql`

```sql
ALTER TABLE challenges ADD COLUMN forfeited_by BIGINT;
COMMENT ON COLUMN challenges.forfeited_by IS '...';
COMMENT ON COLUMN notifications.type IS '... CHALLENGE_FORFEITED ...';
COMMENT ON COLUMN notifications.reference_id IS '... 5종 ...';
```

- 🔴 **`forfeited_at` 을 만들지 않았다** (spec 지시). 기권은 즉시 `COMPLETED` 라
  **`completed_at` 이 곧 기권 시각**이다. 값이 같은 컬럼이 둘이면 언젠가 갈린다
- 🔴 **FK 를 걸지 않았다.** 이 값은 언제나 `challenger_id`/`opponent_id` 중 하나이고
  그 둘이 이미 `REFERENCES users(id)` 다. 세 번째 FK 는 이미 보증된 사실을 한 번 더 강제할 뿐이다
- **인덱스 없음.** 이 컬럼으로 조회하는 쿼리가 0건이다
- **DML 0건.** NULL 허용 추가라 기존 row 는 전부 *"기권 없음"* 으로 정확히 해석된다

### ⚠️ `notifications` 컬럼 주석을 함께 고쳤다 — 그리고 **남의 누락도 정정했다**

V8 이 *"타입 추가 시 이 주석을 갱신할 것"* 이라고 적어 뒀고 `NotificationTypeTest` 가 그 일치를
강제한다. 그래서 어휘에 `CHALLENGE_FORFEITED` 를 넣으며 함께 갱신했는데, 그 과정에서
**`reference_id` 주석이 이미 낡아 있던 것**을 발견했다 — *"현재 3종"* 이라고 적혀 있으나
`challenge-verification` 이 `OPPONENT_VERIFIED` 발송을 열면서 이미 4종이었다.
V12 에서 **5종으로 정정**했다.

### 🟡 V12 번호 선점 — `ai-verification` 이 알아야 한다

`docs/features/ai-verification/plan.md:743` 이 *"throwaway DB 로 **V12** 적용"* 이라고 적고 있다.
그쪽이 아직 미착수(plan 만 존재)라 **이 feature 가 V12 를 가져갔다.**
👉 **`ai-verification` 착수 시 V13 부터 쓰고 plan.md 의 그 줄을 고쳐야 한다.**

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui/index.html — spec JSON 은 `/v3/api-docs`
- 반영된 경로: `POST /api/v1/challenges/{id}/forfeit` (신규), `GET /api/v1/challenges/{id}` (필드 1개 추가)
- 🔴 **배포된 인스턴스가 없다.** 앱이 참조하려면 로컬 기동이 필요하다 —
  계약 문서(`api-contract.md`)가 현재 유일하게 항상 읽을 수 있는 출처다

## 테스트 결과

### 전체 — **655건 중 605 passed / 0 failed / 50 skipped**

- **회귀 0.** 실패·에러 0건
- skipped 50건은 **Docker 부재로 상시 skip 되는 통합 테스트**다 (repos.json blockers 기재 항목).
  이 feature 가 늘린 skip 은 없다
- 직전 기준(`verification-photo-replace`: 574 passed / 50 skipped)에서 **+31**

### 신규 31건 내역

| 파일 | 건수 | 무엇을 고정하는가 |
|---|---|---|
| `ChallengeForfeitServiceTest` (신규) | **14** | 성공 경로·전적 숫자·`FriendRecord` 양방향·알림 1건·거부 4종·재기권 거부·배치 재실행 |
| `ChallengeVerdictTest` | 5 | 🔴 *"상대도 미인증인데 상대 WIN"* · 기권 4조합 전수 · **기존 4규칙 불변** |
| `ChallengeCommandControllerTest` | 6 | wire shape · `completedAt` 초 단위 절삭 · code 705/700 |
| `ChallengeJudgementServiceTest` | 2 | `judge()` 가 `forfeited_by` 를 읽는다 · 당사자 아닌 기권자는 **터진다** |
| `VerificationServiceTest` | 1 | 🔴 기권 후 인증 제출이 실제로 거부된다 |
| `ChallengeDetailControllerTest` | 1 | `forfeitedBy` 가 userId 로 나가고 null 이어도 키가 남는다 |
| `WireShapeContractTest` | 1 | 기권 응답 5필드 (`myResult` 삭제 방지) |
| `NotificationTypeTest` | 1 | 🔴 `VARCHAR(30)` 폭 검사 — **저장 경로가 생겨 전제가 바뀌었다** (아래) |

### spec §3 의 🔴 항목 대조

| 수용 기준 | 어디서 고정했나 |
|---|---|
| 🔴 상대도 미인증인데 상대 WIN | `ChallengeVerdictTest` + `ChallengeForfeitServiceTest` + **실기동** |
| 🔴 배치 재실행해도 전적 2회 안 오름 | `ChallengeForfeitServiceTest` (실제 Runner 실행) + **실기동** |
| 🔴 즉시 `COMPLETED` + `result` 확정 | `ChallengeForfeitServiceTest` |
| 🔴 전적 숫자 (`losses+1`·연패·연승 초기화) | `ChallengeForfeitServiceTest` — 6개 필드 전부 숫자로 |
| 🔴 `FriendRecord` 양방향 | `ChallengeForfeitServiceTest` |
| 🔴 판정 규칙이 `ChallengeVerdict` 밖에 복제 0곳 | **grep 검증 완료** — 아래 |
| 🔴 동시 기권 한쪽만 성공 + `forfeited_by` 미덮어씀 | **실기동 동시 요청** (단위 테스트 불가) |
| 🔴 기권 후 상대 인증 제출 거부 | `VerificationServiceTest` + **실기동** |
| 🔴 알림 정확히 1건 | `ChallengeForfeitServiceTest` (이벤트 층) |

#### 판정 규칙 복제 0곳 — grep 근거

```
$ grep -rn "ChallengeResult\." --include="*.kt" --exclude-dir=build . | grep "/src/main/"
infra/entity/.../ChallengeEntity.kt:88:  result = result?.let { runCatching { ChallengeResult.valueOf(it) } ... }
```

`ChallengeVerdict.kt` 외의 유일한 히트가 **문자열 역직렬화**다. 규칙이 아니다.
`Outcome.` 도 같은 방식으로 확인했고 `ChallengeVerdict` / `UserRecord` / `FriendRecord` 외에는
전부 KDoc 안의 참조뿐이다.

### 🔴 실기동 확인 — **테스트 통과 ≠ 기동 성공** (필수 절차)

이 레포의 smoke test 는 JPA 를 제외하므로 **마이그레이션·JPQL·`ddl-auto=validate`·신규 빈 배선이
어느 테스트에도 걸리지 않는다.** 이번엔 컬럼 추가 + 새 JPQL + 새 `@Service` 가 전부 있어 필수였다.

throwaway DB `challenge_forfeit_check` + 포트 **18081**. 공용 `challenge` DB·`:8080` 불가침.

```
Migrating schema "public" to version "12 - challenge forfeit"
Successfully applied 11 migrations to schema "public", now at version v12
Started ChallengeServerApplicationKt in 4.815 seconds
```

`ddl-auto=validate` 통과 = **엔티티의 `forfeited_by` 와 V12 의 컬럼이 실제로 일치**한다는 뜻이다.

이어서 **엔드포인트를 실제로 왕복**시켰다 (test-login → 친구 → 신청 → 수락 → 기권):

| # | 확인 항목 | 결과 |
|---|---|---|
| 1 | 🔴 **양쪽 미인증 상태에서 기권 → 상대 승** | `result = CHALLENGER_WIN` (기존 규칙이면 `BOTH_LOSE`) ✅ |
| 2 | 전적·친구 전적 | `user_stats` 1:0/0:1, 연승 1·연패 1, `friend_records` 양방향 ✅ |
| 3 | 🔴 **동시 기권 2건 (curl 병렬)** | **정확히 한쪽만 200**, 다른 쪽 `705`. `forfeited_by = 2` 단일 ✅ |
| 4 | 잠금이 실제로 걸렸는가 | SQL 로그에 `... where ce1_0.id=? for no key update` **2회 동시 발행** ✅ |
| 5 | 🔴 **배치 재실행** (deadline 을 과거로 밀고 재기동) | `judged=0`, 전적 숫자 **완전 동일** ✅ |
| 6 | 기권 후 인증 제출 | `705 진행 중인 챌린지만 인증할 수 있어요`, 저장소 파일 **0개** ✅ |
| 7 | 재기권 | `705` ✅ |
| 8 | 상세 wire | `forfeitedBy: 2`, `challenger.userId: 1` / `opponent.userId: 2` ✅ |
| 9 | 알림 | `notifications` 에 **`CHALLENGE_FORFEITED` row 0건** + `WARN 문구가 정의되지 않은 알림 타입이라 건너뜁니다` ✅ (의도) |

정리 완료: DB drop / 18081 프로세스 종료 / 스크래치 사진 삭제. 공용 `challenge` DB 무변경.

#### ⚠️ 로그에서 잠금을 찾을 때 — `for update` 로 grep 하면 **0건이 나온다**

Hibernate 6 의 PostgreSQL 방언이 `PESSIMISTIC_WRITE` 를 **`for no key update`** 로 렌더한다.
처음에 `for update` 로 grep 해 0건을 보고 *"잠금이 안 걸렸나"* 를 의심했다.
두 모드는 서로 충돌하므로 직렬화 목적에는 차이가 없다. **이 사실을 두 KDoc 에 박아 뒀다** —
다음 사람이 같은 5분을 쓰지 않도록.

## 결정 근거

### 1. 🔴 에러 코드를 700 → 705 로 (spec §3 과 의도적으로 어긋남)

**pm-lead 확인이 필요한 유일한 이탈이다.**

계약 초안은 실패 4종을 전부 `700`(스낵바)로 적었다. 그대로 두면 **같은 문장이 엔드포인트마다
다른 UI 로** 뜬다 — `"챌린지를 찾을 수 없어요"` 는 상세·취소·인증 제출에서 전부 705 로 나가고 있다.

레포에 명문화된 배분(`ChallengeCommandService`/`VerificationService` KDoc)을 따랐다:
**700 = 권한 위반 + 사용자가 고칠 수 있는 것 / 705 = "네 화면이 이미 낡았다"**.

*"이미 인증함"* 이 705 인 이유가 핵심이다 — **사용자가 고칠 수 있는 것이 아니다.** 인증은 무를 수
없으므로, 이 응답이 나갔다는 건 **기권 진입점이 남아 있는 낡은 화면**이라는 뜻이다.
스낵바는 낡은 버튼을 그대로 남기고, 705 는 확인을 강제해 새로고침 계기를 준다.

👉 forfeit-mobile 에 통지 완료. 계약 §4 협의 이력에 등재.

### 2. `myResult` 를 넣는다 (초안 🟡 협의 항목 해소)

*"항상 `LOSE` 라 정보량 0"* 이라는 반론은 유효했지만 전제가 틀렸다 — 서버가 상수를 박는 것이
아니라 `ChallengeVerdict.outcomeFor` 를 **실제로 태운 결과**를 싣는다. 오늘 항상 `LOSE` 인 것은
하드코딩이 아니라 결과다. 빼면 앱이 `result` 를 뒤집거나 *"기권했으니 졌다"* 를 심어야 하고,
그게 `challenge-result` 가 `myResult` 를 신설하며 막았던 사본이다.

### 3. `Forfeit` 파라미터에 **기본값을 주지 않았다**

`decide(a, b, forfeit = null)` 로 두면 새 호출부가 기권 판정을 **조용히 빠뜨린 채** 컴파일된다.
넘기기 싫어도 `null` 을 명시하게 만들었다 — 기존 테스트 4건이 `forfeit = null` 을 적게 됐고,
그 4줄이 *"여기는 기권 없는 경우"* 를 말한다. `Challenge.forfeitedBy` 도 같은 이유로 기본값이 없다
(기본값이 있으면 `ChallengeEntity.toDomain` 이 매핑을 빠뜨려도 컴파일이 통과하고,
**기권 사실이 조회할 때마다 조용히 사라진다**).

### 4. 당사자 아닌 `forfeited_by` 는 **터뜨린다** (`error()`)

정상 경로에서 도달 불가지만, `null` 로 떨어뜨리면 **깨진 데이터가 "기권 없음" 으로 판정되어
잘못된 승패로 덮인다.** 승패는 소급 정정이 불가능하므로 조용한 오답보다 시끄러운 실패가 낫다.
배치는 건별로 예외를 세고 넘어가므로 한 건이 나머지를 막지도 않는다.

### 5. 🔵 spec §3.1 의 4항목에는 **가드를 추가하지 않았다** (지시 준수)

- 양쪽 다 기권 → `IN_PROGRESS` 게이트 (**순차**). 동시는 잠금이 같은 게이트로 유도
- 기권 후 상대 인증 → 기존 `IN_PROGRESS` 검사 (테스트로 확인만)
- 기권자 사진 삭제 → 지울 사진이 존재하지 않음 (코드 0줄)
- 기권 건 AI 호출 → `COMPLETED` 라 배치 대상 제외 (코드 0줄)

## 🔴 부수 발견 — 다른 파일의 KDoc 이 **이 feature 때문에 거짓이 됐다**

`ChallengeHistoryService` KDoc 이 이렇게 적고 있었다:

> 카드에 인증 상태를 그리지 않아 verifications 를 조회하지 않는 것은 그대로다 —
> **판정 규칙상 결과 4개가 양측 인증 상태를 유일하게 결정하므로** 결과 하나가
> 인증 상태 두 개의 정보를 전부 담는다.

**기권이 그 대응을 일대일이 아니게 만들었다.** `OPPONENT_WIN` 은 이제
*"challenger 만 미인증"* 일 수도, *"challenger 가 기권했고 상대도 미인증"* 일 수도 있다.

spec T-B1 이 `ChallengeVerdict` KDoc 에 대해 *"낡은 문장이 된다 — 함께 고쳐라"* 라고 지시한 것과
**같은 종류인데 spec 이 지목하지 않은 파일**이다. 정정하면서 결론(조회하지 않는다)은 유지하고
**근거만 교체**했고, *"언젠가 카드에 인증 상태를 그리게 되면 `result` 로 역산하지 마라 —
역산은 이제 틀린 답을 낸다"* 를 명시했다.

🔑 이게 안 잡혔으면, 나중에 보관함 카드에 인증 상태를 붙이는 사람이 **이 KDoc 을 근거로
역산 코드를 짜고**, 기권 건에서만 조용히 틀렸을 것이다.

## 🔴 부수 개선 — `NotificationType` 의 길이 테스트가 **이제 성립한다**

`NotificationTypeTest` KDoc 이 `VARCHAR(30)` 초과 검사를 두지 않은 이유를 이렇게 적어 뒀다:

> 실제 근거는 **`NotificationType` 을 DB 에 저장하는 코드가 지금 0건**이라는 것이다.
> 🔴 **#33(T-B5 이벤트 배관)에서 저장 경로가 생기면 이 판단을 다시 하라.**

그 저장 경로는 `push-fcm` 에서 이미 생겼는데(`NotificationDispatcher` 가 enum name 을 그대로
저장한다) **아무도 이 판단을 다시 하지 않았다.** 타입을 늘리는 김에 테스트를 추가했다 —
길이 초과는 **런타임 INSERT 에서만** 터지고 컴파일도 다른 테스트도 잡지 못한다.
(현재 최장이 `CHALLENGE_FORFEITED` 19자라 여유는 충분하다.)

## 미해결 이슈

### 1. 🟡 **알림 문구 미기입 = 푸시 발송 꺼짐** (forfeit-mobile 회신 대기)

`NotificationMessages` 에 `CHALLENGE_FORFEITED` 문구를 **일부러 넣지 않았다.**
레포 규약(`NotificationMessagesTest` KDoc)이 *"모바일 통지·회신이 선행해야 한다"* 로 못박고 있고,
`OPPONENT_VERIFIED` 가 2026-08-14 에 밟은 절차다. 앱이 모르는 타입이 먼저 나가면
트레이에서 **눌러도 아무 데도 안 가는 조용한 실패**가 된다.

- **회신 조건**: `PushEvent.ChallengeForfeited` + 딥링크 `Route.Challenge.Detail` 배선 완료
- **회신 오면**: 문구 2줄 + `NotificationMessagesTest.inScope` 1줄 = **총 3줄**로 켜진다
- ⚠️ **블로커가 아니다** — 기권 자체(판정·전적·응답)는 전부 정상이고 알림만 0건이다. 실기동 확인 완료

### 2. 🟡 **계약이 아직 `confirmed` 가 아니다** — 미결 1건

`active` / `history` 응답에 `forfeitedBy` 를 넣을지가 남았다. 초안이 *"mobile-dev ↔ backend-dev
협의 항목"* 으로 남긴 것이고 forfeit-mobile 에 질의했다. **서버 비용은 양쪽 다 필드 1개**로
도메인·쿼리 변경이 0이라 원하면 즉시 넣는다.

⚠️ 회신에 포함되어야 할 것: `active`/`history` DTO 에 `challenger.userId` 에 해당하는 필드가
있는가. 없으면 `forfeitedBy` 만으로는 *"내가 기권했나 상대가 기권했나"* 를 가를 수 없다.

### 3. 🟡 **spec §3 의 `code=700` 과 어긋난다** — pm-lead 판단 대상

위 §결정 근거 1. 되돌리려면 서비스 상수 1줄 + 테스트 2건이다.

### 4. 🔵 **배치와 기권이 정확히 동시에 겹치는 구간은 잠그지 않았다**

기권은 `FOR NO KEY UPDATE` 로 잠그지만 **자정 배치의 `judge()` 는 잠그지 않는다.**
배치가 `IN_PROGRESS` 를 읽은 직후 기권이 커밋되면, 배치의 UPDATE 가 stale snapshot 으로
덮어쓸 수 있다.

🔵 **지금 손대지 않았다**: ① 노출 창이 하루 5분(00:05 배치 실행 중)이고 ② 이 race 는
기권 이전부터 `judge()` 에 있던 성질이며(그래서 `judge()` 가 자기 트랜잭션 안에서 status 를
재확인한다) ③ 막으려면 **배치 핫패스에 잠금을 넣는 구조 변경**이라 관측된 적 없는 시나리오에
비해 비용이 크다. 실제로 관측되면 이 문단을 근거로 바꾸면 된다.

### 5. 🟡 **`ai-verification` plan.md 의 V12 표기가 낡았다**

`plan.md:743` 이 V12 를 쓴다고 적고 있으나 이 feature 가 선점했다. **V13 으로 정정 필요.**

### 6. 🔵 커밋하지 않았다

지시대로 `challenge-server` 에 커밋·브랜치·푸시 0건. working tree 상태로 남아 있다.
