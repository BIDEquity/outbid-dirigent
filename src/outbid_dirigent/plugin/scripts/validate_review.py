#!/usr/bin/env python3
"""Validate Review JSON against the Pydantic schema. Standalone — no imports beyond stdlib."""
import json
import re
import sys

VALID_VERDICTS = {"pass", "fail"}
VALID_CR_VERDICTS = {"pass", "fail", "warn"}
VALID_SEVERITIES = {"critical", "warn", "info"}


def validate(path: str):
    errors = []
    warnings = []

    with open(path) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        errors.append("Root must be a JSON object")
        return errors, warnings

    # Required: phase_id
    if "phase_id" not in data:
        errors.append("Missing required field: 'phase_id'")
    elif not isinstance(data["phase_id"], str) or not data["phase_id"].strip():
        errors.append("'phase_id' must be a non-empty string")

    # Required: verdict
    if "verdict" not in data:
        errors.append("Missing required field: 'verdict'")
    elif data["verdict"] not in VALID_VERDICTS:
        errors.append(f"'verdict' must be one of {sorted(VALID_VERDICTS)}, got '{data['verdict']}'")

    # Optional int fields
    for field in ("iteration", "tests_run", "tests_skipped_infra"):
        if field in data and not isinstance(data[field], int):
            errors.append(f"'{field}' must be an integer")

    # Optional str fields
    for field in ("confidence", "infra_tier", "caveat", "summary"):
        if field in data and not isinstance(data[field], str):
            errors.append(f"'{field}' must be a string")

    # Optional: criteria_results
    if "criteria_results" in data:
        cr = data["criteria_results"]
        if not isinstance(cr, list):
            errors.append("'criteria_results' must be a list")
        else:
            for i, item in enumerate(cr):
                prefix = f"criteria_results[{i}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix}: must be an object")
                    continue

                if "ac_id" not in item:
                    errors.append(f"{prefix}: missing 'ac_id'")
                elif not isinstance(item["ac_id"], str):
                    errors.append(f"{prefix}.ac_id: must be a string")

                if "verdict" not in item:
                    errors.append(f"{prefix}: missing 'verdict'")
                elif item["verdict"] not in VALID_CR_VERDICTS:
                    errors.append(f"{prefix}.verdict: must be one of {sorted(VALID_CR_VERDICTS)}, got '{item['verdict']}'")

                # Optional: notes
                if "notes" in item and not isinstance(item["notes"], str):
                    errors.append(f"{prefix}.notes: must be a string")

                # Optional: verification_tier
                if "verification_tier" in item and not isinstance(item["verification_tier"], str):
                    errors.append(f"{prefix}.verification_tier: must be a string")

                # Optional: evidence
                if "evidence" in item:
                    ev = item["evidence"]
                    if not isinstance(ev, list):
                        errors.append(f"{prefix}.evidence: must be a list")
                    else:
                        for j, e in enumerate(ev):
                            eprefix = f"{prefix}.evidence[{j}]"
                            if not isinstance(e, dict):
                                errors.append(f"{eprefix}: must be an object")
                                continue
                            if "command" not in e:
                                errors.append(f"{eprefix}: missing 'command'")
                            elif not isinstance(e["command"], str):
                                errors.append(f"{eprefix}.command: must be a string")
                            if "exit_code" not in e:
                                errors.append(f"{eprefix}: missing 'exit_code'")
                            elif not isinstance(e["exit_code"], int):
                                errors.append(f"{eprefix}.exit_code: must be an integer")

            # Warn if verdict=="pass" but any criteria_result has empty evidence
            top_verdict = data.get("verdict")
            if top_verdict == "pass":
                for i, item in enumerate(cr):
                    if isinstance(item, dict):
                        ev = item.get("evidence")
                        if ev is None or (isinstance(ev, list) and len(ev) == 0):
                            ac_id = item.get("ac_id", f"[{i}]")
                            warnings.append(f"verdict='pass' but criteria_results[{i}] ({ac_id}) has no evidence")

    # Optional: findings
    if "findings" in data:
        findings = data["findings"]
        if not isinstance(findings, list):
            errors.append("'findings' must be a list")
        else:
            for i, item in enumerate(findings):
                prefix = f"findings[{i}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix}: must be an object")
                    continue

                if "severity" not in item:
                    errors.append(f"{prefix}: missing 'severity'")
                elif item["severity"] not in VALID_SEVERITIES:
                    errors.append(f"{prefix}.severity: must be one of {sorted(VALID_SEVERITIES)}, got '{item['severity']}'")

                if "file" not in item:
                    errors.append(f"{prefix}: missing 'file'")
                elif not isinstance(item["file"], str):
                    errors.append(f"{prefix}.file: must be a string")

                if "description" not in item:
                    errors.append(f"{prefix}: missing 'description'")
                elif not isinstance(item["description"], str):
                    errors.append(f"{prefix}.description: must be a string")

                # Optional: line
                if "line" in item and not isinstance(item["line"], int):
                    errors.append(f"{prefix}.line: must be an integer")

                # Optional: suggestion
                if "suggestion" in item and not isinstance(item["suggestion"], str):
                    errors.append(f"{prefix}.suggestion: must be a string")

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
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
