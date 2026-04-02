---
name: commits-summary
description: "Create a summary of all git commits"
disable-model-invocation: true
---

## Context
- List of commits: !`git log main..HEAD --oneline`

## Instructions
Create a unified list of all git commit comments. Deduplicated changes, omit main->branch merges, output a  list (bulleted by default). If stated raw in arguments omit bullets.