# ADR-0014: 페이지네이션 — `isPageEnd` 불리언 허용 + 커서 필드를 기준 키 이름으로

- **상태**: accepted (2026-10-26)
- **결정자**: 사용자 (pm-lead 가 ADR-0012 §근거 3 과의 충돌을 고지한 뒤 결정)
- **부분 대체**: [ADR-0012](./0012-list-pagination-cursor.md) — **§결정 1 의 필드 이름 · §근거 3(`hasNext` 불리언 금지)만** 대체한다.
  커서 방식 · `id DESC` 정렬 축 · 커서 비소비 · `size` 범위 밖 `code 700` · 총 개수 미제공 · 적용 범위(기존 6종 미적용)는 **전부 그대로 유효하다.**
- **적용**: [notification-list](../features/notification-list/api-contract.md) — `GET /api/v1/notifications` (v3)

---

## 맥락

모바일 Notification 모듈 리팩토링 중 사용자가 두 가지를 요청했다.

1. **페이지 끝을 `isPageEnd: Boolean` 으로 받고 싶다.** 클라이언트의 페이징 기반 코드
   (CarOwnerRenew `PaginatedUseCase` → `XxxResult(items, isPageEnd)` → ViewModel `if (state.isPageEnd) return`)가
   이 신호를 전제로 짜여 있다.
2. **`cursor` 라는 이름을 쓰지 않는다.** 무엇을 기준으로 페이징하는지가 이름에 드러나야 한다.

pm-lead 는 1번이 ADR-0012 §근거 3 과 충돌한다고 고지하고 대안(클라이언트 매퍼에서 `nextCursor == null` 로 계산)을
권했으나, 사용자는 서버 응답에 넣는 쪽을 택했다.

## 결정

### 1. shape

```
GET /api/v1/notifications?nextNotificationId={직전 응답의 nextNotificationId}&size={N}
```
```json
{ "data": { "notifications": [ ... ], "nextNotificationId": 38, "isPageEnd": false } }
```

| 필드 | 규약 |
|---|---|
| `nextNotificationId` (요청) | optional. 생략 = 첫 페이지. **직전 응답의 `nextNotificationId` 를 그대로 되돌려 보낸다.** 🔴 **이 `id` 를 포함해** 그 이하부터(`id <= :nextNotificationId`) |
| `nextNotificationId` (응답) | nullable `Long`. **다음 페이지 첫 항목의 id** — `size + 1` 조회에서 잘라 낸 초과분 1건의 id. **`isPageEnd == true` 이면 `null`** |
| `isPageEnd` (응답) | non-null `Boolean`. 더 가져올 페이지가 없으면 `true` |

### 2. 🔴 두 끝 신호는 **한 출처에서** 만든다 — 불변식 `isPageEnd == (nextNotificationId == null)`

ADR-0012 가 불리언을 금지한 이유 하나는 *"끝"을 말하는 신호가 둘이 되는 것*이었다. 그 위험을 받아들이는 대신
**서버가 `size + 1` 조회의 초과분 유무 하나에서 두 값을 동시에 만들고, 이 불변식을 테스트로 고정한다.**
두 값을 따로 계산하는 코드를 만들지 않는다.

클라이언트의 역할 분담:
- **멈출지 판단은 `isPageEnd`**
- **다음 요청 값은 `nextNotificationId` 를 그대로** — 🔴 앱은 *"목록 마지막 항목의 id 를 꺼내 쓴다"* 를 하지 않는다.
  **이제 그 값은 응답값과 다르다**(마지막 항목 id ≠ 다음 첫 항목 id) — 꺼내 쓰면 포함 경계 때문에 **마지막 항목이 중복된다.**
  ADR-0012 §근거 3 이 경계한 "규칙의 사본"은 이 줄이 막는다. 불리언이 생겨도 이 줄은 유지된다.

### 3. 이름은 `next…` — 값을 이름에 맞춘다

사용자가 `nextNotificationId` 를 택했다. ADR-0012 의 `nextCursor` 는 **이번 페이지 마지막 항목의 id**(배타 경계,
`id < :cursor`)였는데, 그 값을 그대로 두고 이름만 `next…` 로 바꾸면 *"다음 페이지 첫 항목의 id"* 로 읽혀
포함/제외 경계를 오독하게 된다(한 건 누락·중복).

그래서 **이름이 아니라 값을 바꾼다** — 응답 값은 **다음 페이지 첫 항목의 id**, 요청은 **포함 경계**
(`id <= :nextNotificationId`). `size + 1` 조회의 초과분 1건이 정확히 그 항목이라 추가 쿼리가 없다.
요청·응답을 **같은 이름**으로 맞춰 *"받은 값을 그대로 보낸다"* 가 이름에서 드러나게 한다.

⚠️ **ADR-0012 §2 "없는 키를 보내도 에러가 아니다"는 유지된다** — 그 항목이 사이에 삭제돼도 `<=` 라 그 이하가 온다.

🔵 **다른 목록에 확대할 때의 규칙**: `next{Entity}Id` (요청·응답 동일) + `isPageEnd`. 기준 키가 id 가 아니게 되면
이름도 그 키를 따른다.

## 결과

**좋은 것**
- 클라이언트가 CarOwnerRenew 페이징 패턴을 그대로 이식할 수 있다
- 파라미터 이름만으로 페이징 기준(알림 id)이 드러난다

**대가**
- 끝 신호가 둘이 됐다 — 불변식 테스트가 유일한 방어다. 테스트를 지우면 조용히 어긋날 수 있다
- 🔴 **breaking change** — 앱·서버 동시 반영 필요(출시 전이라 허용)
- 기준 키를 이름에 박았으므로 정렬 축을 바꾸면 이름도 바뀐다(= 계약 변경). ADR-0012 의 opaque `cursor` 가 피하던 비용이다
