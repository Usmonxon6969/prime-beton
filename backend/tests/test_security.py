"""Password policy, server-side sessions and two-factor sign-in."""
import time

from app.core import passwords, totp
from app.core.config import settings
from tests.conftest import login


def test_password_policy_rules():
    assert passwords.problem("short1") == "too_short"
    assert passwords.problem("onlylettersxx") == "need_letter_and_digit"
    assert passwords.problem("1234567890123") == "need_letter_and_digit"
    assert passwords.problem("Admin123", "admin") == "too_short"
    assert passwords.problem("myadmin12345", "admin") == "too_common"       # contains the username
    assert passwords.problem("qwerty123", "x") == "too_short"
    assert passwords.problem("Bet0n-Zavod-2026", "ali") is None
    assert passwords.problem("Бетон-завод-2026") is None


def test_weak_password_is_refused_with_reason(client, admin):
    r = client.post("/api/auth/users", json={"username": "u1", "password": "abcdefghij", "full_name": "U", "role": "wh"}, headers=admin)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "weak_password" and r.json()["detail"]["params"]["reason"] == "need_letter_and_digit"


def test_logout_and_revoke_sessions(client):
    a = login(client)
    b = login(client)
    sess = client.get("/api/auth/sessions", headers=a).json()
    assert len(sess) == 2 and sum(s["current"] for s in sess) == 1
    other = [s for s in sess if not s["current"]][0]
    assert client.delete(f"/api/auth/sessions/{other['id']}", headers=a).status_code == 204
    assert client.get("/api/auth/me", headers=b).status_code == 401       # that browser is signed out at once
    assert client.get("/api/auth/me", headers=a).status_code == 200
    assert client.post("/api/auth/logout", headers=a).status_code == 204
    assert client.get("/api/auth/me", headers=a).status_code == 401


def test_password_change_signs_out_other_browsers(client):
    a = login(client, "sotuv", "sotuv123")
    b = login(client, "sotuv", "sotuv123")
    r = client.post("/api/auth/password", json={"old_password": "sotuv123", "new_password": "Bet0n-Zavod-77"}, headers=a)
    assert r.status_code == 204
    assert client.get("/api/auth/me", headers=a).status_code == 200
    assert client.get("/api/auth/me", headers=b).status_code == 401


def test_users_cannot_revoke_each_others_sessions(client):
    a = login(client)
    b = login(client, "sotuv", "sotuv123")
    sid = client.get("/api/auth/sessions", headers=b).json()[0]["id"]
    assert client.delete(f"/api/auth/sessions/{sid}", headers=a).status_code == 404


def test_totp_matches_rfc6238_vector():
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"          # "12345678901234567890" in base32
    assert totp._code(secret, 59 // 30) == "287082"
    assert totp.verify(secret, "287082", at=59) == 1
    assert totp.verify(secret, "000000", at=59) is None


def _code_now(secret):
    return totp._code(secret, int(time.time() // totp.STEP))


def test_two_factor_flow(client):
    h = login(client, "buxgalter", "buh123")
    r = client.post("/api/auth/2fa/setup", headers=h)
    assert r.status_code == 200 and r.json()["uri"].startswith("otpauth://totp/") and "<svg" in r.json()["qr_svg"]
    secret = r.json()["secret"]
    assert client.post("/api/auth/2fa/enable", json={"code": "000000"}, headers=h).status_code == 422
    code = _code_now(secret)
    assert client.post("/api/auth/2fa/enable", json={"code": code}, headers=h).status_code == 204
    assert client.get("/api/auth/me", headers=h).json()["totp_enabled"] is True
    # sign-in now needs the code
    r = client.post("/api/auth/login", json={"username": "buxgalter", "password": "buh123"})
    assert r.status_code == 401 and r.json()["detail"]["code"] == "otp_required"
    r = client.post("/api/auth/login", json={"username": "buxgalter", "password": "buh123", "otp": "123456"})
    assert r.status_code == 401 and r.json()["detail"]["code"] == "bad_otp"
    # the code that enabled it cannot be replayed
    r = client.post("/api/auth/login", json={"username": "buxgalter", "password": "buh123", "otp": code})
    assert r.status_code == 401 and r.json()["detail"]["code"] == "bad_otp"


def test_totp_secret_not_stored_in_clear(client, db_session):
    h = login(client, "buxgalter", "buh123")
    secret = client.post("/api/auth/2fa/setup", headers=h).json()["secret"]
    from app.models import User
    with db_session() as s:
        stored = s.query(User).filter(User.username == "buxgalter").one().totp_secret
    assert stored and secret not in stored and totp.unseal(stored) == secret


def test_admin_can_reset_lost_phone(client, admin, db_session):
    from app.models import User
    h = login(client, "buxgalter", "buh123")
    secret = client.post("/api/auth/2fa/setup", headers=h).json()["secret"]
    client.post("/api/auth/2fa/enable", json={"code": _code_now(secret)}, headers=h)
    uid = client.get("/api/auth/me", headers=h).json()["id"]
    assert client.patch(f"/api/auth/users/{uid}", json={"reset_2fa": True}, headers=admin).status_code == 200
    assert client.post("/api/auth/login", json={"username": "buxgalter", "password": "buh123"}).status_code == 200


def test_required_roles_must_set_up_before_working(client, monkeypatch):
    monkeypatch.setattr(settings, "require_2fa_roles", "acc")
    h = login(client, "buxgalter", "buh123")
    me = client.get("/api/auth/me", headers=h).json()
    assert me["must_setup_2fa"] is True
    r = client.get("/api/customers", headers=h)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "2fa_required"
    secret = client.post("/api/auth/2fa/setup", headers=h).json()["secret"]       # /auth/* stays open so setup is possible
    client.post("/api/auth/2fa/enable", json={"code": _code_now(secret)}, headers=h)
    assert client.get("/api/customers", headers=h).status_code == 200
    r = client.post("/api/auth/2fa/disable", json={"password": "buh123", "code": "123456"}, headers=h)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "2fa_mandatory"
