"""
Demo Runner — simulates a full Dirigent execution with fake data.

This module sends realistic events to the portal without actually
running any analysis, planning, or code generation. Useful for:
- Testing the Portal UI
- Demonstrating the system to stakeholders
- Development without API costs
"""

import asyncio
import random
import time
from typing import Optional

from loguru import logger

from outbid_dirigent.portal_reporter import PortalReporter


# ══════════════════════════════════════════════════════════════════════════════
# DEMO DATA - Realistic fake data for a "User Settings Feature"
# ══════════════════════════════════════════════════════════════════════════════

DEMO_SPEC = {
    "title": "User Settings Page",
    "description": "Add a settings page where users can manage their profile and preferences.",
}

DEMO_ANALYSIS = {
    "language": "TypeScript",
    "framework": "Next.js 14",
    "commit_count": 847,
    "file_count": 234,
    "route": "hybrid",
    "confidence": "high",
}

DEMO_ROUTE = {
    "route_type": "hybrid",
    "reason": "Established codebase with clear patterns, feature adds new functionality",
    "steps": ["quick_scan", "planning", "execution", "testing", "shipping"],
    "estimated_tasks": 8,
}

DEMO_PLAN = {
    "phases": [
        {
            "phase": 1,
            "name": "Database & API Setup",
            "description": "Create user settings schema and API endpoints",
            "tasks": [
                {
                    "id": "1.1",
                    "name": "Create user_settings table migration",
                    "description": "Add Supabase migration for user preferences storage",
                },
                {
                    "id": "1.2",
                    "name": "Implement settings API routes",
                    "description": "Create GET/PATCH endpoints for user settings",
                },
            ],
        },
        {
            "phase": 2,
            "name": "Settings UI Components",
            "description": "Build the settings page and form components",
            "tasks": [
                {
                    "id": "2.1",
                    "name": "Create SettingsForm component",
                    "description": "Form with profile fields, theme toggle, notification preferences",
                },
                {
                    "id": "2.2",
                    "name": "Build SettingsPage layout",
                    "description": "Page component with tabs for different setting categories",
                },
                {
                    "id": "2.3",
                    "name": "Add settings navigation link",
                    "description": "Add link to settings in user dropdown menu",
                },
            ],
        },
        {
            "phase": 3,
            "name": "Integration & Polish",
            "description": "Connect components, add validation, and polish UX",
            "tasks": [
                {
                    "id": "3.1",
                    "name": "Wire up form submission",
                    "description": "Connect SettingsForm to API with optimistic updates",
                },
                {
                    "id": "3.2",
                    "name": "Add form validation",
                    "description": "Client-side validation with zod schema",
                },
                {
                    "id": "3.3",
                    "name": "Add success/error toasts",
                    "description": "User feedback for save operations",
                },
            ],
        },
    ],
    "total_tasks": 8,
}

# Fake file operations per task
DEMO_TASK_ACTIVITIES = {
    "1.1": {
        "thinking": [
            "Analyzing existing migration patterns...",
            "Designing user_settings schema with JSONB preferences column...",
        ],
        "files": [
            {"path": "supabase/migrations/20240315_user_settings.sql", "action": "create"},
            {"path": "src/lib/supabase/types.ts", "action": "write", "lines": 15},
        ],
        "bash": ["supabase db push --dry-run"],
        "commit": "feat(db): add user_settings table migration",
    },
    "1.2": {
        "thinking": [
            "Reviewing existing API route patterns...",
            "Implementing GET endpoint with auth check...",
            "Adding PATCH endpoint with validation...",
        ],
        "files": [
            {"path": "src/app/api/user/settings/route.ts", "action": "create"},
            {"path": "src/lib/validations/settings.ts", "action": "create"},
        ],
        "bash": ["npm run typecheck"],
        "commit": "feat(api): add user settings endpoints",
    },
    "2.1": {
        "thinking": [
            "Checking existing form component patterns...",
            "Creating form with react-hook-form...",
            "Adding theme toggle with next-themes...",
        ],
        "files": [
            {"path": "src/components/settings/settings-form.tsx", "action": "create"},
            {"path": "src/components/ui/switch.tsx", "action": "read"},
            {"path": "src/components/settings/settings-form.tsx", "action": "write", "lines": 45},
        ],
        "bash": [],
        "commit": "feat(ui): create SettingsForm component",
    },
    "2.2": {
        "thinking": [
            "Designing page layout with tabs...",
            "Using existing Tab component from shadcn...",
        ],
        "files": [
            {"path": "src/app/(dashboard)/settings/page.tsx", "action": "create"},
            {"path": "src/app/(dashboard)/settings/layout.tsx", "action": "create"},
        ],
        "bash": [],
        "commit": "feat(ui): add settings page with tabbed layout",
    },
    "2.3": {
        "thinking": [
            "Finding user dropdown component...",
            "Adding settings link with icon...",
        ],
        "files": [
            {"path": "src/components/nav/user-menu.tsx", "action": "read"},
            {"path": "src/components/nav/user-menu.tsx", "action": "write", "lines": 8},
        ],
        "bash": [],
        "commit": "feat(nav): add settings link to user menu",
    },
    "3.1": {
        "thinking": [
            "Implementing useMutation hook for settings...",
            "Adding optimistic update logic...",
        ],
        "files": [
            {"path": "src/hooks/use-settings.ts", "action": "create"},
            {"path": "src/components/settings/settings-form.tsx", "action": "write", "lines": 25},
        ],
        "bash": ["npm run typecheck"],
        "commit": "feat: wire up settings form submission",
    },
    "3.2": {
        "thinking": [
            "Creating zod schema for settings validation...",
            "Adding client-side validation to form...",
        ],
        "files": [
            {"path": "src/lib/validations/settings.ts", "action": "write", "lines": 30},
            {"path": "src/components/settings/settings-form.tsx", "action": "write", "lines": 12},
        ],
        "bash": [],
        "commit": "feat: add form validation with zod",
    },
    "3.3": {
        "thinking": [
            "Adding toast notifications for feedback...",
            "Handling error states gracefully...",
        ],
        "files": [
            {"path": "src/components/settings/settings-form.tsx", "action": "write", "lines": 18},
        ],
        "bash": ["npm run build"],
        "commit": "feat: add success/error toast notifications",
    },
}

DEMO_SUMMARY = {
    "markdown": """## Summary

Successfully implemented the User Settings feature with the following changes:

### What was built
- **Database**: New `user_settings` table with JSONB preferences column
- **API**: GET/PATCH endpoints at `/api/user/settings` with auth & validation
- **UI**: Settings page with tabbed layout (Profile, Preferences, Notifications)
- **UX**: Form validation, optimistic updates, toast notifications

### Key Decisions
1. Used JSONB for preferences to allow flexible schema evolution
2. Implemented optimistic updates for snappy UX
3. Added zod validation on both client and server

### Test Instructions
1. Log in as any user
2. Navigate to Settings via user menu dropdown
3. Update profile information and verify save
4. Toggle theme and verify persistence
5. Check notification preferences save correctly
""",
    "files_changed": [
        {"path": "supabase/migrations/20240315_user_settings.sql", "lines_added": 25, "lines_removed": 0},
        {"path": "src/app/api/user/settings/route.ts", "lines_added": 67, "lines_removed": 0},
        {"path": "src/lib/validations/settings.ts", "lines_added": 45, "lines_removed": 0},
        {"path": "src/components/settings/settings-form.tsx", "lines_added": 156, "lines_removed": 0},
        {"path": "src/app/(dashboard)/settings/page.tsx", "lines_added": 48, "lines_removed": 0},
        {"path": "src/app/(dashboard)/settings/layout.tsx", "lines_added": 22, "lines_removed": 0},
        {"path": "src/components/nav/user-menu.tsx", "lines_added": 8, "lines_removed": 1},
        {"path": "src/hooks/use-settings.ts", "lines_added": 52, "lines_removed": 0},
    ],
    "decisions": [
        {
            "question": "How should we store user preferences?",
            "decision": "JSONB column in user_settings table",
            "reason": "Flexible schema, easy to extend, good query performance",
        },
        {
            "question": "Client-side or server-side validation?",
            "decision": "Both with shared zod schema",
            "reason": "Best UX with client validation, security with server validation",
        },
    ],
    "deviations": [],
    "branch_name": "feature/user-settings-demo",
    "pr_url": "https://github.com/example/repo/pull/42",
    "total_commits": 8,
    "total_cost_cents": 2847,
    "total_input_tokens": 125000,
    "total_output_tokens": 48000,
}


class DemoRunner:
    """Simulates a Dirigent execution by sending fake events to the portal."""

    def __init__(
        self,
        reporter: PortalReporter,
        speed: float = 1.0,
    ):
        """
        Initialize the demo runner.

        Args:
            reporter: PortalReporter instance for sending events
            speed: Speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = slower)
        """
        self.reporter = reporter
        self.speed = speed
        self._start_time: Optional[float] = None
        self._tasks_completed = 0
        self._total_tasks = DEMO_PLAN["total_tasks"]

    def _sleep(self, seconds: float):
        """Sleep with speed adjustment."""
        time.sleep(seconds / self.speed)

    def _random_sleep(self, min_sec: float, max_sec: float):
        """Random sleep within range, adjusted for speed."""
        self._sleep(random.uniform(min_sec, max_sec))

    def run(self):
        """Run the full demo sequence."""
        logger.info("🎭 Starting Demo Run...")
        self._start_time = time.time()

        try:
            self._run_analysis_stage()
            self._run_routing_stage()
            self._run_planning_stage()
            self._run_execution_stage()
            self._run_shipping_stage()
            self._send_completion()
            logger.info("🎭 Demo Run completed successfully!")
        except Exception as e:
            logger.error(f"Demo run failed: {e}")
            self.reporter.error(str(e), fatal=True)
            raise

    def _run_analysis_stage(self):
        """Simulate repository analysis."""
        logger.info("📊 Demo: Analysis stage")
        self.reporter.stage_start("analysis", "Analysiere Repository-Struktur und Spec")
        self._sleep(2)

        self.reporter.analysis_result(
            language=DEMO_ANALYSIS["language"],
            framework=DEMO_ANALYSIS["framework"],
            commit_count=DEMO_ANALYSIS["commit_count"],
            file_count=DEMO_ANALYSIS["file_count"],
            route=DEMO_ANALYSIS["route"],
            confidence=DEMO_ANALYSIS["confidence"],
        )
        self._sleep(1)

        self.reporter.stage_complete(
            "analysis",
            result=f"Route: {DEMO_ANALYSIS['route']} ({DEMO_ANALYSIS['confidence']} confidence)",
            details=DEMO_ANALYSIS,
        )

    def _run_routing_stage(self):
        """Simulate route determination."""
        logger.info("🛤️ Demo: Routing stage")
        self.reporter.stage_start("routing", "Bestimme optimalen Ausführungspfad")
        self._sleep(1.5)

        self.reporter.route_determined(
            route_type=DEMO_ROUTE["route_type"],
            reason=DEMO_ROUTE["reason"],
            steps=DEMO_ROUTE["steps"],
            estimated_tasks=DEMO_ROUTE["estimated_tasks"],
        )
        self._sleep(0.5)

        self.reporter.stage_complete(
            "routing",
            result=f"{DEMO_ROUTE['route_type']} Route mit {len(DEMO_ROUTE['steps'])} Schritten",
        )

    def _run_planning_stage(self):
        """Simulate plan creation."""
        logger.info("📝 Demo: Planning stage")
        self.reporter.stage_start("planning", "Erstelle Ausführungsplan mit Claude Code")
        self._sleep(3)

        # Send the plan
        self.reporter.send_plan(
            phases=DEMO_PLAN["phases"],
            total_tasks=DEMO_PLAN["total_tasks"],
        )
        self._sleep(1)

        self.reporter.stage_complete(
            "planning",
            result=f"Plan erstellt: {len(DEMO_PLAN['phases'])} Phasen, {DEMO_PLAN['total_tasks']} Tasks",
        )

    def _run_execution_stage(self):
        """Simulate task execution."""
        logger.info("⚡ Demo: Execution stage")
        self.reporter.stage_start("execution", "Führe Tasks mit Claude Code aus")
        self._sleep(1)

        for phase in DEMO_PLAN["phases"]:
            self._run_phase(phase)

        self.reporter.stage_complete("execution", "Alle Tasks abgeschlossen")

    def _run_phase(self, phase: dict):
        """Simulate a single phase execution."""
        phase_id = str(phase["phase"])
        phase_name = phase["name"]
        tasks = phase["tasks"]

        logger.info(f"  Phase {phase_id}: {phase_name}")
        self.reporter.phase_start(phase_id, phase_name, task_count=len(tasks))
        self._sleep(0.5)

        for task in tasks:
            self._run_task(task, int(phase_id))

        self.reporter.phase_complete(
            phase_id,
            phase_name,
            tasks_completed=len(tasks),
            commit_count=len(tasks),
        )

        # Send progress update
        phases_done = int(phase_id)
        self.reporter.progress(
            tasks_complete=self._tasks_completed,
            total_tasks=self._total_tasks,
            phases_complete=phases_done,
        )
        self._sleep(0.5)

    def _run_task(self, task: dict, phase: int):
        """Simulate a single task execution with file operations."""
        task_id = task["id"]
        task_name = task["name"]
        activities = DEMO_TASK_ACTIVITIES.get(task_id, {})

        logger.info(f"    Task {task_id}: {task_name}")
        self.reporter.task_start(task_id, task_name)
        self._random_sleep(0.3, 0.8)

        # Simulate thinking
        for thought in activities.get("thinking", []):
            self.reporter.thinking(thought)
            self._random_sleep(0.8, 1.5)

        # Simulate file operations
        for file_op in activities.get("files", []):
            self.reporter.file_operation(
                path=file_op["path"],
                action=file_op["action"],
                lines_changed=file_op.get("lines", 0),
            )
            self._random_sleep(0.3, 0.7)

        # Simulate bash commands
        for cmd in activities.get("bash", []):
            self.reporter.bash_command(cmd, exit_code=0)
            self._random_sleep(0.5, 1.0)

        # Complete the task
        commit_msg = activities.get("commit", f"feat: complete {task_id}")
        self.reporter.task_complete(task_id, task_name, commit_hash=f"abc{task_id.replace('.', '')}def")
        self._tasks_completed += 1
        self._random_sleep(0.3, 0.5)

    def _run_shipping_stage(self):
        """Simulate shipping (branch + PR creation)."""
        logger.info("🚀 Demo: Shipping stage")
        self.reporter.stage_start("shipping", "Erstelle Branch und PR")
        self._sleep(2)

        self.reporter.thinking("Creating feature branch...")
        self._sleep(1)
        self.reporter.bash_command("git checkout -b feature/user-settings-demo", exit_code=0)
        self._sleep(0.5)

        self.reporter.thinking("Pushing to remote...")
        self.reporter.bash_command("git push -u origin feature/user-settings-demo", exit_code=0)
        self._sleep(1)

        self.reporter.thinking("Creating pull request...")
        self._sleep(1.5)

        self.reporter.stage_complete(
            "shipping",
            result="PR #42 erstellt",
            details={"prUrl": DEMO_SUMMARY["pr_url"], "branchName": DEMO_SUMMARY["branch_name"]},
        )

    def _send_completion(self):
        """Send summary and completion events."""
        duration_ms = int((time.time() - self._start_time) * 1000)

        # Send summary
        self.reporter.summary(
            markdown=DEMO_SUMMARY["markdown"],
            files_changed=DEMO_SUMMARY["files_changed"],
            decisions=DEMO_SUMMARY["decisions"],
            deviations=DEMO_SUMMARY["deviations"],
            total_cost_cents=DEMO_SUMMARY["total_cost_cents"],
            total_input_tokens=DEMO_SUMMARY["total_input_tokens"],
            total_output_tokens=DEMO_SUMMARY["total_output_tokens"],
            branch_name=DEMO_SUMMARY["branch_name"],
            pr_url=DEMO_SUMMARY["pr_url"],
            duration_ms=duration_ms,
            total_commits=DEMO_SUMMARY["total_commits"],
        )

        # Send completion
        self.reporter.complete(
            success=True,
            duration_ms=duration_ms,
            total_commits=DEMO_SUMMARY["total_commits"],
            total_deviations=0,
            branch_name=DEMO_SUMMARY["branch_name"],
            pr_url=DEMO_SUMMARY["pr_url"],
        )


def run_demo(
    portal_url: str,
    execution_id: str,
    reporter_token: str,
    speed: float = 1.0,
):
    """
    Run a demo execution.

    Args:
        portal_url: URL of the Outbid Portal
        execution_id: Execution ID to report events to
        reporter_token: Authentication token for the portal
        speed: Speed multiplier (default 1.0)
    """
    reporter = PortalReporter(
        portal_url=portal_url,
        execution_id=execution_id,
        reporter_token=reporter_token,
    )

    runner = DemoRunner(reporter, speed=speed)
    runner.run()
