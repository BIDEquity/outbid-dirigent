# Testing Patterns

**Analysis Date:** 2026-03-20

## Test Framework

**Current Status:**
- No test framework currently configured
- `README.md` references `uv run pytest tests/` but no tests directory exists
- No pytest configuration files present
- Testing infrastructure is not yet implemented

**Recommended Setup (if implemented):**
- Framework: **pytest** (mentioned in README)
- Test runner: `uv run pytest`
- Config file: Would be `pytest.ini` or `pyproject.toml` section
- Assertion library: pytest built-in assertions

**Run Commands (when implemented):**
```bash
uv run pytest tests/              # Run all tests
uv run pytest -v tests/           # Verbose output
uv run pytest -k "test_analyzer"  # Run specific test module
uv run pytest --cov              # Coverage report (if coverage installed)
uv run pytest -x                 # Stop on first failure
```

## Test File Organization

**Proposed Location:**
- `tests/` directory at project root (parallel to `src/`)
- File naming: `test_*.py` for test modules
- Pattern: `tests/test_{module_name}.py` mirrors `src/outbid_dirigent/{module_name}.py`

**Proposed Structure:**
```
tests/
├── conftest.py                 # Shared fixtures
├── test_analyzer.py            # Tests for analyzer.py
├── test_router.py              # Tests for router.py
├── test_logger.py              # Tests for logger.py
├── test_executor.py            # Tests for executor.py (integration tests)
├── test_oracle.py              # Tests for oracle.py
├── test_questioner.py          # Tests for questioner.py
├── fixtures/                   # Reusable test data
│   ├── sample_repo/           # Mock repo structure
│   ├── sample_spec.md         # Mock SPEC.md
│   └── mock_responses.json    # Mocked API responses
└── integration/               # End-to-end tests
    └── test_full_flow.py      # Full dirigent workflow
```

## Test Structure

**Unit Test Pattern (not yet implemented, but recommended):**
```python
import pytest
from pathlib import Path
from outbid_dirigent.analyzer import Analyzer, AnalysisResult
from outbid_dirigent.logger import init_logger

@pytest.fixture
def tmp_repo(tmp_path):
    """Fixture: Create a temporary repo structure."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / ".git").mkdir()
    return tmp_path

@pytest.fixture
def tmp_spec(tmp_path):
    """Fixture: Create a temporary SPEC.md."""
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text("""
# Add Feature X
Implement new feature for the codebase.
""", encoding="utf-8")
    return spec_path

class TestAnalyzer:
    """Tests for Analyzer class."""

    def test_analyze_detects_python_repo(self, tmp_repo, tmp_spec):
        """Test: Analyzer detects Python as primary language."""
        analyzer = Analyzer(str(tmp_repo), str(tmp_spec))
        result = analyzer.analyze()
        assert result.repo.primary_language == "Python"

    def test_analyze_greenfield_route(self, tmp_repo, tmp_spec):
        """Test: Small Python repo triggers greenfield route."""
        analyzer = Analyzer(str(tmp_repo), str(tmp_spec))
        result = analyzer.analyze()
        assert result.route == "greenfield"
        assert result.confidence in ["medium", "high"]

    def test_analyze_saves_analysis(self, tmp_repo, tmp_spec):
        """Test: Analysis is persisted to .dirigent/ANALYSIS.json."""
        analyzer = Analyzer(str(tmp_repo), str(tmp_spec))
        analyzer.analyze()

        analysis_file = tmp_repo / ".dirigent" / "ANALYSIS.json"
        assert analysis_file.exists()
```

**Patterns Observed in Codebase:**
- Extensive use of `try-except` blocks for external operations (git, subprocess)
- Silent failure in non-critical operations: `except Exception: pass`
- Custom dataclasses for return values: `AnalysisResult`, `TaskResult`
- Logging on errors via `logger.error()`, `logger.warn()`

## Mocking

**Framework:** Would use **pytest-mock** or **unittest.mock**

**Patterns to Mock:**
```python
from unittest.mock import patch, MagicMock

class TestExecutor:
    """Tests for Executor class."""

    def test_extract_business_rules_calls_claude(self, tmp_repo, tmp_spec):
        """Test: extract_business_rules spawns claude code process."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="BUSINESS_RULES.md content",
                stderr=""
            )
            executor = create_executor(str(tmp_repo), str(tmp_spec))
            success = executor.extract_business_rules()

            assert success
            mock_run.assert_called_once()
            # Verify claude code was invoked
            call_args = mock_run.call_args[0][0]
            assert 'claude' in str(call_args[0])

    def test_oracle_caches_decisions(self, tmp_repo):
        """Test: Oracle returns cached decision on repeated query."""
        oracle = Oracle(str(tmp_repo))

        with patch.object(oracle, '_check_cache') as mock_cache:
            mock_cache.return_value = {
                "cache_key": "abc123",
                "decision": "TypeScript",
                "reasoning": "Cached decision"
            }

            result = oracle.decide(["TypeScript", "Python"], "Choose language")
            assert result == "TypeScript"
            mock_cache.assert_called_once()
```

**What to Mock:**
- External command execution: `subprocess.run()` calls to `claude` CLI
- API calls: `requests.post()` to Portal for questioner
- Anthropic API: `anthropic.Anthropic().messages.create()`
- File system operations (use `tmp_path` fixture instead)
- Git operations: `subprocess.run(['git', ...])` calls

**What NOT to Mock:**
- Core dataclass creation
- Pure Python logic (analyzer detection, routing decisions)
- Logger calls (capture logs instead)
- Path operations (use pytest's `tmp_path` fixture)

## Fixtures and Factories

**Proposed Fixtures (conftest.py):**
```python
# tests/conftest.py
import pytest
from pathlib import Path
from outbid_dirigent.logger import init_logger

@pytest.fixture
def logger_instance(tmp_path):
    """Fixture: Initialize logger with temporary directory."""
    return init_logger(str(tmp_path), verbose=False, output_json=False)

@pytest.fixture
def sample_repo(tmp_path):
    """Fixture: Create a realistic repo structure."""
    # Create src directory
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")

    # Create .git directory (minimal, just for existence check)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

    # Create package manifest
    (tmp_path / "pyproject.toml").write_text("""
[project]
name = "sample-project"
version = "0.1.0"
""")

    return tmp_path

@pytest.fixture
def sample_spec(tmp_path):
    """Fixture: Create a SPEC.md file."""
    spec = tmp_path / "SPEC.md"
    spec.write_text("""
# Add API Endpoint

Implement a new REST API endpoint for user management.

## Requirements
- Create GET /users endpoint
- Return JSON list of users
""", encoding="utf-8")
    return spec

@pytest.fixture
def sample_legacy_spec(tmp_path):
    """Fixture: Create a legacy migration SPEC.md."""
    spec = tmp_path / "SPEC.md"
    spec.write_text("""
# Migrate Java to Python

Refactor legacy Java codebase to modern Python with FastAPI.

## Requirements
- Migrate authentication system
- Rewrite database queries
""", encoding="utf-8")
    return spec
```

**Location:** `tests/conftest.py` — shared across all test modules

**Test Data Files:**
- Mock repos in `tests/fixtures/sample_repo/`
- Mocked API responses in `tests/fixtures/mock_responses.json`
- Sample specs in `tests/fixtures/specs/`

## Coverage

**Requirements:** Not enforced currently

**Recommended Target:** 70%+ for core modules (`analyzer.py`, `router.py`, `executor.py`)

**View Coverage (when implemented):**
```bash
uv run pytest --cov=src/outbid_dirigent --cov-report=html tests/
# Opens htmlcov/index.html
```

## Test Types

**Unit Tests:**
- Scope: Single class/function in isolation
- Mocking: All external dependencies (subprocess, API, filesystem uses tmp_path)
- Location: `tests/test_*.py`
- Example: Testing `Analyzer._detect_languages()` with mocked file list

**Integration Tests:**
- Scope: Multiple components working together
- Mocking: Only external services (Claude API, Portal)
- Location: `tests/integration/test_*.py`
- Example: Full `Analyzer.analyze()` with real repo structure

**End-to-End Tests:**
- Scope: Full dirigent workflow (currently manual/implicit)
- Setup: Real/sample repos, real git operations
- Location: `tests/integration/test_full_flow.py`
- Not automated; would require special test markers: `@pytest.mark.e2e`

## Common Patterns

**Async Testing (if needed for API calls):**
- Use `pytest-asyncio` plugin
- Fixture: `@pytest.mark.asyncio`
- Example:
```python
@pytest.mark.asyncio
async def test_oracle_decision_async():
    """Test async Oracle decision with Anthropic API."""
    oracle = Oracle(str(tmp_repo))
    # Would use async client calls
    result = await oracle.decide_async(...)
    assert result is not None
```

Currently, no async code is used; all subprocess calls are synchronous with timeouts.

**Error Testing:**
```python
def test_analyzer_handles_missing_spec(tmp_repo):
    """Test: Analyzer raises error for missing SPEC.md."""
    fake_spec = tmp_repo / "NONEXISTENT.md"

    with pytest.raises(FileNotFoundError):
        analyzer = Analyzer(str(tmp_repo), str(fake_spec))
        analyzer.analyze()

def test_executor_retry_on_timeout(tmp_repo, tmp_spec):
    """Test: Task is retried up to MAX_TASK_RETRIES on timeout."""
    with patch('subprocess.run') as mock_run:
        # First 2 calls timeout, 3rd succeeds
        mock_run.side_effect = [
            subprocess.TimeoutExpired("claude", 1800),
            subprocess.TimeoutExpired("claude", 1800),
            MagicMock(returncode=0, stdout="Success", stderr="")
        ]

        executor = create_executor(str(tmp_repo), str(tmp_spec))
        result = executor._execute_task({"task_id": "01-01", "name": "Test"})

        assert result.attempts == 3
        assert result.success
        assert mock_run.call_count == 3
```

**Deviation Testing:**
```python
def test_executor_logs_deviation_on_bug_fix(tmp_repo, tmp_spec, logger_instance):
    """Test: Task result logged as deviation when bug is fixed."""
    summary = "DEVIATION: Bug-Fix – Fixed null pointer exception in auth module"

    deviations = executor._extract_deviations(summary)

    assert len(deviations) > 0
    assert any(d['type'] == 'Bug-Fix' for d in deviations)
```

## Special Test Considerations

**State and Resumability Testing:**
```python
def test_executor_saves_state_after_task(tmp_repo, tmp_spec):
    """Test: STATE.json is updated after task completion."""
    executor = create_executor(str(tmp_repo), str(tmp_spec))
    # Execute a task
    result = executor._execute_task({"task_id": "01-01", "name": "Test"})

    state_file = tmp_repo / ".dirigent" / "STATE.json"
    assert state_file.exists()

    state = json.loads(state_file.read_text())
    assert "01-01" in state.get("completed_tasks", [])

def test_executor_resumes_from_state(tmp_repo, tmp_spec):
    """Test: Executor skips completed tasks on resume."""
    # Save partial state
    state_dir = tmp_repo / ".dirigent"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "STATE.json"
    state_file.write_text(json.dumps({
        "completed_tasks": ["01-01", "01-02"],
        "completed_steps": ["planning"]
    }))

    executor = create_executor(str(tmp_repo), str(tmp_spec))
    # Tasks 01-01, 01-02 should be skipped
```

**Logger Testing:**
```python
def test_logger_writes_to_file(tmp_path, logger_instance):
    """Test: Logger writes timestamped entries to .dirigent/logs/."""
    logger_instance.info("Test message")

    log_dir = tmp_path / ".dirigent" / "logs"
    log_files = list(log_dir.glob("run-*.log"))

    assert len(log_files) > 0
    content = log_files[0].read_text()
    assert "Test message" in content

def test_logger_json_output(tmp_path):
    """Test: Logger emits @@JSON@@ lines when --output json enabled."""
    logger = init_logger(str(tmp_path), verbose=True, output_json=True)

    # Capture stdout
    import io, sys
    captured = io.StringIO()
    sys.stdout = captured

    logger.info("JSON test")

    sys.stdout = sys.__stdout__
    output = captured.getvalue()

    assert "@@JSON@@" in output
```

---

*Testing analysis: 2026-03-20*
