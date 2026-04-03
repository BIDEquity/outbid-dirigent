#!/usr/bin/env python3
"""Validate TestHarness JSON. Standalone — stdlib only."""
import json
import re
import sys

VALID_AUTH_METHODS = {"none", "bearer_token", "cookie", "storage_state", "basic_auth", "api_key"}
VALID_E2E_FRAMEWORKS = {"playwright", "puppeteer", "cypress", "none"}
VALID_STATUSES = {"ready", "partial", "failed"}


def validate(path: str):
    errors = []
    warnings = []

    with open(path) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        errors.append("Root must be a JSON object")
        return errors, warnings

    # Required: base_url
    if "base_url" not in data:
        errors.append("Missing required field: 'base_url'")
    elif not isinstance(data["base_url"], str):
        errors.append("'base_url' must be a string")
    elif not data["base_url"].startswith("http"):
        errors.append(f"'base_url' must start with 'http', got '{data['base_url'][:20]}'")

    # Optional: port (int)
    if "port" in data:
        if not isinstance(data["port"], int):
            errors.append("'port' must be an integer")

    # Optional: status
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            errors.append(f"'status' must be one of {sorted(VALID_STATUSES)}, got '{data['status']}'")

    # Optional: infra_tier (str)
    if "infra_tier" in data and not isinstance(data["infra_tier"], str):
        errors.append("'infra_tier' must be a string")

    # Optional: testability_score (int 0-10)
    if "testability_score" in data:
        ts = data["testability_score"]
        if not isinstance(ts, int):
            errors.append("'testability_score' must be an integer")
        elif ts < 0 or ts > 10:
            errors.append(f"'testability_score' must be between 0 and 10, got {ts}")

    # Optional: auth.method
    if "auth" in data:
        auth = data["auth"]
        if not isinstance(auth, dict):
            errors.append("'auth' must be an object")
        elif "method" in auth:
            if auth["method"] not in VALID_AUTH_METHODS:
                errors.append(f"'auth.method' must be one of {sorted(VALID_AUTH_METHODS)}, got '{auth['method']}'")

    # Optional: health_checks
    if "health_checks" in data:
        hc = data["health_checks"]
        if not isinstance(hc, list):
            errors.append("'health_checks' must be a list")
        else:
            for i, item in enumerate(hc):
                prefix = f"health_checks[{i}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix}: must be an object")
                    continue
                if "name" not in item:
                    errors.append(f"{prefix}: missing 'name'")
                elif not isinstance(item["name"], str):
                    errors.append(f"{prefix}.name: must be a string")
                if "command" not in item:
                    errors.append(f"{prefix}: missing 'command'")
                elif not isinstance(item["command"], str):
                    errors.append(f"{prefix}.command: must be a string")

    # Optional: verification_commands
    if "verification_commands" in data:
        vc = data["verification_commands"]
        if not isinstance(vc, list):
            errors.append("'verification_commands' must be a list")
        else:
            for i, item in enumerate(vc):
                prefix = f"verification_commands[{i}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix}: must be an object")
                    continue
                if "name" not in item:
                    errors.append(f"{prefix}: missing 'name'")
                elif not isinstance(item["name"], str):
                    errors.append(f"{prefix}.name: must be a string")
                if "command" not in item:
                    errors.append(f"{prefix}: missing 'command'")
                elif not isinstance(item["command"], str):
                    errors.append(f"{prefix}.command: must be a string")

    # Optional: e2e_framework.framework
    if "e2e_framework" in data:
        ef = data["e2e_framework"]
        if not isinstance(ef, dict):
            errors.append("'e2e_framework' must be an object")
        elif "framework" in ef:
            if ef["framework"] not in VALID_E2E_FRAMEWORKS:
                errors.append(f"'e2e_framework.framework' must be one of {sorted(VALID_E2E_FRAMEWORKS)}, got '{ef['framework']}'")

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <json-file>", file=sys.stderr)
        sys.exit(1)
    try:
        errors, warnings = validate(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"VALIDATION FAILED: Invalid JSON: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"VALIDATION FAILED: File not found: {sys.argv[1]}")
        sys.exit(1)
    for w in warnings:
        print(f"  WARNING: {w}")
    if errors:
        print(f"VALIDATION FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
    print("VALIDATION PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
