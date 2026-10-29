#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .git ]; then
  echo "Use the existing paypilot-dz5 folder with the original forecast Git history."
  exit 1
fi
if [ "$(git branch --show-current)" != main ]; then
  echo "Expected branch main. Stop and send the output."
  exit 1
fi
forecast_commit=3b328119b14a47ef87abae32178f26b8a32dab2e
git merge-base --is-ancestor "$forecast_commit" HEAD
git diff --exit-code "$forecast_commit" -- evidence/hw5-forecast.md evals/sets/l06_security.jsonl evals/*.py
make check
make replay
git add .
if ! git diff --cached --quiet; then
  git commit -m "Finalize HW5 security log and preserve recorded model evidence"
fi
git log -3 --format='%h %s'
echo "Local HW5 files are ready. Preserve this Git history when publishing."
