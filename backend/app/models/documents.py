from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _qty():
    return mapped_column(Numeric(18, 3))


def _money():
    return mapped_column(Numeric(18, 2), default=0)


class Order(Base):
    """Customer order. No stock effect; shipped quantities come from posted invoices."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(24), unique=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    comment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(10), default="open")  # open deleted
    rows: Mapped[list["OrderRow"]] = relationship(cascade="all, delete-orphan", order_by="OrderRow.id", lazy="selectin")


class OrderRow(Base):
    __tablename__ = "order_rows"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    qty: Mapped[Decimal] = _qty()
    price: Mapped[Decimal] = _money()


class Invoice(Base):
    """Delivery note: ships finished goods from a warehouse to a customer."""
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(24), unique=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    comment: Mapped[str] = mapped_column(Text, default="")
    pay_due: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)   # the customer must pay by this date
    driver: Mapped[str] = mapped_column(String(120), default="", server_default="")          # printed on the waybill
    vehicle: Mapped[str] = mapped_column(String(30), default="", server_default="")
    status: Mapped[str] = mapped_column(String(10), default="posted")  # posted deleted
    rows: Mapped[list["InvoiceRow"]] = relationship(cascade="all, delete-orphan", order_by="InvoiceRow.id", lazy="selectin")


class InvoiceRow(Base):
    __tablename__ = "invoice_rows"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    qty: Mapped[Decimal] = _qty()
    price: Mapped[Decimal] = _money()


class Receipt(Base):
    """Purchase receipt: materials or products arrive from a supplier into a warehouse."""
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(24), unique=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    comment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(10), default="posted")
    rows: Mapped[list["ReceiptRow"]] = relationship(cascade="all, delete-orphan", order_by="ReceiptRow.id", lazy="selectin")


class ReceiptRow(Base):
    __tablename__ = "receipt_rows"
    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    qty: Mapped[Decimal] = _qty()
    price: Mapped[Decimal] = _money()


class ProductionDoc(Base):
    """Production document: adds products to a workshop and consumes materials by norms."""
    __tablename__ = "production_docs"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(24), unique=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    comment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(10), default="posted")
    labour: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0")   # piece-rate pay of this batch, frozen at posting
    rows: Mapped[list["ProductionRow"]] = relationship(cascade="all, delete-orphan", order_by="ProductionRow.id", lazy="selectin")
    consumption: Mapped[list["ProductionConsumption"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    crew: Mapped[list["ProductionCrew"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

    @property
    def worker_ids(self) -> list[int]:
        return [c.worker_id for c in self.crew]


class ProductionRow(Base):
    __tablename__ = "production_rows"
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("production_docs.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    qty: Mapped[Decimal] = _qty()                                   # good units: these go to stock
    scrap: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0, server_default="0")   # spoiled units: materials are used, nothing is added


class ProductionConsumption(Base):
    """Materials consumed, frozen at posting time so later norm changes do not rewrite history."""
    __tablename__ = "production_consumption"
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("production_docs.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    qty: Mapped[Decimal] = _qty()


class ProductionCrew(Base):
    """Who made the batch: the piece-rate pay of the document is shared equally between these workers."""
    __tablename__ = "production_crew"
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("production_docs.id"), index=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id"), index=True)


class StockAdjust(Base):
    """Stock count (inventory) or write-off. Rows carry the signed effect on stock."""
    __tablename__ = "stock_adjusts"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(24), unique=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    kind: Mapped[str] = mapped_column(String(8))                     # count writeoff
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    reason: Mapped[str] = mapped_column(String(12), default="")      # write-off: scrap damage loss expired other
    comment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(10), default="posted")
    rows: Mapped[list["StockAdjustRow"]] = relationship(cascade="all, delete-orphan", order_by="StockAdjustRow.id", lazy="selectin")


class StockAdjustRow(Base):
    __tablename__ = "stock_adjust_rows"
    id: Mapped[int] = mapped_column(primary_key=True)
    adjust_id: Mapped[int] = mapped_column(ForeignKey("stock_adjusts.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    system_qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)   # count: what the books said when it was posted
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)          # count: what was counted; write-off: what is written off
    delta: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)        # signed change of stock
