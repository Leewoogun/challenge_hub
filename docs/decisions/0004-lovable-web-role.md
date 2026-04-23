# ADR-0004: Lovable 디자인의 웹 프런트 역할 여부

- **상태**: accepted (2026-04-23)
- **생성**: 2026-04-23
- **영향 범위**: 디자인 브릿지 작업 범위, 백엔드 CORS, 전체 제품 전략

## 맥락

`challenge-design/oathbound-challenges`는 단순 mockup이 아니라 **완전한 TanStack Start + React 19 + shadcn + Cloudflare 배포 구성**이 포함된 웹 앱이다. `wrangler.jsonc`와 `@cloudflare/vite-plugin`이 존재하여 배포가 바로 가능한 상태.

두 가지 운영 방식이 가능하고, 선택에 따라 영향이 다르다.

## 선택지

### A. 디자인 참조 전용

- Lovable 앱을 배포하지 않음. 모바일이 UI 참조용으로만 사용.
- Cloudflare 관련 설정(`wrangler.jsonc`, `@cloudflare/vite-plugin`)은 무시.
- design-bridge는 토큰·컴포넌트·화면 흐름만 mobile-dev에 전달.

### B. 웹 프런트로도 운영

- Lovable 앱을 Cloudflare에 배포. 사용자가 모바일 + 웹 양쪽에서 접근 가능.
- 백엔드 CORS에 Cloudflare 도메인 추가.
- 백엔드가 받는 요청 origin이 늘어남 → 보안 정책 재검토.
- 디자인 변경이 mobile에만 영향 아니라 **웹 제품 자체에도 영향** → 디자이너/프런트 분리된 역할 필요?
- Lovable의 React 코드(라우팅, 검증, 데이터 fetch)가 제품 로직과 분리되어 있는지 검토 필요.

## 고려사항

- **사이드 프로젝트 규모**에서 모바일만으로 충분한가? 웹 버전 유지보수 리소스가 있나?
- 웹 버전이 **공식 제품**이 아니라면 배포는 "프리뷰/대시보드" 수준으로 제한하는 중간안도 가능.
- Lovable은 Figma처럼 디자인 업데이트가 잦을 수 있음 — 배포한다면 CI 자동화 필요.

## 권장

**A(참조 전용)**로 시작. 사이드 프로젝트 초기에 웹까지 동시 운영은 과다한 부담. 제품 방향이 명확해지고 모바일이 안정되면 B로 확장 검토.

## 결정

**2026-04-23: A안 (참조 전용) 확정 (accepted).**

- Lovable `challenge-design/oathbound-challenges`는 **배포하지 않음** — 순전히 PM/디자인/모바일이 참조하는 용도.
- Cloudflare 관련 구성(`wrangler.jsonc`, `@cloudflare/vite-plugin`)은 방치 (제거 불필요, 혼선만 없도록 PM만 인지).
- design-bridge 에이전트는 `src/styles.css` 토큰, `src/routes/` 화면 흐름, `src/components/` 컴포넌트 패턴을 읽어 모바일 명세(`docs/features/{id}/design.md`)로 변환.
- 백엔드 CORS는 **모바일 origin만** 허용 (ADR-0002 foundation에 반영).

향후 웹 배포가 필요해지면 별도 ADR로 재논의.

## 참조

- `challenge-design/oathbound-challenges/wrangler.jsonc`
- `.claude/agents/design-bridge.md` "디자인 소스 특성" 섹션
