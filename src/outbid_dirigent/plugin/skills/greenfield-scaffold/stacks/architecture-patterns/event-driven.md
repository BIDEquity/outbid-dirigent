# Event-Driven

Event occurs → publisher fires → N subscribers react independently.

## When to Use

Decoupled side effects. One trigger, multiple reactions.

Classic example: "When a member scans their pass at the door, log the visit AND notify staff AND update the live dashboard AND send welcome SMS." One event, four independent reactions.

## Core Flow

```
trigger happens → publisher.fire(event, payload)
                → subscriber_1.handle(payload)  ┐
                → subscriber_2.handle(payload)  ├─ independent, parallel
                → subscriber_3.handle(payload)  ┘
```

## Domain Signals

- "when X happens, then Y, Z, W"
- "notify", "trigger", "webhook"
- "on scan", "on upload", "on creation"
- "side effects", "fan out"

## Code Example (Python — adapt to your stack's language)

> **Language note:** Python shown for concreteness. TypeScript would use an `EventEmitter` or a simple dispatcher. The pattern is language-agnostic.

**In-process pub/sub (prototype-grade):**
```python
# events.py
from collections import defaultdict
from typing import Callable

_subscribers: dict[str, list[Callable]] = defaultdict(list)

def on(event: str):
    def decorator(fn):
        _subscribers[event].append(fn)
        return fn
    return decorator

def fire(event: str, payload: dict) -> None:
    for fn in _subscribers[event]:
        fn(payload)

# handlers.py
@on("member_scanned")
def log_visit(payload: dict) -> None:
    insert_visit(payload["member_id"])  # data.py

@on("member_scanned")
def notify_staff(payload: dict) -> None:
    send_slack(f"Member {payload['member_id']} entered")

# app.py
def handle_scan(member_id: str) -> None:
    fire("member_scanned", {"member_id": member_id})
```

**Supabase Database Trigger (cross-service):**
```sql
CREATE OR REPLACE FUNCTION handle_scan() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO visits (member_id) VALUES (NEW.member_id);
  PERFORM http_post('http://api/notify', json_build_object('id', NEW.id));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_scan
  AFTER INSERT ON scans
  FOR EACH ROW EXECUTE FUNCTION handle_scan();
```

## Libraries by Stack

| Stack | Idiom |
|---|---|
| Python in-process | Simple pub/sub dict or `asyncio.Event` |
| FastAPI | Webhook endpoints (`POST /webhooks/...`), `BackgroundTasks` |
| Supabase Local | Database triggers, Edge Functions, Realtime channels |
| PocketBase | Hooks (`onRecordCreate`, etc.), Realtime subscriptions |
| Next.js | Server Actions + webhook routes |
| Expo | Push notifications, app state event listeners |

## Anti-Patterns

- **Don't use for synchronous request/response** — that's [Sync REST](sync-rest.md)
- **Don't chain events deeply** (A fires B fires C fires D) — hard to debug, fragile
- **For prototypes: in-process events only** — no Kafka, RabbitMQ, Redis Pub/Sub
- **Don't skip error handling in subscribers** — one failing handler shouldn't kill the event (unless intentional)
- **Don't fire events inside tight loops** without batching — can overwhelm subscribers
