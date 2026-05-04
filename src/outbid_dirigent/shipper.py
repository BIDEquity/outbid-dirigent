"""
Shipper — handles branch creation, push, and PR creation.

Extracted from the Executor god class.
"""

import json
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.test_harness_schema import TestHarness
from outbid_dirigent.plan_schema import Plan


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-safe slug for branch names."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text or "feature"


class Shipper:
    """Creates branch, pushes, and opens PR."""

    def __init__(
        self,
        repo_path: Path,
        plan: Optional[Plan] = None,
        dry_run: bool = False,
        dirigent_dir: Optional[Path] = None,
    ):
        self.repo_path = repo_path
        self.plan = plan
        self.dry_run = dry_run
        self.dirigent_dir = dirigent_dir or (repo_path / ".dirigent")
        self.summaries_dir = self.dirigent_dir / "summaries"
        self.branch_name: Optional[str] = None
        self.pr_url: Optional[str] = None
        # True only after `git push` succeeded. Distinguishes "branch was
        # planned" (branch_name set early) from "branch is on origin"
        # (push went through). The executor reads this to avoid emitting
        # a success event after a 403/auth failure.
        self.pushed: bool = False

    def ship(self) -> bool:
        """Create branch, push, create PR.

        Idempotent across re-runs of the same FR: a second invocation in the
        same workspace (resume, manual re-trigger) reuses the same
        ``dirigent/<slug>`` branch and the same PR rather than producing a
        timestamp-suffixed duplicate. Force-push semantics are conditional —
        we only force when the remote already has the branch from a previous
        ship() — so plain first runs stay safe.
        """
        spec_title = self.plan.title if self.plan else "Feature"
        slug = slugify(spec_title)
        branch_name = f"dirigent/{slug}"

        self.branch_name = branch_name
        logger.info(f"Shipping to branch: {branch_name}")

        if self.dry_run:
            logger.info("[DRY-RUN] Would create branch and push")
            self.pushed = True
            return True

        # Capture the base branch BEFORE we cut the feature branch — once we
        # `git checkout -b` we lose the upstream context that the PR should
        # target (develop, etc.).
        base_branch = self._resolve_base_branch()
        logger.info(f"PR base branch resolved to: {base_branch}")

        try:
            # Remove .dirigent/ and .planning/ from git history on the PR branch.
            # These are execution artifacts — useful as logs, not as code changes.
            self._strip_artifacts()

            # Re-run handling: if a previous ship() in this workspace already
            # created the branch locally, drop it so we can recreate from the
            # current HEAD with this run's commits. The previous version
            # persists on origin and gets force-pushed below.
            existing_local = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            had_local_branch = existing_local.returncode == 0
            if had_local_branch:
                logger.info(
                    f"Branch {branch_name} already exists locally — dropping "
                    "and recreating from current HEAD (re-run)"
                )
                # `git branch -D` on a checked-out branch fails; switch to a
                # detached HEAD first so the delete always succeeds.
                subprocess.run(
                    ["git", "checkout", "--detach"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )

            # Create branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.error(f"Branch creation failed: {result.stderr}")
                return False

            # Push. Try fast-forward first; if the remote diverged (typical
            # when a previous ship() pushed different commits), retry with
            # --force so this run's HEAD becomes the PR's head.
            push_args = ["git", "push", "-u", "origin", branch_name]
            result = subprocess.run(
                push_args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                stderr_lower = result.stderr.lower()
                diverged = (
                    "non-fast-forward" in stderr_lower
                    or "rejected" in stderr_lower
                    or had_local_branch
                )
                if diverged:
                    logger.info(
                        f"Branch {branch_name} diverged on origin — force-pushing "
                        "this run's commits over the previous state"
                    )
                    result = subprocess.run(
                        push_args + ["--force"],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                    )
            if result.returncode != 0:
                logger.error(f"Push failed: {result.stderr.strip()}")
                return False
            self.pushed = True

            # Create PR if gh available
            if shutil.which("gh"):
                pr_body = self._generate_pr_body()
                pr_args = [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    f"feat: {spec_title}",
                    "--body",
                    pr_body,
                    "--head",
                    branch_name,
                ]
                # Without --base, gh defaults to the repo's default branch
                # (typically master/main). That's wrong when the FR was
                # created against another branch (e.g. develop) — the PR
                # would carry every commit between develop and master plus
                # the actual feature work, and merging it would dump
                # develop's history onto master.
                if base_branch:
                    pr_args.extend(["--base", base_branch])
                result = subprocess.run(
                    pr_args,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    self.pr_url = result.stdout.strip()
                    logger.info(f"PR created: {self.pr_url}")
                else:
                    # Most common failure on re-runs: a PR already exists for
                    # this head. Don't create a new one — look up the
                    # existing PR and surface its URL so the caller treats
                    # the ship as a successful update of the same PR.
                    logger.warning(f"gh pr create failed: {result.stderr.strip()}")
                    existing_url = self._lookup_existing_pr_url(branch_name)
                    if existing_url:
                        self.pr_url = existing_url
                        logger.info(f"Reusing existing PR for {branch_name}: {existing_url}")
            else:
                logger.info("gh CLI not found, create PR manually")

            return True
        except Exception as e:
            logger.error(f"Shipping failed: {e}")
            return False

    def _lookup_existing_pr_url(self, branch_name: str) -> Optional[str]:
        """Return the URL of the open PR whose head is ``branch_name``, if any.

        Used by ``ship()`` to recover when ``gh pr create`` rejects a
        re-run because a PR already exists. We treat the existing PR as the
        canonical one and surface its URL to the caller — same idempotent
        contract the rest of ship() upholds.
        """
        try:
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    branch_name,
                    "--state",
                    "open",
                    "--json",
                    "url",
                    "--limit",
                    "1",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning(f"Could not look up existing PR for {branch_name}: {exc}")
            return None

        if result.returncode != 0:
            logger.warning(
                f"gh pr list for {branch_name} failed: {result.stderr.strip()}"
            )
            return None

        try:
            prs = json.loads(result.stdout or "[]")
        except ValueError:
            return None

        if isinstance(prs, list) and prs:
            url = prs[0].get("url") if isinstance(prs[0], dict) else None
            if isinstance(url, str) and url:
                return url
        return None

    def _resolve_base_branch(self) -> Optional[str]:
        """Determine the branch the PR should target.

        Priority:
          1. ``GIT_BRANCH`` env (set by outbid-portal/launch-workspace from the
             feature_request.branch column — the user's explicit choice).
          2. The current branch name from ``git rev-parse --abbrev-ref HEAD``,
             since the workspace was cloned with ``git clone --branch <X>`` so
             HEAD points at the right place before we cut the feature branch.
          3. ``None`` — caller should then omit ``--base`` and let gh fall back
             to the repository default.

        We resolve this *before* ``git checkout -b`` because afterwards HEAD
        points at the brand-new feature branch and the upstream context is
        gone.
        """
        env_branch = os.environ.get("GIT_BRANCH", "").strip()
        if env_branch:
            return env_branch

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning(f"Could not resolve base branch via git: {exc}")
            return None

        if result.returncode != 0:
            logger.warning(
                f"git rev-parse --abbrev-ref HEAD failed: {result.stderr.strip()}"
            )
            return None

        head = result.stdout.strip()
        # Detached HEAD ("HEAD") is meaningless as a base — bail to fallback.
        if not head or head == "HEAD":
            return None
        return head

    # Directories that are execution artifacts and must not appear in PRs
    ARTIFACT_DIRS = [".dirigent", ".planning"]

    def _strip_artifacts(self) -> None:
        """Remove execution artifact directories from git tracking.

        Removes .dirigent/ and .planning/ from all commits that introduced them,
        so the PR branch contains only production code changes.
        """
        # Check which artifact dirs are actually tracked
        tracked = []
        for d in self.ARTIFACT_DIRS:
            result = subprocess.run(
                ["git", "ls-files", d],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                tracked.append(d)

        if not tracked:
            return

        logger.info(f"Stripping artifact dirs from git: {tracked}")

        # Remove from index (keeps files on disk)
        for d in tracked:
            subprocess.run(
                ["git", "rm", "-r", "--cached", "--quiet", d],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

        # Ensure they stay ignored
        gitignore_path = self.repo_path / ".gitignore"
        existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        additions = [d + "/" for d in tracked if d + "/" not in existing and d not in existing]
        if additions:
            block = "\n# Dirigent execution artifacts\n" + "\n".join(additions) + "\n"
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(block)

        # Commit the removal
        subprocess.run(
            ["git", "add", ".gitignore"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "chore: exclude execution artifacts from PR"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

    def _build_verification_section(self) -> str:
        """Build ## Verification section from TestHarness for PR body."""
        harness = TestHarness.load(self.dirigent_dir / "test-harness.json")
        if harness is None or not harness.commands:
            return ""

        lines = ["## Verification", "```bash"]
        for key in ("build", "test", "e2e"):
            if key in harness.commands:
                cmd = harness.commands[key]
                lines.append(f"# {key}: {cmd.explanation}")
                lines.append(cmd.command)
        lines.append("```")

        if harness.portal:
            lines.append("")
            lines.append("### Live Preview")
            lines.append(f"```bash\n{harness.portal.start_command}\n```")
            lines.append(f"→ `localhost:{harness.portal.port}{harness.portal.url_after_start}`")

        return "\n".join(lines) + "\n\n"

    def _is_greenfield_project(self) -> bool:
        """Check if dirigent authored >80% of commits (new project)."""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            total = int(result.stdout.strip()) if result.returncode == 0 else 0
            if total == 0:
                return False

            result = subprocess.run(
                ["git", "log", "--oneline", "--grep=feat: task", "--count"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            # Fallback: count commits with "task" in message (dirigent pattern)
            result = subprocess.run(
                ["git", "log", "--oneline", "--all"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return False
            all_commits = result.stdout.strip().splitlines()
            dirigent_commits = [
                c for c in all_commits if "task " in c.lower() or "dirigent" in c.lower()
            ]
            return len(dirigent_commits) / len(all_commits) > 0.8 if all_commits else False
        except Exception:
            return False

    def _build_getting_started(self) -> str:
        """Build a Getting Started section from start.sh, test-harness, or runtime info."""
        parts = ["## Getting Started", ""]
        harness_path = self.dirigent_dir / "test-harness.json"
        analysis_path = self.dirigent_dir / "ANALYSIS.json"
        start_script = self.repo_path / "start.sh"

        # Prefer start.sh (greenfield route produces this)
        if start_script.exists():
            parts.append("### Run")
            parts.append("```bash")
            parts.append("./start.sh")
            parts.append("```")
            parts.append("")

            # Extract ports from test-harness for the "Open" hint
            harness = TestHarness.load(harness_path)
            if harness and harness.portal:
                parts.append(
                    f"Open http://localhost:{harness.portal.port}{harness.portal.url_after_start}"
                )
                parts.append("")
        else:
            # Fallback: try runtime info from analysis
            if analysis_path.exists():
                import json

                try:
                    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
                    runtime = analysis.get("runtime", {})
                    if runtime:
                        setup = runtime.get("setup_steps", [])
                        start = runtime.get("start_command", "")
                        port = runtime.get("port", "")
                        if setup:
                            parts.append("### Setup")
                            parts.append("```bash")
                            for step in setup:
                                parts.append(step)
                            parts.append("```")
                            parts.append("")
                        if start:
                            parts.append("### Run")
                            parts.append("```bash")
                            parts.append(start)
                            parts.append("```")
                            if port:
                                parts.append(f"\nOpen http://localhost:{port}")
                            parts.append("")
                except Exception:
                    pass

        # Add verification commands from test-harness
        if harness_path.exists():
            harness = TestHarness.load(harness_path)
            if harness and harness.commands:
                parts.append("### Verify")
                parts.append("```bash")
                for key in ("build", "test", "e2e"):
                    if key in harness.commands:
                        cmd = harness.commands[key]
                        parts.append(f"# {key}: {cmd.explanation}")
                        parts.append(cmd.command)
                parts.append("```")
                parts.append("")

        if len(parts) <= 2:
            # No runtime info found, add minimal note
            parts.append("See the project README for setup instructions.")
            parts.append("")

        return "\n".join(parts)

    def _generate_pr_body(self) -> str:
        verification = self._build_verification_section()
        parts = [
            verification,
            "## Summary",
            self.plan.summary if self.plan else "Automatically created by Outbid Dirigent.",
            "",
        ]

        # For new projects, include how to start the app
        if self._is_greenfield_project():
            parts.append(self._build_getting_started())

        parts.append("## Changes")
        for f in (
            sorted(self.summaries_dir.glob("*-SUMMARY.md")) if self.summaries_dir.exists() else []
        ):
            content = f.read_text(encoding="utf-8")
            match = re.search(r"## Was wurde gemacht\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if match:
                parts.append(f"- {match.group(1).strip()}")
        parts.extend(["", "---", "*Automatically created by Outbid Dirigent*"])
        return "\n".join(parts)
