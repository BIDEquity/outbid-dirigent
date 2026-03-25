#!/usr/bin/env python3
"""
Claude Hook: PostToolUse

Captures tool calls and forwards them to the Outbid Portal for real-time monitoring.
This script is called by Claude Code after each tool use.

Environment variables required:
- OUTBID_PORTAL_URL: Portal API base URL
- OUTBID_EXECUTION_ID: Current execution ID
- OUTBID_REPORTER_TOKEN: Authentication token
- OUTBID_CURRENT_TASK_ID: (optional) Current task being executed
- OUTBID_CURRENT_PHASE: (optional) Current phase number
"""

import json
import os
import sys
import time

import requests


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    # Get portal connection info from environment
    portal_url = os.environ.get("OUTBID_PORTAL_URL")
    execution_id = os.environ.get("OUTBID_EXECUTION_ID")
    reporter_token = os.environ.get("OUTBID_REPORTER_TOKEN")

    if not all([portal_url, execution_id, reporter_token]):
        # Not connected to portal, skip
        return

    # Extract tool info
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    tool_use_id = hook_input.get("tool_use_id", "")

    # Skip if no tool name
    if not tool_name:
        return

    # Build event data
    event_data = {
        "toolName": tool_name,
        "toolInput": _sanitize_tool_input(tool_name, tool_input),
    }
    if tool_use_id:
        event_data["toolUseId"] = tool_use_id

    # Add context from environment
    task_id = os.environ.get("OUTBID_CURRENT_TASK_ID")
    phase = os.environ.get("OUTBID_CURRENT_PHASE")
    if task_id:
        event_data["taskId"] = task_id
    if phase:
        try:
            event_data["phase"] = int(phase)
        except ValueError:
            pass

    # Send to portal
    try:
        requests.post(
            f"{portal_url.rstrip('/')}/api/execution-event",
            headers={"X-Reporter-Token": reporter_token},
            json={
                "execution_id": execution_id,
                "event": {
                    "type": "tool_use",
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "data": event_data,
                },
            },
            timeout=5,
        )
    except Exception:
        # Don't fail the hook if portal is unreachable
        pass


def _sanitize_tool_input(tool_name: str, tool_input: dict) -> dict:
    """Sanitize tool input for logging - truncate large content."""
    sanitized = {}

    for key, value in tool_input.items():
        if isinstance(value, str):
            # Truncate large strings
            if len(value) > 500:
                sanitized[key] = value[:500] + f"... ({len(value)} chars)"
            else:
                sanitized[key] = value
        elif isinstance(value, (dict, list)):
            # Truncate large nested structures
            json_str = json.dumps(value)
            if len(json_str) > 500:
                sanitized[key] = f"[{type(value).__name__} with {len(json_str)} chars]"
            else:
                sanitized[key] = value
        else:
            sanitized[key] = value

    return sanitized


if __name__ == "__main__":
    main()
