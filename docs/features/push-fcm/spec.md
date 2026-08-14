# 푸시 알림 (push-fcm)

- **feature-id**: push-fcm
- **owner**: pm-lead
- **상태**: draft
- **생성**: 2026-08-06

## 배경 / 문제

**지금 앱은 사용자가 홈에 들어와야만 도전장이 온 걸 안다.** 이 결함은 세 feature에서 반복 지적됐다 — [challenge-create/spec.md](../challenge-create/spec.md) 비범위, [challenge-create/design.md §받은 도전장](../challenge-create/design.md)(*받은 도전장 섹션을 진행 중 목록보다 **위**에 올린 이유가 바로 이것이다*), [soul-oath/spec.md](../soul-oath/spec.md) 미해결.

노션 기획서 §3.1은 푸시 알림을 처음부터 명시했고, `users.fcm_token`·`notifications` 테이블·인덱스는 **V1부터 파여 있다**. 배관만 없다.

동시에 **기획서 §3.1의 5종 중 3종은 지금 쏠 수 없다** — `REMIND`/`OPPONENT_VERIFIED`/`RESULT`는 카메라 인증·결과 판정에 종속이고 둘 다 미착수다. `SIGN_REQUEST`는 `soul-oath`에서 수락=서명을 원자로 묶으면서 **대상 상태 자체가 소멸**했다. 반대로 사용자가 요구한 "수락/거절을 신청자에게 알림"은 기획서에 없던 공백이었다(2026-08-06 기획서 개정으로 추가됨).

따라서 이번 범위는 **챌린지 신청·수락·거절 3종 + 그 배관 전체**다. 나머지 알림은 각자의 선행 feature가 끝나면 **발송 한 줄만 붙이면 되는 상태**로 만들어 두는 것이 이 feature의 실질 목표다.

## 사용자 시나리오

1. **A가 B에게 챌린지를 건다** → B의 기기에 *"OO님이 도전장을 보냈어!"* 푸시 → B가 앱을 열면 홈 "받은 도전장"에 있다.
2. **B가 수락(+서명)한다** → A의 기기에 *"OO님이 도전을 받아쳤어!"* 푸시 → A가 앱을 열면 홈 "진행 중"에 있다.
3. **B가 거절한다** → A의 기기에 *"OO님이 도전을 피했어..."* 푸시.
4. **A가 알림 권한을 거부했다** → 푸시는 안 뜨지만 **앱은 정상 동작한다.** 홈에 들어오면 전과 똑같이 확인된다.
5. **A가 로그아웃한다** → 그 기기로 A 앞으로 오던 알림이 **더 이상 오지 않는다.**
6. **한 기기에서 A 로그아웃 → B 로그인** (테스트 계정 전환) → 그 기기에 **A의 알림이 오지 않는다.**

## 수용 기준 (Acceptance Criteria)

### 토큰 수명주기
- [ ] 로그인 성공 직후 모바일이 FCM 토큰을 서버에 등록하고, `users.fcm_token`에 저장된다.
- [ ] FCM이 토큰을 갱신하면(`onNewToken`) **로그인 여부와 무관하게** 인증 상태일 때 재등록된다.
- [ ] ~~로그아웃 시 `users.fcm_token`이 `NULL`이 되고, 그 기기로 해당 계정 알림이 오지 않는다.~~ → 🔴 **2026-08-06 이번 범위에서 제외 (pm-lead 결정). 서버 T-B2는 구현됐으나 모바일이 호출하지 않는다.**
	- **사유**: `LogoutUseCase`가 서버를 호출하지 않는다(로컬 토큰 정리만). 호출을 넣으려면 `KtorfitModule.kt:103`의 `sendWithoutRequest { request.url.pathSegments.none { it == "auth" } }` 술어를 좁혀야 한다 — **`/auth/logout`이 Bearer 필수인데 이 술어에 걸려 토큰이 선제 전송되지 않기 때문이다.** 이는 `auth-refresh-rotation`이 401 처리를 모아둔 **인증 플러그인 전역 동작 변경**이다.
	- 🔴 **그 변경의 필요성을 판단할 근거 자체가 미검증이다** — 401 후 Ktor의 재시도는 응답의 `WWW-Authenticate` challenge를 보고 도는데 `UnauthorizedEntryPoint`가 그 헤더를 보내지 않는다. 재시도가 도는지 안 도는지 실측된 적이 없다. **검증되지 않은 전제 위에서 가장 조심스러운 영역을 이 feature 도중에 흔드는 건 순서가 틀렸다.**
	- **남는 공백**: §0.2 토큰 소유권 이전이 *계정 전환*은 덮으므로, 실제로 남는 건 **"로그아웃하고 아무도 로그인하지 않은 기기"** 하나다. 그 기기는 계속 알림을 받는다.
	- **함께 이월되는 사실 2건** (구현 시 필요): ① 서버 호출은 **`clearTokens()` 앞**이어야 한다 — 뒤에 두면 토큰이 없어 401 → refresh 시도 → 그것도 지워져 **정상적인 테스트 계정 전환이 "세션 만료"로 반응한다.** ② **순수 중복이 아니다** — logout은 소유권 이전이 건드리지 않는 `refresh_token_hash`도 끊는다.
	- → 백로그 이관. 재개 시 **먼저 `WWW-Authenticate` 실측**부터 하고 술어 범위를 정할 것.
- [ ] 🔴 **같은 토큰을 다른 계정이 등록하면 이전 계정의 `fcm_token`이 `NULL`로 밀린다** — 한 기기가 두 계정의 알림을 받는 일이 없다. (시나리오 6)
- [ ] 🔴 FCM 발송이 `UNREGISTERED` / `INVALID_ARGUMENT`를 반환하면 해당 `fcm_token`을 `NULL`로 정리한다.

### 발송
- [ ] 챌린지 신청 성공 시 **상대에게** `CHALLENGE_REQUEST` 알림이 발송된다.
- [ ] 챌린지 수락 성공 시 **신청자에게** `CHALLENGE_ACCEPTED` 알림이 발송된다.
- [ ] 챌린지 거절 성공 시 **신청자에게** `CHALLENGE_REJECTED` 알림이 발송된다.
- [ ] 🔴 **FCM 발송 실패가 챌린지 생성·수락·거절을 롤백시키지 않는다.** 발송은 커밋 이후에 일어난다.
- [ ] 수신자의 `fcm_token`이 `NULL`이어도 **`notifications` row는 저장되고** 요청은 정상 성공한다.
- [ ] 발송 3종 각각에 대해 `notifications` row가 `user_id` / `type` / `title` / `body` / `reference_id`(= `challenge_id`)와 함께 저장된다.

### 격리 (Firebase 없이도 서버가 선다)
- [ ] 🔴 **서비스 계정 키가 없어도 서버가 정상 기동하고 모든 기존 기능이 동작한다.** 발송만 no-op으로 건너뛴다.
- [ ] 키 부재 시 `notifications` row 저장은 **그대로 수행된다**(발송만 생략).
- [ ] 키 설정 오류(잘못된 경로·손상된 JSON)가 **서버를 죽이지 않는다.**

### 모바일 수신 (Android)
- [ ] Android 13+ 에서 `POST_NOTIFICATIONS` 런타임 권한을 요청하고, **거부해도 앱이 정상 동작**한다.
- [ ] 앱이 **백그라운드**일 때 알림이 시스템 트레이에 표시된다.
- [ ] 앱이 **포그라운드**일 때도 알림이 표시된다.
- [ ] 알림을 탭하면 앱이 열리고 **홈 화면**에 도달한다.

## 비범위 (Out of Scope)

| 제외 | 사유 |
|---|---|
| **알림 목록 화면** (`notifications` 조회 API + 화면 + 홈 벨 아이콘) | 별도 feature 분량. Lovable `notifications.tsx`는 이미 있다. **단, row는 이번에 쌓아둔다** — 화면이 붙을 때 과거 알림이 있어야 한다. |
| **iOS 수신** | ⛔ **Apple 계정 제약이지 기술 선택이 아니다** (2026-08-06 확인). ⚠️ 오해 방지 — **iOS에서 Firebase 자체는 무료 Apple 계정으로도 쓸 수 있다**(Analytics·Firestore·Auth·Storage). 막히는 건 **FCM 푸시 하나**이고 막는 주체는 Firebase가 아니라 Apple이다: APNs 인증키(`.p8`)가 **유료 Developer Program($99/년)에서만 발급**되고, 그 앞단 **Push Notifications capability**(`aps-environment` entitlement)도 유료 계정 App ID에서만 켜진다. 🔴 **시뮬레이터로 우회 불가** — `xcrun simctl push`는 APNs를 거치지 않는 로컬 주입이고, 무엇보다 시뮬레이터는 APNs 토큰을 못 받아 **FCM 토큰 자체가 나오지 않는다.** 서버→FCM→APNs→기기 중 어느 구간도 검증되지 않는다. `soul-oath` iOS 실기 미검증(기기 부재)과 성격이 다르다 — **결제 전에는 경로가 존재하지 않는다.** ADR-0005("iOS+Android 동시 MVP")가 이 feature에서 처음 깨지는 지점이라 별도 기록 필요. |
| `REMIND` / `OPPONENT_VERIFIED` / `RESULT` 알림 | 카메라 인증·결과 판정 feature 종속. 각 feature가 **발송 호출 한 줄만 추가**하면 되도록 배관을 이번에 완성한다. |
| `TAUNT` / `FRIEND_REQUEST` 알림 | 도발 기능 미구현 / 친구 요청은 후속. 위와 동일하게 배관은 재사용 가능. |
| **딥링크** (알림 탭 → 챌린지 상세) | Navigation 3 딥링크 배선이 별도 작업. `challengeId`는 **data 페이로드에 실어 두되** 라우팅은 홈까지만. 후속에서 payload만 소비하면 된다. |
| **알림 설정 화면** (종류별 on/off) | 기획서 §4 마이페이지 "설정"에 속한다. |
| **챌린지 취소 알림** | 상대가 아직 도전장을 보지 못한 경우가 대부분이라 알림 가치가 낮다. |
| **prod Firebase 프로젝트** | ADR-0007이 local 단계다. 배포 시점에 생성. |

## 태스크 분해

### 백엔드 (backend-dev)

- [ ] **T-B1: FCM 토큰 등록 엔드포인트** — `PUT /api/v1/users/me/fcm-token`. `UserController`에 추가, `UserService`에 `updateFcmToken`. 🔴 **같은 토큰을 쥔 다른 user의 `fcm_token`을 먼저 `NULL`로 밀고** 나서 저장(수용 기준 시나리오 6). `users` 스키마 변경 없음 — V1의 `fcm_token TEXT`를 그대로 쓴다.
- [ ] **T-B2: logout 구현** — 현재 `AuthController.logout()`은 스텁이다([foundation/backend-report.md:86](../foundation/backend-report.md)). `fcm_token = NULL` + ADR-0009의 `refresh_token_hash = NULL` 무효화를 함께 처리. **백로그의 logout 미구현 항목을 이 feature가 흡수한다.**
- [ ] **T-B3: 알림 타입 재정의** — `NotificationType` enum 신설. V1 주석의 7종에서 `SIGN_REQUEST` **제거**, `CHALLENGE_ACCEPTED` / `CHALLENGE_REJECTED` **추가**. ⚠️ DB는 `VARCHAR(30)`이라 마이그레이션 불필요하나, **V1 주석이 낡았으므로 `COMMENT ON COLUMN`으로 정정**(ADR-0010의 17건 선례).
- [ ] **T-B4: 발송 포트 + no-op 격리** — `NotificationSender` 인터페이스 + `FcmNotificationSender`(firebase-admin) + **`NoOpNotificationSender`**. 🔴 서비스 계정 키가 없거나 초기화에 실패하면 **no-op으로 떨어진다**. `dev-test-login`의 커스텀 `Condition` 선례를 따르되, 그 feature에서 배운 것을 반드시 지킨다 — **"안 열린다"여야지 "터진다"가 아니다.** 설정 오류가 서버를 죽이면 안 된다.
- [ ] **T-B5: 이벤트 배관** — `ChallengeCommandService.create()` / `.accept()` / `.reject()`가 `ApplicationEventPublisher`로 이벤트 발행. `NotificationEventListener`가 `@TransactionalEventListener(phase = AFTER_COMMIT)`로 수신 → `notifications` row 저장 + 발송. ⚠️ **AFTER_COMMIT 리스너는 기존 트랜잭션이 이미 끝난 상태다 — row를 저장하려면 `@Transactional(propagation = REQUIRES_NEW)`가 필요하다.** 이걸 빠뜨리면 저장이 조용히 실패한다.
- [ ] **T-B6: 테스트** — T-B1 토큰 밀어내기 / T-B2 이중 NULL화 / T-B4 키 부재 시 no-op + 설정 오류 시 미사망 / T-B5 롤백 시 미발송·커밋 시 발송. 통합 테스트는 컨테이너 런타임 부재로 skip 예상(백로그 45건 누적 건과 동일).

---

## ✅ 백엔드 완료 기록 (2026-08-06, pm-lead 독립 검증)

**T-B1~T-B6 전부 완료.** 검증 실행: `./gradlew test --rerun-tasks` → `GRADLE_EXIT_CODE=0`, 36 tasks executed, FAILED 0.

```
298 tests / 실패 0 / 에러 0 / skip 45  →  253/253 passed
baseline 192 → 253 (신규 61 = #32의 22 + #33의 39), 회귀 0
XML 최신 17:36:44 (측정 17:36:56 — 12초 전, 잔재 아님)
git 31파일, HEAD e5eade0, 커밋 0건
```

**backend-dev 검토 4개 축 전부 통과.** 특히 **축3 no-op 격리가 "가장 잘 된 부분"** 으로 평가됐다 — 실패 경로를 전수로 덮었다: 경로 null / 빈 문자열 / 공백뿐 / 파일 없음 / 디렉터리 / 손상 JSON / JSON이지만 서비스계정 아님 / type은 맞는데 내용 불완전 **8건**, 빈 선택 **3건**. `dev-test-login`의 *"fail-safe는 안 열린다여야지 터진다가 아니다"* 가 제대로 적용됐다.

**축2 롤백 시 미발송은 코드 방어가 아니라 구조가 보장한다** — 롤백이면 커밋이 없고 `AFTER_COMMIT` 리스너는 커밋에만 걸리므로 애초에 실행되지 않는다. 역방향(챌린지 롤백인데 알림만 발송) 경로 없음.

**수신자 배분 3종 검증** — `CHALLENGE_REQUEST`→`opponentId` / `ACCEPTED`·`REJECTED`→`challengerId`, §0.6 표와 일치. **잘못 가면 남의 알림이 되는 자리**라 별도 확인했다.

### 🔴 백엔드 미검증 3건 — summary.md·backend-report.md에 반드시 들어가야 한다

| 미검증 | 실체 |
|---|---|
| **실제 FCM 발송 0회** | 서비스 계정 키 부재로 전 구간 NoOp. **`send()` 본체가 한 번도 실행된 적 없다.** 검증된 건 에러 코드 분류(`resultFor`)뿐 |
| **`AFTER_COMMIT` / `REQUIRES_NEW` 실동작** | **어노테이션 존재·값만** 검증(`NotificationDispatcherWiringTest`, 리플렉션). 막는 실패 모드는 *"누가 어노테이션을 지우거나 phase/propagation을 바꾼다"* 하나뿐이고, *"정말 커밋 후에 도는가"* 는 증명하지 않는다 |
| **§0.2 SQL `AND id <> :me`** | fake가 술어를 Kotlin으로 다시 쓴 것이라 SQL 미검증. 실검증 경로는 skip 45건뿐(로컬 Postgres 수동 1회, 영향 0행) |

> **이 세 줄은 "덮은 범위를 실제보다 넓게 적지 않는다"는 원칙의 산물이다.** 테스트가 한계를 KDoc에 스스로 적어둔 것도 같은 맥락이다. 닫으려면 **① 서비스 계정 키 ② 컨테이너 런타임**(백로그 🔴 45건 누적 건)이 필요하다.

### 검토 지적 2건 (처리 지시됨)
1. 🟡 `NotificationDispatcher` KDoc이 *"예외 전파도 막아야 한다"* 고 절대문으로 약속하는데 `runCatching`이 메서드 **본문 안**이라 `REQUIRES_NEW` **커밋 시점 예외**(프록시에서 발생)는 못 잡는다. → **문구를 메커니즘에 맞게 좁힌다.** ⚠️ 검토자도 실증하지 못했으므로 "결함"이 아니라 **범위 불일치**로 다룬다.
2. 🟢 `runCatching`은 `catch (Throwable)`이라 `OutOfMemoryError`까지 삼켜 **JVM이 죽어야 할 상황을 숨긴다.** → 요청마다 도는 디스패처만 `catch (Exception)`으로 좁힌다. ⚠️ **기동 시점 1회인 `FirebaseCredentialsLoader`·`NotificationSenderConfig`의 `runCatching`은 유지** — 거기선 "안 터진다"가 목적이라 맞다.

### 모바일 (mobile-dev)

- [x] **T-M1a: FCM 의존성 등재 — ✅ 2026-08-06 완료·검증됨** (Firebase 프로젝트 없이 가능한 부분만 선행)
	- `gradle/libs.versions.toml` — `firebase-bom = "34.17.0"` + `firebase-bom` / `firebase-messaging`(version 미기재, BoM 관장)
	- `composeApp/build.gradle.kts` `androidMain.dependencies` — `project.dependencies.platform(libs.firebase.bom)` + `libs.firebase.messaging`. **`:composeApp`이 유일한 `com.android.application` 모듈**이고 `kakao-sdk-user` 선례와 같은 자리다.
	- **검증 (독립 2회 일치)**: mobile-dev cold 실행 `BUILD SUCCESSFUL in 5m 24s / 717 executed / config cache stored`, pm-lead 재실행 `BUILD SUCCESSFUL in 24s / reused`. `debugRuntimeClasspath`에 `firebase-bom:34.17.0 → firebase-messaging:25.1.1` 해석 확인. **APK 27,860,883 → 28,630,425 바이트(+약 750KB)** 로 실제 패키징 확인.
	- 🔴 **`platform()` 은 이 레포 최초 사용이었고 통과했다** — KMP `KotlinDependencyHandler`에 `platform()`이 없어 `project.dependencies.platform(...)`으로 우회했다. 검증되지 않은 유일한 신규 패턴이었으므로 `compileDebugKotlinAndroid`가 아니라 `assembleDebug`로 확인했다.
	- **`google-services` 플러그인은 의도적으로 미적용.** 918개 태스크 로그에 `processDebugGoogleServices`가 **0건**인 것으로 실증. json 없이 플러그인을 붙이면 그 태스크가 빌드를 실패시킨다.
	- **`.gitignore` 선제 차단 완료** — `**/google-services.json` + `**/GoogleService-Info.plist`. `git check-ignore -v`로 `composeApp/`·`feature/home/`·`iosApp/` 3경로 무시 확인. ⚠️ **플러그인 적용보다 먼저** 넣어야 json이 떨어지는 순간부터 무시되어 실수 커밋 창이 안 열린다.
	- ⚠️ **대가**: 클론 환경에서 `google-services.json` 없이는 Android 빌드가 *"File google-services.json is missing"*으로 실패한다. `local.properties`·`Secrets.xcconfig`에 이어 **"받아와야 하는 파일"이 셋으로 늘었다.** `challenge-app/CLAUDE.md`에 안내 한 줄 필요(ADR-0003 잔여 건과 함께 처리 후보).
	- working tree 3파일 M(`.gitignore` / `composeApp/build.gradle.kts` / `gradle/libs.versions.toml`), 커밋 0건 — 사용자 처리 영역.
- [x] **T-M1b: `google-services` 플러그인 적용 — ✅ 2026-08-06 완료·검증됨** (사용자가 직접 수행)
	- `libs.versions.toml` — `google-services = "4.4.2"` + `googleServices = { id = "com.google.gms.google-services", version.ref = ... }`
	- 루트 `build.gradle.kts` — `alias(libs.plugins.googleServices) apply false` / `composeApp/build.gradle.kts` — `alias(libs.plugins.googleServices)`
	- `composeApp/google-services.json` 배치(677B). **`git check-ignore` 로 무시 확인** — T-M1a에서 규칙을 먼저 넣어둔 것이 의도대로 작동했다.
	- **검증**: `BUILD SUCCESSFUL in 25s`, exit 0, FAILURE 0건. 🔴 **`:composeApp:processDebugGoogleServices` 가 태스크 그래프에 진입**했고 태스크 수가 **918 → 919 로 정확히 1개 증가**했다. 이 태스크가 돌았다는 것은 플러그인이 json을 **읽어 파싱까지 마쳤다**는 뜻이다 — 패키지명 불일치(`com.lwg.challenge`)나 JSON 손상이 있었으면 여기서 끊긴다. APK 16:04 갱신 28,632,937 바이트.
	- working tree 4파일 M(`.gitignore` / `build.gradle.kts` / `composeApp/build.gradle.kts` / `gradle/libs.versions.toml`), 커밋 0건.
- [x] **T-M1c~T-M4 — ✅ 2026-08-06 완료·검증됨** (pm-lead 독립 검증: `GRADLE_EXIT_CODE=0`, **480/480 passed**, 신규 3 / baseline 477 / **회귀 0**, `iosApp/` 변경 0건, `.entitlements` 0개, 커밋 0건)
	- 🔴 **`:core:push`를 신설하지 않았다.** 이 레포의 배치 기준은 *"같은 SDK냐"*가 아니라 **"소비자가 누구냐"** 다 — 카카오 SDK도 OAuth는 `:feature:login/kakao/`, 초대는 `:feature:friends:list/kakao/`로 **같은 SDK인데 core로 안 묶여 있다.** FCM 토큰 소비자가 `MainViewModel` 하나뿐이라 같은 기준을 적용했다. **두 번째 소비자(알림 설정 화면, 기획서 §4)가 생기면 그때 옮긴다.**
	- 배치 3분할: 토큰 획득 expect/actual + `platformPushModule` → `:feature:main` / `NotificationPermissionEffect` → `:core:ui`(`PlatformBackHandler`와 같은 종류) / `ChallengeFirebaseMessagingService`·채널·아이콘 → `:composeApp` androidMain (**강제** — feature 모듈에 소스 `AndroidManifest.xml`이 하나도 없다)
	- 🔴 **T-M2 토큰 등록을 `LoginViewModel`에 넣지 않았다.** 스펙 문구가 *"로그인 성공 직후"*라 거기가 자연스러워 보이지만 **넣으면 조용히 잘린다** — 로그인 성공 시 탭 전환으로 Login NavEntry가 백스택에서 빠지고 그 ViewModelStore가 정리되며 `viewModelScope`가 취소된다. 토큰 획득(FCM SDK 왕복)+등록(네트워크 왕복)이 그 전에 못 끝나면 실패하는데 **아무 신호가 없다.** → Activity 루트인 `MainRoute`에서 *"Splash/Login을 벗어나는 순간"*을 트리거로. 부수적으로 splash 자동 로그인 경로도 덮는다.
	- `onNewToken`은 **인증 상태일 때만** 등록 — 로그아웃 기기가 직전 계정 알림을 계속 받는 것을 막는다.
	- **T-M3 포그라운드 표시는 자동이 아니다** — 혼합 페이로드(§0.5)는 백그라운드면 시스템이 표시하고 `onMessageReceived`가 안 불리며, 포그라운드면 반대다. 그래서 `onMessageReceived`에서 `NotificationCompat`으로 **직접 표시**한다. 채널 id는 manifest와 Kotlin이 **같은 string 리소스를 참조**해 어긋날 수 없게 했다.
	- **T-M4 거부해도 정상 동작**: 권한 결과 콜백이 **비어 있어** 거부가 바꿀 상태 자체가 없다 + `LaunchedEffect`라 흐름 미차단 + 13 미만 조기 return + `rememberSaveable`로 1회만. 🔴 **권한 없이 `notify()`는 예외를 던지지 않고 플랫폼이 조용히 버린다** — 표시 실패가 프로세스에 영향을 주지 않는 근거.
	- **iOS는 전부 no-op 스텁**(pm-lead 실측): `FcmTokenProviderIos.getToken() = null` → `MainViewModel`이 `?: return@launch`로 **등록 호출 자체를 안 한다**(빈 문자열로 §1 blank 거부를 유발하는 경로 없음) / `NotificationPermissionEffect.ios` 빈 본문 / `PlatformPushModule.ios`는 바인딩만. **`iosApp/`·Info.plist·Podfile 무접촉, Push capability 미적용.**
	- **자진 정정 1건**: `notify()`를 감싼 `runCatching` + *"일부 경로에서 SecurityException"* 주석을 **스스로 제거**했다 — 관측된 사실이 아니라 추측이었다는 이유. 사용자 원칙이 지시 없이 적용된 사례다. pm-lead 실측으로 push-fcm 범위 `runCatching` 0건 확인.
## ✅ 실기 검증 기록 (2026-08-07, pm-lead가 DB로 교차 검증)

**서버 재기동 전** (PID 982, `FCM_CREDENTIALS_PATH` 미주입) — §0.4 no-op 격리가 실기에서 증명됐다:
- 키가 없는데도 **서버 정상 기동**, 챌린지 생성 성공, `notifications` row 저장, **발송만 조용히 스킵**
- `notif#1` → `user_id=1`(토큰 NULL): **발송 스킵 + row는 저장** — 수용 기준 *"`fcm_token`이 `NULL`이어도 row는 저장되고 요청은 정상 성공"* 이 실제 DB에서 확인됨

**서버 재기동 후** (PID 4070, `.env`의 `FCM_CREDENTIALS_PATH` 주입 확인) — **`send()` 본체가 처음 실행됨**:

| notif | 시각 | type | 수신자 | 토큰 | ref |
|---|---|---|---|---|---|
| #3 | 14:40:57 | **`CHALLENGE_REJECTED`** | 14 테스터1 | set | 25 |
| #4 | 14:41:27 | `CHALLENGE_REQUEST` | 15 테스터2 | set | 26 |

🔴 **#3이 핵심** — 거절 알림만 **수신자가 신청자 쪽으로 뒤집힌다.** 기획서에 없던 공백이라 이번에 새로 정의한 축인데(§0.6), 실기에서 그대로 동작했다. `reference_id`도 전부 해당 `challenges.id`와 일치.

**부수로 검증된 것**: `uq_challenges_active_pair_date`가 25(PENDING) 때문에 재신청을 막다가, `REJECTED` 전이 후 쌍이 풀려 **26이 정상 생성**됐다 — 제약이 의도대로 걸리고 의도대로 풀리는 것까지 확인.

**`.env` 주입 경로 확정**: 서버가 `./gradlew bootRun`이 아니라 **IntelliJ에서 구동**된다. `.env`를 읽는 코드가 프로젝트에 없어 반영 여부가 불확실했으나, 재기동 후 프로세스 환경에 `FCM_CREDENTIALS_PATH`가 존재함을 실측해 확정했다(IDE 레벨 주입).

---

- [ ] 🔴 **T-M5 실기 검증 — 아래는 아직 미확인.** 아래는 **빌드가 초록인 것과 무관하게 전부 미검증**이다. `soul-oath`에서 *"테스트는 초록인데 실제로는 틀린"* 것을 6번 겪은 것을 감안해 분리해 적는다.

| 실기 필요 항목 | 왜 지금 불가 |
|---|---|
| **FCM 토큰이 실제로 발급되는지** | 실기/에뮬레이터 + Play Services 필요. `google-services.json`이 붙어도 토큰 발급은 런타임 왕복이다 |
| **`PUT /users/me/fcm-token` 왕복** | 서버 실행 필요. 지금은 Ktorfit 인터페이스가 컴파일된 것뿐 |
| **알림이 실제로 뜨는지** (백그라운드/포그라운드) | 🔴 **서비스 계정 키 부재로 발송 자체가 불가.** 서버→FCM 구간이 no-op이라 기기까지 도달할 경로가 없다 |
| **알림 탭 → 홈 도달** | 알림이 떠야 탭할 수 있다 |
| **`POST_NOTIFICATIONS` 다이얼로그 타이밍** | 코드상 Splash/Login 이탈 시점이지만 **실제로 그 순간에 뜨는지 안 봤다** |
| **`onNewToken` 발화** | 토큰 갱신은 재설치·데이터 삭제 등에서만 일어나 인위적 유발 필요 |
| **알림 아이콘 렌더링** | `ic_notification.xml`이 **디자인 미확정 placeholder**(임시 종 모양). 흰색 실루엣+투명 배경 규칙은 지켰으나 실제 트레이 모양 미확인 |

> ⚠️ **`skipped=0`을 "전부 돌았다"로 읽으면 안 된다.** JVM 단위 테스트 집계이고 **iOS `iosSimulatorArm64Test`는 아예 실행하지 않았다.** friends·user-info·challenge-create에 이어 같은 패턴의 누적 항목이다.
>
> ⚠️ **`MainRoute` 재구성 증가** — `backStack.lastOrNull()`을 읽게 되어 네비게이션마다 재구성된다. `NavDisplay` 하위는 영향 없고 트리거에 필요한 동작이지만, 성능 이슈가 보이면 여기가 원인 후보다. ⛔ **`google-services.json`이 없으면 Gradle 빌드가 실패한다** — 사용자 제공 전까지 이 태스크는 착수 불가. iOS는 이번 범위 밖이라 `expect`/`actual`의 iOS actual은 **no-op 스텁**으로 둔다.
	- 🔴 **KMP 커뮤니티 래퍼를 쓰지 않는다 — 네이티브 SDK + expect/actual** (2026-08-06 조사).
	- **공식 Firebase KMP SDK는 존재하지 않는다.** 2026년 중반 기준 Firebase 공개 feature board에도 없고, 공식 SDK는 Android(Kotlin/Java) / iOS(Swift·ObjC)가 별개다. 커뮤니티 대안은 KFire(beta) / GitLive `firebase-kotlin-sdk` / KMPNotifier / Firebase-KMP-Kit 등이 있다.
	- **그런데 FCM은 공통화할 게 거의 없다.** 토큰 획득만 공통 지점이고, **수신·알림 표시는 전적으로 플랫폼 코드**(Android `FirebaseMessagingService`, iOS `UNUserNotificationCenter`)라 래퍼를 써도 양쪽 구현을 다 작성해야 한다. 서버 발송은 firebase-admin(JVM)이라 KMP와 무관하다. 얻는 것이 얇은 expect/actual 하나를 아끼는 것뿐인데, 대가는 **통제 불가한 의존성 + 네이티브 SDK 릴리스 지연 + 메인테이너가 감싼 부분집합만 노출**이다.
	- **레포 선례를 답습한다** — 카카오 SDK도 KMP 지원이 없어 `:core:invite`의 `KakaoInviter` expect/actual + iOS `KakaoInviteBridge` handler 주입 + `KakaoLoginHelper.swift`로 처리했고 잘 동작한다. 같은 구조로 간다.
- [ ] **T-M2: 토큰 등록 배선** — 로그인 성공 직후 + `onNewToken` 두 진입점에서 `PUT /users/me/fcm-token` 호출. ⚠️ **FCM 토큰의 수명주기는 로그인 수명주기와 다르다**(앱 재설치·데이터 삭제·토큰 만료 시 언제든 갱신) — 그래서 로그인 요청 body에 싣지 않고 독립 엔드포인트를 쓴다.
- [ ] **T-M3: 수신 + 표시** — `FirebaseMessagingService` 구현. 포그라운드에서도 표시되도록 처리. 알림 탭 → 홈.
- [ ] **T-M4: `POST_NOTIFICATIONS` 권한** (Android 13+) — 로그인 직후 요청. **거부해도 앱이 정상 동작**해야 한다(수용 기준).
- [ ] **T-M5: 테스트** — 토큰 등록 UseCase/Repository 단위 테스트. 수신부는 플랫폼 코드라 실기 검증으로 대체.

### 사용자 (선행 — 콘솔 작업)

- [ ] **T-U1: Firebase 프로젝트 생성** (`maengse-dev` 등)
- [ ] **T-U2: Android 앱 등록** — 패키지 `com.lwg.challenge`(실측: `composeApp/build.gradle.kts:87`) → `google-services.json`을 `challenge-app/composeApp/`에 배치
- [ ] **T-U3: 서비스 계정 비공개 키 발급** → 레포 **밖**에 두고 경로를 환경변수로 주입. ⚠️ 커밋 금지.

## 의존 관계

```
T-U1 ──> T-U2 ──> T-M1 ──> T-M3, T-M4
   └───> T-U3 ──> (T-B4 실제 발송 검증만)

API 계약 confirmed ──> T-B1, T-B2, T-M2
T-B3 ──> T-B5
T-B4 ──> T-B5 ──> T-B6
```

🔴 **백엔드는 T-U1~T-U3 없이 T-B1~T-B6 전부 완료 가능하다.** T-B4의 no-op 격리가 그것을 성립시키는 장치다 — 키가 없으면 발송만 건너뛰고 나머지(row 저장·이벤트·엔드포인트)는 전부 돌고 테스트도 통과한다. **모바일 T-M1만이 진짜 하드 블로커**다(`google-services.json` 없이는 Gradle이 실패).

## 리스크 / 오픈 이슈

- 🔴 **iOS가 이번에 빠지는 것이 ADR-0005와 어긋난다.** "iOS+Android 동시 MVP"가 이 feature에서 처음 깨진다. 기술 선택이 아니라 Apple 계정 미구입이라는 외부 제약이므로, **ADR로 남길지 백로그 항목으로 둘지 결정 필요**.
- **알림 문구가 미확정이다.** 시나리오의 *"도전장을 보냈어!"* 등은 초안이다. Lovable 화면 톤이 이미 화면별로 갈려 있다는 지적([challenge-create/design.md §9](../challenge-create/design.md))이 있어, 알림 문구도 같은 문제를 겪는다. 디자인 확인 필요.
- **알림 탭 → 홈까지만** 간다. 도전장이 여러 개면 어느 것인지 알 수 없다. 딥링크는 후속인데, 그 전까지 알림 가치가 반감된다는 점을 인지하고 간다.
- `notification` + `data` 혼합 페이로드를 쓸지 `data`-only로 갈지는 **API 계약에서 확정**한다(§ 페이로드 규약).
- 통합 테스트는 컨테이너 런타임 부재로 또 skip될 가능성이 높다. 누적 45건에 더해진다.
