from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Company(Base):
    """Our own details for printed documents (one row, id = 1): letterhead lines of the waybill."""
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), default="", server_default="")
    address: Mapped[str] = mapped_column(String(240), default="", server_default="")
    postcode: Mapped[str] = mapped_column(String(20), default="", server_default="")
    okonh: Mapped[str] = mapped_column(String(30), default="", server_default="")
    account: Mapped[str] = mapped_column(String(40), default="", server_default="")
    bank: Mapped[str] = mapped_column(String(200), default="", server_default="")
    mfo: Mapped[str] = mapped_column(String(20), default="", server_default="")
    inn: Mapped[str] = mapped_column(String(20), default="", server_default="")
    phone: Mapped[str] = mapped_column(String(60), default="", server_default="")
    receive_note: Mapped[str] = mapped_column(Text, default="", server_default="")   # printed after "Received" on the waybill
