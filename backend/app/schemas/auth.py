from pydantic import BaseModel

from app.schemas.common import ORM


class LoginIn(BaseModel):
    username: str
    password: str
    otp: str | None = None          # the 6-digit code, only for accounts with two-factor sign-in


class GrantOut(BaseModel):
    feature: str
    active: bool
    expires_at: str
    uses_limit: int
    uses_left: int
    used: list[str] = []


class UserOut(ORM):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool = True
    totp_enabled: bool = False
    features: list[str] = []          # paid features this user may use right now
    premium: list[GrantOut] = []      # the paid features switched on for this user: until when, how many uses are left


class MeOut(UserOut):
    home: str
    levels: dict[str, int]
    totp_enabled: bool = False
    must_setup_2fa: bool = False
    owner: bool = False               # the main administrator (the only one who switches premium features on)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: MeOut


class UserIn(BaseModel):
    username: str
    password: str
    full_name: str
    role: str


class UserPatch(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None
    premium: dict | None = None         # main administrator only: {"feature": "meeting", "on": true|false} switches a paid feature on (a new period, full uses) or off
    reset_2fa: bool = False        # administrator: switch off a lost phone's two-factor sign-in


class PasswordIn(BaseModel):
    old_password: str
    new_password: str


class SessionOut(BaseModel):
    id: str
    created_at: str
    last_seen: str
    ip: str
    agent: str
    current: bool


class TotpSetupOut(BaseModel):
    secret: str
    uri: str
    qr_svg: str


class TotpEnableIn(BaseModel):
    code: str


class TotpDisableIn(BaseModel):
    password: str
    code: str
