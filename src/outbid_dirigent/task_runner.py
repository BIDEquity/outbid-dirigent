"""
Task runner — executes individual Claude Code tasks.

Extracted from the Executor god class. Handles:
- Building task prompts with context
- Running Claude Code subprocesses
- Parsing results, deviations, summaries
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.plan_schema import Plan, Task
from outbid_dirigent.router import load_state, save_state
from outbid_dirigent.test_manifest import TestManifest


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
        portal_url: str = "",
        execution_id: str = "",
        reporter_token: str = "",
    ):
        self.repo_path = repo_path
        self.spec_content = spec_content
        self.default_model = default_model
        self.default_effort = default_effort
        self.dirigent_dir = repo_path / ".dirigent"
        self.summaries_dir = self.dirigent_dir / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        # Portal connection for hooks
        self.portal_url = portal_url
        self.execution_id = execution_id
        self.reporter_token = reporter_token
        # Current task context for hooks
        self._current_task_id: Optional[str] = None
        self._current_phase: Optional[int] = None
        # Discover spec images in .planning/assets/
        self.spec_images = self._discover_spec_images()

    def set_task_context(self, task_id: Optional[str] = None, phase: Optional[int] = None):
        """Set current task context for hook environment variables."""
        if task_id is not None:
            self._current_task_id = task_id
        if phase is not None:
            self._current_phase = phase

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

        # Inject bundled plugin for session recall skills
        plugin_dir = Path(__file__).parent / "plugin"
        if plugin_dir.exists():
            cmd.extend(["--plugin-dir", str(plugin_dir)])

        cmd.extend(["-p", prompt])

        # Clean env: strip venv vars so subprocess uses target repo's venv
        clean_env = {
            k: v for k, v in os.environ.items()
            if k not in ("VIRTUAL_ENV", "CONDA_PREFIX", "CONDA_DEFAULT_ENV")
        }
        # Remove any venv bin/ dirs from PATH
        if "VIRTUAL_ENV" in os.environ:
            venv_bin = str(Path(os.environ["VIRTUAL_ENV"]) / "bin")
            clean_env["PATH"] = os.pathsep.join(
                p for p in clean_env.get("PATH", "").split(os.pathsep)
                if p != venv_bin
            )

        # Add portal connection info for hooks
        if self.portal_url and self.execution_id and self.reporter_token:
            clean_env["OUTBID_PORTAL_URL"] = self.portal_url
            clean_env["OUTBID_EXECUTION_ID"] = self.execution_id
            clean_env["OUTBID_REPORTER_TOKEN"] = self.reporter_token
            if self._current_task_id:
                clean_env["OUTBID_CURRENT_TASK_ID"] = self._current_task_id
            if self._current_phase is not None:
                clean_env["OUTBID_CURRENT_PHASE"] = str(self._current_phase)

        # Set hook log directory to match where Executor looks for events
        # This ensures hooks write to {repo}/.dirigent/hooks/events.jsonl
        clean_env["DIRIGENT_HOOK_LOG_DIR"] = str(self.dirigent_dir / "hooks")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=clean_env,
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

    # ── Session recall ──

    def _recall_from_sessions(self, max_chars: int = 2000) -> str:
        """Query past Claude session logs via DuckDB for lessons learned."""
        try:
            duckdb_check = subprocess.run(
                ["which", "duckdb"], capture_output=True, text=True, timeout=5,
            )
            if duckdb_check.returncode != 0:
                return ""

            # Build the project path pattern for session logs
            project_key = str(self.repo_path).replace("/", "-").replace("_", "-")
            search_path = Path.home() / ".claude" / "projects" / project_key / "*.jsonl"
            if not any(search_path.parent.glob("*.jsonl")):
                # Try with leading dash (Claude's format)
                project_key = "-" + project_key.lstrip("-")
                search_path = Path.home() / ".claude" / "projects" / project_key / "*.jsonl"
                if not any(search_path.parent.glob("*.jsonl")):
                    return ""

            query = f"""
SELECT DISTINCT
  regexp_replace(
    regexp_extract(message.content::VARCHAR, 'DEVIATION:\\s*(\\S+[-\\w]*)\\s*[-—]?\\s*([^\\n\"]+)', 0),
    '^DEVIATION:\\s*', ''
  ) AS deviation
FROM read_ndjson('{search_path}', auto_detect=true, ignore_errors=true, filename=true)
WHERE message.role = 'assistant'
  AND message.content::VARCHAR LIKE '%DEVIATION:%'
  AND length(regexp_extract(message.content::VARCHAR, 'DEVIATION:\\s*\\S+[-\\w]*\\s*[-—]?\\s*([^\\n\"]+)', 1)) > 5
ORDER BY 1
LIMIT 30;
"""
            result = subprocess.run(
                ["duckdb", ":memory:", "-csv", "-c", query],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return ""

            lines = []
            for l in result.stdout.strip().splitlines()[1:]:
                l = l.strip().strip('"')
                # Clean up escape sequences and truncate at first newline
                l = l.replace("\\n", " ").replace('\\"', '"')
                l = l.split("DEVIATION:")[0].strip() if "DEVIATION:" in l[20:] else l
                l = l[:150].strip()
                if len(l) > 10:
                    lines.append(l)
            if not lines:
                return ""

            # Deduplicate similar entries
            seen = set()
            unique = []
            for line in lines:
                key = line[:50].lower()
                if key not in seen:
                    seen.add(key)
                    unique.append(line)

            recall = "\n".join(f"- {l}" for l in unique[:15])
            return recall[:max_chars]
        except Exception:
            return ""

    # ── Prompt assembly ──

    def _build_prompt(self, task: Task, plan: Plan) -> str:
        """Assemble the full prompt for a task."""
        previous_summaries = self._load_previous_summaries()
        recent_diff = self._get_recent_diff()
        run_files = self._get_run_file_list()
        business_rules = self._load_business_rules()

        sections = [f"<task id=\"{task.id}\">{task.name}</task>"]

        # Plan position
        pos = plan.task_position(task.id)
        if pos:
            sections.append(f"<plan-position task=\"{pos['index']}/{pos['total']}\" phase=\"{pos['phase_id']}/{pos['total_phases']}\" phase-name=\"{pos['phase_name']}\">")
            if "prev_id" in pos:
                sections.append(f"<prev-task id=\"{pos['prev_id']}\">{pos['prev_name']}</prev-task>")
            if "next_id" in pos:
                sections.append(f"<next-task id=\"{pos['next_id']}\">{pos['next_name']}</next-task>")
            sections.append("</plan-position>")

        # Assumptions & out of scope
        if plan.assumptions:
            sections.append("<assumptions>\n" + "\n".join(f"- {a}" for a in plan.assumptions) + "\n</assumptions>")
        if plan.out_of_scope:
            sections.append("<out-of-scope>\n" + "\n".join(f"- {x}" for x in plan.out_of_scope) + "\n</out-of-scope>")

        # Spec
        sections.append(f"<spec>\n{self.spec_content}\n</spec>")

        # Reference spec images if available
        if self.spec_images:
            img_list = "\n".join(f"- .planning/assets/{img.name}" for img in self.spec_images)
            sections.append(f"<visual-references hint=\"nutze Read tool um sie zu betrachten\">\n{img_list}\n</visual-references>")

        # Progress
        sections.append(f"<previous-progress>\n{previous_summaries}\n</previous-progress>")

        # Recent changes
        if recent_diff:
            sections.append(f"<recent-changes hint=\"was vorherige Tasks gemacht haben\">\n{recent_diff}\n</recent-changes>")
        if run_files:
            sections.append(f"<files-changed-this-run>\n{run_files}\n</files-changed-this-run>")

        # Task description
        sections.append(f"<your-task>\n<description>{task.description}</description>")
        sections.append(f"<files-to-create>{', '.join(task.files_to_create) or 'keine'}</files-to-create>")
        sections.append(f"<files-to-modify>{', '.join(task.files_to_modify) or 'keine'}</files-to-modify>")
        sections.append("</your-task>")

        # Business rules
        if business_rules:
            sections.append(f"<business-rules hint=\"MUESSEN erhalten bleiben!\">\n{business_rules[:2000]}\n</business-rules>")

        # Test manifest context
        manifest = TestManifest.load(self.repo_path)
        if manifest:
            sections.append(f"\n{manifest.summary_for_task(task.test_level)}")

        # Session recall — lessons from past runs
        recall = self._recall_from_sessions()
        if recall:
            sections.append(f"""<session-recall hint="Bekannte Probleme aus frueheren Runs — pruefe ob relevant und vermeide proaktiv">
{recall}
</session-recall>""")

        # Init environment context (e2e framework, services, ports)
        init_env_file = self.dirigent_dir / "init-env.json"
        if init_env_file.exists():
            try:
                import json
                init_env = json.loads(init_env_file.read_text(encoding="utf-8"))
                if init_env.get("e2e_framework"):
                    sections.append(f"""<e2e-environment>
<framework>{init_env['e2e_framework']}</framework>
<config-file>{init_env.get('e2e_config_file', 'unknown')}</config-file>
<auth-setup>{'yes' if init_env.get('e2e_has_auth') else 'no'}</auth-setup>
<ports>{', '.join(str(p) for p in init_env.get('ports_listening', []))}</ports>
</e2e-environment>""")
            except Exception:
                pass

        # Contract context (acceptance criteria for current phase)
        phase_pos = plan.task_position(task.id)
        if phase_pos:
            from outbid_dirigent.contract_schema import Contract
            contract = Contract.load(
                self.dirigent_dir / "contracts" / f"phase-{phase_pos['phase_id']}.json"
            )
            if contract:
                sections.append(
                    f"<phase-contract hint=\"dein Task muss zu diesen Kriterien beitragen\">\n"
                    f"{contract.summary_for_prompt()}\n"
                    f"</phase-contract>"
                )

        # Summary format hint (deviation rules are in system prompt)
        sections.append(f"""<output-instructions>
Erstelle .dirigent/summaries/{task.id}-SUMMARY.md mit:
- Was wurde gemacht
- Geaenderte Dateien
- Deviations (falls vorhanden)
- Naechste Schritte (falls relevant)
</output-instructions>""")

        return "\n".join(sections)

    # ── Task execution ──

    def run_task(self, task: Task, plan: Plan, phase_num: int | str = 1) -> TaskResult:
        """Execute a single task with retries."""
        start_time = datetime.now()
        context = self._build_prompt(task, plan)

        # The prompt tells Claude to follow /dirigent:execute-task, then provides
        # all the task context. The skill is loaded natively by the subprocess
        # via the --plugin-dir flag.
        prompt = f"/dirigent:execute-task\n\n{context}"

        # Per-task model/effort override
        task_model = task.model or self.default_model
        task_effort = task.effort or self.default_effort

        for attempt in range(1, self.MAX_RETRIES + 1):
            if attempt > 1:
                logger.info(f"Task {task.id} retry {attempt}/{self.MAX_RETRIES}")

            success, stdout, stderr = self._run_claude(
                prompt, model=task_model, effort=task_effort,
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
