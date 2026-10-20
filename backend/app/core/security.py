"""Password hashing (scrypt, standard library) and JWT access tokens."""
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, dk_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        salt, dk = base64.b64decode(salt_b64), base64.b64decode(dk_b64)
        test = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
        return hmac.compare_digest(dk, test)
    except Exception:
        return False


def create_token(user_id: int, sid: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "sid": sid, "exp": exp}, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> tuple[int, str] | None:
    """(user id, session id) of a valid token, else None."""
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return int(data["sub"]), str(data.get("sid", ""))
    except Exception:
        return None
