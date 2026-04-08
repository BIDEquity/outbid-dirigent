# Lane 2 — Plan a real change in THIS repo

**Goal:** Let the user describe one real feature they want, produce a real SPEC + PLAN for it, show them, and leave the repo in a clean state whether they execute it or not.

## The safety invariant

All artifacts this lane creates live in `.dirigent-onboarding/`, NOT `.dirigent/`. This is deliberate:

1. It keeps the real `.dirigent/` directory reserved for actual dirigent runs.
2. It makes cleanup trivial — `rm -rf .dirigent-onboarding/` and nothing is lost.
3. It models `scratch-state-hygiene.md` by example: the onboarding flow itself practices the hygiene it preaches.

Before writing any file, ensure `.dirigent-onboarding/` is in the repo's `.gitignore`. If it is not, add it (with a comment: `# Dirigent onboarding scratch — safe to delete`) and tell the user.

## Script

### Step 1 — Ask for the idea

Use AskUserQuestion (or free text if a multi-line response is needed):

> "What do you want to build? Give me one sentence — I'll ask for clarification if I need it. Examples: 'add a health check endpoint', 'add dark mode toggle', 'refactor auth to use JWT'."

### Step 2 — Prep the scratch dir

```bash
mkdir -p .dirigent-onboarding
# Ensure gitignore
if ! grep -q "^.dirigent-onboarding/" .gitignore 2>/dev/null; then
  echo "" >> .gitignore
  echo "# Dirigent onboarding scratch — safe to delete" >> .gitignore
  echo ".dirigent-onboarding/" >> .gitignore
fi
```

Tell the user: "Writing to `.dirigent-onboarding/` — this is gitignored, nothing here will land in a PR."

### Step 3 — Invoke `dirigent:generate-spec`

Set `DIRIGENT_RUN_DIR=.dirigent-onboarding` in the environment (or equivalent mechanism matching how sibling skills resolve the run dir). Create a `spec-seed.json`:

```json
{
  "user_description": "<what the user typed>",
  "repo_context": "<auto-gathered from ARCHITECTURE.md, README.md, CLAUDE.md if present>"
}
```

Then invoke `dirigent:generate-spec`. It will ask at most 2-3 clarifying questions and produce `.dirigent-onboarding/SPEC.md`.

### Step 4 — Invoke `dirigent:create-plan`

With `DIRIGENT_RUN_DIR=.dirigent-onboarding` still set, invoke `dirigent:create-plan`. It reads the SPEC and produces `.dirigent-onboarding/PLAN.json`.

### Step 5 — Render via `/dirigent:show-plan`

Invoke `/dirigent:show-plan` against `.dirigent-onboarding/PLAN.json`. (If show-plan assumes `${DIRIGENT_RUN_DIR}/PLAN.json`, set the env var appropriately or pass the path as an argument — check the command's signature.)

### Step 6 — Narrate + next-step menu

> "That's the plan dirigent would execute for your feature. Three options from here:"

Present via AskUserQuestion:

- **Execute it now** — run `dirigent --spec .dirigent-onboarding/SPEC.md --repo .`. Before kicking off, surface `spec-first-or-suffer.md` as a 30-second preview: "One last gut-check — does the SPEC capture what you actually want? If anything's off, stop now. Mid-run corrections are expensive."
- **Execute it inside a worktree first** — use `superpowers:using-git-worktrees` to create an isolated worktree, run dirigent there, let the user inspect the output before merging.
- **Just save the plan and stop** — leave `.dirigent-onboarding/` in place for the user to inspect and execute later on their own time.
- **Throw it away** — `rm -rf .dirigent-onboarding/`. Thank them for trying it.

### Step 7 — Contextual canon

If the user chose "execute it now" and the SPEC's scope looks thin (e.g. no out-of-scope section, vague requirements, only 1-2 Rn entries), surface `spec-first-or-suffer.md` as a pre-flight check before kicking off.

If the user said something like "it's just a small change" or "I don't really need a full SPEC for this," surface `when-not-to-use-dirigent.md` instead.

## Cleanup invariant

At the end of this lane, no matter the path taken:
- `.dirigent/` is untouched.
- `.dirigent-onboarding/` either still exists (user opted to keep) or was deleted (user opted to discard).
- `.gitignore` contains `.dirigent-onboarding/` if it wasn't already there.
- No uncommitted changes the user didn't authorize.
