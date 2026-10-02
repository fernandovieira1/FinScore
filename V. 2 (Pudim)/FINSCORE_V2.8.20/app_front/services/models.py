"""Modelos ORM de autenticação, análises e governança do FinScore."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# Timestamp helper ---------------------------------------------------------

def _utcnow() -> datetime:
    """Return current UTC time without timezone info (SQLite friendly)."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


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


class AnalysisSequence(Base):
    """Contador transacional anual dos identificadores de análise."""

    __tablename__ = "analysis_sequences"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AnalysisDossier(Base):
    """Registro funcional persistente de uma execução do FinScore."""

    __tablename__ = "analysis_dossiers"
    __table_args__ = (
        UniqueConstraint("analysis_id", name="uq_analysis_dossier_id"),
        UniqueConstraint("analysis_fingerprint", name="uq_analysis_fingerprint"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    analysis_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    owner_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    tomador_nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tomador_cnpj: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="em_elaboracao")
    schema_version: Mapped[str] = mapped_column(String(24), nullable=False, default="1.0")
    recommendation_code: Mapped[str] = mapped_column(String(32), nullable=False)
    methodology_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reported_data_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    used_data_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    governance_signature: Mapped[str] = mapped_column(String(64), nullable=False)
    governance_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    functional_dossier_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    document_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class GovernanceEventRecord(Base):
    """Evento imutável e ordenável do fluxo de governança."""

    __tablename__ = "governance_event_records"
    __table_args__ = (UniqueConstraint("event_id", name="uq_governance_event_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_dossier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_order: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    responsible: Mapped[str] = mapped_column(String(255), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class GovernanceSignatureRecord(Base):
    """Comprovante eletrônico associado a manifestação ou deliberação."""

    __tablename__ = "governance_signature_records"
    __table_args__ = (UniqueConstraint("event_id", name="uq_governance_signature_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_dossier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    signer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    signer_role: Mapped[str] = mapped_column(String(32), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    signed_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="registro_autenticado"
    )


class CreditRoleAssignment(Base):
    """Perfil adicional para usuários autorizados a registrar decisão de alçada."""

    __tablename__ = "credit_role_assignments"
    __table_args__ = (UniqueConstraint("email", "role", name="uq_credit_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class TechnicalTelemetryRecord(Base):
    """Telemetria operacional restrita, fisicamente separada do dossiê funcional."""

    __tablename__ = "technical_telemetry_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_dossier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


__all__ = [
    "User",
    "SessionToken",
    "PasswordResetToken",
    "AnalysisSequence",
    "AnalysisDossier",
    "GovernanceEventRecord",
    "GovernanceSignatureRecord",
    "CreditRoleAssignment",
    "TechnicalTelemetryRecord",
]
