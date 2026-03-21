# Coding Conventions

**Analysis Date:** 2026-03-20

## Naming Patterns

**Files:**
- Snake_case for all Python modules: `dirigent.py`, `analyzer.py`, `proteus_integration.py`
- Uppercase for dataclass/class names: `DirigentLogger`, `Analyzer`, `Executor`, `Oracle`
- Constants in UPPERCASE: `MAX_TASK_RETRIES`, `PROTEUS_TIMEOUT`, `CLAUDE_TIMEOUT`

**Functions:**
- Snake_case for all functions: `analyze()`, `extract_business_rules()`, `_analyze_repo()`, `create_executor()`
- Private functions prefixed with underscore: `_analyze_repo()`, `_get_git_stats()`, `_load_decisions()`, `_emit_json()`
- Verbs first for action methods: `extract_business_rules()`, `execute_plan()`, `ship()`, `determine_route()`
- Getters use `get_*` or `is_*`: `get_questioner()`, `is_enabled()`, `is_active()`, `_get_cache_key()`

**Variables:**
- Snake_case for local and instance variables: `repo_path`, `spec_path`, `log_file`, `timeout_minutes`
- Boolean flags with `is_` or `has_` prefix: `has_tests`, `has_ci`, `is_enabled`, `output_json`, `dry_run`
- Config dictionaries with full words, no abbreviations: `analysis_result`, `route_type`, `task_result`
- Temporary accumulators during analysis: `lang_counts`, `legacy_found`, `greenfield_found`

**Types:**
- Use type hints universally: `def analyze(self) -> AnalysisResult:`
- Optional types explicit: `Optional[str]`, `Optional[Dict]`, `Optional[List[str]]`
- Union types with `|` syntax (Python 3.10+): Tuples in return statements: `Tuple[str, str, str, int, int]`
- Enum values in UPPERCASE: `RouteType.GREENFIELD`, `StepType.BUSINESS_RULE_EXTRACTION`, `LogLevel.INFO`

## Code Style

**Formatting:**
- Line length: Flexible, no strict limit enforced; context-aware wrapping
- Indentation: 4 spaces (standard Python)
- Imports organized by group:
  1. Standard library: `import os, sys, json, subprocess`
  2. Third-party: `import anthropic, requests`
  3. Local modules: `from outbid_dirigent.logger import get_logger`

**Linting:**
- No linter configured explicitly
- Manual code review for style consistency
- Black-style formatting conventions followed informally

## Import Organization

**Order:**
1. Standard library imports (os, sys, json, subprocess, pathlib, datetime, etc.)
2. Third-party libraries (anthropic, requests)
3. Local modules (from outbid_dirigent.* imports)

**Pattern:**
```python
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import anthropic
import requests

from outbid_dirigent.logger import get_logger
from outbid_dirigent.analyzer import Analyzer, load_analysis
```

**Path Aliases:**
- No path aliases used; always use full module paths
- Avoid relative imports; use absolute imports from `outbid_dirigent`

## Error Handling

**Patterns:**
- Try-except blocks with specific exception types:
  ```python
  try:
      result = subprocess.run([...], capture_output=True, text=True)
  except subprocess.TimeoutExpired:
      self.logger.error("Process timeout")
  except FileNotFoundError:
      self.logger.error("File not found")
  except Exception as e:
      self.logger.error(f"Unexpected error: {e}")
  ```

- Generic exception handlers use descriptive messages:
  ```python
  try:
      content = config_path.read_text(encoding="utf-8").lower()
  except Exception:
      pass  # Log optional, skip silently for non-critical operations
  ```

- Exceptions are logged via logger, never swallowed without context
- Custom error messages include context: `logger.error(f"Fehler beim Plan-Approval: {e}")`
- Return tuples on failure: `(False, error_message, traceback_info)`

**Error Logging:**
- Use structured logging with logger methods: `logger.error()`, `logger.warn()`, `logger.info()`
- Include meaningful messages, not generic "error occurred" statements
- Log German and English interchangeably based on context

## Logging

**Framework:** Custom `DirigentLogger` class in `logger.py`

**Patterns:**
- Initialize logger once: `logger = init_logger(repo_path, verbose, output_json)`
- Get logger in any module: `logger = get_logger()`
- Log levels via methods: `logger.info()`, `logger.warn()`, `logger.error()`, `logger.debug()`
- Icon-based log types for readability:
  ```python
  logger.analyze("Analysiere Repo")  # 🔍 icon
  logger.route("legacy", "high")     # 🗺️ icon
  logger.extract_done(42)            # ✅ icon
  ```

- JSON output enabled via `--output json` flag:
  ```python
  logger._emit_json("task_complete", {"taskId": "01-01", "phase": 1})
  ```

- Dual output: console + `.dirigent/logs/run-{timestamp}.log`
- Optional JSON logs in `.dirigent/logs/run-{timestamp}.jsonl`

**Logging Guidelines:**
- Log at phase boundaries: starting/completing major operations
- Log decisions that affect execution: route selection, Oracle decisions
- Log errors with full context, never silently skip
- Track token/cost usage via `logger.api_usage()`
- Use `logger.debug()` for verbose internal details only in verbose mode

## Comments

**When to Comment:**
- Function docstrings required for all public methods:
  ```python
  def slugify(text: str, max_length: int = 50) -> str:
      """
      Konvertiert Text in einen URL-sicheren Slug für Branch-Namen.

      Beispiel: "Add Dark Mode Toggle" -> "add-dark-mode-toggle"
      """
  ```

- Complex business logic explained inline:
  ```python
  # Cache-Keys sind SHA256-Hashes der Frage + Optionen
  content = f"{question}|{'|'.join(sorted(options))}"
  return hashlib.sha256(content.encode()).hexdigest()[:16]
  ```

- Non-obvious design decisions documented:
  ```python
  # Limit to 500 files for performance; approximation is acceptable
  for file in files[:500]:
  ```

- Module headers required:
  ```python
  #!/usr/bin/env python3
  """
  Outbid Dirigent – Analyzer
  Analysiert Repo-Struktur und Spec-Inhalt um den optimalen Ausführungspfad zu bestimmen.
  """
  ```

**JSDoc/Docstring Style:**
- Google-style docstrings for functions:
  ```python
  def ask(self, question: str, options: Optional[List[str]] = None) -> QuestionResult:
      """
      Stellt eine Frage und wartet auf Antwort.

      Args:
          question: Die Frage
          options: Liste von Auswahlmöglichkeiten

      Returns:
          QuestionResult mit answered, answer, timeout Flags
      """
  ```

- Dataclass docstrings for intent:
  ```python
  @dataclass
  class TaskResult:
      """Ergebnis einer Task-Ausführung."""
      task_id: str
      success: bool
      commit_hash: Optional[str]
  ```

## Function Design

**Size:**
- Aim for functions < 50 lines; split longer functions into helpers
- Public methods (< 20 lines) that delegate to private `_method()` helpers
- Example: `execute_plan()` orchestrates, `_execute_task()` handles details

**Parameters:**
- Positional for required, essential params: `def analyze(self, path: str)`
- Keyword-only for optional config: `timeout_minutes: int = 30, dry_run: bool = False`
- Avoid more than 4 positional params; use dataclasses for complex configs

**Return Values:**
- Tuples for multiple return values: `Tuple[bool, str, str]` for (success, message, data)
- Dataclasses for structured returns: `AnalysisResult`, `TaskResult`, `QuestionResult`
- Optional for nullable results: `Optional[Dict]` instead of None/error sentinel
- Boolean for success/failure: First element of tuple or dataclass field

## Module Design

**Exports:**
- Factory functions at module level: `create_executor()`, `create_oracle()`, `create_questioner()`
- Dataclasses exported directly: `from outbid_dirigent.analyzer import AnalysisResult`
- Singleton getter functions: `get_logger()`, `get_questioner()`, `get_execution_mode()`

**Barrel Files:**
- No barrel/index files; import directly from specific modules
- `from outbid_dirigent.logger import DirigentLogger, init_logger, get_logger`
- Not `from outbid_dirigent import DirigentLogger`

**Module Structure Pattern:**
1. Shebang + module docstring
2. Standard/third-party/local imports
3. Constants (UPPERCASE)
4. Dataclasses/Enums
5. Main class/function definitions
6. Factory/helper functions at bottom
7. Main guard if applicable: `if __name__ == "__main__":`

**Example from `dirigent.py`:**
```python
#!/usr/bin/env python3
"""Docstring explaining module purpose."""

import sys
from pathlib import Path

from outbid_dirigent.logger import get_logger

# Module-level constants
_questioner = None
_execution_mode = "autonomous"

def get_questioner():
    """Module-level getter for questioner."""
    global _questioner
    return _questioner

def validate_inputs(spec_path: Path, repo_path: Path) -> bool:
    """Validation function before main execution."""
    ...

def main():
    """Entry point - orchestrates phases."""
    ...

if __name__ == "__main__":
    main()
```

---

*Convention analysis: 2026-03-20*
