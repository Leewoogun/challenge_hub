# API Contract — 개발용 테스트 로그인 (dev-test-login)

- **feature-id**: dev-test-login
- **상태**: confirmed
- **최종 수정**: 2026-07-31 by backend-dev (오픈 이슈 **5건 전부 해소** — 미결 항목 없음)
- **상위 spec**: [spec.md](./spec.md)

## 엔드포인트 요약

| # | Method | Path | 설명 | 인증 |
|---|--------|------|------|------|
| 1 | POST | `/api/v1/auth/test-login` | 가짜 계정으로 즉시 로그인 (**조건부 존재**) | 없음 |

공통:
- **이 엔드포인트는 설정을 켠 환경에서만 존재한다.** 끈 환경에서는 라우팅에 등록되지 않아 **404**이며 `/v3/api-docs`에도 나타나지 않는다.
- ADR-0002 BaseResponse 패턴 — 성공·비즈니스 에러는 항상 HTTP 200 + body `code`.
- ADR-0010 시간 규약 — **이 엔드포인트의 요청·응답에는 시간 필드가 없다.**
- 응답 `data` shape는 **`POST /api/v1/auth/kakao`와 완전히 동일하다.** 모바일이 기존 `LoginResponseMapper` / `LoginResult`를 그대로 재사용한다.

---

## 0. 격리 규약 (이 계약의 전제)

> 🔴 **이 엔드포인트는 카카오 검증 없이 JWT를 발급하는 인증 우회 경로다.** 격리는 기능과 동등한 수용 기준이다(spec).

### 0.1 조건부 존재 — 커스텀 `Condition` (2026-07-31 backend-dev 확정, 구현 중 수단 변경)

```
challenge.dev.test-login.enabled=true   → 컨트롤러 빈 생성 → 엔드포인트 존재
(속성 미설정 / false)                    → 빈 미생성 → 라우팅 부재 → 404
```

**프로파일(`@Profile`)을 도입하지 않고 속성 조건을 택한 근거** — 레포 실측: `@Profile`·`spring.profiles`·`SPRING_PROFILES` **0건**, `@ConditionalOn*` **0건**, 프로파일별 yml **0건**(`application.yml` 단일).

1. **fail-closed가 프레임워크 기본값이다.** `matchIfMissing`의 기본이 `false`라 **속성을 안 쓰면 빈이 안 생긴다.** 관례가 아니라 기본 동작으로 보장된다.
2. **단일 목적 스위치.** 프로파일은 시간이 지나며 의미가 누적된다 — 누군가 로깅·목데이터·CORS 때문에 `dev`를 켜는 순간 **인증 우회까지 딸려 켜진다.** spec이 금지한 "끄는 걸 잊으면 열리는" 구조의 변형이다.
3. **사용처 0건인 레포에 프로파일 체계를 엔드포인트 하나 때문에 도입하는 비용.**
4. **속성 이름 자체가 문서다** — `challenge.dev.test-login.enabled=true`는 설정 파일에서 무슨 일이 벌어지는지 그대로 읽힌다.

빈이 없으면 SpringDoc이 스캔할 대상도 없으므로 `/v3/api-docs` 미노출이 자동으로 따라온다.

#### 🔴 `@ConditionalOnProperty`를 쓰지 않았다 — 구현 중 두 가지가 드러났다

결정(**속성 기반, 프로파일 미도입**)은 그대로이고 **수단만 바뀌었다.** `:core`에 `spring-context`만으로 되는 `Condition` 구현을 두고 `:service`와 `:controller`가 **같은 정의를 공유**한다.

**(1) `:service` 모듈에 `spring-boot-autoconfigure`가 없다.** `@ConditionalOnProperty`가 거기 있어 컴파일이 깨진다. 어노테이션 하나 때문에 모듈 의존성을 늘리는 대신 `Condition`을 쓴다. **한 정의를 공유해야 하는 이유**: 두 곳의 조건이 갈리면 "컨트롤러는 있는데 서비스가 없는" 상태가 생긴다.

**(2) 🔴 `getProperty(name, Boolean::class, false)`는 오타에 서버를 죽인다.** 실측(2026-07-31):
```
"true"/"TRUE"/"1"/"yes"/"on"  → true
"0"/"no"/"off"                → false
"enabled" / ""                → ConversionFailedException  ← 던진다
(미설정)                       → false
```
`challenge.dev.test-login.enabled=enable` 같은 **오타 하나로 애플리케이션이 기동 중 죽는다.** dev 전용 플래그의 오타가 서버 전체를 내리는 건 과한 실패 모드다 — **fail-closed는 "안 열린다"여야지 "터진다"가 아니다.**

→ **문자열 `"true"` 정확 비교**(대소문자·앞뒤 공백 무시). 인식 못 하는 값은 전부 **꺼짐으로 수렴**하고, Spring 변환기 구현이 바뀌어도 흔들리지 않는다. `"1"`/`"yes"`/`"on"`을 잃지만 **보안 경계라 켜는 방법이 하나뿐인 편이 낫다.**

### 0.2 🔴 "꺼진 상태 = 404"는 조건부 등록만으로 성립하지 않는다

2026-07-31 실측 (backend-dev 발견 → pm-lead 재현):
```
POST /api/v1/auth/test-login   → 401   ← 404 아님
POST /api/v1/auth/nonexistent  → 401   ← 경로 존재 여부와 무관
GET  /actuator/health          → 500   ← permitAll 인데 핸들러 없음
```

`SecurityConfig`의 permitAll 목록에 없는 경로는 **라우팅에 닿기 전에 Security 필터가 401로 끊는다.**

**401이 해로운 이유 — 구별 불가 정도가 아니라 적극적으로 틀린 결론을 낸다.**

mobile-dev 코드 실측 (`KtorfitModule.kt:67-72`): Ktor `Auth(bearer)`의 `refreshTokens` 블록이 돌면, 로그인 화면에는 refresh token이 없으므로 `authEventBus.emitSessionExpired()` → `MainViewModel` → `navigator.switchTab(Route.Login)` 로 이어진다. **경로가 없을 뿐인데 앱이 "세션 만료"라고 판단하고 전역 이벤트를 쏜다.**

> ⚠️ **다만 이 경로가 실제로 발동하는지는 확정되지 않았다.** Ktor의 refresh 트리거는 서버의 `WWW-Authenticate: Bearer` 챌린지 유무에 영향을 받는데, **실측 결과 현재 서버의 401 응답에는 이 헤더가 없다**(backend-dev·pm-lead 각각 확인):
> ```
> HTTP/1.1 401
> Content-Type: application/json;charset=UTF-8
> (WWW-Authenticate 헤더 없음)
> ```
> 따라서 refresh가 안 돌 수도 있다. **어느 쪽이든 결과는 나쁘다** — 돌면 가짜 세션 만료, 안 돌면 영문 `"Unauthorized"` 스낵바. **해결책(서버가 404를 준다)은 두 경우 모두에 유효**하므로 이 불확실성이 결정을 막지 않는다.

**모바일 단독 방어로는 못 막는다** — repository가 `HttpError.code`로 401을 "미지원"으로 처리할 수는 있으나, `emitSessionExpired()`는 **Ktor Auth 플러그인 내부에서 repository보다 먼저** 일어난다. **서버가 404를 주는 것이 유일한 근본 해결이다.**

따라서 다음 2건이 함께 필요하다:

| | 내용 | 조건부 여부 |
|---|---|---|
| **T-B1a** | `SecurityConfig`에 `/api/v1/auth/test-login` **permitAll 추가** | **상시 (플래그 무관)** |
| **T-B1b** | `GlobalExceptionHandler`에 `NoResourceFoundException`/`NoHandlerFoundException` → **HTTP 404** | 상시 |

> ⚠️ **permitAll을 플래그와 같은 조건으로 묶으면 안 된다.** 플래그 off 시 permitAll도 사라져 다시 401이 되어 목표를 달성하지 못한다. **404가 나오려면 off일 때도 Security를 통과해 라우팅까지 가야 한다.**
>
> **경로에 핸들러가 없을 때의 permitAll은 무해하다** — "인증 없이 라우팅까지 도달"만 허용하고 라우트가 없으면 404다. **fail-closed를 지키는 것은 permitAll이 아니라 빈 조건부다.**
>
> 다만 **나중에 이 경로에 다른 핸들러를 매핑하면 인증 없이 공개된다** — `SecurityConfig`에 그 취지를 주석으로 남긴다.

T-B1b는 test-login과 무관하게 **그 자체로 옳은 수정**이다 — 500은 "서버가 고장났다"는 뜻인데 실제로는 "그런 경로가 없다"이다. 부수적으로 백로그의 `/actuator/health` 500 건도 해소된다.

---

## 1. POST `/api/v1/auth/test-login`

### 설명
지정한 테스트 계정으로 access + refresh 토큰을 발급한다. 계정이 없으면 생성하고 있으면 재사용한다(**멱등**).

### 인증
없음. (이 엔드포인트 자체가 인증을 만드는 지점이다.)

### Request Body (JSON)

```json
{ "testUserNo": 1 }
```

| 이름 | 타입 | 필수 | 검증 |
|------|------|-----|------|
| `testUserNo` | Int | ✓ | **1~3** |

> **선택자 A(인덱스) 확정 근거** (2026-07-31, backend-dev·mobile-dev 독립적으로 같은 결론):
> - **인증 우회 엔드포인트다.** B(`nickname` 문자열)는 임의 문자열로 **아무 이름의 계정이나 만들 수 있는 표면**이 된다. A는 `1..3` 고정이라 **폭발 반경이 제한**된다.
> - `kakao_id = 999000000 + testUserNo` 규약상 **어차피 숫자 인덱스가 필요**하다. B는 nickname→index 매핑이 추가로 붙어 A에 단계만 하나 더 얹는 꼴이다.
> - **닉네임을 서버가 소유**해야 어긋남이 없다. B로 가면 모바일이 문자열을 들고 있어야 하고, 서버에서 이름을 바꾸면 양쪽이 조용히 어긋난다(mobile-dev).
> - 숫자는 URL/JSON 인코딩 잡음이 없다.

### 테스트 계정 (서버 소유)

| `testUserNo` | `kakao_id` | 닉네임 |
|---|---|---|
| 1 | 999000001 | `테스터1` |
| 2 | 999000002 | `테스터2` |
| 3 | 999000003 | `테스터3` |

- **3개 고정.** 시나리오상 필요한 게 정확히 3이다 (요청자 · 수락자 · 제3자 권한 케이스).
- `kakao_id 999000000+` 대역은 **기존 e2e 하네스가 쓰던 대역을 승계**한다 — 실사용자와 한 쿼리로 분리되고 삭제도 그 조건 하나면 된다.
- **모바일 버튼 라벨 = `테스터1` / `테스터2` / `테스터3`** — 서버 닉네임과 **글자 단위로 동일**하다.

> **왜 글자 단위로 같아야 하나** (2026-07-31 mobile-dev 제기 → pm-lead 지시): spec에 **T-M4(debug 빌드에서 `HomeTopBar`에 계정 표시)**가 추가되면서 **버튼 라벨과 홈 상단 닉네임이 같은 화면 흐름에서 나란히 보이게 됐다.** `"테스트 계정 2"`를 눌렀는데 홈에 `테스터2`가 뜨면 "같은 건가" 하고 한 번 멈추게 되고, 계정 전환을 반복하는 도구에서 그 멈칫이 쌓이면 **이 feature가 없애려던 병목의 축소판**이 된다.
>
> `테스터{n}`으로 통일한 이유: **서버가 실제로 DB에 저장하는 값**이라 바꿀 이유가 없고, 모바일이 거기 맞추면 드리프트 방향이 하나뿐이라 안전하다.

> ⚠️ **계약 작성 시점에는 "내가 누구로 로그인했는지" 보이는 화면이 0건이었다** (2026-07-31 mobile-dev 실측). `UserInfo`는 fetch·캐시되어 `HomeUiState.userInfo`에 담기지만 **렌더되는 곳이 없었다**(`user-info`의 "홈에 UserInfo 노출 안 함" 결정). 홈의 유일한 닉네임 렌더는 받은 도전장 카드의 **상대방** 닉네임이다.
>
> → 계정을 오가는 게 목적인 이 feature에서 치명적이라, pm-lead가 **spec에 T-M4(debug 빌드 한정 `HomeTopBar` 계정 표시)를 추가**했다. 그 결과 **버튼 라벨과 홈 표시가 나란히 보이므로 위의 글자 단위 일치 규약이 실질적으로 중요해진다.**
>
> T-M4는 모바일 UI라 계약 범위가 아니다(spec에만 존재).

### 성공 Response (HTTP 200)
```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "accessToken": "eyJhbGciOi...",
    "refreshToken": "eyJhbGciOi...",
    "userId": 101,
    "isNewUser": false
  }
}
```

```kotlin
// POST /auth/kakao 와 동일한 LoginResponse / LoginData 를 그대로 재사용한다
data class LoginResponse(val data: LoginData) : BaseResponse()

data class LoginData(
    val accessToken: String,
    val refreshToken: String,
    val userId: Long,
    val isNewUser: Boolean,
)
```

> 🔴 **초안 정정 (2026-07-31)** — 초안에 있던 **`nickname` 필드는 실제로 존재하지 않는다.** 서버 `controller/auth/dto/LoginResponse.kt`와 모바일 `remote/model/auth/LoginResponse.kt` 양쪽 확인 결과 **4필드**다. 추가하지 않는다 — 넣으면 `/auth/kakao`와 shape이 갈라져 **모바일이 기존 매퍼를 재사용할 수 없고**, 그러면 "테스트 로그인으로 검증한 것이 실제 로그인을 보증한다"는 이 feature의 전제가 무너진다.
>
> 모바일이 성공 스낵바에 닉네임을 쓰고 싶다면 **`테스터{testUserNo}` 공식으로 클라이언트가 직접 생성한다** — 추가 fetch 0, 서버 의존 0 (2026-07-31 mobile-dev 확정).
>
> (데이터만 보면 로그인 후처리가 채우는 `UserInfo`에도 닉네임이 있지만, **현재 그 값이 화면에 렌더되는 곳은 없다** — 위 §테스트 계정의 주의사항 참조. 따라서 "`UserInfo`에서 얻어 표시한다"는 경로는 지금은 실재하지 않는다.)

**`isNewUser`는 실제 값이다** — 최초 생성 시 `true`, 재사용 시 `false`(멱등이라 2회차부터 자연히 `false`).

> 항상 `false`로 고정하지 않는 이유: spec 수용 기준이 **"카카오 로그인과 동일한 후처리를 탄다"**인데 값만 조작하면 그 요구와 어긋난다(mobile-dev). 또한 나중에 온보딩 화면이 생겼을 때 **테스트 로그인으로는 그 경로를 밟을 수 없게 되어** 테스트 도구가 테스트를 못 하는 자기모순이 된다(backend-dev). 현재 모바일은 `LoginUiEffect.NavigateToHome(isNewUser)`로 양쪽을 이미 다루고 있어 추가 분기가 없다.

### 에러 Response

| 상태 | HTTP | 응답 | 상황 |
|---|---|---|---|
| 켜짐 + 범위 밖 | 200 | `code 700` / `"테스트 계정 번호는 1~3이에요"` | `testUserNo`가 1~3 밖 |
| **꺼짐** | **404** | **BaseResponse 아님 — 라우팅 부재** | 엔드포인트 미등록 |

### 🔴 꺼진 서버(404) 처리 — 모바일이 전담

**404는 BaseResponse가 아니라 라우팅 부재다.** Ktor가 채우는 `message`는 `response.status.description`, 즉 **영문 `"Not Found"`** 이므로 **모바일은 이 값을 사용하지 않고 자체 한국어 문구로 치환한다.**

> `challenge-create`에서 "서버 `message`가 곧 UI 텍스트"라고 못박은 것과 같은 함정인데, 이번엔 문자열을 만드는 주체가 **서버가 아니라 Ktor**라 서버측 문구 통제로는 막을 수 없다(mobile-dev 발견). **서버가 404 body에 한국어를 넣어도 무시될 수 있으므로 body 문구에 의존하지 않는다.**

모바일 동작 (2026-07-31 mobile-dev 확정):

| 시점 | 동작 |
|---|---|
| 로그인 화면 진입 | **사전 probe 하지 않는다.** debug 빌드면 버튼을 그냥 노출 |
| 첫 404 수신 | 한국어 안내 스낵바(`"이 서버는 테스트 로그인을 지원하지 않아요"`) + **그 세션 동안 버튼 비활성** + 비활성 사유 캡션 |
| 이후 | 버튼이 눌리지 않아 같은 404가 반복되지 않는다 |

> **사전 probe를 기각한 이유**: 로그인 화면 진입마다 네트워크 왕복이 하나 늘고, probe 자체가 실패하면 무슨 문구를 띄울지 문제가 재귀한다. **단순 스낵바만으로도 부족**한데, 서버가 미지원인데 버튼이 계속 눌리는 상태로 남아 반복해서 누르게 되기 때문이다. **반응형 비활성**은 사전 비용 0이면서 한 번 눌러본 뒤 UI가 현실을 반영한다.

### 모바일 이중 방어 — 404와 **401을 모두** "미지원"으로 처리

배포 시점 차이나 T-B1a 누락으로 401이 돌아올 수 있으므로, 모바일은 이 엔드포인트에 한해 `ApiResult.Failure.HttpError`의 **`code`를 직접 보고 404·401을 모두** "서버가 테스트 로그인을 지원하지 않음"으로 처리한다. repository가 `ApiResult` 원본을 갖고 있어 `onError: (String)`로 뭉개지기 **전에** 가로챈다.

> **계약의 "모바일은 code로 분기하지 않는다" 규약과 충돌하지 않는다.** 그 규약은 **BaseResponse 비즈니스 에러(7xx)**에 대한 것이고, 이건 **HTTP 전송 계층 상태코드**다. 성격이 다르다.

> ⚠️ **단, 401 경로는 모바일 방어만으로 불완전하다.** Ktor Auth 플러그인의 `refreshTokens` → `emitSessionExpired()`는 **repository보다 먼저** 일어나므로, 모바일이 문구를 치환하더라도 **가짜 세션 만료 이벤트로 로그인 화면이 리셋될 수 있다.** **서버가 404를 반환하는 것(T-B1a + T-B1b)이 유일한 근본 해결이다.**

**404 문구 생성 자체는 서버측 추가 구현이 없다** — 그러나 **404가 나오게 만드는 것은 서버 몫**이다. 두 작업이 짝이며, "서버가 할 일이 없다"는 문구 생성에 한한 이야기다.

### 백엔드측 주의사항
- **`AuthService`의 기존 토큰 발급 경로를 재사용할 것.** 별도 발급 로직을 만들면 ADR-0009 rotation(`refresh_token_hash` 저장)이 갈라지고 토큰 형태가 카카오 로그인과 달라진다.
- **멱등**: `kakao_id`로 조회 후 없으면 생성. 반복 호출로 계정이 늘면 안 된다.
- 생성 시 `phoneNumber = null`, `phoneVerified = false`, `profileImageUrl = null`, `status = ACTIVE`.
- 시각은 ADR-0010대로 `Clock`(KST) 경유. `LocalDateTime.now()` 무인자 호출 금지.

### 모바일측 주의사항
- 성공 후처리는 **카카오 로그인과 완전히 동일한 경로** — 토큰 저장, `UserInfo` 캐시, 홈 이동.
- **debug 빌드에서만** 노출 (`:core:utils`의 기존 `expect val isDebug`).
- **계정 전환 시 전환 직전에 `LogoutUseCase`를 호출해 기존 토큰 + `UserInfo` 캐시를 먼저 비운다.**
  > `UserInfoRepository`가 **`CACHE_FIRST`**라 이걸 안 하면 `테스터1` → `테스터2`로 바꿔도 **홈이 계속 `테스터1` 닉네임을 보여준다.** 토큰만 갈리고 캐시는 남기 때문이다(mobile-dev).
  >
  > 🔴 **`clearTokens()`만으로는 부족하다** (2026-07-31 정정, 3자 실측 확인):
  > ```kotlin
  > // LoginRepositoryImpl.clearTokens() — 토큰과 Ktor Auth 캐시만 비운다
  > tokenLocalDataSource.clearTokens()
  > authTokenCacheInvalidator.invalidate()
  > // UserInfo 캐시는 건드리지 않는다
  >
  > // 둘을 함께 정리하는 것은 LogoutUseCase 다
  > loginRepository.clearTokens()
  > userInfoRepository.clearUserInfoCache()
  > ```
  > `userInfoLocalDataSource.clear()` 는 `UserInfoRepositoryImpl.clearUserInfoCache()` 안에서만 호출된다.
  > 초안에 "`clearTokens()`가 이미 `userInfoLocalDataSource.clear()`까지 수행한다"고 적혀 있었으나 **사실이 아니다** — `user-info` mobile-report 의 서술을 근거로 삼았는데 현재 코드에는 없다.
  >
  > **로그아웃 경로 자체에는 버그가 없다** — `LogoutUseCase` 가 이미 둘 다 부른다. 계약 문구만 사실과 달랐다.

### ADR-0009(1기기 1세션)와의 관계 — **충돌 없음**

`updateRefreshTokenHash(userId, hash, issuedAt)`는 **user 행 단위**다. `테스터1` → `테스터2` 전환 시 `테스터2` 행의 hash만 쓰이고 **`테스터1` 행은 건드리지 않는다.** 서버 측에서 이전 계정 세션은 살아 있다.

실제로 일어나는 일은 **클라이언트 저장소 덮어쓰기**뿐이며(토큰 한 쌍만 보관), 서버 상태 문제가 아니다. 1기기 1세션은 **같은 계정을 두 번 로그인할 때** 적용되는데, 그 경우 무효화되는 건 이미 로컬에서 버린 토큰이라 무해하다.

→ **로그아웃 없이 계정 전환을 허용한다.**

---

## 오픈 이슈 — **전건 해소, 미결 없음**

1. ~~**선택자 형태 A vs B**~~ — ✅ **A(`testUserNo` 1~3) 확정.** 인증 우회 표면 제한 + `kakao_id` 규약상 인덱스 필수 + 닉네임 서버 소유로 드리프트 방지.
2. ~~**테스트 계정 수와 닉네임**~~ — ✅ **3개, 닉네임 서버 소유(`테스터{n}`).**
3. ~~**꺼진 서버에 대한 모바일 동작**~~ — ✅ **404 + 모바일 자체 문구 치환 + 반응형 비활성, 사전 probe 없음.** 단 **404가 나오려면 T-B1a/T-B1b가 선행**돼야 한다(초안은 404를 전제했으나 실측은 401이었다).
4. ~~**`isNewUser` 취급**~~ — ✅ **실제 값 그대로.**
5. ~~**로그아웃 없이 계정 전환**~~ — ✅ **허용.** ADR-0009와 충돌 없음(행 단위 hash). 모바일이 전환 전 `clearTokens()`로 캐시 정리.

## 협의 이력

| 일시 | 작성자 | 변경 |
|------|-------|------|
| 2026-07-31 | pm-lead | 초안 — endpoint 1건, 조건부 존재 규약, 오픈 이슈 5건 (상태: `draft`) |
| 2026-07-31 | backend-dev | 서버·모바일 코드 실측 후 5건 구체안. 🔴 **초안 전제 2건이 사실과 다름을 발견** — (1) 응답의 `nickname` 필드가 **실재하지 않음**(양쪽 DTO 4필드), (2) 꺼진 엔드포인트는 404가 아니라 **401**이며 Ktor Auth가 refresh로 가로채 모바일이 상태를 구별할 수 없음. permitAll만 추가하면 **500**(`/actuator/health` 실증). T-B1a/T-B1b 추가 제안 (상태: `draft` → `negotiating`) |
| 2026-07-31 | mobile-dev | 이슈 1·2·4 동의(독립적으로 같은 근거 도출). 이슈 3에 **Ktor가 영문 `"Not Found"`를 `message`에 채워 스낵바에 그대로 뜬다**는 결함 발견 → 모바일 자체 문구 치환 + **반응형 비활성**(사전 probe 기각) 확정. 이슈 5는 **`UserInfoRepository`가 `CACHE_FIRST`라 전환 후 이전 닉네임이 남는다**는 더 정확한 원인 규명 + 전환 전 `clearTokens()` 확정 |
| 2026-07-31 | pm-lead | 발견 3건 재현·승인. **backend-dev의 T-B1a 제안에서 결함 지적** — permitAll을 플래그와 같은 조건으로 묶으면 off 시 permitAll도 사라져 **다시 401**이 되므로 목표 미달성. **permitAll은 상시, 빈만 조건부**로 정정(fail-closed를 지키는 것은 permitAll이 아니라 빈 조건부다). spec에 T-B1a/T-B1b 분리 반영 |
| 2026-07-31 | mobile-dev | `KtorfitModule.kt:67-72` 실측 — 401 시 `refreshTokens` → **`emitSessionExpired()` → 로그인 화면 리셋**. "구별 불가" 정도가 아니라 **적극적으로 틀린 결론**을 낸다. T-B1a/T-B1b를 강하게 지지. 모바일 이중 방어(404·401 모두 미지원 처리) 제안하되 **`emitSessionExpired()`는 repository보다 먼저라 모바일 단독 방어로는 불완전**함을 명시. `confirmed` 계약의 사실 오류 1건 지적 — **`UserInfo`는 캐시만 되고 렌더 0건**이라 "홈에서 실제 이름을 본다"가 사실과 다름 |
| 2026-07-31 | backend-dev | 위 2건 반영 — 모바일 이중 방어 절 신설(전송 계층 vs BaseResponse 구분 명시), **`UserInfo` 관련 서술 2곳 정정**(렌더 0건 실측 확인, 스낵바는 `테스터{n}` 공식으로 클라 생성). `WWW-Authenticate` 헤더 부재를 직접 확인해 **refresh 발동 여부를 "확정되지 않음"으로 등급 하향** — 결론은 불변이나 `confirmed` 문서에 검증되지 않은 인과를 단정으로 남기지 않기 위함 |
| 2026-07-31 | mobile-dev | T-M3 구현 중 계약의 **사실 오류 3번째** 발견·자진 정정 — `clearTokens()` 가 `UserInfo` 캐시를 비운다는 서술이 틀렸다(자신이 `user-info` mobile-report 를 근거로 제공한 정보였고 현재 코드에는 없다). 실제로는 `LogoutUseCase` 가 `clearTokens()` + `clearUserInfoCache()` 를 함께 부른다. **이슈 5 결론은 불변, 호출 대상만 변경.** 로그아웃 경로 자체에는 버그 없음 |
| 2026-07-31 | backend-dev | 위 정정을 **모바일 코드로 직접 재확인 후** 반영(`LoginRepositoryImpl` / `UserInfoRepositoryImpl` / `LogoutUseCase` 3파일). 이 feature 에서 "문서를 근거로 한 미확인 진술"이 `confirmed` 계약에 들어간 게 **세 번째**(① `nickname` 필드 ② 홈 닉네임 렌더 ③ `clearTokens()`)라, 남은 코드 관련 서술 전수 재검증 |
| 2026-07-31 | backend-dev | **구현 중 격리 수단 변경** — `@ConditionalOnProperty` → `:core`의 커스텀 `Condition`. 근거 (1) `:service`에 `spring-boot-autoconfigure` 부재 (2) 🔴 **`getProperty(Boolean::class)`가 오타(`"enabled"`/`""`)에 `ConversionFailedException`을 던져 서버가 기동 중 죽는다**(실측). 문자열 `"true"` 정확 비교로 전환 — fail-closed는 "안 열린다"여야지 "터진다"가 아니다. 결정(속성 기반·프로파일 미도입)은 불변, 수단만 변경 (pm-lead 승인) |
| 2026-07-31 | backend-dev | pm-lead 정정 수용(내 제안이 틀렸다 — 조치의 결과를 확인하지 않았다). **격리 방식을 `@ConditionalOnProperty`로 확정**(프로파일 미도입, 실측 근거 4가지). 응답 shape 4필드 확정, 테스트 계정 3개·닉네임 규약 확정, 모바일 404 처리·`clearTokens()`·ADR-0009 무충돌 분석 반영. **오픈 이슈 5건 전부 해소 — 미결 0건, 상태 `negotiating` → `confirmed`** |
