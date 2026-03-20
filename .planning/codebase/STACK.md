# Technology Stack

**Analysis Date:** 2026-03-20

## Languages

**Primary:**
- Python 3.10+ - Complete codebase for orchestration and control plane

**Secondary:**
- None - Pure Python project

## Runtime

**Environment:**
- Python 3.10 or later

**Package Manager:**
- uv - Fast Python package manager with lockfile support
- Lockfile: `uv.lock` (present and comprehensive)

## Frameworks

**Core:**
- None - Stdlib-based implementation

**CLI:**
- argparse (stdlib) - Command-line argument parsing in `src/outbid_dirigent/dirigent.py`

**Logging:**
- stdlib logging (custom `DirigentLogger`) - Structured logging to `.dirigent/logs/` with JSON support

**Testing:**
- pytest (likely, referenced in README) - Run with `uv run pytest tests/`

**Build/Dev:**
- hatchling - Build backend defined in `pyproject.toml`

## Key Dependencies

**Critical:**
- anthropic >= 0.20.0 - Claude API client for Oracle decisions and direct API calls
  - Uses Claude Sonnet (model: "claude-sonnet-4-20250514") for architecture decisions
  - Location: `src/outbid_dirigent/oracle.py`
- requests >= 2.28.0 - HTTP client for portal integration and polling
  - Location: `src/outbid_dirigent/questioner.py`, `src/outbid_dirigent/executor.py`

**Infrastructure (from uv.lock):**
- httpx 0.28.1 - HTTP client (dependency of anthropic)
- pydantic - Data validation (dependency of anthropic)
- anyio 4.12.1 - Async I/O library
- certifi 2026.2.25 - SSL certificates
- jiter 0.13.0 - JSON parser (dependency of anthropic)

## Configuration

**Environment:**
- Configuration via command-line arguments
- Environment variable overrides for integration credentials (see INTEGRATIONS.md)

**Build:**
- `pyproject.toml` - Project configuration
  - Entry point: `dirigent = "outbid_dirigent.dirigent:main"`
  - Minimum Python version: 3.10

## Platform Requirements

**Development:**
- Python 3.10+ installed
- uv package manager installed (recommended per README)
- Claude CLI installed - for Claude Code execution via subprocess
- Git CLI - for repository operations
- GitHub CLI (gh) - Optional, for automatic PR creation

**Production:**
- Same as development
- Python 3.10+ runtime
- `ANTHROPIC_API_KEY` environment variable (required for Oracle)
- Optional: `PORTAL_URL`, `EXECUTION_ID`, `REPORTER_TOKEN` for interactive modes

## External Tool Dependencies

**Critical External Tools:**
- Claude Code CLI (`claude` command) - Core execution engine
  - Invoked via `subprocess.run(["claude", "--dangerously-skip-permissions", "-p", prompt])`
  - Location: `src/outbid_dirigent/executor.py:116`
  - Timeout: 1800 seconds (30 minutes) per task
- Git CLI - Repository analysis and operations
  - Location: `src/outbid_dirigent/analyzer.py:372+`
- GitHub CLI (gh) - Optional for automated PR creation during Ship phase

**Optional External Tools:**
- Proteus MCP Plugin - For enhanced domain extraction
  - Accessed via Claude Code integration
  - Requires: `uvx` command
  - Controlled by: `--use-proteus` flag
  - Location: `src/outbid_dirigent/proteus_integration.py`

## Module Structure

```
src/outbid_dirigent/
├── dirigent.py              # Entry point + orchestration
├── analyzer.py              # Repo + spec analysis
├── router.py                # Route selection (Greenfield/Legacy/Hybrid)
├── executor.py              # Claude Code invocations + task execution
├── oracle.py                # Architecture decisions via Claude API
├── proteus_integration.py   # Proteus domain extraction wrapper
├── questioner.py            # Portal integration for interactive questions
├── logger.py                # Structured logging
└── __init__.py
```

## Notable Implementation Patterns

**Subprocess Management:**
- All external tool invocation (claude, git, proteus) via `subprocess.run()`
- Timeouts implemented: 1800s for Claude Code, 30s for HTTP requests
- stderr/stdout captured for error handling and logging

**HTTP Integration:**
- `requests` library for synchronous HTTP
- Portal URL configurable via CLI argument or env var
- Request/response pattern with polling for asynchronous operations

**State Management:**
- JSON-based state files in `.dirigent/` directory:
  - `ANALYSIS.json` - Repo analysis results
  - `ROUTE.json` - Selected execution path
  - `PLAN.json` - Phase and task definitions
  - `STATE.json` - Execution progress (for resumability)
  - `DECISIONS.json` - Cached Oracle decisions
- All state persisted for full resumability

---

*Stack analysis: 2026-03-20*
