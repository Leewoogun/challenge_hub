# challenge_hub

challenge 사이드 프로젝트의 **PM 허브**. 기능 스펙, API 계약, 구현 보고, 주간 현황을 기록한다. 제품 코드는 별도 레포에 있다.

## 연관 레포
| 역할 | 레포 | 스택 |
|------|------|------|
| 모바일 앱 | `challenge-app` | Kotlin Compose Multiplatform |
| 백엔드 API | `challenge-server` | Spring Boot (Kotlin) |
| 디자인 | `challenge-design` | Lovable |
| PM 허브 | `challenge_hub` (이 레포) | — |

## 구조
```
.claude/
├── agents/          # pm-lead, mobile-dev, backend-dev, design-bridge
├── skills/          # run-feature, feature-spec, api-contract,
│                    # report-and-document, weekly-status
└── config/
    └── repos.json   # 연관 레포 경로 레지스트리

docs/
├── features/
│   ├── INDEX.md     # 전체 기능 현황
│   └── {id}/        # spec, api-contract, mobile/backend report, summary
├── status/          # 주간 리포트
└── decisions/       # ADR
```

## 실행 모델
PM 에이전트 팀을 구성해 기능 단위로 end-to-end 개발하는 하네스.

```
[pm-lead 리더]
    ├─ feature-spec → 스펙 + API 계약 초안
    ├─ TeamCreate → mobile-dev ⇄ backend-dev (+ design-bridge)
    │     └ SendMessage로 API 계약 직접 협의 → confirmed
    ├─ 각자 레포에서 구현 + 리포트 작성
    └─ report-and-document → summary.md + INDEX.md 갱신
```

## 사용법
Claude Code에서 이 디렉토리를 열고 기능 단위로 요청하면 된다:

> "유저 프로필 조회 기능 만들자"

`pm-lead`가 팀을 구성하고 스펙 → API 계약 협상 → 구현 → 문서화까지 수행한다.

## 요구사항
- [Claude Code](https://claude.com/claude-code)
- `superpowers` 플러그인:
  ```
  /plugin marketplace add obra/superpowers-marketplace
  /plugin install superpowers@superpowers-marketplace
  ```
- `.claude/config/repos.json`의 경로를 본인 환경에 맞게 수정

## 상세 문서
- [CLAUDE.md](./CLAUDE.md) — Claude Code용 운영 가이드
- `.claude/skills/run-feature/SKILL.md` — 기능 개발 오케스트레이터
- `.claude/skills/api-contract/SKILL.md` — 모바일-백엔드 계약 포맷
