# Friends Empty State — Implementation Plan (1차 1단계)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 친구 탭의 `PlaceholderScreen`을 디자이너 산출물 기반 빈 상태 화면으로 교체. 백엔드 호출 0건, 1차 1단계 한정.

**Architecture:** 디자인 트랙(design-bridge agent dispatch → Lovable 빈 상태 화면 + `docs/features/friends/design.md`) 선행 → 모바일 트랙(`:core:designsystem`에 `FriendsEmptyState` + `:feature:friends`에 `component/FriendsTopBar` + `FriendsScreen` 교체 + ViewModel/UiState 정리).

**Tech Stack:** Kotlin Multiplatform, Compose Multiplatform, Koin (KSP annotation), `ChallengeTheme.colorScheme/typography` 디자인 토큰.

---

## 참조 spec

- 본 plan의 입력: [spec.md](./spec.md) — feature-id `friends`, 1차 1단계
- 후속 단계(1차 2단계)는 본 plan 범위 외 — spec.md "후속 계획" 섹션 참조

---

## File Structure

**디자인 트랙 (design-bridge 산출물)**:
- Create: `docs/features/friends/design.md`
- Modify: Lovable repo (`challenge-design/oathbound-challenges`)에 친구 탭 빈 상태 화면 신규

**모바일 트랙 (challenge-app)**:
- Create: `core/designsystem/src/commonMain/kotlin/com/lwg/challenge/designsystem/components/friend/FriendsEmptyState.kt`
- Create: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/component/FriendsTopBar.kt`
- Modify: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsScreen.kt` (PlaceholderScreen 교체)
- Modify: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsViewModel.kt` (정리)
- Modify: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/contract/FriendsState.kt` (`Data` 단순화)
- Modify: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsRoute.kt` (CTA + ShowMessage collect)
- Create: `feature/friends/src/commonTest/kotlin/com/lwg/challenge/feature/friends/FriendsViewModelTest.kt`
- Modify (필요 시): `feature/friends/build.gradle.kts` (`compose.materialIconsExtended` 또는 아이콘 의존성)

**PM 문서**:
- Create: `docs/features/friends/summary.md` (1차 1단계 완료 후)
- Modify: `docs/features/INDEX.md` (상태 `draft` → `partially-completed` 또는 `1차 1단계 완료`)
- Modify: `docs/backlog.md` (1차 1단계 항목 정리, 후속 항목 등재)

**메모리 규칙**:
- 모바일 dispatch 시 git 작업 금지 (`feedback_mobile_dispatch_no_git.md`) — 모바일 코드 변경은 working tree에 두고 보고. 커밋은 사용자 직접.
- Lovable ↔ 모바일 동기 (`feedback_lovable_mobile_sync.md`) — 디자인 결정은 양쪽 즉시 반영.

---

## Tasks

### Task 1: 디자인 트랙 dispatch (design-bridge)

**Files:**
- Read: `/Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/.claude/agents/design-bridge.md`
- Create (산출물): `docs/features/friends/design.md`
- Modify (산출물): Lovable repo의 친구 탭 빈 상태 화면

- [ ] **Step 1: design-bridge agent 정의 읽기**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/.claude/agents/design-bridge.md
```

- [ ] **Step 2: Agent tool로 design-bridge dispatch**

Agent tool 호출, subagent_type=claude. Prompt:

```
당신은 design-bridge 에이전트입니다. PM hub의 .claude/agents/design-bridge.md 정의를 따르세요.

작업: friends feature 1차 1단계 — 친구 빈 상태 화면 디자인.

입력 spec: /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/spec.md

실행 사항:
1. Lovable repo(`.claude/config/repos.json` design 섹션 export_dir 참조) 친구 탭 기존 화면 점검 — 친구 카드 디자인(필드/레이아웃) 파악.
2. Lovable에 친구 탭 **빈 상태 화면 신규 제작**:
   - 일러스트 또는 아이콘 1개
   - 헤드라인 (예: "아직 친구가 없어요" 류, 톤은 chord-aware로 결정)
   - 서브 텍스트 (안내 1줄)
   - stub CTA 버튼 1개 ("친구 추가하기" 라벨 후보, 무동작)
   - 디자인 시스템 토큰만 사용 (tokens.md / colors.md / styles.css)
3. `/Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/design.md` 작성:
   - 화면 구조 (Lovable JSX 추출 + Compose 매핑)
   - 사용 토큰 (color / typography / spacing / radius)
   - Compose 컴포넌트 spec:
     - `FriendsEmptyState` props (아이콘 식별자·헤드라인·서브 텍스트·CTA 라벨·onClickCta)
     - `FriendsTopBar` 구성 (제목 "친구" + 액션 슬롯 결정)
   - 친구 카드 정합 가이드 (1차 2단계 입력)
4. Lovable repo 변경 후 git 커밋(레포 자체 컨벤션) + push.

보고: design.md 경로 + Lovable 커밋 hash + 모바일 측에 필요한 정확한 문구·아이콘 식별자.

주의: 메모리 규칙 — Lovable과 모바일 양쪽 동기 (디자인 결정은 즉시 반영).
```

- [ ] **Step 3: 산출물 확인**

```bash
test -f /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/friends/design.md && echo "design.md 작성 OK"
```
Expected: "design.md 작성 OK".

- [ ] **Step 4: design.md 읽어 모바일 트랙 입력 추출**

다음 4개 정보를 design.md에서 추출해 변수로 보관:
- `FriendsEmptyState`의 정확한 props 시그니처
- 아이콘/일러스트 식별자 (Material Icon 이름 또는 painterResource 경로)
- 헤드라인 / 서브 텍스트 / CTA 라벨 정확한 문구
- `FriendsTopBar` 액션 슬롯 노출 여부

- [ ] **Step 5: PM hub 커밋**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub
git add docs/features/friends/design.md
git commit -m "docs(friends): design.md — 빈 상태 화면 가이드 (T-D1~D3)"
```

---

### Task 2: FriendsViewModelTest 작성 (TDD — 실패 확인)

**Files:**
- Create: `feature/friends/src/commonTest/kotlin/com/lwg/challenge/feature/friends/FriendsViewModelTest.kt`

- [ ] **Step 1: 테스트 파일 작성**

`feature/friends/src/commonTest/kotlin/com/lwg/challenge/feature/friends/FriendsViewModelTest.kt`:

```kotlin
package com.lwg.challenge.feature.friends

import app.cash.turbine.test
import com.lwg.challenge.feature.friends.contract.FriendsUiEffect
import com.lwg.challenge.feature.friends.contract.FriendsUiState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs

@OptIn(ExperimentalCoroutinesApi::class)
class FriendsViewModelTest {

    @BeforeTest
    fun setup() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @AfterTest
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `init 시 uiState 는 Data 로 진입한다`() = runTest {
        val viewModel = FriendsViewModel()
        assertIs<FriendsUiState.Data>(viewModel.uiState.value)
    }

    @Test
    fun `showMessage 호출 시 ShowMessage effect 가 발행된다`() = runTest {
        val viewModel = FriendsViewModel()

        viewModel.uiEffect.test {
            viewModel.showMessage("준비 중입니다")
            val effect = awaitItem()
            assertIs<FriendsUiEffect.ShowMessage>(effect)
            assertEquals("준비 중입니다", effect.message)
        }
    }
}
```

- [ ] **Step 2: 컴파일 시도 — 실패 확인**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-app
./gradlew :feature:friends:compileTestKotlinAndroid 2>&1 | tail -15
```
Expected: 컴파일 실패 — 다음 중 하나 이상:
- `assertIs<FriendsUiState.Data>` 불일치 (현재 `Data`는 `data class Data(placeholder: Unit)`이라 `assertIs`는 통과 가능, 그러나 ...) → 사실은 컴파일 통과. 한 번 실행해보고
- `viewModel.showMessage(...)` 접근 불가 — 현재 `private fun showMessage` → 컴파일 실패 **확정**.

Expected output: `Cannot access 'showMessage': it is private in 'FriendsViewModel'` 또는 동등.

---

### Task 3: FriendsUiState / FriendsViewModel 정리 (테스트 통과)

**Files:**
- Modify: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/contract/FriendsState.kt`
- Modify: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsViewModel.kt`

- [ ] **Step 1: FriendsState.kt 전체 교체**

`feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/contract/FriendsState.kt`:

```kotlin
package com.lwg.challenge.feature.friends.contract

import androidx.compose.runtime.Immutable
import androidx.compose.runtime.Stable

/**
 * 친구 탭 UI 상태.
 *
 * 1차 1단계 — 백엔드 호출 0건. 진입과 동시에 [Data].
 * 1차 2단계 도입 시 [Data] 를 `data class Data(val friends: List<Friend>)` 로 확장.
 */
@Stable
sealed interface FriendsUiState {

    @Immutable
    data object Loading : FriendsUiState

    @Immutable
    data object Data : FriendsUiState
}
```

- [ ] **Step 2: FriendsViewModel.kt 전체 교체**

`feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsViewModel.kt`:

```kotlin
package com.lwg.challenge.feature.friends

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lwg.challenge.feature.friends.contract.FriendsModalEffect
import com.lwg.challenge.feature.friends.contract.FriendsUiEffect
import com.lwg.challenge.feature.friends.contract.FriendsUiState
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import org.koin.android.annotation.KoinViewModel

/**
 * 친구 탭 ViewModel.
 *
 * 1차 1단계 — 백엔드 호출 0건. 진입과 동시에 [FriendsUiState.Data] 상태.
 * 1차 2단계 도입 시 GetFriendsUseCase 주입 + Flow 결합.
 */
@KoinViewModel
class FriendsViewModel : ViewModel() {

    private val _uiState: MutableStateFlow<FriendsUiState> = MutableStateFlow(FriendsUiState.Data)
    val uiState: StateFlow<FriendsUiState> get() = _uiState

    private val _modalEffect = MutableStateFlow<FriendsModalEffect>(FriendsModalEffect.Hidden)
    val modalEffect: StateFlow<FriendsModalEffect> get() = _modalEffect

    private val _uiEffect = MutableSharedFlow<FriendsUiEffect>()
    val uiEffect: SharedFlow<FriendsUiEffect> get() = _uiEffect

    fun dismiss() {
        _modalEffect.update { FriendsModalEffect.Hidden }
    }

    fun showMessage(message: String) {
        viewModelScope.launch {
            _uiEffect.emit(FriendsUiEffect.ShowMessage(message))
        }
    }
}
```

변경 포인트:
- `showMessage`를 `public`으로 변경 (Route가 호출).
- 생성자에서 `// TODO: 의존성을 주입하세요.` 주석 제거.
- KDoc 갱신.

- [ ] **Step 3: 테스트 실행 — 통과 확인**

```bash
./gradlew :feature:friends:testDebugUnitTest 2>&1 | tail -20
```
Expected: BUILD SUCCESSFUL, `2 tests completed, 0 failed`.

XML 결과 직접 확인:
```bash
grep 'tests=' feature/friends/build/test-results/testDebugUnitTest/TEST-*.xml | head
```
Expected: `tests="2" skipped="0" failures="0" errors="0"`.

- [ ] **Step 4: 사용자에게 working tree 변경 보고 (커밋은 사용자 직접)**

메모리 규칙(모바일 git 금지)에 따라 git add/commit 0건. 변경 파일 목록만 보고:

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-app
git status --short
```
보고 형식: "Task 3 완료. modified: FriendsState.kt, FriendsViewModel.kt + 신규 FriendsViewModelTest.kt. 빌드·테스트 통과. 커밋은 사용자 직접 부탁드립니다."

---

### Task 4: FriendsEmptyState 디자인 시스템 컴포넌트 신설

**Files:**
- Create: `core/designsystem/src/commonMain/kotlin/com/lwg/challenge/designsystem/components/friend/FriendsEmptyState.kt`

- [ ] **Step 1: design.md 가이드 재확인**

Task 1에서 추출한 4개 정보 (props 시그니처, 아이콘 식별자, 문구, topBar 액션) 다시 확인. design.md의 spec 섹션을 정확히 따름.

- [ ] **Step 2: 컴포넌트 작성**

`core/designsystem/src/commonMain/kotlin/com/lwg/challenge/designsystem/components/friend/FriendsEmptyState.kt` (디자이너가 결정한 정확한 문구·아이콘으로 교체):

```kotlin
package com.lwg.challenge.designsystem.components.friend

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.lwg.challenge.designsystem.components.VerticalSpacer
import com.lwg.challenge.designsystem.theme.ChallengeTheme

/**
 * 친구가 없는 신규 사용자용 빈 상태 컴포넌트.
 *
 * 1차 1단계 — stub CTA. [onClickCta] 는 호출부에서 placeholder/스낵바 등으로 처리.
 * 디자인 가이드: docs/features/friends/design.md.
 */
@Composable
fun FriendsEmptyState(
    title: String,
    subtitle: String,
    ctaLabel: String,
    icon: ImageVector,
    onClickCta: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = ChallengeTheme.colorScheme.primary,
            modifier = Modifier.size(64.dp),
        )
        VerticalSpacer(height = 16.dp)
        Text(
            text = title,
            style = ChallengeTheme.typography.bold18,
            color = ChallengeTheme.colorScheme.onBackground,
            textAlign = TextAlign.Center,
        )
        VerticalSpacer(height = 8.dp)
        Text(
            text = subtitle,
            style = ChallengeTheme.typography.medium14,
            color = ChallengeTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
        VerticalSpacer(height = 24.dp)
        Button(
            onClick = onClickCta,
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = ChallengeTheme.colorScheme.primary,
                contentColor = ChallengeTheme.colorScheme.onPrimary,
            ),
        ) {
            Text(text = ctaLabel, style = ChallengeTheme.typography.bold14)
        }
    }
}
```

> design.md에서 결정된 색·간격·아이콘이 다르면 이 step에서 수정 후 commit.

- [ ] **Step 3: 컴파일 검증**

```bash
./gradlew :core:designsystem:compileCommonMainKotlinMetadata 2>&1 | tail -10
```
Expected: BUILD SUCCESSFUL.

- [ ] **Step 4: 사용자에게 working tree 보고 (커밋 사용자 직접)**

---

### Task 5: FriendsTopBar 컴포넌트 신설

**Files:**
- Create: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/component/FriendsTopBar.kt`

- [ ] **Step 1: HomeTopBar 패턴 참고**

```bash
cat /Users/hwamulman/woogunProject/challenge/challenge-app/feature/home/src/commonMain/kotlin/com/lwg/challenge/feature/home/component/HomeTopBar.kt
```

- [ ] **Step 2: FriendsTopBar 작성**

design.md의 topBar 액션 슬롯 결정(예: 알림 / 검색)에 따라 액션 슬롯 노출 분기. 본 plan은 액션 미노출 default. 노출이라면 design.md에 명시된 아이콘 사용.

`feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/component/FriendsTopBar.kt`:

```kotlin
package com.lwg.challenge.feature.friends.component

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.lwg.challenge.designsystem.theme.ChallengeTheme

@Composable
internal fun FriendsTopBar(
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = ChallengeTheme.colorScheme.surface,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp)
                .padding(horizontal = 20.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Start,
        ) {
            Text(
                text = "친구",
                style = ChallengeTheme.typography.bold18,
                color = ChallengeTheme.colorScheme.onBackground,
            )
        }
    }
}
```

- [ ] **Step 3: 컴파일 검증**

```bash
./gradlew :feature:friends:compileCommonMainKotlinMetadata 2>&1 | tail -10
```
Expected: BUILD SUCCESSFUL.

- [ ] **Step 4: working tree 보고**

---

### Task 6: FriendsScreen 교체 (PlaceholderScreen → 빈 상태 컴포넌트)

**Files:**
- Modify: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsScreen.kt`

- [ ] **Step 1: FriendsScreen 전체 교체**

design.md의 정확한 문구·아이콘으로 string·icon 인자 교체. 아래는 placeholder 예시 (실제 작성 시 design.md 값으로 교체):

`feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsScreen.kt`:

```kotlin
package com.lwg.challenge.feature.friends

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Group
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.lwg.challenge.designsystem.components.ChallengeScaffold
import com.lwg.challenge.designsystem.components.friend.FriendsEmptyState
import com.lwg.challenge.designsystem.theme.ChallengeTheme
import com.lwg.challenge.feature.friends.component.FriendsTopBar
import com.lwg.challenge.feature.friends.contract.FriendsUiState

@Composable
internal fun FriendsScreen(
    uiState: FriendsUiState,
    onClickAddFriend: () -> Unit,
) {
    ChallengeScaffold(
        statusBarColor = ChallengeTheme.colorScheme.surface,
        topBar = { FriendsTopBar() },
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            when (uiState) {
                FriendsUiState.Loading -> LoadingContent()
                FriendsUiState.Data -> FriendsEmptyState(
                    title = "아직 친구가 없어요",
                    subtitle = "친구를 추가하고 함께 챌린지를 시작해보세요",
                    ctaLabel = "친구 추가하기",
                    icon = Icons.Filled.Group,
                    onClickCta = onClickAddFriend,
                )
            }
        }
    }
}

@Composable
private fun LoadingContent() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        CircularProgressIndicator(color = ChallengeTheme.colorScheme.primary)
    }
}
```

> design.md의 정확한 title/subtitle/ctaLabel/icon으로 교체.

- [ ] **Step 2: 컴파일 검증**

```bash
./gradlew :feature:friends:compileCommonMainKotlinMetadata 2>&1 | tail -10
```
Expected: BUILD SUCCESSFUL.

- [ ] **Step 3: working tree 보고**

---

### Task 7: FriendsRoute — CTA 콜백 + ShowMessage collect

**Files:**
- Modify: `feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsRoute.kt`

- [ ] **Step 1: FriendsRoute 전체 교체**

홈의 `HomeRoute` 패턴 답습 — `viewModel.uiEffect` collect해서 ShowMessage를 MainAction.showSnackBar로 표시. CTA stub은 `viewModel.showMessage("준비 중입니다")`.

`feature/friends/src/commonMain/kotlin/com/lwg/challenge/feature/friends/FriendsRoute.kt`:

```kotlin
package com.lwg.challenge.feature.friends

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.lwg.challenge.feature.friends.contract.FriendsUiEffect
import com.lwg.challenge.feature.friends.contract.FriendsUiState
import com.lwg.challenge.navigation.LocalMainAction
import org.koin.compose.viewmodel.koinViewModel

@Composable
fun FriendsRoute(
    viewModel: FriendsViewModel = koinViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val mainAction = LocalMainAction.current

    LaunchedEffect(viewModel) {
        viewModel.uiEffect.collect { effect ->
            when (effect) {
                is FriendsUiEffect.ShowMessage -> mainAction.showSnackBar(effect.message)
            }
        }
    }

    FriendsContent(
        uiState = uiState,
        onClickAddFriend = { viewModel.showMessage("준비 중입니다") },
    )
}

@Composable
private fun FriendsContent(
    uiState: FriendsUiState,
    onClickAddFriend: () -> Unit,
) {
    FriendsScreen(
        uiState = uiState,
        onClickAddFriend = onClickAddFriend,
    )
}
```

- [ ] **Step 2: 컴파일 검증**

```bash
./gradlew :feature:friends:compileCommonMainKotlinMetadata :feature:friends:compileDebugKotlinAndroid 2>&1 | tail -10
```
Expected: BUILD SUCCESSFUL.

- [ ] **Step 3: working tree 보고**

---

### Task 8: 전체 빌드 + 기존 회귀 0 검증

**Files:** (검증용, 변경 없음)

- [ ] **Step 1: 모바일 모든 ViewModel 테스트 회귀 확인**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-app
./gradlew :feature:home:testDebugUnitTest :feature:login:testDebugUnitTest :feature:friends:testDebugUnitTest 2>&1 | tail -20
```
Expected: 모두 BUILD SUCCESSFUL, fail 0건.

- [ ] **Step 2: 전체 모듈 컴파일**

```bash
./gradlew compileDebugKotlinAndroid 2>&1 | tail -15
```
Expected: 전체 BUILD SUCCESSFUL.

- [ ] **Step 3: 결과 사용자 보고**

테스트 통과 개수 / 실패 개수 / 빌드 시간을 요약. 사용자가 모바일 working tree 전체를 한 커밋으로 묶을지 단계별로 묶을지 결정 — git 작업 자체는 사용자 직접.

---

### Task 9: PM 문서 갱신 (summary.md + INDEX + backlog)

**Files:**
- Create: `docs/features/friends/summary.md`
- Modify: `docs/features/INDEX.md`
- Modify: `docs/backlog.md`

- [ ] **Step 1: summary.md 작성**

home-feed/summary.md 형식 답습. 핵심 섹션: 구현 개요 / 화면 변경 / 주요 변경 파일 / 테스트 결과 / 결정 사항 / 미해결 이슈 / 참조.

본 1차 1단계 summary는 다음을 포함:
- 1차 1단계 = 빈 상태 화면만 (백엔드 0건)
- 변경 파일 목록 (모바일 신규 2 + 수정 4 + 테스트 신규 1, PM 신규 2 + 수정 1)
- 테스트 결과 (FriendsViewModelTest 2/2 passed)
- 1차 2단계 미해결 항목 (백엔드 friendships 테이블 + GET /api/v1/friends + 모바일 도메인/Repository/UseCase + 친구 목록 LazyColumn + 카드 탭 라우팅 + CTA 라우팅)

- [ ] **Step 2: INDEX.md 갱신**

```bash
sed -i.bak 's|| friends | 친구 화면 (1차 1단계: 빈 상태 UI만, 백엔드 X) | draft | — | \[📄\](./friends/spec.md) |\
| friends | 친구 화면 (1차 1단계: 빈 상태 UI만) | partially-completed | 2026-MM-DD | \[📄\](./friends/summary.md) ||' /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/INDEX.md
rm /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub/docs/features/INDEX.md.bak
```

또는 Edit tool로 수동 갱신:
- 기존: `| friends | 친구 화면 (1차 1단계: 빈 상태 UI만, 백엔드 X) | draft | — | [📄](./friends/spec.md) |`
- 신규: `| friends | 친구 화면 (1차 1단계: 빈 상태 UI만) | partially-completed | YYYY-MM-DD | [📄](./friends/summary.md) |`

- [ ] **Step 3: backlog.md 갱신**

다음 항목 추가/이동:
- "최근 완료" 섹션 최상단에 1차 1단계 항목 추가
- 🟢 일반 표에 1차 2단계 항목 등재:
  - 백엔드: `friendships` 테이블 + `GET /api/v1/friends` + 통합 테스트
  - 모바일: 도메인/Repository/UseCase/Remote/Data 레이어 + `FriendCard` + `FriendsList` LazyColumn
  - 카드 탭 라우팅 / CTA 라우팅 (후속의 후속)

- [ ] **Step 4: PM hub 커밋 + 푸시**

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-pm/challenge_hub
git add docs/features/friends/summary.md docs/features/INDEX.md docs/backlog.md
git commit -m "$(cat <<'EOF'
docs(friends): 1차 1단계 완료 — 빈 상태 화면 (백엔드 0건)

- summary.md: 모바일 + 디자인 트랙 산출물 정리
- INDEX: draft → partially-completed
- backlog: 1차 1단계 완료 처리 + 1차 2단계 항목 등재

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

- [ ] **Step 5: 사용자에게 완료 보고**

PM hub 커밋·푸시 hash + 모바일 working tree 변경 사항(사용자 커밋 대기) 요약 보고.

---

## 의존 관계 그래프

```
Task 1 (design-bridge) ──→ Task 4 (FriendsEmptyState)
                       └─→ Task 5 (FriendsTopBar)
                       └─→ Task 6 (FriendsScreen 문구/아이콘)

Task 2 (Test 작성) ──→ Task 3 (UiState/ViewModel 정리)

Task 4, 5 ──→ Task 6 (FriendsScreen 사용)
Task 3, 6 ──→ Task 7 (FriendsRoute)
Task 7 ──→ Task 8 (전체 빌드 검증)
Task 8 ──→ Task 9 (PM 문서)
```

병렬 가능: Task 2-3과 Task 1은 독립. Task 1 진행 중에 Task 2-3 선행 가능.

---

## Self-Review 결과 (plan 작성 후)

**1. Spec coverage**: spec.md의 8개 수용 기준 / 7개 모바일 태스크 / 3개 디자인 태스크 / 1개 백엔드 비범위 모두 plan task에 매핑됨.
- AC1 (PlaceholderScreen 교체) → Task 6
- AC2 (FriendsEmptyState `:core:designsystem` 위치) → Task 4
- AC3 (디자인 토큰만 사용) → Task 4 코드 + design.md 가이드
- AC4 (Lovable 동기) → Task 1
- AC5 (FriendsTopBar) → Task 5
- AC6 (stub CTA onClick) → Task 7
- AC7 (BottomBar 노출 유지) → Task 6에서 MainScreen 변경 없음, 자동 충족
- AC8 (기존 회귀 0) → Task 8

**2. Placeholder scan**: "TODO" / "TBD" 검색 결과 — 코드 내 의도적 KDoc TODO(`// TODO(design.md):`)는 디자이너 산출물 검토 대기 표시로 OK. 그 외 instruction 단계 placeholder 0건.

**3. Type consistency**: `FriendsUiState.Data`를 `data object`로 일관 사용. `FriendsViewModel.showMessage`는 Task 3에서 `public`으로 변경 확정, Task 7에서 `viewModel.showMessage(...)` 호출 일관. `FriendsScreen` 시그니처 (`uiState`, `onClickAddFriend`) Task 6/7 일관.

**4. 사소한 보정**: Task 9 Step 2의 sed 명령어는 정확한 escape가 까다로워 Edit tool 수동 갱신 권장 — 두 옵션 모두 명시.

---

## 메모리 / 규칙 체크리스트

- ✅ 모바일 dispatch 시 git 금지 — plan 전체에서 모바일 working tree 변경만, 커밋은 사용자 직접 (Task 3·4·5·6·7·8 step 마지막에 "사용자 보고").
- ✅ Lovable ↔ 모바일 동기 — Task 1에서 Lovable 작업 + design.md 동시 작성, 모바일 트랙은 design.md 산출물 기반.
- ✅ home-feed v2 패턴 답습 — `ChallengeScaffold` / `ChallengeTheme` / `MainAction.showSnackBar` / Flow + onError 표준 패턴 (1차 1단계엔 Repository 없으나 후속에서 적용).

---

## 후속 계획 (1차 2단계 — 본 plan 범위 외)

spec.md "후속 계획" 섹션 + plan 종료 시 backlog 등재 항목으로 충분. 별도 plan은 1차 2단계 진입 시 신규 작성.
