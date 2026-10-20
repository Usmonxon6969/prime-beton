from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.phone import normalize_phone

from app.schemas.common import ORM


class WorkerIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    position: str = Field(default="", max_length=80)
    phone: str = Field(default="", max_length=40)
    is_active: bool = True

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)


class WorkerOut(ORM):
    id: int
    name: str
    position: str
    phone: str
    is_active: bool


class RateIn(BaseModel):
    item_id: int
    rate: float = Field(ge=0, le=1_000_000_000)


class RatesPut(BaseModel):
    rates: list[RateIn]


class RateOut(ORM):
    item_id: int
    rate: float


class AdjIn(BaseModel):
    worker_id: int
    date: datetime
    amount: float = Field(ge=-1_000_000_000_000, le=1_000_000_000_000)
    note: str = Field(default="", max_length=300)


class AdjOut(ORM):
    id: int
    worker_id: int
    date: datetime
    amount: float
    note: str
    status: str
