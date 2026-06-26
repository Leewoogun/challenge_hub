# user-info feature spec

> 백엔드의 user 테이블 row를 모바일이 조회 → DataStore에 캐시 → Home 화면에서 닉네임/프사 표시. CarOwnerRenew `UserInfoRepositoryImpl` 패턴(cacheFirst / networkOnly) 적용. 부수 작업으로 `UserProfile` 모델을 `LoginResult`에 평탄화하여 의미 정합화.

## 1. 개요

지금까지 모바일은 카카오 로그인 응답으로 토큰 + userId + isNewUser만 받고, **닉네임/프사를 받을 경로가 없었다.** 본 작업은:

- 백엔드: 인증된 사용자의 본인 정보 조회 endpoint 신규 (`GET /api/v1/users/me`)
- 모바일: `:local:datastore` 캐시 + `cacheFirst / networkOnly` 옵션 + Home 화면에서 사용
- 부수 정리: `UserProfile`(실제 내용: `userId, isNewUser`) 모델을 `LoginResult`에 평탄화 + 삭제

## 2. 사용자 요구사항

1. 백엔드: id, kakao_id, nickname, profile_image_url 4개 필드 내려주는 endpoint
2. 모바일: Home 화면 진입 시 유저 정보 조회 → DataStore 저장
3. `cacheFirst` / `networkOnly` 옵션 (`/Users/hwamulman/hwamulman-workspace/CarOwnerRenew`의 `UserInfoRepositoryImpl` 패턴 참고)

## 3. 핵심 결정 사항

### 3.1 fetch 트리거: HomeViewModel init

- `HomeViewModel` `init`에서 `userInfoRepository.getUserInfo(onError, CacheStrategy.CACHE_FIRST)` 호출
- 신규 로그인 / 자동 로그인 양쪽에서 동일 흐름 (Home 진입 시점이 트리거)
- Splash는 토큰 존재만 확인 후 Home으로 직행 (기존 흐름 유지, ADR-0009)
- UI는 `observeUserInfoCache()` 패턴으로 캐시 관찰 — 캐시 변경 시 자동 반영

### 3.2 캐시 정책

| 항목 | 정책 |
|---|---|
| 캐시 만료 | 없음 (무조건 캐시 사용) |
| 명시적 갱신(networkOnly) | 1차에서 호출 지점 없음 (YAGNI). 필요해지면 pull-to-refresh 등 추가. |
| 로그아웃 시 | `clearUserInfoCache()` 호출 (LogoutUseCase 또는 토큰 클리어 흐름에 통합) |
| 세션 만료 (`AuthEventBus.sessionExpired`) 시 | 캐시 클리어 (재로그인 후 자동 fetch) |

### 3.3 진행 방식: Agent Teams + 옵션 C

- backend-dev / mobile-dev 팀원 spawn
- API 협의는 SendMessage (spec에서 거의 합의돼 협의 작음)
- backend-dev: PM hub cwd에서 직접 작업
- mobile-dev: 분석/협의는 본체, **코드 편집은 child claude (`cd challenge-app && claude -p`) 위임** — `mobile-dev.md` "코드 편집 흐름" 섹션 적용

### 3.4 부수 정리: `UserProfile` → `LoginResult` 평탄화

`UserProfile(userId, isNewUser)`이 본 작업의 `UserInfo`와 의미 무관 + misleading. 본 작업에서 정리:
- `LoginResult` 에 `userId`, `isNewUser` 직접 보유
- `UserProfile.kt` 삭제
- Mapper / 테스트 정리

## 4. 백엔드 — Spring Boot multi-module

### 4.1 Endpoint

| Method | Path | 인증 | 용도 |
|---|---|---|---|
| `GET` | `/api/v1/users/me` | Bearer | 본인 정보 조회 |

요청: query/body 없음. Bearer 토큰의 `principal=userId`에서 추출.

응답 (HTTP 200, code 200):
```json
{
  "error": false, "code": 200, "message": "",
  "data": {
    "id": 12,
    "kakaoId": 4883170475,
    "nickname": "이우건",
    "profileImageUrl": "http://img1.kakaocdn.net/..."
  }
}
```

에러:
- HTTP 401, code 401: 인증 만료 (Ktor Auth 자동 처리)
- HTTP 500, code 500: 인프라 장애

### 4.2 DTO

```kotlin
data class UserInfoResponse(val data: UserInfoData) : BaseResponse()
data class UserInfoData(
    val id: Long,
    val kakaoId: Long,
    val nickname: String,
    val profileImageUrl: String?,
)
```

### 4.3 Service

```kotlin
class UserService(private val userRepository: UserRepository) {
    fun getMe(me: Long): User =
        userRepository.findById(me) ?: throw UnauthorizedException("user not found")
}
```

`UserRepository.findById`는 이미 존재 (auth-refresh-rotation 작업에서 추가됨, ADR-0009).

### 4.4 Controller

```kotlin
@RestController
@RequestMapping("/api/v1/users")
class UserController(private val userService: UserService) {
    @GetMapping("/me")
    fun getMe(@AuthenticationPrincipal userId: Long): UserInfoResponse {
        val user = userService.getMe(userId)
        return UserInfoResponse(
            data = UserInfoData(
                id = user.id!!,
                kakaoId = user.kakaoId,
                nickname = user.nickname,
                profileImageUrl = user.profileImageUrl,
            ),
        )
    }
}
```

기존 `JwtAuthenticationFilter`가 `principal=userId(Long)` 주입. `FriendController.currentUserId()` 패턴과 정합.

### 4.5 모듈 배치

- `controller/user/UserController.kt` + `dto/UserInfoResponse.kt`
- `service/user/UserService.kt`
- (기존) `domain/user/User.kt`, `UserRepository.findById`

### 4.6 통합 테스트 (Testcontainers, `UserIntegrationTest`)

- 정상 응답 (4 필드 모두 반환)
- 미인증 (401)
- 토큰의 userId가 DB에 없음 (401)
- `profile_image_url`이 null인 사용자 (응답 `profileImageUrl: null`)

### 4.7 컨트롤러 슬라이스 테스트 (`UserControllerTest`)

- 성공 케이스
- 401 (인증 누락)

## 5. 모바일 — KMP / Compose Multiplatform

### 5.1 모듈

| 모듈 | 신규 / 확장 | 내용 |
|---|---|---|
| `:remote:model` | 확장 | `user/UserInfoResponse.kt` (+ `UserInfoData`) |
| `:remote:api` | 확장 | `UserApi.kt` (Ktorfit) |
| `:remote:mapper` | 확장 | `UserInfoMapper.kt` |
| `:domain:model` | 확장 | `UserInfo.kt`, `CacheStrategy.kt` |
| `:domain:repository` | 확장 | `UserInfoRepository.kt` |
| `:data:repositoryImpl` | 확장 | `UserInfoRepositoryImpl.kt` |
| `:local:datastore` | 확장 | `datasource/UserInfoLocalDataSource.kt`, `model/UserInfoPrefs.kt` |
| `:feature:home` | 확장 | `HomeViewModel` init에서 `getUserInfo` 트리거 + 캐시 관찰 통합 |

### 5.2 도메인 모델

```kotlin
data class UserInfo(
    val id: Long,
    val kakaoId: Long,
    val nickname: String,
    val profileImageUrl: String?,
)

enum class CacheStrategy { CACHE_FIRST, NETWORK_ONLY }
```

### 5.3 Repository 패턴 (메모리 규칙: Flow + onError + AuthEventBus, sealed Result 금지)

```kotlin
interface UserInfoRepository {
    fun getUserInfo(
        onError: (Throwable) -> Unit,
        cacheStrategy: CacheStrategy = CacheStrategy.CACHE_FIRST,
    ): Flow<UserInfo>

    fun observeUserInfoCache(): Flow<UserInfo?>

    suspend fun clearUserInfoCache()
}
```

구현 흐름 (`UserInfoRepositoryImpl`):
- `CACHE_FIRST`: `UserInfoLocalDataSource.getUserInfo()` → null이면 remote fetch → local 저장 → emit
- `NETWORK_ONLY`: 항상 remote fetch → local 저장 → emit
- 401 (`code == 401`): repository 내부에서 `AuthEventBus.emitSessionExpired()` (홈/친구 패턴 동일)
- 에러 클래스:
  - `UserInfoApiException(val code: Int, message: String)` — 도메인 전용 (`:domain:model/user/UserInfoError.kt` 신규)
  - `UserInfoNetworkException(message: String)` — 동일 파일
  - `SilentAuthExpired` — 친구 작업의 `:domain:model/friend/FriendsError.kt:SilentAuthExpired` **재사용** (object sentinel이라 import만 하면 됨). 후속 cleanup으로 `:domain:model/auth/`로 공통 위치 이동은 별도 작업.

### 5.4 DataStore

```kotlin
@Serializable
data class UserInfoPrefs(
    val id: Long = 0L,
    val kakaoId: Long = 0L,
    val nickname: String = "",
    val profileImageUrl: String? = null,
    val hasValue: Boolean = false,  // 캐시 존재 여부 sentinel (id=0과 구분)
)

@Single
class UserInfoLocalDataSource {
    private val dataStore = createDataStore(
        serializer = UserInfoPrefs.serializer(),
        defaultValue = UserInfoPrefs(),
        fileName = "user_info",
    )

    fun observeUserInfo(): Flow<UserInfo?> =
        dataStore.data.map { if (it.hasValue) it.toDomain() else null }

    suspend fun getUserInfo(): UserInfo? =
        dataStore.data.first().let { if (it.hasValue) it.toDomain() else null }

    suspend fun saveUserInfo(userInfo: UserInfo) {
        dataStore.updateData { UserInfoPrefs(
            id = userInfo.id,
            kakaoId = userInfo.kakaoId,
            nickname = userInfo.nickname,
            profileImageUrl = userInfo.profileImageUrl,
            hasValue = true,
        ) }
    }

    suspend fun clear() {
        dataStore.updateData { UserInfoPrefs() }  // hasValue=false로 리셋
    }
}
```

`hasValue` sentinel: 캐시 존재 여부 명시. 기본값 0L/""과 "id=0인 사용자"를 구분.

### 5.5 API (Ktorfit)

```kotlin
interface UserApi {
    @GET("api/v1/users/me")
    suspend fun getMe(): ApiResult<UserInfoResponse>
}
```

기존 `ApiResult` wrapper 패턴 따름 (FriendsApi와 일관).

### 5.6 HomeViewModel 통합

- `init`에서 `userInfoRepository.getUserInfo(onError = ::showMessage, cacheStrategy = CACHE_FIRST)` 트리거 (단발 collect, fetch + 캐시 저장 보장)
- UI는 `userInfoRepository.observeUserInfoCache()` 를 별도 `StateFlow`로 `stateIn` → `HomeUiState.Data`에 `userInfo: UserInfo?` 필드 추가
- 401은 Repository 내부 `AuthEventBus.emitSessionExpired()` 처리 (ViewModel 별도 분기 없음 — `SilentAuthExpired` skip)

### 5.7 LoginResult 평탄화 (UserProfile 삭제)

변경 파일:
- `domain/model/LoginResult.kt` — `userProfile: UserProfile` → `userId: Long, isNewUser: Boolean`로 평탄화
- `domain/model/UserProfile.kt` — **삭제**
- `remote/mapper/LoginResponseMapper.kt` — 매핑 평탄화
- `feature/login/.../LoginViewModelTest.kt` — `result.userProfile.userId` → `result.userId` 갱신
- `feature/login/.../FakeLoginRepository.kt` — 동일 갱신
- `feature/login/.../LoginViewModel.kt:53` — `result.userProfile.isNewUser` → `result.isNewUser` 정정 (확인됨, grep 결과 유일한 사용 처)
- `SplashViewModel`은 `GetStoredTokensUseCase`만 사용 (LoginResult 미사용) — 영향 없음

### 5.8 캐시 클리어 흐름

- 로그아웃 시 (`LogoutUseCase` 또는 토큰 클리어 흐름) `userInfoRepository.clearUserInfoCache()` 호출
- `AuthEventBus.sessionExpired` 트리거 시 (`MainScreen` collect 직후) 캐시 클리어 추가

### 5.9 모바일 테스트

| 대상 | 케이스 |
|---|---|
| `UserInfoRepositoryImplTest` (신규) | CACHE_FIRST 캐시O / 캐시X / NETWORK_ONLY / 401 → SilentAuthExpired / clear 후 캐시 없음 |
| `HomeViewModelTest` (확장) | 신규 케이스: 캐시 있으면 즉시 노출 / 없으면 fetch 후 노출 / 401 SilentAuthExpired skip. 기존 6 케이스 회귀 0 |
| `LoginViewModelTest` (회귀) | `LoginResult` 평탄화 후에도 4 케이스 PASS 유지 |

## 6. 디자인

UI 변경 없음 — 닉네임/프사는 Lovable 디자인에 이미 있던 영역(상단 TopBar 또는 빈 상태 카드)에 표시. design.md 변경 불필요.

## 7. 트레이드오프 / 위험

| # | 위험 | 1차 대응 | 후속 |
|---|---|---|---|
| 1 | `UserProfile` 평탄화가 auth-kakao 작업 영역 건드림 | 영향 5 파일 좁고 명확, 테스트로 회귀 검증 | — |
| 2 | DataStore `hasValue` sentinel 패턴이 기존 `TokenPrefs`와 다름 | sentinel 추가가 0L "id=0인 사용자" 케이스 방지에 필수. KDoc로 의도 명시. | — |
| 3 | cacheFirst의 만료 정책 없음 → 카카오 프로필 변경 시 다음 로그인까지 미반영 | 로그아웃/재로그인 흐름으로 갱신 가능. 친한 친구 앱 특성상 닉네임/프사 자주 안 바뀜. | 필요해지면 pull-to-refresh 또는 시간 기반 추가 |
| 4 | HomeViewModel 기존 테스트 6 케이스 회귀 가능 | 신규 통합 시 회귀 0 보장 (`UserInfoRepository` 주입 추가 + 캐시 관찰 필드 추가) | — |

## 8. 1차 / 후속 분리

### 1차 (본 spec)
- `GET /api/v1/users/me` endpoint + service + 통합 테스트
- 모바일 도메인/Data/datastore 전체 + UserApi + Mapper
- HomeViewModel 통합 + 캐시 관찰
- `LoginResult` 평탄화 + UserProfile 삭제
- 로그아웃/세션만료 시 캐시 클리어

### 후속 작업 (별도 spec/plan)
- 내 프로필 화면 (닉네임 표시 + 친구 초대 시 사용)
- 닉네임 / 프사 명시적 갱신 (pull-to-refresh)
- `UserInfo` 도메인 모델에 친구 추가 코드(예: 4자리 코드) 합류 (필요해질 때)

## 9. dispatch / 메모리 규칙 (Agent Teams 진입 시)

| 규칙 | 적용 |
|---|---|
| **mobile-dev = 옵션 C** | 분석/협의는 본체, 코드 편집은 `cd /Users/hwamulman/woogunProject/challenge/challenge-app && claude -p '...'` 위임. `mobile-dev.md` "코드 편집 흐름" 참조. |
| backend-dev = 직접 작업 | PM hub cwd에서 controller/service/test 직접 작성. |
| API 협의 | SendMessage로 두 팀원이 본체 컨텍스트에서. spec에서 거의 합의돼 협의 작음. |
| Repository 표준 | `Flow<T>` + `onError: (Throwable) -> Unit` + `AuthEventBus`. 도메인 sealed Result 금지(stdlib OK). 401은 repository 내부 처리. |

## 10. 검증 / Definition of Done

### 백엔드
- `UserControllerTest` 슬라이스 2/2 PASS
- `UserIntegrationTest` 4/4 PASS (Docker 가용 시) — 미가용 환경에선 `@EnabledIf` 자동 skip (기존 패턴)
- `./gradlew build` SUCCESS
- backend-dev 자체 commit + push

### 모바일
- `UserInfoRepositoryImplTest` 5/5 PASS
- `HomeViewModelTest` 신규 케이스 PASS + 기존 6 회귀 0
- `LoginViewModelTest` 4/4 PASS 회귀 유지
- `:composeApp:compileDebugKotlinAndroid` SUCCESS
- mobile-dev는 git 작업 0건 (사용자가 직접 commit)

### PM hub
- `spec.md` (본 파일) commit
- `api-contract.md` (작성 후 confirmed) commit
- `plan.md` commit
- `backend-report.md` / `mobile-report.md` (구현 완료 후) commit
- `summary.md` (작업 완료 후) + `INDEX.md` 갱신
