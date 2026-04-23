# ADR-0007: 환경 분리 전략 (dev / staging / prod)

- **상태**: pending
- **생성**: 2026-04-23
- **영향 범위**: 백엔드 프로파일, 모바일 빌드 variant, Firebase 프로젝트, CI/CD

## 맥락

현재 `challenge-server`의 `application.yml`은 단일 환경(로컬 PostgreSQL, Redis)만 구성되어 있고, `challenge-app`의 API base URL은 하드코딩(TMDB). 실서비스 이전에 환경 분리가 필요하다.

기획서에는 환경 분리 관련 언급이 없음.

## 필요한 환경

| 환경 | 용도 | 영향 |
|------|------|------|
| `local` | 개발자 로컬 머신 | PostgreSQL/Redis local, FCM dev 프로젝트, Kakao 개발 앱 키 |
| `dev` | 공용 개발 서버 | AWS/클라우드 또는 공용 VM, 기능 merge 후 확인 |
| `staging` | QA / 출시 전 검증 | prod와 동일 구성, 소규모 데이터 |
| `prod` | 운영 | 실제 사용자, 모니터링·백업 필수 |

## 결정 필요 사항

### 백엔드
- [ ] Spring profile 분리: `application-local.yml`, `application-dev.yml`, `application-stage.yml`, `application-prod.yml`
- [ ] secrets 관리: 환경 변수 / AWS Secrets Manager / Vault
- [ ] DB 인스턴스: 환경별 분리 or 단일 + schema 분리
- [ ] Redis 인스턴스 동일 결정

### 모바일
- [ ] Gradle flavor/variant: `dev`, `stage`, `prod`
- [ ] 환경별 API base URL을 `buildkonfig` 또는 `BuildConfig`로 주입
- [ ] 환경별 Firebase 프로젝트(google-services.json / GoogleService-Info.plist) 분리
- [ ] 환경별 앱 이름·아이콘·패키지 suffix (예: `.dev`, `.stage`)
- [ ] Kakao SDK 앱 키 환경별 분리 (카카오 디벨로퍼스는 환경별 앱 등록)

### 인프라
- [ ] dev/stage/prod 서버 호스팅 결정 (AWS EC2 / ECS / EKS / GCP / Fly.io 등)
- [ ] DNS (api.challenge.example.com, dev-api.challenge.example.com 등)
- [ ] CI/CD 파이프라인 (GitHub Actions?)

## 권장

**MVP는 `local` + `prod` 2단계로 시작, 베타 직전에 `staging` 추가.**
- `dev` 환경은 초기에는 불필요 (팀 규모 작음, 기능 수 적음)
- secrets는 AWS Parameter Store 또는 GitHub Secrets에 저장, 로컬은 `local.properties` / `.env`
- Firebase 프로젝트는 `prod` + `dev` 2개로 시작 (`staging`은 prod 프로젝트 공유)
- Kakao 앱은 `prod` + `dev` 2개

## 결정

**미정.** 첫 실서버 배포 일정 확정 시점까지 결정.

## 참조

- `challenge-server/app/src/main/resources/application.yml`
- `challenge-app/local.properties` (secrets, 커밋 금지)
- `challenge-app/remote/network/build.gradle.kts` (buildkonfig 설정)
