#!/usr/bin/env bash
set -euo pipefail

cd /workspace

if [[ -f uv.lock ]]; then
  echo "Using existing uv.lock"
  uv sync --locked --group dev
else
  echo "uv.lock not found; resolving dependencies and creating it"
  uv sync --group dev
fi

python -m ball_cv doctor
touch /tmp/ball-cv-ready
exec sleep infinity
