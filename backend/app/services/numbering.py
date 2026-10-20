from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Counter


def next_number(db: Session, prefix: str) -> str:
    """Next document number like RN-000119. Row-locked on PostgreSQL so two users never get the same number."""
    row = db.get(Counter, prefix, with_for_update=True)
    if row is None:
        # first document of a series: two requests can arrive together, only one may create the row
        try:
            with db.begin_nested():
                db.add(Counter(prefix=prefix, last=0))
                db.flush()
        except IntegrityError:
            pass
        row = db.get(Counter, prefix, with_for_update=True, populate_existing=True)
    row.last += 1
    db.flush()
    return f"{prefix}-{row.last:06d}"
