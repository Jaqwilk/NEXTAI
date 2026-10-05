#!/usr/bin/env bash
# Requires Python 3.11+ and an already provisioned uv tool.
# No unpinned curl-to-shell installer and no experiment/data acquisition here.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/bootstrap_environment.py
