#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
if [[ ! -d .venv ]]; then
  python -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
# shellcheck disable=SC1091
source .venv/bin/activate
exec uvicorn apso.main:app --host 0.0.0.0 --port 8000 --reload
