#!/usr/bin/env python3
"""Validate TestHarness JSON against the new strict schema. Standalone — stdlib only."""
import json
import sys

VALID_COMMAND_KEYS = {"build", "test", "e2e", "seed", "dev"}
VALID_ENV_SOURCES = {"doppler", "env", "hardcoded", "generated"}


def validate(path: str):
    errors = []
    warnings = []

    with open(path) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        errors.append("Root must be a JSON object")
        return errors, warnings

    # Required: commands (dict)
    if "commands" not in data:
        errors.append("Missing required field: 'commands'")
    elif not isinstance(data["commands"], dict):
        errors.append("'commands' must be an object")
    else:
        for key, cmd in data["commands"].items():
            if key not in VALID_COMMAND_KEYS:
                errors.append(f"commands.{key}: invalid key — must be one of {sorted(VALID_COMMAND_KEYS)}")
            if not isinstance(cmd, dict):
                errors.append(f"commands.{key}: must be an object")
                continue
            if "command" not in cmd or not isinstance(cmd.get("command"), str):
                errors.append(f"commands.{key}: missing or invalid 'command' (must be string)")
            if "explanation" not in cmd or not isinstance(cmd.get("explanation"), str):
                errors.append(f"commands.{key}: missing or invalid 'explanation' (must be string)")

    # Required: portal (object)
    if "portal" not in data:
        errors.append("Missing required field: 'portal'")
    elif not isinstance(data["portal"], dict):
        errors.append("'portal' must be an object")
    else:
        portal = data["portal"]
        if "start_command" not in portal or not isinstance(portal.get("start_command"), str):
            errors.append("portal.start_command: missing or invalid (must be string)")
        if "port" not in portal or not isinstance(portal.get("port"), int):
            errors.append("portal.port: missing or invalid (must be integer)")

    # Optional: env_vars (dict of objects)
    if "env_vars" in data:
        if not isinstance(data["env_vars"], dict):
            errors.append("'env_vars' must be an object")
        else:
            for name, var in data["env_vars"].items():
                prefix = f"env_vars.{name}"
                if not isinstance(var, dict):
                    errors.append(f"{prefix}: must be an object")
                    continue
                if "source" not in var:
                    errors.append(f"{prefix}: missing 'source'")
                elif var["source"] not in VALID_ENV_SOURCES:
                    errors.append(f"{prefix}.source: must be one of {sorted(VALID_ENV_SOURCES)}, got '{var['source']}'")

    # Optional: notes (string)
    if "notes" in data and not isinstance(data["notes"], str):
        errors.append("'notes' must be a string")

    # Optional: _sources (dict of strings)
    if "_sources" in data:
        if not isinstance(data["_sources"], dict):
            errors.append("'_sources' must be an object")
        else:
            for k, v in data["_sources"].items():
                if not isinstance(v, str):
                    errors.append(f"_sources.{k}: must be a string")

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
