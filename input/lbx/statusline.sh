#!/bin/bash
INPUT=$(cat)
MODEL=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('model',{}).get('display_name','?'))" 2>/dev/null)
CTX=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('context_window',{}).get('used_percentage') or 0)" 2>/dev/null)

CACHE_FILE=~/.claude/claude-quota-cache.json
CACHE_TTL=300  # 5 minutes

fetch_quota() {
    TOKEN=$(python3 -c "
import json, os
try:
    creds = json.load(open(os.path.expanduser('~/.claude/.credentials.json')))
    print(creds.get('claudeAiOauth', {}).get('accessToken', ''))
except:
    pass
" 2>/dev/null)
    [ -z "$TOKEN" ] && return
    curl -s --max-time 5 \
        -H "Authorization: Bearer $TOKEN" \
        -H "anthropic-beta: oauth-2025-04-20" \
        -H "User-Agent: claude-code/2.0.32" \
        "https://api.anthropic.com/api/oauth/usage" > "$CACHE_FILE" 2>/dev/null
}

if [ -f "$CACHE_FILE" ]; then
    AGE=$(( $(date +%s) - $(date -r "$CACHE_FILE" +%s) ))
    [ "$AGE" -gt "$CACHE_TTL" ] && fetch_quota
else
    fetch_quota
fi

H5="?"
W7="?"
if [ -f "$CACHE_FILE" ]; then
    H5=$(python3 -c "
import json
try:
    d = json.load(open('${CACHE_FILE}'))
    v = d.get('five_hour', {}).get('utilization', '?')
    print(round(v) if isinstance(v, (int, float)) else v)
except:
    print('?')
" 2>/dev/null)
    W7=$(python3 -c "
import json
try:
    d = json.load(open('${CACHE_FILE}'))
    v = d.get('seven_day', {}).get('utilization', '?')
    print(round(v) if isinstance(v, (int, float)) else v)
except:
    print('?')
" 2>/dev/null)
fi

BRANCH=$(git -C "$(pwd)" rev-parse --abbrev-ref HEAD 2>/dev/null)
TASK_ID=$(echo "$BRANCH" | grep -oP 'DV-\d+' | head -1)
if [ -n "$TASK_ID" ]; then
    TASK_SUFFIX="$TASK_ID"
elif [ -n "$BRANCH" ]; then
    [ ${#BRANCH} -gt 12 ] && TASK_SUFFIX="${BRANCH:0:12}..." || TASK_SUFFIX="$BRANCH"
fi

echo "[$MODEL] ${CTX}% context | 5h: ${H5}% | 7d: ${W7}% | ${TASK_SUFFIX}"
