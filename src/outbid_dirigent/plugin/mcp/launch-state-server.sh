#!/usr/bin/env bash
# Launcher for the dirigent-state MCP server.
#
# Claude Code spawns plugin MCP servers with a minimal PATH that often lacks
# common user-level install locations (`~/.local/bin`, `~/.cargo/bin`, Homebrew).
# This wrapper extends PATH to find `uv` wherever it was installed, then execs
# the self-contained uv-script MCP server.
#
# Portable: works for anyone who installed uv via the official installer, via
# Homebrew, via Cargo, or via pipx. Fails loud with a clear message if uv is
# genuinely absent.

set -euo pipefail

# Extend PATH with every place uv is commonly found.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:${PATH:-/usr/bin:/bin}"

# Resolve the script directory from CLAUDE_PLUGIN_ROOT if set, otherwise from
# our own location (fallback for manual invocation during development).
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  SERVER_SCRIPT="${CLAUDE_PLUGIN_ROOT}/mcp/dirigent_state_server.py"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SERVER_SCRIPT="${SCRIPT_DIR}/dirigent_state_server.py"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "dirigent-state MCP: 'uv' not found on PATH." >&2
  echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  echo "Searched: $PATH" >&2
  exit 127
fi

if [ ! -f "$SERVER_SCRIPT" ]; then
  echo "dirigent-state MCP: server script not found at $SERVER_SCRIPT" >&2
  exit 2
fi

exec uv run --script "$SERVER_SCRIPT"
