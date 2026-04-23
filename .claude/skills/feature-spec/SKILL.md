---
name: feature-spec
description: "challenge 프로젝트의 기능 요구사항을 받아 PM 스펙(spec.md)과 모바일/백엔드 태스크 분해, API 계약 초안(api-contract.md)을 작성한다. 'feature-id 정의', '기능 스펙 작성', '태스크 분해', '수용 기준 정의' 요청에 반드시 사용. run-feature 오케스트레이터의 Phase 2에서 pm-lead가 호출."
---

# Feature Spec — 기능 스펙 작성 및 분해

기능 요구사항을 구조화된 스펙으로 변환하고, 모바일/백엔드 태스크로 분해하며, API 계약 초안을 만든다.

## 언제 사용하나
- pm-lead가 신규 기능 요청을 받았을 때
- 기존 feature의 스펙을 개정할 때 (이 경우 spec.md는 갱신, 변경 사항은 `change-log.md`에 추가)

## 산출물

### 1) `docs/features/{feature-id}/spec.md`

```markdown
# {Feature Title}

- **feature-id**: {kebab-case}
- **owner**: pm-lead
- **상태**: draft | in-progress | completed | partially-completed
- **생성**: {YYYY-MM-DD}

## 배경 / 문제
왜 이 기능이 필요한지 한 단락.

## 사용자 시나리오
1. (행위자) → (동작) → (결과)
2. ...

## 수용 기준 (Acceptance Criteria)
- [ ] 기준 1 — 검증 가능한 단위
- [ ] 기준 2
- ...

## 비범위 (Out of Scope)
이번 기능에서 **하지 않는** 것 명시.

## 태스크 분해

### 모바일 (mobile-dev)
- [ ] T-M1: ...
- [ ] T-M2: ...

### 백엔드 (backend-dev)
- [ ] T-B1: ...
- [ ] T-B2: ...

### 디자인 (design-bridge, UI 기능만)
- [ ] T-D1: ...

## 의존 관계
- T-M1, T-M2는 `api-contract.md` 상태가 `confirmed`가 된 뒤 착수.
- T-B2는 T-B1 완료 후 착수.

## 리스크 / 오픈 이슈
- ...
```

### 2) `docs/features/{feature-id}/api-contract.md`

API 계약 초안. `api-contract` 스킬의 템플릿을 사용하여 작성한다. 초기 상태는 `draft`. 확정은 mobile-dev ↔ backend-dev가 Phase 4에서 수행.

## 작성 원칙

- **수용 기준은 검증 가능해야 한다.** "빠르게 동작" (X) → "프로필 화면 2초 이내 첫 렌더링" (O).
- **태스크 분해는 병렬 가능 단위로.** 한 태스크 안에 모바일+백엔드 코드를 섞지 않는다.
- **의존 관계는 명시적으로.** 특히 "API 계약 확정"은 거의 모든 구현 태스크의 선행 조건.
- **디자인 자료가 아직 없는 UI 기능이면**: 비-UI 태스크만 먼저 분해하고 "디자인 대기" 태스크를 명시.
- **비범위 섹션이 비지 않게.** 항상 무언가 배제되어야 스코프가 명확해진다.

## feature-id 네이밍

| ✅ | ❌ | 이유 |
|----|----|------|
| `user-profile-view` | `viewUserProfile` | 케밥케이스, 명사형 |
| `daily-challenge-feed` | `feed-v2` | 내용 식별 가능 |
| `auth-jwt` | `login-and-register` | 단일 기능 단위 |

## 스펙 품질 체크

스펙 완성 후 다음을 확인한다:
1. 모바일 태스크와 백엔드 태스크가 각자 최소 1개씩인가? (없으면 분해가 덜 됨)
2. 수용 기준이 모두 체크박스이고 검증 가능한가?
3. API 계약 초안에 최소 메서드·경로·요청·응답 shape이 있는가?
4. 비범위 섹션이 비어 있지 않은가?
5. 의존 관계에 "API 계약 확정" 선행 조건이 명시되어 있는가?

## 스펙이 개정되는 경우

기존 `spec.md`가 있는 feature의 개정 요청이 오면:
1. `spec.md`를 갱신 (덮어쓰기)
2. 같은 날짜에 `change-log.md`에 무엇이 왜 바뀌었는지 한 줄 추가
3. 영향받는 태스크가 이미 구현 중이면 pm-lead가 담당 에이전트에게 SendMessage로 통지
