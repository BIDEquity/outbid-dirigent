# Anthropic SDK

**Role:** LLM integration — chatbots, AI assistants, structured extraction, document Q&A
**Tier:** 1 (default for any AI feature)
**When:** SPEC mentions AI, LLM, chatbot, assistant, "use Claude", summarization, extraction, or generation

## Docs

Before using unfamiliar Anthropic SDK features, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="anthropic python sdk"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
uv --version
python -c "import anthropic; print(anthropic.__version__)"
```

## Scaffold

```bash
uv add anthropic
```

Minimal usage:

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.content[0].text)
```

## Patterns

### Streaming (always use for UI-facing calls)

```python
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}],
) as stream:
    for text in stream.text_stream:
        yield text  # feed to st.write_stream() or gradio
```

### Structured Output (always use for data extraction)

```python
from pydantic import BaseModel

class ExtractedData(BaseModel):
    name: str
    category: str
    confidence: float

response = client.messages.parse(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": f"Extract from: {text}"}],
    output_schema=ExtractedData,
)
result: ExtractedData = response.parsed
```

### Prompt Caching (always use for repeated system prompts)

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=[{
        "type": "text",
        "text": large_system_prompt,
        "cache_control": {"type": "ephemeral"},
    }],
    messages=conversation,
)
```

### Tool Use

```python
tools = [{
    "name": "search_database",
    "description": "Search the database for records",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    },
}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Find all active users"}],
)
```

## Test

```bash
uv add --dev pytest respx
```

```python
# tests/test_ai.py
import anthropic
from unittest.mock import patch, MagicMock

def test_basic_call():
    """Test that we construct the API call correctly."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello back")]

    with patch.object(anthropic.Anthropic, "messages") as mock_messages:
        mock_messages.create.return_value = mock_response
        client = anthropic.Anthropic(api_key="test-key")
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert response.content[0].text == "Hello back"
```

```bash
uv run pytest tests/ -v
```

## Start Script Pattern

No separate start — included in the app's start script. Just ensure `.env` has `ANTHROPIC_API_KEY`.

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

## Anti-Patterns

- **Don't install LangChain** for API calls — the SDK is 3 lines
- **Don't parse JSON from free text** — use `messages.parse()` + Pydantic
- **Don't skip streaming** for UI — user stares at blank screen for 30s
- **Don't skip caching** for repeated system prompts — 10x cost without it
- **Don't hardcode API keys** — `.env` + `pydantic-settings`
- **Don't send full documents** when a summary or chunk suffices — costs scale linearly with tokens
- **Don't ignore `response.usage`** — log tokens for cost tracking

## Pairing

- **+ Streamlit** → chatbot UI with `st.write_stream()`
- **+ Gradio** → AI demo with streaming output
- **+ FastAPI** → AI-powered API endpoints
- **+ LanceDB** → RAG: retrieve relevant chunks, then send to Claude
- **+ DuckDB** → AI-powered data analysis (natural language → SQL)
