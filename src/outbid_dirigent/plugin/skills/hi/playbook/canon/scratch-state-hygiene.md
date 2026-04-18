# Scratch state hygiene

**Track:** Agent rule (enforced in `implement-task` skill, in `implementer` agent — including its Review-Fix Mode — and via `.gitignore` convention)

**Thesis:** The *workspace* is not the *deliverable*. Dirigent produces a lot of scratch state — plans, contracts, reviews, summaries, debug dumps. None of it belongs in the PR. Keep it separate, gitignore it, and never let it leak.

## The incident

Debug directories like `.dirigent/.planning/` started showing up in PRs. They contain plan drafts, intermediate contracts, scratch notes — useful while running, noise forever. Every PR that carries them:

- Pollutes the diff, making review harder.
- Leaks implementation details that don't belong in the repo history.
- Creates the illusion that the planning state is *authoritative* when it's just a cache.

The right outcome: dirigent's scratch dirs live in the filesystem during a run, get summarized into commit messages, and vanish from the tree when the PR goes out. If they need to persist for debugging, they persist *outside* the git-tracked tree entirely (e.g., `~/.claude/logs/` or similar).

## The rule

- **Never commit** `.dirigent/`, `.dirigent-onboarding/`, `.planning/`, `.scratch/`, `.brv/` caches, or any dirigent-internal directory.
- **Always gitignore** these directories as the first step of any dirigent-adjacent work.
- **Separate workspace from deliverable** at the directory level. The workspace is where the agent thinks. The deliverable is what the human merges. They should not overlap.
- **If a scratch file needs to survive**, lift its useful content into a proper artifact (commit message, SPEC update, ARCHITECTURE.md note) and then delete the scratch.

## How to apply

- On any new dirigent run, confirm the repo's `.gitignore` covers all scratch dirs before writing a single file.
- If you find yourself writing into a dirigent scratch dir that *isn't* gitignored, stop and add the entry first.
- If you discover a PR contains scratch state, that's a bug — remove it, fix the gitignore, write it up as a hygiene incident.
- When authoring new skills or tools: choose paths that are *already* gitignored, or add the entry proactively.

## Enforced in

- Repo `.gitignore` — must cover all dirigent scratch directories.
- `skills/implement-task/SKILL.md` — scope discipline implicitly covers this, but canon promotes it to explicit hygiene rule.
- This playbook itself uses `.dirigent-onboarding/` (not `.dirigent/`) precisely so the onboarding flow models the pattern it preaches.
