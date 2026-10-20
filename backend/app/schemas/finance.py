from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORM


class AccountIn(BaseModel):
    kind: str = Field(pattern="^(bank|cash)$")
    name_uz: str
    name_ru: str
    name_en: str
    number: str = ""
    opening_balance: float = 0


class AccountUpdate(BaseModel):
    name_uz: str | None = None
    name_ru: str | None = None
    name_en: str | None = None
    number: str | None = None
    opening_balance: float | None = None


class AccountOut(ORM):
    id: int
    kind: str
    name_uz: str
    name_ru: str
    name_en: str
    number: str
    opening_balance: float
    balance: float = 0


class FinIn(BaseModel):
    date: datetime
    kind: str = Field(pattern="^(in|out|tr)$")
    account_id: int
    to_account_id: int | None = None
    article: str
    customer_id: int | None = None
    supplier_id: int | None = None
    order_id: int | None = None
    worker_id: int | None = None
    party: str = ""
    amount: float = Field(gt=0)
    comment: str = ""


class FinOut(ORM):
    id: int
    number: str
    date: datetime
    kind: str
    account_id: int
    to_account_id: int | None
    article: str
    customer_id: int | None
    supplier_id: int | None
    order_id: int | None = None
    worker_id: int | None = None
    party: str
    amount: float
    comment: str
    status: str
