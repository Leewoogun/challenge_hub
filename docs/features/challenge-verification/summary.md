# 챌린지 인증 (challenge-verification) — Summary

- **feature-id**: challenge-verification
- **완료일**: 2026-08-25
- **상태**: **completed** (Android 실기 기준. iOS 는 컴파일·단위 테스트까지 — 촬영 실동작은 실기기 필요)

## 구현 개요

핵심 플로우의 *"양측 인증(카메라)"* 구간 개통. 챌린지 상세의 "인증하기" → **즉석 촬영(갤러리 차단) →
리사이즈·EXIF 제거 → 미리보기 확정 → multipart 제출** → `VERIFIED` 전이 + 상대에게 `OPPONENT_VERIFIED`
푸시 → **상대가 상세에서 사진 확인**까지 왕복이 실기로 검증됐다. 부수로 챌린지 상세 화면이 Lovable
디자인 기준으로 전면 재구성됐고(VS 헤더·미션 카드 분리·남은 시간), **이 앱의 첫 원격 이미지 로딩
스택(Coil 3)** 이 들어왔다.

🔴 **개발 중 사용자 결정으로 계약이 두 번 뒤집혔다** — 업로드(URL 발급→multipart 직접, 8/18)와
조회(서명 URL→JWT 서빙, 8/18). 두 번 다 같은 원리다: *"지금 규모에서 안 쓰는 유연성에 복잡도를
지불하지 않는다."* 릴리즈 전이라 전환 비용이 0이었고, 결과적으로 3단계 왕복·서명 체계·전용
HttpClient·만료 갱신 로직이 전부 사라져 최종 구조가 훨씬 단순하다.

## 엔드포인트

| Method | Path | 설명 | 상태 |
|--------|------|------|------|
| POST | `/api/v1/challenges/{id}/verification` | multipart 사진 제출 → `VERIFIED` + 상대 알림 | implemented (로컬 실기 검증) |
| GET | `/api/v1/challenges/{id}/verifications` | 양측 현황 + `photoUrl`(상대 경로) | implemented |
| GET | `/api/v1/challenges/{id}/photos/{party}` | 사진 바이트 서빙 (JWT 당사자 검사) | implemented |

개발 중 만들어졌다 폐기: `POST .../verification/upload-url` · `PUT/GET /api/v1/photos/**`(서명 URL).
`GET /challenges/{id}` 는 **무변경** (인증 조회를 얹지 않고 분리 — [계약 §4](./api-contract.md)).

## 화면 / UI 변경

- **인증 화면 신설** (`:feature:challenge:verify`): 촬영 → 미리보기 → "이 사진으로 인증" 확정 → 완료.
  재제출 불가 정책의 짝으로 미리보기 확인 단계가 필수다. 디자인 없이 구현(디자이너 대기, 교체 전제)
- **챌린지 상세 재구성** (2026-08-24 사용자 기획 3건 → Lovable `challenge-detail.tsx` 정본 채택):
  VS 헤더(아바타 + 남은 시간 분 단위 갱신) / 나·상대 미션 카드 분리(뱃지 + 내 카드에 인증 CTA·인증
  후 내 사진, 상대 카드에 상대 사진) / 압축 계약서 카드(내기 + **절대 마감 행 존치** — 유일한 Lovable
  이탈, pm-lead 판정) — [design.md](./design.md)
- **홈**: 인증 상태 뱃지가 `:core:ui` `VerificationStatusPill` 로 승격 (홈 회귀 0)
- `:core:camera` 모듈 신설 (시스템 카메라 expect/actual, Android+iOS 실구현)

## 주요 변경 파일

**백엔드** (`1ae7dc8`): `VerificationController`/`Service`(+`readPhoto`) · `PhotoStorage` 포트 +
`LocalDiskPhotoStorage` · `PhotoKeys` · `NotificationMessages`(OPPONENT_VERIFIED) · V9(주석만, DDL 0건)

**모바일** (`74e2f74`, `ec6f9d4`): `:core:camera`(촬영·압축·`JpegMetadata.strip`) ·
`:feature:challenge:verify` · 상세 컴포넌트 4종(`VsHeaderCard`/`MissionCard`/`VerificationPhoto`/
`OathSummaryCard`) · Verification 도메인~remote 전 계층 · Coil 배선(`ChallengeApp` 루트) ·
`HttpNetworkLogger`(Content-Type 분기)

## 테스트 결과

- **백엔드: 320/320 passed** (365 중 통합 45 skip — 컨테이너 부재, 기존과 동일)
- **모바일** (모듈별 최종, failures 0): detail **29/29 JVM + 29/29 iOS** · verify **25/25 JVM+iOS** ·
  mapper 75 · datasource 30 · network 13 · camera 28(양 플랫폼) · utils 35 · **home 회귀 20/20**
- **실기 (Android, 2026-08-25)**: 촬영→압축→제출→상대 사진 확인 왕복. **T-M2 리사이즈 실측 달성** —
  실사진 1080×1440, **115~138KB** (목표 ~500KB 대비 여유). FCM 실발송은 키 부재로 row 저장까지만
- iOS: 전 모듈 컴파일 + 단위 테스트 통과. **촬영 실동작은 실기기 필요** (시뮬레이터 카메라 없음)

## 결정 사항

1. **저장**: 서버 로컬 폴더 + `PhotoStorage` 포트 ([ADR-0011](../../decisions/0011-photo-storage.md))
2. **업로드 = multipart 직접 / 조회 = JWT 서빙** — ADR-0011 §3·§4 의 수단이 사용자 결정(8/18 두 차례)으로
   supersede. 이사 시엔 서버 중계 또는 302 리다이렉트 확장 경로 (앱 무변경)
3. **재제출 전면 거부** + 응답 유실 시 §4 조회로 내 상태 확인 후 회복 (거부를 실패로 오인하지 않는다)
4. **갤러리 차단 이중화**: 시스템 카메라(진입점 구조적 부재) + iOS `NSPhotoLibrary*` plist 의도적 미선언
5. **EXIF 제거는 앱 책임**: 순수 Kotlin `JpegMetadata.strip`(GPS 담는 APP1/APP13 제거, JFIF/ICC 보존) —
   commonTest 로 고정. 서버측 미가공은 **실사용자 유입 전 재검토** 부채
6. **실패 정책**: 인증 조회 실패 시 화면 전체 Error 금지, 뱃지·사진만 강등 + **CTA 는 노출 폴백**
   (막는 실패보다 중복 시도 실패가 낫다 — 한 차례 판정 번복 끝에 확정)
7. **판정은 범위 밖**: 이 feature 가 남기는 것은 `VERIFIED` row + `verified_at`. 후속 판정 feature 는
   **RESULT·REMIND 푸시 제외**(2026-08-25 사용자 결정, 배치는 DB 전이만)

## 실기에서 잡은 버그 — "테스트는 초록인데 실기에서 깨진" 계열

- 🔴 **네트워크 로거가 사진 스트림을 소비** — 로거가 모든 응답에 `bodyAsText()` ∧ 사진이 기본 인증
  클라이언트 사용 ∧ Coil 은 스트리밍 읽기. **각각 무해한 세 결정의 교차점**에서만 터졌고 JSON 경로
  테스트로는 영원히 못 잡는 구조였다. Content-Type 분기로 수정 + 스트리밍 의미론 재현 테스트로 고정
- 🔴 **storage-root 변경으로 이전 사진 404** — 8/14 업로드분이 옛 루트에 남아, 신 루트만 보는 서버가
  "파일 없음" 404. 정상 404("아직 인증 안 함")와 구분 불가능한 조용한 실패. 파일 이관으로 해소.
  🔴 상대 경로 루트는 배포 시 `CHALLENGE_PHOTO_ROOT` 절대 경로로 박아야 한다 (ADR-0007 소관)
- (개발 중 사전 차단) 같은 key 덮어쓰기로 사진 바꿔치기 · multipart boundary 소실(전역 Content-Type) ·
  URL 조인 `//` → 조용한 404 — 셋 다 계약·테스트에 박제

## 미해결 이슈

- [ ] 🟡 **알림 문구 4종 초안 상태** — `OPPONENT_VERIFIED` "증거 도착" 포함, 사용자 확정 대상 (user)
- [ ] 🔵 **디자이너 확인 8건** — 촬영 화면 전체 + 상세 7건([design.md §7](./design.md)) (design)
- [ ] Coil 404 무캐시 런타임 확인 · 남은 시간 티커 갱신 검증(시계 주입 필요) · CTA 첫 화면 이탈 실기 확인 (mobile)
- [ ] iOS 촬영 실기기 검증 (mobile+user)
- [ ] EXIF 서버측 미가공 — 실사용자 유입 전 재검토 (backend)
- [ ] 사진 보관 기간 정책 없음(단조 증가) · `photo_url` 컬럼 개명 · multipart 5MB 상한 테스트 미고정 ·
  제출 실패 시 고아 파일 (backend)
- [ ] **판정(결과) feature** — `:batch` 첫 코드. FCM 제외 스코프 확정 (backend+mobile)

## 참조

- [spec.md](./spec.md) · [api-contract.md](./api-contract.md) · [design.md](./design.md)
- [mobile-report.md](./mobile-report.md) · [backend-report.md](./backend-report.md) · [change-log.md](./change-log.md)
- [ADR-0011](../../decisions/0011-photo-storage.md)
