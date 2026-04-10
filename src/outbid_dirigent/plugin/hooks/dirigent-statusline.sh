#!/usr/bin/env bash
# Dirigent statusline.
#
# Reads JSON from stdin (Claude Code statusline protocol):
#   { "session_id": "...", "model": {...}, "transcript_path": "...", "cwd": "...", "workspace": {...} }
#
# Emits a single line combining:
#   - dirigent run state (phase/task progress, if a run is active in cwd)
#   - token usage (input + output + cache_read against the model context window)
#   - git branch + dirty marker
#
# Token usage is the *most important* signal — keeps the user aware of context staleness.
# When usage > 70% the line turns into a warning so the user knows to /clear or wrap up.
#
# Pure bash + jq, no python deps. jq is assumed (it's already used by dirigent-hook.sh).

set -uo pipefail

INPUT=$(cat)

CWD=$(echo "$INPUT" | jq -r '.cwd // .workspace.current_dir // "."')
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""')
MODEL_NAME=$(echo "$INPUT" | jq -r '.model.display_name // .model.id // ""')

# ---------- token usage ----------
TOKEN_FIELD=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  # Find the *most recent* assistant message with a usage block. The current
  # context size is the cache_read + cache_creation + input + output of the
  # last turn — that's what's actually loaded into the model right now.
  USAGE=$(tac "$TRANSCRIPT_PATH" 2>/dev/null | \
    awk 'BEGIN{found=0} /"usage"/ { print; found=1; exit } END { if (!found) print "" }' | \
    jq -c 'try (.message.usage // .usage // empty) catch empty' 2>/dev/null || echo "")

  if [ -n "$USAGE" ] && [ "$USAGE" != "null" ]; then
    INPUT_T=$(echo "$USAGE" | jq -r '.input_tokens // 0')
    OUTPUT_T=$(echo "$USAGE" | jq -r '.output_tokens // 0')
    CACHE_READ=$(echo "$USAGE" | jq -r '.cache_read_input_tokens // 0')
    CACHE_CREATE=$(echo "$USAGE" | jq -r '.cache_creation_input_tokens // 0')

    CTX_USED=$((INPUT_T + CACHE_READ + CACHE_CREATE))

    # Context window: 1M for *-1m models, else 200K. Heuristic on the model name.
    case "$MODEL_NAME" in
      *1m*|*1M*|*"1m"*) CTX_MAX=1000000 ;;
      *) CTX_MAX=200000 ;;
    esac

    PCT=$(( CTX_USED * 100 / CTX_MAX ))

    # Format with k suffix for compactness.
    if [ "$CTX_USED" -ge 1000 ]; then
      USED_DISPLAY="$(( CTX_USED / 1000 ))k"
    else
      USED_DISPLAY="${CTX_USED}"
    fi
    if [ "$CTX_MAX" -ge 1000 ]; then
      MAX_DISPLAY="$(( CTX_MAX / 1000 ))k"
    else
      MAX_DISPLAY="${CTX_MAX}"
    fi

    # Severity-coded prefix. > 70% = warning, > 90% = critical.
    if [ "$PCT" -ge 90 ]; then
      TOKEN_FIELD="🔴 ${USED_DISPLAY}/${MAX_DISPLAY} (${PCT}% — /clear soon)"
    elif [ "$PCT" -ge 70 ]; then
      TOKEN_FIELD="🟡 ${USED_DISPLAY}/${MAX_DISPLAY} (${PCT}%)"
    else
      TOKEN_FIELD="🟢 ${USED_DISPLAY}/${MAX_DISPLAY} (${PCT}%)"
    fi
  fi
fi

# ---------- dirigent state ----------
DIRIGENT_FIELD=""
if [ -d "$CWD/.dirigent" ]; then
  PLAN_FILE="$CWD/.dirigent/PLAN.json"
  STATE_FILE="$CWD/.dirigent/STATE.json"
  SPEC_FILE="$CWD/.dirigent/SPEC.md"

  if [ -f "$STATE_FILE" ]; then
    # Try to extract current phase/task. Fields are best-effort — fall back gracefully.
    CUR_PHASE=$(jq -r '.current_phase_id // .current_phase // .phase // ""' "$STATE_FILE" 2>/dev/null)
    CUR_TASK=$(jq -r '.current_task_id // .current_task // ""' "$STATE_FILE" 2>/dev/null)
    if [ -n "$CUR_PHASE" ] && [ "$CUR_PHASE" != "null" ]; then
      if [ -n "$CUR_TASK" ] && [ "$CUR_TASK" != "null" ]; then
        DIRIGENT_FIELD="🎯 phase ${CUR_PHASE} · task ${CUR_TASK}"
      else
        DIRIGENT_FIELD="🎯 phase ${CUR_PHASE}"
      fi
    fi
  fi

  if [ -z "$DIRIGENT_FIELD" ] && [ -f "$PLAN_FILE" ]; then
    PHASE_COUNT=$(jq -r '(.phases // []) | length' "$PLAN_FILE" 2>/dev/null)
    if [ -n "$PHASE_COUNT" ] && [ "$PHASE_COUNT" != "null" ] && [ "$PHASE_COUNT" -gt 0 ] 2>/dev/null; then
      DIRIGENT_FIELD="📋 plan ready (${PHASE_COUNT} phases)"
    fi
  fi

  if [ -z "$DIRIGENT_FIELD" ] && [ -f "$SPEC_FILE" ]; then
    DIRIGENT_FIELD="📝 spec only · /dirigent:hi"
  fi
fi

# ---------- git ----------
GIT_FIELD=""
if [ -d "$CWD/.git" ] || git -C "$CWD" rev-parse --git-dir >/dev/null 2>&1; then
  BRANCH=$(git -C "$CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  if [ -n "$BRANCH" ]; then
    DIRTY=""
    if ! git -C "$CWD" diff --quiet 2>/dev/null || ! git -C "$CWD" diff --cached --quiet 2>/dev/null; then
      DIRTY="*"
    fi
    GIT_FIELD="⎇ ${BRANCH}${DIRTY}"
  fi
fi

# ---------- assemble ----------
PARTS=()
[ -n "$TOKEN_FIELD" ] && PARTS+=("$TOKEN_FIELD")
[ -n "$DIRIGENT_FIELD" ] && PARTS+=("$DIRIGENT_FIELD")
[ -n "$GIT_FIELD" ] && PARTS+=("$GIT_FIELD")

if [ ${#PARTS[@]} -eq 0 ]; then
  printf "dirigent"
else
  printf "%s" "${PARTS[0]}"
  for (( i=1; i<${#PARTS[@]}; i++ )); do
    printf " · %s" "${PARTS[$i]}"
  done
fi
