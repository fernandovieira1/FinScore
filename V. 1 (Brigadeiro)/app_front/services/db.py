"""Database utilities for FinScore authentication layer.

This module exposes the SQLAlchemy engine, session factory and helper
utilities used by the authentication subsystem. The goal is to keep the
ORM configuration isolated so the rest of the application can import
lightweight helpers without needing to understand engine details.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# SQLite database stored alongside the Streamlit frontend codebase so it can
# be easily backed up with the rest of the project files.
_DB_FILENAME = "finscore_auth.db"
_DB_PATH = Path(__file__).resolve().parents[1] / _DB_FILENAME


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# Turn on future style engine (SQLAlchemy 2.0) with safe SQLite settings.
engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
    future=True,
    pool_pre_ping=True,
)

# Sessions are configured with autocommit disabled to guarantee explicit
# transaction handling. Expire-on-commit is disabled so callers can still
# read attributes after committing without implicit refreshes.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager that yields a SQLAlchemy session, committing on success
    and performing a rollback if an exception occurs. Typical usage::

        with get_session() as session:
            session.add(obj)

    Returns:
        Iterator yielding an active Session instance.
    """

    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create database tables if they do not exist."""

    # Local import avoids circular dependency when models import Base.
    from . import models  # noqa: F401  # pragma: no cover

    Base.metadata.create_all(bind=engine)


__all__ = ["Base", "engine", "get_session", "init_db", "SessionLocal"]
