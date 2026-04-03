#!/usr/bin/env python3
"""Validate Plan JSON. Standalone — stdlib only."""
import json
import re
import sys

VALID_MODELS = {"", "haiku", "sonnet", "opus"}
VALID_EFFORTS = {"", "low", "medium", "high"}
VALID_TEST_LEVELS = {"", "L1", "L2"}


def validate(path: str):
    errors = []
    warnings = []

    with open(path) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        errors.append("Root must be a JSON object")
        return errors, warnings

    # Required: phases
    if "phases" not in data:
        errors.append("Missing required field: 'phases'")
        return errors, warnings

    phases = data["phases"]
    if not isinstance(phases, list):
        errors.append("'phases' must be a list")
        return errors, warnings

    if len(phases) < 1:
        errors.append("'phases' must have at least 1 item")

    all_task_ids = {}   # task_id -> "phase[i].tasks[j]" for uniqueness tracking
    phase_ids = {}      # phase_id -> "phases[i]" for uniqueness tracking
    depends_on_refs = []  # (ref_task_id, location_str) to validate after collecting all IDs

    for i, phase in enumerate(phases):
        pprefix = f"phases[{i}]"

        if not isinstance(phase, dict):
            errors.append(f"{pprefix}: must be an object")
            continue

        # phase.id
        if "id" not in phase:
            errors.append(f"{pprefix}: missing 'id'")
        elif not isinstance(phase["id"], str) or not phase["id"].strip():
            errors.append(f"{pprefix}.id: must be a non-empty string")
        else:
            pid = phase["id"]
            if pid in phase_ids:
                errors.append(f"{pprefix}.id: duplicate phase id '{pid}' (first seen at {phase_ids[pid]})")
            else:
                phase_ids[pid] = pprefix

        # phase.name
        if "name" not in phase:
            errors.append(f"{pprefix}: missing 'name'")
        elif not isinstance(phase["name"], str) or not phase["name"].strip():
            errors.append(f"{pprefix}.name: must be a non-empty string")

        # phase.tasks
        if "tasks" not in phase:
            errors.append(f"{pprefix}: missing 'tasks'")
            continue

        tasks = phase["tasks"]
        if not isinstance(tasks, list):
            errors.append(f"{pprefix}.tasks: must be a list")
            continue

        if len(tasks) < 1:
            errors.append(f"{pprefix}.tasks: must have at least 1 task")

        for j, task in enumerate(tasks):
            tprefix = f"{pprefix}.tasks[{j}]"

            if not isinstance(task, dict):
                errors.append(f"{tprefix}: must be an object")
                continue

            # task.id
            if "id" not in task:
                errors.append(f"{tprefix}: missing 'id'")
            elif not isinstance(task["id"], str) or not task["id"].strip():
                errors.append(f"{tprefix}.id: must be a non-empty string")
            else:
                tid = task["id"]
                if tid in all_task_ids:
                    errors.append(f"{tprefix}.id: duplicate task id '{tid}' (first seen at {all_task_ids[tid]})")
                else:
                    all_task_ids[tid] = tprefix

            # task.name
            if "name" not in task:
                errors.append(f"{tprefix}: missing 'name'")
            elif not isinstance(task["name"], str) or not task["name"].strip():
                errors.append(f"{tprefix}.name: must be a non-empty string")

            # Optional: model
            if "model" in task:
                if not isinstance(task["model"], str):
                    errors.append(f"{tprefix}.model: must be a string")
                elif task["model"] not in VALID_MODELS:
                    errors.append(f"{tprefix}.model: '{task['model']}' must be one of {sorted(VALID_MODELS)}")

            # Optional: effort
            if "effort" in task:
                if not isinstance(task["effort"], str):
                    errors.append(f"{tprefix}.effort: must be a string")
                elif task["effort"] not in VALID_EFFORTS:
                    errors.append(f"{tprefix}.effort: '{task['effort']}' must be one of {sorted(VALID_EFFORTS)}")

            # Optional: test_level
            if "test_level" in task:
                if not isinstance(task["test_level"], str):
                    errors.append(f"{tprefix}.test_level: must be a string")
                elif task["test_level"] not in VALID_TEST_LEVELS:
                    errors.append(f"{tprefix}.test_level: '{task['test_level']}' must be one of {sorted(VALID_TEST_LEVELS)}")

            # Optional: depends_on
            if "depends_on" in task:
                deps = task["depends_on"]
                if not isinstance(deps, list):
                    errors.append(f"{tprefix}.depends_on: must be a list")
                else:
                    for dep in deps:
                        if not isinstance(dep, str):
                            errors.append(f"{tprefix}.depends_on: each item must be a string, got {type(dep).__name__}")
                        else:
                            depends_on_refs.append((dep, tprefix))

    # Validate depends_on refs point to existing task IDs
    for ref_id, location in depends_on_refs:
        if ref_id not in all_task_ids:
            errors.append(f"{location}.depends_on: references unknown task id '{ref_id}'")

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
