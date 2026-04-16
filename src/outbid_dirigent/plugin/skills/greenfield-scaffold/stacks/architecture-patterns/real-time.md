# Real-time / Collaborative

Clients connect → shared state → broadcasts on changes.

## When to Use

Multiple clients see the same state live. When one client changes something, all others see it immediately.

Examples: chat rooms, shared editors (Figma, Notion), multiplayer games, live dashboards with cross-user sync, kanban boards.

## Core Flow

```
client_A connects  ─┐
client_B connects  ─┼── server holds shared state
client_C connects  ─┘
                    ↓
client_A mutates → server updates state → broadcast to A, B, C
```

## Domain Signals

- "collaborative", "shared"
- "multi-user live"
- "see others' changes", "presence"
- "kanban", "whiteboard", "chat room"

## Code Example (Python — adapt to your stack's language)

> **Language note:** Python shown for the FastAPI variant. Supabase Realtime is used from TypeScript/JS in the client examples because that's where it shines.

**FastAPI WebSocket:**
```python
# app.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
connections: list[WebSocket] = []
state: dict = {"cards": []}  # prototype: in-memory

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    await websocket.send_json({"type": "state", "data": state})
    try:
        while True:
            msg = await websocket.receive_json()
            apply_mutation(state, msg)           # domain.py
            for conn in connections:
                await conn.send_json({"type": "update", "data": msg})
    except WebSocketDisconnect:
        connections.remove(websocket)
```

**Supabase Realtime (from Next.js client):**
```typescript
// lib/realtime.ts
import { createClient } from "@supabase/supabase-js"

const supabase = createClient(url, anonKey)

export function subscribeToCards(onChange: (card: Card) => void) {
  return supabase
    .channel("cards")
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "cards" },
      (payload) => onChange(payload.new as Card),
    )
    .subscribe()
}
```

## Libraries by Stack

| Stack | Idiom |
|---|---|
| FastAPI | `WebSocket` endpoints + in-memory broadcast list (prototype) |
| Supabase Local | Realtime channels (best for prototypes — automatic broadcast on DB changes) |
| PocketBase | Realtime subscriptions on collections |
| Next.js | WebSocket or Server-Sent Events; Supabase Realtime in client |
| Vite+React | `WebSocket` API or `@supabase/supabase-js` |
| Expo | `WebSocket` API or Supabase client |

## Anti-Patterns

- **Don't poll via HTTP** — defeats the purpose; use WebSocket or Realtime
- **Don't skip conflict handling** — for prototypes, last-write-wins is fine; for production, add CRDTs / operational transform
- **Don't mix with [Streaming](streaming.md)** — different pattern, different use case (streaming = server-to-one-client; real-time = many-to-many)
- **Don't hold state only in memory without persistence** if you care about restart — fine for prototypes
- **Don't forget to remove disconnected clients** — leaks memory and fails broadcasts
