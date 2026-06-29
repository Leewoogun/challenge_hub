# Mobile Report — user-info

- **feature-id**: user-info
- **작성일**: 2026-06-29
- **담당**: mobile-dev (옵션 C — child claude 위임)
- **상태**: implemented (모바일 working tree, 사용자 commit 대기)

## 구현 요약

모바일 측 user-info feature 구현 완료. T3(도메인+Data+LoginResult 평탄화)와 T4(HomeViewModel 통합)를 옵션 1 패턴(`onError: (String)`, Ktor Auth 401 전담, 도메인 에러 클래스 없음 — `faae2cd` 표준 정합)으로 구현. UserProfile 모델 삭제 + LoginResult 평탄화 부수 정리 포함.

## 변경된 모듈 & 파일

### 신규 (12)
| 모듈 | 파일 | 용도 |
|---|---|---|
| `:domain:model` | `user/UserInfo.kt` | 도메인 모델 (id, kakaoId, nickname, profileImageUrl) |
| `:domain:model` | `user/CacheStrategy.kt` | enum (CACHE_FIRST / NETWORK_ONLY) |
| `:domain:repository` | `UserInfoRepository.kt` | 인터페이스 (getUserInfo, observeUserInfoCache, clearUserInfoCache) |
| `:remote:model` | `user/UserInfoResponse.kt` | envelope + UserInfoData |
| `:remote:api` | `UserApi.kt` | Ktorfit (`@GET("api/v1/users/me")`) |
| `:remote:mapper` | `UserInfoMapper.kt` | DTO → Domain |
| `:local:datastore` | `model/UserInfoPrefs.kt` | DataStore Prefs (`hasValue` sentinel) |
| `:local:datastore` | `datasource/UserInfoLocalDataSource.kt` | interface (테스트 fake 가능) |
| `:local:datastore` | `datasource/UserInfoLocalDataSourceImpl.kt` | impl (createDataStore) |
| `:data:repositoryImpl` | `repository/UserInfoRepositoryImpl.kt` | `@Single`, Flow + onError(String) + suspendOnSuccess/Failure 패턴 |
| `:data:repositoryImpl` | `commonTest/.../UserInfoRepositoryImplTest.kt` | TDD 5 케이스 |
| `:feature:home` | `commonTest/.../FakeUserInfoRepository.kt` | StateFlow 백킹 fake |

### 수정 (10)
- `:remote:api/di/ApiModule.kt` — `provideUserApi` 추가
- `:domain:model/LoginResult.kt` — `userProfile: UserProfile` → `userId, isNewUser` 평탄화 (`tokens: AuthTokens`는 유지 — 영향 범위 축소)
- `:remote:mapper/LoginResponseMapper.kt` — 평탄화 매핑
- `:feature:login/LoginViewModel.kt:53` — `result.userProfile.isNewUser` → `result.isNewUser`
- `:feature:login/LoginViewModelTest.kt` — 평탄화 반영
- `:feature:login/FakeLoginRepository.kt` — 동일
- `:data:repositoryImpl/data/auth/TokenProviderImpl.kt` — `clearTokens()`에 `userInfoLocalDataSource.clear()` 추가 (세션 만료 진입점)
- `:data:repositoryImpl/data/repository/LoginRepositoryImpl.kt` — `clearTokens()`에 동일 (로그아웃 진입점)
- `:data:repositoryImpl/build.gradle.kts` — commonTest deps
- `:feature:home/HomeViewModel.kt` — `UserInfoRepository` 주입 + `init` 2-launch (트리거 + 관찰) + `combine(getHomeData, _userInfo)`
- `:feature:home/contract/HomeUiState.kt` — `Data.userInfo: UserInfo? = null` 필드 추가
- `:feature:home/commonTest/HomeViewModelTest.kt` — 신규 3 케이스 추가

### 삭제 (1)
- `:domain:model/UserProfile.kt`

## 테스트 결과

### 옵션 1 적용 — 메모리 규칙 (`feedback_mobile_repository_pattern.md`, `faae2cd` 표준)

T3 분석 단계에서 spec/plan과 현재 challenge-app 코드(`faae2cd "refactor: repository 구현 방식 템플릿에 맞게 변경"`) 충돌 발견하여 옵션 1로 진행:
- `onError: (String) -> Unit` (Throwable 아님)
- 도메인 에러 클래스 (`UserInfoError.kt`) 만들지 않음
- `SilentAuthExpired` sentinel 사용 안 함 (`faae2cd`에서 사용자가 직접 삭제한 패턴)
- `AuthEventBus` repository 미주입 — 401은 Ktor Auth(bearer) 플러그인이 전담 (ADR-0009)
- 표준 패턴: `flow { api.call().suspendOnSuccess { emit(...) }.suspendOnFailureWithErrorHandling(onError) }`

### 테스트 (Android testDebugUnitTest)

| 테스트 클래스 | 결과 | timestamp |
|---|---|---|
| `UserInfoRepositoryImplTest` | **5/5 PASS** | 2026-06-29T (T3) |
| `LoginViewModelTest` | **4/4 PASS** (회귀 0) | 2026-06-29T (T3) |
| `HomeViewModelTest` | **10/10 PASS** (기존 7 + 신규 3, 회귀 0) | 2026-06-29T00:07:12Z (T4) |
| **종합** | **19/19 PASS, 회귀 0** | — |

### UserInfoRepositoryImplTest 5종 (옵션 1 정합)
1. CACHE_FIRST + 캐시 있음 → API 0건, 캐시 emit
2. CACHE_FIRST + 캐시 없음 → API 호출 + local 저장 + emit
3. NETWORK_ONLY → 항상 API + 저장 + emit
4. API 실패 (HttpError 등) → onError(String) 호출, emit·저장 없음
5. clearUserInfoCache → local 비움 + observe가 null emit

### HomeViewModelTest 신규 3종
- 캐시 있으면 init 시 즉시 userInfo 노출
- 캐시 없으면 init 트리거가 fetch + 관찰로 노출
- 유저 조회 실패 시 ShowMessage 1회 + userInfo 는 null

### 빌드
- `:remote:model`, `:remote:api`, `:remote:mapper`, `:domain:model`, `:domain:repository`, `:data:repositoryImpl`, `:local:datastore`, `:feature:login`, `:feature:home`: **9 모듈 SUCCESS**
- `compileCommonMainKotlinMetadata` + `compileDebugKotlinAndroid` 모두 SUCCESS

## Working tree 상태

- 작업 브랜치: `main` 유지 (새 브랜치 없음)
- 변경분: 신규 12 + 수정 10 + 삭제 1, **새 커밋 0건** (모바일 dispatch git 금지 규칙 준수)
- 사용자가 직접 commit/push 결정

## 옵션 1 결정 사유 (`feedback_mobile_repository_pattern.md` 갱신 반영)

`spec.md` / `plan.md` 작성 시점(`33ffe88`)에 `feedback_mobile_repository_pattern.md`가 옛 "401 repository 내부 처리 + Throwable + SilentAuthExpired" 룰로 stale 상태였음. mobile-dev가 T3 분석 단계에서 `challenge-app` 실제 코드 grep으로 `SilentAuthExpired` 0건 확인 + `faae2cd` (사용자 본인 commit) 식별 + 메모리 자체 갱신 후 pm-lead에 에스컬레이션. 옵션 1(현재 표준) 진행 승인 후 구현 완료.

## 알려진 한계 / 후속

- **iOS 단위 테스트 미실행** — T4 dispatch 범위가 `testDebugUnitTest` (Android)였음. iOS `:feature:home:iosSimulatorArm64Test` 별도 검증 필요 시 후속 작업으로 등재.
- **iOS framework link 미검증** — `xcodebuild compile` 미수행. UI 표시는 본 범위 외(spec §6 "UI 변경 없음")라 iOS 검증 가치는 후속에서.
- **내 프로필 화면 / 명시적 갱신 UX** — `UserInfo` 캐시 활용처는 본 범위 외. backlog 등재.
- **`UserInfoLocalDataSource` interface 분리**는 본 작업에서 신규 도입한 패턴. `TokenLocalDataSource` / `AppSettingsLocalDataSource`는 concrete class 그대로 유지 (테스트 없는 케이스라 무영향). 향후 테스트 추가 시 동일 분리 검토.
- **`MainScreen.kt` 미수정** — `clearTokens` 두 진입점(TokenProviderImpl + LoginRepositoryImpl)에서 `userInfoLocalDataSource.clear()` 호출하므로 추가 진입점 불필요.

## 미해결 이슈

없음. 모든 spec 요구사항 충족 (옵션 1 패턴으로 정합).

## API 계약 대비 구현 차이

없음. `api-contract.md` (status: confirmed, commit `b4e666a`) 응답 4 필드와 모바일 DTO/도메인 모델 1:1 정합.
