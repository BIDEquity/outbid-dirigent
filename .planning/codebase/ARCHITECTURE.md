# Architecture

**Analysis Date:** 2026-03-20

## Pattern Overview

**Overall:** Autonomous orchestrator with routing-driven execution paths

**Key Characteristics:**
- Multi-path routing system (Greenfield, Legacy, Hybrid) determined by analysis
- Headless by design — no interactive input, no human in the loop
- Fresh context per task — each task spawns a new Claude Code process
- Oracle-driven architecture decisions via Claude API (not Claude Code)
- Fully resumable via STATE.json tracking

## Layers

**Orchestration Layer:**
- Purpose: Entry point and execution flow control
- Location: `src/outbid_dirigent/dirigent.py`
- Contains: Main orchestrator, phase execution, error handling
- Depends on: Analyzer, Router, Executor, Logger, Questioner
- Used by: CLI callers

**Analysis Layer:**
- Purpose: Understand repo structure and spec content to determine optimal route
- Location: `src/outbid_dirigent/analyzer.py`
- Contains: Repository analysis, spec parsing, route signal detection, language/framework recognition
- Depends on: Git, filesystem introspection, logger
- Used by: Orchestrator during initial analysis phase

**Routing Layer:**
- Purpose: Determine and track which execution path to follow
- Location: `src/outbid_dirigent/router.py`
- Contains: Route types (Greenfield/Legacy/Hybrid), step definitions, state tracking
- Depends on: Analyzer results
- Used by: Orchestrator to sequence steps

**Execution Layer:**
- Purpose: Invoke Claude Code processes and manage task workflow
- Location: `src/outbid_dirigent/executor.py`
- Contains: Task invocation, phase execution, commit management, retry logic, summary generation
- Depends on: Oracle, Proteus integration, logger, router
- Used by: Orchestrator during execution phase

**Decision Layer:**
- Purpose: Answer architectural questions autonomously via Claude API
- Location: `src/outbid_dirigent/oracle.py`
- Contains: Architecture decision making, decision caching, Claude API calls
- Depends on: Anthropic API, logger
- Used by: Executor (when Claude Code encounters architecture questions)

**Support Layers:**
- **Logger** (`src/outbid_dirigent/logger.py`): Structured logging to stdout and `.dirigent/logs/`
- **Questioner** (`src/outbid_dirigent/questioner.py`): Portal integration for user questions (plan_first, interactive modes)
- **Proteus Integration** (`src/outbid_dirigent/proteus_integration.py`): Deep domain extraction for Legacy route

## Data Flow

**Primary Flow: Full Autonomous Run**

1. **Input:** SPEC.md (feature/migration description) + repo path
2. **Analyze Phase** (Analyzer)
   - Scan repository structure, detect language, framework, commit history
   - Parse SPEC.md, extract keywords (legacy vs greenfield)
   - Generate signals for route determination
3. **Route Phase** (Router)
   - Compare signals: legacy_signals vs greenfield_signals
   - Select and save route (Greenfield/Legacy/Hybrid)
4. **Route-Specific Setup:**
   - **Legacy route:** Run Proteus (if enabled) → extract business rules → save BUSINESS_RULES.md
   - **Hybrid route:** Quick Scan of relevant files → save CONTEXT.md
   - **Greenfield route:** Skip domain extraction
5. **Planning Phase** (Executor → Claude Code)
   - Read SPEC.md + route-specific context
   - Create phased execution plan → save PLAN.json
6. **Execution Phase** (Executor)
   - For each task in PLAN.json:
     - Spawn new Claude Code process with fresh context (prevents pollution)
     - Pass task description + PLAN.json + relevant files
     - Monitor for deviations (bugs, blockers, architecture questions)
     - On architecture question: Invoke Oracle (Claude API)
     - Commit atomically per task
     - Save task result to STATE.json
     - Retry up to 3 times on failure
7. **Shipping Phase** (Executor)
   - Create feature branch (slugified from spec title)
   - Push branch to remote
   - Create PR via GitHub CLI
   - Save branch name and PR URL
8. **Output:** PLAN.json, task summaries, PR URL, STATE.json

**State Management:**
- **ANALYSIS.json:** Repo structure, framework, language, commit history
- **ROUTE.json:** Chosen path (greenfield/legacy/hybrid), reasoning, estimated scope
- **PLAN.json:** Phased execution plan with tasks
- **STATE.json:** Completed steps, current progress (enables --resume)
- **DECISIONS.json:** Cached Oracle decisions (prevent duplicate API calls)
- **BUSINESS_RULES.md:** Extracted domain knowledge (Legacy route only)
- **CONTEXT.md:** Relevant files for the feature (Hybrid route only)

## Key Abstractions

**Route:**
- Purpose: Encapsulates an execution path with its sequence of steps
- Examples: `Route(GREENFIELD, steps=[Planning, Execution, Ship])`
- Pattern: Dataclass with type, reason, step sequence

**RouteStep:**
- Purpose: Individual step in a route (Business Rule Extraction, Quick Scan, Planning, Execution, Shipping)
- Examples: `RouteStep(PLANNING, name="Planung", description="...")`
- Pattern: Enum-driven with metadata

**Executor.Task:**
- Purpose: Atomic unit of work (maps to a Claude Code invocation)
- Examples: "Add authentication endpoint", "Create migration script"
- Pattern: Defined in PLAN.json, tracked in STATE.json

**Oracle.Decision:**
- Purpose: Cached architectural decision
- Examples: "Should we use React or Vue?", "How to handle database migration?"
- Pattern: Cache-keyed by question + options, stored in DECISIONS.json

**Deviation:**
- Purpose: Track unplanned work performed during task execution
- Examples: `DEVIATION: Bug-Fix (regex error in validation)`, `DEVIATION: Missing dependency`
- Pattern: Logged with source file and description

## Entry Points

**CLI Entry:**
- Location: `src/outbid_dirigent/dirigent.py::main()`
- Triggers: Command-line invocation `dirigent --spec SPEC.md --repo /path/to/repo`
- Responsibilities: Parse args, validate paths, initialize logger, coordinate phases

**Full Orchestration:**
- Location: `src/outbid_dirigent/dirigent.py::main()`
- Calls: `run_analysis()` → `run_routing()` → `run_execution()`
- Sequences: Analysis → Route determination → Phase execution

**Resume Entry:**
- Location: `src/outbid_dirigent/dirigent.py::resume_execution()`
- Triggers: `--resume` flag
- Responsibilities: Load existing route from ROUTE.json, load state from STATE.json, skip completed steps

## Error Handling

**Strategy:** Fail-fast with resumable state tracking

**Patterns:**

**Task Failure:**
- Attempts: Up to 3 retries per task
- Tracking: Failed task logged to STATE.json
- Recovery: `--resume` skips failed task, developer must fix and re-run
- Location: `executor.py::execute_plan()`

**Oracle Failure:**
- Fallback: If Oracle errors, pick safer architectural option
- Logging: Error logged, execution continues
- Cache: Decision not cached (will retry on next Oracle call)
- Location: `oracle.py::ask_oracle()`

**Interruption (Timeout/Crash):**
- State: Partial results saved to STATE.json with completed_steps list
- Recovery: `--resume` loads STATE.json, skips completed steps
- Location: `router.py::mark_step_complete()`

**Missing CLI Tools:**
- Example: Claude Code CLI not installed
- Handling: Executor detects via subprocess error, logs helpful error message
- Continuation: Stops execution (non-resumable without tool)
- Location: `executor.py::_invoke_claude_code()`

## Cross-Cutting Concerns

**Logging:**
- Framework: Custom `DirigentLogger` in `logger.py`
- Outputs: Both stdout (with timestamps and icons) and `.dirigent/logs/run-{timestamp}.log`
- Structured: Supports JSON output with `--output json` flag
- Levels: DEBUG, INFO, WARN, ERROR

**Validation:**
- Input validation: `dirigent.py::validate_inputs()` checks SPEC.md and repo path existence
- Route validation: Router validates analysis results before route determination
- Task validation: Executor validates PLAN.json structure before execution

**Authentication:**
- Environment variable: `ANTHROPIC_API_KEY` for Claude API access
- Optional: `EXECUTION_ID` + `REPORTER_TOKEN` for portal integration (plan_first, interactive modes)
- Location: `dirigent.py` argument parsing

**Parallelism:**
- Design: Sequential by design — each task runs serially in a fresh Claude Code process
- Reason: Prevents context pollution, maintains atomic commits, simplifies state tracking
- Future: Marked as "not supported" in design principles

---

*Architecture analysis: 2026-03-20*
