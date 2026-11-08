#!/bin/zsh
set -e
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

REPO_DIR="/Users/kiran/workplace/spinny_monitor"
cd "$REPO_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting hourly car monitor sweep..."
/opt/homebrew/anaconda3/bin/python3 spinny_checker.py --city bangalore --max-price 0

if [[ -n $(git status --porcelain clean_bangalore_cars.json deals.html index.html) ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Changes detected. Committing and pushing to website..."
    git add clean_bangalore_cars.json deals.html index.html latest_alerts.json
    git commit -m "chore(auto): hourly deals sync [$(date '+%Y-%m-%d %H:%M')]"
    git push origin main
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Successfully published to website."
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No inventory changes."
fi
