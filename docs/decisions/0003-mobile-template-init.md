# ADR-0003: 모바일 레포 템플릿 초기화

- **상태**: in-progress (2/6 완료)
- **생성**: 2026-04-23
- **진행 업데이트**: 2026-04-23 — 패키지명·프로젝트명 리네임 적용됨 (사용자 직접 실행)
- **영향 범위**: 모든 모바일 작업의 선행 조건

## 맥락

`challenge-app`은 `CmpSystem` (Compose Multiplatform System) 템플릿의 복제본으로, challenge 프로젝트용으로 초기화되지 않았다:

| 항목 | 현재 값 | 원하는 값 | 상태 |
|------|--------|----------|------|
| 패키지 루트 | ~~`com.lwg.base`~~ → `com.lwg.challenge` | `com.lwg.challenge` | ✅ 2026-04-23 완료 |
| 프로젝트명 (settings.gradle.kts) | ~~`CmpSystem`~~ → `Challenge` | `Challenge` | ✅ 2026-04-23 완료 |
| API base URL | TMDB (`https://api.themoviedb.org/3/`) | challenge 서버 URL | ⏳ ADR-0007 결정 후 |
| buildkonfig API 토큰 | `tmdb_token` (local.properties) | challenge 서버 인증 토큰 | ⏳ ADR-0007 결정 후 |
| 예제 feature 모듈 | `:feature:ex1`, `ex2`, `ex3` | 제거 | ⏳ 즉시 가능 |
| `:feature:home` | Movie 예제 (HomeViewModel/HomeScreen/HomeTopBar 등) | challenge 홈으로 교체 | ⏳ Sprint 1~2 |
| 디자인 시스템 | 기본 Color/Typography (`ChallengeColorScheme` 하드코딩) | Lovable 토큰 반영 | ⏳ 디자인 스프린트 |
| CLAUDE.md 모듈 구조 | `:core:domain/network/data` (잘못 기술) | `:domain:*`, `:remote:*`, `:data:*` (실제 구조) | ⏳ 즉시 가능 |

## 실행 순서

```bash
cd /Users/hwamulman/woogunProject/challenge/challenge-app

# 1) dry-run으로 변경 미리보기
./scripts/update_package.sh --dry-run com.lwg.challenge ChallengeApp

# 2) 실제 실행
./scripts/update_package.sh com.lwg.challenge ChallengeApp

# 3) buildkonfig / local.properties 의 API base URL & 토큰 교체
#    - remote/network/build.gradle.kts 의 buildkonfig 설정 수정
#    - local.properties: CHALLENGE_API_BASE_URL 등으로 치환

# 4) 예제 feature 정리 결정
#    - 유지: :feature:home을 Movie 예제로 두고 참조용
#    - 제거: ./scripts/ 와 settings.gradle.kts에서 :feature:ex1/ex2/ex3 삭제

# 5) CLAUDE.md 수정
#    - 모듈 구조 섹션을 README.md와 일치하도록 갱신

# 6) 빌드 검증
./gradlew :composeApp:compileCommonMainKotlinMetadata
./gradlew :composeApp:compileDebugKotlinAndroid
```

## 권장

1~2와 5는 즉시 실행(리스크 낮고, 하지 않으면 모든 작업이 틀어짐). 3~4는 첫 모바일 기능 스펙이 올라올 때 결정.

## 결정

**2026-04-23: 부분 accepted. 패키지·프로젝트명 리네임은 완료, 잔여 4개 항목은 개발하면서 자연스럽게 반영 (in-progress).**

### 완료
- 패키지 `com.lwg.base` → `com.lwg.challenge` ✅
- 프로젝트명 `CmpSystem` → `Challenge` ✅

### 잔여 (블로킹 아님, 개발 병행)
- **API base URL 교체**: challenge 서버 로컬 동작 확인 후(Sprint 0 끝무렵). `remote/network/build.gradle.kts` + `local.properties`의 `tmdb_token` 정리.
- **`:feature:ex1/ex2/ex3` 제거**: 첫 challenge feature 착수 시점에 함께 정리.
- **`:feature:home` Movie 예제 교체**: Sprint 1~2 홈 화면 구현 시 자연스럽게 교체.
- **`challenge-app/CLAUDE.md` 모듈 구조 정정**: `:core:domain/network/data` → 실제 `:domain:*`/`:remote:*`/`:data:*` 구조 반영. 모바일 레포에서 별도 수정.

### pm-lead 지침
잔여 항목은 `repos.json` `mobile.blockers`로 트래킹. 모바일 작업 할당 시 블로커가 해당 기능에 영향 주는지만 점검하고, 아니면 진행.

## 참조

- `challenge-app/README.md` — 스크립트 사용법
- `challenge-app/scripts/update_package.sh`
- `.claude/agents/mobile-dev.md` "작업 시작 시 필수 절차"
