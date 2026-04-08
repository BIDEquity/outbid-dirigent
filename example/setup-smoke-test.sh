#!/usr/bin/env bash
# Copy the sample repo to a target directory and initialize git.
# Artifacts go to $HOME/.dirigent/runs/<run-id>/ (matches new RunDir architecture).
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
mkdir -p "$TARGET/tests"

# Generate a deterministic run ID from the spec content
SPEC_HASH=$(shasum -a 256 "$TARGET/.dirigent/SPEC.md" | cut -c1-8)
RUN_ID="smoke-test-${SPEC_HASH}"
RUN_DIR="$HOME/.dirigent/runs/$RUN_ID"

# Move .dirigent/ artifacts to home-dir run location
rm -rf "$RUN_DIR"
mkdir -p "$RUN_DIR"
for subdir in summaries reviews contracts logs hooks; do
    mkdir -p "$RUN_DIR/$subdir"
done

# Move all artifact files to run dir
for f in "$TARGET/.dirigent/"*; do
    [ -f "$f" ] && cp "$f" "$RUN_DIR/"
done
# Copy contract subdirs if they have content
for subdir in contracts reviews; do
    if [ -d "$TARGET/.dirigent/$subdir" ]; then
        cp -r "$TARGET/.dirigent/$subdir/"* "$RUN_DIR/$subdir/" 2>/dev/null || true
    fi
done

# Replace repo .dirigent/ with just manifest.json
rm -rf "$TARGET/.dirigent"
mkdir -p "$TARGET/.dirigent"
cat > "$TARGET/.dirigent/manifest.json" <<MANIFEST
{
  "run_id": "$RUN_ID",
  "run_dir": "$RUN_DIR",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit_sha": "initial",
  "repo_path": "$TARGET",
  "files": {}
}
MANIFEST

# Ensure .dirigent/ is gitignored
if [ ! -f "$TARGET/.gitignore" ] || ! grep -q '.dirigent/' "$TARGET/.gitignore"; then
    echo -e "\n# Dirigent run manifest\n.dirigent/" >> "$TARGET/.gitignore"
fi

cd "$TARGET"

# Init git so dirigent can operate
git init
git config user.email "smoke@test.com"
git config user.name "Smoke Test"
git add .
git commit -m "initial: sample project"

echo ""
echo "Smoke test repo ready at: $TARGET"
echo "Run dir at: $RUN_DIR"
echo ""
echo "Run dirigent from execution phase:"
echo "  cd $TARGET"
echo "  dirigent --repo . --spec $RUN_DIR/SPEC.md --resume --model haiku --effort low"
echo ""
echo "Or run from scratch (re-analyze + re-plan):"
echo "  cd $TARGET"
echo "  dirigent --repo . --spec $RUN_DIR/SPEC.md --force --model haiku --effort low"
