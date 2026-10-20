from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RowIn(BaseModel):
    item_id: int
    qty: float = Field(gt=0)
    price: float = Field(default=0, ge=0)


class RowOut(ORM):
    item_id: int
    qty: float
    price: float = 0


class DocBase(BaseModel):
    date: datetime
    comment: str = ""
