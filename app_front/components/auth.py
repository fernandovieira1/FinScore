"""Authentication helpers for the FinScore overlay login system."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app_front.services.db import get_session, init_db
from app_front.services.models import PasswordResetToken, SessionToken, User

# ---------------------------------------------------------------------------
# Password hashing configuration
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token serializer
_SECRET_KEY = "finscore-auth-secret"
_SALT_SESSION = "finscore-session"
_SALT_RESET = "finscore-reset"
_serializer = URLSafeTimedSerializer(_SECRET_KEY)

# Token expirations
SESSION_TOKEN_EXPIRES_HOURS = 8
RESET_TOKEN_EXPIRES_MINUTES = 30


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------
import logging
logger = logging.getLogger("finscore.auth")

def log_bcrypt_versions():
    try:
        import bcrypt
        import passlib
        logger.info(f"bcrypt version: {getattr(bcrypt, '__version__', str(bcrypt))}")
        logger.info(f"passlib version: {getattr(passlib, '__version__', str(passlib))}")
    except Exception as e:
        logger.warning(f"Erro ao obter versão do bcrypt/passlib: {e}")

def hash_password(raw_password: str) -> str:
    """Hash a password usando bcrypt. Trunca para 72 bytes (não caracteres)."""
    raw_password_bytes = raw_password.encode("utf-8")[:72]
    raw_password = raw_password_bytes.decode("utf-8", errors="ignore")
    logger.debug(f"Hashing password (len={len(raw_password_bytes)} bytes)")
    try:
        hashed = _pwd_context.hash(raw_password)
        logger.debug("Password hashed com sucesso.")
        return hashed
    except Exception as e:
        logger.error(f"Erro ao hashear senha: {e}")
        raise


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """Verify a bcrypt hash."""
    try:
        result = _pwd_context.verify(raw_password, hashed_password)
        logger.debug(f"Verificação de senha: {result}")
        return result
    except Exception as e:
        logger.error(f"Erro ao verificar senha: {e}")
        return False


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------
def create_user(email: str, password: str) -> User:
    """
    Create a new application user.

    Raises:
        ValueError: if the email or password is invalid.
        IntegrityError: if a user already exists with the given email.
    """

    email = email.strip().lower()
    if not email:
        raise ValueError("E-mail é obrigatório.")
    if len(password) < 8:
        raise ValueError("Senha deve ter pelo menos 8 caracteres.")
    # Não trunca aqui, truncamento é feito no hash_password
    hashed = hash_password(password)

    with get_session() as session:
        user = User(email=email, hashed_password=hashed)
        session.add(user)
        try:
            session.flush()
        except IntegrityError as exc:
            session.rollback()
            # Re-raise a clean IntegrityError without potentially None orig reference.
            raise IntegrityError("E-mail já está em uso.", exc.params, exc.orig or Exception("IntegrityError")) from exc
        return user


def authenticate(email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""

    email = (email or "").strip().lower()

    with get_session() as session:
        result = session.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return None
        user.last_login_at = datetime.utcnow()
        session.add(user)
        # session will commit automatically via context manager
        return user


# ---------------------------------------------------------------------------
# Session tokens
# ---------------------------------------------------------------------------
def _issue_session_token(user: User, remember: bool = False) -> SessionToken:
    """Create and persist a session token for the user."""
    logger.info(f"Emitindo session token para user_id={user.id} (remember=True forçado para debug)")
    # Força remember=True para depuração de persistência
    remember = True
    lifetime = SESSION_TOKEN_EXPIRES_HOURS
    if remember:
        lifetime = SESSION_TOKEN_EXPIRES_HOURS * 3

    expires_at = datetime.utcnow() + timedelta(hours=lifetime)
    token = _serializer.dumps({"user_id": user.id, "exp": expires_at.timestamp()}, salt=_SALT_SESSION)

    session_token = SessionToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )

    with get_session() as session:
        session.add(session_token)
        session.flush()
        logger.info(f"Session token criado e persistido para user_id={user.id}")
        return session_token


def create_session_token(user: User, remember: bool = False) -> str:
    """Public helper to issue session tokens."""

    session_token = _issue_session_token(user, remember=remember)
    return session_token.token


def verify_token(token: str, max_age_hours: int | None = None) -> Optional[User]:
    """Verify a session token and return the associated user."""

    import logging
    logger = logging.getLogger("finscore.auth")
    logger.debug(f"[verify_token] Iniciando validação do token: {token}")

    if not token:
        logger.warning("[verify_token] Token vazio recebido.")
        return None

    try:
        data = _serializer.loads(token, salt=_SALT_SESSION, max_age=(max_age_hours or SESSION_TOKEN_EXPIRES_HOURS) * 3600)
        logger.debug(f"[verify_token] Dados decodificados do token: {data}")
    except BadTimeSignature:
        logger.error("[verify_token] Token expirado ou assinatura inválida.")
        return None
    except BadSignature:
        logger.error("[verify_token] Assinatura do token inválida.")
        return None

    user_id = data.get("user_id")
    exp_ts = data.get("exp")
    logger.debug(f"[verify_token] user_id={user_id}, exp_ts={exp_ts}")

    if not user_id or not exp_ts:
        logger.error("[verify_token] Dados do token incompletos: user_id ou exp ausentes.")
        return None
    if datetime.utcnow().timestamp() > float(exp_ts):
        logger.warning("[verify_token] Token expirado com base no timestamp.")
        return None

    with get_session() as session:
        stmt = select(SessionToken).where(SessionToken.token == token)
        session_token = session.execute(stmt).scalar_one_or_none()
        if not session_token:
            logger.warning("[verify_token] Token não encontrado no banco de dados.")
            return None
        if session_token.expires_at < datetime.utcnow():
            logger.info("[verify_token] Token expirado no banco de dados. Removendo.")
            session.delete(session_token)
            session.commit()
            return None
        user = session.get(User, user_id)
        logger.debug(f"[verify_token] Usuário associado ao token: {user}")
        return user


def revoke_session_token(token: str) -> None:
    """Delete a stored session token."""

    if not token:
        return

    with get_session() as session:
        stmt = select(SessionToken).where(SessionToken.token == token)
        session_token = session.execute(stmt).scalar_one_or_none()
        if session_token:
            session.delete(session_token)


# ---------------------------------------------------------------------------
# Password reset flow
# ---------------------------------------------------------------------------
def init_password_reset(email: str) -> Optional[str]:
    """Create a password reset token and return it (simulated delivery)."""

    email = (email or "").strip().lower()
    if not email:
        return None

    with get_session() as session:
        user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            return None

        expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRES_MINUTES)
        token_plain = _serializer.dumps({"user_id": user.id, "type": "reset", "exp": expires_at.timestamp()}, salt=_SALT_RESET)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_password(token_plain),
            expires_at=expires_at,
        )
        session.add(reset_token)
        session.flush()
        return token_plain


def complete_password_reset(email: str, token: str, new_password: str) -> bool:
    """Complete a password reset flow."""

    if not token:
        return False
    email = (email or "").strip().lower()
    if not email or len(new_password) < 8:
        return False

    try:
        data = _serializer.loads(token, salt=_SALT_RESET, max_age=RESET_TOKEN_EXPIRES_MINUTES * 60)
    except BadTimeSignature:
        return False
    except BadSignature:
        return False

    user_id = data.get("user_id")
    if not user_id:
        return False

    with get_session() as session:
        user = session.execute(select(User).where(User.id == user_id, User.email == email)).scalar_one_or_none()
        if not user:
            return False

        stmt = select(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
        token_entry = session.execute(stmt).scalar_one_or_none()
        if not token_entry or token_entry.expires_at < datetime.utcnow():
            return False

        if not verify_password(token, token_entry.token_hash):
            return False

        token_entry.mark_used()
        user.hashed_password = hash_password(new_password)
        session.add_all([user, token_entry])
        return True


# Ensure database tables exist on import.
init_db()


__all__ = [
    "create_user",
    "authenticate",
    "create_session_token",
    "verify_token",
    "revoke_session_token",
    "hash_password",
    "init_password_reset",
    "complete_password_reset",
    "log_bcrypt_versions",
]
