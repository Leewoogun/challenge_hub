# API Contract — 마이페이지 (mypage)

- **feature-id**: mypage
- **상태**: `confirmed` — design(design.md §7) · mobile 회신 반영 완료
- **소유**: backend-dev (mypage-backend)
- **작성**: 2026-08-26 pm-lead (초안) → 2026-08-26 backend 구체화
- **상위 spec**: [spec.md](./spec.md)

## 요약 — 신규 2건 + 기존 1건 연동

| # | Method | Path | 인증 | 설명 | 상태 |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/challenges/history` | Bearer | 계약서 보관함 — 종료 챌린지 목록 | ✅ 확정 |
| 2 | DELETE | `/api/v1/users/me` | Bearer | 회원탈퇴 — 익명화+기록 보존+사진 삭제 | ✅ 확정 |
| 3 | DELETE | `/api/v1/auth/logout` | Bearer | 로그아웃 — 서버 구현·검증 완료, 앱 연동만 | ✅ 확정(기존) |

프로필 카드는 기존 `GET /record` + `GET /users/me` 재사용 — **계약 변경 0.**

시간 포맷은 프로젝트 규약 그대로 `yyyy-MM-dd HH:mm:ss`(날짜 전용 `yyyy-MM-dd`), 전부 KST
([ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)). `T`·`Z`·offset·밀리초 없음.

---

## 1. 보관함 목록 — `GET /api/v1/challenges/history` ✅ 확정

### 확정 근거 (backend 실측 + design.md §7 회신)

- **정렬·월 그룹 키는 `challengeDate`** — `completed_at` 이 아니다.
  판정이 **자정 직후 배치**라, 7월 31일 챌린지의 `completed_at` 은 8월 1일 00:05 다.
  `completed_at` 으로 묶으면 **7월 마지막 날 챌린지가 8월 그룹에 들어간다.**
  홈 피드가 `completed_at DESC` 를 쓰는 건 *"판정이 방금 났다"* 를 보여주는 다른 목적이다.
- **페이지네이션 없음 (전체 반환).** 이 프로젝트의 목록 엔드포인트 5종
  (`/friends`, `/friends/requests/received`, `/challenges/received`, `/challenges/active`,
  `/rankings/losers`) 중 페이지 파라미터를 가진 것이 **0건**이다. PM 규약이
  *"페이지네이션은 프로젝트 전체에서 한 방식으로 통일"* 이므로, 보관함 하나 때문에 첫
  페이지네이션을 도입하면 **그 규약이 금지하는 상태를 만드는 셈**이다. 필요해지는 시점에
  전 엔드포인트를 한 번에 결정한다. → 백로그 항목으로 등재.
- **대상 상태는 `COMPLETED` 만. `EXPIRED` 제외.** `EXPIRED` 는 *"신청했는데 상대가 수락하지
  않아 성립조차 못 한 건"* 이라 계약서·서명·사진·결과가 **전부 없다.** 보관함이 기획
  §3.3(*"이때 너 이거 걸었잖아"* — 증거 보관)의 이행이라면 **증거가 0인 카드**다.
  (`ChallengeRepository.findRecentlyCompletedByUser` 도 같은 이유로 `EXPIRED` 를 제외한다.)
- **`myResult` 는 서버가 뒤집어 준다.** 홈 목록과 동일하게 `ChallengeVerdict.outcomeFor` 를
  거친다 — 앱은 *"내가 challenger 인가"* 를 알 필요가 없다. `BOTH_LOSE` 는 `LOSE` 로 접지 않고
  그대로 내려간다.

### ✅ 조회 단위 — **전체 목록 + 클라이언트 월 그룹핑. 월 파라미터 없음**

design.md §2.1 / §7-① 확정. backend 제안과 일치했다. 근거:

- **월 이동 UI 는 빈 월을 계속 만나게 하는 UI다.** 종료된 것만 담기므로 월당 건수가 한 자릿수고
  **대부분의 월이 0건**이다. 사용자가 *"이때 너 이거 걸었잖아"* 로 찾으려면 몇 월이었는지 먼저
  기억해야 하는데, 못 하면 화살표를 누르며 빈 화면을 넘긴다 — **화면의 목적을 UI 가 방해한다.**
- 🔴 **월 파라미터는 첫 진입이 빈 화면이 될 수 있다.** 최신순 전체 목록은 **첫 화면 최상단이
  가장 최근 종료 건**이라 spec 수용 기준(*"보관함으로 홈 7일 노출이 지난 결과에도 도달할 수
  있다"*)이 **아무 조작 없이** 충족된다. 월 파라미터에서는 "이번 달에 종료 건이 있을 때만"
  성립한다. (design 이 짚은 각도 — backend 가 못 본 근거다.)
- 이 화면에서 '월' 은 **탐색 축이 아니라 그룹핑 라벨**이다. 월이 1급 탐색 축인 UI 가 캘린더인데
  그건 이번 범위에서 빠져 통계 feature 로 이월됐다(design §1.3). 같은 판단이 여기도 걸린다.
- 앱의 상태 분기가 하나도 안 는다 (선택된 월·이동 가능 범위·화살표 비활성이 전부 사라진다).

### 응답 shape ✅ 확정

```json
{
  "error": false, "code": 200, "message": "",
  "data": {
    "histories": [
      {
        "challengeId": 42,
        "challengeDate": "2026-08-14",
        "opponentNickname": "준혁",
        "myMission": "헬스장 가기",
        "opponentMission": "금주",
        "bet": "치킨 한 마리",
        "myResult": "WIN"
      }
    ]
  }
}
```

🔴 **필드 7개가 전부이고 전부 non-null 이다.** design §7-④ 확정. 넣지 않은 것 둘:

- **역할 기준 `result` 원본을 넣지 않는다.** `/challenges/active` 는 `result` + `myResult` 를
  둘 다 주지만 여기는 `myResult` 뿐이다. 카드는 *"내가 이겼나"* 만 그리는데 **둘 다 내려가면
  앱이 어느 쪽을 믿을지 고르게 되고, 그 선택이 화면마다 갈린다.** `Outcome` 에 `BOTH_LOSE` 가
  이미 있어 "양쪽 다 졌다" 도 `myResult` 만으로 표현된다.
- **인증 상태 2필드를 넣지 않는다.** 판정 규칙상 4개 결과가 양측 인증 상태를 **유일하게
  결정**한다(승=나만 인증 / 패=상대만 / 무=양쪽 / 양패=양쪽 미인증). 즉 결과 하나가 인증
  상태 두 개의 정보를 전부 담고 있어 **정보량이 0**이다. 서버 쿼리도 그만큼 줄어
  이 엔드포인트는 **쿼리 2개**로 끝난다(홈 목록은 4개).

- `myResult` = 내 시점(`WIN`/`LOSE`/`DRAW`/`BOTH_LOSE`). 서버가 뒤집어 준다 — 앱은
  *"내가 challenger 인가"* 를 알 필요가 없다.
- `histories` 는 **빌 수 있다** (`[]`). 빈 상태 화면 필요.
- 월 그룹핑은 **앱이** `challengeDate` 앞 7글자로 한다. 서버가 그룹을 나눠 주면 응답 shape 에
  화면 구조가 박힌다.
- 카드 탭 → 기존 `GET /challenges/{id}` 로 상세 진입. 기한 없이 열린다 — **신규 API 불필요.**

---

## 2. 회원탈퇴 — `DELETE /api/v1/users/me` ✅ 확정

### 요청

```
DELETE /api/v1/users/me
Authorization: Bearer {accessToken}
```
body 없음.

### 응답 — 성공

```json
{ "error": false, "code": 200, "message": "" }
```

🔴 **`data` 키가 없다.** `DELETE /auth/logout`·`PUT /users/me/fcm-token` 과 같은 shape 이며
`WireShapeContractTest` 가 고정한다. non-nullable 로 선언하면 `MissingFieldException`.

### 응답 — 실패

| code | HTTP | 언제 | 앱 처리 |
|---|---|---|---|
| 701 | 200 | 카카오 연결 해제(unlink) 실패 | 다이얼로그. *"일시적인 문제로 탈퇴하지 못했어요. 잠시 후 다시 시도해주세요"* — **재시도 가능** |
| 401 | 401 | 토큰 없음/만료 | 기존 흐름 그대로 |

🔴 **탈퇴는 로그아웃과 달리 "언제나 성공" 이 아니다.** 로그아웃은 실패해도 클라이언트를
로그인 상태에 가두면 안 되므로 멱등 성공이지만, 탈퇴는 **카카오 연결 해제가 이행되지
않았는데 성공이라고 답하면 안 된다.**

### 멱등성

이미 탈퇴한 계정으로 다시 호출하면 **아무 것도 하지 않고 200**. (아래 토큰 항목 때문에
실제로 발생 가능한 경로다.)

### 서버가 하는 일 — 실행 순서

```
1. 카카오 unlink            ← 🔴 DB 보다 먼저
2. [한 트랜잭션] 사진 key 수집 → verifications.photo_url NULL
                            → friendships 물리 삭제 → users 익명화
3. [커밋 후] 인증 사진 파일 삭제
```

**왜 unlink 가 먼저인가**: DB 를 먼저 하고 unlink 가 실패하면 계정은 이미 되돌릴 수 없게
익명화됐는데 카카오 연결은 살아 있고, `kakao_id` 를 지워서 **재시도할 대상조차 잃는다**.
반대 순서면 카카오 연결만 끊기고 row 는 ACTIVE 로 남아, 재로그인 시 같은 row 로 돌아와
**다시 탈퇴를 누르면 된다.** 복구 가능한 쪽을 택했다.

### 익명화 범위 (spec 정책표 이행)

| 컬럼 | 값 |
|---|---|
| `kakao_id` | NULL |
| `nickname` | **"탈퇴한 사용자"** |
| `profile_image_url` / `phone_number` / `fcm_token` / `refresh_token_hash` | NULL |
| `phone_verified` | false |
| `status` | `DELETED` |

보존: `challenges`(`PENDING` 제외 — 아래), `contracts`, `verifications` **row**, `user_stats`,
`friend_records`, `taunt_messages`.
삭제: `friendships` 전부 · **`notifications`(수신함) 전부** · 탈퇴자가 **보낸 `PENDING` 챌린지** ·
인증 사진 **파일** + `verifications.photo_url`(=key).

### 🔴 탈퇴자가 상대 화면에 어떻게 보이는가 — 타 응답 계약 변경 **0**

`nickname` 이 **non-null 을 유지**하므로 기존 응답이 하나도 깨지지 않는다. 실측 확인:

| 응답 | 탈퇴자 표현 | 계약 변경 |
|---|---|---|
| `GET /challenges/active` | `opponentNickname = "탈퇴한 사용자"` | 없음 |
| `GET /challenges/{id}` | `challenger/opponent.nickname = "탈퇴한 사용자"` | 없음 |
| `GET /challenges/history` | `opponentNickname = "탈퇴한 사용자"` | 없음 |
| `GET /rankings/losers` | **목록에서 사라짐** — 랭킹은 `friendships` JOIN 이고 그게 삭제된다 | 없음 |
| `GET /friends` | **목록에서 사라짐** — 같은 이유 | 없음 |

### 🔴 신규 계약 사실 — `GET /challenges/{id}/verifications` 에 필드 1개 추가

탈퇴자 쪽은 **`status = "VERIFIED"` 인데 `photoUrl = null`** 인 조합이 나온다.
row 는 보존하되(그 사람이 그날 인증했다는 사실은 상대의 기록이다) 사진 파일과 key 만 지우기
때문이다. 지금까지 서버가 만들지 않던 조합이다.

**`photoUrl == null` 만으로는 부족하다** — 그 자리는 앱에서 이미 *"인증은 됐는데 URL 이 없는
비정상"* 이라는 **다른 뜻**으로 쓰이고 있다(`VerificationPhoto.kt` 실측:
`photoUrl == null -> PhotoMessage(LOAD_FAILED_TEXT)`). 삭제된 사진이 그 문구를 빌려 쓰면
(1) 영구 상태를 *"불러오지 못했어요"* 라는 일시적 실패의 어휘로 말하고,
(2) 🔴 **진짜 데이터 이상이 탈퇴자 뒤에 숨는다.**

→ **`photoDeleted: Boolean` 을 party 객체에 추가한다** (additive, non-null, 기본 false).
design §7-⑤ 요구이며 backend 가 실측 정정 후 채택했다.

```json
"challenger": {
  "userId": 7, "status": "VERIFIED", "photoUrl": null,
  "photoDeleted": true,
  "verifiedAt": "2026-08-12 21:30:00"
}
```

서버 판정: `status == VERIFIED && photoUrl == null && 그 사람이 탈퇴 상태`.

| status | photoUrl | photoDeleted | 앱 표시 |
|---|---|---|---|
| VERIFIED | non-null | false | 사진 |
| VERIFIED | null | **true** | **"탈퇴한 사용자의 사진은 삭제됐어요"** — 재시도 버튼 없음 |
| VERIFIED | null | false | 기존 그대로 (진짜 데이터 이상) |
| PENDING / FAILED | null | false | 기존 그대로 |

🔴 **`isWithdrawn` 이 아니라 `photoDeleted` 인 것이 의도다.** 앱이 *"왜"* 가 아니라
*"뭘 그릴지"* 만 받게 한다 — design 이 보관함 카드에서 `isWithdrawn` 을 **명시적으로 거부**한
이유(받으면 특별 표시를 넣게 되고, 증거 보존 화면에서 그건 *"이 기록은 무효"* 로 읽힌다)가
여기도 그대로 걸린다. `photoDeleted` 는 사진 자리 하나만 바꾸고 다른 데 쓸 수 없다.

⚠️ **challenge-verification 의 confirmed 계약 변경(additive)** — 그쪽 `change-log.md` 등재 대상.

사진 직접 요청 `GET /challenges/{id}/photos/{party}` 는 **HTTP 404** 다.
기존 404(아직 인증 안 함 / 챌린지 없음)와 **구분되지 않는다** — 구분할 필요가 없다는 것이
결정이다. 앱은 위 `photoDeleted` 로 이미 알 수 있으므로 사진 요청 자체를 하지 않는 것이
정상 경로이고, 404 는 그 뒤의 안전망이다.

### 🔴 `GET /users/me` — shape 은 그대로, **동작이 바뀐다**

**탈퇴한 계정이 부르면 401 이다.**

탈퇴 시 `kakao_id` 를 NULL 로 만드는데 `UserInfoData.kakaoId` 는 non-null 계약이다.
nullable 로 바꾸면 모바일 wire 계약이 깨지고(kotlinx.serialization 이 터진다), `0L` 로 채우면
거짓말이므로 **탈퇴자를 401 로 답한다.**

이건 새 규칙이 아니라 **원래 문서화돼 있던 동작의 유지**다 — `UserService.getMe` 의 KDoc 이
원래 *"토큰의 userId 가 DB 에 없으면(회원탈퇴/삭제) 401"* 이었다. **탈퇴가 row 를 지운다는
전제**였고 이번에 그 전제가 바뀌었으므로(row 를 남긴다) status 검사를 더해야 같은 답이 나온다.

부수 효과로 아래 "access token 1시간 잔존" 구멍이 **이 엔드포인트 하나에서는 닫힌다.**

### 토큰 처리 — ⚠️ 정직하게 적는다

- **`refresh_token_hash` 는 즉시 NULL** → 재발급 불가. `POST /auth/refresh` 는 401.
- ⚠️ **access token 은 남은 유효기간(최대 1시간, `jwt.access-token-expiration-ms=3600000`)
  동안 형식상 유효하다.** `JwtAuthenticationFilter` 가 요청마다 계정 상태를 다시 조회하지
  않기 때문이다 (그렇게 하려면 **모든 인증 요청에 DB 조회가 1회씩 붙는다** — 전역 성능·회귀
  비용이 커서 이번 범위에 넣지 않았다).
  - 예외: **`GET /users/me` 는 401 이다** (위 항목). `DELETE /users/me`(탈퇴 재호출)는
    멱등 200 이다. 그 외 엔드포인트는 열려 있다.
- 따라서 **앱은 탈퇴 성공 즉시 로컬 토큰·캐시를 삭제하고 로그인 화면으로 보낸다.**
  실사용 경로에서 그 1시간이 노출되지 않는 것은 **앱의 이 동작이 보장**한다.
- 백로그 등재 대상 (§5 참조).

### 진행 중 챌린지 — **막지 않는다. 자연 판정.** ✅ 확정

탈퇴자는 로그인이 불가능하므로 인증을 올릴 수 없고, 자정 배치가 **기존 판정 규칙 그대로**
처리한다(상대만 인증 → 상대 승 / 양쪽 미인증 → 양패). 탈퇴 시점에 즉시 포기 처리하면
**판정 규칙의 사본이 하나 더 생긴다** — 그게 나중에 본 규칙과 갈린다.

### ✅ `PENDING` 챌린지 — **보낸 것은 삭제, 받은 것은 방치** (pm-lead 확정)

탈퇴자가 **보낸 채 아직 수락되지 않은** 도전장이 남으면, 상대가 그걸 수락해 **탈퇴자와의
챌린지를 새로 시작**할 수 있다. 시작하자마자 탈퇴자는 인증 불가라 **결과가 이미 정해진**
챌린지다.

- 탈퇴자가 **challenger** 인 `PENDING` → **물리 삭제.** `PENDING` 에는 계약서·서명·사진·결과가
  하나도 없어 **보존할 증거가 0** 이고, 처리가 **챌린저가 직접 취소한 것과 정확히 같다**
  (`ChallengeRepository.deleteById` 가 이미 그 용도다).
- 탈퇴자가 **opponent** 인 `PENDING` → **그대로 둔다.** 수락될 수 없으므로 자연 만료된다.

🔴 **`IN_PROGRESS` / `COMPLETED` 는 삭제 대상이 아니다.** 그건 증거가 있는 챌린지이고
"자연 판정" 정책이 적용된다.

⚠️ **모바일에 걸리는 지점**: 상대에게 이미 발송된 `CHALLENGE_REQUEST` 알림 row 는 **상대
것이라 보존**되는데 그 챌린지는 사라진다. 즉 **상대가 그 알림을 탭하면 없는 챌린지로
딥링크한다.** 서버는 `GET /challenges/{id}` 에 **code=705 `"챌린지를 찾을 수 없어요"`** 로
답한다 — 이미 설계된 정상 경로라 서버가 새로 할 일은 없다. push-deeplink 쪽에서 그 코드를
무난히 그리는지만 확인 대상.

### ✅ `notifications` — **삭제** (pm-lead 확정)

수신함은 **본인 전용 개인 데이터**라 *"양자 기록 보존"* 원칙의 대상이 아니고 **개인정보 삭제
축**에 속한다. 아무도 읽을 수 없는 채로 *"누가 나에게 무엇을 했는지"* 를 담은 row 를 남길
이유가 없다.

(backend 는 *"남기는 쪽이 되돌릴 수 있다"* 를 근거로 보류를 제안했으나, pm-lead 판정은
**가역성 문제가 아니라 분류 문제**라는 것이었고 그쪽이 맞다.)

🔴 **상대의 `notifications` 는 건드리지 않는다** — 탈퇴자가 보낸 알림이라도 그건 **받은
사람의 데이터**다.

### ⚠️ 운영 전제 — `KAKAO_ADMIN_KEY`

카카오 unlink 는 **서비스 앱 어드민 키** 방식이다
(`POST https://kapi.kakao.com/v1/user/unlink`, `Authorization: KakaoAK {키}`,
body `target_id_type=user_id&target_id={kakaoId}` — 공식 문서 확인 완료).

사용자 access token 방식을 쓰지 않은 이유: **서버는 카카오 access token 을 저장하지 않는다**
(로그인 때 `/v2/user/me` 한 번 쓰고 버린다). 토큰 방식이면 앱이 탈퇴 시점에 카카오 토큰을
새로 받아 보내야 하고, 기기의 카카오 세션이 만료돼 있으면 **탈퇴 자체가 불가능**해진다.
admin key 는 `users.kakao_id` 만으로 동작한다.

🔴 **`KAKAO_ADMIN_KEY` 가 미설정이면 unlink 를 건너뛰고 DB 익명화만 수행한다**(WARN 로그
2회 — 기동 시 + 호출 시). 로컬 개발에서 탈퇴 플로우를 테스트할 수 있게 하기 위한 것이며
(`NotificationSenderConfig` 의 FCM 키 선례와 같은 판단), **운영 배포 전 필수 설정 항목이다.**
사용자가 카카오 콘솔에서 발급해야 한다 — 서버가 만들 수 없는 값이다.

---

## 3. 로그아웃 — `DELETE /api/v1/auth/logout` ✅ 확정 (기존)

서버 구현·검증 완료. 앱 연동만 남았다.

- **Bearer 필수.** `SecurityConfig` 의 `permitAll` 목록에 없고 `.anyRequest().authenticated()`
  에 걸린다. → `sendWithoutRequest` 술어를 줄일 때 **`/auth/kakao`·`/auth/refresh` 는 공개,
  `/auth/logout` 만 인증 필수**로 갈라야 한다.
- 응답: `BaseResponse` 3필드. **`data` 없음.**
- 서버 동작: `refresh_token_hash = NULL` + `fcm_token = NULL` 을 한 트랜잭션에.
  둘을 묶는 것이 설계 의도다 — 하나만 끊으면 *"로그아웃했는데 알림은 계속 온다"* 또는
  *"알림은 끊겼는데 세션은 살아 있다"* 가 남는다.
- **멱등.** 이미 로그아웃된 상태도, 해당 row 가 없어도 200. 재시도를 자유롭게 넣어도 된다.
- 호출 순서: `clearTokens` **앞**에 서버 호출.

### 🔴 `WWW-Authenticate` 실측 결과 (2026-08-26, 로컬 :8080) — **헤더 없음**

```
GET    /api/v1/challenges/active   -> HTTP 401 | WWW-Authenticate: (absent)
DELETE /api/v1/auth/logout         -> HTTP 401 | WWW-Authenticate: (absent)
GET    /api/v1/users/me            -> HTTP 401 | WWW-Authenticate: (absent)
```

토큰 미첨부와 쓰레기 토큰(`Bearer not.a.jwt`)의 응답이 **바이트 단위로 동일**하다.
401 body 는 `{"error":true,"code":401,"message":"토큰이 만료되었거나 유효하지 않습니다"}`.

코드 근거: `UnauthorizedEntryPoint` 가 status + JSON body 만 쓰고, `SecurityConfig` 가
`httpBasic` 을 disable 해서 Spring Security 쪽에도 그 헤더를 붙일 진입점이 없다.
**우연이 아니라 구조적으로 없다.**

#### ✅ 판정 — **헤더를 추가하지 않는다. 서버 변경 0건**

mobile 이 Ktor `MockEngine` 으로 프로덕션 인증 설정을 그대로 태운 특성화 테스트 9건
(Android/iOS 각각 9 tests / 0 failures)으로 답을 냈다. 결정적인 것:

> `401 에 WWW-Authenticate 헤더가 없어도 갱신이 시도된다` → **pass**

즉 지금 서버가 보내는 그 응답(헤더 없음)에도 `/auth/refresh` 가 나가고 토큰이 갱신된다.
코드 근거도 일치한다 — `ktor-client-auth 3.3.1` 의 `Auth.kt` `findProvider` 에
`authHeaders.isEmpty() && candidateProviders.size == 1 -> candidateProviders.first() to null`
분기가 있고, 이 앱은 프로바이더가 `bearer` **하나뿐**이라 이 분기를 탄다.

🔴 **다만 그 전제를 계약으로 기억해 둔다: 앱의 인증 프로바이더가 1개인 동안만 성립한다.**
프로바이더가 하나 더 붙으면 이 분기가 깨지고 그때는 서버가 헤더를 보내야 한다.
mobile 이 위 테스트 2건을 그 순간 빨갛게 터지도록 박제해 뒀다.

⚠️ RFC 9110 §15.5.2 는 401 에 `WWW-Authenticate` 를 MUST 로 요구하므로 **현재 서버는 규격
위반 상태로 남는다.** 지금 고치면 얻는 것 없이 모든 401 이 바뀌므로 백로그로 넘긴다.

#### ⚠️ 만료된 access token 으로 `/auth/logout` 을 부르면 — **401, 그리고 루프는 없다**

토큰 미첨부 · 쓰레기 토큰 · 만료 토큰의 응답이 **바이트 단위로 동일**하다(위 401 전문).
컨트롤러에 **도달조차 하지 않는다.**

루프가 안 생기는 이유: `/auth/refresh` 의 401 은 **결정적이고 영구적**이다 —
`refresh_token_hash` 가 NULL 이거나 불일치면 몇 번을 불러도 같은 401 이고, **서버가 나중에
성공시킬 여지가 0** 이라 "재시도하면 될지도" 가 성립하지 않는다.

🔴 **그리고 세션 만료 경로에서는 서버 logout 호출이 실패해도 안전하다.** logout 이 끊는 서버
상태는 `refresh_token_hash` 와 `fcm_token` 둘인데,
- 세션 만료 = `refresh_token_hash` 는 **이미 무효** — 첫 목적은 달성돼 있다.
- 남는 `fcm_token` 은 그대로여도 **그 계정 본인에게 가던 푸시가 계속 갈 뿐**이고, 재로그인하면
  같은 토큰이 재등록된다. **그 기기에서 다른 계정으로 로그인하는 경우**만 위험한데 그건
  `clearFcmTokenOwnedByOthers` 가 **등록 시점에** 막는다 (push-fcm 계약 §0.2 가 정확히
  *"logout 이 아예 호출되지 않는 경로"* 를 위해 만든 장치다).

→ 앱은 세션 만료 경로에서 서버 호출을 **건너뛰거나 실패를 삼켜도 된다.**

---

## 4. 인증 요약

| Path | 인증 |
|---|---|
| `GET /api/v1/challenges/history` | Bearer 필수 |
| `DELETE /api/v1/users/me` | Bearer 필수 |
| `DELETE /api/v1/auth/logout` | Bearer 필수 |

공개 엔드포인트 추가 **0건**.

## 5. 백로그로 넘기는 것

- **탈퇴 후 access token 1시간 잔존** — 요청마다 계정 상태를 확인하려면 전역 DB 조회가
  붙는다. 별도 결정 사안.
- **페이지네이션 부재** — 보관함이 프로젝트에서 처음으로 "무한히 자라는 목록" 이 된다.
  전 엔드포인트 일괄 도입 시점을 정해야 한다.
- **`KAKAO_ADMIN_KEY` 운영 설정** — 배포 체크리스트.
- **`PhotoStorage.delete()` 호출부 0건 해소** — 이 feature 가 첫 호출부다. 백로그 항목 갱신.

## 협의 이력

| 일시 | 작성자 | 변경 |
|---|---|---|
| 2026-08-26 | pm-lead | 초안 — 신규 2 + 기존 1, 쟁점 골격 |
| 2026-08-26 | backend-dev | §2 탈퇴 전면 구체화(경로·shape·실행 순서·익명화 범위·타 응답 영향 실측·토큰 잔존 명시·오픈이슈 2건). §3 로그아웃 확정 + `WWW-Authenticate` 실측 등재(헤더 없음). §1 은 `challengeDate` 기준·페이지네이션 없음·`EXPIRED` 제외를 확정하고 조회 단위만 design 대기. 상태 `draft` → `negotiating` |
| 2026-08-26 | backend-dev | design.md §7 회신 반영 → **`confirmed`**. ① 조회 단위 = 전체+클라 월 그룹핑 확정 ④ 카드 필드 7개로 축소 — **역할 기준 `result` 제거**(둘 다 주면 앱이 어느 쪽을 믿을지 고르게 되고 화면마다 갈린다), 인증 상태 2필드 제외 ⑤ **`photoDeleted: Boolean` 신규**(design 요구를 backend 실측 정정 후 채택 — "재시도 버튼 영구 노출"은 발생하지 않으나 *진짜 데이터 이상이 탈퇴자 뒤에 숨는* 문제가 남아 채택). ⑥⑦⑧ 원안 유지. 구현 중 발생한 `GET /users/me` 동작 변화(탈퇴자 401) 등재 |
