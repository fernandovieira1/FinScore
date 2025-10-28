"""Session guards for the FinScore authentication layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import streamlit as st

try:
    from streamlit_cookies_manager import EncryptedCookieManager
except ModuleNotFoundError:  # pragma: no cover
    EncryptedCookieManager = None  # type: ignore[assignment]

from .auth import create_session_token, revoke_session_token, verify_token
from app_front.services.models import User

SESSION_KEY = "finscore_session_token"
SESSION_EXP_KEY = "finscore_session_exp"
SESSION_REMEMBER_KEY = "finscore_session_remember"
COOKIE_TOKEN_KEY = "finscore_session_cookie"
COOKIE_EXP_KEY = "finscore_session_cookie_exp"
COOKIE_MANAGER_STATE_KEY = "_finscore_cookie_manager"
PENDING_COOKIE_SET_KEY = "_finscore_cookie_pending_set"
PENDING_COOKIE_CLEAR_KEY = "_finscore_cookie_pending_clear"
_COOKIE_MANAGER_INSTANCE: Optional[Any] = None


def _get_cookie_password() -> str:
    """Retorna um password fixo para o CookieManager."""
    return "finscore-cookie-secret"


def _create_cookie_manager() -> Any:
    from streamlit_cookies_manager import EncryptedCookieManager
    st.write("[DEBUG] Inicializando EncryptedCookieManager.")
    try:
        manager = EncryptedCookieManager(password=_get_cookie_password())
        st.write("[DEBUG] CookieManager criado com sucesso.")
        return manager
    except Exception as e:
        st.write(f"[ERROR] Falha ao criar CookieManager: {e}")
        return None


def _get_cookie_manager() -> Any:
    global _COOKIE_MANAGER_INSTANCE

    if _COOKIE_MANAGER_INSTANCE is not None:
        st.write("[DEBUG] CookieManager já inicializado.")
        return _COOKIE_MANAGER_INSTANCE

    manager = st.session_state.get(COOKIE_MANAGER_STATE_KEY)
    if manager is None:
        st.write("[DEBUG] Criando novo CookieManager.")
        manager = _create_cookie_manager()
        if manager:
            st.session_state[COOKIE_MANAGER_STATE_KEY] = manager
        else:
            st.write("[ERROR] CookieManager não pôde ser criado.")
    else:
        st.write("[DEBUG] Recuperando CookieManager do session_state.")

    if manager:
        st.write(f"[DEBUG] Estado do CookieManager: ready={manager.ready()}")
    else:
        st.write("[ERROR] CookieManager está nulo.")

    return manager


def _flush_pending_cookie_ops(manager: Any) -> None:
    if manager is None:
        raise ValueError("CookieManager não foi inicializado corretamente.")

    if not manager.ready():
        raise RuntimeError("CookieManager não está pronto para operações.")

    should_clear = bool(st.session_state.pop(PENDING_COOKIE_CLEAR_KEY, False))
    pending_set = st.session_state.pop(PENDING_COOKIE_SET_KEY, None)
    changed = False

    if should_clear:
        if COOKIE_TOKEN_KEY in manager:
            del manager[COOKIE_TOKEN_KEY]
            changed = True
        if COOKIE_EXP_KEY in manager:
            del manager[COOKIE_EXP_KEY]
            changed = True

    if pending_set:
        token, exp_iso = pending_set
        try:
            datetime.fromisoformat(exp_iso)
        except ValueError:
            exp_iso = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        manager[COOKIE_TOKEN_KEY] = token
        manager[COOKIE_EXP_KEY] = exp_iso
        changed = True

    if changed:
        manager.save()


@dataclass
class AuthResult:
    """Structured result returned when checking authentication."""

    user: Optional[User]
    token: Optional[str]


def _current_session_expired() -> bool:
    exp_str = st.session_state.get(SESSION_EXP_KEY)
    if not exp_str:
        return True
    try:
        expires_at = datetime.fromisoformat(exp_str)
    except ValueError:
        return True
    return datetime.utcnow() >= expires_at


def require_auth() -> AuthResult:
    """Ensure the user is authenticated.

    If no valid token is found, returns AuthResult with None user. The caller
    should render the overlay and stop Streamlit execution until the login
    is completed.
    """

    import logging
    logger = logging.getLogger("finscore.guards")
    logger.debug(f"[require_auth] session_state inicial: {dict(st.session_state)}")
    token = st.session_state.get(SESSION_KEY)
    cookies = _get_cookie_manager()
    # Garanta que o componente de cookies esteja pronto antes de continuar
    if cookies is not None and not cookies.ready():
        logger.debug("[require_auth] Interrompendo execução para inicializar CookieManager.")
        st.stop()
    try:
        _flush_pending_cookie_ops(cookies)
        logger.debug("[require_auth] Operações de cookies realizadas com sucesso.")
    except ValueError as ve:
        logger.error(f"[require_auth] Erro ao realizar operações de cookies: {ve}")
        return AuthResult(user=None, token=None)
    except RuntimeError as re:
        logger.error(f"[require_auth] Erro ao realizar operações de cookies: {re}")
        return AuthResult(user=None, token=None)

    logger.debug(f"[require_auth] Após flush cookies: session_state={dict(st.session_state)}")
    if cookies is not None:
        ready = False
        try:
            ready = cookies.ready()
        except Exception as e:
            logger.debug(f"[require_auth] cookies.ready() lançou exceção: {e}")
        logger.debug(f"[require_auth] cookies prontos: {ready}")
        if ready:
            try:
                logger.debug(f"[require_auth] cookies keys: {list(cookies.keys())}")
            except Exception as e:
                logger.debug(f"[require_auth] cookies.keys() lançou exceção: {e}")
        else:
            logger.debug(f"[require_auth] cookies ainda não prontos para acesso a keys.")
    else:
        logger.debug("[require_auth] cookies é None")
    if not token and cookies.ready():
        cookie_token = cookies.get(COOKIE_TOKEN_KEY)
        logger.debug(f"[require_auth] cookie_token lido: {cookie_token}")
        if cookie_token:
            st.session_state[SESSION_KEY] = cookie_token
            token = cookie_token
            cookie_exp = cookies.get(COOKIE_EXP_KEY)
            if cookie_exp:
                st.session_state[SESSION_EXP_KEY] = cookie_exp
    remember = bool(st.session_state.get(SESSION_REMEMBER_KEY, False))
    logger.debug(f"[require_auth] token={token}, remember={remember}")
    if not token or _current_session_expired():
        logger.info("[require_auth] Token ausente ou sessão expirada. Limpando sessão e cookies.")
        st.session_state.pop(SESSION_KEY, None)
        st.session_state.pop(SESSION_EXP_KEY, None)
        st.session_state.pop(SESSION_REMEMBER_KEY, None)
        if cookies.ready():
            changed = False
            if COOKIE_TOKEN_KEY in cookies:
                del cookies[COOKIE_TOKEN_KEY]
                logger.debug("[require_auth] COOKIE_TOKEN_KEY removido.")
                changed = True
            if COOKIE_EXP_KEY in cookies:
                del cookies[COOKIE_EXP_KEY]
                logger.debug("[require_auth] COOKIE_EXP_KEY removido.")
                changed = True
            if changed:
                cookies.save()
                logger.debug("[require_auth] Cookies salvos após limpeza.")
        logger.info("[require_auth] Redirecionando para tela de login.")
        st.stop()
    user = verify_token(token)
    logger.debug(f"[require_auth] Resultado de verify_token: user={user}, token={token}")
    return AuthResult(user=user, token=token)


def store_session(user: User, remember: bool = False) -> str:
    """Persist session information in Streamlit session state."""

    import logging
    logger = logging.getLogger("finscore.guards")
    # Força remember=True para depuração
    remember = True
    token = create_session_token(user, remember=remember)
    st.session_state[SESSION_KEY] = token
    expires_at = datetime.utcnow() + timedelta(hours=8 if not remember else 24)
    st.session_state[SESSION_EXP_KEY] = expires_at.isoformat()
    st.session_state["finscore_user_email"] = user.email
    st.session_state[SESSION_REMEMBER_KEY] = remember

    cookies = _get_cookie_manager()
    exp_iso = expires_at.isoformat()
    logger.info(f"[store_session] Salvando cookie de sessão: token={token[:8]}..., exp={exp_iso}, remember={remember}")
    if cookies.ready():
        changed = False
        if remember:
            cookies[COOKIE_TOKEN_KEY] = token
            cookies[COOKIE_EXP_KEY] = exp_iso
            st.session_state.pop(PENDING_COOKIE_SET_KEY, None)
            changed = True
            logger.info("[store_session] Cookie de sessão salvo com sucesso (cookies.save()).")
        else:
            if COOKIE_TOKEN_KEY in cookies:
                del cookies[COOKIE_TOKEN_KEY]
                changed = True
            if COOKIE_EXP_KEY in cookies:
                del cookies[COOKIE_EXP_KEY]
                changed = True
        st.session_state.pop(PENDING_COOKIE_CLEAR_KEY, None)
        if changed:
            cookies.save()
    else:
        logger.warning("[store_session] cookies não prontos, agendando set no session_state.")
        if remember:
            st.session_state[PENDING_COOKIE_SET_KEY] = (token, exp_iso)
            st.session_state.pop(PENDING_COOKIE_CLEAR_KEY, None)
        else:
            st.session_state[PENDING_COOKIE_CLEAR_KEY] = True
            st.session_state.pop(PENDING_COOKIE_SET_KEY, None)
    return token


def logout() -> None:
    """Clear session token and state."""

    token = st.session_state.get(SESSION_KEY)
    if token:
        revoke_session_token(token)
    for key in (SESSION_KEY, SESSION_EXP_KEY, "finscore_user_email"):
        st.session_state.pop(key, None)
    st.session_state.pop(SESSION_REMEMBER_KEY, None)
    cookies = _get_cookie_manager()
    if cookies.ready():
        changed = False
        if COOKIE_TOKEN_KEY in cookies:
            del cookies[COOKIE_TOKEN_KEY]
            changed = True
        if COOKIE_EXP_KEY in cookies:
            del cookies[COOKIE_EXP_KEY]
            changed = True
        if changed:
            cookies.save()
        st.session_state.pop(PENDING_COOKIE_SET_KEY, None)
        st.session_state.pop(PENDING_COOKIE_CLEAR_KEY, None)
    else:
        st.session_state[PENDING_COOKIE_CLEAR_KEY] = True
        st.session_state.pop(PENDING_COOKIE_SET_KEY, None)


__all__ = ["require_auth", "logout", "store_session", "AuthResult"]
