---
name: find-edits
description: Find all Edit/Write tool calls for a file from past Claude sessions
arguments: file_path (required) - file path or pattern to search for
---

# Find Edits

Find all Edit and Write tool calls that touched a specific file across past sessions.

## Usage

Replace `$PATTERN` with the file path or pattern provided by the user.

### Step 1: Determine search path

```bash
PROJECT_KEY=$(echo "$PWD" | sed 's|/|-|g')
SEARCH_PATH="$HOME/.claude/projects/-${PROJECT_KEY#-}/*.jsonl"
```

### Step 2: Query for edits

```bash
duckdb :memory: -c "
WITH tool_calls AS (
  SELECT timestamp, filename,
    unnest(from_json(
      message.content::VARCHAR,
      '[{\"type\":\"VARCHAR\",\"name\":\"VARCHAR\",\"input\":\"JSON\"}]'
    )) AS item
  FROM read_ndjson('$SEARCH_PATH', auto_detect=true, ignore_errors=true, filename=true)
  WHERE message.role = 'assistant'
    AND message.content::VARCHAR LIKE '%Edit%'
    OR message.content::VARCHAR LIKE '%Write%'
)
SELECT
  timestamp,
  json_extract_string(item, '\$.name') AS tool,
  json_extract_string(item, '\$.input.file_path') AS file,
  left(json_extract_string(item, '\$.input.old_string'), 80) AS old_text,
  left(json_extract_string(item, '\$.input.new_string'), 80) AS new_text,
  left(json_extract_string(item, '\$.input.content'), 80) AS write_content,
  filename AS session
FROM tool_calls
WHERE json_extract_string(item, '\$.name') IN ('Edit', 'Write')
  AND json_extract_string(item, '\$.input.file_path') LIKE '%$PATTERN%'
ORDER BY timestamp DESC
LIMIT 20;
"
```

## Output

Present the results showing:
- When the edit was made
- Which tool (Edit vs Write)
- The file path
- For Edits: what was replaced (old -> new), truncated to 80 chars
- For Writes: first 80 chars of content
- Which session it came from

This helps understand what approaches were tried before on a file and avoid repeating failed changes.
