#!/bin/bash
# fresh sqlite DB + server on :8000
B="$(cd "$(dirname "$0")/../backend" && pwd)"
for p in $(pgrep -f "[u]vicorn app.main"); do kill -9 $p; done
sleep 1
rm -f /tmp/e2e.db
cd $B
export DATABASE_URL=sqlite:////tmp/e2e.db SEED_DEMO_USERS=true
alembic upgrade head >/dev/null 2>&1
python3 -m app.seed >/dev/null
nohup uvicorn app.main:app --port 8000 > /tmp/uv.log 2>&1 &
sleep 3
curl -s localhost:8000/api/health
