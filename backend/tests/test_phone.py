import pytest

from app.core.phone import normalize_phone


@pytest.mark.parametrize("raw,want", [
    ("+998901234567", "+998-90-123-45-67"), ("998 90 123 45 67", "+998-90-123-45-67"), ("90-123-45-67", "+998-90-123-45-67"),
    ("(90) 123 45 67", "+998-90-123-45-67"), ("+998-90-123-45-67", "+998-90-123-45-67"), ("", ""), (None, ""), ("  ", ""),
    ("+7 999 123 45 67", "+7 999 123 45 67"), ("Ali, after 5", "Ali, after 5"), ("+998-90-12", "+998-90-12")])
def test_normalize_phone(raw, want):
    assert normalize_phone(raw) == want


def test_every_place_that_saves_a_number_uses_the_format(ctx):
    c = ctx.post("/customers", {"name": "Fmt Customer", "phone": "901234567"}).json()
    assert c["phone"] == "+998-90-123-45-67"
    s = ctx.post("/suppliers", {"name": "Fmt Supplier", "phone": "+998 93 555 00 11"}).json()
    assert s["phone"] == "+998-93-555-00-11"
    w = ctx.post("/workers", {"name": "Fmt Worker", "position": "x", "phone": "998971112233"}).json()
    assert w["phone"] == "+998-97-111-22-33"
    up = ctx.c.put(f"/api/customers/{c['id']}", json={"name": "Fmt Customer", "phone": "88 777 66 55"}, headers=ctx.h).json()
    assert up["phone"] == "+998-88-777-66-55"
