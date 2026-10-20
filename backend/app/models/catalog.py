from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Unit(Base):
    """Unit of measure (dona, kg, tonna, m3 ...)."""
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)          # Uzbek (also the default label)
    name_ru: Mapped[str] = mapped_column(String(32), default="", server_default="")
    name_en: Mapped[str] = mapped_column(String(32), default="", server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Warehouse(Base):
    """A store. Workshops (is_workshop) are production sites: they cannot be deleted."""
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    is_workshop: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Item(Base):
    """Finished product (kind='product') or raw material (kind='material')."""
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), index=True)
    name_uz: Mapped[str] = mapped_column(String(160))
    name_ru: Mapped[str] = mapped_column(String(160))
    name_en: Mapped[str] = mapped_column(String(160))
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    min_stock: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    unit: Mapped[Unit] = relationship(lazy="joined")


class Norm(Base):
    """Specification: material quantity needed per one unit of a product."""
    __tablename__ = "norms"
    __table_args__ = (UniqueConstraint("product_id", "material_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 3))
