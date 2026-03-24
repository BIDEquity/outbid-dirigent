---
name: validate-manifest
description: Validate an outbid-test-manifest.yaml against the Pydantic schema, check that referenced commands/files actually exist, and report issues
arguments: path (optional) - path to manifest file, defaults to outbid-test-manifest.yaml in repo root
---

# Validate Test Manifest

Validate `outbid-test-manifest.yaml` for schema correctness AND real-world accuracy.

## Step 1: Locate the manifest

Use `$ARGUMENTS` if provided, otherwise look for `outbid-test-manifest.yaml` in the repo root.

If the file doesn't exist, stop and report that.

## Step 2: Schema validation

Run Pydantic validation against the canonical schema:

```bash
python3 -c "
import sys, yaml
from pathlib import Path

manifest_path = Path('${MANIFEST_PATH:-outbid-test-manifest.yaml}')
raw = yaml.safe_load(manifest_path.read_text())

# Import from installed package if available, otherwise inline validation
try:
    from outbid_dirigent.test_manifest import TestManifest
    manifest = TestManifest.model_validate(raw)
    print('Schema validation: PASS')
except ImportError:
    # Fallback: validate against JSON schema
    import json, urllib.request
    # Basic structure check
    errors = []
    if not isinstance(raw, dict):
        errors.append('Root must be a mapping')
    if 'levels' in raw and not isinstance(raw['levels'], dict):
        errors.append('levels must be a mapping')
    if 'components' in raw and not isinstance(raw['components'], (dict, list)):
        errors.append('components must be a mapping or list')
    if 'preview' in raw and not isinstance(raw['preview'], dict):
        errors.append('preview must be a mapping')
    if errors:
        for e in errors:
            print(f'Schema validation: FAIL - {e}')
        sys.exit(1)
    print('Schema validation: PASS (basic, no Pydantic available)')
except Exception as e:
    print(f'Schema validation: FAIL - {e}')
    sys.exit(1)
"
```

If schema validation fails, report every error and stop.

## Step 3: Reality checks

For each section, verify claims against the actual codebase:

### Prerequisites
For each tool in `prerequisites.tools`:
- Run the `check` command — does it actually work?
- If `setup_command` is set, does the binary/package it references exist?

```bash
# Example: validate each prerequisite check command
# For each tool, run: bash -c "<check>" and report pass/fail
```

### Components
For each component:
- If `runtime: docker-compose` — does a docker-compose/compose file exist with that service?
- If `start.command` references a file or script — does it exist?
- If `endpoint.port` is set — is it plausible for that service type?

### Test commands
For each command in `levels.l1.commands` and `levels.l2.commands`:
- Does the test directory/file referenced in the `run` command exist?
  - e.g. `pytest tests/unit` — does `tests/unit/` exist?
  - e.g. `ruff check .` — is ruff in prerequisites or pyproject.toml?
  - e.g. `npm test` — does package.json have a `test` script?
- Do `needs` reference component names that actually exist in `components`?

### Preview
- Does the framework match what's in the codebase? (e.g. `FastAPI` but no FastAPI in deps)
- Does `start_command` reference real scripts/modules?
- Do `setup_steps` commands reference real files/tools?
- If `uses_doppler: true` — does `.doppler.yaml` or `doppler.yaml` exist?
- If `health_check` is set — is that route defined in the code?

### Gaps
- Are there test capabilities that exist but are listed as gaps? (false negatives)
- Are there obvious gaps not listed? (e.g. no E2E tests but no gap entry for it)

## Step 4: Completeness check

Verify nothing important is missing:

- [ ] `test_level` is set
- [ ] At least `l1` level exists with at least one command
- [ ] `preview.start_command` is not empty
- [ ] `preview.port` is set
- [ ] `preview.framework` is set
- [ ] If docker-compose exists in repo, components section is populated
- [ ] If Doppler config exists in repo, `uses_doppler` is true

## Output

Report as a checklist:

```
Manifest: outbid-test-manifest.yaml

Schema validation:     PASS/FAIL
Prerequisites:         X/Y tools verified
Components:            X real, Y mocked — all references valid / N issues
Test commands (L1):    X commands — all paths exist / N issues
Test commands (L2):    X commands — all paths exist / N issues
Preview:               framework=X, port=Y, start_command verified / N issues
Gaps:                  X documented, Y suggested additions
Completeness:          X/7 checks passed

Issues:
  - [FAIL] l1.commands[0].run: "pytest tests/unit" — tests/unit/ does not exist
  - [WARN] Gap missing: no type-check command but pyright is configured
  - ...
```

If everything passes, confirm the manifest is ready for the Dirigent.
