---
name: validate-manifest
description: Validate outbid-test-manifest.yaml against schema and verify all references exist in the codebase
argument-hint: [path/to/manifest.yaml]
allowed-tools: Bash, Read, Glob, Grep
---

Run the `validate-manifest` skill from the dirigent plugin. Validate the manifest at $ARGUMENTS (or `outbid-test-manifest.yaml` in repo root) for schema correctness and real-world accuracy.
