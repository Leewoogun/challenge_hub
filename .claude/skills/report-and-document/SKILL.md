---
name: report-and-document
description: "challenge 기능 구현이 끝난 뒤 mobile-dev/backend-dev/design-bridge의 리포트를 취합하여 summary.md와 change-log.md를 작성하고 docs/features/INDEX.md를 갱신한다. 기능 완료 보고, 구현 문서화, 변경 이력 정리 시점에 pm-lead가 반드시 이 스킬을 사용. run-feature 오케스트레이터의 Phase 5에서 호출."
---

# Report & Document — 완료 보고 취합 및 문서화

팀원들이 작성한 개별 리포트와 코드 변경을 종합하여 PM 레포에 정식 기록을 남긴다.

## 입력

- `docs/features/{feature-id}/spec.md`
- `docs/features/{feature-id}/api-contract.md` (상태 `confirmed`여야 함)
- `docs/features/{feature-id}/mobile-report.md` (mobile-dev 작성)
- `docs/features/{feature-id}/backend-report.md` (backend-dev 작성)
- `docs/features/{feature-id}/design.md` (UI 기능인 경우, design-bridge 작성)

## 산출물

### 1) `docs/features/{feature-id}/summary.md`

```markdown
# {Feature Title} — Summary

- **feature-id**: {kebab-case}
- **완료일**: {YYYY-MM-DD}
- **상태**: completed | partially-completed

## 구현 개요
한 단락 요약.

## 엔드포인트
| Method | Path | 상태 |
|--------|------|------|
| GET | /api/users/{id} | deployed |

## 화면 / UI 변경
- {스크린명}: {변경 요약}

## 주요 변경 파일
**모바일:**
- `path/to/File.kt`

**백엔드:**
- `path/to/Controller.kt`
- `db/migration/V2__...sql`

## 테스트 결과
- 모바일: 단위 N/N passed, UI N/N passed, iOS 빌드 ok
- 백엔드: 단위 N/N passed, 통합 N/N passed, 마이그레이션 적용됨

## 결정 사항
협의 과정에서 확정된 중요 결정 (페이지네이션 방식, nullable 처리, 시간 포맷 등).

## 미해결 이슈
- [ ] 이슈1: ...

## 참조
- [spec.md](./spec.md)
- [api-contract.md](./api-contract.md)
- [mobile-report.md](./mobile-report.md)
- [backend-report.md](./backend-report.md)
```

### 2) `docs/features/{feature-id}/change-log.md` (변경이 있었을 때만)

```markdown
# Change Log — {feature-id}

## {YYYY-MM-DD}
- spec.md: 수용 기준 3번 문구 수정 (이유: ...)
- api-contract.md: `POST /api/users` 요청에 `phone` 필드 추가 (이유: ...)
```

### 3) `docs/features/INDEX.md` 갱신

```markdown
# Features Index

| feature-id | 제목 | 상태 | 완료일 | 링크 |
|-----------|------|------|-------|------|
| user-profile-view | 사용자 프로필 조회 | completed | 2026-04-23 | [📄](./user-profile-view/summary.md) |
| daily-challenge-feed | 일일 챌린지 피드 | in-progress | — | [📄](./daily-challenge-feed/spec.md) |
```

INDEX.md가 없으면 생성, 있으면 해당 feature 행만 삽입/업데이트. 정렬: 상태(in-progress 먼저) → 완료일 내림차순.

## 작성 원칙

- **summary.md는 30초 내 파악 가능해야 한다.** 구현 내역 나열이 아니라 "무엇이 달라졌나" 중심.
- **미해결 이슈를 숨기지 않는다.** 부분 완료는 완료가 아니다 — 상태를 `partially-completed`로 정확히 기록.
- **각 report.md에서 그대로 복붙하지 않는다.** 중복은 줄이고, 결정 근거·인터페이스·영향 범위 중심으로 재구성.
- **파일 경로는 상대 링크로.** summary.md 기준 `./spec.md` 형태.
- **테스트 숫자를 최소 한 번은 명시.** "테스트 통과" (X) → "단위 12/12, 통합 3/3 passed" (O).
- **엔드포인트 표의 상태**: `deployed` | `implemented` | `pending`. `implemented`는 코드만 있고 아직 배포/확인 안 된 상태.

## 부분 완료 처리

모바일만 완료, 백엔드 미완인 경우:
1. summary.md 상태 = `partially-completed`
2. 엔드포인트 표의 해당 행 상태 = `pending`
3. "미해결 이슈"에 "백엔드 엔드포인트 T-B2 구현 필요" 명시
4. INDEX.md에도 `partially-completed` 표기

## 체크리스트

- [ ] api-contract.md 상태가 `confirmed`인가?
- [ ] mobile-report.md와 backend-report.md가 모두 존재하는가? (UI 기능이면 design.md도)
- [ ] summary.md의 엔드포인트 표가 api-contract.md와 일치하는가?
- [ ] INDEX.md가 갱신되었는가?
- [ ] change-log.md에 협의 과정의 변경이 반영되었는가? (변경이 있었던 경우)
- [ ] 테스트 결과가 숫자로 기록되었는가?
