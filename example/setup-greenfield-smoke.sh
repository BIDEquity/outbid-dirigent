#!/usr/bin/env bash
# Set up the greenfield smoke test repo and run dirigent from scratch.
#
# This tests the FULL greenfield route:
#   Scaffold → Plan → Execute → Entropy Min → Test → Ship
#
# Usage:
#   ./setup-greenfield-smoke.sh              # setup + run
#   ./setup-greenfield-smoke.sh --setup-only # setup only, run manually
#   ./setup-greenfield-smoke.sh --resume     # resume an existing run
#
# After execution, observe:
#   - ARCHITECTURE.md: has <key-patterns> with opinionated defaults?
#   - start.sh: exists, executable, binds 0.0.0.0?
#   - test-harness.json: has test + dev commands?
#   - PLAN.json: max 2 phases, max 7 tasks?
#   - Commits: one per task?
#   - App: does ./start.sh actually work?
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${GREENFIELD_TARGET:-/tmp/greenfield-smoke-test}"
MODEL="${GREENFIELD_MODEL:-sonnet}"
EFFORT="${GREENFIELD_EFFORT:-medium}"

# ── Parse flags ──
SETUP_ONLY=false
RESUME=false
for arg in "$@"; do
    case "$arg" in
        --setup-only) SETUP_ONLY=true ;;
        --resume) RESUME=true ;;
    esac
done

# ── Setup ──
if [ "$RESUME" = false ]; then
    if [ -d "$TARGET" ]; then
        echo "Removing existing $TARGET"
        rm -rf "$TARGET"
    fi

    echo "Copying greenfield-streamlit to $TARGET"
    cp -r "$SCRIPT_DIR/greenfield-streamlit" "$TARGET"

    # Generate run ID from spec content
    SPEC_HASH=$(shasum -a 256 "$TARGET/.dirigent/SPEC.md" | cut -c1-8)
    RUN_ID="greenfield-smoke-${SPEC_HASH}"
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

    # Gitignore
    cat > "$TARGET/.gitignore" <<'GITIGNORE'
.dirigent/
__pycache__/
*.pyc
.venv/
*.db
.env
GITIGNORE

    # Init git
    cd "$TARGET"
    git init
    git config user.email "smoke@test.com"
    git config user.name "Smoke Test"
    git add .
    git commit -m "initial: greenfield smoke test repo"

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  Greenfield smoke test repo ready"
    echo "═══════════════════════════════════════════════════════"
    echo "  Repo:    $TARGET"
    echo "  Run dir: $RUN_DIR"
    echo "  Spec:    $RUN_DIR/SPEC.md"
    echo "  Model:   $MODEL"
    echo "  Effort:  $EFFORT"
    echo "═══════════════════════════════════════════════════════"
else
    # Resume: find existing run dir
    cd "$TARGET"
    RUN_DIR=$(python3 -c "import json; print(json.load(open('.dirigent/manifest.json'))['run_dir'])")
    echo "Resuming from $RUN_DIR"
fi

if [ "$SETUP_ONLY" = true ]; then
    echo ""
    echo "Setup only. To run:"
    echo "  cd $TARGET"
    echo "  dirigent --repo . --spec $RUN_DIR/SPEC.md --force --model $MODEL --effort $EFFORT"
    exit 0
fi

# ── Run ──
echo ""
echo "Starting dirigent (greenfield route)..."
echo ""

cd "$TARGET"

if [ "$RESUME" = true ]; then
    dirigent --repo . --spec "$RUN_DIR/SPEC.md" --resume --model "$MODEL" --effort "$EFFORT"
else
    dirigent --repo . --spec "$RUN_DIR/SPEC.md" --force --model "$MODEL" --effort "$EFFORT"
fi

# ── Observe ──
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Execution complete. Observe:"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "── ARCHITECTURE.md ──"
if [ -f "$TARGET/ARCHITECTURE.md" ]; then
    echo "  EXISTS"
    grep -q "<key-patterns>" "$TARGET/ARCHITECTURE.md" && echo "  <key-patterns>: YES" || echo "  <key-patterns>: MISSING"
    grep -q "<testing-verification>" "$TARGET/ARCHITECTURE.md" && echo "  <testing-verification>: YES" || echo "  <testing-verification>: MISSING"
    grep -q "<architecture-decisions>" "$TARGET/ARCHITECTURE.md" && echo "  <architecture-decisions>: YES" || echo "  <architecture-decisions>: MISSING"
    grep -q "uv" "$TARGET/ARCHITECTURE.md" && echo "  mentions uv: YES" || echo "  mentions uv: NO"
    grep -q "polars" "$TARGET/ARCHITECTURE.md" && echo "  mentions polars: YES" || echo "  mentions polars: NO"
else
    echo "  MISSING — scaffold failed"
fi

echo ""
echo "── start.sh ──"
if [ -f "$TARGET/start.sh" ]; then
    echo "  EXISTS"
    [ -x "$TARGET/start.sh" ] && echo "  executable: YES" || echo "  executable: NO"
    grep -q "0.0.0.0" "$TARGET/start.sh" && echo "  binds 0.0.0.0: YES" || echo "  binds 0.0.0.0: NO"
else
    echo "  MISSING — scaffold failed"
fi

echo ""
echo "── test-harness.json ──"
if [ -f "$RUN_DIR/test-harness.json" ]; then
    echo "  EXISTS"
    python3 -c "import json; h=json.load(open('$RUN_DIR/test-harness.json')); print(f'  commands: {list(h.get(\"commands\",{}).keys())}'); print(f'  port: {h.get(\"portal\",{}).get(\"port\",\"?\")}')"
else
    echo "  MISSING — scaffold failed"
fi

echo ""
echo "── PLAN.json ──"
if [ -f "$RUN_DIR/PLAN.json" ]; then
    python3 -c "
import json
p = json.load(open('$RUN_DIR/PLAN.json'))
phases = len(p.get('phases', []))
tasks = sum(len(ph.get('tasks', [])) for ph in p.get('phases', []))
print(f'  phases: {phases} (max 2)')
print(f'  tasks:  {tasks} (max 7)')
if phases > 2: print('  WARNING: exceeds 2 phase limit')
if tasks > 7: print('  WARNING: exceeds 7 task limit')
"
else
    echo "  MISSING — planning failed"
fi

echo ""
echo "── Git log ──"
git log --oneline | head -10

echo ""
echo "── To test the app manually ──"
echo "  cd $TARGET && ./start.sh"
echo "  # Then open http://localhost:8501 and upload data/sample.csv"
