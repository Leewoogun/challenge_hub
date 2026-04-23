# ADR-0001: DB 마이그레이션 도구 선택

- **상태**: accepted (2026-04-23)
- **생성**: 2026-04-23
- **영향 범위**: backend 모든 스키마 변경, 첫 기능 구현 전에 필요

## 맥락

`challenge-server`는 `spring.jpa.hibernate.ddl-auto: validate`로 설정되어 있다. 이 모드는 JPA 엔티티가 DB 스키마와 일치하는지만 검증하고, 스키마를 생성·변경하지 않는다. 즉 **스키마를 관리하는 별도 도구가 필요**한데 현재 Flyway나 Liquibase 의존성이 프로젝트에 없다.

이 상태로는 첫 `@Entity`를 추가한 순간 애플리케이션 기동이 실패한다.

## 선택지

1. **Flyway** — 파일 기반 SQL 마이그레이션. Spring Boot starter 단순. `V{n}__{description}.sql` 파일을 `src/main/resources/db/migration/`에 두면 자동 실행. 사이드 프로젝트 표준.
2. **Liquibase** — XML/YAML/JSON changelog 지원. 롤백·조건부 실행·멀티 DB에 강점. 설정 복잡도 높음.
3. **수동 SQL + pgAdmin 등 외부 도구** — 비권장. 재현성·CI·감사 추적 모두 약함.

## 권장

**Flyway.** 사이드 프로젝트 규모에서는 Flyway의 단순함이 이점. SQL 파일만 관리하면 되고 CI/로컬 양쪽에서 자동 적용.

추가 사항:
- 초기 `V1__init.sql`은 foundation sub-feature(ADR-0002)와 함께 작성
- 테이블/컬럼 네이밍은 snake_case (Hibernate 기본)
- `@Column(name = "...")` 수동 지정은 예외적일 때만

## 결정

**2026-04-23: Flyway로 확정 (accepted).**

### 구성
- 의존성: `spring-boot-starter-flyway` + `org.flywaydb:flyway-database-postgresql`
- 마이그레이션 경로: `app/src/main/resources/db/migration/`
- 파일 네이밍: `V{n}__{snake_case_description}.sql` (예: `V1__init.sql`, `V2__add_challenge_table.sql`)
- 테이블·컬럼 네이밍: snake_case (Hibernate 기본 네이밍 전략)
- 첫 `V1__init.sql`은 ADR-0002 foundation sub-feature와 함께 작성 — `users` 테이블 스키마 포함

### 운영 원칙
- 배포된 마이그레이션은 수정 금지 — 새 버전으로 추가
- 로컬 개발 중에는 `flyway:clean`으로 초기화 가능, prod에서는 금지

## 참조

- Spring Boot Flyway: https://docs.spring.io/spring-boot/reference/data/sql.html#data.sql.migration-tool.flyway
- `challenge-server/app/src/main/resources/application.yml`
