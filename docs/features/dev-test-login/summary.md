# 개발용 테스트 로그인 (dev-test-login) — Summary

- **feature-id**: dev-test-login
- **완료일**: 2026-08-03
- **상태**: **partially-completed** — 기능은 실사용으로 동작 확인. **격리(꺼진 상태) 실서버 검증은 배포 전 관문으로 이월**
  > **2026-08-03 사용자 결정**: 개발이 끝날 때까지 이 기능을 **켠 채로 유지**한다. 개발 중 켜두는 것은 정상이자 의도된 사용법이며, 격리가 막으려는 위험("운영에 새어나감")은 **배포 시점에만 현실화**된다. 따라서 꺼진 상태 실서버 검증은 **미완 결함이 아니라 배포 전 절차**로 이월했다. 단위 6케이스(실제 Spring 컨텍스트에서 빈 미생성 확인)는 통과 상태다.

## 구현 개요

친구 요청·수락·거절과 챌린지 신청·수락은 **계정이 2개 이상** 있어야 손으로 검증되는데, 모바일 로그인 경로가 **카카오 하나뿐**이라 사용자가 혼자 돌 수 없었다. `friends`·`challenge-create`에 "manual smoke", "실기기 검증"이 계속 미해결로 쌓이던 병목이 이것이다.

**가짜 계정 3개 + debug 빌드 전용 로그인 버튼**을 만들어 해소했다. 계정은 미리 심지 않고 **호출 시 upsert**(멱등)한다.

이 feature는 **카카오 검증 없이 JWT를 발급하는 인증 우회 경로**라, 격리를 기능과 동등한 수용 기준으로 다뤘다.

## 엔드포인트

| Method | Path | 상태 |
|--------|------|------|
| POST | `/api/v1/auth/test-login` | deployed (**조건부 존재** — 속성을 켠 환경에서만) |

## 화면 / UI 변경

- `:feature:login` — `TestLoginSection` 신규. **debug 빌드에서만** 노출(`isDebug`), 계정 3개 선택.
- `:feature:home` — **debug 빌드에서만** `HomeTopBar`에 현재 계정 닉네임 노출. 계정을 오가는 게 목적인 feature라 "지금 누구인지"가 안 보이면 손 검증 결과를 신뢰할 수 없다.

## 주요 변경 파일

**백엔드** (커밋 `3b73627`)
- `core/.../TestLoginEnabledCondition.kt` (신규) — 커스텀 `Condition`
- `service/.../TestLoginService.kt` · `controller/.../TestLoginController.kt` (신규)
- `service/.../AuthService.kt` — `issueTokens(userId)` **추출**하여 카카오 로그인과 공유
- `config/SecurityConfig.kt` — test-login 경로 permitAll **상시**
- `controller/.../GlobalExceptionHandler.kt` — `NoResourceFoundException`/`NoHandlerFoundException` → **404**

**모바일** (커밋 `d36b42e`)
- `feature/login/component/TestLoginSection.kt` · `contract/TestLoginState.kt` (신규)
- `domain/usecase/LoginWithTestAccountUseCase.kt` (신규) — 내부에서 `LogoutUseCase` 호출
- `data/.../TokenLocalDataSource` **interface 분리** + `Impl`
- `feature/home/component/HomeTopBar.kt` · `HomeScreen.kt` · `contract/HomeUiState.kt`

## 테스트 결과

**백엔드 — 134/134 passed, 0 failed** (직전 125, +9)
- `TestLoginIsolationTest` 9건 중 **6건이 꺼진 상태** — 실제 Spring 컨텍스트에 태워 빈 생성 여부 확인
- 404 핸들러 회귀 방지 2건

**백엔드 켠 상태 실서버 — 34/34 PASS, 0 FAIL** (2026-08-03)
- `isNewUser` 최초 `true` / 응답 4필드 + `nickname` 부재 / 멱등(4회 추가) / 범위 밖 4종 → 700 / 발급 토큰으로 기존 API 5종 / **ADR-0009 rotation 정상**(`refresh_token_hash` 64자 + `issued_at`) / 사용자 데이터 무결성 6건

**모바일 — 148/148 passed, 0 failed** (직전 134, +14)
- **기존 134건 회귀 0, 삭제·교체 0건.** Android · KMP common · iOS 링크 전부 SUCCESS

**🔴 꺼진 상태 실서버 검증 — 미완.** 단위 6케이스는 커버하나 실서버는 아니다. 이 feature의 **핵심 수용 기준**이다.

## 실사용 검증 (사용자, 2026-08-03)

- **테스트 계정으로 친구 요청 → 수락 성공** — `friendships` 1건 `ACCEPTED`, 09:38:54 요청 → 09:39:01 수락. **이 feature가 만들려던 상황이 실제로 동작했다.**
- **챌린지 플로우** — 사용자가 손 검증 완료로 확인. 단 검증 후 DB에 `challenges` row가 **0건**이라 **수락 경로(`IN_PROGRESS` 전환 + `verifications` 2건)의 DB 레벨 증거는 남아 있지 않다.** 취소가 물리 삭제이므로 "신청 → 취소" 경로만 돌았다면 정상적으로 0이 된다. 수락 경로의 DB 증거가 필요하면 재확인이 필요하다.
- **ADR-0010 KST 저장이 실사용 데이터로 재확인** — 테스터3 `created_at` 09:47:59 vs `now()` 09:50:13(2분 14초 차). UTC였다면 9시간 차다.

## 결정 사항

1. **격리는 커스텀 `Condition`** (프로파일 미도입, `@ConditionalOnProperty`도 미사용)
   - **프로파일 기각**: 프로파일은 시간이 지나며 **의미가 누적된다** — 누군가 로깅·CORS 때문에 `dev`를 켜는 순간 **인증 우회까지 딸려 켜진다.** spec이 금지한 "끄는 걸 잊으면 열리는" 구조의 변형이다.
   - **`@ConditionalOnProperty`도 못 씀**: `:service`에 `spring-boot-autoconfigure`가 없다. 어노테이션 하나 때문에 모듈 의존성을 늘리는 대신 `:core`에 `Condition`을 두고 `:service`/`:controller`가 **같은 정의를 공유**하게 했다(조건이 갈리면 "컨트롤러는 있는데 서비스가 없는" 상태가 생긴다).
2. **🔴 `getProperty(name, Boolean::class, false)`를 쓰지 않는다** — Spring이 `"enabled"`/`""` 같은 인식 불가 값에 `ConversionFailedException`을 **던진다.** 즉 **오타 하나로 서버가 기동 중 죽는다.** **fail-closed는 "안 열린다"여야지 "터진다"가 아니다.** → 문자열 `"true"` 정확 비교로 전환, 인식 불가 값은 전부 꺼짐으로 수렴.
3. **permitAll은 상시, 빈만 조건부** — 플래그와 같은 조건으로 묶으면 off 시 permitAll도 사라져 **다시 401**이 되어 404 목표를 달성하지 못한다. **fail-closed를 지키는 것은 permitAll이 아니라 빈 조건부다.** 경로에 핸들러가 없을 때의 permitAll은 무해하다.
4. **`AuthService.issueTokens` 공유** — 별도 발급 로직을 만들면 ADR-0009 rotation이 갈라지고 토큰 형태가 카카오 로그인과 달라진다. 실서버 검증에서 `refresh_token_hash` 64자 + `issued_at`으로 공유가 실제 동작함을 확인했다.
5. **응답은 `/auth/kakao`와 동일한 4필드** — `nickname`을 추가하지 않는다. shape이 갈라지면 모바일이 기존 매퍼를 못 쓰고, 그러면 **"테스트 로그인으로 검증한 것이 실제 로그인을 보증한다"는 전제가 무너진다.**
6. **꺼진 서버는 404** — 401이면 모바일 Ktor `Auth(bearer)`가 "access 만료"로 보고 refresh를 시도하다 **`emitSessionExpired()`를 쏴 로그인 화면을 리셋한다.** 경로가 없을 뿐인데 앱이 "세션 만료"라고 **적극적으로 틀린 결론**을 낸다. 모바일 방어로는 못 막는다(Ktor 플러그인이 repository보다 먼저 동작).
7. **404 문구는 모바일이 자체 생성** — Ktor가 채우는 `message`가 영문 `"Not Found"`다. `challenge-create`의 "서버 `message`가 곧 UI 텍스트"와 같은 함정인데, 이번엔 문자열을 만드는 주체가 **서버가 아니라 Ktor**라 서버측 통제로는 막을 수 없다.
8. **모바일 격리는 런타임 게이트** — `isDebug`는 코드가 release APK에 들어가되 렌더만 안 된다. 컴파일 제외는 KMP에서 비용이 크고, **실질 방어선은 서버 fail-closed**다(release 환경엔 엔드포인트가 아예 없다). 모바일 게이트는 defense-in-depth.

## 미해결 이슈

- [ ] **🔴 꺼진 상태 실서버 검증 미완** — 이 feature의 핵심 수용 기준. `e2e-off.sh`(9단언) 준비 완료, 속성 빼고 재기동하면 즉시 실행 가능. **`/actuator/health` 404가 test-login 경로의 404를 자동 보장하지 않는다** — 같은 핸들러여도 permitAll 상시 적용이 함께 걸려야 성립하는 조합이다.
- [ ] **챌린지 수락 경로의 DB 증거 부재** — 위 "실사용 검증" 참조.
- [ ] **🟢 테스트 계정 정리 수단 없음** — DB에서 직접 지운다. `DELETE FROM users WHERE kakao_id BETWEEN 999000001 AND 999000999;`
- [ ] iOS 유닛 테스트 미실행 (기존 관행: Android 유닛 + iOS 링크까지가 게이트)

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [change-log.md](./change-log.md)
- [mobile-report.md](./mobile-report.md) · [backend-report.md](./backend-report.md)
