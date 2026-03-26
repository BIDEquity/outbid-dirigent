#!/usr/bin/env bash
# Dirigent Hook — captures Claude Code lifecycle events.
# Always logs to local JSONL. Forwards to outbid-portal when credentials are set.
set -euo pipefail

INPUT=$(cat)

EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // "unknown"')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build a compact log entry based on event type
case "$EVENT" in
  SessionStart)
    ENTRY=$(echo "$INPUT" | jq -c --arg ts "$TIMESTAMP" '{
      timestamp: $ts,
      event: .hook_event_name,
      session_id: .session_id,
      source: .source,
      model: .model,
      cwd: .cwd
    }')
    PORTAL_TYPE="session_start"
    ;;
  SessionEnd)
    ENTRY=$(echo "$INPUT" | jq -c --arg ts "$TIMESTAMP" '{
      timestamp: $ts,
      event: .hook_event_name,
      session_id: .session_id,
      reason: .reason
    }')
    PORTAL_TYPE="session_end"
    ;;
  PostToolUse)
    ENTRY=$(echo "$INPUT" | jq -c --arg ts "$TIMESTAMP" '{
      timestamp: $ts,
      event: .hook_event_name,
      session_id: .session_id,
      tool_name: .tool_name,
      tool_input: (.tool_input | if . then to_entries | map(
        if (.value | type) == "string" and (.value | length) > 500
        then .value = .value[:500] + "... (\(.value | length) chars)"
        else . end
      ) | from_entries else null end),
      tool_use_id: .tool_use_id
    }')
    PORTAL_TYPE="tool_use"
    ;;
  TaskCompleted)
    ENTRY=$(echo "$INPUT" | jq -c --arg ts "$TIMESTAMP" '{
      timestamp: $ts,
      event: .hook_event_name,
      session_id: .session_id,
      task_id: .task_id,
      task_subject: .task_subject,
      task_description: .task_description,
      teammate_name: .teammate_name,
      team_name: .team_name
    }')
    PORTAL_TYPE="task_complete"
    ;;
  *)
    ENTRY=$(echo "$INPUT" | jq -c --arg ts "$TIMESTAMP" '{
      timestamp: $ts,
      event: .hook_event_name,
      session_id: .session_id
    }')
    PORTAL_TYPE="$EVENT"
    ;;
esac

# --- 1. Local JSONL log (always) ---
LOG_DIR="${DIRIGENT_HOOK_LOG_DIR:-${CLAUDE_PROJECT_DIR:-.}/.dirigent/hooks}"
mkdir -p "$LOG_DIR"
echo "$ENTRY" >> "$LOG_DIR/events.jsonl"

# --- 2. Portal forwarding (when credentials are set) ---
if [ -n "${OUTBID_PORTAL_URL:-}" ] && [ -n "${OUTBID_EXECUTION_ID:-}" ] && [ -n "${OUTBID_REPORTER_TOKEN:-}" ]; then
  PORTAL_PAYLOAD=$(echo "$ENTRY" | jq -c --arg type "$PORTAL_TYPE" --arg eid "$OUTBID_EXECUTION_ID" '{
    execution_id: $eid,
    event: {
      type: $type,
      ts: .timestamp,
      data: (. | del(.timestamp, .event))
    }
  }')

  # Add task/phase context from environment if available
  if [ -n "${OUTBID_CURRENT_TASK_ID:-}" ]; then
    PORTAL_PAYLOAD=$(echo "$PORTAL_PAYLOAD" | jq -c --arg tid "$OUTBID_CURRENT_TASK_ID" '.event.data.taskId = $tid')
  fi
  if [ -n "${OUTBID_CURRENT_PHASE:-}" ]; then
    PORTAL_PAYLOAD=$(echo "$PORTAL_PAYLOAD" | jq -c --arg p "$OUTBID_CURRENT_PHASE" '.event.data.phase = ($p | tonumber)')
  fi

  curl -s -X POST \
    "${OUTBID_PORTAL_URL%/}/api/execution-event" \
    -H "Content-Type: application/json" \
    -H "X-Reporter-Token: $OUTBID_REPORTER_TOKEN" \
    -d "$PORTAL_PAYLOAD" \
    --max-time 5 \
    >/dev/null 2>&1 || true
fi
