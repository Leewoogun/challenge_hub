# Change Log — dev-test-login

## 2026-08-03

- **`e2e-on.sh` 34/34 PASS** — 켠 상태 실서버 검증 완료. `backend-report.md`에 반영.
- **`/actuator/health` 500 → 404 확인** — T-B1b의 부수 효과로 백로그 항목 해소.
- **사용자 실사용 검증** — 테스트 계정으로 친구 요청→수락 성공(`friendships` 1건 `ACCEPTED`). 챌린지 플로우는 사용자 확인 완료이나 DB에 `challenges` row 0건이라 수락 경로의 DB 증거는 없음(취소가 물리 삭제라 "신청→취소"만 돌았다면 정상).
- **상태를 `partially-completed`로 마감** — 꺼진 상태 실서버 검증이 미완이라 `completed`로 올리지 않는다.

## 2026-07-31

### 🔴 pm-lead 수용 기준이 틀렸다 — "꺼진 상태 = 404"가 성립하지 않았다

spec 초안은 *"호출 시 404이고 `/v3/api-docs`에도 없다"*로 썼으나 실측:
```
POST /api/v1/auth/test-login   → 401   ← 404 아님
POST /api/v1/auth/nonexistent  → 401   ← 경로 존재 여부와 무관
GET  /actuator/health          → 500   ← permitAll인데 핸들러 없음
```
`SecurityConfig`의 permitAll 목록에 없는 경로는 **라우팅에 닿기 전에 Security가 401로 끊는다.**

**401이 단순 오차가 아닌 이유** (mobile-dev 코드 실측): `KtorfitModule.kt:67-72`에서 refresh token이 없으면 `emitSessionExpired()`가 발화 → `MainViewModel` → `switchTab(Route.Login)`. **경로가 없을 뿐인데 앱이 "세션 만료"라고 판단하고 전역 이벤트를 쏜다.** 구별 불가 정도가 아니라 **적극적으로 틀린 결론**이다. 그리고 `emitSessionExpired()`는 Ktor 플러그인 내부에서 repository보다 먼저 일어나므로 **모바일 방어로는 못 막는다.**

> ⚠️ 이 경로의 실제 발동 여부는 확정되지 않았다 — 서버 401에 `WWW-Authenticate` 헤더가 없어 refresh가 안 돌 수도 있다(pm-lead 실측). **어느 쪽이든 나쁘고**(돌면 가짜 세션 만료, 안 돌면 영문 스낵바) 해결책은 두 경우 모두에 유효하다.

→ **T-B1a**(permitAll 상시) + **T-B1b**(404 핸들러) 2건 추가.

### 🔴 backend-dev의 T-B1a 제안이 목표를 무너뜨렸다 (pm-lead 정정)

제안은 *"permitAll을 격리 플래그와 **같은 조건**으로 묶어 fail-closed 유지"*였는데, 그러면 **플래그 off 시 permitAll도 사라져 다시 401**이 된다.

backend-dev 자기 진단: *"fail-closed라는 원칙을 기계적으로 적용하다가 **그 조치가 실제로 만드는 결과를 확인하지 않았다.**"*

→ **permitAll 상시, 빈만 조건부.** **실제 노출을 막는 건 permitAll이 아니라 빈이 존재하지 않는다는 사실이다.**

### 🔴 격리 방식이 `@ConditionalOnProperty` → 커스텀 `Condition`으로 (결정 불변, 수단 변경)

1. `:service`에 `spring-boot-autoconfigure`가 없어 컴파일 실패. 어노테이션 하나 때문에 모듈 의존성을 늘리는 대신 `:core`에 `Condition`을 두고 **`:service`/`:controller`가 같은 정의를 공유**하게 했다.
2. **더 중요한 발견 — `getProperty(name, Boolean::class, false)`는 오타에 서버를 죽인다.**
   ```
   "true"/"1"/"yes"/"on"  → true
   "enabled" / ""         → ConversionFailedException  ← 던진다
   ```
   `challenge.dev.test-login.enabled=enable` 오타 하나로 애플리케이션이 기동 중 죽는다. **fail-closed는 "안 열린다"여야지 "터진다"가 아니다.** → 문자열 `"true"` 정확 비교. `"1"`/`"yes"`/`"on"`을 잃지만 **보안 경계에서는 켜는 방법이 하나뿐인 편이 낫다.**
   > **테스트가 실패해서 발견했다.** 원래 단언이 틀렸음을 확인하다가 진짜 문제를 찾았다 — 단언을 고쳐 통과시켰으면 묻혔을 건이다.

### 계약 초안의 사실 오류 2건 (pm-lead 책임)

1. **`nickname` 필드가 실재하지 않았다** — 실제 `LoginData`는 4필드(`accessToken`/`refreshToken`/`userId`/`isNewUser`). mobile-dev가 이를 실재하는 필드로 읽고 성공 스낵바 안을 세웠다가 무너졌다. → **추정을 실제처럼 적으면 읽는 쪽이 그 위에 설계를 쌓는다.** 이후 초안에는 확인 안 된 필드를 쓰지 않기로 했다.
2. **"홈에 들어가면 어차피 누구인지 보인다"가 사실이 아니었다** — pm-lead와 backend-dev가 공유한 전제였는데, mobile-dev가 grep으로 깼다. `userInfo`는 `HomeUiState`에 담기만 하고 **렌더되는 곳이 0건**이며 `HomeTopBar`에 닉네임 파라미터가 없다(`user-info`의 "Home에 노출 안 함" 결정이 그대로 남아 있었다).
   → **T-M4 추가**: debug 빌드에서만 `HomeTopBar`에 닉네임 노출. 계정을 오가는 게 목적인 feature에서 "지금 누구인지"가 몇 분간 안 보이면 **손 검증 결과 자체를 신뢰할 수 없다.** `isDebug` 게이트라 사용자의 운영 UI 결정과 충돌하지 않는다.

### mobile-dev의 자기 정정 — `clearTokens()`

계약에 *"`clearTokens()`가 이미 `userInfoLocalDataSource.clear()`까지 수행한다"*고 적혔으나 **사실이 아니었다.** 실제로는 토큰 + `authTokenCacheInvalidator`만 건드린다. `user-info/mobile-report.md`에 "추가했다"고 적혀 있어 그걸 근거로 말한 것.

> *"리포트를 믿고 코드를 확인하지 않은 게 원인이다."* → 이후 **모바일 코드에 관한 진술은 리포트가 아니라 현재 코드를 보고** 하기로 했다. PM 레포 리포트는 작성 시점의 스냅샷이고 코드는 그 뒤로 움직인다.

→ 실제 주체는 `LogoutUseCase`. `LoginWithTestAccountUseCase` 안에서 호출해 **ViewModel이 잊을 수 없게** 했다.

### 범위 밖 변경 승인 — `TokenLocalDataSource` interface 분리

이게 없으면 `LoginRepositoryImpl` 테스트를 **한 건도 쓸 수 없다**(final concrete + 생성자에서 `createDataStore` 즉시 실행). `user-info` 출처의 backlog 항목 *"테스트 추가 시 interface 분리"*의 조건이 충족된 것이라 임의 확장이 아니다. `UserInfoLocalDataSource` 패턴 답습, 사용처 2곳은 타입명 유지로 무변경.

### T-M1이 코드 0줄로 끝났다

`:core:utils`에 `expect val isDebug`가 **이미 있었다**(androidMain `BuildConfig.DEBUG` / iosMain `Platform.isDebugBinary`). `ChallengeFeaturePlugin`이 `:core:utils`를 자동 주입하므로 의존성 추가도 불필요. pm-lead 지시("BuildKonfig 플래그 등")대로 만들었으면 **같은 일을 하는 장치를 둘로 늘릴 뻔했다.**
