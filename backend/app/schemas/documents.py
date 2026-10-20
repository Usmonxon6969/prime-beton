from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORM, DocBase, RowIn, RowOut


class OrderIn(DocBase):
    customer_id: int
    due_date: datetime | None = None
    rows: list[RowIn]


class OrderOut(ORM):
    id: int
    number: str
    date: datetime
    due_date: datetime | None
    customer_id: int
    comment: str
    status: str
    rows: list[RowOut]
    total: float = 0
    advance: float = 0   # money received for this order before shipping
    state: str = "new"   # new partial shipped deleted


class InvoiceIn(DocBase):
    pay_due: datetime | None = None
    driver: str = Field("", max_length=120)
    vehicle: str = Field("", max_length=30)
    customer_id: int
    warehouse_id: int
    order_id: int | None = None
    rows: list[RowIn]


class InvoiceOut(ORM):
    id: int
    number: str
    date: datetime
    customer_id: int
    order_id: int | None
    warehouse_id: int
    comment: str
    status: str
    pay_due: datetime | None = None
    driver: str = ""
    vehicle: str = ""
    rows: list[RowOut]
    total: float = 0


class ReceiptIn(DocBase):
    supplier_id: int
    warehouse_id: int
    rows: list[RowIn]


class ReceiptOut(ORM):
    id: int
    number: str
    date: datetime
    supplier_id: int
    warehouse_id: int
    comment: str
    status: str
    rows: list[RowOut]
    total: float = 0


class ProdRowIn(BaseModel):
    item_id: int
    qty: float = Field(default=0, ge=0)        # good units
    scrap: float = Field(default=0, ge=0)      # spoiled units (materials are used, nothing is added to stock)

    @model_validator(mode="after")
    def _something(self):
        if self.qty + self.scrap <= 0:
            raise ValueError("qty or scrap must be above zero")
        return self


class ProdRowOut(ORM):
    item_id: int
    qty: float
    scrap: float = 0


class ProductionIn(DocBase):
    warehouse_id: int
    rows: list[ProdRowIn]
    worker_ids: list[int] = []                 # the crew that made it (pay is shared equally)


class ConsumptionOut(ORM):
    material_id: int
    qty: float


class ProductionOut(ORM):
    id: int
    number: str
    date: datetime
    warehouse_id: int
    comment: str
    status: str
    rows: list[ProdRowOut]
    consumption: list[ConsumptionOut]
    worker_ids: list[int] = []
    labour: float = 0


class AdjRowIn(BaseModel):
    item_id: int
    qty: float = Field(ge=0)       # count: counted quantity; write-off: quantity written off


class AdjustIn(BaseModel):
    date: datetime
    kind: str = Field(pattern="^(count|writeoff)$")
    warehouse_id: int
    reason: str = Field(default="", pattern="^(|scrap|damage|loss|expired|other)$")
    comment: str = ""
    rows: list[AdjRowIn]


class AdjRowOut(ORM):
    item_id: int
    system_qty: float
    qty: float
    delta: float


class AdjustOut(ORM):
    id: int
    number: str
    date: datetime
    kind: str
    warehouse_id: int
    reason: str
    comment: str
    status: str
    rows: list[AdjRowOut]
