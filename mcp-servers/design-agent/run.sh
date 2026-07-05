#!/usr/bin/env bash
# Self-bootstrapping launcher for the Multimodal Design Agent MCP server.
# Creates a local venv on first run, installs deps, then execs the stdio server.
# Usage (register with Claude Code):
#   claude mcp add design-agent -- bash /ABS/PATH/mcp-servers/design-agent/run.sh
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"
PY="${PYTHON:-python3}"

if [ ! -x "$VENV/bin/python" ]; then
  "$PY" -m venv "$VENV"
  # Quiet install; log to stderr so it never corrupts the MCP stdio (stdout) stream.
  "$VENV/bin/pip" install -q --disable-pip-version-check -r "$DIR/requirements.txt" 1>&2
fi

exec "$VENV/bin/python" "$DIR/server.py"
