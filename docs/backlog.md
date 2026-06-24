# 백로그 — challenge 프로젝트

> 흩어진 TODO/미해결/후속 작업을 한 곳에서 추적하는 살아있는 문서. 분류는 우선순위 + 담당자.
>
> **자동 갱신**: pm-lead가 `report-and-document` 스킬로 feature를 마무리할 때마다 summary.md의 미해결 이슈를 본 백로그에 자동 추가. 임의 시점 재정리는 "백로그 정리해줘" 한 마디로 pm-lead에게 요청.

- **마지막 갱신**: 2026-06-24 (friends 1차 1단계 완료 — 친구 빈 상태 UI 도입, 백엔드 0건. 1차 2단계 항목 등재)
- **우선순위 기호**: 🔴 긴급(블로커) / 🟡 중요 / 🟢 일반 / 🔵 대기(외부 의존)
- **담당 약어**: pm / mobile / backend / design / user(사용자가 직접 처리)

---

## 🔴 긴급 (블로커)

_없음 — 다음 sprint 시작에 직접적 블로커는 없음._

## 🟡 중요

| 항목 | 출처 | 담당 | 메모 |
|---|---|---|---|
| 영혼의 맹세(STT + 서명) 화면 디자인 | 노션 [📋 Common States & PM Questions](https://app.notion.com/p/3523902cbe248111ac2dd40fcd8fda64) | design + user | 핵심 플로우인데 Lovable에 화면 부재. 디자이너 작업 필요. |
| 전화번호 등록 화면 UX (SMS 인증 제거 후) | 노션 동상 / [ADR-0008](./decisions/0008-friend-matching.md) | design + user | 친구 매칭 활성화 조건. 카카오 scope 동의/마이페이지 등록 등 등록 경로 미정. |
| 디자이너 시각 검증 6건 (gradient end / card stops / chart4 / glow brush / 135deg / SoulStampLogo 회전 제거 후 시각 균형) | [colors.md §5](./design-system/colors.md) | design + user | oklch→hex 자체 변환분 + 외곽 회전 링 제거 결정 후 시각 균형. 디자이너 부재로 추정값 그대로 채택 중. |

## 🟢 일반

| 항목 | 출처 | 담당 | 메모 |
|---|---|---|---|
| AuthKakao 통합 테스트 수동 실행 (Docker Desktop 후 `--tests "*AuthKakaoIntegrationTest"`) | [auth-kakao/backend-report.md](./features/auth-kakao/backend-report.md) | user + backend | 5 케이스 검증 (drift 정정 후 5xx 1회 재시도→703 시나리오 추가). CI 적용 시 docker-in-docker 필요. |
| 로컬 서버 기동 + 모바일 수동 smoke test (Android+iOS real Kakao SDK 흐름) | [auth-kakao/summary.md](./features/auth-kakao/summary.md) | user | NATIVE APP KEY 기입 완료. Android 에뮬레이터/실기기 + iOS Simulator/Device에서 카카오 로그인 → JWT 발급 E2E 확인 필요. 카카오톡 앱-간 인증과 웹 fallback 둘 다. |
| iOS SPM 카카오 SDK 버전 pin 적정성 확인 | [auth-kakao/change-log.md](./features/auth-kakao/change-log.md) | mobile | `iosApp/iosApp.xcodeproj/project.pbxproj`의 `XCRemoteSwiftPackageReference`에 `requirement`(`upToNextMajor` 등) 명시 여부 점검. |
| `:feature:login:check` detekt config 부재 (`/config/detekt/detekt.yml`) | [auth-kakao/change-log.md](./features/auth-kakao/change-log.md) | mobile | 컴파일/테스트는 통과하나 `check` 태스크 fail. 인프라 티켓. |
| iOS Keychain 실기기 smoke (write/read roundtrip) | [auth-kakao/mobile-report.md](./features/auth-kakao/mobile-report.md) | mobile | SecItemAdd/Copy 상태코드 확인. |
| Compose blur 미적용 (LoginScreen `blur-3xl` + bottom-navigation `backdrop-blur-xl` 동일 카테고리) | [auth-kakao/mobile-report.md](./features/auth-kakao/mobile-report.md) · [bottom-navigation/summary.md](./features/bottom-navigation/summary.md) | mobile + design | 현재 alpha만으로 근사. 시각 차이 크면 platform actual blur(`graphicsLayer { renderEffect = BlurEffect(...) }` Android API 31+ / iOS `UIVisualEffectView` interop) 도입 검토. KMP 공통 API 부재로 expect/actual 분기 필요. |
| Material Icons Extended 1.7.3 deprecation | [auth-kakao/mobile-report.md](./features/auth-kakao/mobile-report.md) · [bottom-navigation/summary.md](./features/bottom-navigation/summary.md) | mobile + pm | Kotlin 2.2.20 / CMP 1.10.3 호환 이슈로 1.7.3 핀. `:feature:login`(`LocalFireDepartment`/`AutoAwesome`)에 이어 `:feature:main` BottomBar(`Home`/`Group`/`EmojiEvents`/`Person`)도 동일 의존성 사용 시작 — 사용처 누적. Material Symbols(vector resources) 마이그레이션 ADR 후보. |
| Glow shadow / 외광 효과 미구현 | [auth-kakao/mobile-report.md](./features/auth-kakao/mobile-report.md) | mobile + design | tokens.md §3 `--shadow-glow` (0 0 30px primary 20%) Compose 기본 `shadow()` 표현 어려움. Canvas glow 별도 작업 후보. |
| 카카오 버튼 ripple 색 (`KakaoYellowPressed`) | [auth-kakao/design.md](./features/auth-kakao/design.md) | mobile + design | 현재 Surface 기본 ripple. 디자이너 확인 후 `BrandColors.KakaoYellowPressed` ripple 매핑 작업. |
| ~~`./scripts/generate-feature.sh` 패키지 경로 버그~~ | ~~[bottom-navigation/summary.md](./features/bottom-navigation/summary.md)~~ | ~~mobile~~ | ✅ 2026-06-15 — line 35 `com.lwg.base` → `com.lwg.challenge` 정정. 모바일 working tree 변경, 사용자 커밋 대기. |
| `:feature:login` Preview annotation deprecation 경고 다수 | [bottom-navigation/summary.md](./features/bottom-navigation/summary.md) | mobile | bottom-navigation 빌드 중 발견. `@Preview` 사용처 일괄 마이그레이션 (Material3 / KMP Preview annotation 변경). 정리 후보, 즉시 가능. |
| LoginScreen 10sp 라벨 `bold10`/`light10` 슬롯 정합 | [tokens.md §5.2](./design-system/tokens.md) · [auth-kakao/design.md](./features/auth-kakao/design.md) | mobile + design | 2026-05-12 design-bridge Lovable 전수 점검 결과. Lovable `login.tsx`: LabeledDivider "한 번 서명하면 무를 수 없음" `text-[10px] font-bold`(10sp) / 약관 풋터 `text-[10px]`(10sp, weight 미지정→Light). 현 모바일은 `bold12`/`light12`(12sp). (1) `:core:designsystem/ChallengeTypography.kt`에 `bold10`/`light10` 슬롯 추가(`medium10`과 동일 패턴, lineHeight 14). (2) LoginButtonSection의 LabeledDivider `textStyle = typography.bold10`, FooterAgreementText `style = typography.light10`로 교체. ranking/index/notifications/challenge-detail/challenge-new/ChallengeCard 등 다른 화면은 후속 feature 진입 시 자연 정합(현재는 모바일 placeholder). |
| 동시 로그인 시 `kakao_id` UNIQUE 충돌 재시도 로직 | auth-kakao/backend-report.md | backend | MVP 현실성 낮음. 향후 보강. |
| `AuthServiceRefreshTest` 단위 테스트 (정상 rotation / 옛 refresh 재사용 / hash NULL / JWT 만료 / tokenType 잘못 — 5 케이스) | [auth-refresh-rotation/summary.md](./features/auth-refresh-rotation/summary.md) | backend | 본 PR에서 미작성. JwtTokenProvider + UserRepository mock 기반 단위 테스트로 충분. |
| Ktor `Auth(bearer)` 플러그인 모바일 테스트 (200 분기 / 401 분기 / refresh JSON deserialization / 다중 요청 race 처리) | [auth-refresh-rotation/summary.md](./features/auth-refresh-rotation/summary.md) | mobile | Ktor MockEngine + 가짜 TokenProvider/AuthEventBus로 검증. |
| Refresh rotation E2E smoke (access 만료 시뮬 + V1 가입자 강제 재로그인) | [auth-refresh-rotation/summary.md](./features/auth-refresh-rotation/summary.md) | user + backend + mobile | `application.yml` `jwt.access.expire` 짧게 → Android/iOS 모바일에서 (1) 사용자 무자각 갱신 (2) refresh 만료 시 로그인 화면 자동 이동 (3) V1 hash NULL row 강제 재로그인 확인. |
| logout 엔드포인트 구현 (`/auth/logout`) — refresh hash NULL 화 + Spring Security 인증 | foundation Sprint 0 스텁 / [ADR-0009](./decisions/0009-refresh-token-rotation.md) | backend | hash 무효화 자리는 ADR-0009로 마련됨. 호출처(엔드포인트 본체)만 작성하면 됨. |
| Refresh rotation race 동시성 분석 | [auth-refresh-rotation/summary.md](./features/auth-refresh-rotation/summary.md) | backend + mobile | 동일 refresh 2 요청 동시 도착 시 한쪽 401 실패의 UX 영향. Ktor Auth 단일 클라이언트 직렬화로 단일 기기에선 발생 빈도 낮음 — 다중 기기 동시 갱신은 1기기 1세션 정책의 자연 귀결. 관측되면 별도 ADR. |
| ~~`challenge-app/CLAUDE.md` 모듈 구조 정정~~ | ~~[ADR-0003](./decisions/0003-mobile-template-init.md)~~ | ~~mobile~~ | ✅ 2026-06-15 — `:domain:*`/`:remote:*`/`:data:*`/`:local:*` 다중 모듈 구조 + `com.lwg.challenge` ComponentScan 예제로 정정. **ADR-0003 6/6 항목 처리 완료** → accepted 전환 가능. 모바일 working tree 변경, 사용자 커밋 대기. |
| RecordApi/ActiveChallengeApi 통합 테스트 6건 수동 실행 (Docker Desktop 후 `--tests "*RecordApiIntegrationTest" --tests "*ActiveChallengeApiIntegrationTest"`) | [home-feed/change-log.md](./features/home-feed/change-log.md) | user + backend | v2에서 `HomeIntegrationTest`가 `RecordApiIntegrationTest`(3) + `ActiveChallengeApiIntegrationTest`(3)로 분리됨. docker 미설치 자동 skip 패턴 유지. |
| 모바일 시각 검증 (HomeScreen 3 상태 + ChallengeCard + StatsBar muted 톤) | [home-feed/summary.md](./features/home-feed/summary.md) | user | Android 에뮬레이터 + iOS Simulator. default/FIRST_USER/NO_ACTIVE_CHALLENGE 3 상태, 7필드 카드, StatsBar 신규사용자 muted 톤, FAB pulse-fire 부재, safe-area inset 확인. 백엔드 통합 verify 후 권장. |
| 디자이너 결정 4건 (home-feed) — FIRST_USER FAB 노출 / NO_ACTIVE_CHALLENGE CTA 1버튼 vs 2버튼 / 빈 상태 일러스트 자산 / `Swords`↔`SportsKabaddi` 시각 차이 | [home-feed/design.md §7](./features/home-feed/design.md) | design + user | 본안 그대로 구현됨. 디자이너 결정 시 모바일 1줄 수정 또는 props 변형으로 대응. |
| FAB `pulse-fire` 애니메이션 미구현 (HomeScreen) | [home-feed/summary.md](./features/home-feed/summary.md) | mobile + design | Compose에서 LoginScreen pulse-fire 패턴 재사용 후보. |
| ChallengeCard 시간 표시 자동 갱신 부재 | [home-feed/summary.md](./features/home-feed/summary.md) | mobile | 현재 매 composition 재계산만. `LaunchedEffect + delay(60s)` 분 단위 재구성 후보. |
| Lovable "deadline 완료" 케이스 정의 (IN_PROGRESS인데 deadline 지남) | [home-feed/summary.md](./features/home-feed/summary.md) | pm + backend + design | 1차 API 응답에선 미포함, ChallengeCard는 `DISTANT_PAST` 폴백으로 "마감" 표시. 어떤 시점에 COMPLETED로 전환할지 챌린지 결과 판정 feature에서 결정. |
| `verifications` PENDING row 자동 생성 로직 (챌린지 IN_PROGRESS 진입 시) | [home-feed/backend-report.md](./features/home-feed/backend-report.md) | backend | 챌린지 생성/계약 확정 feature(`contract-signing` 등)에서 구현 필요. 현재는 row 없으면 PENDING으로 응답. |
| user_stats 자동 집계 트리거 (챌린지 결과 확정 시) | [home-feed/backend-report.md](./features/home-feed/backend-report.md) | backend | `challenge-result-judgment` 별도 feature 후보. 현재는 LEFT JOIN으로 row 부재 시 0 응답. |
| 챌린지 deadline UTC 일관성 명시 (생성 feature 진입 시) | [home-feed/backend-report.md](./features/home-feed/backend-report.md) | backend + pm | 현재 DB TIMESTAMP를 UTC 가정. 챌린지 생성 feature에서 저장 정책 명문화 필요. |
| friends 1차 2단계 — 친구 목록 백엔드 (`friendships` 테이블 V5 + `GET /api/v1/friends` + 통합 테스트) | [friends/summary.md](./features/friends/summary.md) | backend | spec.md "후속 계획" 참조. 양방향 단일 row(`user_a_id < user_b_id`) + users JOIN 1쿼리. |
| friends 1차 2단계 — 모바일 친구 목록 (`Friend` 도메인 + Repository/UseCase + `FriendCard` + LazyColumn 렌더링) | [friends/summary.md](./features/friends/summary.md) | mobile | Flow + onError + AuthEventBus 표준 패턴. `FriendsUiState.Data` 에 `friends: List<Friend>` 필드 + `isEmpty` derived. |
| friends 시각 검증 (Android 에뮬레이터 + iOS Simulator + Lovable 프리뷰 3방향) | [friends/summary.md](./features/friends/summary.md) | user + design | 빈 상태 일러스트(현재 `Icons.Filled.Group` 임시) / 헤드라인 톤 / CTA 시각. design.md §6 ⚠️ 확인 필요 6건 점검. |
| friends 빈 상태 일러스트 자산 (1차 2단계 진입 전) | [friends/design.md](./features/friends/design.md) | design | 현재 `Icons.Filled.Group` 임시. 디자이너 자산 추가 시 `FriendsEmptyState` 호출 인자만 교체. |
| friends 친구 추가 feature (`friends-add` 등) — 닉네임 검색 / 연락처 매칭(ADR-0008) / 친구 요청 흐름 | [friends/spec.md](./features/friends/spec.md) | design + mobile + backend | 1차 2단계 진입 후. 카카오 scope 승인은 외부 의존(🔵). 빈 상태 CTA 라우팅 본 feature에서 연결. |
| Redis 용도 결정 (캐싱? 세션? blacklist?) | repos.json backend.blockers | backend + pm | dependency만 있고 사용처 미정. |
| 라이트 테마 ADR (보류 결정 공식화) | colors.md / 노션 | pm | dark-first 통일됐으나 명문화 안 됨. ADR-0010(예정). |
| 디자이너 질의 16건 통합 회신 | 노션 [📋 Common States & PM Questions](https://app.notion.com/p/3523902cbe248111ac2dd40fcd8fda64) | design + user | 16건 묶어 디자이너에게 전달. |

## 🔵 대기 (외부 의존, 사용자 액션)

| 항목 | 사유 | 후속 영향 |
|---|---|---|
| Kakao `account_phone_number` scope 승인 | Kakao 개발자 콘솔 신청·승인 | 승인 전에는 `phone_verified=false` 케이스만 검증 가능 |
| Apple Developer Account ($99/년) 구입 | iOS 빌드/배포 | iOS TestFlight 배포 시작 시점 |
| Firebase 프로젝트(dev + prod) 생성 | FCM 푸시 | `push-fcm` feature 시작 시 |
| Lovable 디자인 추가 화면 export (영혼의 맹세, 전화번호 등록 등) | 디자이너 작업 | 해당 화면 구현 시 차단 |

## ADR pending / in-progress

| ADR | 상태 | 비고 |
|---|---|---|
| [ADR-0003 모바일 템플릿 초기화](./decisions/0003-mobile-template-init.md) | in-progress (5/6 완료, `:feature:home` 교체 ✅ home-feed 2026-05-25) | 잔여 1건: `challenge-app/CLAUDE.md` 모듈 구조 정정 (위 🟢 항목 참조). 정리 후 accepted 전환. |
| [ADR-0009 Refresh Token Rotation](./decisions/0009-refresh-token-rotation.md) | **accepted (2026-05-28)** | DB sha256 hash 기반 rotation 채택. ADR-0002 401 의미 세분화 하위 결정 포함. [auth-refresh-rotation](./features/auth-refresh-rotation/summary.md)로 구현 완료. |
| ADR-0010 라이트 테마 (보류 결정) | 미작성 | 위 🟢 "라이트 테마 ADR" 트리거 |

## 분류별 보기 (담당자 기준)

### 사용자 액션 (user)
- Kakao scope 승인 / Apple Developer / Firebase / Docker Desktop 실행
- 디자이너에게 영혼의 맹세 / 전화번호 등록 화면 + 16건 질의 전달
- Refresh rotation E2E smoke (access 짧게 → 무자각 갱신 / refresh 만료 → 로그인 자동 이동 / V1 가입자 강제 재로그인 — auth-refresh-rotation 후속)

### 모바일 (mobile)
- iOS Keychain 실기기 smoke
- iOS SPM 카카오 SDK 버전 pin 적정성 확인
- detekt config 부재 정리 (home-feed에서도 동일 영향 확인)
- Compose blur 미적용 (LoginScreen + BottomBar 동일 카테고리, `BlurEffect` 도입 검토)
- Material Icons Extended deprecation → Material Symbols 마이그레이션 ADR 후보 (`:feature:home` 가세로 사용처 누적)
- Glow shadow / 외광 효과 (Canvas glow)
- 카카오 버튼 ripple 색 매핑
- `:feature:login` `@Preview` deprecation 경고 정리 (즉시 가능)
- LoginScreen 10sp 라벨 `bold10`/`light10` 슬롯 정합 (tokens.md §5.2 후속, 즉시 가능)
- FAB `pulse-fire` 애니메이션 미구현 (HomeScreen)
- ChallengeCard 시간 표시 자동 갱신(분 단위)
- Ktor `Auth(bearer)` 단위 테스트 (auth-refresh-rotation 후속)

### 백엔드 (backend)
- 동시성 보호
- `AuthServiceRefreshTest` 단위 테스트 5 케이스 (auth-refresh-rotation 후속)
- logout 엔드포인트 구현 (refresh hash NULL화 + Spring Security 인증)
- Redis 용도 결정
- HomeIntegrationTest 3건 수동 verify (Docker)
- `verifications` PENDING row 자동 생성 (챌린지 IN_PROGRESS 진입 시) — 후속 feature
- user_stats 자동 집계 트리거 (결과 확정 시) — 후속 feature
- 챌린지 deadline UTC 저장 정책 명문화 (생성 feature 진입 시)

### 디자인 (design)
- 영혼의 맹세 화면
- 전화번호 등록 화면
- 시각 검증 5건 회신 (+ home-feed 시각 검증 1건)
- 16건 통합 회신
- home-feed 결정 4건 회신 (FAB / CTA 수 / 일러스트 / Swords 아이콘)

### PM (pm)
- ADR-0009 / ADR-0010 작성 결정
- 디자이너 질의 통합 전달

---

## ✅ 최근 완료 (최근 10건만 유지, 초과 시 archive로)

- **2026-06-24 — feature `friends` 1차 1단계 완료** (`partially-completed`. 친구 탭의 `PlaceholderScreen` → 디자이너 산출물 기반 빈 상태 화면 교체. 백엔드 0건, 모바일·디자인 트랙만 진행. **디자인**: Lovable `oathbound-challenges/src/routes/friends.tsx`에 `isEmpty` 분기 + `FriendsTopBar` / `FriendsEmptyState` sub-component 분리 + 디자인 토큰만 사용. **PM 산출물**: `docs/features/friends/{spec, plan, design, summary}.md` 4종 작성. **모바일**: `:core:designsystem`에 `FriendsEmptyState`(127줄), `:feature:friends`에 `component/FriendsTopBar` + `FriendsScreen` 교체 + `FriendsRoute` 갱신(`LocalMainAction.showSnackBar` + CTA stub `showMessage("준비 중입니다")`) + `FriendsViewModel` 정리(`Data(placeholder: Unit)` → `data object Data`, `showMessage` private→internal) + `commonTest/FriendsViewModelTest` 2건. **단일 출처 결정**: plan.md 헤드라인 `bold18` 오기를 design.md `bold16`로 정정 — design.md §3.1/§5/§6 강한 어조로 명시. **스코프**: 친구 목록 / 친구 추가 흐름 / 카드 탭 라우팅 / 백엔드 모델·API 모두 1차 2단계로 이연. 모바일 빌드 전 모듈 BUILD SUCCESSFUL, `:feature:friends:testDebugUnitTest` 2/2 + `:feature:home:testDebugUnitTest` 7/7 + `:feature:login:testDebugUnitTest` 4/4, 회귀 0. PM hub 커밋·푸시 완료. 모바일·Lovable working tree는 사용자 커밋 대기(메모리 `feedback_mobile_dispatch_no_git`).)
- **2026-06-15 — feature `home-feed` v2** (`completed (v2)`. 단일 `/api/v1/home` 폐기 → `/api/v1/record` + `/api/v1/challenges/active` 분리. 전적 1쿼리 / 챌린지+users+verifications 3쿼리 단일 read 트랜잭션 그대로. 서버 도메인 `UserStats` → `UserRecord` 리네임(DB 테이블명 `user_stats` 유지, `@Table(name=...)` 매핑). DTO/Service/Controller 분리, 통합 테스트도 `RecordApiIntegrationTest`(3) + `ActiveChallengeApiIntegrationTest`(3)로 분할. 모바일은 **Repository 표준 패턴 정렬** — `sealed HomeResult` 폐기 → `fun get(...)(onError): Flow<T>` + `AuthEventBus.emitSessionExpired()` 401 전역 처리. `HomeViewModel`은 `GetHomeDataUseCase`로 두 Flow 결합, UiState는 `Loading | Data` 두 분기로 단순화. `HomeUiEffect.NavigateToLogin` 제거(MainScreen이 AuthEventBus collect). 서버 커밋 `a80caa6`. HomeViewModelTest 7/7 passed(Android JVM). `feedback_mobile_repository_pattern.md` 메모리 추가 — 다음 모바일 Repository 작업 시 표준 패턴 참조.)
- **2026-05-28 — feature `auth-refresh-rotation` 완료** (`completed`. `foundation`의 단순 refresh(access만 재발급) → DB sha256 hash 기반 **Rotation**으로 교체. 서버: `users` V3 마이그레이션 (`refresh_token_hash VARCHAR(64)` + `refresh_token_issued_at`), `RefreshTokenHasher`(core/hash), `AuthService.refresh()` 신규 — JWT 서명+exp+tokenType+DB hash 4중 검증, 통과 시 새 access+refresh 발급 + hash 회전, 실패는 모두 동일 401 응답으로 통일. login()도 발급 후 hash 저장. `UserRepository`에 `findById` + `updateRefreshTokenHash` 추가 (JPA `@Modifying` 핀포인트 UPDATE, `updated_at` 의도적 미갱신). `RefreshData` DTO에 `refreshToken` 필드 추가. 모바일: Ktor `Auth(bearer)` 플러그인 도입으로 **401 처리 단일 지점화** (`loadTokens`/`refreshTokens`/`sendWithoutRequest(auth 제외)`). `AuthEventBus`(core/utils) `SharedFlow<Unit> sessionExpired` 신규 — `MainScreen`이 collect → 로그인 탭 강제 이동. `TokenProvider` port-adapter 분리 (`:remote:network` 인터페이스 + `:data:repositoryImpl` 구현). 제거: `RefreshAccessTokenUseCase` / `LoginRepository.refreshAccessToken` + Impl + Fake / `RefreshResponseMapper` / `LoginApi.refresh` / `LoginRepositoryImpl.CODE_UNAUTHORIZED` / `SplashViewModel`의 refresh-on-launch. **ADR-0009 accepted** (B안: DB sha256 hash + rotation. Redis 의존 회피). **ADR-0002의 401 의미 세분화** 하위 결정으로 명문화 — 일반 API 401(자동 갱신) vs `/auth/refresh` 401(강제 로그아웃). 신규 단위 테스트 0건 (권장 케이스는 backlog 등재). 서버 11 files +188/-16, 모바일 16 files +143/-116. 커밋 `dfecba5`/`68d6533`. auth-kakao 미해결 "Refresh Token Rotation" 해소.)
- **2026-05-25 — feature `home-feed` 완료** (`completed`. 홈 화면 challenge 도메인 본 UI 구축 — Sticky TopBar + StatsBar(승/패/무/연승) + 진행 중 챌린지 카드 리스트 + 빈 상태 2분기(FIRST_USER/NO_ACTIVE_CHALLENGE) + FAB. 단일 `GET /api/v1/home` 응답으로 전적+챌린지 동시 조회. 백엔드 V2 마이그레이션(`verifications` ALTER) + `UnauthorizedEntryPoint` 신설. `:core:designsystem`에 `ChallengeCard`/`StatsBar`/`HomeEmptyState` 3종 + `:core:utils`에 `Instant.toRelativeKoreanString` 헬퍼. **ADR-0003 잔여 5/6 해소** (`:feature:home` placeholder 교체). 빌드 모듈 13건 BUILD SUCCESSFUL, HomeViewModelTest 6/6 (Android JVM + iOS SimulatorArm64), 백엔드 단위 14/14, 통합 0/8(Docker 미설치 자동 skip), LoginViewModelTest 4/4 회귀 0. API 계약 변경 0건(draft→confirmed). Lovable `index.tsx` 동기 갱신.)
- **2026-05-11 — feature `bottom-navigation` 완료** (`completed`. CmpSystem 잔재 4탭 → challenge 4탭(홈/친구/랭킹/MY) 재구성. `:feature:friends/ranking/mypage` 신규 모듈 3종 + `PlaceholderScreen` 재사용 컴포넌트. `ChallengeBottomBar` Material `NavigationBar` 폐기 → `Surface + Row` 커스텀(alpha 95% / 10.sp / safe-area). `:feature:ex1/ex2/ex3` 모듈 통째 삭제 (ADR-0003 잔여 해소). 빌드 7건 BUILD SUCCESSFUL, LoginViewModelTest 4/4 회귀 0.)
- **2026-05-11 — auth-kakao LoginScreen 디자인 2차 반영 완료** (pm-lead 결정 9건 → Lovable 동기 갱신 → 모바일 LoginScreen 풀세트 반영. Hero/CTA + slide-up/fadeIn + 글로우·블롭 배경. `:core:designsystem`에 StatusPillBadge/LabeledDivider/Divider/Spacer 추출. `:feature:login/component`에 SoulStampLogo/BackgroundDecor/ChallengeSection/ChallengeTitle/FooterAgreementText/LoginButtonSection 분할. 빌드 4건 BUILD SUCCESSFUL, LoginViewModelTest 4/4 passed. 커밋 `fb68069`+`d7529cc` main 푸시 완료. INDEX `partially-completed`→`completed`.)
- 2026-05-07 — **iOS Kakao SDK 실연동 완료** (SPM `kakao-ios-sdk` 통합, `KakaoLoginHelper.swift` Swift→Kotlin bridge, `iOSApp.swift` `KakaoSDK.initSDK` + `onOpenURL` URL handler, Info.plist `kakao$(KAKAO_NATIVE_APP_KEY)` xcconfig 변수 주입, `KakaoAuthClient.ios.kt` placeholder→실 구현. Android+iOS 모두 SDK 통합 완료)
- 2026-05-07 — 백엔드 카카오 로그인 SDK 방식 정렬 (drift 정정: `/oauth/token` 교환 코드 + `KAKAO_REST_API_KEY` 등 4개 env 제거. `:infra/:api/:app` BUILD SUCCESSFUL, AuthControllerTest 5/5)
- 2026-05-07 — 모바일 Android Kakao SDK 실연동 (`com.kakao.sdk:v2-user:2.20.6`, `loginWithKakaoTalk` → fallback `loginWithKakaoAccount`, LoginViewModelTest 4/4)
- 2026-05-07 — `:core:designsystem` ColorScheme 단일화 (`ChallengeExtendedColors` 폐지 → `ChallengeColorScheme` 단일, `ChallengeTheme.colorScheme.<name>` 단일 진입점) + colors.md/tokens.md/노션 동기
- 2026-05-07 — Typography Lovable 정합 (Tailwind 스케일 12/24/30 슬롯 신설, lineHeight 4건 정렬, GmarketSans 3종 자산 매핑 정책 명시)
- 2026-04-30 — 디자인 노션 하위 페이지 5건 정리 (Color/Typography/Component/Screens/Common States)
> 한도(10건) 초과로 2026-04-23 ADR-0001~0008 / 2026-04-24 foundation / 2026-04-24 auth-kakao(당시 partial) / 2026-04-30 `colors.md`+tokens.md 1차 동기 / 2026-04-30 designsystem Lovable 다크 1차 통합 항목은 [backlog-archive/2026-04.md](./backlog-archive/2026-04.md)로 이동.

---

## 갱신 규칙

1. **자동 추가**: pm-lead가 `report-and-document` 스킬로 feature 종료 시, 해당 summary.md의 "미해결 이슈"를 본 백로그의 적절한 우선순위 표에 추가. 출처 컬럼에 summary.md 링크.
2. **자동 이동**: 동일 스킬에서 백로그에 있던 항목이 이번 feature로 해결됐다면 "최근 완료" 섹션으로 이동.
3. **수동 정리**: 사용자가 "백로그 정리해줘" / "백로그 갱신" 요청 시 pm-lead가 모든 출처(features/*/summary.md, design ⚠️, ADR pending, repos.json blockers, 노션 PM Questions)를 다시 스캔하여 백로그를 재구성.
4. **항목 수명**: "최근 완료"는 10건까지만 본 파일에 두고, 초과 시 `docs/backlog-archive/{YYYY-MM}.md`로 이동(아카이브 파일이 처음 생성될 때만 디렉토리 생성).
5. **출처 무손실**: 백로그 항목은 항상 원본 출처 링크를 갖는다. 출처가 사라지면 백로그 항목도 검토하여 폐기/이동.
6. **우선순위 변경**: 기능 진행에 따라 🟡↔🟢 이동 자유. 외부 차단되면 🔵, 다음 sprint 시작을 차단하면 🔴.
