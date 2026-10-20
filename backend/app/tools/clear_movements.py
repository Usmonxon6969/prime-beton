"""Clear the test MOVEMENTS before handing the system to the client. Master data stays.

    docker compose exec api python -m app.tools.clear_movements          # only shows what would be deleted
    docker compose exec api python -m app.tools.clear_movements --yes    # deletes it (one transaction: all or nothing)
    ... --people                                                         # also customers, suppliers and workers (shown / deleted with --yes)

Deleted: orders, delivery notes, receipts, production, stock counts and write-offs, every money movement (cash and bank),
worker pay adjustments, stock balances and stock history, the journal entries of those documents, the document number
counters (numbering starts again from 1) and the Telegram bot's memory of what it announced.

Kept: products, materials, specifications and piece rates, units, warehouses and plants, money accounts (names, numbers and
opening balances), customers, suppliers, workers, users and their sessions, company details, Telegram links.

Make a backup first: `docker compose exec backup sh /ops/backup.sh once`. This cannot be undone without it."""
import argparse

from sqlalchemy import delete, func, select

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal
from app.models import Account, AuditLog

MOVEMENTS = [
    "invoice_rows", "invoices", "order_rows", "orders", "receipt_rows", "receipts",
    "production_consumption", "production_crew", "production_rows", "production_docs",
    "stock_adjust_rows", "stock_adjusts", "fin_docs", "pay_adjusts", "stock_moves", "stock_balances",
    "counters", "telegram_cursors", "telegram_sent", "telegram_drafts",
]
KEPT = ["items", "norms", "product_rates", "units", "warehouses", "accounts", "customers", "suppliers", "workers", "users", "company", "telegram_links"]
PEOPLE = ["customers", "suppliers", "workers"]          # only with --people (nothing can point at them once the movements are gone)
JOURNAL = ["orders", "invoices", "receipts", "production_docs", "stock_adjusts", "fin_docs", "pay_adjusts"]     # journal entries about these documents go too


def _count(db, table) -> int:
    return db.execute(select(func.count()).select_from(table)).scalar_one()


def plan(db, people: bool = False) -> dict[str, int]:
    tables = Base.metadata.tables
    out = {name: _count(db, tables[name]) for name in MOVEMENTS + (PEOPLE if people else [])}
    out["audit_log (documents)"] = db.query(AuditLog).filter(AuditLog.entity.in_(JOURNAL)).count()
    return out


def clear(db, people: bool = False) -> dict[str, int]:
    """Delete the movements in one transaction. Raises (and changes nothing) if anything goes wrong."""
    done = {}
    done["audit_log (documents)"] = db.execute(delete(AuditLog).where(AuditLog.entity.in_(JOURNAL))).rowcount
    for table in reversed(Base.metadata.sorted_tables):      # children before parents, whatever the foreign keys are
        if table.name in MOVEMENTS or (people and table.name in PEOPLE):
            done[table.name] = db.execute(delete(table)).rowcount
    db.commit()
    return done


def kept(db, people: bool = False) -> dict[str, int]:
    tables = Base.metadata.tables
    return {name: _count(db, tables[name]) for name in KEPT if not (people and name in PEOPLE)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--people", action="store_true", help="also delete customers, suppliers and workers")
    ap.add_argument("--yes", action="store_true", help="really delete (without it nothing changes)")
    a = ap.parse_args()
    with SessionLocal() as s:
        if not a.yes:
            print("DRY RUN - nothing is deleted. Would delete:")
            for k, v in plan(s, a.people).items():
                print(f"  {k}: {v}")
            print("Stays:")
            for k, v in kept(s, a.people).items():
                print(f"  {k}: {v}")
            print("Money accounts (opening balance stays as it is):")
            for acc in s.query(Account).order_by(Account.id):
                print(f"  {acc.kind:5} {acc.name_uz}: opening {float(acc.opening_balance):,.0f}")
            print("To delete for real: add --yes (after a backup).")
        else:
            for k, v in clear(s, a.people).items():
                print(f"deleted {k}: {v}")
            print("cleared; " + ("customers, suppliers and workers deleted too; " if a.people else "") + "master data kept")
