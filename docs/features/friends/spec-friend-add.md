# 친구 추가 feature spec

> **본 spec은 friends 1차 1단계(빈 상태 UI) 후속 작업**. 1차 1단계 spec(`spec.md`) / plan(`plan.md`) / summary(`summary.md`)는 historical artifact로 보존하고, 본 spec이 친구 시스템의 실제 동작 정의를 담당한다.

## 1. 개요

challenge 앱의 친구 시스템을 실제 동작 가능하도록 구현한다.

핵심 동작:
- 회원가입된 사용자를 닉네임으로 검색
- 친구 요청 보내기 → 받는 쪽이 수락하면 친구 관계 성립
- 받은 요청 / 보낸 요청 / 친구 목록 조회
- 카카오톡으로 challenge 앱을 안 쓰는 친구 초대 (KakaoLink)

## 2. 사전 컨텍스트 / 1차 1단계 spec drift 정정

friends 1차 1단계 spec/plan에 적힌 후속 작업 가이드와 실제 백엔드 V1 스키마가 다르다. 본 spec이 권위(authority)이며 1차 1단계 문서는 정정하지 않고 보존한다 (당시 결정의 흔적).

| # | 1차 1단계 문서 기술 | 실제 / 본 spec 결정 |
|---|---|---|
| 1 | "후속 V5 마이그레이션으로 `friendships(user_a_id, user_b_id, since)` 양방향 단일 row 생성" | **V1에 이미 `friendships` 테이블 존재** (`requester_id`, `receiver_id`, `status`, `created_at`, `accepted_at`). 단방향 1 row + status 갱신 모델. |
| 2 | "친구 목록 조회: `WHERE user_a_id = me OR user_b_id = me`" | `WHERE (requester_id = me OR receiver_id = me) AND status = 'ACCEPTED'` |
| 3 | "V5 마이그레이션 필요" | **DB 마이그레이션 0건** — V1 스키마 그대로 활용. |

정정 적용 방식: 1차 1단계 `summary.md`에 "본 spec(`spec-friend-add.md`)에서 정정됨" 한 줄만 추가.

## 3. 사용자 요구사항

1. **"앱에 회원가입된 유저 전체를 검색해서 친구 추가"** — 닉네임 검색 기반
2. **"카카오톡으로 친구 초대"** — KakaoLink 메시지 전송

## 4. 핵심 결정 사항

### 4.1 검색 식별자: 닉네임 contains 매칭

- 결정: `WHERE nickname LIKE '%query%'`
- 근거: 사용자 규모가 작음("친구 4명") + 친한 친구끼리만 쓰는 앱 특성. 닉네임 정확 매칭/prefix는 친구 닉네임 일부만 기억나는 경우 대응 불가.
- 가드:
  - **최소 입력 2자** (1자 이하는 결과 비움)
  - **결과 `LIMIT 20`** + UI에 "더 정확히 입력해주세요" 안내
  - **본인 제외** (`WHERE u.id != :me`)

### 4.2 친구 요청 흐름: 요청 → 수락 (양방향 동의)

- 결정: 양쪽 모두 동의해야 친구 관계 성립
- 근거:
  - V1 스키마가 4-state(`PENDING/ACCEPTED/REJECTED/BLOCKED`)로 이 흐름 전제
  - 동명이인 검색 시 잘못 추가하는 사고 방지 (받는 쪽이 거절 가능)
  - 챌린지 신청(맹세) UX와 톤 일치 — 양방향 동의가 자연스러움

### 4.3 검색 결과 사용자별 `relation` enum

서버가 검색 결과 각 사용자(`target`)에 대해 friendships row를 보고 계산해서 응답에 박아 내려준다. **DB에 별도 컬럼/테이블 없음 — 파생 값(derived)**.

| relation | 조건 (friendships row) | UI 액션 |
|---|---|---|
| `NONE` | row 없음 | `[친구 요청]` 버튼 |
| `REQUEST_SENT` | `requester_id = me AND receiver_id = target AND status = 'PENDING'` | `[요청 보냄]` 라벨 + `[X 취소]` 버튼 |
| `REQUEST_RECEIVED` | `requester_id = target AND receiver_id = me AND status = 'PENDING'` | `[수락]` 버튼 (검색에서 바로 수락 가능) |
| `FRIEND` | 양방향 어느 쪽이든 `status = 'ACCEPTED'` | `이미 친구` 뱃지 (액션 비활성) |
| `REJECTED` | `requester_id = me AND receiver_id = target AND status = 'REJECTED'` | `[다시 요청]` 버튼 |

**BLOCKED는 1차에서 미구현** — V1 스키마의 BLOCKED status는 비활성. 검색 결과에 BLOCKED 케이스는 노출되지 않음 (현재는 BLOCKED row가 생성될 경로가 없음).

**REJECTED 후 재요청 처리**: REJECTED row가 있을 때 동일 requester가 동일 receiver에게 sendRequest 호출 시 — 기존 row의 `status='PENDING'`, `accepted_at=null`로 UPDATE (created_at 유지). UNIQUE 제약 호환 + UX 유지.

### 4.4 알림: in-app만 (FCM 없음)

- 결정: 받는 쪽이 친구 화면 진입 시에만 친구 요청을 인지
- 친구 화면 메인에 "받은 요청 N건" 인라인 섹션 + 상단 배지
- FCM 통합은 별도 spec/plan으로 분리 (챌린지 응원/평가 등 더 우선순위 높은 알림과 함께 한꺼번에 도입)

### 4.5 카카오톡 초대: KakaoLink + 커스텀 템플릿

- 결정: 카카오 디벨로퍼스 콘솔에 등록한 커스텀 메시지 템플릿 사용
- "친구 추가"(앱 사용자 대상 검색)와 "친구 초대"(앱 미사용자 대상 KakaoLink) 두 진입점 명확히 분리
- 1차에서는 inviter 자동 연결 X (메시지 버튼 → 마켓 URL만)

### 4.6 진입 순서: 모바일 + 백엔드 동시

- DTO 계약을 `api-contract`로 먼저 확정 후 양쪽 병렬 진행
- subagent dispatch는 mobile-dev / backend-dev 동시 호출

### 4.7 차단(BLOCKED) 미구현 (1차 제외)

- 사용자 신고/스토킹 케이스 발생 시 별도 spec/plan으로 추가

## 5. 백엔드 — Spring Boot multi-module

### 5.1 Endpoints

모두 `Authorization: Bearer <access-token>` 필요. BaseResponse 패턴 (ADR-0002, HTTP 200 + code 기반 에러).

| Method | Path | 용도 | Request | Response data |
|---|---|---|---|---|
| `GET` | `/api/v1/users/search?nickname={q}` | 닉네임 contains 검색 (LIMIT 20) | query: `nickname` (min 2자) | `{ users: [{ id, nickname, profileImageUrl, relation, pendingRequestId? }] }` |
| `POST` | `/api/v1/friends/requests` | 친구 요청 보내기 | `{ receiverId: Long }` | `{ requestId, status: "PENDING" }` |
| `POST` | `/api/v1/friends/requests/{id}/accept` | 받은 요청 수락 | — | `{ friendshipId, status: "ACCEPTED" }` |
| `POST` | `/api/v1/friends/requests/{id}/reject` | 받은 요청 거절 | — | `{ requestId, status: "REJECTED" }` |
| `DELETE` | `/api/v1/friends/requests/{id}` | 내가 보낸 요청 취소 (PENDING 물리 삭제) | — | `{ requestId }` |
| `GET` | `/api/v1/friends` | 친구 목록 (ACCEPTED) | — | `{ friends: [{ id, nickname, profileImageUrl, since }] }` |
| `GET` | `/api/v1/friends/requests/received` | 받은 요청 목록 (PENDING) | — | `{ requests: [{ id, fromUser: {id, nickname, profileImageUrl}, requestedAt }] }` |

`pendingRequestId` 필드: 검색 결과에서 `REQUEST_RECEIVED` / `REQUEST_SENT` 케이스일 때 PENDING row의 id를 함께 내려줘서 클라이언트가 별도 조회 없이 수락/취소 호출 가능하도록.

### 5.2 검색 쿼리 (단일 LEFT JOIN)

```sql
SELECT
  u.id, u.nickname, u.profile_image_url,
  f.id AS pending_request_id,
  CASE
    WHEN f.status = 'ACCEPTED' THEN 'FRIEND'
    WHEN f.requester_id = :me AND f.status = 'PENDING'  THEN 'REQUEST_SENT'
    WHEN f.receiver_id  = :me AND f.status = 'PENDING'  THEN 'REQUEST_RECEIVED'
    WHEN f.requester_id = :me AND f.status = 'REJECTED' THEN 'REJECTED'
    ELSE 'NONE'
  END AS relation
FROM users u
LEFT JOIN friendships f
  ON ((f.requester_id = :me AND f.receiver_id = u.id)
   OR (f.receiver_id  = :me AND f.requester_id = u.id))
WHERE u.id != :me
  AND u.nickname LIKE :pattern ESCAPE '\'  -- '%' || escapedQuery || '%'
  AND u.status = 'ACTIVE'
ORDER BY u.nickname ASC, u.id ASC
LIMIT 20;
```

**LIKE 와일드카드 escape**: service 계층에서 사용자 입력의 `%`, `_`, `\`를 `\%`, `\_`, `\\`로 치환 후 패턴에 끼움. 와일드카드 인젝션 차단.

**정렬**: 닉네임 사전순 + id tiebreaker. 페이지네이션 없는 단순 LIMIT이라 동명이인 다수 시 결과가 안정적이도록.

### 5.3 친구 요청 service 로직

- **친구 목록 정렬**: `ORDER BY accepted_at DESC` (최근 친구가 된 순)
- **받은 요청 정렬**: `ORDER BY created_at DESC` (가장 최근 요청부터)
- **sendRequest 처리 분기** (기존 row 사전 확인):
  - 없음 → INSERT (status=PENDING)
  - 동일 방향 REJECTED 존재 → 기존 row의 `status='PENDING'`, `accepted_at=null`로 UPDATE (created_at 유지). UNIQUE 제약 호환.
  - 동일 방향 PENDING/ACCEPTED 존재 → `code: 700` ("이미 요청 보냈습니다" / "이미 친구입니다")
  - 반대 방향 PENDING 존재 → `code: 700` ("상대가 이미 친구 요청을 보냈어요. 확인해보세요") + 받은 요청 화면 안내
  - 반대 방향 ACCEPTED 존재 → `code: 700` ("이미 친구입니다")
- 양방향 동시 요청 (A→B 동시에 B→A) race 처리: 위 분기 중 "반대 방향 PENDING 존재" 케이스 — service 사전 검사로 차단.
- 수락 시: PENDING row의 `status='ACCEPTED'`, `accepted_at=now()` UPDATE. **양방향 row 추가 생성 X**. 친구 목록 조회는 `WHERE (requester_id = me OR receiver_id = me) AND status = 'ACCEPTED'`.
- 취소(`DELETE`) 시: PENDING row 물리 삭제 (CANCELLED status 없음). 재요청 가능.

### 5.4 Service 인터페이스

```
FriendService
 ├ searchUsersByNickname(me: Long, q: String): List<UserSearchResult>
 ├ sendRequest(me: Long, receiverId: Long): Friendship
 ├ acceptRequest(me: Long, requestId: Long): Friendship
 ├ rejectRequest(me: Long, requestId: Long): Friendship
 ├ cancelRequest(me: Long, requestId: Long): Unit
 ├ listFriends(me: Long): List<Friend>
 └ listReceivedRequests(me: Long): List<FriendRequest>
```

### 5.5 모듈 배치

- `:controller/friend/FriendController.kt` + dto 패키지
- `:service/friend/FriendService.kt`
- `:domain/model` — `Friendship`, `FriendRequest`, `Friend`, `UserSearchResult`, `Relation` enum
- `:infra/entity/friend/FriendshipEntity.kt` (V1 매핑)
- `:infra/repositoryimpl/friend/FriendshipRepositoryImpl.kt`

### 5.6 통합 테스트 (Testcontainers)

`AuthKakaoIntegrationTest` 패턴 따라 `FriendIntegrationTest` 작성:
- 검색 시나리오: 본인 제외, BLOCKED 제외(현재 없음), 동명이인 다수 매칭, relation 모든 케이스 (NONE/SENT/RECEIVED/FRIEND/REJECTED)
- 요청 → 수락 → 친구 목록 갱신
- 요청 → 거절 → 다시 요청 가능
- 요청 취소 → 재요청 가능
- 동시 요청 race (사전 검사 동작 확인)
- 미인증 (401)

## 6. 모바일 — KMP / Compose Multiplatform

### 6.1 모듈

| 모듈 | 신규 / 확장 | 내용 |
|---|---|---|
| `:remote:model` | 확장 | `UserSearchDto`, `FriendRequestDto`, `FriendDto`, `RelationDto` |
| `:remote:api` | 확장 | `FriendsApi` (Ktorfit interface) — 7개 메서드 |
| `:remote:mapper` | 확장 | DTO ↔ Domain mapper |
| `:domain:model` | 확장 | `UserSearchResult`, `FriendRequest`, `Friend`, `Relation` enum |
| `:domain:repository` | 확장 | `FriendsRepository` |
| `:data:repositoryImpl` | 확장 | `FriendsRepositoryImpl` (`@Single`, Koin 등록) |
| `:feature:friends` | 확장 | 검색 화면 추가, 메인 화면에 받은 요청 인라인 섹션 추가 |
| `:core:navigation` | 확장 | `Route.FriendsRoute.Search` |
| `:core:invite` | **신규** | KakaoInviter expect/actual |

UseCase 만들지 않음 — 단순 흐름은 Repository → ViewModel 직접 호출.

### 6.2 Repository 패턴 (메모리 규칙: Flow + onError + AuthEventBus)

```kotlin
interface FriendsRepository {
    fun searchUsers(nickname: String, onError: (Throwable) -> Unit): Flow<List<UserSearchResult>>
    fun listFriends(onError: (Throwable) -> Unit): Flow<List<Friend>>
    fun listReceivedRequests(onError: (Throwable) -> Unit): Flow<List<FriendRequest>>

    suspend fun sendRequest(receiverId: Long): Result<Unit>
    suspend fun acceptRequest(requestId: Long): Result<Unit>
    suspend fun rejectRequest(requestId: Long): Result<Unit>
    suspend fun cancelRequest(requestId: Long): Result<Unit>
}
```

규칙:
- **검색/목록 = `Flow<T>` + `onError` 콜백**
- **mutation = `suspend` + kotlin stdlib `Result<Unit>`** (sealed Result 금지 규칙은 도메인 sealed Result 만들지 말라는 것 — stdlib Result는 사용 가능)
- **401 처리는 repository 내부**에서 `AuthEventBus.emit(Unauthorized)` (홈 화면 패턴과 동일)

### 6.3 Route 구조

```
Route.FriendsRoute
  ├ Main           — 친구 화면 (목록 + 받은 요청 인라인)
  └ Search         — 검색 화면
```

### 6.4 UI 흐름

```
BottomNav: 친구 → FriendsMainScreen
  ├ [받은 요청 N건] 인라인 섹션 (PENDING, [수락] [거절])
  ├ [친구 목록] 섹션 (ACCEPTED)
  ├ 빈 상태 (친구 0건 + 받은 요청 0건) → 1차 1단계 FriendsEmptyState 재사용
  ├ 상단/FAB 액션 2개:
  │   ├ [친구 추가] → FriendsSearchScreen
  │   └ [친구 초대] → KakaoLink 공유 시트
  └ pull-to-refresh로 friends + receivedRequests 새로고침

FriendsSearchScreen
  ├ 검색 입력 (debounce 300ms, min 2자)
  ├ 결과 리스트 (LIMIT 20)
  ├ 각 아이템: relation별 액션 버튼 (5종)
  ├ 클릭 시 낙관적 갱신 (UI 즉시 → 실패 시 롤백 + 스낵바)
  └ 뒤로 가기 → Main 진입 시 자동 refresh
```

### 6.5 ViewModel 상태

```kotlin
@Stable
sealed interface FriendsUiState {
    @Immutable data object Loading : FriendsUiState
    @Immutable data class Data(
        val receivedRequests: List<FriendRequestItemState>,
        val friends: List<FriendItemState>,
    ) : FriendsUiState
}

@Stable
sealed interface FriendsSearchUiState {
    @Immutable data object Idle : FriendsSearchUiState         // 입력 < 2자
    @Immutable data object Searching : FriendsSearchUiState
    @Immutable data class Result(val items: List<FriendSearchItemState>) : FriendsSearchUiState
    @Immutable data object Empty : FriendsSearchUiState        // 입력 ≥ 2자, 결과 0건
}
```

### 6.6 Compose 컴포넌트

| 컴포넌트 | 위치 | 역할 |
|---|---|---|
| `FriendsEmptyState` | `:core:designsystem` | 1차 1단계 자산 재사용 |
| `FriendListItem` | `:core:designsystem/components/friend` | 친구 목록 1행 |
| `FriendRequestCard` | `:core:designsystem/components/friend` | 받은 요청 카드 (수락/거절) |
| `FriendSearchItem` | `:feature:friends/component` | 검색 결과 1행 (relation 분기) |
| `FriendsTopBar` | `:feature:friends/component` | 1차 1단계 자산 유지 |
| `FriendsSearchTopBar` | `:feature:friends/component` | 검색 화면 전용 |

신규 Composable 모두 **`@Preview` 동봉** (`challenge-app/CLAUDE.md` 119–123, design-system skill의 "Preview 필수 규칙").
- 상태 분기별 Preview: relation 5종 / 빈 상태 / 검색 중 / 결과 있음 / 결과 0건
- `org.jetbrains.compose.ui.tooling.preview.Preview` 임포트 (KMP)
- `ChallengeTheme { }` 래핑 + `ChallengeTheme.colorScheme.background`

### 6.7 ViewModel 테스트 (`/test-viewmodel` skill)

- `FriendsViewModel` — Loading → Data, 받은 요청 수락/거절 시 목록 갱신
- `FriendsSearchViewModel` — debounce 동작, 최소 2자 가드, relation별 액션 → 낙관적 갱신 / 실패 롤백
- Turbine으로 StateFlow 변화 검증

## 7. 카카오톡 초대 (KakaoLink)

### 7.1 진입점 분리

- **친구 추가** — challenge 앱 사용자 대상 (검색 화면)
- **친구 초대** — challenge 앱 미사용자 대상 (KakaoLink)

### 7.2 KMP expect/actual

```kotlin
// :core:invite/commonMain
interface KakaoInviter {
    suspend fun sendInvite(templateArgs: Map<String, String>): Result<Unit>
}

// :core:invite/androidMain — kakao-sdk-share
@Single
class AndroidKakaoInviter(
    private val activityProvider: ActivityProvider,
) : KakaoInviter { /* ShareClient.instance.shareCustom(...) */ }

// :core:invite/iosMain — KakaoSDKShare
@Single
class IosKakaoInviter : KakaoInviter { /* ShareApi.shared.shareCustom(...) */ }
```

기존 카카오 로그인 패턴(`ActivityProvider` 등) 재사용.

### 7.3 카카오 디벨로퍼스 콘솔 작업 (사용자 직접 — 가이드 제공)

콘솔에서 **커스텀 템플릿 1건** 등록:
- 제목: `${inviterNickname}님이 challenge에 초대했어요`
- 본문: `맹세하고 도전하고 같이 성장해요`
- 버튼 1개: "challenge 앱 받기" → Play Store / App Store URL
- 템플릿 변수: `inviterNickname` 1개

장점: 메시지 디자인/문구 변경 시 콘솔만 수정, 앱 배포 불필요.

### 7.4 1차 단순화 — inviter 자동 연결 X

받는 쪽 앱 진입 시 inviter 자동 검색/요청은 후속.
- 1차: 메시지 버튼 → 마켓 URL만. 받는 쪽이 정상 가입 후 메인 진입. inviter 닉네임은 수동 검색.
- 후속: deep link(`challenge://invite/{inviterId}`) + iOS Universal Link + cold-start 데이터 보존 → 받는 쪽 가입 후 검색 결과 prefill.

### 7.5 iOS 작업 확인

- `Info.plist`의 `LSApplicationQueriesSchemes`에 `kakaolink` 추가 필요 (카카오 로그인 시 이미 추가됐을 가능성 — 확인 단계 plan에 포함)

### 7.6 에러 처리

| 케이스 | 처리 |
|---|---|
| 카톡 미설치 | KakaoSDK 자동 — 카톡 설치 페이지 분기 / 웹 공유 fallback |
| 사용자 공유 취소 | 정상 종료, 스낵바 없음 |
| SDK 호출 실패 | 스낵바 "친구 초대를 보낼 수 없어요. 잠시 후 다시 시도해주세요" |
| 템플릿 ID 미등록 / 잘못된 ID | 개발자 오류 — 배포 전 검증 단계 |

## 8. 디자인 (Lovable / design-bridge 작업)

작업 대상 repo: `challenge-design/oathbound-challenges`

1. **친구 목록 메인 화면 수정**
   - 받은 요청 인라인 섹션 추가 (상단 또는 친구 목록 위)
   - `[친구 추가]` / `[친구 초대]` 액션 버튼 위치 결정
2. **친구 검색 화면 신규**
   - 검색 입력 + 결과 리스트
   - relation별 액션 버튼 5종 (NONE/SENT/RECEIVED/FRIEND/REJECTED)
3. **상태 분기 스크린**
   - 검색 빈 상태 (입력 < 2자)
   - 검색 결과 0건
   - 받은 요청 0건 + 친구 0건 (1차 1단계 빈 상태 재사용)

메모리 규칙: design-bridge dispatch prompt에 다음 명시:
- `challenge-design/oathbound-challenges/CLAUDE.md` + 매칭 skill 먼저 읽기 (Tailwind v4 토큰, shadcn 패턴)
- Lovable 작업 후 모바일 `design.md` 매핑 자동 작성 (단일 source of truth)

## 9. 트레이드오프 / 위험

| # | 위험 | 영향 | 1차 대응 | 후속 재검토 조건 |
|---|---|---|---|---|
| 1 | `LIKE '%X%'` 인덱스 무효 → 전체 스캔 | DB 부하 ↑ (사용자 수에 선형) | 친구 4명 규모 가정 / `LIMIT 20` / 최소 2자 가드 | 가입 유저 1만 명 또는 검색 응답시간 200ms 초과 시. 옵션: `pg_trgm` GIN 인덱스 → trigram / Elasticsearch / prefix 매칭 강등 |
| 2 | 닉네임 contains 검색으로 모르는 사람도 발견됨 | 프라이버시 노출 | 수락 단계가 1차 방어선 / 받는 쪽이 요청 거절 가능 / 차단은 후속 | 사용자 피드백에서 스토킹/스팸 신고 발생 시 차단 기능 우선순위 상향 |
| 3 | 동명이인 다수 노출 | 잘못된 사람에게 요청 보낼 위험 | 프로필 사진 + 닉네임으로 시각 식별 / 잘못 보내도 받는 쪽이 거절 가능 | — |
| 4 | A→B와 B→A 동시 요청 race | 양쪽 PENDING row 2개 생성 (UNIQUE 단방향이므로) | service에서 사전 검사. 한쪽 PENDING이면 두 번째 요청 시 스낵바 "상대가 이미 요청을 보냈어요" + 받은 요청 화면 이동 안내 | — |
| 5 | FCM 없음 → 받는 쪽이 친구 화면 진입해야 요청 인지 | 즉시성 떨어짐 | 친구 화면 진입 시 받은 요청 인라인 노출 + 상단 배지 | FCM 통합 별도 spec/plan으로 분리 |
| 6 | KakaoLink 초대에 inviterId 미포함 | 받는 쪽이 가입 후 inviter 수동 검색 필요 | 1차에서는 단순 마켓 URL만 | 가입 전환율 데이터 보고 deep link + inviterId 자동 연결 별도 spec |
| 7 | 차단(BLOCKED) 미구현 | 스토커/스팸 대응 불가 | 1차에서 차단 안 만듦 (V1 BLOCKED status 비활성) | 사용자 신고 발생 시 별도 spec |
| 8 | 낙관적 갱신 실패 → UI 롤백 | 사용자 혼란 가능 | 스낵바로 실패 사유 표시, 자동 refresh | — |
| 9 | 카카오 콘솔 템플릿 ID 환경별 분리 안 함 | 개발/운영 메시지 디자인 동일 강제 | 1차에선 단일 템플릿 | 운영 분리 필요해지면 환경 변수로 templateId 주입 |
| 10 | REJECTED row UPDATE 재요청 시 `created_at`이 첫 요청 시각으로 남음 | 재요청 시점/거절 횟수 audit trail 손실 | 영향 적음 — 1차 분석 불필요 (소규모 사용자, 단순 UX 우선) | 사용자 행동/스토킹 분석 요구 시 별도 audit 테이블 (`friendship_events`) 검토 |

## 10. 1차 범위 / 후속 분리

### 1차 범위 (본 spec)
- 닉네임 검색 (contains, LIMIT 20, min 2자)
- 친구 요청 / 수락 / 거절 / 취소
- 친구 목록 / 받은 요청 목록 (in-app)
- KakaoLink 초대 (커스텀 템플릿, inviter 자동 연결 없음)
- 1차 1단계 spec drift 정정 노트 (1차 1단계 summary.md에 한 줄 추가)

### 후속 작업 (별도 spec/plan)
- 차단 (BLOCKED) 기능
- FCM 푸시 알림 (친구 요청 / 챌린지 응원 등 한꺼번에 통합)
- KakaoLink inviter 자동 연결 (deep link + Universal Link + cold-start)
- 친구 삭제 (현재 ACCEPTED row를 다시 어떻게 할지 정의 안 됨)
- 검색 성능 개선 (trigram 인덱스 / Elasticsearch)

## 11. dispatch / 메모리 규칙 (subagent 위임 시 prompt 필수 포함)

| 규칙 | 적용 |
|---|---|
| 모바일 dispatch git 금지 | mobile-dev에 위임 시 브랜치/커밋/푸시/PR 금지. 코드 변경만 working tree에 두고 보고. |
| Repository 표준 패턴 | Flow<T> + onError 콜백 + AuthEventBus. sealed Result 금지(stdlib Result는 OK). 401은 repository 내부에서 처리. |
| Lovable ↔ 모바일 동시 반영 | 디자인 결정은 양쪽에 동시. 모바일 일정 밀려도 Lovable은 즉시 갱신. |
| repo CLAUDE.md + skill 먼저 읽기 | dispatch prompt에 `{repo}/CLAUDE.md` + 매칭 skill 명시. plan.md만 따르면 Preview / DI / skill 매핑 규칙 무시됨. |

## 12. 검증 / Definition of Done

### 백엔드
- `FriendIntegrationTest` Testcontainers green
- 7개 endpoint 모두 컨트롤러 슬라이스 테스트 + 통합 테스트
- relation 5종 모두 검증 케이스 포함

### 모바일
- 신규 Composable 모두 `@Preview` 동봉 (상태 분기별)
- `FriendsViewModel`, `FriendsSearchViewModel` Turbine 테스트 green
- Android `:composeApp:compileDebugKotlinAndroid` 빌드 통과
- iOS 빌드 확인 (xcodebuild compile)

### 디자인
- Lovable에 친구 목록 수정 + 검색 화면 신규 + 상태 분기 3종 반영
- `design.md` 매핑 갱신 (1차 1단계 design.md에 본 작업 섹션 추가)

### PM hub
- 본 spec.md commit
- 1차 1단계 summary.md에 본 spec 참조 한 줄 추가 commit
- (구현 완료 후) summary.md 신규 또는 1차 1단계 summary.md 갱신
