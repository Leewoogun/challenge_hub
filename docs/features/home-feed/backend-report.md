# Backend Report — home-feed

- **feature-id**: home-feed
- **작성**: 2026-05-25 by backend-dev
- **상태**: implemented (로컬), 배포 전
- **빌드 검증**: `:app:build` BUILD SUCCESSFUL / 단위·슬라이스 11/11 passed / 통합 테스트 8건 Docker 미가용으로 skip

## 구현 요약

홈 진입 시 단일 호출되는 `GET /api/v1/home` 을 신규 추가했다. 한 read 트랜잭션으로 누적 전적(`user_stats`)과 진행 중 챌린지(`challenges` IN_PROGRESS) + 인증 상태(`verifications`)를 모아 응답한다. 신규 사용자는 user_stats row 가 없어도 0 으로 채워 응답하고, 진행 중 챌린지가 없으면 빈 배열을 반환한다.

스키마는 V1__init.sql 의 `users` / `challenges` / `verifications` / `user_stats` 를 그대로 사용하되, **`verifications` 에 PENDING 상태 표현을 추가**하기 위해 V2 마이그레이션으로 `status / created_at` 컬럼을 추가하고 `photo_url / verified_at` 을 nullable 화했다 (V1 의 NOT NULL 제약은 인증 전 상태를 표현할 수 없음).

인증되지 않은 요청(JWT 없음 / 만료 / 위조)은 ADR-0002 규약대로 **HTTP 200 + code=401** 로 응답하도록 `UnauthorizedEntryPoint` 를 도입했다. 기존 SecurityConfig 의 `anyRequest().authenticated()` 는 기본 403 을 돌려주는데, 모바일 `ApiResultCall` 이 body.code 만 보고 refresh 로직을 분기하므로 401 코드 변환이 필수다.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| GET | /api/v1/home | Bearer JWT | implemented (배포 전) |

응답 shape 은 `docs/features/home-feed/api-contract.md` 100% 준수.
필터: `status = 'IN_PROGRESS'` 만. 정렬: `deadline ASC`. 페이지네이션 없음.

## 변경된 모듈 & 파일

### 신규 파일

| 모듈 | 경로 |
|------|------|
| :domain:model | `domain/model/src/main/kotlin/com/lwg/challenge/domain/challenge/Challenge.kt` (Challenge, ChallengeStatus, ChallengeResult) |
| :domain:model | `domain/model/src/main/kotlin/com/lwg/challenge/domain/verification/Verification.kt` (Verification, VerificationStatus) |
| :domain:model | `domain/model/src/main/kotlin/com/lwg/challenge/domain/userstats/UserStats.kt` (UserStats + empty() default) |
| :domain:repository | `domain/repository/src/main/kotlin/com/lwg/challenge/domain/challenge/ChallengeRepository.kt` |
| :domain:repository | `domain/repository/src/main/kotlin/com/lwg/challenge/domain/userstats/UserStatsRepository.kt` |
| :domain:repository | `domain/repository/src/main/kotlin/com/lwg/challenge/domain/verification/VerificationRepository.kt` |
| :infra:entity | `infra/entity/src/main/kotlin/com/lwg/challenge/infra/entity/challenge/ChallengeEntity.kt` |
| :infra:entity | `infra/entity/src/main/kotlin/com/lwg/challenge/infra/entity/userstats/UserStatsEntity.kt` |
| :infra:entity | `infra/entity/src/main/kotlin/com/lwg/challenge/infra/entity/verification/VerificationEntity.kt` |
| :infra:jpa | `infra/jpa/src/main/kotlin/com/lwg/challenge/infra/jpa/challenge/ChallengeJpaRepository.kt` |
| :infra:jpa | `infra/jpa/src/main/kotlin/com/lwg/challenge/infra/jpa/userstats/UserStatsJpaRepository.kt` |
| :infra:jpa | `infra/jpa/src/main/kotlin/com/lwg/challenge/infra/jpa/verification/VerificationJpaRepository.kt` |
| :infra:repositoryimpl | `infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/challenge/ChallengeRepositoryImpl.kt` |
| :infra:repositoryimpl | `infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/userstats/UserStatsRepositoryImpl.kt` |
| :infra:repositoryimpl | `infra/repositoryimpl/src/main/kotlin/com/lwg/challenge/infra/repositoryimpl/verification/VerificationRepositoryImpl.kt` |
| :service | `service/src/main/kotlin/com/lwg/challenge/service/home/HomeService.kt` |
| :service | `service/src/main/kotlin/com/lwg/challenge/service/home/HomeFeedResult.kt` |
| :controller | `controller/src/main/kotlin/com/lwg/challenge/controller/home/HomeController.kt` |
| :controller | `controller/src/main/kotlin/com/lwg/challenge/controller/home/dto/HomeResponse.kt` (HomeData, UserStatsDto, ActiveChallengeDto) |
| :app | `app/src/main/kotlin/com/lwg/challenge/config/UnauthorizedEntryPoint.kt` |
| :app (test) | `app/src/test/kotlin/com/lwg/challenge/home/HomeIntegrationTest.kt` |
| :app (resources) | `app/src/main/resources/db/migration/V2__home_feed_verification_status.sql` |

### 수정된 파일

| 파일 | 변경 |
|------|------|
| `domain/repository/.../user/UserRepository.kt` | `findById(Long)` + `findAllByIds(Collection<Long>): Map<Long, User>` 추가 (홈 응답에서 상대 닉네임 일괄 조회용) |
| `infra/repositoryimpl/.../auth/UserRepositoryImpl.kt` | 위 두 메서드 구현 추가 |
| `app/src/main/kotlin/.../config/SecurityConfig.kt` | `UnauthorizedEntryPoint` 주입 + `.exceptionHandling { authenticationEntryPoint(...) }` 추가 |
| `app/src/test/kotlin/.../ChallengeServerApplicationTests.kt` | 신규 JPA Repository 3개(`UserStatsJpaRepository` / `ChallengeJpaRepository` / `VerificationJpaRepository`) `@MockitoBean` 추가 — JPA 제외 환경에서 컨텍스트 로드 가능하도록 |

build.gradle.kts / libs.versions.toml 변경 없음. 기존 의존 그래프 (controller → service → domain.repository → domain.model · infra.* → domain.model) 그대로 사용.

## DB 마이그레이션

### V2__home_feed_verification_status.sql (신규)

```sql
ALTER TABLE verifications ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'PENDING';
ALTER TABLE verifications ALTER COLUMN photo_url DROP NOT NULL;
ALTER TABLE verifications ALTER COLUMN verified_at DROP NOT NULL;
ALTER TABLE verifications ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
UPDATE verifications SET status = 'VERIFIED' WHERE photo_url IS NOT NULL;
```

### V1 의 기존 테이블 재사용 (변경 없음)

- `users` — auth-kakao 그대로
- `challenges` — V1 스키마가 spec 요구를 모두 충족 (challenger_id / opponent_id / challenger_mission / opponent_mission / bet_content / deadline / status enum / result enum)
- `user_stats` — V1 컬럼명 `wins / losses / draws / current_streak / max_streak` 그대로 사용. **API 응답 필드명은 win / lose / draw / currentStreak 로 매핑** (api-contract 와 일치). DB 컬럼명을 바꾸지 않은 이유: V1 이 이미 정의된 안정 스키마이고, 매핑은 HomeService 한 곳에서만 일어나므로 굳이 마이그레이션할 필요가 없다.

### user_stats 매핑

| DB 컬럼 | API 필드 |
|---------|---------|
| wins | win |
| losses | lose |
| draws | draw |
| current_streak | currentStreak |

`max_streak` 와 `total_challenges` 는 이번 응답에 미포함 (api-contract 요구 4개 필드만).

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui/index.html
- 신규 등록 경로: `GET /api/v1/home` (Tag: `Home`)
- 응답: `HomeResponse { data: HomeData { stats: UserStatsDto, activeChallenges: List<ActiveChallengeDto> } }`
- 시간 포맷: `Instant` (ISO-8601 UTC) — Jackson 기본 직렬화 + `controller` 모듈의 BaseResponse 상속 패턴 그대로.

## 테스트 결과

```
./gradlew :app:build      → BUILD SUCCESSFUL
./gradlew test (root)     → BUILD SUCCESSFUL
```

| 테스트 | 결과 |
|--------|------|
| PhoneHasherTest (`:core`) | 3/3 passed |
| GlobalExceptionHandlerTest (`:app` slice) | 5/5 passed |
| AuthControllerTest (`:app` slice) | 5/5 passed |
| ChallengeServerApplicationTests (`:app` smoke) | 1/1 passed |
| **HomeIntegrationTest** (`:app` 통합) | **3/3 skipped (Docker 미가용)** |
| AuthKakaoIntegrationTest (`:app` 통합) | 5/5 skipped (Docker 미가용) |
| **합계** | **14 passed, 8 skipped, 0 failed** |

### HomeIntegrationTest 케이스 (Docker 가용 시 실행)

1. **신규 사용자 빈 상태** — user_stats row 없음 + IN_PROGRESS 챌린지 0 → `stats = 0/0/0/0` + `activeChallenges = []`.
2. **챌린지 2건 + 매핑/정렬** — 내가 challenger 인 챌린지 1건 + 내가 opponent 인 챌린지 1건 + 다른 사용자들의 챌린지 + 내가 참여한 COMPLETED 챌린지. 응답에서:
   - COMPLETED · 타 사용자 챌린지는 제외
   - deadline ASC 정렬 (earlier → later)
   - 첫 카드(내가 opponent): `myMission` = `opponent_mission` 매핑, `opponentNickname` = challenger 닉네임
   - 둘째 카드(내가 challenger): 반대로 매핑
   - verification 미존재 row → PENDING / 존재 row → VERIFIED 또는 FAILED 정확 매핑
   - 누적 전적 7/3/2/3 정확 응답
3. **만료/위조 토큰** — `Authorization: Bearer not.a.valid.jwt.token` → JwtAuthenticationFilter 가 SecurityContext 미주입 → `UnauthorizedEntryPoint` 발동 → HTTP 200 + body.code = 401.

테스트 데이터는 `@AfterEach` 에서 verifications → challenges → user_stats → users 순으로 deleteAll (FK 의존 역순).

### Docker 미가용 skip 이유

작업 환경에 docker CLI 가 설치되어 있지 않다 (`docker info` failed). `AuthKakaoIntegrationTest` 와 동일하게 `@EnabledIf("isDockerAvailable")` 로 전체 스킵. 로컬 Docker Desktop 실행 후 `./gradlew :app:test --tests "*HomeIntegrationTest"` 로 수동 검증 가능. CI 환경에서는 docker-in-docker 세팅 후 자동 실행.

## 응답 매핑 규칙 (참고)

```kotlin
// HomeService.getHome(currentUserId) 내부
val myMission = if (c.challengerId == currentUserId) c.challengerMission else c.opponentMission
val opponentMission = if (c.challengerId == currentUserId) c.opponentMission else c.challengerMission
val opponentUserId = if (c.challengerId == currentUserId) c.opponentId else c.challengerId
val opponentNickname = opponentUsers[opponentUserId]?.nickname ?: "(알 수 없음)"

val myStatus = verifications[challengeId to currentUserId] ?: PENDING
val opponentStatus = verifications[challengeId to opponentUserId] ?: PENDING
```

쿼리 수 (현재 사용자 + N 챌린지 기준):
1. user_stats SELECT — 1
2. challenges SELECT (challenger OR opponent + status IN + ORDER BY) — 1
3. users SELECT IN (상대방 N 명) — 1
4. verifications SELECT IN (challenge_id N 개) — 1
→ N + 1 문제 없음 (4 쿼리 고정).

## 미해결 이슈 / 향후 ALTER 후보

1. **Docker 미가용 환경에서 통합 테스트 자동 검증 불가** — AuthKakaoIntegrationTest 와 동일 한계. 로컬 Docker Desktop / CI docker-in-docker 필요.
2. **user_stats 집계 트리거 없음** — 이번 feature 는 read-only. `CHALLENGER_WIN/OPPONENT_WIN/DRAW/BOTH_LOSE` 결과 발생 시 `wins/losses/draws/current_streak` 를 갱신하는 로직은 별도 feature (challenge-result-judgment 등) 에서 구현 예정.
3. **CONTRACT_SIGNING 포함 여부** — spec.md 리스크에 명시. 1차는 `IN_PROGRESS` 만. 확장 필요 시 `HomeService.ACTIVE_STATUSES` 한 줄 추가.
4. **인증 미존재 row 자동 생성 안 함** — 챌린지가 IN_PROGRESS 가 되는 시점(계약 확정 후)에 `verifications` 에 PENDING row 2개를 자동 생성하는 로직이 별도 feature 필요. 현재는 row 부재 시 응답에서 PENDING 으로 채워주는 방어 코드만 있음.
5. **deadline timezone 가정** — DB `TIMESTAMP` (TZ 없음) 를 UTC 로 간주하여 `Instant` 변환. 챌린지 생성 feature 에서 저장 시점에도 UTC 기준으로 저장해야 일관됨 — 챌린지 생성 feature 작성 시 명시 필요. 추후 `TIMESTAMPTZ` 전환 후보.
6. **동시 진행 한도 정책 미정** — spec.md 가 "사용자당 동시 진행 한도(별도 정책)" 라고만 명시. 한도 enforcement 는 별도 feature.
7. **응답 컬럼 nullable 일관성** — 모바일 측은 빈 배열 / 0 으로 받지만, opponentNickname 안전망이 `"(알 수 없음)"` 하드코딩. 정상 케이스(상대도 ACTIVE 사용자) 에서는 발생하지 않으며, SOFT_DELETE 정책 도입 전엔 문제 없음.

## mobile-dev 에게 전달할 주의사항

1. **`deadline` 은 `Instant` (ISO-8601 UTC).** Kotlin Multiplatform 의 `kotlinx.datetime.Instant` 또는 `kotlinx.serialization` Instant 직렬화 사용. 모바일 표시용 "5시간 32분 남음" 은 클라이언트에서 계산.
2. **`VerificationStatus` enum 값 3종** — `PENDING` / `VERIFIED` / `FAILED`. Lovable mock 의 소문자 (`pending` / `verified` / `failed`) 와 케이스만 다름. 모바일 쪽 enum 도 대문자로 통일하거나 case-insensitive 매핑 사용 권장.
3. **빈 상태 판정 로직은 클라이언트 책임** — 백엔드는 `stats = 0/0/0/0` + `activeChallenges = []` 를 동일하게 응답한다. "신규" vs "기존이지만 챌린지 0개" 구분은 모바일이 `stats.win + lose + draw + currentStreak == 0` 으로 한다 (api-contract 명시).
4. **401 응답 shape** — `{ "error": true, "code": 401, "message": "토큰 만료 — Refresh" }` (data 필드 없음). `ApiResultCall` 기존 처리로 자연스럽게 refresh 트리거.
5. **`opponentNickname` 길이** — DB 의 `users.nickname VARCHAR(50)` 그대로. UI 에서 한 줄 truncation 필요할 수 있음.

## 참고 링크

- spec: `docs/features/home-feed/spec.md`
- contract: `docs/features/home-feed/api-contract.md`
- 관련 ADR: 0001 (Flyway) · 0002 (BaseResponse + foundation)
- 기존 auth-kakao backend-report (테스트 패턴 참조): `docs/features/auth-kakao/backend-report.md`
- V2 마이그레이션: `challenge-server/app/src/main/resources/db/migration/V2__home_feed_verification_status.sql`
