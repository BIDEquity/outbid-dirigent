#!/usr/bin/env python3
"""
Outbid Dirigent – Strukturiertes Logging
Alle Log-Ausgaben gehen sowohl nach stdout als auch in .dirigent/logs/
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class DirigentLogger:
    """Strukturierter Logger für den Outbid Dirigenten."""

    ICONS = {
        "start": "🎼",
        "analyze": "🔍",
        "stats": "📊",
        "route": "🗺️",
        "reason": "📋",
        "extract": "📖",
        "rules": "✅",
        "plan": "📝",
        "phase": "⚡",
        "task": "🔨",
        "task_done": "✅",
        "oracle": "🔮",
        "decision": "💡",
        "deviation": "⚠️",
        "error": "❌",
        "ship": "🚢",
        "done": "🎉",
        "resume": "🔄",
        "skip": "⏭️",
        "retry": "🔁",
        "stop": "🛑",
        # New icons for enhanced logging
        "thinking": "🧠",
        "file_read": "📄",
        "file_write": "✏️",
        "file_create": "📝",
        "bash": "💻",
        "search": "🔎",
        "test": "🧪",
        "lint": "🔧",
    }

    def __init__(self, repo_path: str, verbose: bool = True, output_json: bool = False, dirigent_dir: Optional[Path] = None):
        self.repo_path = Path(repo_path)
        self.verbose = verbose
        self.output_json = output_json
        self.log_dir = (dirigent_dir or self.repo_path / ".dirigent") / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_file = self.log_dir / f"run-{timestamp}.log"
        self.json_log_file = self.log_dir / f"run-{timestamp}.jsonl"

        # Tracking state for JSON output
        self._start_time = datetime.now()
        self._phases_complete = 0
        self._tasks_complete = 0
        self._total_tasks = 0
        self._total_phases = 0
        self._total_commits = 0
        self._total_deviations = 0

        # Token/Cost tracking
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cache_tokens = 0
        self._total_cost_cents = 0

        # Initialisiere Log-Dateien
        self._write_to_file(f"# Outbid Dirigent Log - {timestamp}\n")

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _iso_timestamp(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.utcnow().microsecond // 1000:03d}Z"

    def _emit_json(self, event_type: str, data: dict):
        """Emits a @@JSON@@ prefixed line to stdout if --output json is active."""
        if not self.output_json:
            return
        event = {
            "type": event_type,
            "ts": self._iso_timestamp(),
            "data": data,
        }
        try:
            print(f"@@JSON@@{json.dumps(event, ensure_ascii=False)}")
            sys.stdout.flush()
        except BrokenPipeError:
            # Pipe closed - ignore
            pass

    def _write_to_file(self, message: str):
        """Schreibt in die Text-Log-Datei."""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")

    def _write_json_log(self, entry: dict):
        """Schreibt strukturierten Log-Eintrag als JSON."""
        entry["timestamp"] = datetime.now().isoformat()
        with open(self.json_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _log(self, icon_key: str, message: str, level: LogLevel = LogLevel.INFO,
             data: Optional[dict] = None):
        """Interner Log-Aufruf."""
        icon = self.ICONS.get(icon_key, "•")
        timestamp = self._timestamp()

        formatted = f"[{timestamp}] {icon} {message}"

        # Stdout
        if self.verbose or level in [LogLevel.ERROR, LogLevel.WARN]:
            try:
                print(formatted)
                sys.stdout.flush()
            except BrokenPipeError:
                # Pipe closed (e.g., daemon stopped reading) - ignore
                pass

        # Text-Log
        self._write_to_file(formatted)

        # JSON-Log
        json_entry = {
            "level": level.value,
            "icon": icon_key,
            "message": message,
        }
        if data:
            json_entry["data"] = data
        self._write_json_log(json_entry)

    # Convenience-Methoden für verschiedene Log-Typen

    def start(self, message: str = "Outbid Dirigent gestartet"):
        self._log("start", message, data={"event": "start"})

    def analyze(self, repo_name: str):
        self._log("analyze", f"Analysiere Repo: {repo_name}")

    def stats(self, language: str, commits: int, age_info: str):
        self._log("stats", f"Erkannt: {language}, {commits} Commits, {age_info}")

    def route(self, route_type: str, confidence: str):
        self._log("route", f"Route: {route_type.upper()} (confidence: {confidence})",
                  data={"route": route_type, "confidence": confidence})

    def reason(self, reason: str):
        self._log("reason", f"Grund: {reason}")

    def extract_start(self):
        self._log("extract", "Starte Business Rule Extraktion...")

    def extract_done(self, rule_count: int):
        self._log("rules", f"Business Rules extrahiert ({rule_count} Regeln gefunden)",
                  data={"rule_count": rule_count})

    def plan_start(self):
        self._log("plan", "Erstelle Ausführungsplan...")

    def plan_done(self, phases: int, tasks: int, phase_details: Optional[list] = None):
        self._log("rules", f"Plan: {phases} Phasen, {tasks} Tasks",
                  data={"phases": phases, "tasks": tasks})
        self._total_phases = phases
        self._total_tasks = tasks
        plan_data = {
            "totalPhases": phases,
            "totalTasks": tasks,
        }
        if phase_details:
            plan_data["phases"] = phase_details
        self._emit_json("plan", plan_data)

    def phase_start(self, phase_id: str, phase_name: str, task_count: int = 0):
        self._log("phase", f"Starte Ausführung: Phase {phase_id} – {phase_name}",
                  data={"phase_id": phase_id, "phase_name": phase_name})
        self._emit_json("phase_start", {
            "phase": int(phase_id) if phase_id.isdigit() else phase_id,
            "name": phase_name,
            "taskCount": task_count,
        })

    def task_start(self, task_id: str, task_name: str, phase: Optional[int] = None):
        self._log("task", f"Task {task_id}: {task_name}",
                  data={"task_id": task_id, "task_name": task_name})
        data = {"taskId": task_id, "name": task_name}
        if phase is not None:
            data["phase"] = phase
        self._emit_json("task_start", data)

    def task_done(self, task_id: str, commit_hash: Optional[str] = None,
                  task_name: Optional[str] = None, phase: Optional[int] = None):
        msg = f"Task {task_id} abgeschlossen"
        if commit_hash:
            msg += f" (Commit: {commit_hash[:7]})"
        self._log("task_done", msg, data={"task_id": task_id, "commit": commit_hash})
        self._tasks_complete += 1
        # Emit commit event
        if commit_hash:
            self._total_commits += 1
            commit_data = {"taskId": task_id, "hash": commit_hash[:7], "message": f"Task {task_id} abgeschlossen"}
            if phase is not None:
                commit_data["phase"] = phase
            self._emit_json("commit", commit_data)
        # Emit task_complete event
        complete_data = {"taskId": task_id}
        if task_name:
            complete_data["name"] = task_name
        if commit_hash:
            complete_data["commitHash"] = commit_hash[:7]
        if phase is not None:
            complete_data["phase"] = phase
        self._emit_json("task_complete", complete_data)
        # Emit progress event
        if self._total_tasks > 0:
            progress_data = {
                "phasesComplete": self._phases_complete,
                "tasksComplete": self._tasks_complete,
                "totalTasks": self._total_tasks,
                "percentComplete": round(self._tasks_complete / self._total_tasks * 100),
            }
            if task_id:
                progress_data["taskId"] = task_id
            if phase is not None:
                progress_data["phase"] = phase
            self._emit_json("progress", progress_data)

    def task_failed(self, task_id: str, error: str, attempt: int):
        self._log("error", f"Task {task_id} fehlgeschlagen (Versuch {attempt}): {error}",
                  level=LogLevel.ERROR, data={"task_id": task_id, "attempt": attempt, "error": error})

    def task_retry(self, task_id: str, attempt: int):
        self._log("retry", f"Task {task_id} wird wiederholt (Versuch {attempt})")

    def oracle_query(self, question: str):
        self._log("oracle", f"Oracle-Anfrage: {question[:100]}...")

    def oracle_decision(self, decision: str, reason: str):
        self._log("decision", f"Oracle-Entscheidung: {decision} – {reason[:100]}",
                  data={"decision": decision, "reason": reason})

    def deviation(self, deviation_type: str, description: str,
                  task_id: Optional[str] = None, phase: Optional[int] = None):
        self._log("deviation", f"Deviation ({deviation_type}): {description}",
                  level=LogLevel.WARN, data={"type": deviation_type, "description": description})
        self._total_deviations += 1
        severity_map = {
            "Bug-Fix": "bug-fix", "bug-fix": "bug-fix", "bugfix": "bug-fix",
            "Added-Missing": "missing", "Added Missing": "missing", "missing": "missing",
            "Resolved-Blocker": "resolved", "Resolved Blocker": "resolved", "resolved": "resolved",
        }
        severity = severity_map.get(deviation_type, deviation_type.lower())
        data = {"severity": severity, "message": description}
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("deviation", data)

    def phase_complete(self, phase_id: str, phase_name: str, tasks_completed: int,
                       deviation_count: int, commit_count: int):
        """Emits a phase_complete JSON event."""
        self._phases_complete += 1
        self._emit_json("phase_complete", {
            "phase": int(phase_id) if phase_id.isdigit() else phase_id,
            "name": phase_name,
            "tasksCompleted": tasks_completed,
            "deviationCount": deviation_count,
            "commitCount": commit_count,
        })

    def api_usage(
        self,
        component: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        cost_cents: int = 0,
        operation: Optional[str] = None,
        task_id: Optional[str] = None,
        phase: Optional[int] = None,
        duration_ms: Optional[int] = None,
    ):
        """Emits API usage tracking event."""
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cache_tokens += cache_read_tokens
        self._total_cost_cents += cost_cents

        data = {
            "component": component,
            "model": model,
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
            "cacheReadTokens": cache_read_tokens,
            "cacheWriteTokens": cache_write_tokens,
            "costCents": cost_cents,
        }
        if operation:
            data["operation"] = operation
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        if duration_ms is not None:
            data["durationMs"] = duration_ms

        self._emit_json("api_usage", data)

        # Log to text file
        cost_usd = cost_cents / 100
        self._log(
            "stats",
            f"API Usage ({component}): {input_tokens} in / {output_tokens} out = ${cost_usd:.4f}",
            data=data,
        )

    def summary(
        self,
        markdown: str,
        files_changed: list,
        decisions: list,
        deviations: list,
        total_cost_cents: int,
        total_input_tokens: int,
        total_output_tokens: int,
    ):
        """Emits the final summary event with execution report."""
        self._emit_json("summary", {
            "markdown": markdown,
            "filesChanged": files_changed,
            "decisions": decisions,
            "deviations": deviations,
            "totalCostCents": total_cost_cents,
            "totalInputTokens": total_input_tokens,
            "totalOutputTokens": total_output_tokens,
        })

        # Log summary to file
        self._log("done", f"Summary: ${total_cost_cents/100:.2f}, {len(files_changed)} Dateien, {len(decisions)} Entscheidungen")

    def get_cost_totals(self) -> dict:
        """Returns accumulated token/cost totals."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_cache_tokens": self._total_cache_tokens,
            "total_cost_cents": self._total_cost_cents,
        }

    def run_complete(self, success: bool):
        """Emits the final complete JSON event."""
        elapsed = datetime.now() - self._start_time
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"
        self._emit_json("complete", {
            "success": success,
            "totalPhases": self._total_phases,
            "totalTasks": self._total_tasks,
            "totalCommits": self._total_commits,
            "totalDeviations": self._total_deviations,
            "duration": duration_str,
            "durationMs": int(elapsed.total_seconds() * 1000),
        })

    def error_json(self, message: str, phase: Optional[int] = None,
                   task_id: Optional[str] = None, fatal: bool = False):
        """Emits a structured error JSON event."""
        data = {"message": message, "fatal": fatal}
        if phase is not None:
            data["phase"] = phase
        if task_id:
            data["taskId"] = task_id
        self._emit_json("error", data)

    def ship_start(self, branch_name: str):
        self._log("ship", f"Shipping: Branch {branch_name}")

    def ship_done(self, pr_url: str):
        self._log("done", f"PR erstellt: {pr_url}", data={"pr_url": pr_url})

    def ship_pushed(self, branch_name: str):
        self._log("done", f"Branch {branch_name} gepusht (kein PR erstellt)")

    def resume(self, task_id: str):
        self._log("resume", f"Fortsetzen bei Task {task_id}")

    def skip(self, task_id: str, reason: str):
        self._log("skip", f"Task {task_id} übersprungen: {reason}")

    def stop(self, reason: str):
        self._log("stop", f"Ausführung gestoppt: {reason}", level=LogLevel.ERROR)

    def error(self, message: str, exception: Optional[Exception] = None):
        error_data = {"message": message}
        if exception:
            error_data["exception"] = str(exception)
            message += f" – {exception}"
        self._log("error", message, level=LogLevel.ERROR, data=error_data)

    def info(self, message: str):
        self._log("stats", message)

    def warn(self, message: str):
        self._log("deviation", message, LogLevel.WARN)

    def debug(self, message: str, data: Optional[dict] = None):
        if self.verbose:
            self._log("stats", f"[DEBUG] {message}", level=LogLevel.DEBUG, data=data)

    # ══════════════════════════════════════════
    # ENHANCED LOGGING - Granular Activity Events
    # ══════════════════════════════════════════

    def thinking(self, message: str, task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits a thinking/status event - what the agent is currently doing."""
        self._log("thinking", message)
        data = {"message": message}
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("thinking", data)

    def file_read(self, file_path: str, task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits event when a file is read."""
        self._log("file_read", f"Lese: {file_path}")
        data = {"path": file_path, "action": "read"}
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("file_operation", data)

    def file_write(self, file_path: str, lines_changed: int = 0,
                   task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits event when a file is written/modified."""
        msg = f"Schreibe: {file_path}"
        if lines_changed:
            msg += f" ({lines_changed} Zeilen)"
        self._log("file_write", msg)
        data = {"path": file_path, "action": "write", "linesChanged": lines_changed}
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("file_operation", data)

    def file_create(self, file_path: str, task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits event when a new file is created."""
        self._log("file_create", f"Erstelle: {file_path}")
        data = {"path": file_path, "action": "create"}
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("file_operation", data)

    def bash_command(self, command: str, exit_code: Optional[int] = None,
                     task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits event when a bash command is executed."""
        # Truncate long commands for display
        display_cmd = command[:100] + "..." if len(command) > 100 else command
        self._log("bash", f"$ {display_cmd}")
        data = {"command": command}
        if exit_code is not None:
            data["exitCode"] = exit_code
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("bash", data)

    def search(self, query: str, results_count: int = 0,
               task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits event when searching the codebase."""
        self._log("search", f"Suche: '{query}' ({results_count} Ergebnisse)")
        data = {"query": query, "resultsCount": results_count}
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("search", data)

    def test_run(self, test_command: str, passed: bool = True, details: str = "",
                 task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits event when tests are run."""
        status = "bestanden" if passed else "fehlgeschlagen"
        self._log("test", f"Tests {status}: {test_command}")
        data = {"command": test_command, "passed": passed}
        if details:
            data["details"] = details
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("test", data)

    def lint_run(self, passed: bool = True, errors: int = 0, warnings: int = 0,
                 task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits event when linting is run."""
        status = "bestanden" if passed else f"fehlgeschlagen ({errors} Fehler, {warnings} Warnungen)"
        self._log("lint", f"Linting {status}")
        data = {"passed": passed, "errors": errors, "warnings": warnings}
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("lint", data)

    def tool_use(self, tool_name: str, tool_input: dict, tool_use_id: str = "",
                 task_id: Optional[str] = None, phase: Optional[int] = None):
        """Emits event for any Claude tool use - enables hook integration."""
        self._log("stats", f"Tool: {tool_name}", data={"tool": tool_name})
        data = {
            "toolName": tool_name,
            "toolInput": tool_input,
        }
        if tool_use_id:
            data["toolUseId"] = tool_use_id
        if task_id:
            data["taskId"] = task_id
        if phase is not None:
            data["phase"] = phase
        self._emit_json("tool_use", data)


# Singleton-Pattern für globalen Logger
_logger_instance: Optional[DirigentLogger] = None


def init_logger(repo_path: str, verbose: bool = True, output_json: bool = False, dirigent_dir: Optional[Path] = None) -> DirigentLogger:
    """Initialisiert den globalen Logger."""
    global _logger_instance
    _logger_instance = DirigentLogger(repo_path, verbose, output_json, dirigent_dir=dirigent_dir)
    return _logger_instance


def get_logger() -> DirigentLogger:
    """Gibt den globalen Logger zurück."""
    if _logger_instance is None:
        raise RuntimeError("Logger nicht initialisiert. Rufe init_logger() zuerst auf.")
    return _logger_instance
