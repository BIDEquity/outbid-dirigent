# Astro Starlight

**Role:** Docs/Static — documentation sites, landing pages, content-driven sites
**Tier:** 1 (default for docs and static sites)
**When:** SPEC is "build a docs site", "landing page", or content-heavy static site

## Docs

Before using unfamiliar Astro or Starlight APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="astro"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
node --version   # >= 18
npm --version
```

## Scaffold

```bash
npm create astro@latest . -- --template starlight --no-git --yes
npm install
```

Flags: `--yes` makes it fully non-interactive. `--no-git` avoids nested `.git`.

Content goes in `src/content/docs/` as Markdown files:

```markdown
---
title: Getting Started
description: How to use this app
---

# Getting Started

Your content here.
```

Sidebar is auto-generated from file structure.

## Run

```bash
npm run dev -- --host 0.0.0.0 --port 4321
```

Port: **4321** (default)

## Test

Static sites are tested via build verification:

```bash
# Build succeeds (catches broken links, invalid frontmatter, type errors)
npm run build

# Check output exists
ls dist/index.html
```

For content validation:

```bash
# All markdown files have required frontmatter
grep -rL "^title:" src/content/docs/ && echo "MISSING TITLES" || echo "All docs have titles"
```

## Build & Verify

```bash
npm run build        # produces dist/
npx serve dist       # verify production build locally
```

## Start Script Pattern

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
npm install
exec npm run dev -- --host 0.0.0.0 --port 4321
```

## Pairing

- Typically standalone. For docs with live API examples, pair with the backend stack being documented.
