#!/usr/bin/env sh
#
# outbid-dirigent installer
#
# Usage:
#   curl -LsSf https://raw.githubusercontent.com/BIDEquity/outbid-dirigent/main/install.sh | sh
#   curl -LsSf https://raw.githubusercontent.com/BIDEquity/outbid-dirigent/main/install.sh | sh -s -- v2.0.0rc4
#   curl -LsSf https://raw.githubusercontent.com/BIDEquity/outbid-dirigent/main/install.sh | sh -s -- --uninstall
#
# Env vars:
#   DIRIGENT_VERSION      git ref (tag, branch, or SHA). Default: main. Overridden by positional arg.
#   DIRIGENT_INSTALL_UV   1 to auto-install uv if missing. Default: 0 (refuse, print astral command).
#   DIRIGENT_NO_PLUGIN    1 to skip Claude Code plugin registration. Default: 0.

set -eu

REPO_PY="git+https://github.com/BIDEquity/outbid-dirigent.git"
REPO_GH="BIDEquity/outbid-dirigent"
MARKET_NAME="outbid-dirigent"
PLUGIN_ID="dirigent@${MARKET_NAME}"

# -------- arg parsing --------
ACTION="install"
VERSION_ARG=""
for a in "$@"; do
  case "$a" in
    --uninstall|-U) ACTION="uninstall" ;;
    --help|-h)
      sed -n '2,14p' "$0" 2>/dev/null || grep '^#' "$0" | head -14
      exit 0 ;;
    -*) printf 'unknown flag: %s\n' "$a" >&2; exit 2 ;;
    *)  VERSION_ARG="$a" ;;
  esac
done
VERSION="${VERSION_ARG:-${DIRIGENT_VERSION:-main}}"

# -------- helpers --------
c_green=$(printf '\033[32m'); c_yellow=$(printf '\033[33m'); c_red=$(printf '\033[31m'); c_dim=$(printf '\033[2m'); c_reset=$(printf '\033[0m')
step()  { printf '%s→%s %s\n'   "$c_dim"    "$c_reset" "$1"; }
ok()    { printf '%s✓%s %s\n'   "$c_green"  "$c_reset" "$1"; }
warn()  { printf '%s!%s %s\n'   "$c_yellow" "$c_reset" "$1" >&2; }
die()   { printf '%s✗%s %s\n'   "$c_red"    "$c_reset" "$1" >&2; exit 1; }

# -------- uninstall path --------
if [ "$ACTION" = "uninstall" ]; then
  step "removing Claude Code plugin"
  command -v claude >/dev/null 2>&1 && {
    claude plugin uninstall "$PLUGIN_ID" --scope user 2>/dev/null || true
    claude plugin marketplace remove "$MARKET_NAME" --scope user 2>/dev/null || true
  }
  step "removing dirigent CLI"
  command -v uv >/dev/null 2>&1 && uv tool uninstall outbid-dirigent 2>/dev/null || true
  ok "uninstalled"
  exit 0
fi

# -------- preflight: uv --------
if ! command -v uv >/dev/null 2>&1; then
  if [ "${DIRIGENT_INSTALL_UV:-0}" = "1" ]; then
    step "uv not found — installing via astral"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # shellcheck disable=SC1091
    . "${XDG_DATA_HOME:-$HOME/.local}/share/uv/env" 2>/dev/null \
      || . "$HOME/.local/bin/env" 2>/dev/null \
      || export PATH="$HOME/.local/bin:$PATH"
    command -v uv >/dev/null 2>&1 || die "uv install succeeded but not on PATH — re-open shell and retry"
  else
    warn "uv not found"
    printf '  install uv first:  curl -LsSf https://astral.sh/uv/install.sh | sh\n'
    printf '  or re-run with:    DIRIGENT_INSTALL_UV=1 %s\n' "$(basename "$0") $*"
    exit 1
  fi
fi

# -------- install the Python CLI (bundles the plugin) --------
step "installing dirigent CLI at ${VERSION}"
uv tool install --force "${REPO_PY}@${VERSION}"
ok "dirigent CLI installed"

# -------- register the Claude Code plugin --------
if [ "${DIRIGENT_NO_PLUGIN:-0}" = "1" ]; then
  warn "DIRIGENT_NO_PLUGIN=1 — skipping Claude Code plugin registration"
elif ! command -v claude >/dev/null 2>&1; then
  warn "Claude Code CLI not found — skipping plugin registration (headless CLI still works)"
else
  step "registering Claude Code plugin (scope: user)"

  # Nuke-and-pave: remove prior marketplace/plugin, ignore errors if fresh.
  claude plugin uninstall           "$PLUGIN_ID"   --scope user 2>/dev/null || true
  claude plugin marketplace remove  "$MARKET_NAME" --scope user 2>/dev/null || true
  claude plugin marketplace add     "$REPO_GH"     --scope user

  # Pin the ref in settings.json if caller asked for anything other than main.
  if [ "$VERSION" != "main" ]; then
    step "pinning marketplace ref → ${VERSION}"
    python3 - "$VERSION" <<'PY'
import json, pathlib, sys
ref = sys.argv[1]
p = pathlib.Path.home() / ".claude" / "settings.json"
d = json.loads(p.read_text()) if p.exists() else {}
mkt = d.setdefault("extraKnownMarketplaces", {}).setdefault("outbid-dirigent", {})
src = mkt.setdefault("source", {"source": "github", "repo": "BIDEquity/outbid-dirigent"})
src["ref"] = ref
p.write_text(json.dumps(d, indent=2))
PY
    claude plugin marketplace update "$MARKET_NAME" 2>/dev/null || true
  fi

  claude plugin install "$PLUGIN_ID" --scope user
  ok "Claude Code plugin registered"
  printf '%s  restart Claude Code to activate the new skills%s\n' "$c_dim" "$c_reset"
fi

# -------- verify --------
step "verifying"
dirigent --version 2>/dev/null || die "dirigent --version failed — installation is broken"

# -------- banner --------
cat <<EOF

$(printf '%sdirigent is installed%s' "$c_green" "$c_reset")

  Headless:     dirigent --spec SPEC.md --repo .
  Claude Code:  /dirigent:hi    (or /dirigent:start)

  Version:      ${VERSION}
  Docs:         https://github.com/${REPO_GH}

EOF
