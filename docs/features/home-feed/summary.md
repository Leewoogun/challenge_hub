# 홈 피드 (home-feed) — Summary

- **feature-id**: home-feed
- **완료일**: 2026-05-25
- **상태**: completed

## 구현 개요

홈 화면을 challenge 도메인 본 UI로 신규 구축. 단일 엔드포인트 `GET /api/v1/home`으로 진행 중 챌린지 + 누적 전적을 한 번에 받아 표시하며, 신규 사용자(전적·챌린지 모두 0)와 기존 사용자(챌린지만 0)를 별도 빈 상태로 분기. 이번 작업으로 ADR-0003의 마지막 잔여 항목(`:feature:home` Movie 예제)도 해소.

핵심 결정 3건:
1. **빈 상태 분기는 ViewModel 책임** — `HomeUiState.Success(stats, challenges, emptyType: FIRST_USER | NO_ACTIVE_CHALLENGE | NONE)` 패턴으로 화면 코드의 if/else 분기 최소화.
2. **시각 타입은 stdlib `kotlin.time.Instant`** — Kotlin 2.2.20부터 `kotlinx.datetime.Instant`가 stdlib의 typealias라 외부 의존성 추가 불필요.
3. **클라이언트 빈 상태 판정** — 백엔드는 user_stats row 없으면 0으로 채워 응답하고, "신규" vs "기존이지만 0개" 분류는 모바일이 `stats.win + lose + draw + currentStreak == 0` 식으로 판단.

## 엔드포인트

| Method | Path | 상태 |
|--------|------|------|
| GET | /api/v1/record | implemented (v2) |
| GET | /api/v1/challenges/active | implemented (v2) |
| ~~GET /api/v1/home~~ | ~~v1, 폐기 (2026-06-15)~~ | superseded |

> `implemented`: 코드 빌드 SUCCESS, 통합 테스트는 Docker 미설치 환경 자동 skip. Docker Desktop 환경에서 수동 verify 필요(기존 auth-kakao와 동일 패턴).
>
> v2 변경 사유와 영향은 [change-log.md](./change-log.md) 참조. 모바일 Repository는 `Flow<T> + onError + AuthEventBus` 표준 패턴으로 정렬.

## 화면 / UI 변경

- **HomeScreen (default)** — Sticky TopBar(맹세 로고 + Bell+badge) + StatsBar(승/패/무/연승 4셀) + 진행 중 챌린지 카드 리스트(deadline asc) + FAB(챌린지 생성) + BottomBar.
- **HomeScreen (FIRST_USER)** — Stats 4셀 모두 muted 톤 + 챌린지 영역에 `HomeEmptyState(FIRST_USER)` 카드(친구 등록 + 챌린지 만들기 CTA 2버튼). 신규 사용자 온보딩 톤.
- **HomeScreen (NO_ACTIVE_CHALLENGE)** — Stats 누적값 그대로 + 챌린지 영역만 `HomeEmptyState(NO_ACTIVE_CHALLENGE)`.
- **Lovable `index.tsx` 갱신** — `isEmptyChallenges` / `isFirstUser` 분기 + `StatCell` 헬퍼 + `HomeEmptyState` sub-component 신설. 모바일 동기.
- **신규 designsystem 컴포넌트 3종** — `ChallengeCard`(7 표시 필드 + onClick), `StatsBar`(4 Int props, 톤 분기 컴포넌트 내부 책임), `HomeEmptyState`(type enum + 2 onClick).
- **stub navigation 3종** — `ChallengeDetailRoute(challengeId)`, `ChallengeCreateRoute`, `NotificationsRoute` 신설(모두 `PlaceholderScreen` 진입).

## 주요 변경 파일

**모바일** (20 신규 / 9 수정):
- `:feature:home` — `HomeScreen.kt`, `HomeRoute.kt`, `HomeViewModel.kt`, `component/HomeTopBar.kt` (모두 placeholder 교체), `contract/HomeUiState.kt`, `contract/HomeUiEffect.kt`, `commonTest/FakeHomeRepository.kt`, `commonTest/HomeViewModelTest.kt`
- `:core:designsystem` — `components/challenge/ChallengeCard.kt`, `StatsBar.kt`, `HomeEmptyState.kt`, `ChallengeVerificationStatus.kt`, `HomeEmptyStateType.kt`
- `:core:utils` — `datetime/InstantFormat.kt`(`Instant.toRelativeKoreanString(now)` 헬퍼)
- `:core:navigation` — `Route.kt` (3개 stub Route + 직렬화 등록)
- `:domain:model/repository/usecase` — `VerificationStatus`, `UserStats`, `ActiveChallenge`, `HomeFeed`, `HomeRepository`(+ `HomeResult` sealed), `GetHomeFeedUseCase`
- `:remote:model/api/mapper` — `home/HomeResponse.kt` 외 DTO, `HomeApi`(Ktorfit), `HomeResponseMapper`
- `:data:repositoryImpl` — `HomeRepositoryImpl`(401 → Unauthorized 매핑), `di/UseCaseModule.kt`(`provideGetHomeFeedUseCase`)
- `:feature:main` — `MainScreen.kt`(3 stub NavEntry)

**백엔드** (22 신규 / 4 수정):
- `app/src/main/resources/db/migration/V2__home_feed_verification_status.sql` — `verifications` ALTER (status/created_at 추가, photo_url/verified_at nullable화). `user_stats`/`challenges`/`verifications`/`users` 테이블 자체는 V1에 이미 존재.
- `controller/home/HomeController.kt`, `dto/HomeResponse.kt`
- `service/home/HomeService.kt`, `HomeFeedResult.kt` — `wins/losses/draws` ↔ API `win/lose/draw` 매핑 단일 지점.
- `domain/model/challenge/Challenge.kt`, `userstats/UserStats.kt`, `verification/Verification.kt`
- `domain/repository/{challenge,userstats,verification}/...Repository.kt` (인터페이스), `domain/user/UserRepository.kt`(`findById`/`findAllByIds` 추가)
- `infra/entity/{challenge,userstats,verification}/...Entity.kt`, `infra/jpa/...JpaRepository.kt`, `infra/repositoryimpl/...RepositoryImpl.kt`
- `config/UnauthorizedEntryPoint.kt` — 401 응답을 위해 신규 추가(기존 403 디폴트는 모바일 ApiResultCall과 부정합).
- `config/SecurityConfig.kt` — UnauthorizedEntryPoint 주입.
- `app/src/test/.../home/HomeIntegrationTest.kt` — 신규 사용자/챌린지 2건/401 만료 3 케이스.

**디자인**:
- `src/routes/index.tsx` — `isEmptyChallenges` + `isFirstUser` 분기 + `StatCell` 헬퍼 + `HomeEmptyState` sub-component.

## 테스트 결과

- **모바일**: HomeViewModelTest **6/6 passed** (Android JVM + iOS SimulatorArm64 양쪽), LoginViewModelTest 4/4 회귀 0. 전 모듈 BUILD SUCCESSFUL (`:domain`/`:remote`/`:data`/`:core`/`:feature`/`:composeApp`). detekt 태스크는 프로젝트 공통 `config/detekt/detekt.yml` 부재로 모든 모듈 실패(본 feature 도입 이슈 아님, backlog).
- **백엔드**: `:app:build` BUILD SUCCESSFUL, 단위 14/14 passed (PhoneHasherTest 3 + GlobalExceptionHandlerTest 5 + AuthControllerTest 5 + ChallengeServerApplicationTests 1), 통합 0/8 (HomeIntegrationTest 3 + AuthKakaoIntegrationTest 5 모두 **Docker 미설치 자동 skip**).
- **시각 검증**: 사용자 / QA 영역(Android 에뮬레이터 + iOS Simulator). 백엔드 통합 verify 후 권장.

## 결정 사항

- **API 계약 변경 0건** — draft 그대로 confirmed 전환. 모바일/백엔드 모두 contract 그대로 빌드 성공.
- **VerificationStatus enum 케이스**: 대문자 3종(`PENDING`/`VERIFIED`/`FAILED`). Lovable mock의 소문자와 case가 달라 모바일이 정합 처리.
- **빈 배열 정책**: `activeChallenges`는 null 금지, 빈 배열로 응답. 모바일 DTO 기본값 `emptyList()`로 방어.
- **401 처리**: 토큰 만료만의 단일 케이스로 가정. `HomeResult.Unauthorized` → `HomeUiEffect.NavigateToLogin` → 로그인 화면 라우팅.
- **챌린지 상태 필터**: `IN_PROGRESS`만 응답에 포함(1차). `CONTRACT_SIGNING` 등 다른 상태는 후속 feature에서 별도 협의.
- **deadline 파싱 폴백**: 모바일 DTO는 `String`으로 받아 매퍼에서 `Instant.parse(value)` → 실패 시 `Instant.DISTANT_PAST`. 1개 카드 파싱 실패가 전체 응답을 0건으로 만들지 않도록 방어적 처리.
- **시각 타입**: 모바일/백엔드 모두 `kotlin.time.Instant` (Kotlin 2.2.20 stdlib). kotlinx-datetime 외부 의존성 추가 회피.
- **`materialIconsExtended` 의존성**: `:feature:home` + `:core:designsystem` 양쪽에 추가(bottom-navigation 패턴 연장). 1.7.3 핀 deprecation 경고는 기존 backlog의 Material Symbols 마이그레이션 ADR 후보로 통합.
- **ADR-0003 (모바일 템플릿 초기화) 잔여 해소**: `:feature:home` placeholder 교체 완료 → ADR 6/6 항목 모두 처리(CLAUDE.md 모듈 구조 정정만 backlog로 남음).

## 미해결 이슈

- [ ] `RecordApiIntegrationTest` 3건 + `ActiveChallengeApiIntegrationTest` 3건 + `AuthKakaoIntegrationTest` 5건 수동 verify (Docker Desktop 환경 필요). v2에서 `HomeIntegrationTest`가 두 통합 테스트로 분리됨.
- [ ] 모바일 시각 검증: Android 에뮬레이터 + iOS Simulator 직접 확인 (HomeScreen 3 상태 + ChallengeCard 7필드 + StatsBar 색 톤 / 신규 사용자 muted 톤 / FAB pulse-fire 부재 / safe-area inset).
- [ ] design.md §7 ⚠️ 디자이너 결정 4건: (1) FIRST_USER FAB 노출 여부, (2) NO_ACTIVE_CHALLENGE CTA 2버튼 vs 1버튼, (3) 빈 상태 일러스트 자산(현재 Flame 임시), (4) `Swords` lucide ↔ `SportsKabaddi` Material Icon 시각 차이 검토.
- [ ] FAB `pulse-fire` 애니메이션 미구현 — Compose에서 LoginScreen pulse-fire 패턴 재사용 후보.
- [ ] ChallengeCard 시간 표시 자동 갱신 부재 — `LaunchedEffect + delay(60s)` 분 단위 재구성 후보(현재는 매 composition 재계산만).
- [ ] user_stats 자동 집계 트리거 없음 — challenge-result-judgment 후속 feature.
- [ ] IN_PROGRESS 진입 시 `verifications` PENDING row 자동 생성 로직 없음 — 챌린지 생성/계약 확정 feature에서 구현.
- [ ] 챌린지 생성 feature 작성 시 deadline을 UTC 기준으로 저장하도록 일관성 명시 필요(현재 DB TIMESTAMP를 UTC 가정).
- [ ] Lovable의 "deadline 완료" 케이스(IN_PROGRESS인데 deadline 지남) 정의 필요. 1차 응답에선 미포함이지만 UI 컴포넌트는 `DISTANT_PAST` 폴백으로 "마감" 표시.
- [ ] `:feature:home` `:detekt` 태스크 fail (프로젝트 공통 `config/detekt/detekt.yml` 부재, 기존 backlog 항목).

## 참조

- [spec.md](./spec.md)
- [api-contract.md](./api-contract.md)
- [design.md](./design.md)
- [mobile-report.md](./mobile-report.md)
- [backend-report.md](./backend-report.md)
