#!/bin/bash
#
# Outbid Dirigent – Installation Script
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎼 Outbid Dirigent Installation"
echo "================================"
echo ""

# Python-Version prüfen
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nicht gefunden. Bitte installieren."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION gefunden"

# pip prüfen
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 nicht gefunden. Bitte installieren."
    exit 1
fi

# Dependencies installieren
echo ""
echo "📦 Installiere Abhängigkeiten..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# Claude CLI prüfen
echo ""
if command -v claude &> /dev/null; then
    echo "✅ Claude CLI gefunden"
else
    echo "⚠️  Claude CLI nicht gefunden."
    echo "   Installiere mit: npm install -g @anthropic-ai/claude-code"
fi

# gh CLI prüfen (optional)
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI (gh) gefunden"
else
    echo "ℹ️  GitHub CLI (gh) nicht gefunden (optional für PR-Erstellung)"
fi

# ANTHROPIC_API_KEY prüfen
echo ""
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ ANTHROPIC_API_KEY gesetzt"
else
    echo "⚠️  ANTHROPIC_API_KEY nicht gesetzt."
    echo "   Export mit: export ANTHROPIC_API_KEY=your-key-here"
fi

# Ausführbar machen
chmod +x "$SCRIPT_DIR/dirigent.py"

echo ""
echo "================================"
echo "✅ Outbid Dirigent installiert!"
echo ""
echo "Usage:"
echo "  python3 $SCRIPT_DIR/dirigent.py --spec SPEC.md --repo /path/to/repo"
echo ""
echo "Oder füge zum PATH hinzu:"
echo "  export PATH=\"\$PATH:$SCRIPT_DIR\""
echo ""
