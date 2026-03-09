#!/bin/bash
#
# Outbid Dirigent – Standalone Installation für Coder
#
# Dieses Script klont von einem PRIVATEN GitHub Repo.
# Coder's Git Auth wird automatisch verwendet.
#
# In Coder Template verwenden:
#
#   resource "coder_script" "dirigent" {
#     agent_id     = coder_agent.main.id
#     script       = file("${path.module}/standalone-install.sh")
#     display_name = "Install Dirigent"
#     run_on_start = true
#   }
#

set -e

# ============================================
# KONFIGURATION - Hier anpassen!
# ============================================
GITHUB_ORG="BIDEquity"
REPO_NAME="outbid-dirigent"
# ============================================

REPO_URL="https://github.com/${GITHUB_ORG}/${REPO_NAME}.git"
INSTALL_DIR="$HOME/.local/share/outbid-dirigent"
BIN_DIR="$HOME/.local/bin"

# Skip wenn bereits installiert und aktuell
if [ -x "$BIN_DIR/dirigent" ] && [ -d "$INSTALL_DIR/.git" ]; then
    echo "✅ Dirigent bereits installiert, prüfe Updates..."
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || true
    exit 0
fi

echo "🎼 Installiere Outbid Dirigent..."

# Verzeichnisse erstellen
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Git Clone (nutzt Coder's Git Auth automatisch)
if [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR"
    git pull --ff-only
else
    # Coder setzt GIT_ASKPASS für Auth
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

# Python Dependencies
pip3 install --user -q anthropic 2>/dev/null || pip install --user -q anthropic 2>/dev/null || true

# Symlink erstellen
chmod +x "$INSTALL_DIR/dirigent.py"
ln -sf "$INSTALL_DIR/dirigent.py" "$BIN_DIR/dirigent"

# PATH sicherstellen für Bash
if [ -f "$HOME/.bashrc" ] && ! grep -q '.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

# PATH sicherstellen für Zsh
if [ -f "$HOME/.zshrc" ] && ! grep -q '.local/bin' "$HOME/.zshrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
fi

echo "✅ Outbid Dirigent installiert!"
echo "   Nutze: dirigent --help"
