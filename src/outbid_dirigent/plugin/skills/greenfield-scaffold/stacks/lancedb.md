# LanceDB

**Role:** Vector database (embedded) — semantic search, RAG, document Q&A
**Tier:** 1 (default for semantic search / RAG)
**When:** SPEC mentions document search, Q&A over documents, semantic search, similarity, or RAG

## Docs

Before using unfamiliar LanceDB APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="lancedb"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
uv --version
python -c "import lancedb; print(lancedb.__version__)"
```

## Scaffold

```bash
uv add lancedb sentence-transformers
```

LanceDB is embedded — no server, no Docker, no config. Data stored in local directory.

```python
import lancedb

db = lancedb.connect("./lance_data")
```

## Patterns

### Create table with embeddings

```python
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry

# Use sentence-transformers for local embeddings (no API key needed)
embedder = get_registry().get("sentence-transformers").create(name="all-MiniLM-L6-v2")

class Document(LanceModel):
    text: str = embedder.SourceField()
    vector: Vector(384) = embedder.VectorField()  # 384 = MiniLM output dim
    source: str

db = lancedb.connect("./lance_data")
table = db.create_table("documents", schema=Document, mode="overwrite")
```

### Ingest documents

```python
table.add([
    {"text": "The museum opens at 9am", "source": "faq.md"},
    {"text": "Tickets cost $25 for adults", "source": "pricing.md"},
    {"text": "Children under 5 enter free", "source": "pricing.md"},
])
```

### Search (semantic)

```python
results = table.search("what time does it open?").limit(3).to_pandas()
# Returns: text, source, _distance (lower = more similar)
```

### RAG pattern (search → send to Claude)

```python
import anthropic

def ask(question: str) -> str:
    # Retrieve relevant context
    results = table.search(question).limit(5).to_pandas()
    context = "\n\n".join(results["text"].tolist())

    # Send to Claude with context
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system="Answer based only on the provided context. If the context doesn't contain the answer, say so.",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }],
    )
    return response.content[0].text
```

## Run

No separate process. LanceDB runs in-process. Data is stored in `./lance_data/`.

## Test

```bash
uv add --dev pytest
```

```python
# tests/test_search.py
import lancedb

def test_ingest_and_search(tmp_path):
    db = lancedb.connect(str(tmp_path / "test_lance"))
    table = db.create_table("docs", data=[
        {"text": "hello world", "vector": [0.1] * 384, "source": "test"},
        {"text": "goodbye world", "vector": [0.9] * 384, "source": "test"},
    ])
    results = table.search([0.1] * 384).limit(1).to_pandas()
    assert len(results) == 1
    assert results.iloc[0]["text"] == "hello world"
```

```bash
uv run pytest tests/ -v
```

## Start Script Pattern

No separate start needed — LanceDB is a library, not a server. Data dir (`lance_data/`) is created on first use.

## Pairing

- **+ Anthropic SDK** → RAG: retrieve chunks, send to Claude for answer
- **+ Streamlit** → document Q&A UI
- **+ FastAPI** → search API endpoints
- **+ DuckDB** → combine semantic search with analytical queries
