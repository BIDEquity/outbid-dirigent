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

from outbid_dirigent.infra_schema import InfraContext, InfraTier, ServiceGap, SeedInfo
from outbid_dirigent.test_harness_schema import TestHarness


class InfraDetector:
    """Detects and provisions test infrastructure in tier priority order."""

    KNOWN_DEVBOX_SERVICE_PACKAGES = ["postgresql", "redis", "mysql", "mongodb", "rabbitmq"]

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.dirigent_dir = repo_path / ".dirigent"

    def detect(self) -> InfraContext:
        """Run full detection pipeline and return InfraContext."""
        ctx = self._detect_services()
        ctx.seed = self._detect_seed()
        ctx.save(self.dirigent_dir / "infra-context.json")
        self._store_to_ruflo(ctx)
        return ctx

    def _detect_services(self) -> InfraContext:
        """Try each tier in order, return at first viable one."""
        # Tier 1: devbox
        if self._devbox_viable() and self._devbox_has_services():
            started = self._start_devbox_services()
            if started:
                return InfraContext(tier=InfraTier.DEVBOX, services_started=started, confidence="integration")

        # Tier 2: docker-compose
        compose_file = self._find_compose_file()
        if compose_file and self._docker_viable():
            started = self._start_docker_compose(compose_file)
            if started is not None:
                return InfraContext(tier=InfraTier.DOCKER_COMPOSE, services_started=started, confidence="integration")

        # Tier 3: CI extraction
        ci_services = self._extract_ci_services()
        if ci_services:
            gaps = [ServiceGap(service=s["type"], port=s.get("host_port"), reason="extracted from CI config", suggested_fix=f"docker run -p {s.get('host_port',0)}:{s.get('host_port',0)} {s['image']}") for s in ci_services]
            return InfraContext(tier=InfraTier.CI_EXTRACTED, confidence="static", gaps=gaps)

        # Tier 4: in-process mocks detected
        if self._detect_in_process_mocks():
            return InfraContext(tier=InfraTier.MOCKED, confidence="mocked")

        # Tier 5/6: generate devbox.json or compose.yml
        stack = self._detect_stack()
        if self._devbox_viable() and stack:
            generated = self._generate_devbox_json(stack)
            if generated:
                return InfraContext(tier=InfraTier.GENERATED_DEVBOX, confidence="static", generated_files=[generated])

        if self._docker_viable() and stack:
            generated = self._generate_compose_yml(stack)
            if generated:
                return InfraContext(tier=InfraTier.GENERATED_COMPOSE, confidence="static", generated_files=[generated])

        # Tier 7: nothing viable
        gaps = self._compute_gaps(stack)
        return InfraContext(tier=InfraTier.NONE, confidence="static", gaps=gaps)

    def _devbox_viable(self) -> bool:
        """Check devbox is installed AND nix is functional."""
        try:
            result = subprocess.run(["devbox", "version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _devbox_has_services(self) -> bool:
        """Check devbox.json exists and contains known service packages."""
        devbox_json = self.repo_path / "devbox.json"
        if not devbox_json.exists():
            return False
        try:
            data = json.loads(devbox_json.read_text())
            packages = data.get("packages", [])
            if isinstance(packages, dict):
                packages = list(packages.keys())
            return any(svc in pkg for pkg in packages for svc in self.KNOWN_DEVBOX_SERVICE_PACKAGES)
        except Exception:
            return False

    def _start_devbox_services(self) -> list[str]:
        """Start devbox services. Returns list of started service names."""
        try:
            result = subprocess.run(
                ["devbox", "services", "start"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                # Parse service names from devbox.json packages
                data = json.loads((self.repo_path / "devbox.json").read_text())
                packages = data.get("packages", [])
                if isinstance(packages, dict):
                    packages = list(packages.keys())
                return [p for p in packages if any(s in p for s in self.KNOWN_DEVBOX_SERVICE_PACKAGES)]
            return []
        except Exception:
            return []

    def _find_compose_file(self):
        """Return path to docker-compose file or None."""
        for name in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
            p = self.repo_path / name
            if p.exists():
                return p
        return None

    def _docker_viable(self) -> bool:
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _start_docker_compose(self, compose_file: Path):
        """Start docker-compose services. Returns list of service names or None on failure."""
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=300,
            )
            if result.returncode != 0:
                return None
            # Get service names
            ps = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "ps", "--services"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=30,
            )
            return [s.strip() for s in ps.stdout.splitlines() if s.strip()]
        except Exception:
            return None

    def _extract_ci_services(self) -> list[dict]:
        """Parse GitHub Actions workflows for services blocks."""
        services = []
        workflows_dir = self.repo_path / ".github" / "workflows"
        if not workflows_dir.exists():
            return []
        try:
            import yaml
        except ImportError:
            return []
        for wf_path in workflows_dir.glob("*.yml"):
            try:
                data = yaml.safe_load(wf_path.read_text())
                for job in (data or {}).get("jobs", {}).values():
                    for svc_name, svc in job.get("services", {}).items():
                        if not isinstance(svc, dict):
                            continue
                        image = svc.get("image", "")
                        svc_type = image.split(":")[0].split("/")[-1]
                        ports = svc.get("ports", [])
                        host_port = None
                        for p in ports:
                            parts = str(p).split(":")
                            if len(parts) == 2:
                                try:
                                    host_port = int(parts[0])
                                    break
                                except ValueError:
                                    pass
                        services.append({"name": svc_name, "type": svc_type, "image": image, "host_port": host_port, "env": svc.get("env", {})})
            except Exception:
                continue
        return services

    def _detect_in_process_mocks(self) -> bool:
        """Check if tests use in-process fakes that need no real services."""
        import re
        mock_patterns = [r"fakeredis", r"sqlite:///:memory:", r"mongomock", r"aiosqlite.*memory", r"responses\.activate"]
        for test_file in self.repo_path.rglob("test_*.py"):
            try:
                content = test_file.read_text(encoding="utf-8", errors="ignore")
                if any(re.search(p, content) for p in mock_patterns):
                    return True
            except Exception:
                continue
        return False

    def _detect_stack(self) -> dict:
        """Detect project stack for template generation."""
        stack = {}
        if (self.repo_path / "package.json").exists():
            try:
                pkg = json.loads((self.repo_path / "package.json").read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                stack["runtime"] = "node"
                if "next" in deps:
                    stack["framework"] = "nextjs"
                if "@prisma/client" in deps or "prisma" in deps:
                    stack["db"] = "postgresql"
                if "redis" in deps or "ioredis" in deps:
                    stack["cache"] = "redis"
            except Exception:
                pass
        if (self.repo_path / "requirements.txt").exists() or (self.repo_path / "pyproject.toml").exists():
            stack["runtime"] = "python"
        return stack

    def _generate_devbox_json(self, stack: dict) -> str:
        """Write a devbox.json from detected stack. Returns path or empty string."""
        devbox_json = self.repo_path / "devbox.json"
        if devbox_json.exists():
            return ""
        packages = []
        init_hooks = []
        if stack.get("runtime") == "node":
            packages.append("nodejs@22")
        if stack.get("runtime") == "python":
            packages.append("python@3.12")
        if stack.get("db") == "postgresql":
            packages.append("postgresql@latest")
            init_hooks += ["mkdir -p $PGHOST 2>/dev/null || true", "initdb 2>/dev/null || true"]
        if stack.get("cache") == "redis":
            packages.append("redis@latest")
        if not packages:
            return ""
        data = {
            "$schema": "https://raw.githubusercontent.com/jetify-com/devbox/0.17.0/.schema/devbox.schema.json",
            "packages": packages,
            "shell": {"init_hook": init_hooks} if init_hooks else {},
        }
        devbox_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(devbox_json)

    def _generate_compose_yml(self, stack: dict) -> str:
        """Write a minimal docker-compose.yml from detected stack. Returns path or empty string."""
        compose_file = self.repo_path / "docker-compose.yml"
        if compose_file.exists():
            return ""
        services = {}
        if stack.get("db") == "postgresql":
            services["postgres"] = {
                "image": "postgres:15",
                "environment": {"POSTGRES_PASSWORD": "test", "POSTGRES_DB": "testdb"},
                "ports": ["5432:5432"],
            }
        if stack.get("cache") == "redis":
            services["redis"] = {"image": "redis:7", "ports": ["6379:6379"]}
        if not services:
            return ""
        try:
            import yaml
            data = {"version": "3.8", "services": services}
            compose_file.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
            return str(compose_file)
        except ImportError:
            return ""

    def _compute_gaps(self, stack: dict) -> list[ServiceGap]:
        """Build gap list from detected stack needs."""
        gaps = []
        if stack.get("db") == "postgresql":
            gaps.append(ServiceGap(service="postgresql", port=5432, reason="tests require database", suggested_fix="Add postgresql to devbox.json packages or create docker-compose.yml"))
        if stack.get("cache") == "redis":
            gaps.append(ServiceGap(service="redis", port=6379, reason="tests require cache", suggested_fix="Add redis to devbox.json packages or create docker-compose.yml"))
        return gaps

    def _detect_seed(self) -> SeedInfo:
        """Detect seed command from project files."""
        repo = self.repo_path
        # Prisma
        if (repo / "prisma" / "seed.ts").exists() or (repo / "prisma" / "seed.js").exists():
            return SeedInfo(command="npx prisma db seed", detection_confidence="high")
        # package.json scripts
        pkg_file = repo / "package.json"
        if pkg_file.exists():
            try:
                scripts = json.loads(pkg_file.read_text()).get("scripts", {})
                for key in ["db:seed", "seed", "db:seed:run"]:
                    if key in scripts:
                        return SeedInfo(command=f"npm run {key}", detection_confidence="high")
            except Exception:
                pass
        # Rails
        if (repo / "db" / "seeds.rb").exists():
            return SeedInfo(command="rails db:seed", detection_confidence="high")
        # Knex
        if (repo / "seeds").is_dir():
            return SeedInfo(command="npx knex seed:run", detection_confidence="medium")
        # Django fixtures
        fixtures_dir = repo / "fixtures"
        if fixtures_dir.is_dir():
            fixtures = list(fixtures_dir.glob("*.json"))
            if fixtures:
                return SeedInfo(command=f"python manage.py loaddata {fixtures[0].name}", detection_confidence="medium")
        # SQLite in-memory (no seed needed)
        import re
        for conf in repo.rglob("conftest.py"):
            try:
                if re.search(r"sqlite:///:memory:", conf.read_text()):
                    return SeedInfo(command="", detection_confidence="high")
            except Exception:
                pass
        return SeedInfo(command="", detection_confidence="none")

    def _store_to_ruflo(self, ctx: InfraContext) -> None:
        """Persist infra detection result to ruflo memory for future runs."""
        try:
            stack = self._detect_stack()
            framework = stack.get("framework", stack.get("runtime", "unknown"))
            service = stack.get("db", stack.get("cache", "unknown"))
            key = f"{framework}+{service}"
            value = json.dumps({
                "tier": ctx.tier.value,
                "confidence": ctx.confidence,
                "seed_command": ctx.seed.command,
                "seed_detection_confidence": ctx.seed.detection_confidence,
                "services_started": ctx.services_started,
            })
            subprocess.run(
                ["npx", "@claude-flow/cli@latest", "memory", "store",
                 "--key", key, "--value", value, "--namespace", "dirigent-infra"],
                capture_output=True, timeout=15,
            )
        except Exception:
            pass  # ruflo is optional — never block on it


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

        # NEW: run InfraDetector before anything else
        detector = InfraDetector(self.repo_path)
        ctx = detector.detect()
        logger.info(f"Infra tier: {ctx.tier.value} | confidence: {ctx.confidence}")

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

        # Step 3b: Generate ARCHITECTURE.md if it doesn't exist
        arch_path = self.repo_path / "ARCHITECTURE.md"
        if not arch_path.exists() and self.runner:
            logger.info("No ARCHITECTURE.md found — generating one")
            self.runner._run_claude("Run /dirigent:generate-architecture", timeout=600)
        elif arch_path.exists():
            logger.info("ARCHITECTURE.md exists — skipping generation")

        if harness is None:
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
