#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

echo "[ENTRYPOINT] Starting debug entrypoint..."
echo "[ENTRYPOINT] Environment variables:"
# print only names, not values — for safety
env | awk -F= '{print $1}' || true

echo "[ENTRYPOINT] Attempting to sync time (if ntpdate exists)..."
if command -v ntpdate >/dev/null 2>&1; then
  ntpdate -u time.google.com || true
else
  echo "[ENTRYPOINT] ntpdate not installed — skipping."
fi

echo "[ENTRYPOINT] Current container time:"
date

echo "[ENTRYPOINT] Running python main.py (unbuffered output)..."
# Run python unbuffered (-u) so logs appear immediately
python -u main.py || EXIT_CODE=$?

# If python returns non-zero, show details and keep container alive so logs are visible
if [ -n "${EXIT_CODE:-}" ] && [ "${EXIT_CODE}" -ne 0 ]; then
  echo "[ENTRYPOINT] main.py exited with code ${EXIT_CODE}"
  echo "[ENTRYPOINT] Dumping last 200 lines of app log (if any):"
  # show any logs in the working directory named *.log
  tail -n 200 *.log 2>/dev/null || true

  echo "[ENTRYPOINT] Sleeping so container doesn't disappear — use Render shell to inspect logs"
  # keep alive so Render runtime logs persist for inspection
  sleep 999999
fi

# If main.py succeeded and returned 0, exit normally
echo "[ENTRYPOINT] main.py finished successfully — exiting."
