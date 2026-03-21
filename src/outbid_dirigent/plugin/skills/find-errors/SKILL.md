---
name: find-errors
description: Find errors and failures from past Claude sessions, grouped by type with resolutions
arguments: keyword (optional) - filter errors by keyword
---

# Find Errors

Search past session logs for error patterns — failed commands, tracebacks, and known pitfalls.

## Usage

### Step 1: Determine search path

```bash
PROJECT_KEY=$(echo "$PWD" | sed 's|/|-|g')
SEARCH_PATH="$HOME/.claude/projects/-${PROJECT_KEY#-}/*.jsonl"
```

### Step 2: Find errors

```bash
duckdb :memory: -c "
WITH errors AS (
  SELECT
    timestamp,
    message.role AS role,
    left(message.content::VARCHAR, 500) AS content,
    filename AS session,
    CASE
      WHEN message.content::VARCHAR LIKE '%Traceback%' THEN 'Traceback'
      WHEN message.content::VARCHAR LIKE '%Error:%' THEN 'Error'
      WHEN message.content::VARCHAR LIKE '%FAIL%' THEN 'Test Failure'
      WHEN message.content::VARCHAR LIKE '%exit code%' THEN 'Non-zero Exit'
      WHEN message.content::VARCHAR LIKE '%Permission denied%' THEN 'Permission'
      WHEN message.content::VARCHAR LIKE '%ModuleNotFoundError%' THEN 'Missing Module'
      WHEN message.content::VARCHAR LIKE '%ImportError%' THEN 'Import Error'
      WHEN message.content::VARCHAR LIKE '%SyntaxError%' THEN 'Syntax Error'
      ELSE 'Other'
    END AS error_type
  FROM read_ndjson('$SEARCH_PATH', auto_detect=true, ignore_errors=true, filename=true)
  WHERE message.role = 'tool'
    AND (
      message.content::VARCHAR LIKE '%Error:%'
      OR message.content::VARCHAR LIKE '%FAIL%'
      OR message.content::VARCHAR LIKE '%Traceback%'
      OR message.content::VARCHAR LIKE '%exit code%'
      OR message.content::VARCHAR LIKE '%Permission denied%'
    )
)
SELECT error_type, timestamp, left(content, 300) AS error_context, session
FROM errors
${KEYWORD_FILTER}
ORDER BY timestamp DESC
LIMIT 20;
"
```

If the user provided a keyword, replace `${KEYWORD_FILTER}` with:
```sql
WHERE content ILIKE '%KEYWORD%'
```
Otherwise remove that line.

### Step 3: Check for resolutions

For the most interesting errors, check if the session continued with a fix:

```bash
duckdb :memory: -c "
SELECT timestamp, message.role AS role, left(message.content::VARCHAR, 300) AS content
FROM read_ndjson('SESSION_FILE', auto_detect=true, ignore_errors=true)
WHERE timestamp > 'ERROR_TIMESTAMP'
  AND message.role = 'assistant'
ORDER BY timestamp ASC
LIMIT 3;
"
```

## Output

Present errors grouped by type:
- Error type (Traceback, Test Failure, etc.)
- When it occurred
- Error context (truncated)
- Whether a resolution was found in the same session

This helps avoid known pitfalls and learn from past debugging sessions.
