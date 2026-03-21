# Codebase Concerns

**Analysis Date:** 2026-03-20

## Tech Debt

**Executor Monolith:**
- Issue: `src/outbid_dirigent/executor.py` is 1217 lines, handling business rule extraction, planning, execution, shipping, and summary generation in one class. Multiple responsibilities make testing and modification difficult.
- Files: `src/outbid_dirigent/executor.py`
- Impact: High change friction. New execution modes or extraction strategies require modifying a massive file. Maintenance cost scales with codebase.
- Fix approach: Extract concerns into separate classes: `BusinessRuleExtractor`, `PlanCreator`, `TaskRunner`, `Shipper`, `SummaryGenerator`. Use composition instead of monolithic methods.

**Global State via Module Functions:**
- Issue: `src/outbid_dirigent/dirigent.py` uses module-level globals `_questioner` and `_execution_mode` accessed via getter/setter functions (lines 27-50). This pattern is fragile and complicates testing and dependency injection.
- Files: `src/outbid_dirigent/dirigent.py` (lines 27-50), `src/outbid_dirigent/executor.py` (line 475), `src/outbid_dirigent/oracle.py` (line 23)
- Impact: Circular dependencies possible. Testing requires global state setup. Hard to run tests in parallel. Unpredictable behavior if state is modified by side effects.
- Fix approach: Replace with explicit dependency injection. Pass `questioner` and `execution_mode` as constructor parameters to classes that need them. Create a context object holding execution configuration.

**Loose Error Recovery in Task Retry Loop:**
- Issue: `src/outbid_dirigent/executor.py` lines 697-730 retry logic catches general exceptions without distinguishing transient (network, timeout) from permanent (invalid prompt, bad state) failures. All failures get equal treatment.
- Files: `src/outbid_dirigent/executor.py` (lines 697-730)
- Impact: Permanent failures waste retries and delay failure feedback. Transient failures might not get full retry budget if they trigger state corruption.
- Fix approach: Create `TransientError` and `PermanentError` exception types. Only retry on transient errors. Log failure type for debugging.

**Broad Exception Handling:**
- Issue: Multiple `except Exception:` clauses throughout codebase (e.g., `src/outbid_dirigent/analyzer.py` lines 347, 356, 397, 409) catch all exceptions including system signals and unrecoverable errors without re-raising critical ones.
- Files: `src/outbid_dirigent/analyzer.py`, `src/outbid_dirigent/executor.py`, `src/outbid_dirigent/proteus_integration.py`
- Impact: Hides bugs. System shutdown signals get swallowed. Makes debugging harder.
- Fix approach: Be specific about caught exceptions. Re-raise if not handled. Create custom exception types for domain errors.

**Missing State Validation:**
- Issue: `src/outbid_dirigent/executor.py` loads STATE.json but doesn't validate its structure. Lines 469, 524-525 assume fields like `completed_tasks` and `completed_phases` exist without checking.
- Files: `src/outbid_dirigent/executor.py` (lines 469, 540, 557)
- Impact: Corrupted STATE.json causes silent failures or partial execution. Recovery becomes unreliable.
- Fix approach: Create `ExecutionState` dataclass with validation. Load and validate before use. Migrate old state formats explicitly.

## Known Bugs

**JSON Response Parsing in Oracle:**
- Symptoms: Oracle may return JSON wrapped in markdown code blocks. Lines 217-220 try to unwrap, but only handle `\`\`\`json` and generic `\`\`\``. Other markdown formats (indented code, other delimiters) cause JSONDecodeError.
- Files: `src/outbid_dirigent/oracle.py` (lines 217-220)
- Trigger: When Claude API wraps response in uncommon markdown formats
- Workaround: Currently caught and returned as "Parsing Error" decision. Executor continues but with degraded information.
- Fix approach: Use regex to strip all markdown code block variations. Validate JSON structure before parsing. Return fallback decision with specific error info.

**Questioner Polling Race Condition:**
- Symptoms: `src/outbid_dirigent/questioner.py` polls for answers with 5-second intervals. Between polling loop start and question submission response, the question_id might not be set yet. Lines 124-128 check for missing question_id but don't retry submission.
- Files: `src/outbid_dirigent/questioner.py` (lines 91-128)
- Trigger: High latency to Portal when submitting question
- Workaround: Falls back to default_on_timeout if question_id missing
- Fix approach: Retry submission with backoff. Validate question_id before entering poll loop.

**Incomplete Proteus Status Tracking:**
- Symptoms: `src/outbid_dirigent/proteus_integration.py` doesn't persist phase completion state. If Proteus timeout occurs mid-pipeline, resuming restarts all phases instead of skipping completed ones.
- Files: `src/outbid_dirigent/proteus_integration.py` (lines 96-150+)
- Trigger: Run with `--use-proteus --resume` after timeout
- Workaround: None. Must re-run all Proteus phases.
- Fix approach: Write pipeline.json after each phase. Check and skip completed phases on resume.

**Plan Phase ID Compatibility:**
- Symptoms: `src/outbid_dirigent/executor.py` line 504 tries to handle both `phase.get("id")` and `phase.get("phase")` but logic is fragile. If both exist with different values, behavior is undefined. Plan creation doesn't enforce ID format.
- Files: `src/outbid_dirigent/executor.py` (line 504), `src/outbid_dirigent/executor.py` (lines 440-450 in create_plan)
- Trigger: Plans with inconsistent ID field naming
- Workaround: Assumes one field will be truthy; whichever is first
- Fix approach: Plan schema should specify single ID field. Validate in create_plan. Normalize on load.

## Security Considerations

**Unredacted Logs in Errors:**
- Risk: Error messages and stack traces in logs may contain sensitive data (API keys in prompts, file paths with secrets, token values). `src/outbid_dirigent/logger.py` logs full exception strings without filtering.
- Files: `src/outbid_dirigent/logger.py` (lines 413-418), logs written to `.dirigent/logs/`
- Current mitigation: Logs are in `.dirigent/` which is typically `.gitignored`. But `--output json` sends structured logs to stdout which may be captured by CI systems.
- Recommendations:
  - Redact known sensitive patterns (API_KEY=, sk-, Bearer, Token=) from log messages
  - Hash or obfuscate file paths containing `/home/`, `/Users/`, sensitive directory names
  - Document that logs may contain secrets; advise `.dirigent/` not be committed
  - Add flag to enable "strict" mode that redacts all personal data

**Portal Credentials in Environment:**
- Risk: `src/outbid_dirigent/dirigent.py` lines 362-371 read `EXECUTION_ID` and `REPORTER_TOKEN` from environment. These aren't validated for format and could be echoed in debug output.
- Files: `src/outbid_dirigent/dirigent.py` (lines 355-371)
- Current mitigation: Only used for Portal integration if all three values present
- Recommendations:
  - Validate token format (minimum entropy, expected prefix)
  - Never log token values (even in debug mode)
  - Consider short-lived token support (expiration, rotation)

**Subprocess invocation with untrusted input:**
- Risk: `src/outbid_dirigent/executor.py` line 117 runs Claude CLI with prompt as argument. If prompt contains shell metacharacters or is user-controlled, command injection is possible.
- Files: `src/outbid_dirigent/executor.py` (line 117)
- Current mitigation: Prompt is built internally, not from user input
- Recommendations:
  - Use subprocess.run with list args (not shell=True) — already done but verify
  - Add shell metacharacter validation if prompt ever becomes user-controllable
  - Document this assumption

## Performance Bottlenecks

**Whole Codebase Scans in Analysis:**
- Problem: `src/outbid_dirigent/analyzer.py` lines 340-410 walk entire repo to count files, lines, and detect language. On large monorepos (10000+ files), this is slow.
- Files: `src/outbid_dirigent/analyzer.py` (lines 330-410)
- Cause: No caching, no early termination, no parallelization
- Improvement path:
  - Cache results in ANALYSIS.json with repo mtime/commit hash to detect changes
  - Sample subdirectories instead of scanning all files for initial language detection
  - Parallelize file iteration with concurrent.futures

**Sequential Task Execution:**
- Problem: `src/outbid_dirigent/executor.py` execute_plan loop (lines 502-564) runs tasks one at a time. Each Claude Code process waits for the previous one to complete, even if phases have independent tasks.
- Files: `src/outbid_dirigent/executor.py` (lines 520-554)
- Cause: Design assumes sequential execution for safety. State updates must be atomic.
- Improvement path:
  - Identify task DAG early (depends_on field exists in PLAN.json but not used)
  - Run tasks with no dependencies in parallel using ProcessPoolExecutor or asyncio
  - Protect shared state with locks during phase transitions
  - Start with Greenfield route (simpler) to pilot parallelization

**Context Loading in Oracle Queries:**
- Problem: `src/outbid_dirigent/oracle.py` _load_context (lines 73-119) reads multiple JSON files and markdown files for every query, even if context hasn't changed.
- Files: `src/outbid_dirigent/oracle.py` (lines 73-119)
- Cause: No caching, file I/O happens on every decision
- Improvement path:
  - Cache context in memory with file mtime tracking
  - Lazy load only needed context (SPEC for some decisions, BUSINESS_RULES for others)
  - Implement context hashing to detect changes

## Fragile Areas

**Plan Format Evolution:**
- Files: `src/outbid_dirigent/executor.py` (lines 400-452), output is PLAN.json format
- Why fragile: Claude creates JSON plan structure, but format isn't strongly typed. Executor expects specific fields (id, name, tasks, description, files_to_create, files_to_modify, depends_on) but doesn't validate. If Claude changes output format (new field added, field omitted), execution breaks silently.
- Safe modification:
  - Define strict JSON schema for PLAN.json
  - Validate plan on load (line 437-451)
  - Add migration function if schema changes
  - Test with malformed plans to ensure clear error messages
- Test coverage: PLAN.json creation and validation are untested

**Business Rule Extraction Consistency:**
- Files: `src/outbid_dirigent/executor.py` (lines 187-251), output is BUSINESS_RULES.md
- Why fragile: Business rules are extracted by Claude once and never re-validated. If extraction is incomplete or wrong, subsequent plans built on those rules inherit the errors. No way to detect extraction quality until execution fails.
- Safe modification:
  - Add validation step after extraction (e.g., "Check that all extracted rules are referenced in codebase")
  - Implement extraction verification using Oracle (ask Oracle if rules are complete)
  - Add manual review checkpoint in interactive mode
- Test coverage: Extraction is not unit-tested; only integration-tested via full execution

**Resume State Corruption:**
- Files: `src/outbid_dirigent/router.py`, `src/outbid_dirigent/executor.py` (STATE.json management)
- Why fragile: STATE.json tracks completed steps and tasks. If corruption occurs (partial write, interrupted save), resume logic becomes unreliable. No checksums or atomic writes protect state.
- Safe modification:
  - Use atomic writes: write to temp file, then rename
  - Add checksum or version field to STATE.json
  - Validate state before reading (schema check, field presence)
  - Add state rollback mechanism (keep previous state backup)
- Test coverage: Resume scenarios are not tested

## Scaling Limits

**Task Execution Timeout:**
- Current capacity: 30 minutes per task (CLAUDE_TIMEOUT = 1800)
- Limit: Claude Code processes that take >30min (large test suites, data migrations) will timeout
- Scaling path:
  - Make timeout configurable per phase/task
  - Implement progress tracking within timeout (parse Claude stdout for "progress" events)
  - Break large tasks into subtasks automatically if they approach timeout
  - Support `--timeout-minutes` CLI flag

**Number of Tasks Per Plan:**
- Current capacity: Plan supports unlimited phases/tasks, but executor tracks state linearly. Large plans (50+ tasks) mean large STATE.json updates and slow resume iteration
- Limit: Plans with 100+ tasks become slow to resume due to full list iteration
- Scaling path:
  - Index completed_tasks by task_id (Dict instead of List)
  - Lazy-load phase history only when needed
  - Implement tiered state storage (recent = in memory, old = in file)

**Proteus Phase Timeout:**
- Current capacity: 30 minutes per Proteus phase (PROTEUS_TIMEOUT = 1800)
- Limit: Large codebases (>10000 files, complex domain) may not complete extraction in 30min
- Scaling path:
  - Make timeout configurable
  - Implement phase checkpointing (save partial results mid-phase, resume from checkpoint)
  - Split extraction phases by codebase regions (extract from src/, then test/, then config/)

## Dependencies at Risk

**Anthropic SDK Dependency:**
- Risk: Tight coupling to anthropic.Anthropic client API. If Anthropic changes API signature or deprecates message format, Oracle breaks.
- Files: `src/outbid_dirigent/oracle.py` (line 39, line 183)
- Impact: Entire Oracle functionality blocked until updated
- Migration plan:
  - Wrap Anthropic client in adapter class (AnthropicClientAdapter)
  - Write abstractions for message creation, response parsing
  - Make it easier to swap LLM providers if needed

**Claude Code CLI Dependency:**
- Risk: Hard dependency on `claude` CLI being installed and in PATH. No fallback if missing.
- Files: `src/outbid_dirigent/executor.py` (line 117), `src/outbid_dirigent/proteus_integration.py` (lines 51-54)
- Impact: Entire execution broken if CLI not available. Error message says "Claude CLI nicht gefunden" but doesn't provide next steps.
- Migration plan:
  - Check for Claude CLI at startup (in main before any real work)
  - Provide install instructions URL
  - Support dry-run without CLI for planning phases only
  - Consider API-based execution as fallback

**Requests Library for Portal Polling:**
- Risk: Portal integration uses `requests.post` and `requests.get` with fixed 30-second timeouts. If Portal is down or slow, Questioner blocks entire execution.
- Files: `src/outbid_dirigent/questioner.py` (lines 93-134, 144-149)
- Impact: Long timeouts cascade (30s per request × 5 retries = 2.5min blocked)
- Migration plan:
  - Add exponential backoff to polling (5s, 10s, 20s, 40s)
  - Make timeout configurable
  - Graceful degradation: if Portal unavailable, skip interactive features but continue
  - Add circuit breaker pattern to Portal client

## Missing Critical Features

**No Dependency Tracking in Task Execution:**
- Problem: PLAN.json includes `depends_on` field for each task, but executor ignores it (line 520). All tasks run sequentially regardless of dependencies. This prevents parallelization and doesn't enable task reordering for optimization.
- Blocks: Parallel execution, smart task scheduling, failure recovery (could re-run only failed task + dependents)
- Fix approach:
  - Build task DAG from depends_on during plan load
  - Implement topological sort to enable parallel execution
  - Run all tasks with no dependencies in parallel
  - Wait for all dependencies before running dependent task

**No Execution Metrics or Observability:**
- Problem: Executor logs task completion (commit hash, duration) but doesn't track metrics useful for optimization: token usage per task type, success rate by phase, average retry count. This makes it hard to identify bottlenecks.
- Blocks: Performance tuning, cost analysis, SLA forecasting
- Fix approach:
  - Track TaskMetrics: duration, tokens_in, tokens_out, retries, commit_count
  - Aggregate metrics by phase and task type
  - Output metrics JSON at end of run
  - Add `--metrics` flag to save detailed metrics for later analysis

**No Task Rollback or Undo:**
- Problem: If task execution succeeds but introduces bugs, there's no way to undo it without manual git operations. STATE.json has no rollback field, no previous commit tracking.
- Blocks: Safe failure recovery, multi-attempt strategies where wrong approach can be undone
- Fix approach:
  - Track pre-task commit hash in STATE.json
  - Add `dirigent rollback --task <id>` command to git reset to pre-task state
  - Implement soft rollback: preserve commits but mark as reverted for history

**No Handling of Empty/Invalid Specs:**
- Problem: If SPEC.md is empty or malformed, analyzer/planner proceeds anyway with minimal context. No validation of spec quality or coverage.
- Blocks: Catching user errors early, providing guidance on spec format
- Fix approach:
  - Define SPEC.md schema (required sections, minimum content)
  - Add SPEC validation in dirigent.py before analysis
  - Provide template SPEC.md with examples
  - Return clear errors if SPEC fails validation

## Test Coverage Gaps

**Business Rule Extraction Quality:**
- What's not tested: Does extraction capture all rules? Are edge cases (implicit rules, conditional logic) handled?
- Files: `src/outbid_dirigent/executor.py` (lines 187-251)
- Risk: Silent extraction failures. Plan based on incomplete rules. Execution loses business logic.
- Priority: High
- Testing approach:
  - Create test repos with known business rules (e.g., Java Spring app with 10 documented rules)
  - Extract rules, verify all are present and accurate
  - Measure extraction precision/recall

**Task Resumption After Failures:**
- What's not tested: Does resume() correctly skip completed tasks? Does state recovery work after corruption? Does task retry preserve context?
- Files: `src/outbid_dirigent/executor.py` (lines 462-566), `src/outbid_dirigent/dirigent.py` (lines 190-246)
- Risk: Phantom task execution (task runs twice), lost state, incomplete recovery
- Priority: High
- Testing approach:
  - Create test STATE.json with partially completed phases
  - Call execute_plan with pre-populated state
  - Verify tasks are skipped and phase completes correctly
  - Corrupt STATE.json, verify clear error

**Oracle Cache Consistency:**
- What's not tested: Does cache eviction work? Can concurrent queries corrupt cache? Are cache keys stable?
- Files: `src/outbid_dirigent/oracle.py` (lines 41-71, 229-244)
- Risk: Wrong decisions cached, stale data served, cache becomes untrustworthy
- Priority: Medium
- Testing approach:
  - Ask same question twice, verify cache hit happens
  - Modify SPEC.md, ask question, verify cache doesn't return old answer
  - Test cache key collision (different questions with same hash)

**Error Message Clarity:**
- What's not tested: Are error messages actionable? Can user understand what went wrong?
- Files: Throughout — error handling is scattered
- Risk: User confusion, debugging difficulty, unactionable errors
- Priority: Medium
- Testing approach:
  - Run with known failure scenarios (missing Claude CLI, bad SPEC, repo not git)
  - Verify error message clearly states problem and suggests fix
  - Example: "Claude CLI nicht gefunden" → "Install with `uv tool install claude` or visit https://claude.ai/claude-code"

**Proteus Integration Robustness:**
- What's not tested: Does resume work with partial Proteus results? Are all 5 phases tested? What happens if phase times out?
- Files: `src/outbid_dirigent/proteus_integration.py`, `src/outbid_dirigent/executor.py` (lines 254-290)
- Risk: Proteus pipeline fails silently. Incomplete domain model used for planning.
- Priority: High
- Testing approach:
  - Mock Claude Code to simulate timeout at each phase
  - Verify resume skips completed phases, retries failed phase
  - Test that partial domain data is handled gracefully

---

*Concerns audit: 2026-03-20*
