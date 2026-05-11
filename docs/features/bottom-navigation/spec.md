# Spec — bottom-navigation

- **feature-id**: `bottom-navigation`
- **작성일**: 2026-05-11
- **작성자**: pm-lead
- **범위 한정**: UI / Navigation 전용 (백엔드 영향 없음, API 계약 없음)

## 배경

현재 `challenge-app`의 `:feature:main`에 있는 `ChallengeBottomBar`는 CmpSystem 템플릿 잔재로, HOME + Ex1/Ex2/Ex3 4탭이 매핑되어 있다. 카카오 로그인(`auth-kakao`) 완료로 사용자가 로그인 후 진입하는 메인 셸을 challenge 도메인으로 교체해야 한다. 본 feature는 그 셸의 **BottomNavigation 뼈대**를 challenge 5탭(홈/친구/랭킹/MY) ~~+ 챌린지 생성 진입~~ → **4탭 (홈/친구/랭킹/MY)** 로 재구성하고, 각 탭이 가리킬 placeholder Screen 모듈을 만든다.

## 사용자 시나리오

1. 사용자가 카카오 로그인 → SplashScreen이 토큰 확인 후 `HomeRoute.Main`으로 진입한다.
2. 화면 하단 BottomBar에 4개 탭(홈 / 친구 / 랭킹 / MY)이 보인다.
3. 사용자가 "친구" 탭을 누르면 친구 화면(placeholder "준비 중")이 표시되고, BottomBar의 "친구" 탭이 active 스타일로 바뀐다.
4. 다른 탭으로 이동 시 동일하게 동작. Splash/Login 화면에서는 BottomBar가 숨겨진다(이미 구현된 분기 유지).

## 수용 기준

- [ ] BottomBar에 한글 라벨("홈" / "친구" / "랭킹" / "MY") 4탭이 표시된다.
- [ ] Lovable `BottomNav.tsx` 시각 동등성: Active 탭은 `primary` 색 + 굵은 stroke, Inactive 탭은 `muted-foreground`. 라벨 폰트 크기·아이콘 크기는 design.md 결정대로.
- [ ] 각 탭 클릭 시 해당 Route로 navigate되고, BottomBar의 active 표시가 정확히 갱신된다.
- [ ] 새 placeholder 화면(`:feature:friends` / `:feature:ranking` / `:feature:mypage`) 각각이 다크 배경 + "준비 중" 텍스트만 표시한다.
- [ ] `:feature:ex1`, `:feature:ex2`, `:feature:ex3` 모듈이 settings.gradle.kts / 의존성 / Route.kt에서 모두 제거되며, 디렉토리도 삭제된다.
- [ ] Android safeDrawing + iOS safe-area inset이 BottomBar 아래쪽 패딩에 반영된다.
- [ ] 빌드(`:composeApp:linkDebugFrameworkIosSimulatorArm64`, `:composeApp:compileDebugKotlinAndroid`, `:feature:{main,friends,ranking,mypage}:compileCommonMainKotlinMetadata`) 모두 BUILD SUCCESSFUL.
- [ ] 기존 LoginViewModelTest 4/4 회귀 0.

## 비범위 (Out of Scope)

- **홈 화면 콘텐츠 교체**: `:feature:home`의 Movie 예제 → challenge 홈으로 본격 교체. 별도 feature로 분리(`home-feed` 후속). 본 feature에선 홈 화면이 현재 상태(Movie 예제)로 남아도 무방하나, BottomBar 라우팅 자체는 challenge `HomeRoute.Main` 그대로 사용.
- **친구/랭킹/MY 화면 도메인 로직**: 본 feature에선 placeholder("준비 중") 수준. 실 데이터·API·ViewModel 흐름은 각 후속 feature(`friends-register`, `ranking-view`, `mypage-view`)에서.
- **챌린지 생성 진입(`/challenge-new`)**: Lovable BottomNav에 없음. 별도 feature(`challenge-create-entry`)에서 FAB or 다른 진입 결정. 본 feature는 무관.
- **알림(`/notifications`) 진입**: 동상 비범위. 별도 feature.
- **API 계약**: 백엔드 호출 없음. api-contract.md 생성하지 않음.

## 모바일 태스크 분해

| ID | 태스크 | 담당 | 의존 |
|----|------|------|------|
| T-M1 | Lovable `BottomNav.tsx` 분석 → design.md 작성 (아이콘 매핑/active 토큰/safe-area) | design-bridge | — |
| T-M2 | `:core:navigation`의 `Route.kt`에 `FriendsRoute.Main` / `RankingRoute.Main` / `MyPageRoute.Main` 추가 + SerializersModule 등록. `Ex1Route/Ex2Route/Ex3Route` 제거 | mobile-dev | T-M1 |
| T-M3 | 신규 feature 모듈 3개(`:feature:friends/ranking/mypage`) 생성 — `generate-feature.sh` 활용. 각 Route/Screen/ViewModel skeleton + "준비 중" placeholder UI | mobile-dev | T-M2 |
| T-M4 | `BottomNavItem.kt` enum 갱신(HOME/FRIENDS/RANKING/MYPAGE, 아이콘은 design.md 매핑) + `ChallengeBottomBar.kt` selected 분기 갱신 | mobile-dev | T-M3 |
| T-M5 | `MainScreen.kt` NavDisplay entryProvider에 Friends/Ranking/MyPage 추가. Ex1/Ex2/Ex3 분기 제거. BottomBar 노출 분기에 신규 라우트 반영 | mobile-dev | T-M4 |
| T-M6 | `:feature:ex1/ex2/ex3` 모듈 제거(`settings.gradle.kts` / `:composeApp` / `:feature:main` build.gradle.kts 의존성 / 디렉토리 삭제) | mobile-dev | T-M5 |
| T-M7 | 빌드 검증(4건) + LoginViewModelTest 회귀 확인 | mobile-dev | T-M6 |

> 7개 태스크가 의존 사슬로 묶임. T-M2부터는 mobile-dev 단독 흐름.

## 사용자 결정 권한

다음 항목은 design-bridge가 design.md 작성 시 ⚠️로 플래그하고, pm-lead가 사용자에게 확인 후 결정:

1. **아이콘 출처**: 현재 `:feature:login`이 `materialIconsExtended` 사용 중(deprecation 백로그). BottomBar 4개 아이콘도 같은 선택지:
   - (a) `materialIconsExtended`로 통일 (Home/People/EmojiEvents/Person) — 일관성 ↑, deprecation 부담 ↑
   - (b) 커스텀 SVG 번들 — 일관성 ↓, lucide와 100% 매칭 가능
   - (c) Compose `Icons.Default` 빌트인 (Home/Person 정도만) — 빈약하나 deprecation 무관
2. **"MY" vs "마이페이지" 라벨**: Lovable은 "MY" (영문 약어). 한국어 일관성 vs Lovable 충실 — pm-lead 판단. 기본값 "MY".
3. **Placeholder 화면 디테일**: "준비 중" 단일 텍스트면 충분한지, 아이콘+짧은 설명까지 넣을지.
4. **BottomBar 토큰화 위치**: `:feature:main` 인라인 vs `:core:designsystem`에 재사용 컴포넌트 추출 — design-bridge 권고.

## 리스크 / 오픈 이슈

- ex1/ex2/ex3 디렉토리 삭제 시 `git rm -r` 사용 — 사용자가 직접 처리(에이전트 git 변경 금지 규칙). mobile-dev는 변경만 만들고 보고.
- iOS는 `safeAreaInsets` 처리가 Compose의 `WindowInsets.safeDrawing`과 매핑이 미세할 수 있음. 시뮬레이터 실측 필요(backlog).
- `:feature:home`의 Movie 예제가 그대로 남아 BottomBar 홈 탭이 여전히 TMDB로 호출 시도. backend foundation으로 인증 거부될 수 있으나 본 feature 범위 외.

## 후속 feature 예고

본 feature 완료 후 자연스러운 다음:
- `home-feed`: `:feature:home` Movie 예제 → challenge 홈으로 교체 (ADR-0003 잔여 해소)
- `friends-register`: 친구 등록 화면 도메인 구현 (`account_phone_number` scope 승인 대기)
- `ranking-view` / `mypage-view`: 각 placeholder 화면 채우기
- `challenge-create-entry`: 챌린지 생성 진입 결정(FAB 등)
- `notifications`: 알림 화면 + 진입

## 참조

- Lovable: `challenge-design/oathbound-challenges/src/components/BottomNav.tsx`
- 현재 모바일 코드: `challenge-app/feature/main/.../component/{ChallengeBottomBar, BottomNavItem}.kt`, `challenge-app/core/navigation/.../Route.kt`
- ADR-0003 (모바일 템플릿 초기화) — 본 feature가 잔여의 ex1~3 제거를 처리
