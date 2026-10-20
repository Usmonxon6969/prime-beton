"""Password policy for accounts made or changed through the API (the first administrator of a fresh install is exempt)."""
import re

from fastapi import HTTPException

MIN_LEN = 10
COMMON = {"password", "parol", "qwerty", "12345678", "123456789", "1234567890", "admin123", "admin1234", "password1", "qwerty123",
          "11111111", "00000000", "letmein", "iloveyou", "primebeton", "prime-beton", "primestroy"}


def problem(password: str, username: str = "") -> str | None:
    """A short code for what is wrong with the password, or None when it is acceptable."""
    if len(password) < MIN_LEN:
        return "too_short"
    if not re.search(r"[A-Za-zА-Яа-яЎўҚқҒғҲҳ]", password) or not re.search(r"\d", password):
        return "need_letter_and_digit"
    low = password.lower()
    if low in COMMON or (username and username.lower() in low):
        return "too_common"
    return None


MESSAGES = {
    "too_short": f"Use at least {MIN_LEN} characters",
    "need_letter_and_digit": "Use letters and at least one digit",
    "too_common": "This password is too easy to guess: avoid common words and your username",
}


def check(password: str, username: str = "") -> None:
    p = problem(password, username)
    if p:
        raise HTTPException(422, {"code": "weak_password", "message": MESSAGES[p], "params": {"reason": p, "min": MIN_LEN}})
