# 챌린지 결과 판정 (challenge-result) — Summary

- **feature-id**: challenge-result
- **완료일**: 2026-08-25
- **상태**: **completed** (서버는 실데이터 소급 판정까지 실측 완료. 모바일은 양 플랫폼 테스트까지 —
  디바이스 실기 확인은 미해결에 등재)

## 구현 개요

핵심 플로우의 마지막 구간 개통 — **이제 챌린지가 스스로 끝난다.** 자정 직후(00:05 KST) 배치가
`deadline` 경과 `IN_PROGRESS` 를 기획 §2.6 규칙으로 판정해 `COMPLETED`+`result` 를 기록하고, 미인증
측을 `FAILED` 로, 방치된 `PENDING` 을 `EXPIRED` 로 전이하며, **전적(user_stats·friend_records)을
같은 트랜잭션에서 집계**한다. 홈 전적(StatsBar)이 처음으로 실데이터가 됐고, 연패 2컬럼(V10)까지
채워져 **개돼지 랭킹의 데이터 준비가 끝났다.** 이 프로젝트 **첫 스케줄러**(`:batch` 첫 코드)다.
🔴 **푸시는 없다** — RESULT·REMIND 제외는 사용자 결정(2026-08-25)이며, 결과 도달 경로로 홈에
COMPLETED 를 **판정 후 7일** 한시 노출한다.

## 엔드포인트

**신규 0건.** 기존 `confirmed` 응답 2개 확장 (양쪽 change-log 등재 완료):

| Method | Path | 변경 | 상태 |
|--------|------|------|------|
| GET | `/api/v1/challenges/{id}` | `result` 추가 (COMPLETED 아니면 null, 키 상존) | implemented |
| GET | `/api/v1/challenges/active` | `status`·`result`·`myResult` 추가 + COMPLETED 7일 노출 + 정렬(진행 중 먼저) | implemented |

## 화면 / UI 변경

- **상세**: VS 헤더 한 자리가 시간 순으로 전환 — `남은 시간` → `판정 대기 중` → `승리/패배/무승부/양측 패배`
- **홈**: `진행 중인 챌린지` / `최근 결과` 두 구획 분리(단일 배열이 섞이면 섹션 제목·빈 상태가 거짓말하는
  문제를 해소). 결과 카드는 남은 시간 자리에 결과 pill
- 승패무 색·아이콘·문구를 `:core:ui` `ChallengeOutcomePill` 로 승격 — "승리가 무슨 색인가"의 단일 출처

## 주요 변경 파일

**백엔드**: `:batch` 신설(스케줄러+판정 잡, 빈 2개 분리) · 판정·집계 순수 함수(`:domain:model`) ·
`V10__user_stats_loss_streak.sql` · Active/Detail DTO·서비스 확장
**모바일**: `ChallengeOutcomePill`(`:core:ui`) · 상세 `HeadlineDisplay`(구 DeadlineDisplay) ·
홈 2구획 + 결과 카드 · result 도메인~매퍼 (신설 4 / 삭제 1 / 수정 16, +1270 −150)

## 테스트 결과

- **백엔드: 392/392 passed** (437 중 통합 45 skip — 기존과 동일. 신규 72, 회귀 0)
- **모바일: Android 186/186 + iOS 165/165** (신규 +68: mapper 100·detail 41·home 24 등, 회귀 0.
  마감 후 backend 요청으로 `ActiveChallengeWireFixtureTest` 9건 추가 — active 응답의 실서버 원문
  픽스처가 유일하게 없던 구멍을 메움. `ignoreUnknownKeys` 를 끄면 홈이 통째로 죽는다는 것까지 실패 고정)
- **실서버 실측 2회** (`:8081`, 사용자 `:8080` 무중단, DB 전량 원복):
  ① 마감 최대 21일 경과 실데이터로 **소급 판정 증명** — 기동 1회에 `judged=6, expired=2`, 마감 전 1건
  무변경, `notifications` **14→14**(알림 제외 검증), 재실행 `judged=0`+`user_stats` 해시 동일(멱등)
  ② **V10 실DB 적용**(`validate` 통과 = 엔티티·SQL 정합의 유일한 증거), 연패 누적이 실데이터와 일치,
  `GET /record` 에 연패 필드 무노출 확인

## 결정 사항

1. 🔴 **RESULT·REMIND 푸시 제외** (사용자, 2026-08-25) — 배치는 DB 전이만. 미발송을 **구조로 보장**
   (판정 서비스에 이벤트 퍼블리셔 자체를 주입하지 않음). 추후 도입 시 배관 재사용 + §0.6.1 절차
2. **홈 COMPLETED 노출 = 판정 후 7일** — 히스토리 화면 부재로 창이 닫히면 영영 도달 불가라 3→7일 상향.
   "결과 히스토리 화면 부재"는 백로그 🟡 (N 은 서버 프로퍼티)
3. **`myResult` 4값** (`WIN/LOSE/DRAW/BOTH_LOSE`) — BOTH_LOSE 를 LOSE 로 접으면 앱이 인증 상태로
   역산해야 하고 그게 **판정 규칙의 두 번째 사본**이 된다. `amIChallenger` 안은 키 누락 시 승→패
   조용한 반전이라 기각. 상세는 역할 기준 유지 — **엔드포인트마다 좌표계를 일관되게**
4. **소급은 스케줄러가 아니라 쿼리가 보장** — 대상 선정이 `deadline <= now` 라 놓친 실행 보상 로직
   금지(두 번 도는 원인). 기동 시(`ApplicationReadyEvent`) 1회 실행으로 다운타임 보상
5. **판정~집계 단일 트랜잭션** — "승리인데 상대는 대기중" 창이 구조적으로 불가능함을 계약 §3.1 에 명시
6. **연승은 home-feed `confirmed` 계약의 이행** (win 만 연속 — 협의 대상이 아니었음을 발견) /
   **연패는 그 거울상** (패·양패 +1, 승·무 0. 무승부는 패배가 아니다)
7. **연패 2컬럼(V10) 이번 포함** — 백로그가 8/6 부터 예약한 스코프. 나중이면 completed_at 순회
   백필이 필요해 **비용의 종류가 다르다** (spec 초판의 비범위 판단을 정정)
8. **`EXPIRED` 는 판정이 아니다** — result null·무집계·홈 미노출·상세 미표기(도달 경로 전수 확인,
   홈 노출 시 뒤집힘 조건 명시)
9. **`status` 키 누락 → `IN_PROGRESS` 간주** (앱) — 필드 신설 전 응답의 의미 복원. 없으면 서버 배포 전
   앱 실행 시 홈이 통째로 비는 조용한 장애. 모르는 값은 기존 방침대로 드롭

## 미해결 이슈

- [ ] **사용자 실기(디바이스) 확인** — 홈 결과 카드·상세 결과 표시·판정 왕복. 서버 실측은 완료
- [ ] 🔵 결과 UI 디자이너 확인 — 홈 `"최근 결과"` 구획 제목(시안에 없는 신규 문구) + 결과 pill 표현.
  기획 §2.6 "결과 카드"도 디자인 대기
- [ ] "승리·무승부가 연패를 끊는" 분기 — 실측 데이터가 BOTH_LOSE 일색이라 단위 테스트로만 고정
- [ ] 배치 다중 인스턴스 가드가 in-process 뿐 (멱등이라 손상은 없음) · cron 실제 발화 시각은 테스트
  고정 불가(`zone` 누락 실패 모드 KDoc 박제) — ADR-0007 배포 시점 소관
- [ ] `friend_records` 를 읽는 wire 0건 — 개돼지 랭킹 feature 가 소비자
- [ ] 결과 히스토리 화면 부재 (백로그 🟡 — 7일은 시간벌기)

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md)
- [mobile-report.md](./mobile-report.md) · [backend-report.md](./backend-report.md)
- 소급 개정된 계약: [soul-oath](../soul-oath/change-log.md) · [home-feed](../home-feed/change-log.md)
