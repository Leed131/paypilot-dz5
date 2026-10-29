#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -d .git ]; then
  echo "This folder already has Git history. Keep it and send the terminal output."
  exit 1
fi

git init -q -b main
git add .
git rm -q --cached -- evidence/hw5-forecast.md
git commit -q -m "Prepare HW5 security cases, runner and laboratory evidence"
git add evidence/hw5-forecast.md
git commit -q -m "Record HW5 forecast before security model runs"
git show -s --format='%H%n%P%n%cI%n%s' HEAD > evidence/hw5-forecast-commit.txt
git log -2 --format='%h %s'
make dry-run
make check
