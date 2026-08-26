# Backend Report — loser-ranking (개돼지 랭킹)

- **작성**: 2026-08-26 backend-dev
- **태스크**: T-B1 (랭킹 API)
- **상태**: 구현 + 단위/슬라이스 + **실서버 실측 2회** 완료. 계약 🔴 `confirmed`. 커밋 안 함(working tree)

## 구현 요약

신규 엔드포인트 **1건**. 나 + accepted 친구의 `user_stats` 를 **단일 native query** 로 읽고,
정렬·`rank` 부여·`lossRate` 계산은 **도메인 순수 함수**가 한다. **마이그레이션 0건**(읽기 전용).

계약 쟁점 5개 + 추가 1건을 전부 확정해 [api-contract.md](./api-contract.md) 에 근거와 함께 박제했다:
정렬 4키 / `lossRate` 정수%·0÷0=0 / `isMe` 서버 부여 / LEFT JOIN 0 폴백 / `rankings` 최소 1건 불변식
/ **`totalChallenges` 추가**(§9). backend·mobile·design **3자 합의로 `confirmed`**.

### 🔴 `totalChallenges` — 내 §2 결정을 같은 날 뒤집었다

design.md §1.3.3 이 `totalChallenges == 0` → **`아직 기록 없음`** 캡션을 확정하면서, 기존 shape 으로는
**챌린지 0회인 사람과 전승한 사람이 `losses=0, lossRate=0` 으로 글자 하나까지 같은 행**이 되는 게
드러났다. 이건 **§4 결정(row 부재 유저를 목록에 남긴다)의 완성 조건**이기도 하다 — 들어와서 무의미한
행이 되면 *"친구인데 왜 없지"* 를 막으려던 목적이 절반만 달성된다.

**shape 은 `hasRecord: Boolean` 이 아니라 `totalChallenges: Int`** 로 갔다(pm-lead 가 shape 판정을
계약 소유자인 나에게 위임). 불리언은 *"기록이 있다"* 의 **정의를 서버가 규칙으로 하나 더 소유**하게
만들고, 정의가 바뀌면 서버·앱 양쪽을 봐야 한다. `Int` 는 규칙이 아니라 **사실**이고 앱은 `== 0` 만 본다.
이미 `lossRate` 분모로 읽고 있어 **쿼리도 안 바뀌었다**(추가 비용 0).

> ⚠️ **§2 의 기각 근거가 애초에 부실했다는 것도 계약에 남겼다.** 내가 든 이유는 *"넣으면 앱이 패율을
> 재계산할 길을 열어 준다"* 였는데, mobile 지적대로 **재계산 안 하는 건 계약·규율 문제지 데이터를
> 감춰서 강제할 일이 아니고 그 논리면 `losses` 도 못 준다.** 진짜 이유는 YAGNI 하나였다.
> **기각 사유를 실제 이유보다 강하게 적으면, 그 사유가 무너질 때 결정 전체가 흔들린 것처럼 보인다.**

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| GET | `/api/v1/rankings/losers` | Bearer JWT | **implemented (실측 완료)** |

파라미터 0개. 범위가 토큰의 userId 로 완전히 결정된다. 비즈니스 에러 **0건**(7xx 경로가 설계상 없다).

## 변경된 모듈 & 파일

`git status` 실측이다 — 신규 **10**, 수정 **2**.

| 모듈 | 파일 | 줄 | |
|---|---|---|---|
| `:domain:model` | `domain/ranking/LoserRanking.kt` | 130 | 신규 |
| `:domain:repository` | `domain/ranking/LoserRankingRepository.kt` | 18 | 신규 |
| `:infra:jpa` | `infra/jpa/ranking/LoserRankingJpaRepository.kt` | 64 | 신규 |
| `:infra:repositoryimpl` | `infra/repositoryimpl/ranking/LoserRankingRepositoryImpl.kt` | 35 | 신규 |
| `:service` | `service/ranking/RankingService.kt` | 29 | 신규 |
| `:controller` | `controller/ranking/RankingController.kt` | 67 | 신규 |
| `:controller` | `controller/ranking/dto/LoserRankingResponse.kt` | 58 | 신규 |
| `:app` (test) | `domain/ranking/LoserRankingTest.kt` | 328 | 신규 (단위 **20**) |
| `:app` (test) | `controller/ranking/RankingControllerTest.kt` | 174 | 신규 (슬라이스 4) |
| `:app` (test) | `ranking/RankingApiIntegrationTest.kt` | 280 | 신규 (통합 4, skip) |
| `:app` (test) | `controller/WireShapeContractTest.kt` | +65 | **수정 — 추가만** (키 세트 **9필드**) |
| `:app` (test) | `ChallengeServerApplicationTests.kt` | +5 | **수정 — 아래 참조** |

### `ChallengeServerApplicationTests` 수정이 필요했던 이유

스모크 테스트는 JPA auto-configuration 을 **제외**하고 context 만 로드하므로, 신규 JpaRepository 가
생길 때마다 `@MockitoBean` 한 줄을 요구한다(friends·soul-oath·push-fcm·challenge-result 가 각각
주석과 함께 누적돼 있다). `LoserRankingJpaRepository` 줄이 없어 **첫 전체 테스트에서 `contextLoads()`
1건이 실패**했다 — `NoSuchBeanDefinitionException` → `loserRankingRepositoryImpl` → `rankingService` →
`rankingController` 연쇄. 한 줄 추가로 해소.

> ⚠️ **이건 우회가 아니라 이 레포의 확립된 규약이다.** 다음 사람도 새 JpaRepository 를 만들면 같은
> 곳을 밟는다.

## DB 마이그레이션

**0건.** `user_stats`(V1 + V10 연패 2컬럼) 와 `friendships`(V1), `users`(V1) 를 **읽기만** 한다.
`ddl-auto=validate` 라 엔티티 신설 없이 기존 매핑만 재사용했다 — 신규 `@Entity` 도 0개다.

## 설계 결정 2가지 (계약에 없는 구현 내부 판단)

### ① 정렬을 SQL `ORDER BY` 가 아니라 도메인 순수 함수에 뒀다

목록 길이가 "친구 수 + 1" 로 묶여 있어 in-memory 정렬로 충분하고, `UserRecord.applying` 과 같은 이유로
**규칙은 Spring 도 DB 도 모르는 순수 함수**여야 단위 테스트로 전부 고정된다. SQL 문자열 안의 `ORDER BY`
는 그렇게 못 한다. 실제로 정렬 규칙 검증 6건이 DB 없이 돌아간다.

### ② `lossRate` 를 정렬 **전에 한 번** 계산해 들고 다닌다

비교자 안에서 계산하면 `O(n log n)` 번 나눗셈이 재실행되고, 무엇보다 **"정렬에 쓴 값"과 "응답에 나가는
값"이 같다는 보장이 구조적으로 사라진다.** `map { stat to lossRateOf(...) }` 로 한 번 계산해 그 값을
정렬 키와 응답에 **동시에** 쓴다 — 화면에 똑같이 `78%` 로 보이는 두 사람의 순서가 설명되지 않는 상황을
원천 차단한다.

## OpenAPI

- SpringDoc URL(로컬): http://localhost:8080/swagger-ui.html
- 반영된 경로: `GET /api/v1/rankings/losers` — `@Tag(name = "Ranking")` 그룹, `bearerAuth` scheme
- DTO 3종(`LoserRankingResponse`/`Data`/`Item`)에 `@Schema` 설명. 특히 `lossRate`(재계산 금지),
  `isMe`(userId 대조 아님), `rankings`(절대 비지 않음)의 **계약 불변식이 spec 본문에 들어가 있다**

## 테스트 결과

**전체 466건 중 417 passed / 49 skipped / 실패 0.**
기준선(437 중 392 passed / 45 skip) 대비 **신규 29건, 회귀 0**.

| 종류 | 결과 |
|---|---|
| 단위 (`LoserRankingTest`) | **20/20 passed** |
| 슬라이스 (`RankingControllerTest`) | **4/4 passed** |
| wire shape (`WireShapeContractTest` 추가분) | **1/1 passed** (키 세트 9필드) |
| 통합 (`RankingApiIntegrationTest`) | **0/4 — 4 skip** (컨테이너 런타임 부재, 레포 상시 조건) |

### 단위 20건이 고정한 것

`lossRateOf` 6건(0÷0→**0** 이라는 결정 자체 / 12.5→**13** HALF_UP / 78.125→78 / 100% / 분모만 있는 0)
+ 정렬 6건(키 4개 각각 + **입력 순서를 뒤집어도 결과 동일** + *"1전 1패가 개돼지왕이 되지 않는다"* 회귀)
+ rank·isMe 6건(1..n 연속 고유 / 지표가 전부 같아도 공동 순위 없음 / `isMe` 정확히 1건 / 빈 입력)
+ **`totalChallenges` 2건**(원본 그대로 실림 / 🔴 *"0전 0패와 전승 0패는 `totalChallenges` 로만 구분된다"*).

🔴 회귀선 2개가 이 feature 의 핵심이다:
- **"1전 1패가 개돼지왕이 되지 않는다"** — 누가 `lossRate` 를 1차 키로 올리면 이 테스트만 빨개진다.
- **"0전 0패와 전승 0패는 `totalChallenges` 로만 구분된다"** — 이 필드를 추가한 **이유 자체**를 고정한다.
  누가 "안 쓰는 것 같다"며 지우면 여기서 잡힌다.

## 🔴 실서버 실측 (`:8099`) — 계약 정정 2건이 여기서 나왔다

사용자 서버(`:8080`, PID 10722)는 건드리지 않고 별도 포트 기동 + `dev-test-login`.
challenge-result 가 남긴 `user_stats` 4행 실데이터를 그대로 썼다. 상세·wire 원문은
[api-contract.md §8](./api-contract.md).

**정렬 결정이 실데이터로 증명됐다**: 15·16 은 패율 **100%** 인데 rank 2·4 고, 80% 인 14 가 rank 1 이다.
패율을 1차 키로 뒀다면 포디움이 완전히 달라졌다.
**범위 격리**도 확인 — 같은 DB 에서 테스터1 → 4건 / 테스터2 → **2건**(친구의 친구 제외) / 테스터3 → 3건.

### 2차 실측 — `totalChallenges` + 못 덮던 축 해소 + 픽스처 납품

`user_stats` row 가 **없는** 계정(테스터4)을 일부러 심어 재측정했다. 그 결과 **한 응답에 표시 분기가
전부 들어간 원문**이 나왔고 mobile 에 픽스처로 넘겼다:

| 분기 | 행 |
|---|---|
| 친구 여럿 + 나 포함, `isMe` 정확히 1건 | 5건 중 rank 1 |
| 🔴 `totalChallenges == 0` → `아직 기록 없음` (design §1.3.3) | rank 5 |
| `currentLossStreak > 0` → 🐷 뱃지 | rank 2·4 |
| 🔴 `currentLossStreak == 0` 인 **1위** → 연패 절 생략 (design §1.2.5) | rank 1 |
| `profileImageUrl` 있음 / null | rank 3 / 나머지 4건 |

🔴 **rank 1 이 design 이 물어 온 케이스의 실증이다.** rank-design 이 *"연패 0 인 사람이 1위가 될 수
있나"* 를 물었는데 — **된다.** `losses` 가 1차 키라 25패인데 최근 몇 판을 이긴 사람이 왕좌에 오른다.
가정이 아니라 **개발 DB 의 현재 실데이터가 이미 그 상태**여서, design 의 `lossStreak > 0` 조건부가
없었으면 **첫 실행에서 바로 `🐷0연패 · 25패` 를 밟았다.** 계약 §1 에 *"정상적으로 발생한다"* 로
명시해 뒀다 — 나중에 누가 **버그로 오해**하지 않게.

### 🔴 계약이 틀렸던 지점 2건 (실측이 아니었으면 못 잡았다)

| # | 초안이 말한 것 | 실제 |
|---|---|---|
| ① | `profileImageUrl` 은 "사실상 항상 null" | **카카오 CDN URL 이 실제로 온다.** URL 이 `http://` 평문이라 ATS/cleartext 축도 딸려온다 |
| ② | 인증 실패도 "항상 HTTP 200 + code" | **HTTP 401** 이다. `UnauthorizedEntryPoint` 가 필터 단계에서 직접 쓴다 |

②는 **이 feature 가 만든 동작이 아니다** — 기존 `GET /record` 를 토큰 없이 불러 바이트 단위로 같은
응답임을 확인했다. **문서가 틀렸던 것이지 서버가 틀린 게 아니다.**

①이 왜 중요한가: 개발 DB 에 카카오 실계정이 **1개뿐**이라 실서버를 안 찔렀으면 "전부 null" 이라는
인상이 그대로 굳었을 것이다. 🔴 **슬라이스도 통합 테스트도 이 축을 못 덮는다 — 픽스처 값은 내가
정하기 때문이다.** 둘 다 즉시 mobile 에 전달했고 계약 §6·§7 에 등재했다.

### 🔴 ①에서 내가 한 걸음 더 나갔다가 철회했다 — 사실과 스코프를 섞은 건이다

실측 정정을 전하면서 *"이니셜 placeholder 만 만들면 실사용자 아바타가 안 나온다. 이미지 로드와 이니셜
**두 갈래를 다 구현해라**"* 까지 mobile·design 양쪽에 지시했다. **뒷문장은 화면 스코프 결정이고 내
소관이 아니었다.** pm-lead 판정으로 **이번 feature 는 이니셜 placeholder 유지**가 확정됐고, 그 논거가
실제로 더 낫다 — 아바타를 켜면 **`http://` 평문의 ATS/cleartext 축**이 딸려오는데 그건 화면 명세가
아니라 **앱 전역 설정** 사안이고, 아바타는 홈·친구·챌린지 상세에도 똑같이 걸려 있어 **켤 거면 일괄로
켜야 한다**(백로그 "기존 화면 일괄" 건에 내 실측이 보강 등재됨).

즉시 양쪽에 철회를 보내고 계약 §7 을 취소선으로 정정했다.

> **교훈은 §9 의 것과 짝이다.** 거기서는 *기각 사유를 실제보다 강하게 적었고*, 여기서는 *관측한 사실에서
> 내 권한 밖 결론까지 밀고 나갔다*. 🔴 **실측 보고와 스코프 판단은 분리해서 올려야 한다** — 사실은
> 내가 소유하지만 그 사실이 무엇을 하게 만드는지는 아니다. 계약과 화면 스코프도 별개다: 키를 계속
> 내리는 것이 나중에 아바타를 **계약 변경 없이** 켤 수 있게 해 준다.

### DB 영향 — 2회 실측 모두 원복 완료

랭킹 API 자체는 **쓰기 0**. 실측이 남긴 변경은 둘뿐이고 **양쪽 다 원복**했다:

| 변경 | 원복 |
|---|---|
| `dev-test-login` refresh 토큰 회전 (**테스트 계정 14·15·16 만**) | 사전 스냅샷으로 `UPDATE` → **diff 0** |
| 2차 실측용 시드 (`users` 1행 + `friendships` 1행) | `DELETE` 2건 |

원복 후 `users` 4행 · `friendships` 4행 · `user_stats` 4행이 실측 전과 동일함을 재조회로 확인했고
refresh 컬럼도 스냅샷과 **완전 일치**한다. 실사용자(user 1) row 는 처음부터 끝까지 무변경.
사용자 서버(:8080, PID 10722)는 실측 내내 **무중단**.

## 미해결 이슈

- ✅ **계약 `confirmed` 완료** (2026-08-26). mobile 이 쟁점 1·2·3·4·5 전부 동의, `myRank` **미포함**
  확정(*"구할 수 있어서가 아니라 이미 같은 응답 안에 있어서"* — mobile 이 세운 기준이 내 것보다 나았다),
  §5 판정식은 계약에서 삭제하고 **불변식만** 남겼다(빈 상태 정의가 design 쪽에서 아직 안 닫혀 있어,
  판정식을 박아 뒀으면 계약과 화면이 어긋난 것처럼 보였을 것).
- 🔵 **실측이 못 덮은 축 — 2개 중 1개는 2차 실측에서 해소됐다.**
  - ~~`COALESCE` 0 폴백이 한 번도 안 탔다~~ → ✅ **해소.** `user_stats` row 가 없는 계정을 심어
    실 SQL 에서 `LEFT JOIN`+`COALESCE` 가 동작함을 확인(측정 후 원복). **native query 는 슬라이스가
    원리적으로 못 덮는 유일한 축**이라 이게 컸다.
  - **"친구 0명 → 1건" 불변식은 여전히 안 탔다** — 네 계정 모두 친구가 있다. 컨트롤러 슬라이스
    테스트로만 고정돼 있다.
- 🔵 **통합 테스트 4건 상시 skip** — 컨테이너 런타임 부재(레포 전역 조건, 45→49건). 🔴 **native query 는
  슬라이스가 못 덮는다** — `LEFT JOIN`+`COALESCE` 와 `friendships` 양방향 서브쿼리는 실 SQL 이 돌아야
  검증된다. 지금은 실서버 실측이 대신 덮었지만, 런타임이 생기면 자동으로 켜지도록 써 두었다.
- 🔵 **`LoserRankingJpaRepository` 가 `UserEntity` 에 붙은 두 번째 Spring Data 리포지토리다**
  (`UserJpaRepository` 와 같은 도메인 타입). 지금은 둘 다 명시적 주입이라 무해하지만,
  `Repositories.getRepositoryFor(UserEntity)` 를 쓰는 기능(Spring Data REST, `DomainClassConverter` 로
  `@PathVariable` 엔티티 바인딩)이 들어오면 어느 쪽이 잡힐지 미정이 된다. **버그가 아니라 지뢰라 두었다.**
- 🔵 **알려진 경계** — `users` 에 내 row 가 없으면(하드 삭제된 사용자가 유효 토큰 보유) `rankings: []`
  가 나가 "최소 1건" 불변식이 깨진다. **방어 코드를 넣지 않았다** — 탈퇴는 `status` 변경이라 row 가
  남고(하드 삭제 경로 없음), 관측된 적 없는 가정이다. 하드 삭제 도입 시 재검토.
- 🟡 **`profileImageUrl` 이 `http://` 평문이라 iOS 에서만 차단된다** (rank-design 발견, 내가 검증).
  이 feature 의 실측(§실측 ①)이 열어 놓은 후속 건이고 **랭킹만의 문제가 아니다** — 아바타를 켜는 어느
  화면에서든 밟는다. **내가 확인한 사실 3개**:
  1. **https 로 동일하게 서빙된다** — `http`/`https` 둘 다 `200 image/jpeg` **9203 bytes 동일**,
     리다이렉트 없음, `file` 로 실제 JPEG 확인. **스킴만 바꾸면 되고 경로·쿼리는 손댈 게 없다.**
  2. **저장 시점 정규화가 맞다** — 유입은 `AuthService` **1곳**(카카오 응답을 그대로 저장), 노출은
     **6곳**(user-info / 친구 목록 / 친구 검색 / 챌린지 상세 / 받은 도전장 / 랭킹). 한 곳을 고치면
     6개 응답이 동시에 고쳐진다. 기존 row 마이그레이션은 **현재 1행뿐**이라 사실상 공짜.
  3. 🔴 **함정** — URL 안에 `http` 가 두 번 나온다. `?fname=http%3A%2F%2F...` 는 **카카오 썸네일러가
     서버 쪽에서 원본을 가져올 때 쓰는 파라미터**라 기기가 접속하는 주소가 아니고 **ATS 와 무관**하다.
     `.replace("http://", "https://")` **전체 치환은 버그** — 스킴 접두사 하나만 바꿔야 한다.

  ⚠️ **아바타 활성화와 분리 가능한 건이다** — https 정규화 자체는 **서버 단독**(`AuthService` 1곳 +
  마이그레이션)이고 앱이 아바타를 언제 켜든 무관하다. 먼저 해 두면 나중에 켤 때 iOS 함정이 이미
  사라진 상태가 된다. **일정 판단은 pm-lead 소관** — 사실만 넘겼다(위 "월권" 건의 교훈 적용).

  🔴 **정본은 백로그 항목 `profileImageUrl 화면 적용` 이다.** 위 3개는 이 리포트가 **완료 시점에
  무엇을 발견했는지**를 남기는 기록(스냅샷)이고, 갱신되는 구현 재료는 백로그가 갖는다.
  ⚠️ **여기서 읽고 바로 작업하지 마라** — 백로그 쪽이 최신이다. 같은 이유로 `api-contract.md` §7 에서는
  이 3개를 **표로 옮겼다가 도로 뺐다**(두 벌은 갈린다 — rank-design 지적).
- ⚪ 페이지네이션 미적용. 재검토 조건은 "한 사용자의 목록이 200건 초과 관측 시" (계약 명시).
- ⚪ **커밋하지 않았다** — 지시대로 working tree 에만 있다.
