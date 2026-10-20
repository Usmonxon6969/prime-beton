from pydantic import BaseModel, Field, field_validator

from app.core.phone import normalize_phone
from app.schemas.common import ORM


class UnitIn(BaseModel):
    name: str = Field(min_length=1, max_length=32)       # Uzbek
    name_ru: str = Field(default="", max_length=32)
    name_en: str = Field(default="", max_length=32)


class UnitOut(ORM):
    id: int
    name: str
    name_ru: str
    name_en: str


class WarehouseIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    is_workshop: bool = False       # true = production plant (zavod), false = store


class WarehouseOut(ORM):
    id: int
    name: str
    is_workshop: bool
    sort_order: int


class ItemIn(BaseModel):
    kind: str = Field(pattern="^(product|material)$")
    name_uz: str
    name_ru: str
    name_en: str
    unit_id: int
    min_stock: float = Field(default=0, ge=0)


class ItemUpdate(BaseModel):
    name_uz: str | None = None
    name_ru: str | None = None
    name_en: str | None = None
    unit_id: int | None = None
    min_stock: float | None = Field(default=None, ge=0)


class ItemOut(ORM):
    id: int
    kind: str
    name_uz: str
    name_ru: str
    name_en: str
    unit_id: int
    min_stock: float
    stock: dict[int, float] = {}   # warehouse_id -> qty
    total: float = 0


class NormIn(BaseModel):
    material_id: int
    qty: float = Field(ge=0)


class NormsPut(BaseModel):
    norms: list[NormIn]


class PartnerIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    phone: str = ""
    contact: str = ""

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)


class CustomerIn(PartnerIn):
    pay_days: int = Field(0, ge=0, le=365)


class CustomerOut(ORM):
    id: int
    name: str
    phone: str
    contact: str
    pay_days: int = 0


class PartnerOut(ORM):
    id: int
    name: str
    phone: str
    contact: str
