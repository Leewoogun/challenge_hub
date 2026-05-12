# 백로그 — challenge 프로젝트

> 흩어진 TODO/미해결/후속 작업을 한 곳에서 추적하는 살아있는 문서. 분류는 우선순위 + 담당자.
>
> **자동 갱신**: pm-lead가 `report-and-document` 스킬로 feature를 마무리할 때마다 summary.md의 미해결 이슈를 본 백로그에 자동 추가. 임의 시점 재정리는 "백로그 정리해줘" 한 마디로 pm-lead에게 요청.

- **마지막 갱신**: 2026-05-12 (design-bridge — Lovable `text-[10px]` 전수 점검 + tokens.md §5.2 인벤토리 보강, LoginScreen 10sp 라벨 정합 후속 등재)
- **우선순위 기호**: 🔴 긴급(블로커) / 🟡 중요 / 🟢 일반 / 🔵 대기(외부 의존)
- **담당 약어**: pm / mobile / backend / design / user(사용자가 직접 처리)

---

## 🔴 긴급 (블로커)

_없음 — 다음 sprint 시작에 직접적 블로커는 없음._

## 🟡 중요

| 항목 | 출처 | 담당 | 메모 |
|---|---|---|---|
| Android keyhash 카카오 콘솔 등록 | [auth-kakao/change-log.md](./features/auth-kakao/change-log.md) | user | NATIVE APP KEY는 ✅ 발급+기입 완료. 콘솔에 `debug.keystore` SHA1 keyhash 등록 여부 확인 필요. |
| 영혼의 맹세(STT + 서명) 화면 디자인 | 노션 [📋 Common States & PM Questions](https://app.notion.com/p/3523902cbe248111ac2dd40fcd8fda64) | design + user | 핵심 플로우인데 Lovable에 화면 부재. 디자이너 작업 필요. |
| 전화번호 등록 화면 UX (SMS 인증 제거 후) | 노션 동상 / [ADR-0008](./decisions/0008-friend-matching.md) | design + user | 친구 매칭 활성화 조건. 카카오 scope 동의/마이페이지 등록 등 등록 경로 미정. |
| LoginScreen 시각 검증 (디자인 2차 반영 후) | [auth-kakao/summary.md](./features/auth-kakao/summary.md) | user | Android 에뮬레이터 + iOS Simulator에서 직접 확인 — "영혼" brush / 🔥 wiggle / 스탬프 pulse-fire / 글로우·블롭 톤 / 노치 safeDrawing. |
| BottomBar 시각 검증 (bottom-navigation 완료 후) | [bottom-navigation/summary.md](./features/bottom-navigation/summary.md) | user | Android 에뮬레이터 + iOS Simulator — 4탭 시각 균형(10.sp / 22.dp / gap 2.dp) / Active↔Inactive 대비 / alpha 95% surface 구분 / iOS 홈 인디케이터 침범 / 탭 전환 active 갱신 / Splash/Login에서 숨김 유지. |
| 디자이너 시각 검증 6건 (gradient end / card stops / chart4 / glow brush / 135deg / SoulStampLogo 회전 제거 후 시각 균형) | [colors.md §5](./design-system/colors.md) | design + user | oklch→hex 자체 변환분 + 외곽 회전 링 제거 결정 후 시각 균형. 디자이너 부재로 추정값 그대로 채택 중. |

## 🟢 일반

| 항목 | 출처 | 담당 | 메모 |
|---|---|---|---|
| AuthKakao 통합 테스트 수동 실행 (Docker Desktop 후 `--tests "*AuthKakaoIntegrationTest"`) | [auth-kakao/backend-report.md](./features/auth-kakao/backend-report.md) | user + backend | 5 케이스 검증 (drift 정정 후 5xx 1회 재시도→703 시나리오 추가). CI 적용 시 docker-in-docker 필요. |
| 로컬 서버 기동 + 모바일 수동 smoke test (Android+iOS real Kakao SDK 흐름) | [auth-kakao/summary.md](./features/auth-kakao/summary.md) | user | NATIVE APP KEY 기입 완료. Android 에뮬레이터/실기기 + iOS Simulator/Device에서 카카오 로그인 → JWT 발급 E2E 확인 필요. 카카오톡 앱-간 인증과 웹 fallback 둘 다. |
| iOS SPM 카카오 SDK 버전 pin 적정성 확인 | [auth-kakao/change-log.md](./features/auth-kakao/change-log.md) | mobile | `iosApp/iosApp.xcodeproj/project.pbxproj`의 `XCRemoteSwiftPackageReference`에 `requirement`(`upToNextMajor` 등) 명시 여부 점검. |
| `application.yml` Swagger UI path 한글자음 'ㅠ' 오타 정정 | [auth-kakao/change-log.md](./features/auth-kakao/change-log.md) | backend | line 60 `swagger-ui.path: /swagger-ui/index.htmlㅠ`. Swagger UI 접근 안 될 가능성. 즉시 수정 가능. |
| `:feature:login:check` detekt config 부재 (`/config/detekt/detekt.yml`) | [auth-kakao/change-log.md](./features/auth-kakao/change-log.md) | mobile | 컴파일/테스트는 통과하나 `check` 태스크 fail. 인프라 티켓. |
| iOS Keychain 실기기 smoke (write/read roundtrip) | [auth-kakao/mobile-report.md](./features/auth-kakao/mobile-report.md) | mobile | SecItemAdd/Copy 상태코드 확인. |
| Compose blur 미적용 (LoginScreen `blur-3xl` + bottom-navigation `backdrop-blur-xl` 동일 카테고리) | [auth-kakao/mobile-report.md](./features/auth-kakao/mobile-report.md) · [bottom-navigation/summary.md](./features/bottom-navigation/summary.md) | mobile + design | 현재 alpha만으로 근사. 시각 차이 크면 platform actual blur(`graphicsLayer { renderEffect = BlurEffect(...) }` Android API 31+ / iOS `UIVisualEffectView` interop) 도입 검토. KMP 공통 API 부재로 expect/actual 분기 필요. |
| Material Icons Extended 1.7.3 deprecation | [auth-kakao/mobile-report.md](./features/auth-kakao/mobile-report.md) · [bottom-navigation/summary.md](./features/bottom-navigation/summary.md) | mobile + pm | Kotlin 2.2.20 / CMP 1.10.3 호환 이슈로 1.7.3 핀. `:feature:login`(`LocalFireDepartment`/`AutoAwesome`)에 이어 `:feature:main` BottomBar(`Home`/`Group`/`EmojiEvents`/`Person`)도 동일 의존성 사용 시작 — 사용처 누적. Material Symbols(vector resources) 마이그레이션 ADR 후보. |
| Glow shadow / 외광 효과 미구현 | [auth-kakao/mobile-report.md](./features/auth-kakao/mobile-report.md) | mobile + design | tokens.md §3 `--shadow-glow` (0 0 30px primary 20%) Compose 기본 `shadow()` 표현 어려움. Canvas glow 별도 작업 후보. |
| 카카오 버튼 ripple 색 (`KakaoYellowPressed`) | [auth-kakao/design.md](./features/auth-kakao/design.md) | mobile + design | 현재 Surface 기본 ripple. 디자이너 확인 후 `BrandColors.KakaoYellowPressed` ripple 매핑 작업. |
| `./scripts/generate-feature.sh` 패키지 경로 버그 (line 39 `SRC_DIR=com.lwg.base/...`) | [bottom-navigation/summary.md](./features/bottom-navigation/summary.md) | mobile | 실제 패키지는 `com.lwg.challenge`인데 스크립트가 `com.lwg.base`로 생성. 향후 신규 feature 작업 차단. 본 작업은 ex1 패턴 따라 수동 생성으로 우회. 즉시 가능한 위생 작업. |
| `:feature:login` Preview annotation deprecation 경고 다수 | [bottom-navigation/summary.md](./features/bottom-navigation/summary.md) | mobile | bottom-navigation 빌드 중 발견. `@Preview` 사용처 일괄 마이그레이션 (Material3 / KMP Preview annotation 변경). 정리 후보, 즉시 가능. |
| LoginScreen 10sp 라벨 `bold10`/`light10` 슬롯 정합 | [tokens.md §5.2](./design-system/tokens.md) · [auth-kakao/design.md](./features/auth-kakao/design.md) | mobile + design | 2026-05-12 design-bridge Lovable 전수 점검 결과. Lovable `login.tsx`: LabeledDivider "한 번 서명하면 무를 수 없음" `text-[10px] font-bold`(10sp) / 약관 풋터 `text-[10px]`(10sp, weight 미지정→Light). 현 모바일은 `bold12`/`light12`(12sp). (1) `:core:designsystem/ChallengeTypography.kt`에 `bold10`/`light10` 슬롯 추가(`medium10`과 동일 패턴, lineHeight 14). (2) LoginButtonSection의 LabeledDivider `textStyle = typography.bold10`, FooterAgreementText `style = typography.light10`로 교체. ranking/index/notifications/challenge-detail/challenge-new/ChallengeCard 등 다른 화면은 후속 feature 진입 시 자연 정합(현재는 모바일 placeholder). |
| 동시 로그인 시 `kakao_id` UNIQUE 충돌 재시도 로직 | auth-kakao/backend-report.md | backend | MVP 현실성 낮음. 향후 보강. |
| Refresh Token Rotation (옛 refresh 무효화) | auth-kakao | backend + pm | ADR-0009(예정) 결정 후 작업. |
| `:feature:home` Movie 예제 → challenge 홈으로 교체 | [ADR-0003](./decisions/0003-mobile-template-init.md) | mobile | 후속 feature `home-feed`에서 처리. bottom-navigation 완료 후 자연스러운 다음 단계. |
| `challenge-app/CLAUDE.md` 모듈 구조 정정 (`:core:domain/network/data` → `:domain:*`/`:remote:*`/`:data:*`) | [ADR-0003](./decisions/0003-mobile-template-init.md) | mobile | 즉시 가능, 작업 짧음. |
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
| [ADR-0003 모바일 템플릿 초기화](./decisions/0003-mobile-template-init.md) | in-progress (4/6 완료, ex1~3 제거 ✅ bottom-navigation 2026-05-11) | 잔여: home Movie 교체(후속 `home-feed`), CLAUDE.md 정정 (위 🟢 항목 참조) |
| ADR-0009 Refresh Token Rotation | 미작성 | 위 🟢 "Refresh Token Rotation" 트리거 |
| ADR-0010 라이트 테마 (보류 결정) | 미작성 | 위 🟢 "라이트 테마 ADR" 트리거 |

## 분류별 보기 (담당자 기준)

### 사용자 액션 (user)
- Kakao scope 승인 / Apple Developer / Firebase / Docker Desktop 실행
- 디자이너에게 영혼의 맹세 / 전화번호 등록 화면 + 16건 질의 전달
- 디자이너 시각 검증 5건

### 모바일 (mobile)
- iOS Keychain 실기기 smoke
- iOS SPM 카카오 SDK 버전 pin 적정성 확인
- home Movie 예제 교체 (후속 feature `home-feed`)
- `challenge-app/CLAUDE.md` 모듈 구조 정정
- detekt config 부재 정리
- Compose blur 미적용 (LoginScreen + BottomBar 동일 카테고리, `BlurEffect` 도입 검토)
- Material Icons Extended deprecation → Material Symbols 마이그레이션 ADR 후보
- Glow shadow / 외광 효과 (Canvas glow)
- 카카오 버튼 ripple 색 매핑
- `generate-feature.sh` 패키지 경로 버그 (즉시 가능)
- `:feature:login` `@Preview` deprecation 경고 정리 (즉시 가능)
- LoginScreen 10sp 라벨 `bold10`/`light10` 슬롯 정합 (tokens.md §5.2 후속, 즉시 가능)

### 백엔드 (backend)
- 동시성 보호
- Refresh Token Rotation (ADR-0009 후)
- Redis 용도 결정
- Swagger UI path 오타 정정

### 디자인 (design)
- 영혼의 맹세 화면
- 전화번호 등록 화면
- 시각 검증 5건 회신
- 16건 통합 회신

### PM (pm)
- ADR-0009 / ADR-0010 작성 결정
- 디자이너 질의 통합 전달

---

## ✅ 최근 완료 (최근 10건만 유지, 초과 시 archive로)

- **2026-05-11 — feature `bottom-navigation` 완료** (`completed`. CmpSystem 잔재 4탭 → challenge 4탭(홈/친구/랭킹/MY) 재구성. `:feature:friends/ranking/mypage` 신규 모듈 3종 + `PlaceholderScreen` 재사용 컴포넌트. `ChallengeBottomBar` Material `NavigationBar` 폐기 → `Surface + Row` 커스텀(alpha 95% / 10.sp / safe-area). `:feature:ex1/ex2/ex3` 모듈 통째 삭제 (ADR-0003 잔여 해소). 빌드 7건 BUILD SUCCESSFUL, LoginViewModelTest 4/4 회귀 0.)
- **2026-05-11 — auth-kakao LoginScreen 디자인 2차 반영 완료** (pm-lead 결정 9건 → Lovable 동기 갱신 → 모바일 LoginScreen 풀세트 반영. Hero/CTA + slide-up/fadeIn + 글로우·블롭 배경. `:core:designsystem`에 StatusPillBadge/LabeledDivider/Divider/Spacer 추출. `:feature:login/component`에 SoulStampLogo/BackgroundDecor/ChallengeSection/ChallengeTitle/FooterAgreementText/LoginButtonSection 분할. 빌드 4건 BUILD SUCCESSFUL, LoginViewModelTest 4/4 passed. 커밋 `fb68069`+`d7529cc` main 푸시 완료. INDEX `partially-completed`→`completed`.)
- 2026-05-07 — **iOS Kakao SDK 실연동 완료** (SPM `kakao-ios-sdk` 통합, `KakaoLoginHelper.swift` Swift→Kotlin bridge, `iOSApp.swift` `KakaoSDK.initSDK` + `onOpenURL` URL handler, Info.plist `kakao$(KAKAO_NATIVE_APP_KEY)` xcconfig 변수 주입, `KakaoAuthClient.ios.kt` placeholder→실 구현. Android+iOS 모두 SDK 통합 완료)
- 2026-05-07 — 백엔드 카카오 로그인 SDK 방식 정렬 (drift 정정: `/oauth/token` 교환 코드 + `KAKAO_REST_API_KEY` 등 4개 env 제거. `:infra/:api/:app` BUILD SUCCESSFUL, AuthControllerTest 5/5)
- 2026-05-07 — 모바일 Android Kakao SDK 실연동 (`com.kakao.sdk:v2-user:2.20.6`, `loginWithKakaoTalk` → fallback `loginWithKakaoAccount`, LoginViewModelTest 4/4)
- 2026-05-07 — `:core:designsystem` ColorScheme 단일화 (`ChallengeExtendedColors` 폐지 → `ChallengeColorScheme` 단일, `ChallengeTheme.colorScheme.<name>` 단일 진입점) + colors.md/tokens.md/노션 동기
- 2026-05-07 — Typography Lovable 정합 (Tailwind 스케일 12/24/30 슬롯 신설, lineHeight 4건 정렬, GmarketSans 3종 자산 매핑 정책 명시)
- 2026-04-30 — 디자인 노션 하위 페이지 5건 정리 (Color/Typography/Component/Screens/Common States)
- 2026-04-30 — `:core:designsystem` Lovable 다크 기준 1차 통합 + ExtendedColors/Brushes/BrandColors 신설
- 2026-04-30 — `colors.md` + 노션 Color Tokens 페이지 + tokens.md 1차 동기
> 한도(10건) 초과로 2026-04-23 ADR-0001~0008 / 2026-04-24 foundation / 2026-04-24 auth-kakao(당시 partial) 항목은 [backlog-archive/2026-04.md](./backlog-archive/2026-04.md)로 이동.

---

## 갱신 규칙

1. **자동 추가**: pm-lead가 `report-and-document` 스킬로 feature 종료 시, 해당 summary.md의 "미해결 이슈"를 본 백로그의 적절한 우선순위 표에 추가. 출처 컬럼에 summary.md 링크.
2. **자동 이동**: 동일 스킬에서 백로그에 있던 항목이 이번 feature로 해결됐다면 "최근 완료" 섹션으로 이동.
3. **수동 정리**: 사용자가 "백로그 정리해줘" / "백로그 갱신" 요청 시 pm-lead가 모든 출처(features/*/summary.md, design ⚠️, ADR pending, repos.json blockers, 노션 PM Questions)를 다시 스캔하여 백로그를 재구성.
4. **항목 수명**: "최근 완료"는 10건까지만 본 파일에 두고, 초과 시 `docs/backlog-archive/{YYYY-MM}.md`로 이동(아카이브 파일이 처음 생성될 때만 디렉토리 생성).
5. **출처 무손실**: 백로그 항목은 항상 원본 출처 링크를 갖는다. 출처가 사라지면 백로그 항목도 검토하여 폐기/이동.
6. **우선순위 변경**: 기능 진행에 따라 🟡↔🟢 이동 자유. 외부 차단되면 🔵, 다음 sprint 시작을 차단하면 🔴.
