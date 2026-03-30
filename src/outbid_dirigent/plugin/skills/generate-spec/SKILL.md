---
name: generate-spec
description: Generate a SPEC.md from a user description, asking max 2-3 clarifying questions
---

# Generate Spec

You turn a loose user description into a structured SPEC.md that the Dirigent can execute.

## Input

Read `.dirigent/spec-seed.json` which contains:
- `user_description` — what the user typed (e.g. "Add a dark mode toggle")
- `repo_context` — auto-gathered content from ARCHITECTURE.md, README.md, CLAUDE.md

## Step 1: Understand the Request

Read the seed file. Then quickly scan the repo to understand:
- What tech stack is in use (check package.json, pyproject.toml, etc.)
- What existing patterns apply (check ARCHITECTURE.md if it exists)
- Where this feature would live in the codebase

## Step 2: Ask Clarifying Questions (max 2-3)

You may ask **at most 2-3 questions** to resolve genuine ambiguity. Each question should:
- Be specific, not open-ended
- Offer concrete options (not "what do you want?")
- Have a sensible default the user can accept by pressing Enter

Good questions:
- "Should dark mode use CSS variables (recommended for your Tailwind setup) or a ThemeProvider? [CSS variables]"
- "Should the toggle persist in localStorage or user profile DB? [localStorage]"

Bad questions:
- "What should the feature look like?" (too open)
- "What framework are you using?" (you can check)
- "Are there any edge cases?" (you should figure this out)

**If the description is clear enough to act on, skip questions entirely.** Not every request needs clarification. "Add a health check endpoint at /api/health" needs zero questions.

Ask all questions in a single message, not one at a time.

## Step 3: Write SPEC.md

Write `.dirigent/SPEC.md` with this structure:

```markdown
# {Feature Name}

## Goal

{One paragraph: what we're building and why}

## Requirements

{Bulleted list of concrete, testable requirements. Each requirement should be something the reviewer can verify.}

- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Scope

### In Scope
{What this feature includes}

### Out of Scope
{What this feature explicitly does NOT include — prevents scope creep during execution}

## Technical Notes

{Any technical decisions or constraints derived from the repo context. Reference specific files, patterns, or conventions the executor should follow.}
```

## Rules

<rules>
<rule>Max 2-3 questions. If you can figure it out from the repo, don't ask.</rule>
<rule>Questions must offer defaults. The user should be able to press Enter for all of them.</rule>
<rule>The spec must be concrete enough for the Dirigent to create a plan from it.</rule>
<rule>Requirements must be testable — "looks good" is not testable, "dark mode class is applied to body element" is.</rule>
<rule>Out of Scope is required — it prevents the executor from gold-plating.</rule>
<rule>Technical Notes should reference actual files and patterns in the repo.</rule>
<rule>Write the spec even if you couldn't ask questions (non-interactive mode). Use your best judgment.</rule>
<rule>Output path is always .dirigent/SPEC.md — overwrite if it exists.</rule>
</rules>
