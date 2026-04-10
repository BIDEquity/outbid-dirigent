# Reading List

Curated external reads for deeper context on vibecoding, Dirigent, and the Outbid way of building with agents. Link-out only — no scraping, no fetching. Open in a browser.

This list is intentionally short. The canon in `canon/` is the primary source. These links are *optional depth*, surfaced by the coach at the end of the relevant canon file ("For more, see: …").

## Vibecoding — philosophy

<!--
Add Notion URLs here as they become canonical. Format:
- **Title** — one-line hook. `surface after:` <canon file>
  <URL>
-->

- **(TBD — your canonical "What is vibecoding" page)** — The core idea in one read.
  `surface after:` `when-not-to-use-dirigent.md`, `spec-first-or-suffer.md`
  `<add Notion URL>`

- **(TBD — your "vibecoding anti-patterns" page)** — What it looks like when it's going wrong.
  `surface after:` `no-sycophancy-rule.md`, `scope-is-sacred.md`
  `<add Notion URL>`

## Dirigent — architecture and rationale

- **Dirigent ARCHITECTURE.md** (in-repo) — The full system diagram.
  `surface after:` any lane that ends with "want to go deeper?"
  Path: `ARCHITECTURE.md` (repo root)

- **Dirigent OUTBID_CONTEXT.md** (in-repo) — Why this tool exists at Outbid.
  Path: `OUTBID_CONTEXT.md` (repo root)

- **Dirigent README** (in-repo) — CLI reference.
  Path: `README.md` (repo root)

## Agent skills and patterns

- **(TBD — Notion page on writing good skills)** — How to codify house style.
  `surface after:` `domain-context-beats-orchestration.md`
  `<add Notion URL>`

- **Anthropic — Claude Code plugins and skills docs** — Official plugin/skill authoring reference.
  `surface after:` `domain-context-beats-orchestration.md` (for users new to skill authoring)
  `<add Anthropic docs URL>`

## How to add to this list

1. Keep it curated — max 10 links total. If you're adding an 11th, drop a weaker one.
2. Each entry needs: title, one-line hook, `surface after:` trigger (which canon file this supplements), the URL.
3. Public URLs only. Workspace-internal Notion pages won't open for other plugin users.
4. Link rot is real — re-check annually. If a link is dead, delete the entry.

## The coach's job

When a user finishes reading a canon file, the coach checks this list for any entry whose `surface after:` matches that file, and offers it as optional depth:

> "Want to go deeper? Here's the Outbid take on this: [title] ([link])."

Never more than one link per surfaced canon file. If there are two matches, pick the more recent one.
