# AI 인증 판별 (ai-verification) — Summary

- **feature-id**: ai-verification
- **완료일**: 2026-09-22
- **상태**: **implemented** — 전 범위 구현·검증 완료. 🔴 **기능은 아직 켜지지 않았다**(키 미주입) + **양 레포 미커밋** + **반려 화면 실기 0회**

## 무엇이 달라졌나

**이 앱의 승리 조건에 처음으로 내용이 생겼다.** 이전까지는 *"인증 이미지가 있느냐 없느냐"* 뿐이라
**아무 사진이나 올려도 `VERIFIED`** 였고 자정 배치가 그것을 그대로 읽어 승패를 냈다. 이제 자정
배치 앞단에서 **외부 VLM(Gemini)이 사진을 미션과 대조**하고, 미인증 확정 건은 `FAILED` 가 되어
승패에서 빠지며 **사용자는 반려 사유를 화면에서 읽는다.**

🔑 **판정 주체는 분리했다.** AI 는 **사진 1장의 pass/fail 만** 답하고 **승패는 기존
`ChallengeVerdict` 가 낸다** — `ChallengeVerdict`·`judge()` 변경 **0줄**. AI 에게 *"누가 이겼어"* 를
물으면 승패 규칙(무승부·`BOTH_LOSE`·기권)의 **사본이 프롬프트 안에 생기고**, 규칙이 바뀌는 날
아무것도 실패하지 않은 채 틀린 승패가 나간다 ([ADR-0013](../../decisions/0013-ai-verification-provider.md) §근거 2).

🔴 **단 키 주입 전까지는 `NoOpMissionVerifier` 가 선택되어 이 feature 이전과 정확히 동일하게
동작한다** — **코드 완성 ≠ 기능 점화.**

## 엔드포인트

**새 엔드포인트 0개.** 기존 `confirmed` 계약 1건 **개정**:

| Method | Path | 변경 | 상태 |
|---|---|---|---|
| GET | `/api/v1/challenges/{id}/verifications` | `aiReason: String?` **1필드 추가** | **implemented** |

- 🔴 **wire 게이트가 계약이다** — `aiReason` 은 **미인증 확정 건에만** non-null. 컬럼(rubric 튜닝용
  전건 저장)과 wire(사용자 화면)는 다르다. 정본 [challenge-verification §4.1](../challenge-verification/api-contract.md)
- 🔵 `aiVerdict` / `aiConfidence` 는 **내리지 않는다** — 신뢰도 숫자를 노출하면 사용자가 그 값을 두고 다툰다
- 🔵 `SubmitVerificationResponse` · `ActiveChallengeResponse` **무변경** (판정 결과 화면이 `Challenge.Detail` 하나뿐임을 mobile 이 실측)

## 화면 / UI 변경

- **챌린지 상세 — 반려 카드**: `FAILED` + **사진** + 사유(*"인증이 인정되지 않았어요: {aiReason}"*)
- 🔑 **작업의 무게는 `aiReason` 배관이 아니라 `FAILED` 게이트 해제였다.** 이 feature 가 프로젝트
  최초로 **`FAILED` 인데 사진이 있는 row** 를 만들었고, 앱 3곳 · 서버 3곳이 *"`FAILED` 면 사진이
  없다"* 를 암묵 전제하고 있었다. 그대로 두면 **사용자가 올린 사진이 사라진 채 "인증하지
  못했어요" 만 뜬다** — 사진을 냈는데 못 했다고 하면서 그 사진을 감추는 화면이다
- 🔵 **기존 데이터 동작 변화 0** — 여태 `FAILED` 는 `photoUrl == null` 뿐이었다
- **디자인 산출물 0건** (Lovable 에 반려 화면 부재 — design-bridge 제외 확정). 디자이너 확인 6건 등재

## 주요 변경 파일

**백엔드** (21파일)
- `db/migration/V13__verification_ai_verdict.sql` — 판정 로그 4컬럼
- `db/migration/V14__verification_verified_at_recomment.sql` — **주석 전용** (DDL·DML 0줄)
- `domain/verification/MissionVerdict.kt` · `MissionVerifier.kt` · `Verification.kt`(`rejectedByAi()`)
- `infra/external/gemini/` — `GeminiMissionVerifier` · `NoOpMissionVerifier` · `MissionVerifierConfig`
- `service/verification/MissionVerificationRunner.kt` · `MissionVerdictRecorder.kt` · `VerificationService.kt`(wire 게이트 + 사진 조건 3곳)
- `service/challenge/ChallengeJudgementRunner.kt` — `aiFailOpen` 카운터

**모바일** (12 수정 + 1 신규, +536/-35)
- `remote/model/.../ChallengeVerificationsResponse.kt` → `domain/.../ChallengeVerifications.kt` → `remote/mapper/.../VerificationMappers.kt` → `ChallengeDetailState.kt` (배관)
- `feature/challenge/detail/.../component/VerificationPhoto.kt` — 🔴 **소거형 게이트** 재배열
- `.../contract/ChallengeDetailState.kt` — `FAILED -> NONE` 을 사진 유무로 가름
- `core/ui/.../VerificationStatusPill.kt`

## 테스트 결과

**전부 pm 이 XML 직접 집계로 독립 검증했다.**

| | 결과 |
|---|---|
| **백엔드** | **657/707 passed** (신규 **52**) · failures 0 · errors 0 · skip 50(컨테이너 런타임 부재, 기존 blocker) |
| **모바일 Android** | **283/283** (`:remote:mapper` 140 · `:feature:challenge:detail` 75 · `:remote:datasource` 41 · `:feature:home` 27) |
| **모바일 iOS** | **242/242** (`:remote:datasource` 는 iOS XML 디렉터리 부재 — 기존 백로그 항목) |
| 회귀 | **0** — 추가 11건과 증감이 정확히 일치 (mapper 135→140, detail 69→75) |
| 빌드 | Android `composeApp-debug.apk` 생성 · iOS framework 링크 `BUILD SUCCESSFUL` |
| 서버 실기동 | **5회** (throwaway DB 4개 · 포트 18080~18083). 공용 `challenge` DB·`:8080` 불가침, 전부 정리 |

⚠️ **variant 를 갈라야 맞는 숫자가 나온다** — `testReleaseUnitTest` XML 이 2026-09-05 잔재로 남아
있어 전체 합산은 이중 계산된다. 위 값은 **오늘 실행분(`testDebugUnitTest` + `iosSimulatorArm64Test`)** 이다.

## 결정 사항

1. 🔴 **AI 는 승패를 결정하지 않는다** — 사진 1장 pass/fail 만. 승패는 `ChallengeVerdict` (ADR-0013 §결정 2)
2. **반려 `status` = `FAILED` 전이 (A안)** — 🔑 *양쪽이 독립 수렴.* `ChallengeJudgementService:91-92`
   가 `status == VERIFIED` 로 판정 입력을 만들므로 **판정 로직 0줄 변경**으로 반려가 승패에서
   빠진다. B안(`VERIFIED` 유지 + `aiReason` 판별)은 **앱이 규칙 사본을 갖는다**
3. **미인증 처리 문턱** — `missionVerifiable && verdict == REJECT && confidence >= 0.80`. **느슨한
   쪽**으로 잡았다: 부정행위를 놓치는 비용 < 정상 수행자를 패배시키는 비용(회복 경로 0)
4. **fail-open 4경우** (키 미설정 / 실패 / 타임아웃 / 파싱실패) → 기존 동작 복귀 + `aiFailOpen` 카운터
5. **호출 1건당 정확히 1회** — 자정 최종본 1장. 미제출·기권은 **0회**. 멱등 가드 2겹(`ai_checked_at` + 대상 쿼리)
6. **`/v1/interactions`** — `v1beta` 아님. 모델 `gemini-3.5-flash` · `thinking_level` `low`
7. **`aiReason` wire 게이트** — 도메인 `rejectedByAi()` 위임. `view()` 에 조건식을 적으면 사본이 된다

## 🔑 이 feature 의 수확 — "이름이 같으니 같은 것"

🔴 **개별 결함 12건보다 이 한 줄이 값있다.** pm 과 backend 가 **각자 저지른 실수의 뿌리가 같았고
서로가 상대의 것을 잡았다**:

| | pm 의 실수 | backend 의 실수 |
|---|---|---|
| 판단 | *"**wire** 규약이니 **wire** 테스트에"* | *"문서에 `output_text` 가 있으니 **wire** 에도 온다"* |
| 실제 | 그 테스트는 **DTO 를 손으로 만든다** | 그건 **SDK 헬퍼**다 |
| 결과 | **게이트를 떼도 초록**인 테스트가 *"잠갔다"* 는 착각을 만든다 | **관측 안 된 경로에 방어 코드** + KDoc 이 그걸 계약이라 단정 |

🔴 **선례가 있는데도 둘 다 빠졌다** — `ChallengeVerdict` KDoc 이 이미 *"`:service` 의
`VerificationParty` 를 재사용하지 마라 — **이름도 값도 같지만** 모듈이 다르다"* 로 같은 함정을
경계하고 있었다(challenge-forfeit, 17일 전). **"조심하자" 로는 안 막힌다.**
→ 기계적 단계: **이름을 근거로 쓰기 전에 그 이름을 읽은 자리를 댄다.** 자리를 못 대면 근거가 없다.

### 그리고 *"문서가 코드보다 앞섰다"* **2건** — 성격이 다르다

challenge-forfeit 이 6건을 수확했고 여기서 2건이 더 나왔다:

| # | 건 | 성격 |
|---|---|---|
| **7** | `NoOpMissionVerifier` KDoc 이 **없는 게이트**를 *"(계약)"* 이라 단언 | **처음부터 거짓.** 컴파일·테스트 초록이라 조용했다 |
| **8** | `V9` 의 `verified_at` 주석 *"`PENDING/FAILED` 면 NULL"* | 🔴 **참이었던 문장이 우리 변경으로 거짓이 됨** |

🔴 **8번이 더 위험하다** — 작성 당시엔 정확했으므로 **리뷰에서 안 걸린다.** backend 는 계약에서
낡은 문장 4건을 제대로 훑었는데 **DB 주석을 범위에서 빠뜨렸다.** 훑을 범위는 *"코드 + 계약"* 이
아니라 **"코드 + 계약 + DB 주석 + KDoc"** 이다. 컬럼 주석은 **가장 권위 있는 자리**라 거짓이
남으면 방금 만든 로직을 **버그로 읽고 되돌린다.**

### 🔴 9번째가 될 뻔했다 — 막은 것은 backend 다

경어체 정정 배정에서 pm 이 *"§4 예시에 **'종결어미는 프롬프트가 보장한다'** 를 달아라"* 고
지시했다. **backend 가 거부했다.** 근거: `response_format` 스키마는 **구조를 강제하지만 어체는
강제하지 못한다.** *"보장"* 이라고 적으면 **집행 없는 계약을 문서가 단언하는 형태**가 되고,
그건 위 표의 7번째(`NoOpMissionVerifier` KDoc)·8번째(`V9` 주석)와 **정확히 같은 결함**이다.

🔑 **즉 pm 의 지시가 이 feature 가 수확한 바로 그 패턴을 하나 더 만들려 했다.** 대신 들어간 문장:

> 프롬프트가 이 어체를 **지시한다** · 🔴 **예시를 고칠 일이 생기면 프롬프트를 함께 고쳐라** ·
> ⚠️ **이 예시를 *"서버가 이렇게 보낸다"* 는 보증으로 읽지 마라**

🔵 pm 의 의도(*"예시만 보고 프롬프트를 안 고치는 것을 막기"*)는 **오히려 더 강하게 담겼다** —
*"보장한다"* 로 적으면 읽는 사람이 *"그럼 예시가 곧 실제구나"* 로 **안심하고 넘어간다.**

⚠️ **pm 배정 자체도 불완전했다 — 2곳이라 했으나 실측은 4곳이었다.** 누락된
`VerificationDtos.kt:135` `@field:Schema(example=…)` 이 **SpringDoc OpenAPI = 모바일이 참조하는
source of truth** 라, 계약 문서만 고치면 **Swagger 를 보는 쪽은 여전히 합쇼체를 복사한다.**
backend 가 배정 범위에 갇히지 않고 `grep "보기 어렵습니다"` 를 **양 레포 전수**로 돌려 찾았다.
🔴 ***"조치 N곳" 이라는 숫자 자체를 근거로 쓰지 않는다*** — `V14` 때 backend 가 DB 주석을
범위에서 빠뜨린 것의 역이고, 그 교훈을 같은 feature 안에서 적용한 결과다.

### 교차 검증 3회 — 셋 다 한쪽이 놓친 것을 다른 쪽이 잡았다

| 발견 | 잡은 쪽 |
|---|---|
| 🔴 **wire 게이트 결함** (무키 상태에서 **이긴 사람 화면**에 *"AI 검증이 비활성 상태입니다"*, `ERROR` 는 **예외 메시지**가 그대로) | mobile — backend 의 *"넣었으니 착수해도 된다"* 를 **믿지 않고 코드를 읽어** 적발 |
| 서버 감사 완결성 (소거형 게이트 0건 → backend 의 3곳이 전부) | pm |
| `V14` DB 컬럼 주석 | pm — backend 가 스윕 범위에서 빠뜨린 자리 |

## 미해결 이슈

### 🔴 차단
- [ ] **기능 미점화** — `GEMINI_API_KEY` 미주입이라 `NoOpMissionVerifier` 선택. **제출하면 인정**(이 feature 이전과 동일). `application.yml` 에 `gemini:` 블록 추가도 주입 시점 함께. 🔴 **콘솔에서 `Paid` 표시 눈 확인 필수** — 키만 만들면 free tier 이고 그러면 ADR §근거 1 의 방어(개인 사진이 학습에 안 쓰임)가 무효
- [ ] **반려 화면을 한 번도 본 적이 없다** — 게이트가 `UNVERIFIABLE` 을 막아 `aiReason` 이 실제로 항상 `null`. 보려면 DB 에 `status='FAILED'` + `ai_verdict='REJECT'` + `ai_confidence=0.93` + `ai_reason='…'` **넷을 다 넣어야** 게이트를 통과한다. Compose UI 테스트 인프라 부재
- [ ] **양 레포 미커밋** — server 21파일 · app 13파일. 커밋은 사용자 판단

### 🟡
- [ ] **경어체 혼용** — 앱 접두어는 해요체, AI 사유는 합쇼체로 기울어 **한 문장에 섞인다.** 🔴 **씨앗은 pm 초안 예시**이고 backend 가 정본으로 옮겼다. 조치: 프롬프트 해요체 지정 + 정본 예시 교체. ⚠️ **프롬프트 지시는 확률이지 보장이 아니다** — 구조적 해소는 디자이너 확인 6번
- [ ] **`output_text` 폴백 제거 — 교차 검증 0** — 🔴 **이 feature 에서 두 사람 이상이 확인하지 않은 유일한 판단.** pm 승인은 backend 독해에 기댔다(pm 쪽 API 레퍼런스 URL 404). 첫 실호출에서 응답 원문을 **눈으로** 확인. 틀려도 fail-open + `aiFailOpen` 으로 드러나고 복구는 한 줄
- [ ] **실호출 미검증 4건** — 스키마 준수 / 토큰 실측(ADR 추정 ~1,520, 리사이즈로 더 낮을 가능성) / 응답 지연이 read 타임아웃 30s 안인가 / `reason` 한국어 톤

### 🔵 외부 의존
- [ ] **디자이너 확인 6건** — ①사유 자리(사진 아래 8dp) ②위계(`medium12`+`onSurfaceVariant`, 🔴 **`error` 색 안 쓴 판단** — Pill 과 경쟁) ③**긴 사유 줄바꿈**(`maxLines` 없음 — 이의제기가 없어 유일한 설명이라 자를 수 없다) ④반려 카드 완성 조합 ⑤상대 카드에도 붙는 것 ⑥🔵 **사유를 접두어와 한 문장으로 잇지 말고 인용 블록으로 둘지** — 그러면 *"AI 가 한 말"* 이 되어 어체에 종속되지 않는다(경어체의 구조적 해소)
- [ ] **Gemini auto-reload** — 콘솔. 🔴 **이 템포에선 소진보다 12개월 만료가 먼저 온다**(안 써서 꺼진다). 만료 → 429 → fail-open → **아무 사진이나 통과로 조용히 복귀**
- [ ] **개인정보 처리방침에 "AI 판별 제3자 전송" 반영** — 출시 전 필수. 🔴 **이 코드로 사진이 서버 밖으로 나가는 경로가 실제로 생겼다**(ADR-0011 이 닫아 둔 경계)

### 🟢
- [ ] **실사진 A/B 세트** (통과 10 / 반려 10) — ADR §확정 경위가 *"이게 없으면 모델을 내리지도 올리지도 마라"* 고 못박은 전제
- [ ] **통합 테스트 부재 — 트랜잭션 경계 미검증.** *"AI 호출이 트랜잭션 밖"* 이 **구조로만 보장**된다. 🔴 **어긋나면 `aiFailOpen` 으로도 안 잡힌다**(호출은 성공하므로) — 증상은 배치 지연·커넥션 풀 고갈
- [ ] **root-level `iosSimulatorArm64Test` 실패** — 죽은 TMDB 잔재 `:local:database`. 🔴 조치는 애노테이션 추가가 아니라 **모듈 삭제**. 앱 동작 무해(미배선), 우선도 낮음
- [ ] `repos.json` blockers 의 *"통합 테스트 45건 skip"* → 실측 **50건**

## 참조
- [spec.md](./spec.md) · [plan.md](./plan.md) · [api-contract.md](./api-contract.md) · [change-log.md](./change-log.md)
- [mobile-report.md](./mobile-report.md) · [backend-report.md](./backend-report.md)
- [ADR-0013](../../decisions/0013-ai-verification-provider.md) — 제공자 + 판정 주체 분리
- 정본 계약: [challenge-verification/api-contract.md](../challenge-verification/api-contract.md) §4 · §4.1
