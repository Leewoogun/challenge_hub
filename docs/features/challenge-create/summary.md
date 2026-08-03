# 챌린지 신청 (challenge-create) — Summary

- **feature-id**: challenge-create
- **완료일**: 2026-07-31
- **상태**: completed

## 구현 개요

제품의 핵심 행위인 **"친구에게 챌린지를 건다"**를 열었다. `friends` 2차로 친구를 맺을 수 있게 됐지만 `challenges` 테이블에 row를 만드는 경로가 없어 모든 사용자가 빈 홈 화면을 벗어날 수 없었다. 이 feature가 그 경로를 만든다.

범위는 **신청까지** — 생성 → `PENDING` → 수락/거절이다. 수락 즉시 `IN_PROGRESS`로 전이시켜(`CONTRACT_SIGNING` 건너뜀) 이번 feature 단독으로 "생성 → 수락 → 홈에 노출"이 확인 가능하게 했다. 영혼의 맹세(계약서·서명)와 STT는 각각 파일 스토리지 ADR·ADR-0006 실행이 선행돼야 해서 제외했다.

## 엔드포인트

| Method | Path | 상태 |
|--------|------|------|
| POST | `/api/v1/challenges` | deployed |
| GET | `/api/v1/challenges/received` | deployed |
| POST | `/api/v1/challenges/{id}/accept` | deployed |
| POST | `/api/v1/challenges/{id}/reject` | deployed |
| DELETE | `/api/v1/challenges/{id}` | deployed — **모바일 호출부 없음** (옵션 C, 아래 결정 사항 2) |

> `deployed` = 로컬 실서버에 기동되어 실제 HTTP 호출로 검증된 상태. **아직 어느 레포도 커밋되지 않았다.**

## 화면 / UI 변경

- **`:feature:challenge:create`** — 2-step 위저드 신규. step0 친구 선택 → step1 미션·내기·마감 입력. 홈 FAB에서 진입.
- **`:feature:home`** — "받은 도전장" 섹션 신규(전적 바 아래 / 진행 중 챌린지 위). 수락 시 `AcceptChallengeDialog`로 본인 미션 입력.
- **`DeadlineSelector`** — `오늘 자정` / `내일 자정` 2지선다 + **실제 마감 시각 부기**(`"7/28 24:00"`).
- **Lovable**: `challenge-new.tsx`(마감 선택 UI + step2 계약서의 마감 표시 바인딩), `index.tsx`(받은 도전장 섹션). **신규 디자인 토큰 0건.**

## 주요 변경 파일

**백엔드** (신규 production 7 / 신규 test 4 / 수정 8)
- `app/.../db/migration/V5__challenge_create_opponent_mission_nullable.sql`
- `core/.../challenge/KstDeadlineCalculator.kt`
- `controller/.../challenge/ChallengeCommandController.kt` + `dto/ChallengeCommandDtos.kt`
- `service/.../challenge/ChallengeCommandService.kt`
- `app/.../config/ClockConfig.kt` (신규 `Clock` 빈)

**모바일** (신규 41 / 수정 16 / 삭제 2)
- `domain/model/.../challenge/` + `domain/repository/ChallengeRepository.kt` + `domain/usecase/CreateChallengeUseCase.kt`
- `remote/api/ChallengeApi.kt` + `remote/model/challenge/`(DTO 7) + `remote/mapper/ChallengeMappers.kt`
- `data/repositoryImpl/.../ChallengeRepositoryImpl.kt`
- `feature/challenge/create/` (스텁 6파일 → 실물, 컴포넌트 12 신규)
- `feature/home/component/{ReceivedChallengeCard, ReceivedChallengesSection, AcceptChallengeDialog, BetStrip, ProfilePlaceholder, MissionInputField}.kt`
- `core/utils/.../datetime/KstDeadline.kt`
- `iosApp/iosApp/Info.plist` (`NSLocalNetworkUsageDescription`)

## 테스트 결과

**백엔드 — 111/111 passed, 0 failed**
- 신규: `KstDeadlineCalculatorTest` 17/17 · `ChallengeCommandServiceTest` 39/39 · `ChallengeCommandControllerTest` 18/18
- 기존 회귀 0 (37건: Friend 15 + Auth 5 + GlobalExceptionHandler 5 + User 2 + PhoneHasher 3 + escapeForLike 6 + smoke 1)

**백엔드 실서버 end-to-end — 58/58 PASS, 0 FAIL**

실행 중인 서버 + 실 Postgres에 **실제 JWT로 HTTP 호출**. 생성 7 / 검증규칙 12 / 받은도전장 9 / 수락+read-after-write 17 / 거절 6 / 취소 8 / 미인증 2.

**모바일 — Android 유닛 88/88 passed, 0 failed**
- 신규: `ChallengeRepositoryImplTest` 12/12 · `ChallengeCreateViewModelTest` 15/15 · `KstDeadlineTest` 9/9
- 확장: `HomeViewModelTest` 21/21 (기존 10 + 신규 11)
- 회귀 0: `UserInfoRepositoryImplTest` 5/5 · `FriendsViewModelTest` 10/10 · `FriendsSearchViewModelTest` 12/12 · `LoginViewModelTest` 4/4
- 빌드: Android · KMP common · iOS `linkDebugFrameworkIosSimulatorArm64` · `xcodebuild -sdk iphonesimulator` 전부 SUCCESS

**🔴 실행되지 않음**: 백엔드 통합 테스트 **45건 전부 skip** (컨테이너 런타임 미설치). 아래 미해결 이슈 1 참조.

## 결정 사항

1. **`opponent_mission`은 수락 시 상대가 입력** — 챌린저는 본인 미션 + 내기만 넣는다. V5로 `NOT NULL` 완화.
2. **보낸 도전장 목록은 범위 밖 (옵션 C, 사용자 결정)** — `DELETE`는 서버에 구현·테스트하되 조회 경로(`GET /challenges/sent`)를 만들지 않는다. 모바일 취소 호출부도 없다. `/pending` + `direction` 통합안(B)은 **기각** — 방향별 표시 필드가 달라 한 DTO에 합치면 모바일의 전 필드 기본값 방어 패턴 탓에 잘못된 방향 필드를 읽어도 컴파일·런타임 모두 조용히 통과한다.
3. **모바일은 에러 `code`를 소비할 수 없다** — `onError: (String) -> Unit`이 `CustomError.code`를 버리는 프로젝트 표준(`faae2cd`). 서버의 700/705 배분은 의미대로 유지하되 모바일 동작은 **"실패 시 코드 무관 스낵바 + 목록 항상 재조회"**로 확정. 부수적으로 **모든 에러 `message`를 사용자 노출 확정 문구로 못박고** 슬라이스 테스트가 글자 단위로 검증한다.
4. **V5에 부분 유니크 인덱스 추가** (T-B1 범위 밖, 승인) — `LEAST/GREATEST` + `WHERE status IN ('PENDING','IN_PROGRESS')`. Postgres READ COMMITTED에서 미커밋 INSERT가 동시 트랜잭션에 안 보여 **애플리케이션 검사만으로는 중복 금지 수용 기준을 만족할 수 없다.** 이 인덱스가 있어야 `DataIntegrityViolationException → 700` 백업 catch가 dead code가 아니게 된다.
5. **수락 UI = `AcceptChallengeDialog`** (v1 바텀시트에서 번복) — `ModalBottomSheet` 선례 0건 + CMP 1.10.3 iOS IME 리스크 + 기존 `imePadding()` + 입력 필드 1개. **본 feature가 새로 만드는 오버레이는 이것 하나뿐**이며 `ChallengeErrorDialog`는 만들지 않는다(결정 3의 귀결).
6. **컴포넌트는 feature 모듈에 배치** — spec 초안의 `:core:designsystem`은 커밋 `72d9d9c`(사용자가 feature 컴포넌트를 designsystem에서 걷어낸 작업)를 되돌리는 것이었다. 추가로 `:core:designsystem`은 `:core:utils`만 의존해 `:domain:model`의 `DeadlineType`을 받을 수 없다.
7. **iOS 로컬 서버 접근은 ATS가 아니라 LNP 문제** — 숫자 IP로의 평문 로드는 iOS 10+에서 ATS 대상이 아니다(Apple DTS). 실제 관문은 iOS 14+ Local Network Privacy이므로 `NSLocalNetworkUsageDescription`만 추가했다. `NSAllowsLocalNetworking`은 이 URL 형태에서 **no-op**이라 넣지 않았다 — 넣으면 "로컬 네트워크 처리는 이 키가 한다"는 오해를 만든다.

## 미해결 이슈

- [ ] **🔴 백엔드 통합 테스트 45건 미실행** (기존 24 + 이번 21) — 컨테이너 런타임 미설치(docker/podman/colima/orbstack 전부). 이 프로젝트는 통합 테스트를 **단 한 번도 실행한 적이 없다.** 단 이번 feature는 **실서버 58/58 end-to-end로 해당 층(JPA 매핑·Flyway 적용·Security 필터·직렬화)을 대체 검증**했다.
- [ ] **🟡 잘못된 요청 본문이 HTTP 500** — `GlobalExceptionHandler`가 `HttpMessageNotReadableException` 미처리. foundation 이래 기존 동작이며 정상 클라이언트는 영향 없으나, **`datetime-model-migration`에서 포맷 틀린 날짜가 정확히 이 경로로 500을 만든다.** 해당 feature T-B3에 포함 확정.
- [ ] **🟡 시스템 백 버튼으로 위저드 step1 → step0 복귀 미구현** — `PlatformBackHandler`가 `:feature:main`에 갇혀 있다. `:core:ui` 승격으로 해결.
- [ ] **🟢 `/actuator/health` 500** — actuator 의존성 부재. 현재 사용처 없음.
- [ ] **🟢 `Clock` 빈 혼재** — `ClockConfig`가 `Clock.systemUTC()`를 등록했으나 기존 코드는 `LocalDateTime.now()`. → **`datetime-model-migration`에서 해소된다.**
- [ ] **🟢 `SearchProfilePlaceholder` 4번째 사본** — `:feature:friends:search`에 크기만 다른 동일 구현. 완료된 feature 영역이라 손대지 않음.
- [ ] **🟢 `EXPIRED` 전이 주체 없음** — lazy expiry로 처리. `:batch` 스케줄러는 후속.
- [ ] **🟢 취소가 물리 삭제** — `challenge_states`에 `CANCELED`가 없어 새 상태 도입을 피했다. friends 2차와 동일 선택.
- [ ] **iOS 유닛 테스트 미실행** — Android 유닛 + iOS 링크까지가 검증 게이트였다.
- [ ] **실기기 시각 검증 미수행** — 특히 **수락 다이얼로그의 iOS IME 동작**. 다이얼로그를 택한 이유가 시트의 IME 리스크였던 만큼 실기 확인이 필요하다.
- [ ] **커밋 0건** — PM 허브 / 백엔드 / 모바일 / Lovable 4개 레포 모두 working tree 상태.

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [design.md](./design.md)
- [mobile-report.md](./mobile-report.md) · [backend-report.md](./backend-report.md) · [change-log.md](./change-log.md)
- 후속: [datetime-model-migration](../datetime-model-migration/spec.md) · [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)
