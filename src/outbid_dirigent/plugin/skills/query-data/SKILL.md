---
name: query-data
description: Run ad-hoc DuckDB queries on any data file (CSV, Parquet, JSON, JSONL)
arguments: sql (required) - SQL query to execute
---

# Query Data

Run ad-hoc DuckDB queries on any data file. Works everywhere — no session state needed.

## Usage

Execute the user's SQL query with DuckDB, pre-loading useful extensions:

```bash
duckdb :memory: -c "
INSTALL json; LOAD json;
INSTALL fts; LOAD fts;

$SQL
"
```

Replace `$SQL` with the user's query.

## DuckDB File Reading Cheatsheet

Use these patterns in your queries:

```sql
-- CSV files
SELECT * FROM read_csv('data.csv', auto_detect=true) LIMIT 10;

-- Parquet files
SELECT * FROM read_parquet('data.parquet') LIMIT 10;

-- JSON files
SELECT * FROM read_json('data.json', auto_detect=true) LIMIT 10;

-- JSONL / newline-delimited JSON
SELECT * FROM read_ndjson('data.jsonl', auto_detect=true, ignore_errors=true) LIMIT 10;

-- Glob patterns work everywhere
SELECT * FROM read_csv('data/*.csv', auto_detect=true, filename=true);

-- Schema inspection
DESCRIBE SELECT * FROM read_csv('data.csv', auto_detect=true);
```

## Tips

- Always use `auto_detect=true` for CSV/JSON to let DuckDB infer types
- Use `ignore_errors=true` for JSONL files that may have malformed lines
- Add `filename=true` when reading multiple files via glob to track source
- Use `DESCRIBE` to inspect schema before writing complex queries
- DuckDB can directly query Parquet files without loading them into a table
- Use `LIMIT` when exploring large files to avoid flooding output

## Output

Present query results clearly. If the query fails, show the error and suggest corrections.
