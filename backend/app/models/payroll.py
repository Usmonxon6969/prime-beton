from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Worker(Base):
    """A production worker paid by the piece."""
    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    position: Mapped[str] = mapped_column(String(80), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProductRate(Base):
    """Pay per finished unit of a product."""
    __tablename__ = "product_rates"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), primary_key=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)


class PayAdjust(Base):
    """A bonus (positive) or a deduction (negative) added to a worker's pay."""
    __tablename__ = "pay_adjusts"

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(10), default="posted")
