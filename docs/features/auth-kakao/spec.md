# 카카오 로그인 (auth-kakao)

- **feature-id**: auth-kakao
- **owner**: pm-lead
- **상태**: draft
- **생성**: 2026-04-24
- **관련 ADR**: 0002 (foundation/BaseResponse), 0007 (환경 분리), 0008 (전화번호 등록)

## 배경 / 문제

Sprint 0 `foundation`에서 `/api/v1/auth/kakao`는 "Kakao access_token이 비어있지 않으면 고정 userId=1로 JWT 발급"하는 **스텁**으로 머물러 있다. 실제 사용자를 식별·저장하지 않으므로 이후 어떤 기능(친구 등록, 챌린지 생성 등)도 시작할 수 없다.

이번 기능은 스텁을 **실제 Kakao OAuth 연동**으로 교체한다:
1. 모바일이 Kakao SDK로 획득한 access_token을 서버에 전달한다.
2. 서버가 Kakao `/v2/user/me`로 토큰을 검증하고 사용자 정보(kakao_id, nickname, profile_image_url, phone_number)를 받는다.
3. 서버는 users 테이블에 upsert하고, 전화번호는 SHA-256 해시로 저장한다 (ADR-0008).
4. 서버는 자체 JWT(access + refresh)를 발급한다.
5. 모바일은 토큰을 플랫폼 보안 저장소(Android Keystore / iOS Keychain)에 저장하고, 앱 재진입 시 자동 로그인을 시도한다.

## 사용자 시나리오

1. **신규 사용자** → 앱 첫 실행 → 로그인 화면 → "카카오로 시작하기" 버튼 → Kakao SDK 로그인 → 서버에 token 전달 → users 새 레코드 생성(`isNewUser=true`) → JWT 수신 → 홈 화면.
2. **기존 사용자** → 앱 첫 실행 → 저장된 refresh token 존재 → `/api/v1/auth/refresh` 호출 → 새 access token 수신 → 홈 화면 (로그인 화면 스킵).
3. **기존 사용자, refresh 만료** → 로그인 화면 노출 → 카카오로 재로그인 → users 레코드 업데이트(`isNewUser=false`) → JWT 재수신.
4. **토큰 검증 실패** → 서버가 `code=701` (다이얼로그) 응답 → 모바일이 "카카오 로그인이 만료되었습니다. 다시 시도해주세요" 다이얼로그 → 로그인 화면 유지.
5. **Kakao 동의 철회 (phone_number scope 거부)** → 서버는 phone_number 없이 users 생성, `phone_verified=false` → 로그인은 성공하지만 친구 매칭 화면에서 전화번호 재동의 플로우(별도 기능, 이번 범위 밖).

## 수용 기준 (Acceptance Criteria)

### 서버
- [ ] `POST /api/v1/auth/kakao` 가 Kakao `/v2/user/me`를 실제 호출하여 토큰을 검증한다 (유효하지 않으면 `code=701`).
- [ ] 신규 kakao_id면 users INSERT, 기존이면 UPDATE (nickname, profile_image_url, phone 해시) — 단일 트랜잭션.
- [ ] phone_number는 `SHA-256(kakao_account.phone_number 정규화)` 후 hex 문자열로 저장. 정규화 규칙: `+82-10-1234-5678` 같은 Kakao 원본 → `+821012345678` (공백/하이픈 제거, E.164 유지).
- [ ] phone_number 존재 시 `phone_verified=true`, 없으면 `false`.
- [ ] 응답에 `isNewUser` (신규=true) + `accessToken` + `refreshToken` + `userId` 포함.
- [ ] Kakao 호출 실패(5xx/타임아웃)는 재시도 1회 후 실패 시 `code=703`(전체화면 에러).
- [ ] 같은 kakao_id 동시 요청 시 중복 INSERT 없음 (UNIQUE 제약 + ON CONFLICT 사용).
- [ ] WebClient 타임아웃: connect 2s, read 5s.
- [ ] 통합 테스트: WireMock으로 Kakao 응답 스텁 — 신규/기존/phone 누락/토큰 만료 4케이스 각각 검증.

### 모바일
- [ ] `:feature:auth` 모듈 생성, `LoginScreen` + `LoginViewModel` 구현.
- [ ] Kakao SDK(Android: `v2-user`, iOS: `KakaoSDKUser`)로 access_token 획득 → `ChallengeApi.kakaoLogin(request)` 호출.
- [ ] 성공 시 access/refresh token을 `SecureTokenStorage` (expect/actual, Android: EncryptedSharedPreferences, iOS: Keychain)에 저장.
- [ ] `isNewUser=true`면 온보딩 화면(후속 feature), `false`면 홈 화면으로 네비게이션.
- [ ] 앱 첫 진입 시 `SplashViewModel`이 저장된 refresh token 존재 → `/auth/refresh` 시도 → 성공 시 홈, 실패 시 로그인 화면.
- [ ] 서버 에러 code별 처리: 700 스낵바, 701 다이얼로그, 703 전체화면 에러 (기존 `ApiResultCall` 분기에 위임).
- [ ] API base URL을 `buildkonfig`의 `CHALLENGE_API_BASE_URL`로 교체 (TMDB 제거) — ADR-0003 잔여 항목 동시 처리.

### 디자인
- [ ] Lovable `src/routes/login.tsx`에서 배경 그라데이션, 로고, "카카오로 시작하기" 버튼 스타일, 다크 테마 토큰을 추출하여 `design.md`에 정리.

## 비범위 (Out of Scope)

- **로그아웃 구현**: `/api/v1/auth/logout`의 실제 blacklist 로직. 현재 스텁 유지. (Sprint 2 `auth-logout`에서 처리)
- **회원 탈퇴**: 별도 기능.
- **온보딩 화면**: `isNewUser=true` 시 이동할 화면은 placeholder (홈 화면으로 임시 이동). 별도 `onboarding` feature에서 구현.
- **전화번호부 동기화**: `/friends/sync-contacts` 엔드포인트는 이번 범위 밖. 이번 기능은 "서버에 phone 해시가 저장되는 것까지"만.
- **FCM 토큰 등록**: 별도 feature `push-fcm`. 이번 기능에서는 users.fcm_token을 건드리지 않는다.
- **Refresh Token Rotation**: 현재는 기존 refresh 재사용. 보안 강화는 ADR-0009(예정).
- **웹 로그인**: Lovable React 앱은 참조 전용 (ADR-0004). 웹용 OAuth 콜백은 없음.
- **이메일/소셜 다양화**: 카카오 단일. 애플/구글 로그인 없음.

## 태스크 분해

### 백엔드 (backend-dev)
- [ ] T-B1: `domain` 모듈에 `User` 엔티티 + `UserRepository` (JPA) 정의
- [ ] T-B2: `infra` 모듈에 `KakaoOAuthClient` (Spring WebClient) 작성 — `/v2/user/me` 호출, Kakao 응답 DTO 매핑
- [ ] T-B3: `api` 모듈에 `AuthService` 작성 — Kakao 응답 검증 → phone 해시 → users upsert → JWT 발급
- [ ] T-B4: `AuthController.kakaoLogin` 스텁 제거하고 `AuthService` 위임으로 교체
- [ ] T-B5: `application.yml`에 Kakao 설정 추가 (`kakao.base-url`, WebClient 타임아웃) — 실제 키는 환경변수 없음(Kakao 서버 검증이므로 서버 secret 불필요)
- [ ] T-B6: 통합 테스트 (`@SpringBootTest` + WireMock): 4 케이스 (신규/기존/phone_없음/토큰_무효)
- [ ] T-B7: `AuthControllerTest` 수정 (Service mock로 교체)
- [ ] T-B8: `backend-report.md` 작성

### 모바일 (mobile-dev)
- [ ] T-M1: API base URL 교체 — `remote/network/build.gradle.kts` buildkonfig + `local.properties` (`CHALLENGE_API_BASE_URL=http://10.0.2.2:8080` for Android emulator, `http://localhost:8080` for iOS sim)
- [ ] T-M2: `:remote:model`에 `BaseResponse` (없으면 생성) + `KakaoLoginRequest` / `LoginData` / `LoginResponse` / `RefreshRequest` / `RefreshData` / `RefreshResponse` DTO
- [ ] T-M3: `:remote:api`에 `AuthApi` Ktorfit 인터페이스 (`@POST("api/v1/auth/kakao")`, `@POST("api/v1/auth/refresh")`)
- [ ] T-M4: `:domain:model`에 `AuthTokens`, `UserProfile` + `:domain:repository`에 `AuthRepository` + `:domain:usecase`에 `LoginWithKakaoUseCase`, `RefreshAccessTokenUseCase`, `GetStoredTokensUseCase`
- [ ] T-M5: `:data:repositoryImpl`에 `AuthRepositoryImpl` + `SecureTokenStorage` expect/actual (Android: EncryptedSharedPreferences, iOS: KeyChain wrapper)
- [ ] T-M6: `:feature:auth` 모듈 생성 — `LoginScreen` (버튼 1개, 카카오 브랜드 컬러), `LoginViewModel` (StateFlow), Kakao SDK 호출 래퍼 (expect/actual)
- [ ] T-M7: `:feature:splash` — 저장된 refresh 확인 → 홈 or 로그인 분기
- [ ] T-M8: `core:navigation`에 `AuthRoute.Login`, `SplashRoute` 추가 + `:feature:main` NavDisplay 연결
- [ ] T-M9: Kakao SDK 의존성 추가 (`android`: `com.kakao.sdk:v2-user`, `ios`: cocoapods 혹은 SPM `KakaoSDKUser`) + Android manifest의 KakaoScheme / iOS URL Schemes
- [ ] T-M10: 통합 테스트 — ViewModel 단위 테스트 (`test-viewmodel` skill), Repository fake 기반 UseCase 테스트
- [ ] T-M11: `mobile-report.md` 작성

### 디자인 (design-bridge)
- [ ] T-D1: `src/routes/login.tsx` + 관련 컴포넌트 분석 → `design.md`에 정리
- [ ] T-D2: 색상 토큰(다크 배경, 카카오 옐로우), 타이포, 버튼 스타일, 그라데이션 위치 명시
- [ ] T-D3: 로고 이미지 경로 혹은 SVG source 위치 안내

## 의존 관계

- T-B2 ∥ T-M1 ∥ T-D1 (독립, 병렬 가능) — API 계약 확정 직후 바로 착수
- **모든 구현 태스크는 `api-contract.md` 상태가 `confirmed`가 된 뒤 착수.**
- T-B3 ← T-B1, T-B2
- T-B4 ← T-B3
- T-B6 ← T-B4
- T-M3 ← T-M2 (DTO → API)
- T-M4 ← T-M3
- T-M5 ← T-M4
- T-M6 ← T-M5, T-D1 (디자인 토큰 반영)
- T-M7 ← T-M5
- T-M8 ← T-M6, T-M7
- 통합 검증: T-B6 완료 + T-M10 완료 ← 서버 로컬 기동 후 모바일에서 실제 카카오 로그인 시도 (수동 smoke test)

## 리스크 / 오픈 이슈

- **Kakao `account_phone_number` scope 승인**: Kakao 개발자 콘솔에서 scope 사용 권한을 신청·승인받아야 한다. 사용자 action 필요. 승인 전에는 로컬 테스트에서 phone 필드가 비어서 오므로 `phone_verified=false` 케이스만 검증 가능.
- **Android emulator vs iOS sim의 base URL 차이**: Android는 `10.0.2.2`, iOS는 `localhost`. `buildkonfig`에서 플랫폼 분기 또는 공통 설정 후 플랫폼별 오버라이드 중 하나. T-M1에서 결정.
- **Kakao SDK KMP 연동 난이도**: iOS는 CocoaPods vs SPM 선택, Android는 키해시 등록 필요. design-bridge는 이 부분 모르므로 mobile-dev가 단독 결정.
- **WebClient 의존성**: `challenge-server`는 `spring-boot-starter-web` (tomcat)만 설치되어 있고 WebClient가 포함된 `spring-boot-starter-webflux`는 없음. `implementation("org.springframework:spring-webflux")`만 추가하면 WebClient는 사용 가능(Netty 없이). backend-dev가 추가.
- **Kakao 응답 shape 변동 가능성**: phone_number는 `kakao_account.phone_number`에 있지만 동의 여부(`phone_number_needs_agreement`)도 함께 봐야 한다. 계약 협의 단계에서 명확히.
- **JWT Secret 관리**: 현재 `${JWT_SECRET}` 환경변수 필수. 로컬 개발 문서화 필요 — T-B8에서 README 업데이트 포함.
