# 친구 추가 feature — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** challenge 앱에 친구 검색·요청·수락·목록 기능 + 카카오톡 초대(KakaoLink)를 구현한다. 백엔드 V1 friendships 스키마 그대로 활용, DB 마이그레이션 0건.

**Architecture:** PM hub의 4-agent 흐름 (`pm-lead` / `backend-dev` / `mobile-dev` / `design-bridge`)으로 분담. Phase 0: API 계약 + 디자인 + 카카오 콘솔 선행. Phase 1: backend / mobile / KakaoLink 트랙 병렬. Phase 2: 통합 검증 + 문서화.

**Tech Stack:** Spring Boot multi-module / Kotlin / Testcontainers (백엔드); Kotlin Multiplatform + Compose Multiplatform + Koin + Ktorfit (모바일); KakaoSDK Share (Android + iOS); TanStack Start + React 19 + Tailwind v4 (Lovable 디자인).

---

## 참조 문서

- 입력 spec: [spec-friend-add.md](./spec-friend-add.md) — feature-id `friends` 후속
- 1차 1단계 문서 (historical): [spec.md](./spec.md) / [plan.md](./plan.md) / [design.md](./design.md) / [summary.md](./summary.md)
- PM hub 컨벤션: `challenge_hub/CLAUDE.md`
- 레포 레지스트리: `.claude/config/repos.json`

---

## 메모리 규칙 (모든 subagent dispatch 시 prompt에 반드시 포함)

| 규칙 | 적용 |
|---|---|
| 모바일 dispatch git 금지 | mobile-dev에 위임 시 브랜치/커밋/푸시/PR 금지. 코드 변경만 working tree에 두고 보고. 사용자가 직접 커밋. |
| Repository 표준 패턴 | `Flow<T>` + `onError` 콜백 + `AuthEventBus`. 도메인 sealed Result 만들지 말 것 (kotlin stdlib `Result`는 OK). 401은 repository 내부에서 처리. |
| Lovable ↔ 모바일 동기 | 디자인 결정은 Lovable과 모바일 양쪽 즉시 반영. |
| repo CLAUDE.md + skill 먼저 읽기 | dispatch prompt에 다음 표준 헤더 포함:<br/>`## 시작 전 필수 읽기`<br/>`1. {repo}/CLAUDE.md`<br/>`2. 작업 유형에 매칭되는 .claude/skills/{name}.md`<br/>`3. spec-friend-add.md` |

---

## File Structure

### PM hub (`challenge-pm/challenge_hub`)
- Create: `docs/features/friends/api-contract-friend-add.md` (T1 산출물)
- Modify: `docs/features/friends/design.md` (T2 산출물 — 본 작업 섹션 추가)
- Create: `docs/features/friends/backend-report.md` (T3 산출물)
- Create: `docs/features/friends/mobile-report.md` (T4-T7 산출물 종합)
- Modify: `docs/features/friends/summary.md` (1차 1단계 summary에 정정 노트 + 본 작업 완료 섹션 추가)
- Modify: `docs/features/INDEX.md` (상태 갱신)
- Modify: `docs/backlog.md` (후속 항목 등재: 차단, FCM, inviter 자동 연결, 친구 삭제)

### 백엔드 (`challenge-server`)
- Create: `domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/Friendship.kt`
- Create: `domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/FriendRequest.kt`
- Create: `domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/Friend.kt`
- Create: `domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/UserSearchResult.kt`
- Create: `domain/model/src/main/kotlin/com/lwg/challenge/domain/friend/Relation.kt`
- Create: `domain/repository/src/main/kotlin/com/lwg/challenge/domain/friend/FriendshipRepository.kt`
- Create: `infra/entity/src/main/kotlin/com/lwg/challenge/infra/entity/friend/FriendshipEntity.kt`
- Create: `infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/friend/FriendshipRepositoryImpl.kt`
- Create: `infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/friend/FriendshipJpaRepository.kt`
- Create: `service/src/main/kotlin/com/lwg/challenge/service/friend/FriendService.kt`
- Create: `controller/src/main/kotlin/com/lwg/challenge/controller/friend/FriendController.kt`
- Create: `controller/src/main/kotlin/com/lwg/challenge/controller/friend/dto/UserSearchResponse.kt`
- Create: `controller/src/main/kotlin/com/lwg/challenge/controller/friend/dto/FriendRequestResponses.kt`
- Create: `controller/src/main/kotlin/com/lwg/challenge/controller/friend/dto/FriendListResponse.kt`
- Create: `controller/src/main/kotlin/com/lwg/challenge/controller/friend/dto/SendFriendRequestRequest.kt`
- Create: `app/src/test/kotlin/com/lwg/challenge/controller/friend/FriendControllerTest.kt`
- Create: `app/src/test/kotlin/com/lwg/challenge/integration/FriendIntegrationTest.kt`

### 모바일 (`challenge-app`)
- Create: `remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/friend/UserSearchDto.kt`
- Create: `remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/friend/FriendRequestDto.kt`
- Create: `remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/friend/FriendDto.kt`
- Create: `remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/friend/SendFriendRequestBody.kt`
- Create: `remote/api/src/commonMain/kotlin/com/lwg/challenge/remote/api/FriendsApi.kt`
- Create: `remote/mapper/src/commonMain/kotlin/com/lwg/challenge/remote/mapper/friend/FriendMappers.kt`
- Create: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/friend/Friend.kt`
- Create: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/friend/FriendRequest.kt`
- Create: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/friend/UserSearchResult.kt`
- Create: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/friend/Relation.kt`
- Create: `domain/repository/src/commonMain/kotlin/com/lwg/challenge/domain/repository/FriendsRepository.kt`
- Create: `data/repositoryImpl/src/commonMain/kotlin/com/lwg/challenge/data/repository/FriendsRepositoryImpl.kt`
- Create: `core/invite/...` (신규 모듈, 모듈 등록 포함)
- Create: `feature/friends/src/commonMain/.../FriendsSearchViewModel.kt` + state/effect
- Create: `feature/friends/src/commonMain/.../FriendsSearchScreen.kt` + Preview
- Create: `feature/friends/src/commonMain/.../FriendsSearchRoute.kt`
- Create: `feature/friends/src/commonMain/.../component/FriendsSearchTopBar.kt` + Preview
- Create: `feature/friends/src/commonMain/.../component/FriendSearchItem.kt` + Preview
- Modify: `feature/friends/src/commonMain/.../FriendsViewModel.kt` (Data 확장 + 받은 요청 / 친구 목록)
- Modify: `feature/friends/src/commonMain/.../FriendsScreen.kt` (받은 요청 인라인 + 친구 목록 + 친구 추가/초대 액션)
- Modify: `feature/friends/src/commonMain/.../FriendsRoute.kt`
- Modify: `feature/friends/src/commonMain/.../contract/FriendsState.kt` (Data 확장)
- Create: `core/designsystem/.../components/friend/FriendListItem.kt` + Preview
- Create: `core/designsystem/.../components/friend/FriendRequestCard.kt` + Preview
- Modify: `core/navigation/.../Route.kt` (`FriendsRoute.Search`)
- Modify: `feature/main/.../MainScreen.kt` (NavDisplay 분기)
- Create: ViewModel 테스트 (`FriendsViewModelTest.kt` 확장, `FriendsSearchViewModelTest.kt` 신규)

### 디자인 (`challenge-design/oathbound-challenges`)
- Modify: 친구 목록 메인 화면 (받은 요청 인라인 + 친구 추가/초대 액션)
- Create: 친구 검색 화면 (검색 입력 + 결과 리스트 + relation 5종)
- Create: 검색 상태 분기 (입력 < 2자 / 결과 0건)

---

## 표준 dispatch prompt 헤더 (모든 subagent 호출 시 prepend)

````
## 시작 전 필수 읽기 — repo 규칙

1. {repo}/CLAUDE.md (모듈 구조, 컨벤션, Skill 매핑 테이블)
2. 매칭 skill — {작업 유형}:
   - 백엔드 controller 작성 → 기존 AuthController / RecordController 패턴 참조
   - 모바일 Compose UI → `.claude/skills/design-system` (자동 적용)
   - 모바일 feature → `.claude/skills/feature`
   - 모바일 ViewModel 테스트 → `.claude/skills/test-viewmodel`
3. spec-friend-add.md (작업 가이드)

위 3개를 모두 본 다음 작업 시작. CLAUDE.md와 spec 충돌 시 보고하고 결정 받기.

## 메모리 규칙 (반드시 준수)
- (모바일 dispatch 시) git 작업 전면 금지 — 브랜치/커밋/푸시/PR 모두 X. 코드 변경만 working tree에 두고 보고.
- Repository 표준 패턴: Flow<T> + onError 콜백 + AuthEventBus. 도메인 sealed Result 만들지 말 것 (kotlin stdlib Result는 OK). 401은 repository 내부에서 AuthEventBus.emit(Unauthorized).
- 신규 Composable은 반드시 @Preview 동봉 (상태 분기별, ChallengeTheme 래핑).
- Lovable 작업 결과는 모바일 design.md에 즉시 매핑.
````

---

## Tasks

### Task 1 — pm-lead: API contract 작성 (Phase 0)

**Files:**
- Create: `challenge_hub/docs/features/friends/api-contract-friend-add.md`

- [ ] **Step 1: pm-lead agent 정의 + api-contract skill 읽기**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/.claude/agents/pm-lead.md
cat /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/.claude/skills/api-contract/SKILL.md
```

- [ ] **Step 2: Agent tool로 pm-lead dispatch**

Agent tool, subagent_type=claude. Prompt:

```
당신은 pm-lead 에이전트입니다. .claude/agents/pm-lead.md 정의를 따르세요.

작업: friends feature 후속(친구 추가) — api-contract.md 작성.

입력 spec: /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/spec-friend-add.md

산출물: docs/features/friends/api-contract-friend-add.md (상태 `confirmed` — 모바일/백엔드 동시 진입 전제로 이미 spec에서 endpoint 합의됨)

api-contract 스킬을 그대로 사용. 다음 7개 endpoint 모두 명세:
1. GET  /api/v1/users/search?nickname={q}
2. POST /api/v1/friends/requests
3. POST /api/v1/friends/requests/{id}/accept
4. POST /api/v1/friends/requests/{id}/reject
5. DELETE /api/v1/friends/requests/{id}
6. GET  /api/v1/friends
7. GET  /api/v1/friends/requests/received

각 endpoint에 대해:
- HTTP method + path + query/body
- 요청 DTO 필드 + 검증 (min 2자 등)
- 응답 DTO 필드 (BaseResponse 패턴, ADR-0002)
- 가능한 에러 code (200/700/701/401)
- relation enum 5종 정확히 명시: NONE / REQUEST_SENT / REQUEST_RECEIVED / FRIEND / REJECTED
- 검색 응답에 pendingRequestId? (nullable) 포함 — REQUEST_SENT/RECEIVED일 때만 값 존재

페이지네이션: 검색 결과 LIMIT 20 (페이지네이션 없음). 친구 목록 / 받은 요청도 페이지네이션 없음 (소규모 가정).

인증: 모든 endpoint Authorization Bearer 필수.

마지막에 작성 완료 파일 절대 경로 보고.
```

- [ ] **Step 3: 산출물 확인**

```bash
test -f /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/api-contract-friend-add.md && head -20 /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/api-contract-friend-add.md
```
Expected: 파일 존재 + 헤더 `status: confirmed` 확인.

- [ ] **Step 4: PM hub 커밋**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub
git add docs/features/friends/api-contract-friend-add.md
git commit -m "docs(friends): api-contract-friend-add.md confirmed (T1)"
```

---

### Task 2 — design-bridge: Lovable 디자인 + design.md 갱신 (Phase 0)

**Files:**
- Modify: Lovable repo (`challenge-design/oathbound-challenges`) — 친구 목록 메인 화면 수정, 친구 검색 화면 신규
- Modify: `challenge_hub/docs/features/friends/design.md` — 본 작업 섹션 추가 (1차 1단계 섹션 위에 누적)

- [ ] **Step 1: design-bridge agent 정의 읽기**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/.claude/agents/design-bridge.md
```

- [ ] **Step 2: Agent tool로 design-bridge dispatch**

Agent tool, subagent_type=claude. Prompt (표준 헤더 prepend):

```
당신은 design-bridge 에이전트입니다. .claude/agents/design-bridge.md 정의를 따르세요.

작업: friends feature 후속(친구 추가) — Lovable 디자인 + design.md 갱신.

입력:
- spec: docs/features/friends/spec-friend-add.md
- 기존 1차 1단계 design.md: docs/features/friends/design.md (참조 + 동일 파일에 본 작업 섹션 추가)
- Lovable repo 경로: `.claude/config/repos.json` design 섹션 참조

작업 사항:

1. Lovable repo의 친구 목록 화면 수정:
   - 받은 요청 인라인 섹션 (친구 목록 위, "받은 요청 N건" 헤더 + 카드 리스트)
   - 받은 요청 카드: 프사 + 닉네임 + [수락] [거절] 버튼
   - 액션 진입점 2개: [친구 추가](검색 화면 진입) / [친구 초대](카톡 공유 진입)
   - 친구 0건 + 받은 요청 0건일 때는 1차 1단계의 FriendsEmptyState 노출 유지

2. Lovable에 친구 검색 화면 신규 제작:
   - 상단 검색 입력 (placeholder "닉네임 검색", 좌측 ← 뒤로가기)
   - 결과 리스트 (LIMIT 20)
   - 각 결과 아이템: 프사 + 닉네임 + relation별 액션 버튼/뱃지 5종
     - NONE → [친구 요청] (primary)
     - REQUEST_SENT → [요청 보냄 X] (secondary, X로 취소)
     - REQUEST_RECEIVED → [수락] (primary)
     - FRIEND → "이미 친구" (disabled badge)
     - REJECTED → [다시 요청] (secondary)
   - 검색 빈 상태 (입력 < 2자): 안내 텍스트 "닉네임을 2자 이상 입력해주세요"
   - 검색 결과 0건: 안내 텍스트 "검색 결과가 없어요. 닉네임을 더 정확히 입력해보세요."

3. Lovable 커밋 + push (디자인 repo 자체 컨벤션 따름).

4. `docs/features/friends/design.md`에 "## 2차 — 친구 추가" 섹션 신규 추가 (기존 1차 1단계 섹션 유지):
   - 화면 구조 (Lovable JSX 추출 + Compose 매핑)
   - 사용 토큰 (color / typography / spacing / radius)
   - Compose 컴포넌트 spec (props 시그니처):
     - FriendListItem(props: prof image url, nickname, modifier)
     - FriendRequestCard(props: prof image url, nickname, onAccept, onReject, modifier)
     - FriendSearchItem(props: prof image url, nickname, relation, onClickAction, onClickCancel?, modifier)
     - FriendsSearchTopBar(props: query, onQueryChange, onBack, modifier)
   - relation 5종 시각 명세 (버튼 색/모양/disabled 처리)

보고: design.md 절대 경로 + Lovable 커밋 hash + 모바일 측 정확 토큰/문구.

메모리 규칙: Lovable ↔ 모바일 동기. 디자인 결정은 양쪽에 즉시 반영. design.md를 단일 source of truth로.
```

- [ ] **Step 3: 산출물 확인**

```bash
grep -c "## 2차" /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/design.md
```
Expected: 1 이상.

- [ ] **Step 4: PM hub 커밋**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub
git add docs/features/friends/design.md
git commit -m "docs(friends): design.md 2차 친구 추가 화면 섹션 추가 (T2)"
```

- [ ] **Step 5: 사용자 안내 — 카카오 콘솔 작업 가이드**

사용자에게 다음 메시지 전달 (KakaoLink 템플릿은 사용자 직접 콘솔 작업):

```
카카오 디벨로퍼스 콘솔(https://developers.kakao.com)에서 다음 작업을 직접 진행해주세요:

1. 내 애플리케이션 → 메시지 → 메시지 템플릿 관리
2. "기본 템플릿 추가" → 커스텀 템플릿
3. 템플릿 구성:
   - 제목: ${inviterNickname}님이 challenge에 초대했어요
   - 본문: 맹세하고 도전하고 같이 성장해요
   - 버튼 1개: "challenge 앱 받기"
     - Android: market://details?id={packageName} (실제 패키지 ID 사용)
     - iOS: itms-apps://itunes.apple.com/app/id{APP_ID} (App Store ID 사용)
   - 템플릿 인자: inviterNickname (String, required)
4. 발급된 템플릿 ID를 다음 환경 변수에 추가:
   - challenge-app/local.properties: KAKAO_INVITE_TEMPLATE_ID=<발급된 ID>
5. 완료되면 알려주세요 (Task 7에서 사용).
```

---

### Task 3 — backend-dev: 백엔드 전체 구현 (Phase 1, 병렬)

**Files (산출물):**
- 도메인/엔티티/리포지토리/서비스/컨트롤러/통합 테스트 전부 (File Structure 백엔드 섹션 참조)

**선행 조건:** Task 1 (api-contract 확정)

- [ ] **Step 1: backend-dev agent 정의 읽기**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/.claude/agents/backend-dev.md
```

- [ ] **Step 2: Agent tool로 backend-dev dispatch**

Agent tool, subagent_type=claude. Prompt (표준 헤더 prepend):

```
당신은 backend-dev 에이전트입니다. .claude/agents/backend-dev.md 정의를 따르세요.

작업: friends feature 후속(친구 추가) — 백엔드 전체 구현 (TDD).

## 시작 전 필수 읽기
1. /Users/hwamulman/woogunProject/challenge/challenge-server/CLAUDE.md (있는 경우)
2. 기존 컨트롤러 패턴 참조:
   - controller/src/main/kotlin/com/lwg/challenge/controller/auth/AuthController.kt
   - controller/src/main/kotlin/com/lwg/challenge/controller/record/RecordController.kt
   - app/src/test/kotlin/com/lwg/challenge/controller/auth/AuthControllerTest.kt
3. 기존 통합 테스트 패턴:
   - app/src/test/kotlin/com/lwg/challenge/integration/AuthKakaoIntegrationTest.kt (있는 경우, 아니면 다른 통합 테스트)
4. 입력 spec: docs/features/friends/spec-friend-add.md
5. 입력 api-contract: docs/features/friends/api-contract-friend-add.md

## 구현 범위
spec section 5 (백엔드) 전체:
- domain/model: Friendship, FriendRequest, Friend, UserSearchResult, Relation enum
- domain/repository: FriendshipRepository interface
- infra/entity: FriendshipEntity (V1 friendships 매핑)
- infra/repositoryimpl: FriendshipJpaRepository + FriendshipRepositoryImpl
- service: FriendService (7개 메서드 — searchUsersByNickname / sendRequest / acceptRequest / rejectRequest / cancelRequest / listFriends / listReceivedRequests)
- controller: FriendController + dto
- 통합 테스트: FriendIntegrationTest (Testcontainers, end-to-end 시나리오 8건)
- 컨트롤러 슬라이스 테스트: FriendControllerTest

## TDD 원칙
- 통합 테스트 먼저 작성 (red) → service/controller 구현 → green
- relation 5종 모든 케이스 통합 테스트에 포함
- 동시 요청 race 시나리오 테스트 포함

## 구현 세부사항

### 검색 쿼리 (FriendshipRepositoryImpl 또는 native query)
spec 5.2 SQL 그대로 사용. LIKE escape는 service 계층에서 `%` `_` `\` 치환 (예: q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")). ESCAPE '\\' 절 추가. ORDER BY u.nickname ASC, u.id ASC LIMIT 20.

### service 동시 요청 처리
sendRequest 시 사전 검사: SELECT FROM friendships WHERE (requester=me AND receiver=target) OR (requester=target AND receiver=me). 반대 방향 PENDING이면 DialogException 또는 BaseResponse code 700 ("상대가 이미 친구 요청을 보냈어요. 받은 요청 화면에서 확인해주세요").

### accept / reject / cancel 권한 체크
- accept / reject는 receiver_id = me 만 가능 (다르면 BaseResponse 700 또는 ForbiddenException)
- cancel은 requester_id = me 만 가능
- 모든 mutation은 status가 PENDING일 때만 (이미 ACCEPTED/REJECTED면 409 또는 BaseResponse 700)

### BaseResponse 패턴 (ADR-0002)
- 정상: code 200 + data
- 비즈니스 에러: HTTP 200 + code 700 (스낵바) / 701 (다이얼로그)
- 인증: HTTP 401 + code 401 (UnauthorizedException, refresh 만료)

## 테스트 시나리오 (FriendIntegrationTest, 통합)
1. 검색 — 본인 제외 / 닉네임 contains / LIMIT 20
2. 검색 — 5가지 relation 모두 등장하는 시나리오 검증
3. 친구 요청 → 받은 요청 목록 / 보낸 요청 검색에서 REQUEST_SENT 확인
4. 수락 → 친구 목록에 추가, status ACCEPTED
5. 거절 → status REJECTED, 검색에서 REJECTED relation
6. 취소 → row 물리 삭제 (재요청 가능)
7. 동시 요청 race — A→B 후 B→A 시 사전 검사 안내 메시지
8. 미인증 — 401
9. 권한 외 accept/reject/cancel — 700

## 검증
모든 테스트 통과 후 다음 실행:
- `./gradlew :app:test --tests "com.lwg.challenge.controller.friend.*"` → all pass
- `./gradlew :app:test --tests "com.lwg.challenge.integration.FriendIntegrationTest"` → all pass

## 보고
- 변경 파일 목록
- 테스트 결과 (X/Y passed)
- 알려진 제약/한계
- challenge_hub/docs/features/friends/backend-report.md 작성 (다음 정보 포함):
  - 구현 endpoint 목록 + 매핑 클래스
  - 통합 테스트 시나리오 + 결과
  - V1 스키마 그대로 사용 (마이그레이션 0건) 확인 명시
  - 알려진 한계 (차단 미구현, FCM 없음 등 — spec section 10 참조)

git: 서버 repo는 backend-dev 자체 컨벤션 — 커밋/푸시는 normal flow (PM hub 측 메모리 규칙 "모바일 dispatch git 금지"는 모바일에만 해당).
```

- [ ] **Step 3: 산출물 확인**

```bash
test -f /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/backend-report.md && \
  cd /Users/hwamulman/woogunProject/challenge/challenge-server && \
  ./gradlew :app:test --tests "com.lwg.challenge.controller.friend.*" --tests "com.lwg.challenge.integration.FriendIntegrationTest" 2>&1 | tail -20
```
Expected: backend-report.md 존재 + 모든 테스트 PASSED.

- [ ] **Step 4: PM hub 커밋**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub
git add docs/features/friends/backend-report.md
git commit -m "docs(friends): backend-report.md (T3 — backend 구현 완료)"
```

---

### Task 4 — mobile-dev: 도메인 / Data 레이어 (Phase 1, 병렬)

**Files:** spec section 6.1 모바일 모듈의 :remote / :domain / :data 부분 (File Structure 모바일 섹션 참조)

**선행 조건:** Task 1 (api-contract 확정)

- [ ] **Step 1: mobile-dev agent 정의 + challenge-app skill 매핑 읽기**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/.claude/agents/mobile-dev.md
cat /Users/hwamulman/woogunProject/challenge/challenge-app/CLAUDE.md | head -100
ls /Users/hwamulman/woogunProject/challenge/challenge-app/.claude/skills/
```

- [ ] **Step 2: Agent tool로 mobile-dev dispatch**

Agent tool, subagent_type=claude. Prompt (표준 헤더 prepend):

```
당신은 mobile-dev 에이전트입니다. .claude/agents/mobile-dev.md 정의를 따르세요.

작업: friends feature 후속(친구 추가) — 모바일 도메인 + Data 레이어 구현.

## 시작 전 필수 읽기
1. challenge-app/CLAUDE.md — 특히 모듈 구조 / Skill 매핑 / DI(KSP) / Repository 규칙
2. 매칭 skill:
   - .claude/skills/domain (Domain Layer)
   - .claude/skills/data-remote (DTO/Ktorfit/Mapper/RepositoryImpl/Koin)
3. 입력: docs/features/friends/spec-friend-add.md (section 6) + docs/features/friends/api-contract-friend-add.md
4. 기존 참조 패턴:
   - remote/api/.../HomeApi.kt (Ktorfit interface 패턴)
   - data/repositoryImpl/.../HomeRepositoryImpl.kt (Flow + onError + AuthEventBus 패턴)

## 구현 범위
1. :remote:model
   - UserSearchDto (id, nickname, profileImageUrl, relation: String, pendingRequestId?)
   - FriendRequestDto (id, fromUser: UserBriefDto, requestedAt: String)
   - FriendDto (id, nickname, profileImageUrl, since: String)
   - SendFriendRequestBody (receiverId: Long)
   - UserBriefDto (id, nickname, profileImageUrl) — 신규 또는 기존 재사용
2. :remote:api FriendsApi (Ktorfit interface) — 7개 메서드, 모두 BaseResponse 래핑 (기존 ApiResult 패턴 따라)
3. :remote:mapper FriendMappers (DTO ↔ Domain)
4. :domain:model — Friend / FriendRequest / UserSearchResult / Relation enum (NONE/REQUEST_SENT/REQUEST_RECEIVED/FRIEND/REJECTED)
5. :domain:repository FriendsRepository (인터페이스 — spec 6.2 그대로)
6. :data:repositoryImpl FriendsRepositoryImpl + @Single + Koin 등록 (FriendsModule)

## Repository 패턴 (필수)
spec 6.2:
- 검색/목록: Flow<T> + onError 콜백
- mutation: suspend + kotlin stdlib Result<Unit>
- 401: repository 내부에서 AuthEventBus.emit(Unauthorized) — 기존 HomeRepositoryImpl 패턴 그대로
- 도메인 sealed Result 만들지 말 것 (kotlin stdlib Result는 OK)

## 검증
모든 모듈 빌드 통과:
- ./gradlew :remote:model:compileCommonMainKotlinMetadata
- ./gradlew :remote:api:compileCommonMainKotlinMetadata
- ./gradlew :remote:mapper:compileCommonMainKotlinMetadata
- ./gradlew :domain:model:compileCommonMainKotlinMetadata
- ./gradlew :domain:repository:compileCommonMainKotlinMetadata
- ./gradlew :data:repositoryImpl:compileCommonMainKotlinMetadata

## 메모리 규칙 — git 작업 전면 금지
모바일 repo에서 브랜치/커밋/푸시/PR 모두 금지. 코드 변경만 working tree에 두고 보고. 사용자가 직접 커밋.

## 보고
- 변경 파일 목록 (절대 경로)
- 각 모듈 빌드 결과
- 알려진 제약/이슈
```

- [ ] **Step 3: 산출물 확인**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-app
git status --short | head -30
./gradlew :data:repositoryImpl:compileCommonMainKotlinMetadata 2>&1 | tail -5
```
Expected: 신규 / 수정 파일 목록 + 빌드 SUCCESSFUL.

---

### Task 5 — mobile-dev: ViewModel + 테스트 (TDD) (Phase 1, 병렬)

**Files:**
- Modify: `feature/friends/.../FriendsViewModel.kt` + `contract/FriendsState.kt` (Data 확장)
- Create: `feature/friends/.../FriendsSearchViewModel.kt` + `contract/FriendsSearchState.kt`
- Create/Modify: `feature/friends/src/commonTest/.../FriendsViewModelTest.kt`, `FriendsSearchViewModelTest.kt`

**선행 조건:** Task 4 (Repository interface 존재)

- [ ] **Step 1: 매칭 skill 정의 읽기**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-app/.claude/skills/test-viewmodel/SKILL.md 2>/dev/null || ls /Users/hwamulman/woogunProject/challenge/challenge-app/.claude/skills/ | grep test
cat /Users/hwamulman/woogunProject/challenge/challenge-app/.claude/skills/viewmodel/SKILL.md 2>/dev/null
```

- [ ] **Step 2: Agent tool로 mobile-dev dispatch**

Agent tool, subagent_type=claude. Prompt (표준 헤더 prepend):

```
당신은 mobile-dev 에이전트입니다. .claude/agents/mobile-dev.md 정의를 따르세요.

작업: friends feature 후속 — ViewModel 2개 + 테스트 (TDD).

## 시작 전 필수 읽기
1. challenge-app/CLAUDE.md
2. 매칭 skill:
   - .claude/skills/viewmodel (StateFlow 파이프라인)
   - .claude/skills/test-viewmodel (Turbine + StateFlow/SharedFlow 변화 테스트)
3. 입력: docs/features/friends/spec-friend-add.md (section 6.5)
4. 선행 작업 산출물: Task 4의 FriendsRepository, 도메인 모델
5. 기존 패턴: feature/home/.../HomeViewModel.kt + HomeViewModelTest.kt
6. 기존 친구 ViewModel: feature/friends/.../FriendsViewModel.kt (1차 1단계 산출물, 빈 상태 ViewModel)

## TDD 진행

### A. FriendsViewModel 확장 (메인 화면)
1. FriendsViewModelTest.kt 확장 — 다음 케이스 추가 (RED):
   - init 시 Loading → Data 진입 (받은 요청 + 친구 목록 모두 비어있는 케이스)
   - 받은 요청 N건 + 친구 M건 로드 케이스
   - 수락 호출 시 받은 요청에서 제거 + 친구 목록에 추가 (낙관적 갱신)
   - 거절 호출 시 받은 요청에서 제거
   - 수락 실패 시 ShowMessage effect + 목록 롤백
2. FriendsState.kt 수정 — Data를 다음으로 확장 (GREEN):
   ```
   data class Data(
       val receivedRequests: List<FriendRequestItemState>,
       val friends: List<FriendItemState>,
   ) : FriendsUiState
   ```
3. FriendsViewModel.kt 수정 — FriendsRepository 주입 + combine으로 두 Flow 결합 + 수락/거절 메서드 추가.
4. 빌드 + 테스트 통과 확인.

### B. FriendsSearchViewModel 신규
1. FriendsSearchViewModelTest.kt 신규 (RED):
   - 입력 < 2자 → Idle
   - 입력 ≥ 2자 → debounce 300ms → Searching → Result(items)
   - 결과 0건 → Empty
   - relation별 액션 클릭 → 낙관적 갱신 (검색 결과 자체 갱신)
   - 액션 실패 시 ShowMessage + 롤백
2. FriendsSearchState.kt 신규 (Idle / Searching / Result / Empty) (GREEN)
3. FriendsSearchViewModel.kt 신규 — query StateFlow → debounce(300ms) → flatMapLatest → searchUsers 호출.

### C. ItemState 클래스
spec 6.5 참조 — FriendRequestItemState, FriendItemState, FriendSearchItemState. UI State 파싱 규칙 (CLAUDE.md): get() 프로퍼티로 actionLabel / isActionEnabled / showCancel 등 노출.

## 검증
- ./gradlew :feature:friends:testDebugUnitTest (Android target)
- ./gradlew :feature:friends:compileCommonMainKotlinMetadata
모든 테스트 PASS. 새 테스트 케이스 8건 이상 확보.

## 메모리 규칙 — git 작업 전면 금지

## 보고
- 변경 파일 목록
- 테스트 결과 (X/Y passed)
- 기존 FriendsViewModelTest 케이스 + 신규 케이스 모두 PASS 명시
```

- [ ] **Step 3: 산출물 확인**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-app
./gradlew :feature:friends:testDebugUnitTest 2>&1 | tail -10
```
Expected: BUILD SUCCESSFUL + tests count ≥ 8 passed.

---

### Task 6 — mobile-dev: designsystem 컴포넌트 + Preview (Phase 1, 병렬)

**Files:**
- Create: `core/designsystem/.../components/friend/FriendListItem.kt` + Preview
- Create: `core/designsystem/.../components/friend/FriendRequestCard.kt` + Preview

**선행 조건:** Task 2 (design.md 2차 섹션 작성됨)

- [ ] **Step 1: design-system skill 정의 + design.md 읽기**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-app/.claude/skills/design-system/SKILL.md
grep -A 200 "## 2차" /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/design.md
```

- [ ] **Step 2: Agent tool로 mobile-dev dispatch**

Agent tool, subagent_type=claude. Prompt (표준 헤더 prepend):

```
당신은 mobile-dev 에이전트입니다.

작업: :core:designsystem에 친구 시스템 공통 컴포넌트 2개 신규 + Preview (Compose Multiplatform).

## 시작 전 필수 읽기
1. challenge-app/CLAUDE.md — 119-123 Preview 필수 규칙
2. .claude/skills/design-system (자동 적용 — 디자인 토큰 / 컴포넌트 규칙)
3. design.md 2차 섹션 (challenge_hub/docs/features/friends/design.md "## 2차" 이하)
4. 기존 1차 1단계 산출물 참조: core/designsystem/.../components/friend/FriendsEmptyState.kt

## 구현 대상
1. FriendListItem(profileImageUrl: String?, nickname: String, modifier: Modifier = Modifier)
   - 행 1개: 프사 + 닉네임
   - Preview: 일반 케이스 + 긴 닉네임 케이스 + 프사 없음 케이스 (3건)
2. FriendRequestCard(profileImageUrl: String?, nickname: String, onAccept: () -> Unit, onReject: () -> Unit, modifier: Modifier = Modifier)
   - 카드: 프사 + 닉네임 + [수락] [거절] 버튼 (행 또는 컬럼 배치는 design.md 따름)
   - Preview: 1건 (기본)

## Preview 규칙 (필수)
- 같은 파일 하단에 private @Composable fun {Name}Preview() 형태
- import org.jetbrains.compose.ui.tooling.preview.Preview
- ChallengeTheme { } 래핑 + ChallengeTheme.colorScheme.background
- 상태 분기마다 Preview 별도

## 검증
- ./gradlew :core:designsystem:compileCommonMainKotlinMetadata
- ./gradlew :core:designsystem:compileDebugKotlinAndroid

## 메모리 규칙 — git 작업 전면 금지

## 보고
- 변경 파일 목록 + Preview 함수 개수
- 빌드 결과
```

- [ ] **Step 3: 산출물 확인**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-app
find core/designsystem -name "FriendListItem.kt" -o -name "FriendRequestCard.kt"
grep -c "@Preview" core/designsystem/src/commonMain/kotlin/com/lwg/challenge/designsystem/components/friend/FriendListItem.kt
./gradlew :core:designsystem:compileDebugKotlinAndroid 2>&1 | tail -5
```
Expected: 두 파일 존재, FriendListItem에 @Preview 3건, 빌드 SUCCESSFUL.

---

### Task 7 — mobile-dev: feature 화면 + Navigation + KakaoLink 통합 (Phase 1)

**Files:**
- Modify: `feature/friends/.../FriendsScreen.kt` + `FriendsRoute.kt`
- Create: `feature/friends/.../FriendsSearchScreen.kt` + `FriendsSearchRoute.kt`
- Create: `feature/friends/.../component/FriendsSearchTopBar.kt` + `FriendSearchItem.kt` (Preview 포함)
- Modify: `core/navigation/.../Route.kt`
- Modify: `feature/main/.../MainScreen.kt`
- Create: `core/invite/` 신규 모듈 (KakaoInviter expect/actual)
- Modify: `feature/friends/build.gradle.kts` (`:core:invite` 의존)
- Modify: `composeApp/build.gradle.kts` + `settings.gradle.kts` (`:core:invite` 등록)

**선행 조건:** Task 5 (ViewModel) + Task 6 (designsystem 컴포넌트) + Task 2-Step 5 (카카오 콘솔 템플릿 ID 발급)

- [ ] **Step 1: 카카오 콘솔 작업 완료 확인**

사용자에게 확인 — local.properties의 `KAKAO_INVITE_TEMPLATE_ID` 발급 완료?
Expected: 사용자가 "완료" 응답 + 템플릿 ID 공유.

- [ ] **Step 2: feature / navigation skill 정의 읽기**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-app/.claude/skills/feature/SKILL.md
cat /Users/hwamulman/woogunProject/challenge/challenge-app/.claude/skills/navigation/SKILL.md
```

- [ ] **Step 3: Agent tool로 mobile-dev dispatch**

Agent tool, subagent_type=claude. Prompt (표준 헤더 prepend):

```
당신은 mobile-dev 에이전트입니다.

작업: friends feature 후속 — UI 화면 + Navigation + KakaoLink invite 모듈 통합.

## 시작 전 필수 읽기
1. challenge-app/CLAUDE.md (Compose Preview 필수, Navigation 패턴, KMP expect/actual)
2. .claude/skills/feature (Screen 구성, NavDisplay 통합)
3. .claude/skills/navigation (Route 추가)
4. 기존 카카오 SDK 통합 부분: feature/login/.../KakaoLoginManager 등 (찾아서 패턴 파악)
5. design.md 2차 섹션 (모바일 매핑 영역)
6. spec-friend-add.md section 6 / 7

## 구현 범위

### A. :core:invite 신규 모듈
- settings.gradle.kts에 `:core:invite` 등록
- build.gradle.kts (android-library + kotlin-multiplatform + ksp + koin)
- commonMain: `interface KakaoInviter { suspend fun sendInvite(templateArgs: Map<String, String>): Result<Unit> }`
- commonMain: InviteModule (@Module + @ComponentScan)
- androidMain: AndroidKakaoInviter implements KakaoInviter using Kakao SDK Share (kakao-sdk-share dependency). ActivityProvider 주입 (기존 카카오 로그인 패턴 재사용).
- iosMain: IosKakaoInviter using ShareApi.shared.shareCustom from KakaoSDKShare. 카카오 로그인이 이미 iOS에 통합돼 있다면 동일 의존성 그룹에 share 모듈 추가.
- templateId는 build config or local.properties로 주입 (`KAKAO_INVITE_TEMPLATE_ID`).

### B. Route + Navigation
- core/navigation/.../Route.kt에 다음 추가:
  ```
  @Serializable sealed interface FriendsRoute : Route {
      @Serializable data object Main : FriendsRoute
      @Serializable data object Search : FriendsRoute
  }
  ```
  (기존 1차 1단계가 어떤 식으로 됐는지 보고 호환 유지)
- feature/main/.../MainScreen.kt의 NavDisplay 블록에 FriendsRoute.Search 분기 추가.

### C. FriendsScreen (메인) 수정
- 받은 요청 인라인 섹션 (FriendsUiState.Data.receivedRequests 사용 → FriendRequestCard 리스트)
- 친구 목록 섹션 (FriendListItem 리스트)
- 액션 진입점 2개: "친구 추가" → backStack.add(FriendsRoute.Search), "친구 초대" → kakaoInviter.sendInvite() 호출
- 빈 상태 (양쪽 모두 0건): 기존 FriendsEmptyState 재사용
- ViewModel의 ShowMessage effect 수집 → 스낵바
- @Preview: Loading / Data(empty) / Data(친구만 있음) / Data(요청+친구 있음)

### D. FriendsSearchScreen (신규)
- 상단 FriendsSearchTopBar (검색 입력 + 뒤로가기)
- 4-state 분기: Idle / Searching / Result(items) / Empty
- 결과 리스트 → FriendSearchItem (relation별 액션)
- viewModel.search 함수 + viewModel.onAction(item) 호출
- @Preview: 4-state 각각

### E. FriendsRoute (KMP composable, ViewModel 연결)
- FriendsRoute(viewModel = koinViewModel(), onNavigateToSearch, kakaoInviter = koinInject())
- showMessage effect 수집

### F. FriendsSearchRoute 신규 동일 패턴.

### G. KakaoInviter 호출 흐름
- "친구 초대" 버튼 클릭 → viewModel이 kakaoInviter.sendInvite(mapOf("inviterNickname" to me.nickname)) 호출
- 성공 → 스낵바 (선택, 또는 무동작)
- 실패 → 스낵바 "친구 초대를 보낼 수 없어요"
- 내 닉네임은 어디서? UserRepository.getMe() 또는 기존 home의 me 패턴 재사용

## Preview 필수
신규 Composable 모두 @Preview 동봉 — 상태 분기별.

## 검증
- ./gradlew :composeApp:compileDebugKotlinAndroid
- ./gradlew :feature:friends:compileDebugKotlinAndroid
- ./gradlew :core:invite:compileDebugKotlinAndroid

## 메모리 규칙 — git 작업 전면 금지

## 보고
- 변경 / 신규 파일 목록 (각 모듈 별로)
- @Preview 개수
- 빌드 결과
- 검색 → 요청 → 수락 시나리오의 manual smoke 절차 메모 (사용자가 디바이스에서 검증할 수 있도록)
- KakaoLink 동작 확인 절차 (manual: 친구 초대 → 카톡 공유 시트 → 메시지 전송 확인)
```

- [ ] **Step 4: 산출물 확인**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-app
./gradlew :composeApp:compileDebugKotlinAndroid 2>&1 | tail -5
git status --short | wc -l
```
Expected: 빌드 SUCCESSFUL + 변경 파일 다수.

---

### Task 8 — 통합 검증 + report-and-document (Phase 2)

**Files:**
- Modify: `challenge_hub/docs/features/friends/mobile-report.md` (T4-T7 종합)
- Modify: `challenge_hub/docs/features/friends/summary.md` (1차 1단계 정정 노트 + 본 작업 완료 섹션)
- Modify: `challenge_hub/docs/features/INDEX.md`
- Modify: `challenge_hub/docs/backlog.md` (후속 항목 등재)

**선행 조건:** Task 3 (백엔드 완료) + Task 7 (모바일 완료)

- [ ] **Step 1: 통합 manual smoke 안내**

사용자에게 안내 — 실 디바이스 / 에뮬레이터로 다음 시나리오 확인 요청:
1. 친구 화면 진입 → 빈 상태 OK
2. "친구 추가" → 검색 화면, "이우" 입력 → 결과 노출
3. 친구 요청 → 백엔드 PENDING row 생성 확인 (DB 직접 또는 API)
4. 다른 계정으로 로그인 → 받은 요청 노출 → 수락 → 친구 목록에 추가
5. 친구 검색 시 relation이 FRIEND로 보이는지
6. "친구 초대" → 카톡 공유 시트 → 메시지 미리보기 정상

문제 발생 시 해당 task로 돌아가 수정.

- [ ] **Step 2: mobile-dev 보고 산출물 정리**

T4-T7 보고 내용을 종합해 `challenge_hub/docs/features/friends/mobile-report.md` 작성:
- 변경 / 신규 파일 수 (모듈별)
- ViewModel 테스트 결과 (X/Y passed)
- 빌드 결과 (Android + iOS)
- KakaoLink 동작 확인 결과
- 알려진 제약 (FCM 없음, inviter 자동 연결 없음 등)

```bash
# manual 작성 또는 mobile-dev에 별도 dispatch (선택)
```

- [ ] **Step 3: pm-lead dispatch — report-and-document skill**

Agent tool, subagent_type=claude. Prompt:

```
당신은 pm-lead 에이전트입니다.

작업: friends feature 후속(친구 추가) 완료 문서화.

report-and-document 스킬을 그대로 사용:

1. challenge_hub/docs/features/friends/summary.md 갱신:
   - 1차 1단계 섹션 유지
   - 상단에 "## 2차 — 친구 추가 (2026-MM-DD 완료)" 섹션 추가
   - spec-friend-add.md / api-contract-friend-add.md / backend-report.md / mobile-report.md 참조 링크
   - 테스트 결과 숫자 명시 (백엔드 통합 X/Y, 모바일 ViewModel X/Y)
   - 1차 1단계 spec drift 정정 노트 (한 줄): "본 작업 spec-friend-add.md section 2에서 1차 1단계 spec/plan의 friendships 양방향 단일 row 가정을 V1 실제 스키마(requester/receiver + status)로 정정함."

2. challenge_hub/docs/features/INDEX.md:
   - friends 상태를 "completed" 또는 "1차 2단계 완료"로 갱신

3. challenge_hub/docs/backlog.md에 후속 항목 등재 (spec section 10 참조):
   - [ ] friends 차단(BLOCKED) 기능
   - [ ] FCM 푸시 알림 통합 (친구 요청 + 챌린지 응원/평가)
   - [ ] KakaoLink inviter 자동 연결 (deep link + Universal Link)
   - [ ] 친구 삭제
   - [ ] 검색 성능 개선 (trigram / Elasticsearch — 임계점 도달 시)

보고: 갱신된 3개 파일 절대 경로.
```

- [ ] **Step 4: PM hub 최종 커밋**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub
git add docs/features/friends/mobile-report.md \
        docs/features/friends/summary.md \
        docs/features/INDEX.md \
        docs/backlog.md
git commit -m "docs(friends): 2차 친구 추가 완료 문서화 (T8)"
```

- [ ] **Step 5: 사용자에게 푸시 권한 확인**

```
모든 작업 완료. PM hub commit 5건 (T1, T2, T3, T7-mobile-report, T8). 
push 진행할까요? — 사용자 결정 후 진행.
```

(메모리 규칙: PM hub git 작업은 사용자 명시 승인 후 push)

---

## 후속 작업 (본 plan 범위 외)

spec section 10 참조. 별도 spec/plan으로 분리:
- 차단(BLOCKED) 기능
- FCM 푸시 알림 통합
- KakaoLink inviter 자동 연결 (deep link)
- 친구 삭제
- 검색 성능 개선 (trigram / Elasticsearch)
