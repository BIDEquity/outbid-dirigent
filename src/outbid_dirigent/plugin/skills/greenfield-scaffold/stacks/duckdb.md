# DuckDB

**Role:** Database (Analytics) — data exploration, dashboards, aggregation queries
**Tier:** 1 (default for analytics workloads)
**When:** SPEC involves data analysis, CSV/Parquet processing, dashboards, or reporting

## Docs

Before using unfamiliar DuckDB features, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="duckdb"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
uv --version
python -c "import duckdb; print(duckdb.__version__)"
```

For CLI:
```bash
duckdb --version
```

## Scaffold

No scaffold needed. Add as dependency:

```bash
uv add duckdb
```

DuckDB runs in-process:

```python
import duckdb

# Read and query files directly — no import step
df = duckdb.sql("SELECT * FROM 'data.csv' LIMIT 10").df()

# Or create a persistent database
conn = duckdb.connect("analytics.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS metrics AS
    SELECT * FROM 'raw_data.parquet'
""")
```

## Run

No separate process. DuckDB runs in-process, embedded in your Python app.

For standalone exploration:
```bash
duckdb analytics.db
```

## Test

```bash
uv add --dev pytest
```

```python
# tests/test_analytics.py
import duckdb

def test_query_csv():
    conn = duckdb.connect()
    conn.execute("CREATE TABLE test AS SELECT 1 as id, 'hello' as name")
    result = conn.execute("SELECT count(*) FROM test").fetchone()
    assert result[0] == 1

def test_aggregation():
    conn = duckdb.connect()
    conn.execute("""
        CREATE TABLE sales AS
        SELECT * FROM (VALUES
            ('A', 100), ('B', 200), ('A', 150)
        ) AS t(category, amount)
    """)
    result = conn.execute("""
        SELECT category, SUM(amount) as total
        FROM sales GROUP BY category ORDER BY total DESC
    """).fetchall()
    assert result[0] == ('B', 200)
    assert result[1] == ('A', 250)
```

```bash
uv run pytest tests/ -v
```

## Start Script Pattern

No separate start needed — included in the app's start script. DuckDB is a library, not a server.

## Pairing

- **+ Streamlit** → the canonical combo for data dashboards
- **+ FastAPI** → analytics API endpoints
- **+ SQLite** → DuckDB for analytics, SQLite for OLTP (both in-process, no conflicts)
