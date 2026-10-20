"""Our own details for printed documents (letterhead of the waybill). Everybody signed in may read them, only the administrator changes them."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import current_user, need
from app.db.session import get_db
from app.models import Company, User

router = APIRouter(tags=["company"])
FIELDS = ("name", "address", "postcode", "okonh", "account", "bank", "mfo", "inn", "phone", "receive_note")
DEFAULTS = {"name": "Prime Beton", "receive_note": "Plitalarni butun qabul qilib oldim!"}


class CompanyIO(BaseModel):
    name: str = Field("", max_length=160)
    address: str = Field("", max_length=240)
    postcode: str = Field("", max_length=20)
    okonh: str = Field("", max_length=30)
    account: str = Field("", max_length=40)
    bank: str = Field("", max_length=200)
    mfo: str = Field("", max_length=20)
    inn: str = Field("", max_length=20)
    phone: str = Field("", max_length=60)
    receive_note: str = Field("", max_length=300)


def get_company(db: Session) -> dict:
    row = db.get(Company, 1)
    out = {k: (getattr(row, k, "") if row else "") for k in FIELDS}
    if row is None:                                   # nothing entered yet: sensible starting text
        out.update(DEFAULTS)
    return out


@router.get("/company", response_model=CompanyIO)
def read_company(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return get_company(db)


@router.put("/company", response_model=CompanyIO)
def write_company(body: CompanyIO, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    row = db.get(Company, 1)
    if row is None:
        row = Company(id=1)
        db.add(row)
    for k in FIELDS:
        setattr(row, k, getattr(body, k).strip())
    db.commit()
    return get_company(db)
