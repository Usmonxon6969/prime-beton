from decimal import Decimal

from app.models import Item, Norm, Unit
from app.tools import split_rebar as sr


def _mat(db, name):
    kg = db.query(Unit).filter(Unit.name == "kg").one()
    m = Item(kind="material", name_uz=name, name_ru=name, name_en=name, unit_id=kg.id, min_stock=Decimal(0))
    db.add(m)
    db.flush()
    return m


def _prod(db, name, mat, qty):
    dona = db.query(Unit).filter(Unit.name == "dona").one()
    p = Item(kind="product", name_uz=name, name_ru=name, name_en=name, unit_id=dona.id, min_stock=Decimal(0))
    db.add(p)
    db.flush()
    db.add(Norm(product_id=p.id, material_id=mat.id, qty=Decimal(qty)))
    return p


def test_rebar_diameter_follows_slab_length(db_session):
    with db_session() as db:
        m12, m14, m16 = _mat(db, "Арматура 12мм"), _mat(db, "Арматура 14мм"), _mat(db, "Арматура 16мм")
        cem = _mat(db, "Цемент X")
        cases = {"2ПК 21*12": 12, "2ПК 49*10": 12, "2ПК 49,5*12": 12, "2ПК 50*12": 14, "2ПК 65*10": 14, "2ПК 65,5*12": 16, "2ПК 66*12": 16, "2ПК 73*10": 16}
        prods = {n: _prod(db, n, m12, 40 + i) for i, n in enumerate(cases)}
        pole = _prod(db, "Опора СВ 110-3,5", m12, 57)
        db.add(Norm(product_id=prods["2ПК 21*12"].id, material_id=cem.id, qty=Decimal(180)))
        db.commit()
        mats, rows, untouched = sr.plan(db)
        assert len(rows) == 8 and [u.name_ru for u in untouched] == ["Опора СВ 110-3,5"]
        assert sr.apply(db) == {"slabs checked": 8, "changed": 5}                # 12 mm slabs were already right
        for n, d in cases.items():
            rb = db.query(Norm).filter(Norm.product_id == prods[n].id, Norm.material_id.in_([m12.id, m14.id, m16.id])).all()
            assert [x.material_id for x in rb] == [{12: m12, 14: m14, 16: m16}[d].id], n
            assert rb[0].qty == 40 + list(cases).index(n)                           # the quantity never changes
        assert db.query(Norm).filter(Norm.product_id == prods["2ПК 21*12"].id, Norm.material_id == cem.id).one().qty == 180      # other materials untouched
        assert db.query(Norm).filter(Norm.product_id == pole.id).one().material_id == m12.id                                     # not a slab
        assert sr.apply(db)["changed"] == 0                                                                                      # safe to run twice


def test_split_needs_the_three_rebar_materials(db_session):
    import pytest
    with db_session() as db:
        _mat(db, "Арматура 12мм")
        with pytest.raises(SystemExit):
            sr.plan(db)
