# Outbid Dirigent – Coder Template Module
#
# Usage in deinem Coder Template:
#
#   module "dirigent" {
#     source   = "github.com/BIDEquity/outbid-dirigent//coder"
#     agent_id = coder_agent.main.id
#   }
#
# Oder bei privatem Repo den Code direkt kopieren.

variable "agent_id" {
  type        = string
  description = "The coder_agent ID to attach the script to"
}

resource "coder_script" "install_dirigent" {
  agent_id     = var.agent_id
  display_name = "Outbid Dirigent"
  icon         = "/icon/python.svg"
  run_on_start = true

  script = <<-'SCRIPT'
#!/bin/bash
set -e

INSTALL_DIR="$HOME/.local/share/outbid-dirigent"
BIN_DIR="$HOME/.local/bin"

# Skip wenn bereits installiert
if [ -x "$BIN_DIR/dirigent" ]; then
  echo "✅ Dirigent bereits installiert"
  exit 0
fi

echo "🎼 Installiere Outbid Dirigent..."

mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# Python Dependencies
pip3 install --user -q anthropic 2>/dev/null || pip install --user -q anthropic

# Dirigent Code wird inline erstellt (kein Git Clone nötig)
cat > "$INSTALL_DIR/dirigent.py" << 'DIRIGENT_PY'
${file("${path.module}/../dirigent.py")}
DIRIGENT_PY

cat > "$INSTALL_DIR/logger.py" << 'LOGGER_PY'
${file("${path.module}/../logger.py")}
LOGGER_PY

cat > "$INSTALL_DIR/analyzer.py" << 'ANALYZER_PY'
${file("${path.module}/../analyzer.py")}
ANALYZER_PY

cat > "$INSTALL_DIR/router.py" << 'ROUTER_PY'
${file("${path.module}/../router.py")}
ROUTER_PY

cat > "$INSTALL_DIR/oracle.py" << 'ORACLE_PY'
${file("${path.module}/../oracle.py")}
ORACLE_PY

cat > "$INSTALL_DIR/executor.py" << 'EXECUTOR_PY'
${file("${path.module}/../executor.py")}
EXECUTOR_PY

chmod +x "$INSTALL_DIR/dirigent.py"
ln -sf "$INSTALL_DIR/dirigent.py" "$BIN_DIR/dirigent"

# PATH sicherstellen
if ! grep -q '.local/bin' "$HOME/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

echo "✅ Dirigent installiert"
SCRIPT
}

output "install_path" {
  value = "$HOME/.local/bin/dirigent"
}
