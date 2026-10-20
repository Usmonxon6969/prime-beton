from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(16))  # admin director prod wh sales acc
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")   # the main administrator: other users neither see nor change this account
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)      # encrypted, set while 2FA is being set up or on
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    totp_last_step: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # last accepted time step: a code works once

    grants: Mapped[list["PremiumGrant"]] = relationship(lazy="selectin", cascade="all, delete-orphan")

    @property
    def features(self) -> list[str]:
        """Paid features this user may use right now. The main administrator has all of them."""
        from app.core import premium
        return premium.active_features(self)

    @property
    def premium(self) -> list[dict]:
        """Every grant of this user with its dates and what is left of it (for the users page and the meeting page)."""
        from app.core import premium
        return premium.info(self)


class PremiumGrant(Base):
    """A paid feature the main administrator switched on for one user: valid for a time, with a limited number of uses."""
    __tablename__ = "premium_grants"
    __table_args__ = (UniqueConstraint("user_id", "feature"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    feature: Mapped[str] = mapped_column(String(32))
    granted_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    uses_limit: Mapped[int] = mapped_column(Integer, default=0)
    used: Mapped[str] = mapped_column(String(400), default="")      # what was already used, comma separated (the months of the meetings held)


class UserSession(Base):
    """One signed-in browser. The token carries its id; revoking the row signs that browser out at once."""
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ip: Mapped[str] = mapped_column(String(64), default="")
    agent: Mapped[str] = mapped_column(String(200), default="")
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
