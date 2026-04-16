# Streaming

Start operation → yield chunks as they're produced → close stream.

## When to Use

- LLM responses (tokens stream as generated)
- Log tailing
- Sensor feeds / telemetry
- Progress updates for long operations
- Large responses where first-byte latency matters

## Core Flow

```
client subscribes → server produces chunks → each chunk sent immediately → close
```

## Domain Signals

- "live updates"
- "as it happens"
- "streaming response"
- "progress updates"
- "real-time log tail"

## Code Example (Python — adapt to your stack's language)

> **Language note:** Python shown for concreteness. TypeScript uses `ReadableStream` / `EventSource` / Next.js Streaming RSC for the same pattern.

**Anthropic SDK + Streamlit (LLM streaming):**
```python
# app.py
def stream_answer(question: str):
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": question}],
    ) as stream:
        for text in stream.text_stream:
            yield text

question = st.text_input("Ask")
if question:
    st.write_stream(stream_answer(question))
```

**FastAPI Server-Sent Events:**
```python
# app.py
from fastapi.responses import StreamingResponse

@app.get("/stream/logs")
async def stream_logs():
    async def gen():
        async for line in tail_log_file():  # data.py
            yield f"data: {line}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
```

## Libraries by Stack

| Stack | Idiom |
|---|---|
| FastAPI | `StreamingResponse` with async generators |
| Streamlit | `st.write_stream(generator)` |
| Gradio | `yield` inside the handler function |
| Anthropic SDK | `client.messages.stream()` context manager |
| Next.js | Streaming Server Components, ReadableStream in Route Handlers |
| Vite+React | `EventSource` / `fetch` with `response.body.getReader()` |
| Expo | `EventSource` polyfill, or WebSocket for bidirectional |

## Anti-Patterns

- **Don't conflate with WebSocket-for-collaboration** — that's [Real-time](real-time.md), not Streaming
- **Don't buffer the full result before yielding** — defeats the purpose; use generators
- **Don't forget to close the stream on error** — use try/finally or context managers
- **Don't use for fire-and-forget** — if the client doesn't need progress, just return the final result
