# ADR-0002: 백엔드 기반 인프라(Foundation) 구성

- **상태**: accepted (2026-04-23)
- **생성**: 2026-04-23
- **영향 범위**: 모든 백엔드 기능의 선행 조건

## 맥락

`challenge-server`는 `ChallengeServerApplication.kt`와 smoke 테스트 1개만 있는 **완전 스켈레톤** 상태다. 컨트롤러, 서비스, 도메인, Security 구성, ExceptionHandler 모두 없다.

이 상태에서 feature별로 기반 요소를 임의 추가하면 일관성이 깨진다. 첫 기능 구현 전에 공통 기반을 정리하는 것이 효율적이다.

## 필요한 Foundation 요소

| 항목 | 현재 상태 | 필요한 작업 |
|------|----------|------------|
| SecurityFilterChain | 없음 | `SecurityConfig`에 경로별 `authorizeHttpRequests` 정의 |
| JWT 인증 필터 | JJWT 0.12.6 의존성만 | `JwtAuthenticationFilter` 구현, 토큰 발급·검증 유틸 |
| GlobalExceptionHandler | 없음 | `@RestControllerAdvice`로 표준 에러 바디 반환 |
| 표준 에러 응답 DTO | 없음 | `{code, message, details}` shape — api-contract 표준과 일치 |
| 응답 wrapper 정책 | 미정 | `ApiResponse<T>` 표준화 여부 결정 (권장: 쓰지 않고 raw JSON, 에러만 표준) |
| SpringDoc OpenAPI config | 의존성만 | JWT Bearer 헤더 보안 스키마 설정, grouped API |
| CORS | 없음 | 모바일(origin 불필요) + 웹 프런트(ADR-0004)에 따라 |
| DB 마이그레이션 | 없음 | ADR-0001 결정 반영 |
| 로깅 포맷 | 기본 | JSON 구조화 로깅 도입 여부 |

## 권장 순서

1. ADR-0001(마이그레이션 도구) 결정 → Flyway 의존성 추가 + `V1__init.sql` skeleton
2. ADR-0004(웹 운영 여부) 결정 → CORS 허용 도메인 확정
3. Foundation을 `docs/features/foundation/` feature로 분리하여 구현. 이 feature의 완료가 다른 feature의 선행 조건.
4. Foundation 완료 후 첫 도메인 기능(예: `auth-login`) 착수.

## 대안

"Foundation을 별도 feature로 분리하지 않고 첫 기능과 함께 자연스럽게 쌓는다" 도 가능하나, 권장하지 않음. 이유:
- 첫 feature가 지나치게 커짐
- 기반이 feature별로 다르게 구성될 위험
- mobile-dev가 의존할 에러 shape이 늦게 확정됨

## 결정

**2026-04-23: foundation sub-feature 선행 구성 확정 (accepted). 응답 DTO는 CarOwnerRenew 프로젝트의 `BaseResponse` 패턴을 서버에 이식.**

### 응답 DTO 규약 (BaseResponse 패턴)

CarOwnerRenew(`/Users/hwamulman/hwamulman-workspace/CarOwnerRenew`)의 `remote/model/src/main/kotlin/ktc/cargo/driver/remote/model/base/BaseResponse.kt` 구조를 서버 Spring Boot에 이식:

```kotlin
// :api 모듈
open class BaseResponse(
    val error: Boolean = false,
    val code: Int = 200,
    val message: String = "",
)

// 데이터 응답은 data 필드를 가진 data class가 상속
data class LoginResponse(
    val data: LoginData,
) : BaseResponse()

data class LoginData(
    val accessToken: String,
    val refreshToken: String,
    val userId: Long,
)
```

### 에러 규약 — **항상 HTTP 200**

비즈니스 예외는 HTTP 4xx/5xx를 쓰지 않고 **HTTP 200 OK + body의 code 필드**로 구분:

| code | 의미 | 모바일 처리 |
|------|------|------------|
| 200 | 성공 (`error=false`) | 정상 흐름 |
| 400~499 | 사용하지 않음 (HTTP 레벨 에러는 네트워크/라우팅 문제일 때만) | — |
| 401 | 토큰 만료 | Refresh Token으로 재시도 |
| 700 | 비즈니스 에러 (스낵바) | 토스트/스낵바 |
| 701 | 비즈니스 에러 (다이얼로그) | 확인 다이얼로그 |
| 702, 703 | 비즈니스 에러 (전체화면) | 전체화면 에러 |
| 705 | 비즈니스 에러 (단일 버튼 다이얼로그) | 단일 버튼 |

HTTP 5xx는 인프라 장애(DB 다운 등)에만 사용. 예상 가능한 비즈니스 예외는 전부 HTTP 200.

### GlobalExceptionHandler 구현 지침

```kotlin
@RestControllerAdvice
class GlobalExceptionHandler {
    @ExceptionHandler(BusinessException::class)
    fun handleBusiness(e: BusinessException): ResponseEntity<BaseResponse> =
        ResponseEntity.ok(BaseResponse(error = true, code = e.code, message = e.message))

    @ExceptionHandler(MethodArgumentNotValidException::class)
    fun handleValidation(e: MethodArgumentNotValidException): ResponseEntity<BaseResponse> =
        ResponseEntity.ok(BaseResponse(error = true, code = 700, message = e.bindingResult.firstErrorMessage()))

    @ExceptionHandler(Exception::class)
    fun handleUncaught(e: Exception): ResponseEntity<BaseResponse> =
        ResponseEntity.status(500).body(BaseResponse(error = true, code = 500, message = "Internal server error"))
}

abstract class BusinessException(val code: Int, message: String) : RuntimeException(message)
class SnackbarException(message: String) : BusinessException(code = 700, message = message)
class DialogException(message: String) : BusinessException(code = 701, message = message)
// 필요에 따라 702/703/705 예외 클래스 추가
```

### Foundation sub-feature 요소 (모두 `docs/features/foundation/`에서 구현)

- [x] Flyway 의존성 + `V1__init.sql` (users 테이블 포함, ADR-0001)
- [ ] `SecurityFilterChain` + JWT 인증 필터 (JJWT 0.12.6)
- [ ] `GlobalExceptionHandler` + `BaseResponse` + `BusinessException` 계층
- [ ] `BaseResponse` + `data class data 상속` 패턴 예시 2개 (`LoginResponse`, 간단한 `ChallengeResponse`)
- [ ] SpringDoc OpenAPI config — JWT Bearer scheme, grouped API
- [ ] CORS — 모바일 origin만 (ADR-0004 Lovable 미배포 결정 반영)
- [ ] Kakao OAuth 교환 엔드포인트 skeleton (ADR-0008 scope=`account_phone_number` 포함)

### 모바일 ↔ 서버 합의

- 모바일(`:remote:datasource`의 `ApiResultCall`)이 이미 `body.code == 200` 기준으로 Success/Failure 분기 — 서버가 이 규약을 따라야 모바일이 자연스럽게 처리.
- 모바일 Ktorfit 응답: `ApiResult<LoginResponse>` — 성공 시 `data`, 실패 시 `CustomError(code=700, message)`.

## 참조

- `.claude/agents/backend-dev.md` "선행 조건" 섹션 (이 ADR 반영)
- `.claude/skills/api-contract/SKILL.md` — BaseResponse 규약 반영 예정
- CarOwnerRenew BaseResponse: `/Users/hwamulman/hwamulman-workspace/CarOwnerRenew/remote/model/src/main/kotlin/ktc/cargo/driver/remote/model/base/BaseResponse.kt`
- CarOwnerRenew ApiCode: `/Users/hwamulman/hwamulman-workspace/CarOwnerRenew/remote/datasource/src/main/kotlin/ktc/cargo/driver/remote/datasource/apiResult/ApiCode.kt`
