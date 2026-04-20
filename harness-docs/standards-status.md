<!-- assessed_at: 2026-04-20 -->
<!-- assessed_by: /verify-assessment -->

# Standards Status

> Last assessed: **2026-04-20** via `/verify-assessment` · Run again to refresh.

## Summary

| Category | MUST ✅ | MUST ❌ | REC ✅ | REC ❌ |
|---|---|---|---|---|
| 01 · Culture & Working Agreements | 2 | 4 | 0 | 2 |
| 02 · Architecture & Decision Records | 1 | 6 | 0 | 4 |
| 03 · Code Quality, Reviews & Standards | 5 | 4 | 0 | 3 |
| 04 · Test Strategy | 6 | 3 | 0 | 3 |
| 05 · Continuous Delivery & CI/CD | 10 | 4 | 1 | 2 |
| 06 · Feature Toggles | 0 | 0 | 0 | 0 |
| 07 · Observability, Monitoring & Tracking | 2 | 2 | 0 | 0 |
| 08 · Security & Dependency Management | 2 | 5 | 0 | 2 |
| 09 · Incident Management & Blameless Culture | 0 | 2 | 0 | 0 |
| 10 · Agentic Development | 16 | 0 | 1 | 7 |
| **Total** | **44** | **30** | **2** | **23** |

---

## 01 · Culture & Working Agreements

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Written Working Agreement (cadences, comms, DoD, on-call, decisions) | MUST | ✅ PASS | 2026-04-20 | /working-agreement | `harness-docs/working-agreement.md` covers cadences, comms, DoD, on-call (N/A-justified), decisions |
| Definition of Done applied to every story | MUST | ✅ PASS | 2026-04-20 | /working-agreement | DoD checklist in `working-agreement.md`; mirrored in `.github/pull_request_template.md` |
| Bi-weekly retrospectives with tracked action items | MUST | ⚠️ WARN | 2026-04-20 | /working-agreement | Monthly self-retro declared (slower than bi-weekly, adapted for solo); no retro notes committed |
| Team Topology charter | REC | ❌ FAIL | 2026-04-20 | — | No charter file; N/A for solo-maintainer but not explicitly marked |
| Documented escalation path | REC | ❌ FAIL | 2026-04-20 | — | No escalation section in `working-agreement.md` or elsewhere |
| Build for replacement, not perfection | MUST | ❌ FAIL | 2026-04-20 | — | Principle not stated in CLAUDE.md, working-agreement.md, or any principles doc |
| Default to open (documented forums) | MUST | ⚠️ WARN | 2026-04-20 | — | ADR flow documented, but principle not named |
| Optimize for fast feedback | MUST | ❌ FAIL | 2026-04-20 | — | Principle not stated; CI exists but no articulated principle doc |

---

## 02 · Architecture & Decision Records

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Document significant architectural decisions as ADRs | MUST | ⚠️ WARN | 2026-04-20 | /adr | Only 1 ADR exists (`harness-docs/adr/0001-*`); ARCHITECTURE.md lists 8 architectural decisions but only one has a backing ADR |
| Use standard ADR template | MUST | ✅ PASS | 2026-04-20 | /adr | `harness-docs/templates/adr-template.md` present; ADR-0001 conforms |
| Store ADRs in `/docs/adr/` and link from README | MUST | ❌ FAIL | 2026-04-20 | — | Stored at `harness-docs/adr/` (acceptable location); README contains no link to ADRs |
| Never delete ADRs; mark Deprecated/Superseded | MUST | ➖ SKIP | 2026-04-20 | — | Only 1 ADR exists; nothing to deprecate yet |
| Check for existing ADR before architectural decisions | MUST | ⚠️ WARN | 2026-04-20 | — | No documented process/hook; CLAUDE.md mentions `/adr` skill as suggestion only |
| Architecture Advisory Forum | REC | ❌ FAIL | 2026-04-20 | — | No AAF cadence or minutes |
| Visualise ADRs in architecture map/wiki | REC | ❌ FAIL | 2026-04-20 | — | ARCHITECTURE.md has decisions section but no visualisation/map |
| Clear service/module boundaries with explicit interfaces | MUST | ⚠️ WARN | 2026-04-20 | — | Flat single-package layout; Pydantic schemas document some boundaries but no enforced module interfaces |
| No circular dependencies | MUST | ⚠️ WARN | 2026-04-20 | — | No fitness function / import-linter config |
| CODEOWNERS for every service/module | MUST | ❌ FAIL | 2026-04-20 | — | No CODEOWNERS file at `/`, `.github/`, or `docs/` |
| Automated fitness functions in CI | REC | ❌ FAIL | 2026-04-20 | — | No import-linter, archunit-style checks, or dependency-cycle detection |
| C4 Level 1–2 diagram | REC | ⚠️ WARN | 2026-04-20 | — | ASCII pipeline + ARCHITECTURE.md structural description; no formal C4 diagram |

---

## 03 · Code Quality, Reviews & Standards

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Peer review before merge to main; no self-merge | MUST | ✅ PASS | 2026-04-20 | /working-agreement | `working-agreement.md` §Code Review Norms + CLAUDE.md rule 5 |
| PRs small/focused, reviewable in <30 min | MUST | ✅ PASS | 2026-04-20 | /working-agreement | `pull_request_template.md` header comment instructs this |
| PR description: what/why/how-to-test/ticket | MUST | ✅ PASS | 2026-04-20 | /working-agreement | PR template has What changed / Why / How to test / Ticket or ADR sections |
| Actionable, Conventional Comments style feedback | MUST | ✅ PASS | 2026-04-20 | /working-agreement | `working-agreement.md` links conventionalcomments.org with label examples |
| Flag stale PRs (>3 days without activity) | MUST | ⚠️ WARN | 2026-04-20 | /working-agreement | Stated in working-agreement; no automation (no stale-bot workflow) |
| Pair/mob programming for complex changes | REC | ➖ SKIP | 2026-04-20 | — | Solo maintainer per working-agreement §Team Context |
| Track PR review metrics | REC | ❌ FAIL | 2026-04-20 | — | No metrics tooling |
| README with purpose/setup/tests/deploy/ADR links | MUST | ⚠️ WARN | 2026-04-20 | — | README has purpose + Quick Start + tests; no deploy section, no ADR link |
| Consistent folder structure documented in ADR | MUST | ❌ FAIL | 2026-04-20 | — | Only ADR-0001 (LLM migration); no folder-structure ADR |
| Never commit secrets/config to source control | MUST | ✅ PASS | 2026-04-20 | manual | `.gitignore` covers env files; CLAUDE.md rule 1 enforces; no secrets observed |
| Enforce linting/formatting via pre-commit or CI | MUST | ❌ FAIL | 2026-04-20 | — | No `.pre-commit-config.yaml`; no lint step in any workflow; ruff only in local PostToolUse hook |
| Monorepo vs polyrepo decision in ADR | REC | ❌ FAIL | 2026-04-20 | — | No such ADR |
| Maintain CONTRIBUTING.md | REC | ❌ FAIL | 2026-04-20 | — | File does not exist at repo root |

---

## 04 · Test Strategy

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Documented test strategy covering unit/integration/E2E | MUST | ❌ FAIL | 2026-04-20 | — | No TEST_STRATEGY.md or docs/testing.md; only stale `.planning/codebase/TESTING.md` |
| Unit tests cover business logic | MUST | ✅ PASS | 2026-04-20 | manual | `tests/` has test_analyzer, test_router, test_oracle, test_task_runner, test_contract_schema, etc. |
| Unit tests run in CI on every commit | MUST | ✅ PASS | 2026-04-20 | manual | `tests.yml` runs on push + PR to master/main |
| Unit tests fast (<1 min) | MUST | ⚠️ WARN | 2026-04-20 | — | No timeout enforced in tests.yml; integration-tests.yml uses `--timeout=60` for unit subset |
| Unit tests isolated and deterministic | MUST | ✅ PASS | 2026-04-20 | manual | `tests/fake_claude.py` + `conftest.py` provide hermetic doubles |
| Integration tests with test doubles in CI | MUST | ✅ PASS | 2026-04-20 | manual | `tests/integration/test_portal_contract.py` + fake_claude.py drive mocked Portal/Claude |
| Limit E2E tests to critical user journeys | MUST | ✅ PASS | 2026-04-20 | manual | `test_e2e_portal.py` + `test_e2e.py` gated behind `workflow_dispatch` + `-m e2e` |
| Treat tests as first-class; fix flaky tests within one sprint | MUST | ⚠️ WARN | 2026-04-20 | — | No flaky-test tracking or quarantine policy documented |
| Write/update tests alongside code changes | MUST | ✅ PASS | 2026-04-20 | manual | CLAUDE.md rule 3 + standards-reviewer agent enforce |
| Measure and report code coverage in CI; 70–80% baseline | REC | ❌ FAIL | 2026-04-20 | — | `pytest-cov` installed but `tests.yml` echoes `"Coverage report would go here."` — no report, no gate |
| Contract testing (Pact) | REC | ❌ FAIL | 2026-04-20 | — | Schema-level contract tests only; not Pact-based |
| Perf/load tests | REC | ❌ FAIL | 2026-04-20 | — | None present |

---

## 05 · Continuous Delivery & CI/CD

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Use Conventional Commits format | MUST | ✅ PASS | 2026-04-20 | /add-release | `.commitlintrc.json` extends @commitlint/config-conventional |
| Enforce Conventional Commits via commitlint in CI | MUST | ✅ PASS | 2026-04-20 | /add-release | `commitlint.yml` runs `wagoid/commitlint-github-action@v6` on PR + push-to-master |
| Follow SemVer | MUST | ✅ PASS | 2026-04-20 | /add-release | Tags v1.0.0–v2.0.0; ci.yml enforces PEP 440; release-please-config.json declares `release-type: python` |
| Automate version bumping via semantic-release/release-please | MUST | ✅ PASS | 2026-04-20 | /add-release | `release-please.yml` + config; bump-my-version retained but superseded |
| Auto-generate CHANGELOG.md from commits | MUST | ✅ PASS | 2026-04-20 | /add-release | release-please generates CHANGELOG on each release PR |
| Tag every release commit | REC | ✅ PASS | 2026-04-20 | /add-release | release-please creates tag on release-PR merge; release.yml triggers on tag push |
| Publish release notes to team channel | REC | ❌ FAIL | 2026-04-20 | — | No Slack/Discord/webhook notification step |
| CI runs on every commit | MUST | ✅ PASS | 2026-04-20 | manual | `ci.yml`, `tests.yml`, `integration-tests.yml`, `commitlint.yml` trigger on push + PR |
| CI includes linting | MUST | ❌ FAIL | 2026-04-20 | — | No ruff/black/flake8/pylint step in any workflow; `[tool.ruff]` absent from pyproject.toml |
| CI includes unit tests | MUST | ✅ PASS | 2026-04-20 | manual | `tests.yml` runs `pytest tests/` |
| CI includes integration tests | MUST | ✅ PASS | 2026-04-20 | manual | `integration-tests.yml` runs portal contract + e2e suites |
| CI includes build validation | MUST | ⚠️ WARN | 2026-04-20 | — | `release.yml` runs `uv build` only on tag push, not every PR |
| Automate all production deployments | MUST | ✅ PASS | 2026-04-20 | manual | `release.yml` on tag push runs `uv build` + attaches wheel + sdist to GitHub Release |
| Main branch always deployable | MUST | ⚠️ WARN | 2026-04-20 | — | CI runs on PRs; branch-protection rules not visible in repo |
| Rollback possible within 15 min | MUST | ✅ PASS | 2026-04-20 | manual | Prior version wheels on GitHub Releases; `pip install pkg==<prev>` satisfies 15-min rollback |
| CI config must include lint/test/build/deploy | MUST | ❌ FAIL | 2026-04-20 | — | Lint stage missing; build only on tag push, not every commit |
| Measure DORA metrics | REC | ❌ FAIL | 2026-04-20 | — | No DORA tooling |
| Blue/green or canary | REC | ➖ SKIP | 2026-04-20 | — | Python library/CLI package, not a deployed service |

---

## 06 · Feature Toggles

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Deploy unfinished features behind a toggle | MUST | ➖ SKIP | 2026-04-20 | — | CLI tool; no user-facing runtime features requiring toggles |
| Explicitly distinguish toggle types | MUST | ➖ SKIP | 2026-04-20 | — | No toggles in use |
| Assign owner/creation/removal date; >90d = debt | MUST | ➖ SKIP | 2026-04-20 | — | No toggles to track |
| Central toggle service/library — no ad-hoc booleans | MUST | ➖ SKIP | 2026-04-20 | — | No flag library; env vars are config only |
| Default to wrapping new features in a toggle | MUST | ➖ SKIP | 2026-04-20 | — | CLI scope makes default-wrap policy inapplicable |
| Auditable toggle state | REC | ➖ SKIP | 2026-04-20 | — | No toggles to audit |
| Tie experiment toggles to analytics | REC | ➖ SKIP | 2026-04-20 | — | No experiment toggles |

---

## 07 · Observability, Monitoring & Tracking

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Structured logging (JSON w/ timestamp, service, level, trace ID, message) | MUST | ✅ PASS | 2026-04-20 | /add-structured-logging | `DirigentLogger` at `src/outbid_dirigent/logger.py` now emits all five required fields on every JSONL record and every `@@JSON@@` stdout event; covered by `tests/test_logger_fields.py` |
| Emit key metrics (rate/error/latency/saturation) | MUST | ➖ SKIP | 2026-04-20 | — | CLI tool; no service runtime to emit RED/USE metrics |
| Distributed tracing, propagate trace IDs | MUST | ➖ SKIP | 2026-04-20 | — | CLI tool; no cross-service boundaries |
| Alert on Four Golden Signals | MUST | ➖ SKIP | 2026-04-20 | — | CLI tool; no alerting surface |
| Link runbooks from every alert | MUST | ➖ SKIP | 2026-04-20 | — | No alerts; runbook template unused |
| Structured logging in service code; propagate trace context | MUST | ✅ PASS | 2026-04-20 | /add-structured-logging | `trace_id` sourced from `EXECUTION_ID` env (set by portal when dirigent runs as child) or `uuid4().hex` fallback; stable across a run; `print()` calls remain legitimate CLI user-facing output per CLAUDE.md |
| Define SLOs, track error budgets | REC | ➖ SKIP | 2026-04-20 | — | Not a service |
| Centralised observability platform | REC | ➖ SKIP | 2026-04-20 | — | CLI tool; N/A |
| Chaos engineering | REC | ➖ SKIP | 2026-04-20 | — | Not a service |
| Maintain tracking plan | MUST | ❌ FAIL | 2026-04-20 | — | No `docs/tracking-plan.md` for dirigent; only template |
| Validate analytics events in CI | MUST | ❌ FAIL | 2026-04-20 | — | No tracking plan to validate against |
| Monitor data quality | REC | ➖ SKIP | 2026-04-20 | — | No analytics pipeline |
| Self-serve product dashboards | REC | ➖ SKIP | 2026-04-20 | — | No product dashboards |

---

## 08 · Security & Dependency Management

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Dependency vulnerability scanning in CI on every build | MUST | ❌ FAIL | 2026-04-20 | — | No dependabot.yml, renovate, pip-audit, safety, snyk, or trivy in any workflow |
| Critical/high CVEs block merges | MUST | ❌ FAIL | 2026-04-20 | — | No CVE scanner runs; nothing can block |
| OWASP Top 10 reviewed as part of onboarding | MUST | ⚠️ WARN | 2026-04-20 | — | CLAUDE.md + harness-docs present but no explicit OWASP onboarding checkpoint |
| Encrypt inter-service communication (TLS) | MUST | ✅ PASS | 2026-04-20 | manual | Portal API calls use `https://`; only `http://` references are localhost dev instructions |
| Encrypt data at rest for PII | MUST | ➖ SKIP | 2026-04-20 | — | Agent controller holds no PII datastore |
| Principle of least privilege for accounts/keys/IAM | MUST | ⚠️ WARN | 2026-04-20 | — | Workflow secrets scoped via `${{ secrets.* }}`; no documented IAM/least-privilege policy |
| Never hardcode secrets | MUST | ✅ PASS | 2026-04-20 | manual | No hardcoded credentials; workflows use `${{ secrets.* }}`; no `.env` tracked |
| Check for OWASP Top 10 in code review | MUST | ❌ FAIL | 2026-04-20 | — | `pull_request_template.md` has no OWASP/security checklist item |
| Integrate SAST tools (Semgrep, Snyk Code) | REC | ❌ FAIL | 2026-04-20 | — | No semgrep/snyk/bandit configured |
| Formal threat model annually | REC | ❌ FAIL | 2026-04-20 | — | No THREAT_MODEL.md or equivalent |

---

## 09 · Incident Management & Blameless Culture

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| On-call schedule per production service | MUST | ➖ SKIP | 2026-04-20 | — | CLI dev repo; no production service; working-agreement.md documents N/A with reinstate trigger |
| Severity levels (P1–P3) with response SLAs | MUST | ❌ FAIL | 2026-04-20 | — | No standalone severity-level doc or SLA definition |
| PIRs within 48h of P1/P2; blameless, action-focused | MUST | ➖ SKIP | 2026-04-20 | — | No production service; no P1/P2 incidents possible |
| PIR action items as first-class sprint work | MUST | ➖ SKIP | 2026-04-20 | — | Contingent on PIRs |
| Use PIR template in docs/templates/pir-template.md | MUST | ⚠️ WARN | 2026-04-20 | — | Template at `harness-docs/templates/pir-template.md`; standards spec phrases path as `docs/templates/` |
| Store PIRs in searchable location | REC | ➖ SKIP | 2026-04-20 | — | No incidents; revisit when hosted component ships |
| Track MTTD/MTTR monthly | REC | ➖ SKIP | 2026-04-20 | — | No production service |

---

## 10 · Agentic Development

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Apply same DoD to AI-generated code as human | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md §Agentic Development AI-generated code policy enforces DoD parity |
| Do not merge AI-generated code without human read | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md + PR template checkbox for human-read/understood |
| Treat AI as author under review when writing tests | MUST | ✅ PASS | 2026-04-20 | /working-agreement | CLAUDE.md §Tests with new code + PR template test-coverage checkbox |
| Flag AI-generated code in commits/PR descriptions | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md mandates Co-Authored-By trailer; PR template checkbox |
| AI-assisted review in PR template checklist | REC | ✅ PASS | 2026-04-20 | /working-agreement | PR template has explicit AI-generated section |
| Track proportion of AI-generated changes | REC | ⚠️ WARN | 2026-04-20 | — | Co-Authored-By trailer enables grep-based tracking; no dashboard |
| Define autonomy levels in CLAUDE.md | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md §Agentic Development declares "Autonomy level: Semi-autonomous" |
| Restrict autonomous agents to reversible actions | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | §Blast radius list gates destructive ops behind human confirmation |
| Never grant production access/secrets/IAM to agents | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | §Tool permissions asserts no prod creds in agent context |
| On agent failure: stop and surface, don't silently retry | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | Semi-autonomous section mandates stop-and-surface; no silent retries |
| Blast radius review for new agent workflows | REC | ⚠️ WARN | 2026-04-20 | — | Blast radius list in CLAUDE.md; no per-workflow review checklist |
| Log all agent-initiated actions | REC | ⚠️ WARN | 2026-04-20 | — | `.claude/settings.json` PostToolUse hook logs tool names; not comprehensive audit |
| Treat CLAUDE.md as first-class artifact | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | Checked in at repo root; wrapped in `<!-- BEGIN:bid-harness -->` markers |
| Scope agent instructions to the repo | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | Project CLAUDE.md is repo-scoped |
| Fix CLAUDE.md in same PR that corrects agent output | MUST | ✅ PASS | 2026-04-20 | /working-agreement | `working-agreement.md` codifies same-PR fix rule |
| Remove instructions that no longer apply | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md is lean; no stale directives; `claude-md-improver` skill available |
| Audit CLAUDE.md quarterly | REC | ⚠️ WARN | 2026-04-20 | — | `audit-claude-md` skill available; no scheduled cadence |
| Onboarding walkthrough of CLAUDE.md | REC | ⚠️ WARN | 2026-04-20 | — | No dedicated onboarding doc; CLAUDE.md self-documenting |
| Never pass secrets into agent context | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | PreToolUse hook scans Write/Edit for secrets; CLAUDE.md rule 1 forbids |
| Prompt injection awareness | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md §Prompt injection awareness section |
| Review tool permissions per workflow (least privilege) | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md §Tool permissions asserts least-privilege |
| Do not bypass security controls with AI | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | settings.json deny rules + secrets hook enforce; CLAUDE.md rule 11 mandates standards-reviewer |
| Include agent workflows in threat model | REC | ❌ FAIL | 2026-04-20 | — | No threat model document |
| Prompt injection in OWASP Top 10 review | REC | ❌ FAIL | 2026-04-20 | — | No OWASP review document |
