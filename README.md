<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=white" alt="Python 3.8+">
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
                         |   Route    |  Greenfield / Legacy / Hybrid
                         +-----+-----+
                               |
                    +----------+----------+
                    |          |          |
              +-----v--+ +----v---+ +---v----+
              |Greenfield| |Legacy  | |Hybrid  |
              +-----+--+ +----+---+ +---+----+
                    |          |          |
                    |    +-----v-----+   |
                    |    | Proteus   |   |
                    |    | Extraction|   |
                    |    +-----+-----+   |
                    |          |          |
                    +----------+----------+
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
# Full autonomous run
dirigent --spec .planning/SPEC.md --repo /path/to/repo

# With deep domain extraction (recommended for legacy migrations)
dirigent --spec .planning/SPEC.md --repo /path/to/repo --use-proteus

# Resume after interruption
dirigent --spec .planning/SPEC.md --repo /path/to/repo --resume

# Dry run (no changes)
dirigent --spec .planning/SPEC.md --repo /path/to/repo --dry-run
```

## Installation

### Local

```bash
./install.sh
```

### Global

```bash
git clone https://github.com/BIDEquity/outbid-dirigent.git ~/.local/share/outbid-dirigent

pip3 install --user anthropic

mkdir -p ~/.local/bin
ln -s ~/.local/share/outbid-dirigent/dirigent.py ~/.local/bin/dirigent

# Add to .bashrc or .zshrc
export PATH="$HOME/.local/bin:$PATH"
```

### Coder Workspaces

**Option A: Standalone script in template (recommended)**

```hcl
resource "coder_script" "dirigent" {
  agent_id     = coder_agent.main.id
  script       = file("${path.module}/standalone-install.sh")
  display_name = "Install Dirigent"
  run_on_start = true
}
```

**Option B: Inline in template**

```hcl
resource "coder_script" "dirigent" {
  agent_id     = coder_agent.main.id
  script       = <<-EOF
    REPO="https://github.com/BIDEquity/outbid-dirigent.git"
    INSTALL_DIR="$HOME/.local/share/outbid-dirigent"
    BIN_DIR="$HOME/.local/bin"

    if [ ! -x "$BIN_DIR/dirigent" ]; then
      mkdir -p "$INSTALL_DIR" "$BIN_DIR"
      git clone --depth 1 "$REPO" "$INSTALL_DIR"
      pip3 install --user -q anthropic
      ln -sf "$INSTALL_DIR/dirigent.py" "$BIN_DIR/dirigent"
      echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
  EOF
  display_name = "Install Dirigent"
  run_on_start = true
}
```

**Option C: Devcontainer**

The repo ships with `.devcontainer/devcontainer.json` for VS Code / GitHub Codespaces.

### Prerequisites

| Requirement | Purpose |
|---|---|
| Python 3.8+ | Runtime |
| [Claude Code CLI](https://claude.ai/claude-code) | AI execution engine |
| `ANTHROPIC_API_KEY` env var | Authentication |
| GitHub CLI (`gh`) | *Optional* — auto-creates PRs |

---

## Routing Engine

The Dirigent automatically selects one of three execution paths based on repo analysis and spec content.

### Route A — Greenfield

> New features on existing or new projects.

**Triggers:** Spec contains "add", "build", "create", "implement", "new feature" — actively developed project (last commit < 90 days) — modern stack (TypeScript, JavaScript, Python, Go, Rust)

**Pipeline:**
```
Plan  -->  Execute  -->  Ship
```

### Route B — Legacy

> Refactors, migrations, rewrites.

**Triggers:** Spec contains "refactor", "migrate", "rewrite", "port", "legacy" — inactive project (last commit > 1 year) — language migration detected (e.g. Java to PHP) — large project (> 500 commits)

**Pipeline:**
```
Business Rule Extraction  -->  Plan (with guardrails)  -->  Execute  -->  Ship
```

### Route C — Hybrid

> New features on existing projects that need to be understood first.

**Triggers:** Mix of greenfield and legacy signals — new feature on an existing, complex project

**Pipeline:**
```
Quick Scan  -->  Plan (with repo context)  -->  Execute  -->  Ship
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
dirigent.py                  # Entry point + orchestration
    │
    ├── analyzer.py          # Repo + spec analysis, path selection
    ├── router.py            # Routing logic (Greenfield / Legacy / Hybrid)
    ├── executor.py          # Claude Code invocations
    ├── proteus_integration.py  # Deep domain extraction (5-phase pipeline)
    ├── oracle.py            # Architecture decisions (direct Claude API)
    └── logger.py            # Structured logging to .dirigent/logs/
```

### Generated Files

```
{repo}/.dirigent/
├── ANALYSIS.json        # Repo analysis result
├── ROUTE.json           # Chosen path + reasoning
├── PLAN.json            # Execution plan (phases + tasks)
├── STATE.json           # Current progress (resumable)
├── DECISIONS.json       # Oracle decisions (cached)
├── BUSINESS_RULES.md    # Extracted business rules (Legacy route)
├── CONTEXT.md           # Relevant files (Hybrid route)
├── summaries/           # Per-task summaries
│   └── 01-01-SUMMARY.md
└── logs/
    └── run-{timestamp}.log
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
| `--spec` | Path to the SPEC.md file (required) |
| `--repo` | Path to the target repository (required) |
| `--phase` | Run specific phase: `analyze`, `execute`, `ship`, or `all` (default: `all`) |
| `--use-proteus` | Enable Proteus deep domain extraction |
| `--resume` | Resume interrupted execution |
| `--dry-run` | Analyze only, no changes |
| `--force` | Re-run analysis (ignore cache) |
| `--quiet` | Minimal output |

---

## Design Principles

- **Headless by design** — No stdin reads, no `input()` calls, no waiting
- **Fresh context per task** — Each task spawns a new Claude Code process
- **Oracle over human** — Architecture questions go to the Oracle, never to the user
- **Atomic commits** — One commit per task, never everything at once
- **Fail fast** — 3 retries per task, then stop and log to STATE.json
- **Resumable** — STATE.json tracks progress; pick up where you left off

---

## Example Output

```
[2026-03-10 11:30:00] 🎼 Outbid Dirigent gestartet
[2026-03-10 11:30:01] 🔍 Analysiere Repo: medicheck-portal
[2026-03-10 11:30:02] 📊 Erkannt: Java/Spring Boot, 1205 Commits, 4 Jahre alt
[2026-03-10 11:30:02] 🗺️  Route: LEGACY (confidence: high)
[2026-03-10 11:30:02] 📋 Grund: Java Migration-Spec, inaktives Repo
[2026-03-10 11:30:03] 📊 Nutze Proteus für Domain-Extraktion...
[2026-03-10 11:30:03] 📊 Proteus Phase 1: Survey...
[2026-03-10 11:35:30] 📊 Proteus Survey abgeschlossen
[2026-03-10 11:35:30] 📊 Proteus Phase 2: Extract Fields...
[2026-03-10 11:46:45] 📊 Proteus Fields Extraktion abgeschlossen
[2026-03-10 11:46:45] 📊 Proteus Phase 3: Extract Rules...
[2026-03-10 11:52:00] 📊 Proteus Rules Extraktion abgeschlossen
[2026-03-10 11:52:00] 📊 Proteus Phase 4: Extract Events...
[2026-03-10 11:54:15] 📊 Proteus Events Extraktion abgeschlossen
[2026-03-10 11:54:15] 📊 Proteus Phase 5: Map Dependencies...
[2026-03-10 11:59:00] 📊 Proteus Dependencies Mapping abgeschlossen
[2026-03-10 11:59:00] 📊 Proteus: 1214 Fields, 62 Rules, 33 Events, 129 Dependencies
[2026-03-10 11:59:00] 📝 Erstelle Ausführungsplan...
[2026-03-10 12:05:00] ✅ Plan: 4 Phasen, 12 Tasks
[2026-03-10 12:05:01] ⚡ Starte Ausführung: Phase 1 – Setup
[2026-03-10 12:05:01] 🔨 Task 01-01: PHP Projektstruktur anlegen
[2026-03-10 12:12:00] ✅ Task 01-01 abgeschlossen (Commit: abc1234)
...
[2026-03-10 16:30:00] 🚢 Shipping: Branch feature/dirigent-20260310
[2026-03-10 16:30:15] 🎉 PR erstellt: https://github.com/org/repo/pull/42
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
python3 -m pytest tests/

# Linting
python3 -m flake8 *.py
```

## License

MIT
