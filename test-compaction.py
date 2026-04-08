#!/usr/bin/env python3
"""
Manual test harness for the spec compactor.

Usage:
    echo "eine quiz-app" | python test-compaction.py > spec.compact.xml
    python test-compaction.py path/to/SPEC.md > spec.compact.xml
    python test-compaction.py path/to/SPEC.md --json > spec.compact.json
    python test-compaction.py path/to/SPEC.md --only R1,R3,R7  # filtered render

Environment:
    ANTHROPIC_API_KEY must be set.
    MODEL env var overrides the default model (claude-haiku-4-5).
"""

import argparse
import os
import sys
from pathlib import Path

from outbid_dirigent.logger import init_logger
from outbid_dirigent.spec_compactor import compact_spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact a markdown spec via LLM.")
    parser.add_argument(
        "spec",
        nargs="?",
        help="Path to spec file. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit raw JSON (Pydantic dump) instead of rendered XML.",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Comma-separated req IDs to render (e.g. R1,R3,R7). Default: all.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("MODEL", "claude-haiku-4-5"),
        help="Model to use (default: claude-haiku-4-5 or $MODEL).",
    )
    args = parser.parse_args()

    # Logger must be initialized before any module that calls get_logger()
    init_logger(repo_path=str(Path.cwd()), verbose=False)

    # Read spec content
    if args.spec:
        spec_content = Path(args.spec).read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            print("ERROR: no spec given and stdin is a TTY", file=sys.stderr)
            return 2
        spec_content = sys.stdin.read()

    if not spec_content.strip():
        print("ERROR: empty spec", file=sys.stderr)
        return 2

    # Compact (no dirigent_dir → don't write a file, just return the model)
    print(
        f"# Compacting {len(spec_content)} chars with {args.model}...",
        file=sys.stderr,
    )
    compact = compact_spec(spec_content, model=args.model, dirigent_dir=None)
    if compact is None:
        print("ERROR: compaction returned None (see logs)", file=sys.stderr)
        return 1

    print(
        f"# {len(compact.requirements)} reqs, "
        f"{len(compact.glossary)} glossary, "
        f"{len(compact.entities)} entities, "
        f"{len(compact.flows)} flows",
        file=sys.stderr,
    )

    # Emit
    if args.json:
        sys.stdout.write(compact.model_dump_json(indent=2))
        sys.stdout.write("\n")
    else:
        only = None
        if args.only:
            only = {s.strip() for s in args.only.split(",") if s.strip()}
        sys.stdout.write(compact.render_xml(only_req_ids=only))
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
