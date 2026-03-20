# Codebase Structure

**Analysis Date:** 2026-03-20

## Directory Layout

```
outbid-dirigent/
├── src/
│   └── outbid_dirigent/              # Main Python package
│       ├── __init__.py               # Version info
│       ├── dirigent.py               # Entry point & orchestration
│       ├── analyzer.py               # Repo + spec analysis
│       ├── router.py                 # Routing logic
│       ├── executor.py               # Task execution & Claude Code invocation
│       ├── oracle.py                 # Architecture decisions via Claude API
│       ├── logger.py                 # Structured logging
│       ├── questioner.py             # Portal integration for questions
│       └── proteus_integration.py    # Deep domain extraction
├── .devcontainer/
│   └── devcontainer.json             # VS Code / Codespaces config
├── coder/                            # Coder workspace configuration
├── .dirigent/                        # Runtime state (generated)
├── .planning/                        # Planning files (generated)
├── pyproject.toml                    # Project metadata + dependencies
├── uv.lock                           # Locked dependency versions
├── README.md                         # Full documentation
├── OUTBID_CONTEXT.md                 # Project context
└── .gitignore                        # Git exclusions
```

## Directory Purposes

**src/outbid_dirigent/:**
- Purpose: Core Python package with all orchestration logic
- Contains: Python modules for analysis, routing, execution, logging, and integration
- Key files: `dirigent.py` (entry), `executor.py` (largest, ~44KB), `analyzer.py` (~20KB)

**.devcontainer/:**
- Purpose: Development environment configuration for VS Code / GitHub Codespaces
- Contains: Docker setup for consistent development environments
- Generated: Not committed to git, created on first start

**coder/:**
- Purpose: Coder workspace resource definitions and bootstrap scripts
- Contains: Terraform or HCL configurations for Coder workspaces
- Used by: Coder platform for workspace provisioning

**.dirigent/:**
- Purpose: Runtime state and logs (generated during execution)
- Contains: ANALYSIS.json, ROUTE.json, PLAN.json, STATE.json, DECISIONS.json, logs/
- Committed: No (added to .gitignore)

**.planning/:**
- Purpose: Planning artifacts from Dirigent runs
- Contains: SPEC.md, codebase analysis documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Committed: Yes (part of repo for future runs)

## Key File Locations

**Entry Points:**
- `pyproject.toml` (line 14): Defines CLI entry point: `dirigent = "outbid_dirigent.dirigent:main"`
- `src/outbid_dirigent/dirigent.py` (line 249): `main()` function orchestrates all phases

**Configuration:**
- `pyproject.toml`: Project metadata, Python version requirement (3.10+), dependencies
- `.devcontainer/devcontainer.json`: VS Code / Codespaces environment
- `coder/`: Workspace definitions

**Core Logic:**
- `src/outbid_dirigent/analyzer.py`: Repository and spec analysis (language detection, framework detection, route signals)
- `src/outbid_dirigent/router.py`: Route definition (Greenfield/Legacy/Hybrid steps and logic)
- `src/outbid_dirigent/executor.py`: Claude Code invocation, task execution, commit management
- `src/outbid_dirigent/oracle.py`: Architecture decision making via Claude API

**Testing:**
- None currently committed (run tests via `uv run pytest tests/` when tests exist)

**Logging:**
- `src/outbid_dirigent/logger.py`: Structured logging with icons, timestamps, and JSON support
- Output: `.dirigent/logs/run-{timestamp}.log` and `.dirigent/logs/run-{timestamp}.jsonl`

**Supporting Integration:**
- `src/outbid_dirigent/questioner.py`: Portal communication for interactive mode (plan_first, interactive)
- `src/outbid_dirigent/proteus_integration.py`: Proteus domain extraction orchestration

## Naming Conventions

**Files:**
- Pattern: `snake_case.py` for all modules
- Examples: `dirigent.py`, `analyzer.py`, `proteus_integration.py`

**Directories:**
- Pattern: `lowercase` for package directories, `snake_case` for feature dirs
- Examples: `outbid_dirigent/`, `.dirigent/`, `.planning/`

**Classes:**
- Pattern: `PascalCase`
- Examples: `Analyzer`, `Router`, `Executor`, `Oracle`, `DirigentLogger`

**Functions:**
- Pattern: `snake_case`
- Examples: `analyze()`, `run_analysis()`, `determine_route()`, `mark_step_complete()`

**Enums:**
- Pattern: `UPPERCASE` values
- Examples: `RouteType.GREENFIELD`, `StepType.PLANNING`, `LogLevel.DEBUG`

**Constants:**
- Pattern: `UPPERCASE`
- Examples: `LEGACY_KEYWORDS`, `GREENFIELD_STEPS`, `MAX_TASK_RETRIES`

## Where to Add New Code

**New Feature (New Routing Path):**
- Primary code: `src/outbid_dirigent/router.py` (add new RouteType enum and step definitions)
- Integration: Update `Analyzer._determine_route()` in `analyzer.py` to include new signal detection
- Executor updates: `src/outbid_dirigent/executor.py` to handle new step types

**New Integration (External API/Service):**
- Create new module: `src/outbid_dirigent/{integration_name}.py`
- Example pattern: See `proteus_integration.py` (how to wrap external tool)
- Entry point: Add factory function `create_{integration_name}()` and integrate in `executor.py`

**New Execution Mode (e.g., parallel tasks):**
- Core logic: `src/outbid_dirigent/executor.py` (modify task execution loop)
- State tracking: Update `STATE.json` schema in `router.py` and `executor.py`
- Resumability: Ensure `--resume` understands new state fields

**New Logger Feature:**
- Core: `src/outbid_dirigent/logger.py` (add method to `DirigentLogger` class)
- Output: Both stdout and log files via `_write_to_file()` and `_write_json()`
- Icons: Add to `DirigentLogger.ICONS` dict if needed

**New CLI Flag:**
- Location: `src/outbid_dirigent/dirigent.py::main()` (argument parser section, ~line 250)
- Processing: Add handling in `main()` to use the flag
- Propagation: Pass flag value to relevant classes (Executor, Oracle, etc.)

**New Portal Integration:**
- Primary: `src/outbid_dirigent/questioner.py` (extends Questioner class)
- Usage: Questioner is accessed via `get_questioner()` from `dirigent.py`
- Example: `questioner.ask()` for portal-based questions

## Special Directories

**`.dirigent/` (Runtime):**
- Purpose: Stores execution state and logs during Dirigent runs
- Generated: Yes (created by Executor and Logger)
- Committed: No (in .gitignore)
- Structure:
  ```
  .dirigent/
  ├── ANALYSIS.json       # Repo analysis result
  ├── ROUTE.json          # Selected route + reasoning
  ├── PLAN.json           # Execution plan (phases + tasks)
  ├── STATE.json          # Current progress (for --resume)
  ├── DECISIONS.json      # Oracle decisions cache
  ├── BUSINESS_RULES.md   # Extracted domain rules (Legacy only)
  ├── CONTEXT.md          # Relevant files (Hybrid only)
  ├── summaries/          # Per-task execution summaries
  └── logs/               # Timestamped log files
  ```

**`.planning/` (Persistent):**
- Purpose: Planning artifacts and codebase analysis documents
- Generated: Yes (created by phases and mapping agents)
- Committed: Yes
- Contains: SPEC.md, ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md, INTEGRATIONS.md, STACK.md

**`.proteus/` (Proteus-specific):**
- Purpose: Domain extraction artifacts (when --use-proteus flag is used)
- Generated: Yes (created by Proteus integration)
- Committed: No (in .gitignore, large files)
- Structure:
  ```
  .proteus/
  ├── arch.md             # Architecture profile
  ├── fields.json         # Data fields (1000+ entries possible)
  ├── rules.json          # Business rules
  ├── events.json         # Domain events
  ├── dependencies.json   # CRUD dependency map
  └── pipeline.json       # Extraction progress
  ```

## Imports and Module Dependencies

**Top-level imports in `dirigent.py`:**
- Standard: `argparse`, `sys`, `os`, `pathlib`, `datetime`
- Internal: `logger`, `analyzer`, `router`, `executor`, `questioner`
- Pattern: All core modules imported at top level

**Circular imports prevention:**
- `oracle.py` lazily imports `get_questioner()` from `dirigent.py` via `_get_questioner()` function
- Pattern: Functions import only what they need, avoiding circular dependencies at module load time

**Shared state:**
- Global questioner instance in `dirigent.py` (accessed via `get_questioner()`)
- Global execution mode in `dirigent.py` (accessed via `get_execution_mode()`)
- Pattern: Module-level singletons, set once in `main()` before use

## Generated Files Schema

**PLAN.json (Executor output):**
- Contains: List of phases, each with tasks
- Schema: `{phases: [{id, name, tasks: [{task_id, description, estimated_duration}]}]}`
- Used by: Executor to drive execution loop, returned as metadata

**STATE.json (Router output):**
- Contains: Completed steps, started_at timestamp, updated_at timestamp
- Schema: `{completed_steps: [str], started_at: ISO8601, updated_at: ISO8601}`
- Used by: Resumption logic to skip already-completed work

**DECISIONS.json (Oracle output):**
- Contains: List of cached decisions with cache keys
- Schema: `{decisions: [{cache_key, question, options, decision, reasoning}], created_at, updated_at}`
- Used by: Oracle to avoid duplicate API calls for same question

---

*Structure analysis: 2026-03-20*
