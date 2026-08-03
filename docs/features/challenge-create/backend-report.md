# Backend Report — challenge-create

- **feature-id**: challenge-create
- **작성**: 2026-07-28 by backend-dev
- **상태**: implemented (로컬), 배포 전, **커밋 안 함**
- **선행 입력**: [spec.md](./spec.md), [api-contract.md](./api-contract.md) (status: `confirmed`)
- **빌드 검증**: `./gradlew clean build` → **BUILD SUCCESSFUL** / 실행 테스트 **111/111 passed, 0 failed** / 통합 45건 Docker 미가용 skip

## 구현 요약

`challenges` 테이블에 **최초의 INSERT 경로**를 열었다. 기존 `home-feed`는 read-only였고 `friends`는 다른 테이블이라, 이 feature 전에는 어떤 경로로도 챌린지가 생성되지 않았다.

엔드포인트 5건(`ChallengeCommandController` + `ChallengeCommandService`)과 마이그레이션 V5 1건을 추가했다. 조회 전용 `GET /challenges/active`(home-feed)는 손대지 않았고 응답 shape도 그대로다 — 같은 `/api/v1/challenges` 네임스페이스에 신규 경로만 얹었다.

세 가지가 이 feature의 핵심 난점이었고 각각 대응했다:

1. **KST 자정 vs UTC 저장** — 챌린지의 "하루"는 KST로 끊는데 DB `TIMESTAMP`는 UTC로 간주한다. 두 축이 섞이면 15:00Z 근처에서 하루가 어긋난다. `KstDeadlineCalculator`(`:core`)로 환산을 한곳에 몰고 **경계값 17건을 테스트로 못박았다.**
2. **양방향 중복의 실제 보장** — 애플리케이션 사전 검사만으로는 동시 요청을 막을 수 없다(READ COMMITTED에서 상대의 미커밋 INSERT는 안 보인다). V5에 **부분 유니크 인덱스**를 추가해 DB가 최종 방어선이 되게 했다.
3. **`message`가 곧 UI 텍스트** — 모바일 error-channel이 `code`를 버리고 `message`만 ViewModel에 전달한다(mobile-dev 확인). 모든 문구를 `companion object` 상수로 고정하고 **슬라이스 테스트가 문자열을 그대로 assert**한다.

## 엔드포인트

| Method | Path | 인증 | 상태 | 매핑 |
|--------|------|------|------|------|
| POST | `/api/v1/challenges` | Bearer JWT | implemented | `ChallengeCommandController.create` → `ChallengeCommandService.create` |
| GET | `/api/v1/challenges/received` | Bearer JWT | implemented | `.listReceived` → `.listReceived` |
| POST | `/api/v1/challenges/{id}/accept` | Bearer JWT | implemented | `.accept` → `.accept` |
| POST | `/api/v1/challenges/{id}/reject` | Bearer JWT | implemented | `.reject` → `.reject` |
| DELETE | `/api/v1/challenges/{id}` | Bearer JWT | implemented | `.cancel` → `.cancel` |

계약(`api-contract.md`, `confirmed`) 100% 준수. 계약 대비 차이 **없음** — 협의에서 합의된 변경(에러 문구 확정, DELETE `data.challengeId` 추가, `createdAt` 초 절삭)은 모두 계약서에 먼저 반영한 뒤 구현했다.

### 엔드포인트별 동작

**1. POST `/challenges`** — 검증 순서는 **싼 것 → 비싼 것**(앞에서 걸리면 뒤 쿼리를 안 친다):

| 순서 | 검증 | 실패 시 code / message |
|---|---|---|
| 1 | 본인 여부 (무비용) | 700 `자기 자신에게는 챌린지를 걸 수 없어요` |
| 2 | 미션 trim 후 1~100자 | 700 `미션은 1자 이상 100자 이하로 입력해주세요` |
| 3 | 내기 trim 후 1~100자 | 700 `내기 내용은 1자 이상 100자 이하로 입력해주세요` |
| 4 | 상대 존재 + ACTIVE (1 쿼리) | 700 `상대를 찾을 수 없어요` |
| 5 | ACCEPTED 친구 관계 (1 쿼리) | 700 `친구에게만 챌린지를 걸 수 있어요` |
| 6 | 양방향 중복 (1 쿼리) | 700 — 아래 2종 분기 |

중복 문구 2종 분기: 역방향 PENDING이면 `이 친구가 이미 도전장을 보냈어요. 받은 도전장을 확인해보세요`, 그 외(내가 건 PENDING / 양방향 IN_PROGRESS)는 `오늘은 이 친구와 이미 챌린지가 있어요`.
SUSPENDED/DELETED 사용자는 "존재하지 않음"과 같은 문구로 응답한다 — 계정 상태를 흘리지 않기 위함(friends 검색과 동일 방침).

**2. GET `/challenges/received`** — `opponent_id = me AND status = 'PENDING' AND deadline > now()`, `created_at DESC`. users JOIN 1쿼리로 챌린저 닉네임/프로필을 함께 가져온다(N+1 없음). 마감 지난 row는 **DB에서 `PENDING`인 채로 두고 응답에서만 제외**(lazy expiry).

**3. POST `/{id}/accept`** — 검증 순서가 의미를 만든다: **권한을 상태보다 먼저** 본다. 당사자가 아닌 사람에게 "이미 처리된 챌린지예요"라고 알려주면 남의 챌린지 상태가 새어나가기 때문이다. 단일 트랜잭션으로 `challenges` UPDATE + `verifications` INSERT 2건.

**4. POST `/{id}/reject`** — `REJECTED`로 UPDATE, row 보존. REJECTED는 중복 검사 대상이 아니므로 같은 날 재도전이 가능하다.

**5. DELETE `/{id}`** — 물리 삭제. **마감 경과를 막지 않는다** — 마감 지난 내 도전장을 치우는 것은 사용자에게 유익하고 계약 §5 에러 표에도 마감 항목이 없다.

## 변경된 모듈 & 파일 (절대 경로)

### 신규 (production)

| 모듈 | 파일 |
|---|---|
| `:core` | `/Users/hwamulman/woogunProject/challenge/challenge-server/core/src/main/kotlin/com/lwg/challenge/core/challenge/KstDeadlineCalculator.kt` (DeadlineType, ChallengeSchedule, KstDeadlineCalculator) |
| `:domain:model` | `/Users/hwamulman/woogunProject/challenge/challenge-server/domain/model/src/main/kotlin/com/lwg/challenge/domain/challenge/ReceivedChallenge.kt` |
| `:service` | `/Users/hwamulman/woogunProject/challenge/challenge-server/service/src/main/kotlin/com/lwg/challenge/service/challenge/ChallengeCommandService.kt` |
| `:controller` | `/Users/hwamulman/woogunProject/challenge/challenge-server/controller/src/main/kotlin/com/lwg/challenge/controller/challenge/ChallengeCommandController.kt` |
| `:controller` | `/Users/hwamulman/woogunProject/challenge/challenge-server/controller/src/main/kotlin/com/lwg/challenge/controller/challenge/dto/ChallengeCommandDtos.kt` |
| `:app` | `/Users/hwamulman/woogunProject/challenge/challenge-server/app/src/main/kotlin/com/lwg/challenge/config/ClockConfig.kt` |
| `:app` (resources) | `/Users/hwamulman/woogunProject/challenge/challenge-server/app/src/main/resources/db/migration/V5__challenge_create_opponent_mission_nullable.sql` |

### 신규 (test)

| 위치 | 파일 |
|---|---|
| `:core` 단위 | `/Users/hwamulman/woogunProject/challenge/challenge-server/core/src/test/kotlin/com/lwg/challenge/core/challenge/KstDeadlineCalculatorTest.kt` |
| `:service` 단위 | `/Users/hwamulman/woogunProject/challenge/challenge-server/service/src/test/kotlin/com/lwg/challenge/service/challenge/ChallengeCommandServiceTest.kt` |
| `:app` 슬라이스 | `/Users/hwamulman/woogunProject/challenge/challenge-server/app/src/test/kotlin/com/lwg/challenge/controller/challenge/ChallengeCommandControllerTest.kt` |
| `:app` 통합 | `/Users/hwamulman/woogunProject/challenge/challenge-server/app/src/test/kotlin/com/lwg/challenge/integration/ChallengeCreateIntegrationTest.kt` |

### 수정

| 파일 | 변경 |
|---|---|
| `domain/model/.../challenge/Challenge.kt` | `opponentMission: String` → `String?` (PENDING 구간에는 값이 없다) |
| `infra/entity/.../challenge/ChallengeEntity.kt` | `@Column(nullable=false)` 제거 + 기본값 null |
| `service/.../challenge/ActiveChallengeService.kt` | nullable화로 인한 유일한 컴파일 파손 지점. `orEmpty()` 방어 — IN_PROGRESS만 읽으므로 실제로는 항상 non-null |
| `domain/repository/.../challenge/ChallengeRepository.kt` | `findReceivedPending` / `findConflicting` / `saveAndFlush` / `deleteById` 추가 |
| `infra/jpa/.../challenge/ChallengeJpaRepository.kt` | `findConflicting`(JPQL) / `findReceivedPending`(native, users JOIN) 추가 |
| `infra/repositoryimpl/.../challenge/ChallengeRepositoryImpl.kt` | 위 구현 + Object[] → 도메인 매핑 |
| `domain/repository/.../verification/VerificationRepository.kt` | `saveAllAndFlush` 추가 |
| `infra/repositoryimpl/.../verification/VerificationRepositoryImpl.kt` | 위 구현 |

`build.gradle.kts` / `libs.versions.toml` 변경 **없음**. 기존 의존 그래프 그대로.

## DB 마이그레이션

### V5__challenge_create_opponent_mission_nullable.sql (신규, 2개 블록)

```sql
-- 1. PENDING 구간에는 상대 미션이 없다 (spec 결정 2)
ALTER TABLE challenges ALTER COLUMN opponent_mission DROP NOT NULL;

-- 2. 양방향 중복 차단 (방향 무관 유일성)
CREATE UNIQUE INDEX uq_challenges_active_pair_date
    ON challenges (LEAST(challenger_id, opponent_id), GREATEST(challenger_id, opponent_id), challenge_date)
 WHERE status IN ('PENDING', 'IN_PROGRESS');
```

번호는 V5 — 현재 적용본이 V1, V3, V4다(V2는 비어 있음, V4 주석 참조). 기존 row 백필 불필요(challenges에 프로덕션 데이터 없음).

**⚠️ 2번 블록은 T-B1 원래 범위("opponent_mission 완화") 밖의 추가다.** 근거: spec 수용 기준 "같은 상대 + 같은 `challenge_date`에 PENDING/IN_PROGRESS가 있으면 생성이 거부된다"를 애플리케이션 검사만으로는 **만족시킬 수 없다.** Postgres 기본 격리수준 READ COMMITTED에서 동시 트랜잭션의 미커밋 INSERT는 서로 보이지 않아, 두 요청이 동시에 사전 검사를 통과하면 중복 2건이 그대로 커밋된다. 이 인덱스가 있어야 `DataIntegrityViolationException` → code 700 백업 catch가 friends 2차 `sendRequest`와 동일하게 실제로 동작한다(제약이 없으면 그 catch는 dead code다). **pm-lead 승인 필요 시 되돌릴 수 있으나, 되돌리면 위 수용 기준은 "best-effort"로 강등된다.**

`verifications`는 건드리지 않았다 — V4가 이미 `photo_url`/`verified_at` nullable화 + `status` DEFAULT `'PENDING'` + `created_at`을 마쳐 뒀다(계약 오픈이슈 1에서 확인된 대로).

## 테스트 결과

### 실행된 테스트: **111/111 passed, 0 failed**

| 테스트 | 결과 | 비고 |
|--------|------|------|
| **KstDeadlineCalculatorTest** (`:core` 단위) | **17/17 passed** | 신규 |
| **ChallengeCommandServiceTest** (`:service` 단위) | **39/39 passed** | 신규 |
| **ChallengeCommandControllerTest** (`:app` 슬라이스) | **18/18 passed** | 신규 |
| PhoneHasherTest (`:core`) | 3/3 passed | 회귀 0 |
| FriendServiceEscapeForLikeTest (`:service`) | 6/6 passed | 회귀 0 |
| FriendControllerTest (`:app` 슬라이스) | 15/15 passed | 회귀 0 |
| AuthControllerTest (`:app` 슬라이스) | 5/5 passed | 회귀 0 |
| GlobalExceptionHandlerTest (`:app` 슬라이스) | 5/5 passed | 회귀 0 |
| UserControllerTest (`:app` 슬라이스) | 2/2 passed | 회귀 0 |
| ChallengeServerApplicationTests (smoke) | 1/1 passed | 회귀 0 |

### 🔴 실행되지 않은 테스트: 통합 45건 전부 skip (Docker 미가용)

| 테스트 | 결과 |
|--------|------|
| **ChallengeCreateIntegrationTest** | **21 tests, 21 skipped** (신규) |
| FriendIntegrationTest | 9 skipped |
| AuthKakaoIntegrationTest | 5 skipped |
| UserIntegrationTest | 4 skipped |
| ActiveChallengeApiIntegrationTest | 3 skipped |
| RecordApiIntegrationTest | 3 skipped |

작업 환경에 Docker가 없다(`docker info` 실패, Docker Desktop/OrbStack/Colima/podman 모두 미설치). 기존 통합 테스트 전부와 동일한 `@EnabledIf` 가드 패턴이라 신규 도입 문제는 아니지만, **본 feature에서는 이 skip이 특히 아프다** — V5 마이그레이션과 native 쿼리는 DB를 타야만 검증되고 단위/슬라이스 테스트가 전혀 커버하지 못한다.

### 그래서 로컬 Postgres 16.13으로 직접 검증했다 (Docker 대체)

`localhost:5432`에 Postgres가 떠 있어, **일회용 DB `challenge_v5_scratch`를 만들어** V1→V3→V4→V5를 순서대로 적용하고 수동 검증한 뒤 **DROP했다**(기존 `challenge` DB는 건드리지 않음).

마이그레이션 4건 전부 오류 없이 적용됐고:

| # | 검증 | 결과 |
|---|---|---|
| — | `opponent_mission` nullability | `YES` (challenger_mission은 `NO` 유지) |
| — | 인덱스 생성 확인 | `uq_challenges_active_pair_date` 존재, 정의 일치 |
| 1 | 정방향 PENDING INSERT | 허용 ✅ |
| 2 | **역방향** 같은날 중복 | **BLOCKED** ✅ (방향 무관 유일성 동작) |
| 3 | 정방향 같은날 중복 | **BLOCKED** ✅ |
| 4 | 같은 쌍 + 다른 날짜 | 허용 ✅ |
| 5 | IN_PROGRESS와 충돌 | **BLOCKED** ✅ |
| 6 | REJECTED 같은 쌍·같은날 2건 | 둘 다 허용 ✅ (재도전 보장) |
| 7 | REJECTED만 있는 날짜에 새 PENDING | 허용 ✅ |
| 8 | `opponent_mission IS NULL` row | 5건 저장됨 ✅ (V1 NOT NULL이었다면 불가능) |

추가로 `findReceivedPending`의 native SQL을 실제 Postgres에서 실행해 확인: 마감 지난 건 제외 ✅ / 내가 보낸 건 제외 ✅ / users JOIN으로 닉네임·프로필 조회 ✅ / `created_at DESC` 정렬 ✅.

**다만 이것은 SQL 레벨 검증이지 애플리케이션 end-to-end 검증이 아니다.** JPA 매핑·Flyway 자동 적용·Security 필터·직렬화가 실제로 맞물리는지는 `ChallengeCreateIntegrationTest` 21건이 Docker 환경에서 실행돼야 확인된다. **배포 전 필수 관문으로 남겨둔다.**

### 신규 테스트가 커버하는 것

**KstDeadlineCalculatorTest (17)** — 계약서 예시값 일치 / `15:00Z` 전후 UTC↔KST 날짜 경계 4케이스 / UTC 자정 전후 2케이스 / **"오늘 자정 = 오늘의 끝이지 시작이 아님" 회귀 방지**(`atStartOfDay()`로 잘못 구현하면 이미 지난 시각이 나온다) / 심야 TOMORROW 구제 / 월말·연말·윤년 / 마감 정각은 유효 / deadline을 KST로 오해석하면 깨지는 테스트 / 생성 직후 만료 판정 안 됨(5×2 조합).

**ChallengeCommandServiceTest (39)** — in-memory fake repository 4종 + `Clock.fixed`. Mockito 대신 fake를 쓴 이유: 이 서비스의 핵심이 "여러 저장소에 걸친 상태 전이"라 호출 검증보다 **저장된 결과를 읽어 확인**하는 편이 회귀를 잘 잡는다(수락 시 verifications 2건 같은 것). 중복 판정 6케이스(양방향·IN_PROGRESS·REJECTED 재도전·날짜 다름·다른 친구), 권한 6케이스(**권한 검사가 상태 검사보다 먼저**임을 명시 검증 — 제3자에게 남의 챌린지 상태를 흘리지 않는다), 마감 경계 2케이스(정각 유효 / 1초 후 거부), 길이·trim 5케이스.

**ChallengeCommandControllerTest (18)** — 대부분이 **직렬화 고정**이 목적이다. `challengeDate`가 `"2026-07-28"` 문자열인지(배열 `[2026,7,28]` 회귀 차단), `deadline`/`createdAt`이 `Z` suffix인지, `createdAt`의 나노초가 잘리는지를 jsonPath로 **문자열 그대로** assert한다. 에러 문구 7건도 글자 그대로 검증 — `message`가 UI 텍스트라 오타·영문 유출이 곧 사용자 노출이다.

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui/index.html
- JSON spec: http://localhost:8080/v3/api-docs
- 신규 등록 경로: `POST /api/v1/challenges`, `GET /api/v1/challenges/received`, `POST /api/v1/challenges/{id}/accept`, `POST /api/v1/challenges/{id}/reject`, `DELETE /api/v1/challenges/{id}`
- Tag: `Challenge` (기존 `ActiveChallengeController`와 공유). 전 endpoint `@SecurityRequirement(name="bearerAuth")`.
- 요청/응답 DTO에 `@Schema(description, example)` 부착 — mobile-dev의 Ktorfit 매핑 참조용.

## 계약 협의 결과 (draft → confirmed)

mobile-dev와 1왕복으로 합의. 오픈 이슈 4건 해소, 신규 1건은 별도 트랙 분리.

| # | 이슈 | 결론 |
|---|---|---|
| 1 | 700 vs 705 배분 | **서버는 초안 배분 유지.** 단 모바일 error-channel(`onError: (String) -> Unit`)이 `code`를 버려서 분기 불가 — 계약에 명시하고 모바일 동작을 "실패 시 항상 목록 재조회"로 확정. 부수적으로 **모든 message를 사용자 노출 확정 문구화**, `권한이 없어요` → `내가 받은/보낸 도전장이 아니에요` 교체 |
| 2 | 중복 양방향 | **양방향 유지.** 역방향 PENDING만 별도 문구로 분기 |
| 3 | 100자 | **유지.** UTF-16 code unit 카운팅(양측 `String.length` 자동 일치). 모바일이 `maxLength=100` 하드캡 → 서버 700은 최종 방어선 |
| 4 | 응답 shape | `challengeDate` 평문 ISO date 강제(모바일 kotlinx-datetime 미도입), `Z` suffix 고정 + `createdAt` 초 절삭, DELETE에 `data.challengeId` 추가 |
| 5 | **보낸 도전장 조회 부재** (신규) | **옵션 C 확정** (사용자 결정). `/sent` 미도입, 엔드포인트 5건 유지. DELETE는 계약대로 구현하되 모바일 호출부 없음 → 서버 테스트 전용 검증. (A)는 실제 비용이 design·모바일에 쏠려 기각, (B)는 방향별 필드 오독이 조용히 통과한다는 mobile-dev 근거로 기각 |

계약 상태: **`confirmed`, 오픈 이슈 5건 전부 해소, 미결 항목 0건.**

mobile-dev 질의였던 **read-after-write 보장**은 확답했다: `@Transactional`이 service 메서드에 걸려 컨트롤러가 응답을 직렬화하기 전에 커밋이 끝나고, 리드 리플리카 없는 단일 Postgres다. 통합 테스트에 accept → 즉시 `/active` + `/received` 조회 시나리오를 넣어 검증한다(현재 skip 상태).

## 미해결 이슈

### 1. ✅ end-to-end 통합 검증 완료 (#7, 2026-07-31) — **58/58 PASS, 0 FAIL**

Docker 미가용으로 `ChallengeCreateIntegrationTest` 21건은 여전히 skip이지만, **실행 중인 실서버 + 실 Postgres에 실제 JWT로 HTTP 호출해 같은 층을 전부 훑었다.** Docker 통합 테스트가 검증하려던 JPA 매핑·Flyway 적용·Security 필터·직렬화가 모두 이 경로에 포함된다.

`datetime-model-migration` 직전의 **baseline**이기도 하다.

| 구간 | 케이스 | 결과 |
|---|---|---|
| 1. 생성 | code/status/challengeDate(KST 오늘)/deadline 표기 + DB `opponent_mission IS NULL`(V5 검증) | 7/7 |
| 2. 검증 규칙 | 본인·친구아님·정방향중복·**역방향중복**·미션101자·내기공백 (코드 + 확정 문구 전건) | 12/12 |
| 3. 받은 도전장 | JOIN 필드 6종 + `createdAt` 형태 + 내가 보낸 건 제외 | 9/9 |
| 4. 수락 + **read-after-write** | 제3자 차단 → 수락 → `verifications` 2건 PENDING → **지연 없이 즉시** `/active` 1건·`/received` 0건·양측 미션 매핑 → 재수락 705 | 17/17 |
| 5. 거절 | TOMORROW 생성(challengeDate=내일) → REJECTED → row 보존 → 같은 날 재도전 가능 | 6/6 |
| 6. 취소 | 권한 위반 700 → 취소 200 + `data.challengeId` → 물리 삭제 → IN_PROGRESS 705 → 없는 id 705 | 8/8 |
| 7. 미인증 | 무토큰 → code 401 | 2/2 |
| **합계** | | **58/58 PASS, 0 FAIL** |

검증된 핵심:
- **V5 마이그레이션이 실 DB에 적용돼 동작한다** — `opponent_mission NULL` INSERT 성공, `uq_challenges_active_pair_date`가 정방향·역방향 중복을 모두 차단.
- **read-after-write 보장이 실제로 성립한다** — 수락 응답 직후 지연·재시도 없이 `/active`에 잡히고 `/received`에서 사라진다. mobile-dev에게 확답했던 내용이 실측으로 확인됐다.
- **에러 문구가 계약과 글자 단위로 일치한다** — 문구 7종 전건.

**baseline 시간 표기 (마이그레이션 후 비교용)**:
```
deadline  = "2026-07-31T15:00:00Z"   (KST 08-01 00:00)
createdAt = "2026-07-31T00:31:01Z"   (밀리초 없음 — 초 단위 절삭 동작 확인)
DB 저장값  = 2026-07-31 15:00:00     (challenges.deadline)
```

#### DB 조작 내역 (전량 원복 완료)

pm-lead 승인 하에 실 DB(`challenge`)에 시드를 넣고 **전부 삭제했다**. 실사용자(id=1)는 건드리지 않았다.

- 삽입: `users` 2행(`kakao_id` 999000001 `베이스라인친구` / 999000002 `남남`), `friendships` 1행(1↔친구 ACCEPTED), 테스트 중 생성된 `challenges` 3행 + `verifications` 2행
- 삭제: 위 전부 (`kakao_id 999000001/2`로만 식별하는 idempotent 스크립트)
- **정리 후 상태**: `users=1 friendships=0 challenges=0 verifications=0 user_stats=0` — 시작 시점과 동일
- **실사용자 1행 무결성 확인**: `created_at 2026-05-07 10:10:42.443862` / `updated_at 2026-07-28 11:01:23.650844` / `refresh_token_issued_at 2026-07-31 08:55:05.415106` — 검증 전후 완전 동일

#### 여전히 남는 것

`ChallengeCreateIntegrationTest` 21건은 Docker가 없어 **자동화된 형태로는 미실행**이다. 위 수동 검증이 같은 층을 덮지만 CI에서 반복되지 않으므로, 런타임 확보 시 `./gradlew :app:test --tests "*ChallengeCreateIntegrationTest"`로 회귀 자동화가 필요하다(백로그 🔴 등재됨).

### 2. ✅ 보낸 도전장 조회 엔드포인트 부재 — **해소 (옵션 C 확정)**

2026-07-28 사용자 결정으로 **옵션 C** 채택. `GET /challenges/sent`는 도입하지 않고 엔드포인트는 5건 그대로다.

**코드 변경 없음** — 이미 C에 부합하게 구현돼 있었다. `DELETE /challenges/{id}`는 권한·상태·존재 검증을 전부 포함해 계약대로 구현했고, `/sent`는 만들지 않았다.

취소 엔드포인트는 **모바일 호출부가 없어 서버 테스트로만 검증**된다(spec 수용 기준도 그렇게 한정됨). 현재 커버리지:

| 계층 | 케이스 |
|---|---|
| 서비스 단위 (4) | 물리 삭제 / 취소 후 같은 날 재도전 가능 / 챌린저 아니면 거부 + row 보존 / 이미 수락된 건 취소 불가 / 마감 지나도 취소 가능 |
| 컨트롤러 슬라이스 (3) | `data.challengeId` 반환 / 챌린저 아님 700 + `내가 보낸 도전장이 아니에요` / 이미 처리됨 705 |
| 통합 (2, Docker 대기) | 물리 삭제 확인 / 받은 사람은 취소 불가 |

도달 경로가 생성 직후로 제한될 뿐 죽은 코드가 아니며, 후속 feature가 목록 UI를 붙이면 그대로 살아난다. 백로그 등재는 pm-lead가 처리했다.

### 3. 🟡 V5 부분 유니크 인덱스가 T-B1 범위 밖 추가

위 "DB 마이그레이션" 섹션 참조. 승인 필요 시 되돌릴 수 있으나, 되돌리면 중복 방지 수용 기준이 best-effort로 강등된다.

### 4. 🟢 `EXPIRED` 전이 주체 없음 (spec 기지 리스크, 후속)

lazy expiry로 처리 중 — 목록 응답에서 제외 + 수락 시도 거부. DB `status`는 `PENDING`인 채로 남는다. `:batch` 스케줄러로 실제 전이시키는 작업은 backlog. 방치하면 `uq_challenges_active_pair_date`가 **마감 지난 PENDING 때문에 같은 날 재도전을 막는다** — 단, `challenge_date`가 이미 지난 날짜라 신규 생성은 항상 오늘/내일 날짜여서 실제 충돌은 발생하지 않는다.

### 5. 🟢 취소가 물리 삭제라 감사 추적 없음

`challenge_states`에 `CANCELED`가 없어 새 상태 도입을 피했다. friends 2차 요청 취소와 동일한 선택이라 프로젝트 내 일관성은 있다.

### 6.5 🟡 잘못된 요청 본문이 HTTP 500 을 돌려준다 (#7에서 발견, 기존 이슈)

`GlobalExceptionHandler`가 `HttpMessageNotReadableException`을 처리하지 않아 `handleUncaught` → **HTTP 500 + code 500**으로 나간다. ADR-0002 규약상 비즈니스 에러는 HTTP 200 + code 7xx여야 한다.

| 입력 | 현재 응답 |
|---|---|
| 깨진 JSON (`{"opponentId":}`) | HTTP 500 / code 500 |
| enum 오타 (`"deadlineType":"YESTERDAY"`) | HTTP 500 / code 500 |

challenge-create가 만든 문제가 아니라 foundation 이래의 기존 동작이고, 정상 모바일 클라이언트는 well-formed JSON만 보내므로 실사용 영향은 낮다.

**다만 `datetime-model-migration`에서 중요해진다** — 요청 본문에 시간 문자열이 들어오기 시작하면 **포맷이 틀린 날짜가 정확히 이 경로로 500을 만든다.** 해당 feature의 T-B3(요청 역직렬화)에서 `HttpMessageNotReadableException` 핸들러를 함께 추가할 것을 제안한다.

### 6.6 🟢 `/actuator/health` 가 500 을 돌려준다 (#7에서 발견)

`SecurityConfig`가 `/actuator/health`를 permitAll로 열어 뒀지만 actuator 의존성이 없어 핸들러가 없다 → `handleUncaught` → 500. 헬스체크 용도로 쓰려면 `spring-boot-starter-actuator` 추가가 필요하다. 현재 사용처가 없어 영향 없음.

### 7. 🟢 `Clock` 빈 신규 도입

`ClockConfig`에서 `Clock.systemUTC()`를 등록했다. 기존 코드(`FriendService` 등)는 여전히 `LocalDateTime.now()`를 직접 부르므로 혼재 상태다. 신규 시간 의존 로직은 `Clock` 주입을 쓰는 편이 테스트에 유리하다 — 점진 이관 후보.

## mobile-dev에게 전달할 주의사항

1. **`message`는 그대로 화면에 띄워도 되는 한국어 문장이다.** 서버가 영문/내부 문구를 흘리지 않도록 상수로 고정하고 테스트로 잠갔다.
2. **`challengeDate`는 `"2026-07-28"` 문자열**, `deadline`/`createdAt`은 `"...Z"`. 초 단위까지만 나간다(나노초 없음).
3. **`challengerProfileImageUrl`만 nullable.** 나머지 필드는 절대 누락/null로 나가지 않는다.
4. **accept 성공 후 즉시 두 목록을 재조회해도 된다** — read-after-write 보장. 지연/재시도 불필요.
5. **실패 시에도 받은 도전장 목록을 재조회**하는 게 계약이다(code 분기 없이).
6. **DELETE는 `data.challengeId`를 돌려준다** — friends의 `CancelFriendRequestResponse`와 같은 모양.

## 참고 링크

- spec: `docs/features/challenge-create/spec.md`
- contract: `docs/features/challenge-create/api-contract.md` (status: `confirmed`)
- 관련 ADR: 0001(Flyway) · 0002(BaseResponse + foundation) · 0009(Refresh Rotation)
- 선행 report: `docs/features/home-feed/backend-report.md`(Challenge 엔티티·V4), `docs/features/friends/backend-report.md`(saveAndFlush 선례)
- V5 마이그레이션: `challenge-server/app/src/main/resources/db/migration/V5__challenge_create_opponent_mission_nullable.sql`
