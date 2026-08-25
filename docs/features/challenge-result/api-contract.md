# API Contract — 챌린지 결과 판정 (challenge-result)

- **feature-id**: challenge-result
- **상태**: `confirmed` — 서버 구현 완료 + **실서버 왕복 실측 완료** (아래 §5)
- **작성**: 2026-08-25 pm-lead (초안) → 2026-08-25 backend-dev (구체화·확정)
- **소유**: backend-dev
- **상위 spec**: [spec.md](./spec.md)

## 요약 — 신규 엔드포인트 0건, 기존 응답 확장 2건

판정은 배치(서버 내부)라 wire 가 없다. 계약 쟁점은 **기존 `confirmed` 응답 2개의 확장**뿐이다:

| # | 대상 | 변경 | 소관 계약 |
|---|---|---|---|
| 1 | `GET /api/v1/challenges/{id}` | `result` 필드 추가 | 🔴 soul-oath `confirmed` — **change-log 등재 필수** |
| 2 | `GET /api/v1/challenges/active` | `status`·`result` 필드 추가 + COMPLETED 한시 노출 | 🔴 home-feed `confirmed` — **change-log 등재 필수** |

둘 다 **필드 추가만** 이다. 기존 필드의 이름·타입·의미는 하나도 바뀌지 않는다 —
모바일이 새 필드를 무시하면 기존 동작이 그대로 유지된다(호환 방향이 안전한 쪽).

공통: ADR-0002(HTTP 200 + code) · ADR-0010(`yyyy-MM-dd HH:mm:ss` KST) 그대로.

## 공통 enum — `ChallengeResult`

| 값 | 의미 |
|---|---|
| `CHALLENGER_WIN` | 챌린저 승 (챌린저만 인증) |
| `OPPONENT_WIN` | 상대 승 (상대만 인증) |
| `DRAW` | 무승부 (양측 인증) |
| `BOTH_LOSE` | 양측 패 (양측 미인증) |

🔴 **관점 뒤집기(`CHALLENGER_WIN` → "내가 이겼다")는 앱이 한다.** 응답은 **역할 기준**이다.
상세는 `challenger`/`opponent` 를 역할 그대로 주고 있고(soul-oath §3), 홈 카드도
`challengeId` 로 내가 challenger 인지 알 수 있는 정보가… **없다.** → §2.2 참조.

## 1. `GET /challenges/{id}` — `result` 추가

```json
{
  "error": false, "code": 200, "message": "",
  "data": {
    "challengeId": 7,
    "status": "COMPLETED",
    "result": "CHALLENGER_WIN",
    "challengeDate": "2026-08-24",
    "deadline": "2026-08-25 00:00:00",
    "betContent": "커피 사기",
    "challenger": { "userId": 1, "nickname": "이우건", "profileImageUrl": null, "mission": "운동 1시간" },
    "opponent":   { "userId": 2, "nickname": "민수",   "profileImageUrl": null, "mission": "책 30p" },
    "contract": { "...": "무변경" }
  }
}
```

| 필드 | 타입 | null | 설명 |
|---|---|---|---|
| `result` | String enum | ✅ **nullable** | `COMPLETED` 가 아니면 **항상 null** (도메인 불변식 그대로) |

- 🔴 **키는 null 이어도 항상 존재** (`@JsonInclude(NON_NULL)` 미설정 — 실측 확인, `WireShapeContractTest` 로 고정)
- 🔴 **이 응답과 `GET /challenges/{id}/verifications` 는 서로 어긋나지 않는다.** 상세 화면은 둘을
  **따로** 호출하는데, 판정 배치가 두 테이블을 **한 트랜잭션**에서 바꾸므로 *"여기는 `COMPLETED`+
  `result` 인데 저기는 상대가 아직 `PENDING`"* 인 중간 상태가 **관측될 수 없다** (§3.1).
  앱은 두 응답을 합칠 때 정합성 방어를 짤 필요가 없다
- 🔴 **`status == COMPLETED` ⟺ `result != null`** 이 서버가 보장하는 불변식이다. 앱은 둘 중 하나만
  보고 분기해도 되지만, **`result` 를 보는 쪽을 권장**한다 — 결과 표시의 직접 근거이고,
  `EXPIRED`(성립 안 함)와 `COMPLETED`(판정됨)를 구분하는 데 `status` 만으로는 한 단계가 더 필요하다
- 모르는 enum 값 방어는 verification status 선례(역직렬화 전체를 깨지 않는 방식) 답습

## 2. `GET /challenges/active` — COMPLETED 한시 노출

### 2.1 왜 필요한가

현재 이 응답은 `IN_PROGRESS` 만 준다. 판정되는 순간 챌린지가 홈에서 사라지고 **푸시도 없으므로
사용자가 결과에 도달할 경로가 0 이 된다** (spec 오픈 이슈). 한시 노출이 유일한 진입 경로다.

### 2.2 🔴 필드 2개 추가 — `status` 는 신규 필수 필드다

현재 `ActiveChallengeDto` 에는 **`status` 가 아예 없다** (전부 IN_PROGRESS 라 필요가 없었다).
COMPLETED 가 섞이는 순간 앱이 카드를 구분할 수단이 없으므로 함께 추가한다.

```json
{
  "data": {
    "activeChallenges": [
      {
        "challengeId": 1002,
        "status": "IN_PROGRESS",
        "result": null,
        "myMission": "오늘 운동 1시간 하기",
        "opponentNickname": "민수",
        "opponentMission": "책 30페이지 읽기",
        "deadline": "2026-08-26 00:00:00",
        "myVerificationStatus": "PENDING",
        "opponentVerificationStatus": "VERIFIED",
        "bet": "커피 사기"
      },
      {
        "challengeId": 1001,
        "status": "COMPLETED",
        "result": "OPPONENT_WIN",
        "myMission": "오늘 운동 1시간 하기",
        "opponentNickname": "민수",
        "opponentMission": "책 30페이지 읽기",
        "deadline": "2026-08-25 00:00:00",
        "myVerificationStatus": "FAILED",
        "opponentVerificationStatus": "VERIFIED",
        "bet": "커피 사기"
      }
    ]
  }
}
```

| 필드 | 타입 | null | 설명 |
|---|---|---|---|
| `status` | String enum | ❌ non-null | `IN_PROGRESS` 또는 `COMPLETED` **둘 중 하나만** 나온다 |
| `result` | String enum | ✅ nullable | `IN_PROGRESS` 면 항상 null |

🔴 **`result` 는 역할 기준(`OPPONENT_WIN`)인데 이 응답의 나머지 필드는 "내 시점"(`myMission`)이다.**
같은 객체 안에 두 시점이 섞이는 셈이라 앱이 뒤집으려면 *"내가 challenger 인가"* 를 알아야 하는데,
**이 응답에는 그 정보가 없다** (`opponentNickname` 만 있고 역할은 없다).

→ **확정: 홈 카드용 `myResult` 를 추가한다 (A안).** 서버는 이미 `userId` 로 역할을 안다.
상세(§1)는 계약서 화면이라 역할 기준을 유지한다 — **같은 데이터라도 화면 성격이 다르면 시점이 다르다**
(soul-oath §3 이 세운 원칙 그대로).

| 필드 | 타입 | null | 값 |
|---|---|---|---|
| `myResult` | String enum | ✅ nullable | `WIN` / `LOSE` / `DRAW` / **`BOTH_LOSE`**. `IN_PROGRESS` 면 null |

#### 🔴 `BOTH_LOSE` 를 접지 않는다 — 4값이다 (2026-08-25 확정)

초안은 `BOTH_LOSE` 를 `LOSE` 로 접고 역할 기준 `result` 를 병기해 구분하게 하려 했다.
**result-mobile 이 기각했고 그 논거가 맞다**: 접어서 보내면 앱이 "둘 다 못 했다" 를
`myVerificationStatus == FAILED && opponentVerificationStatus == FAILED` 로 **역산**해야 복원되는데,
**그건 판정 규칙의 두 번째 사본을 앱에 심는 것**이다 — spec T-B2 가 *"판정 규칙은 한 곳에만"* 이라며
경계한 바로 그 지점이라, 서버가 그걸 강제하는 shape 을 내리는 건 자기모순이었다.

`BOTH_LOSE` 는 **관점 중립**이다(양쪽에서 뜻이 같다). 그래서 "내 시점" 좌표계를 깨뜨리지 않는다 —
이것이 4번째 값이 이 enum 에 들어올 자격이다.

#### (B안) `amIChallenger: Boolean` 은 왜 기각됐나 — 실패 모드가 "거짓말"이다

`kotlinx.serialization` 에서 키가 없으면 `Boolean` 은 기본값 `false` 로 **조용히** 채워진다.
그러면 앱이 관점을 **반대로 뒤집어 승리를 "패배"로 그린다.** 화면상 정상으로 보여 잡히지도 않는다.
`myResult` 는 없거나 모르는 값이면 → null → **뱃지를 안 그린다.**
**없는 게 보이는 실패**지 **틀린 걸 보여주는 실패**가 아니다.

⚠️ 기각이지 폐기가 아니다 — 필요하면 `amIChallenger` 를 **추가**로 열 수 있다(파괴적 변경 아님).

#### 역할 기준 `result` 는 이 응답에 **남긴다**

앱은 읽지 않기로 했다(모바일이 *"빼도 된다"* 고 했으나 강하게 주장하진 않았다). `WireShapeContractTest`
로 이미 고정돼 있고, 지난 챌린지 화면이 붙을 때 쓸 수 있어 남긴다.

🔴 **"안 읽어도 무해하다" 는 이제 주장이 아니라 양쪽에서 테스트로 고정된 사실이다** (2026-08-25 모바일).
앱이 `ActiveChallengeWireFixtureTest` 에서 `ignoreUnknownKeys = false` 로 `SerializationException` 을
**실패 고정**해, *"앱이 모르는 `result` 키가 있어도 파싱이 깨지지 않는다"* 를 증명했다.

> ⚠️ 그 옵션을 누가 끄면 **항목 하나가 드롭되는 게 아니라 홈이 통째로 죽는다.**
> **안 읽는 필드를 남겨 둔 선택이 결과적으로 회귀 방지선을 하나 만들어 준 셈**이다 —
> 빼기로 했다면 이 사각지대는 아무도 못 봤을 것이다.

부수로 **`/challenges/active` 에만 실서버 원문 픽스처가 없던 구멍**도 이때 닫혔다
(`/challenges/{id}` 와 `/verifications` 에는 있었다). 기존 테스트가 DTO 를 코드로 조립하는 방식이라
**JSON 키 이름·날짜 포맷·enum 문자열이 통째로 사각지대**였다. 픽스처는 2개다 — 3값으로 접던 시점의
**원문 그대로**(하위호환 증거, `LOSE` 로 읽힌다) + 4값 확정 후 현행 대표 응답(`BOTH_LOSE`).

#### ⚠️ 모바일은 `status`·`result`·`myResult` 를 전부 **`String`** 으로 받는다

서버는 Kotlin enum 을 이름 문자열로 직렬화하므로 **서버측 변경은 없다**(`"IN_PROGRESS"` 그대로).
모바일이 typed enum 을 피하는 이유는 **모르는 enum *값*이 오면 목록 전체 역직렬화가 죽기** 때문이다
(`ignoreUnknownKeys` 는 모르는 **키**만 막는다). 모르는 값의 항목은 앱이 드롭한다.

🔴 `myVerificationStatus` 는 **예외로 typed 를 유지**한다 — `VerificationStatus` 는
`PENDING`/`VERIFIED`/`FAILED` 3종이 상태 공간을 다 덮고 **늘릴 계획이 없다**(backend 확인).
오히려 이 feature 로 `FAILED` 가 처음 실제로 쓰이면서 3종이 다 채워졌다.
*"안 일어날 일에 방어 코드를 넣지 않는다."*

#### 🔴 배포 순서가 **양방향으로** 자유롭다 (2026-08-25 모바일 실측)

이 확장은 어느 쪽을 먼저 내보내도 깨지지 않는다. 두 방향의 근거가 **다르다**:

| 배포 순서 | 무엇이 지켜 주나 |
|---|---|
| **서버 먼저** (새 서버 ↔ 구버전 앱) | 앱 `Json { ignoreUnknownKeys = true }` + DTO 전 필드 기본값 → 새 필드 3개를 **무시**하고 기존대로 동작 |
| **앱 먼저** (새 앱 ↔ 구버전 서버) | 앱이 `status` **키 누락·빈 문자열을 `IN_PROGRESS` 로 간주**한다 |

⚠️ **두 번째가 방어를 위한 방어가 아닌 이유**: `status` 가 생기기 전 이 목록은 **정의상 전부
진행 중**이었다. 즉 폴백은 *"모르니까 대충 찍는다"* 가 아니라 **구버전 응답의 의미를 정확히
복원**하는 것이다. 이게 없으면 새 앱을 옛 서버에 붙이는 순간 **모든 항목이 드롭되어 진행 중
챌린지가 있는데도 홈이 통째로 비는** 조용한 전면 장애가 난다 — 개발 중에 바로 밟는 경로다.

🔴 **키 누락과 "모르는 값"은 다르게 처리된다.**

| 앱이 받은 것 | 처리 | 왜 |
|---|---|---|
| `status` 키 **없음** / `""` | `IN_PROGRESS` 로 간주, **항목 유지** | 복원할 의미가 있다(위 참조) |
| `status` = 모르는 값 (`"ARCHIVED"` 등) | **그 항목만 드롭** (`MappedList.droppedCount` 집계) | 복원할 의미가 **없다.** 카드가 상태에 따라 완전히 다른 것을 그리므로 추측해 그리면 **틀린 카드**를 보여준다 |

모바일이 두 경우를 갈라 wire 원문 테스트로 고정했다.
**서버는 이 규약에 기대어 `status` 를 생략해서는 안 된다** — 폴백은 구버전 호환 장치이지
서버가 필드를 빼도 된다는 허가가 아니다 (`status` 는 non-null 필수 필드다).

### 2.3 노출 조건 · 정렬

| 항목 | 제안값 | 근거 |
|---|---|---|
| 노출 조건 | `status = COMPLETED` **AND** `completed_at > now - N일` | `completed_at` 은 V1 부터 있는 컬럼. 판정 시각이 들어간다 |
| **N** | **7일** | 🔴 spec 제안값은 3일이었으나 **7일로 올린다.** 아래 참조. 서버 프로퍼티(`challenge.result.completed-retention-days`)라 코드 변경 없이 조정 가능 |
| 배열 | **기존 `activeChallenges` 한 배열에 섞는다** | 별도 배열이면 앱이 병합·정렬을 다시 결정해야 한다. 홈은 카드 한 줄기다 |
| 정렬 | **`IN_PROGRESS` 먼저 (deadline ASC) → `COMPLETED` (completed_at DESC)** | 진행 중이 행동 대상이고 결과는 확인 대상이다. 서버가 정렬해서 내리므로 앱은 순서대로 그리면 된다 |
| `EXPIRED` | **노출하지 않는다** | 성립하지 않은 챌린지 (계약 미체결). 전적에도 안 들어간다 |
| `PENDING` / `CONTRACT_SIGNING` | 무변경(미노출) | 이 응답의 기존 정책 그대로 |

#### 🔴 N=7 인 이유 — 이 창이 닫히면 챌린지는 **앱 어디에서도 도달 불가**다

result-mobile 실측([backlog 등재](../../backlog.md)): 지난 챌린지 목록 화면이 **없고**(마이페이지는
전적 숫자만), 알림도 **없다**(FCM 범위 제외). 즉 이 목록이 판정 결과에 도달하는 **유일한 경로**이며,
N 은 "얼마나 오래 보여줄까" 가 아니라 **"언제 영구히 접근 불가로 만들까"** 다.

> **7일도 정답이 아니라 시간벌기다.** 판정 결과는 제품의 종착점인데 열람 기한이 붙은 셈이고,
> 정식 해법은 **지난 챌린지 목록 화면 + 조회 API** 다 — 백로그에 등재됐고 개돼지 랭킹·마이페이지
> 계열 feature 에서 함께 본다. 그때 이 값은 무의미해진다.

⚠️ 서버 보관은 무한이다(row 를 지우지 않는다). 못 보는 것은 **목록**뿐이고
`GET /challenges/{id}` 는 id 만 알면 언제든 열린다 — 히스토리 화면이 붙을 때 바로 쓸 수 있다.

- ⚠️ **빈 목록 → 카드 없음** 의미가 미묘하게 바뀐다: 이제 "진행 중도 없고 최근 결과도 없다" 다.
  `HomeEmptyState` 문구가 그대로여도 무방한지는 mobile 판단.
- ⚠️ COMPLETED 카드의 `myVerificationStatus` 는 판정 배치가 미인증 측을 `FAILED` 로 바꾸므로
  **`PENDING` 이 아니라 `FAILED` 로 내려간다.** 홈의 `VerificationStatusPill` 이 `FAILED` 를
  이미 그릴 수 있는지 확인 필요 (challenge-verification 에서 `:core:ui` 로 승격된 컴포넌트).

## 3. 판정·집계 규약 (wire 없음 — 문서화 대상)

앱이 직접 호출하지 않지만 **화면에 뜨는 숫자의 정의**라 계약에 박아 둔다.

### 3.1 판정 규칙 (기획 §2.6)

배치 실행 시점에 `status = IN_PROGRESS AND deadline <= now(KST)` 인 챌린지 전부를 대상으로:

| 챌린저 인증 | 상대 인증 | `result` | 비고 |
|---|---|---|---|
| VERIFIED | VERIFIED | `DRAW` | 양측 성공 = 무승부 (원안 유지) |
| VERIFIED | 미인증 | `CHALLENGER_WIN` | |
| 미인증 | VERIFIED | `OPPONENT_WIN` | |
| 미인증 | 미인증 | `BOTH_LOSE` | |

- 전이: `status → COMPLETED`, `result` 기록, `completed_at = 판정 시각(KST)`
- 미인증 측 `verifications.status` 를 `PENDING → FAILED` 로 전이 (§2.5 *"미인증 시 자동 패배"* 이행)

#### 🔴 판정 · `FAILED` 전이 · 집계는 **모두 한 트랜잭션**이다 (앱이 기대도 되는 보장)

```
verifications PENDING→FAILED  →  challenges COMPLETED + result + completed_at
                              →  user_stats  →  friend_records      ← 전부 같은 @Transactional
```

**하나라도 실패하면 전부 롤백된다.** 부분 반영된 전적은 소급 수정이 불가능하므로 이 원자성이
판정 서비스의 존재 이유에 가깝다.

⚠️ **이게 왜 계약에 적혀야 하나** — 상세 화면은 **두 번 호출**한다
(`GET /challenges/{id}` + `GET /challenges/{id}/verifications`). 두 커밋이 갈라져 있으면 그 사이에
조회한 사용자가 **"승리" + 상대 뱃지 "대기중"** 을 본다. **앱이 방어할 수 없는 창**이라
표시 규칙을 따로 짜야 했을 것이다. 단일 트랜잭션이므로 그 창은 **존재하지 않는다** —
`{id}` 가 `COMPLETED`+`result` 를 보는 순간 `/verifications` 도 반드시 `FAILED` 를 본다.

> 🔴 이 보장을 위해 대상 선정 루프(`Runner`)와 건별 판정(`Service`)을 **별도 빈**으로 쪼갰다.
> 한 빈에서 self-invocation 하면 `@Transactional` 이 프록시를 타지 않아 **조용히 무효**가 되는데
> (어노테이션도 컴파일도 테스트도 멀쩡한데 운영에서만 부분 커밋), 그게 정확히 이 창이 열리는 경로다.
- **별도로** `status = PENDING AND deadline <= now` 인 챌린지는 `EXPIRED` 로 전이한다.
  🔴 **`EXPIRED` 는 판정이 아니다** — `result` 는 null 로 남고 **전적에 집계되지 않는다.**
  계약서가 체결되지 않았으므로 승부가 성립한 적이 없다.

### 3.2 배치 실행 (T-B1)

| 항목 | 값 |
|---|---|
| 정기 실행 | 매일 **00:05 KST** (`@Scheduled(cron, zone = "Asia/Seoul")`, 프로퍼티로 조정 가능) |
| 기동 시 실행 | ✅ `ApplicationReadyEvent` 에서 1회 — **서버가 자정에 죽어 있었어도 기동 즉시 소급 판정** |
| 소급 보장 | 대상 선정 기준이 **실행 시각이 아니라 `deadline`** 이다. 며칠 밀려도 다음 실행이 전부 처리 |
| 멱등 | 판정 즉시 `COMPLETED` 로 나가므로 재실행 시 **대상 집합에서 빠진다.** 두 번 세지 않는다 |
| 트랜잭션 | **챌린지 1건 = 1 트랜잭션.** 한 건이 터져도 나머지는 판정된다 (다음 실행이 실패분 재시도). 🔴 **그 1 트랜잭션 안에 `verifications` 의 `FAILED` 전이와 전적 집계가 전부 들어 있다 — [§3.1 의 원자성 보장](#-판정--failed-전이--집계는-모두-한-트랜잭션이다-앱이-기대도-되는-보장) 참조.** 상세 화면이 두 번 호출해도 *"승리 + 상대 대기중"* 을 볼 수 없다는 근거가 그것이다 |
| 🔴 알림 | **발송하지 않는다.** `NotificationMessages` 무변경, `notifications` row 증가 0 (범위 제외) |
| 운영 스위치 | `challenge.result.batch.enabled` (기본 true) · `challenge.result.batch.cron` (기본 `0 5 0 * * *`) |

##### ⚠️ 중복 실행 가드는 **단일 인스턴스 전제**다

기동 시 실행과 cron 이 겹칠 수 있어(00:05 근처 재기동) in-process 플래그로 막는다. **다중
인스턴스에서는 두 대가 동시에 돌 수 있다.** 그래도 **전적이 두 번 세어지지는 않는다** — 판정
직전 상태를 다시 확인하는 멱등 가드가 두 번째를 건너뛰기 때문이다. 즉 겹침은 **헛일이지
데이터 손상이 아니다.** 제대로 된 해법(DB 락 / Quartz 잡스토어)은 ADR-0007(local→AWS) 소관이고,
그때까지의 임시 방편은 한 대만 `enabled=true` 로 두는 것이다.

##### ⚠️ 계약이 검증하지 못하는 것 — cron 이 정말 00:05 KST 에 도는가

cron 파싱과 `zone` 적용은 Spring 소관이라 단위 테스트로 고정할 수 없다. 기동 경로와 빈 배선은
실제 컨텍스트 로그로 확인했다. **실패 모드는 `zone` 명시를 지우는 것**이며, 그러면 AWS(UTC)에서
조용히 09:05 KST 에 돈다 — 컴파일러도 테스트도 잡지 못한다. 코드 KDoc 에 박제했다.

### 3.3 전적 집계 — `user_stats` (T-B3)

판정과 **같은 트랜잭션**에서 갱신한다 (롤백되면 둘 다 되돌아간다).

> 🔴 **정본 지정.** 아래 표는 [home-feed api-contract](../home-feed/api-contract.md)
> (`confirmed` v2, 2026-06-15) *"user_stats 집계 규칙"* 의 **사본**이다.
> **어긋나면 home-feed 계약이 정본이고 이 문서가 틀린 것이다.**
> 배치 구현 문서로서 표를 여기 두는 값은 인정하되, 갈라졌을 때 누가 이기는지를 못박아
> 이 레포가 반복해 겪은 문서 드리프트를 막는다 (pm-lead 판정 2026-08-25).

| `result` | 챌린저 | 상대 |
|---|---|---|
| `CHALLENGER_WIN` | `wins+1` | `losses+1` |
| `OPPONENT_WIN` | `losses+1` | `wins+1` |
| `DRAW` | `draws+1` | `draws+1` |
| `BOTH_LOSE` | `losses+1` | `losses+1` |

`total_challenges` 는 양측 모두 `+1` (네 경우 전부).
🔴 **`BOTH_LOSE` 는 별도 카운터가 아니라 `losses`** 다 — 앱 `UserRecord` 에 `both_lose` 필드가 없다.

#### 🔴 `current_streak` = **연승 전용** — DRAW·BOTH_LOSE 는 0 으로 끊는다

spec 이 오픈 이슈로 올렸지만 **협의할 게 없었다. 이미 두 곳에 확정돼 있었다.**

1. 🔴 [home-feed api-contract](../home-feed/api-contract.md) *"user_stats 집계 규칙"* — **`confirmed` 계약이다.**
   위 §3.3 표의 네 줄과 *"`currentStreak` = 가장 최근 결과 시점부터 **win 만 연속**된 횟수.
   lose/draw/both_lose 발생 시 0으로 초기화"* 가 2026-05-25 부터 적혀 있었다.
2. 모바일 `domain/model/UserRecord.kt` KDoc 이 같은 문장을 갖고 있고, `HomeUiState` 가
   `if (currentStreak > 0) "N🔥" else "0"` 로 그린다.

**즉 이 feature 는 새 규칙을 만드는 게 아니라, 계약이 이미 약속했는데 이행하는 코드가 없던 것을
채우는 일이다.** 규칙을 다시 정하면 `confirmed` 계약을 뒤집는 셈이 된다 — 그럴 이유가 없다.

> ⚠️ 배운 것: **집계 규칙이 그 값을 *읽는* 엔드포인트의 계약에 살고 있었다.** 판정 feature 의
> 스펙을 쓸 때 `GET /record` 계약을 보지 않아 "오픈 이슈" 로 잡혔다. 소비자 계약이 생산자 규칙을
> 이미 정의해 둔 경우가 있다.

| 결과 | `current_streak` |
|---|---|
| 승 | `+1` |
| 패 | `0` |
| 무승부 | `0` |
| 양측 패 | `0` |

`max_streak` = 여태까지의 `current_streak` 최댓값 (= 최대 연승). 승리 시점에만 갱신된다.

⚠️ **개돼지 랭킹의 "연패" 는 이 컬럼으로 표현할 수 없다.** 부호를 섞으면(`-2` = 2연패)
`max_streak`("최대 연승")의 의미가 무너지고 홈의 🔥 표기가 거짓말을 한다.

#### 🔴 연패 전용 컬럼 2개를 **이번 feature 에서** 추가한다 (V10, 2026-08-25 pm-lead 승인)

~~연패는 후속 랭킹 feature 로 넘긴다~~ — **뒤집혔다.** `docs/backlog.md` 가 2026-08-06 부터
이 항목을 *"판정 feature 스코프"* 로 예약해 두었고 spec 초판이 그걸 놓친 것이었다(spec 정정 완료).

```sql
-- V10__user_stats_loss_streak.sql
ALTER TABLE user_stats ADD COLUMN current_loss_streak INT NOT NULL DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN max_loss_streak     INT NOT NULL DEFAULT 0;
```

**지금 넣는 이유는 비용의 *크기* 가 아니라 *종류* 다.** 집계 로직을 처음 쓰는 시점이라 지금은
컬럼 추가 + 규칙 2줄이면 끝난다. 나중에 하면 **이미 쌓인 결과를 `completed_at` 순으로 되짚는
백필**이 필요하다 — 연패는 **순서 의존**이라 현재 합계(`losses`)로는 산출할 수 없다.

| `outcome` | `current_loss_streak` |
|---|---|
| `LOSE` | `+1` |
| `BOTH_LOSE` | `+1` |
| `WIN` | `0` |
| **`DRAW`** | **`0`** |

`max_loss_streak` = 여태까지의 `current_loss_streak` 최댓값.

**연승 규칙의 정확한 거울상이다** — `current_streak` 이 "승리만 연속"이고 무승부가 끊듯,
`current_loss_streak` 은 "패배만 연속"이고 **무승부가 끊는다.** 무승부는 패배가 아니므로
연속 패배가 이어질 근거가 없다. 두 규칙이 같은 모양이라야 다음 사람이 한쪽만 보고 나머지를
맞게 추측한다. 결과적으로 **연승과 연패는 동시에 0 보다 클 수 없다.**

`BOTH_LOSE` 가 연패를 잇는 것은 **그것이 패배이기 때문**이다 — home-feed 정본이
*"BOTH_LOSE → 양쪽 lose+1"* 로 이미 패배로 세고 있고, `losses` 와 `current_loss_streak` 이
서로 다른 사건 집합을 세면 랭킹의 두 정렬 축(**총 패배 수 · 연패**, 기획 §3.4)이 어긋난다.

🔴 **wire 노출은 하지 않는다.** `GET /record` 응답(`RecordData`)은 **무변경**이다 — 지금 이 값을
읽는 화면이 없다. 소비는 개돼지 랭킹 feature 몫이고, 이 feature 는 **데이터를 채워만 둔다**
(`friend_records` 와 같은 취급).

#### row 부재

`user_stats` 는 신규 사용자에게 row 가 없을 수 있다. 첫 판정 시 **0 에서 시작하는 row 를 만든다**
(`UserRecord.empty` 와 같은 값). 조회(`GET /record`)의 0 채움 동작과 결과가 일치한다.

🔴 **집계가 붙는 순간 홈 전적(StatsBar)이 실데이터가 된다** — 지금까지 항상 0 이었다.
`GET /record` 는 무변경이고 읽는 값만 채워진다.

### 3.4 `friend_records` (T-B3, 개돼지 랭킹 준비)

`(user_id, friend_id)` **방향 있는 2행**을 챌린지 1건당 갱신한다 (A→B, B→A).
`wins`/`losses`/`draws` 만 있고 streak 컬럼은 없다. `BOTH_LOSE` 는 양쪽 `losses+1`.
**이 feature 에서 읽는 wire 는 없다** — 랭킹 feature 가 소비한다.

## 4. 무변경 확인

| 대상 | |
|---|---|
| `GET /api/v1/record` | 무변경. 값만 실데이터가 된다 |
| `GET /challenges/{id}/verifications` | 무변경. 판정 후 미인증 측이 `FAILED` 로 보이는 것이 유일한 차이 |
| `GET /challenges/{id}/photos/{party}` | 무변경 (`IN_PROGRESS` 를 요구하지 않으므로 판정 후에도 사진이 열린다) |
| `GET /challenges/received` | 무변경. `EXPIRED` 전이는 이미 `deadline > now` 로 걸러지던 row 를 DB 상태까지 정리하는 것 |
| 알림 | 🔴 **일절 없음** |

## 5. 🔴 실서버 실측 (2026-08-25) — 계약이 문서가 아니라 관측이 됐다

사용자 로컬 DB 에 **마감이 최대 21일 지난 챌린지가 그대로 남아 있어서**, 소급 판정을 가정이 아니라
실데이터로 증명할 수 있었다. 사용자 서버(`:8080`)는 건드리지 않고 **`:8081` 에 별도 기동**했다.

### 배치 (기동 시 트리거)

```
ChallengeJudgementRunner : 판정 배치 완료 (now=2026-08-25T15:56:08):
                           JudgementRunResult(judged=6, expired=2, failed=0, skipped=0)
```

| 검증 항목 | 결과 |
|---|---|
| 🔴 **소급 판정** | 마감 `2026-08-04`~`08-19` 인 6건이 **08-25 기동 시점에** 전부 판정됐다. 자정을 21번 놓쳤어도 한 번에 따라잡는다 |
| 판정 규칙 | 양측 미인증 6건 → 전부 `BOTH_LOSE` (규칙표대로) |
| **아직 마감 전은 건드리지 않는다** | `deadline=2026-08-26` 인 1건은 `IN_PROGRESS` 유지, 그 양측 `VERIFIED` 도 그대로 |
| `FAILED` 전이 | `verifications` `PENDING` 12건 → `FAILED` 12건. `VERIFIED` 2건은 **무변경** |
| `EXPIRED` 전이 | 마감 지난 `PENDING` 2건 → `EXPIRED`. **`result` 는 `NULL`, `completed_at` 도 `NULL`** |
| `user_stats` | 4명 생성 — total `3/4/3/2` (= 6건 × 2 = 12). 전부 `losses`, `current_streak=0` |
| `friend_records` | **방향 8행**. 같은 상대와 2번 진 쌍은 `losses=2` 로 누적 |
| 🔴 **알림 0건** | `notifications` **14 → 14**. 증가 0 (수용 기준 충족) |
| 🔴 **멱등** | 재기동 2회차 `judged=0, expired=0`. `user_stats` md5 해시 **동일**, `friend_records` 8행 유지 |

### wire

| 검증 | 결과 |
|---|---|
| `/challenges/active` 정렬 | `IN_PROGRESS`(30) → `COMPLETED`(29, 26, 21, 11) — `completed_at` DESC 정확 |
| `status`/`result`/`myResult` | `COMPLETED` 카드에 `result="BOTH_LOSE"` + **`myResult="BOTH_LOSE"`** (4값 확정 반영) |
| 🔴 **null 키 잔존** | `IN_PROGRESS` 카드에 `"result": null, "myResult": null` — **키가 나간다**(#24) |
| `myVerificationStatus` | `COMPLETED` 카드에서 **`FAILED`** 로 내려간다 (예고대로) |
| `EXPIRED` 미노출 | 24·28 은 목록에 **없다** |
| `GET /challenges/{id}` | `COMPLETED`→`result="BOTH_LOSE"` / `IN_PROGRESS`→`null`(키 존재) / **`EXPIRED`→`null`** |
| `GET /record` | `{"win":0,"lose":4,"draw":0,"currentStreak":0}` — **처음으로 0 이 아닌 실데이터** |

⚠️ 이 실측이 **단위 테스트로는 덮이지 않는 것 3가지**를 확인해 줬다: `@Value` 프로퍼티 주입
(`completed-retention-days`), JPQL 의 `status = 'COMPLETED'` 문자열 리터럴 비교(엔티티가 `String`),
그리고 `ApplicationReadyEvent` → 배치 실행 경로 전체. 통합 테스트는 Docker 부재로 45건이 skip 되므로
이 세 가지를 검증할 다른 수단이 없었다.

**DB 는 전량 원복했다** — 상태·verification·`user_stats`(0행)·`friend_records`(0행)·`notifications`(14)
전부 실측 전과 동일. 원복 SQL 은 backend-report 에 있다.

### 5.1 2차 실측 (V10 연패 컬럼 + `myResult` 4값)

| 검증 | 결과 |
|---|---|
| 🔴 **V10 적용** | `Migrating schema "public" to version "10"` → `Successfully applied 1 migration` |
| 🔴 **`ddl-auto=validate` 통과** | 서버가 **기동됐다.** 엔티티 2컬럼과 SQL 2컬럼이 실제로 맞는다는 유일한 증거 — 어긋나면 기동 자체가 실패한다 |
| 연패 누적 | 4명 `current_loss_streak = 3/4/3/2`. **각자 연속 패배 횟수와 정확히 일치** (user 14 는 BOTH_LOSE 4연패 → 4) |
| `max_loss_streak` | 동일값 3/4/3/2 |
| **연승은 0** | `current_streak` / `max_streak` 전원 0 — 연패와 연승이 **동시에 살아 있지 않다** |
| `myResult` 4값 | `COMPLETED` 카드 전부 **`myResult="BOTH_LOSE"`** (접히지 않는다) |
| 🔴 **`GET /record` 무변경** | `{"win":0,"lose":4,"draw":0,"currentStreak":0}` — **연패 필드가 새지 않는다** |

⚠️ **실데이터가 `BOTH_LOSE` 일색이라 실측으로 못 덮은 것이 하나 있다** — *"무승부·승리가 연패를 0 으로
끊는다"*. 그 분기는 **단위 테스트로만** 고정돼 있다(`UserRecordApplyingTest`).

⚠️ **V10 스키마는 원복하지 않고 남겼다.** 정식 마이그레이션이라 되돌리면 다음 기동에서 어차피 다시
적용된다. 데이터(행)만 원복했다. 컬럼은 `DEFAULT 0` 추가라 기존 row 에 무해하고, 구버전 코드가
읽어도 문제되지 않는다(Hibernate `validate` 는 매핑된 컬럼의 존재만 검사하며 여분 컬럼은 무시한다).

## 협의 이력

| 일시 | 작성자 | 변경 |
|---|---|---|
| 2026-08-25 | pm-lead | 초안 — 신규 0건 / 기존 확장 2건 골격. 쟁점: active 노출 정책·streak 의미 |
| 2026-08-25 | result-mobile → backend-dev | **배포 순서 양방향 안전** 문서화(§2.2). 앱이 `status` **키 누락·빈 문자열을 `IN_PROGRESS` 로 간주**한다 — `status` 가 생기기 전 이 목록은 **정의상 전부 진행 중**이었으므로 구버전 응답의 의미를 정확히 복원하는 것이다. 없었으면 새 앱 ↔ 옛 서버에서 **전 항목 드롭 → 홈 전면 공백**. ⚠️ **모르는 *값*은 여전히 항목 드롭** — 복원할 의미가 없고 카드가 상태별로 완전히 다른 것을 그려서 추측하면 틀린 카드가 된다. 두 경우를 갈라 wire 원문 테스트로 고정. 🔴 서버는 이에 기대어 `status` 를 생략하면 안 된다(non-null 필수) |
| 2026-08-25 | backend-dev | **최종 확정 3건** (모바일 협의 + pm-lead 판정 반영). ① **`myResult` 4값** — `BOTH_LOSE` 를 `LOSE` 로 접지 않는다(접으면 앱이 verification status 로 **역산**해야 하고 그건 판정 규칙의 두 번째 사본이다 — result-mobile 논거 채택). ② **판정·`FAILED` 전이·집계가 단일 트랜잭션**임을 §3.1 에 명시(상세 2회 호출 사이의 *"승리 + 상대 대기중"* 창이 없다는 보장). ③ **V10 연패 2컬럼 이번 feature 포함**(pm-lead 승인) — 규칙은 **연승의 거울상**(무승부가 끊는다), wire 무노출. 최종 `437 tests / 392 passed / 45 skipped / 0 failed` + **2차 실측 완료**(§5.1) |
| 2026-08-25 | backend-dev | 🔴 **`confirmed` 전이.** 서버 구현 완료(테스트 `431 tests / 386 passed / 45 skipped / 0 failed`, 기준선 `365/320/45` 대비 회귀 0) + **실서버 왕복 실측 완료**(§5). 확정된 값: **N=7일**(spec 제안 3일 → backlog 의 result-mobile 실측 근거가 더 강해 그쪽 채택), **`myResult`(A안)**, streak = 연승 전용. ⚠️ `amIChallenger`(B안)는 폐기가 아니라 **미채택** — 필요하면 필드 추가로 열린다(파괴적 변경 아님) |
| 2026-08-25 | backend-dev | 구체화 + 상태 `negotiating`. **쟁점 2건 해소 제안**: ① active 는 단일 배열에 COMPLETED 를 N=3일 섞고 `status`·`result`(+`myResult`) 추가, 정렬은 진행중→결과 ② streak 은 모바일 `UserRecord` KDoc 의 기존 정의(연승 전용)를 서버가 이행, 연패는 별도 컬럼으로 후속. `EXPIRED` 는 집계 제외 명시. **회신 요청: `myResult` vs `amIChallenger`** |
