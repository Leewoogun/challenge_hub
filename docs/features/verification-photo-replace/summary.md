# 인증 사진 교체 허용 (verification-photo-replace) — Summary

- **feature-id**: verification-photo-replace
- **완료일**: 2026-09-02
- **상태**: **implemented** — 전 범위 구현·검증 완료. 🔴 **양 레포 미커밋** + **T-I1 실기 미실시**
- **선행**: [challenge-verification](../challenge-verification/summary.md) — 이 feature 가 그 계약의 재제출 정책을 반전시켰다
- **후행**: [ai-verification](../ai-verification/spec.md) — 이 feature 가 그 전제다

## 구현 개요

인증 사진을 **마감 전까지 몇 번이든 다시 찍어 교체**할 수 있게 했다. 마지막에 올린 것이 최종본이고,
판정 배치와 상대가 보는 것도 그것이다. 이전에는 한 번 제출하면 `code=700` 으로 전면 거부됐다.

**마이그레이션 0건, 새 엔드포인트 0건, 요청/응답 shape 변경 0건.** 바뀐 것은 **같은 요청에 대한
서버의 행동**(거부 → 교체)과 그에 딸린 앱 절차·캐시 처리다.

🔑 **이 feature 의 실제 난점은 재제출 허용이 아니라 캐시였다.** 사진 경로는 교체돼도 그대로라
(`/api/v1/challenges/{id}/photos/{party}`) 서버·앱 양쪽이 옛 사진을 캐시하고 있었다. 그대로 뒀으면
**다시 찍어도 화면이 안 바뀌는데 에러도 로그도 남지 않는** 상태로 배포됐고, 테스트는 전부 초록이었다.
두 팀원이 각자의 계층에서 독립적으로 발견했다 — §"부수 발견" 참조.

## 엔드포인트

**신규 0건.** 기존 2건의 **행동**이 바뀌었다.

| Method | Path | 변경 | 상태 |
|---|---|---|---|
| POST | `/api/v1/challenges/{id}/verifications` | 재제출 **전면 거부 → `last-write-wins`**. 이전 파일 삭제 + `verified_at` 갱신 + 알림은 최초 1회 | implemented |
| GET | `/api/v1/challenges/{id}/photos/{party}` | `Cache-Control: max-age=86400` → **`no-cache` + ETag/304** | implemented |

## 화면 / UI 변경

- **챌린지 상세** — `VERIFIED` 상태에서도 **"다시 찍기"** 노출. 게이트를 새로 만들지 않고 `canVerify` 의
  근거를 `IN_PROGRESS && myStatus != VERIFIED` → **`IN_PROGRESS` 만**으로 바꿨다.
  덕분에 **마감 후 교체 불가가 저절로 지켜진다**(`IN_PROGRESS` 아니면 사진만 표시)
- **인증 완료 화면** — 최초/교체를 구분. 🟡 초안: 교체 시 `사진이 교체됐어요. 상대는 최신 사진을 보게 돼요`
- **사진 표시** — Coil 캐시 키를 `photoUrl + verifiedAt` 으로 지정

## 주요 변경 파일

**백엔드** (마이그레이션 없음)
- `service/.../verification/VerificationService.kt` — `submit()` last-write-wins, KDoc 전면 교체, `MSG_ALREADY_VERIFIED` 삭제
- `controller/.../challenge/VerificationController.kt` — 캐시 헤더 + ETag/`If-None-Match` → 304

**모바일** (16 파일 / +456 −249)
- `feature/challenge/detail/.../component/VerificationPhoto.kt` — `model = url` → `ImageRequest` + `memoryCacheKey`/`diskCacheKey`
- `feature/challenge/detail/.../contract/ChallengeDetailState.kt` — `myVerifiedAt`/`opponentVerifiedAt`
- `feature/challenge/detail/.../component/MissionCard.kt` — `MY_PHOTO_WITH_RETAKE` 슬롯
- `feature/challenge/verify/.../VerifyViewModel.kt` — 재시도 전 status 선행 조회 제거

## 테스트 결과

**백엔드**: 전체 **574/574 passed** (0 failed, 50 skipped = Docker 부재 기존 블로커)
- `VerificationServiceTest` 48/48 · `VerificationControllerTest` 17/17 · 신규 21건 / 삭제 2건
- 🔴 **throwaway DB 실기동 확인** (`Started ChallengeServerApplicationKt`) — 새 `@Service` 빈 배선은 테스트로 못 잡는다

**모바일**: pm-lead 가 XML 에서 직접 집계 (2026-09-02 01:12~01:22)

| 모듈 | Android | iOS |
|---|---|---|
| `feature:challenge:detail` | 52 / 0 | 52 / 0 |
| `feature:challenge:verify` | 21 / 0 | 21 / 0 |
| `remote:datasource` | 39 / 0 | ⚠️ **미컴파일** (아래) |
| **합계** | **112 / 0** | **73 / 0** |

- `detail` 46→52(캐시 키 테스트 6건 신규), `verify` 21(회복 절차 5건 삭제 + 신규 1건),
  `remote:datasource` 39(`Challenge` 23 · `Login` 8 · `Verification` 8)
- `:composeApp:linkDebugFrameworkIosSimulatorArm64` 를 포함해 **`Route.Challenge.Verify` 필드 추가 배선이
  실제로 컴파일되는지**까지 확인

> 🔵 **`detail` XML 이 `01:12`, 나머지가 `01:22` 인 것은 stale 이 아니다.** 마지막 실행은 `verify` 와
> `remote:datasource` 만 건드려 Gradle 이 `detail` 을 `UP-TO-DATE` 로 건너뛰었다 — 즉 **입력이 한 글자도
> 안 바뀐 동일 코드에 대한 결과**다.
>
> 🔴 **여기서 검증 규칙이 하나 다듬어졌다: iOS XML 의 stale 여부는 timestamp 만으로 판정하면 안 되고
> `UP-TO-DATE` 여부까지 봐야 한다.** 과거 사고(challenge-verification T7a·T7b)는 *입력이 바뀌었는데도*
> 옛 XML 을 읽은 경우였다. timestamp 단독을 규칙으로 삼으면 **정상적인 증분 빌드를 매번 stale 로
> 오탐**하게 된다. (pm-lead 가 준 지침을 mobile-dev 가 정정한 것)

## 결정 사항

**1. 재제출 정책 반전의 근거 — 뒤집기가 아니라 전제 소멸**

원래 거부 사유는 *"판별 수단이 없다"* 가 아니라 **"올린 사진이 조용히 버려지고 앱은 성공이라고
답한다"** 였다(`submit()` KDoc). `last-write-wins` 는 올린 사진을 **저장하므로** 그 실패 모드가
발생하지 않는다. 같은 이유로 앱의 *"재시도 전 status 선행 조회"* 회복 절차도 존재 이유를 잃었다.

**2. 캐시 무효화는 앱 캐시 키로. ETag 는 앱이 타지 않는다**

계약 §5 가 스스로 *"Coil 처럼 URL 을 키로 캐시를 두는 로더는 HTTP 캐시 의미를 무시할 수 있다"* 고
적었다. ETag/304 경로는 **바로 그 무시할 수 있다는 동작이 실제로는 잘 된다는 데 거는 베팅**이라,
HTTP 캐시 의미를 하나도 쓰지 않는 **클라이언트 캐시 키**를 택했다. 결정 근거는 성능이 아니라
**의존 대상의 신뢰도**다.

🔵 서버 ETag 는 낭비가 아니다 — **다른 계층**이다. `max-age=86400` 제거가 본체이고(서버가 *"하루
캐시해도 된다"* 고 계속 말하는 건 그 자체로 틀린 진술이다), ETag 는 그 제거의 비용(재진입마다 전량
재다운로드)을 304+0바이트로 되돌린다. 브라우저·프록시·향후 클라이언트에 유효하다.

**3. `?v=<etag>` 미채택** — 제안됐다가 자진 철회. §4 응답의 `verifiedAt` 이 교체마다 갱신되므로
**신호가 처음부터 있었다.** URL 을 안 바꾸므로 계약 §4 `photoUrl` 모양도 서버 작업도 없다.

**4. 초 단위 한계는 인지하고 받는다** — `verifiedAt` 이 초 단위(ADR-0010)라 같은 초에 두 번 교체하면
캐시 키가 겹친다. 촬영→확인→제출→업로드 왕복이 1초에 두 번 일어날 수 없어 도달 불가로 본다.
🔴 **방어 로직을 넣지 않았다** — 관측된 버그가 아니라 가정이다. 필요해지면 §4 에 ETag 를 실으면
되고(ETag 는 저장소 key 기반이라 이 한계가 없다) 계약 변경도 불필요하다.

**5. 삭제는 커밋 후에** — `PhotoStorage.delete` KDoc: *"트랜잭션이 아니다. 롤백돼도 지워진 파일은
돌아오지 않는다."* 삭제 실패는 고아 파일을 남길 뿐 제출을 실패시키지 않는다.

## 부수 발견

**① 캐시 문제를 두 팀원이 각자의 계층에서 독립 발견**
backend-dev 는 *"`max-age` 의 근거가 계약에 **재제출 거부로 불변**이라 적혀 있는데 이 feature 가 그
전제를 없앤다"* 로, mobile-dev 는 *"Coil `ImageLoader` 가 기본값이라 URL 키 캐시가 켜져 있다"* 로.
**범위 밖 수정이었으나 승인했다** — 스코프 이탈이 아니라 우리가 깨뜨린 것의 복구다.

**② T-M4 를 조용히 되돌릴 문장 1건 삭제**
`api-contract.md` 에 *"`challengeId+userId+verifiedAt` 로 우회할 필요도 없다"* 가 남아 있었다.
서명 URL 시절 *"사진은 불변"* 전제의 문장인데, **하필 "필요 없다"고 지목한 조합이 T-M4 가 쓰는
기법**이다. 남았으면 다음 사람이 캐시 키에서 `verifiedAt` 을 뺐을 것이다. (적발: `verif-mobile-entry`)

**③ 🔴 `:remote:datasource` 의 iOS 테스트가 한 번도 컴파일된 적이 없다**
Kotlin/Native 가 백틱 테스트 이름의 `,` `(` `)` 를 금지하는데 그 모듈이 위반한다(15건).
증거: `build/test-results/` 에 **iOS 디렉터리 자체가 없다**. 즉 **그 모듈의 iOS 커버리지가 0** 이었다.
없던 타겟을 불러서 드러났다. → **백로그**

## 미해결 이슈

- [ ] 🔴 **T-I1 실기 왕복 미실시** — 캐시는 런타임 동작이라 단위 테스트로 못 잡는다. 4항목:
      ① 교체 후 같은 화면 ② 재진입 ③ **상대가 교체 → 내 화면 재진입**(육안 필수) ④ 앱 재실행
- [ ] 🔴 **양 레포 미커밋** — 서버·앱 모두 unstaged. 커밋은 사용자 판단
- [ ] 🔴 `:remote:datasource` iOS 테스트 미컴파일 (부수 발견 ③)
- [ ] 🟡 `MissionCardMineFailedPreview` 가 실제로 안 나오는 화면을 그린다 — `FAILED` → 슬롯 `NONE` 인데
      Preview 는 "다시 인증하기" 버튼을 그림. **현재 코드가 옳고 Preview 가 낡았다**(`FAILED` 에 재시도를
      열지 않는 것이 `ai-verification` 결정). challenge-verification 때부터 어긋나 있었다
- [ ] 🎨 **디자이너 확인 6건** — "다시 찍기" 문구·`Outlined` 스타일·`PhotoCamera` 아이콘·사진 아래 12dp·
      `bold16` / **완료 뱃지를 둔 채 재촬영 버튼을 얹는 조합에 앱 선례 없음** / Done 문구 🟡 초안

## 참조

- [spec.md](./spec.md) · [backend-report.md](./backend-report.md) · [mobile-report.md](./mobile-report.md) · [change-log.md](./change-log.md)
- 개정한 계약: [challenge-verification/api-contract.md](../challenge-verification/api-contract.md) §3·§5 · [change-log.md](../challenge-verification/change-log.md)
- [ADR-0011](../../decisions/0011-photo-storage.md)(`PhotoStorage`) · [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)(`verifiedAt` 초 단위)
- **design.md 없음** — Lovable 에 인증/카메라 화면 0건, "재촬영" 상태도 없어 design-bridge 를 팀에서 제외했다
