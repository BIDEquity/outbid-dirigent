#!/usr/bin/env bash
# Copy the sample repo to a target directory and initialize git.
# Usage: ./setup-smoke-test.sh [target-dir]
# Default: /tmp/dirigent-smoke-test
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-/tmp/dirigent-smoke-test}"

if [ -d "$TARGET" ]; then
    echo "Removing existing $TARGET"
    rm -rf "$TARGET"
fi

echo "Copying sample repo to $TARGET"
cp -r "$SCRIPT_DIR/sample-repo" "$TARGET"

cd "$TARGET"

# Init git so dirigent can operate
git init
git config user.email "smoke@test.com"
git config user.name "Smoke Test"
git add .
git commit -m "initial: sample project with .dirigent artifacts"

echo ""
echo "Smoke test repo ready at: $TARGET"
echo ""
echo "Run dirigent from execution phase:"
echo "  cd $TARGET"
echo "  dirigent --repo . --spec .dirigent/SPEC.md --resume --model haiku --effort low"
echo ""
echo "Or run from scratch (re-analyze + re-plan):"
echo "  cd $TARGET"
echo "  dirigent --repo . --spec .dirigent/SPEC.md --force --model haiku --effort low"
