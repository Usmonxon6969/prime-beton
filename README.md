# Prime Beton

Production, warehouse, sales, purchasing and cash for a precast-concrete plant, with an AI assistant, financier and analyst. Uzbek, Russian and English.
A real server application: FastAPI + PostgreSQL behind a plain HTML/JS frontend.

```
daybook-app/
├── backend/        FastAPI service, SQLAlchemy models, Alembic migrations, tests
│   ├── app/api         HTTP endpoints (one file per area)
│   ├── app/services    business rules: stock, orders, production, money, reports
│   ├── app/models      database tables
│   ├── app/core        settings, security, roles, errors
│   ├── app/tools       import_csv.py – load customers, suppliers, items from a 1C export
│   ├── alembic/        schema migrations
│   ├── app/ai          Claude integration: client, role-scoped tools, assistant, signals, document drafts
│   └── tests/          50 tests (API, rules, reports, audit, AI with a scripted fake model)
├── frontend/       the web app: index.html, css/, js/ (no build step)
├── e2e/            browser tests (Playwright)
├── docs/           architecture.md, ai.md
└── docker-compose.yml
```

> Handing the system over? See [docs/handover-uz.md](docs/handover-uz.md) (acceptance checklist, known limits) and [docs/user-guide-uz.md](docs/user-guide-uz.md).

## Run it (Docker)

```bash
cp .env.example .env          # then edit: passwords, SECRET_KEY, ADMIN_PASSWORD
docker compose up --build
```

Open http://localhost:8000 and sign in as `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `.env`.
The container applies the migrations and the catalogue seed on every start (both are safe to repeat).

- `SECRET_KEY` signs the login tokens. Use a long random value (`openssl rand -hex 32`); the server refuses to start
  with the default key on a real database.
- `SEED_DEMO_USERS=true` additionally creates six demo logins (admin/direktor/ishlab/omborchi/sotuv/buxgalter) and
  shows them on the sign-in page. For trying it out only; leave it `false` in production.
- Backups: a daily dump goes to ./backups (see [docs/security.md](docs/security.md), also HTTPS and the security checklist).
- Data lives in the Docker volume `prime-stroy_dbdata` and survives `docker compose restart`, `stop`, `up` and `up --build`. It is deleted only by `docker compose down -v` (or `docker volume rm`, or Docker Desktop's *Clean up / Prune*). Never use `-v` unless you want an empty database.
- Data lives in the `dbdata` volume. Back it up with
  `docker compose exec db pg_dump -U daybook daybook > backup.sql`.

## AI (Claude)

Put your key in `.env` (`ANTHROPIC_API_KEY=...`) and restart; nothing else to configure. The key is read only by the
server. What it adds:

- **AI assistant / financier / analyst** (menu *AI assistant*): chat that answers from your database in uz/ru/en
  ("how much cement is left?", "who owes us this month?", "will the money last until next month?").
- **Briefing and signals** on the dashboard and the AI page: stock-out forecast, slow-moving goods, overdue debts,
  sales trend, 30-day cash forecast, odd prices or payments.
- **Fill a document with AI**: paste a message or attach a photo of an invoice; you get a draft that opens in the
  normal form for review. Nothing is saved until you press Post.

The AI only reads, and only what the signed-in user's role may open. Without a key the chat and drafting are off
and the signals, reports and a rule-based briefing still work. Details and privacy: [docs/ai.md](docs/ai.md).

## Reports, printing, journal

- **Reports** (menu *Reports*): stock turnover (oborotka), sales, purchases, cash flow, estimated profit, customer and
  supplier debts for any period, each with **Excel export**.
- **PDF**: delivery note (open an invoice → *PDF*) and reconciliation act (customer/supplier act → *PDF*).
- **Change journal** (menu *Change journal*, admin and director): who created, changed, deleted or restored what,
  with the old and new values. Written automatically on every commit.
- **Users** (menu *Users*): administrators add users, change roles, reset passwords, deactivate. Everyone can change
  their own password (key icon in the side menu). Five wrong sign-ins lock that username for five minutes.

## Run it for development (no Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
SEED_DEMO_USERS=true alembic upgrade head && python -m app.seed      # SQLite file daybook.db
uvicorn app.main:app --reload                                         # http://localhost:8000
```

API documentation (Swagger): http://localhost:8000/api/docs

To use PostgreSQL set `DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname`.

## Tests

```bash
cd backend
pytest                                                     # SQLite, in memory
TEST_DATABASE_URL=postgresql+psycopg://user:pw@host/db_for_tests pytest   # PostgreSQL (the database is wiped)
```

Browser tests: see `e2e/README.md`.

## Roles

| Role | Can edit | Can only view |
| --- | --- | --- |
| admin | everything | |
| director | | everything |
| prod (production) | production, products, materials, specifications | dashboard, warehouse |
| wh (warehouse) | warehouse, delivery notes, receipts | dashboard, production, products, materials, orders, suppliers |
| sales | customers, orders, delivery notes | dashboard, warehouse, products |
| acc (accountant) | bank, cash | dashboard, customers, orders, delivery notes, suppliers, receipts |

The matrix is in `backend/app/core/roles.py`; the server enforces it on every request.

## Importing from 1C

Export *Номенклатура*, *Контрагенты* (покупатели) and the suppliers list from 1C to CSV or Excel → CSV, then:

```bash
cd backend
python -m app.tools.import_csv customers kontragenty.csv
python -m app.tools.import_csv suppliers  postavshiki.csv
python -m app.tools.import_csv items      nomenklatura.csv
```

Columns are matched by name in English or Russian (`Наименование`, `Телефон`, `Контактное лицо`, `Вид`, `Единица`,
`Мин. остаток`). Existing names are skipped, so running it twice is safe. Opening stock is not imported: enter it as a
receipt so the stock ledger stays complete. A live two-way link with 1C (OData / HTTP service) can be built on the same
API; it is not part of this version.

## How the pieces fit

See [docs/architecture.md](docs/architecture.md).

## Updating to a new version
Unpack the new zip, copy your `.env` into it, and run `docker compose up -d --build` **from the new folder**. The frontend is mounted from the folder you run compose in, so running it from the old folder keeps serving the old pages. Data stays in the `prime-stroy_dbdata` volume. If the browser still shows the old look, press Ctrl+Shift+R.
