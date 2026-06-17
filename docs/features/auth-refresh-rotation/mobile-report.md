# Mobile Report — auth-refresh-rotation

- **커밋**: `68d6533` "feat: Rotation Refresh token 클라이언트 처리 추가" (2026-05-28)
- **변경 파일 수**: 16 / +143 / -116
- **빌드 / 테스트**: 신규 테스트 없음. 본 PM 정리 시점에 별도 재실행은 안 함 (코드 변경 0건의 사후 박제). 기존 LoginViewModelTest는 refresh 분기를 직접 검증하지 않아 회귀 가능성 낮음.

## 변경 개요

401 처리를 산재된 Repository/Splash 분기에서 **Ktor `Auth(bearer)` 플러그인 단일 지점**으로 옮기고, 서버 rotation 응답(`data.refreshToken` 신규)에 맞춰 새 refresh를 저장하도록 했다.

## 핵심 변경: KtorfitModule (`remote/network`)

**파일**: `remote/network/src/commonMain/kotlin/com/lwg/challenge/remote/network/di/KtorfitModule.kt`

```kotlin
install(Auth) {
    bearer {
        loadTokens {
            val access = tokenProvider.getAccessToken()
            val refresh = tokenProvider.getRefreshToken()
            if (access.isNotBlank()) BearerTokens(access, refresh) else null
        }

        refreshTokens {
            val refreshToken = oldTokens?.refreshToken
            if (refreshToken.isNullOrBlank()) {
                authEventBus.emitSessionExpired()
                return@refreshTokens null
            }

            try {
                val response = client.post("${BuildKonfig.BASE_URL}api/v1/auth/refresh") {
                    contentType(ContentType.Application.Json)
                    setBody(RefreshRequest(refreshToken))
                }

                val body = response.body<RefreshResponse>()
                when (body.code) {
                    CODE_SUCCESS -> {
                        tokenProvider.updateTokens(body.data.accessToken, body.data.refreshToken)
                        BearerTokens(body.data.accessToken, body.data.refreshToken)
                    }
                    CODE_UNAUTHORIZED -> {
                        Logger.w("Refresh token expired — forcing logout")
                        tokenProvider.clearTokens()
                        authEventBus.emitSessionExpired()
                        null
                    }
                    else -> {
                        Logger.e("Unexpected refresh response code: ${body.code}")
                        null
                    }
                }
            } catch (e: Exception) {
                Logger.e("Token refresh failed", e)
                null
            }
        }

        sendWithoutRequest { request ->
            request.url.pathSegments.none { it == "auth" }
        }
    }
}
```

**핵심 동작**:
- 일반 API 요청 → 401 응답 → Ktor가 `refreshTokens` 자동 트리거 → 새 토큰으로 원 요청 재시도. 사용자/ViewModel 무자각.
- refresh 실패 → 토큰 클리어 + `AuthEventBus.sessionExpired` 발사. `MainScreen`이 받아 로그인 탭으로.
- `sendWithoutRequest`: `auth` 경로는 Authorization 미부착 (`/api/v1/auth/kakao`, `/api/v1/auth/refresh` 모두 공개 — refresh 자체가 인증).

### 추가 의존성

**`gradle/libs.versions.toml`**:
```
ktor-client-auth = { module = "io.ktor:ktor-client-auth", version.ref = "ktor" }
```

**`remote/network/build.gradle.kts`**:
```
implementation(libs.ktor.client.auth)
```

## 신규 컴포넌트

### AuthEventBus (`core/utils`, 신규)

**파일**: `core/utils/src/commonMain/kotlin/com/lwg/challenge/utils/AuthEventBus.kt`

```kotlin
class AuthEventBus {
    private val _sessionExpired = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
    val sessionExpired: SharedFlow<Unit> = _sessionExpired.asSharedFlow()
    fun emitSessionExpired() { _sessionExpired.tryEmit(Unit) }
}
```

- `core/utils`에 위치 — `:remote:network`, `:feature:main` 등 여러 모듈이 의존하기 위함.
- Koin Single (`KtorfitModule.provideAuthEventBus`).

### TokenProvider (`remote/network`, 신규 인터페이스)

**파일**: `remote/network/src/commonMain/kotlin/com/lwg/challenge/remote/network/auth/TokenProvider.kt`

```kotlin
interface TokenProvider {
    suspend fun getAccessToken(): String
    suspend fun getRefreshToken(): String
    suspend fun updateTokens(accessToken: String, refreshToken: String)
    suspend fun clearTokens()
}
```

- `:remote:network`가 `:local:datastore`에 직접 의존하지 않도록 인터페이스만 노출. Hexagonal port.

### TokenProviderImpl (`data/repositoryImpl`, 신규)

**파일**: `data/repositoryImpl/src/commonMain/kotlin/com/lwg/challenge/data/auth/TokenProviderImpl.kt`

```kotlin
@Single(binds = [TokenProvider::class])
class TokenProviderImpl(
    private val tokenLocalDataSource: TokenLocalDataSource,
) : TokenProvider { ... }
```

- Koin `@Single`로 `TokenProvider` 바인딩. `TokenLocalDataSource` 위임.

## MainScreen 변경

**파일**: `feature/main/.../MainScreen.kt`

```kotlin
val authEventBus = koinInject<AuthEventBus>()

LaunchedEffect(authEventBus) {
    authEventBus.sessionExpired.collect {
        navigator.switchTab(Route.LoginRoute.Main)
    }
}
```

세션 만료 시 `Route.LoginRoute.Main`으로 강제 이동. ChallengeTheme 바깥 LaunchedEffect로 배치하여 화면 전환과 무관히 동작.

## SplashViewModel 단순화

**파일**: `feature/splash/.../SplashViewModel.kt`

```kotlin
// before
val tokens = getStoredTokensUseCase()
if (tokens.refreshToken.isBlank()) { /* Login */ }
val refreshed = refreshAccessTokenUseCase(...).firstOrNull()
_uiEffect.emit(if (refreshed != null) Home else Login)

// after
val tokens = getStoredTokensUseCase()
_uiEffect.emit(if (tokens.refreshToken.isBlank()) Login else Home)
```

- splash에서 refresh를 시도하지 않음. 만료 판정은 첫 API 호출 시점에서 Ktor Auth가 함.
- `RefreshAccessTokenUseCase` 의존성 제거.

## 제거된 코드

| 파일 | 사유 |
|------|------|
| `domain/usecase/RefreshAccessTokenUseCase.kt` | Ktor Auth가 흡수 |
| `data/repository/LoginRepositoryImpl.refreshAccessToken` + `CODE_UNAUTHORIZED=401` 상수 | 동상 |
| `domain/repository/LoginRepository.refreshAccessToken` | 동상 |
| `remote/api/LoginApi.refresh` 엔드포인트 선언 | refresh는 Ktor Auth가 직접 POST. Ktorfit 통하지 않음 (순환 의존 방지 — Ktorfit 인스턴스 안에 또 Ktorfit 호출 X). |
| `remote/mapper/RefreshResponseMapper.kt` | 동상 |
| `data/di/UseCaseModule.provideRefreshAccessTokenUseCase` | 동상 |
| `feature/login/FakeLoginRepository.RefreshResponse` sealed interface + `refreshAccessToken` override | 동상 |

## RefreshResponse DTO 갱신

**파일**: `remote/model/.../auth/RefreshResponse.kt`

```kotlin
data class RefreshData(
    val accessToken: String = "",
    val refreshToken: String = "",  // 신규
)
```

주석도 갱신:
```
// before: Refresh token 은 재발급하지 않고 기존 값을 재사용. (ADR-0009 예정 시 변경)
// after: Rotation Refresh Token: 매 refresh 시 access + refresh 모두 재발급 (ADR-0009).
```

## LoginApi 주석 갱신

**파일**: `remote/api/.../LoginApi.kt`

- 두 엔드포인트 모두 공개라는 표현 → "카카오 로그인은 공개 엔드포인트", "토큰 갱신은 Ktor Auth 플러그인이 직접 처리"로 명확화.
- `refresh` 메서드 제거됨에 따른 정합.

## 검증

- **단위 테스트 신규 0**. 권장 케이스(backlog 등재):
  - Ktor Auth `refreshTokens` 200 분기 — 새 토큰 저장 + 원 요청 재시도
  - 401 분기 — 토큰 클리어 + sessionExpired 발사
  - refresh JSON deserialization (`refreshToken` 신규 필드)
  - SplashViewModel: refreshToken blank → Login, 그 외 → Home
- **회귀**: LoginViewModelTest는 refresh 흐름과 무관 (로그인 분기만 검증). 회귀 영향 없을 것으로 추정.
- **수동 검증 권장** (backlog 등재):
  - access 만료 후 일반 API 호출 → 사용자 무자각 갱신 확인
  - refresh 만료 시 로그인 화면으로 강제 이동
  - V1 가입자(hash 없음) → 첫 refresh에서 401 → 재로그인 후 정상 동작
  - 토큰 만료가 두 요청 동시 발생 시 race — Ktor Auth가 한 refresh로 직렬화하는지 확인

## 변경 파일 목록

```
A core/utils/.../utils/AuthEventBus.kt
A data/repositoryImpl/.../data/auth/TokenProviderImpl.kt
M data/repositoryImpl/.../data/di/UseCaseModule.kt
M data/repositoryImpl/.../data/repository/LoginRepositoryImpl.kt
M domain/repository/.../domain/repository/LoginRepository.kt
D domain/usecase/.../domain/usecase/RefreshAccessTokenUseCase.kt
M feature/login/.../feature/login/FakeLoginRepository.kt (test)
M feature/main/.../feature/main/MainScreen.kt
M feature/splash/.../feature/splash/SplashViewModel.kt
M gradle/libs.versions.toml
M remote/api/.../remote/api/LoginApi.kt
D remote/mapper/.../remote/mapper/RefreshResponseMapper.kt
M remote/model/.../remote/model/auth/RefreshResponse.kt
M remote/network/build.gradle.kts
A remote/network/.../remote/network/auth/TokenProvider.kt
M remote/network/.../remote/network/di/KtorfitModule.kt
```
