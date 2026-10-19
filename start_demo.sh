#!/usr/bin/env bash
# Avvio demo locale per macOS/Linux. Equivalente di start_demo.bat (Windows).
# Runtime supportato: Python 3.13, 3.14 o 3.15 (vedi docs/DEMO_RUNTIME.md).
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8080}"
SUPPORTED_VERSIONS="3.15 3.14 3.13"

if [ ! -d .venv ]; then
  if [ -z "${PYTHON:-}" ]; then
    for version in $SUPPORTED_VERSIONS; do
      if command -v "python$version" >/dev/null 2>&1; then
        PYTHON="python$version"
        break
      fi
    done
  fi
  if [ -z "${PYTHON:-}" ] || ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3.13, 3.14 o 3.15 non trovato. Installarlo o impostare PYTHON=/percorso/python3.x." >&2
    exit 1
  fi
  "$PYTHON" -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi

VENV_VERSION="$(.venv/bin/python -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
case " $SUPPORTED_VERSIONS " in
  *" $VENV_VERSION "*) ;;
  *)
    echo "La .venv usa Python $VENV_VERSION: rimuoverla e rilanciare con Python 3.13, 3.14 o 3.15." >&2
    exit 1
    ;;
esac

export BROFIND_RUNTIME="${BROFIND_RUNTIME:-demo}"
echo "Cockpit in avvio su http://127.0.0.1:${PORT} (runtime: ${BROFIND_RUNTIME})"
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
