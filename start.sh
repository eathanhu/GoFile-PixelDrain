#!/usr/bin/env bash
set -euo pipefail

# If you use a virtualenv named mltbenv, activate it. Otherwise remove this line.
if [ -f "./mltbenv/bin/activate" ]; then
  source ./mltbenv/bin/activate
fi

# optional: print a small startup marker
echo "Starting bot at $(date -u)"

# Run update/prestart tasks if needed
# python3 update.py   # uncomment only if you need it

# Run the app
# adjust command if your entrypoint module differs
exec python main.py
