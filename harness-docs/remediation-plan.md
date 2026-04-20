<!-- generated_at: 2026-04-20 -->
<!-- generated_by: /verify-assessment -->

# Remediation Plan

> Generated **2026-04-20** · Run `/verify-assessment` to refresh after making changes.

## Skills to run

| Priority | Skill | Failing requirements addressed |
|---|---|---|
| 1 | `/add-ci` | CI includes linting · CI config must include lint/test/build/deploy · CI build validation on every commit |
| 2 | `/add-security-scan` | Dependency vulnerability scanning in CI · Critical/high CVEs block merges |
| 3 | `/add-structured-logging` | Structured logging with service + trace_id fields · Structured logging in service code with trace context |
| 4 | `/security-audit` | OWASP Top 10 onboarding · Least privilege for accounts/keys/IAM · OWASP Top 10 in code review |
| 5 | `/test-bootstrap` | Documented test strategy · First-class tests / flaky test policy |
| 6 | `/adr` | More ADRs for architectural decisions · Folder structure ADR · ADR-before-decision process |
| 7 | `/document-codebase` | README with deployment notes and ADR/runbook links |
| 8 | `/generate-architecture` | CODEOWNERS file · Clear module boundaries · Circular dependency check |
| 9 | `/working-agreement` | Bi-weekly retrospectives · Engineering principles (build-for-replacement, default-to-open, fast-feedback) |
| 10 | `/tracking-plan` | Tracking plan for dirigent itself · Validate analytics events in CI |
| 11 | `/pir` | Severity levels (P1–P3) with response SLAs |

## Full failing MUST inventory

| Section | Requirement | Suggested skill |
|---|---|---|
| 01 · Culture & Working Agreements | Bi-weekly retrospectives with tracked action items (monthly declared) | `/working-agreement` |
| 01 · Culture & Working Agreements | Principle: Build for replacement, not perfection | `/working-agreement` |
| 01 · Culture & Working Agreements | Principle: Default to open (documented forums) | `/working-agreement` |
| 01 · Culture & Working Agreements | Principle: Optimize for fast feedback | `/working-agreement` |
| 02 · Architecture & Decision Records | Document significant architectural decisions as ADRs | `/adr` |
| 02 · Architecture & Decision Records | Store ADRs at standard path and link from README | `/document-codebase` |
| 02 · Architecture & Decision Records | Check for existing ADR before architectural decisions | `/adr` |
| 02 · Architecture & Decision Records | Clear service/module boundaries with explicit interfaces | `/generate-architecture` |
| 02 · Architecture & Decision Records | Eliminate circular dependencies between modules | `/generate-architecture` |
| 02 · Architecture & Decision Records | Documented owner for every service/module (CODEOWNERS) | `/generate-architecture` |
| 03 · Code Quality, Reviews & Standards | Flag stale PRs (>3 days without activity) | `/working-agreement` |
| 03 · Code Quality, Reviews & Standards | README with purpose/setup/tests/deploy/ADR links | `/document-codebase` |
| 03 · Code Quality, Reviews & Standards | Consistent folder structure documented in ADR | `/adr` |
| 03 · Code Quality, Reviews & Standards | Enforce linting/formatting via pre-commit or CI | `/add-ci` |
| 04 · Test Strategy | Documented test strategy covering unit/integration/E2E | `/test-bootstrap` |
| 04 · Test Strategy | Unit tests fast (<1 min) enforced | `/test-coverage` |
| 04 · Test Strategy | Treat tests as first-class; fix flaky tests within one sprint | `/test-bootstrap` |
| 05 · Continuous Delivery & CI/CD | CI includes linting | `/add-ci` |
| 05 · Continuous Delivery & CI/CD | CI includes build validation on every commit | `/add-ci` |
| 05 · Continuous Delivery & CI/CD | Main branch always deployable (branch protection) | manual |
| 05 · Continuous Delivery & CI/CD | CI config must include lint/test/build/deploy | `/add-ci` |
| 07 · Observability, Monitoring & Tracking | Structured logging with service + trace_id fields | `/add-structured-logging` |
| 07 · Observability, Monitoring & Tracking | Structured logging in service code with trace context | `/add-structured-logging` |
| 07 · Observability, Monitoring & Tracking | Maintain tracking plan | `/tracking-plan` |
| 07 · Observability, Monitoring & Tracking | Validate analytics events in CI | `/tracking-plan` |
| 08 · Security & Dependency Management | Dependency vulnerability scanning in CI on every build | `/add-security-scan` |
| 08 · Security & Dependency Management | Critical/high CVEs block merges | `/add-security-scan` |
| 08 · Security & Dependency Management | OWASP Top 10 reviewed as part of onboarding | `/security-audit` |
| 08 · Security & Dependency Management | Principle of least privilege for accounts/keys/IAM | `/security-audit` |
| 08 · Security & Dependency Management | Check for OWASP Top 10 in code review | `/security-audit` |
| 09 · Incident Management & Blameless Culture | Severity levels (P1–P3) with response SLAs | `/pir` |
| 09 · Incident Management & Blameless Culture | Use PIR template (path mismatch with standards spec) | manual |
