# 푸시 알림 (push-fcm) — Summary

- **feature-id**: push-fcm
- **완료일**: 2026-08-07
- **상태**: `completed` (Android). **iOS 수신은 범위 제외** — 기술 선택이 아니라 Apple 계정 제약

## 구현 개요

**앱이 사용자에게 먼저 말을 걸 수 있게 됐다.** 이전까지는 홈에 들어와야만 도전장이 온 걸 알 수 있었고, 이 결함은 세 feature에서 반복 지적됐다 — [challenge-create/spec.md](../challenge-create/spec.md) 비범위, [challenge-create/design.md](../challenge-create/design.md)(*받은 도전장 섹션을 진행 중 목록보다 위에 올린 이유가 이것이다*), [soul-oath/spec.md](../soul-oath/spec.md) 미해결.

`users.fcm_token`·`notifications` 테이블·인덱스는 **V1부터 파여 있었고 배관만 없었다.** 이번에 그 배관을 채웠다: 토큰 등록 엔드포인트 → 챌린지 상태 전이 시 이벤트 발행 → `AFTER_COMMIT` 리스너가 `notifications` row 저장 + FCM 발송.

**기획서 §3.1의 5종 중 3종만 이번 범위**다. `REMIND`/`OPPONENT_VERIFIED`/`RESULT`는 카메라 인증·결과 판정에 종속이고 둘 다 미착수다. `SIGN_REQUEST`는 `soul-oath`가 수락과 서명을 원자로 묶으면서 **대상 상태 자체가 소멸**해 폐기했다. 반대로 *"수락/거절을 신청자에게 알림"*은 기획서에 없던 공백이라 이번에 새로 정의했다(2026-08-06 기획서 개정 반영).

> **후속 feature를 위한 상태**: 나머지 3종은 타입·배관·no-op 격리가 전부 준비된 채 대기 중이다. 인증·판정 feature는 **발송 호출 한 줄만** 붙이면 된다.

## 엔드포인트

| Method | Path | 설명 | 상태 |
|---|---|---|---|
| PUT | `/api/v1/users/me/fcm-token` | FCM 토큰 등록·갱신 (신규) | **deployed** |
| DELETE | `/api/v1/auth/logout` | 스텁 → 실구현. `refresh_token_hash` + `fcm_token` 이중 NULL화 | **implemented** (모바일이 아직 호출 안 함 — 미해결 참조) |

`POST /challenges` · `/accept` · `/reject` 는 **요청·응답 shape 무변경**. 알림 발송은 부수 효과로만 붙었다.

## 주요 변경

**백엔드** (`f01bd44` 42파일 +2999/-5, `e76c64c` 문구 수정)
- `UserController.updateFcmToken` + `UserService` — §0.2 **토큰 소유권 이전 2단계 UPDATE**
- `AuthController.logout` 실구현 — `foundation` 시절 미구현 TODO 흡수
- `NotificationType` enum + `V8__notification_type_recomment.sql` (**DDL·DML 0건, `COMMENT ON COLUMN` 2건만**)
- `NotificationSender` 포트 + `FcmNotificationSender` + **`NoOpNotificationSender`** + `NotificationSenderConfig`
- `NotificationDispatcher` — `@TransactionalEventListener(AFTER_COMMIT)` + `@Transactional(REQUIRES_NEW)`
- `NotificationMessages` — 문구 단일 출처
- `.gitignore` 비밀키 방어 (`*-adminsdk-*.json` 등 5패턴)

**모바일** (`d13dd9b` 36파일 +766/-2, `27dfb96`, `799a71e` 20파일 +355/-70)
- **`:core:push` 모듈 신설** — `FcmTokenProvider` expect/actual (android/ios)
- `ChallengeFirebaseMessagingService` — 수신 + 포그라운드 직접 표시 + `onNewToken`
- `FcmTokenRepository` / `FcmTokenRemoteDataSource` / DTO 2종
- `LoginViewModel.registerFcmToken()` — 로그인 성공 직후 등록
- moko-permission 도입 + 플랫폼별 권한 요청

## 테스트 결과

- **백엔드: 254/254 passed** (전체 299 중 skip 45). baseline 192 → 신규 62, **회귀 0**
- **모바일: 빌드 초록** (`assembleDebug` + 단위 테스트, `GRADLE_EXIT_CODE=0`, FAILED 0)
- 통합 테스트 45건은 **컨테이너 런타임 부재로 skip** (누적 건, 백로그 🔴)

## 🔴 실기 검증 (2026-08-07) — DB 교차 검증

**서버 재기동 전** (키 미주입): §0.4 no-op 격리가 실기에서 증명됐다 — 키가 없는데도 서버 정상 기동, 챌린지 생성 성공, row 저장, **발송만 조용히 스킵**. `notif#1`(수신자 토큰 NULL)은 *"발송 스킵 + row는 저장"* 수용 기준을 실제 DB에서 확인.

**재기동 후** (`.env`의 `FCM_CREDENTIALS_PATH` 주입): **`send()` 본체가 처음 실행됨.** 알림 3종 전부 발화.

| type | 발화 | 수신자 배분 |
|---|---|---|
| `CHALLENGE_REQUEST` | 5회 | 상대 ✅ |
| `CHALLENGE_REJECTED` | 2회 | **신청자** ✅ (방향 반전) |
| `CHALLENGE_ACCEPTED` | 1회 | **신청자** ✅ |

### 🔴 §0.2 토큰 소유권 이전이 실사용으로 증명됐다

같은 기기에서 테스터2 → 테스터3으로 계정을 전환하자 토큰 `dmdMHyuMQyeh…`이 **15 → 16으로 이동하고 15는 `NULL`이 됐다.**

**이것이 중요한 이유**: `LogoutUseCase`가 서버를 호출하지 않으므로 로그아웃이 지운 게 아니다. 지운 것은 **테스터3 로그인 시 §0.2의 첫 번째 UPDATE**다. 이 SQL은 그때까지 **무검증**이었다 — 단위 테스트가 fake를 쓰는데 그 fake는 SQL 술어를 Kotlin으로 다시 쓴 것이라 실제 `AND id <> :me`를 태우지 않았고, 실검증 경로는 skip 중인 통합 테스트뿐이었다. **한 기기가 두 계정의 알림을 받는 일이 실제로 막혔다.**

**부수 검증**: `uq_challenges_active_pair_date`가 `PENDING` 때문에 재신청을 막다가 `REJECTED` 전이 후 풀려 새 챌린지가 생성됐다 — 제약이 의도대로 걸리고 풀리는 것까지.

## 결정 사항

1. **토큰 등록은 로그인 body가 아니라 독립 엔드포인트** — FCM 토큰 수명주기가 로그인 수명주기와 다르다(`onNewToken`은 재설치·데이터 삭제·만료 시 언제든). 로그인에만 실으면 갱신 토큰을 보낼 곳이 없다. 부수 효과로 `auth-kakao` `confirmed` 계약 무접촉.
2. 🔴 **토큰 소유권은 한 계정에만** — 등록 시 같은 토큰을 쥔 다른 user를 먼저 `NULL`로 민다. `dev-test-login` 계정 전환이 **표준 검증 방식**이라 방어가 없으면 개발 첫날 발생한다. **실사용 증명됨**(위 참조).
3. 🔴 **발송은 `AFTER_COMMIT`** — FCM 실패가 챌린지 생성을 롤백시키면 안 된다. *"알림이 안 갔다"*는 불편이지만 *"챌린지가 안 걸렸다"*는 기능 실패다. **롤백 시 미발송은 코드 방어가 아니라 구조가 보장**한다.
4. 🔴 **키 없어도 서버가 선다** — `NoOpNotificationSender` 격리. 덕분에 **Firebase 프로젝트 생성을 기다리지 않고 백엔드 전체를 완성·테스트**했다. `dev-test-login` 교훈(*fail-safe는 "안 열린다"여야지 "터진다"가 아니다*) 적용. 실패 경로 8건 + 빈 선택 3건 전수 커버.
5. **페이로드는 `notification` + `data` 혼합** — 백그라운드 표시 보장 + 라우팅 정보 확보. 딥링크는 범위 밖이지만 `challengeId`를 미리 실어 후속에서 서버 변경 0.
6. **`reference_id`를 `challenge_id`로 못 박지 않는다** — 이름은 중립으로 두고 참조 대상을 `COMMENT ON COLUMN`에 적는다. *현재 3종이 전부 challenge라는 건 오늘의 사실이지 규약이 아니다.* `soul-oath`의 `_signature_url` → `_signature_data` 와 같은 판단.
7. **`notifications.title`/`body`는 박제** — V1 스키마(`VARCHAR(100)` / `TEXT`)가 이미 렌더된 문구를 담는 모양이다. 문구를 바꿔도 과거 알림이 안 바뀌는 게 *"그때 이렇게 통지했다"*는 기록으로 맞다.
8. **KMP 커뮤니티 래퍼 미사용** — 공식 Firebase KMP SDK가 없고, FCM은 공통화할 게 토큰 획득뿐이다(수신·표시는 전적으로 플랫폼 코드). 래퍼는 통제 불가 의존성 + 릴리스 지연 + 부분집합 노출이라 수지가 안 맞는다. **카카오 SDK 선례를 답습**해 네이티브 + expect/actual.
9. **`:core:push` 신설** — 이 레포의 배치 기준은 *"같은 SDK냐"*가 아니라 **"소비자가 누구냐"**다(카카오 SDK도 OAuth는 `:feature:login`, 초대는 `:feature:friends:list`로 갈려 있다). 소비자가 둘이 되는 순간 승격했다.

## 미해결 이슈

- [ ] 🔵 **iOS 수신 미구현** — APNs 인증키가 **유료 Apple Developer($99/년)에서만 발급**되고 Push capability도 유료 계정 App ID에서만 켜진다. ⚠️ **시뮬레이터로 우회 불가** — 시뮬레이터는 APNs 토큰을 못 받아 FCM 토큰 자체가 나오지 않는다. `soul-oath` iOS 실기 미검증(기기 부재)과 성격이 다르다 — **결제 전에는 경로가 존재하지 않는다.** ADR-0005("iOS+Android 동시 MVP")가 처음 깨지는 지점. iOS actual은 전부 no-op 스텁이고 `iosApp/` 무접촉.
- [ ] 🟡 **`LogoutUseCase`가 서버를 호출하지 않는다** — 서버 T-B2는 구현·검증 완료인데 **아무도 부르지 않는다.** 로그아웃해도 서버 `fcm_token`이 남아 그 기기로 알림이 계속 간다. §0.2가 계정 전환은 덮으므로 **실제 공백은 "로그아웃하고 아무도 로그인하지 않은 기기" 하나.** 🔴 한 줄이 아니다 — `KtorfitModule.kt:103`의 `sendWithoutRequest`가 `/auth/logout`(Bearer 필수)까지 걸어버려 술어를 좁혀야 하고, 그건 인증 플러그인 전역 변경이다. **재개 전 선결: `WWW-Authenticate` 실측**(`UnauthorizedEntryPoint`가 그 헤더를 안 보내 401 후 Ktor 재시도가 도는지 미검증).
- [ ] 🔴 **`AFTER_COMMIT` / `REQUIRES_NEW` 실동작 미검증** — `NotificationDispatcherWiringTest`는 리플렉션으로 **어노테이션 존재·값만** 고정한다. 막는 실패 모드는 *"누가 어노테이션을 지운다"* 하나이고 *"정말 커밋 후에 도는가"*는 증명하지 않는다. 통합 테스트 필요.
- [ ] 🔴 **§0.2 SQL 단위 검증 부재** — 실사용으로는 증명됐으나(위) 자동 테스트는 fake만 태운다. 회귀를 잡으려면 통합 테스트가 필요하다.
- [ ] 🟢 **`onNewToken` 등록이 `scope.cancel()`에 잘릴 수 있다** — `onNewToken` 반환 ≠ 코루틴 완료. 서비스가 `stopSelf` → `onDestroy` → `cancel()`로 네트워크 왕복 중인 등록을 죽일 수 있다. **관측된 적 없고 자가 치유된다**(다음 로그인 시 재등록). 발화 빈도도 낮다. **조치하지 않되 기록** — *"토큰 갱신 후 푸시가 안 온다"* 증상의 첫 용의자.
- [ ] 🟢 **알림 아이콘이 디자인 미확정 placeholder** — `ic_notification.xml` 임시 종 모양. 흰색 실루엣+투명 배경 규칙은 지켰으나 실제 트레이 렌더 미확인.
- [ ] 🟢 **알림 문구 톤 불균일** — `영혼의 맹세`(격식) / `계약 완료.` / `ㅠㅠ`(구어). [challenge-create/design.md §9](../challenge-create/design.md)의 Lovable 화면별 톤 불일치와 같은 축. 사용자 결정이므로 유지하되 전역 톤 통일 시 함께 다룬다.
- [ ] 🟢 **알림 목록 화면 미구현** — `notifications` row는 이번에 쌓기 시작했으나 조회 API·화면·홈 벨 아이콘이 없다. Lovable `notifications.tsx`는 존재.
- [ ] 🟢 **딥링크 미구현** — 알림 탭 → 홈까지만. `data.challengeId`는 이미 실려 있어 후속에서 라우팅만 붙이면 서버 변경 0.
- [ ] 🟢 **iOS 단위 테스트 미실행** — `iosSimulatorArm64Test`. friends·user-info·challenge-create에 이은 누적 항목.

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md) (`confirmed`) · [change-log.md](./change-log.md)
- 기획서 개정: [notion-planning-snapshot-2026-08-06.md](../../product/notion-planning-snapshot-2026-08-06.md)
- ⚠️ **`mobile-report.md` / `backend-report.md`는 작성되지 않았다** — 각 트랙이 파일이 아니라 메시지로 보고했고, 그 실질 내용은 spec.md의 태스크별 완료 기록과 본 문서에 흡수돼 있다.
