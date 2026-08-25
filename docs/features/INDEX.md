# Features Index

| feature-id | 제목 | 상태 | 완료일 | 링크 |
|-----------|------|------|-------|------|
| challenge-verification | 챌린지 인증 (즉석 촬영 → multipart 제출 → 상대 사진 확인 + 상세 화면 재구성) | completed (Android 실기. iOS 촬영은 실기기 필요. 계약 2차 개정: multipart + JWT 서빙) | 2026-08-25 | [📄](./challenge-verification/summary.md) |
| push-deeplink | 푸시 알림 딥링크 (알림 탭 → 목적지 이동, 인증 게이트 + 트레이 중복 제거) | **implemented** (모바일 커밋 `d25e394`. 🔴 **서버 3파일 미커밋** + 실기 5케이스 전수 미확인) | 2026-08-08 | [📄](./push-deeplink/summary.md) |
| push-fcm | 푸시 알림 (챌린지 신청·수락·거절 3종 + 토큰 등록 + logout 실구현) | completed (Android. iOS 수신은 Apple 계정 제약으로 범위 제외) | 2026-08-07 | [📄](./push-fcm/summary.md) |
| soul-oath | 영혼의 맹세 (계약서 + 양측 서명 → `is_finalized` 시 `IN_PROGRESS`) | partially-completed (iOS 실기 미검증 / 주관 판단 3건) | 2026-08-03 | [📄](./soul-oath/summary.md) |
| dev-test-login | 개발용 테스트 로그인 (가짜 계정 3개 + debug 전용 버튼) | partially-completed (격리 OFF는 배포 전 관문으로 이월) | 2026-08-03 | [📄](./dev-test-login/summary.md) |
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
