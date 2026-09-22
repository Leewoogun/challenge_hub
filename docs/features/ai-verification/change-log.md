# Change Log — ai-verification

> 🔵 **정본 계약의 변경 이력은 여기가 아니다.** 이 feature 는 새 엔드포인트를 만들지 않고
> 기존 `confirmed` 계약을 개정했으므로, wire 변경은
> [challenge-verification/change-log.md](../challenge-verification/change-log.md) 에 등재돼 있다
> (`aiReason` 추가 / `photoDeleted` 누락 보정 **2건 별도**). 여기는 **이 feature 문서들의** 변경 이력이다.

## 2026-09-22

### 결정 확정
- **ADR-0013 `accepted`** — 제공자(Gemini 유료 티어) + 🔴 **판정 주체 분리**(AI 는 사진 1장
  pass/fail 만, 승패는 `ChallengeVerdict`). 사용자 확정 2건: 시작 모델 `gemini-3.5-flash` ·
  `thinking_level` `low`. **내려갈 조건을 ADR 에 명문화**(A/B 20장 전부 일치 시 Flash-Lite 로,
  단 불일치가 **false reject 방향이면 내리지 않는다**)
- `repos.json` — *"인증 진위 판정 주체 보류 — 원안 유지"* **반전 반영** + 낡은 문구 2곳 인라인 폐기 표시

### api-contract.md
- 신규 작성(`draft`) → **`confirmed`** (backend-dev). §1 은 **정본으로 이관**되어 축약
- **§1.1 신설 — wire 게이트는 계약이다.** `aiReason` 은 미인증 확정 건에만 non-null.
  🔑 이유: **컬럼(rubric 튜닝용 전건 저장)과 wire(사용자 화면)는 다르다**
- **§2 미결 확정 — A안**(`FAILED` 전이). 앱 3곳 · 서버 3곳의 *"`FAILED` 면 사진이 없다"* 전제가
  A안의 실제 비용이라는 실측 표 등재
- **§3 미결 확정** — 앱은 `aiReason: null` 의 세 의미를 구분하지 않는다. **fail-open 관측은
  서버 배치 요약이 진다**(이 줄을 근거로 배치 로깅을 빼지 마라)

### 🔴 pm 초안 오류 정정 3건 (`aiverify-mobile` 적발 → pm 실측 확인)
1. **§1 예시 JSON 이 실재하지 않는 shape** — `data.verifications[]` 배열로 썼으나 실제는
   `data.challenger{}` / `data.opponent{}`. ⚠️ **그대로 이관됐으면 `confirmed` 계약에 거짓 shape 이
   들어갔다.** 실제 shape 으로 교체 + 실재 필드 `photoDeleted` 추가
2. **§2 의 *"A안이면 `MissionCardMineFailedPreview` 가 되살아난다"*** — 틀렸다. 그 Preview 는
   *"다시 인증하기"* CTA 를 그리는데 판정이 **자정 = 마감**이라 재시도 창이 구조적으로 없다.
   **철회**하고 A안의 실제 비용(앱 3곳)으로 교체
3. 🔴 **전달 누락** — §1 정정만 backend 에 보내고 **§2 철회를 안 보냈다.** backend 가 고치기 전
   판본을 A안 이점으로 인용했고 mobile 이 하류에서 잡았다. *"내 메시지는 시점이 박힌
   스냅샷"* 이 pm 쪽에도 그대로 적용된 사례

### spec.md
- §5.1 — *"← 시작점"* 이 `3.5 Flash-Lite` 에 붙어 **거짓이 됐다**(ADR 이 `3.5 Flash` 로 확정).
  취소선 + `Flash` 행 신설 + ⚠️ **`Flash` 와 `Flash-Lite` 는 다른 모델**(입력 5배·출력 3.6배) 경고
- §5.3 — **Gemini API 표기 인라인 정정**(개정 아님). `generateContent` 는 legacy,
  Interactions API 가 **`v1` GA**. 🔴 **`v1beta` 아님** — 2026-05 default flip · 6/8 레거시 제거가
  일어난 채널이고 공식 표현이 *"actively being developed"* 다
- §4 — **폐기 태스크 2건**(T-B3 재제출 허용 · T-M1 재촬영 UI)에 **인라인 폐기 표시** + 잔여 범위 요약

### plan.md
- **폐기 3건**(Task 5 · Task 8 · **Task 9 Step 2**)에 인라인 표시. Step 2(재제출 전 선행 조회
  제거)는 `VerifyViewModel.kt:90` 이 이미 선행 조회 없이 제출함을 pm 이 실측해 확인
- §2 머리에 🔴 *"이 plan 은 2026-09-02 에 쓰였고 그 뒤로 두 feature 가 지나갔다 — 남은 Step 을
  실행하기 전에 이미 돼 있지 않은지 코드로 먼저 확인하라"*
- §4 열린 항목 2번(ADR-0013) **해소 표기**

> 🔑 **한 문서에서 낡은 항목이 세 번 나왔다.** 원인은 분할 배너가 **파일 머리에만** 있었던 것이고,
> 에이전트는 grep 으로 읽어 해당 절만 본다. → **폐기 표시는 명령문 바로 앞줄에.**

### 서버 마이그레이션 판단 2건
- **`V13` 직접 수정** (`NUMERIC(3,2)` → `DOUBLE PRECISION`). 🔴 **테스트 693건이 전건 통과한
  상태에서 서버가 기동하지 않았다** — `ddl-auto=validate` 가 Kotlin `Double?` 에 `float(53)` 을
  요구한다. 부수 이유: `NUMERIC(3,2)` 는 **0.799 를 0.80 으로 반올림**해 **하필 가장 튜닝하고
  싶은 임계 구간에서** 컬럼의 존재 이유가 무효가 된다. 미커밋이었으므로 V14 쌍을 만들지 않았다
- **`V14` 신설** (주석 전용, DDL·DML 0줄) — `V9` 의 *"`PENDING/FAILED` 면 NULL"* 이 거짓이 됐고
  **하필 새 `photoDeleted` 로직이 그 반대에 의존**한다. `V9` 는 **이미 커밋돼 배포 이력에
  있으므로** 직접 고치지 않고 재주석했다(`V9` 자신이 그 패턴의 선례)
