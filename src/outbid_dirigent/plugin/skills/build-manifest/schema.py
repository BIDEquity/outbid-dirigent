# Canonical Pydantic schema for outbid-test-manifest.yaml
# This is the source of truth — the Dirigent validates manifests against these models.
# Keep in sync with src/outbid_dirigent/test_manifest.py

from pydantic import BaseModel, Field


class EnvVar(BaseModel):
    name: str
    source: str = ""
    secret: bool = False


class Prerequisite(BaseModel):
    name: str
    check: str                    # shell command that proves the tool is installed
    setup_command: str = ""       # optional auto-install command
    manual: bool = False          # if true, skip automated check
    install_hint: str = ""        # human-readable install instructions
    required_version: str = ""    # e.g. ">=3.10"


class ReadyCheck(BaseModel):
    type: str = ""                # http, tcp, log, delay
    target: str = ""              # e.g. "localhost:5432" or "http://localhost:8000/health"
    timeout: int = 30


class Endpoint(BaseModel):
    host: str = "localhost"
    port: int = 0
    protocol: str = "tcp"


class MockConfig(BaseModel):
    strategy: str = "stub"        # stub, record, passthrough
    config: dict = Field(default_factory=dict)  # e.g. {"note": "mocked in conftest.py"}


class ComponentStart(BaseModel):
    command: str = ""
    working_dir: str = ""
    env: dict[str, str] = Field(default_factory=dict)
    ready_check: ReadyCheck = Field(default_factory=ReadyCheck)


class Component(BaseModel):
    name: str = ""
    type: str = ""                # database, cache, queue, external, backend, frontend, worker
    runtime: str = ""             # docker-compose, process
    start: ComponentStart | None = None
    # Legacy flat fields (still supported)
    start_cmd: str = ""
    stop_cmd: str = ""
    ready_check: str = ""
    ready_timeout: int = 30
    endpoint: Endpoint | None = None
    mock: MockConfig | None = None       # if set, component is auto-mocked
    depends_on: list[str] = Field(default_factory=list)


class Gap(BaseModel):
    area: str = ""                # e.g. "E2E/Playwright", "Load testing"
    reason: str = ""              # e.g. "not_configured", "requires_hardware"
    description: str = ""         # human-readable description
    mitigation: str = ""          # how to cope without it
    risk: str = "medium"          # low, medium, high


class TestCommand(BaseModel):
    name: str                     # e.g. "unit-tests", "lint"
    run: str                      # shell command to execute
    expect: str = "exit_0"        # exit_0 = must exit 0
    expect_value: str = ""        # for custom expectations
    needs: list[str] = Field(default_factory=list)  # component names that must be running


class TestLevelConfig(BaseModel):
    pre_commands: list[str] = Field(default_factory=list)
    commands: list[TestCommand] = Field(default_factory=list)


class Prerequisites(BaseModel):
    tools: list[Prerequisite] = Field(default_factory=list)
    env_vars: list[EnvVar] = Field(default_factory=list)


class PreviewConfig(BaseModel):
    start_command: str = ""       # the dev-server start command
    port: int = 3000              # dev server port
    framework: str = ""           # detected framework (Next.js, FastAPI, Django, etc.)
    health_check: str = ""        # health endpoint path, e.g. "/health"
    setup_steps: list[str] = Field(default_factory=list)
    uses_doppler: bool = False
    doppler_project: str = ""
    doppler_config: str = ""


class ReadinessScore(BaseModel):
    score: int = 0                # 0-10, agentic development readiness
    rationale: str = ""           # 1-2 sentence explanation


class TestManifest(BaseModel):
    """Root object — represents the entire outbid-test-manifest.yaml file."""
    test_level: int = 1           # 1 = L1 only, 2 = L1+L2
    prerequisites: Prerequisites | list[Prerequisite] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)  # also accepts dict keyed by name
    levels: dict[str, TestLevelConfig] = Field(default_factory=dict)  # keys: "l1", "l2"
    gaps: list[Gap | str] = Field(default_factory=list)
    preview: PreviewConfig = Field(default_factory=PreviewConfig)
    readiness: ReadinessScore = Field(default_factory=ReadinessScore)
