# 인증 사진 교체 허용 (verification-photo-replace) — Spec

- **feature-id**: verification-photo-replace
- **owner**: pm-lead
- **상태**: `in-progress` (2026-09-02 착수)
- **선행**: [challenge-verification](../challenge-verification/summary.md) — 이 feature 는 그 계약의 **재제출 정책을 반전**한다
- **후행**: [ai-verification](../ai-verification/spec.md) — 이 feature 가 그 전제다. **AI 판별은 이번 범위가 아니다**

## 배경

challenge-verification 이 재제출을 **전면 거부**로 확정했다. 한 번 제출하면 사진을 바꿀 수 없다.

두 가지 이유로 뒤집는다:

1. **그 자체로 가치가 있다.** 흔들리거나 어둡게 찍힌 사진을 올린 사용자가 지금은 손쓸 방법이 없다.
2. **[ai-verification](../ai-verification/spec.md) 의 전제다.** AI 가 자정에 판별하는데 사진을 못 바꾸면
   사용자에게 방어 수단이 하나도 없다. 그 feature 는 *"마감 전까지 무제한 교체"* 를 fail-open 의
   두 겹 중 하나로 삼는다.

🔴 **사용자 결정(2026-09-02): 사진 교체를 먼저 개통하고 AI 판별을 그 뒤에 얹는다.** 독립적으로
가치 있고 검증 가능한 단위로 쪼개 위험을 줄인다.

---

## §0 사전 실측 (2026-09-02, pm-lead)

| 항목 | 결과 |
|---|---|
| 거부 지점 | `VerificationService.submit()` — `if (mine.status == VERIFIED) throw SnackbarException(MSG_ALREADY_VERIFIED)` |
| `PhotoStorage.delete(key)` | ✅ **이미 있다** (현 호출부는 회원탈퇴 하나). ⚠️ KDoc: *"트랜잭션이 아니다 — 롤백돼도 지워진 파일은 돌아오지 않으므로 반드시 **커밋 후에** 불러라"* |
| 마이그레이션 | ❌ **불필요.** 컬럼 변화 없음 |
| 앱의 인증 CTA 게이트 | 내 status 가 `VERIFIED` 면 CTA 를 숨긴다 (challenge-verification T-M4 ④) |
| 앱의 "회복 절차" | 재제출 재시도 전 `GET /challenges/{id}/verifications` 로 status 선행 조회 (T-M3) — **§1 참조** |

### 🔴 §0.1 거부의 진짜 사유와, 그것이 소멸하는 이유

`submit()` KDoc 원문:

> *"멱등 성공으로 두면 **사용자가 다시 찍어 올린 사진이 조용히 버려지고 앱은 성공이라고 답한다** —
> 상대가 보는 것과 사용자가 올렸다고 믿는 것이 갈라진다. 기획서 §2.4(증거 보존)와 정면으로 어긋난다.
> 따라서 **거부가 유일하게 정직한 답**이다."*

핵심 걱정은 *"판별 수단이 없다"* 가 아니라 **"올린 사진이 조용히 버려진다"** 다.

🔑 **`last-write-wins` 는 올린 사진을 저장한다.** 버려지는 사진이 0 이므로 KDoc 이 지목한 실패
모드가 발생하지 않는다. **정책 뒤집기가 아니라 전제 소멸이다.** 이 논거를 `change-log.md` 에
그대로 남긴다 — 다음 사람이 "왜 확정된 걸 뒤집었나" 를 물을 때 답이 되어야 한다.

### 🔴 §0.2 앱의 회복 절차가 존재 이유를 잃는다

같은 KDoc 이 앱 동작까지 계약으로 못박고 있다:

> *"앱은 재제출을 재시도하기 전에 `GET /challenges/{id}/verifications` 로 내 status 를 먼저
> 확인한다. `VERIFIED` 면 완료 처리하고 `PENDING` 이면 재제출한다."*

재제출이 허용되면 **그냥 다시 올리면 되므로 이 선행 조회가 불필요해진다.**

⚠️ **제거 순서에 제약이 있다** — §4 T-M2 참조.

---

## §1 범위

### 포함

1. **백엔드 — `last-write-wins` 전환**: 재제출 허용, 이전 파일 삭제, 알림 1회, `verified_at` 갱신
2. **계약 개정** — challenge-verification `api-contract.md` §3 + `change-log.md` 등재
3. **모바일 — 재촬영 진입점**: `VERIFIED` 상태에서도 "다시 찍기" 가능
4. **모바일 — 회복 절차 제거** (§0.2)

### 🔴 제외

- **AI 판별 일체** — [ai-verification](../ai-verification/spec.md) 소관. 이번엔 사진을 바꿀 수 있게만 한다
- **마감 직전 제출 고지** — "23:5x 제출은 손쓸 시간이 없다" 안내. AI 판별이 붙어야 의미가 생긴다
- **교체 이력 보존** — 이전 사진은 **지운다.** 몇 번 바꿨는지 남기지 않는다. 필요해지면 별도 feature

---

## §2 사용자 시나리오

1. 챌린지가 `IN_PROGRESS` 인 동안 미션을 수행하고 촬영해 제출한다.
2. 사진이 흔들렸거나 더 나은 걸 찍고 싶으면 **상세 화면에서 "다시 찍기"** 를 눌러 교체한다.
   마감 전까지 몇 번이든 가능하다.
3. **마지막에 올린 사진이 최종본**이다. 상대와 판정 배치가 보는 것도 그것이다.
4. 상대는 **처음 인증했을 때 한 번만** 알림을 받는다. 교체할 때마다 알림이 오지 않는다.

---

## §3 수용 기준

- [ ] `VERIFIED` 상태에서 재제출하면 **거부되지 않고 사진이 교체**된다
- [ ] 교체 후 조회하면 **최신 사진**이 내려온다 (상대 조회도 동일)
- [ ] row 는 여전히 하나다 (`uq_verifications_challenge_user` 유지)
- [ ] 🔴 **이전 사진 파일이 삭제된다** — 참조 0인 파일이 디스크에 쌓이지 않는다
- [ ] 🔴 **삭제가 커밋 후에 일어난다** — 롤백 시 파일이 살아 있어야 한다 (`PhotoStorage.delete` KDoc)
- [ ] 🔴 **`OPPONENT_VERIFIED` 알림은 최초 1회만** — 3회 제출 시 `notifications` row 증가가 **1** 임을 숫자로 검증
- [ ] `verified_at` 이 **최종 교체 시각**으로 갱신된다
- [ ] `IN_PROGRESS` 가 아니면 여전히 거부된다 (마감 후 교체 불가)
- [ ] 당사자가 아니면 여전히 거부된다
- [ ] JPEG 검사·크기 상한 등 기존 검증이 **교체 경로에도 동일 적용**된다
- [ ] 🔴 앱에서 `VERIFIED` 상태에도 **재촬영 진입점이 보인다**
- [ ] 🔴 **기존 "재제출 거부" 테스트가 삭제된다** — 남으면 이제 틀린 것을 지키는 테스트가 된다
- [ ] 백엔드 전체 테스트 회귀 0, 모바일 빌드 성공. 결과는 **숫자로** (CLAUDE.md)

---

## §4 태스크 분해

### 백엔드 (backend-dev)

**T-B1. `submit()` last-write-wins 전환** — 4곳을 고친다

1. **거부 제거** — `if (mine.status == VerificationStatus.VERIFIED) throw ...` 삭제
2. **이전 파일 삭제** — 🔴 **커밋 후에** (`PhotoStorage.delete` KDoc / `WithdrawalService` 선례)
3. **알림 1회** — 이미 `VERIFIED` 였으면 `OPPONENT_VERIFIED` 를 보내지 않는다
4. **`verified_at` 갱신** — 최종 교체 시각

🔴 **KDoc 을 그 자리에서 고쳐라.** 현재 KDoc 의 재제출 정책 표와 *"거부가 유일하게 정직한 답"*
서술이 **코드보다 낡은 채 남으면 다음 사람이 그걸 계약으로 읽는다.** §0.1 의 새 근거로 교체하고,
소비처가 사라진 `MSG_ALREADY_VERIFIED` 상수도 삭제한다.

**T-B2. 계약 개정** — 🔴 `confirmed` 계약 변경

challenge-verification `api-contract.md` §3(재제출 정책) 개정 + `change-log.md` 등재.
근거는 §0.1 을 그대로 옮긴다. **api-contract 의 소유자는 backend-dev 다** — 묻지 말고 고치고
협의 이력에 남긴다.

⚠️ **`verification-photo-replace/api-contract.md` 를 새로 만들지 마라.** 이 feature 는 새 계약을
만드는 게 아니라 **기존 계약을 개정**한다. 사실의 소유자는 한 곳이어야 한다.

**T-B3. 테스트** — 최소 3건. 결과는 숫자로
- 재제출 시 사진이 교체된다
- 재제출 시 이전 파일이 삭제된다
- 3회 제출해도 알림 row 증가가 1이다

### 모바일 (mobile-dev)

> 🔴 코드 편집은 `cd challenge-app && claude -p` child 위임 (`.claude/agents/mobile-dev.md`)

**T-M1. 재촬영 진입점** — 내 status 가 `VERIFIED` 여도 "다시 찍기" 를 노출한다.
현재 CTA 게이트(T-M4 ④)를 조정하되 **인증 완료 표시 자체는 유지**한다.

**디자인 없음** — Lovable 에 이 상태가 0건이다. `:core:designsystem` 토큰과 상세 화면 기존
패턴을 따르고, **디자이너 확인 대상으로 리포트에 등재**한다.

**T-M2. 회복 절차 제거** (§0.2)

⚠️ **순서 제약**: T-B2 의 계약 개정이 **커밋된 것을 파일로 확인한 뒤에** 지운다.
계약이 아직 옛 절차를 요구하는데 앱만 먼저 지우면 어긋난다.

**T-M3. 테스트 + 빌드 검증** — 결과는 **숫자로**

### 통합

**T-I1. 실기 왕복** — 촬영 → 제출 → 상대 알림 1건 확인 → **다시 찍어 교체** → 상대에게 알림이
**추가로 오지 않는지** 확인 → 상대 화면에 **교체된 사진**이 보이는지 확인 → 서버 폴더에
이전 파일이 남아 있지 않은지 확인

---

## §5 의존 관계

```
T-B1 → T-B2 ─(계약 개정 커밋 확인)→ T-M2
  └──→ T-B3
T-M1 (독립 — 계약 shape 변화가 없어 선행 착수 가능)
전부 → T-M3 → T-I1
```

🔵 **API 계약 협의의 실질 쟁점이 적다** — 요청/응답 shape 이 바뀌지 않는다. 바뀌는 것은
**같은 요청에 대한 서버의 행동**(거부 → 교체)과 그에 딸린 앱 절차뿐이다. 협의는 §0.1 근거와
T-M2 순서 제약 확인에 집중한다.

## §6 리스크 / 오픈 이슈

- 🔴 **상대가 본 사진이 바뀐다.** 상대가 A 를 보고 반응했는데 최종본이 B 가 될 수 있다.
  막으면 교체 자체가 막히므로 **그대로 둔다** — 1:1 친구 관계라 실질 피해가 없다는 판단
- **파일 삭제 실패** — 커밋 후 삭제라 실패해도 트랜잭션은 이미 끝났다. **고아 파일이 남을 뿐
  기능은 정상**이다. 예외를 전파해 제출을 실패시키지 마라
- **동시 제출** — 같은 사용자가 두 기기에서 동시에 올리는 경우. 현 규모(1:1, 개인 프로젝트)에서
  발생 가능성이 낮아 **별도 락을 두지 않는다.** `uq` 제약이 row 중복은 막는다
- **교체 이력 부재** — 몇 번 바꿨는지 남지 않는다. AI 판별이 붙은 뒤 *"반려당하고 바꿨나"* 를
  보고 싶어지면 그때 컬럼을 추가한다 (YAGNI)

## 참조

- [challenge-verification/api-contract.md](../challenge-verification/api-contract.md) §3 · [spec.md](../challenge-verification/spec.md) T-M3/T-M4
- [ai-verification/spec.md](../ai-verification/spec.md) §1 · [plan.md](../ai-verification/plan.md) Task 5·8·9 — **이 feature 가 그 셋을 떼어낸 것이다**
- [ADR-0011](../../decisions/0011-photo-storage.md) — `PhotoStorage` 포트
