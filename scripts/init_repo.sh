#!/usr/bin/env bash
# One-time setup: initialize the git repo and make the first commit.
set -e

git init
git add .
git commit -m "Initial scaffold: docs, structure, and phase plan"

echo ""
echo "Repo initialized. Next steps:"
echo "  1. Create an empty repo named 'fraud-detection-realtime' on GitHub"
echo "  2. git remote add origin git@github.com:gabrielcaixeta01/fraud-detection-realtime.git"
echo "  3. git branch -M main"
echo "  4. git push -u origin main"
