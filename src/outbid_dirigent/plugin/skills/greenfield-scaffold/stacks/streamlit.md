# Streamlit

**Role:** Python UI — dashboards, data apps, internal tools
**Tier:** 1 (default for Python UI)
**When:** SPEC mentions data, dashboard, analytics, internal tool, or "show me X"

## Docs

Before using unfamiliar Streamlit APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="streamlit"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
uv --version
python -c "import streamlit; print(streamlit.__version__)"
```

## Scaffold

```bash
uv init --name app
uv add streamlit
```

Create `app.py`:

```python
import streamlit as st

st.set_page_config(page_title="App Title", layout="wide")
st.title("App Title")
```

## Run

```bash
uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

Port: **8501** (default)

## Test

Streamlit apps are tested via `pytest` + the built-in `AppTest` API:

```bash
uv add --dev pytest
```

```python
# tests/test_app.py
from streamlit.testing.v1 import AppTest

def test_app_runs():
    at = AppTest.from_file("app.py")
    at.run(timeout=10)
    assert not at.exception

def test_title_displayed():
    at = AppTest.from_file("app.py")
    at.run(timeout=10)
    assert at.title[0].value == "App Title"
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
exec uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

## Pairing

- **+ DuckDB** → analytics dashboards (read CSV/Parquet directly)
- **+ FastAPI** → Streamlit as frontend, FastAPI as backend API
- **+ SQLite** → persistent app state
- **+ PocketBase** → auth + user management
