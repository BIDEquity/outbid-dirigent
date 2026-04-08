---
name: query-brv
description: Retrieve or store domain knowledge via ByteRover (.brv/context-tree/)
arguments: question (required) - what to look up or curate
---

# ByteRover Knowledge

Interact with the project's domain knowledge stored in `.brv/context-tree/`.

## Retrieve Context

When you need domain knowledge — architecture patterns, business rules,
past decisions — query the knowledge store:

```bash
brv query "$QUESTION"
```

Examples:
- `brv query "How does authentication work?"`
- `brv query "What patterns does the billing module follow?"`

Use this BEFORE implementing when `<knowledge-store>` in your prompt
mentions a relevant domain, or when you need context not in your prompt.

## Save Patterns

After implementing something that establishes a new pattern or decision,
save it for future tasks:

```bash
brv curate "Description of the pattern or decision" -f path/to/relevant/file.ts
```

Only curate genuinely reusable patterns — architectural decisions, naming
conventions, integration patterns. Do NOT curate task-specific details.
Maximum 5 files per curate command.

## When to Use

**Query when:**
- Your task touches a domain mentioned in `<knowledge-store>`
- You need to understand existing patterns before writing code
- You're unsure how something is implemented in this project

**Curate when:**
- You established a new architectural pattern
- You made a design decision that future tasks should follow
- You discovered an important integration detail

**Skip when:**
- The info is already in your prompt context
- The question is general programming knowledge, not project-specific

## Troubleshooting

If `brv query` fails with "No provider connected", run:
```bash
brv providers connect byterover
```
Then retry. The ByteRover provider is free and needs no API key.

## Important

- `.brv/context-tree/` files are human-readable Markdown — you can also Read them directly
- Do NOT modify `.brv/` files manually — always use `brv curate`
