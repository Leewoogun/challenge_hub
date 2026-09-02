# Features Index

| feature-id | 제목 | 상태 | 완료일 | 링크 |
|-----------|------|------|-------|------|
| verification-photo-replace | 인증 사진 교체 허용 (재제출 `last-write-wins` + Coil 캐시 무효화 — **ai-verification 선행 feature**) | **implemented** (전 범위 구현·검증 완료. 🔴 **양 레포 미커밋** + **T-I1 실기 미실시**. 마이그레이션 0 / 새 엔드포인트 0 — 기존 계약 2건 **개정**. 부수 발견: `:remote:datasource` iOS 테스트가 한 번도 컴파일된 적 없음) | 2026-09-02 | [📄](./verification-photo-replace/summary.md) |
| notification-list | 알림 목록 (조회 API 3종 + 화면 + 홈 벨 뱃지 점등 — **앱 placeholder 0 달성**) | **implemented** (전 범위 구현·검증 완료. 🔴 **양 레포 미커밋** — 서버 12파일·앱 34경로 / 실기 미확인. 커서 페이지네이션 최초 도입 → ADR-0012) | 2026-09-01 | [📄](./notification-list/summary.md) |
| mypage | 마이페이지 (프로필·계약서 보관함·로그아웃 실구현·회원탈퇴 — 4탭 완성) | completed (서버 실구동 검증. 디바이스 실기·KAKAO_ADMIN_KEY 대기) | 2026-08-26 | [📄](./mypage/summary.md) |
| loser-ranking | 개돼지 랭킹 (나+친구 패자 랭킹 — Top3 포디움 + 수치의 명단, 4탭 placeholder 0 달성) | completed (실서버 실측. 디바이스 실기 미확인) | 2026-08-26 | [📄](./loser-ranking/summary.md) |
| challenge-result | 챌린지 결과 판정 (자정 배치 §2.6 판정 + FAILED·EXPIRED 전이 + 전적 집계, 푸시 제외) | completed (서버 실데이터 소급 실측. 디바이스 실기 미확인. 첫 스케줄러 — :batch 개통) | 2026-08-25 | [📄](./challenge-result/summary.md) |
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
