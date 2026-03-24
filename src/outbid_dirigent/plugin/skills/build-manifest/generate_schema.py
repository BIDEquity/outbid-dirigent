#!/usr/bin/env python3
"""Regenerate schema.json from the canonical Pydantic models in test_manifest.py.

Usage:
    python generate_schema.py
    # or from repo root:
    python src/outbid_dirigent/plugin/skills/build-manifest/generate_schema.py
"""

import json
from pathlib import Path

from outbid_dirigent.test_manifest import TestManifest

DESCRIPTIONS = {
    # Root
    ("TestManifest", ""): "Outbid test manifest — describes test infrastructure, components, and local preview config for a repository.",
    ("TestManifest", "test_level"): "1 = L1 only, 2 = L1+L2",
    ("TestManifest", "components"): "Also accepts dict keyed by component name",
    ("TestManifest", "levels"): "Keys: l1, l2",
    # Component
    ("Component", "type"): "database, cache, queue, external, backend, frontend, worker",
    ("Component", "runtime"): "docker-compose, process",
    ("Component", "start_cmd"): "Legacy flat field — prefer start.command",
    ("Component", "ready_check"): "Legacy flat field — prefer start.ready_check",
    ("Component", "mock"): "If set, component is auto-mocked in tests (no real service needed)",
    # Prerequisite
    ("Prerequisite", "check"): "Shell command that proves the tool is installed",
    ("Prerequisite", "setup_command"): "Optional auto-install command",
    ("Prerequisite", "manual"): "If true, skip automated check",
    ("Prerequisite", "install_hint"): "Human-readable install instructions",
    ("Prerequisite", "required_version"): "e.g. >=3.10",
    # EnvVar
    ("EnvVar", "source"): "Where this env var comes from (e.g. 'Doppler', '.env')",
    # ReadyCheck
    ("ReadyCheck", "type"): "http, tcp, log, delay",
    ("ReadyCheck", "target"): "e.g. localhost:5432 or http://localhost:8000/health",
    # TestCommand
    ("TestCommand", "name"): "e.g. unit-tests, lint",
    ("TestCommand", "run"): "Shell command to execute",
    ("TestCommand", "expect"): "exit_0 = must exit 0",
    ("TestCommand", "needs"): "Component names that must be running",
    # TestLevelConfig
    ("TestLevelConfig", "pre_commands"): "Run before test commands (install, migrate, etc.)",
    # MockConfig
    ("MockConfig", "strategy"): "stub, record, passthrough",
    # Gap
    ("Gap", ""): "A known gap in test coverage",
    ("Gap", "area"): "e.g. E2E/Playwright, Load testing",
    ("Gap", "reason"): "e.g. not_configured, requires_hardware",
    ("Gap", "risk"): "low, medium, high",
    # PreviewConfig
    ("PreviewConfig", ""): "How to start the app locally for workspace preview",
    ("PreviewConfig", "start_command"): "The dev-server start command",
    ("PreviewConfig", "port"): "Dev server port",
    ("PreviewConfig", "framework"): "Detected framework (Next.js, FastAPI, Django, etc.)",
    ("PreviewConfig", "health_check"): "Health endpoint path, e.g. /health",
    ("PreviewConfig", "setup_steps"): "Commands to run before start (install, migrate, seed)",
    # ReadinessScore
    ("ReadinessScore", ""): "Agentic development readiness assessment (0-10)",
    ("ReadinessScore", "score"): "0-10 score indicating how well-equipped this repo is for autonomous AI development",
    ("ReadinessScore", "rationale"): "1-2 sentence explanation of the score",
}


def inject_descriptions(schema: dict) -> dict:
    """Inject human-readable descriptions into the generated JSON Schema."""
    # Root level
    root_desc = DESCRIPTIONS.get(("TestManifest", ""))
    if root_desc:
        schema["description"] = root_desc

    for prop_name, prop_def in schema.get("properties", {}).items():
        desc = DESCRIPTIONS.get(("TestManifest", prop_name))
        if desc:
            prop_def["description"] = desc

    # $defs
    for type_name, type_def in schema.get("$defs", {}).items():
        type_desc = DESCRIPTIONS.get((type_name, ""))
        if type_desc:
            type_def["description"] = type_desc

        for prop_name, prop_def in type_def.get("properties", {}).items():
            desc = DESCRIPTIONS.get((type_name, prop_name))
            if desc:
                prop_def["description"] = desc

            # Special: Gap.risk -> add enum
            if type_name == "Gap" and prop_name == "risk":
                prop_def["enum"] = ["low", "medium", "high"]

    return schema


def main():
    schema = TestManifest.model_json_schema()

    # Add JSON Schema meta
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://outbid.dev/schemas/test-manifest.json"

    schema = inject_descriptions(schema)

    out_path = Path(__file__).parent / "schema.json"
    out_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
