#!/usr/bin/env bash
set -euo pipefail

# If you have a venv, activate it
if [ -f "./mltbenv/bin/activate" ]; then
  source ./mltbenv/bin/activate
fi

echo "Starting bot at $(date -u)"
exec python main.py
