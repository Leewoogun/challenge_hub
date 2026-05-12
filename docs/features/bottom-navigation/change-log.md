# Change Log — bottom-navigation

## 2026-05-12 — 결정 #6 변경: inline TextStyle → `medium10` 슬롯 신설

### 변경

design.md ✅ #6 (10.sp 라벨 처리)를 (i) inline `TextStyle` → (ii) `medium10` 슬롯 신설로 변경. 디자인시스템 일관성과 향후 다른 10sp 사용처 발생 시 단일 진실 소스 유지를 위해.

### 영향 범위

**PM 허브**:
- `docs/design-system/tokens.md` §5.2 — `medium10` row 추가 (Lovable `text-[10px]`, lineHeight 14, FontWeight.Medium). 변경 이력에도 등재.
- `docs/features/bottom-navigation/design.md` — ✅ #6 결정 셀 + 시각 토큰 매핑 표(라벨 폰트 사이즈 row) + 변경 이력에 반영.
- `docs/features/bottom-navigation/summary.md` — 결정 #6 row 갱신.

**모바일 코드** (challenge-app):
- `:core:designsystem/.../theme/ChallengeTypography.kt` — `medium10` 슬롯 신설 (`TextStyle(fontSize = 10.sp, fontWeight = FontWeight.Medium, lineHeight = 14.sp)`). 다른 slot과 동일 패턴.
- `:feature:main/.../component/ChallengeBottomBar.kt` — inline `BottomNavLabelStyle: TextStyle` private val 제거. 라벨 사용처를 `ChallengeTheme.typography.medium10`으로 교체.

### 사유

- 디자인시스템 슬롯 일관성: 다른 사이즈(`medium12`/`14`/...)와 동일 명명 규칙으로 통일.
- 결정 #6 당시 권고 사유였던 "다른 사용처 누적 시 슬롯화"의 임계점이 사용자 판단으로 이미 도달했다고 봄.
- 후속 feature(notifications, friends-register 등)에서 10sp 라벨 재사용 시 자동으로 동일 토큰.

### 빌드/테스트 영향

UI 토큰 교체만이라 회귀 영향 없음. mobile-dev가 빌드 4건 + LoginViewModelTest 4/4 재확인.
