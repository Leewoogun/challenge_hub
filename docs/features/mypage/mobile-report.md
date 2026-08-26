# Mobile Report — mypage

- **작성**: 2026-08-26 mypage-mobile
- **상위**: [spec.md](./spec.md) · [api-contract.md](./api-contract.md) (`confirmed`) · [design.md](./design.md)

## 구현 요약

| 태스크 | 상태 |
|---|---|
| T-M1 프로필 카드 + 마이페이지 골격 | ✅ 완료·검증 |
| T-M2 로그아웃 실구현 | ✅ 완료·검증 |
| T-M3 계약서 보관함 화면 | ✅ 완료·검증 |
| T-M4 회원탈퇴 플로우 (+ `photoDeleted`) | ✅ 완료·검증 |
| T-M5 테스트 | ✅ failures=0 (아래 표) |

마이페이지가 `PlaceholderScreen` 에서 실제 화면이 됐고, **로그아웃이 처음으로 서버에 도달**한다.
계약서 보관함이 신설되어 **홈 7일 노출이 지난 결과에도 도달**할 수 있다(백로그 "결과 히스토리 화면
부재" 해소 조건).

## 사용한 모바일 레포 스킬

- `/viewmodel` — `MyPageViewModel` StateFlow 파이프라인(`triggerStateIn` + `combine`)
- `/domain` — `GetMyPageDataUseCase` · `WithdrawUseCase` · `LogoutReason`
- `/data-remote` — `logout` · `withdraw` 배선(Api → RemoteDataSource → Repository)
- `/feature` — 마이페이지 화면·컴포넌트
- `design-system` (자동 적용) — 토큰·프리뷰 규칙

## 🔴 이 작업의 핵심 발견 — `WWW-Authenticate` 없이도 Ktor 자동 갱신이 돈다

계약 §3 이 *"Ktor 자동 갱신이 이 헤더를 필요로 한다는 결론이 나오면 `UnauthorizedEntryPoint` 에
추가한다 — **모든 401 의 전역 변경**이라 mobile 확인 전에는 넣지 않는다"* 로 mobile 회신을 대기하고
있었다. **실측으로 답했다: 필요 없다. 서버 변경 0건.**

프로덕션 인증 설정을 `MockEngine` 에 그대로 태우는 특성화 테스트를 신설해 확인했다.

| 테스트 | 결과 |
|---|---|
| 401 + `WWW-Authenticate: Bearer` → 갱신 후 원 요청 재시도 | ✅ pass |
| 🔴 401 에 헤더 **없어도** 갱신이 시도된다 | ✅ **pass** |

코드 근거도 일치한다 — `ktor-client-auth 3.3.1` `Auth.kt` `findProvider` 에
`authHeaders.isEmpty() && candidateProviders.size == 1 -> candidateProviders.first() to null` 분기가
있고, 이 앱은 프로바이더가 `bearer` 하나뿐이라 이 경로를 탄다. **우연이 아니라 후보가 하나인 한
구조적으로 돈다.** ⚠️ 그 전제(프로바이더 1개)가 깨지면 헤더가 필요해지며, 위 테스트 2건이 그 순간
빨갛게 터지도록 박제해 뒀다.

RFC 9110 §15.5.2 위반은 남지만 **동작을 위해 전역 401 을 건드릴 이유는 사라졌다.** 규격 정합은
별건으로 백로그 대상.

## 변경된 파일

### T-M1 — 프로필 카드 + 골격

- `domain/model/.../MyPageData.kt` (신규) — `record: UserRecord?` + `userInfo: UserInfo?`
- `domain/usecase/.../GetMyPageDataUseCase.kt` (신규) — `combine`. 🔴 **두 소스 모두 `onEmpty` 폴백** —
  없으면 한쪽 실패가 화면 전체를 `Loading` 에 영구히 가둔다
- `feature/mypage/.../contract/MyPageState.kt` — `Data(record, userInfo, isWithdrawing)` + `recordSummary`
- `feature/mypage/.../MyPageViewModel.kt` — `triggerStateIn(WhileSubscribed(0))` (탭 복귀 시 전적 재조회)
- `feature/mypage/.../MyPageRoute.kt` — `ChallengeScaffold` + `ChallengeTopBar(titleStyle = bold20)`
- `feature/mypage/.../MyPageScreen.kt` — `Column(verticalScroll)` 골격
- `feature/mypage/.../component/ProfileCard.kt` (신규) — 아바타 64dp/**radius 20dp**, 승=`primary`
- `feature/mypage/.../component/MyPageMenuCard.kt` (신규) — 목록 전제로 파라미터화
- `data/repositoryImpl/.../di/UseCaseModule.kt` — UseCase 등록
- `feature/mypage/build.gradle.kts` — `compose.materialIconsExtended` + commonTest 의존

### T-M2 — 로그아웃

- `remote/network/.../auth/ChallengeAuth.kt` (신규) — `install(Auth)` 블록을 추출(동작 무변경).
  🔴 `sendWithoutRequest` 술어를 **공개 3경로 allowlist** 로 교체
- `remote/network/.../di/KtorfitModule.kt` — 한 줄 호출로 축약
- `remote/model/.../auth/LogoutResponse.kt` (신규) — `data` 키 없음
- `remote/api/.../LoginApi.kt` — `@DELETE("api/v1/auth/logout")` + *"공개 엔드포인트"* KDoc 정정
- `remote/datasource/.../LoginRemoteDataSourceImpl.kt` · `data/datasource/.../LoginRemoteDataSource.kt` ·
  `domain/repository/.../LoginRepository.kt` · `data/repositoryImpl/.../LoginRepositoryImpl.kt` — 배선
- `domain/model/.../LogoutReason.kt` (신규) — `USER` / `SESSION_EXPIRED` / `WITHDRAWN`
- `domain/usecase/.../LogoutUseCase.kt` — `invoke(reason)`
- `domain/usecase/.../LoginWithTestAccountUseCase.kt` — `LogoutReason.USER` 전달
- `feature/main/.../MainViewModel.kt` — `merge` 에 이유를 실어 보냄

### T-M4 — 회원탈퇴

- `core/ui/.../ConfirmDialog.kt` (신규) — `destructive: Boolean` 하나로 색 판정
- `feature/mypage/.../component/WithdrawText.kt` (신규) — `onSurfaceVariant`, 세로 패딩으로 48dp 터치 타깃
- `remote/model/.../user/WithdrawResponse.kt` · `remote/api/.../UserApi.kt` (`@DELETE api/v1/users/me`)
- `data/datasource/.../WithdrawRemoteDataSource.kt` · `remote/datasource/.../WithdrawRemoteDataSourceImpl.kt` ·
  `domain/repository/.../WithdrawRepository.kt` · `data/repositoryImpl/.../WithdrawRepositoryImpl.kt` (전부 신규)
- `domain/usecase/.../WithdrawUseCase.kt` (신규)
- `core/navigation/.../MainAction.kt` — `fun withdrawn()`
- `feature/main/.../MainScreen.kt` · `MainViewModel.kt` — `withdrawn` 배선

### T-M3 — 계약서 보관함

- `domain/model/.../challenge/ChallengeHistory.kt` (신규) — `myResult: ChallengeOutcome` non-null
  (기존 `Outcome` 타입 재사용, 새 매핑 만들지 않음)
- `remote/model/.../challenge/ChallengeHistoryResponse.kt` · `remote/mapper/.../ChallengeHistoryResponseMapper.kt` (신규)
- `remote/api/.../ChallengeApi.kt` — `@GET("api/v1/challenges/history")`
- `remote/datasource` · `data/datasource` · `domain/repository` · `data/repositoryImpl` — `getChallengeHistories` 배선
- `domain/usecase/.../GetChallengeHistoriesUseCase.kt` (신규)
- `feature/mypage/.../ArchiveRoute.kt` · `ArchiveScreen.kt` · `ArchiveViewModel.kt` ·
  `contract/ArchiveState.kt` · `contract/ArchiveEffect.kt` · `ArchivePreviewFixtures.kt` (전부 신규)
- `feature/mypage/.../component/ArchiveMonthHeader.kt` · `ArchiveChallengeCard.kt` (신규)
- 🔴 `feature/home/.../component/BetStrip.kt` → **`core/ui/.../components/BetStrip.kt`** (`git mv`).
  `internal` → `public`, **렌더 코드 무변경**. KDoc 의 *"홈 카드 2곳이 공유한다"* 문장도 함께 정정 —
  안 고치면 다음 사람이 또 사본을 뜬다
- `core/navigation/.../Route.kt` — `Route.Archive` + `routeSerializersModule` 등재
- `feature/main/.../MainScreen.kt` — `entry<Route.Archive>` 등록
  (`feature/main/build.gradle.kts` 는 `:feature:mypage` 가 이미 의존성에 있어 변경 없음)
- `feature/{home,challenge/detail,challenge/oath,challenge/create}` 의 `FakeChallengeRepository` +
  `remote/datasource` 의 `FakeChallengeApi` — 신규 인터페이스 멤버 스텁

## 🔴 T-M2 의 세 가지 계약 — 테스트로 고정했다

1. **서버 호출은 `clearTokens()` 앞.** 뒤에 두면 토큰이 없어 401 → refresh 실패로 **정상적인 계정
   전환이 "세션 만료"로 반응**한다. → `listOf("logout", "clearTokens")` 순서를 단언
2. **서버 실패를 삼키고 로컬 정리는 반드시 수행.** 서버가 죽었다고 사용자를 로그인 상태에 가둘 수
   없다(계약의 *"멱등 성공"* 철학). 단 `CancellationException` 은 재던진다 —
   `PhotoCompressor.android.kt:52` 의 레포 관례
3. **`SESSION_EXPIRED` 는 서버를 부르지 않는다.** `MainViewModel` 이 자동/수동 로그아웃을 한 흐름에
   합쳐 놔서, 만료 경로에서 서버를 부르면 401 → refresh 실패 → `emitSessionExpired()` → **같은
   merge 흐름에 재진입**한다

### `sendWithoutRequest` 술어를 왜 allowlist 로 바꿨나

기존 `pathSegments.none { it == "auth" }` 는 `/auth/logout`(Bearer **필수**)까지 걸러 토큰을 안 붙였다.
그리고 이건 "토큰이 안 붙는다"에서 끝나지 않는다 — `ktor-client-auth` 의 `refreshTokenIfNeeded` 는
**토큰이 선제 부착된 요청만** 갱신 대상으로 삼으므로, 401 을 받아도 **자동 갱신조차 돌지 않았다.**

allowlist 방향을 고른 이유는 **실패 방향이 안전**하기 때문이다 — 새 공개 엔드포인트를 빠뜨리면 공개
API 에 토큰이 붙을 뿐(무해)이지만, 차단목록 방식은 보호된 API 에서 토큰이 빠져 **조용히 401** 이 된다.
`/auth/refresh` 가 목록에 남아야 하는 것도 고정했다(만료 토큰으로 갱신을 시도하면 재귀).

## 테스트 결과 — 실측 XML (최종, `GRADLE_EXIT=0` · BUILD SUCCESSFUL)

| 모듈 | Android | iOS | XML timestamp (UTC) |
|---|---|---|---|
| `:remote:network` | 23 | 23 | 07:55:31 / 07:58:39 |
| `:remote:mapper` | **120** | **120** | 08:10:10 / 08:10:12 |
| `:remote:datasource` | 32 | — | 07:58:37 |
| `:data:repositoryImpl` | 15 | — | 07:58:40 |
| `:core:ui` | 4 | 4 | 07:54:03 / 07:54:35 |
| `:feature:main` | 17 | 17 | 07:55:04 / 07:55:19 |
| `:feature:login` | 15 | — | 07:55:27 |
| `:feature:home` | 24 | 24 | 07:54:32 / 07:54:34 |
| `:feature:mypage` | **30** | **30** | 08:30:30 / 08:30:32 |
| `:feature:challenge:detail` | **45** | **45** | 08:09:52 / 08:09:54 |
| `:feature:challenge:verify` | 25 | (미실행) | 08:10:09 |
| **합계** | **346** | **259** | 전부 `2026-08-26` |

`photoDeleted` 반영 후 재측정: `:feature:challenge:detail` **41 → 45**(신규 4, 회귀 0, Android·iOS 동일),
`:remote:mapper` **116 → 120**. pm-lead 가 건 조건(*"기존 41건 전량 회귀 확인"*) 충족.

`failures=0 errors=0 skipped=0`. `:composeApp:compileDebugKotlinAndroid` 성공.

⚠️ **stale 1건 — 숫자에서 제외했다.** `:feature:challenge:verify` 의 **iOS** XML 은 `2026-08-18` 자로
이번 실행분이 아니다(태스크 목록에 넣지 않았다). 그 모듈은 이번에 **테스트 fixture 2줄만** 바뀌었고
Android 25건은 fresh 하게 통과했다.

⚠️ `:feature:main` 의 iOS XML 은 작업 **시작 시점에 `2026-08-08` 자 stale** 이었다 — 이번 작업으로
갱신됐음을 확인했다. 원래 stale 이던 것을 되살린 사례다.

🔴 **검증 과정에서 오탐 2건을 잡았다.**
1. `./gradlew ... | tail -80` 로 돌렸더니 셸이 **`tail` 의 exit code** 를 반환해 **실패한 빌드가
   성공으로 보였다.** XML timestamp 가 실행 시각보다 과거인 것으로 발각했다(실제로는
   `ChallengeAuth.kt:94 Unresolved reference 'encodedPath'` — Ktor 3.3.1 `URLBuilder` 에 없는 프로퍼티).
   **gradle 을 파이프에 물리지 말 것.**
2. 첫 T-M3 실행이 `:feature:mypage` 에서 먼저 실패해 **뒤쪽 모듈의 컴파일 에러가 가려졌다**
   (`FakeChallengeApi` 가 신규 `getChallengeHistories` 미구현). 모듈 하나가 실패하면 나머지는
   검증되지 않은 것으로 취급해야 한다.

### 🔴 `kotlin.math.round` 는 은행가 반올림이다 — 테스트가 design 의 서술 오류를 잡았다

design.md §1.2.5.2 가 요구한 반올림 회귀 테스트(`5승 3패` → 5/8 = 62.5% → **63%**)가 **실패**했다.
원인은 같은 절의 서술이 사실과 달랐던 것 —

> ⚠️ Kotlin `round()` 는 `.5` 를 가장 가까운 짝수가 아니라 위로 보내므로 `Math.round` 와 같다

`kotlin.math.round` 는 **ties-to-even** 이라 `round(62.5) == 62.0` 이다. 서버가 쓰는
`java.lang.Math.round(double)` 은 **`floor(x + 0.5)`** 로 정의돼 `63` 이다. **둘이 다르다.**

→ 구현을 `floor(win * 100.0 / total + 0.5).toInt()` 로 고쳤다. **테스트가 옳았고 문서가 틀렸다** —
design.md §1.2.5.2 의 해당 ⚠️ 문장은 정정 대상이다.

## Working tree 상태

- **작업 브랜치**: `main` (현재 체크아웃된 브랜치. 새로 만들지 않았다)
- **변경분**: staged/unstaged 그대로. **커밋·푸시·PR 생성 안 함** — 사용자 처리 영역

## `photoDeleted` — 탈퇴자 인증 사진 (pm-lead 판정으로 T-M4 범위 확정, 완료)

`photoDeleted: Boolean`(additive·non-null·기본 `false`)을 DTO → 도메인 → 매퍼 → 화면까지 배선하고,
`VerificationPhoto` 의 `when` 에 분기를 **하나 추가**했다.

```kotlin
photoDeleted -> PhotoMessage(PHOTO_DELETED_TEXT)      // 신규 — "탈퇴한 사용자의 사진은 삭제됐어요"
photoUrl == null -> PhotoMessage(LOAD_FAILED_TEXT)    // 🔴 유지
```

🔴 **`photoUrl == null` 분기를 지우지 않은 것이 이 작업의 핵심이다.** 그 자리는 *"인증은 됐는데 URL 이
없는 비정상"* 을 잡으려고 일부러 만든 **감지기**다. 두 신호를 한 문구로 합치면 **URL 유실 버그가
탈퇴자 뒤에 영영 숨는다.** `photoDeleted == false` 인데 URL 이 null 이면 여전히 기존 문구가 나온다.

- **`PhotoRetryMessage` 가 아니라 `PhotoMessage`** — 삭제는 영구 상태라 재시도할 대상이 없다.
- `FAILED` 분기가 새 분기보다 **위**라, 서버 실측의 `FAILED + photoDeleted` 조합도 기존 문구를 유지한다.
- DTO 필드에 **기본값 `false`** 를 줬다 — 서버가 아직 안 내리는 환경에서 `MissingFieldException` 이 난다.
- 프리뷰 4종(사진 / 삭제됨 / **URL 유실** / 미인증)으로 ②와 ③이 다른 문구인지 눈으로 고정했다.

## 보관함 조회 실패 — 인라인 실패 카드 + 두 실패 경로 분리 (design §2.5.4.1, 완료)

초판 §2.5.4 의 *"스낵바 + 로딩 직전 상태 유지"* 는 첫 진입에서 **유지할 상태가 없어 무한 스피너**가
됐다(§1.7.2 가 마이페이지에서 기각한 바로 그 상태). design 이 판정을 뒤집어 **인라인 실패 카드 +
"다시 시도"** 로 확정했고 그대로 구현했다.

`EmptyStateCard` 골격 재사용, 값만 교체 — `CloudOff` / `"보관함을 불러오지 못했어요"` /
`"잠시 후 다시 시도해주세요"` / `"다시 시도"` + `Refresh` → `uiState.restart()`.
🔴 **재시도 버튼이 여기엔 필수다** — 마이페이지에서 뺀 사유(*"탭이라 재진입이 재시도"*)가 **push 하위
화면엔 성립하지 않는다.** 뒤로 가는 순간 실패했다는 사실도 화면과 함께 사라진다.
🔴 **아이콘을 `Description` 으로 두지 않았다** — 빈 상태와 구분이 안 된다.

**실패를 상태로 만든 방식**: `onEmpty { emit(Failure) }` + 그 **바깥**의 `onStart { emit(Loading) }`.
⚠️ `onStart` 가 `onEmpty` **안쪽**이면 `Loading` emit 이 "비어있지 않음"으로 세어져 `Failure` 가
영원히 안 나온다 — 바깥에 둔 것이 핵심이다.

### 🔴 두 실패를 갈랐다 — `onError` 하나가 서로 다른 두 사건을 나른다

`ChallengeRemoteDataSourceImpl.getChallengeHistories` 실측(40~51행):

```kotlin
if (mapped.droppedCount > 0) onError("일부 항목을 불러오지 못했어요")  // 부분 실패: onError 후 emit 이 온다
this@flow.emit(mapped.items)
.suspendOnFailureWithErrorHandling(onError)                          // 전체 실패: emit 이 없다
```

**`onError` 자체로는 구분되지 않는다. 판별자는 "emit 이 뒤따르는가" 다.**

| 사건 | 표현 |
|---|---|
| 전체 실패 (emit 없음) | 실패 카드, **스낵바 없음** |
| 부분 실패 (목록은 오고 몇 건 드롭) | **목록 + 스낵바 병행** |

design 이 세운 규칙(*"실패 표시가 주 내용을 차지하면 생략, **부분 표시면 병행**"*)을 그대로 적용한
것이다 — 규칙을 바꾼 게 아니다. pm-lead 승인.

이 구분이 필요한 이유는 T-M3 의 드롭 정책과 맞물린다 — 보관함 매퍼는 `challengeDate`·`myResult` 를
못 읽으면 **항목을 버린다**(홈과 반대). **드롭을 정당화한 논리가 곧 드롭이 실제로 일어난다는 뜻**인데,
알림이 없으면 목록은 정상으로 보이면서 몇 건이 조용히 빠진다. §2.5.2.1 의 신호 분리와 같은 결이다.

구현: `flow { }` 빌더 **람다 안 지역 변수**에 메시지를 보류하고, `collect` 람다(= emit 이 일어나는
지점)에서 flush → 부분 실패. `onEmpty` 는 보류분을 버리고 `Failure` 만 낸다 → 전체 실패.
🔴 **보류 상태가 수집 단위여야 한다** — ViewModel 프로퍼티면 `retry()` 재수집 때 **이전 실패
메시지가 새어 나온다.** `flow { }` 지역 변수라 재수집이 블록을 처음부터 다시 실행해 살아남을 경로가
구조적으로 없다. 그 누수를 막는 회귀 테스트를 넣었다.

🔴 **`ArchiveRoute` 에 `uiEffect` 수집이 아예 없었다** — 이펙트를 흘려도 스낵바가 뜨지 않는 상태였다.
`LocalMainAction.showSnackBar` 로 연결했다(`RankingRoute`·`MyPageRoute` 와 동일 패턴).

## 미해결 이슈

1. **로컬 정리가 두 번 탄다** — `WithdrawUseCase` 가 `logoutUseCase(WITHDRAWN)` 을 부르고,
   `MainViewModel.withdrawn()` 도 같은 정리를 탄다. 멱등이라 무해하지만 소유자가 둘이다
4. **실기 검증 없음** — 로그아웃이 서버 `fcm_token` 을 실제로 NULL 로 만들어 *"그 기기로 푸시가 더
   안 온다"* 는 수용 기준은 **실기로만 확인 가능**하다. 탈퇴·보관함 플로우도 동일
5. **문구 미확정** — design §6 의 디자이너 확인 대상(승/패/무 색, 빈 상태 문구, 탈퇴 문구·색·배치,
   탈퇴 다이얼로그 본문 등)이 전부 "제안" 상태로 구현돼 있다

## T-M3 구현 시 내린 판단 (design.md 반영 필요)

1. **신규 route 이름 = `Route.Archive`** (평탄한 `data object`). `:feature:mypage` 가 하위 모듈로
   나뉘지 않은 단일 모듈이라 `Route.kt` 주석의 *"중첩은 하위 모듈로 나뉜 feature 만"* 규칙을 적용
2. **`stickyHeader` 를 썼다** (일반 `item` 으로 내리지 않음)
3. **월 헤더의 좌우 gutter 를 `contentPadding` 이 아니라 컴포넌트가 직접 낸다.** §2.3 도식대로
   `contentPadding(horizontal = 20.dp)` 을 주면 **sticky 헤더 배경이 gutter 만큼 좁아져 좌우로
   카드가 비친다** (§2.3.2 가 Lovable 의 `-mx-5 px-6` 로 지적한 것과 같은 문제)
4. **매퍼 드롭 정책이 홈과 반대다.** 홈은 모르는 `myResult` 를 null 로 흡수하고 카드를 살리지만,
   보관함은 `challengeDate`·`myResult` 중 하나라도 못 읽으면 항목을 드롭한다 — §2.4.2 가
   "결과 pill 항상 non-null" 을 전제하고 날짜가 월 그룹 키라 둘 다 없으면 그릴 자리가 없다
5. **`toArchiveMonths` 가 `challengeDate` 내림차순 정렬을 한 번 더 한다.** 레포 관례는
   *"정렬은 서버 책임"* 이지만, 그룹핑은 순서가 어긋난 응답에서 **같은 월 헤더가 두 번 나오는
   형태로 깨진다** — 목록 순서가 바뀌는 것과 다른 급이라 방어했다

## API 계약 대비 구현 차이

**없음.** 계약 `confirmed` 3종을 그대로 따랐다. 다만 계약 협의 과정에서 mobile 이 요구했다가
**철회한 것 1건**: `GET /record` 에 `winRate`·`totalChallenges` 추가. design 이 *"loser-ranking 에서
재계산을 막은 이유는 서버가 그 정수를 정렬 3차 키로도 쓰기 때문이고 여기엔 정렬이 없다"* 로
반박했고 타당해 철회했다 — **`GET /record` 계약 변경 0 유지.**

## design.md 에 반영이 필요한 것 (구현이 문서를 앞선 지점)

1. **§3.2 `ProfileCard` 시그니처** — 문서는 "개별 `Int` 3개"(원래 mobile 제안)인데, §1.7.3 의
   *"전적 실패를 0 과 구분"* 요구를 타입으로 강제하려고 **`record: UserRecord?` 하나**로 바꿨다.
   `Int` 3개면 `win = 0` 을 넘기는 경로가 컴파일된다. CLAUDE.md *"파생값이 없으면 도메인 모델을
   그대로 UiState 에 담는다"* 와도 이쪽이 맞는다
2. **탈퇴 다이얼로그를 별도 컴포넌트로 만들지 않았다** — §3.2 신규 목록에 없어
   `MyPageRoute` 에서 `ConfirmDialog` 를 직접 호출하고 문구는 같은 파일 `private const` 로 뒀다
