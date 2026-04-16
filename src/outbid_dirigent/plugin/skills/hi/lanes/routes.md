# Lane 3 — The 6 Routes

**Goal:** In one scannable table, show the user every execution route dirigent can auto-select, what triggers each, and a one-line example of when to use it. Then route them to the matching lane for hands-on.

## Display this table

| Route | Trigger condition | Phase sequence | Example use case | One-line CLI |
|---|---|---|---|---|
| **Quick** ⚡ | Small, self-contained change doable in 1-3 files | Plan → Execute → Ship | "Fix the typo in the welcome email subject line" | `dirigent --spec SPEC.md --repo .` (auto-routed) |
| **Greenfield** 🌱 | New or small repo, no existing tests, no complex conventions | Scaffold → Plan → Execute → Entropy Min → Ship | "Scaffold a new FastAPI service with auth and a health endpoint" | `dirigent --spec SPEC.md --repo .` |
| **Legacy** 🏛️ | Established codebase with domain rules to preserve, migration-heavy work | Init → Extract Rules → Plan → Execute → Entropy Min → Ship | "Migrate this Rails app's auth from Devise to a custom JWT middleware without losing business rules" | `dirigent --spec SPEC.md --repo . --use-proteus` |
| **Hybrid** 🧩 | Mid-sized repo where only part of the codebase is relevant to the change | Init → Quick Scan → Plan → Execute → Entropy Min → Ship | "Add a new endpoint to an existing API without touching the frontend" | `dirigent --spec SPEC.md --repo .` (auto-routed) |
| **Testability** 🧪 | Repo has poor test coverage and you want to improve *before* adding features | Init → Testability Analysis → Plan → Execute → Ship | "Get this module to 80% coverage and remove the untested death zones" | `dirigent --spec SPEC.md --repo . --route testability` |
| **Tracking** 📊 | Feature is analytics/instrumentation, not behavior | Init → PostHog Setup → Plan → Execute → Ship | "Instrument the checkout flow with PostHog events for conversion tracking" | `dirigent --spec SPEC.md --repo . --route tracking` |

## The selection logic

Dirigent auto-detects the route from the repo state and the SPEC during the `Init` phase. You can override with `--route`, but the auto-detection is usually right:

- **Tiny, self-contained change** → Quick
- **No tests + small codebase** → Greenfield
- **Domain rules + large/legacy codebase** → Legacy (with optional Proteus for deep extraction)
- **Well-bounded change in a mid-sized repo** → Hybrid
- **SPEC is mostly about "add coverage" or "make X testable"** → Testability
- **SPEC is mostly about events, analytics, or instrumentation** → Tracking

## The prompt

After showing the table, ask (via AskUserQuestion):

> "Which one matches what you're trying to do today?"

Options:
- **Quick — tiny self-contained change** → jump to Lane 2 (plan a real change) with the Quick hint
- **Greenfield — I'm building something new** → jump to Lane 2 (plan a real change) with the Greenfield hint
- **Legacy — I'm modifying an established codebase** → jump to Lane 2 with the Legacy hint (and surface `domain-context-beats-orchestration.md`)
- **Hybrid — I'm making a bounded change to an existing repo** → jump to Lane 2 with the Hybrid hint
- **Testability — I want to improve test coverage** → jump to Lane 2 (SPEC should be scoped to test coverage)
- **Tracking — I want to add analytics** → jump to Lane 2 with the Tracking hint
- **None of these / I'm not sure** → jump to Lane 4 (Playbook) with `when-not-to-use-dirigent.md` as the first read

Whatever they pick, the answer is almost always "now let's write a SPEC in Lane 2." Lane 3 is primarily mental-model formation, not a terminal state.
