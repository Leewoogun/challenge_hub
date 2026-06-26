# user-info Implementation Plan

> **For agentic workers:** REQUIRED EXECUTION: **Agent Teams** (Claude Code v2.1.178+ 기준, 사용자 명시). `mobile-dev` agent type 팀원은 코드 편집을 child claude(`cd challenge-app && claude -p`)에 위임 강제 — `mobile-dev.md` "코드 편집 흐름" 섹션 적용.

**Goal:** 인증된 사용자의 본인 정보(id, kakaoId, nickname, profileImageUrl)를 모바일이 백엔드 endpoint로 조회 → DataStore에 캐시 → Home 화면에서 표시. cacheFirst/networkOnly 옵션 지원.

**Architecture:** 백엔드 신규 `GET /api/v1/users/me` (`UserController` + `UserService`, 기존 `UserRepository.findById` 활용). 모바일은 `:remote:api/UserApi` + `:domain:repository/UserInfoRepository` + `:data:repositoryImpl/UserInfoRepositoryImpl` + `:local:datastore/UserInfoLocalDataSource`로 8 모듈 확장. `HomeViewModel`이 `init`에서 `getUserInfo(CACHE_FIRST)` 트리거 + `observeUserInfoCache()` 관찰. 부수 작업: `LoginResult` 평탄화 + `UserProfile.kt` 삭제.

**Tech Stack:** Spring Boot multi-module / Kotlin / Testcontainers (백엔드); Kotlin Multiplatform + Compose Multiplatform + Koin (KSP) + Ktorfit + AndroidX DataStore (모바일).

---

## 참조 문서

- 입력 spec: [spec.md](./spec.md) (commit `33ffe88`)
- 참고 패턴: `/Users/hwamulman/hwamulman-workspace/CarOwnerRenew/data/repositoryImpl/.../UserInfoRepositoryImpl.kt`
- 친구 작업 산출물 (재사용 / 패턴 일관):
  - `:domain:model/friend/FriendsError.kt` — `SilentAuthExpired` object sentinel (import 재사용)
  - `:data:repositoryImpl/.../FriendsRepositoryImpl.kt` — Repository 표준 패턴 baseline
- PM hub 컨벤션: `challenge_hub/CLAUDE.md`
- `mobile-dev.md` 정의 (Agent Teams 페르소나) — 특히 "코드 편집 흐름" 섹션

---

## 메모리 규칙 (Agent Teams 진입 시 prompt에 반드시 포함)

| 규칙 | 적용 |
|---|---|
| **mobile-dev = 옵션 C (child claude 위임 강제)** | 분석/협의는 본체, **모든 Edit/Write/MultiEdit는 `Bash: cd /Users/hwamulman/woogunProject/challenge/challenge-app && claude -p "..."`** 위임. 직접 절대경로 Edit 금지. mobile-dev.md 정의 본문 참조 (자동 시스템 프롬프트 주입). |
| **mobile-dev 모바일 git 금지** | 모바일 repo에 브랜치/커밋/푸시/PR 금지. child claude 안에서도 git 작업 금지. 코드 변경만 working tree. |
| **backend-dev = PM hub cwd 직접 작업 + git OK** | challenge-server에 commit/push 정상 진행. |
| Repository 표준 | `Flow<T>` + `onError: (Throwable) -> Unit` + `AuthEventBus`. 도메인 sealed Result 금지(stdlib `Result` OK). 401은 repository 내부 `AuthEventBus.emitSessionExpired()` + `SilentAuthExpired` sentinel. |
| API 협의 | `SendMessage(backend-dev / mobile-dev)`로 본체 컨텍스트에서. spec에서 거의 합의됨. |

---

## File Structure

### PM hub (`challenge-pm/challenge_hub`)
- Create: `docs/features/user-info/api-contract.md` (T1)
- Create: `docs/features/user-info/backend-report.md` (T2)
- Create: `docs/features/user-info/mobile-report.md` (T3 + T4 종합, T5)
- Create: `docs/features/user-info/summary.md` (T5)
- Modify: `docs/features/INDEX.md` (T5)
- Modify: `docs/backlog.md` (T5 — 후속 작업 등재)

### 백엔드 (`challenge-server`)
- Create: `controller/src/main/kotlin/com/lwg/challenge/controller/user/UserController.kt`
- Create: `controller/src/main/kotlin/com/lwg/challenge/controller/user/dto/UserInfoResponse.kt`
- Create: `service/src/main/kotlin/com/lwg/challenge/service/user/UserService.kt`
- Create: `app/src/test/kotlin/com/lwg/challenge/controller/user/UserControllerTest.kt`
- Create: `app/src/test/kotlin/com/lwg/challenge/integration/UserIntegrationTest.kt`

### 모바일 (`challenge-app`)
- Create: `remote/model/src/commonMain/kotlin/com/lwg/challenge/remote/model/user/UserInfoResponse.kt`
- Create: `remote/api/src/commonMain/kotlin/com/lwg/challenge/remote/api/UserApi.kt`
- Modify: `remote/api/src/commonMain/kotlin/com/lwg/challenge/remote/api/di/ApiModule.kt` (`provideUserApi`)
- Create: `remote/mapper/src/commonMain/kotlin/com/lwg/challenge/remote/mapper/UserInfoMapper.kt`
- Create: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/user/UserInfo.kt`
- Create: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/user/CacheStrategy.kt`
- Create: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/user/UserInfoError.kt` (`UserInfoApiException`, `UserInfoNetworkException`)
- Create: `domain/repository/src/commonMain/kotlin/com/lwg/challenge/domain/repository/UserInfoRepository.kt`
- Create: `data/repositoryImpl/src/commonMain/kotlin/com/lwg/challenge/data/repository/UserInfoRepositoryImpl.kt`
- Create: `local/datastore/src/commonMain/kotlin/com/lwg/challenge/local/datastore/model/UserInfoPrefs.kt`
- Create: `local/datastore/src/commonMain/kotlin/com/lwg/challenge/local/datastore/datasource/UserInfoLocalDataSource.kt`
- Modify: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/LoginResult.kt` (평탄화)
- Delete: `domain/model/src/commonMain/kotlin/com/lwg/challenge/domain/model/UserProfile.kt`
- Modify: `remote/mapper/src/commonMain/kotlin/com/lwg/challenge/remote/mapper/LoginResponseMapper.kt` (평탄화 반영)
- Modify: `feature/login/src/commonMain/kotlin/com/lwg/challenge/feature/login/LoginViewModel.kt:53` (`result.userProfile.isNewUser` → `result.isNewUser`)
- Modify: `feature/login/src/commonTest/kotlin/com/lwg/challenge/feature/login/LoginViewModelTest.kt` (평탄화 반영)
- Modify: `feature/login/src/commonTest/kotlin/com/lwg/challenge/feature/login/FakeLoginRepository.kt` (평탄화 반영)
- Modify: `feature/home/src/commonMain/kotlin/com/lwg/challenge/feature/home/HomeViewModel.kt` (UserInfoRepository 주입 + 트리거 + 캐시 관찰)
- Modify: `feature/home/src/commonMain/kotlin/com/lwg/challenge/feature/home/contract/HomeUiState.kt` (`userInfo: UserInfo?` 필드 추가)
- Modify: `feature/home/src/commonTest/kotlin/com/lwg/challenge/feature/home/HomeViewModelTest.kt` (신규 케이스 + 기존 회귀)
- Create: `feature/home/src/commonTest/kotlin/com/lwg/challenge/feature/home/FakeUserInfoRepository.kt`
- Create: `data/repositoryImpl/src/commonTest/kotlin/com/lwg/challenge/data/repository/UserInfoRepositoryImplTest.kt`

---

## Tasks

### Task 1 — pm-lead: api-contract.md 작성

**담당:** pm-lead (= 메인 세션, 나)

**Files:**
- Create: `challenge_hub/docs/features/user-info/api-contract.md` (status: `confirmed` — spec에서 합의됨)

- [ ] **Step 1: api-contract.md 작성**

내용:
- frontmatter (feature-id, status: confirmed, 최종 수정)
- `GET /api/v1/users/me` endpoint 명세 (method, path, auth, request, response, 에러 코드)
- 응답 DTO 구조 (`UserInfoResponse(data: UserInfoData)`, BaseResponse 패턴)
- 4 필드 (id: Long, kakaoId: Long, nickname: String, profileImageUrl: String?)
- 에러: 401 (Bearer 누락/만료, Ktor Auth 자동 처리)
- 정렬/페이지네이션: 해당 없음
- 협의 이력 (단일 endpoint라 짧음)

- [ ] **Step 2: PM hub commit**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub
git add docs/features/user-info/api-contract.md
git commit -m "docs(user-info): api-contract confirmed (T1)"
```

---

### Task 2 — backend-dev (Agent Teams 팀원): 백엔드 전체

**담당:** backend-dev 팀원 (SendMessage로 작업 지시)

**선행:** T1 완료

**Files (산출물):**
- Create: `controller/user/UserController.kt`
- Create: `controller/user/dto/UserInfoResponse.kt`
- Create: `service/user/UserService.kt`
- Create: `app/src/test/.../controller/user/UserControllerTest.kt`
- Create: `app/src/test/.../integration/UserIntegrationTest.kt`
- Create: `challenge_hub/docs/features/user-info/backend-report.md`

- [ ] **Step 1: SendMessage로 backend-dev에 작업 지시**

prompt (full text):

```
당신은 challenge 프로젝트의 backend-dev 에이전트입니다.

작업: user-info feature의 백엔드 전체 구현 (TDD).

## 시작 전 필수 읽기
1. `/Users/hwamulman/woogunProject/challenge/challenge-server/CLAUDE.md` (있으면)
2. spec: `/Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/user-info/spec.md` (특히 §4 백엔드)
3. api-contract: `/Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/user-info/api-contract.md`
4. 기존 컨트롤러 패턴: `controller/src/main/kotlin/com/lwg/challenge/controller/friend/FriendController.kt` (currentUserId 헬퍼, BaseResponse)
5. 기존 슬라이스 테스트 패턴: `app/src/test/kotlin/com/lwg/challenge/controller/friend/FriendControllerTest.kt`
6. 기존 통합 테스트 패턴: `app/src/test/kotlin/com/lwg/challenge/integration/FriendIntegrationTest.kt`
7. UserRepository.findById는 이미 존재 (auth-refresh-rotation 작업) — 그대로 활용

## 구현 범위
1. UserController (`controller/user/UserController.kt`)
   - `@RestController @RequestMapping("/api/v1/users")`
   - `@GetMapping("/me")` fun getMe + `@AuthenticationPrincipal userId: Long`
   - `currentUserId()` 헬퍼는 FriendController 패턴 그대로 또는 `@AuthenticationPrincipal` 직접 사용
2. UserInfoResponse DTO (`controller/user/dto/UserInfoResponse.kt`)
   - `data class UserInfoResponse(val data: UserInfoData) : BaseResponse()`
   - `data class UserInfoData(val id: Long, val kakaoId: Long, val nickname: String, val profileImageUrl: String?)`
3. UserService (`service/user/UserService.kt`)
   - `fun getMe(me: Long): User = userRepository.findById(me) ?: throw UnauthorizedException("user not found")`

## TDD 진행
1. 통합 테스트 먼저 (RED) → 구현 (GREEN)
2. 슬라이스 테스트도 함께

## 통합 테스트 시나리오 (UserIntegrationTest, 4건)
1. 정상 응답 — 4 필드 모두 반환
2. 미인증 (401)
3. 토큰의 userId가 DB에 없음 (401)
4. profile_image_url null 사용자 (응답에 null)

## 슬라이스 테스트 (UserControllerTest, 2건)
1. 성공 응답 (200 + 4 필드)
2. UnauthorizedException → 401

## 검증
- ./gradlew :app:test --tests "com.lwg.challenge.controller.user.*"
- ./gradlew :app:test --tests "com.lwg.challenge.integration.UserIntegrationTest"
- ./gradlew build

## 보고 산출물
- challenge-server commit + push
- `challenge_hub/docs/features/user-info/backend-report.md` 작성 (구현 endpoint + 매핑 클래스 + 테스트 결과 X/Y + 알려진 한계)
- PM hub commit: `docs(user-info): backend-report.md (T2)`

## git
- challenge-server git commit + push OK (backend-dev 표준 흐름)
- PM hub git commit OK

## Self-Review 체크리스트
- [ ] UserController @GetMapping("/me") + currentUserId 추출
- [ ] UserService.getMe Optional null 처리
- [ ] UserInfoResponse extends BaseResponse + 4 필드
- [ ] 슬라이스 2/2 + 통합 4/4 (Docker 가용 시) PASS
- [ ] V1 스키마 그대로 (마이그레이션 추가 없음)

완료 후 SendMessage로 pm-lead(=리더)에게 보고: commit SHA + 테스트 결과 + 알려진 한계.
```

- [ ] **Step 2: backend-dev 완료 보고 대기 + 검토**

리더(나)가 결과 검토. 빌드/테스트 결과 + commit SHA 확인.

---

### Task 3 — mobile-dev (Agent Teams 팀원): 모바일 도메인/Data + LoginResult 평탄화

**담당:** mobile-dev 팀원 (코드 편집은 child claude 위임 — 옵션 C 강제)

**선행:** T1 완료 (api-contract 참조). T2와 병렬 가능.

**Files (산출물):**
- Create: `:remote:model/user/UserInfoResponse.kt`
- Create: `:remote:api/UserApi.kt` + `ApiModule.provideUserApi` 추가
- Create: `:remote:mapper/UserInfoMapper.kt`
- Create: `:domain:model/user/UserInfo.kt`, `CacheStrategy.kt`, `UserInfoError.kt`
- Create: `:domain:repository/UserInfoRepository.kt`
- Create: `:data:repositoryImpl/.../UserInfoRepositoryImpl.kt`
- Create: `:local:datastore/datasource/UserInfoLocalDataSource.kt` + `model/UserInfoPrefs.kt`
- Create: `:data:repositoryImpl/src/commonTest/.../UserInfoRepositoryImplTest.kt`
- Modify: `:domain:model/LoginResult.kt` (평탄화), 삭제 `UserProfile.kt`, `LoginResponseMapper.kt`, `LoginViewModel.kt:53`, `LoginViewModelTest.kt`, `FakeLoginRepository.kt`

- [ ] **Step 1: SendMessage로 mobile-dev에 작업 지시**

prompt (full text):

```
당신은 challenge 프로젝트의 mobile-dev 에이전트입니다. 페르소나/규칙은 `mobile-dev.md` 정의 그대로.

작업: user-info feature의 모바일 도메인 + Data 레이어 + LoginResult 평탄화.

## ⚠️ 코드 편집 흐름 — 옵션 C (필수)
당신의 cwd는 PM hub. 모든 코드 파일 Edit/Write는 다음 흐름으로 위임:

bash:
cd /Users/hwamulman/woogunProject/challenge/challenge-app && claude -p "<상세 prompt>"

분석/조회/spec read는 본체에서 직접 OK. **Edit/Write/MultiEdit 도구 직접 호출 금지** (cwd가 PM hub인 한 컨벤션 자동 발화 X).

## 시작 전 필수 읽기 (본체에서)
1. spec: `/Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/user-info/spec.md` (§5 모바일)
2. api-contract: `/Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/user-info/api-contract.md`
3. CarOwnerRenew 참조: `/Users/hwamulman/hwamulman-workspace/CarOwnerRenew/data/repositoryImpl/src/main/kotlin/ktc/cargo/driver/data/repositoryImpl/UserInfoRepositoryImpl.kt`
4. 친구 작업 패턴 참조 (FriendsRepositoryImpl + FriendsError.kt) — 절대경로 cat 가능

## 구현 범위
A. 도메인 모델 + Repository 인터페이스
   - `:domain:model/user/UserInfo.kt`: `data class UserInfo(id, kakaoId, nickname, profileImageUrl?)`
   - `:domain:model/user/CacheStrategy.kt`: `enum class CacheStrategy { CACHE_FIRST, NETWORK_ONLY }`
   - `:domain:model/user/UserInfoError.kt`: `UserInfoApiException(code, message)`, `UserInfoNetworkException(message)`
   - `:domain:repository/UserInfoRepository.kt`: 인터페이스 (spec 5.3 그대로)

B. Remote 레이어
   - `:remote:model/user/UserInfoResponse.kt`: envelope + UserInfoData
   - `:remote:api/UserApi.kt`: Ktorfit, `@GET("api/v1/users/me") suspend fun getMe(): ApiResult<UserInfoResponse>`
   - `:remote:api/di/ApiModule.kt`: `provideUserApi` 추가
   - `:remote:mapper/UserInfoMapper.kt`: DTO → Domain

C. Local 레이어
   - `:local:datastore/model/UserInfoPrefs.kt`: `@Serializable data class UserInfoPrefs(id, kakaoId, nickname, profileImageUrl?, hasValue=false)`
   - `:local:datastore/datasource/UserInfoLocalDataSource.kt`: `@Single`, `createDataStore(serializer, defaultValue, fileName="user_info")`, 4 메서드 (observeUserInfo, getUserInfo, saveUserInfo, clear)

D. RepositoryImpl
   - `:data:repositoryImpl/.../UserInfoRepositoryImpl.kt`: `@Single(binds=[UserInfoRepository::class])`
   - getUserInfo 분기 (CACHE_FIRST / NETWORK_ONLY)
   - 401 처리: `AuthEventBus.emitSessionExpired()` + `SilentAuthExpired` import (`:domain:model/friend/FriendsError.kt`에서 재사용)
   - `Throwable` 시그니처로 정규화: `UserInfoApiException` (code 700/기타) / `UserInfoNetworkException` / `SilentAuthExpired`

E. LoginResult 평탄화
   - `:domain:model/LoginResult.kt`: `data class LoginResult(accessToken, refreshToken, userId: Long, isNewUser: Boolean)` (UserProfile 제거)
   - `:domain:model/UserProfile.kt`: 삭제
   - `:remote:mapper/LoginResponseMapper.kt`: 평탄화 매핑
   - `feature/login/.../LoginViewModel.kt:53`: `result.userProfile.isNewUser` → `result.isNewUser`
   - `feature/login/.../LoginViewModelTest.kt`: `UserProfile(...)` 제거 + 평탄화
   - `feature/login/.../FakeLoginRepository.kt`: 동일

F. 캐시 클리어 흐름 통합 (spec §5.8)
   - `LogoutUseCase` 또는 토큰 클리어 흐름의 존재 여부 점검:
     - 있으면: 그 흐름 끝에 `userInfoRepository.clearUserInfoCache()` 호출 추가
     - 없으면: `feature/main/.../MainScreen.kt`의 `AuthEventBus.sessionExpired` collect 직후에 `clearUserInfoCache()` 호출 추가 (별도 ViewModel 통한 호출 가능)
   - mobile-dev가 grep으로 logout/clear 관련 진입점 확인 후 적절한 위치 결정

G. UserInfoRepositoryImplTest (TDD, 5 케이스)
   1. CACHE_FIRST + 캐시 있음 → API 호출 0건, 캐시값 emit
   2. CACHE_FIRST + 캐시 없음 → API 호출 + local 저장 + emit
   3. NETWORK_ONLY → 캐시 무관하게 API 호출 + 저장 + emit
   4. 401 (code 401 응답) → AuthEventBus.emitSessionExpired() 호출 + Result.failure(SilentAuthExpired)
   5. clearUserInfoCache → local 비워짐 + observeUserInfoCache가 null emit

## 빌드 검증 (child claude 안에서)
- ./gradlew :remote:model:compileCommonMainKotlinMetadata
- ./gradlew :remote:api:compileCommonMainKotlinMetadata
- ./gradlew :remote:mapper:compileCommonMainKotlinMetadata
- ./gradlew :domain:model:compileCommonMainKotlinMetadata
- ./gradlew :domain:repository:compileCommonMainKotlinMetadata
- ./gradlew :data:repositoryImpl:compileCommonMainKotlinMetadata
- ./gradlew :local:datastore:compileCommonMainKotlinMetadata
- ./gradlew :feature:login:compileCommonMainKotlinMetadata (LoginResult 평탄화 회귀)
- ./gradlew :data:repositoryImpl:testDebugUnitTest (UserInfoRepositoryImplTest 5/5)
- ./gradlew :feature:login:testDebugUnitTest (LoginViewModelTest 4/4 회귀)

모두 SUCCESS + 모든 테스트 PASS.

## git (필수)
- challenge-app repo에 git 작업 0건 (브랜치/커밋/푸시/PR 모두 X)
- 코드 변경만 working tree에 두고 보고

## Self-Review
- [ ] 8 모듈 빌드 SUCCESS
- [ ] UserInfoRepositoryImplTest 5/5 PASS
- [ ] LoginViewModelTest 4/4 PASS (회귀 0)
- [ ] UserProfile.kt 삭제 확인 (`git status`로 deleted)
- [ ] LoginResult 평탄화 (userId, isNewUser 직접 필드)
- [ ] git: branch/commit/push/PR 0건

## 보고
- 변경 / 신규 / 삭제 파일 목록 (절대 경로)
- 빌드 결과 (모듈별)
- 테스트 결과 (X/Y PASS)
- 알려진 제약 / 후속

SendMessage로 pm-lead(=리더)에게 보고.
```

- [ ] **Step 2: mobile-dev 완료 보고 대기 + 검토**

---

### Task 4 — mobile-dev (Agent Teams 팀원): HomeViewModel 통합 + 테스트

**담당:** mobile-dev 팀원 (옵션 C)

**선행:** T3 완료 (UserInfoRepository 존재 필요)

**Files:**
- Modify: `:feature:home/.../HomeViewModel.kt`
- Modify: `:feature:home/.../contract/HomeUiState.kt` (`userInfo: UserInfo?` 필드)
- Modify: `:feature:home/src/commonTest/.../HomeViewModelTest.kt` (신규 케이스 + 회귀)
- Create: `:feature:home/src/commonTest/.../FakeUserInfoRepository.kt`

- [ ] **Step 1: SendMessage로 mobile-dev에 작업 지시**

prompt (full text):

```
당신은 mobile-dev 에이전트입니다. 코드 편집은 옵션 C (child claude 위임) 강제.

작업: user-info — HomeViewModel 통합 + 캐시 관찰 + 테스트.

## 시작 전 필수 읽기 (본체)
1. spec §5.6 HomeViewModel 통합
2. 기존 HomeViewModel + HomeViewModelTest (특히 회귀 0 보장)
3. T3에서 만든 UserInfoRepository 인터페이스

## 구현 범위 (TDD)
A. HomeViewModelTest 확장 (RED → GREEN)
   - 신규 케이스 3건:
     a. 캐시 있는 상태 → init 시 즉시 userInfo 노출 (관찰)
     b. 캐시 없는 상태 → init 트리거가 fetch + 캐시 저장 + 관찰로 노출
     c. 401 SilentAuthExpired → ShowMessage 안 보냄 (skip)
   - 기존 6 케이스 회귀 0 (assertion 그대로)

B. FakeUserInfoRepository (commonTest)
   - StateFlow 백킹 (캐시값), getUserInfo Result 주입 가능
   - observeUserInfoCache는 StateFlow.map { ... } 형태

C. HomeUiState.Data 확장
   - `userInfo: UserInfo?` 필드 추가
   - 기존 필드(stats, challenges, emptyType) 유지

D. HomeViewModel 수정
   - 생성자에 `UserInfoRepository` 주입 추가
   - init에서 다음 두 launch:
     1. `userInfoRepository.getUserInfo(onError = ::showMessage, cacheStrategy = CACHE_FIRST).collect { }` — 트리거 (fetch + local 저장)
     2. `userInfoRepository.observeUserInfoCache()` collect → `_userInfo` MutableStateFlow 갱신
   - 기존 stats/challenges combine에 `_userInfo` 추가 → Data에 합쳐서 emit
   - SilentAuthExpired는 showMessage 안 보냄 (기존 emitErrorIfNotSilent 패턴)

## 빌드 검증
- ./gradlew :feature:home:compileCommonMainKotlinMetadata
- ./gradlew :feature:home:compileDebugKotlinAndroid
- ./gradlew :feature:home:testDebugUnitTest (HomeViewModelTest 9+/9+ PASS)

## git: branch/commit/push 0건

## 보고
- 변경/신규 파일 목록
- 테스트 결과 (기존 6 + 신규 3 = 9 PASS)
- 회귀 0 명시
```

- [ ] **Step 2: mobile-dev 완료 보고 대기 + 검토**

---

### Task 5 — pm-lead: 통합 검증 + report-and-document

**담당:** pm-lead (메인 세션)

**선행:** T2 + T4 완료

**Files:**
- Create: `docs/features/user-info/mobile-report.md` (T3 + T4 종합)
- Create: `docs/features/user-info/summary.md`
- Modify: `docs/features/INDEX.md`
- Modify: `docs/backlog.md` (후속 작업 등재)

- [ ] **Step 1: T3 + T4 보고 종합 → mobile-report.md 작성**

내용:
- 변경 / 신규 / 삭제 파일 (모듈별)
- 테스트 결과 (UserInfoRepositoryImplTest 5/5, LoginViewModelTest 4/4 회귀 0, HomeViewModelTest 9+/9+)
- LoginResult 평탄화 결과 (UserProfile 삭제 확인)
- 알려진 제약

- [ ] **Step 2: summary.md 작성**

내용:
- feature-id: user-info / 완료일 / 상태: completed
- 구현 개요 (백엔드 1 endpoint + 모바일 8 모듈 + LoginResult 평탄화)
- 엔드포인트 표
- 테스트 결과 숫자
- 결정 사항 (cacheFirst 디폴트 / 만료 정책 없음 / SilentAuthExpired 재사용)
- 미해결 / 후속

- [ ] **Step 3: INDEX.md 갱신**

`user-info` 행 추가 (status: completed, 완료일).

- [ ] **Step 4: backlog.md 후속 작업 등재**

- [ ] 내 프로필 화면 (UserInfo 활용)
- [ ] 닉네임/프사 명시적 갱신 (pull-to-refresh)
- [ ] `SilentAuthExpired` 공통 위치(`:domain:model/auth/`) 이동 cleanup
- [ ] 친구 추가 시 본인 user code 표시 (현재 spec엔 user_code 없음, 후속 검토)

- [ ] **Step 5: PM hub commit**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub
git add docs/features/user-info/mobile-report.md \
        docs/features/user-info/summary.md \
        docs/features/INDEX.md \
        docs/backlog.md
git commit -m "docs(user-info): 구현 완료 + summary (T5)"
```

- [ ] **Step 6: 사용자 보고 + manual smoke 안내**

manual smoke 시나리오 (사용자 디바이스):
1. 신규 가입 → Home 진입 → 닉네임/프사 표시
2. 앱 재시작 (자동 로그인) → Home 진입 → 캐시에서 즉시 닉네임/프사 표시
3. 로그아웃 → 캐시 비워졌는지 (재로그인 후 fetch)

PM hub push 결정도 사용자에게.

---

## 후속 작업 (본 plan 범위 외)

- 내 프로필 화면 (UserInfo 활용)
- 닉네임/프사 명시적 갱신 (pull-to-refresh)
- `SilentAuthExpired` 공통 위치 이동
- 친구 추가 시 본인 user_code (현재 spec에 컬럼 없음)
