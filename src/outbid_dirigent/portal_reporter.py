"""
Portal Reporter — sends real-time events to the Outbid Portal.

This module handles communication with the portal API for:
- Plan events (with full task details)
- Progress updates
- Granular activity events (thinking, file operations, tool use)
- Error reporting
"""

import json
import time
from typing import Any, Dict, List, Optional

import requests
from loguru import logger


class PortalReporter:
    """Sends real-time events to the Outbid Portal."""

    def __init__(
        self,
        portal_url: str,
        execution_id: str,
        reporter_token: str,
        enabled: bool = True,
    ):
        self.portal_url = portal_url.rstrip("/")
        self.execution_id = execution_id
        self.reporter_token = reporter_token
        self.enabled = enabled
        self._current_task_id: Optional[str] = None
        self._current_phase: Optional[int] = None

    def set_context(self, task_id: Optional[str] = None, phase: Optional[int] = None):
        """Set the current task/phase context for subsequent events."""
        if task_id is not None:
            self._current_task_id = task_id
        if phase is not None:
            self._current_phase = phase

    def _send_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Send an event to the portal. Returns True on success."""
        if not self.enabled:
            return True

        # Add context if not already present
        if self._current_task_id and "taskId" not in data:
            data["taskId"] = self._current_task_id
        if self._current_phase is not None and "phase" not in data:
            data["phase"] = self._current_phase

        payload = {
            "execution_id": self.execution_id,
            "event": {
                "type": event_type,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "data": data,
            },
        }

        try:
            response = requests.post(
                f"{self.portal_url}/api/execution-event",
                headers={"X-Reporter-Token": self.reporter_token},
                json=payload,
                timeout=10,
            )
            if response.status_code != 200:
                logger.warning(f"Portal event failed: {response.status_code} - {response.text}")
                return False
            return True
        except requests.RequestException as e:
            logger.warning(f"Portal event error: {e}")
            return False

    # ══════════════════════════════════════════
    # PLAN EVENTS
    # ══════════════════════════════════════════

    def send_plan(
        self,
        phases: List[Dict[str, Any]],
        total_tasks: int,
        timeout_minutes: Optional[int] = None,
    ) -> bool:
        """Send the full execution plan to the portal."""
        data = {
            "planContent": {
                "phases": phases,
                "total_tasks": total_tasks,
            },
            "totalPhases": len(phases),
            "totalTasks": total_tasks,
        }
        if timeout_minutes:
            data["timeoutMinutes"] = timeout_minutes
        return self._send_event("plan", data)

    # ══════════════════════════════════════════
    # ACTIVITY EVENTS
    # ══════════════════════════════════════════

    def thinking(self, message: str) -> bool:
        """Send a thinking/status update."""
        return self._send_event("thinking", {"message": message})

    def file_operation(
        self,
        path: str,
        action: str,  # "read", "write", "create", "delete"
        lines_changed: int = 0,
    ) -> bool:
        """Send a file operation event."""
        data = {"path": path, "action": action}
        if lines_changed:
            data["linesChanged"] = lines_changed
        return self._send_event("file_operation", data)

    def bash_command(self, command: str, exit_code: Optional[int] = None) -> bool:
        """Send a bash command execution event."""
        data = {"command": command}
        if exit_code is not None:
            data["exitCode"] = exit_code
        return self._send_event("bash", data)

    def search(self, query: str, results_count: int = 0) -> bool:
        """Send a search event."""
        return self._send_event("search", {
            "query": query,
            "resultsCount": results_count,
        })

    def tool_use(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_use_id: str = "",
    ) -> bool:
        """Send a tool use event (from Claude hooks)."""
        data = {"toolName": tool_name, "toolInput": tool_input}
        if tool_use_id:
            data["toolUseId"] = tool_use_id
        return self._send_event("tool_use", data)

    # ══════════════════════════════════════════
    # PROGRESS EVENTS
    # ══════════════════════════════════════════

    def progress(
        self,
        tasks_complete: int,
        total_tasks: int,
        phases_complete: int = 0,
    ) -> bool:
        """Send a progress update."""
        percent = round(tasks_complete / total_tasks * 100) if total_tasks > 0 else 0
        return self._send_event("progress", {
            "tasksComplete": tasks_complete,
            "totalTasks": total_tasks,
            "phasesComplete": phases_complete,
            "percentComplete": percent,
        })

    def task_start(self, task_id: str, task_name: str) -> bool:
        """Signal that a task has started."""
        self._current_task_id = task_id
        return self._send_event("task_start", {
            "taskId": task_id,
            "name": task_name,
        })

    def task_complete(
        self,
        task_id: str,
        task_name: str = "",
        commit_hash: str = "",
    ) -> bool:
        """Signal that a task has completed."""
        data = {"taskId": task_id}
        if task_name:
            data["name"] = task_name
        if commit_hash:
            data["commitHash"] = commit_hash[:7]
        return self._send_event("task_complete", data)

    def phase_start(self, phase_id: str, phase_name: str, task_count: int = 0) -> bool:
        """Signal that a phase has started."""
        self._current_phase = int(phase_id) if phase_id.isdigit() else None
        return self._send_event("phase_start", {
            "phase": self._current_phase or phase_id,
            "name": phase_name,
            "taskCount": task_count,
        })

    def phase_complete(
        self,
        phase_id: str,
        phase_name: str,
        tasks_completed: int,
        deviation_count: int = 0,
        commit_count: int = 0,
    ) -> bool:
        """Signal that a phase has completed."""
        return self._send_event("phase_complete", {
            "phase": int(phase_id) if phase_id.isdigit() else phase_id,
            "name": phase_name,
            "tasksCompleted": tasks_completed,
            "deviationCount": deviation_count,
            "commitCount": commit_count,
        })

    # ══════════════════════════════════════════
    # ERROR & COMPLETION EVENTS
    # ══════════════════════════════════════════

    def error(self, message: str, fatal: bool = False) -> bool:
        """Send an error event."""
        return self._send_event("error", {
            "message": message,
            "fatal": fatal,
        })

    def deviation(self, severity: str, message: str) -> bool:
        """Send a deviation event."""
        return self._send_event("deviation", {
            "severity": severity,
            "message": message,
        })

    def complete(
        self,
        success: bool,
        duration_ms: int = 0,
        total_commits: int = 0,
        total_deviations: int = 0,
        branch_name: str = "",
        pr_url: str = "",
    ) -> bool:
        """Send the completion event."""
        data = {
            "success": success,
            "durationMs": duration_ms,
            "totalCommits": total_commits,
            "totalDeviations": total_deviations,
        }
        if branch_name:
            data["branchName"] = branch_name
        if pr_url:
            data["prUrl"] = pr_url
        return self._send_event("complete", data)

    def summary(
        self,
        markdown: str,
        files_changed: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        deviations: List[Dict[str, Any]],
        total_cost_cents: int = 0,
        total_input_tokens: int = 0,
        total_output_tokens: int = 0,
        branch_name: str = "",
        pr_url: str = "",
        duration_ms: int = 0,
        total_commits: int = 0,
    ) -> bool:
        """Send the final summary event."""
        return self._send_event("summary", {
            "markdown": markdown,
            "filesChanged": files_changed,
            "decisions": decisions,
            "deviations": deviations,
            "totalCostCents": total_cost_cents,
            "totalInputTokens": total_input_tokens,
            "totalOutputTokens": total_output_tokens,
            "branchName": branch_name,
            "prUrl": pr_url,
            "durationMs": duration_ms,
            "totalCommits": total_commits,
        })


def create_portal_reporter(
    portal_url: Optional[str] = None,
    execution_id: Optional[str] = None,
    reporter_token: Optional[str] = None,
) -> Optional[PortalReporter]:
    """Factory function to create a PortalReporter if all required params are present."""
    if not all([portal_url, execution_id, reporter_token]):
        return None
    return PortalReporter(
        portal_url=portal_url,
        execution_id=execution_id,
        reporter_token=reporter_token,
    )
