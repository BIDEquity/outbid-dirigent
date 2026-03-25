# Claude Hooks Integration

This directory contains hook scripts that can be used with Claude Code to capture granular activity events.

## How it works

Claude Code supports hooks that execute on various events:
- `PreToolUse` - Before a tool is called
- `PostToolUse` - After a tool completes
- `Notification` - When Claude sends a notification

The hook receives JSON data about the event and can forward it to the portal.

## Setup

The Dirigent automatically configures hooks when running in portal-connected mode by:
1. Setting the `OUTBID_PORTAL_URL`, `OUTBID_EXECUTION_ID`, and `OUTBID_REPORTER_TOKEN` environment variables
2. Pointing Claude Code to use the hook scripts via the `--hook-dir` flag

## Event Types Captured

- **PostToolUse**: Captures all tool calls (Read, Write, Edit, Bash, Grep, Glob, etc.)
- **Notification**: Captures Claude's thinking/status messages

## Portal Events Generated

These hooks send events to `/api/execution-event`:
- `tool_use`: Every tool call with tool name and input
- `thinking`: Status updates from Claude
