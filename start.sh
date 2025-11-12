#!/bin/sh
set -e

# Try to sync system time using chrony
if command -v chronyd >/dev/null 2>&1; then
  echo "⏱️  Syncing system time using chrony..."
  chronyd -q 'server time.google.com iburst' || echo "⚠️  chrony sync failed (continuing anyway)"
else
  echo "⚠️  chrony not available"
fi

# Start bot
exec python main.py
