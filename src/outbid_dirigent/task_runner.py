"""
Task runner — executes individual Claude Code tasks.

Extracted from the Executor god class. Handles:
- Building task prompts with context
- Running Claude Code subprocesses
- Parsing results, deviations, summaries
"""

import asyncio
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from claude_agent_sdk import query
from claude_agent_sdk.types import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

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
        portal_url: str = "",
        execution_id: str = "",
        reporter_token: str = "",
        dirigent_dir: Optional[Path] = None,
    ):
        self.repo_path = repo_path
        self.spec_content = spec_content
        self.default_model = default_model
        self.default_effort = default_effort
        self.dirigent_dir = dirigent_dir or (repo_path / ".dirigent")
        self.summaries_dir = self.dirigent_dir / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        # Portal connection for hooks
        self.portal_url = portal_url
        self.execution_id = execution_id
        self.reporter_token = reporter_token
        # Current task context for hooks
        self._current_task_id: Optional[str] = None
        self._current_phase: Optional[int] = None
        # OpenCode bridge — set by Executor if .opencode/ exists
        self.opencode_plugin_dir: Optional[Path] = None
        self.opencode_skill_catalog: list[dict] = []
        self.opencode_plugin_name: str = ""
        # BRV context-tree bridge — set by Executor if .brv/context-tree/ exists
        self.brv_bridge = None
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

    async def _aquery_claude(
        self,
        prompt: str,
        timeout: int = 0,
        model: str = "",
        effort: str = "",
        system_prompt: str = "",
        output_format: dict | None = None,
        agents: dict[str, AgentDefinition] | None = None,
    ) -> tuple[bool, str, str, dict | None]:
        """Async query via claude_agent_sdk. Returns (success, result_text, error_text, structured_output)."""
        timeout = timeout or self.DEFAULT_TIMEOUT
        model = model or self.default_model
        effort = effort or self.default_effort

        run_dir_hint = (
            f"DIRIGENT_RUN_DIR={self.dirigent_dir} — "
            f"all dirigent artifacts (PLAN.json, SPEC.md, contracts/, reviews/, summaries/, test-harness.json) "
            f"live here, NOT in .dirigent/ in the repo."
        )
        append_text = f"{run_dir_hint}\n\n{system_prompt}" if system_prompt else run_dir_hint

        # Clean env: strip venv vars so subprocess uses target repo's venv
        clean_env = {
            k: v for k, v in os.environ.items()
            if k not in ("VIRTUAL_ENV", "CONDA_PREFIX", "CONDA_DEFAULT_ENV")
        }
        if "VIRTUAL_ENV" in os.environ:
            venv_bin = str(Path(os.environ["VIRTUAL_ENV"]) / "bin")
            clean_env["PATH"] = os.pathsep.join(
                p for p in clean_env.get("PATH", "").split(os.pathsep) if p != venv_bin
            )
        clean_env["DIRIGENT_HOOK_LOG_DIR"] = str(self.dirigent_dir / "hooks")
        clean_env["DIRIGENT_RUN_DIR"] = str(self.dirigent_dir)
        if self.portal_url and self.execution_id and self.reporter_token:
            clean_env["OUTBID_PORTAL_URL"] = self.portal_url
            clean_env["OUTBID_EXECUTION_ID"] = self.execution_id
            clean_env["OUTBID_REPORTER_TOKEN"] = self.reporter_token
            if self._current_task_id:
                clean_env["OUTBID_CURRENT_TASK_ID"] = self._current_task_id
            if self._current_phase is not None:
                clean_env["OUTBID_CURRENT_PHASE"] = str(self._current_phase)

        # Build plugins list
        plugins: list[dict] = []
        plugin_dir = Path(__file__).parent / "plugin"
        if plugin_dir.exists():
            plugins.append({"type": "local", "path": str(plugin_dir)})
        if self.opencode_plugin_dir:
            plugins.append({"type": "local", "path": str(self.opencode_plugin_dir)})

        # "Agent" is always needed: plugin agents (contract-negotiator, reviewer, implementer)
        # are available whenever plugins are loaded — they must not be passed inline.
        allowed_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"]
        if plugins:
            allowed_tools.append("Agent")

        options = ClaudeAgentOptions(
            model=model or None,
            effort=effort or None,
            cwd=str(self.repo_path),
            env=clean_env,
            plugins=plugins,
            allowed_tools=allowed_tools,
            permission_mode="bypassPermissions",
            system_prompt={"type": "preset", "preset": "claude_code", "append": append_text},
            output_format=output_format,
            agents=agents,
        )

        result_text = ""
        error_text = ""
        structured: dict | None = None

        async def _consume():
            nonlocal result_text, error_text, structured
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock) and block.text.strip():
                            logger.debug(f"[claude:text] {block.text[:300]}")
                        elif isinstance(block, ToolUseBlock):
                            logger.debug(f"[claude:tool] {block.name}({str(block.input)[:120]})")
                elif isinstance(message, ResultMessage):
                    if message.is_error:
                        error_text = message.result or "Unknown error"
                        logger.info(f"[claude:error] {error_text[:500]}")
                    else:
                        result_text = message.result or ""
                        structured = message.structured_output
                        logger.info(f"[claude:result] {result_text[:500]}")

        try:
            await asyncio.wait_for(_consume(), timeout=timeout)
            return True, result_text, error_text, structured
        except asyncio.TimeoutError:
            error_text = f"Timeout after {timeout}s"
            logger.error(f"[claude:timeout] {error_text}")
            return False, "", error_text, None
        except Exception as e:
            error_text = str(e)
            logger.error(f"[claude:error] {error_text}")
            return False, "", error_text, None

    def _run_claude(
        self,
        prompt: str,
        timeout: int = 0,
        model: str = "",
        effort: str = "",
        system_prompt: str = "",
    ) -> tuple[bool, str, str]:
        """Run Claude Code with a prompt. Returns (success, stdout, stderr)."""
        success, stdout, stderr, _ = asyncio.run(
            self._aquery_claude(prompt, timeout=timeout, model=model,
                                effort=effort, system_prompt=system_prompt)
        )
        return success, stdout, stderr

    def _run_claude_structured(
        self,
        prompt: str,
        output_format: dict,
        timeout: int = 0,
        model: str = "",
        effort: str = "",
        system_prompt: str = "",
        agents: dict | None = None,
    ) -> tuple[bool, dict | None]:
        """Run Claude Code and return structured output. Returns (success, structured_dict)."""
        success, _, stderr, structured = asyncio.run(
            self._aquery_claude(prompt, timeout=timeout, model=model,
                                effort=effort, system_prompt=system_prompt,
                                output_format=output_format, agents=agents)
        )
        if not success or structured is None:
            logger.error(f"Structured query failed: {stderr[:200]}")
            return False, None
        return True, structured

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

    def _compact_spec_has_rules(self) -> bool:
        """Check if the CompactSpec already contains business rules."""
        compact_path = self.dirigent_dir / "SPEC.compact.json"
        if not compact_path.exists():
            return False
        try:
            import json
            data = json.loads(compact_path.read_text(encoding="utf-8"))
            return bool(data.get("business_rules"))
        except Exception:
            return False

    def _build_convention_skills_block(self, task: "Task") -> Optional[str]:
        """Build <convention-skills> block telling the agent which skills to load.

        Uses task.convention_skills if the planner tagged the task.
        Falls back to full catalog if not tagged.
        """
        if not self.opencode_skill_catalog:
            return None

        plugin = self.opencode_plugin_name

        # Use planner-tagged skills if available, otherwise full skill catalog
        if task.convention_skills:
            catalog_by_name = {s["name"]: s for s in self.opencode_skill_catalog}
            relevant = [
                catalog_by_name[name]
                for name in task.convention_skills
                if name in catalog_by_name
            ]
        else:
            # Fallback: include all skills (let the agent decide)
            relevant = [s for s in self.opencode_skill_catalog if s["type"] == "skill"]

        if not relevant:
            return None

        lines = ['<convention-skills hint="load these skills BEFORE writing any code">']
        for skill in relevant:
            desc = skill["description"][:100] if skill["description"] else ""
            lines.append(f"- {skill['name']}: {desc}")
        lines.append("")
        lines.append(f"Load with: /{plugin}:{relevant[0]['name']}  (replace skill name as needed)")
        lines.append("</convention-skills>")
        return "\n".join(lines)

    def _load_architecture_section(self, tag: str, max_chars: int = 6000) -> Optional[str]:
        """Extract an XML-tagged section from ARCHITECTURE.md."""
        arch_file = self.repo_path / "ARCHITECTURE.md"
        if not arch_file.exists():
            return None
        content = arch_file.read_text(encoding="utf-8")
        import re
        match = re.search(rf"<{tag}>(.*?)</{tag}>", content, re.DOTALL)
        if not match:
            return None
        section = match.group(1).strip()
        if len(section) > max_chars:
            section = section[:max_chars] + "\n... (truncated)"
        return section

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
        state = load_state(str(self.repo_path), dirigent_dir=self.dirigent_dir)
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

            # Extract DEVIATION, LESSON, and WARNING markers from past sessions
            query = f"""
WITH raw AS (
  SELECT
    regexp_extract(message.content::VARCHAR, '(DEVIATION|LESSON|WARNING):\\s*(\\S+[-\\w]*)\\s*[-—]?\\s*([^\\n\"]+)', 0) AS marker,
    regexp_extract(message.content::VARCHAR, '(DEVIATION|LESSON|WARNING):', 1) AS kind
  FROM read_ndjson('{search_path}', auto_detect=true, ignore_errors=true, filename=true)
  WHERE message.role = 'assistant'
    AND (
      message.content::VARCHAR LIKE '%DEVIATION:%'
      OR message.content::VARCHAR LIKE '%LESSON:%'
      OR message.content::VARCHAR LIKE '%WARNING:%'
    )
)
SELECT DISTINCT kind, regexp_replace(marker, '^(DEVIATION|LESSON|WARNING):\\s*', '') AS entry
FROM raw
WHERE length(entry) > 5
ORDER BY kind, entry
LIMIT 45;
"""
            result = subprocess.run(
                ["duckdb", ":memory:", "-csv", "-c", query],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return ""

            tagged: dict[str, list[str]] = {"DEVIATION": [], "LESSON": [], "WARNING": []}
            for row in result.stdout.strip().splitlines()[1:]:
                parts = row.strip().split(",", 1)
                if len(parts) != 2:
                    continue
                kind, entry = parts[0].strip().strip('"'), parts[1].strip().strip('"')
                entry = entry.replace("\\n", " ").replace('\\"', '"')[:150].strip()
                if len(entry) > 10 and kind in tagged:
                    tagged[kind].append(entry)

            # Deduplicate within each category using word-set overlap
            def dedupe(entries: list[str]) -> list[str]:
                seen_sets: list[set] = []
                unique = []
                for entry in entries:
                    words = set(entry.lower().split())
                    if not any(len(words & s) / max(len(words | s), 1) > 0.6 for s in seen_sets):
                        seen_sets.append(words)
                        unique.append(entry)
                return unique

            lines = []
            for kind, prefix in [("LESSON", "lesson"), ("WARNING", "warning"), ("DEVIATION", "deviation")]:
                for entry in dedupe(tagged[kind])[:8]:
                    lines.append(f"[{prefix}] {entry}")

            if not lines:
                return ""

            return "\n".join(f"- {l}" for l in lines)[:max_chars]
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

        # Spec — prefer compacted form, fall back to full blob
        spec_block: Optional[str] = None
        compact_path = self.dirigent_dir / "SPEC.compact.json"
        if compact_path.exists():
            try:
                from outbid_dirigent.spec_compactor import CompactSpec
                compact = CompactSpec.model_validate_json(
                    compact_path.read_text(encoding="utf-8")
                )
                # If task has no relevant_req_ids, inject ALL reqs (safe fallback
                # so we never silently drop requirements when the planner forgot
                # to tag a task).
                relevant = set(task.relevant_req_ids) if task.relevant_req_ids else None
                spec_block = compact.render_xml(only_req_ids=relevant)
            except Exception as e:
                logger.warning(
                    f"Compact spec load failed, falling back to full spec: {e}"
                )

        if spec_block is None:
            spec_block = f"<spec>\n{self.spec_content}\n</spec>"
        sections.append(spec_block)

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

        # Convention skills — tell the agent which project-specific skills to load
        skill_block = self._build_convention_skills_block(task)
        if skill_block:
            sections.append(skill_block)
        else:
            # Fallback: inject <key-patterns> from ARCHITECTURE.md
            patterns = self._load_architecture_section("key-patterns")
            if patterns:
                sections.append(f"<key-patterns hint=\"follow these patterns when writing code\">\n{patterns}\n</key-patterns>")

        # Architecture context — testing strategy + architecture decisions from ARCHITECTURE.md
        for tag, hint in [
            ("testing-verification", "follow this test strategy"),
            ("architecture-decisions", "follow these architecture patterns"),
        ]:
            section = self._load_architecture_section(tag, max_chars=3000)
            if section:
                sections.append(f"<{tag} hint=\"{hint}\">\n{section}\n</{tag}>")

        # Business rules — only inject separately if CompactSpec doesn't contain them
        # (CompactSpec now includes business_rules from Proteus extraction)
        if business_rules and not self._compact_spec_has_rules():
            sections.append(f"<business-rules hint=\"MUESSEN erhalten bleiben!\">\n{business_rules[:2000]}\n</business-rules>")

        # Session recall — lessons from past runs
        recall = self._recall_from_sessions()
        if recall:
            sections.append(f"""<session-recall hint="Bekannte Probleme aus frueheren Runs — pruefe ob relevant und vermeide proaktiv">
{recall}
</session-recall>""")

        # BRV domain knowledge
        if self.brv_bridge:
            brv_ctx = self.brv_bridge.context_for_task(task)
            if brv_ctx:
                sections.append(
                    '<knowledge-store hint="domain knowledge from .brv/context-tree/ '
                    '— use /dirigent:query-brv for deeper queries">\n'
                    f'{brv_ctx}\n'
                    '</knowledge-store>'
                )

        # Test harness context (build/test/dev commands, env vars)
        from outbid_dirigent.test_harness_schema import TestHarness
        harness = TestHarness.load(self.dirigent_dir / "test-harness.json")
        if harness:
            sections.append(
                f"<test-harness hint=\"project commands and environment\">\n"
                f"{harness.summary_for_prompt()}\n"
                f"</test-harness>"
            )

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
Erstelle ${{DIRIGENT_RUN_DIR}}/summaries/{task.id}-SUMMARY.md mit:
- Was wurde gemacht
- Geaenderte Dateien
- Deviations (falls vorhanden)
- Naechste Schritte (falls relevant)
</output-instructions>""")

        return "\n".join(sections)

    # ── System prompt for coding agent ──

    AGENT_SYSTEM_PROMPT = (
        "You are the long-term maintainer of this codebase. "
        "Every line you write, you will read again. Every shortcut you take, you will debug later. "
        "Write scalable, maintainable code: clear interfaces, separation of concerns, "
        "dependency injection, no implicit state, test-friendly by construction. "
        "The reviewer will execute real verification commands against your code — "
        "it must actually work end-to-end, not just compile."
    )

    # ── Task execution ──

    def _has_uncommitted_changes(self) -> bool:
        """Check if the working tree has staged or unstaged changes."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return False
            # Filter out dirigent artifacts and untracked files in run dir
            for line in result.stdout.splitlines():
                path = line[3:].strip()
                if not path.startswith(".dirigent/"):
                    return True
            return False
        except Exception:
            return False

    def _auto_commit(self, task: Task) -> Optional[str]:
        """Auto-commit uncommitted changes the agent forgot to commit."""
        msg = f"feat({task.id}): {task.name}\n\n[auto-committed by dirigent — agent forgot to commit]"
        return self._auto_commit_msg(msg)

    def _auto_commit_msg(self, msg: str) -> Optional[str]:
        """Auto-commit with a custom message. Returns new commit hash or None."""
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=10,
            )
            result = subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=self.repo_path, capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return self._get_latest_commit_hash()
            return None
        except Exception as e:
            logger.warning(f"Auto-commit failed: {e}")
            return None

    def run_task(self, task: Task, plan: Plan, phase_num: int | str = 1) -> TaskResult:
        """Execute a single task with retries."""
        start_time = datetime.now()
        context = self._build_prompt(task, plan)

        # The prompt tells Claude to follow /dirigent:implement-task, then provides
        # all the task context. The skill is loaded natively by the subprocess
        # via the --plugin-dir flag.
        prompt = f"/dirigent:implement-task\n\n{context}"

        # Per-task model/effort override
        task_model = task.model or self.default_model
        task_effort = task.effort or self.default_effort

        for attempt in range(1, self.MAX_RETRIES + 1):
            if attempt > 1:
                logger.info(f"Task {task.id} retry {attempt}/{self.MAX_RETRIES}")

            head_before = self._get_latest_commit_hash()

            success, stdout, stderr = self._run_claude(
                prompt, model=task_model, effort=task_effort,
                system_prompt=self.AGENT_SYSTEM_PROMPT,
            )

            if success:
                commit_hash = self._get_latest_commit_hash()

                # Agent forgot to commit — rescue uncommitted work
                if commit_hash == head_before and self._has_uncommitted_changes():
                    logger.warning(f"Task {task.id}: agent did not commit — auto-committing changes")
                    auto_hash = self._auto_commit(task)
                    if auto_hash:
                        commit_hash = auto_hash
                    else:
                        logger.error(f"Task {task.id}: auto-commit failed, changes are uncommitted")

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
