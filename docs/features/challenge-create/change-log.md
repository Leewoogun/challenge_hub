# Change Log — challenge-create

스펙·계약이 확정된 뒤 바뀐 것들. 각 항목은 **누가 무엇을 근거로 뒤집었는지**를 남긴다.

## 2026-07-31

- **spec.md**: 상태 `in-progress` → `completed`. #7(통합 검증)이 실서버 58/58 PASS로 마감.
- **backend-report.md**: 미해결 이슈 1(end-to-end 미검증) → **해소**. 이슈 6.5(잘못된 요청 본문 500) / 6.6(`/actuator/health` 500) **신규 추가** — #7 검증 중 발견된 기존 동작이며 challenge-create가 만든 문제가 아니다.
- **backlog.md**: `/actuator/health` 500 등재. 컨테이너 런타임 부재를 🔴로 통합 등재(기존 24 + 신규 21 = 45건 누적).

## 2026-07-28

### 스코프 — 보낸 도전장 목록 제외 (옵션 C, 사용자 결정)

- **제기**: backend-dev가 착수 전 **스펙 갭** 발견 — `DELETE /challenges/{id}`는 `challengeId`를 요구하는데 챌린저가 자기 `PENDING` 챌린지를 나열할 경로가 없다(`/received`는 opponent만, `/active`는 `IN_PROGRESS`만). 시나리오 4가 앱 재시작 후 성립하지 않는다.
- **결정**: **C — 범위 유지, 백로그 강등.** 서버 비용은 `/received` 대칭이라 거의 0이지만 실제 비용이 design(섹션 +1)과 모바일(T-M5 +25%, 홈 `combine` 소스 4→5)에 쏠려 임계 경로가 늘고, 이미 등재된 "`HomeViewModel` 기존 10건 회귀 0" 리스크를 압박한다. 핵심 검증 목표(생성→수락→홈 노출)는 C로 온전히 달성된다.
- **(B) 기각 근거** (mobile-dev): `/pending` + `direction` 통합 시 방향별 표시 필드가 달라(RECEIVED=상대 닉네임·상대 미션·수락/거절, SENT=내 미션·취소) 한 DTO에 합치면 **모바일의 전 필드 기본값 방어 패턴 탓에 잘못된 방향 필드를 읽어도 컴파일·런타임 모두 조용히 통과한다.**
- **반영**: spec 시나리오 4 취소선 + 스코프 결정 6 신설, 취소 수용 기준을 "서버 테스트로만 검증 · #7 대상 아님"으로 한정, 비범위 추가, 백로그 등재. **코드 변경 0** — backend-dev가 "결정 전까지 계약대로만 구현한다"는 원칙을 지켜 재작업이 없었다.

### spec 태스크 정정 — 레포 실상과 어긋남 (mobile-dev 제기)

- **T-M3 컴포넌트 배치**: `:core:designsystem` → **feature 모듈**. 초안대로면 커밋 `72d9d9c "fix: feature component가 디자인시스템 모듈에 있던 문제 수정"`(사용자 작업)을 되돌린다. design-bridge가 독립적으로 같은 결론에 도달했고, `:core:designsystem`이 `:core:utils`만 의존해 `:domain:model`의 `DeadlineType`을 못 받는다는 근거를 추가했다.
- **T-M4 범위 축소**: "모듈 신설 + Navigation 연결"이 커밋 `be324b9`로 **이미 완료** 상태였다. 남은 건 스텁 6파일 교체뿐이고 `generate-feature.sh` 실행은 불필요. 모듈 경로도 `:feature:challenge` → **`:feature:challenge:create`**(중첩) 정정.
- **`repos.json`**: `mobile.modules`를 `settings.gradle.kts` 실측으로 갱신(`:feature:friends:list/search`, `:feature:challenge:create`, `:local:*`, `:core:ui`, `:feature:splash` 반영). base URL blocker도 "이미 challenge 서버 기준, TMDB 흔적 0건"으로 정정.

### api-contract — 모바일 error-channel 제약 반영 (draft → negotiating → confirmed)

- **L229 문구 정정**: "705면 다이얼로그 + 확인 시 재조회" → **삭제.** `suspendOnFailureWithErrorHandling(onError: (String) -> Unit)`이 `CustomError.code`를 버리는 게 5개 Repository 공통 표준(`faae2cd`)이라 **모바일은 700/705를 구분할 수 없다.** 전 Repository + 테스트 27건 리팩터는 범위 밖. 서버 배분은 의미대로 유지하고 모바일 동작을 "실패 시 코드 무관 스낵바 + 목록 항상 재조회"로 확정 — **기능 손실 0.**
- **부수 결정**: `message`가 곧 UI 텍스트이므로 **모든 에러 문구를 확정 문구화**하고 슬라이스가 글자 단위로 검증. `권한이 없어요` → `내가 받은/보낸 도전장이 아니에요`.
- **중복 메시지 2종 분기** (backend-dev 제안): 역방향 `PENDING`인데 "이미 진행 중인 챌린지가 있어요"라고 하면 홈 진행중 목록이 비어 있어 사용자가 버그로 오인한다.
- **`challengeDate` 평문 ISO date 강제 + `@JsonFormat` 명시**: Jackson 기본 직렬화가 `[2026,7,28]` 배열이라 회귀 방지. **`deadline`/`createdAt`은 `Z` suffix 고정 + 초 절삭** — 파싱 실패 시 `Instant.DISTANT_PAST` 폴백이라 **조용히 "마감된 카드"가 된다.**
- **DELETE에 `data.challengeId` 추가**: friends `CancelFriendRequestResponse`와 shape 통일.

### V5 범위 확대 — 부분 유니크 인덱스 (backend-dev 제기, 승인)

- T-B1 원래 범위는 `opponent_mission` NULL 완화뿐이었으나 `uq_challenges_active_pair_date`를 추가했다.
- **근거**: 수용 기준의 중복 금지는 **단정문이지 best-effort가 아니다.** Postgres READ COMMITTED에서 미커밋 INSERT가 동시 트랜잭션에 보이지 않아 애플리케이션 사전 검사만으로는 두 요청이 나란히 통과한다. 계약 초안의 "인덱스가 없으므로 앱 레벨 검사 권장" 문구는 **초안의 한계였지 결정이 아니었다.**

### design.md v1 → v2 → v3 — 수락 UI 2회 번복

- **v1 → v2 (바텀시트 → 다이얼로그)**: mobile-dev의 플랫폼 제약 지적을 design-bridge가 검증한 결과 **v1의 1순위 근거("시트가 IME에 유리")가 반대**였다. `ModalBottomSheet` 사용처 **0건**(grep 확인), CMP 1.10.3 시트+`TextField`의 iOS IME 리스크, `MainScreen.kt:142`의 기존 `imePadding()`, 입력 필드 1개.
- **v2 → v3 (근거 1건 무효화)**: v2가 결정적 근거로 삼은 "705 확인 다이얼로그가 어차피 필요하니 시트까지 넣으면 오버레이 프리미티브 2개" — **계약 확정으로 전제가 무너졌다.** 모바일이 `code`를 소비하지 않으므로 705 전용 다이얼로그 자체가 없다. → **`ChallengeErrorDialog` 폐기**, §3.3의 700/705 2행을 "실패(코드 무관)" 1행으로 통합. **결론(다이얼로그)은 나머지 근거로 유지**되며, 오히려 신규 오버레이가 1개로 줄어 단순해졌다.
- **v1 명세 오류 정정** (구현 전 발견): `toRelativeKoreanString()`이 `"곧 마감"`/`"마감"`도 반환하는데 v1이 `" 남음"` 접미사를 지시해 **"곧 마감 남음"**이 될 뻔했다.
- **추가 명세**: `DeadlineSelector`에 실제 마감 시각 부기(mobile-dev 제안 채택 — spec 결정 3의 "심야 생성 방지" 취지가 실제 시각 없이는 죽는다), 마감 임박 강조를 **잔여 1시간 경계**로(3시간이면 목록 대부분이 강조돼 강조가 죽는다), step1 CTA disabled를 **trim 기준**으로(기존 `!myMission || !bet`은 공백만 넣어도 통과해 서버 700).
- **step2(영혼의 맹세) 마감 표시 바인딩 1줄 수정** — "step2를 건드리지 마라"의 의도는 **범위 밖이라고 삭제·축소하지 말라**는 것이었고, T-D1이 만든 표시 모순(step1에서 "내일 자정"을 골라도 계약서엔 "오늘 자정")을 T-D1이 닫는 건 그 취지에 어긋나지 않는다.

### 구현 중 발견 — `combine` 실패 전파 (mobile-dev, 승인)

- `GetHomeDataUseCase`가 `combine`으로 소스를 합치는데 `combine`은 **모든 소스가 1회 이상 emit해야** 결과를 낸다. 실패 시 emit 없이 `onError`만 부르는 표준 패턴이라, 받은 도전장을 4번째 소스로 그냥 추가하면 **조회 실패가 홈 전체를 백지로 만든다**(기존 테스트 2건이 이 동작을 고정 중).
- → 받은 도전장 소스만 `.onEmpty { emit(emptyList()) }`로 격리. 같은 함정이 **위저드의 친구 목록**에도 있어 `loadFailed` 플래그로 Empty/Error를 구분해 동일 처리.
- **`HomeViewModelTest` 기존 10건에 `uiState` 구독 1줄 추가** — `WhileSubscribed(0)`이라 구독자가 없으면 파이프라인이 시작되지 않아 "record 실패 → Loading 유지" 케이스가 **공짜로 통과**하고 있었다. 단언 약화가 아니라 **강화**다.

### 모바일 — `kotlinx-datetime` 미도입 (당시 판단)

- design.md §4.2의 `kotlinx.datetime` 예시가 컴파일 실패 → stdlib 산술(`floorDiv` + Howard Hinnant `civil_from_days`)로 우회, 테스트 9건으로 고정.
- ⚠️ **2026-07-31 정정**: 당시 원인 분석("0.7.x에서 관계가 바뀌어 안 맞는다")은 **절반만 맞았다.** 실제로는 **버전 스큐** — 선언 0.6.2를 JVM/Android가 그대로 썼고 common metadata만 0.7.1로 해석됐다. **선언을 0.7.1로 맞추면 그대로 컴파일된다.** `datetime-model-migration` T-M1 실측(6/6 + 6/6 passed)에서 규명됐다.

### iOS 로컬 네트워크 — ATS가 아니라 LNP (mobile-dev 정정)

- pm-lead가 `NSAllowsLocalNetworking` 추가를 지시했으나 **지시의 전제가 틀렸다.** Apple DTS에 따르면 **숫자 IP로의 평문 로드는 iOS 10+에서 ATS 대상이 아니다** — 해당 키는 이 URL 형태에서 **no-op**이다.
- 실제 관문은 **iOS 14+ Local Network Privacy** → `NSLocalNetworkUsageDescription`만 추가. `NSAllowsLocalNetworking`은 **의도적으로 넣지 않았다** — 동작에 영향이 없으면서 이름이 이 상황을 가리키는 것처럼 보여 오해를 만든다.
- mobile-dev가 런타임 검증을 시도했으나 **macOS 대조군(ATS 키 없음)도 통과**해 실험 자체를 무효 판정하고 **결과를 근거로 쓰지 않았다.** 런타임 확인은 실기기 몫으로 남는다.
