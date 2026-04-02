"""
Shipper — handles branch creation, push, and PR creation.

Extracted from the Executor god class.
"""

import re
import shutil
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.infra_schema import InfraContext
from outbid_dirigent.plan_schema import Plan


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-safe slug for branch names."""
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii').lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    if len(text) > max_length:
        text = text[:max_length].rsplit('-', 1)[0]
    return text or "feature"


class Shipper:
    """Creates branch, pushes, and opens PR."""

    def __init__(self, repo_path: Path, plan: Optional[Plan] = None, dry_run: bool = False):
        self.repo_path = repo_path
        self.plan = plan
        self.dry_run = dry_run
        self.summaries_dir = repo_path / ".dirigent" / "summaries"
        self.branch_name: Optional[str] = None
        self.pr_url: Optional[str] = None

    def ship(self) -> bool:
        """Create branch, push, create PR."""
        spec_title = self.plan.title if self.plan else "Feature"
        slug = slugify(spec_title)
        branch_name = f"dirigent/{slug}"

        # Deduplicate branch name
        check = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=self.repo_path, capture_output=True, text=True,
        )
        if check.returncode == 0:
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            branch_name = f"dirigent/{slug}-{ts}"

        self.branch_name = branch_name
        logger.info(f"Shipping to branch: {branch_name}")

        if self.dry_run:
            logger.info("[DRY-RUN] Would create branch and push")
            return True

        try:
            # Remove .dirigent/ and .planning/ from git history on the PR branch.
            # These are execution artifacts — useful as logs, not as code changes.
            self._strip_artifacts()

            # Create branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path, capture_output=True, text=True,
            )
            if result.returncode != 0:
                logger.error(f"Branch creation failed: {result.stderr}")
                return False

            # Push
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=self.repo_path, capture_output=True, text=True,
            )
            if result.returncode != 0:
                logger.warning(f"Push failed (maybe no remote): {result.stderr}")
                return True

            # Create PR if gh available
            if shutil.which("gh"):
                pr_body = self._generate_pr_body()
                result = subprocess.run(
                    ["gh", "pr", "create", "--title", f"feat: {spec_title}", "--body", pr_body, "--head", branch_name],
                    cwd=self.repo_path, capture_output=True, text=True,
                )
                if result.returncode == 0:
                    self.pr_url = result.stdout.strip()
                    logger.info(f"PR created: {self.pr_url}")
                else:
                    logger.warning(f"PR creation failed: {result.stderr}")
            else:
                logger.info("gh CLI not found, create PR manually")

            return True
        except Exception as e:
            logger.error(f"Shipping failed: {e}")
            return False

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
                cwd=self.repo_path, capture_output=True, text=True,
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
                cwd=self.repo_path, capture_output=True, text=True,
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
            cwd=self.repo_path, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "chore: exclude execution artifacts from PR"],
            cwd=self.repo_path, capture_output=True, text=True,
        )

    def _build_verification_section(self) -> str:
        """Build ## Verification section from InfraContext for PR body."""
        ctx = InfraContext.load(self.repo_path / ".dirigent" / "infra-context.json")
        if ctx is None:
            return ""

        confidence_emoji = {"e2e": "✅", "integration": "✅", "unit": "✅", "mocked": "⚠️", "static": "⚠️", "none": "❌"}
        emoji = confidence_emoji.get(ctx.confidence, "⚠️")

        lines = ["## Verification", f"{emoji} Tests passed — {ctx.confidence} confidence ({ctx.tier.value})"]
        if ctx.tests_run > 0 or ctx.tests_skipped_infra > 0:
            lines.append(f"   {ctx.tests_run} tests run, {ctx.tests_skipped_infra} skipped due to missing infra")
        if ctx.caveat:
            lines.append(f"   _{ctx.caveat}_")
        if ctx.gaps:
            lines.append("")
            lines.append("**To verify at higher confidence:**")
            for gap in ctx.gaps:
                lines.append(f"- {gap.suggested_fix}")
        return "\n".join(lines) + "\n\n"

    def _generate_pr_body(self) -> str:
        verification = self._build_verification_section()
        parts = [
            verification,
            "## Summary",
            self.plan.summary if self.plan else "Automatically created by Outbid Dirigent.",
            "",
            "## Changes",
        ]
        for f in sorted(self.summaries_dir.glob("*-SUMMARY.md")) if self.summaries_dir.exists() else []:
            content = f.read_text(encoding="utf-8")
            match = re.search(r"## Was wurde gemacht\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if match:
                parts.append(f"- {match.group(1).strip()}")
        parts.extend(["", "---", "*Automatically created by Outbid Dirigent*"])
        return "\n".join(parts)
