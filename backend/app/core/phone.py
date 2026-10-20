"""One phone format for the whole system: +998-90-123-45-67."""
import re


def normalize_phone(value: str | None) -> str:
    """Uzbek numbers in any common spelling become +998-XX-XXX-XX-XX; anything else (a foreign number, a note) is kept as typed."""
    s = (value or "").strip()
    if not s:
        return ""
    d = re.sub(r"\D", "", s)
    if d.startswith("998") and len(d) == 12:
        d = d[3:]
    if len(d) == 9:
        return f"+998-{d[:2]}-{d[2:5]}-{d[5:7]}-{d[7:]}"
    return s
