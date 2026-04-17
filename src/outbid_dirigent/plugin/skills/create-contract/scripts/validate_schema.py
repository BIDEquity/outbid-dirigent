#!/usr/bin/env python3
"""Validate Contract JSON against the Pydantic schema. Standalone — no imports beyond stdlib."""
import json
import re
import sys

VALID_TOP_LEVEL_KEYS = {
    "phase_id",
    "phase_name",
    "phase_kind",
    "objective",
    "acceptance_criteria",
    "quality_gates",
    "out_of_scope",
    "expected_files",
}

VALID_LAYERS = {"structural", "unit", "user-journey", "edge-case"}
VALID_PHASE_KINDS = {"user-facing", "integration", "infrastructure"}

# Map legacy layer values (pre-UX-reframe) to current ones, for warnings only.
LEGACY_LAYER_RENAMES = {"behavioral": "user-journey", "boundary": "edge-case"}


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

    # phase_kind
    phase_kind = data.get("phase_kind")
    if phase_kind is None:
        errors.append(
            "Missing required field: 'phase_kind' "
            "(one of: user-facing | integration | infrastructure)"
        )
    elif phase_kind not in VALID_PHASE_KINDS:
        errors.append(
            f"'phase_kind' must be one of {sorted(VALID_PHASE_KINDS)} (got '{phase_kind}')"
        )

    # acceptance_criteria
    ac = data.get("acceptance_criteria")
    if ac is None:
        errors.append("Missing required field: 'acceptance_criteria'")
        ac = []
    elif not isinstance(ac, list):
        errors.append("'acceptance_criteria' must be a list")
        ac = []
    elif len(ac) < 1:
        errors.append("'acceptance_criteria' must have at least 1 item")

    counts = {"structural": 0, "unit": 0, "user-journey": 0, "edge-case": 0}

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
        else:
            layer = criterion["layer"]
            if layer in LEGACY_LAYER_RENAMES:
                warnings.append(
                    f"{prefix}.layer: '{layer}' is deprecated; "
                    f"use '{LEGACY_LAYER_RENAMES[layer]}'"
                )
                layer = LEGACY_LAYER_RENAMES[layer]  # count it under the new name
            if layer not in VALID_LAYERS:
                errors.append(
                    f"{prefix}.layer: '{criterion['layer']}' must be one of {sorted(VALID_LAYERS)}"
                )
            elif layer in counts:
                counts[layer] += 1

    # Phase-kind-aware quota checks
    if phase_kind == "user-facing":
        if len(ac) > 8:
            errors.append(f"user-facing phase: max 8 criteria (got {len(ac)})")
        if counts["structural"] > 2:
            errors.append(f"user-facing: max 2 structural (got {counts['structural']})")
        if counts["user-journey"] < 3:
            errors.append(f"user-facing: min 3 user-journey (got {counts['user-journey']})")
        if counts["edge-case"] < 1:
            errors.append(f"user-facing: min 1 edge-case (got {counts['edge-case']})")
        if counts["unit"] == 0:
            warnings.append(
                "user-facing: no unit criterion — "
                "if this phase adds pure logic (validators, transformers, state machines), add one"
            )

    elif phase_kind == "integration":
        if len(ac) > 8:
            errors.append(f"integration phase: max 8 criteria (got {len(ac)})")
        if counts["structural"] > 2:
            errors.append(f"integration: max 2 structural (got {counts['structural']})")
        if counts["unit"] < 2:
            errors.append(f"integration: min 2 unit (got {counts['unit']})")
        if counts["user-journey"] < 2:
            errors.append(
                f"integration: min 2 user-journey as contract probes (got {counts['user-journey']})"
            )
        if counts["edge-case"] < 1:
            errors.append(f"integration: min 1 edge-case (got {counts['edge-case']})")

    elif phase_kind == "infrastructure":
        if len(ac) > 3:
            errors.append(f"infrastructure phase: max 3 criteria (got {len(ac)})")
        if counts["structural"] < 1:
            errors.append("infrastructure: min 1 structural")
        if counts["structural"] > 3:
            errors.append(f"infrastructure: max 3 structural (got {counts['structural']})")
        for bad_layer in ("unit", "user-journey", "edge-case"):
            if counts[bad_layer] > 0:
                errors.append(
                    f"infrastructure phase: no {bad_layer} criteria allowed "
                    f"(got {counts[bad_layer]}) — re-classify the phase if user-visible work exists"
                )

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
