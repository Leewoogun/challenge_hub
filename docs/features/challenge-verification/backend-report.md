# Backend Report — challenge-verification

- **작성일**: 2026-08-14 by backend-dev · 🔴 **2026-08-18 개정 2회** (1차 업로드 multipart 전환 / 2차 조회 JWT 전환)
- **레포**: `challenge-server` (main, **미커밋** — 커밋은 사용자 몫)
- **계약**: [api-contract.md](./api-contract.md) — ✅ **`confirmed`** (2026-08-18 개정분은 [change-log.md](./change-log.md) 등재)
- **결정**: [ADR-0011](../../decisions/0011-photo-storage.md) (🔴 **§3 superseded · §4 수단 변경** — 둘 다 2026-08-18)

---

## 🔴 2026-08-18 (2차) 개정 — 조회가 JWT 보호 엔드포인트가 됐다

사용자 2차 결정으로 **서명 URL 체계를 통째로 폐기**했다. ADR-0011 §4 의 *수단* 변경이며
원칙(*"접근 제어는 서버가 한다"*)은 유지된다.

```
[전] §4 photoUrl(절대 URL + exp/sig) + photoUrlExpiresAt
     §5 GET /api/v1/photos/{cid}/{uid}/{파일명}?exp=&sig=   ← Bearer 금지, permitAll
[후] §4 photoUrl(상대 경로)                                  ← photoUrlExpiresAt 제거
     §5 GET /api/v1/challenges/{id}/photos/{party}          ← Bearer 필수, 당사자만
```

| 항목 | 조치 |
|---|---|
| `PhotoUrlSigner` · `SelfHostedPhotoEndpoint`(+`ServeOutcome`) · `LocalPhotoController` · `PhotoBaseUrlProvider` | 🔴 **전부 삭제** |
| `PhotoStorage` 포트 | `issueReadUrl`/`ReadUrl` 제거 → **`read(key): ByteArray?`** 추가 |
| `LocalDiskPhotoStorage` 생성자 | `signer`·`baseUrlProvider`·`readTtlSeconds` 제거 → **`root` 하나** |
| `SecurityConfig` | `/api/v1/photos/**` permitAll **제거** — `anyRequest().authenticated()` 가 덮는다 |
| 설정 | `signing-secret`·`public-base-url`·`read-url-ttl-seconds` 제거. 🔵 **환경변수 2개 감소** |
| 마이그레이션 | **0건** |

### 🔴 이 경로에서 `BusinessException` 을 던지지 않는다 — 설계의 핵심

응답이 **바이트**인데 `GlobalExceptionHandler` 는 `BusinessException` 을 **HTTP 200 + JSON** 으로 바꾼다.
그러면 앱 이미지 로더가 **JSON 을 이미지로 파싱하려다 깨지고, status 가 200 이라 실패를 감지할 수도 없다.**
→ 서비스가 `PhotoReadResult`(`Found`/`Forbidden`/`NotFound`) sealed result 를 돌려주고
컨트롤러가 HTTP status 로 매핑한다. **삭제된 `ServeOutcome` 의 발상을 살린 것이다.**

### `SelfHostedPhotoEndpoint` 를 없앤 판정 근거

그 포트의 존재 이유는 *"서명 검증 + 바이트 서빙"* 이었다. **서명이 사라지면 남는 일은 바이트 읽기뿐**이고
`PhotoStorage.read` 하나로 충분하다. 원래의 분리 근거(*"이사하면 이쪽은 통째로 사라진다"*)도 더는
성립하지 않는다 — 이사해도 서버는 **중계(`read`)하거나 302 리다이렉트(서명 URL 재도입)** 중 하나를
하므로 `PhotoStorage` 쪽이 계속 산다.

### 🔵 부수 이득 — `PhotoBaseUrlProvider` 문제의 소멸

그 조각은 *"저장소가 서버 자신이라 URL 의 host 를 모른다 — Android 에뮬레이터는 `10.0.2.2`,
iOS 시뮬레이터는 `localhost`"* 때문에 존재했다. **서버가 URL 을 만들지 않게 되면서 문제 자체가 사라졌다.**
`photoUrl` 을 **상대 경로**로 내리므로 배포 시 프록시·도메인 설정에도 영향받지 않는다.

### 🔵 보안이 강해졌다

| | 서명 URL | JWT 엔드포인트 |
|---|---|---|
| URL 유출 시 | 만료 전까지 누구나 열림 | 🔵 토큰 없이는 못 연다 |
| 당사자 검사 | 발급 시점 1회 | 🔵 **요청 시점 매번** |
| 토큰 만료 | 403 → 앱이 §4 재조회 | 🔵 401 → Authenticator 자동 갱신 |

### 캐시 정책

200 은 `private, max-age=86400` (만료가 없고 사진은 재제출 거부로 불변 — 재진입 시 재다운로드 0).
🔴 **403/404 는 `no-store`** — 같은 URL 이 **404 → 200 으로 바뀌는 자리**라, 상대가 인증하기 전에
받은 404 를 캐시하면 **인증 후에도 사진이 안 보인다.** 서명 URL 시절에는 URL 이 매번 달라 없던 문제다.

---

## 🔴 2026-08-18 (1차) 개정 — 업로드가 multipart 직접 수신이 됐다

사용자 결정으로 ADR-0011 §3(URL 발급 방식)이 supersede 됐다. **아래 본문 중 업로드 3단계를
전제한 서술은 역사 기록이다** — 현재 동작은 이 절과 계약 §3 이 정본이다.

```
[개정 전] upload-url 발급 → 서명 URL 에 PUT → photoKey 로 제출 확정   (3 왕복)
[개정 후] POST .../verification  multipart part "photo"              (1 왕복, 응답 shape 동일)
```

| 항목 | 조치 |
|---|---|
| `POST .../verification/upload-url` | **삭제** |
| `PUT /api/v1/photos/...` | **삭제** — `/api/v1/photos` 이하는 `HttpMethod.GET` 한정 permitAll 로 축소 |
| `POST .../verification` | multipart 수신. **응답 shape 무변경** |
| `PhotoStorage` 포트 | `newKey`/`issueUploadTarget`/`exists` + `UploadTarget` 제거 → **`store(challengeId, userId, bytes): String`** 하나로 |
| `SelfHostedPhotoEndpoint` | `acceptUpload` + `UploadOutcome` 제거. `serve`/`ServeOutcome` 만 |
| `PhotoUrlSigner` | `Op`(PUT/GET) 제거 — 허가할 동작이 읽기 하나뿐. 도메인 분리 태그 `v1`→`v2` |
| 크기 상한 | `challenge.photo.max-bytes` 제거 → **`spring.servlet.multipart.max-file-size: 5MB` 단일 지점** |
| `GlobalExceptionHandler` | 핸들러 **4건 추가** (`MaxUploadSizeExceeded` / `MissingServletRequestPart` / `HttpMediaTypeNotSupported` / `MultipartException`) — 없으면 전부 **HTTP 500** 이 나간다 |
| 마이그레이션 | **0건** — `photo_url` 에 key 를 넣는다는 사실이 그대로다 |

### 🔴 재제출 정책을 다시 정했다 (이 개정에서 가장 무거운 결정)

`photoKey` 왕복이 사라져 *"같은 촬영본의 재시도"* 와 *"다른 사진으로 교체"* 를 **판별할 수단이 없다.**
멱등 성공을 남기면 **다시 찍어 올린 사진이 조용히 버려지는데 앱은 성공이라고 답한다** — 원안이
막으려던 실패(기획서 §2.4 증거 보존)와 같다. **→ 이미 `VERIFIED` 면 전면 거부(700).**

응답 유실 회복은 문구 해석이 아니라 **§4 조회로 status 확인**하는 절차로 계약에 명문화했다.

### 저장소 계층 덮어쓰기 방어(409)를 내린 근거

그 방어의 위협 모델은 *"앱이 발급받은 key 를 재사용해 같은 자리에 다른 바이트를 올린다"* 였다.
**key 는 이제 `store()` 호출마다 서버가 만들고 앱은 key 를 보지도 못하며, 업로드 URL 자체가 없다.**
덮어쓸 대상이 존재하지 않는다. 설령 재제출 검사를 통과하는 버그가 생겨도 **새 key 에 쓰이므로
덮어쓰기 방어로는 어차피 막히지 않았다.** 원자적 쓰기는 유지한다(잘린 파일 방지).

---

## 구현 요약

**T-B1 ~ T-B4 전부 완료.**

| 태스크 | 상태 |
|---|---|
| T-B1 `PhotoStorage` 포트 + 로컬 디스크 구현체 | ✅ (개정으로 포트 축소) |
| T-B2 ~~업로드 대상 발급 +~~ **사진 제출** | ✅ **2026-08-18 multipart 로 재구현** |
| T-B3 조회 — 만료 있는 읽기 URL | ✅ (개정 영향 없음) |
| T-B4 `OPPONENT_VERIFIED` 알림 | ✅ **발송 개시됨** — §0.6.1 절차 완료 후 문구 투입, 실기로 발송 확인 (개정 영향 없음) |

<details><summary>개정 전(2026-08-14) 요약 — 역사 기록</summary>

계약은 **`confirmed`** 이며 3쟁점 전부 **구현된 안 그대로**였다.
그 협의 과정에서 **덮어쓰기 결함 1건을 발견해 고쳤다**(아래 4-a). 🔴 **그 수정은 2026-08-18 개정으로
대상이 소멸해 제거됐다** — 결함이 아니었다는 뜻이 아니라, 그 결함을 만들던 구조가 없어졌다는 뜻이다.

</details>

### 설계상 짚어 둘 것

**1. ~~`PhotoStorage` 를 두 포트로 갈랐다.~~** ⚠️ **2026-08-18 2차 개정으로 다시 하나가 됐다** — 서명이 사라지자 `SelfHostedPhotoEndpoint` 에 남는 일이 바이트 읽기뿐이라 `PhotoStorage.read` 로 흡수했다. 아래는 그 분리의 역사 기록이다.
ADR-0011 §2 의 스케치는 인터페이스 하나였는데 **이사하면 사라지는 부분**을 분리했었다.

| 포트 | 위치 | 이사 후 |
|---|---|---|
| `PhotoStorage` | `:domain:repository` | **살아남는다** — "올릴 곳/읽을 곳을 알려줘" 는 S3 든 R2 든 성립 |
| `SelfHostedPhotoEndpoint` | `:domain:repository` | 🔴 **통째로 사라진다** — 바이트를 받아 적고 서빙하는 일은 이사하면 서버가 아예 안 한다 |

`LocalDiskPhotoStorage` 가 둘 다 구현한다(서명 발급기와 검증기가 **같은 설정을 봐야** 해서 한 클래스다).
이사는 두 번째 포트와 `LocalPhotoController` 를 지우고 첫 번째 구현체만 갈아끼우는 일이 된다.

**2. `verifications.photo_url` 에는 URL 이 아니라 key 를 넣는다.**
URL 을 저장하면 **만료와 host 가 DB 에 박제된다** — 만료된 URL 이 영구히 남고, 이사하면 옛 row 가 전부 죽는다.
컬럼 개명은 엔티티·도메인·홈 피드 매핑까지 건드리는 변경이라 범위 밖으로 두고 주석으로 못박았다(V9).

**3. ~~`/api/v1/photos` 이하는 Bearer 없이 열려 있다.~~** 🔴 **2026-08-18 2차 개정으로 폐기 — 비인증 사진 경로가 사라졌다.**
사진 서빙은 이제 `anyRequest().authenticated()` 가 덮는 **일반 인증 엔드포인트**이고, 당사자 검사를
**발급 시점이 아니라 요청 시점에 매번** 한다. 아래는 역사 기록이다:

> 앱이 그 URL 에 `Authorization` 을 붙이는 코드를 갖게 되면 **이사하는 순간 남의 스토리지로 우리 JWT 를 보낸다.**
> 🔒 지키는 것은 Security 가 아니라 **URL 서명**이다 — HMAC-SHA256 이 *"이 key 를, 이 시각까지"* 읽기를 허가한다.

🔴 **그 위험은 URL 이 남의 도메인을 가리킬 수 있다는 전제 위에 있었다.** 업로드·조회가 모두
우리 서버 엔드포인트로 고정되면서 전제가 사라졌다. presigned 를 되살리면 이 규약도 함께 되살려야 한다.

**4. 재제출 정책 — 같은 key 멱등 / 다른 key 거부.** ⚠️ **2026-08-18 개정으로 폐기됨 — 전면 거부로 대체.** 아래는 그 판단의 역사 기록이다.
`uq_verifications_challenge_user` 때문에 정하지 않으면 500 이 나는 자리였다(spec T-B2).
덮어쓰기를 막은 이유는 *"상대가 본 것"* 과 *"지금 보이는 것"* 이 갈라지면 안 되기 때문이고,
같은 key 를 멱등으로 둔 이유는 그러지 않으면 **앱이 §3 재시도의 성공·실패를 구분할 수 없기** 때문이다.
`verif-mobile` 은 단순 거부를, pm-lead 는 처음 그것을 확정했다가 **멱등 쪽이 낫다며 이 안을 승인**했다.

**4-a. 🔴 그 정책이 저장소 계층에서 우회되는 결함을 발견해 고쳤다.** ⚠️ **이 방어는 2026-08-18 개정으로 제거됐다** — 위협 모델(앱이 key 를 알고 재사용)이 소멸했기 때문이다. 아래는 역사 기록이다.

`verif-mobile` 이 *"이미 그 key 로 올리면 어떤 status 냐"* 를 물어 확인하다 드러났다.
초기 구현은 같은 key 에 **덮어쓰기**를 허용했는데, **업로드 URL 은 제출 확정 뒤에도 자기 만료(10분)까지
살아 있다.** 즉 제출해서 상대에게 알림이 나간 뒤에 **같은 URL 로 다른 바이트를 올려 상대가 이미 본
사진을 바꿔치기**할 수 있었다. `verifications` row 는 그대로라 **아무 흔적도 남지 않는다.**

§3 의 거부 정책이 지키려던 것(기획서 §2.4 *"작성 완료된 계약서는 수정 불가 (증거 보존)"*)이
**한 계층 아래에서 통째로 뚫려 있었다.**

- **수정**: `acceptUpload` 가 대상 key 에 파일이 있으면 **바이트를 읽기 전에** `ALREADY_EXISTS` → **HTTP 409**
- **정상 흐름 무영향**: `upload-url` 은 부를 때마다 새 key 를 만든다. 다시 찍어 올리는 경로는 항상 빈 key 다
- **409 의 유일한 도달 경로**: 업로드는 성공했는데 응답을 못 받아 앱이 재시도한 때 → **앱은 그대로 제출 확정으로 진행**
- 전송이 중간에 끊긴 경우는 원자적 쓰기라 잘린 파일이 key 에 나타나지 않아 **409 가 아니라 204** 다

> ⚠️ **이 방어는 로컬 디스크 단계에서만 서버가 강제할 수 있다.** 오브젝트 스토리지는 presigned PUT 이
> 대개 덮어쓰기를 허용하므로 **버킷 정책(버저닝·오브젝트 잠금)으로 옮겨야 한다.** 계약 §2 에 이사 항목으로 적었다.

**5. 조회를 `GET /challenges/{id}` 에 얹지 않았다.** ⚠️ **2026-08-18 2차 개정으로 이 근거는 소멸했지만 결론은 유지된다** — 아래 부수 이득(객체가 절대 null 이 아니다)이 그대로 유효하기 때문이다.
~~읽기 URL 에 만료가 있어 상세 전체가 단명 응답이 되고, *"만료 후 갱신"*(T-M4)이 계약서 재조회를 요구하게 된다.~~ (만료가 사라졌다.)
부수 효과로 `soul-oath` 의 `confirmed` 계약 shape 이 무변경이라 **`change-log.md` 등재가 불필요하다.**

> **경위**: `verif-mobile` 은 얹기를 주장했고 pm-lead 가 한 번 그렇게 확정했다가 **철회**하고 이 안으로
> 최종 확정했다. `verif-mobile` 이 얹기를 원한 근거(*"만료를 이미지 로드 실패로만 감지하면 네트워크
> 오류와 구분이 안 된다"*)는 **`photoUrlExpiresAt` 을 party 마다 실어 해소**됐다.
> 부수 이득: 별도 엔드포인트라 **`challenger`/`opponent` 객체가 절대 null 이 아니다** —
> 얹기였다면 미수락 챌린지에서 `verification: null` 이 생겨 **`contract: null`(#24)과 똑같은
> 실패 모드가 반복**됐을 것이다.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| ~~POST~~ | ~~`/api/v1/challenges/{id}/verification/upload-url`~~ | — | 🔴 **removed (2026-08-18)** |
| ~~PUT~~ | ~~`/api/v1/photos/{challengeId}/{userId}/{파일명}`~~ | — | 🔴 **removed (2026-08-18)** |
| POST | `/api/v1/challenges/{id}/verification` | Bearer JWT | implemented — 🔴 **multipart (`photo`)** |
| GET | `/api/v1/challenges/{id}/verifications` | Bearer JWT | implemented — 🔴 **`photoUrlExpiresAt` 제거** |
| ~~GET~~ | ~~`/api/v1/photos/{challengeId}/{userId}/{파일명}`~~ | — | 🔴 **removed (2026-08-18 2차)** |
| GET | `/api/v1/challenges/{id}/photos/{party}` | Bearer JWT | **신설 (2026-08-18 2차)** — 🔴 바이트 응답 |

전부 **미배포**(로컬 기동만). `GET /api/v1/challenges/{id}` 는 **변경 없음.**

## 변경된 모듈 & 파일

### 신규

| 모듈 | 파일 |
|---|---|
| `:domain:repository` | `domain/photo/PhotoStorage.kt` — 🔴 1차에 `UploadTarget` 제거, **2차에 `issueReadUrl`/`ReadUrl` 제거 + `read(key)` 추가** |
| ~~`:domain:repository`~~ | ~~`domain/photo/SelfHostedPhotoEndpoint.kt`~~ — 🔴 **2026-08-18 2차에 파일째 삭제** (서명이 사라지자 남는 일이 바이트 읽기뿐) |
| `:infra:external` | `photo/PhotoKeys.kt` · `photo/LocalDiskPhotoStorage.kt` — 🔴 **2026-08-18 2차에 `PhotoUrlSigner.kt` 삭제, `PhotoBaseUrlProvider` 삭제** |
| `:service` | `verification/VerificationService.kt` (+ `VerificationsView` / `PartyVerificationView`) |
| `:controller` | `challenge/VerificationController.kt` · `challenge/dto/VerificationDtos.kt` — 🔴 **2026-08-18 2차에 `photo/LocalPhotoController.kt` 삭제** |
| `:app` | `config/PhotoStorageConfig.kt` |

### 수정

- `app/src/main/kotlin/com/lwg/challenge/config/SecurityConfig.kt` — `/api/v1/photos` 이하 permitAll + 근거 주석 (🔴 2026-08-18 에 **`HttpMethod.GET` 한정**으로 축소)
- `app/src/main/resources/application.yml` — `challenge.photo.*` 블록 신설 (🔴 2026-08-18 에 `max-bytes`·`upload-url-ttl-seconds` 제거 + `spring.servlet.multipart` 신설)
- `app/src/test/.../controller/WireShapeContractTest.kt` — 인증 응답 3종 wire shape 추가
- 🔴 `domain/model/.../NotificationMessages.kt` — **`OPPONENT_VERIFIED` 문구 투입 = 발송 스위치 ON**
  (+ 문구 상태 표를 4종으로 갱신). ⚠️ 이 파일은 **push-deeplink 의 미커밋 변경이 이미 있던 파일**이라,
  기존 변경을 보존한 채 `null` 분기에서 이 타입만 빼내는 방식으로 편집했다
- `domain/model/src/test/.../NotificationMessagesTest.kt` — `inScope` 에 `OPPONENT_VERIFIED` 추가.
  🔵 그 목록이 **곧 발송 스위치의 상태**라는 점을 KDoc 으로 명시했다

> ⚠️ push-deeplink 의 미커밋 3파일(`NotificationMessages.kt` / `FcmNotificationSender.kt` / `FcmNotificationSenderTest.kt`)은
> **건드리지 않았다.** `git status` 로 확인함.

### 설정값 (`application.yml`)

| 키 | 기본값 | 비고 |
|---|---|---|
| `challenge.photo.storage-root` | `${user.home}/challenge-photos` | 🔴 **레포 밖.** `./` 아래면 `git status` 에 사진이 뜨고 `gradlew clean` 이 지운다 |
| `challenge.photo.signing-secret` | `${jwt.secret}` | **새 필수 환경변수 없음.** 도메인 분리 태그로 용도 충돌 방지 |
| `challenge.photo.public-base-url` | **빈 문자열** | 비면 *"요청이 들어온 host"*. Android=`10.0.2.2` / iOS=`localhost` 를 한 값으로 못 맞추기 때문 |
| `challenge.photo.read-url-ttl-seconds` | `600` | 읽기 URL 만료 |
| ~~`challenge.photo.upload-url-ttl-seconds`~~ | — | 🔴 **제거 (2026-08-18)** — 업로드 URL 이 없다 |
| ~~`challenge.photo.max-bytes`~~ | — | 🔴 **제거 (2026-08-18)** — 아래 multipart 설정으로 일원화 |
| 🔴 `spring.servlet.multipart.max-file-size` | `5MB` | **크기의 유일한 강제 지점.** 초과분은 컨트롤러 도달 **전**에 끊긴다 |
| `spring.servlet.multipart.max-request-size` | `6MB` | multipart 경계·헤더 오버헤드 몫 |

> 🔴 **상한을 두 곳에 두지 않는 것이 요점이다.** 예전에는 `max-bytes`(응답 필드 + 서버 검사)와
> 앱 목표치가 따로 있었고, 값이 어긋나면 *"발급은 5MB 라 했는데 실제로는 다른 곳에서 잘리는"*
> 상태가 가능했다. 이제 강제는 한 곳뿐이다.
>
> ⚠️ **대신 그 값을 테스트가 고정하지 못한다** — 예전에는 생성자 파라미터라 단위 테스트로 잡혔지만
> 지금은 yml 설정이라 통합 테스트 없이는 검증 불가다. `MaxUploadSizeExceededException` 이 code 700 으로
> 변환되는 것까지만 테스트가 덮는다.

🔴 **FCM 과 달리 fail-safe 로 떨어지지 않는다.** 푸시는 없어도 앱이 동작하지만 사진 저장은 없으면
인증 자체가 불가능하다 — 저장 루트를 못 만들면 기동 시점에 터진다.

## DB 마이그레이션

**DDL 0건 / DML 0건.** 주석 정정 1건만 추가했다.

`V9__verification_photo_key_recomment.sql` — `verifications` 의 `photo_url` / `status` / `verified_at` 컬럼 주석.
`V6`·`V8` 과 같은 성격(스키마 무변경 재주석)이다.

> ⚠️ **pm-lead 지시는 "마이그레이션 불필요" 였고 그 판단은 맞다** — `verifications` 는 V1+V4 로 완성돼 있다.
> V9 를 **추가한 이유는 하나**다: `photo_url` 이 URL 이 아니라 key 를 담게 되면서 **컬럼 이름이 거짓말을 하게 됐다.**
> `\d+ verifications` 로 바로 보이는 자리이고, V8 이 정확히 같은 이유로 낡은 주석을 정정한 선례가 있다.
> 스키마를 바꾸지 않으므로 기존 DB 에 위험이 없다. **불필요하다고 보시면 지워도 코드는 그대로 동작한다.**

## OpenAPI

- SpringDoc (로컬): http://localhost:8080/swagger-ui/index.html · JSON: http://localhost:8080/v3/api-docs
- 반영된 태그: `Verification`(**3종** — 제출 / 조회 / 🔴 **사진 서빙 신설**). `Photo (local storage)` 태그는 **소멸**했다 (컨트롤러 삭제)
- ⚠️ **사진 서빙만 `BaseResponse` 를 쓰지 않는다**(바이트 응답). `@Operation` description 에 status 표(200/400/401/403/404)와 그 사실을 적어 뒀다.
- 🔴 제출은 이제 `multipart/form-data` 로 문서화된다 — SpringDoc 이 `@RequestPart("photo") MultipartFile` 에서
  자동 생성한다. **요청 DTO 클래스가 없다.**

## 테스트 결과

### 🔴 2026-08-18 2차 개정 후 (현재)

**전체 320/320 passed** (365 중 skip 45). **실패 0.**

1차 개정 후 326/326 대비 **-6 tests** (`PhotoKeys.require()` 삭제로 -1 추가). 🔴 **줄어든 것은 전부 사라진 기능의 테스트다** —
서명 발급·검증(`PhotoUrlSignerTest` 11건 삭제), 서명 URL 서빙 컨트롤러(`LocalPhotoControllerTest` 4건 삭제),
만료·baseUrl 분기(`LocalDiskPhotoStorageTest` 6건 삭제). **대신 `readPhoto` 계열이 13건 늘었다**
(서비스 8 + 컨트롤러 5). 🔴 **skip 은 45 로 그대로**이며 실패는 0 이다.

| 모듈 | passed / total (skip) |
|---|---|
| `:app` | 117 / 162 (45) |
| `:service` | 125 / 125 |
| `:infra:external` | 33 / 33 |
| `:domain:model` | 22 / 22 |
| `:core` | 23 / 23 |

| 클래스 | 결과 | 무엇을 고정하나 |
|---|---|---|
| `VerificationServiceTest` | 28/28 | 🔴 **`readPhoto` 8건** — 제3자 `Forbidden`(**예외가 아니라 result**) · **제3자는 미인증 상태여도 `Forbidden`**(판정 순서: 권한이 상태보다 먼저) · 끝난 챌린지도 `Found` · 파일 소실 `NotFound`. 조회는 **상대 경로** 고정 |
| `VerificationControllerTest` | 13/13 | 🔴 **서빙 5건** — 200+`private, max-age=86400` · 403/404 **빈 바디 + `no-store`** · 잘못된 `party`→400 **+ 서비스 미호출**(`verify(never())`) · 대문자 `CHALLENGER` 통과 |
| `LocalDiskPhotoStorageTest` | 7/7 | `store`→`read` 왕복 · **재기동 후에도 읽힌다**(유지) · 없는 key·형태 틀린 key → **null(예외 아님)** |
| `WireShapeContractTest` | 17/17 | `PartyVerificationDto` **4필드** · `"photoUrl":null` 원문 단언 |
| `PhotoKeysTest` | **4/4** | 🔴 **경로 탈출 방어의 단독 고정점**(공격 문자열 6종) · key 유일성. `require` 테스트 1건은 함수와 함께 삭제 |

🔴 **삭제로 덮이지 않게 된 성질과 대체:**

| 사라진 커버리지 | 대체 |
|---|---|
| 서명 검증·만료·baseUrl 분기 | 성질 자체가 소멸. 접근 제어는 `readPhoto` 의 JWT 당사자 검사가 지고, 서비스 테스트의 `Forbidden`·판정 순서 테스트가 고정 |
| *"바디 없는 status 응답, `BaseResponse` 미개입"* (구 `LocalPhotoControllerTest` 의 존재 이유) | `VerificationControllerTest` 서빙 5건이 **승계** — 빈 바디 단언이 `BaseResponse` 미개입을 함께 고정 |
| 경로 탈출 key 거부(구 `serve` Forbidden) | `read` 가 **null 을 돌려준다**는 테스트로 승계 |

| 클래스 | 결과 | 무엇을 고정하나 |
|---|---|---|
| `PhotoKeysTest` | 5/5 passed | 🔴 경로 탈출 6종 거부 · key 유일성(200회) — **개정 영향 없음** |
| `PhotoUrlSignerTest` | 11/11 passed | exp 위조 · 만료 경계 · **위조 검사가 만료 검사보다 먼저** (교차 op 2건 삭제) |
| `LocalDiskPhotoStorageTest` | 12/12 passed | 실제 디스크. 🔴 **재기동 후 사진 유지** · `store` 가 매번 새 key 를 만들고 **이전 파일이 불변** · store→issueReadUrl→serve 왕복 · 경로 탈출 |
| `VerificationServiceTest` | 19/19 passed | 🔴 **재제출 거부 시 저장·알림·기존 row 가 모두 불변** · 권한이 상태보다 먼저 · 알림 수신자 방향(양방향) · **거부된 제출은 저장소에 아무것도 남기지 않는다**(5경로) · JPEG 매직 넘버 |
| `VerificationControllerTest` | 8/8 passed | 🔴 **part 이름이 `photo`** 라는 계약 · ADR-0010 표기 · 응답에 `photoKey` 없음 · 비즈니스 에러가 HTTP 200 + code |
| `LocalPhotoControllerTest` | 3/3 passed | GET 서빙만. 🔴 **바디가 비어 있다**(403/404) · `Cache-Control` |
| `GlobalExceptionHandlerTest` | 14/14 passed | (+5) multipart 4종이 **HTTP 500 이 아니라 200 + code 700** 으로 나간다 · 🔴 `ExceptionHandlerMethodResolver` 로 **디스패치 선택**을 고정(용량 문구가 상위 타입 핸들러에 가려지지 않는다) |
| `WireShapeContractTest` | 17/17 passed | (-1) `UploadTargetData` 삭제. **조회·제출 응답 shape 과 null 픽스처는 무변경** |

🔴 **삭제로 덮이지 않게 된 성질과 그 대체:**

| 사라진 커버리지 | 대체 |
|---|---|
| 저장소 계층 크기 상한 | `MaxUploadSizeExceededException` → code 700 변환만 검증. ⚠️ **`5MB` 설정값 자체는 어떤 테스트도 고정하지 않는다**(yml 설정이라 통합 테스트 필요) |
| 저장소 계층 JPEG 검사 | `VerificationService` 의 매직 넘버 테스트로 이동 |
| 덮어쓰기 거부(409) | 위협 소멸. *"매번 다른 key + 이전 파일 불변"* 이 같은 성질(증거 보존)을 고정 |
| `.tmp` 찌꺼기 미잔류 | 🟡 **미검증** — `store` 에 거부 경로가 없어 기존 시나리오가 재현 불가(예외 주입 테스트는 개정 전에도 없었다) |

<details><summary>개정 전(2026-08-14) 수치 — 역사 기록</summary>

**전체 345/345 passed** (390 중 skip 45). 기준선 260/260 대비 +85.

| 클래스 | 결과 |
|---|---|
| `PhotoKeysTest` 5/5 · `PhotoUrlSignerTest` 13/13 · `LocalDiskPhotoStorageTest` 21/21 | |
| `VerificationServiceTest` 26/26 · `VerificationControllerTest` 10/10 · `LocalPhotoControllerTest` 6/6 · `WireShapeContractTest` 18/18 | |

</details>

⚠️ **자동 테스트가 덮지 못한 것**:
- `AFTER_COMMIT` / `REQUIRES_NEW` 타이밍 — 단위 테스트에 트랜잭션이 없다(`NotificationDispatcherTest` 와 같은 한계).
- **실제 SQL** — 통합 테스트 45건이 컨테이너 런타임 부재로 여전히 skip 중이다. 다만 이 feature 는 **DDL 변경이 0건**이라 그 공백이 새로 넓어지지는 않았다.

### 🟢 실서버 E2E 실측 (2026-08-14 10:39 KST)

**로컬 기동 서버 + 실 PostgreSQL 로 전 경로를 왕복했다.** 단위·슬라이스가 못 덮는 축(실제 파일 IO,
실제 SQL, Security 필터체인, 서명 URL 왕복)을 실측으로 메운 것이다.

대상: `challenges.id = 26` (challenger=14 `테스터1` / opponent=15 `테스터2`, `IN_PROGRESS`).
인증은 `dev-test-login` — repos.json 이 *"이 프로젝트의 표준 검증 방식"* 이라 적은 그 경로다.

| # | 확인 | 결과 |
|---|---|---|
| 1 | `POST .../verification/upload-url` (user 14) | ✅ `photoKey=26/14/b1c994bc…jpg`, `expiresAt` 이 발급 +**10분** 정확 |
| 2 | `PUT uploadUrl` — 🔴 **`Authorization` 없이** JPEG 212B | ✅ **204, 바디 0바이트** (`BaseResponse` 아님) |
| 3 | `POST .../verification` | ✅ `VERIFIED` / `verifiedAt=2026-08-14 10:39:39` (**`T`·`Z`·밀리초 없음**) |
| 4 | **상대(user 15)** 가 `GET .../verifications` | ✅ challenger 만 `photoUrl`+`photoUrlExpiresAt`, opponent 는 **키가 남은 채 3필드 null** |
| 5 | 그 `photoUrl` 을 **`Authorization` 없이** 열기 | ✅ **200 / `image/jpeg` / 212B — 올린 바이트와 `cmp` 완전 일치** |
| 6 | **제3자(user 16)** 조회 | ✅ `code=700` `내 챌린지가 아니에요` — **응답에 URL 없음** |
| 7 | 같은 `photoKey` 재제출 | ✅ **멱등** — `verifiedAt` 이 10:39:39 그대로 (재전이 없음) |
| 8 | 인증 후 `upload-url` 재발급 | ✅ `code=700` `이미 인증을 완료했어요` |
| 9 | **user 15 가 user 14 의 key** 로 제출 | ✅ `code=700` `내 인증 사진이 아니에요` |
| 10 | 읽기 URL 의 `sig` 한 글자 조작 | ✅ **403** |
| 11 | 서명 없이 `PUT`/`GET /api/v1/photos/...` | ✅ **403 / 바디 0바이트** (permitAll 이지만 서명이 막는다) |
| 12 | Bearer 없이 인증 3종 호출 | ✅ **401** + `BaseResponse` |
| 13 | DB | ✅ row **2건 유지**(늘지 않음). `photo_url` 에 **key** 가 들어감 |
| 14 | 디스크 | ✅ `~/challenge-photos/26/14/b1c994bc….jpg` 212B, 권한 `-rw-------` |

**Flyway**: V9 가 실 DB 에 적용됐고(`installed_rank` 9, success=t) `\d+ verifications` 의
`photo_url`/`status`/`verified_at` 주석이 의도대로 박혔다. 스키마는 무변경.

### 🔴 덮어쓰기 결함 — 실서버에서 재현하고 수정본을 실측 검증했다

위 E2E 를 돌린 뒤 `verif-mobile` 질문을 따라가다 발견했다. **수정 전 빌드가 도는 :8080 에서 재현했다:**

```
1st PUT (원본 212B)      → 204
2nd PUT (같은 key, 506B) → 204     ← 🔴 그대로 통과. 상대가 본 사진이 바뀐다
```

**수정본을 :8081 에 따로 띄워 검증했다** (사용자의 :8080 인스턴스는 건드리지 않았다):

```
1st PUT (원본 212B)      → 204
2nd PUT (같은 key, 506B) → 409     디스크 잔존 크기 = 212 bytes  ← 원본 보존
새 key 로 PUT            → 204     ← 정상 재촬영 경로 무영향
```

검증 후 `challenge_id=21` 의 사진과 8081 인스턴스는 정리했다 — **21 은 양측 `PENDING` + 사진 0건**
상태로 되돌려 뒀다(`verif-mobile` 의 쓰기 경로 테스트용).

⚠️ **:8080 에서 도는 인스턴스는 여전히 수정 전 빌드다.** 재기동해야 409 가 적용된다.

### 🟢 `OPPONENT_VERIFIED` 발송 실기 확인 (2026-08-14 11:02 KST)

문구를 넣은 뒤 **실제로 발송 경로를 탔는지**까지 확인했다. 단위 테스트는 *"이벤트를 발행했다"* 까지만
증명하고, `AFTER_COMMIT` + `REQUIRES_NEW` 를 지나 **row 가 실제로 커밋되는지**는 못 덮는다
(그게 push-fcm 이 *"테스트는 초록인데 실제로는 안 됨"* 이라고 못박은 자리다).

`challenge_id = 18`(테스터3 ↔ 테스터2)에서 challenger 가 제출:

```
notifications row: user_id=15  type=OPPONENT_VERIFIED  reference_id=18  is_read=f
                   title="증거 도착"  body="테스터3님이 인증 사진을 올렸습니다"
```

| 확인 | 결과 |
|---|---|
| 🔴 수신자가 **상대(15)** 이고 제출자(16)가 아님 | ✅ `verif-mobile` 이 *"본인에게 가면 자기 알림을 눌러 자기 사진을 보러 간다"* 며 확인 요청한 항목 |
| `reference_id` = challengeId (→ `data.challengeId`) | ✅ 18 |
| 닉네임 치환 | ✅ `테스터3` |
| `AFTER_COMMIT` 리스너가 **실제로 커밋** | ✅ row 가 남았다 |
| FCM 실발송 | ⏭️ **건너뜀** — 서비스 계정 키가 없어 `NoOpNotificationSender`. **이게 설계된 동작이다**(계약 §0.4) — 발송만 생략하고 row 저장은 그대로 |

> ### ⚠️ 검증이 개발 DB 에 남긴 상태 (pm-lead 지시로 **남겨 둔다** — T-I1 에 그대로 쓴다)
>
> | challenge | 상태 | 용도 |
> |---|---|---|
> | **26** (테스터1↔테스터2) | user 14 `VERIFIED` + 사진 1 | `verif-mobile` 이 **§4·§5(조회·서빙)** 를 앱 없이 바로 확인 |
> | **18** (테스터3↔테스터2) | user 16 `VERIFIED` + 사진 1 + **`OPPONENT_VERIFIED` 알림 row** | 푸시 수신·딥링크 확인 |
> | **21** (테스터1↔테스터2) | 🔵 **양측 `PENDING`, 사진 0** | **쓰기 경로(§1~§3) 전용으로 깨끗하게 비워 뒀다** |
>
> 되돌리려면 (T-I1 이후):
> ```sql
> UPDATE verifications SET status='PENDING', photo_url=NULL, verified_at=NULL WHERE challenge_id IN (18,26);
> DELETE FROM notifications WHERE type='OPPONENT_VERIFIED';
> ```
> ```sh
> rm -rf ~/challenge-photos/18 ~/challenge-photos/26
> ```

**여전히 안 덮인 것**: 실기 촬영→리사이즈→업로드(T-I1)는 모바일 구현 후. 위 2번은 `curl` 이 앱을 대신했다.

## 🔴 T-I1 실기 검증 전 필수 조건 — **서버 재기동**

**로컬 :8080 에 도는 인스턴스는 `409` 수정과 `OPPONENT_VERIFIED` 문구 투입 **이전** 빌드다.**
그 상태로 T-I1 을 돌리면 두 가지가 **검증 안 된 채 초록이 된다**:

| 항목 | 재기동 없이 검증하면 |
|---|---|
| 앱의 **409 처리** | 2차 PUT 이 **204** 로 나와 그 분기가 **한 번도 안 타고 통과**한다 (`verif-mobile` 지적) |
| `OPPONENT_VERIFIED` 발송 | 문구가 없는 빌드라 **알림이 아예 안 나간다** |

⚠️ **:8080 은 backend-dev 가 띄운 서버가 아니라 사용자 소유라 임의로 재기동하지 않았다.**
검증용으로는 다른 포트에 새로 띄우면 된다(:8080 과 공존, DB 는 동일):

```sh
cd /Users/hwamulman/woogunProject/challenge/challenge-server
JWT_SECRET=<기존과 동일한 값> \
  ./gradlew :app:bootRun --args='--server.port=8081 --challenge.dev.test-login.enabled=true'
```

🔴 **`--challenge.dev.test-login.enabled=true` 를 빠뜨리면 `test-login` 이 404 다** (실측으로 한 번 걸렸다).

**+ FCM 실발송을 보려면 `FCM_CREDENTIALS_PATH` 가 필요하다.** 없으면 `NoOpNotificationSender` 라
`notifications` row 만 남고 **기기에 푸시는 뜨지 않는다** — 이번 검증이 딱 그 상태였다.

## 미해결 이슈

1. 🟡 **`OPPONENT_VERIFIED` 문구가 초안값이다 — 사용자 확정 대상.**
   title `"증거 도착"` / body `"{닉네임}님이 인증 사진을 올렸습니다"`.
   🔴 **기존 3종에 톤을 맞추지 않았다** — `NotificationMessages` KDoc 이 *"임의로 통일하지 마라,
   확정분을 초안에 맞추는 방향은 특히 안 된다"* 고 명시한다. 이제 초안이 3건(`CHALLENGE_ACCEPTED` /
   `CHALLENGE_REJECTED` / `OPPONENT_VERIFIED`)이고 확정이 1건이다. **네 종을 함께 확정하는 게 맞다.**

   ⚠️ **발송 개시 기준에 단서가 붙었다** (계약 §0.5 각주 — pm-lead 판단).
   승인 시점에 `verif-mobile` 의 앱 변경은 **워킹트리에만 있었고 커밋·배포되지 않았다.**
   *"다음 실기 검증(T-I1) 빌드에 포함"* 으로 갈음한 것이며 **실사용자가 없는 개발 단계 한정**이다.
   🔴 **릴리스 이후에는 이 갈음이 성립하지 않는다** — 그때는 배포 완료가 곧 개시 조건이다.

2. ✅ **해소됨 (2026-08-18)** — ~~모바일 구현 비용이 계약 문면보다 크다~~.
   업로드가 Bearer 필수인 평범한 `BaseResponse` 엔드포인트가 되면서 **별도 `HttpClient` 도,
   Ktorfit 우회도 필요 없어졌다.** 🔴 **다만 §5(사진 서빙)에는 그대로 남는다** — 이미지 로더가
   그 URL 을 직접 열고 `Auth(bearer)` 가 헤더를 선제 주입하므로 별도 경로가 여전히 필요하다.
   *"표준 에러 처리·회귀 테스트 사각지대"* 라는 모바일 백로그 항목도 **범위가 §5 로 줄었다.**

3. **보관 기간 정책 없음** — ADR-0011 이 범위 밖으로 넘겼다. 지금은 **아무것도 지우지 않으며 용량이 단조 증가**한다.
   `PhotoStorage.delete()` 는 구현돼 있으나 **호출부가 없다.** 정책이 정해지면 그 feature 가 부른다.

4. **`photo_url` 컬럼 개명 미실행** — 값이 key 인데 이름이 url 이다. V9 주석이 근거를 남겼고,
   개명은 엔티티·도메인·홈 피드 매핑을 함께 건드려야 해서 별도 건으로 남긴다
   (`soul-oath` 의 `_signature_url` → `_signature_data` 가 선례).

5. 🟡 **`spring.servlet.multipart.max-file-size` 값을 테스트가 고정하지 못한다** (2026-08-18 신규).
   상한이 생성자 파라미터에서 yml 설정으로 옮겨가면서 단위 테스트의 손이 닿지 않는다.
   **초과 시 code 700 으로 변환되는 것까지만** 덮인다. 통합 테스트가 살아나면 함께 볼 항목이다.

6. 🔴 **EXIF 가 서버를 그대로 통과한다 — 앱이 지워야 한다** (2026-08-18 신규, `verif-mobile` 질문 3에서 드러남).
   `store` 는 받은 바이트를 그대로 쓰고 §5 는 저장된 바이트를 그대로 돌려준다. **가공이 0이다.**
   따라서 앱이 EXIF 를 실어 보내면 **`GPSLatitude`/`GPSLongitude` 가 상대에게 그대로 간다.**
   이 앱은 **즉석 촬영을 강제**(기획서 §2.5)하므로 위치가 붙을 확률이 오히려 높다.
   **서버는 제거하지 않는다** — 이미지 디코딩 라이브러리를 들이는 비용이 크고 앱이 이미 재인코딩
   단계(spec T-M2)를 갖고 있다. ⚠️ **앱이 아닌 클라이언트가 EXIF 를 실으면 그대로 저장된다** —
   인지하고 받는 부채이며 **실사용자 유입 전에 다시 볼 항목**이다.

7. ✅ **해소됨 (2026-08-18)** — ~~`PhotoKeys.require()` 가 호출부 0 개~~. **pm-lead 승인 후 삭제했다.**
   🔴 **삭제 사유가 "호출자가 없어서"가 아니다** — `require` 는 **던지는데**, 이번 설계는 서빙 경로에서
   예외를 의도적으로 버렸다(예외가 새면 `GlobalExceptionHandler` 가 JSON/500 으로 바꿔 앱 이미지
   로더가 깨진다). 그래서 `read`/`delete` 는 `isValid` **fail-soft**(null / no-op)를 택했고,
   던지는 헬퍼가 남아 있으면 **다음 진입점 작성자가 "안전망"으로 집어 들어 그 회귀를 되살린다.**
   `isValid` KDoc 에 이 근거를 남겨 재도입을 막았다.
   ⚠️ **경로 탈출 방어는 약해지지 않았다** — 런타임은 여전히 2중이다(`PhotoKeys` 정규식 +
   `LocalDiskPhotoStorage` 의 `normalize()` 후 루트 포함 검사). 사라진 것은 그 사이의 **던지는 계층**뿐이고,
   테스트 고정점은 `PhotoKeysTest.경로 탈출 시도는 전부 거부된다`(공격 문자열 6종)로 유지된다.

8. 🔵 **`photoUrl` 조인 규칙을 계약에 명시했다** (2026-08-18, `verif-mobile` 실측이 발단 — **앱 소관**).
   `photoUrl` 이 `/` 로 시작하는데 **이 레포의 기존 조인 관행은 leading slash 없는 경로**라
   (`"${BASE_URL}api/v1/..."`), **관행을 따르면 100% `//` 가 된다.**
   🔴 **서버는 관용하지 않는다 — 실측 404 이고 핸들러에 도달조차 못 한다**
   (`StrictHttpFirewall` 은 빈 세그먼트를 통과시키고 `PathPatternParser` 가 막는다. MockMvc 로 측정 후 프로브 삭제).
   ⚠️ **위험은 404 가 아니라 그 404 가 조용하다는 것**이다 — §5 는 *"상대가 아직 인증 안 함"* 도
   404 라서 **조인 버그와 정상 상태가 앱에서 구분되지 않는다.**
   **서버는 `//` 를 흡수하지 않는다**(흡수하면 잘못된 URL 이 정상 동작해 버그가 숨고, 같은 사진에
   캐시 키가 둘 생긴다). 앱이 T-M4 착수 첫 항목으로 고치기로 했다.

9. 🟡 **커밋 실패 시 고아 파일** (2026-08-18 신규, 범위 축소된 잔여).
   파일 저장과 row 기록이 같은 트랜잭션이 되면서 예전의 고아 경로는 사라졌지만,
   **저장 후 커밋이 실패하면 파일만 남는다.** 지우지 않는다 — 보관 기간 정책(3번) 소관이다.

10. **부채 인지 (ADR-0011 이 받아들인 것)** — 서버가 죽으면 사진도 죽는다(백업 없음).
   **PaaS 형 호스팅으로 가면 재배포 시 파일이 사라진다.** 호스팅 결정이 이 부채의 만기다.

11. ⚠️ **용량 상한 도달 불가 판단이 모바일 상수 2개에 매달려 있다.**
   (⚠️ 2026-08-18 개정으로 **HTTP 413 이 아니라 `code=700`** 이 됐다. 판단 자체는 그대로 유효하다.)
   `verif-mobile` 이 자동 재압축을 넣지
   않기로 했고 계약도 그렇게 정정했는데, 그 근거는 **장변 1440px** + **JPEG 품질 상한 85(하향 50)** 이다.
   둘 중 하나라도 바뀌면 재계산이 필요하다 — **오늘의 사실이지 규약이 아니다.**

   🔴 **그 과정에서 `verif-mobile` 의 근거 하나를 정정했다.** *"비압축 RGB 조차 5 MiB 에 못 미친다"* 는
   **정사각 크롭에서 깨진다** — 1440×1440 의 비압축 RGB 는 **5.93 MiB 로 상한을 넘는다**(임계 종횡비 1.19:1).
   폰 원본이 4:3·16:9 라 실무에서는 성립하지만 일반 명제가 아니라, **정본 논거를 JPEG 압축률로 바꿔 적었다**
   (실제 산출물 ~500KB 대 = 상한의 1/10). 결론은 그대로다.

12. **판정은 이 feature 밖이다.** `FAILED` 전이·`REMIND`·`RESULT` 는 배치 소관이고 `:batch` 는 여전히 `.kt` 0개다.
   이 feature 가 남기는 것은 `VERIFIED` row 와 `verified_at` 이며, 판정 feature 는 그것을 읽기만 하면 된다.
