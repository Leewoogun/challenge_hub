# Backend Report — verification-photo-replace

- **작성**: 2026-09-02, backend-dev
- **상위 spec**: [spec.md](./spec.md) §4 백엔드 태스크 (T-B1 / T-B2 / T-B3)
- **상태**: `implemented` — **커밋하지 않았다.** 양 레포 워킹트리 상태 (notification-list 선례)

## 구현 요약

`VerificationService.submit()` 이 **재제출 전면 거부 → `last-write-wins`** 로 바뀌었다.
`IN_PROGRESS` 인 동안 사진을 몇 번이든 교체할 수 있고, 마지막에 올린 사진이 최종본이다.

| spec §4 | 항목 | 결과 |
|---|---|---|
| T-B1 ① | 거부 제거 | ✅ `if (mine.status == VERIFIED) throw ...` 삭제 |
| T-B1 ② | 이전 파일 삭제 — **커밋 후** | ✅ 트랜잭션 경계를 별도 빈으로 분리해 구조로 강제 (아래) |
| T-B1 ③ | `OPPONENT_VERIFIED` 최초 1회 | ✅ *저장 전* `mine.status` 로 판정 |
| T-B1 ④ | `verified_at` 최종 교체 시각 갱신 | ✅ |
| T-B1 🔴 | `submit()` KDoc 정정 + `MSG_ALREADY_VERIFIED` 삭제 | ✅ 정책 표·*"거부가 유일하게 정직한 답"* 서술 전면 교체 |
| T-B2 | 계약 개정 + change-log 등재 | ✅ **기존 계약 개정** (새 파일 만들지 않음) |
| T-B3 | 테스트 최소 3건 | ✅ **신규 21건 / 삭제 2건** (아래) |
| — | 마이그레이션 | ❌ **만들지 않았다** (컬럼 변화 0건) |
| — | AI 판별 | ❌ **넣지 않았다** (`ai-verification` 소관) |

### 🔴 삭제가 커밋 뒤임을 **구조로** 강제했다

`PhotoStorage.delete` KDoc 이 *"트랜잭션이 아니다 — 롤백돼도 지워진 파일은 돌아오지 않으므로
반드시 커밋 후에 불러라"* 를 요구한다. `WithdrawalService` 선례를 그대로 이식했다:

```
VerificationService.submit()                     ← @Transactional 없음 (의도)
  └─ VerificationSubmitTransactionalWorker.submit()   ← @Transactional (여기가 커밋 경계)
        · 검사 → 새 파일 저장 → row 저장 → (최초면) 알림 이벤트 발행
        · 🔴 지우지 않는다. 이전 key 를 SubmitOutcome.replacedPhotoKey 로 반환
  └─ [커밋 후] deleteReplacedPhotoQuietly(key)   ← 실패는 삼키고 WARN
```

⚠️ **바깥 `submit()` 에 `@Transactional` 을 되붙이면 삭제가 커밋 전으로 당겨진다.**
컴파일도 되고 다른 테스트도 전부 통과하므로 **리플렉션 구조 테스트로 고정**했다
(`submit 의 트랜잭션 경계는 worker 에만 있다`).

### 🔴 지울 key 는 `status` 가 아니라 직전 `photo_url` 로 판정한다

탈퇴가 row(`status`/`verified_at`)를 남긴 채 `photo_url` 만 NULL 로 밀기 때문에(mypage T-B2),
`status == VERIFIED` 로 판정하면 **없는 파일을 지우러 간다.** 전용 테스트로 고정했다.

### 🔴 거부 하나를 지우면서 다른 검증이 흘러가지 않았다

당사자 검사 · `IN_PROGRESS` 검사 · JPEG 매직 넘버 · 빈 바이트 · 5 MiB 상한이 **교체 경로에도
그대로 산다.** 거부되면 새 파일도 안 생기고 **이전 사진도 지워지지 않는다** — 5건의 전용
테스트로 각각 고정했다.

---

## 🔴 발견한 문제 — §5 사진 캐시가 조용히 틀리게 된다 (범위 밖이었지만 고쳤다)

**spec 에 없던 항목이다.** 그런데 고치지 않으면 spec §3 수용 기준
*"교체 후 조회하면 최신 사진이 내려온다 (상대 조회도 동일)"* 가 **성립하지 않는다.**

`GET /challenges/{id}/photos/{party}` 는 `Cache-Control: private, max-age=86400` 을 내고 있었고,
계약이 그 값의 근거를 명시하고 있었다:

> *"사진은 **재제출 거부로 불변**이고 경로도 불변이다."* — api-contract §5

**이 feature 가 그 전제를 없앤다.** 경로는 그대로인데 바이트가 바뀌므로, 그대로 뒀다면:

> 상대가 사진을 바꿔도 **최대 하루 동안 옛 사진이 보인다.** 에러도 로그도 남지 않고, 앱은
> 정상적으로 캐시를 쓴 것뿐이라 **어디에서도 실패로 관측되지 않는다.**

**조치**: 200 응답을 `private, no-cache` + **`ETag`** 로 바꾸고 `If-None-Match` → **304** 를 지원한다.
안 바뀌었으면 **304 + 바디 0바이트**라 재진입 비용은 그대로 싸다(옛 `max-age` 가 노리던 이득 보존).
ETag 는 **저장소 key 의 sha256 앞 32자** — key 는 `store()` 호출마다 새로 만들어지므로 *"사진이
바뀌면 반드시 바뀌고 안 바뀌면 절대 안 바뀐다"* 가 보장된다. 🔴 **key 자체는 실리지 않는다**
(계약 §0.4 *"photoKey 는 앱에 노출되지 않는다"* 를 응답 헤더에도 적용).

### 🔴 남은 위험 — **앱 몫이다** (mobile-dev 통지함)

이 헤더는 **HTTP 캐시만** 다룬다. Coil 처럼 **URL 을 키로 하는 메모리/디스크 캐시**는 HTTP 캐시
의미를 무시할 수 있어서, **교체 후에도 같은 화면에서 옛 사진이 그대로 보일 수 있다.**
앱이 교체 시점에 해당 URL 의 캐시 항목을 **명시적으로 무효화**해야 한다.

> 서버가 `photoUrl` 에 버전 쿼리(`?v=...`)를 붙이면 URL 이 바뀌어 로더 캐시까지 자연히 무효화된다.
> 다만 그건 **§4 `photoUrl` 값의 모양을 바꾸는 것**이라(계약이 *"쿼리가 없다"* 를 명문화하고 있다)
> **모바일 합의가 필요한 별건**으로 남긴다. 요청하면 설정 하나 차이다.

---

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| POST | `/api/v1/challenges/{id}/verification` | Bearer JWT | **implemented** — 🔴 행동 변경(거부 → 교체). **요청·응답 shape 무변경** |
| GET | `/api/v1/challenges/{id}/verifications` | Bearer JWT | 무변경 |
| GET | `/api/v1/challenges/{id}/photos/{party}` | Bearer JWT | **implemented** — 🔴 응답 **헤더** 변경(`Cache-Control` 교체 + `ETag` 신설 + `304` 신설). 바디 무변경 |

**신규 엔드포인트 0건. 요청/응답 바디 필드 변경 0건.**

## 변경된 모듈 & 파일

### challenge-server (미커밋)

| 모듈 | 파일 | 변경 |
|---|---|---|
| `:service` | `service/verification/VerificationService.kt` | `submit()` last-write-wins + KDoc 전면 교체, `VerificationSubmitTransactionalWorker`·`SubmitOutcome` 신설, `MSG_ALREADY_VERIFIED` 삭제, `photoETag()` 신설, `PhotoReadResult.Found.etag` 추가, `loadAsParticipant`/`isJpeg` 를 파일 스코프로 이동 |
| `:controller` | `controller/challenge/VerificationController.kt` | `@Operation` 설명 갱신(제출·사진 서빙 둘 다), `If-None-Match` 처리 + `304`, `max-age` → `no-cache` + `ETag` |
| `:service` (test) | `VerificationServiceTest.kt` | 🔴 거부 테스트 **삭제**, 교체 계열 13건 신설, `MutableClock`·`FakePhotoStorage.deleted`/`failDelete` 추가 |
| `:app` (test) | `VerificationControllerTest.kt` | 🔴 `이미 인증했으면 code 700` **삭제**, 캐시 단언 교체, 304 계열 4건 신설 |

`git diff --stat`: 4 files, **+659 / −148**.

🔴 **마이그레이션 0건** — `verifications` 컬럼 변화가 없다. 새 SQL 파일을 만들지 않았다.

### PM 허브 (미커밋)

| 파일 | 변경 |
|---|---|
| `challenge-verification/api-contract.md` | 🔴 **개정** — §3 재제출 정책, 회복 절차 삭제, 에러표, 고아 파일, 순서 조항, §4 전제 주석, §5 캐시, 모바일/백엔드 주의사항, 협의 이력 |
| `challenge-verification/change-log.md` | 🔴 **2026-09-02 항목 등재** (최상단) |
| `challenge-verification/summary.md` | 상단에 **폐기 안내 배너** — 같은 폴더의 옛 리포트를 계약으로 읽지 말라는 경고 |
| `verification-photo-replace/backend-report.md` | 이 문서 |

⚠️ **`verification-photo-replace/api-contract.md` 를 만들지 않았다** — 새 계약이 아니라 기존 계약
개정이고, 사실의 소유자는 한 곳이어야 한다 (spec T-B2 지시).

## OpenAPI

- SpringDoc URL (로컬): http://localhost:8080/swagger-ui.html · JSON: `/v3/api-docs`
- ✅ **실기동으로 확인함** (throwaway DB `challenge_boot_check`, port 18080). 두 경로의 갱신된
  description 이 실제 스펙에 나오는 것을 `curl /v3/api-docs` 로 확인:
  - `POST .../verification` → *"인증 사진 제출/교체 (저장 + VERIFIED 전이 + **최초 1회** 상대에게 알림)"* +
    *"재제출은 **last-write-wins** — 마지막에 올린 사진이 최종본이고 이전 사진 파일은 삭제된다 …
    응답을 유실했으면 그냥 다시 올리면 된다 — 선행 status 조회가 필요 없다"*
  - `GET .../photos/{party}` → `304=If-None-Match 가 현재 ETag 와 같음` 추가 +
    *"사진 교체가 가능하므로 같은 경로가 다른 바이트를 낼 수 있다 — 200 은 `no-cache` 이며 ETag 로 재검증한다"*

## 테스트 결과

| 대상 | 결과 |
|---|---|
| `VerificationServiceTest` | **48/48 passed** (32 → 48: **신규 17건, 삭제 1건**) |
| `VerificationControllerTest` | **17/17 passed** (14 → 17: **신규 4건, 삭제 1건**, 캐시 테스트 1건 개정) |
| **전체 회귀** (`./gradlew test --rerun-tasks`) | **574/574 passed**, 0 failed, **50 skipped** |

🔴 **50 skip 은 이번 변경과 무관한 기존 블로커다** — 컨테이너 런타임(Docker) 부재로 상시 skip
(`repos.json` backend.blockers 기재). 사용자가 Docker 를 켜면 일괄 해소된다.

### 신규 테스트 21건

**`VerificationServiceTest` (17)**

| 테스트 | 고정하는 것 |
|---|---|
| `재제출하면 사진이 교체되고 마지막 사진이 최종본이다` | spec 수용 기준 ①② |
| `재제출하면 이전 사진 파일이 삭제된다` | spec 수용 기준 ④ (삭제 key 순서까지 단언) |
| `첫 제출은 아무것도 삭제하지 않는다` | 없는 key 를 지우러 가지 않는다 |
| 🔴 `트랜잭션 경계 안에서는 이전 파일을 지우지 않고 key 만 돌려준다` | worker 가 지우면 깨진다 |
| 🔴 `submit 의 트랜잭션 경계는 worker 에만 있다` | `@Transactional` 위치를 리플렉션으로 못박음 |
| 🔴 `세 번 제출해도 상대에게 가는 알림은 한 건이다` | spec 수용 기준 ⑥ (**숫자로**) |
| `재제출하면 verified_at 이 최종 교체 시각으로 갱신된다` | spec 수용 기준 ⑦ |
| `재제출해도 row 는 여전히 하나다` | `uq_verifications_challenge_user` |
| `교체 요청도 JPEG 검사를 지나고 거부되면 이전 사진이 살아 있다` | 🔴 검증 누수 방지 |
| `교체 요청도 빈 바이트를 거부하고 이전 사진이 살아 있다` | 🔴 검증 누수 방지 |
| `마감 후에는 교체할 수 없고 이전 사진이 그대로 남는다` | spec 수용 기준 ⑧ (증거 보존) |
| `제3자는 남의 인증 사진을 교체할 수 없다` | spec 수용 기준 ⑨ |
| `이전 파일 삭제가 실패해도 교체는 성공한다` | spec §6 — 예외를 전파해 제출을 실패시키지 않는다 |
| `key 가 없는 VERIFIED row 에 제출해도 삭제를 시도하지 않는다` | 탈퇴 row 와의 상호작용 |
| `사진을 교체하면 ETag 가 바뀐다` | 🔴 캐시 정정의 근거 — 안 바뀌면 앱이 옛 사진을 계속 본다 |
| `사진이 그대로면 ETag 도 그대로다` | 304 로 재진입이 싸다 |
| `ETag 에 저장소 key 가 그대로 실리지 않는다` | 계약 §0.4 (key 비노출)를 헤더에도 적용 |

**`VerificationControllerTest` (4 신규 + 1 개정)**

| 테스트 | 고정하는 것 |
|---|---|
| `교체 제출도 첫 제출과 같은 모양으로 나간다` | wire shape 무변경 |
| `사진을 찾으면 200 과 이미지 바이트를 주고 매번 재검증하게 한다` (개정) | 🔴 `max-age=86400` 이 **다시 들어오면 깨진다** |
| `If-None-Match 가 현재 ETag 면 304 에 바디가 없다` | 재진입 비용 |
| `If-None-Match 가 옛 ETag 면 새 바이트가 나간다` | 🔴 교체 후 최신 사진 보장 |
| `약한 검증자와 목록 형태의 If-None-Match 도 받아들인다` | 중간 캐시 호환 |

### 🔴 삭제한 테스트 2건 (spec 지시)

| 파일 | 테스트 | 사유 |
|---|---|---|
| `VerificationServiceTest` | `이미 인증했으면 재제출이 거부되고 저장도 알림도 없다` | 남기면 **틀린 것을 지키는 테스트**가 된다 |
| `VerificationControllerTest` | `이미 인증했으면 code 700 이 나간다` | 같음 |

### 실기동 확인 (테스트 통과 ≠ 기동 성공)

`ChallengeServerApplication` smoke test 가 JPA 를 제외하므로 단위·슬라이스 테스트만으로는 빈 배선
실패를 못 잡는다. **새 `@Service` 빈(`VerificationSubmitTransactionalWorker`)이 생겼고
`VerificationService` 생성자가 바뀌었으므로** throwaway DB 로 실제 기동을 확인했다:

```
Flyway: Successfully applied 10 migrations to schema "public", now at version v11
Started ChallengeServerApplicationKt in 14.852 seconds
```

확인 후 `challenge_boot_check` DB 는 drop 했다. (기동 로그의 netty macOS DNS ERROR 는 기존 경고이며
이번 변경과 무관하다.)

## 모바일이 알아야 할 것

### 🔴 지워도 되는 것 (T-M2)

| 대상 | 근거 |
|---|---|
| 재시도 전 `GET /challenges/{id}/verifications` **status 선행 조회** | 재제출이 그냥 성공한다. 실패하면 **같은 사진으로 다시 POST** 하면 끝 |
| `이미 인증을 완료했어요` **문구 대응 코드/테스트** | 그 응답이 **더는 나가지 않는다.** 서버 상수도 삭제됐다 |
| *"한 번의 제출이 곧 확정, 되돌릴 수 없다"* 전제의 UI 문구 | 마감 전까지 몇 번이든 바꿀 수 있다 |

⚠️ **두 번 도착해도 알림은 한 번뿐이다** — 첫 제출이 실제로는 성공했었다면 두 번째는 교체로
처리되고 교체는 알리지 않는다. 상대에게 중복 푸시가 가지 않는다.

### 🔴 새로 해야 하는 것

| 대상 | 근거 |
|---|---|
| `VERIFIED` 에서도 **재촬영 진입점 노출** (T-M1) | 서버가 교체를 받는데 CTA 를 숨기면 도달할 수 없다 |
| 🔴 **교체 후 사진 캐시 무효화** | §5 가 `no-cache` + ETag 를 주지만 **URL 을 키로 하는 로더 메모리 캐시에는 닿지 않는다.** 안 하면 교체 후에도 옛 사진이 보인다 |

### 유지되는 것

- **요청·응답 shape 무변경.** 교체 전용 엔드포인트·플래그가 없다 — 첫 제출과 **완전히 같은 요청**이다
- multipart part 이름 **`photo`**, JPEG 매직 넘버, 5 MiB 상한 — 교체 경로에도 그대로 적용
- 🔴 **업로드 전 EXIF 제거** — 교체하는 두 번째 사진에도 필요하다. 서버는 바이트를 가공하지 않는다
- 🔵 **제출 전 확인(촬영 → 미리보기 → 확정)은 유지하라.** 필수 → 권장으로 내려왔지만 왕복 없이
  그 자리에서 확인하는 편이 여전히 싸다. **이번 개정은 그것을 제거할 근거가 아니다**

## 미해결 이슈

| # | 항목 | 상태 |
|---|---|---|
| 1 | 🔴 **로더 메모리 캐시 무효화** | **앱 몫.** 서버가 `?v=` 버전 쿼리를 붙이는 대안이 있으나 §4 값 모양이 바뀌므로 **모바일 합의 필요**. 요청하면 설정 하나 차이 |
| 2 | **T-I1 실기 왕복** | 미실시. 촬영 → 제출 → 알림 1건 → 교체 → **알림 추가 없음** → 상대 화면에 교체된 사진 → 서버 폴더에 이전 파일 없음 |
| 3 | `ai-verification/plan.md` §0.1·Task 5·8·9 | 🔴 **이 feature 가 그 셋을 떼어냈으므로 그 plan 의 재제출 서술이 낡았다.** 갱신 주체는 pm-lead |
| 4 | `challenge-verification` 의 `mobile-report.md`·`backend-report.md`·`design.md` | 2026-08-25 시점 기록이라 재제출·캐시 서술이 낡았다. **`summary.md` 상단에 폐기 배너를 넣어 계약으로 읽히는 것을 막았다.** 본문은 역사 기록이라 고치지 않았다 |
| 5 | 고아 파일 정리 | 커밋 후 삭제 실패 시 옛 파일이 남는다(무해). ADR-0011 이 넘긴 **보관 기간 정책** 소관 — 여전히 범위 밖 |
| 6 | 교체 이력 | 남기지 않는다 (spec §1 제외, YAGNI). AI 판별이 붙은 뒤 필요해지면 컬럼 추가 |
| 7 | 통합 테스트 50건 skip | 기존 블로커. Docker 부재 |
| 8 | 🔴 **커밋 안 함** | spec/지시대로 구현·테스트까지만. 커밋은 사용자 판단 |
