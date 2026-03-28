"""
Init phase — bootstraps dev environment before planning.

The init phase has two jobs:
1. Run .outbid/init.sh or init.sh to start services, seed data, set up auth
2. Produce .dirigent/test-harness.json — a structured specification that tells
   the reviewer exactly how to verify features end-to-end

The init script is expected to:
- Start required services (databases, queues, etc.)
- Start the dev server (or leave instructions for starting it)
- Seed test data (users, sample records)
- Set up e2e auth (create storageState, export tokens, etc.)
- Write .dirigent/test-harness.json OR print enough info for the
  /dirigent:run-init skill to construct it

If no init script exists, the skill still inspects the repo to build
a best-effort test harness from config files and package.json.
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.test_harness_schema import TestHarness


class InitPhase:
    """Handles the pre-planning init phase."""

    INIT_TIMEOUT = 300  # 5 minutes
    INIT_SCRIPT_LOCATIONS = [
        ".outbid/init.sh",
        "init.sh",
    ]
    READINESS_TIMEOUT = 60  # seconds to wait for services after init script

    def __init__(self, repo_path: Path, runner=None):
        self.repo_path = repo_path
        self.runner = runner
        self.dirigent_dir = repo_path / ".dirigent"
        self.dirigent_dir.mkdir(parents=True, exist_ok=True)

    def discover_init_script(self) -> Optional[Path]:
        """Find the init script in the repo."""
        for location in self.INIT_SCRIPT_LOCATIONS:
            script = self.repo_path / location
            if script.exists():
                logger.info(f"Found init script: {script}")
                return script
        return None

    def run_init_script(self, script_path: Path) -> dict:
        """Execute the init script and return results.

        The script runs in a NEW shell that inherits the current environment.
        If the script writes .dirigent/test-harness.json, we use that directly.
        Otherwise we capture stdout/stderr for the skill to analyze.

        The script is NOT run with capture_output — it runs attached so that
        background processes (dev servers) survive the script exiting.
        """
        result = {
            "script": str(script_path.relative_to(self.repo_path)),
            "success": False,
            "output": "",
            "error": "",
            "duration_seconds": 0,
            "produced_harness": False,
        }

        start = datetime.now()

        try:
            script_path.chmod(0o755)

            # Run the init script. Use a subshell that sources the script
            # so exported env vars are captured in a sidecar file.
            env_capture = self.dirigent_dir / "init-exports.env"
            wrapper = (
                f'set -e; source "{script_path}" 2>&1; '
                f'env > "{env_capture}"'
            )

            proc = subprocess.run(
                ["bash", "-c", wrapper],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=self.INIT_TIMEOUT,
            )

            result["output"] = proc.stdout[:10000]
            result["error"] = proc.stderr[:5000]
            result["success"] = proc.returncode == 0

            if proc.returncode != 0:
                logger.warning(f"Init script exited with code {proc.returncode}")

        except subprocess.TimeoutExpired:
            result["error"] = f"Init script timed out after {self.INIT_TIMEOUT}s"
            logger.error(result["error"])
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Init script error: {e}")

        result["duration_seconds"] = (datetime.now() - start).total_seconds()

        # Check if the script produced the harness itself
        harness_path = self.dirigent_dir / "test-harness.json"
        if harness_path.exists():
            harness = TestHarness.load(harness_path)
            if harness:
                result["produced_harness"] = True
                logger.info("Init script produced test-harness.json directly")

        # Save raw output for the skill to analyze if needed
        log_file = self.dirigent_dir / "init-output.log"
        log_file.write_text(
            f"=== Init Script: {script_path} ===\n"
            f"=== Exit Code: {proc.returncode if result['success'] or result['error'] else 'N/A'} ===\n\n"
            f"--- STDOUT ---\n{result['output']}\n\n"
            f"--- STDERR ---\n{result['error']}\n",
            encoding="utf-8",
        )

        # Save exported environment (from the init script's perspective)
        if env_capture.exists():
            self._extract_env_diff(env_capture)

        return result

    def _extract_env_diff(self, env_file: Path):
        """Compare init script's exported env with current env.

        Saves new/changed vars to .dirigent/init-new-env.json.
        Only saves var NAMES for security — never values (except for
        non-sensitive ones like URLs and ports).
        """
        try:
            current_env = dict(os.environ)
            init_env = {}
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line:
                    key, val = line.split("=", 1)
                    init_env[key] = val

            # Find vars that are new or changed
            safe_value_patterns = ["URL", "PORT", "HOST", "BASE", "ADDR"]
            new_vars = {}
            for key, val in init_env.items():
                if key not in current_env or current_env[key] != val:
                    # Only expose values for URL/PORT-like vars, redact the rest
                    if any(p in key.upper() for p in safe_value_patterns):
                        new_vars[key] = val
                    else:
                        new_vars[key] = "(set by init)"

            if new_vars:
                out = self.dirigent_dir / "init-new-env.json"
                out.write_text(json.dumps(new_vars, indent=2), encoding="utf-8")
                logger.info(f"Init script exported {len(new_vars)} new/changed env vars")

        except Exception as e:
            logger.debug(f"Failed to extract env diff: {e}")

    def wait_for_readiness(self, harness: TestHarness) -> bool:
        """Wait for health checks in the test harness to pass."""
        if not harness.health_checks:
            return True

        logger.info(f"Waiting for {len(harness.health_checks)} health checks...")
        all_passed = True

        for check in harness.health_checks:
            timeout = min(check.timeout_seconds, self.READINESS_TIMEOUT)
            deadline = time.time() + timeout
            passed = False

            while time.time() < deadline:
                try:
                    proc = subprocess.run(
                        ["bash", "-c", check.command],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if proc.returncode == 0:
                        logger.info(f"  Health check passed: {check.name}")
                        passed = True
                        break
                except (subprocess.TimeoutExpired, Exception):
                    pass
                time.sleep(2)

            if not passed:
                logger.warning(f"  Health check failed: {check.name} (timeout {timeout}s)")
                all_passed = False

        return all_passed

    # ══════════════════════════════════════════
    # MAIN ENTRY POINT
    # ══════════════════════════════════════════

    def run(self) -> bool:
        """Run the complete init phase.

        Flow:
        1. Discover and run init script (if exists)
        2. If init script produced test-harness.json → validate and use it
        3. If not → invoke /dirigent:run-init skill to inspect the repo
           and build a best-effort harness
        4. Wait for health checks in the harness to pass
        5. Harness is available for planner, executor, and reviewer

        Returns True always (non-blocking — best effort).
        """
        logger.info("Starting init phase...")

        script = self.discover_init_script()
        harness_path = self.dirigent_dir / "test-harness.json"

        # Step 1: Run init script if it exists
        if script:
            logger.info(f"Running init script: {script}")
            init_result = self.run_init_script(script)

            if not init_result["success"]:
                logger.warning("Init script failed (continuing — non-blocking)")
        else:
            logger.info("No init script found (.outbid/init.sh or init.sh)")

        # Step 2: Check if the script produced the harness
        harness = TestHarness.load(harness_path)

        # Step 3: If no harness yet, have the skill build one
        if harness is None and self.runner:
            logger.info("No test-harness.json — invoking /dirigent:run-init to build one")
            success, _, stderr = self.runner._run_claude(
                "Run /dirigent:run-init", timeout=300,
            )
            if success:
                harness = TestHarness.load(harness_path)

        if harness is None:
            logger.warning("No test harness produced — reviewer will only do static analysis")
            return True

        # Step 4: Wait for health checks
        logger.info(f"Test harness: {harness.base_url}, auth={harness.auth.method.value}, "
                    f"{len(harness.verification_commands)} verification commands")

        if harness.health_checks:
            ready = self.wait_for_readiness(harness)
            if ready:
                logger.info("All health checks passed — environment is ready")
            else:
                harness.status = "partial"
                harness.notes = "Some health checks failed"
                harness.save(harness_path)
                logger.warning("Some health checks failed — harness marked as partial")

        return True
