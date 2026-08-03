# 개발용 테스트 로그인 (dev-test-login)

- **feature-id**: dev-test-login
- **owner**: pm-lead
- **상태**: draft
- **생성**: 2026-07-31

## 배경 / 문제

친구 요청·수락·거절과 챌린지 신청·수락은 **계정이 2개 이상 있어야** 손으로 검증할 수 있다. 그런데 현재 모바일의 로그인 경로는 **카카오 로그인 하나뿐**이라, 사용자가 혼자 테스트하려면 실제 카카오 계정을 여러 개 준비해 기기를 바꿔가며 로그인해야 한다.

`challenge-create`와 `friends`의 미해결 이슈에 "실기기 시각 검증", "manual smoke"가 계속 쌓이고 있는데 그 병목이 정확히 이것이다.

→ **가짜 계정 N개 + 그 계정으로 즉시 로그인하는 버튼**을 만들어 혼자서 양쪽 역할을 오갈 수 있게 한다.

## 🔴 이 feature는 인증 우회 경로를 만든다 — 격리가 수용 기준이다

카카오 검증 없이 JWT를 발급하는 엔드포인트다. **운영에 새어 나가면 누구나 임의 계정으로 로그인할 수 있다.** 따라서 아래를 기능 요구사항과 **동등한 우선순위**로 다룬다.

1. **fail-closed** — 설정을 하지 않으면 **꺼진 상태가 기본값**이어야 한다. "운영에서 끄는 것을 잊으면 열리는" 구조는 금지. 명시적으로 켠 환경에서만 빈이 생성돼야 한다.
2. **빈 자체가 존재하지 않아야 한다** — 엔드포인트가 등록되고 내부에서 403을 주는 방식이 아니라, **애초에 라우팅에 없어야** 한다(`/v3/api-docs`에도 안 보여야 한다).
3. **모바일 버튼은 debug 빌드에서만** — release 빌드에 컴파일되지 않거나, 최소한 렌더되지 않아야 한다.
4. **가짜 계정은 식별 가능해야 한다** — 실사용자와 섞이면 안 되고, 한 번에 지울 수 있어야 한다. 기존 e2e 하네스가 쓴 `kakao_id 999000001~` 대역을 승계한다.

## 사용자 시나리오

1. (사용자) 앱 실행 → 로그인 화면에 **"테스트 로그인"** 노출(debug 빌드) → 계정 목록에서 `테스터A` 선택 → 즉시 홈 진입
2. (사용자) `테스터A`로 `테스터B`에게 친구 요청 → 로그아웃 → **`테스터B`로 테스트 로그인** → 받은 요청 수락
3. (사용자) `테스터A`로 `테스터B`에게 챌린지 신청 → `테스터B`로 전환 → 받은 도전장 수락 → 홈에 진행 중 챌린지 노출 확인
4. (사용자) 거절·취소 경로도 같은 방식으로 왕복 검증

## 수용 기준 (Acceptance Criteria)

### 격리 (기능과 동등 우선순위)
- [ ] 설정을 **하지 않은** 상태로 서버를 띄우면 테스트 로그인 엔드포인트가 **존재하지 않는다** — 호출 시 404이고 `/v3/api-docs` 경로 목록에도 없다
- [ ] 설정을 켠 상태에서만 엔드포인트가 등록된다
- [ ] 위 두 상태를 **각각 테스트로 고정**한다 (켰을 때 동작 / 껐을 때 부재)
- [ ] 모바일 release 빌드에 테스트 로그인 UI가 **노출되지 않는다**
- [ ] 가짜 계정이 `kakao_id 999000001~` 대역으로만 생성되어 한 쿼리로 식별·삭제 가능하다

### 기능
- [ ] 테스트 로그인 호출 시 지정한 가짜 계정의 **access + refresh 토큰**이 발급된다 (실제 로그인과 동일한 형태)
- [ ] 해당 계정이 없으면 생성하고, 있으면 재사용한다 (**멱등**) — 반복 호출해도 계정이 늘지 않는다
- [ ] 발급된 토큰으로 기존 인증 API(`/users/me`, `/friends`, `/challenges/*`)가 정상 동작한다
- [ ] 최소 **3개** 계정을 선택할 수 있다 (친구 요청·수락 + 제3자 케이스 검증용)
- [ ] 모바일에서 테스트 로그인 성공 시 **기존 카카오 로그인과 동일한 후처리**를 탄다 (토큰 저장 / 홈 이동 / `UserInfo` 캐시)
- [ ] 로그아웃 후 다른 테스트 계정으로 재로그인이 가능하다 (**ADR-0009 1기기 1세션**과 충돌하지 않는지 확인)

### 회귀
- [ ] 백엔드 기존 테스트 회귀 0
- [ ] 모바일 기존 테스트 회귀 0 (`LoginViewModelTest` 포함)
- [ ] Android · KMP common · iOS 빌드 성공

## 비범위 (Out of Scope)

- **운영 환경 배포 설정** — ADR-0007(local→AWS phased)의 범위다. 이 feature는 "운영에서 꺼져 있음"만 보장한다.
- **가짜 데이터 시드 확장** — 계정만 만든다. 친구 관계·챌린지·전적을 미리 채우지 않는다. 그건 사용자가 앱에서 직접 만들면서 검증하는 게 이 feature의 목적이다.
- **테스트 계정 관리 UI** — 삭제·초기화 화면 없음. 필요하면 DB에서 지운다.
- **디자인** — dev 전용 affordance다. 기존 토큰만 쓰고 디자이너 검토 대상이 아니다. design-bridge는 이 feature에 참여하지 않는다.
- **자동화 테스트 대체** — 사람이 손으로 도는 걸 돕는 도구지 e2e 자동화가 아니다.

## 태스크 분해

### 백엔드 (backend-dev)

- [ ] **T-B1**: 격리 장치 — 설정 기반 조건부 등록. **fail-closed(기본 꺼짐)**를 만족하는 방식을 선택하고 근거를 남길 것. 현재 레포에 Spring 프로파일 사용처가 **0건**이므로 프로파일을 새로 도입할지, 속성(`@ConditionalOnProperty`) 기반으로 갈지 backend-dev가 판단한다. **"운영에서 끄는 것을 잊으면 열리는" 구조는 금지.**
  > **🔴 2026-07-31 실측 — "꺼진 상태 = 404" 기준은 격리 장치만으로 성립하지 않는다** (backend-dev 발견, pm-lead 재현). 아래 2건이 함께 필요하다.
  > ```
  > POST /api/v1/auth/test-login   → 401   (SecurityConfig가 라우팅 전에 가로챔)
  > POST /api/v1/auth/nonexistent  → 401   (경로 존재 여부와 무관)
  > GET  /actuator/health          → 500   (permitAll인데 핸들러 없음 → handleUncaught)
  > ```
  > **왜 401이 해로운가 — 구별 불가 정도가 아니라 적극적으로 틀린 결론을 낸다** (2026-07-31 mobile-dev 코드 실측, pm-lead 재확인). `KtorfitModule.kt:67-72`:
  > ```kotlin
  > refreshTokens {
  >     val refreshToken = oldTokens?.refreshToken
  >     if (refreshToken.isNullOrBlank()) {
  >         authEventBus.emitSessionExpired()   // ← 로그인 화면엔 refresh token이 없다
  >         return@refreshTokens null
  >     }
  > ```
  > `emitSessionExpired()` → `MainViewModel` → `navigator.switchTab(Route.Login)`. **경로가 없을 뿐인데 앱이 "세션 만료"라고 판단하고 전역 이벤트를 쏜다.** 그 뒤 원래 401이 흘러 스낵바에 영문 `"Unauthorized"`가 뜬다.
  >
  > ⚠️ **단, 이 경로가 실제로 발동하는지는 확정되지 않았다.** Ktor `Auth(bearer)`의 refresh 트리거는 서버의 `WWW-Authenticate: Bearer` 챌린지 유무에 영향을 받는데, **실측 결과 현재 서버의 401 응답에는 이 헤더가 없다**(pm-lead 확인). 따라서 refresh 자체가 안 돌 가능성이 있다. **어느 쪽이든 결과는 나쁘다** — 돌면 가짜 세션 만료, 안 돌면 영문 스낵바. 정확한 동작은 T-B1a 적용 전 실기 확인이 필요하나, **해결책(서버가 404를 준다)은 두 경우 모두에 유효**하므로 이 불확실성이 작업을 막지는 않는다.
  >
  > **모바일 단독 방어로는 못 막는다** — repository가 `HttpError.code`를 보고 404·401을 "미지원"으로 처리할 수는 있으나, `emitSessionExpired()`는 **Ktor Auth 플러그인 내부에서 repository보다 먼저** 일어난다. **서버가 404를 주는 것이 유일한 근본 해결이다.**
- [ ] **T-B1a**: `SecurityConfig`에 test-login 경로 **permitAll 추가**. ⚠️ **격리 플래그와 같은 조건으로 묶으면 안 된다** — 플래그 off 시 permitAll도 사라져 다시 401이 되므로 목표(404)를 달성하지 못한다. **경로가 없을 때의 permitAll은 무해하다**(인증 없이 라우팅까지 도달할 뿐이고, 라우트가 없으면 404가 난다). 다만 "나중에 이 경로에 핸들러를 매핑하면 공개된다"는 점을 주석으로 남길 것.
- [ ] **T-B1b**: `GlobalExceptionHandler`에 **404 핸들러 추가** — `NoResourceFoundException` / `NoHandlerFoundException` → **HTTP 404**. 현재는 catch-all이 500으로 삼킨다. **미등록 경로가 500을 주는 건 그 자체로 틀렸다** — 500은 "서버가 고장났다"는 뜻인데 실제로는 "그런 경로가 없다"이다. 부수 효과로 **백로그의 `/actuator/health` 500 건도 해소**된다.
  > 응답 body를 BaseResponse 형태로 줄지는 backend-dev 판단. 단 **모바일은 HTTP 404를 `HttpError`로 받아 `response.status.description`(영문 "Not Found")을 쓰므로 서버가 넣은 body 문구가 무시될 수 있다** — 모바일측 특별 처리가 별도로 필요하다(리스크 항목 참조).
- [ ] **T-B2**: 테스트 로그인 엔드포인트 — 계정 선택자를 받아 upsert 후 실제 로그인과 동일하게 access + refresh 발급(ADR-0009 rotation 포함). `kakao_id 999000001~` 대역 사용. `AuthService`의 기존 발급 경로를 재사용해 **토큰 형태가 갈라지지 않게** 할 것.
- [ ] **T-B3**: 테스트 — 켠 상태 동작 / **끈 상태 부재(404)** / 멱등성 / 발급 토큰으로 기존 API 접근. 회귀 0 확인.

### 모바일 (mobile-dev)

- [x] **T-M1**: ✅ **2026-07-31 완료 — 코드 0줄.** 새 장치가 필요 없다. `:core:utils`에 **`expect val isDebug`가 이미 구현돼 있고**(androidMain → `BuildConfig.DEBUG`, iosMain → `Platform.isDebugBinary`) `ChallengeFeaturePlugin`이 모든 feature 모듈에 `:core:utils`를 자동 주입하므로 `:feature:login`에서 의존성 추가 없이 쓴다. BuildKonfig 플래그 신설 불필요. **working tree 오염 0.**
  > **격리 강도 — 런타임 게이트다** (2026-07-31 mobile-dev 제기 → pm-lead 승인). `isDebug`는 코드가 release APK에 **들어가되 렌더만 안 되는** 수준이다. 컴파일 제외는 KMP common/iOS에서 Android `debug` 소스셋처럼 깔끔하지 않아 비용이 크다. **실질 방어선은 서버의 fail-closed** — release 환경에서는 엔드포인트가 애초에 없어 404다. 모바일 게이트는 defense-in-depth이지 유일한 방어가 아니다. 아래 격리 §3이 두 수준을 허용하므로 이 선택은 기준을 충족한다.
- [ ] **T-M2**: 로그인 화면에 테스트 로그인 진입 + 계정 선택 UI. **기존 카카오 로그인과 동일한 성공 후처리**를 타야 한다(토큰 저장 / 네비게이션 / `UserInfo` 캐시). `LoginViewModel`에 갈래 추가.
- [ ] **T-M3**: `:remote`/`:domain`/`:data` 배선 + 테스트. `LoginViewModelTest` 회귀 0.
- [ ] **T-M4**: **debug 빌드에서만 `HomeTopBar`에 현재 계정 닉네임 노출** (2026-07-31 mobile-dev 제기 → pm-lead 승인, 옵션 나).
  > **🔴 왜 필요한가** — 실측 결과 **지금 앱에는 "내가 누구로 로그인했는지" 알 수 있는 화면이 한 곳도 없다.** `userInfo`는 fetch·캐시까지 되지만 `HomeUiState.Data.userInfo`에 담기만 하고 **렌더되는 곳이 0건**이며 `HomeTopBar`에 닉네임 파라미터가 없다(pm-lead 재확인). 카카오 계정 하나만 쓸 땐 문제가 아니었으나 **이 feature는 계정을 오가는 것이 목적**이라 성격이 다르다.
  > 스낵바만으로는 부족하다 — 몇 초 뒤 사라지는데 실제 사용 흐름은 **로그인 → 친구 요청 → 챌린지 신청 → 수락**으로 몇 분간 이어진다. 중간에 "내가 테스터1이었나 2였나"가 헷갈리면 **손 테스트 결과 자체를 신뢰할 수 없다** — 이 feature가 없애려던 병목이 다른 형태로 남는다.
  > **debug 전용인 이유**: `user-info` feature에서 사용자가 "Home에 `UserInfo` 노출 안 함"을 결정했다. `isDebug` 게이트를 쓰면 **운영 UI는 그대로 두면서** 그 결정과 충돌하지 않는다. 데이터는 이미 `HomeUiState.Data.userInfo`에 와 있어 렌더만 붙이면 된다.
  > **항상 노출(옵션 다)은 채택하지 않는다** — 사용자 결정 번복이라 별도 확인이 필요하다.

## 의존 관계

- T-B2/T-B3, T-M2/T-M3은 `api-contract.md`가 `confirmed`가 된 뒤 착수.
- **T-B1(격리)은 계약과 독립 — 선행 착수.** 여기서 방식이 정해져야 계약에 "이 엔드포인트는 조건부 존재"를 정확히 쓸 수 있다.
- T-M1은 계약과 독립 — 선행 착수 가능.
- **`datetime-model-migration`의 실서버 검증이 끝난 뒤 착수한다.** 지금 서버·모바일 working tree에 두 feature가 이미 섞여 있어 세 번째를 얹으면 회귀 원인 절연이 어려워진다.

## 리스크 / 오픈 이슈

- **🔴 인증 우회 경로 신설** — 위 격리 4항목이 이 feature의 핵심이다. 기능이 되는데 격리가 안 되면 **완료가 아니다.**
- **🔴 꺼진 서버의 404가 사용자에게 영문으로 샌다** (2026-07-31 mobile-dev 발견) — 404는 `ApiResult.Failure.HttpError`가 되고 `suspendOnFailureWithErrorHandling`이 `onError(message)`로 넘기는 `message`는 `ApiResultConverterFactory`가 넣은 **`response.status.description`, 즉 영문 `"Not Found"`**다. 그대로 두면 **스낵바에 "Not Found"가 뜬다.** `challenge-create`에서 "서버 `message`가 곧 UI 텍스트"라고 못박은 것과 같은 함정인데, 이번엔 문자열을 만드는 주체가 **서버가 아니라 Ktor**라 서버측 문구 통제로는 막을 수 없다. → 모바일이 이 엔드포인트에 한해 404를 특별 처리해야 한다. 계약 오픈 이슈 3에서 확정할 것.
- **🟡 ADR-0009 1기기 1세션과의 상호작용** — refresh rotation이 `users.refresh_token_hash`를 덮어쓰므로, 테스트 계정을 오가면 이전 계정의 세션이 무효화된다. 계정 전환 UX가 이 동작과 어긋나지 않는지 확인 필요.
- **🟡 `challenge-create`의 중복 금지 인덱스** — 같은 쌍·같은 날짜에 `PENDING`/`IN_PROGRESS`가 있으면 재신청이 막힌다. 손 테스트 중 "왜 안 되지"로 헤맬 수 있으니 메시지가 그 상황을 정확히 안내하는지 함께 확인.
- **🟢 working tree 3중 누적** — 이미 `challenge-create` + `datetime-model-migration`이 미커밋 상태다. 커밋 분리는 사용자 판단 영역이나, 이 feature까지 얹히면 분리 비용이 더 커진다.
