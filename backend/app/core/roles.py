"""Role matrix: section -> access level (0 none, 1 view, 2 edit).

Sections: set dash prod wh items mats specs cus ord inv sup rec bank cash adj (stock counts and write-offs) pay (workers and pay).
Mirrors the roles shown in the frontend so the server enforces what the UI hides.
"""
SECTIONS = ["set", "dash", "prod", "wh", "items", "mats", "specs", "cus", "ord", "inv", "sup", "rec", "bank", "cash", "adj", "pay"]

ROLES: dict[str, dict[str, int]] = {
    "admin": {s: 2 for s in SECTIONS},
    "director": {s: 1 for s in SECTIONS},
    "prod": {"dash": 1, "prod": 2, "wh": 1, "items": 2, "mats": 2, "specs": 2, "adj": 2, "pay": 1},
    "wh": {"dash": 1, "prod": 1, "wh": 2, "items": 1, "mats": 1, "ord": 1, "inv": 2, "sup": 1, "rec": 2, "adj": 2},
    "sales": {"dash": 1, "wh": 1, "items": 1, "cus": 2, "ord": 2, "inv": 2},
    "acc": {"dash": 1, "cus": 1, "ord": 1, "inv": 1, "sup": 1, "rec": 1, "bank": 2, "cash": 2, "adj": 1, "pay": 2},
}
HOME = {"admin": "dash", "director": "dash", "prod": "prod", "wh": "wh", "sales": "ord", "acc": "bank"}


def level(role: str, section: str) -> int:
    return ROLES.get(role, {}).get(section, 0)
