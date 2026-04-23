---
name: generate-spec
description: Generate a SPEC.md from a user description, with optional clarifying questions
context: fork
---

# Generate Spec

Turn a user description into a structured SPEC.md by filling the template at
`${CLAUDE_SKILL_DIR}/templates/SPEC.template.md`.

## Invocation

This skill takes one optional argument in `$ARGUMENTS`: a path to a config JSON file.

### With config file (programmatic)

```
/dirigent:generate-spec /abs/path/to/spec-config.json
```

Config JSON schema:

```json
{
  "output_path":      "/abs/path/to/SPEC.md",
  "user_description": "Add a dark mode toggle",
  "repo_context":     "...optional pre-gathered context as a single string...",
  "mode":             "interactive"
}
```

| Field              | Required | Notes                                                      |
|--------------------|----------|------------------------------------------------------------|
| `output_path`      | yes      | Where to write the SPEC. Overwrite if it exists.          |
| `user_description` | yes      | What the user wants built.                                 |
| `repo_context`     | no       | If absent, gather it yourself (Step 1 below).              |
| `mode`             | no       | `"interactive"` (default) or `"non-interactive"`.          |

### Without args (interactive use by a human)

If `$ARGUMENTS` is empty:

1. Ask the user once: "What do you want to build? One sentence."
2. Set `output_path = ./SPEC.md` (or `./.dirigent/SPEC.md` if that directory already exists).
3. Set `mode = "interactive"`.
4. Gather `repo_context` per Step 1 below.

## Reverse mode (extract a SPEC from an existing codebase)

If `user_description` matches a phrase like *"generate spec from this codebase"*,
*"reverse-engineer the spec"*, *"extract a spec from this repo"*, or any wording
where the goal is to **describe what already exists** instead of what to build
next, switch to **reverse mode**.

In reverse mode the SPEC documents current behavior. The template structure
(Goal / Requirements / Scope / Technical Notes) stays — but each
`**Rn** (category/priority): text` entry describes a behavior the system
*currently has*. Priority reflects centrality: `must` = core,
`should` = secondary, `may` = peripheral.

**Source priority — read in this order, stop when the template can be filled:**

1. `ARCHITECTURE.md`
2. `README.md`
3. ADRs if present: `docs/adr/`, `docs/decisions/`, `.architecture/decisions/`, `adr/`
4. `CLAUDE.md`, `.claude/CLAUDE.md`

**Fallback to grep** if the above are missing or thin (combined < 1500 bytes of
substantive content, or no concrete behaviors named):

- Entry points: `find . -name 'main.*' -o -name 'app.*' -o -name 'server.*'` ; `grep -l "if __name__" .`
- Routes: `grep -rn "@app\.\|@router\.\|app\.get\|app\.post\|router\.\(get\|post\|put\|delete\)" --include='*.py' --include='*.ts' --include='*.js' --include='*.tsx'`
- Data shapes: `grep -rn "class .*Model\|class .*Schema\|@dataclass\|^interface \|^type .* =" --include='*.py' --include='*.ts'`
- User-facing scripts: `package.json` `scripts`, `pyproject.toml` `[project.scripts]`, `Makefile` targets

`### Out of Scope` in reverse mode names what the codebase *deliberately does
not do*, based on absences you confirmed by searching (e.g. "No authentication
— no auth middleware found on any route"). If you cannot confirm an absence,
omit it rather than guess.

Reverse mode is always non-interactive — never ask clarifying questions, the
codebase is the source of truth.

**Self-contained output.** A reverse-engineered SPEC MUST be self-contained.
It describes *behavior*, not *implementation*. Concretely, in reverse mode:

- **No file paths anywhere in the SPEC.** Not in Requirements, not in
  Technical Notes, not as inline references like `(see src/auth/middleware.py)`.
- **No links to commits, PRs, or issue trackers.**
- **No "as implemented in X" phrasing.** Describe the behavior in domain terms
  so a different team could re-implement from scratch using only the SPEC.
- **Technical Notes** in reverse mode lists *behavioral constraints* the
  system honors (e.g. "All money values stored as integer cents, not floats"),
  not file references. If you have nothing of that kind, write `None`.

This constraint applies only in reverse mode. Forward-mode SPECs still
reference real files in Technical Notes per the normal rules.

## Steps

### Step 1 — Gather repo context (if not provided)

Read each of these files if it exists, capping each at 5000 bytes:

- `ARCHITECTURE.md`
- `README.md`
- `CLAUDE.md`
- `.claude/CLAUDE.md`

If `.brv/context-tree/` exists, also run `brv query "<user_description>"` and
include the result.

If reverse mode is active, follow the source priority and grep fallback in the
"Reverse mode" section above instead of this list.

### Step 2 — Decide whether to ask clarifying questions

Skip this step entirely if `mode == "non-interactive"`.

In `interactive` mode, ask **at most 3** questions, and only if at least one
trigger fires:

| Trigger                                                                                  | Question must resolve                  |
|------------------------------------------------------------------------------------------|----------------------------------------|
| Description is < 10 words AND the feature touches more than one of {data, ui, auth, api} | Which surface is in scope              |
| The repo offers two visibly-supported tech options for this feature                      | Which option to use                    |
| A field of the SPEC template (persistence layer, auth boundary, data shape) cannot be filled from description + repo_context | That specific field                    |

If no trigger fires, write the SPEC without asking.

Each question MUST:

- List ≤ 2 named options inline (not free text)
- Mark the default in `[brackets]` so the user can press Enter
- Be answerable in one word

Ask all questions in a **single** message. Do not chain.

Example good question:
> "Persist the toggle state in localStorage or in user_profile.theme? [localStorage]"

Example bad question (rejected):
> "How should the toggle work?"  ← open-ended, no options, no default

### Step 3 — Write the SPEC

Read `${CLAUDE_SKILL_DIR}/templates/SPEC.template.md`. Substitute every `{placeholder}`
with concrete content. Write the result to `output_path`. Overwrite if it exists.

When writing requirements:

- Each `**Rn** (category/priority): text` line is one verifiable claim.
- `category` MUST be one of: `data-model, api, ui, auth, integration, infra, policy, workflow, validation, other`.
- `priority` MUST be one of: `must, should, may`.
- IDs are sequential from R1, never reused, never renumbered. Split compound requirements.

When writing Technical Notes:

- Reference real file paths. If you reference `src/components/ThemeToggle.tsx`, that file (or its parent directory) must exist.
- If a needed input is missing, write `TBD: <what you'd need>` instead of inventing.

### Step 4 — Self-check before finishing

Verify the written SPEC against this checklist. If any item fails, fix and rewrite.

- [ ] `# ` heading exists and is not the literal string `{Feature Name}`
- [ ] Sections present in this order: `## Goal`, `## Requirements`, `## Scope`, `## Technical Notes`
- [ ] `## Scope` contains both `### In Scope` and `### Out of Scope` subsections
- [ ] At least one requirement matches the regex `^- \*\*R\d+\*\* \([a-z-]+/(must|should|may)\):`
- [ ] R-IDs are sequential from R1 with no gaps
- [ ] Every category appears in the allowed set; every priority appears in the allowed set
- [ ] `### Out of Scope` has at least one bullet (or the exact line `- None — full scope is in scope.`)
- [ ] No `{placeholder}` strings remain in the output

## Rules

<rule>If `$ARGUMENTS` is non-empty, treat it as a path to a config JSON file. Do not parse it as inline JSON, and do not interpret it as the user description.</rule>
<rule>The template at `${CLAUDE_SKILL_DIR}/templates/SPEC.template.md` is the source of truth for structure. Do not invent additional sections.</rule>
<rule>Non-interactive mode never asks questions. If a field cannot be filled, write `TBD: <what you'd need>` in Technical Notes — do not guess.</rule>
<rule>Reverse mode (extracting a SPEC from an existing codebase) is always non-interactive. The codebase is the source of truth — read ARCHITECTURE.md, README.md, ADRs, then grep as fallback. Each requirement describes a behavior the code currently has.</rule>
<rule>A reverse-engineered SPEC MUST be self-contained: no file paths, no commit/PR links, no "as implemented in X" phrasing. Describe behavior in domain terms so the SPEC could drive a clean re-implementation. This rule applies only in reverse mode.</rule>
<rule>Interactive mode asks at most 3 questions, and only if a trigger from Step 2 fires.</rule>
<rule>Every question has ≤ 2 named options listed inline and a default in `[brackets]`.</rule>
<rule>Requirement IDs are sequential from R1, never reused, never renumbered. Split compound requirements into separate Rn entries.</rule>
<rule>`### Out of Scope` is required. If genuinely none, write `- None — full scope is in scope.` Do not omit the section.</rule>
<rule>File paths in Technical Notes must resolve in the repo. If unsure, omit the path rather than invent it.</rule>
<rule>Do not write any file other than the SPEC at `output_path`.</rule>
<rule>Overwrite `output_path` if it exists. Do not back it up, do not prompt.</rule>
