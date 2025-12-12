#!/usr/bin/env bash
set -e

echo "[Time Sync] Attempting to sync system clock..."
ntpdate -u time.google.com || true

echo "[Time Sync] Current container time:"
date

echo "[Bot] Starting GoFile-PixelDrain bot..."
exec python main.py
