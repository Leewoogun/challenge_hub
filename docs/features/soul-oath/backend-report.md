# Backend Report — soul-oath

- **feature-id**: soul-oath
- **작성**: 2026-08-03 by backend-dev
- **상태**: implemented + **실서버 검증 완료** (재기동 후 **56/56 PASS**), 커밋 안 함
- **선행 입력**: [spec.md](./spec.md), [api-contract.md](./api-contract.md) (status: `confirmed`), [design.md](./design.md), [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)
- **빌드 검증**: `./gradlew build` → **BUILD SUCCESSFUL** / 전체 **216** / 실행 **171 passed, 0 failed, 0 error** / 통합 **45 skip**(Docker 부재)

## 구현 요약

챌린지 신청·수락에 **영혼의 맹세(서명)** 를 붙였다. 핵심 결정 두 가지가 구현 형태를 결정했다.

1. **서명을 파일이 아니라 벡터 스트로크 JSON 으로 DB 에 저장한다** — 파일 스토리지 ADR 을 선행시키지 않는다.
2. **`CONTRACT_SIGNING` 상태를 도입하지 않는다** — 수락+서명이 단일 원자 요청이라 최종 상태는 여전히 `IN_PROGRESS` 다.

2번 덕분에 `challenge-create` 의 기존 테스트에서 **단언을 고친 게 한 건도 없다**(→ T-B4).

구현 후 **두 건의 정정**이 들어왔다. 둘 다 내 최초 구현이 틀린 경우다:

- **서명 필드가 JSON 객체가 아니라 문자열이어야 한다** (mobile-dev 지적 → §T-B2a)
- **계약서 본문 문구 3건** (design-bridge 검토 → pm-lead 지시 → §T-B2b)

## 엔드포인트

| Method | Path | 인증 | 변경 | 상태 |
|--------|------|------|------|------|
| POST | `/api/v1/challenges` | 필요 | **`signature` 추가** (필수) | implemented |
| POST | `/api/v1/challenges/{id}/accept` | 필요 | **`signature` 추가** (필수) | implemented |
| GET | `/api/v1/challenges/{id}` | 필요 | **신규** — 계약서 + 양측 서명 | implemented |
| POST | `/api/v1/challenges/{id}/reject` | 필요 | 무변경 (contract **보존**) | implemented |
| DELETE | `/api/v1/challenges/{id}` | 필요 | contract **선삭제** 추가 | implemented |

## T-B1 — V7 마이그레이션 (rename + 컬럼 주석 6건)

`app/src/main/resources/db/migration/V7__soul_oath_signature_data.sql` — **DML 0줄.** DDL 은 rename 2건, 나머지는 전부 주석이다.

### `_url` → `_data` 인 이유

V1 이 만든 `challenger_signature_url` / `opponent_signature_url` 은 이름대로 가려면 파일 스토리지가 선행돼야 한다. 벡터 저장으로 결정한 순간 **컬럼 이름이 거짓이 된다.**

**`_strokes` 가 아니라 `_data` 로 간 이유**는 별도다. `_url` 의 진짜 실패는 "저장 표현을 컬럼 이름에 박았다"는 것이고, `_strokes` 는 같은 실수를 다른 표현으로 반복한다(포맷이 바뀌면 또 거짓이 된다). **이름은 중립으로 두고 정확한 형식은 주석에 남겼다** — `\d+ contracts` 로 찾을 수 있는 자리다.

> `contracts` row = **0**(2026-08-03 실측). rename 이 가장 싼 시점이 지금이다.

### 주석 6건 (ADR-0010 의 `COMMENT ON COLUMN` 17건 선례 승계)

| 컬럼 | 남긴 것 |
|---|---|
| `challenger_signature_data` | 저장 포맷 실례 `{"v":1,"g":1000,"s":[[...]]}` + `v`/`g`/`s` 의미 + 평탄 배열·짝수 길이 + `NULL = 미서명` |
| `opponent_signature_data` | 위와 동일 형식임을 명시 |
| `is_finalized` | **`CONTRACT_SIGNING` 을 도입하지 않은 이유** — 그 상태의 챌린지는 `/received`(PENDING만)에도 `/active`(IN_PROGRESS만)에도 안 잡혀 재개 경로가 사라진다 |
| `content` | 서버 템플릿이 채운다(커스터마이즈 비범위) |
| `challenger_signed_at` / `opponent_signed_at` | KST 기준 (ADR-0010) |

`is_finalized` 주석에 **"왜 안 했는가"** 를 넣은 게 의도적이다. 하지 않은 선택은 코드 어디에도 흔적이 없어서, 다음 사람이 같은 아이디어를 다시 떠올렸을 때 막을 게 없다.

### FK — CASCADE 를 쓰지 않는다

`contracts_challenge_id_fkey` 에 `ON DELETE` 절이 없다. **의도적으로 그대로 뒀고**, 취소 경로에서 서비스가 contract 를 명시적으로 먼저 지운다.

> 근거를 마이그레이션 주석에 남겼다: 이 제품의 컨셉은 "무를 수 없는 약속"이다. CASCADE 는 **다른 이유로 challenge 를 지울 때도 맹세를 조용히 함께 지운다.** 물리 삭제 + 감사 추적 없음 위에 암묵적 연쇄 삭제까지 얹으면 되돌릴 근거가 사라진다. 명시적 삭제는 코드에 순서가 보인다.

## T-B2 — 서명 검증 + 계약서 생성/완결

### `SignatureValidator` (`:domain:model`)

검증 **순서가 의미를 만든다**:

1. **길이** (≤ 32KB) — 파싱 **전에** 본다. 32KB 를 파싱한 뒤 "너무 크다"고 하는 건 순서가 거꾸로고, 악의적 대용량이 파싱 비용을 치르게 된다.
2. **파싱 + `v == 1` + `g > 0` + 모든 획 길이 짝수 + 전 좌표 Int**
3. **빈 서명 거부**

**`v == 1` 고정**: 구조 검증(평탄 배열·짝수 길이)은 v1 전용 규칙이다. 고정하지 않으면 v2 데이터에 v1 규칙을 조용히 적용하게 된다. 버전 상향에 양측 동시 배포가 필요해지는 게 의도다.

**점 1개(탭)는 유효**로 본다 — 최소 점 개수를 서버가 발명하면 짧게 서명하는 사람을 오거부하고 그 임계값에 근거가 없다. 모바일 CTA 활성 조건과 같은 규칙(≥1점)이라 **클라 통과 → 서버 거부**가 생기지 않는다.

**검증은 쓰기 시점에만 한다.** 읽기 경로는 크기를 안 본다 — 상한은 입력 규칙이지, 나중에 상한을 낮췄을 때 **기존 계약서가 통째로 안 열리게** 만들 이유가 아니다(mobile-dev 디코드 정책과 대칭).

### 상수는 서버가 **길이 하나만** 갖는다

`MAX_POINTS 2,000` / `MAX_STROKES 64` 는 **캡처 상한이라 모바일 소유**다. 서버가 같은 숫자를 중복 보유하면 한쪽만 바뀌었을 때 조용히 어긋난다. 서버는 `MAX_SIGNATURE_LENGTH = 32 * 1024` 하나로 막는다.

> pm-lead 지시("두 축 유지")에 대한 답: **두 축은 모바일에서 유지되고, 서버는 그 두 축의 결과를 덮는 상한 하나를 본다.** 서버에 점 개수 상한을 두려면 파싱이 필요한데 길이 체크가 먼저 걸러주므로 이득이 없고, 숫자 중복만 남는다.

### 🔴 최악값을 서버가 **독립적으로 다시 만들어** 길이를 대조했다

pm-lead 지시대로 mobile-dev 방식을 서버에서도 실행했다. 캡처 상한(2,000점 / 64획)에서 나올 수 있는 가장 긴 인코딩을 서버 테스트가 직접 생성한다 — 좌표 전부 4자리(`1000`), 획을 64개로 쪼개 대괄호·쉼표 최대.

```
서버가 만든 최악값 길이 = 20,150자
mobile-dev 실측값      = 20,150자   ← 일치
32KB(32,768) 대비        61.5%
```

이 숫자를 **테스트에 하드코딩해 단언**했다(`assertEquals(20_150, worst.length)`). 한쪽만 재면 인코딩 가정(구분자·자릿수)이 어긋나도 아무도 모른다. 그리고 그 최악값이 **실제로 `validate` 를 통과하는지**까지 확인한다 — 길이만 재고 검증을 안 돌리면 반쪽이다.

### 계약서 생성 / 완결

| 시점 | 하는 일 |
|---|---|
| **신청** | 같은 트랜잭션에서 contract 생성. `content` 렌더 + 챌린저 서명 + `challenger_signed_at`, `is_finalized = false` |
| **수락** | contract 로드 → `is_finalized` 이면 거부 → 상대 서명 + `opponent_signed_at` + `is_finalized = true` → **그 다음** challenge 를 `IN_PROGRESS` 로 |
| **거절** | contract **무변경 보존** |
| **취소** | `contractRepository.deleteByChallengeId(id)` → `challengeRepository.deleteById(id)` (**순서 고정**) |

**신청 시 계약서를 함께 만드는 이유**: 챌린지는 있는데 계약서가 없는 상태가 생기면 상대가 맹세 화면에서 볼 게 없다. `PENDING` 구간에 **한쪽만 서명된 계약서가 실재**하는 게 정상 상태다.

**수락에서 contract 를 먼저 완결시키는 이유**: spec 수용 기준이 *"`is_finalized = true` 가 된 시점에만 `IN_PROGRESS`"* 다. 원자 요청이라 둘은 항상 함께 일어나지만, 코드 순서가 그 문장과 같은 방향이어야 나중에 읽는 사람이 조건을 뒤집지 않는다.

`is_finalized` 재서명 거부는 **2차 방어선**이다 — 대개 status 가드가 먼저 막지만, "무를 수 없다"가 이 feature 의 컨셉이라 계약 자체에도 걸어뒀다.

### 계약서 본문은 **박제**한다

`ContractContent.render(...)` 결과를 `contracts.content` 에 저장한다. 템플릿을 참조하지 않는다.

> 계약서는 **그 시점의 약속을 남기는 기록**이다. 나중에 템플릿 문구를 바꾸면 이미 맺은 맹세의 본문까지 소급해 바뀌는데, 그건 "무를 수 없는 약속"과 어긋난다.

**단, 굳는 시점은 신청이 아니라 완결이다** — 아래 T-B2b 참조.

---

## T-B2a — 🔴 서명 필드는 JSON 객체가 아니라 **문자열**이다 (정정)

**mobile-dev 가 계약을 읽고 "문자열이어야 한다"고 물어왔고, 그 판단이 맞았다. 내 최초 구현이 틀렸다.**

내가 요청 DTO 를 `JsonNode`(JSON 객체)로 받고 `body.signature?.toString()` 으로 문자열화해 저장하고 있었다.

### 무엇이 문제였나 — 내가 계약에 적고 테스트로까지 고정한 순서가 무효였다

계약 §4.4 의 검증 순서는 **"길이 → 파싱"** 이고, 근거는 *"악의적 대용량을 파싱 비용을 치르기 전에 막는다"* 였다. 그런데 `JsonNode` 로 받으면 **DTO 바인딩 시점에 Jackson 이 이미 전체를 파싱**한다.

```
실제 순서:  Jackson 이 body 전체 파싱  →  내 validate() 의 길이 체크
```

즉 **10MB 서명을 보내면 검증기에 닿기 전에 다 파싱된다.** 상한 검사가 막으려던 것을 막지 못했다.

> **단위 테스트가 이걸 못 잡은 이유**: `SignatureValidatorTest` 는 `validate()` 를 직접 호출하므로 순서가 지켜지는 것처럼 보인다. **DTO 바인딩 층이 테스트 범위 밖이었다.** 계약을 읽은 소비자가 "이 순서가 성립하려면 타입이 뭐여야 하나"를 역산해서 찾아낸 건이다.

**부수 효과**: `JsonNode.toString()` 은 재직렬화라 **모바일이 보낸 바이트가 그대로 저장된다는 보장이 없다**(구조 보존이지 바이트 보존이 아니다). §4.2 의 "무손실" 범위가 약해진다.

### 응답도 문자열로 — `@JsonRawValue` 제거

응답에는 `@JsonRawValue` 를 걸어 저장된 JSON 을 객체로 내보내고 있었다. 근거는 *"문자열로 이스케이프하면 모바일이 두 번 파싱한다"* 였는데, **모바일 코덱이 문자열 기반이라는 사실을 전제하지 않은 판단이었다.**

raw 로 내보내면 모바일은 이렇게 된다:

```
응답 JSON 파싱 → JsonElement → 다시 문자열로 인코딩 → SignatureCodec.decode()
                                ↑ 재직렬화 (키 순서·공백이 바뀔 수 있다)
```

**그 재인코딩이 정확히 §4.2 "무손실"이 깨지는 지점이다.** raw 로 막으려던 문제를 raw 가 만들고 있었다.

→ **요청·응답 모두 문자열.** 대칭이라 DB 에 들어간 바이트가 그대로 돌아오고, 모바일의 기존 코덱(18/18 통과)이 양방향에서 그대로 쓰인다.

### 🔴 계약 문서 정정이 필요하다 (pm-lead)

`api-contract.md` **§1/§2/§3 의 요청·응답 예시가 초안 그대로 남아 있다:**

```
§1/§2/§3 예시:  {"v":1,"strokes":[[[0.12,0.34],...]]}   ← 초안 (키 strokes, Float 중첩)
§4.1 (확정):    {"v":1,"g":1000,"s":[[123,456,...]]}     ← 정본
```

mobile-dev 지적: *"§4까지 안 내려간 사람은 §1 예시를 그대로 믿는다."* 계약이 `confirmed` 라 내가 임의로 못 고친다. **§1/§2/§3 예시를 §4.1 형식 + 문자열 필드로 정정하고 `change-log.md` 에 등재해달라.**

---

## T-B2b — 계약서 본문 문구 3건 (design-bridge 검토 → pm-lead 지시)

**톤은 유지했다** — 화면이 반말인데 계약서만 격식체인 건 의도다(*"화면은 앱이 나에게 말을 거는 것이고, 계약서는 문서다"*). `"서명한 맹세는 무를 수 없다."` 그대로.

### 1. 조사 병기 제거

```
before:  2026년 8월 3일, 도윤 와(과) 수아 은(는)      ← 병기 + 조사가 띄어져 나온다
after:   2026년 8월 3일, 도윤과 수아는
```

받침 판정은 `(code - 0xAC00) % 28 != 0`. **영문·이모지는 받침 없음으로 떨어뜨린다** — 영문 이름의 조사는 한글 발음을 따라 갈리는데(`Kim`→"과", `Sua`→"와") **표기만으로는 발음이 정해지지 않는다.** 서버가 추정하면 반드시 틀리는 경우가 생기므로 한쪽으로 고정하고, 병기로 되돌아가는 건 이 수정이 없애려던 그 문투다.

#### 🔴 후속 수정 — 숫자로 끝나는 닉네임 (mobile-dev 발견, 실서버 본문)

최초 구현은 숫자도 "비한글"로 묶어 받침 없음 처리했다. **틀렸다.**

```
before:  2026년 8월 3일, 테스터3와 테스터2는     ← 3=삼, 받침 ㅁ 이라 "테스터3과" 가 맞다
after:   2026년 8월 3일, 테스터3과 테스터2는
```

**숫자는 영문과 다르다 — 읽기가 하나로 정해져 있어 추정이 아니다.** 내가 "판정 불가"와 "판정 안 함"을 한 덩어리로 묶은 게 원인이다.

| 받침 있음 | 받침 없음 |
|---|---|
| 0(영/십) 1(일) 3(삼) 6(육) 7(칠) 8(팔) | 2(이) 4(사) 5(오) 9(구) |

여러 자리는 **마지막 자리가 읽기의 끝을 결정한다**(12→십`이`, 13→십`삼`). `0` 으로 끝나면 십/백/천/만 중 하나로 끝나는데 전부 받침이 있다.

`ContractContentTest` **+2건**(숫자 10종 전수 + 여러 자리 3건). **숫자로 끝나는 닉네임은 실사용에서 흔하다**(`우건1`, 테스트 계정 전부).

> ⚠️ **이미 박제된 계약서는 안 바뀐다** — `challenges id=18` 의 본문은 `테스터3와` 인 채로 남는다. 그게 박제의 정의이고, **소급되지 않기 때문에 지금 고치는 게 싸다**는 근거가 여기서 다시 확인됐다. 수정은 **다음 재기동부터** 새 계약서에 적용된다.

`· $nickname 의 미션` 의 띄어쓰기도 함께 고쳤다(`· 도윤의 미션`).

> ⚠️ **pm-lead 지시의 두 예시가 서로 달랐다** — `도윤과`(이 없음) vs `수현이와`(이 있음). 둘 다 받침이 있는데 처리가 갈린다. **문서체라는 판단에 따라 `이` 접미사 없이 통일**했다(`수현과 민준은`). 구어체 `이` 를 원하면 알려달라 — 그쪽으로 바꾸는 건 한 줄이다.

### 2. 🔴 완결 시 본문 **재렌더** — 상대 미션이 영구 공란이던 문제

```
before:  · 수아의 미션: (수락 시 기재)     ← 완성된 계약서에도 영영 이대로 남는다
```

**신청 시점에 한 번만 굳혔는데 상대 미션은 수락 시점에야 정해진다.** 계약서의 존재 이유가 "양측의 약속"인데 완성본에 한쪽이 비어 있었다.

→ **`is_finalized` 가 되는 시점에 본문을 다시 렌더하고, 그 뒤로 굳힌다.**

박제 원칙과 충돌하지 않는다. 박제의 취지는 *"나중에 템플릿을 바꿔도 이미 맺은 맹세가 소급해 바뀌면 안 된다"* 이지 *"미완성 스냅샷을 영원히 남기자"* 가 아니다. **박제 대상은 완성된 약속이어야 하고, 약속이 완성되는 시점이 `is_finalized` 다.** 내가 KDoc 에 쓴 근거("그 시점의 약속을 남기는 기록")를 그대로 따르면 오히려 재렌더가 맞다.

재렌더가 계약당 정확히 한 번만 도는 것은 **재서명 거부가 보장한다** — 그 경로가 막혀 있어 `accept` 가 두 번 성공할 수 없다. 테스트로 고정했다.

### 3. 마감 표기를 화면과 맞췄다

```
before:  · 마감: 8월 1일 00:00      ← deadline 을 그대로 포맷
after:   · 마감: 2026년 7월 31일 24:00
```

`KstDeadlineCalculator` 는 `challengeDate=07-31` 에 `deadline=08-01 00:00` 을 준다(같은 순간). 그대로 포맷하면 **계약서만 "8월 1일"** 이라고 적는다. 사용자는 화면에서 "오늘(7/31) 자정"으로 보고 서명했는데 계약서엔 다른 날짜가 있으니 *"어? 내일 마감이었나?"* 가 된다. design 이 화면에서 `24:00` 표기를 택한 이유가 정확히 이거라 계약서도 맞췄다.

**값이 아니라 표기만 바뀐다** — `deadline` 은 항상 `challengeDate + 1일 00:00` 이라 `challengeDate 24:00` 과 정확히 같은 순간이다. 그래서 `render` 가 `deadline` 을 인자로 받을 필요도 없어졌다.

---

## T-B3 — `GET /challenges/{id}` 상세

`ChallengeDetailService` + `ChallengeDetailResponse`.

### `challenger`/`opponent` 를 **역할 그대로** 준다 — "나/상대"로 뒤집지 않는다

홈 카드(`/challenges/active`)는 "내 시점"이 맞다. **상세는 계약서를 보여주는 화면이라 양쪽을 다 그린다.** `myMission`/`opponentMission` 으로 뒤집으면 **"이 서명이 누구 것인지"를 클라가 다시 계산**해야 한다.

> 같은 데이터라도 화면의 성격이 다르면 시점이 다르다. 프로젝트 일관성을 이유로 뒤집는 쪽으로 통일하면 계약서 화면이 손해를 본다.

### 서명은 **문자열**로 내보낸다 (`@JsonRawValue` 제거 — T-B2a)

요청과 대칭이어야 DB 에 들어간 바이트가 그대로 돌아온다. 근거는 T-B2a 참조.

### null 이 의미를 갖는 자리 3곳

| 필드 | null 의 뜻 |
|---|---|
| `contract` | 계약서가 아직 없다 |
| `challengerSignature` / `opponentSignature` | **미서명** — `PENDING` 구간의 정상 상태 |
| `opponent.mission` | 상대가 아직 수락 전 (V5 이후 `opponent_mission` nullable) |

권한은 **당사자만** — 계약서에는 양측의 미션·서명이 들어 있다.

## T-B4 — 테스트

### 결과: 전체 **216** / 실행 **171** / skip **45** / 실패 **0** / 에러 **0**  (직전 실행 134 → **+37**)

| 테스트 | 이전 | 지금 | 증감 |
|---|---|---|---|
| `SignatureValidatorTest` | — | **15** | **신규 +15** |
| `ContractContentTest` | — | **11** | **신규 +11** (T-B2b + 숫자 조사 2) |
| `ChallengeCommandServiceTest` | 39 | **50** | **+11** (soul-oath 8 + 재렌더 3) |
| `ChallengeCommandControllerTest` | 18 | 18 | 0 (회귀 0) |
| `GlobalExceptionHandlerTest` | 9 | 9 | 0 |
| `TestLoginIsolationTest` | 9 | 9 | 0 |
| `KstDeadlineCalculatorTest` / `WireDateTimeSerdeTest` / `FriendControllerTest` | 16 / 7 / 15 | 동일 | 0 |
| `AuthControllerTest` / `UserControllerTest` / `KstTimeTest` / `PhoneHasherTest` / `FriendServiceEscapeForLikeTest` / smoke | 5/2/4/3/6/1 | 동일 | 0 |

### 🔴 수락 로직 전환 — **회귀 0 / 의도적 교체 0**

pm-lead 요청: *"교체 5건을 '회귀 0 / 의도적 교체 N' 으로 분리 보고해라."*

**착수 전 내 추정은 교체 5건이었는데, 실제로는 0건이다.**

| 구분 | 건수 |
|---|---|
| 회귀 (의도치 않게 깨진 것) | **0** |
| **의도적 교체** (단언의 의미가 바뀌어 고친 것) | **0** |
| 기계적 인자 추가 (호출부만 `accept(...)` → `acceptSigned(...)`) | **7** |
| 신규 | **+37** |

> **T-B2a 정정으로 요청 본문 형태가 바뀌면서 테스트 body 15곳을 고쳤다.** 이것도 **의미 변경이 아니라 인코딩 변경**이다 — `"signature":{...}` → `"signature":"{\"v\":...}"`. 단언은 그대로다. 통합 테스트는 `SIGNATURE` 하나에서 `SIGNATURE_FIELD` 를 **파생**시켜 두 값이 어긋날 수 없게 했다.

**단언을 고친 줄이 한 줄도 없다.** 원인은 §0.3 결정이다 — 수락+서명이 원자 요청이라 **최종 상태가 여전히 `IN_PROGRESS`** 이므로 `assertEquals(IN_PROGRESS, accepted.status)` 같은 단언이 그대로 참이다. 바뀐 건 호출 인자뿐이라 `createSigned` / `acceptSigned` 헬퍼로 감쌌다.

> **`CONTRACT_SIGNING` 을 도입했다면 이 5건은 전부 의미가 바뀌었을 것이다.** "수락하면 진행 중이 된다"가 "수락하면 서명 대기가 된다"로 바뀌므로 단언 자체를 다시 써야 했다. **상태를 늘리지 않은 결정이 테스트에서 값으로 나타났다.**

### 신규 8건 — 취소와 거절을 **갈라서** 덮었다

pm-lead 지시("두 경로를 한 테스트에서 보면 나중에 누가 '일관성' 명목으로 합칠 수 있다")대로 별도 테스트다.

| 테스트 | 무엇을 막는가 |
|---|---|
| `생성하면 계약서가 함께 만들어지고 챌린저 서명만 채워진다` | `PENDING` 의 한쪽 서명 상태 |
| `수락하면 상대 서명이 채워지고 isFinalized 가 true 가 된다` | 완결 + `IN_PROGRESS` 동시성 |
| `서명은 저장 왕복에서 문자열이 그대로 보존된다` | 저장 단계 변형 |
| `빈 서명은 거부된다` | 문구까지 단언 (`"서명을 해주세요"`) + **거부된 요청이 챌린지를 만들지 않는지** |
| `점 1개짜리 획도 유효한 서명이다` | 과잉 거부 |
| **`취소하면 계약서도 함께 사라진다`** | **FK 위반 → HTTP 500**. 지금 `contracts` row 가 0이라 안 터지지만 이 feature 가 들어가면 **첫날부터** 터지는 자리 |
| **`거절해도 계약서는 보존된다`** | 취소와 같은 처리로 합쳐지는 것 |
| `이미 맹세를 마친 계약에는 재서명할 수 없다` | 2차 방어선 |

`SignatureValidatorTest` 15건은 유효 4 / 빈 서명 2 / 크기 2(**길이 검사가 파싱보다 먼저인지** 포함) / 구조 5 / 상수 1 / **최악값 대조 1**.

### 신규 12건 — 본문 문구 (T-B2b)

문구는 DB 에 **박제**돼 소급 수정이 안 된다. 그래서 문구 자체를 단언으로 고정했다.

`ContractContentTest` 9건 — 병기 부재 / 받침 판정 양방향 / 비한글 4종 / 소유격 띄어쓰기 / 자리표시 유무 2 / 마감 `24:00` / **머리말 날짜와 마감 날짜가 같은 날** / 격식체 유지.

`ChallengeCommandServiceTest` 재렌더 3건 — pm-lead 지시대로 세 단계를 각각 박았다:

| 테스트 | 단언 |
|---|---|
| `수락 전 본문에는 상대 미션이 자리표시로 남는다` | `(수락 시 기재)` 존재 |
| `완결 시 본문이 실제 상대 미션으로 재렌더된다` | 자리표시 **부재** + 양측 미션 실제값 |
| **`완결된 뒤에는 본문이 더 이상 바뀌지 않는다`** | 재서명 거부 후 `content` 가 바이트 동일 |

마지막 건이 **박제가 실제로 성립하는지**를 본다. 재렌더 경로가 계약당 한 번만 도는 것은 재서명 거부가 보장하는데, **그 보장이 깨지면 이 테스트가 잡는다.**

### 통합 테스트 요청 본문 수정

`ChallengeCreateIntegrationTest` 의 요청 body 5곳에 `signature` 를 넣고(1차), T-B2a 이후 문자열 형태로 다시 고쳤다(2차). **이 21건은 skip 상태라 고치지 않았어도 초록으로 보였고**, Docker 가 생기는 시점에야 깨졌을 것이다.

## 변경 파일

모두 `/Users/hwamulman/woogunProject/challenge/challenge-server/` 하위.

### 신규
```
app/src/main/resources/db/migration/V7__soul_oath_signature_data.sql
domain/model/src/main/kotlin/com/lwg/challenge/domain/contract/Contract.kt
domain/model/src/main/kotlin/com/lwg/challenge/domain/contract/SignatureValidator.kt
domain/repository/src/main/kotlin/com/lwg/challenge/domain/contract/ContractRepository.kt
infra/entity/src/main/kotlin/com/lwg/challenge/infra/entity/contract/ContractEntity.kt
infra/jpa/src/main/kotlin/com/lwg/challenge/infra/jpa/contract/ContractJpaRepository.kt
infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/contract/ContractRepositoryImpl.kt
service/src/main/kotlin/com/lwg/challenge/service/challenge/ChallengeDetailService.kt
service/src/main/kotlin/com/lwg/challenge/service/challenge/ContractContent.kt
controller/src/main/kotlin/com/lwg/challenge/controller/challenge/dto/ChallengeDetailResponse.kt
domain/model/src/test/kotlin/com/lwg/challenge/domain/contract/SignatureValidatorTest.kt
service/src/test/kotlin/com/lwg/challenge/service/challenge/ContractContentTest.kt
```
> `domain/model/src/test/` 는 **이 모듈의 첫 테스트 소스셋**이다.

### 수정
- `service/.../challenge/ChallengeCommandService.kt` — `contractRepository` 주입, `create`/`accept` 에 `signature`, contract 생성·**완결 시 본문 재렌더**·**취소 시 선삭제**
- `service/.../challenge/ContractContent.kt` — 조사 함수 신설, `opponentMission` 파라미터 추가, `deadline` 파라미터 **제거**(마감을 `challengeDate 24:00` 으로 표기)
- `controller/.../challenge/ChallengeCommandController.kt` — `GET /challenges/{id}` 추가, `signature` 전달
- `controller/.../challenge/dto/ChallengeCommandDtos.kt` — `signature: String?` 2곳 (`@NotNull`)
- `controller/.../challenge/dto/ChallengeDetailResponse.kt` — `@JsonRawValue` 제거
- 테스트 3종 (`ChallengeCommandServiceTest`, `ChallengeCommandControllerTest`, `ChallengeCreateIntegrationTest`) + smoke(`ContractJpaRepository` mock 추가)

## OpenAPI

- SpringDoc: `http://localhost:8080/swagger-ui.html` (재기동 후 반영)
- 신규 반영 경로: `GET /api/v1/challenges/{id}`
- 변경 반영: `POST /api/v1/challenges`, `POST /api/v1/challenges/{id}/accept` 의 `signature` 필드 + `example`

## ✅ 실서버 검증 — 완료 (2026-08-03 재기동 후, **56/56 PASS, 0 FAIL**)

`soul-oath.sh`, `SECOND=2`(pm-lead 승인).

| 구간 | 결과 |
|---|---|
| 0. V7 마이그레이션 (rename·주석·FK `ON DELETE` 부재) | 8/8 |
| 0-B. 사전 상태 + 로그인 | 1/1 |
| 1. 신청 + 챌린저 서명 + **TEXT 바이트 왕복** + 본문 4단언 | 11/11 |
| 2. 상세 조회 — **응답이 문자열 타입인지** | 7/7 |
| 3. 서명 검증 4종 + 문구 + **최악값 20,150자** | 11/11 |
| 4. 🔴 **취소 FK 경로** | 5/5 |
| 5. 미인증 | 2/2 |
| 6. 수락 + **완결 재렌더** + 재서명 거부 | 10/10 |
| 7. 사용자 데이터 무결성 | 1/1 |
| **합계** | **56/56 PASS, 0 FAIL** |

### 🔴 취소 FK — 첫날 터질 뻔한 500 이 안 터진다는 게 증명됐다

단위 테스트가 fake 라 **FK 제약 자체를 재현하지 못한다**고 리포트에 미리 적어둔 자리다. 실 DB 에서 `contracts` row 가 실제로 존재하는 상태로 취소를 눌렀다:

```
취소 전 contract 존재      ✅
DELETE /challenges/15  →  {"code":200,"error":false}     ← 500 아님
challenge 물리 삭제        ✅
contract 도 함께 삭제      ✅
```

### 🔴 바이트 왕복 — 요청·응답·DB 3자 동일

```
보낸 문자열   {"v":1,"g":1000,"s":[[123,456,130,460],[700,200,705,210]]}
DB 저장값     동일 ✅
응답 값       동일 ✅   + 타입이 str (객체 아님) ✅
최악값 20,150자도 DB 왕복 무손실 ✅
```

T-B2a 로 바뀐 직렬화 층은 단위 테스트가 안 덮는 구간이었다. **실서버에서 3자가 일치하는 것으로 §4.2 "무손실"이 wire 까지 성립함이 확인됐다.**

### 완결 재렌더 — 실 DB 에서 본문이 실제로 바뀐다

```
신청 시:  · 테스터2의 미션: (수락 시 기재)
수락 후:  · 테스터2의 미션: 책 30페이지 읽기
재서명 시도 → 705 → 본문 불변 ✅
```

조사(`테스터3와 테스터2는`)·마감(`2026년 8월 3일 24:00`) 표기도 실 DB 본문에서 확인됐다.

### 실행 중 발견한 것 — **둘 다 하네스 결함이지 서버 결함이 아니다**

1. **1차 `FAIL=10`** — 챌린지를 테스터1 앞으로 만들고 `SECOND=2`(테스터2)로 수락을 시도했다. 서버는 `700 내가 받은 도전장이 아니에요` 로 정확히 막았다 — **권한 가드가 정상 동작한 것**이다. `OPP` 를 `SECOND` 에서 파생시키도록 고쳤다.
2. **2차 `FAIL=1` — 컬럼 주석 개수 단언이 틀렸다.** 6 을 기대했으나 실제 7이다. **V7 이 다는 건 6건이지만 V6 이 이미 `contracts.created_at` 에 달아뒀다**(V6 의 `*_signed_at` 2건은 V7 이 soul-oath 문구로 덮었다). **내 변경분 개수를 세고 최종 상태를 안 본 것**이 원인이다 — `datetime-model-migration` 의 `:00Z` 오단언과 같은 실패 모드다.
   > 개수만 세는 단언은 이런 식으로 약하다. 그래서 **soul-oath 주석 6건을 이름으로 확인**하고 **서명 컬럼 주석에 저장 형식(`"v":1,"g":1000`)이 들어 있는지**까지 단언을 2건 추가했다(그래서 54 → 56).

### DB 조작 내역

- **삽입**: 테스터3↔테스터2 friendship 1행 (`RETURNING id` 로 받은 그 id 만 trap 이 삭제, 잔존 0)
- **API 로만 생성/삭제**: challenges·contracts·verifications
- **SQL 직접 삭제 1건** — 2차 실행이 남긴 `challenges id=14`(테스터3→테스터2, `IN_PROGRESS`). 3차 실행이 중복 가드에 걸려서 제거했다. **당사자 양쪽이 테스트 계정(999000xxx)일 때만 지우도록 조건을 걸었고**, 트랜잭션 안에서 확인 후 커밋했다.
- **사용자 데이터 불변 확인**: `users` 4명, `users id=1`(이우건) `created_at`/`updated_at` 검증 전후 동일, `friendships id=6`(1↔14) 그대로, **`challenges id=11`(이우건 실사용, 10:51 생성) 무변경**

### 🟢 남겨둔 것 — 모바일 실연동용

`challenges id=18` (테스터3 16 → 테스터2 15, `IN_PROGRESS`) + **양측 서명이 채워진 `is_finalized=true` 계약서 1건**. mobile-dev 가 상세 화면에서 **실제 서명 2개가 그려지는지** 확인할 수 있다. 서명 길이 58자씩, 완결 본문 렌더 완료 상태다.

## 🔴 미검증 (남은 것)

1. **통합 테스트 45건 여전히 skip** — 컨테이너 런타임 부재(백로그 등재). 위 56단언이 같은 층(Flyway·JPA 매핑·FK 제약·직렬화)을 수동으로 덮었으나 **CI 에서 반복되지 않는다는 한계는 그대로다.**
2. **🟡 모바일 실연동 미확인** — 서버 단독 검증은 끝났다. `challenges id=18` 에 양측 서명된 계약서를 남겨뒀으니 mobile-dev 가 상세 화면 렌더를 확인해야 한다.

### 해소된 것

- ~~**실서버 미검증**~~ — ✅ 위 56/56.
- ~~**`contracts.content` 문구를 디자인이 검토하지 않았다**~~ — ✅ design-bridge 검토 후 수정 3건 반영(T-B2b). 톤은 유지 결정.
- ~~**`api-contract.md` §1/§2/§3 예시가 초안 그대로다**~~ — ✅ pm-lead 가 정정 + 협의 이력 등재 완료. `signature` 가 객체가 아닌 이유도 §1 에 명시됐다.
  > 협의 이력의 최초 문구("코드 영향 없음")는 서버에 대해 사실이 아니었고, **지적 후 "동작이 바뀐 정정"으로 수정됐다.**

## 실서버 하네스 — `soul-oath.sh`

**안전 제약을 스크립트에 박았고 실행에서 지켜졌다:**
- `users` 에 DELETE/UPDATE/TRUNCATE **0줄**
- **테스터3 를 주 계정으로 쓴다.** 테스터2 로그인은 `SECOND=2` opt-in 일 때만 — pm-lead 가 `refresh_token_issued_at` 으로 활성 세션 없음을 확인하고 승인했다.
- 사용자 `friendships` 행은 읽지도 쓰지도 않는다. 필요한 friendship 이 없을 때만 삽입하고 **`RETURNING id` 로 받은 그 id 만** trap 이 정리한다(잔존 0 확인).
- challenges/contracts 는 **API 로만** 생성/삭제. 단 하나의 SQL 삭제(잔여 `id=14`)는 **양측이 테스트 계정일 때만** 지우도록 조건을 걸고 트랜잭션 안에서 확인 후 커밋했다.

> 하네스의 최악값 생성기는 Kotlin 테스트와 **독립적으로 다시 작성**했고 역시 20,150자가 나왔다 — 이 숫자는 서로 모르는 세 구현(모바일 실측 / Kotlin 테스트 / bash 하네스)에서 일치한다.

**재실행 시 주의**: 성공하면 `IN_PROGRESS` 챌린지가 1건 남고, 그 상태로 다시 돌리면 **중복 가드(`오늘은 이 친구와 이미 챌린지가 있어요`)에 걸려 §1 이후가 전부 실패한다.** 서버 정상 동작이니 잔여를 먼저 정리해야 한다.

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md) (`confirmed`) · [design.md](./design.md)
