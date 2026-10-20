"""Get back into the main administrator account (forgotten password, lost authenticator). Runs only on the server, by someone who can
open a shell there, so it needs no other login.

    docker compose exec api python -m app.tools.reset_owner                 # asks for a new password (typed twice, not shown)
    docker compose exec api python -m app.tools.reset_owner --generate      # makes a strong password and shows it once
    docker compose exec api python -m app.tools.reset_owner --reset-2fa     # also turns the authenticator code off (set it up again after signing in)
    docker compose exec api python -m app.tools.reset_owner --username muhammadrizo --make-owner   # name another account the main one

It also reactivates the account, makes it an administrator and signs it out everywhere. The password is never written to a file
or a log. If sign-in is still refused as «too many attempts», wait a few minutes or run `docker compose restart api`."""
import argparse
import getpass
import secrets
import string
import sys

import app.models  # noqa: F401
from app.core import passwords
from app.core.audit import record
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User, UserSession


def generate() -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        p = "".join(secrets.choice(alphabet) for _ in range(16))
        if passwords.problem(p) is None:
            return p


def recover(db, password: str, username: str | None = None, reset_2fa: bool = False, make_owner: bool = False) -> User:
    u = db.query(User).filter(User.username == username.strip().lower()).first() if username else db.query(User).filter(User.is_owner).first()
    if not u:
        raise SystemExit("no such account" if username else "no main administrator is marked; use --username NAME --make-owner")
    why = passwords.problem(password, u.username)
    if why:
        raise SystemExit(f"password refused: {passwords.MESSAGES[why]}")
    if make_owner:
        db.query(User).filter(User.is_owner).update({"is_owner": False})
        u.is_owner = True
    elif not u.is_owner:
        raise SystemExit(f"«{u.username}» is not the main administrator (add --make-owner to name it)")
    u.password_hash = hash_password(password)
    u.is_active, u.role = True, "admin"
    if reset_2fa:
        u.totp_enabled, u.totp_secret, u.totp_last_step = False, None, 0
    for s in db.query(UserSession).filter(UserSession.user_id == u.id, UserSession.revoked.is_(False)):
        s.revoked = True
    record(db, u, "update", "users", u.id, u.username, {"recovery": "password reset on the server" + (", 2fa off" if reset_2fa else "")})
    db.commit()
    return u


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--username", help="account to recover (default: the main administrator)")
    ap.add_argument("--generate", action="store_true", help="make a random password and show it once")
    ap.add_argument("--reset-2fa", action="store_true")
    ap.add_argument("--make-owner", action="store_true", help="name this account the main administrator")
    a = ap.parse_args()
    if a.generate:
        pw = generate()
    else:
        pw = getpass.getpass("New password: ")
        if pw != getpass.getpass("Again: "):
            sys.exit("the two passwords differ, nothing changed")
    with SessionLocal() as s:
        u = recover(s, pw, a.username, a.reset_2fa, a.make_owner)
    print(f"done: «{u.username}» can sign in with the new password" + (" (authenticator code is off)" if a.reset_2fa else ""))
    if a.generate:
        print("password:", pw, "\n(shown once: save it somewhere safe, away from the server)")
