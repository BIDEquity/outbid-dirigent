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
${file("${path.module}/../src/outbid_dirigent/dirigent.py")}
DIRIGENT_PY

cat > "$INSTALL_DIR/logger.py" << 'LOGGER_PY'
${file("${path.module}/../src/outbid_dirigent/logger.py")}
LOGGER_PY

cat > "$INSTALL_DIR/analyzer.py" << 'ANALYZER_PY'
${file("${path.module}/../src/outbid_dirigent/analyzer.py")}
ANALYZER_PY

cat > "$INSTALL_DIR/router.py" << 'ROUTER_PY'
${file("${path.module}/../src/outbid_dirigent/router.py")}
ROUTER_PY

cat > "$INSTALL_DIR/oracle.py" << 'ORACLE_PY'
${file("${path.module}/../src/outbid_dirigent/oracle.py")}
ORACLE_PY

cat > "$INSTALL_DIR/executor.py" << 'EXECUTOR_PY'
${file("${path.module}/../src/outbid_dirigent/executor.py")}
EXECUTOR_PY

cat > "$INSTALL_DIR/questioner.py" << 'QUESTIONER_PY'
${file("${path.module}/../src/outbid_dirigent/questioner.py")}
QUESTIONER_PY

cat > "$INSTALL_DIR/proteus_integration.py" << 'PROTEUS_PY'
${file("${path.module}/../src/outbid_dirigent/proteus_integration.py")}
PROTEUS_PY

cat > "$INSTALL_DIR/__init__.py" << 'INIT_PY'
# Outbid Dirigent Package
INIT_PY

# Wrapper-Script mit Portal-Integration
cat > "$BIN_DIR/dirigent-run" << 'WRAPPER'
#!/bin/bash
# Dirigent Runner mit Portal-Integration
# Nutzt env vars: EXECUTION_ID, REPORTER_TOKEN, PORTAL_URL, INTERACTIVE

SPEC_PATH="${1:-.planning/SPEC.md}"
REPO_PATH="${2:-.}"

ARGS="--spec $SPEC_PATH --repo $REPO_PATH --output json"

if [ -n "$INTERACTIVE" ] && [ "$INTERACTIVE" = "true" ]; then
  ARGS="$ARGS --interactive"
fi

if [ -n "$PORTAL_URL" ]; then
  ARGS="$ARGS --portal-url $PORTAL_URL"
fi

if [ -n "$EXECUTION_ID" ]; then
  ARGS="$ARGS --execution-id $EXECUTION_ID"
fi

if [ -n "$REPORTER_TOKEN" ]; then
  ARGS="$ARGS --reporter-token $REPORTER_TOKEN"
fi

if [ -n "$QUESTION_TIMEOUT" ]; then
  ARGS="$ARGS --question-timeout $QUESTION_TIMEOUT"
fi

exec python3 "$HOME/.local/share/outbid-dirigent/dirigent.py" $ARGS
WRAPPER
chmod +x "$BIN_DIR/dirigent-run"

chmod +x "$INSTALL_DIR/dirigent.py"
ln -sf "$INSTALL_DIR/dirigent.py" "$BIN_DIR/dirigent"

# PATH sicherstellen (für alle Shells)
for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
  if ! grep -q '^export PATH=.*\.local/bin' "$rc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
  fi
done

echo "✅ Dirigent installiert"
SCRIPT
}

output "install_path" {
  value = "$HOME/.local/bin/dirigent"
}
