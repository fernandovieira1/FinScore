"""ORM models for the FinScore authentication subsystem."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# Timestamp helper ---------------------------------------------------------

def _utcnow() -> datetime:
    """Return current UTC time without timezone info (SQLite friendly)."""

    return datetime.utcnow()


class User(Base):
    """Application user able to authenticate into FinScore."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sessions: Mapped[list[SessionToken]] = relationship(
        "SessionToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - repr debugging helper
        return f"<User id={self.id} email={self.email!r}>"


class SessionToken(Base):
    """Persistent session token for the "manter sessão ativa" feature."""

    __tablename__ = "session_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_session_token"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SessionToken user_id={self.user_id} token={self.token[:6]}...>"


class PasswordResetToken(Base):
    """Token registry for password reset requests."""

    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_password_reset_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="reset_tokens")

    def mark_used(self) -> None:
        """Flag the token as used, preventing reuse."""

        self.used_at = _utcnow()

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PasswordResetToken user_id={self.user_id} expires_at={self.expires_at}>"


__all__ = [
    "User",
    "SessionToken",
    "PasswordResetToken",
]
