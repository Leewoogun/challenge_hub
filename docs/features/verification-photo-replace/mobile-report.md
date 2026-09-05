# Mobile Report — verification-photo-replace

- **작성**: mobile-dev, 2026-09-02
- **범위**: spec §4 의 **T-M1 / T-M2 / T-M3 / T-M4** + Done 문구 분기
- **결과**: ✅ **전부 완료.** Android 112 · iOS 73 · failures 0

> T-M4(Coil 캐시 무효화)와 Done 문구 분기는 **원래 배정에 없던 항목**이다. 착수 후 계약 개정에
> 딸려 온 모바일 의무를 발견해 등재했다 — 각각 §T-M4 · §Done 문구 참조.

---

## 구현 요약

네 덩어리가 들어갔다.

| # | 무엇 | 왜 |
|---|---|---|
| **T-M1** | `VERIFIED` 여도 "다시 찍기" 노출 | 재제출이 허용됐으므로 게이트의 근거가 소멸 |
| **T-M2** | 회복 절차(`confirmSubmission`) 제거 | 재제출이 그냥 성공하므로 판별할 것이 없음 |
| **T-M4** | Coil 캐시 키 = `photoUrl + verifiedAt` | 🔴 **없으면 다시 찍어도 옛 사진이 뜬다** |
| — | Done 문구 최초/교체 분기 | 교체는 알림이 안 나가는데 *"전달돼요"* 는 거짓 |

**API 요청/응답 shape 변경 0건.** DTO·Mapper·Repository·UseCase·`:remote:*`·`:data:*` 무변경.
`PartyVerification.verifiedAt` 이 **이미 도메인 모델에 있어** 새로 받아올 값도 없었다.

---

## T-M1 — 재촬영 진입점

바꾼 것은 **게이트의 근거 하나**다.

| | 전 | 후 |
|---|---|---|
| `canVerify` | `IN_PROGRESS` **그리고** 내가 `VERIFIED` 가 아님 | `IN_PROGRESS` **만** |
| `VERIFIED` 의 역할 | 진입점을 **닫는다** | 같은 칸의 **모양만 가른다** |

`MyMissionSlot` 에 `MY_PHOTO_WITH_RETAKE` 를 신설했다. 완료 뱃지와 내 사진은 그대로 두고 사진
아래에 "다시 찍기"(Outlined)를 얹는다.

🔴 **마감 후 교체 불가는 지켜진다** — `IN_PROGRESS` 가 아니면 `VERIFIED` 여도 `MY_PHOTO`(사진만)로
떨어진다. **내 인증 상태를 양쪽 다 `VERIFIED` 로 고정하고 챌린지 상태 한 줄만** `IN_PROGRESS` ↔
`COMPLETED` 로 바꿔 가르는 테스트로 고정했다 — 한쪽 입력만 쓰면 그 테스트는 아무것도 증명하지 않는다.

## T-M2 — 회복 절차 제거

계약 §3 이 *"재시도 전에 §4 로 status 를 확인하던 절차는 **소멸했다**"* 로 개정된 것을 **working
tree 본문으로 확인한 뒤** 지웠다(§계약 확인 근거).

- `VerifyViewModel.confirmSubmission()` (전송 끊김 → `getVerifications` → `VERIFIED` 면 Done) **삭제**
- 그 유일한 소비자였던 `myUserId()` **삭제**, 생성자에서 `userInfoRepository` **제거**
- `VerificationSubmitOutcome.Unreachable` → `failSubmit(isRetryable = true)` 로 직결
- `FakeUserInfoRepository.kt` **파일째 삭제**(verify 모듈 잔여 참조 0건 확인)

```
$ grep -rn "confirmSubmission" --include="*.kt" . | grep -v "/build/" | wc -l
0
```

### 🔵 `Rejected` 는 그대로 뒀다 — 계약이 그렇게 말한다

계약 §3 재시도 판정 표(L449-458)를 직접 읽고 맞췄다:

| code | 상황 | 같은 사진 재시도 |
|---|---|---|
| 700 | `photo` 누락 / JPEG 아님 / 5 MiB 초과 / multipart 형식 오류 | ❌ 소용없다 |
| 700 | 당사자 아님 | ❌ 소용없다 |
| 705 | 챌린지 없음 / `IN_PROGRESS` 아님 | ❌ 소용없다 |
| — | **네트워크 오류 · 타임아웃** | ✅ 🔴 **여기가 개정으로 바뀐 유일한 칸** |

> *"`isRetryable` 은 **서버가 답을 줬는가** 로 갈린다."*

따라서 `Rejected.isRetryable = false` **유지**가 맞고, 바뀐 것은 `Unreachable` 하나뿐이다.
⚠️ **`code=700` 자체는 사라지지 않았다** — 없어진 것은 `이미 인증을 완료했어요` **한 줄**이다.

## T-M4 — 🔴 Coil 캐시 무효화 (원래 배정에 없던 항목)

### 왜 필요했나

계약 §5 가 `max-age=86400` → `no-cache` + ETag 로 개정되면서 **앱에 직접 의무를 지웠다**:

> *"이 헤더는 이미지 로더의 **메모리** 캐시에 닿지 않는다. Coil 처럼 URL 을 키로 메모리/디스크
> 캐시를 따로 두는 로더는 HTTP 캐시 의미를 무시할 수 있다. 그러면 **교체 후에도 같은 화면에서
> 옛 사진이 그대로 보인다.**"*

**실측**: `composeApp/.../App.kt:79-85` 의 `ImageLoader.Builder(context)` 는 기본값이라 메모리·디스크
캐시가 URL 키로 켜져 있다. 사진 경로는 교체돼도 그대로다(`/api/v1/challenges/{id}/photos/{party}`).

🔴 **이 실패는 조용하다** — 예외도 로그도 없고 앱은 정상적으로 캐시를 쓴 것뿐이다. **테스트는 전부
초록인데 사용자가 다시 찍어도 옛 사진이 뜬다.** 이 feature 의 핵심 UX 가 통째로 안 먹는 상태였다.

### 🔴 수용 기준 2 — 내가 직접 돌린 grep (명령과 결과 그대로)

*"구현했다"* 를 근거로 쓰지 않는다. 이 항목은 근거 없이 완료 처리된 이력이 있다.

```
$ cd /Users/hwamulman/woogunProject/challenge/challenge-app
$ grep -rn "memoryCacheKey\|diskCacheKey" --include="*.kt" . | grep -v "/build/"
feature/challenge/detail/src/commonMain/kotlin/com/lwg/challenge/feature/challenge/detail/component/VerificationPhoto.kt:113:            .memoryCacheKey(cacheKey)
feature/challenge/detail/src/commonMain/kotlin/com/lwg/challenge/feature/challenge/detail/component/VerificationPhoto.kt:114:            .diskCacheKey(cacheKey)

$ grep -n "model = " feature/challenge/detail/.../component/VerificationPhoto.kt
124:            model = request,
```

**0건 아님. 두 층 모두 설정됨.** `model = url` → `model = request` 로 바뀐 것도 함께 확인.
🔴 **한 층만 갈면 다른 층에서 옛 사진이 돌아온다** — 그래서 둘 다 지정했다.

### 구현

```kotlin
private fun photoCacheKey(photoUrl: String?, verifiedAt: LocalDateTime?): String? {
    val url = photoUrl ?: return null
    return if (verifiedAt == null) url else "$url|$verifiedAt"
}
```

**URL 자체는 안 바꿨다.** 계약이 *"URL 에 버전 쿼리를 붙이는 건 §4 `photoUrl` 모양을 바꾸므로
모바일과 합의해야 하는 별건"* 이라 했는데, **클라이언트 캐시 키는 URL 을 바꾸지 않으므로 그 별건에
해당하지 않는다.** 요청은 여전히 같은 경로로 나간다 — **서버 작업 0.**

교체 시 서버가 `verified_at` 을 갱신하므로(T-B1 ④) 키가 반드시 바뀐다. **내 교체와 상대 교체를
구분할 필요가 없다** — §4 재조회만으로 신선도가 따라온다.

### 🔵 서버 ETag/304 를 앱이 타지 않는 이유

**의존 대상의 신뢰도** 때문이다. ETag 방식은 **계약이 스스로 *"무시할 수 있다"* 고 경고한 바로 그
동작이 실제로는 제대로 작동한다는 데 거는 베팅**이다. 캐시 키 방식은 HTTP 캐시 의미를 **하나도
쓰지 않는다** — 클라이언트가 키를 직접 정하므로 결정적이다. (부차적으로 화면 진입마다 왕복 2회가
붙는 비용도 있지만 그건 두 번째 이유다.)

🔵 **backend 의 ETag 는 낭비가 아니다.** 브라우저·프록시·향후 다른 클라이언트에는 정상 동작하고,
오브젝트 스토리지로 이사할 때도 산다. **앱이 안 탈 뿐이다.** 다음 사람이 *"왜 만든 걸 안 쓰나"* 를
물을 자리라 남긴다.

### ⚠️ 알려진 한계 — 방어 로직을 넣지 않았다

`verifiedAt` 이 **초 단위**(ADR-0010)라 **같은 초에 두 번 교체하면 키가 겹쳐** 옛 사진이 남는다.

촬영 → 미리보기 확인 → 제출 → 업로드 왕복이 1초 안에 두 번 끝날 수 없어 **실사용상 도달하지
않는다**고 본다. 🔴 **여기에 방어 로직을 넣지 않았다** — 관측된 버그가 아니라 가정이고, 이 레포는
가정에 방어를 넣지 않는다. 나중에 도달 가능해지면(예: 자동 재제출 기능) 그때 근거를 갖고 고친다.

### `PENDING` 상대의 키 + `PENDING → VERIFIED` 전이 — **안 뜨는 경로 없음**

근거 3겹:

1. 🔑 **`PENDING` 이면 애초에 캐시에 아무것도 안 들어간다.** 계약상 `photoUrl` 은 `VERIFIED` 가
   아니면 `null` 이라 키가 `null` 이고, 더 중요하게는 `VerificationPhoto` 가 `PENDING` 에서
   **`RemotePhoto` 를 아예 렌더하지 않는다**(`"아직 인증하지 않았어요"` 문구만). **요청 자체가 안
   나간다.** 키 설계 이전에 경로가 없다.
2. **전이 시 키가 반드시 새 값이다.** `verifiedAt` 이 `null → 시각` 이 되므로 키가
   `null` → `"url|2026-09-02 15:32:10"`. **충돌할 옛 항목이 존재하지 않는다.**
3. **`null` 을 문자열로 접지 않았다.** `"url|null"` 같은 키를 만들지 않고 `verifiedAt == null` 이면
   **URL 단독**(= 키 미지정 시 Coil 기본 동작)으로 떨어뜨린다. **옛 동작보다 나빠지는 경로가 없다.**

🔵 오히려 이 자리는 **좋아진다** — 상대 사진이 `404 → 200` 으로 바뀌는 구간에서 키까지 함께
갈리므로 **신선도가 두 겹**이 된다.

## Done 문구 — 최초/교체 분기 (🟡 초안)

교체했는데 *"상대에게 전달돼요"* 가 뜨면 **사용자가 상대에게 알림이 갔다고 오해한다.** 실제로는
알림이 안 가고(계약 §3: 최초 1회만) 상대가 들어와야 본다.

| | 문구 |
|---|---|
| 최초 인증 | `오늘의 미션 인증이 상대에게 전달돼요.` — **무변경** |
| 교체 | 🟡 `사진이 교체됐어요. 상대는 최신 사진을 보게 돼요.` |

🔴 *"알림은 가지 않아요"* 로 쓰지 않았다 — 사실이지만 사용자가 손해로 읽는다. **상대가 최신 사진을
본다는 것이 실제로 일어나는 일**이라 그게 더 정확하다.

제목 `인증이 완료됐어요 🔥` 는 **유지**했다. 교체해도 인증 상태 자체는 완료이고, 제목까지 가르면
교체가 *다른 결과*처럼 읽혀 *"그럼 내 인증은 어떻게 된 거지"* 를 만든다.

**배선**: `Route.Challenge.Verify(challengeId, isReplace)` — **API 추가 호출 0건.** 상세 화면이 이미
내 인증 상태를 아는 값이라 서버에 다시 묻지 않는다. 기본값을 주지 않아 새 진입점(알림 딥링크 등)이
생기면 `false` 로 조용히 새는 대신 컴파일 에러가 난다.

⚠️ `uniqueContentKey()` 영향 확인함 — `"${this::class.qualifiedName}#$this"` 라 필드가 늘면 key
문자열이 바뀐다. **영향은 없고 오히려 안전해진다**: key 가 더 세분화될 뿐 합쳐지지 않으며,
`Verify(1, false)` 와 `Verify(1, true)` 가 별개 entry·별개 ViewModel scope 가 되는 것은 의도에 맞다.

---

## 테스트 결과

🔴 **판정 근거는 로그의 `BUILD SUCCESSFUL` 이다** (종료 코드·`| tail` 을 쓰지 않았다).

```
./gradlew :feature:challenge:detail:testDebugUnitTest \
          :feature:challenge:detail:iosSimulatorArm64Test \
          :feature:challenge:verify:testDebugUnitTest \
          :feature:challenge:verify:iosSimulatorArm64Test \
          :remote:datasource:testDebugUnitTest \
          :composeApp:compileDebugKotlinAndroid \
          :composeApp:linkDebugFrameworkIosSimulatorArm64
→ BUILD SUCCESSFUL in 48s        ← 최종 (픽스처 정리 반영분)
```

> 이전 실행(픽스처 정리 전, `:remote:datasource` 미포함)은 `BUILD SUCCESSFUL in 3m 26s` 로
> `detail` 52 · `verify` 21 이었다. 아래 표가 **최종값**이다.
>
> ⚠️ `:remote:datasource:iosSimulatorArm64Test` 는 **의도적으로 뺐다** — 이 모듈의 iOS 테스트는
> 선행 결함으로 컴파일되지 않는다(§미해결 이슈 2). 넣으면 `BUILD FAILED` 가 나며, 그 실패는
> 이번 변경과 무관하다.

XML 직접 실측:

| 모듈 / 타겟 | tests | failures | errors | skipped | XML timestamp |
|---|---|---|---|---|---|
| `detail` / `testDebugUnitTest` | **52** | **0** | 0 | 0 | `2026-09-02T01:12:12.655Z` ⚠️ |
| `detail` / `iosSimulatorArm64Test` | **52** | **0** | 0 | 0 | `2026-09-02T01:12:06.057Z` ⚠️ |
| `verify` / `testDebugUnitTest` | **21** | **0** | 0 | 0 | `2026-09-02T01:22:49.054Z` |
| `verify` / `iosSimulatorArm64Test` | **21** | **0** | 0 | 0 | `2026-09-02T01:22:51.143Z` |
| `remote:datasource` / `testDebugUnitTest` | **39** | **0** | 0 | 0 | `2026-09-02T01:22:53.xxxZ` |
| `remote:datasource` / `iosSimulatorArm64Test` | — | — | — | — | 🔴 **디렉터리 자체가 없다** (§iOS 결함) |

`remote:datasource` 39건 내역: `ChallengeRemoteDataSourceImplTest` 23 · `LoginRemoteDataSourceImplTest` 8 ·
`VerificationRemoteDataSourceImplTest` 8.

### **Android 112 · iOS 73 · failures 0**

⚠️ **`detail` 의 XML timestamp 가 `01:12` 인 것은 stale 오탐이 아니다.** 픽스처 정리가 `verify` 와
`remote:datasource` 만 건드려 Gradle 이 `detail` 을 **`UP-TO-DATE` 로 건너뛴 것**이고, 로그로 확인했다:

```
> Task :feature:challenge:detail:testDebugUnitTest UP-TO-DATE
> Task :feature:challenge:detail:iosSimulatorArm64Test UP-TO-DATE
> Task :feature:challenge:verify:testDebugUnitTest          ← 실행됨
> Task :feature:challenge:verify:iosSimulatorArm64Test      ← 실행됨
> Task :remote:datasource:testDebugUnitTest                 ← 실행됨
```

즉 `detail` 의 52/52 는 **입력이 한 글자도 바뀌지 않은 동일 코드**에 대한 `01:12` 실행 결과다.
🔴 **iOS XML 이 stale 인지 판단할 때는 timestamp 만 보지 말고 `UP-TO-DATE` 여부까지 함께 봐야 한다** —
과거 사고(T7a·T7b)는 *입력이 바뀌었는데도* 옛 XML 을 읽은 경우이고, 이번은 그것과 다르다.
- 빌드: Android `compileDebugKotlinAndroid` ok / iOS `linkDebugFrameworkIosSimulatorArm64` ok
  — `:composeApp` 링크가 `:core:navigation` · `:feature:main` 을 전부 끌고 가므로 **배선 변경
  (`Route.Challenge.Verify` 필드 추가)이 실제로 컴파일되는지까지 이 실행이 답한다.**
- detail 이 46 → **52** 로 는 것은 캐시 키 테스트 6건이다. verify 는 회복 절차 5건 삭제 + 신규 1건.
- detekt max-line-length(120자) — 변경 파일 전부 위반 0건. ⚠️ 한글은 **문자** 기준으로 세야 한다
  (`awk length` 는 바이트라 오탐).

### 추가/변경한 테스트

**캐시 키 6건 (신규)** — 🔴 두 축을 갈라놓는 입력으로 검증했다:
```
사진을 교체하면 URL 이 같아도 캐시 키가 달라진다     ← 핵심. 같은 URL / 다른 verifiedAt
인증 시각이 그대로면 캐시 키도 그대로다              ← 불필요한 재로딩을 만들지 않는다
인증 시각이 없으면 캐시 키가 URL 로만 떨어진다
사진 URL 이 없으면 캐시 키도 null 이다
나와 상대의 캐시 키가 서로 섞이지 않는다
인증 현황을 모르면 캐시 키도 null 이다
```

**T-M1 관련**: `내가 이미 인증했어도 재촬영 진입점이 열린다`(개명+뒤집기),
`내 미션 슬롯이 챌린지 상태와 내 인증 상태의 조합으로 갈린다`(신규, 슬롯 4값 전부 고정),
`IN_PROGRESS 가 아니면…`(슬롯 단언 추가 — **마감 후 교체 불가를 지키는 테스트**),
`내가 opponent 여도…`(판정 축을 `canVerify` → `myMissionSlot` 으로 교체).

**T-M2 관련**: 회복 절차 검증 **5건 삭제** →
`Unreachable 이면 현황 조회 없이 재시도 가능한 실패를 표시한다` **신규**
(`getVerificationsCallCount == 0` 으로 *"조회 없이"* 를 고정).

### 추가한 Preview

| 이름 | 파일 |
|---|---|
| `ChallengeDetailScreenVerifiedWithRetakePreview` | `screen/ChallengeDetailScreen.kt:190` |
| `MissionCardMineWithPhotoAndRetakePreview` | `component/MissionCard.kt:155` |
| `VerifyDoneSectionReplacePreview` | `verify/component/VerifyDoneSection.kt:101` |

---

## 🎨 디자이너 확인 대상

### T-M1 재촬영 진입점 — **Lovable 에 이 상태(내가 인증 완료 + 진행 중)가 0건**

`:core:designsystem` 토큰과 상세 화면 기존 패턴만으로 정했다. **전부 확인 대상이다.**

| 항목 | 고른 값 | 근거 |
|---|---|---|
| 문구 | **"다시 찍기"** | spec §2 용어 그대로 |
| 버튼 스타일 | **`IconTextButtonStyle.Outlined`** | 🔴 이미 인증을 마친 카드라 **주 액션이 아니다.** `Filled` 면 완료 표시보다 버튼이 강조돼 *"아직 인증이 안 됐나"* 로 읽힌다 |
| 아이콘 | `Icons.Filled.PhotoCamera` | "인증하기" CTA 와 동일 — *카메라 아이콘 = 카메라를 여는 버튼* 매핑 유지 |
| 배치 | 사진 **아래**, 간격 **12dp** | 상대 카드 사진 슬롯과 같은 리듬(`PhotoFooterSpacing`) |
| 타이포 | `bold16` | "인증하기" CTA 와 동일 |

🔴 **특히 확인이 필요한 판단**: 완료 뱃지를 **그대로 둔 채** 재촬영 버튼을 얹는 것. "인증 완료" 와
"다시 찍기" 가 한 카드에 같이 있는 조합은 이 앱에 선례가 없다.

### Done 문구 2종 — 🟡 **초안값, 문구 확정 대상**

교체 문구 끝의 마침표를 최초 문구(`…전달돼요.`)에 맞춰 `…보게 돼요.` 로 뒀다. 나란히 놓이는
문구라 통일한 것이며, **확정 시 함께 정해달라.**

---

## 🔬 T-I1 실기 검증 항목 (단위 테스트로 못 잡는다)

캐시는 **실기기 런타임 동작**이다. 아래는 자동화로 갈음할 수 없다.

| # | 항목 | 확인 방법 |
|---|---|---|
| 1 | 내가 교체 → **같은 화면을 벗어나지 않고** 새 사진이 보이는가 | 육안 |
| 2 | 내가 교체 → 화면 나갔다 재진입 → 새 사진이 보이는가 | 육안 |
| 3 | 🔴 **상대가 교체 → 내 화면 재진입 → 상대의 새 사진이 보이는가** | 🔴 **반드시 사람이 육안 확인.** 자동화로 갈음 금지 |
| 4 | 앱 강제종료 → 재실행 → 새 사진이 보이는가 (**디스크 캐시**) | 육안 |

**③ 이 진짜 위험 구간이다** — 내 교체는 로컬 상태가 밀어주지만 **상대 것은 순수하게 캐시 문제**다.

기존 왕복(spec T-I1)도 그대로: 촬영 → 제출 → 상대 알림 1건 → 교체 → **알림이 추가로 오지 않는지** →
상대 화면에 교체된 사진 → 서버 폴더에 이전 파일 없음.

---

## 🔍 방법론 관찰 — `git grep HEAD` vs `git show HEAD:`

`photoDeleted` 필드가 내 작업분인지 확인하려다 겪은 일이다. **두 방향으로 물었더니 답이 갈렸다.**

```
$ git show HEAD:<path> | grep -n "photoDeleted"
(출력 없음, exit 1)          ← 🔴 "HEAD 에 없다" 로 오판하게 만든다

$ git grep -n "myPhotoDeleted" HEAD -- feature/challenge/detail
HEAD:.../contract/ChallengeDetailState.kt:80
HEAD:.../contract/ChallengeDetailState.kt:159
HEAD:.../ChallengeDetailViewModel.kt:172
(외 6건)                     ← ✅ HEAD 에 9곳 있다
```

**`git grep HEAD` 가 맞다.** 이 레포에 이미 기록된 두 교훈이 **겹친 사례**다 —
*"좌표(`git show <hash>:`) 말고 사실(`git grep HEAD`)을 검증하라"* 와
*"셸이 내 문자열을 먼저 읽는다(파이프가 종료 코드를 가로챈다)"*.
`git show | grep` 은 **빈 결과와 실패를 구분해 주지 않아** "없다"는 결론을 조용히 만들어 낸다.

> 📌 이 관찰이 실무로 이어진 건: `photoDeleted` 는 **탈퇴 기능 때 들어온 기존 필드**이고 내
> 작업분이 아니다. 이번에 `VerificationSection` 이 커진 것은 `myVerifiedAt`/`opponentVerifiedAt`
> **두 칸**을 더한 것 때문이며(`git grep HEAD` 로 0건 확인), 그건 T-M4 캐시 키 재료다.

---

## 계약 확인 근거 (T-M2 해제)

pm-lead 정정 기준(**커밋이 아니라 working tree 본문**)으로 실측했다.

| 확인 | 결과 |
|---|---|
| `api-contract.md` L288 | `### 🔴 재제출 정책 — **last-write-wins** (2026-09-02 재정의)` |
| L290 | *"`전면 거부` 는 폐기됐다"* |
| L295 | `이미 VERIFIED (재제출) → ✅ 사진 교체 + verified_at 갱신 + 이전 파일 삭제. 알림을 보내지 않는다` |
| L327 | `#### 🔵 응답을 유실했으면 — **그냥 다시 올린다**` |
| 헤더 | `**최종 수정**: 2026-09-02 by backend-dev` |
| `change-log.md` L88 | *"✅ 앱 해법은 캐시 키 — `photoUrl + verifiedAt` (2026-09-02 확정)"* |

---

## 변경된 파일 — **16 파일 / +456 −249**

```
core/navigation/.../navigation/Route.kt                                    (isReplace 추가)
feature/main/.../feature/main/MainScreen.kt                                (isReplace 전달)

feature/challenge/detail/.../contract/ChallengeDetailState.kt              (T-M1 슬롯 + T-M4 키)
feature/challenge/detail/.../ChallengeDetailViewModel.kt                   (canVerify + verifiedAt)
feature/challenge/detail/.../ChallengeDetailRoute.kt                       (isReplace 산출)
feature/challenge/detail/.../screen/ChallengeDetailScreen.kt               (재촬영 슬롯 + 키 전달)
feature/challenge/detail/.../component/VerificationPhoto.kt                (🔴 ImageRequest + 캐시 키)
feature/challenge/detail/.../component/MissionCard.kt                      (Preview 만)
feature/challenge/detail/.../commonTest/ChallengeDetailViewModelTest.kt

feature/challenge/verify/.../VerifyViewModel.kt                            (🔴 회복 절차 삭제)
feature/challenge/verify/.../VerifyRoute.kt                                (isReplace 배선)
feature/challenge/verify/.../component/VerifyDoneSection.kt                (문구 분기)
feature/challenge/verify/.../contract/VerifyState.kt                       (낡은 KDoc 정정)
feature/challenge/verify/.../commonTest/VerifyViewModelTest.kt
feature/challenge/verify/.../commonTest/FakeVerificationRepository.kt
feature/challenge/verify/.../commonTest/FakeUserInfoRepository.kt          🔴 삭제
```

### 🔴 함께 정정한 낡은 서술 (방치하면 다음 사람이 계약으로 읽는다)

`canVerify` 가 `verifications` 를 안 보게 되면서 *"조회 실패 시 노출 쪽으로 폴백한다"* 계열 서술
**5곳**이 근거 없는 문장이 됐다(폴백이라는 개념 자체가 소멸). 전부 새 사실로 교체했다.
`VerifyState.Confirm` 의 *"제출이 확정되면 되돌릴 수 없으므로(재제출 불가)"* 도 같은 이유로 정정.

⚠️ 그중 2곳은 1차 작성분에서 **"인증 CTA 만 남는다" 로 과잉 단정**돼 있었다(마감 뒤엔 `NONE` 이라
CTA 가 없다). 자체 검토에서 잡아 조건부 사실로 다시 고쳤다.

---

## 미해결 이슈 / 발견한 문제

**1. ✅ 계약이 삭제한 문구가 앱 테스트 픽스처에 남아 있었다 (발견 → pm-lead 승인 → 정리 완료)**

계약 §3 에러표는 `이미 인증을 완료했어요` 를 **취소선 처리**(L433)하고 *"더는 나가지 않는다 — 서버
상수도 제거됐다"* 고 못박았는데, 앱 테스트 5곳이 그 문자열을 예시로 쓰고 있었다.
**테스트 이름은 실행 결과에 찍혀서 읽히므로 픽스처보다 나쁘다** — 문서와 코드가 서로 다른 말을 하는 상태.

| 위치 | before | after |
|---|---|---|
| `VerifyViewModelTest.kt:227` (**테스트 이름**) | `이미 인증을 완료했어요 거부 문구가 와도…` | `거부 문구가 와도 성공으로 해석하지 않는다` (**제거**) |
| `VerifyViewModelTest.kt:229` `Rejected(...)` | `"이미 인증을 완료했어요"` | `"JPEG 사진만 올릴 수 있어요"` |
| `VerifyViewModelTest.kt:236` `assertEquals` 기대값 | 〃 | 〃 |
| `VerificationRemoteDataSourceImplTest.kt:83` `CustomError(700, ...)` | 〃 | 〃 |
| `VerificationRemoteDataSourceImplTest.kt:88` `assertEquals` 기대값 | 〃 | 〃 |

- 대체 문구가 **계약에 살아 있는지 파일로 확인**했다: L435 `| 700 | JPEG 이 아님 (매직 넘버 불일치) | JPEG 사진만 올릴 수 있어요 |`
- 🔴 **동작 단언은 한 글자도 바꾸지 않았다.** `Rejected` 타입 기대, `isRetryable` 단언, 700 → `Rejected`
  매핑 전부 그대로다 — 그게 이 테스트들의 존재 이유다. 바뀐 것은 **무엇을 예시로 쓰는가**뿐이다.
- 227행은 **치환이 아니라 제거**다. 문구가 이름에서 사라져야 목적이 달성된다(그래서 새 문구 grep 은 4곳).
- 검증: `grep -rn "이미 인증을 완료했어요" --include="*.kt" . | grep -v /build/` → **0건**

**2. 🔴 `:remote:datasource` 의 iOS 테스트가 한 번도 컴파일된 적이 없다 (선행 결함, 이번에 드러남)**

픽스처를 바꾼 두 번째 모듈이라 `:remote:datasource:iosSimulatorArm64Test` 를 태스크에 넣었더니
`BUILD FAILED` 가 났다.

```
* What went wrong:
Execution failed for task ':remote:datasource:compileTestKotlinIosSimulatorArm64'
e: ChallengeRemoteDataSourceImplTest.kt:151:9  Name contains illegal characters: ","
e: LoginRemoteDataSourceImplTest.kt:96:9       Name contains illegal characters: ",()"
… 총 15건
```

**Kotlin/Native 는 백틱 테스트 이름에 `,` `(` `)` 를 금지한다.**

🔴 **이번 변경과 무관하다. 근거 4겹:**

1. 에러 난 파일은 `ChallengeRemoteDataSourceImplTest.kt` / `LoginRemoteDataSourceImplTest.kt` **둘뿐** —
   이번에 건드리지 않은 파일이다
2. 이번에 고친 `VerificationRemoteDataSourceImplTest.kt` 의 에러 **0건**
3. 문제 이름들이 **HEAD 에 이미 있다**:
   ```
   $ git show HEAD:.../LoginRemoteDataSourceImplTest.kt | sed -n '37p;96p'
   fun `loginWithTestAccount 성공 - LoginResult emit, 요청 body 일치`()
   fun `loginWithTestAccount 비즈니스 에러(CustomError 700) - onError 1회, onUnsupported 0회`()
   ```
4. 🔑 **결정적 증거** — `remote/datasource/build/test-results/` 에 `testDebugUnitTest` ·
   `testReleaseUnitTest` 만 있고 **iOS 디렉터리가 아예 없다.** 한 번도 돈 적이 없다는 뜻이다.

**즉 이 모듈의 iOS 검증 커버리지가 0 이다.** 없던 타겟을 불러서 드러난 것이지 이번에 깨뜨린 것이 아니며,
**안 불렀으면 계속 안 보였을 결함**이다.

🔵 **다른 모듈들은 이미 이 제약을 지키고 있다** — 이번에 추가한 테스트들도 그래서 백틱 이름에서
`,` `(` `)` 를 뺐다(예: `Unreachable 이면 현황 조회 없이 재시도 가능한 실패를 표시한다`).
**이 모듈만 예외로 남은 것으로 보인다.** 다음 사람이 *"왜 여기만 다르냐"* 를 묻지 않도록 남긴다.

🟡 **백로그**: 고치려면 기존 테스트 이름 15개+ 를 개명해야 해 **이번 범위 밖.** pm-lead 가 백로그로 받았다.
`:remote:datasource:testDebugUnitTest`(Android)로 재실행했고 그것이 이번에 바꾼 파일을 덮는다.

**3. 🟡 `MissionCardMineFailedPreview` 가 나올 수 없는 화면을 그린다 (선행 이슈, 미수정)**

KDoc 이 *"`FAILED` — CTA 는 그대로 열려 있다"* 라며 재시도 버튼을 그리는데, `myMissionSlot` 은
`FAILED` → `NONE` 이라 화면에서는 슬롯이 통째로 빠진다. challenge-verification 때부터 어긋나 있었다.
pm-lead 판정: **현재 코드가 옳고 Preview 가 낡았다. `FAILED` 에 재시도를 열지 않는다**
(`ai-verification` 이 자정 배치 판정이라 `FAILED` 시점엔 이미 마감 — 재시도 창이 없다).
**이번 범위 밖이며 백로그에서 처리한다.**

**4. 🔵 재촬영 진입점은 단일 경로다** — `Route.Challenge.Verify` 로 가는 곳은
`ChallengeDetailRoute.onVerifyClick` 하나뿐임을 grep 으로 확인. 놓친 진입점 없음.

---

## Working tree 상태

- **작업 브랜치: `main`** — 기존에 체크아웃돼 있던 브랜치다. **새로 만들지 않았다.**
- 변경분은 **unstaged 그대로** 뒀다. **커밋·푸시·PR 생성 안 함** (사용자 처리 영역).
- `challenge-app` 트리는 이 작업 단독 공간이었다(pm-lead 확인). 다른 에이전트와의 충돌 없음.

## API 계약 대비 구현 차이

**없다.** 요청/응답 shape 무변경(계약 §3 *"응답 shape 은 첫 제출과 완전히 같다"*).
DTO·엔드포인트·파라미터 전부 그대로다.

바뀐 것은 **같은 요청에 대한 서버의 행동**(거부 → 교체)과 그에 딸린 **앱의 절차·표시·캐시**뿐이다.

## 참조

- [spec.md](spec.md) §4 T-M1·T-M2·T-M3·T-M4
- [challenge-verification/api-contract.md](../challenge-verification/api-contract.md) §3(재제출·재시도 판정) · §5(캐시)
- [challenge-verification/change-log.md](../challenge-verification/change-log.md) — 2026-09-02 개정
- [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md) — `verifiedAt` 초 단위의 근거
