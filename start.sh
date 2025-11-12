#!/usr/bin/env bash
set -e

# attempt to sync time (non-fatal)
if command -v ntpdate >/dev/null 2>&1; then
  ntpdate -u pool.ntp.org || true
else
  echo "ntpdate not installed; skipping time sync"
fi

# start the app
exec python main.py
