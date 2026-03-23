---
name: search-memories
description: Search past Claude session logs for relevant context using DuckDB
arguments: keyword (required) - search term, --all (optional) - search across all projects
---

# Search Memories

Search past Claude Code session logs for relevant context.

**Important**: Session log content is JSON-encoded (tool_use arrays), so DuckDB FTS cannot tokenize it properly. Use ILIKE for reliable results.

## Usage

When invoked with a keyword, run the following in Bash. Replace `$KEYWORD` with the user's search term.

### Step 1: Determine search path

```bash
# Current project sessions (default)
PROJECT_KEY=$(echo "$PWD" | sed 's|/|-|g')
SEARCH_PATH="$HOME/.claude/projects/-${PROJECT_KEY#-}/*.jsonl"

# If --all flag is set, search all projects:
# SEARCH_PATH="$HOME/.claude/projects/*/*.jsonl"
```

### Step 2: Search via ILIKE

```bash
duckdb :memory: -c "
SELECT timestamp,
  message.role AS role,
  left(message.content::VARCHAR, 300) AS context
FROM read_ndjson('$SEARCH_PATH', auto_detect=true, ignore_errors=true)
WHERE message.content::VARCHAR ILIKE '%$KEYWORD%'
ORDER BY timestamp DESC
LIMIT 10;
"
```

### Step 3: For multi-keyword search, combine with AND

```bash
duckdb :memory: -c "
SELECT timestamp,
  message.role AS role,
  left(message.content::VARCHAR, 300) AS context
FROM read_ndjson('$SEARCH_PATH', auto_detect=true, ignore_errors=true)
WHERE message.content::VARCHAR ILIKE '%KEYWORD1%'
  AND message.content::VARCHAR ILIKE '%KEYWORD2%'
ORDER BY timestamp DESC
LIMIT 10;
"
```

### Step 4 (optional): Extract specific patterns

For structured extraction (e.g. commands, errors, file paths):

```bash
duckdb :memory: -c "
SELECT timestamp,
  regexp_extract(message.content::VARCHAR, '\"command\":\"([^\"]+)\"', 1) AS command,
  left(message.content::VARCHAR, 200) AS context
FROM read_ndjson('$SEARCH_PATH', auto_detect=true, ignore_errors=true)
WHERE message.content::VARCHAR ILIKE '%$KEYWORD%'
  AND message.content::VARCHAR LIKE '%command%'
ORDER BY timestamp DESC
LIMIT 10;
"
```

## Output

Present the results as a list with:
- Timestamp
- Role (user/assistant/tool)
- Context snippet (first 300 chars)

If no results found, say so clearly — the keyword may not appear in past sessions.
