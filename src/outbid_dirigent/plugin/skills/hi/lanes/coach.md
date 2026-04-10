# Coach mode — free-text intent routing

**Goal:** When the user types `/dirigent:hi <some natural-language intent>` or answers "What do you want to build?" with a sentence, classify the intent and route to the right sibling skill. Narrate the decision so the user learns the workflow.

## Intent classes and routing

Classify the user's intent into one of these categories. LLM-mediated — no rules engine, just good judgment.

| Intent | Signals | Route to | Notes |
|---|---|---|---|
| **Feature** | "add X", "build Y", "create Z endpoint", "new page" | `dirigent:generate-spec` → `dirigent:create-plan` | Standard happy path. Ask what kind of repo (route hint from Lane 3). |
| **Migration** | "migrate from X to Y", "rewrite this in Z", "replace the old W" | `dirigent:extract-business-rules` → `dirigent:generate-spec` → `dirigent:create-plan` | Legacy route. Surface `domain-context-beats-orchestration.md` before starting. |
| **Quick tweak** | "rename this", "fix this typo", "update this constant" | (redirect to plain Claude Code) | Surface `when-not-to-use-dirigent.md`. Don't invoke dirigent for 1-line changes. |
| **Bug fix** | "fix the bug in X", "Y is broken", "Z throws when…" | Triage first: is it reproducible and bounded? If yes → `dirigent:quick-feature`. If "I'm still debugging it" → redirect to interactive mode. | Bug fixes are often quick tweaks in disguise. |
| **Test coverage** | "add tests for X", "improve coverage on Y", "make this testable" | `dirigent:increase-testability` → then `dirigent:generate-spec` | Testability route. |
| **Tracking / analytics** | "add PostHog events", "instrument the checkout flow", "track user behavior in X" | `dirigent:add-posthog` → `dirigent:create-plan` | Tracking route. |
| **Explore** | "how does X work?", "where is Y defined?", "explain this codebase" | (redirect — this is not a dirigent task) | Use the Explore subagent or plain Claude Code. Dirigent is for execution, not discovery. |
| **Documentation** | "generate an ARCHITECTURE.md", "write CONVENTIONS.md", "update the README" | `dirigent:generate-architecture` or `dirigent:generate-conventions` directly | These skills are self-contained. |

## The narration pattern

Before invoking any sibling skill, tell the user *what* you're doing and *why*. This is what makes the coach educational rather than magical.

Template:

> "This looks like a [intent class] — you want to [paraphrase the goal]. I'm going to:
>
> 1. Run `dirigent:generate-spec` to turn your description into a SPEC.md. It'll ask you at most 2-3 clarifying questions.
> 2. Then `dirigent:create-plan` to produce a PLAN.json with phases and tasks.
> 3. I'll show you both before we execute anything.
>
> Sound right? (Or say 'skip' if you want to go straight to execution.)"

The user sees the three-step pipeline every time. After a few sessions, they internalize it and the narration can shrink.

## Decision points where canon surfaces

The coach watches for these moments and surfaces the matching canon file as optional depth:

- User says "skip the spec" or "just implement it" → `spec-first-or-suffer.md` (2-min read before proceeding)
- User says "it's just a small change" → `when-not-to-use-dirigent.md` (maybe wrong tool)
- User expresses frustration that dirigent produces "generic" code in their repo → `domain-context-beats-orchestration.md`
- User asks why dirigent commits so often → `atomic-commits-per-task.md`
- User catches the agent "agreeing with everything" → `no-sycophancy-rule.md`
- User asks how verification works → `verify-dont-vibe.md`
- User finds scratch dirs in a PR → `scratch-state-hygiene.md`
- User is new and asks "where do I even start?" → `terminal-survival-kit.md` or `installing-dirigent.md` (Track C)

Surface rules: one canon per decision point, never twice in one session, always with the file path so the user can re-read it later.

## When to hand off entirely

After the coach routes to a sibling skill, it steps back. The coach is a router, not a babysitter. Let `generate-spec` do its job without the coach narrating every sub-step. Re-engage only when:

1. The sibling skill completes and the next routing decision is needed.
2. The user explicitly asks the coach something mid-flow.
3. A canon decision point fires.

Otherwise: silence is correct.
