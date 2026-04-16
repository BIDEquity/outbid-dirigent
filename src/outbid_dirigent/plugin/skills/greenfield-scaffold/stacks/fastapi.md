# FastAPI

**Role:** Python Backend — APIs, webhooks, microservices
**Tier:** 1 (default for Python backend)
**When:** SPEC needs an API, backend logic, webhook receiver, or Python backend paired with a JS frontend

## Docs

Before using unfamiliar FastAPI features, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="fastapi"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
uv --version
python -c "import fastapi; print(fastapi.__version__)"
uvicorn --version
```

## Scaffold

```bash
uv init --name app
uv add fastapi 'uvicorn[standard]'
```

Create minimal structure:

```
project/
  main.py
  pyproject.toml
  tests/
    test_main.py
```

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="App Title")

@app.get("/health")
def health():
    return {"status": "ok"}
```

## Run

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Port: **8000** (default)

## Test

```bash
uv add --dev pytest httpx
```

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

```bash
uv run pytest tests/ -v
```

## Start Script Pattern

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
uv sync
exec uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Pairing

- **+ SQLite** → persistent storage (`sqlmodel` package)
- **+ DuckDB** → analytics endpoints
- **+ Supabase Local** → Postgres + auth via connection string
- **+ Vite+React** → FastAPI as API, React as SPA frontend
- **+ Streamlit** → FastAPI as backend, Streamlit as dashboard frontend
