# ADR-0001: Migrate control-plane LLM callers from Anthropic SDK to Claude Agent SDK

**Status:** Accepted
**Date:** 2026-04-20
**Author:** Jonah Kresse

## Context

Three control-plane modules called the Anthropic LLM directly via the raw
`anthropic.Anthropic()` client:

- `src/outbid_dirigent/llm_router.py`
- `src/outbid_dirigent/spec_compactor.py`
- `src/outbid_dirigent/init_phase.py`

The rest of the codebase — `task_runner.py` and `oracle.py` — already routed
through `claude_agent_sdk.query()`, inheriting Claude Code's machine auth. The
split produced two incompatible auth regimes inside a single dirigent run: SDK
callers worked in any environment Claude Code could run in, while the raw-
Anthropic callers required `ANTHROPIC_API_KEY` to be present.

The 2026-04-18 `cuseum-vam-full` dogfood surfaced the consequence at runtime.
SDK-based steps executed cleanly; `spec_compactor` and `llm_router` died at
run start because the environment had machine auth but no API key. The bug
was structural, not a misconfiguration — as long as two SDKs coexisted,
every new deployment target would be fragile.

Unifying on the Claude Agent SDK was also a prerequisite for the
single-`ClaudeSDKClient` session direction captured in the orchestrator
follow-up notes.

## Decision

Route every control-plane LLM call through `claude_agent_sdk.query()`, using
the pattern established in `oracle.py`:

```python
from claude_agent_sdk import query as sdk_query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage

options = ClaudeAgentOptions(
    model=model,
    allowed_tools=[],
    permission_mode="bypassPermissions",
    system_prompt=SYSTEM_PROMPT,
    output_format={"type": "json_schema", "schema": strict_json_schema(Schema.model_json_schema())},
)
async for message in sdk_query(prompt=prompt, options=options):
    if isinstance(message, ResultMessage) and not message.is_error:
        return message.structured_output, (message.usage or {})
```

Sync call sites bridge with `asyncio.run(_aquery(...))`. Drop the `anthropic`
dependency from `pyproject.toml`. Preserve per-component API usage logging by
reading defensively from the `ResultMessage.usage` dict.

Skill-template markdown under
`src/outbid_dirigent/plugin/skills/greenfield-scaffold/stacks/` that
recommends the `anthropic` SDK to *generated* projects stays unchanged —
those are guidance for user-built apps, not control-plane calls from dirigent
itself.

Shipped on `feat/v2` in commit `cde939c` (2026-04-18).

## Consequences

**Positive**

- Single auth path for all dirigent-initiated LLM calls; no more
  `ANTHROPIC_API_KEY` surface in control-plane code.
- Every component works identically under Claude Code's machine auth —
  dogfood failure mode eliminated at the source.
- Consistent structured-output contract across components via the SDK's
  JSON-schema `output_format`.
- Unblocks the single-`ClaudeSDKClient`-session direction for the
  orchestrator skill rewrite.
- Drops one Python dependency (`anthropic`) and its transitive surface.

**Negative / trade-offs**

- Adds async/sync bridge boilerplate (`asyncio.run(_aquery(...))`) at each
  synchronous call site.
- Couples control-plane components to `claude-agent-sdk` release cadence and
  the `ResultMessage.usage` dict shape — requires defensive `.get()` reads
  whenever the SDK adds or renames usage keys.
- The SDK's streaming message loop is heavier than a direct
  `messages.create()` call when all we want is a single structured output.
- Not yet verified end-to-end by a live run after commit — memory flags
  this as pending confirmation on the next dogfood.

## Alternatives Considered

**Keep the Anthropic SDK and require `ANTHROPIC_API_KEY` in every
environment.** Rejected: diverges from the rest of the codebase's auth
model, fails under machine-auth-only environments (Claude Code harness,
CI runners without the key), and treats the dogfood failure as a config
problem instead of a structural one.

**Keep the split — some components on `anthropic`, others on the SDK.**
Rejected: the split is exactly what caused the `cuseum-vam-full` failure.
Every new caller becomes a forking decision; the cost compounds.

**Build a thin abstraction over both SDKs.** Rejected: premature. Only one
caller (`oracle.py`) had the target pattern and it worked; adding an
abstraction layer for a one-directional migration violates the "no new
complexity layers" rule in `CLAUDE.md`. If a second LLM backend becomes
necessary later, this ADR can be superseded.

**Rewrite onto a third SDK (e.g. `langchain`, `instructor`).** Rejected:
introduces a larger migration with its own API churn, adds a dependency with
a much wider surface than `claude-agent-sdk`, and buys nothing that the
existing SDK doesn't already provide (JSON-schema output, usage accounting).
