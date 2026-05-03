---
name: report-and-document
description: "challenge 기능 구현이 끝난 뒤 mobile-dev/backend-dev/design-bridge의 리포트를 취합하여 summary.md와 change-log.md를 작성하고 docs/features/INDEX.md, docs/backlog.md를 갱신한다. 기능 완료 보고, 구현 문서화, 변경 이력 정리, '백로그 정리/갱신' 요청 시점에 pm-lead가 반드시 이 스킬을 사용. run-feature 오케스트레이터의 Phase 5에서 호출."
---

# Report & Document — 완료 보고 취합 및 문서화

팀원들이 작성한 개별 리포트와 코드 변경을 종합하여 PM 레포에 정식 기록을 남긴다.

## 입력

- `docs/features/{feature-id}/spec.md`
- `docs/features/{feature-id}/api-contract.md` (상태 `confirmed`여야 함)
- `docs/features/{feature-id}/mobile-report.md` (mobile-dev 작성)
- `docs/features/{feature-id}/backend-report.md` (backend-dev 작성)
- `docs/features/{feature-id}/design.md` (UI 기능인 경우, design-bridge 작성)
- `docs/backlog.md` (이번 feature가 해결한 항목 / 새로 발생한 미해결 항목 갱신)

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

### 3) `docs/backlog.md` 갱신 (필수)

이번 feature가 끝나면서 발생한 변화를 반영한다. 두 방향으로 동기화:

**3-1) 이번 feature가 해결한 항목** → "✅ 최근 완료" 섹션으로 이동 (이미 백로그에 있던 경우만; 새로 추가하지 말 것).
- 동일 항목 두 곳 존재 금지 — 우선순위 표에서는 제거.
- "최근 완료"가 10건 초과면 가장 오래된 entry를 `docs/backlog-archive/{YYYY-MM}.md`로 이동(필요 시 디렉토리 생성).

**3-2) 새로 생긴 미해결 항목** → summary.md의 "미해결 이슈" 각 행을 백로그의 적절한 우선순위 표에 추가:
- 분류 가이드:
  - 다음 sprint 시작을 차단하면 🔴
  - 외부 의존(사용자 콘솔 작업 / 디자이너 / 결제 등)이면 🔵
  - 다음 sprint에서 다룰 가능성이 높으면 🟡
  - 그 외 일반은 🟢
- 출처 컬럼은 summary.md의 상대 링크: `[auth-kakao/summary.md](./features/auth-kakao/summary.md)`.
- 담당 컬럼은 mobile / backend / design / user / pm 중 해당.
- 메모는 한 줄로 핵심만.

**3-3) "마지막 갱신" 헤더 날짜 갱신** + "분류별 보기" 섹션도 일관성 있게 동기화.

**3-4) ADR 발생 시** "ADR pending / in-progress" 표 갱신 (예: 새 ADR이 미작성 상태로 트리거됐다면).

> 이 단계는 **건너뛰지 말 것**. 백로그가 갱신되지 않으면 프로젝트 차원의 후속 작업 가시성이 즉시 무너진다.

### 4) `docs/features/INDEX.md` 갱신

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
- [ ] **`backlog.md`** 가 갱신되었는가? (해결된 항목 → 최근 완료 / 새 미해결 → 우선순위 표)
- [ ] INDEX.md가 갱신되었는가?
- [ ] change-log.md에 협의 과정의 변경이 반영되었는가? (변경이 있었던 경우)
- [ ] 테스트 결과가 숫자로 기록되었는가?

## "백로그 정리해줘" 단독 호출 (feature 종료와 무관)

사용자가 임의 시점에 "백로그 정리/갱신" 요청을 하면 본 스킬의 "3) 백로그 갱신" 단계만 단독 실행한다. 이때는 다음 출처를 모두 다시 스캔한다:

1. `docs/features/*/summary.md`의 "미해결 이슈" 전부
2. `docs/features/*/spec.md`의 "리스크 / 오픈 이슈"
3. `docs/features/*/design.md`의 ⚠️ 항목
4. `docs/decisions/*.md` 의 `상태: in-progress` 또는 `pending`
5. `.claude/config/repos.json`의 `*.blockers` 배열
6. 노션 핵심 페이지 (필요 시 mcp 호출 — 페이지 ID는 repos.json `product.notion`)

스캔 결과로 백로그 우선순위 표를 재구성. 이미 있는 항목은 그대로 유지(우선순위 변동 시만 이동), 신규 발견은 추가, 출처가 사라진 항목은 검토 후 제거.

> 단독 호출에서도 `docs/features/*/summary.md` 전수 검토는 비용이 크지 않으므로 항상 수행한다.
