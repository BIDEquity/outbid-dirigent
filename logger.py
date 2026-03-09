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
    }

    def __init__(self, repo_path: str, verbose: bool = True):
        self.repo_path = Path(repo_path)
        self.verbose = verbose
        self.log_dir = self.repo_path / ".dirigent" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_file = self.log_dir / f"run-{timestamp}.log"
        self.json_log_file = self.log_dir / f"run-{timestamp}.jsonl"

        # Initialisiere Log-Dateien
        self._write_to_file(f"# Outbid Dirigent Log - {timestamp}\n")

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
            print(formatted)
            sys.stdout.flush()

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

    def plan_done(self, phases: int, tasks: int):
        self._log("rules", f"Plan: {phases} Phasen, {tasks} Tasks",
                  data={"phases": phases, "tasks": tasks})

    def phase_start(self, phase_id: str, phase_name: str):
        self._log("phase", f"Starte Ausführung: Phase {phase_id} – {phase_name}",
                  data={"phase_id": phase_id, "phase_name": phase_name})

    def task_start(self, task_id: str, task_name: str):
        self._log("task", f"Task {task_id}: {task_name}",
                  data={"task_id": task_id, "task_name": task_name})

    def task_done(self, task_id: str, commit_hash: Optional[str] = None):
        msg = f"Task {task_id} abgeschlossen"
        if commit_hash:
            msg += f" (Commit: {commit_hash[:7]})"
        self._log("task_done", msg, data={"task_id": task_id, "commit": commit_hash})

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

    def deviation(self, deviation_type: str, description: str):
        self._log("deviation", f"Deviation ({deviation_type}): {description}",
                  level=LogLevel.WARN, data={"type": deviation_type, "description": description})

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

    def debug(self, message: str, data: Optional[dict] = None):
        if self.verbose:
            self._log("stats", f"[DEBUG] {message}", level=LogLevel.DEBUG, data=data)


# Singleton-Pattern für globalen Logger
_logger_instance: Optional[DirigentLogger] = None


def init_logger(repo_path: str, verbose: bool = True) -> DirigentLogger:
    """Initialisiert den globalen Logger."""
    global _logger_instance
    _logger_instance = DirigentLogger(repo_path, verbose)
    return _logger_instance


def get_logger() -> DirigentLogger:
    """Gibt den globalen Logger zurück."""
    if _logger_instance is None:
        raise RuntimeError("Logger nicht initialisiert. Rufe init_logger() zuerst auf.")
    return _logger_instance
