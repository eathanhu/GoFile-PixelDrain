#!/usr/bin/env bash
set -euo pipefail

echo "==========================================="
echo "⏱  Time sync attempt starting..."
echo "Before sync: $(date -u) (epoch: $(python -c 'import time; print(int(time.time()))'))"

# Try chronyd quick one-shot
if command -v chronyd >/dev/null 2>&1; then
  echo "Using chronyd -q to sync time..."
  # -q: run in foreground, set the clock, then exit
  chronyd -q || echo "⚠️  chronyd -q failed (continuing anyway)"
fi

# Try chronyc makestep as a fallback
if command -v chronyc >/dev/null 2>&1; then
  echo "Running chronyc makestep..."
  chronyc makestep || echo "⚠️  chronyc makestep failed (continuing anyway)"
fi

echo "After sync:  $(date -u) (epoch: $(python -c 'import time; print(int(time.time()))'))"
echo "==========================================="

# Start the application
exec python main.py
