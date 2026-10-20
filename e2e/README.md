# Browser tests

These drive the real app (the page, the API and the database) with Playwright.

```bash
pip install playwright && playwright install chromium
./e2e/reset.sh              # fresh SQLite database + server on http://localhost:8000 (demo users on)
python e2e/flow_main.py     # receipt -> production -> order -> delivery note -> payments, settings, reload
python e2e/flow_edit.py     # edit / delete / restore and the rules that block them (run after flow_main.py)
python e2e/roles.py         # all six roles in all three languages: every page opens without errors
```

```bash
./e2e/reset_ai.sh           # fresh database + a fake Claude on :9099 (e2e/fake_claude.py), server on :8000
python e2e/flow_v2.py /tmp  # AI chat, AI draft -> form, reports + Excel, PDF, journal, users, role scoping (screenshots go to /tmp)
```

Each script prints `OK` / `FAIL` per check and exits non-zero on a failure. `reset.sh` wipes `/tmp/e2e.db`,
so never point it at a real database.
