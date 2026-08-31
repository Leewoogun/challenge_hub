# Backend Report — mypage

- **작성**: 2026-08-26 backend-dev (mypage-backend) → **2026-08-28 개정분 추가 (archive-month-backend)**
- **레포**: `challenge-server` (main, **커밋 0건** — 워킹트리 상태로 인계)
- **관련**: [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [change-log.md](./change-log.md) · [design.md](./design.md)

---

# 🔴 2026-08-28 (2차) 개정 — 과거 하한 폐기 (T-B1 v4)

**아래 v2 절은 월 단위 조회 개정의 기록이다.** 이 절이 그 위에 얹힌 2차 변경이며
`GET /challenges/history` 에 대해서는 **이쪽이 현행**이다.

## 결론 — 🔴 **서버 코드 변경 0**

사용자 실기 확인 후 **과거 하한이 폐기됐다**(기록이 없어도 뒤로 갈 수 있다). 그런데 이
엔드포인트는 **애초에 하한을 강제한 적이 없다** — 거부하는 것은 **미래 달 하나뿐**이고 과거는
어느 달이든 빈 목록으로 정상 응답해 왔다. 하한은 서버가 준 `firstArchivedMonth` 를 **앱이
경계로 해석**해서 생긴 규칙이라, 그 해석을 앱에서 걷어내면 개정이 끝난다.

**서버가 한 일**: 계약·KDoc 의 용도 서술 정정 + 회귀 방지 단언 1건.

## 계기 — 🔴 정확한 동작이 고장으로 보였다

실기 DB 의 종료 챌린지가 전부 이번 달이라 **하한(최초 기록월) = 상한(이번 달)** 이 되어 양쪽
화살표가 동시에 비활성됐다. 카드는 보이는데 아무것도 안 움직여 사용자가 **"고장"으로 읽었다.**
v3 의 하한은 *"확정적으로 빈 달의 사막으로 걸어 들어가지 않게 한다"* 를 정확히 이행한 것이고
기록이 이번 달뿐이면 갈 곳이 없는 게 참인데, **참인 상태를 화면이 고장처럼 말했다.**

## ⚠️ `가입월` 안을 폐기한 근거 — 실측

pm-lead 초기 선호가 가입월이었고 **논리는 참이었다**(`challengeDate >= created_at` 이 구조적으로
성립 → 상한과 같은 데이터 사실). 🔴 **그런데 사고를 못 고친다.** 공용 DB 읽기 전용 조회:

| 계정 | 가입월 | COMPLETED 기록 | 가입월 안 | 무제한 안 |
|---|---|---|---|---|
| 이우건 | 2026-05 | 2026-08 전부 | ✅ | ✅ |
| 테스터1·2·3 | **2026-08** | 2026-08 전부 | 🔴 **양쪽 비활성 유지** | ✅ |

가입 첫 달 사용자는 정의상 `가입월 = 이번 달` 이라 하한 = 상한이 된다. **가입월 안은 계정이
오래됐을수록 잘 듣고 신규일수록 안 듣는데**, spec 이 이 문제를 *"신규 서비스에서 가장 흔한 초기
상태"* 로 규정했다 — **문제가 가장 자주 나는 집합에서 해법이 가장 약하다.**
backend·mobile·design 이 독립적으로 같은 실측에 도달했고 pm-lead 가 선호를 철회했다.

🔴 **여기서 배운 것**: *"대칭성은 **이 경계가 참인가**를 증명하지 **경계를 두는 것이 바람직한가**를
증명하지 않는다."*

⚠️ **가입월 구현을 한 번 만들었다가 걷어냈다.** pm-lead 판정이 무제한으로 바뀐 것과 내 착수가
교차했다. `joinedMonth` 필드·쿼리·테스트를 전부 되돌렸고, 🔴 **`git checkout` 을 쓰지 않았다** —
같은 워킹트리에 미커밋 v2/v3 작업이 함께 있어 통째로 날아갔을 것이다. 수작업으로 되돌렸다.

## 🔴 `firstArchivedMonth` 존치 — "안 읽는 필드" 원칙의 대상이 아니다

pm-lead 가 그 정식화 적용을 지시했으나 **여전히 읽힌다.** 역할 셋 중 하나만 죽었다:

| 역할 | v4 |
|---|---|
| ① `<` 경계(하한) | 🔴 소멸 |
| ② 빈 달 vs 기록 전무 판별 (CTA 유무) | ✅ 존치 — 대체 출처 없음 |
| ③ 빈 달 고지 (design §2.5.1a-⑤ *"첫 기록은 YYYY년 M월이에요"*) | ✅ **신규 용도** |

③ 때문에 🔴 **1차 하한 논거는 폐기가 아니라 수단 변경**이다 — *"'이게 네 기록 전부다'라고
주장하는 화면"* 의 요구는 **차단이 아니라 주장할 수단**이었고 design 이 **차단 → 고지**로 옮겼다.

**되살림 방지**: 계약·KDoc 에 *"이 값으로 `<` 를 막지 마라"* 를 박고, 컨트롤러 테스트에
**하한 필드가 wire 에 되살아나면 실패**하는 단언을 추가했다.

## 변경된 파일

| 파일 | 변경 |
|---|---|
| `service/.../ChallengeHistoryService.kt` | KDoc 만 — 하한 서술 폐기 + *"서버 코드 변경 0"* 사유. **로직 무변경** |
| `controller/.../dto/ChallengeHistoryResponse.kt` | `firstArchivedMonth` KDoc 용도 축소 + 금지 명시. **필드 무변경** |
| `controller/.../ChallengeHistoryController.kt` | `@Operation` 설명만 |
| `app/src/test/.../ChallengeHistoryControllerTest.kt` | **회귀 방지 단언 1건 추가** (하한 필드 부재) |

**신규 파일 0 · 마이그레이션 0 · 응답 shape 변경 0.**

## 테스트 결과

| 시점 | tests | passed | skipped | failures |
|---|---|---|---|---|
| 기준선 (v3) | 534 | 485 | 49 | 0 |
| **v4** | **535** | **486** | **49** | **0** |

**회귀 0. 신규 1건** — 하한 경계 필드가 wire 에 되살아나면 실패하는 단언.

⚠️ **throwaway DB 실구동을 하지 않았다.** JPQL·쿼리·엔티티가 **한 줄도 바뀌지 않아** 실구동이
덮을 새 축이 없다. v3 검증(21건)이 그대로 유효하다 — 그중 *"하한 아래(`2026-02`·`2025-01`) →
에러 아님, 빈 달 정상 응답"* 항목이 **이번 개정의 핵심 동작을 이미 실측해 둔 것**이다.
가입월 안을 시험하던 중의 실구동에서도 *"가입 8월 계정 → 양쪽 비활성"* 을 재현 확인했고,
그 throwaway DB 는 정리했다(공용 `challenge` DB·`:8080` 불가침 유지).

## 미해결 (v4)

- ⚠️ **이론상 무한 과거** — 실사용 유인이 없고 각 화면이 빈 달로 일관되므로 수용(spec 명시).
- 🔴 **말일 챌린지 JPQL 축 자동화 공백** — v3 에서 등재한 항목 그대로. pm-lead 가 백로그의
  컨테이너 런타임 항목에 "설치 시 1순위" 로 승격했다.

---

# 2026-08-28 개정 — 보관함 월 단위 조회 (T-B1 v2·v3) — ⚠️ 하한 서술은 위 v4 가 정정

**아래 "1차" 절들은 2026-08-26 시점의 기록이다.** 이 절이 그 위에 얹힌 변경분이며,
`GET /challenges/history` 에 대해서는 **이쪽이 현행**이다. 탈퇴(T-B2)·로그아웃(T-B3)·
`photoDeleted` 는 이번에 손대지 않았다.

## 무엇이 바뀌었나

`GET /api/v1/challenges/history` 가 **전체 반환 → 한 달치 조회**가 됐다.
사용자 확정(spec §후속 개정): 월 1칸 이동 · 빈 달 통과 · 첫 진입 이번 달 · 미래 달 금지.
계약 shape 변경 상세는 [change-log.md](./change-log.md) 2026-08-28 항목.

```
GET /challenges/history?month=2026-08     ← optional. 생략 시 서버 KST 이번 달
data: { month, firstArchivedMonth, histories: [...카드 7필드 그대로...] }
```

## 핵심 설계 결정 4건

### 1. 🔴 두 경계가 **모두 서버 값**이다 — 앱은 기기 시계를 읽지 않는다

| | 앱이 어디서 얻나 |
|---|---|
| **상한** (이번 달) | 파라미터 없이 부른 **첫 응답의 `month` 에코** |
| **하한** | `firstArchivedMonth` |

앱이 상한을 기기 시계로 계산하면 서버가 준 하한과 **다른 시계에서 나온 두 경계**가 된다.
기기 타임존이 KST 가 아니면 월말·월초에 한 달 어긋나고, 증상은 **`>` 가 잠긴 채 이번 달 기록이
안 보이는** 형태다. ADR-0010 이 프로젝트를 KST 로 고정했지만 **사용자 기기 시계는 그 규약 밖**이다.
이 레포는 이미 `DeadlineType`/`KstDeadlineCalculator` 에서 *"기기 시계 조작·타임존 불일치를
차단하고 마감 기준을 서버로 일원화"* 를 규약으로 박아 뒀고, 같은 판단이다.

🔴 **`month` 파라미터를 optional 로 둔 것이 이 결정의 실행 수단이다** — 앱의 첫 요청에 월이
없으므로 첫 달도 서버 시계에서 나온다. `ChallengeHistoryService` 가 `Clock` 을 주입받게 됐다
(레포 전역 규약 — `KstTime` KDoc).

`month` 에코는 두 번째 일도 한다: **응답 경합 방어.** 빈 달을 건너뛰지 않는 확정 때문에 화살표
연타가 정상 사용이고 요청 겹침도 정상이라, 늦게 도착한 옛 응답이 현재 월 표시 아래 다른 달
카드를 그릴 수 있다. 1차(1회 조회)에는 없던 표면이다.

### 2. 🔴 하한은 **절대값 `firstArchivedMonth`.** 불리언 2개는 협의로 뒤집혔다

**값 자체**는 최초 `COMPLETED` 기록의 월이다. 후보 ① 무한 ② 가입월(`users.created_at`)
③ 최초 기록월 중 ③:

- 하한의 목적은 *"확정적으로 빈 달의 사막으로 걸어 들어가지 않게 한다"* 이다. ③ 아래는
  **0건이 보장**된다. ②는 가입~첫 기록 사이의 빈 달을 열어 둬 목적을 절반만 이룬다.
- ①은 화살표가 영원히 살아 있어 *"더 뒤에 있나"* 를 확인할 방법이 없다. **보관함은
  *"이게 네 기록 전부다"* 라고 주장하는 화면**인데(design §2.5.4.2) 하한이 없으면 화면이 그
  주장을 할 수 없다.
- 🔴 **기록 0건이면 `null`** — 그게 곧 *"보관함이 통째로 비었다"* 신호이고, 앱이 이걸로
  **빈 달 화면**과 **기록 전무 화면**을 가른다(후자만 *"챌린지 만들기"* CTA. 전자에 CTA 를
  띄우면 기록을 찾는 중인 사용자를 보관함 밖으로 내보낸다).
- **하한은 내려가지 않는다.** `challengeDate` 는 생성 시점의 오늘/내일이고 `COMPLETED` 는 마감
  후 상태라 새 기록은 항상 기존 최소값보다 뒤다 — 죽은 화살표가 되살아나지 않는다.

🔴 **형태는 내 초안이 틀렸다.** v2 는 `hasPrevious`/`hasNext` 불리언 2개였는데,
archive-month-design(§2.1.2)·archive-month-mobile 이 **독립적으로 같은 반례**로 기각했다:
사용자 확정(*"빈 달도 건너뛰지 않는다"*) + design §2.5.4.3-①(*"월 전환 중에도 화살표는 계속
눌린다"*) 때문에 **연타가 정상 사용**인데, 불리언은 **그 달의 응답이 와야** 그 달의 경계를
알려준다 — 하한 5월에서 6월→탭→5월(in flight)→탭→**4월**이 되고, 그제서야 `hasPrevious=false`
가 도착한다. **경계를 넘은 뒤에 경계를 통보받는다.** `>` 쪽은 한술 더 떠 미래 달 요청 →
code 700 이라 **정상 조작이 오류 화면**이 된다.

⚠️ **내 오류의 성격을 적어 둔다** — *"불리언이 신호가 하나라 더 적다"* 며 `result`+`myResult`
유추를 걸었는데, **여기서 불리언은 절대값의 손실 있는 투영**이지 경쟁하는 두 표현이 아니다.
절대값 하나만 주므로 경쟁하는 신호도 없다(design 은 별도 `earliestMonth` 필드 추가를
명시적으로 금지했다 — `firstArchivedMonth` 가 곧 그 값이다).

`MIN(challenge_date)` 쿼리 1개가 늘어 **쿼리가 2 → 3**이 됐다(빈 달은 users 조회를 건너뛰어 2).
🔴 **`EXISTS(< monthStart)` 로 안 짠 것이 결과적으로 맞았다** — 같은 인덱스 스캔으로 가장
오래된 달 자체를 얻어 두었기 때문에, 계약이 절대값으로 뒤집혔을 때 **쿼리를 다시 설계하지
않고 불리언으로 접던 한 줄만 지우면 됐다.**


### 3. 🔴 미래 달·형식 오류 = **code 700 (HTTP 200)**. clamp 하지 않는다

조용히 이번 달로 clamp 하면 응답의 `month` 에코가 요청과 달라져 **앱 화면의 월 표시와 카드
내용이 어긋난다.** 정상 경로에서는 발생하지 않는다 — 앱은 첫 응답의 `month` 에코를 상한으로
삼아 `>` 를 죽인다. **안전망이다.**

🔴 **하한 아래는 에러가 아니다** — 빈 달로 정상 응답하고 `firstArchivedMonth` 는 평소와 같은
값이 실린다(사용자 전역 값이라 요청 월과 무관하다). 비대칭인 이유: **미래는 데이터가 존재할 수
없는 구간(좌표계 밖)**, **과거는 존재할 수 있었지만 없는 구간(정상적인 빈 달)** 이다.

### 4. ⚠️ `month` 를 `YearMonth` 가 아니라 **`String` 으로 받는다** — 이게 없으면 HTTP 500 이다

`@RequestParam month: YearMonth?` + `@DateTimeFormat` 으로도 바인딩은 되지만, 형식이 틀리면
Spring 이 `MethodArgumentTypeMismatchException` 을 던진다. **`GlobalExceptionHandler` 에 그
핸들러가 없어서** `handleUncaught` 로 떨어지고 **HTTP 500 + code=500** 이 나간다 —
클라이언트가 잘못 보낸 쿼리 파라미터 하나가 서버 장애로 보고된다 (ADR-0002: 5xx 는 인프라 장애
전용). 전역 핸들러를 새로 추가하면 **다른 모든 엔드포인트의 타입 불일치 응답까지 바뀌므로**
이 개정이 열 범위가 아니다. → 계약 §5 백로그 등재.

## 변경된 파일 (개정분)

**수정 8** — 신규 파일 0, **마이그레이션 0**

| 파일 | 변경 |
|---|---|
| `infra/jpa/.../ChallengeJpaRepository.kt` | `findCompletedHistoryByUser` → `findCompletedHistoryByUserInMonth`(반개구간) + `findEarliestCompletedChallengeDate`(`MIN`) 신규 |
| `domain/repository/.../ChallengeRepository.kt` | 위 둘의 인터페이스 + KDoc |
| `infra/repositoryimpl/.../ChallengeRepositoryImpl.kt` | 위임 2개 |
| `service/.../ChallengeHistoryService.kt` | `Clock` 주입, 월 범위 + 하한 산출, `ChallengeHistoryPage` 신규. **카드 산출 로직은 무변경** |
| `controller/.../ChallengeHistoryController.kt` | `?month=` 수용 + `parseMonth` |
| `controller/.../dto/ChallengeHistoryResponse.kt` | `ChallengeHistoryListData` → `ChallengeHistoryMonthData`(3키: `month`·`firstArchivedMonth`·`histories`). **`ChallengeHistoryDto` 무변경** |
| `controller/common/WireDateTimeFormat.kt` | `WIRE_MONTH = "yyyy-MM"` 신규 |
| 테스트 7 | 아래 참조 |

🔴 **DB 마이그레이션이 없다.** 스키마 변경 0 — 기존 `challenge_date` 컬럼에 범위 조건이 붙었을
뿐이고, 인덱스도 기존 `idx_challenges_challenger_status`/`_opponent_status` 를 그대로 탄다.

## 테스트 결과 (개정분)

| 시점 | tests | passed | skipped | failures |
|---|---|---|---|---|
| 기준선 (1차 최종) | 513 | 464 | 49 | 0 |
| v2 (불리언 2개) | 533 | 484 | 49 | 0 |
| **v3 최종 (절대값)** | **534** | **485** | **49** | **0** |

**회귀 0. 신규 21건** — `ChallengeHistoryServiceTest` +14(월 범위 4 · 기본값 2 · 하한 5 ·
미래 달 3), `ChallengeHistoryControllerTest` +6(`month` 전달 2 · 형식 오류 2 · 빈 달 1 ·
**`firstArchivedMonth` null 키 잔존 1**), `WireShapeContractTest` +1(빈 달 3키) — v3 에서
**null 직렬화 단언 2건이 늘었다.**

수정된 fake 5곳(`ActiveChallengeServiceTest`·`ChallengeCommandServiceTest`·`WithdrawalServiceTest`·
`VerificationServiceTest`·`JudgementFakes`)은 인터페이스 변경에 따른 시그니처 교체뿐이다.

skip 49 는 **기존 블로커**(Docker 부재) — 이번 작업이 늘린 것이 아니다.

## 🔴 실구동 검증 — **단위 테스트가 새 JPQL 을 한 줄도 실행하지 않는다**

smoke test 가 JPA 를 auto-configuration 에서 제외하고 repository 를 전부 mock 으로 세운다.
즉 통과한 534건 중 **어느 것도 반개구간 범위 조건이나 `MIN` 집계를 실제 DB 에 대고 실행하지
않는다.** fake 가 같은 규칙을 다시 구현할 뿐이라, 구현과 fake 가 **함께 틀리면** 전부 통과한다.

그래서 throwaway DB + 포트 **8089** 로 확인했다 (v2·v3 각 1회, 총 2회).
**`:8080` 과 공용 `challenge` DB 는 건드리지 않았고** 끝난 뒤 전부 정리했다. 아래는 v3 최종분.

| # | 검증 | 결과 |
|---|---|---|
| 0 | Flyway V1→V11 + `ddl-auto=validate` + 새 JPQL 파싱 (컨텍스트 기동) | ✅ `now at version v11`, 기동 성공 |
| 1 | 파라미터 없이 호출 → `month=2026-08`(서버 KST 이번 달), 8월 것만 | ✅ |
| 2 | 같은 날 2건 `id DESC` (107 → 106) | ✅ |
| 3 | `myResult` 뒤집기 — 내가 opponent 인 `CHALLENGER_WIN` → `LOSE` | ✅ |
| 4 | `BOTH_LOSE` 안 접힘 | ✅ |
| 5 | 🔴 **월 경계** — `?month=2026-06` 이 6/1·6/30 포함, **5/31·7/1 제외** | ✅ `[103, 102]` |
| 6 | 🔴 **2월 경계** — 2/28 포함, 3/1 제외 (말일 계산 없이) | ✅ user3 `[120]` |
| 7 | 🔴 **`firstArchivedMonth` 가 어느 달에서 봐도 같다** — 8월·6월·4월·3월·2025-01 전부 `"2026-03"` | ✅ |
| 8 | `?month=2026-04`(빈 달) → `[]` + 하한 그대로 | ✅ |
| 9 | 🔴 **하한이 `COMPLETED` 만 센다** — 1월 `EXPIRED`·2월 `IN_PROGRESS` 가 하한을 못 민다 | ✅ `2026-03` 유지 |
| 10 | 🔴 **남의 챌린지가 내 하한을 못 민다** (제3자 2/28 건이 있는데 내 하한은 3월) | ✅ |
| 11 | 🔴 **하한 아래**(`2026-02`·`2025-01`) → 에러 아님, `[]` + 하한 그대로 | ✅ |
| 12 | 🔴 **기록 0건 사용자** → `firstArchivedMonth: null` | ✅ |
| 13 | 🔴 **null 이어도 키가 원문에 남는다** (`@JsonInclude(NON_NULL)` 부재 실증) | ✅ `"firstArchivedMonth":null` |
| 14 | 미래 달(`2026-09`) → **HTTP 200 + code 700** | ✅ |
| 15 | 형식 오류(`2026-8`) → **HTTP 200 + code 700** | ✅ |
| 16 | `?month=`(빈 문자열) → 이번 달 | ✅ |
| 17 | 🔴 `month`·`firstArchivedMonth` 가 **문자열** (`[2026,6]` 배열 아님) | ✅ 원문 확인 |
| 18 | 금지 필드 부재 — `result`·인증상태 2필드·`isWithdrawn`·**`hasPrevious`/`hasNext`** | ✅ 전부 0건 |
| 19 | 인증 없이 호출 → HTTP 401 | ✅ |
| 20 | OpenAPI — `month` 쿼리 파라미터 + `data` 3키 + `required: ["histories","month"]`(= `firstArchivedMonth` 는 optional) | ✅ |

정리 완료 확인: throwaway DB 2개 모두 drop / 8089 프로세스 종료 / 스크래치 삭제 /
공용 `challenge` DB 에 seed id(100~121) **0건** / `:8080` 정상(401) 응답.

## 미해결 (개정분)

- ⚠️ **`MethodArgumentTypeMismatchException` 전역 핸들러 부재** — 보관함은 문자열 파싱으로
  우회했지만 다른 엔드포인트가 타입 있는 파라미터를 쓰면 같은 구멍이 열린다. 계약 §5 백로그.
- ✅ **백로그 "페이지네이션 부재" 항목 철회** — pm-lead 반영 완료 (🟡→🟢 하향).
- 🔴 **`말일 챌린지` 축의 자동화 공백** — mobile 이 앱측 버킷팅과 그 회귀 테스트를 지우게 되므로
  서버 테스트가 유일한 방어라고 요청했다. `ChallengeHistoryServiceTest.판정 시각이 아니라
  챌린지 날짜로 월을 자른다` 가 **양방향으로**(7월 응답에 있고 8월 응답에 없다) 고정하지만,
  그건 **fake 를 태우는 단위 테스트**라 JPQL 축은 못 덮는다. 실제 SQL 축은 위 검증 #5(6/30 건의
  `completed_at` 이 7/1 인데 6월 응답에 담긴다)로 확인했으나 **자동화돼 있지 않다** —
  통합 테스트 49건 상시 skip(Docker 부재)과 같은 공백이다.

---

# 1차 (2026-08-26) — 이하 기록

## 구현 요약

| 태스크 | 상태 |
|---|---|
| T-B1 보관함 목록 API | ✅ 완료 |
| T-B2 회원탈퇴 API | ✅ 완료 |
| T-B3 로그아웃 계약 확인 + `WWW-Authenticate` 실측 | ✅ 완료 (서버 무변경) |
| 부록 — `photoDeleted` 필드 (design §7-⑤) | ✅ 완료 |
| T-B4 탈퇴 정책 2건 추가 (pm-lead 확정) | ✅ 완료 |

`PhotoStorage.delete()` 의 **첫 호출부가 생겼다** — 백로그 항목 해소 대상.

### T-B4 — pm-lead 확정 정책 2건

1. **탈퇴자가 보낸(challenger) `PENDING` 챌린지 = 물리 삭제.** 남겨 두면 상대가 수락해
   **결과가 이미 정해진** 챌린지를 시작한다(탈퇴자는 인증 불가). `PENDING` 에는 계약서·서명·
   사진·결과가 없어 **보존할 증거가 0** 이고, 처리가 챌린저의 취소와 정확히 같다.
   **받은(opponent) `PENDING` 은 그대로 둔다** — 수락될 수 없어 자연 만료된다.
2. **탈퇴자의 `notifications`(수신함) = 물리 삭제.** 본인 전용 개인 데이터라 *"양자 기록 보존"*
   대상이 아니라 **개인정보 삭제 축**에 속한다. **상대의 알림은 건드리지 않는다.**

🔴 두 JPQL 모두 `status` 를 **리터럴로 박았다.** DELETE 라 파라미터로 열면 `IN_PROGRESS`/
`COMPLETED` 가 흘러들어 **보존해야 할, 상대의 기록이기도 한 챌린지를 지우는 쿼리**가 된다.

⚠️ **모바일에 남는 표면**: 상대에게 이미 발송된 `CHALLENGE_REQUEST` 알림 row 는 보존되는데
그 챌린지는 삭제된다 → 상대가 탭하면 없는 챌린지로 딥링크한다.
**실측: `GET /challenges/{id}` 가 code=705 `"챌린지를 찾을 수 없어요"` 로 답한다** — 이미
설계된 정상 경로라 서버가 할 일은 없다. push-deeplink 쪽 표시만 확인 대상.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|---|---|---|---|
| GET | `/api/v1/challenges/history` | Bearer | implemented (미배포) — 🔴 **2026-08-28 월 단위로 개정됨. 위 개정 절이 현행** |
| DELETE | `/api/v1/users/me` | Bearer | implemented (미배포) |
| DELETE | `/api/v1/auth/logout` | Bearer | 기존 — **서버 변경 0** |
| GET | `/api/v1/challenges/{id}/verifications` | Bearer | **필드 1개 추가** (additive) |
| GET | `/api/v1/users/me` | Bearer | shape 무변경, **동작 변경 1건** (아래) |

공개 엔드포인트 추가 **0건**.

## 핵심 설계 결정

### 1. 카카오 unlink = **admin key** 방식, **DB 보다 먼저**

`POST https://kapi.kakao.com/v1/user/unlink` + `Authorization: KakaoAK {키}` +
`target_id_type=user_id&target_id={kakaoId}` (공식 문서 확인).

**사용자 access token 방식을 쓰지 않은 이유**: 서버는 카카오 access token 을 저장하지 않는다
(로그인 때 `/v2/user/me` 한 번 쓰고 버린다). 토큰 방식이면 앱이 탈퇴 시점에 카카오 토큰을 새로
받아 보내야 하고, **기기의 카카오 세션이 만료돼 있으면 탈퇴 자체가 불가능**해진다.

**순서가 unlink → DB 인 이유**: 두 순서의 실패 결과가 비대칭이다.
- DB 먼저 → unlink 실패: 계정은 이미 **되돌릴 수 없게** 익명화됐는데 카카오 연결은 살아 있고,
  `kakao_id` 를 지워서 **재시도할 대상조차 잃는다.** 복구 불가.
- unlink 먼저 → DB 실패: 카카오 연결만 끊기고 row 는 ACTIVE 로 남는다. 재로그인하면 같은
  row 로 돌아와 다시 탈퇴하면 된다. **복구 가능, 손실 0.**

카카오 `-101`(이미 연결 없음)은 **성공으로 삼킨다** — 부분 실패 후 재시도가 막히지 않는다.

### 2. `kakao_id` 를 NULL 로 만든다 (V11)

남겨 두면 **탈퇴자가 재로그인할 때 계정이 부활한다** — `findByKakaoId` 가 익명화된 DELETED row
를 찾아 그 위에 덮어쓴다. **실측으로 확인**했다 (§검증 16번: 재로그인이 새 계정 id=3 을 만들고
탈퇴 row 는 그대로 남는다). 더불어 `kakao_id` 자체가 개인 식별자다.

UNIQUE 는 유지 — Postgres 는 UNIQUE 컬럼에 NULL 을 여러 개 허용한다.

### 3. 사진 삭제는 **커밋 후**

파일 삭제는 트랜잭션이 아니다. tx 안에서 지우면 롤백돼도 파일이 안 돌아온다. 커밋 후로 미루면
최악이 **고아 파일**뿐이고 그건 읽히지 않으므로 무해하다. 삭제 실패는 삼키고 WARN 만 남긴다 —
이미 커밋된 탈퇴를 되돌릴 수 없기 때문이다.

### 4. ~~보관함은 **전체 목록 + 페이지네이션 없음**~~ 🔴 **2026-08-28 폐기 — 위 개정 절 참조**

~~실측: 이 프로젝트 목록 엔드포인트 5종 전부 페이지 파라미터가 **0건**이다. PM 규약이
*"페이지네이션은 프로젝트 전체에서 한 방식으로 통일"* 이라 보관함 하나만 도입하면
**그 규약이 금지하는 상태를 이 feature 가 만드는 셈**이다. → 백로그.~~

🔴 **월 단위 조회가 되면서 이 논거 전체가 무효다** — 한 응답의 상한이 한 달치로 고정돼
보관함은 "무한히 자라는 목록" 이 아니게 됐다. 백로그 항목도 철회 대상.

정렬·월 키가 `challengeDate` 인 것은 **유지된다** — 판정이 자정 직후 배치라 `completed_at` 으로
자르면 **말일 챌린지가 다음 달 응답으로 넘어간다.**

## 변경된 모듈 & 파일

**신규 11**
- `app/src/main/resources/db/migration/V11__user_withdrawal.sql`
- `domain/repository/.../auth/KakaoUnlinkPort.kt`
- `infra/external/.../kakao/KakaoUnlinkAdapter.kt` · `KakaoUnlinkConfig.kt`
- `service/.../user/WithdrawalService.kt` (+ `WithdrawalTransactionalWorker`)
- `service/.../challenge/ChallengeHistoryService.kt`
- `controller/.../challenge/ChallengeHistoryController.kt` · `dto/ChallengeHistoryResponse.kt`
- 테스트 3: `WithdrawalServiceTest` · `ChallengeHistoryServiceTest` · `ChallengeHistoryControllerTest`

**수정 (주요)** — `User.kt`(kakaoId nullable) · `UserEntity` · `UserRepository`/`Jpa`/`Impl` ·
`FriendshipRepository`/`Jpa`/`Impl` · `VerificationRepository`/`Jpa`/`Impl` ·
`ChallengeRepository`/`Jpa`/`Impl` · `KakaoOAuthClient` · `UserController` · `UserService` ·
`VerificationService` · `VerificationDtos` · `application.yml` · `WireShapeContractTest` 외 테스트 fake 다수.

## DB 마이그레이션

`V11__user_withdrawal.sql` — **DDL 한 줄**: `ALTER TABLE users ALTER COLUMN kakao_id DROP NOT NULL;`
+ `COMMENT ON COLUMN` 3건(`kakao_id` / `nickname` / `status`).

⚠️ **로컬 `challenge` DB 에는 아직 적용하지 않았다** (현재 `kakao_id` = `NOT NULL`).
검증은 별도 throwaway DB 에서 했고 끝난 뒤 drop 했다.

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui.html
- 반영: `GET /challenges/history`(Challenge 태그), `DELETE /users/me`(User 태그),
  `GET /challenges/{id}/verifications` 의 `photoDeleted` 필드.

## 테스트 결과

| 시점 | tests | passed | skipped | failures |
|---|---|---|---|---|
| 기준선 | 466 | 417 | 49 | 0 |
| T-B2 후 | 479 | 430 | 49 | 0 |
| T-B1 + photoDeleted 후 | 508 | 459 | 49 | 0 |
| **최종 (T-B4 후)** | **513** | **464** | **49** | **0** |

**회귀 0. 신규 47건** (WithdrawalServiceTest 15 · ChallengeHistoryServiceTest 14 ·
ChallengeHistoryControllerTest 6 · UserControllerTest +3 · VerificationServiceTest +4 ·
WireShapeContractTest +4 · VerificationControllerTest +1).

skip 49 는 **기존 블로커** — 컨테이너 런타임(Docker) 부재로 통합 테스트 전체가 `@EnabledIf` 로
비활성. 이번 작업이 늘린 것이 아니다.

## 🔴 실제 구동 검증 (unit test 가 못 덮는 축)

**smoke test 가 JPA 를 auto-configuration 에서 제외**하고 repository 를 전부 mock 으로 세운다.
즉 **통과한 508건 중 어느 것도 새 JPQL 이나 V11 을 실제 DB 에 대고 실행하지 않는다.**
그래서 별도로 확인했다 — throwaway DB(`challenge_verify`) + 포트 8087, **`:8080` 과 공용
`challenge` DB 는 건드리지 않았고** 끝난 뒤 DB·사진·프로세스 전부 정리했다.

| # | 검증 | 결과 |
|---|---|---|
| 1 | Flyway V1→V11 전체 적용 | ✅ `now at version v11` |
| 2 | Hibernate `ddl-auto=validate` + Spring Data JPQL 파싱 | ✅ 컨텍스트 기동 성공 |
| 3 | `KAKAO_ADMIN_KEY` 미설정 시 기동 WARN | ✅ 로그 확인 |
| 4 | 보관함 빈 목록 | ✅ `{"histories":[]}` |
| 5 | 정렬 `challengeDate DESC, id DESC` | ✅ ch2(8/14)→ch1(8/14)→ch3(7/3) |
| 6 | `myResult` 뒤집기 + `BOTH_LOSE` 안 접힘 | ✅ LOSE / DRAW / **BOTH_LOSE** |
| 7 | 응답에 `result`·인증상태 필드 없음 | ✅ |
| 8 | 시간 포맷 `yyyy-MM-dd` / `yyyy-MM-dd HH:mm:ss`, `T`·`Z` 없음 | ✅ |
| 9 | 탈퇴 → HTTP 200, `data` 키 없음 | ✅ |
| 10 | users 익명화 (kakao_id NULL / "탈퇴한 사용자" / 나머지 NULL / DELETED) | ✅ |
| 11 | friendships 물리 삭제 | ✅ 0행 |
| 12 | challenges 3건 · verifications 4건 **보존** (`status`/`verified_at` 그대로) | ✅ |
| 13 | 🔴 **인증 사진 파일 삭제** — 탈퇴자 것만 (`PhotoStorage.delete` 첫 실동작) | ✅ user1 것 1개 잔존, user2 것 2개 삭제 |
| 14 | 탈퇴자 사진 요청 404 / 정상 사용자 200 | ✅ |
| 15 | `photoDeleted` — 탈퇴자 VERIFIED 만 true, FAILED 는 false | ✅ |
| 16 | 상세·홈·랭킹·친구 무파손 (`vs 탈퇴한 사용자`, 랭킹·친구에서 제외) | ✅ |
| 17 | `GET /users/me` 탈퇴자 → 401 | ✅ |
| 18 | 탈퇴 재호출 멱등 → 200 | ✅ |
| 19 | 🔴 **재로그인이 부활이 아니라 신규 계정** | ✅ `userId=3, isNewUser=true` (탈퇴 row id=2 잔존) |

정리 완료 확인: `challenge_verify` drop / 사진 디렉터리 삭제 / 8087 프로세스 종료 /
공용 `challenge` DB 의 `users.kakao_id` 여전히 `NOT NULL` / `:8080` 정상 응답.

### 🔴 T-B4 2차 실구동 검증 — DELETE 는 단위 테스트로 못 덮는다

T-B4 는 **DELETE 두 개**를 추가한다. 단위 테스트의 fake 는 *"호출됐다"* 만 기록하므로
**어떤 row 가 실제로 지워지는지는 검증하지 못한다.** JPQL 이 파싱은 되면서 의미가 틀린
경우(예: `status` 조건 누락)를 전부 통과시킨다. 그래서 throwaway DB 로 다시 확인했다.

user1(탈퇴자) 기준 seed 후 탈퇴 실행:

| id | 관계 | 상태 | 기대 | 결과 |
|---|---|---|---|---|
| 10 | 내가 **보낸** | `PENDING` | 삭제 | ✅ 삭제됨 |
| 11 | 내가 **받은** | `PENDING` | 보존 | ✅ 남음 |
| 12 | 내 | `IN_PROGRESS` | 보존 | ✅ 남음 |
| 13 | 내 | `COMPLETED` | 보존 | ✅ 남음 |
| 14 | 제3자끼리 | `PENDING` | 보존 | ✅ 남음 |

`notifications`: user1 의 2건 삭제, **user2·user3 의 것은 보존** ✅

추가 확인:
- 🔴 **삭제된 챌린지로 딥링크** → `GET /challenges/10` 이 **HTTP 200 + code 705
  `"챌린지를 찾을 수 없어요"`** (앱이 무난히 그릴 수 있는 기존 경로) ✅
- 상대의 보관함(`ch13 vs 탈퇴한 사용자`)·홈(`ch12 IN_PROGRESS vs 탈퇴한 사용자`) 무파손 ✅

⚠️ **부수 발견**: `challenges` 에 `uq_challenges_active_pair_date`
(`LEAST(challenger,opponent), GREATEST(...), challenge_date`) 부분 유니크 인덱스가 있다.
seed 중 같은 쌍·같은 날짜로 두 건을 넣으려다 걸렸다 — V1 이후 마이그레이션에서 들어온
제약이며 **이번 변경과 무관**하다. 기록만 남긴다.

## 계약에 반영된 사항

- `api-contract.md` → **`confirmed`** (design §7 회신 + mobile 통지 반영)
- `docs/features/challenge-verification/change-log.md` → `photoDeleted` 추가 등재 (additive)

### ⚠️ `GET /users/me` 동작 변경 (shape 무변경)

**탈퇴한 계정이 부르면 401.** `kakao_id` 가 nullable 이 되면서 `UserInfoData.kakaoId: Long`
(non-null 계약)을 지키려면 필요했다. 이건 새 규칙이 아니라 **원래 KDoc 에 적혀 있던 동작의
유지**다 — *"DB 에 없으면(회원탈퇴/삭제) 401"* 은 **탈퇴가 row 를 지운다는 전제**였고 이번에
그 전제가 바뀌었다. 부수 효과로 access token 잔존 구멍이 이 엔드포인트에서는 닫힌다.

## 미해결 이슈

### ✅ 해소 — pm-lead 확정 2건은 T-B4 로 구현 완료

`PENDING` 삭제 · `notifications` 삭제 둘 다 익명화 트랜잭션에 들어갔고 실구동으로 검증했다.
계약 §2 의 오픈 이슈 두 절도 확정으로 전환했다.

### ⚠️ 운영 필수

- **`KAKAO_ADMIN_KEY`** — 사용자가 카카오 콘솔에서 발급해야 하는 값이라 서버가 만들 수 없다.
  미설정이면 unlink 를 건너뛰고 DB 익명화만 한다(기동+호출 WARN 2회). **배포 체크리스트.**
- 🔴 **카카오 `-101` 파싱은 실제 왕복으로 검증된 적이 없다.** admin key 가 없어 로컬·CI 가
  항상 No-Op 경로다. WireMock 통합 테스트를 붙일 수 있으나 이번 범위 밖으로 뒀다.

### 백로그 등재 요청

1. **탈퇴 후 access token 최대 1시간 잔존** — 닫으려면 **모든 인증 요청에 DB 조회 1회**가
   붙는다(전역 회귀 위험). 앱의 "탈퇴 즉시 로컬 토큰 삭제" 로 실사용 경로는 막았고 계약에
   수용 기준으로 명시. `GET /users/me` 만 예외적으로 닫혔다.
2. ~~**페이지네이션 부재** — 보관함이 프로젝트 최초의 "무한히 자라는 목록" 이다. 전 엔드포인트
   일괄 도입 시점 결정 필요.~~ 🔴 **2026-08-28 철회** — 월 단위 조회로 전제가 사라졌다.
   (전 엔드포인트 통일 논의 자체는 남지만 보관함은 그 1순위가 아니다.)
3. **`PhotoStorage.delete()` 호출부 0건** → **해소.** 백로그 항목 갱신 대상.
4. **통합 테스트 49건 상시 skip** (Docker 부재) — 기존 블로커. 이번에 그 공백을 수동 구동
   검증으로 메웠으나 **자동화돼 있지 않다.**
