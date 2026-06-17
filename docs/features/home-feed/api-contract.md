# API Contract — 홈 피드 (home-feed)

- **feature-id**: home-feed
- **상태**: confirmed (v2)
- **최종 수정**: 2026-06-15 by pm-lead (v2 — `/home` 폐기, `/record` + `/challenges/active` 분리)

## 엔드포인트 요약
| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| GET | /api/v1/record | 내 누적 전적 조회 | Bearer JWT |
| GET | /api/v1/challenges/active | 진행 중 챌린지 목록 조회 | Bearer JWT |

> v1의 `GET /api/v1/home` 단일 엔드포인트는 **폐기**. 전적/챌린지 캐시 주기를 따로 가져갈 수 있도록 분리. 모바일은 두 API를 병렬 호출 후 결합(`GetHomeDataUseCase`).

---

## GET /api/v1/record

### 설명
인증된 사용자의 **누적 전적**을 단건 반환. `user_stats` row가 없는 신규 사용자도 동일 엔드포인트(0으로 채움).

### 인증
- 방식: `Bearer JWT`
- 스코프/권한: 일반 인증된 사용자

### Path / Query / Request Body
없음. 현재 사용자는 JWT subject로 식별.

### 성공 Response (HTTP 200)

```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "win": 7,
    "lose": 3,
    "draw": 2,
    "currentStreak": 3
  }
}
```

서버 타입:
```kotlin
data class RecordResponse(val data: RecordData) : BaseResponse()
data class RecordData(
    val win: Int,
    val lose: Int,
    val draw: Int,
    val currentStreak: Int,
)
```

### 빈 상태 응답 (신규 사용자)
```json
{ "error": false, "code": 200, "message": "",
  "data": { "win": 0, "lose": 0, "draw": 0, "currentStreak": 0 } }
```
- user_stats row가 없으면 백엔드가 0으로 채워서 응답.

### user_stats 집계 규칙
- `CHALLENGER_WIN` → 챌린저는 win+1, 상대는 lose+1
- `OPPONENT_WIN` → 상대는 win+1, 챌린저는 lose+1
- `DRAW` → 양쪽 draw+1
- `BOTH_LOSE` → 양쪽 lose+1
- `currentStreak` = 가장 최근 결과 시점부터 **win 만 연속**된 횟수. lose/draw/both_lose 발생 시 0으로 초기화.

### 백엔드측 주의사항
- DB 테이블명은 `user_stats` 그대로(V1 마이그레이션 호환). 도메인 네이밍만 `UserRecord`로 정렬, JPA `@Table(name = "user_stats")` 매핑.
- `user_stats` 단건 조회 1쿼리.

---

## GET /api/v1/challenges/active

### 설명
인증된 사용자가 challenger 또는 opponent인 **`IN_PROGRESS` 챌린지 목록**을 `deadline` 오름차순으로 반환. 진행 중 챌린지가 없으면 빈 배열.

### 인증
- 방식: `Bearer JWT`

### Path / Query / Request Body
없음.

### 성공 Response (HTTP 200)

```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "activeChallenges": [
      {
        "challengeId": 1001,
        "myMission": "오늘 운동 1시간 하기",
        "opponentNickname": "민수",
        "opponentMission": "책 30페이지 읽기",
        "deadline": "2026-05-26T00:00:00Z",
        "myVerificationStatus": "PENDING",
        "opponentVerificationStatus": "VERIFIED",
        "bet": "커피 사기 ☕"
      }
    ]
  }
}
```

서버 타입:
```kotlin
data class ActiveChallengeResponse(val data: ActiveChallengeListData) : BaseResponse()
data class ActiveChallengeListData(
    val activeChallenges: List<ActiveChallengeDto>,
)
data class ActiveChallengeDto(
    val challengeId: Long,
    val myMission: String,
    val opponentNickname: String,
    val opponentMission: String,
    val deadline: Instant,             // ISO-8601 UTC
    val myVerificationStatus: VerificationStatus,
    val opponentVerificationStatus: VerificationStatus,
    val bet: String,
)
enum class VerificationStatus { PENDING, VERIFIED, FAILED }
```

### 빈 상태 응답
```json
{ "error": false, "code": 200, "message": "", "data": { "activeChallenges": [] } }
```
- `activeChallenges`는 빈 배열로 응답 (null 금지).

### 페이지네이션 / 정렬
- 페이지네이션 없음. 진행 중 챌린지는 사용자당 동시 진행 한도로 제한(별도 정책).
- 정렬: `deadline` 오름차순(백엔드 처리).

### 챌린지 상태 필터
- 응답에 포함: `IN_PROGRESS` 만 (1차).
- 응답에서 제외: `PENDING`, `ACCEPTED`, `REJECTED`, `CONTRACT_SIGNING`, `COMPLETED`, `EXPIRED`.
- 향후 확장: `CONTRACT_SIGNING` 도 포함 필요 시 별도 협의.

### 백엔드측 주의사항
- 3쿼리 단일 read 트랜잭션(N+1 회피): ① challenges 조회 ② users 일괄(상대 닉네임) ③ verifications 일괄.
- 챌린지 ↔ users JOIN: challenger/opponent 양쪽에 현재 사용자가 있을 수 있음. 응답 시 "내" 미션과 "상대" 미션을 항상 현재 사용자 기준으로 매핑.
- verification row 없으면 양측 PENDING으로 응답.

---

## 공통: 에러 Response (HTTP 200, body의 code로 구분)

| code | 상황 | 예시 메시지 |
|------|------|-----------|
| 401 | 토큰 만료 | "토큰 만료 — Refresh" |
| 702 | 서버 일시 장애 | "잠시 후 다시 시도해주세요" |

에러 바디 shape:
```json
{ "error": true, "code": 401, "message": "토큰 만료 — Refresh" }
```

ADR-0002에 따라 HTTP는 항상 200, code로 분기. ADR-0009/auth-refresh-rotation로 일반 API 401은 모바일 Ktor Auth 플러그인이 자동 갱신 시도, `/auth/refresh` 401은 강제 로그아웃.

---

## 모바일측 주의사항

- 두 API는 **병렬 호출**(`GetHomeDataUseCase`에서 결합). 각각 독립 Flow.
- Repository 시그니처는 프로젝트 표준 `fun get(...)(onError: (String) -> Unit): Flow<T>`.
- 401은 RepositoryImpl 내부에서 `AuthEventBus.emitSessionExpired()`로 발행 → `MainScreen`이 collect해서 로그인 탭으로 강제 이동(글로벌 처리). 화면별 `NavigateToLogin` effect 없음.
- 응답 캐시 정책: 메모리 캐시만(StateFlow), 디스크 캐시 없음. 진입할 때마다 호출.
- 빈 상태 판정: `record.isEmpty && challenges.isEmpty()` → `FIRST_USER`, `challenges.isEmpty()` 만 true → `NO_ACTIVE_CHALLENGE`. `HomeUiState.Data.emptyType` derived 프로퍼티.
- `deadline`이 `Instant`(ISO-8601 UTC) → 상대 시간 텍스트는 모바일에서 변환.

---

## 협의 이력
| 일시 | 작성자 | 변경 |
|------|--------|------|
| 2026-05-25 | pm-lead | 초안 작성 (draft) |
| 2026-05-25 | pm-lead | 모바일/백엔드 양측 구현 완료, 계약 변경 0건 → `confirmed` 전환 |
| 2026-06-15 | pm-lead | **v2** — `/api/v1/home` 폐기, `/api/v1/record` + `/api/v1/challenges/active` 분리. 모바일 Repository 표준 패턴(Flow + onError + AuthEventBus) 정렬. 자세한 사항은 [change-log.md](./change-log.md). |
