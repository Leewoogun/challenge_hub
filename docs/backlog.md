# 백로그 — challenge 프로젝트

> 흩어진 TODO/미해결/후속 작업을 한 곳에서 추적하는 살아있는 문서. 분류는 우선순위 + 담당자.
>
> **자동 갱신**: pm-lead가 `report-and-document` 스킬로 feature를 마무리할 때마다 summary.md의 미해결 이슈를 본 백로그에 자동 추가. 임의 시점 재정리는 "백로그 정리해줘" 한 마디로 pm-lead에게 요청.

- **마지막 갱신**: 2026-08-03 (`soul-oath` partially-completed — 양측 서명 없이는 챌린지가 시작되지 않는다. 백엔드 171/171 + 실서버 56/56, 모바일 230/230, Android 실기 통과. 🔴 **실기에서 버그 3건** — 전부 테스트가 초록인 채였다. 미해결: iOS 실기 / 주관 3건 / 통합 45 skip / 3개 레포 커밋 0건)
- **우선순위 기호**: 🔴 긴급(블로커) / 🟡 중요 / 🟢 일반 / 🔵 대기(외부 의존)
- **담당 약어**: pm / mobile / backend / design / user(사용자가 직접 처리)

---

## 🔴 긴급 (블로커)

_없음 — 다음 sprint 시작에 직접적 블로커는 없음._

## 🟡 중요

| 항목 | 출처 | 담당 | 메모 |
|---|---|---|---|
| 🔴 **`soul-oath` iOS 실기 미검증** (서명 캔버스 `pointerInput`) | [soul-oath/summary.md](./features/soul-oath/summary.md) | user + mobile | **기기 없음.** Compose `pointerInput` 드로잉은 KMP **선례 0건**이고 **지연·좌표 정확도는 손가락이 아니면 안 나온다.** ⚠️ **시뮬레이터로 대체하지 않았다** — 마우스 드래그는 손가락과 다르다. Android 실기에서는 통과(획 픽셀 97→13,701 / 인셋 박스 밖 0px / 종횡비 2.0000). |
| **`soul-oath` 주관 판단 3건** (지연 체감 / 획이 각져 보이는가 / 캔버스 170dp 충분한가) | [soul-oath/summary.md](./features/soul-oath/summary.md) | user + design | 앱에서 **서명 한 번 그어보면** 된다. 각져 보이면 솎아내기 임계(정규화 거리 0.003)를 낮춘다. design.md §7 실기 항목이 여기 녹아 있다. |
| **자정 경계에 위저드 힌트와 계약서 날짜가 갈릴 수 있다** | [soul-oath/summary.md](./features/soul-oath/summary.md) | backend + mobile | 클라 시계로 계산한 힌트(`7/28 24:00`)와 서버가 **요청 도착 시점**에 정하는 `challengeDate`가 초 단위 창에서 어긋나고, `soul-oath`가 그 결과를 **계약서에 영구 기록**한다. 🔴 **"클라 시계를 맞추면 된다"가 아니다** — 시계가 완벽해도 서명→도착 사이에 직렬화·네트워크가 들어간다. 진짜 고치려면 클라가 의도한 날짜를 보내고 서버가 존중해야 하는데 그건 `deadlineType` enum의 취지(**기기 시계 조작·타임존 불일치 차단**)와 맞바꾸는 것 — **버그 수정이 아니라 트레이드오프 재검토**다. 현재 판단은 안 고치는 쪽. |
| 🔴 **컨테이너 런타임 부재 → 백엔드 통합 테스트 45건 누적 미실행** (기존 24건 + challenge-create 21건) | [challenge-create/backend-report.md](./features/challenge-create/backend-report.md) · [auth-kakao](./features/auth-kakao/backend-report.md) · [home-feed](./features/home-feed/change-log.md) | user + backend | **2026-07-28 pm-lead 실측: docker/podman/colima/orbstack/nerdctl 전부 미설치, Docker.app·OrbStack.app 번들도 없음.** 지금까지 이 프로젝트는 통합 테스트를 **단 한 번도 실행한 적이 없다** — 매 feature마다 자동 skip되어 리스크가 누적 중. challenge-create는 V5 마이그레이션 + 부분 유니크 인덱스 + native 쿼리가 DB를 타야만 검증되는 구조라 특히 아프다. backend-dev가 로컬 Postgres 16.13에 일회용 DB로 SQL 레벨 대체 검증(마이그레이션 4건 / 인덱스 8케이스 / native 쿼리)은 마쳤으나 **JPA 매핑·Flyway 자동 적용·Security 필터·직렬화가 맞물리는 층은 미검증.** → 런타임 하나(Docker Desktop / OrbStack / Colima 아무거나) 설치 후 `./gradlew :app:test` 일괄 실행 필요. **배포 전 필수 관문.** |
| 🔵 **`dev-test-login` 격리(꺼진 상태) 실서버 검증 — 배포 전 관문** | [dev-test-login/summary.md](./features/dev-test-login/summary.md) | user + backend | **개발 중에는 켜둔 채로 두는 것이 정상이다** (2026-08-03 사용자 결정 — 개발 끝날 때까지 유지). 이 검증이 막으려는 위험("테스트 로그인이 운영에 새어나감")은 **배포 시점에만 현실화**되므로 그때 확인한다. 현재 단위 6케이스(실제 Spring 컨텍스트에 태워 빈 미생성 확인)는 통과 상태. **배포 전 절차**: VM options에서 `-Dchallenge.dev.test-login.enabled=true`를 빼고 기동 → backend-dev가 `e2e-off.sh`(9단언) 실행 → 확인 후 운영 배포. ⚠️ `/actuator/health` 404가 **test-login 경로의 404를 자동 보장하지 않는다** — 같은 핸들러여도 permitAll 상시 적용이 함께 걸려야 성립한다. |
| **챌린지 수락 경로 DB 증거 부재** | [dev-test-login/summary.md](./features/dev-test-login/summary.md) | user | 2026-08-03 사용자 손 검증 완료 확인. 단 직후 `challenges=0`이라 **수락 경로(`IN_PROGRESS` 전환 + `verifications` 2건 생성)의 DB 레벨 증거가 없다.** 취소가 물리 삭제이므로 "신청→취소"만 돌았다면 정상. 증거가 필요하면 신청→수락으로 한 번 더. |
| 영혼의 맹세(STT + 서명) 화면 디자인 | 노션 [📋 Common States & PM Questions](https://app.notion.com/p/3523902cbe248111ac2dd40fcd8fda64) | design + user | 핵심 플로우인데 Lovable에 화면 부재. 디자이너 작업 필요. |
| 전화번호 등록 화면 UX (SMS 인증 제거 후) | 노션 동상 / [ADR-0008](./decisions/0008-friend-matching.md) | design + user | 친구 매칭 활성화 조건. 카카오 scope 동의/마이페이지 등록 등 등록 경로 미정. |
| 디자이너 시각 검증 6건 (gradient end / card stops / chart4 / glow brush / 135deg / SoulStampLogo 회전 제거 후 시각 균형) | [colors.md §5](./design-system/colors.md) | design + user | oklch→hex 자체 변환분 + 외곽 회전 링 제거 결정 후 시각 균형. 디자이너 부재로 추정값 그대로 채택 중. |

## 🟢 일반

| 항목 | 출처 | 담당 | 메모 |
|---|---|---|---|
| **보낸 도전장 목록 조회 + 취소 UI** (`GET /api/v1/challenges/sent` + 홈 "보낸 도전장" 섹션 + 취소 버튼) | [challenge-create/spec.md 스코프 결정 6](./features/challenge-create/spec.md) | backend + mobile + design | **challenge-create에서 옵션 C로 강등 (2026-07-28 사용자 결정).** 서버 `DELETE /api/v1/challenges/{id}`는 이미 구현·테스트 완료 상태라 목록 조회만 붙이면 살아난다. 현재는 생성 직후(create 응답의 `challengeId` 보유 시)에만 도달 가능하고 앱 재시작 후 취소 불가. 서버 비용은 `/received` 대칭 쿼리라 거의 0, 실제 비용은 design 섹션 1건 + 모바일 T-M5 대비 약 +25%(홈 `combine` 소스 +1). ⚠️ `/pending` + `direction` 필드 통합안(B)은 **채택 금지** — 방향별 표시 필드가 달라 한 DTO에 합치면 모바일 기본값 방어 패턴 탓에 오독이 컴파일·런타임 모두 조용히 통과한다. |
| **friends iOS 카톡 공유 실제 연동** (iosApp SPM에 `KakaoSDKShare` 추가 + Swift에서 `KakaoInviteBridge.inviteHandler` 주입) | [friends/mobile-report.md](./features/friends/mobile-report.md) | mobile + user | 현재 iOS는 placeholder(handler null→failure). `KakaoLoginHelper.swift` 패턴 답습. Xcode 작업 필요. |
| **friends iOS 유닛테스트** (`:feature:friends:iosSimulatorArm64Test`) + iOS framework link | [friends/mobile-report.md](./features/friends/mobile-report.md) | mobile | T7b 검증은 Android 유닛 + iOS 컴파일까지. iOS 유닛 별도 실행. |
| **원격 이미지 로더 도입** (Coil3 KMP / Kamel / CMP Resources) | [friends/mobile-report.md](./features/friends/mobile-report.md) | mobile + design | 친구 목록/검색 결과/내 프로필 화면 등에서 필요. 현재는 닉네임 이니셜 placeholder만. 🟡 후보. |
| **`IconTextButton iconSize` 파라미터화** (design.md 14dp vs 공용 컴포넌트 16dp) | [friends/mobile-report.md](./features/friends/mobile-report.md) | mobile | 2dp 차이 정정 원할 때. `:core:designsystem/IconTextButton.kt`에 `iconSize: Dp = 16.dp` 파라미터 추가. |
| **friends 초대 manual smoke** (Android 카톡 공유 시트 정상 열림 + Default TextTemplate 렌더 확인) | [friends/summary.md](./features/friends/summary.md) | user | 모바일 commit/push 후 디바이스에서 확인. |
| **friends 모바일 working tree commit/push** (T6+T7a+T7b 누적, 신규 ~19 + 수정 ~12) | [friends/mobile-report.md](./features/friends/mobile-report.md) | user | mobile-dev git 금지 룰로 working tree만 변경됨. 한 commit / 분리 사용자 결정. |
| user-info iOS 단위 테스트 + framework link 검증 (`:feature:home:iosSimulatorArm64Test` + `xcodebuild`) | [user-info/summary.md](./features/user-info/summary.md) | mobile + user | T4 dispatch가 Android testDebugUnitTest만 수행. iOS 측 검증 별도 필요. |
| 내 프로필 화면 (UserInfo 활용 — 닉네임 / 프사 노출 + 친구 초대 시 사용) | [user-info/summary.md](./features/user-info/summary.md) | design + mobile | 본 작업에선 캐시만 채우고 UI 노출 없음 (HomeScreen.kt 미수정). 디자인 + Lovable 작업 후 mobile 통합. |
| user-info 명시적 갱신 UX (pull-to-refresh / 카카오 프로필 변경 감지) | [user-info/summary.md](./features/user-info/summary.md) | mobile | 1차에 `NETWORK_ONLY` 호출 지점 없음. 사용자 트리거 추가 시 호출. |
| user-info manual smoke (신규 가입 / 자동 로그인 / 로그아웃 캐시 클리어 디바이스 검증) | [user-info/summary.md](./features/user-info/summary.md) | user | 모바일 commit/push 후 디바이스에서 확인. |
| user-info 모바일 commit/push 결정 (신규 12 + 수정 10 + 삭제 1) | [user-info/mobile-report.md](./features/user-info/mobile-report.md) | user | mobile-dev git 금지 룰로 working tree만 변경됨. 한 commit / 분리 사용자 결정. |
| `SilentAuthExpired` 공통 위치 이동 (`:domain:model/auth/`) — `faae2cd`로 삭제된 sentinel 재도입 검토 | [user-info/summary.md](./features/user-info/summary.md) | mobile | 본 작업에선 사용 안 함 (옵션 1 표준 따름). 필요해지면 별도 spec. |
| ~~`TokenLocalDataSource` interface 분리~~ / `AppSettingsLocalDataSource` interface 분리 (테스트 추가 시) | [user-info/mobile-report.md](./features/user-info/mobile-report.md) · [dev-test-login](./features/dev-test-login/spec.md) | mobile | `TokenLocalDataSource`는 ✅ **2026-07-31 `dev-test-login`에서 해소** — "테스트 추가 시" 조건 충족(final concrete + 생성자에서 `createDataStore` 즉시 실행이라 `LoginRepositoryImpl` 테스트가 **한 건도 불가능**했다). `UserInfoLocalDataSource` 패턴 답습, 사용처 2곳 타입명 유지로 무변경. **`AppSettingsLocalDataSource`는 미해소** — 동일 조건 충족 시 검토. |
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
| ~~`/actuator/health`가 HTTP 500~~ ✅ **2026-08-03 해소** (`dev-test-login` T-B1b의 `NoResourceFoundException` → 404 핸들러. 실서버 404 확인) | [challenge-create/backend-report.md](./features/challenge-create/backend-report.md) | backend | 2026-07-31 #7 통합 검증 중 발견. `SecurityConfig`가 permitAll로 열어 뒀으나 **actuator 의존성이 없어 핸들러가 없다.** 현재 사용처 없어 영향 0. 헬스체크·로드밸런서 프로브로 쓰려면 `spring-boot-starter-actuator` 추가 필요. ADR-0007 AWS 배포 시 실제 필요해진다. |
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
| **`challengeKotlinMultiplatformPure` 모듈의 `api()` 의존성이 Android 타깃으로 전이되지 않음** | [datetime-model-migration/mobile-report.md](./features/datetime-model-migration/mobile-report.md) | mobile | `:domain:model`이 `api(kotlinx-datetime)`을 선언해도 android 타깃이 없는 모듈이라 변형 매칭에서 api 간선이 유실된다. 현재는 feature 3곳에 `implementation` **명시 선언**으로 우회(레포의 `materialIconsExtended` 선례와 동일 대응). 근본 해결은 build-logic 컨벤션 플러그인 수정. |
| **위저드 시스템 백 버튼 배선 미완** (~~`:core:ui` 승격~~ → **승격은 완료**, 위저드 연결만 남음) | [challenge-create/summary.md](./features/challenge-create/summary.md) · [soul-oath](./features/soul-oath/spec.md) | mobile | ⚠️ **2026-08-03 사유 정정** — 원래 문구였던 *"`PlatformBackHandler`가 `:feature:main`에 갇혀 못 쓴다"*는 **더 이상 사실이 아니다.** `soul-oath`에서 `:core:ui`로 승격됐고(맹세 화면이 두 번째 소비자) `OathRoute.kt:33`이 실제로 쓴다. **남은 건 위저드 배선뿐.** 의도적으로 미착수 — 위저드는 시스템 백이 **3단계 상태기계**(OATH → MISSION_INPUT → FRIEND_PICK → pop)를 거슬러야 하고, 맹세 step엔 서명이 있어 **dirty 이탈 확인까지 얽힌다.** 대충 붙이면 TopBar 백과 시스템 백이 다르게 동작한다. `ChallengeCreateRoute.kt:41` 주석도 정정돼 있다. |
| **challenge-create 실기기 시각 검증** (위저드 2-step / 받은 도전장 섹션 / **수락 다이얼로그 iOS IME**) | [challenge-create/summary.md](./features/challenge-create/summary.md) | user + mobile | 다이얼로그를 택한 이유가 바텀시트의 iOS IME 리스크였던 만큼 다이얼로그 쪽도 실기 확인이 필요하다. ⚠️ 실기기 첫 네트워크 호출 시 **로컬 네트워크 권한 팝업 "허용"** 필수 — 거부하면 Apple 버그 r.131764908로 기기 재시작 전까지 캐시된 거부가 유지된다. |
| challenge-create iOS 유닛 테스트 미실행 (`:feature:home` / `:feature:challenge:create` `iosSimulatorArm64Test`) | [challenge-create/summary.md](./features/challenge-create/summary.md) | mobile | Android 유닛 + iOS 링크까지가 검증 게이트였다. friends·user-info와 동일 패턴의 누적 항목. |
| `SearchProfilePlaceholder` 4번째 사본 흡수 (`:feature:friends:search`) | [challenge-create/mobile-report.md](./features/challenge-create/mobile-report.md) | mobile | challenge-create에서 `ProfilePlaceholder`에 `size` 파라미터를 넣어 시각 변화 없이 흡수 가능. 완료된 feature 영역이라 손대지 않음. |
| `EXPIRED` 전이 주체 없음 (`:batch` 스케줄러) | [challenge-create/summary.md](./features/challenge-create/summary.md) | backend | lazy expiry로 처리 중 — 목록 제외 + 수락 거부. DB `status`는 `PENDING`인 채 남는다. |
| ~~`verifications` PENDING row 자동 생성 로직 (챌린지 IN_PROGRESS 진입 시)~~ | ~~[home-feed/backend-report.md](./features/home-feed/backend-report.md)~~ | ~~backend~~ | ✅ **2026-07-31 challenge-create로 해소** — 수락 시 양측 2건을 단일 트랜잭션으로 생성. |
| user_stats 자동 집계 트리거 (챌린지 결과 확정 시) | [home-feed/backend-report.md](./features/home-feed/backend-report.md) | backend | `challenge-result-judgment` 별도 feature 후보. 현재는 LEFT JOIN으로 row 부재 시 0 응답. |
| 챌린지 deadline UTC 일관성 명시 (생성 feature 진입 시) | [home-feed/backend-report.md](./features/home-feed/backend-report.md) | backend + pm | 현재 DB TIMESTAMP를 UTC 가정. 챌린지 생성 feature에서 저장 정책 명문화 필요. |
| friends 1차 2단계 — 친구 목록 백엔드 (`friendships` 테이블 V5 + `GET /api/v1/friends` + 통합 테스트) | [friends/summary.md](./features/friends/summary.md) | backend | spec.md "후속 계획" 참조. 양방향 단일 row(`user_a_id < user_b_id`) + users JOIN 1쿼리. |
| friends 1차 2단계 — 모바일 친구 목록 (`Friend` 도메인 + Repository/UseCase + `FriendCard` + LazyColumn 렌더링) | [friends/summary.md](./features/friends/summary.md) | mobile | Flow + onError + AuthEventBus 표준 패턴. `FriendsUiState.Data` 에 `friends: List<Friend>` 필드 + `isEmpty` derived. |
| friends 시각 검증 (Android 에뮬레이터 + iOS Simulator + Lovable 프리뷰 3방향) | [friends/summary.md](./features/friends/summary.md) | user + design | 빈 상태 일러스트(현재 `Icons.Filled.Group` 임시) / 헤드라인 톤 / CTA 시각. design.md §6 ⚠️ 확인 필요 6건 점검. |
| friends 빈 상태 일러스트 자산 (1차 2단계 진입 전) | [friends/design.md](./features/friends/design.md) | design | 현재 `Icons.Filled.Group` 임시. 디자이너 자산 추가 시 `FriendsEmptyState` 호출 인자만 교체. |
| friends 친구 추가 feature (`friends-add` 등) — 닉네임 검색 / 연락처 매칭(ADR-0008) / 친구 요청 흐름 | [friends/spec.md](./features/friends/spec.md) | design + mobile + backend | 1차 2단계 진입 후. 카카오 scope 승인은 외부 의존(🔵). 빈 상태 CTA 라우팅 본 feature에서 연결. |
| Redis 용도 결정 (캐싱? 세션? blacklist?) | repos.json backend.blockers | backend + pm | dependency만 있고 사용처 미정. |
| 라이트 테마 ADR (보류 결정 공식화) | colors.md / 노션 | pm | dark-first 통일됐으나 명문화 안 됨. **ADR-0011**(예정 — 0010은 날짜·시간 모델이 선점). |
| **challenge-create 디자이너 검토 12건** (수락 UI 바텀시트 채택 사후 검토 / 시트 상단 radius 24.dp vs Lovable drawer 기본 10px / 마감 캡션 신규 문구 "선택한 자정까지가 챌린지 기간이야" 외) | [challenge-create/design.md §9](./features/challenge-create/design.md) | design + user | design-bridge가 Lovable에 대응 화면이 없어 기존 토큰만으로 신규 설계한 부분. 신규 토큰 0건. 디자이너 검토는 사후. |
| **Lovable 화면별 문구 톤 불일치** (챌린지 화면 반말 "걸래?"/"받아친다" vs 친구 화면 존댓말) | [challenge-create/design.md §9](./features/challenge-create/design.md) | design + user + pm | **원본 Lovable이 이미 화면별로 갈려 있어** design-bridge가 각 화면 원본 톤을 따랐다. challenge-create 범위 밖 전역 이슈 — 전체 톤 통일 여부는 별도 결정 필요. |
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
| [ADR-0010 날짜·시간 모델 `LocalDateTime` 통일](./decisions/0010-datetime-model-localdatetime.md) | **accepted (2026-07-31) — 구현 대기** | 사용자 결정. 선결 7건 ADR에 정리. 별도 feature로 분리 예정. |
| ADR-0011 라이트 테마 (보류 결정) | 미작성 | 위 🟢 "라이트 테마 ADR" 트리거. **번호가 0010 → 0011로 변경됨**(0010을 날짜·시간 모델이 선점). |

## 분류별 보기 (담당자 기준)

### 사용자 액션 (user)
- 🔴 **컨테이너 런타임 설치** (Docker Desktop / OrbStack / Colima 아무거나) → 통합 테스트 45건 일괄 해소
- **4개 레포 커밋 결정** (PM 허브 / 백엔드 / 모바일 / Lovable — challenge-create 누적, 에이전트 git 금지 룰)
- **challenge-create 실기기 시각 검증** (위저드 / 받은 도전장 / 수락 다이얼로그 iOS IME + 로컬 네트워크 권한 "허용")
- Kakao scope 승인 / Apple Developer / Firebase
- 디자이너에게 영혼의 맹세 / 전화번호 등록 화면 + 16건 질의 전달
- Refresh rotation E2E smoke (access 짧게 → 무자각 갱신 / refresh 만료 → 로그인 자동 이동 / V1 가입자 강제 재로그인 — auth-refresh-rotation 후속)

### 모바일 (mobile)
- 위저드 시스템 백 버튼 (`PlatformBackHandler` → `:core:ui` 승격)
- challenge-create iOS 유닛 테스트 (`:feature:home` / `:feature:challenge:create`)
- `SearchProfilePlaceholder` 4번째 사본 흡수
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
- 🟡 잘못된 요청 본문 → HTTP 500 (`HttpMessageNotReadableException` 핸들러) — `datetime-model-migration` T-B3에 포함 확정
- `/actuator/health` 500 (actuator 의존성 부재)
- `EXPIRED` 전이 스케줄러 (`:batch`)
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

- **2026-08-03 — feature `soul-oath` (`partially-completed`)** (제품 컨셉의 **핵심 차별점** 구현 — *"영혼의 맹세(계약서)까지 작성해야 시작되는 진짜 약속"*. `challenge-create`가 의도적으로 건너뛰고 "나중에 삽입한다"고 적어둔 그 약속을 이행했다. **이제 양측이 서명해야만 챌린지가 시작된다.** 서명은 **벡터 스트로크를 DB에 저장** — 파일 스토리지 ADR을 이 feature 하나 때문에 세우지 않았다(카메라 인증 때 결정). **백엔드**: V7(`_signature_url` → `_signature_data` + 주석 6건), `Contract` 도메인, 신규 `GET /challenges/{id}`, 계약서 본문 **박제 + `is_finalized` 재렌더**. **171/171** + **실서버 56/56**(취소 FK / 바이트 왕복 3자 동일 / 완결 재렌더). **모바일**: `:feature:challenge:oath`·`:detail` 2모듈 신설, `:core:ui`에 `ContractCard`/`SignatureCanvas`/`SignatureView`, `AcceptChallengeDialog` 삭제 → 전체 화면. **230/230, 회귀 0 / 의도적 교체 5 / 신규 86.** **디자인**: design.md v7.1, Lovable `/oath` 프리뷰 동작, **신규 토큰 0건**. **주요 결정**: `CONTRACT_SIGNING` 미도입 + 수락·서명 **원자 요청**(도입하면 "수락 후 서명 전 이탈"이 어느 목록에도 안 잡혀 재개 불가 — `/sent` 부재와 동형. 부수 효과로 **교체 테스트 0건**) / 취소 시 contract **명시적 선삭제**(CASCADE 기각 — 컨셉상 조용한 연쇄 삭제 불가) / 상대 맹세 화면 **전체 화면**(근거는 면적이 아니라 **제스처 소유권** — 캔버스를 `verticalScroll`에 두면 획 긋기와 스크롤이 다툰다) / 종횡비 2:1을 **컴포넌트 내부에서 강제**(불변식은 파라미터로 열지 않는다). 🔴 **실기에서 버그 3건** — 서명 캔버스가 **획당 점 1개**(223건 초록인데 기능 무동작) / 맹세 화면 **100% 미개방**(PENDING의 `null` mission) / **전역** `UnknownApiError`가 `onError` 미호출로 **역직렬화 실패가 조용한 무한 로딩**(호출부 24곳). 🔴 **"테스트는 통과하는데 실제로는 틀린" 계열이 이 feature에서만 6번** — spec에 절로 정리. **검증이 판정에서 측정으로**: 종횡비 픽셀 실측 2.0000 / 입력↔렌더 잉크 bbox 차이 ≤ 0.0038 / 인셋은 대조군 계산 후 실측 / 최악값 20,150자를 **세 독립 구현**이 일치. **미해결**: 🔴 iOS 실기 미검증(시뮬레이터로 대체 안 함) / 주관 3건 / 자정 경계 / 위저드 백 배선 / 통합 45 skip / **3개 레포 커밋 0건**.)
- **2026-08-03 — feature `dev-test-login` (`partially-completed`)** (가짜 계정 3개 + debug 전용 로그인 버튼으로 **혼자 친구·챌린지 플로우를 검증할 수 있게** 했다 — `friends`·`challenge-create`의 "manual smoke" 미해결이 계속 쌓이던 병목. **인증 우회 경로라 격리를 기능과 동등한 수용 기준으로** 다뤘다. **백엔드**(`3b73627`): 커스텀 `Condition`(프로파일 미도입 — *프로파일은 의미가 누적돼 로깅·CORS 때문에 `dev`를 켜면 인증 우회까지 딸려 켜진다*), `AuthService.issueTokens` 추출로 카카오와 발급 경로 공유, permitAll **상시**+빈만 조건부(*fail-closed를 지키는 건 permitAll이 아니라 빈 조건부*), `NoResourceFoundException`→404 핸들러. **134/134** + **켠 상태 실서버 34/34**. 🔴 **`getProperty(Boolean::class)`가 오타에 서버를 죽인다는 발견** — `"enabled"`/`""`에 `ConversionFailedException`을 던진다. *fail-closed는 "안 열린다"여야지 "터진다"가 아니다* → 문자열 `"true"` 정확 비교. **모바일**(`d36b42e`): `TestLoginSection`(`isDebug` 게이트), `LoginWithTestAccountUseCase`가 `LogoutUseCase`를 내부 호출, **T-M4 `HomeTopBar` debug 계정 표시**(실측 결과 *앱에 "내가 누구인지" 보이는 화면이 0건*이었다 — 계정을 오가는 feature에서 치명적), `TokenLocalDataSource` interface 분리(backlog 조건 충족). **148/148, 회귀 0 / 삭제 0.** **실사용**: 테스트 계정으로 **친구 요청→수락 성공**(09:38:54→09:39:01), ADR-0010 KST 저장 신규 데이터로 재확인. **pm-lead 오류 3건을 팀이 잡았다** — "꺼진 상태=404" 수용 기준이 실제로는 401 / 계약 초안의 `nickname` 필드 부재 / "홈에 닉네임 보인다" 전제. **미해결**: 🔴 **격리 OFF 실서버 검증 미완**(핵심 수용 기준) / 챌린지 수락 경로 DB 증거 부재.)
- **2026-07-31 — feature `datetime-model-migration` 완료** (`completed`. ADR-0010 구현. 시간 표현을 **`Instant`+ISO-8601 UTC → `LocalDateTime`+KST+`yyyy-MM-dd HH:mm:ss`** 로 통일. 신규 엔드포인트 0건, 기존 `confirmed` 계약 3건의 표기만 개정한 횡단 변경. **🔴 착수 후 문제 정의가 뒤집혔다** — 초안은 "서버가 UTC 저장이니 KST로 바꾼다"였으나 실측 결과 **서버는 이미 KST였고**(`users` 1행에 `+9h` 쳤으면 **데이터 손상**), 진짜 문제는 **시계가 두 갈래로 갈라져 있던 것**(`ChallengeCommandService`만 `Clock.systemUTC()`=UTC, 나머지는 `LocalDateTime.now()`=KST → 같은 DB에 9시간 다른 두 기준). "DB TIMESTAMP를 UTC로 간주"라는 문서 규약을 레포 코드가 한 번도 안 지켰고, challenge-create가 그 규약을 충실히 따르며 **UTC 섬**을 만든 것이 드러났다. **백엔드**: `KstTime`(엔티티 기본값용) + `Clock.system(Asia/Seoul)` 병행, `WIRE_DATETIME` 상수 단일 출처 + `@JsonFormat` 명시(정본) + `JacksonDateTimeConfig`(안전망), V6(**DML 0건 + `COMMENT ON COLUMN` 17건** — offset을 잃는 리스크를 DB 메타데이터로 대응), `NoResourceFoundException`→404 핸들러. **123/123 passed**(이전 111) + **`TZ=UTC` 전 코드베이스 재실행 123/123**(안전망 없이 정본만으로 선다는 직접 증거) + **실서버 65/65 PASS**(`DB deadline == 응답 deadline` 직접 대조로 시각 이동 없음 증명, challenge-create 58건도 새 포맷에서 전부 통과). **모바일**: `kotlinx-datetime` 도입 — challenge-create에서 깨진 원인이 API 비호환이 아니라 **버전 스큐**(선언 0.6.2 / common 해석 0.7.1)였음이 규명돼 0.7.1 선언으로 해결. 손으로 짠 `floorDiv`+Hinnant `civil_from_days` 제거(테스트 9건 무수정 통과가 등가성 보장), `DISTANT_PAST` 센티넬 폐기 → 필드 중요도 분기(`deadline`=제외+`onError` / 나머지=nullable), **`:remote:mapper`에 `commonTest` 소스셋 신설**(mapper 레이어 전체가 미검증이었음). **123/123 passed** — 기존 87 회귀 0 / 의도적 삭제 1 / 신규 36(`WireFormatBaselineTest` 4건이 baseline 대조를 **사람 검수에서 자동 테스트로** 전환). Android·KMP·iOS 링크 SUCCESS. **CLAUDE.md 시간 규칙 개정 + confirmed 계약 3건에 대체 고지.** 미해결: 통합 45건 skip 유지 / 모바일↔서버 실연동(dev-test-login 후 손 검증) / iOS 유닛 / `api()` 전이 / **3개 레포 커밋 0건**.)
- **2026-07-31 — feature `challenge-create` 완료** (`completed`. 제품 핵심 행위 "친구에게 챌린지를 건다" 개통 — 생성 → `PENDING` → 수락/거절. 수락 즉시 `IN_PROGRESS`로 전이시켜(`CONTRACT_SIGNING` 건너뜀) 이번 feature 단독으로 "생성→수락→홈 노출" 확인 가능. **백엔드**: endpoint 5건 + V5(`opponent_mission` NULL 완화 + **부분 유니크 인덱스** `uq_challenges_active_pair_date` — READ COMMITTED에서 앱 레벨 검사만으로는 중복 금지 수용 기준을 만족 못 한다는 근거로 범위 확대 승인) + `KstDeadlineCalculator` + `ClockConfig`. **111/111 passed** + **실서버 end-to-end 58/58 PASS**(실 JWT HTTP 호출로 JPA 매핑·Flyway·Security 필터·직렬화 검증, DB 시드 전량 원복). **모바일**: `:feature:challenge:create` 2-step 위저드(스텁 6파일 → 실물 + 컴포넌트 12), `:feature:home` "받은 도전장" 섹션 + `AcceptChallengeDialog`, `:domain`/`:remote`/`:data` challenge 계층 신설. **88/88 passed**(`HomeViewModelTest` 21/21 = 기존 10 + 신규 11, 기존 10건 이름·단언 무변경) + Android·KMP·iOS 링크 + `xcodebuild` SUCCESS. **디자인**: design.md v3, Lovable 2파일, **신규 토큰 0건**. **주요 결정**: 보낸 도전장 목록 제외(옵션 C, 사용자) / 모바일이 에러 `code`를 소비 못 하므로 "실패 시 코드 무관 스낵바 + 항상 재조회" + 전 에러 문구 확정 / 수락 UI 바텀시트→다이얼로그 2회 번복(근거 1건은 계약 확정으로 무효화됐으나 결론 유지) / 컴포넌트는 feature 모듈 배치(`72d9d9c` 존중) / iOS는 ATS가 아니라 **LNP**가 관문(`NSLocalNetworkUsageDescription`만 추가, `NSAllowsLocalNetworking`은 no-op이라 미추가). **팀이 잡은 pm-lead 오류 3건**: spec T-M3가 사용자 커밋을 되돌림 / T-M4가 이미 완료된 작업 / (후속 feature에서) `users` 1행 `+9h` 보정이 데이터 손상. **미해결**: 통합 45건 미실행(런타임 부재) / 잘못된 요청 본문 500 / 시스템 백 미구현 / 실기기 검증 / **4개 레포 커밋 0건**.)
- **2026-07-02 — feature `friends` 2차 친구 추가 완료** (`completed`. 친구 시스템의 실제 동작 구현 — 검색·요청·수락·거절·취소·목록·받은요청 7 endpoint + 모바일 도메인/Data/ViewModel/UI + 카카오톡 초대. **백엔드**: `V1 friendships` 그대로 활용(마이그레이션 0건), `FriendController` + `FriendService` + 통합 4건 + 슬라이스 15/15 PASS + `saveAndFlush` race recovery + `escapeForLike` 단위테스트 6/6. 커밋 `bae8ab6` → `1d9d88d` push. **모바일 T3-T5**: 사용자가 `81eccf0`로 직접 커밋 (`FriendsViewModel` / `FriendsSearchViewModel` / ItemState / FakeFriendsRepository). **모바일 T6-T7b** (Agent Teams + 옵션 C): `:core:designsystem/friend/{FriendListItem, FriendRequestCard}` (@Preview 4건, 이니셜 placeholder) + `:feature:friends`에 화면·라우팅·컴포넌트 wire-up (`FriendsScreen` 확장 / `FriendsSearchScreen` 신규 / `FriendsActionRow, ReceivedRequestsSection, FriendsListSection` 3분할 / `FriendsSearchTopBar, FriendSearchItem` + 5-relation Preview) + `:core:invite` 모듈 신규 (interface KakaoInviter + Android/iOS expect-actual + KakaoInviteBridge iOS handler injection) + KakaoLink 초대 (SDK Default `TextTemplate`, 콘솔 templateId 발급 skip — spec §4.5 정정 2026-07-02, App Distribution 소규모 운용 결정 반영). **HEAD 드리프트 대응**: 사용자 커밋 `8a5e725`에서 `UserInfoRepository.observeUserInfoCache()` 제거 확인 → T7b `inviteFriend`는 `getUserInfo(CACHE_FIRST).firstOrNull()` + null 가드로 처리 (옵션 B). **테스트**: Android testDebugUnitTest 32/32 PASS (FriendsViewModelTest 10 [T7a 7 + invite 3] + FriendsSearchViewModelTest 12 + HomeViewModelTest 10, 회귀 0). Android/common 166 tasks BUILD SUCCESSFUL + iOS 컴파일 SUCCESS. iOS 유닛테스트 미실행(backlog). **Agent Teams 학습**: `Agent tool name parameter`로 spawn 검증 + 옵션 C(child claude 위임)로 컨벤션 강제 발화 + Bash 10분 캡 학습 후 `mobile-dev.md` 재갱신 "child = Edit only / 본체 = background 빌드" 새 표준 도입. PM hub 커밋 다수, 모바일 working tree 사용자 commit 대기.)
- **2026-06-29 — feature `user-info` 완료** (`completed`. 인증된 사용자의 본인 정보(id, kakaoId, nickname, profileImageUrl) 조회 endpoint 신규 + 모바일 DataStore 캐시 + LoginResult 평탄화. **백엔드**: `GET /api/v1/users/me` Bearer (`UserController` + `UserService.getMe` + `UserInfoResponse`/`UserInfoData` DTO). 기존 `UserRepository.findById`(auth-refresh-rotation) + `JwtAuthenticationFilter` 활용. V1 스키마 그대로(마이그레이션 0건). SecurityConfig 변경 불필요. 슬라이스 2/2 PASS + 통합 4건 작성(Docker 미가용 skip). 커밋 `ef784b1` push. **모바일**: 9 모듈 확장 — `:domain:model/user/{UserInfo, CacheStrategy}`, `:domain:repository/UserInfoRepository`, `:remote:{model,api,mapper}/user/...`, `:local:datastore/{model/UserInfoPrefs, datasource/UserInfoLocalDataSource interface + Impl}`, `:data:repositoryImpl/UserInfoRepositoryImpl`, `:feature:home`에 `HomeViewModel` 통합(`UserInfoRepository` 주입 + init 2-launch(getUserInfo CACHE_FIRST 트리거 + observeUserInfoCache 관찰) + `combine(getHomeData, _userInfo)`). `HomeUiState.Data.userInfo: UserInfo? = null` 필드 추가(default null로 Preview 보존). HomeScreen.kt 미수정(UI 노출은 후속). 캐시 클리어: `TokenProviderImpl` + `LoginRepositoryImpl`의 `clearTokens()` 두 진입점에 통합. **부수 정리**: `UserProfile.kt`(`userId, isNewUser`) 삭제 + `LoginResult` 평탄화 + `LoginViewModel.kt:53` 정정 + 테스트 갱신. `LoginResult.tokens: AuthTokens`는 유지(영향 범위 축소). **옵션 1 적용** (T3 분석 단계 정정): spec/plan 작성 시 `feedback_mobile_repository_pattern.md`가 옛 패턴(Throwable + SilentAuthExpired + AuthEventBus 내부 처리)으로 stale 상태였음. mobile-dev가 `faae2cd "refactor: repository 구현 방식 템플릿에 맞게 변경"`(사용자 본인 commit) 식별 + 메모리 자체 갱신 + pm-lead 에스컬레이션 후 사용자 승인 받아 진행 — `onError: (String)` 시그니처 / `UserInfoError.kt` 만들지 않음 / `SilentAuthExpired` 미사용 / `AuthEventBus` repository 미주입(401은 Ktor Auth(bearer) 플러그인 전담, ADR-0009). **테스트**: 백엔드 슬라이스 2/2 + 모바일 19/19(`UserInfoRepositoryImplTest` 5 + `LoginViewModelTest` 4 회귀 + `HomeViewModelTest` 10[기존 7 + 신규 3]) 회귀 0. 9 모듈 `compileCommonMainKotlinMetadata` + `compileDebugKotlinAndroid` SUCCESS. iOS 단위 테스트 / framework link는 본 범위 외(후속 등재). **Agent Teams 첫 정식 사용** — backend-dev / mobile-dev 두 팀원 spawn(Agent tool `name` parameter 발견), SendMessage 협업, mobile-dev는 옵션 C(`cd challenge-app && claude -p`) 위임으로 컨벤션 강제 발화. PM hub 커밋 6건. 모바일 working tree 변경(신규 12 + 수정 10 + 삭제 1), 사용자 commit 대기.)
- **2026-06-24 — feature `friends` 1차 1단계 완료** (`partially-completed`. 친구 탭의 `PlaceholderScreen` → 디자이너 산출물 기반 빈 상태 화면 교체. 백엔드 0건, 모바일·디자인 트랙만 진행. **디자인**: Lovable `oathbound-challenges/src/routes/friends.tsx`에 `isEmpty` 분기 + `FriendsTopBar` / `FriendsEmptyState` sub-component 분리 + 디자인 토큰만 사용. **PM 산출물**: `docs/features/friends/{spec, plan, design, summary}.md` 4종 작성. **모바일**: `:core:designsystem`에 `FriendsEmptyState`(127줄), `:feature:friends`에 `component/FriendsTopBar` + `FriendsScreen` 교체 + `FriendsRoute` 갱신(`LocalMainAction.showSnackBar` + CTA stub `showMessage("준비 중입니다")`) + `FriendsViewModel` 정리(`Data(placeholder: Unit)` → `data object Data`, `showMessage` private→internal) + `commonTest/FriendsViewModelTest` 2건. **단일 출처 결정**: plan.md 헤드라인 `bold18` 오기를 design.md `bold16`로 정정 — design.md §3.1/§5/§6 강한 어조로 명시. **스코프**: 친구 목록 / 친구 추가 흐름 / 카드 탭 라우팅 / 백엔드 모델·API 모두 1차 2단계로 이연. 모바일 빌드 전 모듈 BUILD SUCCESSFUL, `:feature:friends:testDebugUnitTest` 2/2 + `:feature:home:testDebugUnitTest` 7/7 + `:feature:login:testDebugUnitTest` 4/4, 회귀 0. PM hub 커밋·푸시 완료. 모바일·Lovable working tree는 사용자 커밋 대기(메모리 `feedback_mobile_dispatch_no_git`).)
- **2026-06-15 — feature `home-feed` v2** (`completed (v2)`. 단일 `/api/v1/home` 폐기 → `/api/v1/record` + `/api/v1/challenges/active` 분리. 전적 1쿼리 / 챌린지+users+verifications 3쿼리 단일 read 트랜잭션 그대로. 서버 도메인 `UserStats` → `UserRecord` 리네임(DB 테이블명 `user_stats` 유지, `@Table(name=...)` 매핑). DTO/Service/Controller 분리, 통합 테스트도 `RecordApiIntegrationTest`(3) + `ActiveChallengeApiIntegrationTest`(3)로 분할. 모바일은 **Repository 표준 패턴 정렬** — `sealed HomeResult` 폐기 → `fun get(...)(onError): Flow<T>` + `AuthEventBus.emitSessionExpired()` 401 전역 처리. `HomeViewModel`은 `GetHomeDataUseCase`로 두 Flow 결합, UiState는 `Loading | Data` 두 분기로 단순화. `HomeUiEffect.NavigateToLogin` 제거(MainScreen이 AuthEventBus collect). 서버 커밋 `a80caa6`. HomeViewModelTest 7/7 passed(Android JVM). `feedback_mobile_repository_pattern.md` 메모리 추가 — 다음 모바일 Repository 작업 시 표준 패턴 참조.)
- **2026-05-28 — feature `auth-refresh-rotation` 완료** (`completed`. `foundation`의 단순 refresh(access만 재발급) → DB sha256 hash 기반 **Rotation**으로 교체. 서버: `users` V3 마이그레이션 (`refresh_token_hash VARCHAR(64)` + `refresh_token_issued_at`), `RefreshTokenHasher`(core/hash), `AuthService.refresh()` 신규 — JWT 서명+exp+tokenType+DB hash 4중 검증, 통과 시 새 access+refresh 발급 + hash 회전, 실패는 모두 동일 401 응답으로 통일. login()도 발급 후 hash 저장. `UserRepository`에 `findById` + `updateRefreshTokenHash` 추가 (JPA `@Modifying` 핀포인트 UPDATE, `updated_at` 의도적 미갱신). `RefreshData` DTO에 `refreshToken` 필드 추가. 모바일: Ktor `Auth(bearer)` 플러그인 도입으로 **401 처리 단일 지점화** (`loadTokens`/`refreshTokens`/`sendWithoutRequest(auth 제외)`). `AuthEventBus`(core/utils) `SharedFlow<Unit> sessionExpired` 신규 — `MainScreen`이 collect → 로그인 탭 강제 이동. `TokenProvider` port-adapter 분리 (`:remote:network` 인터페이스 + `:data:repositoryImpl` 구현). 제거: `RefreshAccessTokenUseCase` / `LoginRepository.refreshAccessToken` + Impl + Fake / `RefreshResponseMapper` / `LoginApi.refresh` / `LoginRepositoryImpl.CODE_UNAUTHORIZED` / `SplashViewModel`의 refresh-on-launch. **ADR-0009 accepted** (B안: DB sha256 hash + rotation. Redis 의존 회피). **ADR-0002의 401 의미 세분화** 하위 결정으로 명문화 — 일반 API 401(자동 갱신) vs `/auth/refresh` 401(강제 로그아웃). 신규 단위 테스트 0건 (권장 케이스는 backlog 등재). 서버 11 files +188/-16, 모바일 16 files +143/-116. 커밋 `dfecba5`/`68d6533`. auth-kakao 미해결 "Refresh Token Rotation" 해소.)
- **2026-05-25 — feature `home-feed` 완료** (`completed`. 홈 화면 challenge 도메인 본 UI 구축 — Sticky TopBar + StatsBar(승/패/무/연승) + 진행 중 챌린지 카드 리스트 + 빈 상태 2분기(FIRST_USER/NO_ACTIVE_CHALLENGE) + FAB. 단일 `GET /api/v1/home` 응답으로 전적+챌린지 동시 조회. 백엔드 V2 마이그레이션(`verifications` ALTER) + `UnauthorizedEntryPoint` 신설. `:core:designsystem`에 `ChallengeCard`/`StatsBar`/`HomeEmptyState` 3종 + `:core:utils`에 `Instant.toRelativeKoreanString` 헬퍼. **ADR-0003 잔여 5/6 해소** (`:feature:home` placeholder 교체). 빌드 모듈 13건 BUILD SUCCESSFUL, HomeViewModelTest 6/6 (Android JVM + iOS SimulatorArm64), 백엔드 단위 14/14, 통합 0/8(Docker 미설치 자동 skip), LoginViewModelTest 4/4 회귀 0. API 계약 변경 0건(draft→confirmed). Lovable `index.tsx` 동기 갱신.)
> 한도(10건) 초과로 2026-04-23 ADR-0001~0008 / 2026-04-24 foundation / 2026-04-24 auth-kakao(당시 partial) / 2026-04-30 `colors.md`+tokens.md 1차 동기 / 2026-04-30 designsystem Lovable 다크 1차 통합 항목은 [backlog-archive/2026-04.md](./backlog-archive/2026-04.md)로 이동.

---

## 갱신 규칙

1. **자동 추가**: pm-lead가 `report-and-document` 스킬로 feature 종료 시, 해당 summary.md의 "미해결 이슈"를 본 백로그의 적절한 우선순위 표에 추가. 출처 컬럼에 summary.md 링크.
2. **자동 이동**: 동일 스킬에서 백로그에 있던 항목이 이번 feature로 해결됐다면 "최근 완료" 섹션으로 이동.
3. **수동 정리**: 사용자가 "백로그 정리해줘" / "백로그 갱신" 요청 시 pm-lead가 모든 출처(features/*/summary.md, design ⚠️, ADR pending, repos.json blockers, 노션 PM Questions)를 다시 스캔하여 백로그를 재구성.
4. **항목 수명**: "최근 완료"는 10건까지만 본 파일에 두고, 초과 시 `docs/backlog-archive/{YYYY-MM}.md`로 이동(아카이브 파일이 처음 생성될 때만 디렉토리 생성).
5. **출처 무손실**: 백로그 항목은 항상 원본 출처 링크를 갖는다. 출처가 사라지면 백로그 항목도 검토하여 폐기/이동.
6. **우선순위 변경**: 기능 진행에 따라 🟡↔🟢 이동 자유. 외부 차단되면 🔵, 다음 sprint 시작을 차단하면 🔴.
