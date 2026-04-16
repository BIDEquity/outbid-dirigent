# Agent Loop

LLM called with tools → LLM decides next action → execute tool → feed result back → repeat until done.

## When to Use

Problems where the sequence of steps can't be predicted upfront. The LLM needs to iterate, using tools, to reach a result.

Examples: research assistants, multi-step reasoning, data exploration agents, code analysis tools.

## Core Flow

```
user_query → LLM(tools) → decides: "use tool X with args Y"
           → execute X(Y) → result
           → LLM(messages + result) → decides: "use tool Z" OR "done, here's answer"
           → ... repeat until stop_reason == "end_turn"
```

## Domain Signals

- "AI agent", "research assistant"
- "self-directed", "autonomous"
- "tool use", "can execute commands"
- "explore the data and answer"

## Code Example (Python — adapt to your stack's language)

> **Language note:** Python shown because the Anthropic SDK's Python API is the canonical reference. TypeScript has `@anthropic-ai/sdk` with the same semantics.

**Anthropic SDK with tool_use:**
```python
# agent.py
from anthropic import Anthropic

client = Anthropic()

TOOLS = [
    {
        "name": "search_docs",
        "description": "Search internal documentation",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file from the workspace",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]

def dispatch_tool(name: str, args: dict) -> str:
    if name == "search_docs":
        return search(args["query"])       # data.py
    if name == "read_file":
        return read_file(args["path"])     # data.py
    raise ValueError(f"Unknown tool: {name}")

def run_agent(user_query: str, max_iterations: int = 10) -> str:
    messages = [{"role": "user", "content": user_query}]
    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )
        if response.stop_reason == "end_turn":
            return "".join(b.text for b in response.content if b.type == "text")

        # Model requested a tool
        tool_use = next(b for b in response.content if b.type == "tool_use")
        result = dispatch_tool(tool_use.name, tool_use.input)
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": str(result),
            }],
        })
    raise RuntimeError(f"Agent did not converge in {max_iterations} iterations")
```

## Libraries by Stack

| Stack | Idiom |
|---|---|
| Anthropic SDK (Python) | `messages.create(tools=..., messages=...)` with `tool_use` blocks |
| Anthropic SDK (TS) | Same API in `@anthropic-ai/sdk` |
| FastAPI | Endpoint runs the loop, streams intermediate steps via SSE |
| Streamlit | Run loop in a callback, display progress via `st.status` |
| Supabase Edge Functions | Agent loop in a serverless function |

**Avoid:** LangChain / LangGraph / CrewAI / AutoGen. Too much abstraction, opaque behavior, hard to debug. The raw SDK is 30 lines.

## Anti-Patterns

- **Don't loop without `max_iterations`** — runaway costs if the agent doesn't converge
- **Don't skip error recovery on tool failures** — feed the error back to the agent
- **Don't let the agent call arbitrary code** — validate tool inputs strictly
- **Don't skip logging tool calls** — you need to audit what the agent did
- **Don't use this for simple Q&A** — if you don't need tools, just call `messages.create()` directly
