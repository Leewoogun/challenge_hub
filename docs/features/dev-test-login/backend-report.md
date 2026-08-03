# Backend Report — dev-test-login

- **feature-id**: dev-test-login
- **작성**: 2026-08-03 by backend-dev
- **상태**: implemented + **켠 상태 실서버 검증 완료 (34/34)**, 🔴 **꺼진 상태 실서버 검증 미완**
- **선행 입력**: [spec.md](./spec.md), [api-contract.md](./api-contract.md) (status: `confirmed`)
- **빌드 검증**: `./gradlew clean build` → **BUILD SUCCESSFUL** / 실행 테스트 **134/134 passed, 0 failed** / 통합 45건 Docker 미가용 skip
- **커밋**: 사용자가 `3b73627 "테스트 계정으로 로그인 기능 추가"` 로 커밋함 (내가 하지 않음)

## 구현 요약

카카오 검증 없이 JWT 를 발급하는 **인증 우회 엔드포인트** 1건을 추가했다. spec 이 격리를 기능과 동등한 수용 기준으로 못박았으므로, 이 리포트도 **격리를 먼저** 다룬다.

핵심 설계는 셋이다:
1. **빈 자체가 조건부** — 속성을 켠 환경에서만 컨트롤러·서비스 빈이 생성된다. 등록해 놓고 403 을 주는 방식이 아니다.
2. **`AuthService.issueTokens` 공유** — 카카오 로그인과 **같은 발급 경로**를 탄다. 별도 로직이면 ADR-0009 rotation 이 갈라진다.
3. **꺼진 상태가 404 로 보이게 하는 부수 작업 2건**(T-B1a/T-B1b) — 이게 없으면 401·500 이 나가 모바일이 틀린 결론을 낸다.

## T-B1 — 격리 장치

### 🔴 채택: 커스텀 `Condition` (프로파일 미도입, `@ConditionalOnProperty` 도 미사용)

```
challenge.dev.test-login.enabled=true   → 빈 생성
(미설정 / false / 그 외 값)              → 빈 미생성 → 라우팅 부재 → 404
```

**프로파일을 쓰지 않은 이유** — 레포 실측: `@Profile`·`spring.profiles` **0건**, 프로파일별 yml **0건**.
프로파일은 시간이 지나며 **의미가 누적**된다. 누군가 로깅·목데이터·CORS 때문에 `dev` 를 켜는 순간 **인증 우회까지 딸려 켜진다.** spec 이 금지한 "끄는 걸 잊으면 열리는" 구조의 변형이다.

**`@ConditionalOnProperty` 를 쓰지 않은 이유 2가지** (구현 중 드러남):

**(1) `:service` 에 `spring-boot-autoconfigure` 가 없다.** 어노테이션 하나 때문에 모듈 의존성을 늘리는 대신 `spring-context` 만으로 되는 `Condition` 을 `:core` 에 두고 **`:service`/`:controller` 가 같은 정의를 공유**한다. 두 곳 조건이 갈리면 "컨트롤러는 있는데 서비스가 없는" 상태가 생긴다.

**(2) 🔴 `getProperty(name, Boolean::class, false)` 는 오타에 서버를 죽인다.** 실측:
```
"true"/"TRUE"/"1"/"yes"/"on"  → true
"0"/"no"/"off"                → false
"enabled" / ""                → ConversionFailedException  ← 던진다
(미설정)                       → false
```
`challenge.dev.test-login.enabled=enable` 같은 **오타 하나로 애플리케이션이 기동 중 죽는다.** dev 전용 플래그의 오타가 서버 전체를 내리는 건 과한 실패 모드다 — **fail-closed 는 "안 열린다"여야지 "터진다"가 아니다.**

→ **문자열 `"true"` 정확 비교**(대소문자·앞뒤 공백 무시). 인식 못 하는 값은 전부 **꺼짐으로 수렴**하고, Spring 변환기 구현이 바뀌어도 흔들리지 않는다. `"1"`/`"yes"`/`"on"` 을 잃지만 **보안 경계라 켜는 방법이 하나뿐인 편이 낫다.**

> 이건 내 테스트가 실패해서 발견했다. 원래 단언("`1` 도 거부한다")이 틀렸고, **단언을 고쳐 통과시키는 대신 왜 실패하는지 판 결과** 진짜 문제가 나왔다.

### T-B1a — `SecurityConfig` permitAll **상시**

```
플래그 off → permitAll ○ / 라우트 ✗ → 404   ← 원하는 상태
플래그 on  → permitAll ○ / 라우트 ○ → 정상
```

⚠️ **내 최초 제안(플래그와 같은 조건으로 묶기)은 틀렸고 pm-lead 가 정정했다.** 묶으면 꺼졌을 때 permitAll 도 사라져 **다시 401** 이 되어 목표를 놓친다. "fail-closed" 원칙을 조치에 기계적으로 붙이면서 **그 조치가 실제로 만드는 결과를 확인하지 않은** 실수다.

**실제 노출을 막는 것은 permitAll 이 아니라 "빈이 존재하지 않는다"는 사실이다.** 핸들러가 없으면 permitAll 은 "인증 없이 라우팅까지 도달"만 허용하고 그 끝은 404 다. 이 문장과 **"이 경로에 다른 핸들러를 매핑하면 인증 없이 공개된다"** 는 경고를 `SecurityConfig` 주석에 남겼다.

### T-B1b — `GlobalExceptionHandler` 404 핸들러

`NoResourceFoundException`/`NoHandlerFoundException` → **HTTP 404**. 없으면 catch-all 이 **500** 으로 삼킨다.

**미등록 경로가 500 을 주는 건 그 자체로 틀렸다** — 500 은 "서버가 고장났다"는 뜻인데 실제로는 "그런 경로가 없다"이다. 부수적으로 **백로그의 `/actuator/health` 500 건이 해소**됐다(pm-lead 실측 확인: 404).

## T-B2 — 엔드포인트

| 항목 | 내용 |
|---|---|
| 경로 | `POST /api/v1/auth/test-login` (조건부 존재) |
| 요청 | `{"testUserNo": 1~3}` |
| 응답 | `LoginResponse`/`LoginData` **그대로 재사용** — `/auth/kakao` 와 4필드 동일 |
| 계정 | `kakao_id 999000001~3` / 닉네임 `테스터1~3` |
| 멱등 | `kakao_id` 조회 후 없으면 생성. 있으면 **닉네임도 덮지 않는다**(손 테스트 중 DB 에서 이름을 바꿔 구분하는 경우를 지키기 위해) |

**`AuthService.issueTokens(userId)` 추출** — `loginWithKakao` 와 test-login 이 공유한다. 별도 발급 로직이면 `refresh_token_hash` 저장이 갈라져 rotation 이 한쪽에서만 동작하고, 토큰 형태가 달라져 모바일이 후처리를 두 벌 만들어야 한다.

## 테스트 결과

### 단위·슬라이스: **134/134 passed, 0 failed** (직전 125 → +9)

| 테스트 | 건수 | 비고 |
|---|---|---|
| **TestLoginIsolationTest** | **9** | 신규 — 아래 상술 |
| GlobalExceptionHandlerTest | 9 | +2 (404 핸들러) |
| 그 외 전건 | 116 | 회귀 0 |

**`TestLoginIsolationTest` 9건 중 6건이 꺼진 상태다** (spec: *"후자가 더 중요하다 — 켜진 건 눈에 보이지만 꺼진 건 검증 안 하면 아무도 모른다"*).

**실제 Spring 컨텍스트에 태워** 빈 생성 여부를 본다 — 조건 클래스의 `matches()` 만 직접 부르면 "Spring 이 실제로 이 조건을 존중하는가"를 검증하지 못한다.

- 속성 미설정 → 빈 없음 (**fail-closed 기본값**)
- `false` → 빈 없음
- `1`/`yes`/`on`/`0`/`no`/`off`/`enabled`/`""`/`tru`/`false` **10종 전부** → 빈 없음
- **인식 불가 값에서도 예외 없이 꺼짐** — 서버가 안 죽는다
- `true`/`TRUE`/`  true  ` → 빈 생성
- 속성 이름·계정 규약이 계약과 일치

### 🟢 켠 상태 실서버 검증: **34/34 PASS, 0 FAIL** (2026-08-03)

서버가 `challenge.dev.test-login.enabled=true` 로 기동 중인 상태에서 실행.

| 구간 | 결과 |
|---|---|
| 1. `isNewUser` 최초 생성 = `true` | 2/2 |
| 2. 응답 shape 4필드 + `nickname` 부재 + JWT 형태 | 4/4 |
| 3. 재사용 `false` + 멱등(4회 추가 호출) | 3/3 |
| 4. 계정 규약 `999000001~3` / `테스터1~3` | 2/2 |
| 5. 범위 밖 4종 → 700 + 확정 문구 + 계정 미생성 | 6/6 |
| 6. 발급 토큰으로 기존 API 5종 | 7/7 |
| 7. ADR-0009 rotation (`hash` 64자 + `issued_at`) | 2/2 |
| 8. **KST 저장 실사용 확인** | 1/1 |
| 9. `/v3/api-docs` 노출 | 1/1 |
| 10. **사용자 데이터 무결성** | 6/6 |
| **합계** | **34/34** |

검증된 것:
- **`AuthService.issueTokens` 공유가 실제로 동작한다** — 테스트 로그인으로 발급해도 `refresh_token_hash` 가 sha256 64자로 저장되고 `issued_at` 이 채워진다. rotation 이 갈라지지 않았다는 직접 증거다.
- **발급 토큰이 기존 인증 API 전부에서 동작한다** — `/users/me`·`/friends`·`/challenges/received`·`/challenges/active`·`/record`.
- **ADR-0010 KST 저장이 실사용 데이터로 확인됐다** — 테스터3 `created_at` 과 `now()` 차이가 **1초**다. UTC 저장이었다면 32,400초여야 한다.

### 🔒 사용자 데이터 보호 — 하네스를 고쳐서 돌렸다

pm-lead 경고를 받고 실행 **전에** DB 를 확인한 결과 두 가지가 나왔다:

1. `friendships` 1행이 **실사용자(id 1) ↔ 테스터1(id 14)** 이다. 사용자가 손으로 만든 검증 결과다.
2. **더 중요한 것**: `test-login` 호출은 **ADR-0009 rotation 을 일으켜 해당 계정의 `refresh_token_hash` 를 덮어쓴다.** 사용자가 테스터1/2 로 앱에 로그인해 있으면 **진행 중인 손 검증 세션이 끊긴다.**

→ 하네스를 다음과 같이 **고쳐서** 돌렸다:
- 원래 있던 `DELETE FROM users WHERE kakao_id = 999000003` **제거**. 대신 **테스터3 이 아직 없다는 사실을 이용해 첫 호출로 `isNewUser=true` 를 검증**했다 — 삭제 없이 같은 것을 확인한다.
- **테스터1/2 로는 한 번도 로그인하지 않았다.** 모든 로그인 검증을 테스터3 으로만 수행. 테스터1/2 의 `refresh_token_hash` 는 그대로다.
- `DELETE`/`UPDATE`/`TRUNCATE` 를 **한 줄도 쓰지 않는다**(실행 전 grep 으로 기계적 확인).

**실행 후 상태**:
```
users:       3 → 4        (테스터3 생성분만 증가 — 엔드포인트가 하는 일 그 자체)
friendships: 1 → 1        (불변)
friendship 내용: 1|14|ACCEPTED  (유지)
테스터1(id14)/테스터2(id15): 그대로
실사용자(id1) created_at: 2026-05-07 10:10:42 (불변)
challenges:  0 → 0        (사용자 미검증 구간, 건드리지 않음)
```

**테스터3(id 16)이 새로 생겼다.** 사용자가 3계정을 쓰게 되므로 남겨도 무해하고, 오히려 제3자 케이스 검증에 필요하다. 삭제 원하면 `DELETE FROM users WHERE kakao_id=999000003;`(FK 없음).

## 🔴 미검증 — 꺼진 상태 실서버 검증

**이 feature 의 핵심 수용 기준이 실서버에서 아직 확인되지 않았다.**

| 레벨 | 확인 | 결과 |
|---|---|---|
| 단위 (Spring 컨텍스트) | 꺼진 상태 6케이스 빈 미생성 | ✅ |
| **실서버** | `POST /auth/test-login` → **404** + `/v3/api-docs` 미노출 | **미확인** |

서버가 **켠 상태로만** 떠 있었기 때문이다. `e2e-off.sh`(9단언)는 작성·문법검사 완료 상태로 대기 중이며, 사용자가 챌린지 손 검증을 마치고 속성을 빼고 재기동하면 즉시 실행한다.

검사 항목: `test-login` **404**(401 아님/500 아님을 **각각 별도 단언**으로 — 실패 시 원인이 Security 인지 T-B1b 인지 갈린다) / `/v3/api-docs` 미노출 / `/actuator/health` 404 / 임의 미등록 경로 404 / **기존 인증 경로가 여전히 401**(permitAll 추가가 뭔가 열지 않았는지).

> `/actuator/health` 가 404 로 바뀐 것은 pm-lead 가 이미 실서버에서 확인했다 — T-B1b 가 동작한다는 방증이다. 다만 test-login 경로 자체의 404 는 별도 확인이 필요하다.

## 변경 파일

### 신규
```
core/src/main/kotlin/com/lwg/challenge/core/config/TestLoginEnabledCondition.kt
service/src/main/kotlin/com/lwg/challenge/service/auth/TestLoginService.kt
service/src/main/kotlin/com/lwg/challenge/service/auth/IssuedTokens.kt
controller/src/main/kotlin/com/lwg/challenge/controller/auth/TestLoginController.kt
controller/src/main/kotlin/com/lwg/challenge/controller/auth/dto/TestLoginRequest.kt
app/src/test/kotlin/com/lwg/challenge/controller/auth/TestLoginIsolationTest.kt
```
### 수정
```
app/src/main/kotlin/com/lwg/challenge/config/SecurityConfig.kt          (T-B1a permitAll 상시 + 주석)
controller/.../common/exception/GlobalExceptionHandler.kt               (T-B1b 404 핸들러)
service/.../auth/AuthService.kt                                         (issueTokens 추출)
app/src/test/.../common/exception/GlobalExceptionHandlerTest.kt         (404 테스트 2건)
```
(전부 `/Users/hwamulman/woogunProject/challenge/challenge-server/` 하위)

## 미해결 이슈

1. **🔴 꺼진 상태 실서버 검증 미완** — 위 참조. `e2e-off.sh` 준비 완료, 재기동 대기.
2. **🔴 통합 테스트 45건 여전히 skip** — 컨테이너 런타임 부재(백로그). 이번 변경도 자동화된 통합 검증을 받지 못한다.
3. **🟡 `test-login` 호출이 해당 계정의 기존 세션을 무효화한다** — ADR-0009 rotation 의 정상 동작이지만, 손 검증 중 같은 계정으로 재호출하면 앱 세션이 끊긴다. 모바일이 전환 시 `LogoutUseCase` 로 정리하므로 실사용 흐름에는 문제없다. **운영상 알아둘 것.**
4. **🟢 `TestLoginService` 가 기존 계정의 닉네임을 갱신하지 않는다** — 의도된 선택(위 T-B2 표). DB 에서 이름을 바꿔 계정을 구분하는 손 테스트 방식을 지킨다.
