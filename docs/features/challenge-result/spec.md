# 챌린지 결과 판정 (challenge-result) — Spec

- **feature-id**: challenge-result
- **owner**: pm-lead
- **상태**: completed (2026-08-25 — [summary.md](./summary.md))
- **생성**: 2026-08-25
- **선행**: [challenge-verification](../challenge-verification/summary.md) — 이 feature 는 그것이 남긴 `VERIFIED` row 와 `verified_at` 을 **읽기만** 한다
- **범위 결정**: 🔴 **`RESULT`·`REMIND` FCM 알림 제외** (2026-08-25 사용자 결정 — [backlog 등재](../../backlog.md)). 배치는 DB 전이만 한다

## 배경

핵심 플로우의 마지막 미개통 구간이다: *"… 양측 인증(카메라) → **자정 직후 배치 판정 → 결과**"*.
기획서 §2.6 이 원안이며 판정 규칙은 세 줄이 전부다:

```
- 양측 모두 인증 완료 → 무승부
- 한쪽만 인증        → 인증한 쪽 승리
- 양측 모두 미인증    → 양쪽 모두 패배
```

§2.5 의 4번째 줄 *"인증 마감 시간 전까지 미인증 시 자동 패배"* 도 여기서 이행한다
(challenge-verification 이 명시적으로 이월).

## §0 사전 실측 — 스키마는 처음부터 다 있었다. 없는 것은 배치뿐

| | 상태 |
|---|---|
| `challenges.result` 컬럼 + `ChallengeResult` 4종 enum (`CHALLENGER_WIN`/`OPPONENT_WIN`/`DRAW`/`BOTH_LOSE`) | ✅ **V1 부터 존재.** 도메인 KDoc: *"result 는 COMPLETED 되기 전까지 null"* |
| `ChallengeStatus.COMPLETED` / `EXPIRED` | ✅ enum 존재. **전이시키는 코드 0건** |
| `user_stats` (total/wins/losses/draws/current_streak/max_streak) · `friend_records` | ✅ V1 존재. **쓰는 코드 0건 — 홈 `GET /record` 가 이미 읽고 있어서 집계가 붙는 순간 홈 전적(StatsBar)이 실데이터가 된다** |
| `:batch` 모듈 | `build.gradle.kts` 만 있고 **`.kt` 0개**. ⚠️ 의존이 `:core`+`:domain:model` 뿐 — 리포지토리·서비스 접근 배선부터 필요 |
| `@Scheduled` / `@EnableScheduling` | ❌ 레포 전체 0건 — **이 프로젝트 첫 스케줄러다** |
| `EXPIRED` 전이 | ❌ 배치 부재. `accept()` 가 마감 지난 PENDING 을 *"마감이 지난 챌린지예요"* 로 거부만 한다. `ChallengeRepository` KDoc 이 배치 부재를 명시. **백로그 항목** |
| `GET /challenges/{id}` 응답의 `result` | ❌ **없다.** `status` 만 내려간다 — 결과를 보여주려면 wire 변경 필요 (`confirmed` 계약 → change-log) |
| 모바일의 `result`/`COMPLETED` 소비 | ❌ 0건 |
| `deadline` 의미 | **익일 00:00 배타적 끝점** (challenge-verification 에서 실측·문서화) — 자정 직후 배치가 `deadline <= now` 를 판정 대상으로 잡으면 정확히 맞물린다 |

## 사용자 시나리오

1. 챌린지 마감(자정)이 지나면, **아무도 아무것도 하지 않아도** 서버 배치가 §2.6 규칙으로 판정한다.
2. 사용자가 앱에 들어오면 결과를 본다 — 홈 카드에 결과가 표시되고, 상세에서 결과 + 양측 인증 사진을 확인한다.
   (푸시는 없다 — 사용자 결정. 앱에 들어와야 안다는 트레이드오프를 인지하고 받았다)
3. 홈 전적(승/패/무/연승)이 실제 숫자로 채워진다 — 지금까지는 전부 0 이었다.
4. 신청만 하고 방치된 챌린지(PENDING)는 마감이 지나면 자동 만료(EXPIRED)된다.

## 수용 기준

- [ ] 자정 직후 배치가 `deadline <= now` 인 `IN_PROGRESS` 를 전부 판정한다: 양측 VERIFIED→`DRAW` / 한쪽만→그쪽 승 / 양측 미인증→`BOTH_LOSE`. `COMPLETED` + `result` 기록
- [ ] 판정 시 미인증 party 의 `verifications.status` 가 `PENDING → FAILED` 로 전이된다
- [ ] `deadline <= now` 인 `PENDING` 챌린지는 `EXPIRED` 로 전이된다 (백로그 해소)
- [ ] 🔴 **배치가 멱등이다** — 같은 배치를 두 번 돌려도 결과·집계가 두 번 반영되지 않는다
- [ ] 🔴 **서버가 자정에 죽어 있었어도** 다음 기동/실행 시 미판정분이 소급 판정된다 (판정 기준은 실행 시각이 아니라 `deadline`)
- [ ] `user_stats` 가 정확히 갱신된다 — 숫자로 검증 (예: 승 1 → wins=1, total=1, streak=1)
- [ ] 판정 후 상세 조회에 `result` 가 내려가고 앱이 결과를 표시한다
- [ ] 🔴 **알림이 발송되지 않는다** — `notifications` row 증가 0 (범위 제외 검증)
- [ ] 시간 기준은 전부 KST (ADR-0010) — 배치 스케줄 표기·판정 비교 모두

## 비범위 (Out of Scope)

- 🔴 **`RESULT`·`REMIND` 푸시** — 사용자 결정(2026-08-25). 나중에 붙일 때: 배관 재사용 + §0.6.1 통지 절차
- **결과 카드 생성** (기획 §2.6 *"계약서와 함께 결과 카드"*) — 디자인 없음. 상세 화면 결과 표시로 갈음하고 디자인이 나오면 별도
- **개돼지 랭킹** — 이 feature 의 집계를 소비하는 다음 feature. 준비만 한다 — 단 ⚠️ **준비의 범위가
  spec 초판보다 커졌다**: `friend_records` 에 더해 🔴 **연패 2컬럼(`current_loss_streak`/`max_loss_streak`)
  마이그레이션 + 집계를 이번에 포함**한다 (2026-08-25 pm-lead 정정 — backlog 🟡 32행이 2026-08-06 부터
  "판정 feature 스코프"로 예약해 둔 항목인데 초판이 놓쳤다. backend-dev 지적. 결정 근거: 지금은
  마이그레이션 + 집계 2줄이지만, **나중이면 과거 결과 순서를 되짚는 백필**이 필요해 비용의 종류가
  달라진다. 랭킹 자체(화면·API)는 여전히 비범위)
- 월별 달성 캘린더 · 재대결
- 무승부/진위 판정 규칙 재론 — 원안 유지 (repos.json 사용자 결정)

## 태스크 분해

### 백엔드 (backend-dev)

- [ ] **T-B1. `:batch` 인프라** — 모듈 의존 배선(리포지토리 접근) + 스케줄링 방식 결정(첫 스케줄러 — `@Scheduled` vs 대안, 근거 남길 것) + 자정 직후 실행 + **미판정 소급** 보장
- [ ] **T-B2. 판정 서비스** — §2.6 3규칙 + `FAILED` 전이 + `EXPIRED` 전이. 🔴 멱등성(재실행 안전) 필수. 판정 규칙은 **한 곳**에만 (challenge-verification spec 이 *"절반만 구현하면 규칙이 두 곳에 흩어진다"* 며 경계한 지점)
- [ ] **T-B3. 전적 집계** — `user_stats`(+ `friend_records` 권장) 판정 트랜잭션에서 갱신. ⚠️ **무승부·양패 시 streak 처리를 정하고 계약/문서에 명시** (오픈 이슈)
- [ ] **T-B4. wire 노출** — `GET /challenges/{id}` 에 `result` 추가(🔴 soul-oath `confirmed` 계약 변경 → change-log 등재 필수) + 홈 목록의 COMPLETED 노출 정책(아래 오픈 이슈) 계약 확정

### 모바일 (mobile-dev)

- [ ] **T-M1. 도메인/DTO** — `result` 수용 (nullable, 모르는 값 방어는 기존 status 선례)
- [ ] **T-M2. 상세 결과 표시** — 승/패/무 표시 + `COMPLETED` 시 남은 시간 → 결과 전환. challenge-verification [design.md §7](../challenge-verification/design.md) 의 ①(내 인증 후 카드)·③(판정 대기 표기)·⑦(FAILED 뱃지) 제안값이 여기서 소비된다. **디자인 없음 — 기존 토큰·패턴으로, 교체 전제**
- [ ] **T-M3. 홈 카드 결과 반영** — T-B4 정책 확정 후
- [ ] **T-M4. 테스트** — 숫자로

### 디자인

**design-bridge 제외** — Lovable 에 결과 화면·결과 카드가 0건임을 challenge-verification 때 실측했다.
상세 design.md §7 제안값 재사용 + 디자이너 확인 대상에 이미 등재돼 있다.

## 의존 관계

```
T-B1 → T-B2 → T-B3
        └──→ T-B4 ─(계약 confirmed)→ T-M1 → T-M2 · T-M3 → T-M4
```

계약 협의의 실질 쟁점은 **T-B4 두 가지**(result 노출 위치·홈 COMPLETED 정책)다. 배치 자체는 wire 가 없다.

## 리스크 / 오픈 이슈

- 🔴 **결과 확인 진입 경로** — 홈 active 는 현재 `IN_PROGRESS` 만 응답한다. 판정되는 순간 챌린지가 홈에서
  사라지고, **푸시도 없으므로 사용자가 결과에 도달할 경로가 없다.**
  ✅ **확정 (2026-08-25 pm-lead, result-mobile 실측 반영)**: 홈 목록에 COMPLETED 를 **판정 후 7일** 한시
  노출(카드에 결과 뱃지). 초안의 3일에서 늘린 이유 — **히스토리 화면이 없어 창이 닫히면 그 결과는 앱
  어디에서도 영영 도달 불가**가 되기 때문(mypage 는 전적 숫자만). 7일은 시간벌기이지 해법이 아니며
  🔴 **"결과 히스토리 화면 부재"를 백로그에 등재**한다. `/challenges/active` 는 `confirmed` 계약 변경이라
  change-log 등재. `ActiveChallengeService.ACTIVE_STATUSES` 가 정확히 이 확장을 예고하고 만든 자리다
- ~~무승부·양패의 streak 의미 — backend 제안 → 계약 명시~~ ✅ **stale 정정 (2026-08-25, result-mobile
  발견)**: **열린 쟁점이 아니다.** home-feed api-contract(`confirmed` v2, 2026-06-15)가 집계 규칙을 이미
  확정했다 — 결과 4종별 증감 + `currentStreak = win 만 연속, lose/draw/both_lose 시 0`. 앱이 그 위에
  출시돼 있다(홈 StatsBar "연승" 라벨, `UserRecord` KDoc). **이 feature 는 그 계약의 이행**이며,
  challenge-result 계약 §3 은 규칙을 재서술하지 않고 **"home-feed 계약 승계" 한 줄**로 참조한다
  (두 곳에 쓰면 갈라진다)
- **배치 실행 시각·재시도** — 자정 "직후"의 구체값(예: 00:05 KST), 실패 시 재시도 정책. T-B1 에서 결정
- KST 자정 경계 — 서버 시계·`LocalDateTime` 비교는 ADR-0010 체계라 일관되나, 배치 스케줄 표현(cron)의
  타임존 명시 누락이 고전적 함정
