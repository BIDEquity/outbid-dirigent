<!-- generated_at: 2026-04-20 -->
<!-- generated_by: /assess -->

# Remediation Plan

> Generated **2026-04-20** · Run `/verify-assessment` to refresh after making changes.

## Skills to run

| Priority | Skill | Failing requirements addressed |
|---|---|---|
| 1 | `/working-agreement` | Working Agreement doc · Definition of Done · Retrospectives · Engineering principles (replacement, open, fast feedback) |
| 2 | `/adr` | Document significant architectural decisions · Store in /docs/adr/ · Check ADR before decisions · Consistent folder structure documented · Monorepo vs polyrepo decision |
| 3 | `/generate-architecture` | Clear module boundaries · Eliminate circular deps · CODEOWNERS · C4 diagrams |
| 4 | `/document-codebase` | README deployment/ADR/runbook links · CONTRIBUTING.md |
| 5 | `/add-ci` | CI linting step · CI build validation on every commit · Lint/test/build/deploy coverage · CI config completeness |
| 6 | `/add-release` | Enforce Conventional Commits via commitlint · Automate version bumping (semantic-release/release-please) · Auto-generate CHANGELOG.md · Release notes automation |
| 7 | `/test-bootstrap` | Documented test strategy · Flaky-test policy · Tests-with-code enforcement |
| 8 | `/test-coverage` | Measure and report code coverage in CI with threshold |
| 9 | `/add-structured-logging` | Structured logging with service + trace ID fields · Replace stray `print()` calls · Centralised log shipping |
| 10 | `/tracking-plan` | Tracking plan for dirigent itself · Validate analytics events in CI |
| 11 | `/add-security-scan` | Dependency vulnerability scanning · CVEs blocking merges · SAST tooling |
| 12 | `/security-audit` | OWASP Top 10 review · Least-privilege policy · Threat model · TLS policy |
| 13 | `/pir` | Severity level doc · PIR storage location · MTTD/MTTR tracking |
| 14 | `/setup-agentic-standards` | Autonomy levels in CLAUDE.md · Reversible-by-default policy · Fail-stop policy · Prompt-injection awareness · AI-as-author test review · No-bypass security controls policy · Blast radius review · Agent action audit log |
| 15 | `/audit-claude-md` | Fix-in-same-PR process · Remove dead instructions · Quarterly audit cadence · Onboarding walkthrough |

## Full failing MUST inventory

| Section | Requirement | Suggested skill |
|---|---|---|
| 01 · Culture & Working Agreements | Written Working Agreement (cadences, comms, DoD, on-call, decisions) | `/working-agreement` |
| 01 · Culture & Working Agreements | Definition of Done applied to every story | `/working-agreement` |
| 01 · Culture & Working Agreements | Bi-weekly retrospectives with tracked action items | `/working-agreement` |
| 01 · Culture & Working Agreements | Principle: Build for replacement, not perfection | `/working-agreement` |
| 01 · Culture & Working Agreements | Principle: Default to open (documented forums) | `/working-agreement` |
| 01 · Culture & Working Agreements | Principle: Optimize for fast feedback | `/working-agreement` |
| 02 · Architecture & Decision Records | Document significant architectural decisions as ADRs | `/adr` |
| 02 · Architecture & Decision Records | Store ADRs in /docs/adr/ and link from README | `/adr` |
| 02 · Architecture & Decision Records | Check for existing ADR before architectural decisions | `/adr` |
| 02 · Architecture & Decision Records | Clear service/module boundaries with explicit interfaces | `/generate-architecture` |
| 02 · Architecture & Decision Records | Eliminate circular dependencies between modules | `/generate-architecture` |
| 02 · Architecture & Decision Records | Documented owner for every service/module (CODEOWNERS) | `/generate-architecture` |
| 03 · Code Quality, Reviews & Standards | Peer review required before merge to main | `/working-agreement` |
| 03 · Code Quality, Reviews & Standards | PRs small/focused, reviewable in under 30 min | `/working-agreement` |
| 03 · Code Quality, Reviews & Standards | PR description includes what/why/test/ticket link | `/working-agreement` |
| 03 · Code Quality, Reviews & Standards | Conventional Comments style feedback | `/working-agreement` |
| 03 · Code Quality, Reviews & Standards | Flag stale PRs (>3 days without activity) | `/working-agreement` |
| 03 · Code Quality, Reviews & Standards | README with purpose/setup/tests/deploy/ADR links | `/document-codebase` |
| 03 · Code Quality, Reviews & Standards | Consistent folder structure documented in ADR | `/adr` |
| 03 · Code Quality, Reviews & Standards | Enforce linting/formatting via pre-commit or CI | `/add-ci` |
| 04 · Test Strategy | Documented test strategy covering unit/integration/E2E | `/test-bootstrap` |
| 04 · Test Strategy | Unit tests in CI, fast/isolated/deterministic | `/test-bootstrap` |
| 04 · Test Strategy | Treat tests as first-class; fix flaky tests within one sprint | `/test-bootstrap` |
| 04 · Test Strategy | Write/update tests alongside code changes | `/test-bootstrap` |
| 05 · Continuous Delivery & CI/CD | Use Conventional Commits format | `/add-release` |
| 05 · Continuous Delivery & CI/CD | Enforce Conventional Commits via commitlint in CI | `/add-release` |
| 05 · Continuous Delivery & CI/CD | Automate version bumping (semantic-release/release-please) | `/add-release` |
| 05 · Continuous Delivery & CI/CD | Auto-generate CHANGELOG.md from commits | `/add-release` |
| 05 · Continuous Delivery & CI/CD | CI includes linting | `/add-ci` |
| 05 · Continuous Delivery & CI/CD | CI includes build validation | `/add-ci` |
| 05 · Continuous Delivery & CI/CD | Automate all production deployments | `/add-ci` |
| 05 · Continuous Delivery & CI/CD | Main branch always deployable | `/add-ci` |
| 05 · Continuous Delivery & CI/CD | Rollback possible within 15 min | `/add-ci` |
| 05 · Continuous Delivery & CI/CD | CI config must include lint/test/build/deploy | `/add-ci` |
| 07 · Observability, Monitoring & Tracking | Structured logging with service + trace ID fields | `/add-structured-logging` |
| 07 · Observability, Monitoring & Tracking | Structured logging in service code; propagate trace context | `/add-structured-logging` |
| 07 · Observability, Monitoring & Tracking | Maintain tracking plan | `/tracking-plan` |
| 07 · Observability, Monitoring & Tracking | Validate analytics events in CI | `/tracking-plan` |
| 08 · Security & Dependency Management | Dependency vulnerability scanning in CI on every build | `/add-security-scan` |
| 08 · Security & Dependency Management | Critical/high CVEs block merges | `/add-security-scan` |
| 08 · Security & Dependency Management | OWASP Top 10 reviewed as part of onboarding | `/security-audit` |
| 08 · Security & Dependency Management | Encrypt inter-service communication (TLS) | `/security-audit` |
| 08 · Security & Dependency Management | Principle of least privilege for accounts/keys/IAM | `/security-audit` |
| 08 · Security & Dependency Management | Check for OWASP Top 10 in code review | `/security-audit` |
| 09 · Incident Management & Blameless Culture | Severity levels (P1–P3) with response SLAs | `/pir` |
| 09 · Incident Management & Blameless Culture | Use PIR template in docs/templates/pir-template.md | `/pir` |
| 10 · Agentic Development | Apply same DoD to AI-generated code as human | `/setup-agentic-standards` |
| 10 · Agentic Development | Do not merge AI-generated code without human read | `/setup-agentic-standards` |
| 10 · Agentic Development | Treat AI as author under review when writing tests | `/setup-agentic-standards` |
| 10 · Agentic Development | Flag AI-generated code in commits/PR descriptions | `/setup-agentic-standards` |
| 10 · Agentic Development | Define autonomy levels in CLAUDE.md | `/setup-agentic-standards` |
| 10 · Agentic Development | Restrict autonomous agents to reversible actions | `/setup-agentic-standards` |
| 10 · Agentic Development | Never grant production access/secrets/IAM to agents | `/setup-agentic-standards` |
| 10 · Agentic Development | On agent failure: stop and surface, don't silently retry | `/setup-agentic-standards` |
| 10 · Agentic Development | Fix CLAUDE.md in same PR that corrects agent output | `/audit-claude-md` |
| 10 · Agentic Development | Remove instructions that no longer apply | `/audit-claude-md` |
| 10 · Agentic Development | Prompt injection awareness | `/setup-agentic-standards` |
| 10 · Agentic Development | Review tool permissions per workflow (least privilege) | `/setup-agentic-standards` |
| 10 · Agentic Development | Do not bypass security controls with AI | `/setup-agentic-standards` |
