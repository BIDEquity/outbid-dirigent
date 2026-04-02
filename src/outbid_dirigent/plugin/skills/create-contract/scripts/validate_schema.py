#!/usr/bin/env python3
"""Validate Contract JSON against the Pydantic schema. Standalone — no imports beyond stdlib."""
import json
import re
import sys

VALID_TOP_LEVEL_KEYS = {
    "phase_id",
    "phase_name",
    "objective",
    "acceptance_criteria",
    "quality_gates",
    "out_of_scope",
    "expected_files",
}

VALID_LAYERS = {"structural", "behavioral", "boundary"}


def validate(path: str):
    errors = []
    warnings = []

    with open(path) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        errors.append("Root must be a JSON object")
        return errors, warnings

    # Reject unknown top-level keys
    unknown_keys = set(data.keys()) - VALID_TOP_LEVEL_KEYS
    if unknown_keys:
        errors.append(f"Unknown top-level keys: {sorted(unknown_keys)} — did you mean 'acceptance_criteria'?")

    # Required fields
    for field in ("phase_id", "phase_name", "objective"):
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
        elif not isinstance(data[field], str) or not data[field].strip():
            errors.append(f"'{field}' must be a non-empty string")

    # acceptance_criteria
    if "acceptance_criteria" not in data:
        errors.append("Missing required field: 'acceptance_criteria'")
    else:
        ac = data["acceptance_criteria"]
        if not isinstance(ac, list):
            errors.append("'acceptance_criteria' must be a list")
        else:
            if len(ac) < 1:
                errors.append("'acceptance_criteria' must have at least 1 item")
            if len(ac) > 8:
                errors.append(f"'acceptance_criteria' has {len(ac)} items; maximum is 8")

            structural_count = 0
            behavioral_count = 0

            for i, criterion in enumerate(ac):
                prefix = f"acceptance_criteria[{i}]"
                if not isinstance(criterion, dict):
                    errors.append(f"{prefix}: must be an object")
                    continue

                # id
                if "id" not in criterion:
                    errors.append(f"{prefix}: missing 'id'")
                elif not isinstance(criterion["id"], str):
                    errors.append(f"{prefix}.id: must be a string")
                elif not re.fullmatch(r"AC-\d+-\d+", criterion["id"]):
                    errors.append(f"{prefix}.id: '{criterion['id']}' does not match AC-\\d+-\\d+")

                # description
                if "description" not in criterion:
                    errors.append(f"{prefix}: missing 'description'")
                elif not isinstance(criterion["description"], str) or not criterion["description"].strip():
                    errors.append(f"{prefix}.description: must be a non-empty string")

                # verification
                if "verification" not in criterion:
                    errors.append(f"{prefix}: missing 'verification'")
                elif not isinstance(criterion["verification"], str):
                    errors.append(f"{prefix}.verification: must be a string")
                elif not criterion["verification"].startswith("Run: "):
                    errors.append(f"{prefix}.verification: must start with 'Run: ' (got '{criterion['verification'][:20]}...')")

                # layer
                if "layer" not in criterion:
                    errors.append(f"{prefix}: missing 'layer'")
                elif criterion["layer"] not in VALID_LAYERS:
                    errors.append(f"{prefix}.layer: '{criterion['layer']}' must be one of {sorted(VALID_LAYERS)}")
                else:
                    if criterion["layer"] == "structural":
                        structural_count += 1
                    elif criterion["layer"] == "behavioral":
                        behavioral_count += 1

            if structural_count > 2:
                errors.append(f"Too many structural criteria: {structural_count} (max 2)")
            if behavioral_count < 1:
                errors.append("At least 1 behavioral criterion is required")

    # Optional: quality_gates
    if "quality_gates" in data:
        qg = data["quality_gates"]
        if not isinstance(qg, list):
            errors.append("'quality_gates' must be a list")
        else:
            for i, item in enumerate(qg):
                if not isinstance(item, str):
                    errors.append(f"quality_gates[{i}]: must be a string")

    # Optional: out_of_scope
    if "out_of_scope" in data:
        oos = data["out_of_scope"]
        if not isinstance(oos, list):
            errors.append("'out_of_scope' must be a list")
        else:
            for i, item in enumerate(oos):
                if not isinstance(item, str):
                    errors.append(f"out_of_scope[{i}]: must be a string")

    # Optional: expected_files
    if "expected_files" in data:
        ef = data["expected_files"]
        if not isinstance(ef, list):
            errors.append("'expected_files' must be a list")
        else:
            for i, item in enumerate(ef):
                prefix = f"expected_files[{i}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix}: must be an object")
                    continue
                if "path" not in item:
                    errors.append(f"{prefix}: missing 'path'")
                elif not isinstance(item["path"], str):
                    errors.append(f"{prefix}.path: must be a string")
                if "change" not in item:
                    errors.append(f"{prefix}: missing 'change'")
                elif not isinstance(item["change"], str):
                    errors.append(f"{prefix}.change: must be a string")

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
