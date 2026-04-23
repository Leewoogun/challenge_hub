---
name: weekly-status
description: "challenge 프로젝트의 주간 상태 리포트를 docs/features/ 상태와 git 이력 기반으로 생성하여 docs/status/{YYYY-Www}.md에 저장한다. '주간 리포트', '주간 회고', '이번 주 진행 상황', '위클리' 요청이나 금요일 정기 리포트 생성 시 이 스킬을 사용. pm-lead가 호출."
---

# Weekly Status — 주간 상태 리포트

이번 주 동안의 feature 진행 현황을 취합하여 주간 리포트를 `docs/status/{YYYY-Www}.md`에 남긴다.

## 언제 사용하나
- 사용자가 주간 상태/리포트/회고를 요청할 때
- pm-lead가 금요일 정기 리포트를 생성할 때

## 입력
- `docs/features/INDEX.md` — 전체 feature 상태
- 각 `docs/features/{id}/summary.md` 또는 `spec.md`
- 각 `docs/features/{id}/change-log.md`
- PM 레포의 이번 주 git log (가능한 경우)

## 산출물: `docs/status/{YYYY-Www}.md`

```markdown
# Weekly Status — {YYYY-Www} ({월요일 YYYY-MM-DD ~ 일요일 YYYY-MM-DD})

## 하이라이트
3줄 이내. 의사결정권자가 1분 내 판단할 수 있는 요약.

## 완료된 기능
| feature-id | 완료일 | 요약 |
|-----------|--------|------|

## 진행 중
| feature-id | 단계 | 블로커 |
|-----------|------|--------|
| {id} | spec | 없음 |
| {id} | api-contract negotiating | {내용} |
| {id} | implementation | {내용} |

## 신규 착수
- feature-id: 시작일, 우선순위

## 블로커 / 에스컬레이션
- {내용} — 책임자, 목표 해결일.

## 지표
- 완료 기능 수: N
- 진행 중 기능 수: M
- 평균 리드타임(spec draft → summary completed): X일

## 다음 주 계획
- 우선순위 상위 3개 (이상은 쓰지 않음 — 위시리스트가 됨).
```

## 주차 표기 규칙

- ISO 주차 사용: `2026-W17` 형식.
- 월요일 시작, 일요일 종료.
- 주차 경계에 걸친 기간을 다룰 때는 "일요일까지 완료"를 기준으로 포함/제외.

## 작성 원칙

- **수치는 거짓말하지 않게.** 완료 기준 = summary.md 상태가 `completed`. `partially-completed`는 완료에 포함하지 않는다.
- **블로커는 책임자와 마감을 함께.** "API 계약 합의 중" (X) → "user-profile-view 페이지네이션 방식 — mobile-dev/backend-dev, 목표: 2026-04-25" (O).
- **하이라이트는 마케팅 문구가 아니다.** "큰 진전!" (X) → "인증 기능 완료, 모바일 온보딩 흐름 연결 가능해짐" (O).
- **다음 주 계획은 3개 이하, 우선순위 순.** 4개 이상은 계획이 아니라 위시리스트.
- **지표는 정의를 고정.** 리드타임 계산 기준을 주차 간에 바꾸지 않는다.

## 재생성 처리

같은 주차에 대해 재생성 요청이 오면:
1. 기존 파일을 덮어쓰되,
2. 파일 하단에 `## 수정 이력` 섹션을 추가하고 `{YYYY-MM-DD HH:mm} - {사유}` 한 줄을 append.

## 체크리스트

- [ ] 파일명이 `{YYYY-Www}.md` 형식인가?
- [ ] 완료 기능 수 = summary 상태 `completed` 인 feature 개수인가?
- [ ] 블로커에 책임자와 목표 해결일이 있는가?
- [ ] 다음 주 계획이 3개 이하인가?
- [ ] 지표 정의가 지난 주 리포트와 일관되는가?
