# SQLite

**Role:** Database (OLTP) — persistent app storage, user data, CRUD
**Tier:** 1 (default for transactional storage)
**When:** App needs persistent data without a separate database server

## Docs

Before using unfamiliar SQLite features or Python's sqlite3 API, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="python"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="sqlite3 module"` → get current docs

## Check Installation

```bash
python -c "import sqlite3; print(sqlite3.sqlite_version)"
# Always available — ships with Python
```

For Node.js:
```bash
node -e "require('better-sqlite3')" 2>/dev/null && echo "OK" || echo "npm install better-sqlite3"
```

## Scaffold

No scaffold needed. Create the database in code:

Python:
```python
import sqlite3

def init_db(path="app.db"):
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn
```

Node.js:
```javascript
import Database from 'better-sqlite3'

const db = new Database('app.db')
db.exec(`
  CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`)
```

## Run

No separate process. SQLite runs in-process. The database file is created on first use.

## Test

```bash
uv add --dev pytest  # if in a Python project
```

```python
# tests/test_db.py
import sqlite3
import os

def test_init_and_crud():
    db_path = "test.db"
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
        conn.execute("INSERT INTO items (title) VALUES (?)", ("Test",))
        conn.commit()

        row = conn.execute("SELECT title FROM items WHERE id = 1").fetchone()
        assert row[0] == "Test"
        conn.close()
    finally:
        os.unlink(db_path)
```

```bash
uv run pytest tests/ -v
```

## Start Script Pattern

No separate start needed — included in the app's start script. Just ensure the database file path is writable.

## Pairing

- **+ FastAPI** → `sqlite3` or `sqlmodel` for ORM
- **+ Streamlit** → direct queries for data display
- **+ Next.js** → `better-sqlite3` in API routes
- **+ PocketBase** → PocketBase uses SQLite internally (no need to wire separately)
