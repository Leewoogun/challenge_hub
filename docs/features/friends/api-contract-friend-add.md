# API Contract — 친구 추가 (friend-add)

- **feature-id**: friends (후속 — 친구 추가)
- **상태**: confirmed
- **최종 수정**: 2026-06-25 by pm-lead (모바일/백엔드 동시 진입 전제 — spec-friend-add.md §5에서 endpoint 합의)
- **상위 spec**: [spec-friend-add.md](./spec-friend-add.md)

## 엔드포인트 요약

| # | Method | Path | 설명 | 인증 |
|---|--------|------|------|------|
| 1 | GET | `/api/v1/users/search` | 닉네임 contains 검색 (LIMIT 20) | Bearer JWT |
| 2 | POST | `/api/v1/friends/requests` | 친구 요청 보내기 | Bearer JWT |
| 3 | POST | `/api/v1/friends/requests/{id}/accept` | 받은 요청 수락 | Bearer JWT |
| 4 | POST | `/api/v1/friends/requests/{id}/reject` | 받은 요청 거절 | Bearer JWT |
| 5 | DELETE | `/api/v1/friends/requests/{id}` | 내가 보낸 PENDING 요청 취소 (물리 삭제) | Bearer JWT |
| 6 | GET | `/api/v1/friends` | 친구 목록 (ACCEPTED) | Bearer JWT |
| 7 | GET | `/api/v1/friends/requests/received` | 받은 요청 목록 (PENDING) | Bearer JWT |

공통:
- 모든 endpoint `Authorization: Bearer <access-token>` 필수.
- ADR-0002 BaseResponse 패턴 — HTTP 200 + body `code`로 성공/비즈니스 에러 구분.
- ADR-0009 refresh — 일반 API 401은 Ktor Auth 플러그인 자동 갱신 시도, `/auth/refresh` 401은 강제 재로그인.
- 페이지네이션 없음 (소규모 친구 앱 가정, 검색은 LIMIT 20 고정).
- 시간 필드 직렬화: ISO-8601 UTC (`Instant` / `OffsetDateTime` → `2026-06-25T03:14:15Z`).
- ID 타입: 전부 `Long` (BIGSERIAL 기반).

## 공통 enum

### Relation (검색 결과 derived 값)
| 값 | 조건 (friendships row 기준) |
|---|---|
| `NONE` | row 없음 |
| `REQUEST_SENT` | `requester_id = me AND receiver_id = target AND status = 'PENDING'` |
| `REQUEST_RECEIVED` | `requester_id = target AND receiver_id = me AND status = 'PENDING'` |
| `FRIEND` | 어느 방향이든 `status = 'ACCEPTED'` |
| `REJECTED` | `requester_id = me AND receiver_id = target AND status = 'REJECTED'` |

- **직렬화**: 대문자 UPPER_SNAKE_CASE 문자열 (Server enum class `Relation` → Jackson 기본).
- BLOCKED는 1차 미구현 — 검색 결과에 BLOCKED row 자체가 생성될 경로 없음. 응답에 포함되지 않음.

### FriendshipStatus (mutation 응답의 status 필드)
| 값 | 의미 |
|---|---|
| `PENDING` | 친구 요청 보낸 직후 |
| `ACCEPTED` | 수락 완료 — 친구 관계 성립 |
| `REJECTED` | 거절 완료 |

---

## 1. GET `/api/v1/users/search`

### 설명
닉네임 contains 매칭으로 사용자 검색. 본인 제외, ACTIVE 유저만, LIMIT 20.

### 인증
- 방식: `Bearer JWT`

### Path Parameters
없음.

### Query Parameters
| 이름 | 타입 | 필수 | 검증 | 설명 |
|------|------|------|------|------|
| `nickname` | string | ✓ | min 2자 (trim 후) | 검색어. `%`, `_`, `\` 와일드카드는 서버에서 escape. |

### Request Body
없음.

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "users": [
      {
        "id": 42,
        "nickname": "민수",
        "profileImageUrl": "https://cdn.example.com/u/42.jpg",
        "relation": "REQUEST_SENT",
        "pendingRequestId": 901
      },
      {
        "id": 43,
        "nickname": "민수네집",
        "profileImageUrl": null,
        "relation": "NONE",
        "pendingRequestId": null
      }
    ]
  }
}
```

서버 타입:
```kotlin
data class UserSearchResponse(val data: UserSearchData) : BaseResponse()
data class UserSearchData(val users: List<UserSearchItem>)
data class UserSearchItem(
    val id: Long,
    val nickname: String,
    val profileImageUrl: String?,
    val relation: Relation,                 // enum, UPPER_SNAKE_CASE 직렬화
    val pendingRequestId: Long?,            // REQUEST_SENT / REQUEST_RECEIVED일 때만 값
)
enum class Relation { NONE, REQUEST_SENT, REQUEST_RECEIVED, FRIEND, REJECTED }
```

### pendingRequestId nullable 조건
| relation | pendingRequestId |
|---|---|
| `NONE` | null |
| `REQUEST_SENT` | **non-null** — 내가 보낸 PENDING row id (취소 호출에 사용) |
| `REQUEST_RECEIVED` | **non-null** — 상대가 보낸 PENDING row id (수락/거절 호출에 사용) |
| `FRIEND` | null (ACCEPTED row의 id는 별도 필요 시 `/friends` 응답에서) |
| `REJECTED` | null (기존 REJECTED row를 보유하지만 PENDING이 아니므로 null. 재요청 시 §2에서 해당 row를 PENDING으로 UPDATE.) |

### 에러 Response (HTTP 200, body code로 분기)
| code | 상황 | 예시 메시지 | 모바일 처리 |
|------|------|-------------|-------------|
| 700 | 닉네임 2자 미만 / 와일드카드만 입력 등 | "검색어를 2자 이상 입력해주세요" | 스낵바 |
| 401 | 토큰 만료 | "토큰 만료 — Refresh" | Auth 플러그인 자동 갱신 |

### 페이지네이션 / 정렬
- 페이지네이션 없음. 고정 LIMIT 20.
- 정렬: `u.nickname ASC, u.id ASC` (서버 처리).

### 모바일측 주의사항
- debounce 300ms, min 2자 가드 (서버 가드와 이중).
- `pendingRequestId`는 relation이 `REQUEST_SENT` / `REQUEST_RECEIVED`일 때만 사용. 다른 값에서는 무시.
- 결과 20건 도달 시 "더 정확히 입력해주세요" 안내 표시.

### 백엔드측 주의사항
- 단일 `SELECT u.* LEFT JOIN friendships f` 쿼리 (spec §5.2). N+1 없음.
- `LIKE` 와일드카드 escape는 service 계층에서 수행 (`%`→`\%`, `_`→`\_`, `\`→`\\`).
- `u.status = 'ACTIVE'` 조건 필수 — 탈퇴/정지 유저 노출 차단.

---

## 2. POST `/api/v1/friends/requests`

### 설명
다른 사용자에게 친구 요청을 보낸다. 새 friendships row를 `PENDING` 상태로 생성.

### 인증
- 방식: `Bearer JWT`
- 권한: 인증된 사용자가 `requester_id = me`로 생성.

### Path / Query Parameters
없음.

### Request Body (JSON)
```json
{
  "receiverId": 42
}
```

서버 타입:
```kotlin
data class SendFriendRequestBody(val receiverId: Long)
```

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "requestId": 901,
    "status": "PENDING"
  }
}
```

서버 타입:
```kotlin
data class SendFriendRequestResponse(val data: SendFriendRequestData) : BaseResponse()
data class SendFriendRequestData(
    val requestId: Long,                    // friendships.id
    val status: FriendshipStatus,           // 항상 "PENDING"
)
```

### 에러 Response (HTTP 200, body code로 분기)
| code | 상황 | 예시 메시지 | 모바일 처리 |
|------|------|-------------|-------------|
| 700 | 이미 내가 같은 상대에게 요청 보냄 (UNIQUE 위반) | "이미 요청 보냈습니다" | 스낵바 |
| 700 | 상대가 이미 나에게 PENDING 요청 보냄 (역방향 race) | "상대가 이미 친구 요청을 보냈어요. 확인해보세요" | 스낵바 + 받은 요청 화면 안내 |
| 700 | 이미 친구(ACCEPTED) | "이미 친구입니다" | 스낵바 |
| 700 | 본인에게 요청 시도 (`receiverId = me`) | "자기 자신에게는 요청할 수 없어요" | 스낵바 |
| 700 | `receiverId` 존재하지 않음 / INACTIVE | "사용자를 찾을 수 없어요" | 스낵바 |
| 401 | 토큰 만료 | "토큰 만료 — Refresh" | 자동 갱신 |

> 모든 비즈니스 에러를 `code: 700`(스낵바)으로 통일. 모바일은 `message`를 그대로 노출. 동시 race로 양방향 PENDING이 생기지 않도록 service에서 사전 검사 (spec §5.3).

### service 처리 분기 (sendRequest)
기존 row를 사전 조회한 뒤 다음 분기로 처리 (spec §4.3 / §5.3):

| 케이스 | 처리 | 응답 |
|---|---|---|
| 기존 row 없음 | INSERT (status=PENDING) | 성공 `requestId` (신규 row id) |
| 동일 방향 REJECTED row 존재 (`requester=me, receiver=target, status=REJECTED`) | 기존 row UPDATE — `status=PENDING`, `accepted_at=null`. `created_at` 유지. | 성공 `requestId` (기존 row id 재사용) |
| 동일 방향 PENDING row 존재 | 차단 | `code: 700` "이미 요청 보냈습니다" |
| 동일 방향 ACCEPTED row 존재 | 차단 | `code: 700` "이미 친구입니다" |
| 반대 방향 PENDING row 존재 (`requester=target, receiver=me, status=PENDING`) | 차단 (race 안내) | `code: 700` "상대가 이미 친구 요청을 보냈어요. 확인해보세요" |
| 반대 방향 ACCEPTED row 존재 | 차단 | `code: 700` "이미 친구입니다" |
| `receiverId = me` | 차단 | `code: 700` "자기 자신에게는 요청할 수 없어요" |
| `receiverId` 미존재 / INACTIVE | 차단 | `code: 700` "사용자를 찾을 수 없어요" |

응답의 `requestId` 의미: 신규 INSERT는 새 PK, REJECTED UPDATE는 기존 row의 PK 재사용. 모바일은 양쪽 모두 `pendingRequestId`로 동일하게 취급.

### 모바일측 주의사항
- 검색 결과 화면에서 낙관적 갱신 (해당 row의 relation을 `NONE`/`REJECTED` → `REQUEST_SENT`로 즉시 전환, `pendingRequestId`에 응답 값 반영). 실패 시 롤백 + 스낵바.

### 백엔드측 주의사항
- 트랜잭션 1건: 사전 검사(위 분기) → INSERT 또는 UPDATE.
- 영향 테이블: `friendships` (INSERT 1행 또는 UPDATE 1행).
- `UNIQUE(requester_id, receiver_id)` 제약 위반은 catch해서 `code: 700`로 변환 — 단 정상 흐름에서는 사전 검사로 도달하지 않아야 한다 (race 백업).
- REJECTED → PENDING UPDATE 시 `created_at`은 변경하지 않는다 (첫 요청 시각 보존).

---

## 3. POST `/api/v1/friends/requests/{id}/accept`

### 설명
받은 친구 요청을 수락. 해당 PENDING row를 `status='ACCEPTED'`, `accepted_at=now()`로 UPDATE. 양방향 row 추가 생성하지 않음.

### 인증
- 방식: `Bearer JWT`
- 권한: 해당 row의 `receiver_id = me`만 수락 가능.

### Path Parameters
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | Long | ✓ | `friendships.id` (PENDING row) |

### Request Body
없음.

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "friendshipId": 901,
    "status": "ACCEPTED"
  }
}
```

서버 타입:
```kotlin
data class AcceptFriendRequestResponse(val data: AcceptFriendRequestData) : BaseResponse()
data class AcceptFriendRequestData(
    val friendshipId: Long,                 // = path의 id (UPDATE된 row)
    val status: FriendshipStatus,           // 항상 "ACCEPTED"
)
```

### 에러 Response (HTTP 200)
| code | 상황 | 예시 메시지 |
|------|------|-------------|
| 700 | `receiver_id != me` (권한 외) | "이 요청을 수락할 권한이 없어요" |
| 700 | row 상태가 `PENDING`이 아님 (이미 ACCEPTED / REJECTED / 삭제됨) | "이미 처리된 요청입니다" |
| 700 | `id`에 해당하는 row 없음 | "요청을 찾을 수 없어요" |
| 401 | 토큰 만료 | "토큰 만료 — Refresh" |

### 모바일측 주의사항
- 검색 결과 / 받은 요청 화면에서 모두 호출 가능. 호출 후 받은 요청 목록과 친구 목록을 refresh (또는 낙관적 갱신).
- 검색 결과의 `pendingRequestId`(REQUEST_RECEIVED일 때)를 path에 사용.

### 백엔드측 주의사항
- 트랜잭션 1건: 권한/상태 검사 → UPDATE.
- 영향 테이블: `friendships` (UPDATE 1행).
- 양방향 row를 추가로 만들지 않는다. 목록 조회는 `WHERE (requester_id = me OR receiver_id = me) AND status = 'ACCEPTED'`.

---

## 4. POST `/api/v1/friends/requests/{id}/reject`

### 설명
받은 친구 요청을 거절. 해당 PENDING row를 `status='REJECTED'`로 UPDATE. row는 보존.

> REJECTED 후 동일 requester의 재요청은 §2 sendRequest 흐름이 처리한다 — 기존 REJECTED row를 `status=PENDING`으로 UPDATE (`accepted_at=null`, `created_at` 유지). 후속 작업 이관 없음 (spec §4.3 / §5.3).

### 인증
- 방식: `Bearer JWT`
- 권한: 해당 row의 `receiver_id = me`만 거절 가능.

### Path Parameters
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | Long | ✓ | `friendships.id` (PENDING row) |

### Request Body
없음.

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "requestId": 901,
    "status": "REJECTED"
  }
}
```

서버 타입:
```kotlin
data class RejectFriendRequestResponse(val data: RejectFriendRequestData) : BaseResponse()
data class RejectFriendRequestData(
    val requestId: Long,
    val status: FriendshipStatus,           // 항상 "REJECTED"
)
```

### 에러 Response (HTTP 200)
| code | 상황 | 예시 메시지 |
|------|------|-------------|
| 700 | `receiver_id != me` (권한 외) | "이 요청을 거절할 권한이 없어요" |
| 700 | row 상태가 `PENDING`이 아님 | "이미 처리된 요청입니다" |
| 700 | row 없음 | "요청을 찾을 수 없어요" |
| 401 | 토큰 만료 | "토큰 만료 — Refresh" |

### 모바일측 주의사항
- 받은 요청 카드 / 검색 결과 모두에서 호출 가능. 호출 후 받은 요청 목록 refresh.

### 백엔드측 주의사항
- 트랜잭션 1건: 권한/상태 검사 → UPDATE.
- 영향 테이블: `friendships` (UPDATE 1행).

---

## 5. DELETE `/api/v1/friends/requests/{id}`

### 설명
내가 보낸 PENDING 친구 요청을 취소. 해당 row를 **물리 삭제** (CANCELLED status 없음). 삭제 후 동일 상대에게 재요청 가능.

### 인증
- 방식: `Bearer JWT`
- 권한: 해당 row의 `requester_id = me`만 취소 가능.

### Path Parameters
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | Long | ✓ | `friendships.id` (PENDING row) |

### Request Body
없음.

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "requestId": 901
  }
}
```

서버 타입:
```kotlin
data class CancelFriendRequestResponse(val data: CancelFriendRequestData) : BaseResponse()
data class CancelFriendRequestData(
    val requestId: Long,                    // 삭제된 row의 id (참조용)
)
```

### 에러 Response (HTTP 200)
| code | 상황 | 예시 메시지 |
|------|------|-------------|
| 700 | `requester_id != me` (권한 외) | "이 요청을 취소할 권한이 없어요" |
| 700 | row 상태가 `PENDING`이 아님 (이미 수락/거절됨) | "이미 처리된 요청입니다" |
| 700 | row 없음 | "요청을 찾을 수 없어요" |
| 401 | 토큰 만료 | "토큰 만료 — Refresh" |

### 모바일측 주의사항
- 검색 결과의 `REQUEST_SENT` 행에서 호출. 호출 후 해당 row의 relation을 `NONE`으로 낙관적 갱신, `pendingRequestId`를 null로.
- 삭제 후 재요청은 새 POST `/friends/requests` 호출 (relation이 `NONE`이므로 자연스러움).

### 백엔드측 주의사항
- 트랜잭션 1건: 권한/상태 검사 → DELETE.
- 영향 테이블: `friendships` (DELETE 1행, 물리 삭제).
- CANCELLED status를 추가하지 않는 이유: 재요청 가능성을 위해 row를 깔끔히 비우는 편이 단순.

---

## 6. GET `/api/v1/friends`

### 설명
내 친구 목록(`status = 'ACCEPTED'`) 반환. 양방향 어느 쪽이든 ACCEPTED row가 매칭. `accepted_at DESC` 정렬.

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
    "friends": [
      {
        "id": 42,
        "nickname": "민수",
        "profileImageUrl": "https://cdn.example.com/u/42.jpg",
        "since": "2026-06-20T12:34:56Z"
      }
    ]
  }
}
```

빈 상태:
```json
{ "error": false, "code": 200, "message": "", "data": { "friends": [] } }
```

서버 타입:
```kotlin
data class FriendsResponse(val data: FriendsData) : BaseResponse()
data class FriendsData(val friends: List<FriendItem>)
data class FriendItem(
    val id: Long,                           // 친구(상대) user id (= 나 아님)
    val nickname: String,
    val profileImageUrl: String?,
    val since: Instant,                     // friendships.accepted_at, ISO-8601 UTC
)
```

### 에러 Response (HTTP 200)
| code | 상황 | 예시 메시지 |
|------|------|-------------|
| 401 | 토큰 만료 | "토큰 만료 — Refresh" |

### 페이지네이션 / 정렬
- 페이지네이션 없음.
- 정렬: `accepted_at DESC` (최근 친구가 된 순).

### 모바일측 주의사항
- `id`는 상대(나 아닌 사용자)의 user id — 백엔드가 항상 "내가 아닌 쪽"을 매핑.
- `friends`는 빈 배열로 반환 (null 금지). 친구 0건 빈 상태는 모바일에서 길이 0으로 판정.
- 진입 시마다 호출 (디스크 캐시 없음, StateFlow 메모리만).

### 백엔드측 주의사항
- 단일 쿼리: `WHERE (requester_id = :me OR receiver_id = :me) AND status = 'ACCEPTED'` + users JOIN.
- "내가 아닌 쪽"의 user id / nickname / profileImageUrl을 매핑해서 응답.

---

## 7. GET `/api/v1/friends/requests/received`

### 설명
나에게 도착한 친구 요청 중 `status = 'PENDING'`인 목록. `created_at DESC` 정렬.

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
    "requests": [
      {
        "id": 901,
        "fromUser": {
          "id": 42,
          "nickname": "민수",
          "profileImageUrl": "https://cdn.example.com/u/42.jpg"
        },
        "requestedAt": "2026-06-24T18:00:00Z"
      }
    ]
  }
}
```

빈 상태:
```json
{ "error": false, "code": 200, "message": "", "data": { "requests": [] } }
```

서버 타입:
```kotlin
data class ReceivedFriendRequestsResponse(val data: ReceivedFriendRequestsData) : BaseResponse()
data class ReceivedFriendRequestsData(val requests: List<ReceivedFriendRequestItem>)
data class ReceivedFriendRequestItem(
    val id: Long,                           // friendships.id (PENDING)
    val fromUser: FromUser,
    val requestedAt: Instant,               // friendships.created_at, ISO-8601 UTC
)
data class FromUser(
    val id: Long,
    val nickname: String,
    val profileImageUrl: String?,
)
```

### 에러 Response (HTTP 200)
| code | 상황 | 예시 메시지 |
|------|------|-------------|
| 401 | 토큰 만료 | "토큰 만료 — Refresh" |

### 페이지네이션 / 정렬
- 페이지네이션 없음.
- 정렬: `created_at DESC` (가장 최근 요청부터).

### 모바일측 주의사항
- 친구 화면 메인 상단 인라인 섹션 + 배지 표시용. 친구 목록과 병렬 호출.
- 수락/거절 액션은 `id`를 path로 사용.
- `requests`는 빈 배열로 반환 (null 금지).

### 백엔드측 주의사항
- 단일 쿼리: `WHERE receiver_id = :me AND status = 'PENDING'` + users JOIN (requester).
- N+1 없음 — `JOIN users u ON u.id = f.requester_id`.

---

## 공통 에러 코드 정리

| code | 의미 | HTTP | 모바일 처리 |
|------|------|------|-------------|
| 200 | 성공 (`error=false`) | 200 | 정상 처리 |
| 700 | 비즈니스 에러 — 스낵바 (검증 / 권한 외 / 상태 외 / race) | **200** | `message`를 그대로 스낵바 표시 |
| 701 | 비즈니스 에러 — 다이얼로그 | **200** | **본 feature에서는 사용 안 함** |
| 401 | 토큰 만료 | 401 | Ktor Auth 플러그인 자동 갱신, `/auth/refresh` 401 시 강제 재로그인 (ADR-0009) |
| 500 | 인프라 장애 | 500 | 재시도/장애 안내 |

> ADR-0002에 따라 비즈니스 에러는 HTTP 200 + body `code`로 분기. HTTP 4xx는 인프라/인증 경로(401, 5xx)에서만 발생.

---

## 모바일 ↔ 백엔드 공통 합의

- **시간**: 모든 시간 필드는 `Instant` / ISO-8601 UTC (`2026-06-25T03:14:15Z`). KST 변환은 모바일이 표시 단계에서.
- **enum 직렬화**: `Relation`, `FriendshipStatus` 모두 대문자 UPPER_SNAKE_CASE 문자열. 서버 enum class 기반, Jackson 기본 직렬화.
- **빈 배열**: 응답의 `users` / `friends` / `requests` 모두 빈 배열 반환 (null 금지).
- **ID 타입**: 전부 `Long` (BIGSERIAL 기반).
- **nullable**: `profileImageUrl`은 사용자가 미설정 시 null. `pendingRequestId`는 §1 표대로.
- **인증 만료**: 일반 API 401은 모바일 Auth 플러그인이 자동 refresh 시도. Repository는 401 발생 시 `AuthEventBus.emit(Unauthorized)`만 — refresh 실패 시 ADR-0009대로 강제 재로그인.
- **소비자 측 낙관적 갱신**: 검색 결과 / 받은 요청 / 친구 목록 UI에서 mutation은 낙관적으로 즉시 반영, 실패 시 롤백 + 스낵바.

---

## 협의 이력
| 일시 | 작성자 | 변경 |
|------|--------|------|
| 2026-06-25 | pm-lead | 초안 + 확정 (모바일/백엔드 동시 진입 전제 — spec-friend-add.md §5에서 7개 endpoint 이미 합의됨, T1으로 곧장 `confirmed` 진입) |
| 2026-06-25 | pm-lead | REJECTED 재요청 처리 = UPDATE 결정 (옵션 🅰️). spec §4.3 + §5.3 보강. code 701 미사용 명시. (T1 fix after code quality review) |

> 본 contract 확정 이후 변경은 [change-log.md](./change-log.md)와 본 섹션 양쪽에 append. 본 spec(`spec-friend-add.md`)이 친구 시스템 권위(authority) — 1차 1단계 `spec.md` / `plan.md`는 historical artifact.
