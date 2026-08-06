# API Contract — 영혼의 맹세 (soul-oath)

- **feature-id**: soul-oath
- **상태**: confirmed
- **최종 수정**: 2026-08-03 by backend-dev (T-M1 실측 반영 — **오픈 이슈 0건**)
- **상위 spec**: [spec.md](./spec.md)

## 엔드포인트 요약

| # | Method | Path | 설명 | 인증 | 변경 |
|---|--------|------|------|------|------|
| 1 | POST | `/api/v1/challenges` | 챌린지 신청 **+ 챌린저 서명** | Bearer JWT | **필드 추가** |
| 2 | POST | `/api/v1/challenges/{id}/accept` | 수락 **+ 상대 서명** → `IN_PROGRESS` | Bearer JWT | **필드 추가** |
| 3 | GET | `/api/v1/challenges/{id}` | 챌린지 상세 + 계약서 + 양측 서명 | Bearer JWT | **신규** |

공통:
- ADR-0002 BaseResponse — 성공·비즈니스 에러는 HTTP 200 + body `code`.
- ADR-0010 시간 규약 — `yyyy-MM-dd HH:mm:ss` (KST). `T`·`Z`·offset·밀리초 없음.
- `challenge-create` 의 `GET /challenges/received`·`/active`·`DELETE /{id}` 는 **응답 shape 변경 없음.**

---

## 0. 핵심 결정 (확정)

### 0.1 서명은 **벡터 스트로크 데이터로 DB 에 저장**한다 — 파일 스토리지 미도입

- 서명은 손가락 획의 좌표 목록이다. 정규화 스트로크 배열을 JSON 으로 두면 수 KB 이고, 렌더는 Compose `Path` 로 그대로 그린다.
- **파일 스토리지 ADR·인프라·수명주기·CDN 을 전부 회피한다.** 이 feature 하나 때문에 인프라 축을 새로 세우지 않는다.
- 벡터라 어느 해상도에서도 깨지지 않는다.
- **파일 스토리지가 진짜 필요해지는 시점은 카메라 인증**(`verifications.photo_url`)이다. 사진은 벡터로 대체 불가다. 그때 ADR 을 쓰는 게 맞고, 서명을 이유로 앞당기지 않는다.

### 0.2 컬럼명 — `challenger_signature_data` / `opponent_signature_data`

기존 `*_signature_url` 에서 **rename** (V7 마이그레이션, `contracts` row 0 이라 데이터 이관 없음).

> **왜 `_strokes` 가 아니라 `_data` 인가** — `_url` 이 문제였던 이유는 **"저장 표현을 컬럼 이름에 박았다"** 는 것이다. `_strokes` 는 같은 실수를 다른 표현으로 반복한다. 표현이 바뀌어도 이름이 틀리지 않는 쪽을 고른다.
>
> **정확한 형식은 `COMMENT ON COLUMN` 에 적는다** (ADR-0010 의 17건 선례). 이름은 중립적으로, 형식은 검색 가능한 곳에.

### 0.3 🔴 `CONTRACT_SIGNING` 상태를 **도입하지 않는다** — 수락+서명은 단일 원자 요청

> ⚠️ **enum 값 자체는 V1 부터 존재한다. 제거하지 말고, 쓰지도 마라.** 이 절이 그 이유다.

**도입하면 "수락했지만 서명 전 이탈" 챌린지가 어느 목록에도 안 나온다:**
```
GET /challenges/received  →  status = 'PENDING'      만
GET /challenges/active    →  status = 'IN_PROGRESS'  만
```
`CONTRACT_SIGNING` 은 **양쪽 다 아니다.** 받은 도전장에서 사라지고 진행 중에도 없어 **재개할 경로가 없다.** `challenge-create` 에서 `GET /challenges/sent` 부재로 취소가 도달 불가였던 것과 **정확히 같은 구조**다 — 그때는 겪고 나서 알았고, 이번엔 들어가기 전에 막는다.

**대신 수락+서명을 한 요청으로 묶는다:**
- spec 시나리오 4(*"맹세 화면에서 이탈하면 챌린지는 진행되지 않는다"*)가 **자동으로 성립**한다 — 요청을 안 보냈으니 아무것도 안 바뀌고 `PENDING` 그대로, 받은 도전장 목록에 남아 있어 **다시 들어가면 재개된다.**
- 목록 필터·모바일 분기·기존 테스트가 그대로다.
- **`is_finalized` 는 contract 의 속성이지 challenge 의 상태가 아니다.** 이 구분이 결정의 핵심이다.

**상태를 하나 늘리면 그 상태에 갇힌 것을 꺼낼 경로가 함께 필요하다.** 그 경로를 설계할 계획이 없다면 상태를 늘리지 않는다.

### 0.4 🔴 취소 시 contract 를 **명시적으로 먼저 삭제**한다 (CASCADE 아님)

```
contracts_challenge_id_fkey : FOREIGN KEY (challenge_id) REFERENCES challenges(id)
                              ← ON DELETE 절 없음 (2026-08-03 실측)
```

`DELETE /challenges/{id}` 는 challenge 를 **물리 삭제**한다(challenge-create 스코프 결정 — `CANCELED` 상태를 안 만들기 위한 선택). 이 feature 는 **생성 시점에 contract row 를 만들므로**, 조치 없이는 **취소가 FK 위반 → HTTP 500** 이다. `contracts` row 가 0 인 지금은 안 터지지만 **이 feature 가 들어가는 첫날부터 터진다.**

**`ON DELETE CASCADE` 를 쓰지 않는 이유**: 이 제품의 컨셉은 **"무를 수 없는 약속"** 이다. CASCADE 는 **다른 이유로 challenge 를 지울 때도 맹세를 조용히 함께 지운다.** 물리 삭제 + 감사 추적 없음이라는 기존 선택 위에 암묵적 연쇄 삭제까지 얹으면 되돌릴 근거가 사라진다. 명시적 삭제는 **코드에 순서가 보인다.**

### 0.5 거절(`REJECTED`)은 contract 를 **보존**한다

spec 초안은 "거절·취소 시 정리"로 묶었으나 **둘은 다르다.** 거절은 challenge row 를 보존(`REJECTED`)하므로 **FK 문제가 없다.** 거절당한 맹세도 이력이므로 남긴다.

---

## 1. POST `/api/v1/challenges` — 신청 + 챌린저 서명

### Request Body (변경: `signature` 추가)
```json
{
  "opponentId": 42,
  "myMission": "오늘 운동 1시간 하기",
  "betContent": "커피 사기",
  "deadlineType": "TODAY",
  "signature": "{\"v\":1,\"g\":1000,\"s\":[[123,456,130,460],[700,200,705,210]]}"
}
```
> 🔴 **`signature`는 JSON 객체가 아니라 문자열이다** (2026-08-03 정정). §4.4의 검증 순서(**길이 1차 → 파싱 2차**)는 **필드가 문자열로 도착해야만 성립한다** — 객체로 바인딩하면 Jackson이 DTO 바인딩 시점에 이미 파싱을 끝내므로 상한이 막으려던 대용량이 검증기에 닿기 전에 파싱된다. 응답도 같은 이유로 문자열이다(§3 참조).

`challenges`(PENDING) + `contracts` 1건을 **한 트랜잭션**에서 생성한다. 챌린저 서명과 `challenger_signed_at` 만 채워지고 `is_finalized = false`.

### 성공 Response — 기존 shape 유지
```json
{ "error": false, "code": 200, "message": "",
  "data": { "challengeId": 7, "status": "PENDING",
            "challengeDate": "2026-08-03", "deadline": "2026-08-04 00:00:00" } }
```
> 계약 정보를 응답에 넣지 않는다 — 생성 직후 클라가 필요로 하지 않고, 필요하면 상세 조회(§3)를 쓴다.

### 에러 (기존 + 신규)
| code | 상황 | message |
|---|---|---|
| 700 | 빈 서명 (획 0개 또는 모든 획의 점 0개) | `서명을 해주세요` |
| 700 | 서명 데이터 상한 초과 | `서명 데이터가 너무 큽니다` |
| 700 | 기존 검증 5종 | challenge-create 계약 그대로 |

---

## 2. POST `/api/v1/challenges/{id}/accept` — 수락 + 상대 서명

### Request Body (변경: `signature` 추가)
```json
{ "myMission": "책 30페이지 읽기",
  "signature": "{\"v\":1,\"g\":1000,\"s\":[[100,300,120,330]]}" }
```

**한 트랜잭션**에서 전부 일어난다:
1. `contracts` — 상대 서명 + `opponent_signed_at` + **`is_finalized = true`**
2. `challenges` — `status = IN_PROGRESS`, `opponent_mission`
3. `verifications` — PENDING row 2건

**`is_finalized = true` 가 된 시점에만 `IN_PROGRESS` 로 전환된다** (spec 수용 기준). 원자 요청이므로 이 둘은 항상 함께 일어난다.

### 성공 Response — 기존 shape 유지
```json
{ "error": false, "code": 200, "message": "", "data": { "challengeId": 7, "status": "IN_PROGRESS" } }
```

### 에러
| code | 상황 | message |
|---|---|---|
| 700 | 빈 서명 / 상한 초과 | §1 과 동일 |
| **705** | **이미 맹세를 마친 계약에 재서명** | `이미 맹세를 마친 챌린지예요` |
| 705 | 이미 처리됨 / 마감 경과 / 없음 | challenge-create 그대로 |
| 700 | 당사자 아님 | `내가 받은 도전장이 아니에요` |

> 재서명은 기존 상태 가드(`status != PENDING → 705`)가 대부분 막는다. contract 레벨(`is_finalized`) 가드는 **2차 방어선**이다.

---

## 3. GET `/api/v1/challenges/{id}` — 상세 (신규)

```json
{ "error": false, "code": 200, "message": "",
  "data": {
    "challengeId": 7, "status": "IN_PROGRESS",
    "challengeDate": "2026-08-03", "deadline": "2026-08-04 00:00:00",
    "betContent": "커피 사기",
    "challenger": { "userId": 1, "nickname": "이우건", "profileImageUrl": null, "mission": "운동 1시간" },
    "opponent":   { "userId": 14, "nickname": "테스터1", "profileImageUrl": null, "mission": "책 30페이지" },
    "contract": {
      "content": "...",
      "isFinalized": true,
      "challengerSignature": "{\"v\":1,\"g\":1000,\"s\":[[123,456,130,460]]}",
      "challengerSignedAt": "2026-08-03 11:20:00",
      "opponentSignature":  "{\"v\":1,\"g\":1000,\"s\":[[700,200,705,210]]}",
      "opponentSignedAt":   "2026-08-03 11:25:00"
    } } }
```

**`challenger`/`opponent` 를 역할 그대로 준다 — "나/상대" 로 뒤집지 않는다.**
> 상세는 **계약서를 보여주는 화면**이라 양쪽을 다 그린다. `myMission`/`opponentMission` 으로 뒤집어 주면 "이 서명이 누구 것인지" 를 클라가 다시 계산해야 한다. 홈 카드(`/challenges/active`)는 "내 시점" 이 맞지만 계약서는 아니다.

- 당사자(challenger 또는 opponent)가 아니면 **700** `내 챌린지가 아니에요`.
- 없는 id 는 **705** `챌린지를 찾을 수 없어요`.

### 🔴 3.1 nullable 필드 — **전수 표** (2026-08-06 신설)

**이 표에 없는 필드는 절대 `null` 이 아니다. 있는 필드는 반드시 `null` 을 받을 수 있어야 한다.**

| 필드 | `null` 의 의미 | 언제 발생하나 | 지금 도달 가능? |
|---|---|---|---|
| `contract` | **이 챌린지에는 계약서가 없다** (맹세 개념 이전에 생성) | soul-oath 배포(2026-08-03 13:31) **이전에 만들어진 챌린지** | 레거시 1건(`id=11`)만. **신규는 구조적으로 불가** |
| `contract.challengerSignature` / `challengerSignedAt` | 챌린저 미서명 | 실제로는 안 나온다(생성 시 항상 채워짐). 타입상 허용 | ❌ |
| `contract.opponentSignature` / `opponentSignedAt` | **상대 미서명** | `PENDING` 구간 — 정상 상태 | ✅ 흔함 |
| `challenger.mission` | — | 실제로는 안 나온다(생성 시 필수) | ❌ |
| `opponent.mission` | **상대가 아직 수락 전** | `PENDING` 구간 (V5 이후 `opponent_mission` nullable) | ✅ 흔함 |
| `challenger.profileImageUrl` / `opponent.profileImageUrl` | 카카오 프로필 이미지 없음 | 계정에 따라 | ✅ **흔함** (테스트 계정 3개 전부 `NULL` — 실측) |

#### 절대 `null` 이 아닌 필드 — **확정 보증**

위 표의 여집합이지만, 방어 코드를 넣을지 말지 갈리는 자리라 **명시적으로 보증한다.**

| 필드 | 보증 |
|---|---|
| `challengeId` / `status` / `betContent` | 항상 값이 있다 |
| **`challengeDate`** | 항상 `yyyy-MM-dd` 문자열 |
| **`deadline`** | 항상 `yyyy-MM-dd HH:mm:ss` (KST). **`null` 을 보내지 않는다** |
| `challenger.userId` / `nickname`, `opponent.userId` / `nickname` | 항상 값이 있다 |
| `contract.content` / `contract.isFinalized` | `contract` 가 `null` 이 아닌 한 항상 값이 있다 |

> `contract.content` 는 `contract` 안에 있으므로 **`contract` 자체의 `null` 검사만 통과하면 안전하다.** 이중 검사가 필요 없다.

##### 🔴 이 보증의 범위 — **"서버가 안 보낸다"이지 "클라가 항상 파싱한다"가 아니다**

`deadline` 을 두고 확인하다 나온 구분이라 남긴다. 내가 처음에 *"상세 매퍼의 `deadline == null` 방어는 여기선 발동하지 않는다"* 고 적었는데 **틀렸다** (2026-08-06 mobile-dev 정정).

모바일 `WireLocalDateTimeSerializer` 는 **파싱 실패도 `null` 로 흡수**한다:
```
JSON null → null   /   문자열 아님 → null   /   🔴 포맷 파싱 실패 → null
```
즉 서버가 `null` 을 안 보내도 **포맷이 어긋난 문자열**을 보내면 클라에는 똑같이 `null` 로 도착한다. **위 표는 "서버가 `null` 을 보내지 않는다"를 보증하지, "클라 쪽 `null` 분기가 죽는다"를 보증하지 않는다.**

→ **non-null 보증을 근거로 클라의 `null` 방어를 지우면 안 된다.** 보증이 없애주는 것은 *"서버가 빈 값을 줄까 봐"* 하는 방어뿐이고, **역직렬화 실패 경로는 그대로 남는다.**

##### `contract: null` 과 `deadline` 파싱 실패를 다르게 처리하는 이유

둘 다 클라에는 `null` 로 보이지만 뜻이 반대다 (mobile-dev 정리):

| | 뜻 | 처리 |
|---|---|---|
| `contract: null` | **맹세가 존재하지 않는다** | 사실이므로 그대로 보여준다 — 카드 그리고 서명 블록만 생략 |
| `deadline` 파싱 실패 | **마감은 존재하는데 못 읽었다** | 조건 하나가 빠진 계약서를 계약서라고 내놓게 된다 → 전체 실패 |

**전자는 없는 걸 없다고 말하는 것이고, 후자는 있는 걸 없는 것처럼 보이게 하는 것이다.** §4.6("존재할 수 없는 것은 행 자체를 뺀다")이 전자에만 적용되는 이유도 같다.

#### 이 표가 왜 생겼나 — 같은 버그가 두 번 났다

`opponent.mission` 과 `contract` 가 **정확히 같은 실패 모드**로 모바일을 깨뜨렸다(non-nullable 필드에 명시적 `null` → `JsonConvertException`). 우연이 아니라 **계약이 nullable 을 산문으로 적고 일부를 빠뜨린 결과**다 — 개정 전 §3 에는 `*Signature`/`*SignedAt` 한 줄만 있었고, 서버 DTO 는 그때도 이미 `contract`·`opponent.mission`·`profileImageUrl` 을 nullable 로 갖고 있었다.

**산문 대신 표를 쓰는 이유는 빠뜨린 게 눈에 띄기 때문이다.**

#### 🔴 `contract: null` 을 백필로 없애지 않는 이유

"신규는 도달 불가면 레거시 1건을 채우고 non-nullable 로 만들면 되지 않나" — **안 된다. 세 방법 전부 다른 걸 깨뜨린다.**

| 백필 방식 | 깨지는 것 |
|---|---|
| 서명을 만들어 넣는다 | **없던 맹세를 날조한다.** "무를 수 없는 약속" 이 컨셉인 제품에서 최악의 조작이다 |
| 서명 `null` + `is_finalized=false` | `id=11` 은 `IN_PROGRESS` 다 → **"`is_finalized=true` 인 시점에만 `IN_PROGRESS`"** 불변식의 **첫 위반**이 된다 |
| 서명 `null` + `is_finalized=true` | 자기모순 (완결인데 서명이 없다) |

**레거시 row 는 맹세라는 개념 자체보다 먼저 만들어졌다. 어떤 값을 넣어도 거짓이 되므로 `null` 이 유일하게 참인 값이다.**

#### 테스트 파생 규칙

**이 표에서 파싱 테스트를 파생시킨다 — 라이브 응답 샘플링이 아니라 표가 출처다.**

라이브 응답 픽스처는 **"지금 존재하는 것"** 을 검증하지 **"계약이 허용하는 것"** 을 검증하지 못한다. 실제로 mobile-dev 의 wire 픽스처는 `GET /challenges/18`(모든 필드가 찬 응답)에서 떠서 `contract: null` 을 **구조적으로 못 덮었고**, 서버는 이 엔드포인트에 테스트가 **0건**이었다.

**null 최대 픽스처** — 모든 nullable 이 동시에 `null` 인 응답. 실서버로는 만들 수 없는 조합이라 **서버 슬라이스 테스트가 실제 직렬화기로 생성**한다(`ChallengeDetailControllerTest`):
```json
{"data":{"challengeId":7,"status":"IN_PROGRESS","challengeDate":"2026-08-03","deadline":"2026-08-04 00:00:00","betContent":"커피 사기","challenger":{"userId":1,"nickname":"이우건","profileImageUrl":null,"mission":null},"opponent":{"userId":14,"nickname":"테스터1","profileImageUrl":null,"mission":null},"contract":null},"error":false,"code":200,"message":""}
```

> ⚠️ **"키 없음" 과 "키가 null" 은 다른 실패다.** kotlinx.serialization 기준 전자는 `MissingFieldException`(기본값 없을 때), 후자는 `JsonConvertException`(필드가 non-nullable 일 때). 서버는 **키를 포함하고 값을 `null`** 로 보낸다. 누군가 `@JsonInclude(NON_NULL)` 을 켜면 키가 사라져 모바일 실패 모드가 조용히 바뀌므로, 서버 테스트가 **원문에 `"contract":null` 이 있는지**까지 확인한다.

---

## 4. 서명 데이터 규약 (확정 — mobile-dev T-M1 **실측** 기반)

> 검증: `SignatureCodecTest` **18/18** + `SignatureTest` **4/4** passed, 기존 mapper 14건 회귀 0.

### 4.1 저장 포맷

```json
{"v":1,"g":1000,"s":[[123,456,130,460],[700,200,705,210]]}
```

| 키 | 의미 |
|---|---|
| `v` | 포맷 버전. 현재 **1**. 알 수 없는 버전은 **양측 모두 거부** |
| `g` | 인코딩 당시 그리드 해상도. 현재 **1000** |
| `s` | 획 배열. **각 획은 `x,y` 가 번갈아 나오는 평탄 Int 배열** |

- 좌표는 **0..g 범위의 정수**. 정규화 좌표를 양자화한 값이라 **어느 해상도에서도 렌더**된다(맹세 화면의 작은 서명란 ↔ 상세 화면의 큰 렌더).
- **평탄 배열**을 쓴 이유: `[[x,y],...]` 대비 점당 2바이트 절약(800점이면 1.6KB). 대가로 **디코드 시 길이 짝수 검증이 필수**다.
- **`g` 를 함께 저장하는 이유**: 나중에 그리드 해상도를 바꿔도 **기존 데이터가 그대로 읽힌다.** 디코더가 하드코딩 상수에 의존하지 않는다.

> 초안은 `[[x,y],...]` Float 정규화였다. **실측 결과 평탄 Int 배열이 낫다** — 크기가 작고, 무손실 주장이 부동소수 표현에 의존하지 않는다.

### 4.2 🔴 "무손실" 의 정확한 범위

**원본 손가락 입력에 대한 무손실이 아니다.**

```
손가락 px → 정규화(0..1 Float) → 양자화(0..1000 Int)   ← 손실은 여기 한 번뿐
                                        ↓
                            encode ↔ decode              ← 전단사, 무손실 (테스트 고정)
```

spec 수용 기준 *"저장·조회 왕복에서 동일하게 렌더된다"* 는 **이 의미에서 엄밀히 성립한다.**
`Float` 를 JSON 에 그대로 쓰지 않은 이유가 이것이다 — 크기가 3~4배 늘고 **무손실 주장이 부동소수 표현에 의존**하게 된다.

### 4.3 크기 상한 — **실측값**

| 항목 | 값 | 근거 |
|---|---|---|
| `MAX_POINTS` | **2,000** | 모바일 캡처 상한 |
| `MAX_STROKES` | **64** | 모바일 캡처 상한 |
| 최악값 실제 인코딩 길이 | **20,150자** | 최악 서명을 실제로 만들어 측정 |
| **서버 검증 상한** | **32 KB** | 20.2KB + 여유 |

**서버는 문자열 길이 32KB 하나로 검증한다.** 점 개수를 세려면 파싱이 필요한데 **길이 체크가 먼저 걸러준다** — 악의적 대용량은 파싱 전에 막는 게 맞다.

> 초안은 점 10,000 + 64KB 였다. **실측값(2,000 / 32KB)이 더 타이트하므로 그쪽을 채택한다.**
> **양측이 공유하는 상수만 값이 같아야 한다** — `MAX_SIGNATURE_LENGTH`(32KB) / `FORMAT_VERSION`(1). 모바일 `SignatureLimits` ↔ 서버 `SignatureLimits`.
>
> 🔴 **캡처 상한(`MAX_POINTS` 2000 / `MAX_STROKES` 64)은 모바일만 갖는다.** 서버가 복제하면 **한쪽만 바뀔 때 조용히 어긋난다.** 그리고 서버가 점 개수를 세려면 파싱이 필요한데 **길이 체크(§4.4 1차)가 먼저 걸러주므로** 이득 없이 숫자 중복만 남는다. `g=1000` 고정으로 좌표가 최대 4자리라 **바이트 길이가 점 개수를 이미 구속한다** — 축 하나가 다른 축을 종속시킨다.

### 4.4 서버 검증 규칙 (쓰기 시점에만)

1. **문자열 길이 ≤ 32 KB**
2. **파싱 가능** + `v == 1` + `g > 0` + **모든 획 길이 짝수**
3. **빈 서명 거부** — `s` 가 비었거나 **모든 획의 점이 0개**

**`v == 1` 을 고정하는 이유**: 서버의 구조 검증(평탄 배열·짝수 길이)은 **v1 전용 규칙**이다. 버전이 바뀌면 검증도 바뀌어야 하므로, 고정하지 않으면 **v2 데이터에 v1 규칙을 조용히 적용**하게 된다. 버전 상향은 양측 동시 배포가 필요하다는 뜻이며, 그게 의도다.

**서버는 서명을 파싱해 렌더하지 않는다** — 구조 검증 후 문자열 그대로 저장한다.

### 4.5 점 1개짜리 획(탭)은 **유효**로 본다

`s` 가 비었거나 모든 획의 점이 0개일 때만 빈 서명이다. **점 1개(탭 한 번)는 "비어 있지 않음"으로 친다.**

> **더 엄격한 하한(최소 점 개수)을 두지 않는 이유**: spec 수용 기준은 *"빈 서명(획 0개)은 거부된다"* 까지다. 최소 점 개수를 서버가 발명하면 **짧게 서명하는 사람을 오거부**할 수 있고, 그 임계값에 근거가 없다. 클라이언트 CTA 활성 조건도 같은 규칙(≥1점)을 쓴다 — **양측이 같아야 클라 통과 → 서버 거부가 안 생긴다.**
>
> 탭 한 번이 사실상 안 보이는 점으로 렌더되는 것은 UX 판단 영역이며, 필요하면 design 에서 다룬다.

### 4.6 디코드 실패 정책 — 모바일

`decode` 는 예외가 아니라 **`null`** 을 반환한다(`datetime-model-migration` 의 파싱 실패 정책과 일관).

실패 조건: 잘못된 JSON / 홀수 길이 획 / `g <= 0` / 알 수 없는 `v` / 필수 필드 누락.

**의도적으로 실패로 보지 않는 것 2가지 — 서버도 같은 원칙을 따른다:**

1. **크기 상한 초과** — 상한은 **쓰기 시점 입력 검증 규칙**이지, 이미 저장된 데이터를 못 읽게 만들 이유가 아니다. **서버도 읽기 경로에서는 크기를 검사하지 않는다.**
2. **범위를 벗어난 좌표** — `null` 대신 `0..g` 로 클램프한다. **점 하나 때문에 계약서 전체가 안 보이는 것보다 낫다.**

### 4.7 컬럼 주석

V7 에서 `*_signature_data` 컬럼에 위 포맷 예시를 `COMMENT ON COLUMN` 으로 남긴다 (ADR-0010 의 17건 선례). 이름은 중립적으로, **형식은 DB 에서 검색 가능한 곳에.**

## 협의 이력

| 일시 | 작성자 | 변경 |
|------|-------|------|
| 2026-08-03 | backend-dev | 초안 작성 + 서버 스키마·코드 실측. **spec 에 없던 결함 2건 제기** — (1) `contracts` FK 에 `ON DELETE` 가 없어 **취소가 FK 위반 → 500**, (2) `CONTRACT_SIGNING` 도입 시 "수락 후 서명 전 이탈" 챌린지가 `/received`·`/active` 어디에도 안 나와 **재개 경로가 사라진다**(challenge-create `/sent` 부재와 동형). 컬럼명 `_signature_data` 제안 (상태: `draft` → `negotiating`) |
| 2026-08-03 | mobile-dev | **T-M1 실측 완료** (`SignatureCodecTest` 18/18 + `SignatureTest` 4/4, 회귀 0). 포맷을 `{"v","g","s"}` **평탄 Int 배열**로 확정 — 초안의 `[[x,y],...]` Float 대비 크기 절감 + **무손실 주장이 부동소수에 의존하지 않음**. `g`(그리드 해상도) 동봉으로 해상도 변경 시 기존 데이터 호환. **"무손실"의 범위를 정밀화** — 손실은 캡처 시 양자화 1회뿐이고 encode↔decode 는 전단사. 상한 **실측**(MAX_POINTS 2000 / MAX_STROKES 64 / 최악 20,150자 → **32KB 권고**). 디코드 실패 정책 2건 제기(상한 초과·범위 밖 좌표를 실패로 보지 않음) |
| 2026-08-03 | backend-dev | T-M1 실측 전량 채택 — **초안(10,000점/64KB)보다 타이트한 실측값(2,000/32KB)을 따름**. 서버 검증을 **길이 1차 → 파싱 2차** 순으로 확정(악의적 대용량을 파싱 전에 차단). `v==1` 고정 근거 명시(구조 검증이 v1 전용이라 고정 안 하면 **v2 에 v1 규칙을 조용히 적용**하게 된다). **점 1개 획은 유효**로 확정 — 최소 점 개수를 서버가 발명하면 짧은 서명을 오거부하고 임계값에 근거가 없다. 디코드 실패 정책 2건 승인 + **서버도 읽기 경로에서 크기를 검사하지 않는다**로 대칭 확장. **오픈 이슈 0건 — `negotiating` → `confirmed`** |
| 2026-08-03 | pm-lead | **발견 2건 재현 후 전량 승인.** 명시적 삭제 채택(CASCADE 기각 — "무를 수 없는 약속" 컨셉 + 기존 물리삭제가 이미 감사추적을 포기한 맥락), 거절/취소 구분 승인(거절은 contract **보존**), **`CONTRACT_SIGNING` 미도입 + 원자 요청 확정**(enum 값은 제거하지 말고 쓰지도 말 것), `_signature_data` 승인. spec 에 확정 반영 |
| 2026-08-03 | pm-lead | 🔴 **`confirmed` 후 정정 — §1/§2/§3 예시가 초안 포맷(`{"v","strokes"}` 객체 + Float 중첩)으로 남아 §4.1 정본(`{"v","g","s"}` 평탄 Int, **문자열**)과 한 문서 안에서 충돌했다.** mobile-dev 제기 — *"§4까지 안 내려간 사람은 §1을 그대로 믿는다"*. 세 예시를 정본으로 통일하고, **`signature`가 객체가 아니라 문자열인 이유**(§4.4 길이→파싱 순서는 문자열 도착이 전제)를 §1에 명시. **모바일은 정본을 따르고 있었으나 서버는 아니었다** — `signature`를 `JsonNode`(객체)로 받고 있어 **32KB 상한이 파싱 앞에서 막지 못했다.** 문서 정리가 아니라 **동작이 바뀐 정정**이다. 실제 변경: DTO 2곳 `JsonNode?`→`String?` / 응답 `@JsonRawValue` **제거** 3곳 (raw로 주면 모바일이 `JsonElement`→문자열 재인코딩을 타 무손실이 깨진다 — raw로 막으려던 문제를 raw가 만들고 있었다) / 컨트롤러 2곳 / 테스트 body 15곳 인코딩 변경(단언 불변) |
| 2026-08-06 | mobile-dev → backend-dev | **§3.1 non-null 보증의 범위 정정.** backend-dev 가 *"상세 매퍼의 `deadline == null` 방어는 여기선 발동하지 않는다"* 고 적은 것이 **틀렸다** — 모바일 `WireLocalDateTimeSerializer` 가 **포맷 파싱 실패도 `null` 로 흡수**하므로, 서버가 `null` 을 안 보내도 **어긋난 포맷 문자열**은 클라에 `null` 로 도착한다. **non-null 보증은 "서버가 안 보낸다"이지 "클라가 항상 파싱한다"가 아니다** — 보증을 근거로 클라 `null` 방어를 지우면 안 된다. `contract:null`(없는 걸 없다고 함 → 그대로 표시)과 `deadline` 파싱 실패(있는 걸 없는 것처럼 보이게 함 → 전체 실패)를 다르게 처리하는 근거도 함께 명시 |
| 2026-08-06 | backend-dev ↔ mobile-dev | **#24 합의 완료.** `contract:null` = **정상 상태**(백필 3안이 전부 다른 걸 깨뜨림 — 서명 날조 / `is_finalized` 불변식 첫 위반 / 자기모순). 레거시 행 **삭제도 기각** — 지워도 API nullable 여부라는 질문이 남고, 구조적 불가능을 만드는 건 삭제가 아니라 **단일 INSERT 경로 + 같은 트랜잭션**이다. 화면 처리는 **카드는 그리고 서명 블록만 생략**(mobile-dev 제3안) — backend-dev 의 "섹션 감추기" 안은 상세 화면이 `ContractCard` 하나뿐이라 **백지가 되므로 기각**됐다. `id=11` 최상위 필드 전부 정상임을 DB 로 확인(레거시에 없는 건 나중에 붙은 층뿐). §3.1 에 **non-nullable 확정 보증** 절 추가 — 특히 **`deadline` 은 이 엔드포인트에서 null 이 될 수 없다** |
| 2026-08-06 | backend-dev | 🔴 **`confirmed` 후 정정 — §3.1 nullable 전수 표 신설.** 사용자 실기에서 `GET /challenges/11` 의 `contract:null` 이 모바일 상세 화면을 깨뜨렸다(#24). **`opponent.mission` 건과 같은 실패 모드**이며, 원인은 §3 이 nullable 을 산문으로 적고 `contract`·`opponent.mission`·`profileImageUrl` 을 빠뜨린 것이다(서버 DTO 는 그때도 nullable 이었다). **`contract:null` 을 정상 상태로 확정** — 백필 세 방법이 전부 다른 걸 깨뜨린다(서명 날조 / `is_finalized` 불변식 위반 / 자기모순). 표에서 파싱 테스트를 파생시키는 규칙 + null 최대 픽스처 추가. 서버는 `GET /challenges/{id}` 테스트가 **0건**이었고 `ChallengeDetailControllerTest` 8건 신설 |
