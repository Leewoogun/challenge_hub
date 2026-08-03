# Mobile Report — datetime-model-migration

- **feature-id**: datetime-model-migration
- **작성**: 2026-07-31 by mobile-dev
- **상태**: implemented (working tree, **커밋 안 함**)
- **선행 입력**: [spec.md](./spec.md), [api-contract.md](./api-contract.md) (`confirmed`), [ADR-0010](../../decisions/0010-datetime-model-localdatetime.md)
- **담당 태스크**: #9(T-M1 실측) · #12(T-M2~T-M5)

## 구현 요약

모바일의 시간 타입을 `kotlin.time.Instant`(UTC) → **`kotlinx.datetime.LocalDateTime`/`LocalDate`(KST)** 로 전환하고, 서버 응답 포맷 `yyyy-MM-dd HH:mm:ss`(ISO 아님) 파서를 도입했다. 함께 **파싱 실패 시 `Instant.DISTANT_PAST` 센티넬 폴백을 제거**했다 — 그게 이 작업의 실질적 위험 지점이었다.

세 가지가 핵심이었다:

1. **`kotlinx-datetime` 도입 가능 여부 (#9)** — challenge-create에서 "쓸 수 없다"는 결론이 났던 라이브러리다. 실측으로 뒤집었고 원인은 **버전 스큐**였다.
2. **센티넬 제거** — 파싱 실패가 "이미 마감된 카드"로 위장되던 경로. 필드 중요도로 정책을 갈랐다.
3. **회귀 0 유지** — challenge-create가 방금 끝낸 88건 위에서 타입을 통째로 바꿨다.

---

## #9 — `kotlinx-datetime` 도입 실측 (T-M1)

### 결론: 도입 가능. 자체 타입 불필요.

| 검증 | 결과 |
|---|---|
| probe Android/JVM | **6/6 passed** |
| probe iOS SimulatorArm64 | **6/6 passed** |
| 기존 `KstDeadlineTest` | 9/9 양쪽 유지 |
| Android + KMP common + iOS 컴파일 | BUILD SUCCESSFUL |

**iOS 네이티브 tzdb에서 `TimeZone.of("Asia/Seoul")`이 동작**하는 것이 최대 리스크였고 통과했다.

### 🔴 challenge-create에서 깨졌던 원인은 API 비호환이 아니라 **버전 스큐**였다

당시 나는 "0.7.x에서 `Instant` 관계가 바뀌어 안 맞는다"고 보고했는데 **절반만 맞았다.**

- `libs.versions.toml`은 **0.6.2** 선언 → common metadata만 `compose.material3:1.9.0` 제약으로 **0.7.1**로 해석. **JVM/Android 타깃은 선언값 0.6.2를 그대로 썼다** (Gradle 캐시에 `kotlinx-datetime-jvm`이 0.6.0/0.6.2까지만 존재).
- 0.6.2의 `kotlinx.datetime.Instant`는 **별개 클래스** → `kotlin.time.Instant`와 매칭 실패.
- 0.7.1은 `public typealias Instant = kotlin.time.Instant`(deprecated)이고 `TimeZone.kt`가 `import kotlin.time.Instant`를 해서 확장이 **`kotlin.time.Instant`에 직접** 걸린다.
- **선언을 0.7.1로 맞추니 그대로 컴파일된다.** 라이브러리가 아니라 우리 버전 선언이 문제였다.

**부수 소득**: `compose.material3`가 이미 kotlinx-datetime을 의존성 그래프에 끌어오고 있다 — 신규 서드파티 추가가 아니라 **이미 있는 것을 선언**하는 것이다.

> 이걸 파지 않았으면 자체 타입을 만들고 `floorDiv` + `civil_from_days`를 또 손으로 짜면서 "kotlinx-datetime은 못 쓴다"는 잘못된 통념이 레포에 굳었을 것이다.

### 실측으로 확정한 API (Android·iOS 양쪽 통과)

```kotlin
val KST = TimeZone.of("Asia/Seoul")
val WIRE_DATE_TIME = LocalDateTime.Format {
    year(); char('-'); monthNumber(); char('-'); day()
    char(' ')
    hour(); char(':'); minute(); char(':'); second()
}
```
**`"2026-07-28T15:04:05"`(ISO `T` 구분자)가 파싱 실패하는 것도 테스트로 고정했다** — 서버가 실수로 `T`를 흘리면 조용히 통과하지 않는다.

트랩: `LocalDateTime`은 `monthNumber`/`day`를 **직접 멤버**로 갖지만 `month.number`는 최상위 확장이라 `import kotlinx.datetime.number` 없이는 `Unresolved reference 'number'`로 깨진다. 실제로 여기서 한 번 깨졌다.

---

## #12 — T-M2~T-M5

### T-M2 `:domain:model` — `Instant` 0건

| 파일 | 필드 | 새 타입 |
|---|---|---|
| `ActiveChallenge` | `deadline` | `LocalDateTime` |
| `challenge/ReceivedChallenge` | `deadline` / `createdAt` | `LocalDateTime` / **`LocalDateTime?`** |
| `friend/Friend` | `since` | **`LocalDateTime?`** |
| `friend/FriendRequest` | `requestedAt` | **`LocalDateTime?`** |

`deadline`만 non-null인 이유: 파싱 실패 시 **항목 자체를 제외**하므로 도메인에 도달하면 항상 유효하다.
`domain/model/build.gradle.kts`에 `api(libs.kotlinx.datetime)` — 공개 타입이라 `implementation`이 아니다.

### T-M3 `:core:utils` — 손으로 짠 날짜 산술 제거

- `InstantFormat.kt` → **`RelativeTimeFormat.kt`** 재작성. `LocalDateTime.toRelativeKoreanString(now)`. **4종 반환(`"X시간 Y분"`/`"X분"`/`"곧 마감"`/`"마감"`)을 그대로 보존** — design.md가 의존하는 계약이다.
- **`KstDeadline.kt`에서 `floorDiv` + Hinnant `civil_from_days`를 통째로 삭제**하고 kotlinx-datetime으로 교체. 시그니처를 유지해 **기존 `KstDeadlineTest` 9건을 무수정으로 통과**시켰다 — 경계 의도(KST 날짜 경계·월말·연말·윤년·1970 이전)가 그대로 살아 있다.
- `KstTime.kt` 신설 — `KST` / `nowKst()`를 **프로젝트에서 한 곳에만** 정의.
- `ChallengeDateTimeFormats` — `parseWireDateTime(text): LocalDateTime?` / `parseWireDate(text): LocalDate?`. **실패 시 예외가 아니라 `null`** (repository가 이 null로 항목을 거른다).
- **probe 2파일 삭제** (수용 기준) + `build.gradle.kts` 주석 정리.

### T-M4 `:remote:mapper` + `:data:repositoryImpl` — 센티넬 제거

**`Instant.DISTANT_PAST`를 3개 mapper 전부에서 제거했다. 잔재 0건(grep 확인).**

계약 §3의 필드 중요도 분기:

| 필드 | 정책 |
|---|---|
| `deadline` | **항목 제외 + `onError` 1회 발화** |
| `createdAt` / `since` / `requestedAt` | **nullable 통과** (항목 유지) |

mapper는 순수 함수라 `onError`에 접근할 수 없다. 그래서 `MappedList<T>(items, droppedCount)`로 **거른 개수를 반환값에 실어** repository가 판단하게 했다:

```kotlin
if (mapped.droppedCount > 0) onError("일부 항목을 불러오지 못했어요")
this@flow.emit(mapped.items)
```
**거르고 남은 항목은 그대로 emit한다** — 5건 중 1건이 깨졌다고 나머지 4건을 못 보게 하지 않는다(계약 §3).

> ⚠️ **`:remote:mapper`에 테스트 소스셋 자체가 없었다.** mapper 테스트가 0건이라 `FriendMappers`·`ActiveChallengeResponseMapper`의 폴백은 **아무도 검증하지 않는 상태**였고, 동작을 바꿔도 아무 테스트도 말해주지 않았을 것이다. commonTest를 신설하고 3개 mapper 전부에 테스트를 붙였다(pm-lead 요구).

### T-M5 — ItemState·화면·DTO 문서

- `ReceivedChallengeItemState` — `now: LocalDateTime`, `isUrgent`는 **문자열 파싱이 아니라 `toInstant(KST)` 간격 비교**(잔여 1시간 경계 유지), `deadlineText`는 접미사 없음.
- `FriendItemStates` — `since`/`requestedAt` nullable, null이면 **`"-"`**. **일 단위 버킷 동작 보존**(`"오늘 친구가 됨"` / `"N일 전"` …) — 계약 §2.3이 `since`를 날짜 전용으로 낮추지 않기로 한 이유가 이것이다(시각 정보를 계산에 쓴다).
- `HomeViewModel` / `FriendsViewModel` — `Clock.System.now()` → `nowKst()`.
- Preview 더미를 결정적 `LocalDateTime` 리터럴로 교체(임박/여유 의도 유지).
- `:remote:model` DTO 4종의 **stale KDoc 정정** — `"ISO-8601 UTC ... kotlin.time.Instant로 파싱"` → 새 규약. DTO 필드 타입은 `String` 그대로.

---

## 테스트 결과 — **119/119 passed, 0 failed**

전건 XML 실측. 집계 전 `build/test-results`를 삭제해 **stale XML이 섞이지 않도록** 했다.

| 모듈 | 테스트 클래스 | 건수 | 성격 |
|---|---|---|---|
| `:core:utils` | `KstDeadlineTest` | **9** | 기존 — **무수정 통과** |
| | `RelativeTimeFormatTest` | 9 | 신규 |
| | `ChallengeDateTimeFormatsTest` | 6 | 신규 |
| | `WireFormatBaselineTest` | **4** | 신규 — **baseline 대조 자동화** |
| `:remote:mapper` | `ChallengeMappersTest` | 6 | 신규 |
| | `ActiveChallengeResponseMapperTest` | 3 | 신규 |
| | `FriendMappersTest` | 5 | 신규 |
| `:data:repositoryImpl` | `ChallengeRepositoryImplTest` | **13** | 12 − 삭제 1 + 신설 2 |
| | `UserInfoRepositoryImplTest` | 5 | 기존 유지 |
| `:feature:home` | `HomeViewModelTest` | **21** | 기존 유지 |
| `:feature:friends:list` | `FriendsViewModelTest` | **11** | 10 + 신설 1 |
| `:feature:friends:search` | `FriendsSearchViewModelTest` | 12 | 기존 유지 |
| `:feature:challenge:create` | `ChallengeCreateViewModelTest` | 15 | 기존 유지 |
| `:feature:login` | `LoginViewModelTest` | 4 | 기존 유지 |
| **합계** | | **123** | |

### 🔴 회귀 카운트 (수용 기준 형식)

> **기존 87건 회귀 0 / 의도적 삭제 1건 / 신규 36건 (그중 2건이 삭제분의 대체)**

- **baseline 88** = ChallengeRepositoryImpl 12 + ChallengeCreate 15 + Home 21 + KstDeadline 9 + UserInfo 5 + Friends 10 + FriendsSearch 12 + Login 4
- **삭제 1건**: `ChallengeRepositoryImplTest`의 `getReceivedChallenges - 시간 파싱 실패 시 DISTANT_PAST 폴백` — 이번 결정으로 **정반대 동작을 고정한 테스트**가 됐다.
- **삭제분 대체 2건**: 한 테스트가 `deadline`과 `createdAt`을 동시에 단언했는데 새 정책이 두 필드를 **정반대로 가르므로**(제외+`onError` vs null 유지) 1:1로 담을 수 없다. 1) `deadline` 실패 → 항목 제외 + `onError` 1회 2) `createdAt` 실패 → 항목 유지 + null + `onError` 미발화.
- **신규 36건** = 대체 2 + `since = null → "-"` 1 + 신규 파일 33(`RelativeTimeFormat` 9 + `ChallengeDateTimeFormats` 6 + `WireFormatBaseline` 4 + mapper 3종 14)
- **87 + 36 = 123** ✓

### baseline 대조를 테스트로 자동화했다

spec은 마이그레이션 전후 대조(`"2026-07-31T15:00:00Z"` ↔ `"2026-08-01 00:00:00"` — **같은 순간의 다른 표기**)를 **사람이 눈으로 확인하는 항목**으로 두고 있었다. 실패하면 즉시 중단해야 하는 기준인데 수동 확인은 놓치기 쉬워 `WireFormatBaselineTest` 4건으로 고정했다:

1. `parseWireDateTime("2026-08-01 00:00:00").toInstant(KST)` == `Instant.parse("2026-07-31T15:00:00Z")` — **spec baseline 그대로**
2. 남은 시간이 옛 방식(`Instant` 차)과 새 방식(`LocalDateTime` → `toInstant(KST)` 차)에서 동일
3. `toRelativeKoreanString`이 마이그레이션 전 구현과 같은 값 반환
4. KST가 DST 없는 고정 UTC+9임을 고정

**이 테스트가 깨지면 실제 시각이 이동한 것이므로 마이그레이션을 중단해야 한다** — 파일 KDoc에도 그 취지를 남겼다.

기존 테스트는 **이름과 단언을 바꾸지 않았다.** 타입·픽스처만 이관했다.

### 빌드

| 대상 | 결과 |
|---|---|
| Android (`:composeApp:compileDebugKotlinAndroid`, 전 모듈 전이) | ✅ BUILD SUCCESSFUL |
| KMP common (`compileCommonMainKotlinMetadata`) | ✅ BUILD SUCCESSFUL |
| iOS framework (`linkDebugFrameworkIosSimulatorArm64`) | ✅ BUILD SUCCESSFUL |

---

## 수용 기준 대조

| 기준 | 결과 |
|---|---|
| `:domain:model` 시간 필드에 `Instant` 0건 | ✅ (grep 확인) |
| `:core:utils` 상대 시간 함수가 `LocalDateTime` 기반 | ✅ |
| mapper가 `yyyy-MM-dd HH:mm:ss` / `yyyy-MM-dd` 파싱 | ✅ |
| 파싱 실패가 조용히 삼켜지지 않음 (센티넬 대체 + 테스트 고정) | ✅ `DISTANT_PAST` 잔재 0건 |
| 기존 88건 중 87건 회귀 0 + 의도적 교체 | ✅ 위 표 |
| **임시 probe 파일 미잔존** | ✅ 2파일 삭제 + 주석 정리 |
| Android·KMP common·iOS 빌드 성공 | ✅ |

### `Instant` 잔재에 대한 정확한 진술

`kotlin.time.Instant`는 **`KstDeadline.kt`와 그 테스트에만** 남아 있다(2파일). 이는 **의도적**이다:
- `kstDeadlineHintText(daysAhead, now: Instant = Clock.System.now())`의 `now`는 **도메인 필드가 아니라 시계 판독값**이고 `Clock.System.now()`가 원래 `Instant`를 준다.
- 시그니처를 유지한 덕에 **기존 테스트 9건을 한 줄도 고치지 않고** 경계 의도를 보존했다.
- 계약의 "**도메인·UI 계층**에 `Instant`를 남기지 않는다"와 충돌하지 않는다. `:domain:model` / `:remote:*` / `:data:*` / `:feature:*` 는 **전부 0건**이다.

---

## Working tree 상태

- **작업 브랜치: `main`**, **새 커밋 0건**
- staged/unstaged 그대로 둠 — 커밋·푸시·PR 생성 안 함(사용자 처리 영역)
- ⚠️ **`challenge-create` 미커밋 분과 누적**돼 있다. 두 feature의 변경이 한 working tree에 섞여 있으므로 커밋 분리는 사용자 판단이다.

## 미해결 / 후속

1. **실서버 연동 미검증** — 본 리포트는 모바일 단위 검증까지다. 서버의 새 포맷(`yyyy-MM-dd HH:mm:ss`)과 실제로 맞물리는지는 backend 트랙 완료 후 확인이 필요하다. spec의 baseline 대조(`deadline`이 `"2026-07-31T15:00:00Z"` → `"2026-08-01 00:00:00"`, **같은 순간의 다른 표기**)가 어긋나면 시각이 이동한 것이므로 즉시 중단해야 한다.
2. **iOS 유닛 테스트 미실행** — Android 유닛 + iOS framework link까지가 검증 게이트(기존 관행). `:feature:*:iosSimulatorArm64Test` 별도 실행은 후속.
3. **`:domain:model`의 `api(kotlinx-datetime)`가 Android 타깃으로 전이되지 않는다** — `challengeKotlinMultiplatformPure`(android 타깃 없음) 모듈이라 변형 매칭에서 api 간선이 유실된다. feature 모듈 3곳에 `implementation(libs.kotlinx.datetime)`을 **명시 선언**해 해결했다(레포의 기존 `materialIconsExtended` 선례와 동일한 대응). 근본 해결(pure 모듈의 api 전이)은 build-logic 이슈로 backlog 후보.
4. **`libs.versions.toml`의 `kotlinx-datetime` 버전** — 0.6.2 → **0.7.1**로 올렸다. 이제 실제 해석 버전과 선언이 일치한다.
