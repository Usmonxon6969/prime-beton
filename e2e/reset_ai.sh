#!/bin/bash
# fresh SQLite DB + server on :8000 wired to a fake Claude on :9099 (no real key needed)
D="$(cd "$(dirname "$0")" && pwd)"
[ -f /tmp/fc.pid ] && kill -9 $(cat /tmp/fc.pid) 2>/dev/null
[ -f /tmp/uv.pid ] && kill -9 $(cat /tmp/uv.pid) 2>/dev/null
sleep 1; rm -f /tmp/e2e.db
nohup python3 $D/fake_claude.py >/tmp/fc.log 2>&1 & echo $! > /tmp/fc.pid
cd $D/../backend
export DATABASE_URL=sqlite:////tmp/e2e.db SEED_DEMO_USERS=true ANTHROPIC_API_KEY=test-key AI_BASE_URL=http://127.0.0.1:9099
alembic upgrade head >/dev/null 2>&1; python3 -m app.seed >/dev/null
nohup uvicorn app.main:app --port 8000 >/tmp/uv.log 2>&1 & echo $! > /tmp/uv.pid
sleep 3; curl -s localhost:8000/api/health
