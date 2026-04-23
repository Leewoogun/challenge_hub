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

## 워크플로우

### Phase 1: 준비
1. 사용자 요청에서 feature-id(kebab-case 명사형) 결정. 명시 없으면 제안 후 사용자 확인.
2. `.claude/config/repos.json` 로드 → `mobile.path`, `backend.path`, UI 기능이면 `design.*` 검증.
3. `docs/features/{feature-id}/` 디렉토리 생성.
4. UI 포함 여부 판단 → design-bridge 팀 포함 여부 결정.

### Phase 2: 기능 스펙 작성 (pm-lead 단독)
1. pm-lead가 `feature-spec` 스킬 호출.
2. 산출물:
   - `docs/features/{feature-id}/spec.md` — 사용자 시나리오, 수용 기준, 모바일/백엔드 태스크 분해
   - `docs/features/{feature-id}/api-contract.md` — API 계약 **초안** (상태: `draft`)
3. UI 기능이면 이 Phase에서 design-bridge에게 디자인 자료 수집을 병렬로 요청.

### Phase 3: 팀 구성 + 작업 등록
1. TeamCreate로 팀 구성. 모든 팀원은 `model: "opus"` 고정:
   ```
   TeamCreate(
     team_name: "challenge-{feature-id}",
     members: [
       { name: "mobile-dev",    agent_type: "mobile-dev",    model: "opus",
         prompt: "challenge 모바일 담당. docs/features/{id}/spec.md와 api-contract.md를 읽고 모바일 레포에서 구현. backend-dev와 직접 API 계약 협의. 완료 시 mobile-report.md 작성." },
       { name: "backend-dev",   agent_type: "backend-dev",   model: "opus",
         prompt: "challenge 백엔드 담당. docs/features/{id}/spec.md와 api-contract.md를 읽고 백엔드 레포에서 구현. mobile-dev와 직접 API 계약 확정. 완료 시 backend-report.md 작성." },
       { name: "design-bridge", agent_type: "design-bridge", model: "opus",
         prompt: "Lovable 디자인을 design.md로 정리하여 mobile-dev에게 전달." }  // UI 기능일 때만
     ]
   )
   ```
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
2. TeamDelete로 팀 정리.
3. `_workspace/`가 생성되었다면 `docs/features/{id}/_workspace/`로 이동하여 보존(감사 추적용).
4. 사용자에게 완료 보고 — 생성 문서 경로, 엔드포인트 수, 미해결 이슈 요약.

## 데이터 흐름

```
사용자 기능 요청
    ↓
[pm-lead] → feature-spec → spec.md + api-contract.md(draft)
    ↓ TeamCreate + TaskCreate
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
