"""
Progress & Plan output tools — console and text format renderers.

Provides formatted output for:
- Execution progress (phases, tasks, status)
- Plan display (structured view of PLAN.json)
- Contract status tracking
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from outbid_dirigent.contract_schema import Contract, Review, Verdict
from outbid_dirigent.plan_schema import Plan
from outbid_dirigent.router import load_state, load_route


class ProgressRenderer:
    """Renders execution progress in console and text formats."""

    # Progress bar characters
    FILLED = "\u2588"  # █
    EMPTY = "\u2591"   # ░

    # Status icons
    ICONS = {
        "done": "\u2705",       # ✅
        "current": "\U0001f528", # 🔨
        "pending": "\u23f3",    # ⏳
        "failed": "\u274c",     # ❌
        "contract_pass": "\U0001f4cb PASS",  # 📋
        "contract_fail": "\U0001f4cb FAIL",
        "contract_pending": "\U0001f4cb PENDING",
    }

    def __init__(self, repo_path: str | Path, dirigent_dir: Optional[Path] = None):
        self.repo_path = Path(repo_path)
        self.dirigent_dir = dirigent_dir or (self.repo_path / ".dirigent")

    def _load_data(self) -> tuple[Optional[Plan], dict, Optional[dict]]:
        """Load plan, state, and route data."""
        plan = Plan.load(self.dirigent_dir / "PLAN.json")
        state = load_state(str(self.repo_path), dirigent_dir=self.dirigent_dir) or {
            "completed_phases": [], "completed_tasks": [], "failed_tasks": [],
        }
        route = load_route(str(self.repo_path), dirigent_dir=self.dirigent_dir)
        return plan, state, route

    def _get_contract_status(self, phase_id: str) -> str:
        """Check contract status for a phase using structured JSON."""
        review = Review.load(self.dirigent_dir / "reviews" / f"phase-{phase_id}.json")
        if review:
            return review.verdict.value  # "pass" or "fail"

        contract = Contract.load(self.dirigent_dir / "contracts" / f"phase-{phase_id}.json")
        if contract:
            return "pending"

        return "none"

    def _count_deviations(self) -> int:
        """Count total deviations from summaries."""
        summaries_dir = self.dirigent_dir / "summaries"
        if not summaries_dir.exists():
            return 0
        count = 0
        for f in summaries_dir.glob("*-SUMMARY.md"):
            content = f.read_text(encoding="utf-8")
            count += content.lower().count("deviation:")
        return count

    def _count_reviews(self) -> tuple[int, int]:
        """Count pass/fail reviews from structured JSON."""
        reviews_dir = self.dirigent_dir / "reviews"
        if not reviews_dir.exists():
            return 0, 0
        passes = fails = 0
        for f in reviews_dir.glob("phase-*.json"):
            review = Review.load(f)
            if review:
                if review.verdict == Verdict.PASS:
                    passes += 1
                else:
                    fails += 1
        return passes, fails

    def _duration_str(self, state: dict) -> str:
        """Get duration string from state."""
        started = state.get("started_at")
        if not started:
            return "—"
        try:
            start = datetime.fromisoformat(started)
            elapsed = datetime.now() - start
            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)
            return f"{minutes}m {seconds:02d}s"
        except (ValueError, TypeError):
            return "—"

    def _progress_bar(self, completed: int, total: int, width: int = 12) -> str:
        """Create a progress bar."""
        if total == 0:
            return self.EMPTY * width
        filled = int(width * completed / total)
        return self.FILLED * filled + self.EMPTY * (width - filled)

    # ── Console format ──

    def console(self) -> str:
        """Render full console progress display."""
        plan, state, route = self._load_data()

        if not plan:
            return "No plan found. Run planning phase first."

        completed_tasks = set(state.get("completed_tasks", []))
        completed_phases = set(state.get("completed_phases", []))
        failed_task_ids = {t["task_id"] for t in state.get("failed_tasks", []) if isinstance(t, dict)}

        total_tasks = plan.total_tasks
        done_tasks = len(completed_tasks)

        route_type = route.get("route", "unknown") if route else "unknown"
        deviations = self._count_deviations()
        review_pass, review_fail = self._count_reviews()
        duration = self._duration_str(state)

        lines = [
            "\u2550" * 55,
            "  OUTBID DIRIGENT \u2014 Progress Report",
            "\u2550" * 55,
            "",
            f"  Route: {route_type}",
            f"  Plan:  \"{plan.title}\" ({len(plan.phases)} phases, {total_tasks} tasks)",
            "",
        ]

        # Find current task
        current_task_id = None
        for phase in plan.phases:
            for task in phase.tasks:
                if task.id not in completed_tasks and task.id not in failed_task_ids:
                    current_task_id = task.id
                    break
            if current_task_id:
                break

        for phase in plan.phases:
            phase_done = phase.id in completed_phases
            phase_tasks_done = sum(1 for t in phase.tasks if t.id in completed_tasks)

            if phase_done:
                status = "DONE"
            elif any(t.id in completed_tasks or t.id == current_task_id for t in phase.tasks):
                status = "IN PROGRESS"
            else:
                status = "PENDING"

            bar = self._progress_bar(phase_tasks_done, len(phase.tasks))
            lines.append(f"  Phase {phase.id}: {phase.name:<30} {bar} {status}")

            for task in phase.tasks:
                if task.id in completed_tasks:
                    icon = self.ICONS["done"]
                elif task.id in failed_task_ids:
                    icon = self.ICONS["failed"]
                elif task.id == current_task_id:
                    icon = self.ICONS["current"]
                else:
                    icon = self.ICONS["pending"]

                suffix = "    \u2190 current" if task.id == current_task_id else ""
                lines.append(f"    {icon} {task.id}  {task.name}{suffix}")

            # Contract status
            contract_status = self._get_contract_status(phase.id)
            if contract_status != "none":
                icon_key = f"contract_{contract_status}"
                lines.append(f"    {self.ICONS.get(icon_key, contract_status)}")

            lines.append("")

        # Summary line
        pct = int(100 * done_tasks / total_tasks) if total_tasks > 0 else 0
        phases_done = len(completed_phases)
        lines.extend([
            "\u2500" * 55,
            f"  Progress: {done_tasks}/{total_tasks} tasks ({pct}%) | {phases_done}/{len(plan.phases)} phases done",
            f"  Deviations: {deviations} | Reviews: {review_pass} pass, {review_fail} fail",
            f"  Duration: {duration}",
            "\u2550" * 55,
        ])

        return "\n".join(lines)

    # ── Text format ──

    def text(self) -> str:
        """Render compact text progress (one line)."""
        plan, state, route = self._load_data()
        if not plan:
            return "No plan found."

        completed_tasks = set(state.get("completed_tasks", []))
        completed_phases = set(state.get("completed_phases", []))
        total_tasks = plan.total_tasks
        done_tasks = len(completed_tasks)
        pct = int(100 * done_tasks / total_tasks) if total_tasks > 0 else 0
        duration = self._duration_str(state)
        deviations = self._count_deviations()

        # Find current task
        current_desc = "idle"
        for phase in plan.phases:
            for task in phase.tasks:
                if task.id not in completed_tasks:
                    current_desc = f'Phase {phase.id} "{phase.name}" \u2014 Task {task.id} "{task.name}"'
                    break
            else:
                continue
            break

        route_type = route.get("route", "?") if route else "?"
        return (
            f"Progress: {done_tasks}/{total_tasks} tasks ({pct}%), "
            f"{len(completed_phases)}/{len(plan.phases)} phases complete | "
            f"Current: {current_desc} | "
            f"Route: {route_type} | Duration: {duration} | Deviations: {deviations}"
        )

    # ── JSON format ──

    def to_json(self) -> dict:
        """Render progress as structured dict."""
        plan, state, route = self._load_data()
        if not plan:
            return {"error": "No plan found"}

        completed_tasks = set(state.get("completed_tasks", []))
        completed_phases = set(state.get("completed_phases", []))

        phases = []
        for phase in plan.phases:
            tasks = []
            for task in phase.tasks:
                status = "completed" if task.id in completed_tasks else "pending"
                tasks.append({"id": task.id, "name": task.name, "status": status})
            phases.append({
                "id": phase.id,
                "name": phase.name,
                "status": "completed" if phase.id in completed_phases else "pending",
                "contract": self._get_contract_status(phase.id),
                "tasks": tasks,
            })

        return {
            "title": plan.title,
            "route": route.get("route") if route else None,
            "total_tasks": plan.total_tasks,
            "completed_tasks": len(completed_tasks),
            "total_phases": len(plan.phases),
            "completed_phases": len(completed_phases),
            "deviations": self._count_deviations(),
            "duration": self._duration_str(state),
            "phases": phases,
        }


class PlanRenderer:
    """Renders PLAN.json in console and text formats."""

    def __init__(self, repo_path: str | Path, dirigent_dir: Optional[Path] = None):
        self.repo_path = Path(repo_path)
        self.dirigent_dir = dirigent_dir or (self.repo_path / ".dirigent")

    def console(self) -> str:
        """Render full console plan display."""
        plan = Plan.load(self.dirigent_dir / "PLAN.json")
        if not plan:
            return "No plan found."

        lines = [
            "\u2550" * 55,
            f"  PLAN: {plan.title}",
            "\u2550" * 55,
            "",
            f"  Summary: {plan.summary}",
            f"  Complexity: {plan.estimated_complexity}",
            f"  Phases: {len(plan.phases)} | Tasks: {plan.total_tasks}",
            "",
        ]

        for phase in plan.phases:
            lines.append(f"  \u2500\u2500\u2500 Phase {phase.id}: {phase.name} \u2500\u2500\u2500")
            if phase.description:
                lines.append(f"  {phase.description}")
            lines.append("")

            for task in phase.tasks:
                model_tag = task.model or "sonnet"
                effort_tag = task.effort or "medium"
                lines.append(f"    {task.id}  {task.name:<36} [{model_tag}/{effort_tag}]")
                if task.description:
                    # Wrap description to ~70 chars
                    desc = task.description[:100]
                    lines.append(f"           {desc}")
                if task.files_to_create:
                    lines.append(f"           Create: {', '.join(task.files_to_create)}")
                if task.files_to_modify:
                    lines.append(f"           Modify: {', '.join(task.files_to_modify)}")
                lines.append("")

        if plan.assumptions:
            lines.append("  Assumptions:")
            for a in plan.assumptions:
                lines.append(f"    \u2022 {a}")
            lines.append("")

        if plan.out_of_scope:
            lines.append("  Out of Scope:")
            for x in plan.out_of_scope:
                lines.append(f"    \u2022 {x}")
            lines.append("")

        if plan.risks:
            lines.append("  Risks:")
            for r in plan.risks:
                lines.append(f"    \u26a0 {r}")
            lines.append("")

        lines.append("\u2550" * 55)
        return "\n".join(lines)

    def text(self) -> str:
        """Render compact text plan."""
        plan = Plan.load(self.dirigent_dir / "PLAN.json")
        if not plan:
            return "No plan found."

        lines = [f"Plan: {plan.title} ({len(plan.phases)} phases, {plan.total_tasks} tasks)"]
        for phase in plan.phases:
            lines.append(f"  Phase {phase.id}: {phase.name}")
            for task in phase.tasks:
                lines.append(f"    {task.id}: {task.name} [{task.model or 'sonnet'}]")
        return "\n".join(lines)

    def to_json(self) -> dict:
        """Return raw plan as dict."""
        plan_file = self.dirigent_dir / "PLAN.json"
        if not plan_file.exists():
            return {"error": "No plan found"}
        return json.loads(plan_file.read_text(encoding="utf-8"))


def print_progress(repo_path: str, fmt: str = "console", dirigent_dir: Optional[Path] = None) -> str:
    """Print progress in the given format. Returns the formatted string."""
    renderer = ProgressRenderer(repo_path, dirigent_dir=dirigent_dir)
    if fmt == "json":
        return json.dumps(renderer.to_json(), indent=2, ensure_ascii=False)
    elif fmt == "text":
        return renderer.text()
    return renderer.console()


def print_plan(repo_path: str, fmt: str = "console", dirigent_dir: Optional[Path] = None) -> str:
    """Print plan in the given format. Returns the formatted string."""
    renderer = PlanRenderer(repo_path, dirigent_dir=dirigent_dir)
    if fmt == "json":
        return json.dumps(renderer.to_json(), indent=2, ensure_ascii=False)
    elif fmt == "text":
        return renderer.text()
    return renderer.console()
