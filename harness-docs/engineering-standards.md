# Engineering Standards

**Portfolio Company Engineering Playbook** *Version 1.0 · April 2026*

This standard bootstraps Claude Code into any git repository as enforceable engineering guidelines for both developers and AI agents.

---

## Purpose

A common foundation of engineering excellence across all portfolio companies — enabling speed, quality, and scalability.

## Scope

Applies to all engineering teams. Standards are marked **[MUST]** (baseline required) or **[RECOMMENDED]** (maturity milestones).

---

## 01 · Culture & Working Agreements

### Working Agreements

**[MUST]**

- Maintain a written Working Agreement covering: meeting cadences, communication norms, Definition of Done, on-call expectations, and decision-making process.
- Apply a Definition of Done (DoD) to every story before marking it complete. DoD must include: code reviewed, tests passing, feature toggled if needed, monitoring in place.
- Run retrospectives at least bi-weekly. Track action items with an owner and due date.

**[RECOMMENDED]**

- Maintain a Team Topology charter to make responsibilities and interaction modes explicit.
- Document an escalation path for incidents, architecture conflicts, and cross-team dependencies.

### Engineering Principles

**[MUST]**

- **Build for replacement, not perfection.** Design systems to be decomposed and replaced incrementally rather than built to last forever.
- **Default to open.** Architecture decisions, coding standards, and design discussions are open to input from all engineers via documented forums.
- **Optimize for fast feedback.** Use short iteration cycles, automated tests, and feature toggles over long-lived branches.

---

## 02 · Architecture & Decision Records

### Architecture Decision Records (ADRs)

ADRs capture the context, decision, and consequences of significant architecture choices. They are not bureaucracy — they are memory.

**[MUST]**

- Document all significant architectural decisions as ADRs. "Significant" means: technology choices, patterns adopted, integration approaches, infrastructure changes, or anything hard to reverse.
- Use the standard ADR template: **Title · Status** (Proposed / Accepted / Deprecated / Superseded) **· Context · Decision · Consequences · Alternatives Considered**.
- Store ADRs in `/docs/adr/` alongside the code. Version-control them and link from the README.
- Never delete ADRs. Mark outdated decisions as Deprecated or Superseded with a link to the replacement.
- When making an architectural decision, check if an ADR exists. If not, create one using `/adr`.

**[RECOMMENDED]**

- Run an Architecture Advisory Forum (AAF) bi-weekly or monthly where any engineer can propose ADRs.
- Visualise ADRs in a lightweight architecture map or wiki page.

### Evolutionary Architecture

**[MUST]**

- Give services and modules clear boundaries with explicit interfaces (APIs, events, contracts). Do not leak internal implementation details across boundaries.
- Eliminate circular dependencies between modules or services. Dependency direction flows inward toward domain/business logic.
- Record a documented owner for every service or significant module in a `CODEOWNERS` file or equivalent.

**[RECOMMENDED]**

- Automate architectural fitness functions in CI: cyclic dependency checks, module boundary violations, and performance thresholds.
- Maintain a C4 Level 1–2 system context diagram for each product.

---

## 03 · Code Quality, Reviews & Standards

### Code Review Practices

**[MUST]**

- Require at least one peer review for all code changes before merging to main or a release branch. No self-merging of feature work.
- Keep Pull Requests small and focused — one logical change, reviewable in under 30 minutes.
- Include in every PR description: what changed, why, how to test it, and a link to the related ticket or ADR.
- Provide actionable, specific, and respectful feedback. Use Conventional Comments style.
- Flag stale PRs (open > 3 days without activity). Merge, revise, or close them.

**[RECOMMENDED]**

- Use pair or mob programming for complex or risky changes.
- Track PR review metrics (time-to-review, comment density, cycle time) and discuss in retrospectives.

### Code Organisation & Repository Standards

**[MUST]**

- Every repository must have a README with: purpose, setup instructions, how to run tests, deployment notes, and links to ADRs and runbooks.
- Follow a consistent folder structure. Document structure choices in an ADR.
- Never commit secrets or configuration to source control. Use environment variables, secret managers, or vaults.
- Enforce linting and formatting automatically via pre-commit hooks or CI. Commit config to the repository.

**[RECOMMENDED]**

- Document monorepo vs. polyrepo decisions in an ADR tied to team topology and deployment strategy.
- Maintain a `CONTRIBUTING.md` covering branch naming, Conventional Commits format, and how to get started.

---

## 04 · Test Strategy

### Testing Pyramid

**[MUST]**

- Maintain a documented test strategy covering unit, integration, and end-to-end tests — with explicit decisions on what is and is not tested at each layer.
- Cover business logic with unit tests that run in CI on every commit. Target: fast (< 1 min for the full suite), isolated, and deterministic.
- Cover key interaction points (database, external services, message queues) with integration tests in CI using test doubles where appropriate.
- Limit end-to-end (E2E) tests to critical user journeys only — permutation testing belongs in unit/integration tests.
- Treat tests as first-class code: reviewed, refactored, kept deterministic. Fix or remove flaky tests within one sprint.
- When writing code, always write or update corresponding tests. When reviewing code, verify that test coverage is adequate.

**[RECOMMENDED]**

- Measure and report code coverage in CI. Set a baseline (e.g. 70–80% line coverage for business logic) and prevent regressions.
- Adopt contract testing for service-to-service integrations (e.g. Pact) to catch breaking changes without full E2E runs.
- Maintain performance and load tests for critical paths, run on a schedule or before major releases.

---

## 05 · Continuous Delivery & CI/CD

### Commit Conventions & Versioning

**[MUST]**

- Use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages. Format: `<type>(<scope>): <description>` where type is one of `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`, or `BREAKING CHANGE`.
- Enforce Conventional Commits via a commit-msg hook in CI (e.g. `commitlint`). Non-conforming commits block merge.
- All repositories must follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH). Version numbers are the canonical signal of change impact — do not use date-based or arbitrary versioning schemes.
- Automate version bumping on every merge to main using a tool that derives the next version from commit history (e.g. `semantic-release`, `release-please`). Version bumps must not require manual intervention.
- Automatically generate or update a `CHANGELOG.md` from commit history on every release. The changelog is an artifact of the CI pipeline, not a manually maintained file.

**[RECOMMENDED]**

- Tag every release commit in git with the version number (e.g. `v1.4.2`). Use the git tag as the single source of truth for what is deployed.
- Publish release notes to the team's communication channel automatically on each release.

### CI/CD Pipeline

**[MUST]**

- Every repository must have a CI pipeline that runs on every commit: linting, unit tests, integration tests, and build validation.
- Automate and make repeatable all production deployments. Document, minimise, and target manual steps for automation.
- Keep the main branch always in a deployable state. Broken builds block merges — they are not ignored or worked around.
- Ensure rollback is possible for every deployment within 15 minutes, via re-deploy, toggle, or automated revert.
- When creating or modifying CI configuration, ensure it includes all required stages: lint, test (unit + integration), build, deploy.

**[RECOMMENDED]**

- Measure DORA metrics: deployment frequency, lead time for changes, change failure rate, and mean time to restore (MTTR).
- Use blue/green or canary deployments for high-risk changes.

---

## 06 · Feature Toggles

### Feature Toggle Standards

Feature toggles decouple deployment from release. They enable continuous delivery, safe experimentation, and instant rollback without redeployment.

**[MUST]**

- Deploy unfinished features to production behind a toggle. New user-facing capabilities ship behind a toggle as the default approach.
- Explicitly distinguish toggle types: **Release toggles** (temporary), **Experiment toggles** (A/B tests), **Ops toggles** (kill switches), **Permission toggles** (per user/segment).
- Assign every toggle an owner, creation date, and planned removal date. Treat toggles active > 90 days without review as technical debt.
- Use a central feature toggle service or library — no ad-hoc booleans scattered across config files.
- When implementing a new feature, default to wrapping it in a feature toggle. When you see ad-hoc boolean flags controlling feature access, flag them as candidates for the central toggle system.

**[RECOMMENDED]**

- Make toggle state auditable: log every change to toggle state with actor, timestamp, and reason.
- Tie experiment toggles to an analytics event to track adoption and impact automatically.

---

## 07 · Observability, Monitoring & Tracking

### Logs, Metrics, Traces

Observability is not optional. You cannot operate what you cannot see. Every production service must be observable from day one.

**[MUST]**

- Use structured logging throughout. Emit logs in JSON format with consistent fields: timestamp, service, level, correlation/trace ID, and message.
- Emit key metrics from all services: request rate, error rate, latency (p50/p95/p99), and saturation (CPU, memory, queue depth).
- Implement distributed tracing for inter-service calls. Propagate trace IDs across service boundaries and through async messaging.
- Alert on the Four Golden Signals (latency, traffic, errors, saturation) for every production service. Alerts must be actionable — not noisy.
- Link runbooks from every alert. An engineer woken at 3am must know what to do without searching through chat history.
- When writing service code, use structured logging. When adding inter-service communication, propagate trace context.

**[RECOMMENDED]**

- Define Service Level Objectives (SLOs) for critical services. Track error budgets and use them to govern deployment decisions.
- Use a centralised observability platform (e.g. Datadog, Grafana + Loki + Tempo, or equivalent).
- Practice chaos engineering or failure injection to validate observability and resilience.

### Product Tracking & Analytics

**[MUST]**

- Maintain a tracking plan: every significant user interaction must have a named event, defined properties, and a documented owner before it ships.
- Validate analytics events in CI. Catch breaking changes to event schemas before they reach production.

**[RECOMMENDED]**

- Monitor data quality: alert on missing or anomalous event volumes.
- Maintain self-serve product dashboards accessible to non-engineers without requiring SQL or analytics expertise.

---

## 08 · Security & Dependency Management

### Security Baseline

**[MUST]**

- Run dependency vulnerability scanning in CI on every build. Critical and high-severity CVEs block merges to main.
- Review OWASP Top 10 as part of onboarding and incorporate it into the team's threat model.
- Encrypt all inter-service communication in transit (TLS). Encrypt data at rest for any personally identifiable or sensitive information.
- Apply the principle of least privilege to all service accounts, API keys, and IAM roles. Broad permissions are a blocker in PR review.
- Never hardcode secrets, API keys, or credentials. Use environment variables or a secrets manager.
- When reviewing code, check for OWASP Top 10 vulnerabilities: injection, broken auth, sensitive data exposure, etc.

**[RECOMMENDED]**

- Integrate SAST tools into CI (e.g. Semgrep, Snyk Code).
- Produce and review a formal threat model annually for each product.

---

## 09 · Incident Management & Blameless Culture

### Incident Response

Incidents are learning opportunities. A well-run incident process restores service quickly and systematically improves the system — without blame.

**[MUST]**

- Maintain an on-call schedule for every production service. Document responsibilities, escalation paths, and handover norms.
- Define severity levels (P1–P3 or equivalent) with explicit response time expectations for each level.
- Conduct post-incident reviews (PIRs) within 48 hours of any P1 or P2 incident. PIRs are blameless, action-focused, and outcomes are tracked.
- Treat PIR action items as first-class work and schedule them in the next sprint.
- When working on hotfixes or rollbacks, prioritise safety and speed. Use the PIR template in `docs/templates/pir-template.md` via `/pir`.

**[RECOMMENDED]**

- Store incident timelines and PIRs in a shared, searchable location accessible to all engineers.
- Track Mean Time to Detect (MTTD) and Mean Time to Restore (MTTR) monthly and discuss in engineering leadership reviews.

---

## 10 · Agentic Development

### Code Review of AI-Generated Code

**[MUST]**

- Apply the same Definition of Done to AI-generated code as to human-written code: peer reviewed, tests passing, feature toggled if needed, monitoring in place.
- Do not merge AI-generated code that has not been read and understood by at least one human engineer. "The AI wrote it" is not a substitute for review.
- When writing tests for AI-generated code, treat the AI as the author under review — do not rely on the AI to also write its own test coverage without independent verification.
- Flag AI-generated code in commit messages or PR descriptions when it constitutes a significant portion of the change. This is a traceability practice, not a stigma.

**[RECOMMENDED]**

- Add AI-assisted code review to your PR template as an explicit checklist item: *"If this PR includes AI-generated code, has a human verified correctness, test coverage, and security implications?"*
- Track the proportion of AI-generated changes in retrospectives to calibrate review overhead and identify areas where agent guidance (CLAUDE.md) needs improvement.

### Autonomy & Blast Radius

AI agents can operate across a wide range of autonomy — from supervised single-step suggestions to fully autonomous multi-step execution. Defining the boundary prevents irreversible mistakes.

**[MUST]**

- Define explicit autonomy levels for each agent workflow: **supervised** (human approves each action), **semi-autonomous** (human reviews plan before execution), or **autonomous** (agent runs unattended). Document these in the repo's CLAUDE.md or equivalent.
- Restrict autonomous agents to reversible actions by default. Actions that are hard to undo — force-pushes, production deployments, database migrations, external API calls, file deletions — require explicit human confirmation unless the workflow explicitly opts in.
- Never grant agents access to production environments, production secrets, or broad IAM permissions during development or CI workflows. Agent execution contexts must use the minimum credentials needed for the task.
- When an agent fails mid-task in an autonomous workflow, it must stop and surface the failure clearly — not silently retry or take a fallback action that was not explicitly authorised.

**[RECOMMENDED]**

- Implement a "blast radius" review as part of approving new agent workflows: what is the worst-case outcome if the agent misunderstands the task? If the answer is data loss or a production incident, add a human gate.
- Log all agent-initiated actions (file writes, shell commands, external calls) with enough context to reconstruct what the agent did and why. Treat this as an audit trail, not debug output.

### CLAUDE.md & Agent Instruction Hygiene

Agent instructions are code. Stale, vague, or unreviewed CLAUDE.md files produce inconsistent agent behaviour across the team — and inconsistency is the source of most agent-related bugs.

**[MUST]**

- Treat CLAUDE.md as a first-class artifact: version-controlled, reviewed in PRs, and updated when project conventions change. Never leave it in a known-stale state.
- Scope agent instructions to the repository they live in. Do not encode assumptions about external systems, team processes, or organisation-wide conventions unless they are also enforced in this repo's CI.
- When an agent produces unexpected output because of missing or incorrect instructions, fix the CLAUDE.md in the same PR that corrects the output — not in a follow-up ticket.
- Remove instructions that no longer apply. Dead instructions create noise that degrades agent output quality.

**[RECOMMENDED]**

- Audit CLAUDE.md quarterly or after any major architectural change. Check that enforced patterns still match what the codebase actually does.
- When onboarding a new engineer, walk them through CLAUDE.md as part of the repo tour — it documents how the project works and how the agent is configured to help.

### Security with Agents

AI agents inherit the attack surface of the tools they can call and the context they receive. Security hygiene that matters for humans matters more for agents — agents act faster and don't hesitate.

**[MUST]**

- Never pass secrets, API keys, or credentials into agent context (prompts, tool arguments, environment variables visible to the agent's shell). Use a secrets manager and inject credentials only into the process that needs them.
- Be aware of prompt injection: untrusted content processed by an agent (web pages, file contents, external API responses) can contain instructions intended to redirect the agent's behaviour. Treat agent output that acts on externally-sourced content with the same scrutiny as user input in a web application.
- Review the tool permissions granted to each agent workflow — especially shell access, network access, and filesystem write scope. Apply least-privilege: grant only what the workflow demonstrably needs.
- Do not use agent-assisted code generation to bypass security controls (code review, dependency scanning, secret detection). All CI gates apply to AI-generated code.

**[RECOMMENDED]**

- Include agent workflows in your threat model. Ask: what can go wrong if the agent is misdirected, given bad context, or produces subtly incorrect output in a security-sensitive path?
- Add prompt injection to the team's OWASP Top 10 review. It is the agentic equivalent of SQL injection.

---

## Summary · Standards at a Glance

| Category | Must Have | Recommended |
| --- | --- | --- |
| Culture & Working Agreements | Working Agreement, DoD, Retrospectives, Engineering Principles | Team Topology Charter, Escalation Paths |
| Architecture & ADRs | ADRs for all significant decisions, stored in repo, never deleted | Architecture Advisory Forum, Architecture Maps |
| Evolutionary Architecture | Clear boundaries, no circular deps, CODEOWNERS | Automated fitness functions, C4 diagrams |
| Code Review | Mandatory peer review, small PRs, etiquette guide | Pair programming, review metrics |
| Code Organisation | README standard, no secrets in code, linting in CI | CONTRIBUTING.md, monorepo ADR |
| Test Strategy | Documented strategy, unit + integration + E2E, no flaky tests | Coverage enforcement, contract tests, load tests |
| Commit Conventions & Versioning | Conventional Commits enforced in CI, semver, automated version bumping on merge, auto-generated CHANGELOG | Git release tags, automated release notes |
| CI/CD Pipeline | CI on every commit, automated deployments, rollback in 15 min | DORA metrics, blue/green deploys |
| Feature Toggles | All features behind toggles, typed toggles, central service, stale toggle policy | Toggle audit log, linked analytics events |
| Observability | Structured logs, golden signal metrics, tracing, alerts with runbooks | SLOs, centralised platform, chaos engineering |
| Product Tracking | Tracking plan, schema validation in CI | Data quality monitoring, self-serve dashboards |
| Security | CVE scanning in CI, TLS everywhere, least privilege | SAST integration, formal threat model |
| Incident Management | On-call schedule, severity levels, blameless PIRs within 48h | Searchable PIR library, MTTD/MTTR tracking |
| Agentic Development | DoD for AI-generated code, autonomy levels defined, CLAUDE.md version-controlled, no secrets in agent context, prompt injection awareness | AI-assisted PR checklist, blast radius review, agent audit log, quarterly CLAUDE.md audit |

---

*This document is a living standard. All engineers are encouraged to propose updates via the Architecture Advisory Forum or directly as pull requests to the standards repository.*
