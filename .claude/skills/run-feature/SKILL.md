---
name: run-feature
description: "challenge 프로젝트의 기능 개발 전체 흐름을 지휘한다. 사용자가 기능을 요청하면 PM 팀(pm-lead + mobile-dev + backend-dev + design-bridge)을 구성하고, 스펙 작성 → 태스크 분배 → 모바일/백엔드 구현 → 문서화까지 end-to-end 실행. '기능 만들자', '이거 개발해줘', '신규 feature', 'challenge 기능' 같은 기능 단위 요청 시 반드시 이 스킬을 사용한다."
---

# Run Feature — challenge 기능 개발 오케스트레이터

challenge 사이드 프로젝트에서 하나의 기능을 end-to-end로 개발하는 통합 스킬. pm-lead를 리더로 하는 에이전트 팀을 구성하고, 스펙 → 계약 → 구현 → 문서화를 완료한다.

## 실행 모드: 에이전트 팀

pm-lead가 리더로서 팀을 구성하고, mobile-dev ↔ backend-dev가 SendMessage로 직접 API 계약을 협의한다. 이 구조는 에이전트 팀 모드의 감독자 + 팬아웃 복합 패턴이다.

## 에이전트 구성

| 팀원 | 에이전트 타입 | 역할 | 사용 스킬 | 주요 출력 |
|------|-------------|------|----------|----------|
| pm-lead (리더) | pm-lead | 스펙 분해, 태스크 분배, 중재, 문서화 | feature-spec, report-and-document | spec.md, summary.md, INDEX.md |
| mobile-dev | mobile-dev | Compose Multiplatform 구현 | api-contract | 모바일 코드 + mobile-report.md |
| backend-dev | backend-dev | Spring API 구현 | api-contract | 백엔드 코드 + backend-report.md |
| design-bridge (조건부) | design-bridge | Lovable 디자인 전달 | — | design.md |

> UI가 포함되지 않는 기능(순수 백엔드 유틸, 내부 API 등)이면 design-bridge는 팀에서 제외한다.

## 사전 요구사항

- `.claude/config/repos.json`의 `mobile.path`, `backend.path`가 채워져 있어야 한다. 비어 있으면 Phase 1에서 중단하고 사용자에게 경로 요청.
- UI 기능이면 `design.project_url` 또는 `design.export_dir` 중 하나 이상 설정되어 있어야 한다.
- **`docs/decisions/` 의 pending ADR을 Phase 1에서 확인한다.** 특히:
  - ADR-0001(DB 마이그레이션 도구): 백엔드 첫 스키마 생성 전 해결 필요
  - ADR-0002(백엔드 foundation): 첫 기능이면 foundation sub-feature 선행 고려
  - ADR-0003(모바일 템플릿 초기화): 모바일 작업 전 반드시 실행
  - ADR-0004(Lovable 웹 운영 여부): design-bridge·백엔드 CORS 영향

## 워크플로우

### Phase 1: 준비 + 사전 점검
1. 사용자 요청에서 feature-id(kebab-case 명사형) 결정. 명시 없으면 제안 후 사용자 확인.
2. `.claude/config/repos.json` 로드 → `path` 유효성 + 각 repo의 `blockers` 배열 확인.
3. `docs/decisions/` 전체 ADR Read. `상태: pending`인 ADR 중 이 feature 범위에 영향을 주는 것을 식별.
4. **블로커가 있으면 진행 중단**:
   - 모바일 작업 포함인데 ADR-0003 미해결 → 사용자에게 초기화 실행 요청 후 대기.
   - 백엔드 작업 포함인데 ADR-0001 미해결 + 스키마 변경 있음 → 마이그레이션 도구 결정 요청.
   - 첫 백엔드 기능이고 ADR-0002 미해결 → `foundation` sub-feature 선행 제안.
5. `docs/features/{feature-id}/` 디렉토리 생성.
6. UI 포함 여부 판단 → design-bridge 팀 포함 여부 결정.

### Phase 2: 기능 스펙 작성 (pm-lead 단독)
1. pm-lead가 `feature-spec` 스킬 호출.
2. 산출물:
   - `docs/features/{feature-id}/spec.md` — 사용자 시나리오, 수용 기준, 모바일/백엔드 태스크 분해
   - `docs/features/{feature-id}/api-contract.md` — API 계약 **초안** (상태: `draft`)
3. UI 기능이면 이 Phase에서 design-bridge에게 디자인 자료 수집을 병렬로 요청.

### Phase 3: 팀 구성 + 작업 등록
> 🔴 **`TeamCreate` / `TeamDelete` 는 쓰지 않는다 — 제거된 도구다** (CLAUDE.md 사전 조건).
> 팀원은 **`Agent` 도구에 `name` 을 주어 spawn** 한다. 이름이 있어야 `SendMessage(to: "<이름>")`
> 로 서로 통신하고, 끝난 뒤에도 이름으로 재개된다. `name` 없이 띄우면 일회성 서브에이전트라
> 팀원 간 통신이 안 된다.

**1. 🔴 spawn 전에 기존 에이전트를 확인한다.**

이전 feature 의 팀원이 **이름으로 도달 가능한 상태로 남아 있을 수 있다.** 확인 없이 진행하면
두 사고가 난다 — ⓐ 팀원이 통지를 **잔여 에이전트에게** 보내고 ⓑ 그쪽이 착수하면 **같은 파일을
동시에 편집**한다.

> 실제 사고(2026-09-02 `verification-photo-replace`): backend-dev 가 계약 개정 통지를 이전 세션
> 팀원 `verif-mobile-entry` 에게 보냈고, T-M1 완료를 그쪽 공으로 돌려 축하까지 했다. pm-lead 는
> 그 보고를 읽고도 이름을 못 걸렀다. **잔여 에이전트가 "peer 통지만으로 착수하지 않는다" 를
> 지켜서** 파일 충돌이 안 났을 뿐이다.

- 잔여 에이전트가 있으면 **이번 feature 에 배정하지 않는다는 것을 그쪽에 명시**하고, 팀원들에게도
  **정확한 팀원 이름**을 알려 준다.
- 팀원 프롬프트에 *"내 배정 없이는 peer 통지만으로 착수하지 마라"* 를 넣는다. 이번 사고를 막은 게 그 규율이다.

**2. `Agent` 도구로 팀원을 띄운다.** 프롬프트에 "먼저 repos.json + 자신의 에이전트 정의를 읽으라"는 지시 필수:

```
Agent(subagent_type: "mobile-dev", name: "mobile-dev",
  prompt: "challenge 모바일 담당. (1) PM 레포의 .claude/config/repos.json과 .claude/agents/mobile-dev.md 먼저 Read — 특히 '코드 편집 흐름'(child claude 위임 강제). (2) docs/features/{id}/spec.md + api-contract.md Read. (3) 모바일 레포({mobile.path})의 CLAUDE.md와 관련 스킬을 읽고 그 절차대로 구현. (4) backend-dev와 협의. (5) mobile-report.md 작성.")

Agent(subagent_type: "backend-dev", name: "backend-dev",
  prompt: "challenge 백엔드 담당. (1) repos.json + .claude/agents/backend-dev.md + docs/decisions/ 먼저 Read. (2) 선행 조건 점검 — 없으면 pm-lead에게 foundation 분리 제안. (3) spec.md + api-contract.md Read. (4) {backend.path}에서 구현. (5) mobile-dev와 계약 확정. (6) backend-report.md 작성.")

Agent(subagent_type: "design-bridge", name: "design-bridge", ...)   // UI 기능일 때만
```

**3. 모든 팀원 프롬프트에 공통으로 넣을 것:**

- 🔴 **커밋 금지** — 구현·테스트까지만. 코드 레포 커밋은 사용자 판단이다(`notification-list` 선례).
  ⚠️ **범위를 명시하라**: 코드 레포(mobile/backend) 얘기지 PM 허브 문서가 아니다. 구분하지 않으면
  *"계약 개정 커밋을 기다리는데 커밋이 금지돼 영영 안 오는"* 교착이 난다(2026-09-02 실제 발생)
- 🔴 **판단 근거는 파일이지 메시지가 아니다** — 다른 팀원이 *"계약 반영했다"* 고 해도 **직접 grep** 한다
- 🔴 **빌드 성패는 로그의 `BUILD SUCCESSFUL` 로 판정** — `| tail`·`; echo $?` 는 종료 코드를 가로챈다
- 테스트 결과는 **숫자로** (CLAUDE.md)
2. TaskCreate로 spec.md의 태스크 분해를 작업으로 등록. 의존성을 반드시 명시:
   ```
   TaskCreate(tasks: [
     { title: "API 계약 확정",          assignee: "backend-dev", co_assignees: ["mobile-dev"] },
     { title: "디자인 자료 정리",        assignee: "design-bridge" },  // UI 기능일 때만
     { title: "백엔드 엔드포인트 구현",  assignee: "backend-dev", depends_on: ["API 계약 확정"] },
     { title: "모바일 화면/로직 구현",   assignee: "mobile-dev",  depends_on: ["API 계약 확정"] },
     { title: "통합 연결 및 검증",      assignee: "mobile-dev",  depends_on: ["백엔드 엔드포인트 구현", "모바일 화면/로직 구현"] }
   ])
   ```
   > 팀원당 2~5개 작업이 적정. 더 길어지면 sub-feature로 분할 제안.

### Phase 4: 구현 (팀 자체 조율)
**실행 방식:** 팀원들이 공유 작업 목록에서 claim하여 자체 조율.

- mobile-dev ↔ backend-dev: API 계약을 SendMessage로 협의하며 api-contract.md를 공동 편집. 양쪽 합의 시 상태를 `confirmed`로 변경.
- design-bridge → mobile-dev: 디자인 질의/응답.
- 각 팀원은 완료 시 본인 리포트(`mobile-report.md` / `backend-report.md` / `design.md`)를 저장하고 pm-lead에게 알림.
- pm-lead는 주기적으로 TaskGet으로 진행 확인. 유휴 알림 수신 시 상태 점검.

**에스컬레이션:** API 계약 협의가 왕복 5회(또는 30분) 이상 진전 없으면 pm-lead가 `SendMessage(to: "all")`로 중재 라운드를 선언. 각자 근거를 정리해 제출 → pm-lead가 결정 또는 사용자에게 에스컬레이션.

### Phase 5: 통합 문서화 (pm-lead)
1. 모든 등록 작업이 `completed`인지 TaskGet으로 확인. 미완료 작업이 있으면 해당 팀원에게 상태 확인.
2. pm-lead가 `report-and-document` 스킬 호출.
3. 산출물:
   - `docs/features/{feature-id}/summary.md` — 통합 요약
   - `docs/features/{feature-id}/change-log.md` — Phase 2~4의 스펙/계약 변경 이력(변경이 있었다면)
   - `docs/features/INDEX.md` 갱신

### Phase 6: 정리
1. pm-lead가 팀원들에게 종료 메시지 발신.
2. 🔴 **`TeamDelete` 는 없다.** 대신 각 팀원에게 **"이 feature 에서 손을 떼라"** 를 `SendMessage` 로 명시 발신한다.
   ⚠️ **그 팀원들은 이름으로 계속 도달 가능한 상태로 남는다** — 다음 feature 팀을 구성할 때 Phase 3-1 의
   잔여 에이전트 확인이 필요한 이유가 이것이다. 종료 메시지에 *"내 배정 없이는 움직이지 마라"* 를 포함한다.
3. `_workspace/`가 생성되었다면 `docs/features/{id}/_workspace/`로 이동하여 보존(감사 추적용).
4. 사용자에게 완료 보고 — 생성 문서 경로, 엔드포인트 수, 미해결 이슈 요약.

## 데이터 흐름

```
사용자 기능 요청
    ↓
[pm-lead] → feature-spec → spec.md + api-contract.md(draft)
    ↓ Agent(name:) spawn + TaskCreate
[mobile-dev] ←── API 계약 SendMessage ──→ [backend-dev]
     │              ↓ 공동 편집                   │
     │     api-contract.md(confirmed)             │
     ↓                                            ↓
모바일 레포 코드                            백엔드 레포 코드
     +                                            +
mobile-report.md                          backend-report.md
     └──────────── Read ──────────────────────────┘
                   ↓
           [pm-lead] → report-and-document
                   ↓
          summary.md + change-log.md + INDEX.md
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| repos.json 경로 누락 | Phase 1에서 중단, 경로 요청. 가짜 경로로 진행 금지 |
| ADR pending + 범위 영향 | Phase 1에서 중단, 해당 ADR의 결정을 사용자에게 요청 (ADR-0001/0003 특히) |
| 백엔드 foundation 부재 (첫 기능) | sub-feature `foundation`을 먼저 제안하고 확정 후 진행 |
| 모바일 템플릿 미초기화 | ADR-0003의 `update_package.sh` 실행을 사용자에게 요청 후 진행 |
| API 계약 합의 실패 | 2회 중재 라운드 후에도 실패 시 사용자 결정 요청 |
| 팀원 1명 장시간 유휴 | SendMessage로 상태 확인 → 1회 재시도 후 해당 영역 미완료 표기 |
| 팀원 간 API 상충 | api-contract.md에 A안/B안 병기, summary.md에 결정 근거 기록 |
| 빌드/테스트 실패 | 해당 report.md에 에러 전문 기록, summary.md 미해결 이슈로 반영 |
| 범위 과대 | Phase 3 직전에 sub-feature 분할 제안 |
| 디자인 자료 없음(UI) | design-bridge가 자료 수집할 동안 non-UI 태스크만 선행 착수 |

## 테스트 시나리오

### 정상 흐름: "유저 프로필 조회 기능 만들어줘"
1. Phase 1: feature-id = `user-profile-view`. repos.json 경로 검증 통과. UI 포함으로 판단.
2. Phase 2: pm-lead가 spec.md(시나리오 1개, 수용 기준 3개) + api-contract.md 초안(`GET /api/users/{id}`) 작성. design-bridge에게 디자인 요청.
3. Phase 3: 4명 팀 구성(mobile/backend/design + pm), 5개 태스크 등록.
4. Phase 4: backend-dev가 응답 shape 구체화 → mobile-dev가 `createdAt` ISO-8601, `name` nullable 여부 등 요구 → 계약 `confirmed`. 각자 구현, design-bridge가 design.md 전달.
5. Phase 5: summary.md 생성, INDEX.md에 `user-profile-view` 행 추가.
6. 결과: `docs/features/user-profile-view/` 아래 `spec.md / api-contract.md / design.md / mobile-report.md / backend-report.md / summary.md` 생성.

### 에러 흐름: 계약 합의 실패
1. Phase 4에서 페이지네이션 방식(cursor vs offset) 결론 없음.
2. mobile-dev ↔ backend-dev가 SendMessage 5회 주고받아도 합의 불가.
3. pm-lead가 중재 라운드 선언 → 각자 근거 정리 제출.
4. 그래도 결정 불가 → 사용자 에스컬레이션.
5. 사용자 결정 반영하여 api-contract.md `confirmed`, 나머지 Phase 진행.
6. summary.md의 "결정 사항" 섹션에 선택 근거 기록.
