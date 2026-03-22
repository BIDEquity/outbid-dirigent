"""
Task runner — executes individual Claude Code tasks.

Extracted from the Executor god class. Handles:
- Building task prompts with context
- Running Claude Code subprocesses
- Parsing results, deviations, summaries
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.plan_schema import Plan, Task
from outbid_dirigent.router import load_state, save_state


class TaskResult:
    """Result of a single task execution."""
    def __init__(
        self,
        task_id: str,
        success: bool,
        commit_hash: Optional[str] = None,
        summary: str = "",
        deviations: Optional[list[dict]] = None,
        duration_seconds: float = 0,
        attempts: int = 1,
    ):
        self.task_id = task_id
        self.success = success
        self.commit_hash = commit_hash
        self.summary = summary
        self.deviations = deviations or []
        self.duration_seconds = duration_seconds
        self.attempts = attempts


class TaskRunner:
    """Runs individual tasks via Claude Code subprocesses."""

    MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 1800  # 30 min

    def __init__(
        self,
        repo_path: Path,
        spec_content: str,
        default_model: str = "",
        default_effort: str = "",
    ):
        self.repo_path = repo_path
        self.spec_content = spec_content
        self.default_model = default_model
        self.default_effort = default_effort
        self.dirigent_dir = repo_path / ".dirigent"
        self.summaries_dir = self.dirigent_dir / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        # Discover spec images in .planning/assets/
        self.spec_images = self._discover_spec_images()

    def _discover_spec_images(self) -> list[Path]:
        """Find all images in .planning/assets/ directory."""
        assets_dir = self.repo_path / ".planning" / "assets"
        if not assets_dir.exists():
            return []
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        return [
            f for f in assets_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

    # ── Claude Code invocation ──

    def _run_claude(
        self,
        prompt: str,
        timeout: int = 0,
        model: str = "",
        effort: str = "",
        system_prompt: str = "",
    ) -> tuple[bool, str, str]:
        """Run Claude Code with a prompt. Returns (success, stdout, stderr)."""
        timeout = timeout or self.DEFAULT_TIMEOUT
        model = model or self.default_model
        effort = effort or self.default_effort

        cmd = ["claude", "--dangerously-skip-permissions"]
        if model:
            cmd.extend(["--model", model])
        if effort:
            cmd.extend(["--effort", effort])
        if system_prompt:
            cmd.extend(["--append-system-prompt", system_prompt])
        cmd.extend(["-p", prompt])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Claude Code timeout after {timeout}s")
            return False, "", f"Timeout after {timeout}s"
        except FileNotFoundError:
            logger.error("Claude CLI not found. Is 'claude' installed?")
            return False, "", "Claude CLI not found"
        except Exception as e:
            logger.error(f"Claude Code error: {e}")
            return False, "", str(e)

    # ── Context building ──

    def _load_previous_summaries(self) -> str:
        summaries = []
        for f in sorted(self.summaries_dir.glob("*-SUMMARY.md")):
            task_id = f.stem.replace("-SUMMARY", "")
            summaries.append(f"### Task {task_id}\n{f.read_text(encoding='utf-8')}")
        return "\n\n".join(summaries) if summaries else "Keine vorherigen Tasks."

    def _load_business_rules(self) -> Optional[str]:
        rules_file = self.dirigent_dir / "BUSINESS_RULES.md"
        return rules_file.read_text(encoding="utf-8") if rules_file.exists() else None

    def _get_recent_diff(self, max_commits: int = 3, max_chars: int = 4000) -> str:
        try:
            result = subprocess.run(
                ["git", "log", f"-{max_commits}", "--oneline", "--stat", "--no-color"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return ""
            diff = result.stdout.strip()
            return diff[:max_chars] + "\n... (truncated)" if len(diff) > max_chars else diff
        except Exception:
            return ""

    def _get_run_file_list(self) -> str:
        state = load_state(str(self.repo_path))
        if not state or not state.get("completed_tasks"):
            return ""
        try:
            count = len(state["completed_tasks"]) + 2
            result = subprocess.run(
                ["git", "diff", "--name-only", f"HEAD~{count}"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return ""
            files = [f for f in result.stdout.strip().splitlines() if not f.startswith(".dirigent/")]
            return "\n".join(files) if files else ""
        except Exception:
            return ""

    def _get_latest_commit_hash(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H"],
                cwd=self.repo_path, capture_output=True, text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    @staticmethod
    def _extract_deviations(summary: str) -> list[dict]:
        pattern = r"DEVIATION:\s*(\w+[-\w]*)\s*[:\-]?\s*(.+)"
        return [
            {"type": m.group(1).strip(), "description": m.group(2).strip()}
            for m in re.finditer(pattern, summary, re.IGNORECASE)
        ]

    # ── Prompt assembly ──

    def _build_prompt(self, task: Task, plan: Plan) -> str:
        """Assemble the full prompt for a task."""
        previous_summaries = self._load_previous_summaries()
        recent_diff = self._get_recent_diff()
        run_files = self._get_run_file_list()
        business_rules = self._load_business_rules()

        sections = [f"Du führst Task {task.id} aus: {task.name}"]

        # Plan position
        pos = plan.task_position(task.id)
        if pos:
            sections.append(f"""
# Deine Position im Plan
Position: Task {pos['index']}/{pos['total']}, Phase {pos['phase_id']}/{pos['total_phases']} ({pos['phase_name']})""")
            if "prev_id" in pos:
                sections.append(f"Vorheriger Task: {pos['prev_id']} - {pos['prev_name']}")
            if "next_id" in pos:
                sections.append(f"Nächster Task: {pos['next_id']} - {pos['next_name']}")

        # Assumptions & out of scope
        if plan.assumptions:
            sections.append("\n# Annahmen\n" + "\n".join(f"- {a}" for a in plan.assumptions))
        if plan.out_of_scope:
            sections.append("\n# NICHT dein Job (out of scope)\n" + "\n".join(f"- {x}" for x in plan.out_of_scope))

        # Spec
        sections.append(f"\n# Gesamt-Spec\n{self.spec_content}")

        # Reference spec images if available
        if self.spec_images:
            img_list = "\n".join(f"- .planning/assets/{img.name}" for img in self.spec_images)
            sections.append(f"\n# Visuelle Referenzen\nFolgende Bilder sind verfügbar (nutze Read tool um sie zu betrachten):\n{img_list}")

        # Progress
        sections.append(f"\n# Bisheriger Fortschritt\n{previous_summaries}")

        # Recent changes
        if recent_diff:
            sections.append(f"\n# Letzte Änderungen (was vorherige Tasks gemacht haben)\n```\n{recent_diff}\n```")
        if run_files:
            sections.append(f"\n# Alle bisher geänderten/erstellten Dateien in diesem Run\n{run_files}")

        # Task description
        sections.append(f"\n# Dein Task\n{task.description}")
        sections.append(f"Dateien zu erstellen: {', '.join(task.files_to_create) or 'keine'}")
        sections.append(f"Dateien zu modifizieren: {', '.join(task.files_to_modify) or 'keine'}")

        # Business rules
        if business_rules:
            sections.append(f"\n## Business Rules (MÜSSEN erhalten bleiben!)\n{business_rules[:2000]}")

        # Summary format hint (deviation rules are in system prompt)
        sections.append(f"""
## Summary Format
Erstelle .dirigent/summaries/{task.id}-SUMMARY.md mit:
- Was wurde gemacht
- Geänderte Dateien
- Deviations (falls vorhanden)
- Nächste Schritte (falls relevant)""")

        return "\n".join(sections)

    # ── Task execution ──

    SYSTEM_PROMPT_SUFFIX = """Du bist ein autonomer Coding-Agent der Tasks aus einem Plan ausführt.

Deviation Rules:
1. Bug gefunden → Automatisch fixen, in Summary als "DEVIATION: Bug-Fix" dokumentieren
2. Kritisches fehlt → Hinzufügen, als "DEVIATION: Added Missing" dokumentieren
3. Blocker entdeckt → Beheben, als "DEVIATION: Resolved Blocker" dokumentieren
4. Architektur-Frage → STOPP – Frage für Oracle dokumentieren

Nach Abschluss:
1. git add -A && git commit -m "feat(TASK_ID): TASK_NAME"
2. Summary in .dirigent/summaries/TASK_ID-SUMMARY.md erstellen

Keine Rückfragen. Kein Warten. Durcharbeiten und committen."""

    def run_task(self, task: Task, plan: Plan, phase_num: int | str = 1) -> TaskResult:
        """Execute a single task with retries."""
        start_time = datetime.now()
        prompt = self._build_prompt(task, plan)

        # Per-task model/effort override
        task_model = task.model or self.default_model
        task_effort = task.effort or self.default_effort

        # Inject static rules via system prompt (keeps user prompt focused)
        sys_prompt = self.SYSTEM_PROMPT_SUFFIX.replace("TASK_ID", task.id).replace("TASK_NAME", task.name)

        for attempt in range(1, self.MAX_RETRIES + 1):
            if attempt > 1:
                logger.info(f"Task {task.id} retry {attempt}/{self.MAX_RETRIES}")

            success, stdout, stderr = self._run_claude(
                prompt, model=task_model, effort=task_effort,
                system_prompt=sys_prompt,
            )

            if success:
                commit_hash = self._get_latest_commit_hash()
                summary_file = self.summaries_dir / f"{task.id}-SUMMARY.md"
                summary = summary_file.read_text(encoding="utf-8") if summary_file.exists() else ""
                deviations = self._extract_deviations(summary)

                duration = (datetime.now() - start_time).total_seconds()
                return TaskResult(
                    task_id=task.id,
                    success=True,
                    commit_hash=commit_hash,
                    summary=summary,
                    deviations=deviations,
                    duration_seconds=duration,
                    attempts=attempt,
                )

            if attempt < self.MAX_RETRIES:
                logger.warning(f"Task {task.id} failed (attempt {attempt}), retrying...")

        duration = (datetime.now() - start_time).total_seconds()
        return TaskResult(
            task_id=task.id,
            success=False,
            summary=f"Failed after {self.MAX_RETRIES} attempts: {stderr[:200]}",
            duration_seconds=duration,
            attempts=self.MAX_RETRIES,
        )
