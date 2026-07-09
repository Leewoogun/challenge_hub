# challenge_hub — PM 하네스

이 레포는 challenge 사이드 프로젝트의 **PM 허브**다. 제품 코드는 없고, 스펙·API 계약·구현 보고·진행 현황만 둔다.

## 역할 분담
- 모바일/백엔드 코드는 각 레포에서 수정한다. 이 레포에서 직접 편집하지 않는다.
- 연관 레포 경로는 `.claude/config/repos.json`에 등록되어 있다 — 작업 전 읽고 따르라.

## 기능 단위 작업 진입점
사용자가 "○○ 기능 만들자", "신규 feature", "기능 개발" 같은 요청을 하면 `run-feature` 스킬을 사용한다(`.claude/skills/run-feature/SKILL.md`).

### 사전 조건 (Agent Teams)
- `~/.claude/settings.json`에 `"env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }` 설정 (한 번만, 재시작 필요)
- Claude Code **v2.1.178+** 사용. 이전 버전의 `TeamCreate` / `TeamDelete` 도구는 제거됨.

### 흐름 (Agent Teams 기반)
1. pm-lead가 `feature-spec`으로 스펙 + API 계약 초안 작성
2. **자연어로 팀원 spawn 요청** — "mobile-dev / backend-dev / (UI면) design-bridge agent type으로 팀원 spawn"
   - 활성화돼 있으면 별도 도구 호출 없이 Claude가 자동으로 팀 구성
   - 각 팀원은 `.claude/agents/{name}.md` 정의의 페르소나 + tools allowlist + model을 적용받음
   - subagent 정의의 `skills` / `mcpServers` frontmatter는 팀원으로 실행 시 적용 안 됨 (일반 세션과 동일하게 프로젝트/사용자 설정에서 로드)
3. mobile-dev ↔ backend-dev가 **SendMessage**로 API 계약 확정 → 각자 구현
   - **mobile-dev는 코드 편집 시 child claude 위임 강제** — 상세는 `mobile-dev.md`의 "코드 편집 흐름" 섹션. 분석/협의는 본체, 실제 Edit/Write는 `cd challenge-app && claude -p`로 spawn (challenge-app의 SessionStart 훅 / skills / 자동 메모리 발화 보장).
   - backend-dev / design-bridge는 PM hub cwd에서 직접 작업 (절대경로 reach-in 편집).
4. pm-lead가 `report-and-document`로 summary.md + INDEX.md 작성

### Agent Teams 한계 (인지)
- **세션당 1팀** — 다중 feature 동시 진행은 별도 세션 필요.
- **중첩 팀 X** — 팀원이 자기 팀원 못 만듦 (Agent tool로 일회성 subagent는 가능).
- **in-process 세션 재개 시 팀원 복원 X** — `/resume` 후 새로 spawn 필요.
- **토큰 사용량 큼** — 각 팀원이 별도 Claude 인스턴스. 작업 비용 큰 점 인지.
- 표시 모드는 기본 `"in-process"` (메인 터미널 내 에이전트 패널, 화살표+Enter로 팀원 대화 전환). 분할창 원하면 `~/.claude/settings.json`에 `"teammateMode": "tmux"` 또는 `"iterm2"` 설정.

## 문서 위치
- `docs/features/{feature-id}/` — 기능별 문서 묶음
  - `spec.md`, `api-contract.md`, `mobile-report.md`, `backend-report.md`, `design.md`(UI), `summary.md`, `change-log.md`
- `docs/features/INDEX.md` — 전체 현황 (신규 feature 완료 시 갱신)
- `docs/backlog.md` — 프로젝트 전반의 TODO/미해결/대기 항목 통합 백로그 (각 feature 종료 시 `report-and-document` 스킬이 자동 갱신, "백로그 정리해줘" 요청으로 임의 시점 단독 갱신 가능)
- `docs/backlog-archive/{YYYY-MM}.md` — 백로그 "최근 완료"가 10건 초과 시 월별 아카이브
- `docs/design-system/` — 토큰/색상 카탈로그 (`tokens.md`, `colors.md`)
- `docs/status/{YYYY-Www}.md` — 주간 리포트 (`weekly-status` 스킬)
- `docs/decisions/` — ADR 용

## 규칙
- feature-id는 kebab-case 명사형. `user-login` (O), `viewUserProfile` (X).
- `api-contract.md` 상태 전이: `draft` → `negotiating` → `confirmed`. `confirmed` 후 변경은 `change-log.md`에 기록.
- 시간 포맷은 ISO-8601 UTC. 페이지네이션은 프로젝트 전체에서 한 방식으로 통일.
- summary.md의 테스트 결과는 반드시 숫자로: "단위 12/12 passed" (O), "테스트 통과" (X).
- 개별 에이전트를 우회하여 mobile/backend 레포에 직접 커밋하지 않는다.

## 참고
- 에이전트: `.claude/agents/` (pm-lead, mobile-dev, backend-dev, design-bridge)
- 스킬: `.claude/skills/` (run-feature, feature-spec, api-contract, report-and-document, weekly-status)
- 하네스 구조 상세는 각 파일의 frontmatter description과 "팀 통신 프로토콜" 섹션 참조.
