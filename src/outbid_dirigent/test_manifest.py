"""
Test manifest — loads outbid-test-manifest.yaml and runs test suites.

Provides:
- Pydantic models for the manifest schema
- summary_for_prompt() for injection into planner/task prompts
- TestStepRunner for the dedicated TEST pipeline step
- ManifestGenerator for 3-way generation + consolidation
"""

import json
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger
from pydantic import BaseModel, Field, model_validator


# ── Manifest schema ──


class EnvVar(BaseModel):
    name: str
    source: str = ""
    secret: bool = False


class Prerequisite(BaseModel):
    name: str
    check: str
    setup_command: str = ""
    manual: bool = False
    install_hint: str = ""
    required_version: str = ""


class ReadyCheck(BaseModel):
    type: str = ""        # http, tcp, log, delay
    target: str = ""
    timeout: int = 30


class Endpoint(BaseModel):
    host: str = "localhost"
    port: int = 0
    protocol: str = "tcp"


class MockConfig(BaseModel):
    strategy: str = "stub"
    config: dict = Field(default_factory=dict)


class ComponentStart(BaseModel):
    command: str = ""
    working_dir: str = ""
    env: dict[str, str] = Field(default_factory=dict)
    ready_check: ReadyCheck = Field(default_factory=ReadyCheck)


class Component(BaseModel):
    name: str = ""
    type: str = ""  # database, cache, queue, external, backend, frontend, worker
    runtime: str = ""  # docker-compose, process
    start: ComponentStart | None = None
    # Legacy flat fields (still supported)
    start_cmd: str = ""
    stop_cmd: str = ""
    ready_check: str = ""
    ready_timeout: int = 30
    endpoint: Endpoint | None = None
    mock: MockConfig | None = None
    depends_on: list[str] = Field(default_factory=list)

    @property
    def effective_start_cmd(self) -> str:
        if self.start_cmd:
            return self.start_cmd
        if self.start and self.start.command:
            return self.start.command
        return ""

    @property
    def effective_ready_check(self) -> str:
        if isinstance(self.ready_check, str) and self.ready_check:
            return self.ready_check
        if self.start and self.start.ready_check.target:
            rc = self.start.ready_check
            if rc.type == "http":
                return f"curl -sf {rc.target}"
            if rc.type == "tcp":
                host, _, port = rc.target.partition(":")
                return f"nc -z {host} {port}"
            return rc.target
        return ""

    @property
    def is_mocked(self) -> bool:
        return self.mock is not None


class Gap(BaseModel):
    area: str = ""
    reason: str = ""
    description: str = ""
    mitigation: str = ""
    risk: str = "medium"

    def __str__(self) -> str:
        if self.area:
            parts = [self.area]
            if self.reason:
                parts.append(f"({self.reason})")
            if self.risk and self.risk != "medium":
                parts.append(f"[{self.risk}]")
            return " ".join(parts)
        return self.description or ""


class TestCommand(BaseModel):
    name: str
    run: str
    expect: str = "exit_0"
    expect_value: str = ""
    needs: list[str] = Field(default_factory=list)


class TestLevelConfig(BaseModel):
    pre_commands: list[str] = Field(default_factory=list)
    commands: list[TestCommand] = Field(default_factory=list)


class Prerequisites(BaseModel):
    tools: list[Prerequisite] = Field(default_factory=list)
    env_vars: list[EnvVar] = Field(default_factory=list)


class TestManifest(BaseModel):
    test_level: int = 1
    prerequisites: list[Prerequisite] | Prerequisites = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)
    levels: dict[str, TestLevelConfig] = Field(default_factory=dict)
    gaps: list[str | Gap] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def normalize(cls, data):
        if not isinstance(data, dict):
            return data

        # Components: dict-keyed -> list
        comps = data.get('components')
        if isinstance(comps, dict):
            data['components'] = [
                {'name': k, **(v if isinstance(v, dict) else {})}
                for k, v in comps.items()
            ]

        # Prerequisites: dict with 'tools' key -> use tools as the list
        prereqs = data.get('prerequisites')
        if isinstance(prereqs, dict) and 'tools' in prereqs:
            # Keep as Prerequisites object
            pass
        elif isinstance(prereqs, dict):
            # Unknown dict format — try to convert
            data['prerequisites'] = list(prereqs.values()) if prereqs else []

        # Gaps: list of dicts -> list of Gap objects (pydantic handles this)
        # Gaps: list of strings -> keep as-is (pydantic handles this)

        return data

    @property
    def prerequisite_tools(self) -> list[Prerequisite]:
        if isinstance(self.prerequisites, Prerequisites):
            return self.prerequisites.tools
        return self.prerequisites if isinstance(self.prerequisites, list) else []

    @property
    def env_vars(self) -> list[EnvVar]:
        if isinstance(self.prerequisites, Prerequisites):
            return self.prerequisites.env_vars
        return []

    def mocked_components(self) -> list[Component]:
        return [c for c in self.components if c.is_mocked]

    def gap_strings(self) -> list[str]:
        return [str(g) if isinstance(g, Gap) else g for g in self.gaps]

    @classmethod
    def load(cls, repo_path: Path) -> Optional["TestManifest"]:
        """Load outbid-test-manifest.yaml from repo root. Returns None if missing/invalid."""
        manifest_path = repo_path / "outbid-test-manifest.yaml"
        if not manifest_path.exists():
            return None
        try:
            raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            if not raw or not isinstance(raw, dict):
                return None
            return cls.model_validate(raw)
        except Exception as e:
            logger.warning(f"Failed to parse test manifest: {e}")
            return None

    def summary_for_prompt(self) -> str:
        """Compact summary for injection into planner/task prompts."""
        lines = ["# Test-Infrastruktur (aus outbid-test-manifest.yaml)"]

        for level_name, level_cfg in self.levels.items():
            cmds = ", ".join(f"`{c.run}`" for c in level_cfg.commands)
            lines.append(f"- **{level_name.upper()}**: {cmds}")

        real_comps = [c for c in self.components if not c.is_mocked]
        if real_comps:
            comp_names = ", ".join(c.name for c in real_comps)
            lines.append(f"- **Benoetigte Services**: {comp_names}")

        mocked = self.mocked_components()
        if mocked:
            mock_names = ", ".join(c.name for c in mocked)
            lines.append(f"- **Auto-mocked (kein Setup noetig)**: {mock_names}")

        if self.gaps:
            lines.append(f"- **Bekannte Gaps**: {', '.join(self.gap_strings())}")

        return "\n".join(lines)

    def commands_for_level(self, level: str) -> list[TestCommand]:
        """Get commands for a given level (e.g. 'l1', 'l2')."""
        cfg = self.levels.get(level)
        return cfg.commands if cfg else []

    def summary_for_task(self, test_level: str) -> str:
        """Context block for an individual task prompt."""
        lines = ["# Test-Infrastruktur (aus Test-Manifest)"]

        lines.append("\nVerfuegbare Test-Commands:")
        for level_name, level_cfg in self.levels.items():
            for cmd in level_cfg.commands:
                needs = f" (braucht: {', '.join(cmd.needs)})" if cmd.needs else ""
                lines.append(f"- `{cmd.run}` ({cmd.name}){needs}")

        real_comps = [c for c in self.components if not c.is_mocked]
        if real_comps:
            lines.append("\nBenoetigte Services fuer L2:")
            for comp in real_comps:
                start = comp.effective_start_cmd
                lines.append(f"- {comp.name} — `{start}`" if start else f"- {comp.name}")

        mocked = self.mocked_components()
        if mocked:
            lines.append("\nAuto-mocked Services (kein Setup noetig, in Tests automatisch gemockt):")
            for comp in mocked:
                note = comp.mock.config.get("note", "") if comp.mock and comp.mock.config else ""
                lines.append(f"- {comp.name}" + (f" — {note}" if note else ""))

        if self.gaps:
            lines.append("\nBekannte Gaps (NICHT versuchen zu loesen):")
            for gap in self.gaps:
                lines.append(f"- {gap}")

        if test_level:
            level_key = test_level.lower()
            cmds = self.commands_for_level(level_key)
            if cmds:
                cmd_strs = " und ".join(f"`{c.run}`" for c in cmds)
                lines.append(f"\nDein Task test_level: {test_level}")
                lines.append(f"-> Fuehre nach deinen Aenderungen {cmd_strs} aus um zu verifizieren.")
            else:
                lines.append(f"\nDein Task test_level: {test_level}")
        else:
            lines.append("\nKein Testing fuer diesen Task noetig.")

        return "\n".join(lines)


# ── Test step runner ──


@dataclass
class TestCommandResult:
    name: str
    command: str
    success: bool
    output: str = ""
    duration_seconds: float = 0


@dataclass
class TestStepResult:
    passed: bool
    results: list[TestCommandResult]
    components_started: list[str]
    skipped_levels: list[str]
    summary: str = ""


class TestStepRunner:
    """Runs the full test suite as a pipeline step."""

    def __init__(self, repo_path: Path, manifest: TestManifest):
        self.repo_path = repo_path
        self.manifest = manifest

    def run(self) -> TestStepResult:
        results: list[TestCommandResult] = []
        components_started: list[str] = []
        skipped_levels: list[str] = []

        # Check prerequisites
        if not self._check_prerequisites():
            return TestStepResult(
                passed=False, results=results,
                components_started=[], skipped_levels=[],
                summary="Prerequisites check failed",
            )

        # Start components
        components_started = self._start_components()

        # Run L1
        l1_results = self._run_level("l1")
        results.extend(l1_results)

        l1_passed = all(r.success for r in l1_results)
        if not l1_passed:
            self._stop_components(components_started)
            return TestStepResult(
                passed=False, results=results,
                components_started=components_started,
                skipped_levels=["l2"] if self.manifest.test_level >= 2 else [],
                summary="L1 tests failed",
            )

        # Run L2 if configured and components are healthy
        if self.manifest.test_level >= 2 and "l2" in self.manifest.levels:
            if self._components_healthy(components_started):
                l2_results = self._run_level("l2")
                results.extend(l2_results)
            else:
                skipped_levels.append("l2")
                logger.warning("Components not healthy, skipping L2")

        self._stop_components(components_started)

        all_passed = all(r.success for r in results)
        summary_parts = []
        for r in results:
            status = "PASS" if r.success else "FAIL"
            summary_parts.append(f"  [{status}] {r.name}: {r.command} ({r.duration_seconds:.1f}s)")

        return TestStepResult(
            passed=all_passed,
            results=results,
            components_started=components_started,
            skipped_levels=skipped_levels,
            summary="\n".join(summary_parts),
        )

    def _check_prerequisites(self) -> bool:
        for prereq in self.manifest.prerequisite_tools:
            if prereq.manual:
                continue
            try:
                result = subprocess.run(
                    prereq.check, shell=True, cwd=self.repo_path,
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode != 0:
                    if prereq.setup_command:
                        logger.info(f"Setting up prerequisite: {prereq.name}")
                        subprocess.run(
                            prereq.setup_command, shell=True, cwd=self.repo_path,
                            capture_output=True, text=True, timeout=120,
                        )
                    else:
                        logger.error(f"Prerequisite failed: {prereq.name} ({prereq.check})")
                        return False
            except Exception as e:
                logger.error(f"Prerequisite check error: {prereq.name}: {e}")
                return False
        return True

    def _start_components(self) -> list[str]:
        started = []
        for comp in self.manifest.components:
            start_cmd = comp.effective_start_cmd
            if not start_cmd:
                continue
            # Check dependencies
            if any(dep not in started for dep in comp.depends_on):
                logger.warning(f"Skipping {comp.name}: dependency not started")
                continue
            try:
                subprocess.Popen(
                    start_cmd, shell=True, cwd=self.repo_path,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                ready_check = comp.effective_ready_check
                if ready_check:
                    if self._wait_for_ready(comp):
                        started.append(comp.name)
                        logger.info(f"Component started: {comp.name}")
                    else:
                        logger.warning(f"Component {comp.name} did not become ready")
                else:
                    started.append(comp.name)
            except Exception as e:
                logger.warning(f"Failed to start {comp.name}: {e}")
        return started

    def _wait_for_ready(self, comp: Component) -> bool:
        timeout = comp.ready_timeout
        if comp.start and comp.start.ready_check.timeout:
            timeout = comp.start.ready_check.timeout
        ready_check = comp.effective_ready_check
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                result = subprocess.run(
                    ready_check, shell=True, cwd=self.repo_path,
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def _stop_components(self, started: list[str]):
        for comp in reversed(self.manifest.components):
            if comp.name in started and comp.stop_cmd:
                try:
                    subprocess.run(
                        comp.stop_cmd, shell=True, cwd=self.repo_path,
                        capture_output=True, text=True, timeout=30,
                    )
                except Exception as e:
                    logger.warning(f"Failed to stop {comp.name}: {e}")

    def _components_healthy(self, started: list[str]) -> bool:
        for comp in self.manifest.components:
            ready_check = comp.effective_ready_check
            if comp.name in started and ready_check:
                try:
                    result = subprocess.run(
                        ready_check, shell=True, cwd=self.repo_path,
                        capture_output=True, text=True, timeout=5,
                    )
                    if result.returncode != 0:
                        return False
                except Exception:
                    return False
        return True

    def _run_level(self, level: str) -> list[TestCommandResult]:
        cfg = self.manifest.levels.get(level)
        if not cfg:
            return []

        # Pre-commands
        for pre_cmd in cfg.pre_commands:
            subprocess.run(
                pre_cmd, shell=True, cwd=self.repo_path,
                capture_output=True, text=True, timeout=120,
            )

        results = []
        for cmd in cfg.commands:
            start = time.time()
            try:
                proc = subprocess.run(
                    cmd.run, shell=True, cwd=self.repo_path,
                    capture_output=True, text=True, timeout=600,
                )
                duration = time.time() - start
                success = proc.returncode == 0 if cmd.expect == "exit_0" else True
                output = proc.stdout[-2000:] if len(proc.stdout) > 2000 else proc.stdout
                if not success:
                    output += "\n--- STDERR ---\n" + (proc.stderr[-1000:] if len(proc.stderr) > 1000 else proc.stderr)
                results.append(TestCommandResult(
                    name=cmd.name, command=cmd.run,
                    success=success, output=output, duration_seconds=duration,
                ))
                logger.info(f"  {'PASS' if success else 'FAIL'} {cmd.name} ({duration:.1f}s)")
            except subprocess.TimeoutExpired:
                results.append(TestCommandResult(
                    name=cmd.name, command=cmd.run,
                    success=False, output="Timeout after 600s",
                    duration_seconds=600,
                ))
            except Exception as e:
                results.append(TestCommandResult(
                    name=cmd.name, command=cmd.run,
                    success=False, output=str(e),
                    duration_seconds=time.time() - start,
                ))
        return results


# ── Manifest generator (3-way + consolidation) ──

MANIFEST_SCHEMA_EXAMPLE = """\
# outbid-test-manifest.yaml — describes the test infrastructure for this repo.
# The Dirigent reads this to know what tests exist and how to run them.

test_level: 2  # 1 = L1 only, 2 = L1+L2

prerequisites:
  tools:
    - name: python
      check: "python3 --version"
      install_hint: "brew install python@3.12"
      required_version: ">=3.10"
    - name: docker
      check: "docker --version"
      install_hint: "brew install --cask docker"
    - name: doppler
      check: "doppler --version"
      install_hint: "brew install dopplerhq/cli/doppler && doppler login"
  env_vars:
    - name: DATABASE_URL
      source: "Doppler — auto-injected via doppler run"
      secret: true
    - name: OPENAI_API_KEY
      source: "Doppler"
      secret: true

# Components as dict keyed by name
components:
  postgres:
    type: database
    runtime: docker-compose
    start:
      command: "docker compose up -d postgres"
      ready_check:
        type: tcp
        target: "localhost:5432"
        timeout: 30
    endpoint:
      host: localhost
      port: 5432
      protocol: tcp

  redis:
    type: cache
    runtime: docker-compose
    start:
      command: "docker compose up -d redis"
      ready_check:
        type: tcp
        target: "localhost:6379"
        timeout: 15

  # External APIs that are auto-mocked in tests
  openai_api:
    type: external
    mock:
      strategy: stub
      config:
        note: "Auto-mocked in pytest via conftest.py"

levels:
  l1:
    pre_commands:
      - "uv pip install -e '.[dev]'"
    commands:
      - name: unit-tests
        run: "pytest tests/unit -x -q"
        expect: exit_0
      - name: lint
        run: "ruff check ."
        expect: exit_0
      - name: type-check
        run: "pyright src/"
        expect: exit_0
  l2:
    pre_commands:
      - "doppler run -- docker compose up -d postgres redis"
      - "sleep 5"
    commands:
      - name: integration-tests
        run: "doppler run -- pytest tests/integration -x -q"
        expect: exit_0
        needs: [postgres, redis]
      - name: health-check
        run: "curl -sf http://localhost:8000/health"
        expect: exit_0
        needs: [postgres]

gaps:
  - area: "E2E/Playwright"
    reason: "not_configured"
    description: "No browser-based end-to-end tests"
    mitigation: "Manual QA via staging"
    risk: medium
  - area: "Load testing"
    reason: "requires_hardware"
    description: "No performance/load testing setup"
    mitigation: "Monitor production metrics"
    risk: low
"""

GENERATE_PROMPT = """\
Analysiere dieses Repository und erstelle ein outbid-test-manifest.yaml.

Das Manifest beschreibt die Test-Infrastruktur: welche Tests existieren,
wie man sie ausfuehrt, welche Services gebraucht werden, und was fehlt (gaps).

## Schema und Beispiel
```yaml
{schema}
```

## Regeln
- Nur Commands auflisten die TATSAECHLICH funktionieren (Dateien/Config existiert)
- prerequisites: Was installiert sein muss (check-Command muss funktionieren)
- components: Externe Services (DB, Cache, etc.) — nur wenn docker-compose.yml o.ae. existiert
- levels.l1: Schnelle Tests (unit tests, lint, type check) — kein externer Service noetig
- levels.l2: Integration tests — brauchen components
- gaps: Was NICHT vorhanden ist aber sinnvoll waere
- test_level: 1 wenn nur L1 verfuegbar, 2 wenn L1+L2 verfuegbar
- Sei konservativ: lieber eine Luecke als Gap dokumentieren als einen Command der nicht funktioniert

Analysiere die Codebase gruendlich:
- Schau dir pyproject.toml, package.json, Makefile, justfile, tox.ini, setup.cfg an
- Pruefe ob test-Verzeichnisse existieren
- Pruefe ob Linter/Formatter konfiguriert sind (ruff, eslint, prettier, etc.)
- Pruefe ob Docker/docker-compose vorhanden ist
- Pruefe ob CI-Config existiert (.github/workflows, .gitlab-ci.yml, etc.)

Gib NUR das YAML aus, keine Erklaerung, kein Markdown-Fence. Reines YAML.
"""

CONSOLIDATE_PROMPT = """\
Du bekommst 3 Versionen eines outbid-test-manifest.yaml fuer dasselbe Repository.
Konsolidiere sie zu einer einzigen, optimalen Version.

## Regeln
- Nimm die UNION aller korrekt erkannten Test-Commands
- Wenn sich Versionen widersprechen: waehle die konservativere Variante
- Wenn ein Command in 2+ Versionen vorkommt, ist er wahrscheinlich korrekt
- Wenn ein Command nur in 1 Version vorkommt, pruefe ob er plausibel ist
- gaps: Vereinige alle erkannten Gaps (dedupliziert)
- Bevorzuge spezifischere Commands (z.B. "pytest tests/unit" > "pytest")
- test_level: Setze auf das Maximum das plausibel funktioniert

## Version A
```yaml
{version_a}
```

## Version B
```yaml
{version_b}
```

## Version C
```yaml
{version_c}
```

Gib NUR das konsolidierte YAML aus, keine Erklaerung, kein Markdown-Fence. Reines YAML.
"""


class ManifestGenerator:
    """Generates outbid-test-manifest.yaml via 3 parallel Claude runs + consolidation."""

    def __init__(self, repo_path: Path, runner: "TaskRunner"):
        self.repo_path = repo_path
        self.runner = runner

    def generate(self) -> Optional[TestManifest]:
        """Run 3 sonnet generations in parallel, consolidate with haiku."""
        logger.info("Generating test manifest (3x sonnet + haiku consolidation)...")

        prompt = GENERATE_PROMPT.format(schema=MANIFEST_SCHEMA_EXAMPLE)

        # Run 3 generations in parallel
        versions: list[str] = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(self._generate_one, prompt, i)
                for i in range(3)
            ]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    versions.append(result)

        if len(versions) < 2:
            logger.error(f"Only {len(versions)}/3 manifest generations succeeded, need at least 2")
            if len(versions) == 1:
                # Fallback: use the single version
                return self._parse_and_save(versions[0])
            return None

        logger.info(f"{len(versions)}/3 versions generated, consolidating with haiku...")

        # Pad to 3 if only 2 succeeded
        while len(versions) < 3:
            versions.append(versions[0])

        # Consolidate
        consolidate_prompt = CONSOLIDATE_PROMPT.format(
            version_a=versions[0],
            version_b=versions[1],
            version_c=versions[2],
        )
        success, stdout, stderr = self.runner._run_claude(
            consolidate_prompt, model="haiku", timeout=120,
        )
        if not success:
            logger.warning(f"Consolidation failed: {stderr}, using first version as fallback")
            return self._parse_and_save(versions[0])

        consolidated = self._extract_yaml(stdout)
        if not consolidated:
            logger.warning("Could not extract YAML from consolidation, using first version")
            return self._parse_and_save(versions[0])

        return self._parse_and_save(consolidated)

    def _generate_one(self, prompt: str, index: int) -> Optional[str]:
        """Generate one version of the manifest."""
        logger.info(f"  Manifest generation {index + 1}/3 starting...")
        success, stdout, stderr = self.runner._run_claude(
            prompt, model="sonnet", timeout=180,
        )
        if not success:
            logger.warning(f"  Manifest generation {index + 1}/3 failed: {stderr[:100]}")
            return None

        yaml_content = self._extract_yaml(stdout)
        if yaml_content:
            logger.info(f"  Manifest generation {index + 1}/3 done ({len(yaml_content)} chars)")
        else:
            logger.warning(f"  Manifest generation {index + 1}/3: no valid YAML in output")
        return yaml_content

    def _extract_yaml(self, text: str) -> Optional[str]:
        """Extract YAML from Claude output (may be wrapped in markdown fences)."""
        # Try stripping markdown fences first
        import re
        fence_match = re.search(r"```(?:ya?ml)?\s*\n(.+?)```", text, re.DOTALL)
        candidate = fence_match.group(1).strip() if fence_match else text.strip()

        # Validate it's parseable YAML
        try:
            parsed = yaml.safe_load(candidate)
            if isinstance(parsed, dict):
                return candidate
        except Exception:
            pass

        # Try the raw text
        try:
            parsed = yaml.safe_load(text.strip())
            if isinstance(parsed, dict):
                return text.strip()
        except Exception:
            pass

        return None

    def _parse_and_save(self, yaml_content: str) -> Optional[TestManifest]:
        """Parse YAML, validate as TestManifest, save to repo."""
        try:
            raw = yaml.safe_load(yaml_content)
            manifest = TestManifest.model_validate(raw)
        except Exception as e:
            logger.error(f"Failed to validate manifest: {e}")
            return None

        # Save to repo root
        manifest_path = self.repo_path / "outbid-test-manifest.yaml"
        manifest_path.write_text(yaml_content, encoding="utf-8")
        logger.info(f"Test manifest saved: {manifest_path}")
        logger.info(f"  Levels: {list(manifest.levels.keys())}")
        logger.info(f"  Components: {[c.name for c in manifest.components]}")
        logger.info(f"  Gaps: {manifest.gaps}")

        return manifest


# Forward reference for type hint
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from outbid_dirigent.task_runner import TaskRunner
