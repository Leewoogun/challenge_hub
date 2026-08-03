# Features Index

| feature-id | 제목 | 상태 | 완료일 | 링크 |
|-----------|------|------|-------|------|
| dev-test-login | 개발용 테스트 로그인 (가짜 계정 3개 + debug 전용 버튼) | partially-completed (격리 OFF 실서버 검증 미완) | 2026-08-03 | [📄](./dev-test-login/summary.md) |
| datetime-model-migration | 날짜·시간 모델 통일 (`Instant`/UTC → `LocalDateTime`/KST, `yyyy-MM-dd HH:mm:ss`) | completed | 2026-07-31 | [📄](./datetime-model-migration/summary.md) |
| challenge-create | 챌린지 신청 (생성 → PENDING → 수락/거절, 홈 "받은 도전장") | completed | 2026-07-31 | [📄](./challenge-create/summary.md) |
| friends | 친구 화면 + 검색·요청·수락·카톡 초대 (2차 완료) | completed | 2026-07-02 | [📄](./friends/summary.md) |
| user-info | 본인 정보 조회 endpoint + 모바일 캐시 (LoginResult 평탄화, T4 Home 통합은 사용자 결정으로 취소) | completed | 2026-06-29 | [📄](./user-info/summary.md) |
| auth-refresh-rotation | Refresh Token Rotation (DB sha256 hash + Ktor Auth 일원화) | completed | 2026-05-28 | [📄](./auth-refresh-rotation/summary.md) |
| home-feed | 홈 화면 (진행 중 챌린지 + 전적 + 빈 상태) | completed (v2: 2026-06-15 API 분리) | 2026-05-25 | [📄](./home-feed/summary.md) |
| bottom-navigation | 하단 네비게이션 (challenge 4탭 재구성 + ex1~3 제거) | completed | 2026-05-11 | [📄](./bottom-navigation/summary.md) |
| auth-kakao | 카카오 로그인 (실연동 교체) | completed | 2026-05-11 | [📄](./auth-kakao/summary.md) |
| foundation | 백엔드 기반 인프라 (Flyway + BaseResponse + JWT + Auth skeleton) | completed | 2026-04-24 | [📄](./foundation/summary.md) |

> 정렬 규칙: 진행 중 먼저 → 완료일 내림차순.
