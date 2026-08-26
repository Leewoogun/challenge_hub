# 마이페이지 (mypage) — Summary

- **feature-id**: mypage
- **완료일**: 2026-08-26
- **상태**: **completed** (서버 throwaway DB 실구동 2회 검증. 디바이스 실기 확인은 미해결 등재 — 서버 미기동 상태)

## 구현 개요

4탭의 마지막 실속(MY 탭) 개통 + **계정 수명주기의 마감 처리**. 프로필 카드(전적 실데이터),
**계약서 보관함**(월별 카드 목록 — 기획 §3.3 *"이때 너 이거 걸었잖아"* 이행이자 백로그 🟡
**"결과 히스토리 화면 부재"의 정식 해소**), **로그아웃 실구현**(백로그 🟡 — 서버 세션·FCM 토큰까지
끊김), **회원탈퇴**(익명화+기록 보존+사진 삭제 — 사용자 확정 정책). Lovable 프리뷰
(`/archive` 신규 + `/mypage` 갱신)도 이번에 제작·푸시됐다(`c578d00`).

## 엔드포인트

| Method | Path | 설명 | 상태 |
|--------|------|------|------|
| GET | `/api/v1/challenges/history` | 보관함 — COMPLETED 전체(최신순), 월 그룹은 `challengeDate` 기준 | implemented (throwaway 실구동) |
| DELETE | `/api/v1/users/me` | 회원탈퇴 — unlink→익명화→사진 삭제 순 | implemented (〃) |
| DELETE | `/api/v1/auth/logout` | 기존 — 앱 연동 완료 (호출부 0 이던 것) | 연동 완료 |

계약 변경: `GET /challenges/{id}/verifications` 에 **`photoDeleted` 추가**(additive —
"봉인이 풀린 게 아니라 조건이 붙었다"로 change-log 등재). 프로필 카드는 기존 API 재사용 — 신규 0.

## 화면 / UI 변경

- **MY 탭**: placeholder → 프로필 카드(닉네임·아바타·총N·승률·승/패/무) + 보관함 메뉴 + 로그아웃 +
  회원탈퇴(경고 다이얼로그, 시각 위계 분리). 설정 화면·캘린더·"준비 중" 행은 의도적 미생성
- **계약서 보관함**(신규): 월 섹션 헤더(sticky) + 카드(상대·양측 미션·내기·결과 pill·날짜) →
  탭하면 기존 상세. 빈 상태 / **인라인 실패 카드+재시도**(전체 실패) / 스낵바(부분 실패) 분리
- **상세**: 탈퇴자 사진 자리 "탈퇴한 사용자의 사진은 삭제됐어요" (`photoDeleted` 분기 — 기존
  이상 감지 분기는 보존)
- `:core:ui` 신설: `ConfirmDialog`(destructive) / `EmptyStateCard` 재사용 확장

## 테스트 결과

- **백엔드: 513건 중 464 passed / 49 skip(기존 Docker 블로커) / 실패 0** — 신규 47, 회귀 0.
  ⚠️ 이 레포 단위 테스트는 JPA 를 mock 으로 세워 **JPQL·마이그레이션이 어느 테스트에도 안 걸린다** —
  **throwaway DB 실구동 2회**(19항목 + 탈퇴 정책 5행 매트릭스)로 메움. V1→V11 Flyway 적용,
  `PhotoStorage.delete()` **첫 실동작**(탈퇴자 사진 2개 삭제·상대 1개 잔존), 재로그인=신규 계정,
  탈퇴 후 상대 화면 전부 무파손 실측
- **모바일: Android 346 / iOS 259, 실패 0** — 로그아웃 특성화 10건(WWW-Authenticate 없이 갱신됨
  실증), 탈퇴·보관함·photoDeleted·부분 실패 2경로 전부 테스트 고정

## 결정 사항

1. **탈퇴 = 익명화 + 기록 보존 + 사진 삭제** (사용자 확정). 실행 순서 **unlink → DB → 파일**
   (실패 시 복구 가능한 쪽). 추가 확정 2건: 탈퇴자가 보낸 `PENDING` 삭제(결과가 정해진 챌린지의
   신규 시작 차단) / `notifications` 삭제(수신함은 개인 데이터 — 양자 보존 원칙의 대상이 아님).
   진행 중 챌린지는 막지 않고 자연 판정. **탈퇴자 표현은 타 응답 계약 변경 0**(nickname non-null 유지)
2. **보관함 = 전체 최신순 + 월 섹션 헤더** (월 파라미터 아님 — 빈 달 문제 + 홈 7일 이후 도달이
   무조작 충족. ⚠️ 사용자 문면 "월별 조회"의 해석 건 — 재확인 항목). 월 경계 `challengeDate`,
   `EXPIRED` 제외, 페이지네이션 미도입(통일 규약 준수 — 일괄 도입은 백로그)
3. **`photoDeleted` additive** — pm-lead 의 "조합 재정의" 지시를 팀이 뒤집음: null 조합은 의도된
   이상 감지기라 재정의는 감지기 소거 + confirmed 의미 변경이 additive 보다 위험(조용한 오독)
4. **`WWW-Authenticate` 서버 전역 변경 차단** — 헤더 없어도 Ktor 갱신 동작 실증(프로바이더 1개 전제,
   깨지면 터지는 테스트 박제). RFC 정합 잔여는 백로그
5. **승률·패율 분모 = 총 챌린지(무 포함)** — 두 탭 합 112% 모순을 잡고 CLAUDE.md 전역 규칙 승격.
   반올림 `floor(x+0.5)`(kotlin round 는 ties-to-even — 문서 오류를 테스트가 잡음)
6. **실패 표시 3원칙 확립** — 가짜 0 을 그리지 않는다(성공 데이터만 표시) / 전체 실패 = 인라인
   실패 카드(성공 데이터 없는 화면은 전체 대체가 원칙 위반 아님) / 부분 실패 = 목록+스낵바 병행
   (표시 0 이면 스낵바가 유일 채널)
7. **문서 작성 교훈 3건**(design 자기 교정 6건에서 도출): 기대값에는 근거를 같이 적는다 /
   비율 케이스는 `.5` 로 떨어지는 값을 넣는다 / **금지 지시의 예외는 같은 자리에 쓴다**

## 미해결 이슈

- [ ] 🔴 **실기 검증 0** — 로그아웃 후 푸시 차단 / 탈퇴 왕복(상대 화면·재로그인 신규 계정) /
  보관함 실데이터. ⚠️ **서버 재기동 필요**(V11 자동 적용, `/history` 는 구 빌드에서 404)
- [ ] 🔵 **`KAKAO_ADMIN_KEY`** — 카카오 콘솔 발급(사용자). 미설정 시 unlink 만 생략(fail-soft)
- [ ] ⑭ 보관함 조회 단위 사용자 재확인 (월 선택 UI 원했으면 뒤집기 — 비용 소)
- [ ] 탈퇴자가 보낸 도전장의 상대측 알림 → 705 딥링크 표시 확인 (서버 실측 완료, 앱 확인만)
- [ ] 로컬 정리 이중 경로(무해·소유자 2) / design §6 문구 미확정 / verify iOS XML 1건 stale
- [ ] 탈퇴 후 access token 최대 1h 잔존(수용 트레이드오프) · 페이지네이션 일괄 도입 — 백로그 등재됨

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [design.md](./design.md)
- [mobile-report.md](./mobile-report.md) · [backend-report.md](./backend-report.md)
- 소급 변경: [challenge-verification/change-log.md](../challenge-verification/change-log.md) (`photoDeleted`)
