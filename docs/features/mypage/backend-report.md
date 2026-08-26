# Backend Report — mypage

- **작성**: 2026-08-26 backend-dev (mypage-backend)
- **레포**: `challenge-server` (main, **커밋 0건** — 워킹트리 상태로 인계)
- **관련**: [spec.md](./spec.md) · [api-contract.md](./api-contract.md) (`confirmed`) · [design.md](./design.md)

## 구현 요약

| 태스크 | 상태 |
|---|---|
| T-B1 보관함 목록 API | ✅ 완료 |
| T-B2 회원탈퇴 API | ✅ 완료 |
| T-B3 로그아웃 계약 확인 + `WWW-Authenticate` 실측 | ✅ 완료 (서버 무변경) |
| 부록 — `photoDeleted` 필드 (design §7-⑤) | ✅ 완료 |
| T-B4 탈퇴 정책 2건 추가 (pm-lead 확정) | ✅ 완료 |

`PhotoStorage.delete()` 의 **첫 호출부가 생겼다** — 백로그 항목 해소 대상.

### T-B4 — pm-lead 확정 정책 2건

1. **탈퇴자가 보낸(challenger) `PENDING` 챌린지 = 물리 삭제.** 남겨 두면 상대가 수락해
   **결과가 이미 정해진** 챌린지를 시작한다(탈퇴자는 인증 불가). `PENDING` 에는 계약서·서명·
   사진·결과가 없어 **보존할 증거가 0** 이고, 처리가 챌린저의 취소와 정확히 같다.
   **받은(opponent) `PENDING` 은 그대로 둔다** — 수락될 수 없어 자연 만료된다.
2. **탈퇴자의 `notifications`(수신함) = 물리 삭제.** 본인 전용 개인 데이터라 *"양자 기록 보존"*
   대상이 아니라 **개인정보 삭제 축**에 속한다. **상대의 알림은 건드리지 않는다.**

🔴 두 JPQL 모두 `status` 를 **리터럴로 박았다.** DELETE 라 파라미터로 열면 `IN_PROGRESS`/
`COMPLETED` 가 흘러들어 **보존해야 할, 상대의 기록이기도 한 챌린지를 지우는 쿼리**가 된다.

⚠️ **모바일에 남는 표면**: 상대에게 이미 발송된 `CHALLENGE_REQUEST` 알림 row 는 보존되는데
그 챌린지는 삭제된다 → 상대가 탭하면 없는 챌린지로 딥링크한다.
**실측: `GET /challenges/{id}` 가 code=705 `"챌린지를 찾을 수 없어요"` 로 답한다** — 이미
설계된 정상 경로라 서버가 할 일은 없다. push-deeplink 쪽 표시만 확인 대상.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|---|---|---|---|
| GET | `/api/v1/challenges/history` | Bearer | implemented (미배포) |
| DELETE | `/api/v1/users/me` | Bearer | implemented (미배포) |
| DELETE | `/api/v1/auth/logout` | Bearer | 기존 — **서버 변경 0** |
| GET | `/api/v1/challenges/{id}/verifications` | Bearer | **필드 1개 추가** (additive) |
| GET | `/api/v1/users/me` | Bearer | shape 무변경, **동작 변경 1건** (아래) |

공개 엔드포인트 추가 **0건**.

## 핵심 설계 결정

### 1. 카카오 unlink = **admin key** 방식, **DB 보다 먼저**

`POST https://kapi.kakao.com/v1/user/unlink` + `Authorization: KakaoAK {키}` +
`target_id_type=user_id&target_id={kakaoId}` (공식 문서 확인).

**사용자 access token 방식을 쓰지 않은 이유**: 서버는 카카오 access token 을 저장하지 않는다
(로그인 때 `/v2/user/me` 한 번 쓰고 버린다). 토큰 방식이면 앱이 탈퇴 시점에 카카오 토큰을 새로
받아 보내야 하고, **기기의 카카오 세션이 만료돼 있으면 탈퇴 자체가 불가능**해진다.

**순서가 unlink → DB 인 이유**: 두 순서의 실패 결과가 비대칭이다.
- DB 먼저 → unlink 실패: 계정은 이미 **되돌릴 수 없게** 익명화됐는데 카카오 연결은 살아 있고,
  `kakao_id` 를 지워서 **재시도할 대상조차 잃는다.** 복구 불가.
- unlink 먼저 → DB 실패: 카카오 연결만 끊기고 row 는 ACTIVE 로 남는다. 재로그인하면 같은
  row 로 돌아와 다시 탈퇴하면 된다. **복구 가능, 손실 0.**

카카오 `-101`(이미 연결 없음)은 **성공으로 삼킨다** — 부분 실패 후 재시도가 막히지 않는다.

### 2. `kakao_id` 를 NULL 로 만든다 (V11)

남겨 두면 **탈퇴자가 재로그인할 때 계정이 부활한다** — `findByKakaoId` 가 익명화된 DELETED row
를 찾아 그 위에 덮어쓴다. **실측으로 확인**했다 (§검증 16번: 재로그인이 새 계정 id=3 을 만들고
탈퇴 row 는 그대로 남는다). 더불어 `kakao_id` 자체가 개인 식별자다.

UNIQUE 는 유지 — Postgres 는 UNIQUE 컬럼에 NULL 을 여러 개 허용한다.

### 3. 사진 삭제는 **커밋 후**

파일 삭제는 트랜잭션이 아니다. tx 안에서 지우면 롤백돼도 파일이 안 돌아온다. 커밋 후로 미루면
최악이 **고아 파일**뿐이고 그건 읽히지 않으므로 무해하다. 삭제 실패는 삼키고 WARN 만 남긴다 —
이미 커밋된 탈퇴를 되돌릴 수 없기 때문이다.

### 4. 보관함은 **전체 목록 + 페이지네이션 없음**

실측: 이 프로젝트 목록 엔드포인트 5종 전부 페이지 파라미터가 **0건**이다. PM 규약이
*"페이지네이션은 프로젝트 전체에서 한 방식으로 통일"* 이라 보관함 하나만 도입하면
**그 규약이 금지하는 상태를 이 feature 가 만드는 셈**이다. → 백로그.

정렬·월 키는 `challengeDate` — 판정이 자정 직후 배치라 `completed_at` 으로 묶으면 **말일
챌린지가 다음 달 그룹으로 넘어간다.**

## 변경된 모듈 & 파일

**신규 11**
- `app/src/main/resources/db/migration/V11__user_withdrawal.sql`
- `domain/repository/.../auth/KakaoUnlinkPort.kt`
- `infra/external/.../kakao/KakaoUnlinkAdapter.kt` · `KakaoUnlinkConfig.kt`
- `service/.../user/WithdrawalService.kt` (+ `WithdrawalTransactionalWorker`)
- `service/.../challenge/ChallengeHistoryService.kt`
- `controller/.../challenge/ChallengeHistoryController.kt` · `dto/ChallengeHistoryResponse.kt`
- 테스트 3: `WithdrawalServiceTest` · `ChallengeHistoryServiceTest` · `ChallengeHistoryControllerTest`

**수정 (주요)** — `User.kt`(kakaoId nullable) · `UserEntity` · `UserRepository`/`Jpa`/`Impl` ·
`FriendshipRepository`/`Jpa`/`Impl` · `VerificationRepository`/`Jpa`/`Impl` ·
`ChallengeRepository`/`Jpa`/`Impl` · `KakaoOAuthClient` · `UserController` · `UserService` ·
`VerificationService` · `VerificationDtos` · `application.yml` · `WireShapeContractTest` 외 테스트 fake 다수.

## DB 마이그레이션

`V11__user_withdrawal.sql` — **DDL 한 줄**: `ALTER TABLE users ALTER COLUMN kakao_id DROP NOT NULL;`
+ `COMMENT ON COLUMN` 3건(`kakao_id` / `nickname` / `status`).

⚠️ **로컬 `challenge` DB 에는 아직 적용하지 않았다** (현재 `kakao_id` = `NOT NULL`).
검증은 별도 throwaway DB 에서 했고 끝난 뒤 drop 했다.

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui.html
- 반영: `GET /challenges/history`(Challenge 태그), `DELETE /users/me`(User 태그),
  `GET /challenges/{id}/verifications` 의 `photoDeleted` 필드.

## 테스트 결과

| 시점 | tests | passed | skipped | failures |
|---|---|---|---|---|
| 기준선 | 466 | 417 | 49 | 0 |
| T-B2 후 | 479 | 430 | 49 | 0 |
| T-B1 + photoDeleted 후 | 508 | 459 | 49 | 0 |
| **최종 (T-B4 후)** | **513** | **464** | **49** | **0** |

**회귀 0. 신규 47건** (WithdrawalServiceTest 15 · ChallengeHistoryServiceTest 14 ·
ChallengeHistoryControllerTest 6 · UserControllerTest +3 · VerificationServiceTest +4 ·
WireShapeContractTest +4 · VerificationControllerTest +1).

skip 49 는 **기존 블로커** — 컨테이너 런타임(Docker) 부재로 통합 테스트 전체가 `@EnabledIf` 로
비활성. 이번 작업이 늘린 것이 아니다.

## 🔴 실제 구동 검증 (unit test 가 못 덮는 축)

**smoke test 가 JPA 를 auto-configuration 에서 제외**하고 repository 를 전부 mock 으로 세운다.
즉 **통과한 508건 중 어느 것도 새 JPQL 이나 V11 을 실제 DB 에 대고 실행하지 않는다.**
그래서 별도로 확인했다 — throwaway DB(`challenge_verify`) + 포트 8087, **`:8080` 과 공용
`challenge` DB 는 건드리지 않았고** 끝난 뒤 DB·사진·프로세스 전부 정리했다.

| # | 검증 | 결과 |
|---|---|---|
| 1 | Flyway V1→V11 전체 적용 | ✅ `now at version v11` |
| 2 | Hibernate `ddl-auto=validate` + Spring Data JPQL 파싱 | ✅ 컨텍스트 기동 성공 |
| 3 | `KAKAO_ADMIN_KEY` 미설정 시 기동 WARN | ✅ 로그 확인 |
| 4 | 보관함 빈 목록 | ✅ `{"histories":[]}` |
| 5 | 정렬 `challengeDate DESC, id DESC` | ✅ ch2(8/14)→ch1(8/14)→ch3(7/3) |
| 6 | `myResult` 뒤집기 + `BOTH_LOSE` 안 접힘 | ✅ LOSE / DRAW / **BOTH_LOSE** |
| 7 | 응답에 `result`·인증상태 필드 없음 | ✅ |
| 8 | 시간 포맷 `yyyy-MM-dd` / `yyyy-MM-dd HH:mm:ss`, `T`·`Z` 없음 | ✅ |
| 9 | 탈퇴 → HTTP 200, `data` 키 없음 | ✅ |
| 10 | users 익명화 (kakao_id NULL / "탈퇴한 사용자" / 나머지 NULL / DELETED) | ✅ |
| 11 | friendships 물리 삭제 | ✅ 0행 |
| 12 | challenges 3건 · verifications 4건 **보존** (`status`/`verified_at` 그대로) | ✅ |
| 13 | 🔴 **인증 사진 파일 삭제** — 탈퇴자 것만 (`PhotoStorage.delete` 첫 실동작) | ✅ user1 것 1개 잔존, user2 것 2개 삭제 |
| 14 | 탈퇴자 사진 요청 404 / 정상 사용자 200 | ✅ |
| 15 | `photoDeleted` — 탈퇴자 VERIFIED 만 true, FAILED 는 false | ✅ |
| 16 | 상세·홈·랭킹·친구 무파손 (`vs 탈퇴한 사용자`, 랭킹·친구에서 제외) | ✅ |
| 17 | `GET /users/me` 탈퇴자 → 401 | ✅ |
| 18 | 탈퇴 재호출 멱등 → 200 | ✅ |
| 19 | 🔴 **재로그인이 부활이 아니라 신규 계정** | ✅ `userId=3, isNewUser=true` (탈퇴 row id=2 잔존) |

정리 완료 확인: `challenge_verify` drop / 사진 디렉터리 삭제 / 8087 프로세스 종료 /
공용 `challenge` DB 의 `users.kakao_id` 여전히 `NOT NULL` / `:8080` 정상 응답.

### 🔴 T-B4 2차 실구동 검증 — DELETE 는 단위 테스트로 못 덮는다

T-B4 는 **DELETE 두 개**를 추가한다. 단위 테스트의 fake 는 *"호출됐다"* 만 기록하므로
**어떤 row 가 실제로 지워지는지는 검증하지 못한다.** JPQL 이 파싱은 되면서 의미가 틀린
경우(예: `status` 조건 누락)를 전부 통과시킨다. 그래서 throwaway DB 로 다시 확인했다.

user1(탈퇴자) 기준 seed 후 탈퇴 실행:

| id | 관계 | 상태 | 기대 | 결과 |
|---|---|---|---|---|
| 10 | 내가 **보낸** | `PENDING` | 삭제 | ✅ 삭제됨 |
| 11 | 내가 **받은** | `PENDING` | 보존 | ✅ 남음 |
| 12 | 내 | `IN_PROGRESS` | 보존 | ✅ 남음 |
| 13 | 내 | `COMPLETED` | 보존 | ✅ 남음 |
| 14 | 제3자끼리 | `PENDING` | 보존 | ✅ 남음 |

`notifications`: user1 의 2건 삭제, **user2·user3 의 것은 보존** ✅

추가 확인:
- 🔴 **삭제된 챌린지로 딥링크** → `GET /challenges/10` 이 **HTTP 200 + code 705
  `"챌린지를 찾을 수 없어요"`** (앱이 무난히 그릴 수 있는 기존 경로) ✅
- 상대의 보관함(`ch13 vs 탈퇴한 사용자`)·홈(`ch12 IN_PROGRESS vs 탈퇴한 사용자`) 무파손 ✅

⚠️ **부수 발견**: `challenges` 에 `uq_challenges_active_pair_date`
(`LEAST(challenger,opponent), GREATEST(...), challenge_date`) 부분 유니크 인덱스가 있다.
seed 중 같은 쌍·같은 날짜로 두 건을 넣으려다 걸렸다 — V1 이후 마이그레이션에서 들어온
제약이며 **이번 변경과 무관**하다. 기록만 남긴다.

## 계약에 반영된 사항

- `api-contract.md` → **`confirmed`** (design §7 회신 + mobile 통지 반영)
- `docs/features/challenge-verification/change-log.md` → `photoDeleted` 추가 등재 (additive)

### ⚠️ `GET /users/me` 동작 변경 (shape 무변경)

**탈퇴한 계정이 부르면 401.** `kakao_id` 가 nullable 이 되면서 `UserInfoData.kakaoId: Long`
(non-null 계약)을 지키려면 필요했다. 이건 새 규칙이 아니라 **원래 KDoc 에 적혀 있던 동작의
유지**다 — *"DB 에 없으면(회원탈퇴/삭제) 401"* 은 **탈퇴가 row 를 지운다는 전제**였고 이번에
그 전제가 바뀌었다. 부수 효과로 access token 잔존 구멍이 이 엔드포인트에서는 닫힌다.

## 미해결 이슈

### ✅ 해소 — pm-lead 확정 2건은 T-B4 로 구현 완료

`PENDING` 삭제 · `notifications` 삭제 둘 다 익명화 트랜잭션에 들어갔고 실구동으로 검증했다.
계약 §2 의 오픈 이슈 두 절도 확정으로 전환했다.

### ⚠️ 운영 필수

- **`KAKAO_ADMIN_KEY`** — 사용자가 카카오 콘솔에서 발급해야 하는 값이라 서버가 만들 수 없다.
  미설정이면 unlink 를 건너뛰고 DB 익명화만 한다(기동+호출 WARN 2회). **배포 체크리스트.**
- 🔴 **카카오 `-101` 파싱은 실제 왕복으로 검증된 적이 없다.** admin key 가 없어 로컬·CI 가
  항상 No-Op 경로다. WireMock 통합 테스트를 붙일 수 있으나 이번 범위 밖으로 뒀다.

### 백로그 등재 요청

1. **탈퇴 후 access token 최대 1시간 잔존** — 닫으려면 **모든 인증 요청에 DB 조회 1회**가
   붙는다(전역 회귀 위험). 앱의 "탈퇴 즉시 로컬 토큰 삭제" 로 실사용 경로는 막았고 계약에
   수용 기준으로 명시. `GET /users/me` 만 예외적으로 닫혔다.
2. **페이지네이션 부재** — 보관함이 프로젝트 최초의 "무한히 자라는 목록" 이다. 전 엔드포인트
   일괄 도입 시점 결정 필요.
3. **`PhotoStorage.delete()` 호출부 0건** → **해소.** 백로그 항목 갱신 대상.
4. **통합 테스트 49건 상시 skip** (Docker 부재) — 기존 블로커. 이번에 그 공백을 수동 구동
   검증으로 메웠으나 **자동화돼 있지 않다.**
