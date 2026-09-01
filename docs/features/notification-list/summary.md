# 알림 목록 (notification-list) — Summary

- **feature-id**: notification-list
- **완료일**: 2026-09-01
- **상태**: **implemented** — 전 범위 구현·검증 완료. 🔴 **양 레포 미커밋**(서버 12파일 · 앱 34경로) · 실기 미확인
  > `completed` 로 적지 않은 이유는 부분 구현이라서가 아니다. **범위는 전부 닫혔고 검증도 끝났는데
  > 결과물이 아직 working tree 에만 있다.** 커밋 전까지는 없는 것과 같다는 선례가 이 프로젝트에 있다
  > (`scripts/e2e-off.sh` 유실). 사용자 커밋 후 `completed` 로 전환한다.

## 구현 개요

**알림은 오는데 볼 곳이 없던 상태를 닫았다.** `notifications` row 는 push-fcm 부터 쌓이고 홈 벨도
이미 연결돼 있었는데 그 화면이 `PlaceholderScreen` 이었다. 조회 API 3개와 화면을 만들어
**푸시를 놓치면 그걸로 끝**이던 구조를 없앴다.

범위가 진행 중 두 번 늘었다 — **읽음 처리와 홈 벨 뱃지**가 비범위에서 범위로 들어왔다.
근거는 *"목록의 존재 이유가 푸시를 놓쳤을 때인데, 안 읽은 것을 구분 못 하면 목적이 반쪽"* 이고,
**뱃지는 사용자가 「볼 게 있다」를 아는 유일한 신호**라 그게 빠지면 목록을 열 이유를 못 만든다.

## 엔드포인트

| Method | Path | 상태 |
|--------|------|------|
| GET | `/api/v1/notifications?cursor=&size=` | implemented (미배포·미커밋) |
| GET | `/api/v1/notifications/unread-count` | implemented (미배포·미커밋) |
| POST | `/api/v1/notifications/read-all` | implemented (미배포·미커밋) |

**마이그레이션 0건 · `SecurityConfig` 무변경** — 쓰는 것이 전부 V1 자산이다(`is_read` 컬럼 포함).

## 화면 / UI 변경

- **알림 목록**(신규 `:feature:notification`) — `MainScreen.kt:228` 의 `PlaceholderScreen` 교체.
  타입별 아이콘·색, 경과 시각, 커서 무한 스크롤, 빈 상태, 탭 → 딥링크
- **홈 벨 뱃지 점등** — `HomeScreen.kt:61`. 🔴 **`:125`(로딩 화면)는 `false` 유지**
- 🔵 **앱에 `PlaceholderScreen` 소비처가 0건이 됐다** — 알림이 마지막이었다. 기획서 §4 IA 의
  진입 경로 중 **빈 화면으로 끝나는 것이 하나도 안 남았다**

## 주요 변경 파일

**모바일** (34 경로 — 신규 15 · 수정 19)
- `feature/notification/` — 신규 모듈 14파일
- `core/push/PushEventRoute.kt` — `toRoute()` 승격(`MainViewModel` private → public)
- `core/utils/.../ElapsedTimeFormat.kt` — `toElapsedKoreanString` 신규
- `feature/home/HomeScreen.kt` · `GetHomeDataUseCase` — 뱃지 배선
- `core/utils/.../WireFormatBaselineTest.kt` — 백틱 함수명 1건 rename(iOS 개통)

**백엔드** (12파일 — 신규 6 · 수정 6)
- `controller/.../NotificationController.kt` · `service/.../NotificationQueryService`·`CommandService`
- `infra/jpa/.../NotificationJpaRepository.kt` — 커서 JPQL
- `infra/entity/.../NotificationEntity.kt` — KDoc 만(로직 무변경)

## 테스트 결과

**모바일 — Android 162/162 · iOS 162/162, failures 0 · errors 0** (pm 이 XML 원문에서 재집계)

| 모듈 | AND | iOS |
|---|---|---|
| `:feature:notification`(신규) | 23 | 23 |
| `:remote:model` | 21 | 21 |
| `:core:push` | 24 | 24 |
| `:feature:home` | 27 | 27 |
| `:feature:main` | 17 | 17 |
| `:core:utils` | 50 | 50 |

신규 약 57건. `:composeApp` Android 컴파일 통과. ⚠️ 첫 실행은 `BUILD FAILED`(타입 추론)였고
**단언의 의미·값·개수를 그대로 둔 채 기대값에 타입 인자만 명시**해 고쳤다.

**백엔드 — 535/486 → 589/540 passed, failures 0, 회귀 0** (증가 54 전부 신규).
skipped 49 는 기존 Docker 부재 블로커로 변동 없음.

🔴 **실구동 21항목** — 이 레포 단위 테스트는 JPA 를 mock 으로 대체해 **통과한 540건 중 어느 것도
새 JPQL 을 실제 DB 에 실행하지 않는다.** throwaway DB(`challenge_noti_verify` · 포트 8088)로
확인했고 공용 DB·`:8080` 불가침 유지 + 종료 후 정리까지 확인했다.

## 결정 사항

### 1. 페이지네이션 = 커서 → [ADR-0012](../../decisions/0012-list-pagination-cursor.md) 승격
프로젝트 최초 도입이라 규약을 열었다. offset 기각 근거는 일반론이 아니라 **알림은 정의상 새 행이
머리에 꽂히므로 페이지 밀림이 드문 경합이 아니라 상시 조건**이라는 것.
🔴 **정렬·커서 키는 `id`, `created_at` 이 아니다** — `created_at` 은 엔티티가 실어 보내는 값이라
시계 보정에 밀리면 삽입 순서와 어긋나고, **어긋난 구간이 예외도 로그도 없이 건너뛰어진다.**
**표시는 시각, 순서는 id.**

### 2. 읽음 처리 = (B) 전체 읽음
행 단위를 버리는 대신 *"목록을 열면 전부"* 로 고정해 **"언제 읽음인가"라는 기획 결정을 소멸시킨다.**
🔴 **응답에 `isRead` 필드가 아예 없다**(서버 테스트가 `doesNotExist()` 로 고정) — 없는 것이지
항상 false 인 게 아니다.
🔵 **`read-all` 이 개수를 돌려주는 이유**: 앱이 *"불렀으니 0"* 이라는 **규칙을 갖지 않게** 하려고.
앱은 서버가 준 값 하나만 본다. 서버도 0 을 하드코딩하지 않고 UPDATE 후 다시 COUNT 한다 —
**조건이 잘못돼 한 행도 안 바뀌면 즉시 드러난다.**

### 3. `type` 은 열린 집합(String)
wire 바이트는 enum 이든 String 이든 같고 **달라지는 것은 OpenAPI 스키마**다. enum 으로 내면
닫힌 집합을 광고해 모바일이 typed enum 을 만들고, **새 타입 한 행에 응답 전체 역직렬화가 깨져
알림 화면이 통째로 빈다.**

### 4. `title` 제거 (초안 뒤집음)
`title` 4종이 `영혼의 맹세`/`계약 완료.`/`ㅠㅠ`/`증거 도착` — 푸시 헤드라인이라 목록에서 홀로
못 선다. 🔵 초안 논거의 오류는 *"`title` 이 담은 것은 정보가 아니라 톤"* 이었다는 것이고,
비용 판단도 틀렸다 — *"뺄 때 breaking"* 은 **이미 쓰이고 있을 때만** 성립한다.

### 5. 뱃지는 점, 숫자로 가지 않는다
(B) 아래서 **숫자는 사용자의 행동을 바꾸지 못한다** — 열면 전부 읽음이라 3이든 17이든 할 수 있는
것은 "연다" 하나다. 숫자는 선택지를 바꿀 때만 값이 있다.

### 6. 경과 시각은 신규 포맷터 — 기존 함수 재사용 불가
`toRelativeKoreanString` 은 마감까지 **남은** 시간용이라 과거 시각에 `"마감"` 을 반환한다.
알림 시각은 전부 과거라 그대로 썼으면 **모든 행이 "마감"** 이었다.
🔴 **`"N시간 전"`(산술)을 `"어제"`(달력)보다 먼저 평가한다** — 두 축을 한 자료로 계산하면 반드시
거짓이 난다. 구현은 축 자체를 분리했다(경과는 `toInstant` 차, 어제는 `daysUntil`).

## 미해결 이슈

| # | 내용 | 담당 |
|---|---|---|
| 1 | 🔴 **양 레포 미커밋** — 서버 12파일 · 앱 34경로 | user |
| 2 | **실기 검증 0건** — 무한 스크롤 트리거, 뱃지 점등·소거 | user |
| 3 | 🟡 **`"민수과 계약을 하시렵니까?"`** 조사 결함. 사용자 확정 문구라 안 건드렸다 — **확정 당시엔 푸시밖에 없었고 목록은 남는다**(노출 조건 변화) | user |
| 4 | 뱃지 위치 육안 검증(정본 6px vs 구현 10dp) — **점이 처음 켜지므로** 실물 보고 판단 | design |
| 5 | 서버 강등 존치(enum 밖 `type` → `CHALLENGE_REQUEST`). 오늘 도달 경로 없음, 트리거는 롤링 배포 | backend |
| 6 | 목록용 인덱스 `(user_id, id DESC)` 미생성 — 관측 후 추가 | backend |
| 7 | 백틱 잔존 2모듈(위반 22 → iOS 54건) · `PlaceholderScreen` 소비처 0건 | mobile |
| 8 | 기준 시각 공유가 간접 검증 | mobile |

## 이 feature 에서 값이 컸던 것 — 전부 "조용히 틀리는" 것을 잡은 사례다

1. **`toRelativeKoreanString` 재사용** — 썼으면 모든 행이 `"마감"`. 컴파일도 테스트도 통과한다.
2. **서버 타입 강등** — 모르는 알림이 *"도전장 도착"* 으로 둔갑. **모르는 값보다 나쁘다 —
   아는 척하는 오답이라 앱이 방어할 표면이 없다.**
3. 🔴 **폴백 KDoc 의 거짓 근거** — *"서버가 원문을 내린다"* 가 **폴백의 정당화 자리**에 거짓으로
   적혀 있었다. 강등이 고쳐지는 날 누가 그 줄을 읽고 폴백을 걷어내면 **근거를 확인한 셈이 된다.**
4. **정렬 축** — `id` 와 `created_at` 은 **평소에 같은 결과를 낸다.** 어긋날 때만 다르고,
   그때는 행이 조용히 건너뛰어진다. backend 가 두 축을 **갈라놓는 시드**로 증명했다.
5. **숫자 5중 복제** — *"나머지 4종"* 이 계약 한 줄에서 ADR·CLAUDE.md·백로그·report 로 번졌다.
   🔴 **4곳이 일치했지만 일치한 쪽이 전부 틀렸다 — 복제본끼리의 합의는 원본의 증거가 아니다.**

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md)(`confirmed`) · [design.md](./design.md)
- [mobile-report.md](./mobile-report.md) · [backend-report.md](./backend-report.md) · [change-log.md](./change-log.md)
- [ADR-0012 목록 페이지네이션](../../decisions/0012-list-pagination-cursor.md)
