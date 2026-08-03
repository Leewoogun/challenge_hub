# ADR-0010: 날짜·시간 모델을 `Instant`(UTC) → `LocalDateTime`으로 통일

- **상태**: **accepted — 구현 완료 (2026-07-31)**. [datetime-model-migration](../features/datetime-model-migration/summary.md)으로 구현. 백엔드 123/123 + 실서버 65/65, 모바일 123/123.
- **생성**: 2026-07-31
- **결정자**: 사용자
- **영향 범위**: 서버 DTO·도메인·엔티티, 모바일 도메인 모델·mapper·ItemState·`:core:utils`, **모든 feature의 `api-contract.md`**, CLAUDE.md의 시간 포맷 규칙, ADR-0002(응답 규약)

> ⚠️ 이 ADR은 **결정을 기록**한 것이며 아직 구현되지 않았다. 구현 시점에 상태를 갱신하고 `change-log.md`에 반영할 것.

## 맥락

프로젝트는 지금까지 시간 필드를 **`Instant` + ISO-8601 UTC(`Z` suffix)** 로 다뤄 왔다. CLAUDE.md 규칙("시간 포맷은 ISO-8601 UTC")과 `foundation` 이래의 관행이다.

2026-07-31 사용자가 **서버와 모바일 양쪽의 날짜·시간 모델을 `LocalDateTime` 형식으로 맞추기로** 결정했다.

### 현재 표면 (2026-07-31 실측)

**서버** (`java.time.Instant` 사용 8파일)
```
controller/.../challenge/dto/ChallengeCommandDtos.kt      ← deadline, createdAt
controller/.../challenge/dto/ActiveChallengeResponse.kt   ← deadline
controller/.../friend/dto/FriendListResponse.kt           ← since
service/.../challenge/ChallengeCommandService.kt
core/.../challenge/KstDeadlineCalculator.kt               ← UTC 환산 핵심
+ 테스트 3파일
```

**모바일** (`kotlin.time.Instant` 사용 20파일)
```
domain/model/     ActiveChallenge, ReceivedChallenge, Friend, FriendRequest
remote/mapper/    ChallengeMappers, FriendMappers, ActiveChallengeResponseMapper
core/utils/       InstantFormat(toRelativeKoreanString), KstDeadline
feature/          home(HomeScreen/HomeUiState/ReceivedChallengeItemState),
                  friends:list(FriendItemStates), challenge:create(Screen/FriendPickStep)
+ 테스트 5파일
```

**계약 문서**: `challenge-create`(deadline·createdAt), `home-feed`(deadline), `friends`(since)

## 근거 / 기대 효과

사용자 결정이므로 근거는 구현 시 보강한다. 현재까지 파악된 동기:

- 서버와 모바일이 **서로 다른 시간 타입 계층**을 쓰고 있다. 모바일은 `kotlinx-datetime`을 의존성에서 배제하고 stdlib `kotlin.time.Instant`만 쓰기로 확정했는데(home-feed), 그 결과 KST 변환이 필요할 때마다 **직접 산술로 푸는 코드가 늘고 있다** — `KstDeadlineCalculator`(서버) / `KstDeadline`(모바일)이 같은 로직의 중복 구현이다.
- `challenge-create`에서 `kotlinx-datetime` 도입을 시도했다가 버전 충돌(`libs.versions.toml`은 0.6.2인데 실제 해석은 `strictly 0.7.1`, `Instant.toLocalDateTime(TimeZone)` 확장 미매칭)로 stdlib 산술 우회를 택했다. 시간 타입 전략이 정리되지 않은 상태가 드러난 사례다.
- 이 서비스는 **KST 단일 타임존**을 전제한다(해외 사용자 대응은 명시적 비범위). UTC 왕복 변환이 실질 이득 없이 양쪽에 환산 코드를 만든다.

## 결정

**서버·모바일의 날짜·시간 모델을 `LocalDateTime`으로 통일한다.**

## 영향 및 선행 정리 사항

구현 착수 전에 아래를 결정해야 한다. **이 ADR은 이 항목들을 열어둔 채 기록된다.**

1. **직렬화 표기 확정** — `"2026-07-28T15:00:00"`(offset 없음)이 될 텐데, 이는 **현재 계약의 `Z` suffix 고정 규약을 깨뜨린다.** 모바일이 `Instant.parse()` 실패 시 `Instant.DISTANT_PAST`로 폴백하는 구조라 **파싱 에러가 "이미 마감된 카드"로 조용히 나타난다**(home-feed 선례, challenge-create 계약 L222에 명시). 양측 동시 배포가 아니면 이 방식으로 깨진다.
2. **타임존 소유권** — `LocalDateTime`은 offset 정보를 잃는다. "이 값은 KST"라는 약속이 타입이 아니라 **문서와 관행에만** 존재하게 된다. DB `TIMESTAMP` 컬럼의 해석 기준(현재 UTC 가정 — backlog "챌린지 deadline UTC 일관성 명시" 항목 참조)도 함께 정리해야 한다.
3. **기존 데이터** — `challenges.deadline`, `friendships.created_at` 등에 이미 UTC 기준으로 저장된 값이 있으면 마이그레이션 또는 해석 변경이 필요하다.
4. **모바일 타입 선택** — `kotlinx-datetime`을 도입할지(버전 충돌 선결 필요), 자체 `LocalDateTime` 표현을 만들지. `libs.versions.toml`의 `kotlinx-datetime` 항목은 현재 **참조 모듈 0개**다.
5. **CLAUDE.md 규칙 개정** — "시간 포맷은 ISO-8601 UTC" 문구를 새 규약으로 교체해야 한다.
6. **`confirmed` 계약 3건 개정** — `challenge-create` / `home-feed` / `friends`의 `api-contract.md`. 각 feature의 `change-log.md`에 기록.
7. **중복 구현 정리 기회** — `KstDeadlineCalculator`(서버) ↔ `KstDeadline`(모바일)이 이 작업으로 단순해지거나 사라질 수 있다.

## 대안 (기록용)

- **현행 유지(`Instant` + UTC)** — 표준적이고 타임존 버그에 강하지만, KST 단일 타임존 서비스에서 양측 환산 코드를 계속 유지해야 한다.
- **서버만 `LocalDateTime`, 모바일은 문자열 취급** — 모바일이 시간 연산을 안 하면 가능하지만, 마감 카운트다운·임박 강조(잔여 1시간 경계)가 있어 연산이 필요하다.

## 후속

- 구현은 **별도 feature로 분리**한다. `challenge-create`에 끼워 넣지 않는다 — 3개 레포와 3건의 `confirmed` 계약을 건드리는 횡단 변경이다.
- backlog에 🟡로 등재.
