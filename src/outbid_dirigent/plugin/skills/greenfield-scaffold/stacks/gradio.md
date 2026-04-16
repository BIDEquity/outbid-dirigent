# Gradio

**Role:** ML/Model UI — input-to-output interfaces for models and pipelines
**Tier:** 1 (default for ML demos)
**When:** SPEC is "build a UI for this model" or follows an input → process → output pattern

## Docs

Before using unfamiliar Gradio APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="gradio"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
uv --version
python -c "import gradio; print(gradio.__version__)"
```

## Scaffold

```bash
uv init --name app
uv add gradio
```

Create `app.py`:

```python
import gradio as gr

def process(input_text):
    return f"Processed: {input_text}"

demo = gr.Interface(
    fn=process,
    inputs=gr.Textbox(label="Input"),
    outputs=gr.Textbox(label="Output"),
    title="App Title",
)

if __name__ == "__main__":
    demo.launch()
```

## Run

```bash
uv run python app.py
```

Default port: **7860**

To bind to all interfaces:
```python
demo.launch(server_name="0.0.0.0", server_port=7860)
```

## Test

```bash
uv add --dev pytest
```

Gradio apps are tested via the built-in test client:

```python
# tests/test_app.py
from app import demo

def test_process():
    result = demo.fn("hello")
    assert "Processed" in result

def test_api():
    # Test via Gradio's API client
    with demo.launch(prevent_thread_lock=True) as client:
        result = client.predict("hello", api_name="/predict")
        assert "Processed" in result
```

For simpler function-level testing:

```python
# tests/test_logic.py
from app import process

def test_process_function():
    assert process("hello") == "Processed: hello"
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
exec uv run python app.py
```

## Pairing

- **+ DuckDB** → data processing pipeline with visual interface
- **+ FastAPI** → Gradio as UI, FastAPI for additional API endpoints (Gradio can mount inside FastAPI)
