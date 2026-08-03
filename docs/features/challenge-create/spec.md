# 챌린지 신청 (challenge-create)

- **feature-id**: challenge-create
- **owner**: pm-lead
- **상태**: in-progress (Phase 4 구현 중)
- **생성**: 2026-07-28
- **최종 수정**: 2026-07-28 by pm-lead — Phase 3 팀 실측 피드백 반영 (스코프 결정 6 추가 / T-M3·T-M4 정정 / 리스크 2건 추가)

## 배경 / 문제

`friends` 2차까지 완료되어 친구를 맺을 수 있게 됐지만, 정작 제품의 핵심 행위인 **"친구에게 챌린지를 건다"**가 없다. 홈 피드(`home-feed`)는 `IN_PROGRESS` 챌린지를 읽어 그리는 화면만 있고 챌린지를 만드는 경로가 없어, 현재 앱은 어떤 사용자도 빈 상태를 벗어날 수 없다.

이 feature는 `challenges` 테이블에 최초의 row를 만드는 경로를 연다. 제품 전체 플로우(카카오 로그인 → 친구 등록 → **1:1 챌린지 신청** → 영혼의 맹세 → 양측 인증 → 자정 판정 → 결과) 중 3번째 단계에 해당한다.

## 스코프 결정 (2026-07-28, 사용자 확정)

브레인스토밍에서 5건을 확정했다. 근거를 남긴다.

1. **범위는 "신청까지"** — 생성 → PENDING → 수락/거절. 영혼의 맹세(계약서·서명)·STT 음성입력은 제외.
   - 서명은 `contracts.challenger_signature_url`이 URL 컬럼인데 프로젝트에 **파일 스토리지 결정(ADR)이 없다.** 선행 ADR 없이 진행 불가.
   - STT는 ADR-0006(클라이언트 SDK) 실행이 필요해 Android `SpeechRecognizer` + iOS `SFSpeechRecognizer` expect/actual 모듈 신설 건이다. 한 feature에 묶기엔 크다.
2. **`opponent_mission`은 수락 시 상대가 입력** — 챌린저는 본인 미션 + 내기만 넣는다.
   - Lovable `challenge-new.tsx` step1의 라벨이 "나의 미션"이고, `home-feed` 계약과 Lovable 목업 모두 두 미션이 **서로 다른 값**("운동 1시간" vs "책 30페이지")을 전제한다. 챌린저가 남의 미션까지 정하는 UX보다 자연스럽다.
   - 비용: `opponent_mission NOT NULL` 완화 마이그레이션 1건.
3. **마감은 사용자가 선택** — `오늘 자정` / `내일 자정` 2지선다.
   - 디자인은 "오늘 자정" 고정 텍스트였으나 심야 생성 시 10분짜리 챌린지가 되는 허점이 있어 선택제로 바꾼다.
   - 임의 날짜 선택(date picker)은 다중일 챌린지로 범위가 번지므로 **2지선다로 못박는다.**
4. **받은 도전장은 홈 화면 섹션** — `friends` 2차의 `ReceivedRequestsSection` 패턴을 답습.
   - 별도 화면은 하단 4탭(홈/친구/랭킹/MY)이 고정이라 진입 경로 신설이 필요하고, 알림 화면은 notifications feature 자체가 미구현이라 선행 비용이 크다.
5. **수락 직후 바로 `IN_PROGRESS`** — `CONTRACT_SIGNING`을 건너뛴다.
   - `ACCEPTED`에 머무르면 홈 피드가 `IN_PROGRESS`만 읽으므로 수락해도 화면에 아무것도 안 나타나, 이번 feature 단독으로 동작을 확인할 수 없다.
   - 영혼의 맹세 feature가 나중에 `ACCEPTED`와 `IN_PROGRESS` 사이에 `CONTRACT_SIGNING`을 삽입한다.

**추가 결정 — 중복 금지**: 같은 상대와 같은 `challenge_date`에 `PENDING` 또는 `IN_PROGRESS`인 챌린지가 이미 있으면 신규 생성을 거부한다. 1:1 대결 컨셉상 하루 한 판.

### 6. 보낸 도전장 목록은 이번 범위 밖 (2026-07-28 추가 확정, 옵션 C)

Phase 3에서 backend-dev가 **스펙 갭**을 발견했다: 취소 엔드포인트는 `DELETE /api/v1/challenges/{id}`로 `challengeId`를 요구하는데, 챌린저가 자기가 보낸 `PENDING` 챌린지를 나열할 경로가 없다. `/challenges/received`는 내가 `opponent`인 것만, `/challenges/active`(home-feed)는 `IN_PROGRESS`만 반환한다.

사용자 결정은 **C — 이번 범위 유지, 보낸 도전장 목록은 백로그로 강등**이다.

- `DELETE /api/v1/challenges/{id}`는 **서버에 구현하고 테스트도 작성한다.** 도달 경로가 생성 직후(create 응답의 `challengeId` 보유 시)로 제한될 뿐 죽은 코드가 아니며, 후속 feature가 목록 UI를 붙이면 그대로 살아난다.
- **모바일은 취소 호출부를 만들지 않는다.** 홈 화면은 전적 / 진행 중 챌린지 / 받은 도전장 3구성으로 확정.
- 근거: 이번 feature의 핵심 검증 목표(생성 → `PENDING` → 수락 → `IN_PROGRESS`가 홈에 노출)는 C로 온전히 달성된다. `GET /challenges/sent`는 서버 비용이 거의 0이지만 실제 비용이 design(T-D2 섹션 +1)과 모바일(T-M5 약 +25%, 홈 `combine` 소스 4→5)에 쏠려 임계 경로가 늘고, 이미 리스크로 등재된 "`HomeViewModel` 기존 테스트 10건 회귀 0" 기준을 더 압박한다.
- 대안 B(`/received`를 `/pending` + `direction` 필드로 통합)는 **채택하지 않는다.** mobile-dev 지적대로 방향별 표시 필드가 서로 다른데(RECEIVED = 상대 닉네임·상대 미션·수락/거절, SENT = 내 미션·취소) 한 DTO에 합치면 모바일의 전 필드 기본값 방어 패턴 탓에 잘못된 방향의 필드를 읽어도 컴파일·런타임 모두 조용히 통과한다.

## 사용자 시나리오

1. (챌린저) 홈 FAB 탭 → 친구 목록에서 대결 상대 선택 → 나의 미션·내기·마감 입력 → "챌린지 걸기" → `PENDING` 생성, 홈 복귀
2. (상대) 홈 진입 → "받은 도전장" 섹션에 카드 노출 → "수락" → 자기 미션 입력 → 챌린지가 `IN_PROGRESS`로 전환되어 진행 중 목록에 나타남
3. (상대) "거절" → 카드 사라짐, 챌린저 쪽에서도 목록에서 빠짐
4. ~~(챌린저) 상대가 아직 응답 전이면 보낸 도전장을 취소할 수 있음~~ → **이번 범위에서 제외** (스코프 결정 6). 서버 `DELETE`는 구현하되 모바일 진입 경로(보낸 도전장 목록)는 후속 feature. 백로그 등재.
5. (양측) 마감이 지나도록 상대가 응답하지 않으면 해당 도전장은 목록에서 사라짐 (`EXPIRED` 취급)

## 수용 기준 (Acceptance Criteria)

- [ ] 친구가 아닌 사용자에게는 챌린지를 걸 수 없다 (`friendships.status = 'ACCEPTED'` 아니면 거부)
- [ ] 본인에게 챌린지를 걸 수 없다
- [ ] 같은 상대 + 같은 `challenge_date`에 `PENDING`/`IN_PROGRESS` 챌린지가 있으면 생성이 거부된다
- [ ] 미션·내기는 trim 후 1~100자를 벗어나면 거부된다
- [ ] `deadlineType=TODAY`면 `deadline`이 **KST 당일 24:00을 UTC로 환산한 값**으로 저장된다 (`TOMORROW`는 +1일)
- [ ] `challenge_date`는 KST 기준 날짜로 저장된다
- [ ] 생성 직후 챌린지 상태는 `PENDING`이고 `opponent_mission`은 NULL이다
- [ ] 받은 도전장 목록은 `PENDING` + 마감 미경과 + 본인이 `opponent`인 것만 반환한다
- [ ] 수락 시 상태가 `IN_PROGRESS`로 바뀌고 `opponent_mission`이 채워진다
- [ ] 수락 시 해당 챌린지의 `verifications` PENDING row가 양측 2건 생성된다
- [ ] 수락된 챌린지가 `GET /api/v1/challenges/active` 응답에 즉시 나타난다
- [ ] 거절 시 상태가 `REJECTED`로 바뀌고 양쪽 목록에서 사라진다
- [ ] 챌린저가 `PENDING` 챌린지를 취소하면 row가 물리 삭제된다 — **서버 테스트로만 검증**(스코프 결정 6). 모바일 호출부가 없어 #7 통합 검증 대상이 아니다.
- [ ] 이미 처리된(PENDING이 아닌) 챌린지에 수락/거절/취소를 시도하면 비즈니스 에러로 거부된다
- [ ] 마감이 지난 `PENDING` 챌린지에 수락을 시도하면 거부된다
- [ ] 챌린지의 당사자가 아닌 사용자가 수락/거절/취소를 시도하면 거부된다
- [ ] 모바일: 위저드 2-step이 뒤로가기로 step0 ↔ step1 이동 가능하고, 미션·내기 미입력 시 다음 단계 버튼이 비활성이다
- [ ] 모바일: `HomeViewModel` 기존 테스트 10건이 회귀 없이 통과한다

## 비범위 (Out of Scope)

- **영혼의 맹세 / 계약서 / 서명** — `contracts` 테이블은 이번에 건드리지 않는다. 파일 스토리지 ADR 선행 필요.
- **STT 음성입력** — ADR-0006 실행은 별도 feature.
- **카메라 인증, 자정 판정, 결과 산출** — `verifications` row는 생성만 하고 채우지 않는다. `user_stats` 갱신 없음.
- **알림 / FCM** — 도전장이 왔다는 푸시 없음. 사용자가 홈에 들어와야 확인된다. (Firebase 프로젝트 생성이 🔵 대기 중)
- **챌린지 상세 화면** — Lovable `challenge-detail.tsx`는 이번 범위 밖.
- **다중일 챌린지** — 마감은 오늘/내일 2지선다 고정.
- **`EXPIRED` 배치 스케줄러** — 조회 시점 lazy 판정으로 대체. `:batch` 모듈 작업은 후속.
- **보낸 도전장 목록 (`GET /api/v1/challenges/sent`) + 모바일 취소 UI** — 스코프 결정 6. 서버 `DELETE /challenges/{id}`만 구현하고 목록 조회 엔드포인트·홈 섹션·취소 버튼은 만들지 않는다. 백로그 등재.
- **도발 메시지(`taunt_messages`)** — 별도 feature.

## 태스크 분해

### 백엔드 (backend-dev)

- [ ] **T-B1**: V5 마이그레이션 — `challenges.opponent_mission`을 NULL 허용으로 완화. 기존 row 없으므로 데이터 이관 불필요.
  - **범위 확대 승인 (2026-07-28)**: V5에 **부분 유니크 인덱스**를 함께 넣는다.
    ```sql
    CREATE UNIQUE INDEX uq_challenges_active_pair_date
        ON challenges (LEAST(challenger_id,opponent_id), GREATEST(challenger_id,opponent_id), challenge_date)
     WHERE status IN ('PENDING','IN_PROGRESS');
    ```
    근거: 수용 기준의 중복 금지는 **단정문이지 best-effort가 아니다.** Postgres 기본 READ COMMITTED에서 동시 트랜잭션의 미커밋 INSERT는 서로 보이지 않으므로 애플리케이션 사전 검사만으로는 두 요청이 나란히 통과해 중복 2건이 커밋된다. 이 인덱스가 있어야 friends 2차의 `DataIntegrityViolationException → 700` 백업 catch가 실제로 동작한다(없으면 dead code). api-contract 초안의 "부분 유니크 인덱스가 없으므로 애플리케이션 레벨 검사 권장" 문구는 **초안의 한계였지 결정이 아니다.**
    `LEAST`/`GREATEST`가 양방향 중복을 표현하고, `WHERE` 절이 PENDING/IN_PROGRESS만 차단하므로 **REJECTED된 쌍의 같은 날 재도전은 허용**된다(취소는 물리 삭제라 역시 막지 않는다) — spec 의도와 일치.
- [ ] **T-B2**: 도메인 확장 — `Challenge` 엔티티 쓰기 지원(현재 home-feed의 읽기 전용), `ChallengeRepository`에 생성/조회/상태전이 메서드 추가. `KstDeadlineCalculator`(core) 신설 — `deadlineType` → `challengeDate` + `deadline(UTC)` 환산.
- [ ] **T-B3**: 엔드포인트 5건 구현 — `ChallengeCommandController` + `ChallengeCommandService`. 검증 규칙(친구 여부·본인 여부·중복·길이·상태·권한·마감) 전부 포함. 수락 시 `verifications` PENDING row 2건 동시 생성(단일 트랜잭션).
- [ ] **T-B4**: 테스트 — 슬라이스(컨트롤러) + 서비스 단위(경계 케이스: KST 자정 환산, 중복 판정, 권한) + 통합. 통합은 Docker 미가용 시 자동 skip 패턴 유지.

### 모바일 (mobile-dev)

- [ ] **T-M1**: `:domain` — `challenge/` 하위 모델(`ReceivedChallenge`, `DeadlineType`, `ChallengeCreateInput` 등) + `ChallengeRepository` interface + UseCase.
- [ ] **T-M2**: `:remote` + `:data` — Ktorfit API 5건, DTO, mapper, `ChallengeRepositoryImpl`. **표준 패턴 준수**: `Flow<T>` + `onError: (String) -> Unit` 콜백, sealed Result 만들지 않음, 401은 Ktor `Auth(bearer)` 전담(`AuthEventBus` 주입 안 함).
- [ ] **T-M3**: 컴포넌트 3종 + `@Preview`. **배치는 feature 모듈** (2026-07-28 정정, 아래 참조) — `FriendPickItem`·`DeadlineSelector` → `:feature:challenge:create/component/`, `ReceivedChallengeCard` → `:feature:home/component/`. `:core:designsystem`은 건드리지 않는다.
  > **정정 근거**: 초안은 `:core:designsystem`에 두라고 했으나, 커밋 `72d9d9c "fix: feature component가 디자인시스템 모듈에 있던 문제 수정"`에서 **사용자가 feature 전용 컴포넌트를 designsystem에서 전부 걷어냈다.** 현재 `:core:designsystem`에는 범용 프리미티브(Button/Divider/Label/Scaffold 등) + 테마만 남아 있고, home-feed의 `ChallengeCard`/`StatsBar`/`HomeEmptyState`는 `:feature:home/component/`로, friends의 `FriendListItem`/`FriendRequestCard`는 `:feature:friends:list/component/`로 이미 옮겨졌다. 초안대로 하면 사용자 수정을 되돌린다. 이 배치에서 T-M3은 사실상 T-M4/T-M5에 흡수된다.
  > **의존성 근거 추가** (design-bridge): `:core:designsystem`은 `:core:utils`만 의존하므로 `:domain:model`의 `DeadlineType`을 받을 수 없다. 초안대로 가면 미러 enum + 매퍼가 추가로 필요하다(`ChallengeVerificationStatus` 선례). mobile-dev와 design-bridge가 **독립적으로 같은 결론**에 도달했다.
- [ ] **T-M4**: `:feature:challenge:create`의 **스텁 6파일을 2-step 위저드 실물로 교체**. `ChallengeCreateViewModel`은 TDD.
  > **정정 근거**: 초안의 "모듈 신설 + Navigation 연결"은 **이미 완료 상태**다. 커밋 `be324b9`로 `:feature:challenge:create` 모듈이 존재하고 `settings.gradle.kts` include / `:feature:main` 의존 / `Route.Challenge.Create` + `routeSerializersModule` / `MainScreen` entryProvider / Koin `ChallengeCreateModule` / **홈 FAB → 위저드 네비게이션**(`HomeRoute.onFabClick`·`onCreateChallengeClick`)까지 배선이 끝나 있다. `Route`/`Screen`/`ViewModel`/`contract`/`di` 6파일이 "준비 중입니다" 스텁일 뿐이다. → `scripts/generate-feature.sh` 실행 불필요, 태스크 범위 축소.
  > 모듈 경로는 `:feature:challenge`가 아니라 **`:feature:challenge:create`**(중첩). friends도 `:feature:friends:list` / `:feature:friends:search`로 분할됐다.
- [ ] **T-M5**: `:feature:home` 확장 — `ReceivedChallengesSection` + 수락 미션 입력 UI(**`AcceptChallengeDialog` 확정**, design.md v3 §3.1) + `HomeViewModel`에 받은 도전장 갈래 추가. **기존 테스트 10건 회귀 0 유지.**
  - **본 feature가 새로 만드는 오버레이는 `AcceptChallengeDialog` 하나뿐이다.** 에러 전용 다이얼로그는 만들지 않는다 — 계약 §공통 규약 2가 "모바일은 `code`로 분기하지 않는다"를 명문화했으므로(`onError: (String) -> Unit`이 `CustomError`의 code를 버리는 프로젝트 표준) 수락/거절 실패는 **코드 무관 스낵바 + 목록 무조건 재조회**로 처리된다. 실패 문구는 서버 `message` 그대로.
  - ⚠️ **결정 번복 이력 (2건, 둘 다 pm-lead 승인)**
    1. **v1 `ModalBottomSheet` → v2 다이얼로그.** mobile-dev의 플랫폼 제약 지적을 design-bridge가 검증한 결과 v1의 1순위 근거가 틀렸다. 유효 근거: (a) `challenge-app` 전체에 `ModalBottomSheet` 사용처 **0건**(grep 확인) — CMP 1.10.3의 시트 + `TextField`는 iOS IME 동작이 갈리는 구간이라 iOS 실기 검증 시간이 별도로 필요하다. (b) `MainScreen.kt:142`에 이미 `imePadding()`이 있어 기존 인셋 처리와 충돌이 적은 쪽은 다이얼로그다. (c) 입력 필드가 1개뿐이라 시트의 넓은 면적이 불필요하다.
    2. **v2의 "705 다이얼로그와의 역할 분리" 근거 → v3에서 폐기.** 계약 확정 내용(모바일 code 미분기)이 반영되지 않은 상태에서 세운 논리였고, 705 전용 확인 다이얼로그 자체가 존재하지 않으므로 전제가 무너졌다. **결론(다이얼로그)은 유지** — 나머지 근거가 그대로이고, 오히려 신규 오버레이가 1개로 줄어 더 단순해졌다. `ChallengeErrorDialog`는 **만들지 않는다**(design.md §4.6에 폐기 사유가 남아 있으니 재발명 금지).
  - 추가 확정 (2026-07-28, design-bridge 제안 → pm-lead 승인): `isFirstUser` 판정에 `received.isEmpty()`를 AND로 추가한다. 받은 도전장이 화면에 떠 있는데 그 아래에서 "친구를 등록하고 첫 약속을 걸어보세요"는 사실과 어긋나므로 `NO_ACTIVE_CHALLENGE` 톤으로 낮춘다. 기존 테스트 10건은 받은 도전장 개념 이전에 작성돼 fake가 빈 목록을 주므로 `isFirstUser && true`가 되어 결과 불변 — 다만 mobile-dev가 실측 확인 후 진행할 것.

### 디자인 (design-bridge)

- [ ] **T-D1**: Lovable `challenge-new.tsx` step1에 마감 선택(오늘/내일) UI 추가. **step2(영혼의 맹세)는 건드리지 않고 그대로 둔다** — Lovable은 완성형 비전을 앞서 들고 있어도 된다(메모리 규칙).
- [ ] **T-D2**: 홈 "받은 도전장" 섹션 신규 설계 — `friends.tsx`의 받은 요청 섹션 패턴 + 기존 토큰만 사용.
- [ ] **T-D3**: `design.md` 작성 — 위 두 건 + 수락 시 미션 입력 UI(바텀시트/다이얼로그 중 택1) 명세.

## 의존 관계

- T-M1~T-M5, T-B2~T-B4는 `api-contract.md` 상태가 `confirmed`가 된 뒤 착수.
- T-B1(마이그레이션)은 계약 확정 전에도 착수 가능 — 스키마 완화는 계약과 독립.
- T-B3는 T-B1, T-B2 완료 후.
- T-M2는 T-M1 완료 후. T-M4/T-M5는 T-M2, T-M3 완료 후.
- T-M4/T-M5의 화면 작업은 T-D3(`design.md`) 완료 후. 디자인 대기 중에는 T-M1~T-M3 선행.

## 리스크 / 오픈 이슈

- **`EXPIRED` 전이 주체 없음** — 이번엔 조회 시점 lazy 판정(목록 응답에서 제외 + 수락 시도 시 거부)으로 처리한다. DB의 `status`는 `PENDING`인 채로 남는다. `:batch` 스케줄러로 실제 전이시키는 작업은 backlog 등재.
- **취소가 물리 삭제** — `challenge_states`에 `CANCELED`가 없어 새 상태 도입을 피했다. 감사 추적이 남지 않는다. `friends` 2차의 요청 취소와 동일한 선택이므로 프로젝트 내 일관성은 있다.
- **홈 화면 소유권** — `HomeScreen`/`HomeViewModel`은 `home-feed` feature 산출물이다. 확장 시 기존 3-상태(default/FIRST_USER/NO_ACTIVE_CHALLENGE) 렌더링과 테스트 10건이 깨지지 않는지 확인 필요.
- **`HomeViewModel`에 refresh 메커니즘 부재** (2026-07-28 mobile-dev 실측) — 현재는 `GetHomeDataUseCase(::showMessage)` 콜드 Flow를 `.map{}.stateIn(WhileSubscribed(0))` 한 게 전부라 한 번 흘러간 뒤 다시 당길 방법이 없다. T-M5의 수락/거절 후 재조회를 위해 refresh 트리거 도입이 불가피하며, 이는 `home-feed` 산출물의 구조 변경이다. `FriendsViewModel`의 `MutableSharedFlow` refreshTrigger + `onStart` + `flatMapLatest` + `onSuccess = ::reload` 패턴을 이식하므로 신규 패턴 발명은 없다.
- **`combine` 실패 전파 위험** (2026-07-28 mobile-dev 실측, **대응 확정**) — `GetHomeDataUseCase`가 `combine`으로 3개 소스를 합치는데 `combine`은 모든 소스가 1회 이상 emit해야 결과를 낸다. 실패 시 emit 없이 `onError`만 부르는 표준 패턴이라 소스 하나가 실패하면 홈 전체가 `Loading`에 갇힌다(기존 테스트 2건이 이 동작을 고정 중). 받은 도전장을 4번째 소스로 그냥 추가하면 **받은 도전장 조회 실패가 홈 화면 전체를 백지로 만든다.** → 받은 도전장 소스는 실패 시 `emptyList()`를 emit하도록 degrade시켜 격리한다(`userInfo`의 `.onEmpty { emit(null) }` 선례와 동일). pm-lead 승인 완료.
- ~~**`:feature:challenge` 모듈 신설**~~ — ✅ 해소. 커밋 `be324b9`로 `:feature:challenge:create` 모듈 생성 + `settings.gradle.kts` include + Navigation 배선이 이미 끝나 있다(T-M4 정정 근거 참조). `repos.json`의 `mobile.modules` 목록은 낡았으므로 pm이 갱신한다.
- **수락 시 미션 입력 UI가 디자인 부재** — Lovable에 대응 화면이 없다. T-D3에서 기존 토큰으로 신규 설계했으며(→ `AcceptChallengeDialog`), 디자이너 검토는 사후(design.md v3 §9, 15건).
  - 수용한 트레이드오프: **수락 실패 시 다이얼로그가 닫혀 입력값이 사라진다.** 길이 위반은 클라 검증(trim + 100자 하드캡)으로 도달 불가하므로 실제 손실은 네트워크 오류·낡은 목록 두 경우뿐이다.
- **`toRelativeKoreanString()` 반환값 오해 주의** (2026-07-28 design-bridge가 구현 전 발견) — `:core:utils`의 이 헬퍼는 `"X시간 Y분"` 외에 **`"곧 마감"` / `"마감"`도 반환한다.** design.md v1이 `" 남음"` 접미사를 지시해 `"곧 마감 남음"`이 될 뻔했다. v2에서 접미사 제거로 정정. 이 헬퍼를 쓰는 다른 화면도 같은 함정이 있다.
- **마감 임박 강조는 잔여 1시간 경계** (design.md v3) — `error` 톤, 그 외 `warning`. 3시간으로 잡으면 목록 대부분이 강조돼 강조가 죽는다.
