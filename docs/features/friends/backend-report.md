# Backend Report — friends (친구 추가 — 2차)

작성: backend-dev — 2026-06-25
선행 입력: [spec-friend-add.md](./spec-friend-add.md), [api-contract-friend-add.md](./api-contract-friend-add.md) (status: confirmed), [plan-friend-add.md](./plan-friend-add.md) (Task 3)

## 구현 요약

challenge-server (Spring Boot 멀티모듈 + 헥사고날 + DIP) 위에 친구 시스템 7개 endpoint 를 TDD 로 구현. **V1 friendships 스키마 그대로 활용 — DB 마이그레이션 0건**.

- 도메인: `Friendship` / `FriendRequest` / `Friend` / `UserSearchResult` / `Relation` enum + `FriendshipStatus` enum
- 영속: `FriendshipEntity` (V1 매핑) + `FriendshipJpaRepository` (native query: 검색 / 친구 목록 / 받은 요청) + `FriendshipRepositoryImpl`
- 비즈니스: `FriendService` 7개 메서드 — spec §5.3 분기 5종 모두 명시적으로 분리
- HTTP: `FriendController` + 5개 응답 DTO 파일
- 테스트: 슬라이스 15건 + 통합 9건 (Testcontainers)

## 엔드포인트

| Method | Path | 인증 | 매핑 클래스 (file:line) |
|--------|------|------|------|
| GET    | `/api/v1/users/search` | Bearer | `controller/.../friend/FriendController.kt:66 → FriendService.kt:39 searchUsersByNickname` |
| POST   | `/api/v1/friends/requests` | Bearer | `controller/.../friend/FriendController.kt:82 → FriendService.kt:56 sendRequest` |
| POST   | `/api/v1/friends/requests/{id}/accept` | Bearer | `controller/.../friend/FriendController.kt:101 → FriendService.kt:126 acceptRequest` |
| POST   | `/api/v1/friends/requests/{id}/reject` | Bearer | `controller/.../friend/FriendController.kt:120 → FriendService.kt:149 rejectRequest` |
| DELETE | `/api/v1/friends/requests/{id}` | Bearer | `controller/.../friend/FriendController.kt:139 → FriendService.kt:172 cancelRequest` |
| GET    | `/api/v1/friends` | Bearer | `controller/.../friend/FriendController.kt:155 → FriendService.kt:189 listFriends` |
| GET    | `/api/v1/friends/requests/received` | Bearer | `controller/.../friend/FriendController.kt:169 → FriendService.kt:193 listReceivedRequests` |

모든 응답은 ADR-0002 BaseResponse 패턴 — HTTP 200 + body code. 비즈니스 에러는 `SnackbarException(code=700)`, 인증 만료는 `UnauthorizedException(code=401)`. 본 feature 는 code 701 (다이얼로그) 미사용.

## 변경된 모듈 & 파일 (절대 경로)

### 신규 (production)

| 모듈 | 파일 |
|---|---|
| `:domain:model` | `/Users/hwamulman/woogunProject/challenge/challenge-server/domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/Relation.kt` |
| `:domain:model` | `/Users/hwamulman/woogunProject/challenge/challenge-server/domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/Friendship.kt` |
| `:domain:model` | `/Users/hwamulman/woogunProject/challenge/challenge-server/domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/Friend.kt` |
| `:domain:model` | `/Users/hwamulman/woogunProject/challenge/challenge-server/domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/FriendRequest.kt` |
| `:domain:model` | `/Users/hwamulman/woogunProject/challenge/challenge-server/domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/UserSearchResult.kt` |
| `:domain:repository` | `/Users/hwamulman/woogunProject/challenge/challenge-server/domain/repository/src/main/kotlin/com/lwg/challenge/domain/friend/FriendshipRepository.kt` |
| `:infra:entity` | `/Users/hwamulman/woogunProject/challenge/challenge-server/infra/entity/src/main/kotlin/com/lwg/challenge/infra/entity/friend/FriendshipEntity.kt` |
| `:infra:jpa` | `/Users/hwamulman/woogunProject/challenge/challenge-server/infra/jpa/src/main/kotlin/com/lwg/challenge/infra/jpa/friend/FriendshipJpaRepository.kt` |
| `:infra:repositoryimpl` | `/Users/hwamulman/woogunProject/challenge/challenge-server/infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/friend/FriendshipRepositoryImpl.kt` |
| `:service` | `/Users/hwamulman/woogunProject/challenge/challenge-server/service/src/main/kotlin/com/lwg/challenge/service/friend/FriendService.kt` |
| `:controller` | `/Users/hwamulman/woogunProject/challenge/challenge-server/controller/src/main/kotlin/com/lwg/challenge/controller/friend/FriendController.kt` |
| `:controller` | `/Users/hwamulman/woogunProject/challenge/challenge-server/controller/src/main/kotlin/com/lwg/challenge/controller/friend/dto/UserSearchResponse.kt` |
| `:controller` | `/Users/hwamulman/woogunProject/challenge/challenge-server/controller/src/main/kotlin/com/lwg/challenge/controller/friend/dto/SendFriendRequestBody.kt` |
| `:controller` | `/Users/hwamulman/woogunProject/challenge/challenge-server/controller/src/main/kotlin/com/lwg/challenge/controller/friend/dto/FriendRequestResponses.kt` |
| `:controller` | `/Users/hwamulman/woogunProject/challenge/challenge-server/controller/src/main/kotlin/com/lwg/challenge/controller/friend/dto/FriendListResponse.kt` |

### 신규 (test)

| 위치 | 파일 |
|---|---|
| 컨트롤러 슬라이스 | `/Users/hwamulman/woogunProject/challenge/challenge-server/app/src/test/kotlin/com/lwg/challenge/controller/friend/FriendControllerTest.kt` |
| 통합 (Testcontainers) | `/Users/hwamulman/woogunProject/challenge/challenge-server/app/src/test/kotlin/com/lwg/challenge/integration/FriendIntegrationTest.kt` |
| 서비스 단위 (escapeForLike) | `/Users/hwamulman/woogunProject/challenge/challenge-server/service/src/test/kotlin/com/lwg/challenge/service/friend/FriendServiceEscapeForLikeTest.kt` (T3 code quality fix, commit `1d9d88d`) |

### 수정

| 파일 | 변경 |
|---|---|
| `/Users/hwamulman/woogunProject/challenge/challenge-server/app/src/test/kotlin/com/lwg/challenge/ChallengeServerApplicationTests.kt` | `FriendshipJpaRepository` `@MockitoBean` 추가 (smoke test가 JPA auto-config 제외 환경에서 컨텍스트 로딩 성공하도록 — 기존 패턴과 동일) |

## DB 마이그레이션

**0건.** V1__init.sql 의 `friendships` 테이블 그대로 사용. 컬럼: `id`, `requester_id`, `receiver_id`, `status` VARCHAR(20), `created_at`, `accepted_at`. UNIQUE(requester_id, receiver_id) + (receiver_id,status) / (requester_id,status) 인덱스.

검색 LIKE 와일드카드 가속 인덱스(pg_trgm 등)는 1차 범위에서 미적용 — spec §9 #1 참조 (사용자 규모 증가 시 재검토).

## 핵심 구현 결정 / 주요 분기

### 검색 쿼리 (`FriendshipJpaRepository.searchByNickname`)

- 단일 `LEFT JOIN` + `CASE` 식으로 `relation` derived (spec §5.2 SQL 그대로 native query).
- `pendingRequestId` 는 service/repositoryImpl 매핑 단계에서 `REQUEST_SENT` / `REQUEST_RECEIVED` 일 때만 non-null 강제 (api-contract §1 표).
- LIKE 와일드카드 escape: `FriendService.escapeForLike` — `\` → `%` → `_` 순서. `ESCAPE '\'` 절과 짝.
- 정렬: `ORDER BY u.nickname ASC, u.id ASC LIMIT 20`. 동명이인 안정 정렬.
- `u.status = 'ACTIVE'` 필터 — SUSPENDED/DELETED 사용자 노출 차단.
- 본인 제외: `u.id <> :me`.

### sendRequest 5종 분기 (`FriendService.sendRequest`)

| # | 조건 | 처리 |
|---|---|---|
| 1 | row 없음 | INSERT (status=PENDING) |
| 2 | 동일 방향(me→target) PENDING | `SnackbarException("이미 요청 보냈습니다")` |
| 3 | 동일 방향(me→target) ACCEPTED | `SnackbarException("이미 친구입니다")` |
| 4 | 동일 방향(me→target) REJECTED | 기존 row UPDATE — `status=PENDING`, `acceptedAt=null`. **created_at 보존** (Entity `updatable=false` 로 강제) — `requestId` 는 기존 id 재사용. |
| 5 | 반대 방향(target→me) PENDING | `SnackbarException("상대가 이미 친구 요청을 보냈어요. 확인해보세요")` |
| 6 | 반대 방향(target→me) ACCEPTED | `SnackbarException("이미 친구입니다")` |
| 7 | 반대 방향(target→me) REJECTED | 사전 검사 통과 → INSERT 신규 row (내가 보내는 별도 시도). |
| 8 | `me == receiverId` | `SnackbarException("자기 자신에게는 요청할 수 없어요")` |
| 9 | receiver 미존재 / INACTIVE | `SnackbarException("사용자를 찾을 수 없어요")` |

추가 안전망: 사전 검사 통과 후 동시 INSERT race 시 `UNIQUE(requester_id, receiver_id)` 위반을 `DataIntegrityViolationException` 으로 catch → `SnackbarException("이미 요청 보냈습니다")` 변환. **신규 INSERT 분기는 `saveAndFlush` 사용** — `save` 만 호출하면 flush 가 트랜잭션 commit 시점으로 미뤄져 catch 블록 밖에서 예외가 터지므로 의도한 700 대신 500 으로 노출되는 dead code 가 된다 (T3 code quality fix, commit `1d9d88d`).

### accept / reject / cancel 권한

- `accept`: `receiver_id = me` && `status = PENDING`. status 갱신 + `accepted_at = now()`.
- `reject`: `receiver_id = me` && `status = PENDING`. row 보존 — REJECTED 로 UPDATE. 재요청은 위 분기 #4 처리.
- `cancel`: `requester_id = me` && `status = PENDING`. **물리 삭제**. CANCELLED status 추가하지 않음 — 재요청 가능성 단순화 (spec §5.3 마지막 줄).

위 권한/상태 검증 위반은 전부 `SnackbarException` (code 700) — 본 feature 는 code 701 미사용.

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui.html
- 반영된 경로: `/api/v1/users/search`, `/api/v1/friends/**`
- `@Tag(name="Friend")` 그룹. 모든 endpoint `@SecurityRequirement(name="bearerAuth")`.
- DTO 에 `@Schema(description, example)` 부착 → 모바일 측 ApiResultCall 매핑 참조 가능.

## 테스트 결과

### 컨트롤러 슬라이스 (FriendControllerTest)

`./gradlew :app:test --tests "com.lwg.challenge.controller.friend.*"` → **15/15 passed** (0 skipped, 0 failures).

| # | 시나리오 |
|---|---|
| 1 | searchUsers — relation 5종 직렬화 (UPPER_SNAKE_CASE) + pendingRequestId nullable |
| 2 | searchUsers — 검색어 2자 미만 → code 700 |
| 3 | searchUsers — 결과 0건 빈 배열 |
| 4 | sendRequest — 정상 PENDING |
| 5 | sendRequest — 동일 방향 PENDING → code 700 |
| 6 | sendRequest — `receiverId <= 0` validation 실패 → code 700 |
| 7 | acceptRequest — 정상 ACCEPTED |
| 8 | acceptRequest — 권한 없음 → code 700 |
| 9 | rejectRequest — 정상 REJECTED |
| 10 | cancelRequest — 정상 (`requestId` 반환) |
| 11 | cancelRequest — 권한 없음 → code 700 |
| 12 | listFriends — 친구 목록 + `since` ISO-8601 UTC 직렬화 |
| 13 | listFriends — 0건 빈 배열 |
| 14 | listReceivedRequests — 받은 요청 목록 + `requestedAt` ISO-8601 UTC |
| 15 | listReceivedRequests — 0건 빈 배열 |

### 통합 (FriendIntegrationTest, Testcontainers)

`./gradlew :app:test --tests "com.lwg.challenge.integration.FriendIntegrationTest"` → **9 tests, 9 skipped** (현재 환경 Docker 미가용. 코드 컴파일 / 클래스 로드 / `@EnabledIf` 검증 모두 통과 — 기존 `AuthKakaoIntegrationTest`, `RecordApiIntegrationTest`, `ActiveChallengeApiIntegrationTest` 와 동일 패턴: Docker 미가용 시 전체 skip, Docker 가용 시 자동 실행). 빌드 자체는 SUCCESSFUL.

| # | 시나리오 |
|---|---|
| 1 | 검색 — 본인 제외 / 닉네임 contains / LIMIT 20 / ACTIVE 만 (SUSPENDED/DELETED 노출 X) |
| 2 | 검색 — relation 5종(NONE/REQUEST_SENT/REQUEST_RECEIVED/FRIEND/REJECTED) 한 시나리오에 모두 등장 + pendingRequestId nullable 검증 |
| 3 | 요청 → 수락 → 양쪽 친구 목록에 상대 매핑 (row 1건, status=ACCEPTED, accepted_at non-null) |
| 4 | 요청 → 거절 → status REJECTED, accepted_at null, 검색에서 REJECTED relation |
| 5 | 요청 → 거절 → 재요청 시 동일 row UPDATE — 행 수 불변(1), id 재사용, `created_at` 보존, status=PENDING |
| 6 | 요청 → 취소 → 물리 삭제 (count=0), 재요청 시 신규 row INSERT 가능 |
| 7 | A→B 후 B→A 시 사전 검사 차단 + "상대가 이미 친구 요청을 보냈어요. 확인해보세요" 메시지 |
| 8 | 미인증 (토큰 없음) → HTTP 401 + code 401 (검색 / 친구 목록 / 받은 요청 모두) |
| 9 | 권한 외 accept/reject/cancel → code 700 ("권한이 없어요" 3종 + receiver 가 cancel 시도 분기) |

### 전체 빌드

`./gradlew build` → **BUILD SUCCESSFUL**. 모든 모듈 컴파일 + smoke test (ChallengeServerApplicationTests) pass.

기타 모듈 / 기존 테스트 영향 없음:
- `core` PhoneHasherTest: 3/3 passed
- `AuthControllerTest`: 5/5 passed
- `GlobalExceptionHandlerTest`: 5/5 passed
- 기존 Testcontainers 테스트(Auth/Record/ActiveChallenge): 모두 동일 환경 사유로 skip 처리, 변경된 동작 없음

## 미해결 이슈 / 알려진 한계

### 1차 범위 외(spec §10 후속 분리)

| # | 항목 | 후속 액션 |
|---|---|---|
| 1 | 차단(BLOCKED) 미구현 | V1 스키마의 BLOCKED status 비활성. 사용자 신고 / 스토킹 발생 시 별도 spec/plan. |
| 2 | FCM 푸시 알림 없음 | 받는 쪽이 친구 화면 진입해야 요청 인지 (in-app only). 챌린지 응원/평가 통합 spec 으로 같이 도입. |
| 3 | 친구 삭제(unfriend) 없음 | ACCEPTED row 를 어떻게 처리할지 미정 (REJECTED 로 되돌릴지 / DELETE 할지) — 후속 spec. |
| 4 | REJECTED → PENDING UPDATE 시 `created_at` 첫 요청 시각으로 잔존 | spec §9 #10 — 소규모 사용자 가정에서 audit trail 손실은 영향 적음. 행동 분석 요구 시 `friendship_events` 별도 테이블 검토. |
| 5 | LIKE `'%X%'` 인덱스 무효 — 전체 스캔 | spec §9 #1 — 친구 4명 규모 가정 + LIMIT 20 + 최소 2자 가드. 가입 유저 1만 명 또는 200ms 초과 시 pg_trgm GIN / Elasticsearch / prefix 매칭 강등 검토. |

### 환경 제약 (Docker)

현재 작업 환경에 Docker 미설치 → `FriendIntegrationTest` 의 실제 Testcontainers 실행 불가. 코드 컴파일 / 클래스 로드 검증은 통과, 9 시나리오 모두 `@EnabledIf` 가드로 자동 skip. CI 또는 Docker Desktop / OrbStack / Colima 활성 환경에서는 자동 실행. (`AuthKakaoIntegrationTest` / `RecordApiIntegrationTest` / `ActiveChallengeApiIntegrationTest` 도 동일 패턴 — 본 PR 신규 도입 사항 아님.)

### 추후 모니터링 권장

- `sendRequest` 의 race 백업 `DataIntegrityViolationException` catch 빈도 (로그 레벨 INFO+ 잡기)
- 검색 응답 시간 P95 (현재 단일 LEFT JOIN + LIKE — 사용자 증가 시 우선 모니터링 대상)

## 변경 이력 — Code Quality Fix (2026-06-25, commit `1d9d88d`)

T3 초기 구현 (`bae8ab6`) 의 code quality review 에서 정확성 영향이 있는 Important 2건 식별 → 즉시 fix.

### 1. `sendRequest` INSERT 분기 — `save` → `saveAndFlush`

- **증상**: `jpa.save()` 는 `EntityManager.persist()` 만 호출하고 flush 는 트랜잭션 commit 시점으로 미룬다. UNIQUE(requester_id, receiver_id) 위반은 flush 시점에 발생하므로 service 의 `try/catch (DataIntegrityViolationException)` 블록 밖에서 터진다. → race 발생 시 의도한 `SnackbarException("이미 요청 보냈습니다", code=700)` 대신 `handleUncaught` 가 처리하여 HTTP 500 + code 500 으로 노출.
- **수정**: `FriendshipRepository.saveAndFlush(...)` 포트 추가 → `FriendshipRepositoryImpl` 에서 `JpaRepository.saveAndFlush` 위임 → `FriendService.sendRequest` 신규 INSERT 분기에서 호출. 동일 분기의 `try/catch` 가 실제로 동작하도록 보장. 다른 분기(REJECTED → PENDING UPDATE, accept/reject)는 영향 없음.
- **영향 파일**: `domain/repository/.../FriendshipRepository.kt`, `infra/repositoryimpl/.../FriendshipRepositoryImpl.kt`, `service/.../FriendService.kt`.

### 2. `escapeForLike` 단위 테스트 6건 추가

- **증상**: `\` → `%` → `_` replace 순서가 유일한 정확성 가드인데 어디에도 테스트가 없었음. 미래 refactor 가 순서를 바꾸면 silent break — `\` 가 이중 escape 되어 LIKE 패턴이 의미 깨짐 (사용자 입력 `"50%"` 등이 와일드카드로 동작할 수 있음).
- **수정**: `service/src/test/kotlin/com/lwg/challenge/service/friend/FriendServiceEscapeForLikeTest.kt` 신규 (service 모듈 첫 테스트). 6 케이스 — 한글 / 퍼센트 / 언더스코어 / backslash (순서 회귀 방지) / 세 와일드카드 혼합 / 빈 문자열.
- **검증**: `./gradlew :service:test` → 6/6 passed.

### 회귀 검증

- `./gradlew build` → BUILD SUCCESSFUL.
- `./gradlew :app:test` → 동일 결과 (FriendControllerTest 15/15, GlobalExceptionHandlerTest 5/5, AuthControllerTest 5/5, Smoke 1/1; 통합 테스트 17건은 Docker 미가용으로 동일하게 skip — Auth 5 / Record 3 / ActiveChallenge 3 / FriendIntegrationTest 9).
- 모바일/디자인 영향 없음 (포트 시그니처 호환 추가, 외부 노출 컨트랙트 변경 없음).

## 다음 단계 (Task 4-8)

본 Task 3 산출물 (FriendController / FriendService / 7 endpoint OpenAPI spec) 을 기반으로:
- Task 4: 모바일 `:remote` / `:domain` / `:data` (FriendsApi, FriendsRepository, FriendsRepositoryImpl)
- Task 5: 모바일 ViewModel (FriendsViewModel 확장 + FriendsSearchViewModel 신규) — Turbine 테스트
- Task 6: 모바일 designsystem 컴포넌트 (FriendListItem / FriendRequestCard) + Preview
- Task 7: 모바일 feature UI + Navigation + KakaoLink invite
- Task 8: 통합 검증 + report-and-document
