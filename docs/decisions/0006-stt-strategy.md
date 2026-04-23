# ADR-0006: STT (음성 → 텍스트) 제공 방식

- **상태**: accepted (2026-04-23, 모니터링 필요)
- **생성**: 2026-04-23
- **영향 범위**: 영혼의 맹세 작성 기능, 비용, 네트워크 지연, 오프라인 대응

## 맥락

기획서 2.4에서 계약서 내용을 음성으로 말하면 STT로 텍스트 변환. 기술 스택에 "Google Speech-to-Text API 또는 Kakao Neuro STT"가 언급되어 있고, Server 스펙 3.11에 `POST /api/v1/stt/convert` (Google STT API 프록시) 엔드포인트가 정의되어 있음.

즉 **클라이언트 SDK 사용**과 **서버 프록시**의 두 길이 열려 있다. 둘 중 하나(혹은 혼합)를 선택해야 한다.

## 선택지

### A. 클라이언트 플랫폼 SDK 사용

- Android: `android.speech.SpeechRecognizer` (무료, 온디바이스 일부 지원)
- iOS: `SFSpeechRecognizer` (무료, 온디바이스 일부 지원)
- 서버 `/stt/convert` 엔드포인트는 제거 또는 옵션.

**장점**: 비용 0, 오프라인 부분 가능, 네트워크 지연 없음.
**단점**: 플랫폼별 품질 차이, KMP common에서 expect/actual 필요, 한국어 품질 변수.

### B. 서버 프록시 사용 (Google STT / Kakao Neuro STT)

- 클라이언트는 음성 파일만 업로드, 서버가 외부 API 호출.
- 서버 `/api/v1/stt/convert` 활용.

**장점**: 플랫폼 간 일관 품질, 한국어 최적화(Kakao Neuro), 서버에서 비용 집계/제한 용이.
**단점**: 유료(Google STT 분당 ~$0.024, Kakao Neuro 유료 플랜), 네트워크 의존, 음성 파일 S3 업로드 추가.

### C. 혼합 (primary=A, fallback=B)

- 기본은 플랫폼 SDK, 품질 미만이거나 실패 시 서버 프록시.
- 복잡도 증가.

## 트레이드오프 표

| 축 | A (SDK) | B (프록시) | C (혼합) |
|----|---------|-----------|---------|
| 비용 | 0 | 유료 | 저~중 |
| 한국어 품질 | 중 | 고 (Kakao Neuro) | 고 |
| 구현 복잡도 | 중 (expect/actual) | 저 | 고 |
| 오프라인 | 부분 | X | 부분 |
| 운영 제어 | 플랫폼 의존 | 서버 로그/제한 | 둘 다 |
| 사용자 프라이버시 | 온디바이스 처리 일부 가능 | 서버 전송 | 혼합 |

## 권장

**A로 MVP 시작, 품질 이슈 확인되면 B 도입 검토.**
- MVP에서는 비용을 피하고 UX 검증.
- 한국어 STT 품질이 실제 사용에서 문제되면 B로 전환(혹은 C).
- 서버 `/stt/convert` 엔드포인트는 유지하되 초기에는 호출 안 함 (후속 전환 대비).

## 비용 예상 (B 선택 시)

- Google STT 표준 모델: $0.024/분 (60초 기준 약 30원)
- 하루 1인당 계약서 1건, 평균 30초 녹음 가정
- MAU 1,000명 × 30일 × 15초(평균) = 약 7,500분 → **월 약 $180**
- 사용자 규모 확장 시 큰 비용 → Kakao Neuro 한국어 특화 플랜 병행 검토

## 결정

**2026-04-23: A안 (클라이언트 SDK) 기본 채택. 단, 정확도 모니터링 후 부족 시 C안(하이브리드)으로 전환 (accepted with monitoring).**

사용자 의도: "클라이언트 SDK 선호 + 정확도 높은 것 선호" — 상충 요소를 A+모니터링으로 절충.

### 정확도 최대화 전략 (A안 내에서)

| 플랫폼 | API | 설정 |
|-------|-----|------|
| Android | `SpeechRecognizer` | `EXTRA_LANGUAGE_MODEL = LANGUAGE_MODEL_FREE_FORM`, `EXTRA_LANGUAGE = "ko-KR"`, `EXTRA_PREFER_OFFLINE = false` (네트워크 기반 고정확도 모델) |
| iOS | `SFSpeechRecognizer` | `locale = Locale(identifier: "ko_KR")`, `requiresOnDeviceRecognition = false` |

공통:
- **계약서 도메인 어휘 힌트** 주입 시도 (iOS `SFSpeechRecognitionRequest.contextualStrings`, Android는 직접 지원 제한적 → 후처리 교정 테이블 검토)
- 사용자 **직접 편집 필수** — STT 결과는 텍스트 필드에 바인딩, 사용자가 수정하여 계약서 확정

### 모니터링 및 Fallback 트리거

MVP 출시 후 다음 지표 수집:
- **재녹음 비율**: 30% 초과 시 문제
- **STT → 확정 전 편집 비율**: 40% 초과 시 문제
- **정확도 피드백(부정적)**: 20% 초과 시 문제

하나라도 트리거되면:
1. 서버 `POST /api/v1/stt/convert` 엔드포인트 구현 (Google Cloud Speech-to-Text 또는 Kakao Neuro STT 연동)
2. 클라이언트에서 A(SDK) 1차 → confidence score 낮거나 짧은 발화면 B(서버) 2차 — 하이브리드
3. ADR-0006을 업데이트 (superseded by 하이브리드 변형)

### 기술 구현 (commonMain)

```kotlin
// :domain:usecase (또는 :core:stt)
expect class SpeechRecognizer(context: Any? = null) {
    val isAvailable: Boolean
    suspend fun start(): Flow<RecognitionResult>
    fun stop()
}

data class RecognitionResult(
    val text: String,
    val confidence: Float,  // fallback 판단용
    val isFinal: Boolean,
)
```

### Sprint 2 착수 전 체크
- [ ] Android: `RECORD_AUDIO` 권한 요청 플로우
- [ ] iOS: `NSSpeechRecognitionUsageDescription` + `NSMicrophoneUsageDescription` Info.plist
- [ ] 네트워크 없을 때 UX (온디바이스 fallback 또는 에러 메시지)

## 참조

- Server 스펙 3.11 `/api/v1/stt/convert`
- `.claude/agents/mobile-dev.md` — 모바일 구현 시 STT 처리 가이드
