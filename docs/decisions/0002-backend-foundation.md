# ADR-0002: 백엔드 기반 인프라(Foundation) 구성

- **상태**: pending
- **생성**: 2026-04-23
- **영향 범위**: 모든 백엔드 기능의 선행 조건

## 맥락

`challenge-server`는 `ChallengeServerApplication.kt`와 smoke 테스트 1개만 있는 **완전 스켈레톤** 상태다. 컨트롤러, 서비스, 도메인, Security 구성, ExceptionHandler 모두 없다.

이 상태에서 feature별로 기반 요소를 임의 추가하면 일관성이 깨진다. 첫 기능 구현 전에 공통 기반을 정리하는 것이 효율적이다.

## 필요한 Foundation 요소

| 항목 | 현재 상태 | 필요한 작업 |
|------|----------|------------|
| SecurityFilterChain | 없음 | `SecurityConfig`에 경로별 `authorizeHttpRequests` 정의 |
| JWT 인증 필터 | JJWT 0.12.6 의존성만 | `JwtAuthenticationFilter` 구현, 토큰 발급·검증 유틸 |
| GlobalExceptionHandler | 없음 | `@RestControllerAdvice`로 표준 에러 바디 반환 |
| 표준 에러 응답 DTO | 없음 | `{code, message, details}` shape — api-contract 표준과 일치 |
| 응답 wrapper 정책 | 미정 | `ApiResponse<T>` 표준화 여부 결정 (권장: 쓰지 않고 raw JSON, 에러만 표준) |
| SpringDoc OpenAPI config | 의존성만 | JWT Bearer 헤더 보안 스키마 설정, grouped API |
| CORS | 없음 | 모바일(origin 불필요) + 웹 프런트(ADR-0004)에 따라 |
| DB 마이그레이션 | 없음 | ADR-0001 결정 반영 |
| 로깅 포맷 | 기본 | JSON 구조화 로깅 도입 여부 |

## 권장 순서

1. ADR-0001(마이그레이션 도구) 결정 → Flyway 의존성 추가 + `V1__init.sql` skeleton
2. ADR-0004(웹 운영 여부) 결정 → CORS 허용 도메인 확정
3. Foundation을 `docs/features/foundation/` feature로 분리하여 구현. 이 feature의 완료가 다른 feature의 선행 조건.
4. Foundation 완료 후 첫 도메인 기능(예: `auth-login`) 착수.

## 대안

"Foundation을 별도 feature로 분리하지 않고 첫 기능과 함께 자연스럽게 쌓는다" 도 가능하나, 권장하지 않음. 이유:
- 첫 feature가 지나치게 커짐
- 기반이 feature별로 다르게 구성될 위험
- mobile-dev가 의존할 에러 shape이 늦게 확정됨

## 결정

**미정.** 첫 기능 제안이 올라올 때 pm-lead가 이 ADR을 읽고 foundation 선행 여부 결정.

## 참조

- `.claude/agents/backend-dev.md` "선행 조건" 섹션
- `.claude/skills/api-contract/SKILL.md` — 에러 바디 shape 표준
