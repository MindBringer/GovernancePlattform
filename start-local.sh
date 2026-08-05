#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-${GOVERNANCE_COMPANION_PORT:-8770}}"
python3 tools/companion/server.py --port "$PORT"
