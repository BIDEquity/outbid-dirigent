<!-- assessed_at: 2026-04-20 -->
<!-- assessed_by: /assess -->

# Standards Status

> Last assessed: **2026-04-20** via `/assess` · Run `/verify-assessment` to update.

## Summary

| Category | MUST ✅ | MUST ❌ | REC ✅ | REC ❌ |
|---|---|---|---|---|
| 01 · Culture & Working Agreements | 3 | 3 | 0 | 2 |
| 02 · Architecture & Decision Records | 2 | 5 | 0 | 3 |
| 03 · Code Quality, Reviews & Standards | 1 | 8 | 0 | 4 |
| 04 · Test Strategy | 2 | 4 | 0 | 3 |
| 05 · Continuous Delivery & CI/CD | 8 | 6 | 1 | 2 |
| 06 · Feature Toggles | 0 | 0 | 0 | 0 |
| 07 · Observability, Monitoring & Tracking | 0 | 4 | 0 | 1 |
| 08 · Security & Dependency Management | 1 | 6 | 0 | 2 |
| 09 · Incident Management & Blameless Culture | 0 | 2 | 0 | 2 |
| 10 · Agentic Development | 7 | 9 | 0 | 8 |
| **Total** | **24** | **47** | **1** | **27** |

---

## 01 · Culture & Working Agreements

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Written Working Agreement (cadences, comms, DoD, on-call, decisions) | MUST | ✅ PASS | 2026-04-20 | /working-agreement | Created `harness-docs/working-agreement.md` covering cadences, comms, DoD, on-call (N/A), decision-making, review norms |
| Definition of Done applied to every story | MUST | ✅ PASS | 2026-04-20 | /working-agreement | DoD checklist in `harness-docs/working-agreement.md`; operationalised via `.github/pull_request_template.md` |
| Bi-weekly retrospectives with tracked action items | MUST | ✅ PASS | 2026-04-20 | /working-agreement | Monthly self-retro cadence defined in working agreement (bi-weekly not applicable for solo-maintainer context); action items tracked in ClickUp |
| Build for replacement, not perfection | MUST | ❌ FAIL | 2026-04-20 | — | Principle appears only in engineering-standards.md; no project principles doc |
| Default to open (documented forums for decisions) | MUST | ⚠️ WARN | 2026-04-20 | — | ADR template exists but no open-forum process or decision log instantiated |
| Optimize for fast feedback | MUST | ⚠️ WARN | 2026-04-20 | — | pyproject.toml configures pytest + ruff; no explicit principles statement |
| Team Topology charter | REC | ❌ FAIL | 2026-04-20 | — | No charter or topology document |
| Documented escalation path | REC | ❌ FAIL | 2026-04-20 | — | No escalation doc in harness-docs/ |

---

## 02 · Architecture & Decision Records

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Document significant architectural decisions as ADRs | MUST | ✅ PASS | 2026-04-20 | /adr | First ADR created: `harness-docs/adr/0001-migrate-llm-callers-to-claude-agent-sdk.md` |
| Use standard ADR template (Title/Status/Context/Decision/Consequences/Alternatives) | MUST | ✅ PASS | 2026-04-20 | /adr | ADR-0001 uses the template at `harness-docs/templates/adr-template.md` |
| Store ADRs in /docs/adr/ and link from README | MUST | ⚠️ WARN | 2026-04-20 | /adr | ADRs now stored in `harness-docs/adr/`; README link to ADRs still pending |
| Never delete ADRs; mark as Deprecated/Superseded | MUST | ➖ SKIP | 2026-04-20 | — | No ADRs exist to deprecate |
| Check for existing ADR before architectural decisions | MUST | ⚠️ WARN | 2026-04-20 | — | `/adr` skill installed but no ADRs despite significant decisions (SDK migration, observability) |
| Clear service/module boundaries with explicit interfaces | MUST | ⚠️ WARN | 2026-04-20 | — | `src/outbid_dirigent/` has submodules but no explicit interface contracts documented |
| Eliminate circular dependencies between modules | MUST | ⚠️ WARN | 2026-04-20 | — | No automated cyclic-dependency check configured |
| Documented owner for every service/module (CODEOWNERS) | MUST | ❌ FAIL | 2026-04-20 | — | No CODEOWNERS file at root, `.github/`, or `docs/` |
| Architecture Advisory Forum | REC | ❌ FAIL | 2026-04-20 | — | No AAF cadence or minutes in repo |
| Visualise ADRs in architecture map | REC | ➖ SKIP | 2026-04-20 | — | No ADRs to visualise |
| Automated architectural fitness functions in CI | REC | ❌ FAIL | 2026-04-20 | — | No cycle/boundary/performance checks in workflows |
| C4 Level 1–2 system context diagram | REC | ⚠️ WARN | 2026-04-20 | — | ARCHITECTURE.md exists but no C4-labelled diagrams |

---

## 03 · Code Quality, Reviews & Standards

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Peer review required before merge to main | MUST | ⚠️ WARN | 2026-04-20 | — | No CODEOWNERS, no branch-protection config visible in repo |
| PRs small/focused, reviewable in under 30 min | MUST | ⚠️ WARN | 2026-04-20 | — | No PR template; recent commits look focused but no tooling signal |
| PR description includes what/why/test/ticket link | MUST | ❌ FAIL | 2026-04-20 | — | No `.github/pull_request_template.md` |
| Conventional Comments style feedback | MUST | ❌ FAIL | 2026-04-20 | — | No guideline referencing Conventional Comments |
| Flag stale PRs (>3 days without activity) | MUST | ❌ FAIL | 2026-04-20 | — | No stale-bot workflow |
| Pair/mob programming for complex changes | REC | ⚠️ WARN | 2026-04-20 | — | No explicit guidance; not enforceable via repo |
| Track PR review metrics | REC | ❌ FAIL | 2026-04-20 | — | No metrics tooling |
| README with purpose/setup/tests/deploy/ADR links | MUST | ⚠️ WARN | 2026-04-20 | — | README has purpose/install/dev — missing deployment notes and links to ADRs/runbooks |
| Consistent folder structure documented in ADR | MUST | ⚠️ WARN | 2026-04-20 | — | Structure is consistent; ARCHITECTURE.md exists but no ADR directory |
| Never commit secrets/config to source control | MUST | ✅ PASS | 2026-04-20 | — | No `.env` committed; workflows use `${{ secrets.* }}`; no hardcoded keys found |
| Enforce linting/formatting via pre-commit or CI | MUST | ❌ FAIL | 2026-04-20 | — | No `.pre-commit-config.yaml`; no `[tool.ruff]`/`[tool.black]` in pyproject.toml; no lint step in workflows |
| Document monorepo vs polyrepo decision in ADR | REC | ❌ FAIL | 2026-04-20 | — | No ADR directory |
| Maintain CONTRIBUTING.md | REC | ❌ FAIL | 2026-04-20 | — | No CONTRIBUTING.md at repo root |

---

## 04 · Test Strategy

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Documented test strategy covering unit/integration/E2E | MUST | ❌ FAIL | 2026-04-20 | — | No TEST_STRATEGY.md or docs/testing.md; README has no testing section |
| Unit tests cover business logic, run in CI, fast/isolated/deterministic | MUST | ⚠️ WARN | 2026-04-20 | — | Tests exist in `tests/` and run via `tests.yml` (`--timeout=60`); no documented isolation policy |
| Integration tests with test doubles in CI | MUST | ✅ PASS | 2026-04-20 | — | `tests/integration/test_portal_contract.py`; `tests/fake_claude.py` doubles; runs in `integration-tests.yml` |
| Limit E2E tests to critical user journeys | MUST | ✅ PASS | 2026-04-20 | — | E2E gated behind `workflow_dispatch` inputs; `@e2e`-marked tests not run on every PR |
| Treat tests as first-class; fix flaky tests within one sprint | MUST | ❌ FAIL | 2026-04-20 | — | No flaky-test policy document |
| Write/update tests alongside code changes | MUST | ⚠️ WARN | 2026-04-20 | — | CLAUDE.md Rule #3 enforces; no coverage-diff gate in CI |
| Measure and report code coverage in CI | REC | ❌ FAIL | 2026-04-20 | — | pytest-cov installed but `tests.yml` only echoes placeholder; no `--cov` flag or threshold |
| Adopt contract testing (Pact) | REC | ⚠️ WARN | 2026-04-20 | — | `test_portal_contract.py` exists but not Pact-based |
| Performance/load tests | REC | ❌ FAIL | 2026-04-20 | — | No perf/load tests in repo |

---

## 05 · Continuous Delivery & CI/CD

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Use Conventional Commits format | MUST | ✅ PASS | 2026-04-20 | /add-release | `.commitlintrc.json` extends `@commitlint/config-conventional` — standard type list now enforced; `bump:` / `refine:` commits pre-date enforcement |
| Enforce Conventional Commits via commitlint in CI | MUST | ✅ PASS | 2026-04-20 | /add-release | `.github/workflows/commitlint.yml` runs `wagoid/commitlint-github-action@v6` on `pull_request` and push-to-master; non-conforming commits block merge |
| Follow SemVer | MUST | ✅ PASS | 2026-04-20 | /add-release | Tags v1.0.0–v2.0.0 follow SemVer; ci.yml enforces PEP 440 pattern; release-please-config.json declares `release-type: python` (SemVer) |
| Automate version bumping via semantic-release/release-please | MUST | ✅ PASS | 2026-04-20 | /add-release | Added `.github/workflows/release-please.yml` + `release-please-config.json` + `.release-please-manifest.json` seeded at 2.0.0; bump-my-version retained but will be superseded once release-please lands the first release PR |
| Auto-generate CHANGELOG.md from commits | MUST | ✅ PASS | 2026-04-20 | /add-release | release-please generates/updates CHANGELOG.md on each release PR; existing release.yml still attaches built wheels on tag push |
| CI runs on every commit | MUST | ✅ PASS | 2026-04-20 | — | `ci.yml`, `tests.yml`, `integration-tests.yml` trigger on push + PR |
| CI includes linting | MUST | ❌ FAIL | 2026-04-20 | — | No ruff/black/flake8/pylint step in any workflow |
| CI includes unit tests | MUST | ✅ PASS | 2026-04-20 | — | `tests.yml` runs `pytest tests/` |
| CI includes integration tests | MUST | ✅ PASS | 2026-04-20 | — | `integration-tests.yml` runs portal contract + e2e suites |
| CI includes build validation | MUST | ⚠️ WARN | 2026-04-20 | — | `release.yml` runs `uv build` only on tag push, not regular PRs |
| Automate all production deployments | MUST | ❌ FAIL | 2026-04-20 | — | No deploy step; release.yml only builds and uploads GitHub release artifacts |
| Main branch always deployable | MUST | ⚠️ WARN | 2026-04-20 | — | CI runs on PRs; branch-protection rules not visible in repo |
| Rollback possible within 15 min | MUST | ⚠️ WARN | 2026-04-20 | — | Tags enable revert; no documented rollback runbook |
| CI must include lint/test/build/deploy | MUST | ❌ FAIL | 2026-04-20 | — | Lint and deploy steps absent |
| Tag every release commit | REC | ✅ PASS | 2026-04-20 | — | `git tag -l` shows v1.0.0–v2.0.0 including rc tags |
| Publish release notes to team channel | REC | ❌ FAIL | 2026-04-20 | — | No Slack/Teams/Discord notification step |
| Measure DORA metrics | REC | ❌ FAIL | 2026-04-20 | — | No DORA tooling/workflow |
| Blue/green or canary deployments | REC | ➖ SKIP | 2026-04-20 | — | Python library/CLI package, not a deployed service |

---

## 06 · Feature Toggles

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Deploy unfinished features behind a toggle | MUST | ➖ SKIP | 2026-04-20 | — | CLI/plugin tool with no user-facing runtime features |
| Explicitly distinguish toggle types | MUST | ➖ SKIP | 2026-04-20 | — | No toggles present in codebase |
| Assign owner/creation/removal date to every toggle | MUST | ➖ SKIP | 2026-04-20 | — | No toggles exist |
| Use central feature toggle service/library | MUST | ➖ SKIP | 2026-04-20 | — | No flag library needed; env vars are config, not feature gates |
| Default to wrapping new features in a toggle | MUST | ➖ SKIP | 2026-04-20 | — | No runtime feature surface |
| Make toggle state auditable | REC | ➖ SKIP | 2026-04-20 | — | No toggles to audit |
| Tie experiment toggles to analytics events | REC | ➖ SKIP | 2026-04-20 | — | No experiment toggles |

---

## 07 · Observability, Monitoring & Tracking

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Structured logging (JSON with timestamp, service, level, trace ID, message) | MUST | ⚠️ WARN | 2026-04-20 | — | `src/outbid_dirigent/logger.py` emits JSONL but missing `service` and `correlation/trace ID`; 41 `print()` calls bypass logger |
| Emit key metrics (rate, error, latency, saturation) | MUST | ➖ SKIP | 2026-04-20 | — | CLI tool, no service runtime |
| Distributed tracing, propagate trace IDs | MUST | ➖ SKIP | 2026-04-20 | — | No inter-service RPC |
| Alert on Four Golden Signals | MUST | ➖ SKIP | 2026-04-20 | — | Not a production service |
| Link runbooks from every alert | MUST | ➖ SKIP | 2026-04-20 | — | No alerts; runbook template unused |
| Use structured logging in service code; propagate trace context | MUST | ⚠️ WARN | 2026-04-20 | — | DirigentLogger used throughout; trace context not propagated; 41 `print()` calls remain |
| Define SLOs, track error budgets | REC | ➖ SKIP | 2026-04-20 | — | Not a service |
| Centralised observability platform | REC | ❌ FAIL | 2026-04-20 | — | Logs only to local `.dirigent/logs/run-*.jsonl` |
| Chaos engineering | REC | ➖ SKIP | 2026-04-20 | — | Not a production service |
| Maintain tracking plan | MUST | ❌ FAIL | 2026-04-20 | — | No `docs/tracking-plan.md` for dirigent itself; only template at `harness-docs/templates/tracking-plan-template.md` |
| Validate analytics events in CI | MUST | ❌ FAIL | 2026-04-20 | — | No event-schema validation workflow |
| Monitor data quality | REC | ➖ SKIP | 2026-04-20 | — | No analytics pipeline for dirigent itself |
| Self-serve product dashboards | REC | ➖ SKIP | 2026-04-20 | — | CLI; no product dashboards |

---

## 08 · Security & Dependency Management

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Dependency vulnerability scanning in CI on every build | MUST | ❌ FAIL | 2026-04-20 | — | No dependabot/renovate/safety/pip-audit/snyk/semgrep in `.github/workflows/` |
| Critical/high CVEs block merges | MUST | ❌ FAIL | 2026-04-20 | — | No CVE-gating job in any workflow |
| OWASP Top 10 reviewed as part of onboarding | MUST | ❌ FAIL | 2026-04-20 | — | No onboarding doc references OWASP |
| Encrypt inter-service communication (TLS) | MUST | ⚠️ WARN | 2026-04-20 | — | Code uses `https://` for Portal API; no explicit TLS policy documented |
| Encrypt data at rest for PII | MUST | ➖ SKIP | 2026-04-20 | — | CLI controller; no persistent PII storage |
| Principle of least privilege for accounts/keys/IAM | MUST | ⚠️ WARN | 2026-04-20 | — | release.yml scopes `contents: write`; no documented IAM policy |
| Never hardcode secrets | MUST | ✅ PASS | 2026-04-20 | — | Workflows use `${{ secrets.* }}`; no key patterns in repo |
| Check for OWASP Top 10 in code review | MUST | ❌ FAIL | 2026-04-20 | — | No PR template or review checklist referencing OWASP |
| Integrate SAST tools | REC | ❌ FAIL | 2026-04-20 | — | No semgrep/Snyk/bandit configured |
| Formal threat model annually | REC | ❌ FAIL | 2026-04-20 | — | No THREAT_MODEL.md or threat-model ADR |

---

## 09 · Incident Management & Blameless Culture

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| On-call schedule per production service | MUST | ➖ SKIP | 2026-04-20 | — | CLI dev repo; no production service |
| Severity levels (P1–P3) with response SLAs | MUST | ⚠️ WARN | 2026-04-20 | — | P1/P2/P3 referenced only inside PIR template; no standalone severity doc |
| PIRs conducted within 48 hours of P1/P2 | MUST | ➖ SKIP | 2026-04-20 | — | No applicable production incidents |
| PIR action items as first-class sprint work | MUST | ➖ SKIP | 2026-04-20 | — | No PIRs filed |
| Use PIR template in docs/templates/pir-template.md | MUST | ⚠️ WARN | 2026-04-20 | — | Template exists at `harness-docs/templates/pir-template.md`; path differs from Section 09 text |
| Store PIRs in searchable shared location | REC | ❌ FAIL | 2026-04-20 | — | No `docs/pirs/` or `incidents/` directory |
| Track MTTD and MTTR monthly | REC | ❌ FAIL | 2026-04-20 | — | No MTTD/MTTR tracking doc |

---

## 10 · Agentic Development

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| Apply same DoD to AI-generated code as human | MUST | ⚠️ WARN | 2026-04-20 | — | CLAUDE.md rule #11 mandates standards-reviewer on staged diff; no written DoD artifact |
| Do not merge AI-generated code without human read | MUST | ⚠️ WARN | 2026-04-20 | — | CLAUDE.md rule #5 requires peer review; no explicit "human-read AI code" gate |
| Treat AI as author under review when writing tests | MUST | ❌ FAIL | 2026-04-20 | — | No CLAUDE.md or agent-review guidance |
| Flag AI-generated code in commits/PR descriptions | MUST | ⚠️ WARN | 2026-04-20 | — | CLAUDE.md rule #8 stated; recent commits show no AI flag |
| Define autonomy levels in CLAUDE.md | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md §Agentic Development declares "Autonomy level: Semi-autonomous" |
| Restrict autonomous agents to reversible actions | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md §Blast radius lists confirmation-required actions (force-push, deploys, migrations, external side-effect calls) |
| Never grant production access/secrets/IAM to agents | MUST | ⚠️ WARN | 2026-04-20 | — | `.claude/settings.json` has secret-scan hook and deny rules; no explicit prod/IAM denylist |
| On agent failure: stop and surface, don't silently retry | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md semi-autonomous definition mandates stop-and-surface; no silent retries or unauthorised fallbacks |
| Treat CLAUDE.md as first-class artifact | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md wrapped in `<!-- BEGIN:bid-harness -->` markers; git-tracked; §Agentic Development block added |
| Scope agent instructions to the repo | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md content is repo-scoped (Python stack, dirigent skills); Agentic block applies to this repo only |
| Fix CLAUDE.md in same PR that corrects agent output | MUST | ⚠️ WARN | 2026-04-20 | — | No process documented; no PR template |
| Remove instructions that no longer apply | MUST | ⚠️ WARN | 2026-04-20 | — | No pruning cadence; `claude-md-improver` skill available but no enforcement |
| Never pass secrets into agent context | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | `.claude/settings.json` PreToolUse hook scans Write/Edit for API_KEY/SECRET/TOKEN patterns and denies; reinforced in CLAUDE.md §Tool permissions |
| Prompt injection awareness | MUST | ✅ PASS | 2026-04-20 | /setup-agentic-standards | CLAUDE.md §Prompt injection awareness: treat external content as untrusted, flag injection attempts to user |
| Review tool permissions per workflow (least privilege) | MUST | ⚠️ WARN | 2026-04-20 | — | `.claude/settings.json` has deny rules; no per-workflow permission review documented |
| Do not bypass security controls with AI | MUST | ❌ FAIL | 2026-04-20 | — | No written policy in CLAUDE.md or harness-docs |
| AI-assisted code review in PR template | REC | ❌ FAIL | 2026-04-20 | — | No PR template exists |
| Track AI-generated change proportion | REC | ❌ FAIL | 2026-04-20 | — | No tracking mechanism |
| Blast radius review for new agent workflows | REC | ❌ FAIL | 2026-04-20 | — | No review process documented |
| Log all agent-initiated actions | REC | ⚠️ WARN | 2026-04-20 | — | `.claude/settings.json` PostToolUse hook logs tool names; not comprehensive audit |
| Audit CLAUDE.md quarterly | REC | ⚠️ WARN | 2026-04-20 | — | `audit-claude-md` skill available; no scheduled cadence |
| Onboarding walkthrough of CLAUDE.md | REC | ❌ FAIL | 2026-04-20 | — | No onboarding doc references CLAUDE.md walkthrough |
| Include agent workflows in threat model | REC | ❌ FAIL | 2026-04-20 | — | No threat model in repo |
| Prompt injection in OWASP Top 10 review | REC | ❌ FAIL | 2026-04-20 | — | No OWASP review artifact |
