#!/usr/bin/env python3
"""
Mock Claude Code CLI for integration testing.

This script simulates Claude Code behavior without making API calls.
It detects the type of request and generates appropriate outputs:

1. Planning requests → Creates .dirigent/PLAN.json
2. Test manifest requests → Creates outbid-test-manifest.yaml
3. Task execution requests → Creates files + commits

Usage:
    Set PATH to include this script's directory before running tests.
    The Dirigent will call this instead of the real `claude` CLI.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def detect_request_type(prompt: str) -> str:
    """Detect what kind of request this is based on prompt content."""
    prompt_lower = prompt.lower()

    if "plan.json" in prompt_lower or "ausführungsplan" in prompt_lower:
        return "plan"
    elif "test-manifest" in prompt_lower or "outbid-test-manifest.yaml" in prompt_lower:
        return "manifest"
    elif "<task id=" in prompt:
        return "task"
    elif "business rules" in prompt_lower or "business_rules" in prompt_lower:
        return "business_rules"
    else:
        return "unknown"


def create_plan(repo_path: Path, prompt: str) -> None:
    """Create a mock PLAN.json based on the spec in the prompt."""
    dirigent_dir = repo_path / ".dirigent"
    dirigent_dir.mkdir(parents=True, exist_ok=True)

    # Extract spec content to understand what files to create
    spec_match = re.search(r"<spec>(.*?)</spec>", prompt, re.DOTALL)
    spec_content = spec_match.group(1) if spec_match else ""

    # Detect files mentioned in spec
    files_to_create = []
    if "hello.txt" in spec_content.lower():
        files_to_create.append("hello.txt")
    if "file1.txt" in spec_content.lower():
        files_to_create.append("file1.txt")
    if "file2.txt" in spec_content.lower():
        files_to_create.append("file2.txt")

    # Default to hello.txt if nothing specific found
    if not files_to_create:
        files_to_create = ["hello.txt"]

    # Create a simple plan
    plan = {
        "title": "Test Feature Implementation",
        "summary": "Implementing the requested feature",
        "assumptions": ["Repository is a valid git repo", "No external dependencies required"],
        "out_of_scope": ["Deployment", "Documentation updates"],
        "phases": [
            {
                "id": "01",
                "name": "Implementation",
                "description": "Create the required files",
                "tasks": [
                    {
                        "id": "01-01",
                        "name": f"Create {files_to_create[0]}",
                        "description": f"Create the {files_to_create[0]} file with appropriate content",
                        "files_to_create": [files_to_create[0]],
                        "files_to_modify": [],
                        "depends_on": [],
                        "model": "haiku",
                        "effort": "low",
                        "test_level": "",
                    }
                ],
            }
        ],
        "estimated_complexity": "low",
        "risks": [],
    }

    # Add additional tasks for more files
    for i, filename in enumerate(files_to_create[1:], start=2):
        plan["phases"][0]["tasks"].append(
            {
                "id": f"01-{i:02d}",
                "name": f"Create {filename}",
                "description": f"Create the {filename} file",
                "files_to_create": [filename],
                "files_to_modify": [],
                "depends_on": [],
                "model": "haiku",
                "effort": "low",
                "test_level": "",
            }
        )

    plan_path = dirigent_dir / "PLAN.json"
    plan_path.write_text(json.dumps(plan, indent=2))

    print(f"[mock-claude] Created PLAN.json with {len(plan['phases'][0]['tasks'])} task(s)")


def create_test_manifest(repo_path: Path) -> None:
    """Create a minimal mock test manifest."""
    manifest = """# Auto-generated test manifest
name: test-repo
version: "1.0"

prerequisites: []

components: []

test_commands:
  l1:
    - name: lint
      run: "echo 'lint ok'"
      timeout: 60
  l2: []

gaps: []
"""
    manifest_path = repo_path / "outbid-test-manifest.yaml"
    manifest_path.write_text(manifest)
    print("[mock-claude] Created outbid-test-manifest.yaml")


def parse_task_from_prompt(prompt: str) -> dict:
    """Extract task information from the Dirigent prompt."""
    task_info = {
        "id": "unknown",
        "name": "unknown",
        "description": "",
        "files_to_create": [],
        "files_to_modify": [],
    }

    # Extract task ID
    id_match = re.search(r'<task id="([^"]+)">', prompt)
    if id_match:
        task_info["id"] = id_match.group(1)

    # Extract task name (after the id)
    name_match = re.search(r'<task id="[^"]+">([^<]+)</task>', prompt)
    if name_match:
        task_info["name"] = name_match.group(1).strip()

    # Extract description
    desc_match = re.search(r"<description>([^<]+)</description>", prompt, re.DOTALL)
    if desc_match:
        task_info["description"] = desc_match.group(1).strip()

    # Extract files to create
    create_match = re.search(r"<files-to-create>([^<]+)</files-to-create>", prompt)
    if create_match:
        files = create_match.group(1).strip()
        if files and files.lower() != "keine":
            task_info["files_to_create"] = [f.strip() for f in files.split(",") if f.strip()]

    # Extract files to modify
    modify_match = re.search(r"<files-to-modify>([^<]+)</files-to-modify>", prompt)
    if modify_match:
        files = modify_match.group(1).strip()
        if files and files.lower() != "keine":
            task_info["files_to_modify"] = [f.strip() for f in files.split(",") if f.strip()]

    return task_info


def execute_task(repo_path: Path, task_info: dict) -> None:
    """Execute a task by creating files and committing."""
    task_id = task_info["id"]
    task_name = task_info["name"]

    # Create files
    for filename in task_info["files_to_create"]:
        filepath = repo_path / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Generate content based on filename
        if filename.endswith(".txt"):
            content = f"Hello, World!\nCreated by task {task_id}\n"
        elif filename.endswith(".js"):
            content = f"// Created by task {task_id}\nconsole.log('Hello from {filename}');\n"
        elif filename.endswith(".ts"):
            content = (
                f"// Created by task {task_id}\nexport const greeting = 'Hello from {filename}';\n"
            )
        elif filename.endswith(".py"):
            content = f"# Created by task {task_id}\nprint('Hello from {filename}')\n"
        elif filename.endswith(".json"):
            content = json.dumps({"created_by": task_id, "name": filename}, indent=2)
        elif filename.endswith(".md"):
            content = f"# {filename}\n\nCreated by task {task_id}\n"
        else:
            content = f"Created by task {task_id}\n"

        filepath.write_text(content)
        print(f"[mock-claude] Created {filename}")

    # Modify files
    for filename in task_info["files_to_modify"]:
        filepath = repo_path / filename
        if filepath.exists():
            current = filepath.read_text()
            if filename.endswith(".json"):
                try:
                    data = json.loads(current)
                    data["_modified_by_task"] = task_id
                    filepath.write_text(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    pass
            else:
                filepath.write_text(f"// Modified by task {task_id}\n{current}")
            print(f"[mock-claude] Modified {filename}")

    # Create summary file
    summaries_dir = repo_path / ".dirigent" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    summary_content = f"""# Task {task_id} Summary

## Was wurde gemacht
{task_name}

## Geänderte Dateien
"""
    for f in task_info["files_to_create"]:
        summary_content += f"- Created: {f}\n"
    for f in task_info["files_to_modify"]:
        summary_content += f"- Modified: {f}\n"

    summary_content += "\n## Deviations\nKeine.\n"

    summary_file = summaries_dir / f"{task_id}-SUMMARY.md"
    summary_file.write_text(summary_content)

    # Git commit
    subprocess.run(["git", "add", "-A"], cwd=repo_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"feat({task_id}): {task_name}"],
        cwd=repo_path,
        capture_output=True,
    )

    print(f"[mock-claude] Task {task_id} completed with commit")


def create_business_rules(repo_path: Path) -> None:
    """Create a mock business rules file."""
    dirigent_dir = repo_path / ".dirigent"
    dirigent_dir.mkdir(parents=True, exist_ok=True)

    rules_content = """# Business Rules

## Entities
- User: Basic user entity

## Rules
- No specific business rules for test repo

## API Endpoints
- None defined
"""
    rules_path = dirigent_dir / "BUSINESS_RULES.md"
    rules_path.write_text(rules_content)
    print("[mock-claude] Created BUSINESS_RULES.md")


def main():
    parser = argparse.ArgumentParser(description="Mock Claude Code CLI")
    parser.add_argument("-p", "--prompt", help="The prompt to process")
    parser.add_argument("--model", help="Model to use (ignored)")
    parser.add_argument("--effort", help="Effort level (ignored)")
    parser.add_argument("--append-system-prompt", help="System prompt (ignored)")
    parser.add_argument("--plugin-dir", help="Plugin directory (ignored)")
    parser.add_argument("--dangerously-skip-permissions", action="store_true")

    args = parser.parse_args()

    if not args.prompt:
        print("Error: No prompt provided", file=sys.stderr)
        sys.exit(1)

    repo_path = Path.cwd()
    request_type = detect_request_type(args.prompt)

    print(f"[mock-claude] Request type: {request_type}")

    if request_type == "plan":
        create_plan(repo_path, args.prompt)
    elif request_type == "manifest":
        create_test_manifest(repo_path)
    elif request_type == "task":
        task_info = parse_task_from_prompt(args.prompt)
        print(f"[mock-claude] Task: {task_info['id']} - {task_info['name']}")
        execute_task(repo_path, task_info)
    elif request_type == "business_rules":
        create_business_rules(repo_path)
    else:
        print("[mock-claude] Unknown request type, doing nothing")

    sys.exit(0)


if __name__ == "__main__":
    main()
