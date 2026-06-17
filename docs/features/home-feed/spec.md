# 홈 피드 (home-feed)

- **feature-id**: home-feed
- **owner**: pm-lead
- **상태**: draft
- **생성**: 2026-05-25

## 배경 / 문제

bottom-navigation 완료로 홈 탭의 진입점은 마련됐지만, `:feature:home`은 여전히 템플릿 잔재인 Movie 예제 화면이다(ADR-0003 잔여). 사용자가 앱을 열었을 때 가장 먼저 보는 화면이므로 challenge 도메인 정체성을 즉시 전달해야 한다.

홈은 두 가지 핵심 정보를 한 화면에서 제공한다:
1. **진행 중인 챌린지** — 사용자가 지금 책임지고 있는 약속들
2. **나의 전적** — 7승 3패 2무 / 연승 같은 누적 결과

신규 가입 사용자는 둘 다 비어있으므로, 빈 상태에서도 다음 행동(친구 등록 → 첫 챌린지 시작)을 명확히 유도해야 한다.

## 사용자 시나리오

1. **기존 사용자가 홈을 연다** → 헤더(맹세 로고 + 알림 벨) + 전적 카드(승/패/무/연승) + 진행 중인 챌린지 카드 목록(시간순) + 우하단 FAB(챌린지 생성) 표시.
2. **신규 사용자(첫 로그인)가 홈을 연다** → 전적 카드는 모두 0(또는 placeholder) 표시 + 진행 중인 챌린지 자리에 빈 상태 UI("아직 챌린지가 없어요" + 친구 등록/챌린지 만들기 CTA) 표시.
3. **진행 중인 챌린지가 0개인 기존 사용자** → 전적 카드는 누적값 유지 + 챌린지 영역만 빈 상태로 전환("새 챌린지를 시작해보세요" CTA만).
4. **챌린지 카드 탭** → 챌린지 상세 화면으로 이동(이번 feature 범위 밖, navigation 연결만).
5. **FAB 탭** → 챌린지 생성 화면으로 이동(이번 feature 범위 밖, navigation 연결만).

## 수용 기준 (Acceptance Criteria)

- [ ] 홈 화면이 `GET /api/v1/home` 단일 호출로 전적 + 진행 중 챌린지를 동시에 받아 렌더링한다.
- [ ] 신규 사용자(전적·챌린지 둘 다 0)의 빈 상태가 별도 컴포넌트로 표시된다(스피너/실패 화면과 구분).
- [ ] 전적은 승/패/무/연승 4개 숫자를 모두 표시. 데이터가 0이어도 "0" 또는 placeholder 처리(빈 칸 금지).
- [ ] 진행 중인 챌린지 카드는 내 미션, 상대 닉네임, 상대 미션, 남은 시간, 내 인증 상태, 상대 인증 상태, 내기 내용 7개 필드를 표시.
- [ ] 챌린지 목록은 마감 임박순(deadline asc)으로 정렬.
- [ ] API 응답 BaseResponse code=200만 성공. 그 외 code/네트워크 실패는 재시도 가능한 에러 상태로 표시.
- [ ] 401 토큰 만료 시 로그인 화면으로 라우팅.
- [ ] `:feature:home` 모듈에 남아있던 Movie 예제 코드(데이터 모델/뷰모델/Composable) 완전 제거.
- [ ] LoginViewModelTest 등 기존 회귀 테스트 0건 fail.

## 비범위 (Out of Scope)

- 챌린지 상세 화면 구현(navigation 진입 stub만).
- 챌린지 생성 화면 구현(FAB 진입 stub만).
- 알림 화면 진입(벨 아이콘은 표시만, 추후 push-fcm/notifications feature).
- 풀-투-리프레시(pull-to-refresh) 제스처 — 단순 진입 시 1회 조회만.
- 페이지네이션 — 진행 중 챌린지는 사용자당 동시 진행 한도(별도 정책)로 제한되므로 cursor/offset 불필요.
- 친구 매칭/연락처 동기화(빈 상태의 "친구 등록" CTA는 friends 탭으로 라우팅만).

## 태스크 분해

### 모바일 (mobile-dev)
- [ ] T-M1: `:feature:home`에서 Movie 예제 코드(`MovieListScreen` 등) 완전 제거.
- [ ] T-M2: `HomeScreen` Composable 작성 — 헤더 + 전적 카드 + 진행 중 챌린지 리스트 + 빈 상태 + FAB.
- [ ] T-M3: `HomeViewModel` + `GetHomeFeedUseCase` + `HomeRepository` impl/remote 레이어 구현(`:domain`/`:data`/`:remote` 분리).
- [ ] T-M4: `:core:designsystem`에 `ChallengeCard`(7필드) + `StatsBar`(4숫자) + `HomeEmptyState` 추가(다른 화면 재사용 가능 단위로).
- [ ] T-M5: HomeViewModel 단위 테스트(로딩/성공/빈상태/에러 4상태).

### 백엔드 (backend-dev)
- [ ] T-B1: Flyway 마이그레이션 — `user_stats`(win/lose/draw/current_streak/best_streak) 테이블 + `challenges` 테이블 컬럼 확정(스켈레톤이므로 신규 생성).
- [ ] T-B2: `GET /api/v1/home` 컨트롤러/서비스 — 인증된 사용자의 진행중 챌린지(IN_PROGRESS + CONTRACT_SIGNING 상태, deadline asc 정렬) + user_stats를 한 응답으로.
- [ ] T-B3: 빈 데이터 정상 처리(신규 사용자 user_stats row 없으면 0 응답, 진행 중 챌린지 빈 배열).
- [ ] T-B4: AuthKakao 통합 테스트와 동일 패턴의 home 통합 테스트 3건(신규 사용자, 챌린지 1+개, 401 만료 토큰).

### 디자인 (design-bridge)
- [ ] T-D1: Lovable `index.tsx`에 빈 상태 UI 추가(친구 등록/챌린지 만들기 CTA 2개 버튼) + 챌린지 0개 분기 처리.
- [ ] T-D2: `docs/features/home-feed/design.md` 작성 — 화면 구조 / 토큰 / Compose 매핑 / 빈 상태 가이드 / 모바일 대응.
- [ ] T-D3: `ChallengeCard`, `StatsBar`, `HomeEmptyState` 컴포넌트의 spec(props, 상태별 표현)을 design.md에 명시.

## 의존 관계

- T-D1~D3 → T-M2 선행 (디자인이 모바일 화면 구현의 입력).
- API 계약 `confirmed` → T-B2, T-M3 동시 착수 가능.
- T-B1 → T-B2 (스키마 없이 서비스 불가).
- T-D1(Lovable 수정)과 T-B1~T-B2(백엔드)는 병렬 가능. **사용자 지시: 디자인 + 백엔드 동시 진행, 디자인 완료 후 모바일 진입.**

## 리스크 / 오픈 이슈

- **챌린지/user_stats 스키마 초안**: 백엔드는 현재 완전 스켈레톤. 이번에 만드는 스키마가 향후 챌린지 도메인 전체의 기반이 된다 → 과한 스코프로 번지지 않도록 home-feed에 필요한 컬럼만 정의(이후 feature가 ALTER로 확장).
- **챌린지 result enum**: `CHALLENGER_WIN`/`OPPONENT_WIN`/`DRAW`/`BOTH_LOSE` 중 user_stats 집계 규칙 — `BOTH_LOSE`는 양쪽 패 처리(이번 계약에 명시).
- **myStatus / opponentStatus 값 도메인**: Lovable mock은 `pending` / `verified` / `failed` 3종 — 백엔드 verification 모델과 정합 필요.
- **데드라인이 "완료"인 카드의 의미**: Lovable mock에 "완료" 케이스 존재 — 챌린지가 COMPLETED 상태인데 결과 미확정 짧은 윈도우 케이스인지 별도 정의 필요. 1차에선 IN_PROGRESS만 응답 → 추후 확장.
