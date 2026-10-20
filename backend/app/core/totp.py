"""Time-based one-time passwords (RFC 6238, the Google Authenticator / Microsoft Authenticator standard), standard library only.
The shared secret is stored encrypted with a key derived from SECRET_KEY, so a copy of the database alone does not reveal it."""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

STEP, DIGITS, WINDOW = 30, 6, 1          # 30-second codes, one step of clock drift either way


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _code(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    o = mac[-1] & 0x0F
    n = (struct.unpack(">I", mac[o:o + 4])[0] & 0x7FFFFFFF) % (10 ** DIGITS)
    return str(n).zfill(DIGITS)


def verify(secret: str, code: str, at: float | None = None) -> int | None:
    """The time step the code belongs to, or None. The caller remembers it so one code cannot be used twice."""
    code = (code or "").strip().replace(" ", "")
    if len(code) != DIGITS or not code.isdigit():
        return None
    now = int((at if at is not None else time.time()) // STEP)
    for d in range(-WINDOW, WINDOW + 1):
        if hmac.compare_digest(_code(secret, now + d), code):
            return now + d
    return None


def uri(secret: str, username: str, issuer: str = "Prime Beton") -> str:
    return f"otpauth://totp/{quote(issuer)}:{quote(username)}?secret={secret}&issuer={quote(issuer)}&digits={DIGITS}&period={STEP}"


def _fernet() -> Fernet:
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("totp|" + settings.secret_key).encode()).digest()))


def seal(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def unseal(blob: str) -> str | None:
    try:
        return _fernet().decrypt(blob.encode()).decode()
    except (InvalidToken, ValueError):
        return None


def qr_svg(text: str) -> str:
    import io

    import segno
    buf = io.BytesIO()
    segno.make(text, error="m").save(buf, kind="svg", scale=5, border=2, xmldecl=False, svgns=True, nl=False)
    return buf.getvalue().decode()
