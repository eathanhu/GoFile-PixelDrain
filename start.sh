#!/bin/sh
set -e

# Try to sync system time (non-fatal)
if command -v ntpdate >/dev/null 2>&1; then
  echo "⏱️  Syncing system time with time.google.com..."
  ntpdate -u time.google.com || echo "⚠️  ntpdate failed (continuing anyway)"
else
  echo "⚠️  ntpdate not available"
fi

# Start the bot (replace python main.py if you use a module)
exec python main.py
