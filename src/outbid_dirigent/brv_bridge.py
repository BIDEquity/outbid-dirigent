"""
BRV Bridge — reads domain knowledge from ByteRover's .brv/context-tree/.

When a target repo has .brv/context-tree/ and the `brv` CLI is installed,
this bridge queries BRV for domain context relevant to each task and
injects it into the task prompt. Complete no-op when either is missing.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.plan_schema import Task


class BrvBridge:
    """Queries .brv/context-tree/ for task-relevant domain knowledge."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.context_tree = repo_path / ".brv" / "context-tree"
        self._cli_available: Optional[bool] = None

    def available(self) -> bool:
        """True if .brv/context-tree/ exists AND brv CLI is installed."""
        if not self.context_tree.is_dir():
            return False
        if self._cli_available is None:
            self._cli_available = shutil.which("brv") is not None
        return self._cli_available

    def context_for_task(self, task: Task, max_chars: int = 4000) -> Optional[str]:
        """Use `brv query` to get domain context relevant to this task.

        Builds a query from the task's name, description, and file paths,
        then delegates to the brv CLI for relevance-scored retrieval.
        Returns formatted text or None if nothing relevant found.
        """
        query_parts = [task.name]
        if task.description:
            query_parts.append(task.description[:200])
        file_context = task.files_to_create + task.files_to_modify
        if file_context:
            query_parts.append(f"Files: {', '.join(file_context[:10])}")
        query = " | ".join(query_parts)

        try:
            result = subprocess.run(
                ["brv", "query", query],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
                stdin=subprocess.DEVNULL,
            )
            if result.returncode != 0 or not result.stdout.strip():
                if result.stderr.strip():
                    logger.debug(f"brv query failed: {result.stderr[:200]}")
                return None
            output = result.stdout.strip()
            if len(output) > max_chars:
                output = output[:max_chars] + "\n... (truncated)"
            return output
        except subprocess.TimeoutExpired:
            logger.debug("brv query timed out after 30s")
            return None
        except Exception as e:
            logger.debug(f"brv query error: {e}")
            return None
