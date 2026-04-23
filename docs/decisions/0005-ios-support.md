# ADR-0005: iOS 지원 범위 및 시점

- **상태**: pending
- **생성**: 2026-04-23
- **영향 범위**: 모바일 전반, 카카오 SDK, FCM, 배포 일정, 비용

## 맥락

기획서는 "Android (Kotlin)"만 언급하나, `challenge-app`은 Compose Multiplatform 기반으로 **iOS 타겟까지 사전 구성**되어 있다 (iosApp/, iosMain/ sourceSet, MainViewController).

iOS를 포함하는지, 포함한다면 MVP부터인지 후속 릴리즈인지에 따라 영향이 크다.

## 선택지

### A. Android MVP → iOS 후속 (권장)

- MVP는 Android만 릴리즈. iOS는 안정화 후 추가.
- 장점: 초기 스코프 축소, Kakao SDK iOS/APNs 연동 지연 가능, Apple Developer Account 즉시 불필요.
- 단점: KMP로 작성하되 iOS actual 일부 stub 처리 → 후속 때 본격 구현 필요.

### B. Android + iOS 동시 MVP

- MVP부터 양 플랫폼 릴리즈.
- 장점: 처음부터 KMP 이점 최대 활용, 양 플랫폼 일관성 유지.
- 단점: Kakao iOS SDK 통합, APNs(FCM iOS), AVFoundation 카메라, SFSpeechRecognizer 등 iOS 전용 작업이 1~2 Sprint 추가. Apple Developer Account 비용($99/year).

### C. Android only (iOS 포기)

- 기획서 그대로 Android만. 현 레포의 KMP 구조는 유지 가능하되 iosMain은 방치.
- 장점: 최소 부담.
- 단점: 레포 선택과 모순. KMP의 장점 활용 못 함 → 차라리 순수 Android 프로젝트로 재구성이 명확.

## 고려 요인

- **제품 타겟**: 기획서는 "20~30대 친구 그룹". 한국에서 이 연령대의 iOS 점유율은 낮지 않음(약 30~40%). 출시 시 iOS 배제는 도달률 큰 손실.
- **개발 리소스**: Claude 에이전트 기반 개발이라 코드 생산성은 높으나, **빌드 환경(Mac+Xcode) 유지**가 필수.
- **Kakao iOS SDK**: 카카오 공식 지원, 문서 충분. 큰 리스크 아님.
- **FCM iOS**: APNs 인증서 설정, provisioning profile 필요 — 초기 설정 시간 발생.

## 권장

**A (Android MVP → iOS 후속).** 사이드 프로젝트 초기 스코프 관리에 합리적. 단, 코드는 KMP 원칙대로 작성하여 iOS 추가 시 비용 최소화.

단, 기획서 업데이트(플랫폼 표기)는 필수.

## 결정

**미정.** Sprint 0 진입 전 반드시 결정. 결정이 A/C면 `challenge-app/iosApp/` 방치 정책 명시.

## 참조

- `challenge-app/CLAUDE.md` — KMP 소스셋 구조
- `challenge-app/iosApp/iosApp.xcodeproj` — iOS 진입점 존재
