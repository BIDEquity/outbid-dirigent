<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/claude-code-blueviolet?logo=anthropic&logoColor=white" alt="Claude Code">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/status-production-brightgreen" alt="Production">
</p>

<h1 align="center">Outbid Dirigent</h1>

<p align="center">
  <strong>A headless Python control plane that reads a spec, analyzes the target repo, picks the optimal execution path, and autonomously works through every task.</strong>
</p>

<p align="center">
  No human in the loop. No interactive terminal. No waiting for input.
</p>

---

## How It Works

```
                         +-----------+
                         |  SPEC.md  |
                         +-----+-----+
                               |
                         +-----v-----+
                         |  Analyze   |  Repo structure, language, history
                         +-----+-----+
                               |
                         +-----v-----+
                         |   Route    |  5 execution paths
                         +-----+-----+
                               |
              +-------+--------+--------+--------+-------+
              |       |        |        |        |
           +--v--+ +--v--+ +--v--+ +---v--+ +--v---+
           |Green| |Legcy| |Hybrd| |Test  | |Track |
           |field| |     | |     | |abilty| |ing   |
           +--+--+ +--+--+ +--+--+ +--+---+ +--+---+
              |       |        |        |        |
              |    +--v---+    |        |        |
              |    |Proteus|   |        |        |
              |    +--+---+    |        |        |
              |       |        |        |        |
              +---+---+--------+--------+--------+
                               |
                         +-----v-----+
                         |   Plan     |  Phased execution plan
                         +-----+-----+
                               |
                         +-----v-----+
                         |  Execute   |  One Claude Code process per task
                         +-----+-----+
                               |
                         +-----v-----+
                         |   Ship     |  Branch, push, PR
                         +-----------+
```

## Quick Start

```bash
# Full autonomous run with existing spec
dirigent --spec .planning/SPEC.md --repo /path/to/repo

# Inline description — generates SPEC.md, asks 2-3 questions
dirigent --repo . "Add a dark mode toggle to the settings page"

# YOLO mode — no questions, best-effort spec from description + context
dirigent --repo . --yolo "Add a dark mode toggle"

# Auto-detect spec (searches .planning/SPEC.md, SPEC.md, .dirigent/SPEC.md)
dirigent --repo /path/to/repo

# With deep domain extraction (recommended for legacy migrations)
dirigent --spec .planning/SPEC.md --repo /path/to/repo --use-proteus

# Resume after interruption
dirigent --spec .planning/SPEC.md --repo /path/to/repo --resume
```

## Installation

### Via uvx (recommended)

No installation needed. Run directly:

```bash
uvx --from git+https://github.com/BIDEquity/outbid-dirigent.git dirigent \
  --spec .planning/SPEC.md --repo /path/to/repo
```

### Via uv

```bash
uv tool install git+https://github.com/BIDEquity/outbid-dirigent.git
```

### Via pip

```bash
pip install git+https://github.com/BIDEquity/outbid-dirigent.git
```

### Development

```bash
git clone https://github.com/BIDEquity/outbid-dirigent.git
cd outbid-dirigent
uv sync
```

### Coder Workspaces

```hcl
resource "coder_script" "dirigent" {
  agent_id     = coder_agent.main.id
  script       = <<-EOF
    uv tool install git+https://github.com/BIDEquity/outbid-dirigent.git
  EOF
  display_name = "Install Dirigent"
  run_on_start = true
}
```

The repo ships with `.devcontainer/devcontainer.json` for VS Code / GitHub Codespaces.

### Prerequisites

| Requirement | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| [Claude Code CLI](https://claude.ai/claude-code) | AI execution engine |
| `ANTHROPIC_API_KEY` env var | Authentication |
| GitHub CLI (`gh`) | *Optional* — auto-creates PRs |

---

## Routing Engine

The Dirigent automatically selects one of five execution paths based on repo analysis and spec content.

### Route A — Greenfield

> New features on existing or new projects.

**Triggers:** Spec contains "add", "build", "create", "implement", "new feature" — actively developed project (last commit < 90 days) — modern stack (TypeScript, JavaScript, Python, Go, Rust)

**Pipeline:**
```
Init (optional) --> Plan --> Execute --> Entropy Min (optional) --> Test (optional) --> Ship
```

### Route B — Legacy

> Refactors, migrations, rewrites.

**Triggers:** Spec contains "refactor", "migrate", "rewrite", "port", "legacy" — inactive project (last commit > 1 year) — language migration detected (e.g. Java to PHP) — large project (> 500 commits)

**Pipeline:**
```
Init (optional) --> Business Rule Extraction --> Plan (with guardrails) --> Execute --> Entropy Min (optional) --> Test (optional) --> Ship
```

### Route C — Hybrid

> New features on existing projects that need to be understood first.

**Triggers:** Mix of greenfield and legacy signals — new feature on an existing, complex project

**Pipeline:**
```
Init (optional) --> Quick Scan --> Plan (with repo context) --> Execute --> Entropy Min (optional) --> Test (optional) --> Ship
```

### Route D — Testability

> Improve test coverage and test infrastructure.

**Triggers:** Spec contains "test", "coverage", "testability", "e2e" — low testability score detected

**Pipeline:**
```
Init --> Testability Analysis --> Plan --> Execute --> Entropy Min (optional) --> Test (optional) --> Ship
```

### Route E — Tracking

> Add analytics and event tracking (PostHog).

**Triggers:** Spec contains "analytics", "tracking", "events", "PostHog" — no existing analytics detected

**Pipeline:**
```
Init (optional) --> Quick Scan --> PostHog Setup --> Plan --> Execute --> Entropy Min (optional) --> Test (optional) --> Ship
```

---

## Proteus Integration

For legacy migrations, the `--use-proteus` flag enables **deep domain extraction** powered by [Proteus](https://github.com/BIDEquity/proteus-alpha) — a multi-phase domain knowledge extractor that goes far beyond simple business rule scanning.

### What Proteus Does

Instead of a single Claude Code pass to extract business rules, Proteus runs **5 dedicated extraction phases**, each with its own 30-minute timeout:

| Phase | Output | Description |
|---|---|---|
| **1. Survey** | `arch.md` | Architecture profile — entry points, data models, service layers, API clients, tech stack |
| **2. Extract Fields** | `fields.json` | Every data field across entities, DTOs, API objects, and config |
| **3. Extract Rules** | `rules.json` | Business rules — validations, calculations, constraints, workflows, permissions |
| **4. Extract Events** | `events.json` | Domain events — triggers, consequences, state changes, side effects, notifications |
| **5. Map Dependencies** | `dependencies.json` | CRUD dependency map between rules and fields |

### Why It Matters

On a real-world legacy codebase, Proteus typically extracts:

```
1214 Fields  ·  62 Rules  ·  33 Events  ·  129 Dependencies
```

This rich domain model is then fed into the planning phase as guardrails, ensuring that **no business logic is lost** during migration.

### Proteus Output Structure

```
{repo}/.proteus/
├── arch.md              # Architecture profile
├── fields.json          # All extracted data fields
├── rules.json           # Business rules with source locations
├── events.json          # Domain events and their flows
├── dependencies.json    # CRUD dependency map
└── pipeline.json        # Extraction progress tracker
```

### Usage

```bash
# Legacy migration with deep extraction
dirigent --spec .planning/SPEC.md --repo . --use-proteus

# Resume if interrupted (skips completed phases)
dirigent --spec .planning/SPEC.md --repo . --use-proteus --resume
```

---

## Architecture

```
src/outbid_dirigent/
    ├─ dirigent.py              # Entry point + orchestration
    ├─ analyzer.py              # Repo + spec analysis
    ├─ router.py                # Route selection (5 routes)
    ├─ executor.py              # Master orchestrator
    ├─ task_runner.py           # Individual task execution (subprocess per task)
    ├─ planner.py               # Plan creation via Claude Code
    ├─ contract.py              # Phase contracts + review/fix loop
    ├─ contract_schema.py       # Contract/Review/Verdict data models
    ├─ plan_schema.py           # Plan/Phase/Task data models
    ├─ shipper.py               # Branch, push, PR creation
    ├─ oracle.py                # Architecture decisions (Claude API)
    ├─ init_phase.py            # Environment bootstrap
    ├─ progress.py              # Progress reporting
    ├─ logger.py                # Structured logging to .dirigent/logs/
    ├─ portal_reporter.py       # Outbid Portal event reporting
    ├─ questioner.py            # Interactive question handling
    ├─ test_harness_schema.py   # Test harness data model
    ├─ test_manifest.py         # Test manifest handling
    ├─ proteus_integration.py   # Proteus domain extraction
    └─ demo_runner.py           # Demo mode with simulated events
```

### Generated Files

```
{repo}/.dirigent/
├── ANALYSIS.json          # Repo analysis result
├── ROUTE.json             # Selected route + steps
├── PLAN.json              # Execution plan (phases → tasks)
├── STATE.json             # Progress tracking (resumable)
├── DECISIONS.json         # Oracle decision cache
├── SPEC.md                # Copy of input spec
├── test-harness.json      # Endpoint/auth/seed config
├── BUSINESS_RULES.md      # Extracted rules (Legacy route)
├── CONTEXT.md             # Relevant files (Hybrid route)
├── contracts/             # Phase acceptance criteria
│   └── phase-{id}.json
├── reviews/               # Phase review verdicts
│   └── phase-{id}.json
├── summaries/             # Per-task execution summaries
│   └── {task_id}-SUMMARY.md
└── logs/                  # Structured execution logs
    ├── run-*.log
    └── run-*.jsonl
```

---

## Deviation Rules

During execution, Claude Code follows strict deviation rules:

| # | Trigger | Action |
|---|---|---|
| 1 | Bug discovered | Auto-fix, log as `DEVIATION: Bug-Fix` |
| 2 | Critical missing piece | Add it, log as `DEVIATION` |
| 3 | Blocker encountered | Resolve it, log as `DEVIATION` |
| 4 | Architecture question | **STOP** — ask the Oracle |

## Oracle

The Oracle answers architectural questions autonomously via the Claude API:

- **Reads:** SPEC.md, PLAN.json, DECISIONS.json, BUSINESS_RULES.md
- **Caches:** All decisions in DECISIONS.json (no duplicate API calls)
- **Model:** Claude Sonnet for fast, cost-effective answers

---

## Timeouts

| Step | Timeout | Notes |
|---|---|---|
| Codebase analysis | 15 min | Full repo scan |
| Quick scan | 5 min | Targeted file scan (Hybrid route) |
| Plan creation | 30 min | Scales with domain complexity |
| Task execution | 30 min | Per task, up to 3 retries |
| Proteus phases | 30 min | Per phase (5 phases total) |

## Resumability

Dirigent is fully resumable. Every completed step is tracked in `STATE.json`. If execution is interrupted — timeout, crash, network failure — just run with `--resume`:

```bash
dirigent --spec .planning/SPEC.md --repo . --resume
```

It picks up exactly where it left off. Completed analysis, extraction, and tasks are skipped automatically.

---

## CLI Reference

```
dirigent --spec <path> --repo <path> [options]
```

| Flag | Description |
|---|---|
| `description` | Inline spec description (positional, alternative to `--spec`) |
| `--spec` | Path to SPEC.md (auto-detected if omitted) |
| `--repo` | Path to the target repository (required) |
| `--yolo` | Skip questions — generate spec from description + repo context |
| `--phase` | Run specific phase: `analyze`, `execute`, `ship`, or `all` (default: `all`) |
| `--use-proteus` | Enable Proteus deep domain extraction |
| `--resume` | Resume interrupted execution |
| `--dry-run` | Analyze only, no changes |
| `--force` | Re-run analysis (ignore cache) |
| `--quiet` | Minimal output |
| `--verbose` | Verbose output (default: true) |
| `--output` | Output format: `json` for JSON Lines to stdout |
| `--execution-mode` | `autonomous` (default), `plan_first`, or `interactive` |
| `--plan-only` | Create plan then stop (no execution) |
| `--question-timeout` | Timeout in minutes for interactive questions (default: 30) |
| `--model` | Claude model for task execution (e.g. haiku, sonnet, opus) |
| `--effort` | Thinking effort level: `low`, `medium`, `high`, `max` |
| `--portal-url` | Outbid Portal URL (env: `PORTAL_URL`) |
| `--execution-id` | Execution ID for Portal integration (env: `EXECUTION_ID`) |
| `--reporter-token` | Reporter token for Portal integration (env: `REPORTER_TOKEN`) |
| `--demo` | Demo mode: send simulated events without real execution |
| `--demo-speed` | Demo mode speed multiplier (default: 1.0) |
| `--interactive` | **DEPRECATED** — use `--execution-mode interactive` |

---

## Design Principles

- **Headless by design** — No stdin reads, no `input()` calls, no waiting
- **Fresh context per task** — Each task spawns a new Claude Code process
- **Oracle over human** — Architecture questions go to the Oracle, never to the user
- **Atomic commits** — One commit per task, never everything at once
- **Fail fast** — 3 retries per task, then stop and log to STATE.json
- **Resumable** — STATE.json tracks progress; pick up where you left off
- **Entropy minimization** — After execution, a fresh agent aligns docs, removes dead code, and resolves contradictions

---

## Example Output

```
[2026-03-10 11:30:00] Outbid Dirigent gestartet
[2026-03-10 11:30:01] Analysiere Repo: medicheck-portal
[2026-03-10 11:30:02] Erkannt: Java/Spring Boot, 1205 Commits, 4 Jahre alt
[2026-03-10 11:30:02] Route: LEGACY (confidence: high)
[2026-03-10 11:30:02] Grund: Java Migration-Spec, inaktives Repo
[2026-03-10 11:30:03] Nutze Proteus für Domain-Extraktion...
[2026-03-10 11:30:03] Proteus Phase 1: Survey...
[2026-03-10 11:35:30] Proteus Survey abgeschlossen
[2026-03-10 11:35:30] Proteus Phase 2: Extract Fields...
[2026-03-10 11:46:45] Proteus Fields Extraktion abgeschlossen
[2026-03-10 11:46:45] Proteus Phase 3: Extract Rules...
[2026-03-10 11:52:00] Proteus Rules Extraktion abgeschlossen
[2026-03-10 11:52:00] Proteus Phase 4: Extract Events...
[2026-03-10 11:54:15] Proteus Events Extraktion abgeschlossen
[2026-03-10 11:54:15] Proteus Phase 5: Map Dependencies...
[2026-03-10 11:59:00] Proteus Dependencies Mapping abgeschlossen
[2026-03-10 11:59:00] Proteus: 1214 Fields, 62 Rules, 33 Events, 129 Dependencies
[2026-03-10 11:59:00] Erstelle Ausführungsplan...
[2026-03-10 12:05:00] Plan: 4 Phasen, 12 Tasks
[2026-03-10 12:05:01] Starte Ausführung: Phase 1 – Setup
[2026-03-10 12:05:01] Task 01-01: PHP Projektstruktur anlegen
[2026-03-10 12:12:00] Task 01-01 abgeschlossen (Commit: abc1234)
...
[2026-03-10 16:30:00] Shipping: Branch feature/dirigent-20260310
[2026-03-10 16:30:15] PR erstellt: https://github.com/org/repo/pull/42
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Task fails | Up to 3 retries, then stop |
| Oracle error | Log error, pick safer option |
| Interruption | Resume with `--resume` |
| Claude CLI missing | Error message with install instructions |
| Timeout | Logged with duration, resumable |

## Development

```bash
# Run tests
uv run pytest tests/

# Linting
uv run ruff check
```

## License

MIT
