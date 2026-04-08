#!/usr/bin/env bash
# Dirigent SessionStart UX hook.
#
# Sister to dirigent-hook.sh (which handles telemetry).
# This hook is purely user-facing: detects dirigent state in cwd and emits
# `additionalContext` so the assistant opens the session with the right framing.
#
# Output protocol (Claude Code SessionStart hooks):
#   {
#     "hookSpecificOutput": {
#       "hookEventName": "SessionStart",
#       "additionalContext": "<text appended to system prompt>"
#     }
#   }
#
# We never block; we never write to stderr unless something is wrong with the
# hook itself. The agent reads the additionalContext and decides what to say.

set -uo pipefail

INPUT=$(cat 2>/dev/null || echo "{}")
EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // ""' 2>/dev/null)

if [ "$EVENT" != "SessionStart" ]; then
  # Wrong event — emit nothing.
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd // .workspace.current_dir // ""' 2>/dev/null)
[ -z "$CWD" ] && CWD="$PWD"

# ---------- detect state ----------
HAS_DIRIGENT_DIR=0
HAS_SPEC=0
HAS_PLAN=0
HAS_STATE=0
HAS_RECENT_SUMMARIES=0
PHASE_INFO=""

[ -d "$CWD/.dirigent" ] && HAS_DIRIGENT_DIR=1
[ -f "$CWD/.dirigent/SPEC.md" ] && HAS_SPEC=1
[ -f "$CWD/.dirigent/PLAN.json" ] && HAS_PLAN=1
[ -f "$CWD/.dirigent/STATE.json" ] && HAS_STATE=1
if [ -d "$CWD/.dirigent/summaries" ] && [ -n "$(ls -A "$CWD/.dirigent/summaries" 2>/dev/null)" ]; then
  HAS_RECENT_SUMMARIES=1
fi

if [ "$HAS_STATE" -eq 1 ]; then
  PHASE_INFO=$(jq -r '
    "phase=" + (.current_phase_id // .current_phase // .phase // "?" | tostring)
    + " task=" + (.current_task_id // .current_task // "?" | tostring)
  ' "$CWD/.dirigent/STATE.json" 2>/dev/null || echo "")
fi

# ---------- detect git uncommitted state ----------
GIT_DIRTY=0
if git -C "$CWD" rev-parse --git-dir >/dev/null 2>&1; then
  if [ -n "$(git -C "$CWD" status --porcelain 2>/dev/null)" ]; then
    GIT_DIRTY=1
  fi
fi

# ---------- pick a mode ----------
# Modes mirror skills/hi/SKILL.md state-detection table.
MODE="onboarding"
HINT=""

if [ "$HAS_PLAN" -eq 1 ] && [ "$HAS_STATE" -eq 1 ]; then
  MODE="resume"
  HINT="A dirigent run is in progress (${PHASE_INFO}). If the user asks to continue work, suggest \`/dirigent:show-progress\` and offer to resume from the next task. Do NOT suggest /dirigent:hi as a first move — they are a veteran user; the tool already knows where they are."
elif [ "$HAS_SPEC" -eq 1 ] && [ "$HAS_PLAN" -eq 0 ]; then
  MODE="continue"
  HINT="A SPEC.md exists at .dirigent/SPEC.md but no PLAN.json yet. If the user wants to act on the spec, suggest \`/dirigent:create-plan\` directly. They have already started — do not re-onboard them."
elif [ "$HAS_RECENT_SUMMARIES" -eq 1 ] && [ "$GIT_DIRTY" -eq 1 ]; then
  MODE="recovery"
  HINT="A previous dirigent run completed task summaries (.dirigent/summaries/) and there are uncommitted changes. The user may want to ship/review/discard prior work. Offer \`git status\` and \`/dirigent:show-progress\` as orientation."
elif [ "$HAS_DIRIGENT_DIR" -eq 1 ]; then
  MODE="welcome-back"
  HINT="This repo has used dirigent before but has no active run. Greet the user as a veteran. If they describe building something, route through /dirigent:hi (which will hand off to the right sibling skill). Do not show onboarding lanes unless they explicitly ask."
else
  MODE="onboarding"
  HINT="This repo has no .dirigent/ directory. The user has not started a dirigent run here. If they describe wanting to build, refactor, migrate, or test something, proactively mention \`/dirigent:hi\` as the entry point — it will detect what they need and route to the right skill. Do NOT push it for one-line tweaks, exploratory questions, or debugging — see the playbook canon \`when-not-to-use-dirigent.md\` for the rule."
fi

# ---------- always inject the playbook rules ----------
PLAYBOOK_RULES='Dirigent playbook (apply silently, do not narrate unless asked):
- Spec first: scope battles are cheaper in the SPEC than mid-execution.
- Scope is sacred: do not add features beyond what was asked.
- Verify, do not vibe: every change needs a structural gate (syntax/typecheck/lint) before commit.
- Read before you write: never edit a file you have not read in this session.
- No sycophancy: never say "you are absolutely right" — push back with evidence when warranted.
- Scratch state hygiene: never commit .dirigent/, .dirigent-onboarding/, or other scratch dirs.
- Atomic commits per task: each task is a commit; do not bundle.
Full playbook: skills/hi/playbook/canon/ in the dirigent plugin.'

# ---------- assemble additionalContext ----------
ADDITIONAL_CONTEXT="[Dirigent SessionStart, mode=${MODE}, cwd=${CWD}]
${HINT}

${PLAYBOOK_RULES}"

# ---------- emit ----------
jq -n --arg ctx "$ADDITIONAL_CONTEXT" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $ctx
  }
}'
