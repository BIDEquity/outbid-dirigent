"""
Init phase — bootstraps dev environment before planning.

Discovers and runs init scripts that:
1. Start required services (databases, APIs, etc.)
2. Seed development data
3. Configure credentials for Playwright/Puppeteer e2e testing
4. Validate the environment is ready

Init script discovery order:
1. .outbid/init.sh — Outbid-specific init
2. init.sh — Generic init in repo root
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


class InitPhase:
    """Handles the pre-planning init phase."""

    INIT_TIMEOUT = 300  # 5 minutes
    INIT_SCRIPT_LOCATIONS = [
        ".outbid/init.sh",
        "init.sh",
    ]

    # Environment variable patterns relevant to e2e testing
    E2E_ENV_PATTERNS = [
        "PLAYWRIGHT", "PUPPETEER", "BROWSER", "E2E", "TEST_URL",
        "BASE_URL", "COOKIE", "TOKEN", "SESSION", "AUTH",
        "CREDENTIAL", "HEADLESS", "CYPRESS",
    ]

    def __init__(self, repo_path: Path, runner=None):
        """
        Args:
            repo_path: Path to the target repository
            runner: Optional TaskRunner for Claude Code invocations
        """
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
        logger.info("No init script found (.outbid/init.sh or init.sh)")
        return None

    def detect_e2e_framework(self) -> dict:
        """Detect which e2e testing framework is configured in the repo.

        Checks for:
        - Playwright (playwright.config.ts/js, @playwright/test in package.json)
        - Puppeteer (puppeteer in package.json)
        - Cypress (cypress.config.ts/js, cypress in package.json)

        Returns dict with framework info.
        """
        result = {
            "framework": None,
            "config_file": None,
            "has_auth_setup": False,
            "storage_state_path": None,
        }

        # Check Playwright
        for config in ["playwright.config.ts", "playwright.config.js", "playwright.config.mjs"]:
            config_path = self.repo_path / config
            if config_path.exists():
                result["framework"] = "playwright"
                result["config_file"] = config
                content = config_path.read_text(encoding="utf-8", errors="ignore")
                if "storageState" in content:
                    result["has_auth_setup"] = True
                    # Try to extract storage state path
                    import re
                    match = re.search(r"storageState['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]", content)
                    if match:
                        result["storage_state_path"] = match.group(1)
                break

        # Check Cypress
        if not result["framework"]:
            for config in ["cypress.config.ts", "cypress.config.js", "cypress.config.mjs"]:
                if (self.repo_path / config).exists():
                    result["framework"] = "cypress"
                    result["config_file"] = config
                    break

        # Check Puppeteer in package.json
        if not result["framework"]:
            pkg_json = self.repo_path / "package.json"
            if pkg_json.exists():
                try:
                    pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
                    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "puppeteer" in all_deps:
                        result["framework"] = "puppeteer"
                    elif "@playwright/test" in all_deps or "playwright" in all_deps:
                        result["framework"] = "playwright"
                    elif "cypress" in all_deps:
                        result["framework"] = "cypress"
                except (json.JSONDecodeError, KeyError):
                    pass

        return result

    def run_init_script(self, script_path: Path) -> dict:
        """Execute the init script and capture results.

        Returns dict with execution results.
        """
        result = {
            "script": str(script_path.relative_to(self.repo_path)),
            "success": False,
            "output": "",
            "error": "",
            "duration_seconds": 0,
            "env_vars": [],
            "ports_listening": [],
            "services": [],
        }

        start = datetime.now()

        try:
            # Make executable
            script_path.chmod(0o755)

            proc = subprocess.run(
                ["bash", str(script_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=self.INIT_TIMEOUT,
                env=None,  # inherit full environment
            )

            result["output"] = proc.stdout[:5000]
            result["error"] = proc.stderr[:2000]
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

        # Capture environment state after init
        result["env_vars"] = self._capture_e2e_env_vars()
        result["ports_listening"] = self._check_listening_ports()
        result["services"] = self._check_docker_services()

        # Save output log
        log_file = self.dirigent_dir / "init-output.log"
        log_file.write_text(
            f"=== Init Script: {script_path} ===\n"
            f"=== Exit Code: {proc.returncode if 'proc' in dir() else 'N/A'} ===\n\n"
            f"--- STDOUT ---\n{result['output']}\n\n"
            f"--- STDERR ---\n{result['error']}\n",
            encoding="utf-8",
        )

        return result

    def _capture_e2e_env_vars(self) -> list[str]:
        """Capture environment variable names (not values!) relevant to e2e testing."""
        try:
            proc = subprocess.run(
                ["env"], capture_output=True, text=True, timeout=5,
            )
            vars_found = []
            for line in proc.stdout.splitlines():
                name = line.split("=", 1)[0] if "=" in line else ""
                if any(pattern in name.upper() for pattern in self.E2E_ENV_PATTERNS):
                    vars_found.append(name)
            return vars_found
        except Exception:
            return []

    def _check_listening_ports(self) -> list[int]:
        """Check which common dev ports are listening."""
        common_ports = [3000, 3001, 4000, 5000, 5173, 5432, 6379, 8000, 8080, 9090, 27017]
        listening = []
        try:
            proc = subprocess.run(
                ["ss", "-tlnp"], capture_output=True, text=True, timeout=5,
            )
            for port in common_ports:
                if f":{port} " in proc.stdout or f":{port}\t" in proc.stdout:
                    listening.append(port)
        except Exception:
            pass
        return listening

    def _check_docker_services(self) -> list[dict]:
        """Check running Docker containers."""
        try:
            proc = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
                capture_output=True, text=True, timeout=10,
            )
            services = []
            for line in proc.stdout.strip().splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    services.append({
                        "name": parts[0],
                        "status": parts[1],
                        "ports": parts[2] if len(parts) > 2 else "",
                    })
            return services
        except Exception:
            return []

    def write_init_report(self, init_result: dict, e2e_info: dict) -> Path:
        """Write the init report to .dirigent/INIT_REPORT.md."""
        report_path = self.dirigent_dir / "INIT_REPORT.md"

        # Determine overall status
        if init_result["success"]:
            status = "READY"
        elif init_result["output"]:
            status = "PARTIAL"
        else:
            status = "FAILED"

        # Build report
        lines = [
            "# Init Report\n",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "## Script Used",
            f"`{init_result['script']}`\n",
        ]

        # Services
        if init_result["services"]:
            lines.append("## Services Running")
            for svc in init_result["services"]:
                lines.append(f"- **{svc['name']}**: {svc['status']} ({svc['ports']})")
            lines.append("")

        # Ports
        if init_result["ports_listening"]:
            lines.append("## Ports Listening")
            for port in init_result["ports_listening"]:
                lines.append(f"- Port {port}")
            lines.append("")

        # E2E config
        lines.append("## E2E Test Configuration")
        if e2e_info["framework"]:
            lines.append(f"- **Framework:** {e2e_info['framework']}")
            if e2e_info["config_file"]:
                lines.append(f"- **Config:** `{e2e_info['config_file']}`")
            if e2e_info["has_auth_setup"]:
                lines.append("- **Auth Setup:** Yes (storageState configured)")
                if e2e_info["storage_state_path"]:
                    lines.append(f"- **Storage State:** `{e2e_info['storage_state_path']}`")
            else:
                lines.append("- **Auth Setup:** Not configured")
        else:
            lines.append("- No e2e framework detected")
        lines.append("")

        # Environment variables (names only, never values)
        if init_result["env_vars"]:
            lines.append("## Environment Variables (e2e-relevant)")
            for var in init_result["env_vars"]:
                lines.append(f"- `{var}` (set)")
            lines.append("")

        # Execution details
        lines.append("## Execution Details")
        lines.append(f"- **Duration:** {init_result['duration_seconds']:.1f}s")
        lines.append(f"- **Exit Status:** {'Success' if init_result['success'] else 'Failed'}")
        if init_result["error"]:
            lines.append(f"- **Errors:** {init_result['error'][:300]}")
        lines.append("")

        lines.append(f"## Status: {status}")
        lines.append("")

        report_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Init report written to {report_path}")
        return report_path

    def write_no_init_report(self, e2e_info: dict) -> Path:
        """Write a minimal init report when no init script exists."""
        report_path = self.dirigent_dir / "INIT_REPORT.md"

        lines = [
            "# Init Report\n",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "## Script Used",
            "No init script found (checked `.outbid/init.sh` and `init.sh`).\n",
        ]

        # Still report e2e framework info
        lines.append("## E2E Test Configuration")
        if e2e_info["framework"]:
            lines.append(f"- **Framework:** {e2e_info['framework']}")
            if e2e_info["config_file"]:
                lines.append(f"- **Config:** `{e2e_info['config_file']}`")
            if e2e_info["has_auth_setup"]:
                lines.append("- **Auth Setup:** Yes (storageState configured)")
            else:
                lines.append("- **Auth Setup:** Not configured — may need manual setup")
        else:
            lines.append("- No e2e framework detected")
        lines.append("")

        # Check ports anyway
        ports = self._check_listening_ports()
        if ports:
            lines.append("## Ports Already Listening")
            for port in ports:
                lines.append(f"- Port {port}")
            lines.append("")

        lines.append("## Status: SKIPPED")
        lines.append("No init script to run. E2e tests may require manual environment setup.\n")

        report_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Init report written (no init script): {report_path}")
        return report_path

    # ══════════════════════════════════════════
    # MAIN ENTRY POINT
    # ══════════════════════════════════════════

    def run(self) -> bool:
        """Run the complete init phase.

        Returns True if init completed (or was skipped) successfully.
        """
        logger.info("Starting init phase...")

        # Detect e2e framework regardless of init script
        e2e_info = self.detect_e2e_framework()
        if e2e_info["framework"]:
            logger.info(f"Detected e2e framework: {e2e_info['framework']}")

        # Discover init script
        script = self.discover_init_script()

        if script is None:
            self.write_no_init_report(e2e_info)
            logger.info("Init phase: no init script, skipping")
            return True

        # Run init script
        logger.info(f"Running init script: {script}")
        init_result = self.run_init_script(script)

        # Write report
        self.write_init_report(init_result, e2e_info)

        if init_result["success"]:
            logger.info("Init phase completed successfully")
        else:
            logger.warning("Init phase completed with errors (non-blocking)")

        # Save init env for later use by tasks
        env_file = self.dirigent_dir / "init-env.json"
        env_data = {
            "e2e_framework": e2e_info["framework"],
            "e2e_config_file": e2e_info["config_file"],
            "e2e_has_auth": e2e_info["has_auth_setup"],
            "e2e_storage_state": e2e_info["storage_state_path"],
            "ports_listening": init_result["ports_listening"],
            "services": init_result["services"],
            "env_vars": init_result["env_vars"],
            "status": "ready" if init_result["success"] else "partial",
        }
        env_file.write_text(json.dumps(env_data, indent=2, ensure_ascii=False), encoding="utf-8")

        return True  # Always non-blocking
