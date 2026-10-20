from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StockBalance(Base):
    """Current quantity of an item in a warehouse."""
    __tablename__ = "stock_balances"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), primary_key=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)


class StockMove(Base):
    """Append-only ledger. The net of a document's moves is its current effect on stock."""
    __tablename__ = "stock_moves"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    delta: Mapped[Decimal] = mapped_column(Numeric(18, 3))
    doc_type: Mapped[str] = mapped_column(String(12))  # production order invoice receipt
    doc_id: Mapped[int] = mapped_column(Integer, index=True)
    doc_number: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Counter(Base):
    """Per-prefix document number sequence (PRD, ZK, RN, PN, PKO, RKO, BP, BS)."""
    __tablename__ = "counters"

    prefix: Mapped[str] = mapped_column(String(8), primary_key=True)
    last: Mapped[int] = mapped_column(Integer, default=0)
