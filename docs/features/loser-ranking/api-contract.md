# API Contract — 개돼지 랭킹 (loser-ranking)

- **feature-id**: loser-ranking
- **상태**: 🔴 `confirmed` (2026-08-26) — 쟁점 5개 + `totalChallenges` 추가까지 backend·mobile·design 3자 합의
  - 이후 변경은 `change-log.md` 기록 + 아래 "협의 이력" append
- **작성**: 2026-08-26 pm-lead (초안) → 2026-08-26 backend-dev (구체화·확정안)
- **소유**: backend-dev
- **상위 spec**: [spec.md](./spec.md)

## 엔드포인트 요약

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| GET | `/api/v1/rankings/losers` | 나 + accepted 친구의 패배 랭킹 (서버 정렬·rank 부여) | Bearer JWT |

**신규 1건이 이 feature 의 전부다.** 마이그레이션 0건 — `user_stats`(V1+V10) 와 `friendships`(V1) 를
읽기만 한다.

---

## GET /api/v1/rankings/losers

### 설명

**나 + accepted 친구**의 누적 전적을 패배 기준으로 줄 세워 반환한다. 정렬과 `rank` 부여는 **전부 서버**가
한다 — 앱은 받은 배열을 그 순서대로 그린다.

### 인증

- 방식: `Bearer JWT`
- 인증 실패 시 `code=401` (ADR-0009 — access 만료면 앱이 자동 갱신 후 재요청)

### Path / Query Parameters

**없다.** 파라미터 0개, 요청 바디 없음. 범위("나 + 내 친구")가 토큰의 userId 로 완전히 결정된다.

### 성공 Response (HTTP 200)

```json
{
  "error": false,
  "code": 200,
  "message": "",
  "data": {
    "rankings": [
      { "rank": 1, "userId": 3, "nickname": "준혁",   "profileImageUrl": null,
        "isMe": false, "losses": 25, "lossRate": 78, "currentLossStreak": 7, "totalChallenges": 32 },
      { "rank": 2, "userId": 1, "nickname": "이우건", "profileImageUrl": null,
        "isMe": true,  "losses": 12, "lossRate": 30, "currentLossStreak": 0, "totalChallenges": 40 },
      { "rank": 3, "userId": 8, "nickname": "지민",   "profileImageUrl": null,
        "isMe": false, "losses": 0,  "lossRate": 0,  "currentLossStreak": 0, "totalChallenges": 0 }
    ]
  }
}
```

| 필드 | 타입 | null | 설명 |
|---|---|---|---|
| `rank` | Int | ❌ | **1부터 연속 고유값.** 공동 순위 없음 (§1) |
| `userId` | Long | ❌ | `users.id`. "나" 판정용이 **아니다** — `isMe` 를 봐라 (§3) |
| `nickname` | String | ❌ | `users.nickname` |
| `profileImageUrl` | String | ✅ **nullable** | 이 응답의 **유일한** nullable. 🔴 **실제로 값이 들어온다** — §6 |
| `isMe` | Boolean | ❌ | 서버 부여. 목록 중 정확히 **1건만** true (§3) |
| `losses` | Int | ❌ | `user_stats.losses`. row 없으면 0 (§4) |
| `lossRate` | Int | ❌ | **0~100 정수 %**. 서버 계산. 0전이면 0 (§2) |
| `currentLossStreak` | Int | ❌ | `user_stats.current_loss_streak`. row 없으면 0 |
| `totalChallenges` | Int | ❌ | `user_stats.total_challenges`. row 없으면 0. 🔴 **정렬 키가 아니다** — 표시 분기 전용 (§9) |

서버 쪽 타입:

```kotlin
data class LoserRankingResponse(
    val data: LoserRankingData,
) : BaseResponse()

data class LoserRankingData(
    val rankings: List<LoserRankingItem>,
)

data class LoserRankingItem(
    val rank: Int,
    val userId: Long,
    val nickname: String,
    val profileImageUrl: String?,
    val isMe: Boolean,
    val losses: Int,
    val lossRate: Int,
    val currentLossStreak: Int,
    val totalChallenges: Int,
)
```

시간 필드가 없다 — ADR-0010 의 `yyyy-MM-dd HH:mm:ss` (KST) 규칙이 적용될 대상이 이 응답엔 하나도 없다.
`user_stats.updated_at` 은 화면이 쓰지 않으므로 내보내지 않는다.

---

## 쟁점 확정 — 5건

### §1. 정렬 우선순위 + 동률

```
losses DESC → currentLossStreak DESC → lossRate DESC → userId ASC
```

기획 정의의 나열 순서("**총 패배 수·연패·패율**")를 그대로 우선순위로 읽었다. 나열이 곧 우선순위라는
해석이 가장 방어 가능하고, 서사(*"많이 진 놈이 대장"*)와도 일치한다.

🔴 **`lossRate` 를 1차 키로 두면 1전 1패(100%)가 25패(78%)를 제치고 개돼지왕이 된다.**
그건 기획 서사의 정반대다. 패율은 "적게 한 사람"을 위로 올리는 힘이 있어서 단독 1차 키가 될 수 없다.
그래서 3차다.

🔴 **`userId ASC` 는 장식이 아니라 결정성 타이브레이커다.** 앞 3키가 모두 같은 두 사람(예: 둘 다 0전 0패
— 챌린지를 아직 안 한 친구들은 **전부 여기 해당한다**)의 순서를 PostgreSQL 이 매 호출마다 다르게 줄 수
있다. 그러면 **새로고침할 때마다 포디움 1·2위가 자리를 바꾸고**, 재현 가능한 테스트도 못 쓴다.

#### 🔴 `currentLossStreak == 0` 인 1위는 **정상적으로 발생한다** (design 질의 회신)

rank-design 이 *"연패 0 인 사람이 1위가 될 수 있나"* 를 물었다. **된다.** `losses` 가 1차 키이므로
**25패인데 최근 몇 판을 이겨 현재 연패가 0인 사람**이 개돼지왕이 된다. 누적 패배가 왕좌의 근거지
"최근에 지고 있는 중"이 근거가 아니다.

⚠️ Lovable 정본이 1위 캡션에 연패를 **무조건** 찍는 구조라 그대로 두면 화면에 **`🐷0연패 · 25패`** 가
뜬다(목데이터 1위가 항상 `lossStreak: 7` 이라 mock 에서는 안 드러난다). design.md §1.2.5 가
`currentLossStreak > 0` 조건부로 교정했고 **그 조건부는 불필요하지 않다 — 반드시 필요하다.**

**계약 변경은 없다**(순수 표시 분기). 여기 적어 두는 이유는 나중에 누가 이걸 **버그로 오해**하지 않게 하기
위해서다 — 정렬 규칙의 정상 귀결이다.

**공동 순위는 없다 — `rank` 는 1,2,3,4… 연속 고유값이다.**
위 4키가 전순서(total order)를 만들므로 동률이 남지 않는다. Top3 포디움이 1/2/3 자리를 하나씩 그리는
구조라 공동 1위가 오면 레이아웃이 깨지는데, **그 방어를 앱에 시키지 않고 서버가 원천 차단**한다.

### §2. `lossRate` — 계산 주체·형식·0÷0

**서버 계산. `Int`, 0~100 정수 %, 반올림(HALF_UP). `total_challenges == 0` 이면 `0`.**

- 정렬 키이므로 클라 재계산은 **금지**다. challenge-result 계약 §2.2 의 **"파생 계산 0"** 원칙 승계 —
  같은 규칙의 두 번째 사본을 앱에 심지 않는다.
- Lovable `ranking.tsx` 가 `패배율 N%` 로 정수 표기한다. 앱은 받은 수에 `%` 만 붙인다.

🔴 **0÷0 에 `null` 을 주지 않는 이유**: 앱이 "표시 안 함"과 "0%"를 매번 분기해야 하고, **정렬 키가 null 이
되어 순서 정의 자체가 흔들린다**(0전 유저가 여럿이면 그들끼리의 순서가 정의되지 않는다).
**진 적이 없으면 패배율은 0% 다** — 이건 폴백이 아니라 사실 진술이다.

🔴 **정렬도 표시값(반올림 후 정수)으로 한다.** 반올림 전 실수로 정렬하면 화면에 똑같이 `78%` 로 보이는 두
사람의 순서가 갈리는데 **사용자가 이유를 알 방법이 없다.** 보이는 것과 정렬되는 것이 같은 수여야 한다.

> ~~⚠️ `totalChallenges` 는 응답에 넣지 않는다. 넣으면 앱이 패율을 재계산할 길을 열어 준다.~~
> 🔴 **뒤집혔다 — §9 참조.** 예고한 대로 "필요해지면 추가"가 같은 날 왔고, **기각 근거 자체도 부실했다.**

### §3. "나" 식별 → `isMe: Boolean` (서버 부여)

앱이 로그인 userId 를 들고 `userId` 를 대조하는 방식은 **두 번째 진실 소스**를 만든다.
`myResult` 선례(파생 계산 0) 그대로 서버가 판정해 내린다.

🔴 **challenge-result 에서 `amIChallenger: Boolean` 을 기각했던 논거가 여기엔 적용되지 않는다.**
같은 타입인데 판정이 갈리는 근거는 **실패 모드의 방향**이다:

| | 키 누락 시 (kotlinx.serialization 이 `false` 로 채움) | 성격 |
|---|---|---|
| `amIChallenger` (기각됨) | 관점이 **반대로 뒤집혀 승리를 "패배"로 그린다** | **틀린 걸 보여주는 실패** |
| `isMe` (채택) | "나" 하이라이트가 **안 그려질** 뿐 | **없는 게 보이는 실패** |

`false` 기본값으로는 **남을 나로 표시하는 방향의 실패가 만들어지지 않는다.** 한 명도 강조가 안 되는 것은
사용자가 즉시 알아채는 종류의 고장이고, 데이터를 거짓으로 읽지도 않는다.

`userId` 는 계속 내려준다(친구별 전적 화면 등 후속 진입에 필요). 다만 **"나" 판정의 정본은 `isMe`** 다.

**서버 보증: `rankings` 안에 `isMe == true` 인 항목이 정확히 1건 존재한다.**

#### `data.myRank` 는 **넣지 않는다** (2026-08-26 확정)

내가 "화면이 요구하면 넣겠다"고 열어 뒀는데, mobile 이 **더 나은 기준**을 세워 닫았다:
**"구할 수 있어서"가 아니라 그 값이 이미 같은 응답 안에 있어서**다.

`find { it.isMe }?.rank` 는 **이미 메모리에 있는 리스트의 조회**지 두 번째 네트워크 호출도 파생 계산도
아니다. `rank` 는 서버가 부여한 값이고 앱은 그걸 **읽기만** 한다 — 랭킹 규칙의 사본이 앱에 생기지 않는다.
`lossRate` 재계산 금지와는 **성격이 다른 축**이다.

`myRank` 가 정당해지는 조건은 **목록 없이 순위만 그려야 할 때**(별도 엔드포인트/부분 응답)인데
이 API 는 목록을 통째로 준다. design.md §1.1 헤더 명세에도 "내 순위" 고정 바가 없다(제목+부제 2줄).
고정 바가 나중에 생겨도 같은 응답에서 뽑으면 된다.

### §4. `user_stats` row 부재 유저

**LEFT JOIN + 전부 0.** `losses: 0`, `lossRate: 0`, `currentLossStreak: 0`.
챌린지를 한 번도 안 한 친구도 **목록에서 빠지지 않는다.**

home-feed `GET /record` 의 0 폴백(`UserRecord.empty`) 선례를 그대로 승계한다. 도메인에 이미
`UserRecord.empty(userId)` 가 있고 같은 의미다 — 다만 이 API 는 N명을 한 번에 읽으므로 폴백을 **SQL
`COALESCE`** 로 처리한다(N+1 회피). 값의 정의는 동일하다.

### §5. 친구 0명

🔴 **`rankings` 는 절대 비지 않는다. 최소 1건(나)이 서버 불변식이다.**
"나 + accepted 친구" 라는 범위 정의상 나는 무조건 포함된다.

이 불변식은 서버 슬라이스 테스트로 고정한다.

> ~~→ 앱의 빈 상태 판정은 `rankings.size == 1` 이다.~~
> 🔴 **판정식은 계약에서 뺐다 (2026-08-26, mobile 요청 — 타당하다).** 계약이 정할 것은 **불변식**이고
> 판정식은 **앱 구현**이다. `size == 1` 은 불변식을 *암묵적으로* 인코딩하는데, mobile 은
> `count { !it.isMe } == 0` 을 쓴다 — *"친구가 없다"* 가 코드에 그대로 읽혀서다. 불변식이 성립하는 한
> 두 식은 **항상 같은 답**을 내므로 어느 쪽도 계약 위반이 아니다.
>
> ⚠️ 그리고 **빈 상태의 정의가 아직 안 닫혔다** — spec 은 *"친구가 없으면 (또는 아무도 챌린지를 안
> 했으면)"* 이라 썼고, design.md §3.2 는 참가자 수로 분기(N≥3 만 포디움, N=1·2 는 명단+빈 상태 카드)한다.
> 판정식을 계약에 박아 뒀다면 **계약과 화면이 어긋난 것처럼 보였을 것**이다. 불변식만 남기는 게 맞다.

**기각된 안 — 친구 0명이면 빈 배열**: 그러면 *"친구를 추가해보세요"* 화면에 내 기록을 곁들이는 디자인이
나중에 **불가능해진다.** 데이터를 주고 앱이 안 그리는 쪽은 되돌릴 수 있고, 안 주는 쪽은 계약 변경이
필요하다.

---

## §9. 🔴 `totalChallenges: Int` 추가 (2026-08-26) — §2 의 결정을 뒤집는다

### 왜 뒤집혔나

**§2 가 "안 넣는다"고 했는데 같은 날 뒤집혔다.** design.md §1.3.3 이 캡션을 이렇게 확정했기 때문이다:

| 조건 | 캡션 |
|---|---|
| `totalChallenges == 0` | **`아직 기록 없음`** (캡션 전체 대체) |
| `totalChallenges > 0` | `{losses}패 · 패배율 {lossRate}%` |

🔴 **현재 shape 으로는 이 분기를 앱이 도출할 수 없다.** 챌린지를 한 번도 안 한 사람과 **전승한 사람**이
둘 다 `losses = 0, lossRate = 0` 으로 와서 **글자 하나까지 같은 행**이 된다. 정반대 상태인데.

그리고 이건 **§4 결정의 완성 조건**이다 — `user_stats` row 부재 유저를 굳이 목록에 남기기로 한 이유가
*"친구인데 왜 없지"* 를 막는 것이었는데, **들어와서 무의미한 행이 되면 목적을 절반만 달성한다.**
명단 하단에 신규 사용자와 안 지는 사람이 같은 구간에 쌓여 그 구간의 정보량이 0 이 된다.

### ⚠️ 기각 근거가 애초에 부실했다 — 기록해 둔다

§2 에서 내가 든 이유는 *"넣으면 앱이 패율을 재계산할 길을 열어 준다"* 였다. **약한 논거다.**
mobile 지적대로 **앱이 재계산하지 않는 건 계약·규율의 문제지 데이터를 감춰서 강제할 일이 아니고,
그 논리를 밀면 `losses` 도 못 준다.**

넣지 않을 **진짜** 이유는 *"지금 쓸 화면이 없다"*(YAGNI) 하나였고, design.md 가 도착한 순간 그게 사라졌다.
🔴 **기각 사유를 실제 이유보다 강하게 적으면, 그 사유가 무너질 때 결정 전체가 흔들린 것처럼 보인다.**

### shape 판정 — `hasRecord: Boolean` 이 아니라 `Int` 다

pm-lead 가 "요구는 승인, shape 은 계약 소유자가 확정"으로 넘겼다. **`totalChallenges: Int` non-null.**

| | `totalChallenges: Int` ✅ | `hasRecord: Boolean` ❌ |
|---|---|---|
| 서버가 소유하는 것 | **사실** (컬럼 값 그대로) | **규칙** ("기록 있음"의 정의) |
| 정의가 바뀌면 | 앱의 `== 0` 만 본다 | **서버·앱 양쪽**을 봐야 한다 |
| 추가 비용 | **0** — 이미 `lossRate` 분모로 읽고 있다 | 0 (같은 값에서 파생) |
| 후속 재사용 | "N전 M패" 표기 등에 그대로 | 없음 |

🔴 **불리언은 규칙을 하나 더 서버로 옮긴다.** 이 feature 는 *"규칙은 한 곳에만"* 을 세 번(정렬·패율·판정)
지켜 왔는데 여기서 굳이 새 규칙을 만들 이유가 없다. 앱은 `== 0` 만 보면 된다.

### 🔴 재계산 금지 규약을 이 필드로 **확장**한다

`totalChallenges` 가 생겼다고 **`lossRate` 를 `losses / totalChallenges` 로 다시 계산하지 마라.**
서버는 그 몫을 **반올림한 정수**로 만들고 **그 정수를 정렬 3차 키로도 쓴다**(§2). 앱이 다시 나누면
반올림 방식이 조금만 달라도 **표시값이 서버의 정렬 순서와 어긋난다** — 화면에서 설명 불가능한 상태다.

**`totalChallenges` 의 용도는 `== 0` 판별 하나다. 정렬 키가 아니다.**

## §6. 에러 Response — 🔴 401 은 HTTP 200 이 **아니다** (2026-08-26 실측 정정)

| HTTP | body `code` | 상황 |
|------|------|------|
| **401** | 401 | 토큰 없음 / 만료 / 서명 불일치 |

```
HTTP/1.1 401
{"error":true,"code":401,"message":"토큰이 만료되었거나 유효하지 않습니다"}
```

⚠️ **초안에 "ADR-0002 — 항상 HTTP 200" 이라고 적었는데, 인증 실패 경로는 그 규칙의 예외다.**
`UnauthorizedEntryPoint` 가 SecurityFilterChain 단계에서 **HTTP 401 + BaseResponse 본문**을 직접 쓴다 —
요청이 컨트롤러·`GlobalExceptionHandler` 에 도달하기 전이라 "항상 200" 이 적용될 자리가 없다.

🔴 **이건 이 feature 가 만든 동작이 아니다.** 같은 서버에서 기존 `GET /api/v1/record` 를 토큰 없이
불러 **바이트 단위로 같은 응답**임을 확인했다(§7). 프로젝트 전역 동작이고, 모바일 Ktor `Auth(bearer)`
플러그인이 **HTTP 401 을 트리거로** refresh 하는 구조라 이 편이 오히려 맞다.
**계약 문서가 틀렸던 것이지 서버가 틀린 게 아니다.**

🔴 **비즈니스 에러(700/701/702/703/705)는 0건이다.**
내 `users` row 는 인증이 통과한 이상 항상 존재하고, 친구 0명도 `user_stats` row 부재도 **정상 응답**이다.
7xx 가 나올 경로가 설계상 없다 — 앱은 이 API 에 스낵바·다이얼로그 분기를 짤 필요가 없다.

인프라 장애(DB down)만 HTTP 5xx.

## §7. 🔴 `profileImageUrl` 은 "항상 null" 이 아니다 (2026-08-26 실측 정정)

초안과 최초 제안에서 *"지금은 사실상 항상 null"* 이라고 적었다. **틀렸다.**
실서버 응답에 **카카오 CDN 원본 URL 이 그대로 실려 나온다**:

```
"profileImageUrl": "http://img1.kakaocdn.net/thumb/R640x640.q70/?fname=http%3A%2F%2Ft1.kakaocdn.net%2Faccount_images%2Fdefault_profile.jpeg"
```

| 계정 종류 | 값 |
|---|---|
| 카카오 로그인 사용자 | **URL 있음** (`users.profile_image_url` 을 카카오가 채운다) |
| `dev-test-login` 테스트 계정 | `null` (테스트 로그인이 이 컬럼을 채우지 않는다) |

### 🔴 그러나 **이번 feature 의 화면 스코프는 이니셜 placeholder 다** (pm-lead 판정, 2026-08-26)

> ~~⚠️ 모바일 영향: 이니셜 placeholder 만 구현하면 실사용자 아바타가 통째로 안 나온다.
> `profileImageUrl != null` 이면 이미지 로드, null 이면 이니셜 — 두 갈래가 다 필요하다.~~
> 🔴 **내가 여기서 실측 사실로부터 스코프 결론까지 밀고 나간 것이 월권이었다.** 아래로 정정한다.

**사실**(URL 이 실제로 온다)은 유효하다. **스코프 결론**(두 갈래를 다 구현해라)은 **철회한다.**
아바타 활성화는 **"기존 화면 일괄" 백로그 건**이고 랭킹 화면 하나에 얹을 범위가 아니다 —
`http://` **평문**의 iOS ATS / Android cleartext 정책 축까지 딸려오기 때문이다.

| | 이번 feature |
|---|---|
| **계약** | `profileImageUrl` 키를 **그대로 내린다** (값이 있을 수 있는 정상 nullable, #24) |
| **화면** | **이니셜 placeholder 만** — design.md 확정이 정본 |
| **아바타 이미지 로드** | ❌ **범위 밖.** 백로그(기존 화면 일괄 + 평문 축 + 랭킹 화면 포함)로 등재됨 |

#### ⚠️ 이 계약에 **미결 요구는 없다** — https 정규화는 백로그 선행 조건이다

rank-design 이 *"서버가 `profileImageUrl` 을 `https` 로 정규화해 달라"* 를 요구로 올렸다가
**본인이 철회**했고(design.md §8-⑥ 취소선 + §8.1 사유), pm-lead 가 **백로그 "아바타 활성화(기존 화면
일괄)" 항목의 선행 조건 ①로 이관**했다 (2026-08-26).

🔴 **이 feature 의 어떤 수용 기준도 그 URL 을 그리지 않으므로 계약이 질 조건이 아니다.** 그리고 정규화의
올바른 지점은 **랭킹 응답이 아니라 저장 시점(카카오 로그인) + 기존 row 정리**다 — 응답 한 곳만 고치면
`user-info`·`friends` 등과 갈라진 **반쪽 수정**이 된다.

**구현 재료(https 서빙 실측 · 수정 지점 · 치환 함정)는 백로그 항목 `profileImageUrl 화면 적용` 이
갖는다. 여기에 옮겨 적지 않는다.**

> ⚠️ **처음엔 그 사실 3개를 여기에 표로 옮겨 적었다가 뺐다.** rank-design 이 같은 제안을 거절하며 든
> 근거가 나에게도 그대로 적용된다 — **같은 사실을 두 문서가 들고 있으면 한쪽만 고쳐지는 날이 온다.**
> (이 세션에만 그 실패를 세 번 봤다: EmptyState 사본 3개의 모서리 값이 갈렸고, 🐷 가 두 뜻으로
> 갈렸고, design.md 의 *"Coil 배선 0건"* 이 코드보다 낡았다.)
>
> 역할을 이렇게 가른다 — **계약**은 *"왜 이 계약의 조건이 아닌가"*, **백로그 항목**은 *"어떻게 켜는가"*.
> 계약이 구현 절차까지 들면 백로그가 갱신될 때 계약이 조용히 낡는다.

⚠️ **앱은 이 필드를 받되 이번엔 그리지 않는다.** 계약과 화면 스코프는 별개다 —
키를 내리는 것이 나중에 아바타를 켤 때 **계약 변경 없이** 되게 해 준다.

> 이 정정이 왜 늦게 나왔나: 개발 DB 에 카카오 실계정이 **1개뿐**(`이우건`)이고 나머지 3개가 전부
> 테스트 계정이라, 실서버를 안 찔러 봤으면 "전부 null" 이라는 인상이 그대로 굳었을 것이다.
> **슬라이스 테스트도 통합 테스트도 이 축을 못 덮는다** — 픽스처 값은 내가 정하기 때문이다.

## 페이지네이션 — 미적용

목록 길이가 **친구 수 + 1** 로 묶인다. `GET /friends`·`GET /challenges/active` 도 전부 비페이지네이션이라
프로젝트 통일 규칙(한 방식으로 통일)과도 정합하다.

**재검토 조건**: 한 사용자의 목록이 **200건**을 넘는 사례가 관측되면. 그 전엔 열지 않는다.
(친구 목록 자체에 상한이 없으므로 "언젠가"는 온다 — 다만 지금 여는 것은 쓰지 않을 커서 규약을 계약에
박제하는 일이다.)

## 모바일측 주의사항

- **정렬·rank 를 다시 계산하지 마라.** 받은 배열 순서 = 화면 순서. `rank` 는 서버 값을 그대로 쓴다.
- 🔴 **`lossRate` 를 재계산하지 마라.** `totalChallenges` 를 주게 됐다고 나누지 마라 — 서버가 반올림한
  정수를 **정렬 3차 키로도** 쓰기 때문에, 앱이 다시 나누면 표시값이 서버 정렬과 어긋날 수 있다 (§9).
- **`totalChallenges` 의 용도는 `== 0` 판별 하나다** — `아직 기록 없음` 캡션 분기 (§9).
- 🔴 `profileImageUrl` 은 이 응답의 **유일한 nullable** 이고 **null 도 URL 도 실제로 온다** (§7).
  **다만 이번 feature 에서는 그리지 않는다** — 화면은 **이니셜 placeholder 만**(design.md 정본,
  pm-lead 스코프 판정). 키는 받되 이미지 로드는 배선하지 마라. 아바타 활성화는 별도 백로그 건이다.
- 🔴 이모지 아바타(😤😏)는 **Lovable mock 값이고 도메인에 필드가 없다** — 서버가 줄 수 있는 게 없다.
- 🔴 `rankings` 는 **절대 비지 않는다** (최소 1건 = 나). `isEmpty()` 로 빈 상태를 판정하면
  **영원히 false 다.** 판정식은 앱이 정한다 (§5).
- null 이어도 키는 항상 존재한다(#24 — 서버에 `@JsonInclude(NON_NULL)` 미설정).

## 백엔드측 주의사항

- 읽기 전용 단일 트랜잭션(`@Transactional(readOnly = true)`). **쓰기 0, 이벤트 발행 0.**
- 영향 테이블: `friendships`(읽기) · `users`(읽기) · `user_stats`(읽기). **마이그레이션 0건.**
- 친구 목록 + 전적을 **native query 1회**로 읽는다 — `findFriendsOf` 후 N번 `findByUserId` 하면 N+1 이다.
- 판정 배치(challenge-result)와 동시에 읽어도 손상 없다 — readOnly 스냅샷을 읽을 뿐이고,
  이 API 는 집계를 다시 세지 않는다(`user_stats` 를 그대로 읽는다).
- `WireShapeContractTest` 에 `LoserRankingResponse` 등재.

---

## §8. 🔴 실서버 실측 (2026-08-26) — 정렬 규칙을 실데이터로 증명했다

challenge-result 가 남긴 집계 실데이터(`user_stats` 4행)를 그대로 썼다. 사용자 서버(`:8080`, PID 10722)는
건드리지 않고 **`:8099` 별도 기동** + `dev-test-login`.

### 🔴 테스터1(user 14) 시점 — wire 원문 (`totalChallenges` 포함 최종본, 2차 실측)

**이 원문이 모바일 wire 픽스처의 정본이다.** `remote/mapper` 에 그대로 박으면 된다.

```json
{"data":{"rankings":[
  {"rank":1,"userId":14,"nickname":"테스터1","profileImageUrl":null,"isMe":true, "losses":4,"lossRate":80, "currentLossStreak":0,"totalChallenges":5},
  {"rank":2,"userId":15,"nickname":"테스터2","profileImageUrl":null,"isMe":false,"losses":3,"lossRate":100,"currentLossStreak":3,"totalChallenges":3},
  {"rank":3,"userId":1, "nickname":"이우건","profileImageUrl":"http://img1.kakaocdn.net/thumb/R640x640.q70/?fname=http%3A%2F%2Ft1.kakaocdn.net%2Faccount_images%2Fdefault_profile.jpeg","isMe":false,"losses":3,"lossRate":75,"currentLossStreak":0,"totalChallenges":4},
  {"rank":4,"userId":16,"nickname":"테스터3","profileImageUrl":null,"isMe":false,"losses":2,"lossRate":100,"currentLossStreak":2,"totalChallenges":2},
  {"rank":5,"userId":17,"nickname":"테스터4","profileImageUrl":null,"isMe":false,"losses":0,"lossRate":0,  "currentLossStreak":0,"totalChallenges":0}
]},"error":false,"code":200,"message":""}
```

**표시 분기가 이 한 응답에 전부 들어 있다** (mobile 요청 4요소 + design 조건부 2개):

| 분기 | 어느 행 |
|---|---|
| 친구 여럿 + 나 포함 (`isMe` 정확히 1건) | 5건 중 rank 1 |
| 🔴 **`totalChallenges == 0`** → `아직 기록 없음` 캡션 (§9) | **rank 5 (user 17)** |
| `currentLossStreak > 0` → 🐷 뱃지 | rank 2·4 |
| 🔴 **`currentLossStreak == 0` 인 1위** → 연패 절 생략 (design §1.2.5) | **rank 1** |
| `profileImageUrl` 있음 → 이미지 로드 (§7) | rank 3 |
| `profileImageUrl` null → 이니셜 placeholder | 나머지 4건 |

⚠️ **rank 5(user 17 `테스터4`)는 이 실측을 위해 일부러 심은 계정**이다 — `users` row 만 만들고
`user_stats` row 는 만들지 않아 **`LEFT JOIN` + `COALESCE` 폴백이 실제 SQL 에서 타도록** 했다.
측정 후 friendship·user 를 삭제해 원복했다(아래).

**이 4행이 §1 의 정렬 결정을 우연이 아니라 실증으로 만든다:**

| 확인된 것 | 증거 |
|---|---|
| 1차 키가 `losses` | 14(4패) → 15·1(3패) → 16(2패) |
| 2차 키가 연패 | 15 와 1 이 **둘 다 3패**인데 15(연패 3)가 1(연패 0)보다 위 |
| 🔴 **`lossRate` 가 1차 키가 아니다** | **15 와 16 은 패율 100%인데 rank 2·4**, 80% 인 14 가 rank 1 |
| `isMe` 정확히 1건 | 14 만 true |
| null 이어도 키 상존 | `"profileImageUrl":null` 이 원문에 그대로 |

세 번째 줄이 핵심이다 — 패율을 1차 키로 뒀다면 **100% 인 두 명이 포디움 1·2위**를 먹고 4패인 14 가
밀렸다. 계약이 말로 주장한 것을 **실데이터가 그대로 재현**했다.

### 범위 격리 — 세 계정이 서로 다른 목록을 본다

| 요청자 | 결과 | 검증된 것 |
|---|---|---|
| 테스터1 (14) | 4건 — 14, 15, 1, 16 | 친구 3명 전원 |
| 테스터2 (15) | **2건** — 14, 15 | 🔴 **1·16 은 "친구의 친구" 라 제외** |
| 테스터3 (16) | 3건 — 14, 1, 16 | 15 제외 |

같은 DB 인데 요청자마다 목록이 다르다 — `friendships` 서브쿼리가 **요청자 기준**으로 동작함을 증명한다.
전체 유저 목록이 새어 나오지 않는다는 뜻이기도 하다.

### DB 영향 — 원복 완료

랭킹 API 자체는 **쓰기 0** 이다. 실측이 남긴 변경은 둘뿐이었고 **양쪽 다 원복했다**:

| 변경 | 원복 |
|---|---|
| `dev-test-login` 의 refresh 토큰 회전 (`users.refresh_token_hash`/`refresh_token_issued_at`, **테스트 계정 14·15·16 만**) | 실측 **전** 스냅샷으로 `UPDATE` → **diff 0** |
| 2차 실측용 시드 (`users` 1행 = 테스터4, `friendships` 1행) | `DELETE` 2건 |

원복 후 `users` 4행 · `friendships` 4행 · `user_stats` 4행 전부 실측 전과 동일함을 재조회로 확인했고,
refresh 컬럼도 **스냅샷과 완전 일치**한다. 실사용자(user 1) row 는 처음부터 끝까지 무변경.
사용자 서버(:8080, PID 10722)는 실측 내내 **무중단**.

### ⚠️ 이 실측이 덮지 못한 것

- ~~**0÷0 (챌린지 0회) 경로** — 개발 DB 의 4명이 전부 `user_stats` row 를 갖고 있어 `COALESCE` 폴백이
  한 번도 안 탔다.~~ → 🔴 **2차 실측에서 해소.** `user_stats` row 가 없는 계정(user 17)을 심어
  **`LEFT JOIN` + `COALESCE` 0 폴백이 실제 SQL 에서 동작**함을 확인했다 (`totalChallenges: 0`,
  `losses: 0`, `lossRate: 0`, 목록에서 빠지지 않음). **native query 는 슬라이스가 못 덮는 유일한 축이라
  이게 중요하다.**
- **친구 0명 → 1건** 불변식은 **여전히 안 탔다.** 네 계정 모두 친구가 있다. 컨트롤러 슬라이스
  테스트로만 고정돼 있다.

### ⚠️ 알려진 경계 — `users` 에 내 row 가 없으면 `rankings: []` 가 나간다

하드 삭제된 사용자가 유효 토큰을 들고 오는 경우다. 그러면 §5 의 "최소 1건" 불변식이 깨지고 앱의
`size == 1` 빈 상태 판정이 조용히 어긋난다. **방어 코드를 넣지 않았다** — 탈퇴는 `status` 변경이라
row 가 남고(하드 삭제 경로가 없다), 관측된 적도 없는 가정이기 때문이다. 하드 삭제를 도입하게 되면
**이 줄로 돌아와라.**

---

## 협의 이력

| 일시 | 작성자 | 변경 |
|---|---|---|
| 2026-08-26 | pm-lead | 초안 — 신규 1건 골격 + 쟁점 5개 |
| 2026-08-26 | pm-lead | **스코프 판정**: `profileImageUrl` 실 URL 발견은 유효하나 **이번 feature 는 이니셜 placeholder 유지**. 아바타 활성화는 "기존 화면 일괄" 백로그(평문 `http://` ATS/cleartext 축 포함). §7 의 "두 갈래를 다 구현해라"는 backend-dev 가 철회 |
| 2026-08-26 | backend-dev | 🔴 **`confirmed` 전이.** `totalChallenges: Int` 추가(§9) — design.md §1.3.3 의 `아직 기록 없음` 분기가 현 shape 으로 도출 불가. `hasRecord: Boolean` 대신 `Int` 선택(불리언은 "기록 있음"의 **정의**를 서버가 소유하게 만든다). §2 의 기각 근거가 부실했음도 함께 기록. `myRank` **미포함** 확정, §5 판정식 삭제(불변식만 유지), §1 에 "연패 0 인 1위 정상 발생" 명시 |
| 2026-08-26 | rank-mobile | 쟁점 1·2·3·4·5 전부 동의. `myRank` 미포함 요청(같은 응답에 있는 값이라 조회지 파생 계산이 아니다). `profileImageUrl` 유지로 정정(초안의 "실컬럼 없으면 빼자"를 철회 — 컬럼 존재 확인). §5 판정식은 계약이 아닌 앱 구현이라 제외 요청. `size == 1` 대신 `count { !it.isMe } == 0` 사용 |
| 2026-08-26 | rank-design | `isMe` 강한 요구(`isMe` 행은 닉네임을 `"나"` 로 치환), `lossRate` 서버계산+`0`(null 금지), 친구 0명은 `[{나}]`. **`totalChallenges` 추가 요구**(§1.3.3). 정렬 질의 — "연패 0 인 1위가 가능한가" |
| 2026-08-26 | backend-dev | **실측 정정 2건** (§6·§7). ① 인증 실패는 HTTP 200 이 아니라 **HTTP 401**(기존 `/record` 와 동일 — 계약 문서가 틀렸던 것). ② `profileImageUrl` 이 "사실상 항상 null" 이 아니라 **카카오 URL 이 실제로 온다**. ~~모바일이 이미지 로드 갈래를 반드시 구현해야 한다~~ ← **이 결론은 같은 날 철회됨**(위 pm-lead 행) — 사실은 유효하나 스코프 결론은 내 월권이었다. §8 실서버 실측 기록 추가 |
| 2026-08-26 | backend-dev | 쟁점 5개 확정안. 정렬 4키(`userId ASC` 결정성 타이브레이커 포함)·`lossRate` 정수%/0÷0=0·`isMe` 서버 부여·LEFT JOIN 0 폴백·`rankings` 최소 1건 불변식. `totalChallenges` 미포함(패율 재계산 차단), 페이지네이션 미적용+재검토 200건, 7xx 0건 명시. `myRank` 추가 여부는 모바일 회신 대기 |
