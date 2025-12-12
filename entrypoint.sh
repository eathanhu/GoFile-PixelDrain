#!/usr/bin/env bash
set -e

echo "[Time Sync] Checking for ntpdate..."
if command -v ntpdate >/dev/null 2>&1; then
  echo "[Time Sync] ntpdate found — syncing time..."
  ntpdate -u time.google.com || true
else
  echo "[Time Sync] ntpdate not installed — skipping time sync."
fi

echo "[Time Sync] Current container time:"
date

echo "[Bot] Starting main.py..."
exec python main.py
