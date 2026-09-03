#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the NEXTAI autoresearch harness.
# Installs the uv toolchain (if missing) and materializes the locked
# environment, including the dev extra used by the test suite. It never
# downloads the large, gitignored research datasets: those are acquired
# on demand per experiment (see research/data/*/*.json manifests).
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# uv installs to ~/.local/bin, which the base image already exposes on PATH;
# export it explicitly so this script also works in a bare non-login shell.
export PATH="$HOME/.local/bin:$PATH"

# Reproduce the exact locked interpreter + dependency set (pinned in uv.lock).
uv sync --frozen --extra dev

uv run nextai --help >/dev/null
echo "NEXTAI environment ready: $(uv run python -c 'import torch,numpy,scipy,pyamg; print("torch",torch.__version__,"numpy",numpy.__version__)')"
