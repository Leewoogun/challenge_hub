# 친구 화면 (friends)

- **feature-id**: friends
- **owner**: pm-lead
- **상태**: draft
- **생성**: 2026-06-24
- **범위**: 본 spec은 **1차 1단계 — 친구 없는 신규 사용자용 빈 상태 화면만**. 친구 목록 렌더링 / 백엔드 API / 데이터 모델은 **1차 2단계(별도 작업)**로 명시만 하고 본 단계에선 구현하지 않는다.

## 배경 / 문제

bottom-navigation 완료로 친구 탭 진입점은 마련됐지만, `:feature:friends`는 `generate-feature.sh` 템플릿 잔재(`FriendsScreen = PlaceholderScreen`, `FriendsUiState.Data(placeholder: Unit)`) 상태다. 사용자는 BottomBar의 친구 탭을 누르면 "친구" 한 글자만 떠 있는 placeholder를 보게 된다.

Lovable에는 **친구가 있을 때**의 친구 목록 화면 디자인이 이미 있지만, **친구가 없는 신규 사용자**가 보게 될 빈 상태 화면이 부재하다. 첫 사용 경험의 큰 공백.

본 1차 1단계는 이 공백 메우기 — 빈 상태 화면만 디자이너 산출물 + 모바일 컴포넌트로 완성. 백엔드 데이터/API 없이 모든 사용자가 일단 빈 상태로 보이도록 한다. 친구 목록·API·데이터 모델은 1차 2단계에서 묶어 처리.

## 사용자 시나리오

1. **신규/기존 무관, 친구 탭 진입** → "친구" topBar + 빈 상태 컴포넌트(아이콘 또는 일러스트 + 헤드라인 + 서브 텍스트 + "친구 추가하기" stub CTA 버튼 1개) 표시.
2. **stub CTA 탭** → 1차 1단계엔 무동작 또는 "준비 중입니다" 안내(스낵바). 1차 2단계 이후 친구 추가 feature 진입 시 라우팅 연결.
3. **홈 화면 `FIRST_USER` 빈 상태의 "친구 등록" CTA** → 현재처럼 친구 탭으로 `switchTab` (변경 없음). 친구 탭에서 본 빈 상태가 자연스럽게 이어진다.

## 수용 기준 (Acceptance Criteria)

- [ ] `:feature:friends`의 `PlaceholderScreen`이 빈 상태 컴포넌트로 교체된다. 템플릿 `placeholder: Unit` TODO 잔재 정리.
- [ ] 빈 상태 컴포넌트는 `:core:designsystem/components/friend/FriendsEmptyState.kt`에 재사용 단위로 위치한다.
- [ ] 빈 상태 컴포넌트는 디자인 시스템 토큰(`tokens.md` / `colors.md`)만 사용. 인라인 색·간격 금지.
- [ ] Lovable에 친구 탭 빈 상태 화면이 추가되어 모바일과 동기된다(메모리 규칙: 디자인 결정은 양쪽 즉시 반영).
- [ ] 친구 탭 topBar(제목 "친구" + 디자이너 결정에 따라 알림/검색 아이콘 stub)가 표시된다. 홈의 `HomeTopBar`와 시각적 결을 맞춘다.
- [ ] stub CTA 버튼이 표시되며 onClick이 stub(무동작 또는 "준비 중" 스낵바)이다.
- [ ] BottomBar는 친구 탭에서도 그대로 노출된다(MainScreen 변경 없음).
- [ ] LoginViewModelTest / HomeViewModelTest 등 기존 회귀 테스트 0건 fail.

## 비범위 (Out of Scope) — 1차 2단계로 이연

- 백엔드 — `friendships` 테이블 / `FriendController` / `GET /api/v1/friends` / `FriendService` / 통합 테스트. **0건.**
- 모바일 도메인/Repository/UseCase/Remote API/Mapper 레이어 — `Friend` 도메인 모델, `FriendRepository`, `GetFriendsUseCase`, `FriendApi`, `FriendsResponseMapper`. **0건.**
- 친구 목록 렌더링 (`FriendCard` LazyColumn).
- 친구 카드 탭 동작 — 친구 프로필 화면, 챌린지 생성 화면 진입 라우팅.
- 빈 상태 CTA 버튼 실제 라우팅 — 친구 추가 feature(`friends-add` 등) 진입.
- 친구 추가 흐름 — 닉네임 검색, 연락처 매칭(ADR-0008), 카카오 친구 가져오기.
- 친구 요청 받기/보내기/수락/거절.
- 친구 삭제 / 차단 / 신고.
- 페이지네이션 / pull-to-refresh.

## 태스크 분해

### 디자인 (design-bridge)
- [ ] T-D1: Lovable 기존 친구 탭 화면 점검 — 친구 카드 디자인(필드, 레이아웃) 정리해 `design.md`에 모바일 정합 가이드로 기록(1차 2단계 입력으로 활용).
- [ ] T-D2: Lovable에 친구 탭 **빈 상태 화면** 신규 — 아이콘/일러스트 + 헤드라인 + 서브 텍스트 + stub CTA 버튼 1개. 디자인 시스템 토큰만 사용.
- [ ] T-D3: `docs/features/friends/design.md` 작성 — 화면 구조 / 토큰 매핑 / Compose 컴포넌트 spec(`FriendsEmptyState` props, `FriendsTopBar` 구성) / 모바일 대응 가이드.

### 모바일 (mobile-dev)
- [ ] T-M1: `:core:designsystem/components/friend/FriendsEmptyState.kt` 신설 — 디자이너 산출물 기반. props: 아이콘/일러스트 식별자, 헤드라인·서브 텍스트(리소스), `onClickCta: () -> Unit`.
- [ ] T-M2: `:core:designsystem/components/friend/FriendsTopBar.kt` 신설 — 제목 "친구" + (디자이너 결정 시) 알림/검색 아이콘 stub. `HomeTopBar` 패턴 답습.
- [ ] T-M3: `:feature:friends/FriendsScreen.kt` 교체 — `PlaceholderScreen` → `ChallengeScaffold(topBar = FriendsTopBar) { FriendsEmptyState(onClickCta = { showMessage("준비 중입니다") }) }`.
- [ ] T-M4: `:feature:friends/FriendsViewModel.kt` 정리 — 의존성 0개 유지(또는 향후 확장 위한 코멘트만). `placeholder: Unit` TODO 제거. 진입과 동시에 `FriendsUiState.Data` 상태.
- [ ] T-M5: `:feature:friends/contract/FriendsUiState.kt` — `Data`를 `data object Data` 또는 빈 `data class Data()`로 단순화. 향후 친구 목록 도입 시 필드 추가하는 자리 명시.
- [ ] T-M6: `FriendsRoute` — 변경 최소. CTA stub 콜백은 라우팅 미연결.
- [ ] T-M7: 빌드 검증 — `:feature:friends:compileCommonMainKotlinMetadata` + `:feature:friends:testDebugUnitTest` BUILD SUCCESSFUL + 기존 ViewModelTest 회귀 0.

### 백엔드 (backend-dev)
- **본 단계 작업 없음.** 1차 2단계 진입 시 별도 spec 갱신 또는 본 spec change-log로 추가.

## 의존 관계

- **T-D1~D3 → T-M1~M3 선행** (디자이너 산출물이 모바일 빈 상태 컴포넌트 구현 입력).
- T-M1 → T-M3 (컴포넌트 → 화면 사용).
- T-M2 → T-M3 (topBar → Scaffold 조립).
- T-M4 / T-M5 / T-M6 / T-M7은 T-M3과 병렬 가능.
- **사용자 지시**: 디자이너 트랙(T-D1~D3) 먼저 진행, 산출물 받은 뒤 모바일 트랙(T-M1~M7) 진입.

## 후속 계획 — 1차 2단계 (`friends-list` 또는 본 feature 확장)

본 spec과 별도 작업으로 처리. 이번 단계 종료 후 진입 시점 사용자 결정.

**백엔드**:
- Flyway V5 마이그레이션: `friendships(user_a_id, user_b_id, since, PK + CHECK user_a_id < user_b_id)` + `idx_friendships_b`.
- 도메인: `Friendship`, `Friend(friendId, nickname, profileImageUrl)` view.
- Repository / Service / Controller: `GET /api/v1/friends` 단일 read 트랜잭션 + JOIN 1쿼리(`friendships ⨝ users`, 정렬 `nickname ASC`).
- 통합 테스트 3건(친구 0명 / 친구 N명·정렬·필드 매핑 / 위조 토큰 401).

**모바일**:
- 도메인 `Friend`, `FriendRepository`(Flow + onError + AuthEventBus 표준 패턴 — 메모리 규칙), `GetFriendsUseCase`.
- Remote: `FriendApi`, `FriendsResponse` DTO, `FriendsResponseMapper`.
- Data: `FriendRepositoryImpl`(401 시 `AuthEventBus.emitSessionExpired()`).
- `FriendsUiState`에 `friends: List<Friend>` 필드 추가, `Data.isEmpty` derived 프로퍼티. 본 1차 1단계의 빈 상태 분기는 그대로 활용.
- `:core:designsystem/components/friend/FriendCard.kt` 신설(T-D1 산출물 기반).
- `FriendsViewModelTest` 시나리오: 빈 응답 → `isEmpty=true`, N건 응답 → `isEmpty=false`, 에러 → `ShowMessage` 효과.

**카드 탭 / CTA 라우팅**: 후속의 후속(친구 추가 feature, 챌린지 생성 feature) 진입 시 연결.

## 리스크 / 오픈 이슈

- **빈 상태 CTA 라벨·아이콘 결정 디자이너 의존**: "친구 추가하기" 외 다른 문구·아이콘 후보가 있다면 디자이너 결정. 본 spec은 라벨 1안만 가정.
- **`FriendsTopBar` 액션 슬롯(알림/검색)**: 1차 1단계엔 노출 여부 불명확. 디자이너가 friends 탭 통일된 topBar 정의 시 결정. 본 spec은 미노출 default.
- **빈 상태 컴포넌트 재사용성**: `HomeEmptyState`처럼 type enum으로 두 화면(home + friends) 공용 vs 화면별 분리. 본 spec은 화면별 분리(`FriendsEmptyState`)로 가정 — friends 빈 상태 메시지·CTA가 home과 다르고 일러스트도 따로 가져갈 가능성. 디자이너 점검 시 통합 가능성 재검토.
- **`generate-feature.sh` 잔재(`FriendsModalEffect.Hidden`)**: 본 1차 1단계엔 modal 사용처 없음. 제거 vs 향후 친구 추가 feature 위해 보존. 본 spec은 **보존**(`Hidden` 1 case만 유지).
- **HomeScreen `FIRST_USER` 빈 상태의 "친구 등록" CTA**: 현재 `switchTab(FriendsRoute.Main)`로 친구 탭만 보냄. 친구 탭에서도 빈 상태 + "친구 추가하기" stub → 진짜 친구 추가 화면 없음 → 사용자 경험상 순환. 1차 2단계 진입 전까지 감수.
