# External Integrations

**Analysis Date:** 2026-03-20

## APIs & External Services

**Anthropic Claude API:**
- Claude Sonnet (model: "claude-sonnet-4-20250514") - Architecture decision making
  - SDK/Client: `anthropic>=0.20.0`
  - Auth: `ANTHROPIC_API_KEY` environment variable
  - Location: `src/outbid_dirigent/oracle.py:39`
  - Usage: Direct API calls for caching architectural decisions
  - Decision caching: `DECISIONS.json` in `.dirigent/` directory

**Outbid Portal:**
- Interactive question/answer system for plan approval and interactive execution
  - Protocol: HTTP REST (requests library)
  - Base URL: `PORTAL_URL` environment variable (default: "https://outbid-portal.vercel.app")
  - Auth: `X-Reporter-Token` header with `REPORTER_TOKEN` value
  - Endpoints:
    - `POST /api/execution-event` - Send questions, events to portal
    - `GET /api/poll-answer` - Poll for user answer to questions
    - `GET /api/poll-plan-approval` - Poll for plan approval in plan_first mode
  - Timeout: 30 seconds per HTTP request; polling interval 5 seconds
  - Location: `src/outbid_dirigent/questioner.py`

## Data Storage

**Databases:**
- None - Project is filesystem-based

**File Storage:**
- Local filesystem only
  - `.dirigent/` directory - Execution state and logs
    - `ANALYSIS.json` - Repository analysis result
    - `ROUTE.json` - Selected execution path (Greenfield/Legacy/Hybrid)
    - `PLAN.json` - Phase and task definitions
    - `STATE.json` - Current execution progress (resumable)
    - `DECISIONS.json` - Cached architecture decisions from Oracle
    - `BUSINESS_RULES.md` - Extracted business rules (Legacy route only)
    - `CONTEXT.md` - Relevant files context (Hybrid route only)
    - `logs/run-{timestamp}.log` - Structured execution logs
    - `logs/run-{timestamp}.jsonl` - JSON Lines format logs (optional)
    - `summaries/` - Per-task execution summaries
  - `.proteus/` directory - Proteus extraction artifacts (if --use-proteus enabled)
    - `arch.md` - Architecture profile
    - `fields.json` - Extracted data fields
    - `rules.json` - Business rules with locations
    - `events.json` - Domain events
    - `dependencies.json` - CRUD dependency map
    - `pipeline.json` - Extraction progress

**Caching:**
- Oracle decision cache: `.dirigent/DECISIONS.json`
  - Stores architectural decisions to avoid duplicate API calls
  - Cache key: SHA256 hash of question + options
  - Location: `src/outbid_dirigent/oracle.py:42-71`

## Authentication & Identity

**Auth Provider:**
- Custom token-based authentication for Portal integration
  - `REPORTER_TOKEN` environment variable - Bearer token for portal API
  - `EXECUTION_ID` environment variable - Identifier for execution session
  - Passed via `X-Reporter-Token` HTTP header
  - Location: `src/outbid_dirigent/questioner.py:93-94`

**API Authentication:**
- Anthropic: `ANTHROPIC_API_KEY` environment variable
  - Used by anthropic SDK automatically
  - Location: `src/outbid_dirigent/oracle.py:39`

## Monitoring & Observability

**Error Tracking:**
- None - Custom error logging to `.dirigent/logs/`

**Logs:**
- Structured logging to `.dirigent/logs/run-{timestamp}.log`
- Optional JSON Lines output to stdout with `--output json` flag
- JSON log file: `.dirigent/logs/run-{timestamp}.jsonl`
- Logging implementation: `src/outbid_dirigent/logger.py`
  - Contains fields: timestamp, level (DEBUG/INFO/WARN/ERROR), icon markers
  - Tracks: phases, tasks, deviations, commits, token usage
  - Supports JSON events with `@@JSON@@` prefix for streaming consumption

## CI/CD & Deployment

**Hosting:**
- Outbid Portal (https://outbid-portal.vercel.app) - Optional interactive hub

**CI Pipeline:**
- GitHub Actions optional (detected but not required)
- GitHub CLI (gh) optional for automatic PR creation
  - Invoked in Ship phase to create pull requests
  - Location: `src/outbid_dirigent/executor.py` - Ship phase

**Execution Modes:**
- Three modes with different integration points:
  1. `autonomous` (default) - No external interaction
  2. `plan_first` - Polls portal for plan approval before execution
  3. `interactive` - Polls portal for answers during execution

## Environment Configuration

**Required env vars:**
- `ANTHROPIC_API_KEY` - Claude API authentication (required for Oracle)

**Optional env vars:**
- `PORTAL_URL` - Portal base URL (default: https://outbid-portal.vercel.app)
- `EXECUTION_ID` - Execution session identifier (required if using interactive modes)
- `REPORTER_TOKEN` - Portal API authentication token (required if using interactive modes)

**Secrets location:**
- Environment variables only - No .env file storage
- Portal credentials passed via CLI args or env vars

## Webhooks & Callbacks

**Incoming:**
- None - Dirigent is headless, no webhook receivers

**Outgoing:**
- Portal Event API (`POST /api/execution-event`)
  - Sends questions, plan approvals, execution events
  - Polling responses via `GET /api/poll-answer` and `GET /api/poll-plan-approval`
  - Location: `src/outbid_dirigent/questioner.py:93-128`, `src/outbid_dirigent/questioner.py:316-395`

## External Tool Integrations

**Claude Code CLI:**
- Subprocess integration for task execution
- Command: `claude --dangerously-skip-permissions -p "{prompt}"`
- Timeout: 1800 seconds per task
- Location: `src/outbid_dirigent/executor.py:102-135`
- Used for:
  - Business rule extraction (Legacy route)
  - Planning phase (all routes)
  - Task execution (all routes)

**Git & GitHub:**
- Git CLI for repository operations:
  - Commit counting, branch detection, language analysis
  - Location: `src/outbid_dirigent/analyzer.py:372+`
- GitHub CLI (gh) for PR creation:
  - Optional, used only if available
  - Location: `src/outbid_dirigent/executor.py` - Ship phase

**Proteus MCP:**
- Optional Claude Code plugin for deep domain extraction
- Installed via: `claude plugin install proteus@proteus-marketplace`
- Requires: `uvx` command available
- Timeout: 1800 seconds per extraction phase
- 5 phases: Survey, Extract Fields, Extract Rules, Extract Events, Map Dependencies
- Location: `src/outbid_dirigent/proteus_integration.py`

---

*Integration audit: 2026-03-20*
