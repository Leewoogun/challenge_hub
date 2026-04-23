# ADR-0007: 환경 분리 전략 (dev / staging / prod)

- **상태**: accepted (2026-04-23, phased)
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

**2026-04-23: Phase 1 = 로컬만, Phase 2 = AWS prod (accepted, phased).**

### Phase 1 (현재~출시 전, 로컬 단일 환경)

**백엔드:**
- PostgreSQL @ `localhost:5432/challenge`
- Redis @ `localhost:6379`
- Spring profile: 단일 (분리 없이 `application.yml` 하나)
- secrets: `application.yml`의 `${VAR:default}` + 개발자 로컬 환경 변수 or `.env`

**모바일:**
- API base URL:
  - Android emulator: `http://10.0.2.2:8080`
  - iOS simulator: `http://localhost:8080`
  - 실기기(같은 Wi-Fi): 개발자 Mac IP, 예: `http://192.168.x.x:8080`
- buildkonfig에 `CHALLENGE_API_BASE_URL` 단일 상수로 주입 (`local.properties`에서)
- Kakao 앱 키: 개발용 1개
- Firebase: dev 프로젝트 1개 (google-services.json / GoogleService-Info.plist)

**인프라:**
- CI/CD: 현재 없음 (로컬 개발만)
- 모니터링: 로그 콘솔 출력

### Phase 2 (출시 직전, AWS 전환 — 별도 ADR로 확정)

- 서버: EC2 또는 ECS(Fargate), RDS PostgreSQL, ElastiCache Redis, S3(이미지 저장), CloudFront
- 도메인 + Route 53 + ACM (HTTPS)
- prod용 Kakao 앱 분리, Firebase prod 프로젝트 분리
- Spring profile `local` / `prod` 분리
- 모바일 빌드 variant: `dev` / `prod`, buildkonfig에서 환경별 URL 주입
- CI/CD: GitHub Actions (빌드 + 배포)
- 비용 관리: 프리티어 최대한 활용 + billing alert

### 전환 체크리스트 (Phase 2 착수 시)
- [ ] ADR-0007을 superseded로 변경, 신규 ADR(AWS 배포 전략) 작성
- [ ] 도메인 확보 (maengse.app 또는 대체)
- [ ] AWS 계정 + IAM 설정
- [ ] RDS 백업 정책, S3 버전관리, 로그 집계(CloudWatch)
- [ ] Flyway 마이그레이션 prod 적용 전 staging으로 검증

## 참조

- `challenge-server/app/src/main/resources/application.yml`
- `challenge-app/local.properties` (secrets, 커밋 금지)
- `challenge-app/remote/network/build.gradle.kts` (buildkonfig 설정)
