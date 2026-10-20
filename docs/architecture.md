# Architecture

```
browser ──HTTP/JSON──▶  FastAPI (backend/app)  ──SQLAlchemy──▶  PostgreSQL
  frontend/ (static)      api → services → models                 (SQLite for local dev and tests)
```

One process serves both the API (`/api/...`) and the static frontend, so one container is enough.

## Backend layers

| Layer | Folder | Rule |
| --- | --- | --- |
| API | `app/api` | Parses the request, checks the role (`need(section, level)`), calls a service, commits. No business rules. |
| Services | `app/services` | All business rules and the only place that changes stock or money. Raise `ApiError` with a stable `code`. |
| Models | `app/models` | SQLAlchemy tables. |
| Schemas | `app/schemas` | Pydantic request/response shapes. |
| Core | `app/core` | Settings, passwords and tokens, the role matrix, error type, audit hook, login throttle. |
| AI | `app/ai` | Claude client, role-scoped read-only tools, assistant, deterministic signals, document drafts (see `docs/ai.md`). |

## Data model

- **Catalogue**: `units`, `warehouses` (workshops are `is_workshop` and cannot be deleted), `items`
  (`kind` = `product` or `material`, names in uz/ru/en), `norms` (the specification: material per product unit).
- **Partners**: `customers`, `suppliers`.
- **Documents** (each has a header and `..._rows`): `orders`, `invoices` (delivery notes), `receipts`,
  `production_docs` (+ `production_consumption`, a snapshot of the materials written off).
- **Money**: `accounts` (bank or cash, opening balance) and `fin_docs` (in / out / transfer, with an article).
- **Stock**: `stock_balances` (current quantity per item and warehouse) and `stock_moves`, an append-only ledger.
- **Audit**: `audit_log` (user, action, table, record, old → new values), written by `app/core/audit.py`.
- **System**: `users`, `counters` (document numbers PRD, ZK, RN, PN, PKO, RKO, BP, BS; row-locked so numbers never repeat).

## Rules worth knowing

- **Stock only moves through documents.** Receipt and production add, invoice and production consumption subtract.
  A balance can never go below zero; the request fails with `insufficient_stock`.
- **Editing is undo + redo in one transaction.** The old effect is reverted, the new one applied, and only the final
  balances are checked (`stock.deferred`). A failed edit changes nothing.
- **Nothing is hard-deleted.** Documents get `status = deleted` and can be restored; catalogue rows and partners get
  `is_active = false`. A record that documents use cannot be deleted or have its unit changed.
- **Cash desks cannot go negative** (`cash_negative`); bank accounts may.
- **Orders** track what is shipped; an invoice cannot ship more than is left on its order (`over_order`) and an order row
  cannot drop below what was shipped (`order_below_shipped`).
- **Roles** (`app/core/roles.py`): every section has level 0 / 1 (view) / 2 (edit) per role. The server enforces it;
  the frontend only hides what the server would refuse.

- **Audit trail.** A session hook (`app/core/audit.py`) records every create / update / delete / restore of business
  records with the signed-in user (`db.info["user"]`, set by `current_user`). Row tables are folded into their document
  ("rows changed"); stock tables, counters and the log itself are skipped. Nothing in the services needs to remember it.
- **Login guard.** Five failed sign-ins for the same username and address lock it for five minutes (in memory, per
  process: with several workers put a shared store such as Redis behind `app/core/throttle.py`).
- **Reports** (`app/services/analytics.py`) all return one table shape (`columns`, `rows`, `totals`), so the screen,
  the Excel export and the AI tools share a single implementation. Turnover is computed from posted documents by their
  own dates, so it stays right after edits.

## Error contract

Every failure is `{"detail": {"code", "message", "params"}}` with status 401, 403, 404, 409 (rule broken) or 422
(invalid input). `code` is stable; the frontend turns `code` + `params` into text in the user's language
(`frontend/js/api.js`, table `APIX`).

## Frontend

Plain HTML, CSS and JavaScript, no build step. `frontend/js` loads in the order listed in `index.html`.

- `api.js` – `api(method, path, body)`, token handling, error text, and `srv(call, ok, fail)`:
  run a request, reload the data, then continue.
- `store.js` – `Store.load()` fetches every list the signed-in role may read and refills the lists the pages use
  (`WH`, `PRODUCTS`, `ITEMS`, `CUS`, `ORD`, `INV`, `REC`, `plog`, `FIN`, `ACC`, ...), keeping the server id of each record.
  Every successful change calls it, so the screen always shows what the database holds.
- One file per section (`production.js`, `orders.js`, `finance.js`, ...) with its own render and save functions.

## Adding a feature

1. Model + Alembic migration (`alembic revision --autogenerate -m "..."`).
2. Service function with the rule, API endpoint, schema.
3. A test in `backend/tests` (the `ctx` fixture gives you a logged-in client).
4. Load it in `Store.build`, render it, call it through `srv(...)`.


## Several documents at once (tabs)

`frontend/js/tabs.js` keeps every opened document form (order, delivery note, receipt, production, bank/cash document) as a tab above the page,. A tab stores a copy of the form's globals (`OS`, `IS`, `RS`, `rows`..., `FS`) and its inputs when you leave it and restores them when you return.
The router calls `Tabs.pre(h)` / `Tabs.post(h)` around `routeCore()`; a successful save calls `Tabs.done()` to close the tab. Closing a tab with
unsaved data asks for a second click. The same file adds "+ new customer / supplier" inside the order, delivery note and receipt forms.
