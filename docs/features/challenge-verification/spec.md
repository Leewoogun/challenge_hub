# 챌린지 인증 (challenge-verification) — Spec

- **feature-id**: challenge-verification
- **작성일**: 2026-08-14
- **상태**: `completed` (2026-08-25 — [summary.md](./summary.md))
- **선행**: [soul-oath](../soul-oath/summary.md)(수락=서명 원자화로 `IN_PROGRESS` 진입) · [push-fcm](../push-fcm/summary.md)(알림 배관)
- **결정**: [ADR-0011](../decisions/0011-photo-storage.md) — 사진은 서버 로컬 폴더 + `PhotoStorage` 포트

## 배경

핵심 플로우에서 `영혼의 맹세`까지 개통됐고 **그 다음이 이 feature 다.**
기획서 §2.5 가 원안이며 아래 4줄이 요구사항의 전부다.

```
- 카메라 촬영 인증: 실시간 카메라로 촬영한 사진만 허용 (갤러리 선택 불가)
- 인증 사진 업로드 시 타임스탬프 자동 기록
- 상대방에게 인증 사진 실시간 전달
- 인증 마감 시간 전까지 미인증 시 자동 패배
```

---

## §0 사전 실측 — 예상보다 많이 깔려 있다

### §0.1 🔴 DB 마이그레이션이 필요 없다

`verifications` 는 **V1 + V4 로 이미 완성돼 있다.**

```sql
-- V1 + V4 적용 후 현재 상태
id, challenge_id, user_id,
status      VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING/VERIFIED/FAILED (V4)
photo_url   TEXT        NULL,                        -- V4에서 nullable화
verified_at TIMESTAMP   NULL,                        -- V4에서 nullable화
created_at  TIMESTAMP   NOT NULL,                    -- V4 추가
CONSTRAINT uq_verifications_challenge_user UNIQUE (challenge_id, user_id)
```

**V4 가 이 feature 를 정확히 내다보고 만들어졌다** — 주석에 *"V1 은 `photo_url NOT NULL` 이라 '아직 인증 안 함'(PENDING) 표현이 불가능했다"* 고 적혀 있다. **새 마이그레이션 0건**이다.

### §0.2 🔴 PENDING row 는 이미 생성되고 있다

`ChallengeCommandService.accept()` 가 수락 트랜잭션 안에서 `pendingVerification()` 2건
(challenger·opponent)을 `saveAllAndFlush` 한다. `soul-oath` 때 들어갔다.

⚠️ **백로그가 이 항목을 "후속 feature"로 남겨 둬 스코프가 부풀어 보였다.** 2026-08-14 정정했다.
**이 feature 는 row 를 만들지 않는다. 이미 있는 row 를 채운다.**

### §0.3 이미 있는 것 / 없는 것

| | 상태 |
|---|---|
| `Verification` 도메인 · `VerificationStatus`(모바일과 값 일치) · repo 포트·구현·엔티티·JPA | ✅ 있음 |
| 홈 피드가 `status` 를 읽어 표시 | ✅ 있음 |
| `NotificationType.OPPONENT_VERIFIED` | ✅ enum 예약됨 (발송 문구는 없음 — §3) |
| `moko-permissions-camera` | ✅ **배선까지 완료** — `AppPermission.CAMERA` enum + `PermissionManagerImpl` 매핑 + `core/permission` 실제 의존. (⚠️ pm-lead 초기 브리핑이 *"등록만 돼 있다"* 고 **과소평가**했다. mobile-dev 실측 정정) |
| **Coil (이미지 로더)** | 🔴 **카탈로그 등록만. 사용처 0건** — `build.gradle.kts` 의존 선언조차 없다. **인증 사진이 이 앱의 첫 원격 이미지가 된다.** §0.4 |
| **verification 엔드포인트** | ❌ **0건** |
| **파일 업로드 인프라 · `spring.servlet.multipart` 설정** | ❌ **0건** |
| **`AndroidManifest` CAMERA 권한 · 카메라 촬영 코드** | ❌ 없음 |
| **Lovable 인증/카메라 화면** | ❌ **route 0건** — §5 참조 |

### §0.4 🔴 T-M4 는 "사진을 보여준다" 한 줄이 아니다 — 이미지 로더가 없다

**이 앱은 원격 이미지를 한 번도 로드한 적이 없다.** Coil 3.2.0 이 카탈로그에 있으나 **사용처 0건**이고,
`profileImageUrl` 은 도메인·DTO·State 를 타고 화면까지 도달하는데 **그리는 단계만 없다.**
`FriendSearchItem` KDoc 이 직접 증언한다 — *"이미지 로더 부재로 `profileImageUrl` 은 시그니처에만 받고
닉네임 이니셜 placeholder 로 렌더한다."*

**따라서 T-M4 는 이미지 로딩 스택 초기화를 포함한다:**

1. `ImageLoader` 전역 초기화 (Coil 3 `SingletonImageLoader`, KMP)
2. 🔴 **fetcher 는 기존 `HttpClient` 를 재사용하면 안 된다** — Ktor `Auth(bearer)` 플러그인이
   **사진 URL 에도 우리 JWT 를 붙인다.** 계약이 업로드 URL 에서 JWT 를 뗀 것과 **같은 문제가 조회에서 재발**한다.
   지금은 우리 서버라 무해해 보이지만 오브젝트 스토리지로 이사하면 **자격증명을 제3자 호스트로 보낸다**
3. **디스크 캐시 키** — 서명 URL 은 매 조회마다 쿼리가 달라진다. Coil 기본 캐시 키가 full URL 이라
   **같은 사진을 매번 다시 받는다.** ⚠️ **계약은 이미 요구를 충족한다**(경로 고정 + 토큰은 쿼리) —
   **클라이언트가 캐시 키를 경로만으로 지정하면 된다. 계약 변경 불필요**

> 🔴 **교훈 — "카탈로그 등록"을 "준비됨"으로 읽으면 스코프를 과소평가한다.** 이번 feature 에서
> **두 번** 나왔다: `moko-permissions-camera`(실제로는 배선 완료 — 과소평가) / `coil`(등록만 — 과대평가).
> **두 번 다 카탈로그만 보고 판단했고 방향이 서로 반대였다.** 실측 대상은 카탈로그가 아니라 **사용처**다.

**범위 판정 (pm-lead)**: **배선만 하고 기존 화면은 건드리지 않는다.** 이미지 로더가 들어가면
`profileImageUrl` placeholder 들(홈 받은 도전장 카드 / 친구 목록 / 친구 검색)이 살아날 수 있으나,
**세 화면을 동시에 바꾸면 회귀 표면이 넓어진다.** 백로그로 넘긴다.

---

## §1 범위

### 포함

1. 사진 업로드 (촬영 → 업로드 → 제출 확정 → `VERIFIED` 전이 + `verified_at` 기록)
2. 상대 인증 사진 조회 (당사자 검사 + 만료 있는 읽기 URL)
3. `OPPONENT_VERIFIED` 알림 발송
4. `PhotoStorage` 포트 + 로컬 디스크 구현체 (ADR-0011)

### 🔴 제외 — 판정 feature 소관

**"마감 전 미인증 시 자동 패배"(기획서 §2.5 4번째 줄)는 이번 범위가 아니다.**

- `FAILED` 전이는 **시각 기준 배치**이고 `:batch` 모듈은 **`.kt` 파일 0개**다
- 기획서 §2.6 판정 규칙(양측 인증=무승부 / 한쪽만=인증한 쪽 승 / 양측 미인증=양쪽 패)은
  **결과 판정 feature 의 입력**이다. 여기서 절반만 구현하면 규칙이 두 곳에 흩어진다
- `REMIND`(마감 1시간 전) · `RESULT` 알림도 같은 이유로 제외

**이번 feature 가 남기는 상태**: `VERIFIED` row 와 `verified_at`. 판정 feature 는 그것을 읽기만 하면 된다.

### 제외 — 별도 결정 필요

- **보관 기간 / 삭제 정책** — ADR-0011 이 "별도로 정해야 할 것"으로 넘겼다. 지우지 않는다(단조 증가 인지)
- **진위 판정** — 🔵 **기획서 원안에 판정 절차가 없다.** 제출하면 인정이고 상대는 **보기만 한다.**
  승인/거부 액션을 만들지 않는다. (repos.json 의 *"인증 진위 판정 주체 보류"* 는 이 원안을 유지한다는 뜻)

---

## §2 사용자 시나리오

1. 챌린지가 `IN_PROGRESS` 인 동안, 미션을 수행하고 **앱에서 카메라로 촬영**한다.
   🔴 **갤러리 선택은 막는다**(기획서 §2.5) — 미리 찍어둔 사진이나 남의 사진을 올릴 수 없어야 한다.
2. 촬영 후 제출하면 내 인증이 `VERIFIED` 가 되고 **상대에게 알림이 간다.**
3. 상대는 알림을 눌러 챌린지로 들어와 **내가 올린 사진을 본다.** 판정하지 않고 보기만 한다.
4. 나도 상대가 올린 사진을 본다. 양쪽 다 올리면 각자 상대 것을 볼 수 있다.

## §3 수용 기준

- [ ] 촬영 → 제출 후 `verifications.status = VERIFIED`, `photo_url` 채워짐, `verified_at` 기록됨
- [ ] 🔴 **갤러리에서 고를 수 없다** — 촬영 경로만 열린다
- [ ] 제출 시 상대에게 `OPPONENT_VERIFIED` 알림이 간다
- [ ] 🔴 **당사자가 아니면 사진을 볼 수 없다** — 제3자 요청은 거부된다
- [ ] 읽기 URL 에 **만료가 있다** — 유출돼도 영구히 열려 있지 않다
- [ ] 같은 사용자가 두 번 제출해도 row 가 하나다 (`uq_verifications_challenge_user`)
- [ ] 🔴 **업로드 실패가 챌린지 상태를 깨뜨리지 않는다** — 실패 시 `PENDING` 이 유지된다
- [ ] `IN_PROGRESS` 가 아닌 챌린지에는 제출할 수 없다
- [ ] 🔴 **사진이 리사이즈되어 올라간다** — 장당 목표 ~500KB (§4 T-M2)
- [ ] 서버 재기동 후에도 이전에 올린 사진이 보인다 (로컬 폴더 영속 확인)

---

## §4 태스크 분해

### 백엔드 (backend-dev)

**T-B1. `PhotoStorage` 포트 + 로컬 디스크 구현체** — ADR-0011 §2
- `NotificationSender` ↔ `FcmNotificationSender`/`NoOpNotificationSender` 구조를 그대로 따른다
- 🔴 **저장 경로·파일명 규칙을 정하고 근거를 남겨라.** 사용자 입력을 파일명에 그대로 쓰지 않는다
  (경로 탈출). key 는 서버가 만든다
- 저장 루트는 **설정값**으로 뺀다 — 로컬/배포에서 달라진다 (ADR-0007)

**T-B2. 사진 제출 엔드포인트** — 🔴 **2026-08-18 개정: multipart 직접 수신** (ADR-0011 §3 supersede)

> ⚠️ **이 태스크의 지시가 뒤집혔다.** 원문은 *"URL 발급 방식 고정 — 앱이 서버로 파일을 밀어넣는
> multipart 로 만들지 마라"* 였다. 사용자 결정(2026-08-18)으로 **정확히 그 반대**가 됐다.
> 사유·트레이드오프는 [ADR-0011 §3](../../decisions/0011-photo-storage.md) 과
> [change-log.md](./change-log.md) 2026-08-18 항목.

- 앱이 `multipart/form-data` (part 이름 `photo`) 로 올리면 **한 요청에서 저장 + 확정**까지 한다
- 제출 시 `VERIFIED` 전이 + `verified_at` 기록
- **`IN_PROGRESS` 아니면 거부. 당사자 아니면 거부.** `ChallengeDetailService` 의 당사자 검사가 선례
- 재제출 정책을 정하고 계약에 적어라. `uq_` 제약이 있으므로 **정하지 않으면 500 이 난다**
  → ✅ **확정: 전면 거부.** `photoKey` 왕복이 사라져 *"같은 촬영본의 재시도"* 와 *"다른 사진으로 교체"* 를
  **판별할 수단이 없으므로**, 멱등 성공을 두면 다시 찍은 사진이 조용히 버려진다 (계약 §3)
- 크기 상한은 `spring.servlet.multipart` 로 건다 — spec §2 가 *"0건"* 으로 적었던 그 설정이다

**T-B3. 조회 — 만료 있는 읽기 URL** — ADR-0011 §4
- 🔴 **당사자 검사는 서버가 한다.** 자체 JWT 라 스토리지 규칙 엔진으로는 판정 불가
- ✅ **확정(2026-08-14): 별도 엔드포인트 `GET /challenges/{id}/verifications`.** `GET /challenges/{id}` 는 무변경 →
  `change-log.md` 등재 불필요. 🔴 **pm-lead 가 처음에 *"얹어라"* 로 판정했다가 철회했다** — 얹으면
  **상세 전체가 단명 응답**이 되어 사진 하나 갱신에 계약서 재조회를 강요한다. 반대 논거였던
  *"만료를 이미지 로드 실패로만 감지"* 는 `photoUrlExpiresAt` 이 해소했다

**T-B4. `OPPONENT_VERIFIED` 알림 발송**
- 배관은 이미 있다. `NotificationMessages.of()` 에 문구를 추가하면 게이트가 풀린다
- 🔴 **계약 §0.6.1 규약이 여기 걸린다** — *"문구 추가 = 발송 개시"* 이므로 **모바일 통지가 선행**한다
- 🔴 **문구는 사용자 확정 대상이다.** 초안값으로 넣고 **`🟡 초안값` 으로 표시**하라.
  ⚠️ **기존 3종에 톤을 맞추려 하지 마라** — KDoc 이 *"임의로 통일하지 마라, 확정분을 초안에 맞추는
  방향은 특히 안 된다"* 고 명시했다. 백로그 🟡 항목이다
- 발송은 `AFTER_COMMIT` (push-fcm 결정사항 3번). **알림 실패가 인증을 롤백시키면 안 된다**

### 모바일 (mobile-dev)

> 🔴 코드 편집은 `cd challenge-app && claude -p` child 위임 (`.claude/agents/mobile-dev.md`)

**T-M1. 카메라 촬영 화면**
- 🔴 **갤러리 진입점을 만들지 마라** (기획서 §2.5)
- `moko-permissions-camera` 는 의존성만 등록돼 있다. **`AndroidManifest` CAMERA 권한 + 실제 촬영 코드가 없다**
- 🔵 **구현 방식은 네가 정하라.** 다만 `push-fcm` 결정사항 8번(**KMP 커뮤니티 래퍼 미사용 — 네이티브 +
  expect/actual**)과 카카오 SDK 선례가 이 프로젝트의 기준이다. 다르게 가려면 근거를 대라
- iOS 는 `push-fcm` 처럼 **스텁으로 두고 Android 우선**해도 된다. 그 경우 리포트에 명시

**T-M2. 🔴 업로드 전 리사이즈** — ADR-0011 이 *"저장소 선택보다 실질 영향이 크다"* 고 적은 항목
- 목표 장당 ~500KB. 원본 그대로면 어떤 저장소든 금방 찬다
- 목표치와 실측값을 리포트에 **숫자로** 남겨라

**T-M3. 업로드 + 제출 연동** — 🔴 **2026-08-18 개정: 제출 API 에 multipart 로 한 번에** (원문은 *"서버가 준 대상으로 올리고 제출 확정"*)
- 업로드 실패 시 사용자에게 알리고 **재시도 가능**해야 한다. 실패가 조용히 삼켜지면 안 된다
- 🔴 **재시도 전에 T-M4 의 조회 API 로 내 status 를 확인**해야 한다 — 재제출이 전면 거부라
  *"성공했는데 응답만 유실"* 된 경우를 문구가 아니라 상태로 판별한다 (계약 §3 회복 절차)

**T-M4. 상대 사진 보기** — ~~챌린지 상세에서. 만료 URL 이므로 만료 후 재진입 시 갱신되어야 한다~~
🔴 **2026-08-24 확장 개정 (사용자 결정)** — 만료 URL 은 2차 계약 개정으로 소멸했고, 범위가 **상세 화면
재구성**으로 확장됐다. **Lovable `challenge-detail.tsx` 가 정본**이며 (§5 정정 참조) 다음을 포함한다:

1. **VS 헤더** — 나/상대 아바타 + **남은 시간 상대 표기**(예: `남은 시간: 5시간 32분`, 분 단위 갱신)
2. **미션 카드 2장 분리** — 현행 계약서 카드의 미션 행 나열을 폐기. "나의 미션" 카드(미션 + 상태 뱃지 +
   **인증하기 CTA 를 카드 안으로 이동**) / "상대의 미션" 카드(미션 + 상태 뱃지 + **인증 사진**)
3. **내 사진** — 인증 완료 후 내 카드의 CTA 자리를 내 사진 + 완료 뱃지로 교체 (Lovable 에 이 상태가
   없어 상대 카드 패턴을 미러링한다 — 디자이너 확인 대상으로 design.md 에 표기)
4. **§4 조회 연동 + 버튼 게이트** — 내 status 가 `VERIFIED` 면 인증 CTA 를 숨긴다 (기존 "IN_PROGRESS 면
   항상 노출" 한계 해소)
5. **Coil 배선** — 이 앱의 첫 원격 이미지. 기본 인증 `HttpClient` 를 그대로 물린다 (2차 개정으로 단순화)
   - 🔴 **URL 조인**: `baseUrl.trimEnd('/') + photoUrl` 한 곳으로 모으고 결과를 테스트로 고정 —
     `//` 는 서버가 404 로 거부하며 **정상 404 와 구분 불가능하게 조용히 실패**한다 (mobile-report 16번)
   - 🔴 **404 무캐시 확인** — 같은 URL 이 404→200 으로 바뀐다 (mobile-report 17번)
6. 계약서(내기 공유 1건 + 서명 2열) 카드는 유지. **도발하기(Taunt) 섹션은 범위 밖** — 별도 feature

> 배경: 사용자 기획 판단 3건 (2026-08-24) — ① 양측 인증 사진은 상세에서 통합 확인 ② 미션 나/상대
> 가독 분리 ③ 남은 시간 표기. 셋 다 Lovable 상세 디자인에 이미 반영돼 있음이 확인돼 그 디자인을 채택했다.

**T-M5. 테스트 + 빌드 검증** — 🔴 결과는 **숫자로** (CLAUDE.md)

### 통합

**T-I1. 실기 검증** — 촬영 → 업로드 → 상대 알림 → 상대가 사진 확인. **서버 재기동 후 사진 유지 확인**

---

## §5 🔴 디자인이 없다 — design-bridge 를 팀에서 제외한다

> 🔴 **2026-08-24 부분 정정**: 아래 서술은 **촬영/인증 화면**에 대해서는 여전히 참이나, **챌린지 상세**에는
> `challenge-detail.tsx` 디자인이 존재하고 T-M4 확장(위)이 그것을 정본으로 채택했다.
> **T-M4 에는 design-bridge 를 투입한다.** 촬영 화면(Verify)은 계속 디자인 대기.

**Lovable 에 카메라/인증 route 가 0건이다.** 기획서 §4 IA 에는 *"인증 카메라 — 카메라 촬영 → 인증 제출"*
화면이 있으나 **디자이너가 만든 적이 없다.**

백로그 🟡 *"영혼의 맹세(STT + 서명) 화면 디자인"* 과 같은 축이며, **디자이너 대기 화면이 2개가 된다.**

**대응**: design-bridge 를 팀에 넣지 않는다(가져올 자료가 없다). mobile-dev 가 `:core:designsystem`
토큰과 기존 화면 패턴을 따라 구현하고, **디자인이 나오면 교체한다는 전제를 리포트에 명시**한다.
`soul-oath` 도 같은 상태로 진행했다.

---

## §6 의존성

```
T-B1 → T-B2 → T-B3
         └──→ T-B4 (통지 선행)
T-M1 → T-M2 → T-M3 → T-M4
계약 확정 → T-B2..T-B4 / T-M3..T-M4
전부 → T-M5 → T-I1
```

🔴 **API 계약 협의가 이번엔 실질적이다.** `push-deeplink` 는 shape 변경이 0이라 협의가 형식적이었으나,
여기서는 **업로드 방식·재제출 정책·조회 위치** 세 가지가 실제로 갈린다. 착수 전에 확정하라.

## 참조

- [ADR-0011](../decisions/0011-photo-storage.md) · [ADR-0007](../decisions/0007-environment-split.md)
- [기획서 원안 §2.5/§2.6](../product/notion-planning-snapshot-2026-08-06.md)
- [push-fcm/api-contract.md](../push-fcm/api-contract.md) §0.6.1(발송 개시 통지 규약) · [push-fcm/summary.md](../push-fcm/summary.md)(결정사항 3·4·8번)
