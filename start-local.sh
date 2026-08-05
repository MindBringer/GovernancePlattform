#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ARGS=()
if [[ $# -gt 0 ]]; then
  ARGS+=(--port "$1")
fi
if [[ "${GOVERNANCE_COMPANION_NO_BROWSER:-0}" == "1" ]]; then
  ARGS+=(--no-browser)
fi
python3 tools/companion/server.py "${ARGS[@]}"
