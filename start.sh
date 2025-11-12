#!/usr/bin/env bash
set -e

echo "==========================================="
echo "⏱  Attempting to sync container time..."
echo "Before sync: $(date -u) (epoch: $(python -c 'import time; print(int(time.time()))'))"

# Try ntpdate first (quick)
if command -v ntpdate >/dev/null 2>&1; then
  echo "Using ntpdate to sync time..."
  ntpdate -u pool.ntp.org || echo "⚠️  ntpdate failed (continuing anyway)"
fi

# Fallback: chrony/chronyd if present
if command -v chronyd >/dev/null 2>&1; then
  echo "Using chronyd to sync time..."
  chronyd -q 'server time.google.com iburst' || echo "⚠️  chronyd failed (continuing anyway)"
elif command -v chronyc >/dev/null 2>&1; then
  echo "Using chronyc to makestep..."
  chronyc makestep || echo "⚠️  chronyc failed (continuing anyway)"
fi

echo "After sync: $(date -u) (epoch: $(python -c 'import time; print(int(time.time()))'))"
echo "==========================================="

# Start the app
exec python main.py
