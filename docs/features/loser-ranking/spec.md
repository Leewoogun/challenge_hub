# 개돼지 랭킹 (loser-ranking) — Spec

- **feature-id**: loser-ranking
- **owner**: pm-lead
- **상태**: draft
- **생성**: 2026-08-26
- **선행**: [challenge-result](../challenge-result/summary.md) — 이 feature 가 소비하는 데이터
  (`user_stats` 의 `losses`·`current_loss_streak` + 집계 배관)를 그것이 완성했다

## 배경

2026-08-06 기획 전면 개정의 **축 반전 1건** — 명예의 전당(승자 랭킹) → **개돼지 랭킹(패자 랭킹)**.
*"패배의 왕좌 — 많이 진 놈이 대장."* 정의는 repos.json 에 박제돼 있다:
**총 패배 수·연패·패율로 정렬, 1위 = 개돼지왕, 목록명 '수치의 명단', 범위는 친구 한정 단일 목록.**
4탭 중 랭킹 탭이 마지막 placeholder 다 — 이 feature 로 살아난다.

## §0 사전 실측

| | 상태 |
|---|---|
| **데이터** — `user_stats.losses`/`total_challenges`/`current_loss_streak`/`max_loss_streak` | ✅ V1+V10. challenge-result 판정 트랜잭션이 채운다. **실데이터 검증까지 끝난 상태** |
| `friendships` (accepted 친구 관계) + `FriendService` | ✅ friends feature 부터 운용 중 |
| **디자인** — Lovable `ranking.tsx` (116줄) | ✅ **완성돼 있다** — 헤더("개돼지 랭킹 🐷 / 패배의 왕좌") + **Top3 포디움**(1위 개돼지왕: fire-gradient + 🐷 wiggle + pulse-fire) + **"수치의 명단"** 전체 리스트(rank·아바타·이름·`N패 · 패배율 N%`·연패 `🐷N` 뱃지). 인당 필드 3종: `losses`/`lossRate`/`lossStreak` |
| 모바일 `:feature:ranking` | `PlaceholderScreen("랭킹")` 한 줄 — 도메인~remote 계층 전부 신설 대상 |
| 랭킹 엔드포인트 | ❌ 0건 — **이 feature 의 유일한 신규 API** |
| 프로필 이모지 아바타 (mock 😤😏) | ❌ 도메인에 없음 — VS 헤더와 같은 결정(이니셜 placeholder) 재사용 |

## 사용자 시나리오

1. 랭킹 탭 진입 → **나 + 내 친구들**이 패배 기준으로 줄 세워진 목록을 본다. 1위가 개돼지왕 🐷.
2. 내가 몇 위인지 본다 — 목록 안에 "나"도 포함된다 (Lovable mock 의 rank 4 "나").
3. 친구가 없으면(또는 아무도 챌린지를 안 했으면) 빈 상태를 본다.

## 수용 기준

- [ ] `GET` 랭킹 API 가 **나 + accepted 친구**의 목록을 정렬·rank 부여해 내려준다 (친구 한정 — 전체 유저 아님)
- [ ] 정렬 기준이 기획 정의(총 패배·연패·패율)를 따르고 **동률 규칙까지 계약에 명시**된다
- [ ] 패배율 = `losses / total_challenges`. 🔴 **`total = 0` (0/0) 처리 방식이 계약에 명시**된다
- [ ] `user_stats` row 가 없는 유저(챌린지 0회)도 목록에서 빠지지 않는다 (0패로 표시 — LEFT JOIN 선례)
- [ ] 화면: Top3 포디움 + 수치의 명단 리스트, Lovable 디자인 정합 (토큰 카탈로그 준수)
- [ ] "나" 항목이 식별된다 (계약에 식별 방식 명시 — userId 대조 or `isMe`)
- [ ] 빈 상태(친구 0명)가 화면으로 처리된다
- [ ] 테스트 결과 숫자로 (Android+iOS)

## 비범위 (Out of Scope)

- **결과 히스토리 화면** — 백로그 🟡 별건 (이번에 안 묶는다. 랭킹 탭과 화면 축이 다르다)
- **1:1 친구별 전적 화면** (`friend_records` 소비, §3.2) — 데이터는 쌓이는 중. 별도 feature
- 전체 유저 랭킹 / 기간별(주간·월간) 랭킹 — 기획에 없음
- 프로필 이모지 선택 기능 — 도메인에 필드 없음. 이니셜 placeholder (기존 결정 재사용)
- 랭킹 변동 알림 — 알림은 전부 후속

## 태스크 분해

### 백엔드 (backend-dev)

- [ ] **T-B1. 랭킹 API** — 나+친구 `user_stats` 조인 조회, 정렬·rank 서버 부여(앱이 다시 세지 않게),
  패배율 계산 주체·0/0·동률·row 부재 정책을 **계약으로 확정**. 마이그레이션 0건 예상.
  페이지네이션: 친구 한정 소규모라 **미적용이 기본** — 다르게 가려면 프로젝트 통일 규칙과 함께 근거

### 모바일 (mobile-dev)

- [ ] **T-M1. 도메인~remote 계층** — 계약 confirmed 후
- [ ] **T-M2. 랭킹 화면** — placeholder 교체: Top3 포디움 + 수치의 명단 (design.md 정본)
- [ ] **T-M3. 테스트** — 숫자로

### 디자인 (design-bridge)

- [ ] **T-D1. design.md** — `ranking.tsx` → Compose 명세. 특히: fire-gradient·wiggle·pulse-fire
  애니메이션의 구현/보류 판정(백로그의 FAB pulse-fire 미구현과 같은 축), Top3 포디움 레이아웃,
  이모지 아바타 → 이니셜 placeholder 대체 명시

## 의존 관계

```
T-B1(계약 초안) ⇄ mobile 협의 → confirmed → T-M1 → T-M2 → T-M3
T-D1 은 병렬 (T-M2 전까지만 도착하면 됨)
```

## 리스크 / 오픈 이슈

- **정렬 우선순위** — 기획은 "총 패배·연패·패율"을 나열만 했다. 1차 키가 무엇인지, 동률이면 어느
  순서인지 계약 협의로 확정 (Lovable mock 은 losses DESC 순으로 보이나 mock 이 근거는 아니다)
- **"나" 포함 여부의 재확인** — Lovable mock 에 "나"(rank 4)가 있어 포함으로 간주. 계약에 명시
- 친구가 많아질 때의 상한 — 지금 규모에선 무의미. 계약에 "미적용 + 재검토 조건"만 남긴다
