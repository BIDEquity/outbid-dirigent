#!/usr/bin/env python3
"""Validate Plan JSON. Standalone — stdlib only."""
import json
import re
import sys

VALID_MODELS = {"", "haiku", "sonnet", "opus"}
VALID_EFFORTS = {"", "low", "medium", "high"}
VALID_TEST_LEVELS = {"", "L1", "L2"}
VALID_PHASE_KINDS = {"user-facing", "integration", "infrastructure"}
VALID_SIZES = {"standard", "large"}

# Default caps (size="standard")
DEFAULT_MAX_PHASES = 4
DEFAULT_MAX_TASKS_PER_PHASE = 4
# Expanded caps (size="large") — opt-in escape hatch for genuinely large features
LARGE_MAX_PHASES = 5
LARGE_MAX_TASKS_PER_PHASE = 5

MAX_INFRASTRUCTURE_PHASES = 1  # independent of size — scaffolds always monolithize


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

    # Resolve size → caps
    size = data.get("size", "standard")
    if size not in VALID_SIZES:
        errors.append(f"'size' must be one of {sorted(VALID_SIZES)} (got '{size}')")
        size = "standard"  # fall through with default caps for the rest of validation
    max_phases = LARGE_MAX_PHASES if size == "large" else DEFAULT_MAX_PHASES
    max_tasks_per_phase = LARGE_MAX_TASKS_PER_PHASE if size == "large" else DEFAULT_MAX_TASKS_PER_PHASE

    if len(phases) < 1:
        errors.append("'phases' must have at least 1 item")
    if len(phases) > max_phases:
        hint = (
            " Or set 'size': 'large' to raise caps to 5×5 if the feature genuinely doesn't fit."
            if size == "standard" else ""
        )
        errors.append(
            f"'phases' has {len(phases)} items; max is {max_phases} (size='{size}'). "
            f"If the feature genuinely needs more, split the SPEC into multiple runs.{hint}"
        )

    all_task_ids = {}         # task_id -> "phase[i].tasks[j]"
    phase_ids = {}            # phase_id -> "phases[i]"
    depends_on_refs = []      # (ref_task_id, location_str)
    phase_kinds_in_order = [] # list of (kind, phase_index, is_last_phase_flag_resolved_later)
    infrastructure_count = 0

    for i, phase in enumerate(phases):
        pprefix = f"phases[{i}]"
        is_last_phase = (i == len(phases) - 1)

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

        # phase.kind (required)
        kind = phase.get("kind")
        if kind is None:
            errors.append(
                f"{pprefix}: missing 'kind' "
                f"(one of: user-facing | integration | infrastructure)"
            )
        elif kind not in VALID_PHASE_KINDS:
            errors.append(
                f"{pprefix}.kind: '{kind}' must be one of {sorted(VALID_PHASE_KINDS)}"
            )
        else:
            phase_kinds_in_order.append(kind)
            if kind == "infrastructure":
                infrastructure_count += 1
                if is_last_phase:
                    errors.append(
                        f"{pprefix}: the final phase cannot be 'infrastructure' — "
                        f"every run must end on user-observable delivery"
                    )

        # phase.merge_justification (required except on the last phase)
        mj = phase.get("merge_justification", "")
        if not is_last_phase:
            if not isinstance(mj, str) or not mj.strip():
                errors.append(
                    f"{pprefix}: missing 'merge_justification' — "
                    f"one sentence on why this phase can't be merged with the next. "
                    f"If you can't justify it, merge them."
                )

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
        if len(tasks) > max_tasks_per_phase:
            errors.append(
                f"{pprefix}.tasks: has {len(tasks)} tasks; max is {max_tasks_per_phase} (size='{size}'). "
                f"Split into a new phase or reduce the task count."
            )

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

            # Optional: relevant_req_ids
            if "relevant_req_ids" in task:
                rids = task["relevant_req_ids"]
                if not isinstance(rids, list):
                    errors.append(f"{tprefix}.relevant_req_ids: must be a list")
                else:
                    for rid in rids:
                        if not isinstance(rid, str):
                            errors.append(
                                f"{tprefix}.relevant_req_ids: each item must be a string, got {type(rid).__name__}"
                            )
                        elif not re.fullmatch(r"R\d+", rid):
                            errors.append(
                                f"{tprefix}.relevant_req_ids: '{rid}' must match pattern R\\d+"
                            )

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

    # Cross-phase kind rules
    if infrastructure_count > MAX_INFRASTRUCTURE_PHASES:
        errors.append(
            f"Plan has {infrastructure_count} infrastructure phases; max is {MAX_INFRASTRUCTURE_PHASES}. "
            f"Merge scaffolding/migrations/tooling into a single infrastructure phase."
        )

    # Consecutive same-kind phases → merge candidates (warning, not error).
    # Skip user-facing: different user-facing phases often serve different users
    # (e.g. transactional staff UI vs. observability coordinator UI) — consecutive
    # user-facing is typically correct, not over-slicing. Flag only integration
    # (real subsystem over-slicing) and infrastructure (already capped at 1; defensive).
    for a, b in zip(phase_kinds_in_order, phase_kinds_in_order[1:]):
        if a == b and a != "user-facing":
            warnings.append(
                f"Two consecutive '{a}' phases — consider merging them unless "
                f"merge_justification makes a strong case for separation."
            )
            break  # one warning is enough; don't spam

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
