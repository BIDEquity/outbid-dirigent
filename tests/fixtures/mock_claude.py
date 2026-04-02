#!/usr/bin/env python3
"""
Mock Claude Code CLI for integration testing.

This script simulates Claude Code behavior without making API calls.
It parses the task prompt and creates the expected outputs:
1. Creates files mentioned in the task
2. Creates a summary in .dirigent/summaries/
3. Makes a git commit

Usage:
    Set MOCK_CLAUDE_BIN to point to this script before running tests.
    The Dirigent will call this instead of the real `claude` CLI.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


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
    desc_match = re.search(r'<description>([^<]+)</description>', prompt, re.DOTALL)
    if desc_match:
        task_info["description"] = desc_match.group(1).strip()

    # Extract files to create
    create_match = re.search(r'<files-to-create>([^<]+)</files-to-create>', prompt)
    if create_match:
        files = create_match.group(1).strip()
        if files and files.lower() != "keine":
            task_info["files_to_create"] = [f.strip() for f in files.split(",")]

    # Extract files to modify
    modify_match = re.search(r'<files-to-modify>([^<]+)</files-to-modify>', prompt)
    if modify_match:
        files = modify_match.group(1).strip()
        if files and files.lower() != "keine":
            task_info["files_to_modify"] = [f.strip() for f in files.split(",")]

    return task_info


def create_mock_output(repo_path: Path, task_info: dict) -> None:
    """Create mock output files based on task info."""
    task_id = task_info["id"]
    task_name = task_info["name"]
    description = task_info["description"]

    # Create files mentioned in files_to_create
    for filename in task_info["files_to_create"]:
        filepath = repo_path / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Generate content based on filename
        if filename.endswith(".txt"):
            content = f"Hello, World!\nCreated by task {task_id}\n"
        elif filename.endswith(".js"):
            content = f"// Created by task {task_id}\nconsole.log('Hello from {filename}');\n"
        elif filename.endswith(".ts"):
            content = f"// Created by task {task_id}\nexport const greeting = 'Hello from {filename}';\n"
        elif filename.endswith(".py"):
            content = f"# Created by task {task_id}\nprint('Hello from {filename}')\n"
        elif filename.endswith(".json"):
            content = json.dumps({"created_by": task_id, "name": filename}, indent=2)
        elif filename.endswith(".md"):
            content = f"# {filename}\n\nCreated by task {task_id}\n"
        else:
            content = f"Created by task {task_id}\n"

        filepath.write_text(content)

    # Modify files mentioned in files_to_modify
    for filename in task_info["files_to_modify"]:
        filepath = repo_path / filename
        if filepath.exists():
            current = filepath.read_text()
            # Add a comment/modification marker
            if filename.endswith(".json"):
                try:
                    data = json.loads(current)
                    data["_modified_by_task"] = task_id
                    filepath.write_text(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    pass
            else:
                filepath.write_text(f"// Modified by task {task_id}\n{current}")

    # Create summary file
    summaries_dir = repo_path / ".dirigent" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    summary_content = f"""# Task {task_id} Summary

## Was wurde gemacht
{task_name}

{description}

## Geänderte Dateien
"""
    for f in task_info["files_to_create"]:
        summary_content += f"- Created: {f}\n"
    for f in task_info["files_to_modify"]:
        summary_content += f"- Modified: {f}\n"

    summary_content += """
## Deviations
Keine.

## Nächste Schritte
Task abgeschlossen.
"""

    summary_file = summaries_dir / f"{task_id}-SUMMARY.md"
    summary_file.write_text(summary_content)


def git_commit(repo_path: Path, task_id: str, task_name: str) -> None:
    """Create a git commit for the task."""
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        capture_output=True,
    )

    subprocess.run(
        ["git", "commit", "-m", f"feat({task_id}): {task_name}"],
        cwd=repo_path,
        capture_output=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Mock Claude Code CLI")
    parser.add_argument("-p", "--prompt", help="The prompt to process")
    parser.add_argument("--model", help="Model to use (ignored)")
    parser.add_argument("--effort", help="Effort level (ignored)")
    parser.add_argument("--append-system-prompt", help="System prompt (ignored)")
    parser.add_argument("--plugin-dir", help="Plugin directory (ignored)")
    parser.add_argument("--dangerously-skip-permissions", action="store_true", help="Skip permissions (ignored)")

    args = parser.parse_args()

    if not args.prompt:
        print("Error: No prompt provided", file=sys.stderr)
        sys.exit(1)

    # Get repo path from cwd
    repo_path = Path.cwd()

    # Parse task from prompt
    task_info = parse_task_from_prompt(args.prompt)

    # Log what we're doing
    print(f"[mock-claude] Processing task: {task_info['id']} - {task_info['name']}")
    print(f"[mock-claude] Files to create: {task_info['files_to_create']}")
    print(f"[mock-claude] Files to modify: {task_info['files_to_modify']}")

    # Create mock outputs
    create_mock_output(repo_path, task_info)

    # Commit changes
    git_commit(repo_path, task_info["id"], task_info["name"])

    print(f"[mock-claude] Task {task_info['id']} completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
