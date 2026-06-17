# Backend Report — auth-refresh-rotation

- **커밋**: `dfecba5` "feat: Rotation Refresh token 처리 추가" (2026-05-28)
- **변경 파일 수**: 11 / +188 / -16
- **빌드 / 테스트**: 신규 단위 테스트 없음. 기존 테스트 회귀는 백엔드 dev 본인이 확인 (이번 PM 정리 시점에 별도 재실행은 안 함 — 본 작업은 코드 변경 0건의 사후 박제).

## 변경 개요

`foundation` Sprint 0의 단순 refresh를 다음으로 교체:
- DB에 sha256(rawRefreshToken) hash 저장.
- `refresh` 호출 시 새 access + 새 refresh 발급, hash 회전.
- 검증 실패 모든 경로를 동일 401 응답으로 통일.

## V3 마이그레이션

**파일**: `app/src/main/resources/db/migration/V3__users_refresh_token.sql`

```sql
ALTER TABLE users ADD COLUMN refresh_token_hash VARCHAR(64);
ALTER TABLE users ADD COLUMN refresh_token_issued_at TIMESTAMP;
```

- 컬럼 둘 다 nullable. 길이 `VARCHAR(64)` — sha256 hex 고정 길이.
- V1 가입자는 hash NULL → 다음 refresh에서 401 → 카카오 재로그인 → 그때부터 rotation.
- logout/강제 무효화 시 NULL 권장 (둘 다 같이).

## RefreshTokenHasher (신규)

**파일**: `core/src/main/kotlin/com/lwg/challenge/core/hash/RefreshTokenHasher.kt`

```kotlin
object RefreshTokenHasher {
    fun hash(rawToken: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(rawToken.toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it) }
    }
}
```

- 입력이 JWT 고엔트로피 문자열이라 salt 불필요. 비밀번호 hash가 아닌 lookup key 용도.
- `PhoneHasher`와 같은 `core/hash` 패키지 — 해시 유틸 일관 위치.
- 반환은 항상 64자 lower-case hex.

## AuthService 변경

**파일**: `service/src/main/kotlin/com/lwg/challenge/service/auth/AuthService.kt`

### login(): refresh hash 저장 추가

기존 카카오 로그인 흐름 끝부분에 hash 저장 1단계 추가.

```kotlin
val accessToken = jwtTokenProvider.generateAccessToken(userId)
val refreshToken = jwtTokenProvider.generateRefreshToken(userId)

userRepository.updateRefreshTokenHash(
    userId = userId,
    hash = RefreshTokenHasher.hash(refreshToken),
    issuedAt = LocalDateTime.now(),
)

return LoginResult(...)
```

### refresh() 신규 (이전엔 Controller가 직접 처리)

```kotlin
@Transactional
fun refresh(refreshToken: String): RefreshResult {
    val userId = jwtTokenProvider.verifyAndGetUserId(
        refreshToken,
        expectedType = JwtTokenProvider.TOKEN_TYPE_REFRESH,
    ) ?: throw UnauthorizedException(REFRESH_INVALID_MESSAGE)

    val user = userRepository.findById(userId)
        ?: throw UnauthorizedException(REFRESH_INVALID_MESSAGE)

    val incomingHash = RefreshTokenHasher.hash(refreshToken)
    if (user.refreshTokenHash == null || user.refreshTokenHash != incomingHash) {
        throw UnauthorizedException(REFRESH_INVALID_MESSAGE)
    }

    val newAccessToken = jwtTokenProvider.generateAccessToken(userId)
    val newRefreshToken = jwtTokenProvider.generateRefreshToken(userId)

    userRepository.updateRefreshTokenHash(
        userId = userId,
        hash = RefreshTokenHasher.hash(newRefreshToken),
        issuedAt = LocalDateTime.now(),
    )

    log.info("refresh token rotated: userId={}", userId)
    return RefreshResult(newAccessToken, newRefreshToken)
}
```

- `@Transactional` — JWT 검증과 hash UPDATE를 한 트랜잭션. 실패 시 hash 갱신 롤백.
- 모든 실패 경로가 동일 `UnauthorizedException(REFRESH_INVALID_MESSAGE)` → `GlobalExceptionHandler`가 BaseResponse `code=401`로 변환.
- 성공 시 `log.info`만 — 실패는 GlobalExceptionHandler가 일관 처리하므로 별도 로그 미생성 (필요 시 audit feature에서 추가).

### RefreshResult (신규)

**파일**: `service/src/main/kotlin/com/lwg/challenge/service/auth/RefreshResult.kt`

```kotlin
data class RefreshResult(val accessToken: String, val refreshToken: String)
```

Controller가 `RefreshData`(HTTP DTO)로 변환.

## AuthController 변경

**파일**: `controller/src/main/kotlin/com/lwg/challenge/controller/auth/AuthController.kt`

- 기존: Controller가 `JwtTokenProvider` 직접 의존 → `verifyAndGetUserId` 호출 후 새 access 만들어 반환.
- 변경: `authService.refresh()` 위임. Controller에서 `JwtTokenProvider` import 제거.
- OpenAPI 설명 갱신:
  - summary: "Access Token 재발급" → "Access Token 재발급 (Rotation)"
  - description: "Refresh Token 자체는 재발급하지 않는다" → "새 access + 새 refresh 를 함께 발급한다. 이전 refresh 는 즉시 무효화된다."

## DTO 변경

**파일**: `controller/src/main/kotlin/com/lwg/challenge/controller/auth/dto/RefreshResponse.kt`

```kotlin
data class RefreshData(
    @field:Schema(example = "eyJhbGciOi...")
    val accessToken: String,
    @field:Schema(
        example = "eyJhbGciOi...",
        description = "회전된 새 refresh token. 클라이언트는 로컬 저장소를 이 값으로 덮어써야 한다.",
    )
    val refreshToken: String,
)
```

## Domain / Repository 변경

**파일**: `domain/model/src/main/kotlin/com/lwg/challenge/domain/user/User.kt`

```kotlin
data class User(
    ...,
    val refreshTokenHash: String? = null,
    val refreshTokenIssuedAt: LocalDateTime? = null,
)
```

**파일**: `domain/repository/src/main/kotlin/com/lwg/challenge/domain/user/UserRepository.kt`

```kotlin
interface UserRepository {
    fun findByKakaoId(kakaoId: Long): User?
    fun findById(id: Long): User?  // 신규
    fun save(user: User): User
    fun updateRefreshTokenHash(userId: Long, hash: String?, issuedAt: LocalDateTime?)  // 신규
}
```

**파일**: `infra/jpa/.../UserJpaRepository.kt`

```kotlin
@Modifying
@Query("""
    UPDATE UserEntity u
       SET u.refreshTokenHash = :hash,
           u.refreshTokenIssuedAt = :issuedAt
     WHERE u.id = :userId
""")
fun updateRefreshTokenHash(@Param("userId") userId: Long, @Param("hash") hash: String?, @Param("issuedAt") issuedAt: LocalDateTime?): Int
```

- 영속 컨텍스트 dirty checking 대신 핀포인트 UPDATE — rotation은 logical update 아님 (`@PreUpdate`로 `updated_at` 자동 갱신되면 의미 왜곡).
- `updated_at`은 의도적으로 건드리지 않음.

**파일**: `infra/repositoryimpl/.../UserRepositoryImpl.kt`

위 두 신규 메서드 위임 구현 추가.

**파일**: `infra/entity/.../UserEntity.kt`

`refreshTokenHash`, `refreshTokenIssuedAt` 두 필드 추가. `toDomain()` / `fromDomain()` 양방향 매핑 갱신.

## 검증

- **단위 테스트 신규 0**. 권장 케이스(backlog 등재):
  - 정상 rotation
  - 옛 refresh 재사용 (hash 불일치) → 401
  - V1 가입자 (hash NULL) → 401
  - JWT 만료 → 401
  - tokenType=access를 refresh로 보냄 → 401
- **회귀**: 기존 AuthControllerTest 5/5, ChallengeServerApplicationTests, AuthKakaoIntegrationTest는 본 변경에 영향받지 않음 (refresh 응답 DTO에 필드 추가는 backward-compatible).
- **수동 검증 권장**: backlog "백엔드" 섹션 신규 항목 참조.

## 변경 파일 목록

```
A app/src/main/resources/db/migration/V3__users_refresh_token.sql
M controller/src/main/kotlin/com/lwg/challenge/controller/auth/AuthController.kt
M controller/src/main/kotlin/com/lwg/challenge/controller/auth/dto/RefreshResponse.kt
A core/src/main/kotlin/com/lwg/challenge/core/hash/RefreshTokenHasher.kt
M domain/model/src/main/kotlin/com/lwg/challenge/domain/user/User.kt
M domain/repository/src/main/kotlin/com/lwg/challenge/domain/user/UserRepository.kt
M infra/entity/src/main/kotlin/com/lwg/challenge/infra/entity/auth/UserEntity.kt
M infra/jpa/src/main/kotlin/com/lwg/challenge/infra/jpa/auth/UserJpaRepository.kt
M infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/auth/UserRepositoryImpl.kt
M service/src/main/kotlin/com/lwg/challenge/service/auth/AuthService.kt
A service/src/main/kotlin/com/lwg/challenge/service/auth/RefreshResult.kt
```
