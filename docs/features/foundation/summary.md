# Foundation — Summary

- **feature-id**: `foundation`
- **완료일**: 2026-04-24
- **상태**: completed (pm-lead 문서 완료, 서버 코드 사용자 리뷰 대기)

## 구현 개요

challenge-server 완전 스켈레톤 → 첫 도메인 기능 착수 가능 상태로 전환. Flyway + 9 테이블 초기 스키마, BaseResponse 응답 규약(ADR-0002) + GlobalExceptionHandler, JWT 인증(JJWT) + SecurityFilterChain, Kakao/Refresh/Logout 3개 엔드포인트 skeleton, SpringDoc OpenAPI + CORS까지 일괄 구성. 로컬 Postgres 없이도 10개 테스트 전부 통과.

## 엔드포인트

| Method | Path | 인증 | 상태 |
|--------|------|------|------|
| POST | /api/v1/auth/kakao | 공개 | implemented (Kakao 검증 stub) |
| POST | /api/v1/auth/refresh | 공개 | implemented |
| DELETE | /api/v1/auth/logout | Bearer | implemented (stub) |

## 주요 변경 파일

**백엔드 (`/Users/hwamulman/woogunProject/challenge/challenge-server`):**
- **신규 15개**: V1__init.sql, BaseResponse/ResponseCode, BusinessException 계층, GlobalExceptionHandler, JwtTokenProvider, JwtAuthenticationFilter, AuthController, 4 auth DTOs, OpenAPIConfig, SecurityConfig, 2 테스트 파일
- **수정 5개**: app/build.gradle.kts (Flyway 추가), application.yml (flyway/jwt/springdoc 블록), libs.versions.toml (Flyway 라이브러리), SpringLibraryConventionPlugin.kt (Spring Boot BOM import), KotlinLibraryConventionPlugin.kt (useJUnitPlatform), ChallengeServerApplicationTests.kt (DB 없이 context load)

## 테스트 결과

- 단위: 5/5 passed (GlobalExceptionHandlerTest)
- 슬라이스: 4/4 passed (AuthControllerTest, @WebMvcTest)
- smoke: 1/1 passed (ChallengeServerApplicationTests, DB 제외)
- **합계 10/10 passed**
- `bootRun`: 미수행 (로컬 Postgres/Redis 기동 필요)

## 결정 사항 (구현 중 확정)

- **OpenAPIConfig를 `:api` 모듈에** 배치 — swagger-models 의존성이 `:api`에만 있음. `@Configuration`은 `:app`의 `@ComponentScan`에 의해 자동 등록.
- **SpringLibraryConventionPlugin에 Spring Boot BOM import 추가** — library 모듈도 starter 의존성을 버전 없이 사용 가능하게. 이전에는 `:app`에서 `org.springframework.boot` 플러그인으로 암묵 import만 돼 있었음.
- **모든 모듈 테스트 태스크에 useJUnitPlatform()** — JUnit 5 annotations가 실제로 실행되도록.
- **ChallengeServerApplicationTests에서 DB/Redis/Flyway auto-config 제외** — 로컬 인프라 없이도 smoke test 통과. 실제 통합 테스트는 Sprint 1 Testcontainers로 이관.
- **SecurityConfig의 `"/**"` 문자열 리터럴 회피** — Kotlin 컴파일러가 "Unclosed comment"로 오판하여 `"/" + "**"` concat으로 우회.

## 미해결 이슈

### Sprint 1에서 처리해야 할 것
- [ ] Kakao `/v2/user/me` 실제 연동 (현재 AuthController.kakaoLogin이 임의 userId=1로 JWT 발급하는 stub)
- [ ] users 테이블 upsert + phone_number SHA-256 저장
- [ ] Refresh Token blacklist (Redis) + logout의 fcm_token null 처리
- [ ] Testcontainers 기반 통합 테스트 도입

### 일반 TODO
- [ ] prod 환경변수 `JWT_SECRET` 확정 (ADR-0007 Phase 2)
- [ ] Refresh Token rotation 정책 (탈취 감지 필요해지면)

## 참조

- [spec.md](./spec.md)
- [api-contract.md](./api-contract.md)
- [backend-report.md](./backend-report.md)
- 관련 ADR: 0001 (Flyway) · 0002 (foundation + BaseResponse) · 0004 (CORS) · 0007 (환경) · 0008 (phone scope)

## 후속 작업

사용자가 challenge-server 레포에서:
1. 변경사항 리뷰 (주요: build-logic 2개 파일 수정 + V1__init.sql + application.yml)
2. 로컬 Postgres + Redis 기동 후 `./gradlew :app:bootRun`으로 실제 동작 확인
3. `http://localhost:8080/swagger-ui/index.html`에서 3개 엔드포인트 테스트
4. OK면 커밋
