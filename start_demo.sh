#!/usr/bin/env bash
# Avvio demo locale per macOS/Linux. Equivalente di start_demo.bat (Windows).
# Runtime supportato: Python 3.13.x (3.14 non supportato: vedi docs/DEMO_RUNTIME.md).
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8080}"
PYTHON="${PYTHON:-python3.13}"

if [ ! -d .venv ]; then
  if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3.13 non trovato ($PYTHON). Installarlo o impostare PYTHON=/percorso/python3.13." >&2
    exit 1
  fi
  "$PYTHON" -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi

VENV_VERSION="$(.venv/bin/python -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if [ "$VENV_VERSION" != "3.13" ]; then
  echo "La .venv usa Python $VENV_VERSION: rimuoverla e rilanciare con Python 3.13." >&2
  exit 1
fi

export BROFIND_RUNTIME="${BROFIND_RUNTIME:-demo}"
echo "Cockpit in avvio su http://127.0.0.1:${PORT} (runtime: ${BROFIND_RUNTIME})"
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
