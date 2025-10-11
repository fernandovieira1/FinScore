# components/state_manager.py
"""Centralized state manager for the FinScore Streamlit app."""

from __future__ import annotations

import copy
import time
import uuid
from typing import Any, Optional

import streamlit as st

from components.config import SLUG_MAP, DEBUG_MODE

_REVERSE_SLUG_MAP = {label: slug for slug, label in SLUG_MAP.items()}
_DEFAULT_SLUG = "home"
_DEFAULT_PAGE = SLUG_MAP.get(_DEFAULT_SLUG, "Home")
_NAVIGATION_SUPPRESS_WINDOW = 1.0
_PROCESS_CACHE_KEY = "_cached_process_data"
_PROCESS_DATA_KEYS = ("df", "out", "meta", "erros", "policy_inputs", "anos_rotulos")
_PROCESS_FLAG_KEYS = ("liberar_lancamentos", "liberar_analise", "liberar_parecer")
_CLIENT_TOKEN_KEY = "client_token"
_SKIP_URL_SYNC_FLAG = "_skip_url_sync_once"
_SKIP_SIDEBAR_FLAG = "_skip_sidebar_qp_once"
_NAV_LOCK_KEY = "_nav_lock"

_GLOBAL_PROCESS_CACHE: dict[str, dict[str, Any]] = {}


class AppState:
    """Utility helpers to manage shared Streamlit session state."""

    @staticmethod
    def initialize() -> None:
        """Populate default keys the first time the app runs."""
        AppState._ensure_client_token()
        if "app_initialized" in st.session_state:
            return

        # Navigation
        st.session_state.current_page = _DEFAULT_PAGE
        st.session_state.current_slug = _DEFAULT_SLUG
        st.session_state.previous_page = None
        st.session_state.last_navigation_time = 0.0
        st.session_state.navigation_source = None

        # Process data
        st.session_state.df = None
        st.session_state.out = None
        st.session_state.erros = {}
        st.session_state.meta = {}

        # Tabs and feature flags
        st.session_state.novo_tab = "Cliente"
        st.session_state.analise_tab = "Resumo"
        st.session_state.calculo_ativo = False
        st.session_state.liberar_lancamentos = False
        st.session_state.liberar_analise = False
        st.session_state.liberar_parecer = False

        st.session_state.app_initialized = True

    @staticmethod
    def get_current_page() -> str:
        """Return the current logical page."""
        return st.session_state.get("current_page", _DEFAULT_PAGE)

    @staticmethod
    def get_previous_page() -> Optional[str]:
        """Return the previously selected page, if any."""
        return st.session_state.get("previous_page")

    @staticmethod
    def set_current_page(page_name: str, source: str = "unknown", slug: Optional[str] = None) -> None:
        """Update navigation state, keeping track of the trigger source."""
        previous = st.session_state.get("current_page")
        if slug is None:
            slug = _REVERSE_SLUG_MAP.get(page_name, st.session_state.get("current_slug", _DEFAULT_SLUG))

        # Garantir que page_name seja uma string válida
        page_name = page_name or _DEFAULT_PAGE

        st.session_state.previous_page = previous
        st.session_state.current_page = page_name
        st.session_state.current_slug = slug
        st.session_state.navigation_source = source
        st.session_state.last_navigation_time = time.time()

        if DEBUG_MODE:
            print(f"[AppState] page change: {previous} -> {page_name} (source={source}, slug={slug})")

        if slug != "analise":
            st.session_state.pop("_insight_polling_active", None)
            st.session_state.pop("_insight_last_poll_ts", None)
            st.session_state.pop("_review_tasks", None)

    @staticmethod
    def _process_cache() -> dict:
        return st.session_state.setdefault(_PROCESS_CACHE_KEY, {})

    @staticmethod
    def _ensure_client_token() -> str:
        token = st.session_state.get(_CLIENT_TOKEN_KEY)
        if token:
            return token

        sid_param = st.query_params.get("sid")
        if isinstance(sid_param, list) and sid_param:
            sid_param = sid_param[0]
        if isinstance(sid_param, str) and sid_param.strip():
            token = sid_param.strip()
        else:
            token = uuid.uuid4().hex
            st.query_params["sid"] = token

        st.session_state[_CLIENT_TOKEN_KEY] = token
        return token

    @staticmethod
    def get_client_token() -> str:
        return AppState._ensure_client_token()

    @staticmethod
    def skip_next_url_sync(
        target_slug: str | None = None,
        duration: float = 2.5,
        blocked_slugs: Optional[set[str]] = None,
    ) -> None:
        """Prevent the next URL sync from overriding an explicit navigation."""
        st.session_state[_SKIP_URL_SYNC_FLAG] = True
        st.session_state[_SKIP_SIDEBAR_FLAG] = True
        st.session_state[_NAV_LOCK_KEY] = {
            "slug": target_slug,
            "expires": time.time() + max(0.5, duration),
            "blocked": set(blocked_slugs or ()),
        }

    @staticmethod
    def consume_sidebar_skip() -> bool:
        """Return True once when sidebar should ignore query-param navigation."""
        return bool(st.session_state.pop(_SKIP_SIDEBAR_FLAG, False))

    @staticmethod
    def clear_nav_lock() -> None:
        """Remove temporary navigation locks."""
        st.session_state.pop(_NAV_LOCK_KEY, None)
        st.session_state.pop(_SKIP_SIDEBAR_FLAG, None)

    @staticmethod
    def is_slug_blocked(slug: str) -> bool:
        """Check if a slug is temporarily blocked by the navigation lock."""
        lock = st.session_state.get(_NAV_LOCK_KEY)
        if not lock:
            return False
        try:
            expires = float(lock.get("expires", 0.0))
        except (TypeError, ValueError):
            expires = 0.0
        if time.time() > expires:
            AppState.clear_nav_lock()
            return False
        blocked = set(lock.get("blocked") or ())
        return slug in blocked

    @staticmethod
    def _has_meaningful_value(value) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (str, bytes)):
            return bool(value.strip())
        if isinstance(value, (list, tuple, set)):
            return len(value) > 0
        if isinstance(value, dict):
            if not value:
                return False
            return any(item not in (None, "", [], {}, False) for item in value.values())
        empty_attr = getattr(value, "empty", None)
        if empty_attr is not None:
            try:
                return not bool(value.empty)
            except Exception:
                return True
        return True

    @staticmethod
    def drop_cached_process_data(*keys: str) -> None:
        cache = st.session_state.get(_PROCESS_CACHE_KEY)
        target_keys = keys or _PROCESS_DATA_KEYS
        for key in target_keys:
            if cache is not None:
                cache.pop(key, None)
            st.session_state[f"_{key}_cleared"] = True

        token = AppState._ensure_client_token()
        global_entry = _GLOBAL_PROCESS_CACHE.get(token)
        if global_entry is not None:
            for key in target_keys:
                global_entry.pop(key, None)
            if any(AppState._has_meaningful_value(global_entry.get(k)) for k in (_PROCESS_DATA_KEYS + _PROCESS_FLAG_KEYS)):
                _GLOBAL_PROCESS_CACHE[token] = copy.deepcopy(global_entry)
            else:
                _GLOBAL_PROCESS_CACHE.pop(token, None)

    @staticmethod
    def should_ignore_navigation(source: str) -> bool:
        """Throttle competing navigation events triggered in quick succession."""
        current_time = time.time()
        last_time = st.session_state.get("last_navigation_time", 0.0)
        last_source = st.session_state.get("navigation_source")

        # Garantir que last_source seja avaliado como booleano
        return bool((current_time - last_time < _NAVIGATION_SUPPRESS_WINDOW) and last_source and last_source != source)

    @staticmethod
    def sync_from_query_params() -> bool:
        """Copy navigation state from the URL query parameters."""
        if st.session_state.pop(_SKIP_URL_SYNC_FLAG, False):
            return False

        page_param = st.query_params.get("p")
        if not page_param:
            return False

        slug = page_param[0] if isinstance(page_param, list) else page_param

        lock = st.session_state.get(_NAV_LOCK_KEY)
        if lock:
            try:
                expires = float(lock.get("expires", 0.0))
            except (TypeError, ValueError):
                expires = 0.0
            if time.time() > expires:
                AppState.clear_nav_lock()
            else:
                blocked_slugs = set(lock.get("blocked") or ())
                if slug in blocked_slugs:
                    return False
                target_slug = lock.get("slug")
                if target_slug and slug != target_slug:
                    return False
                if target_slug and slug == target_slug:
                    lock["slug"] = None
                    lock["handled_at"] = time.time()

        target_page = SLUG_MAP.get(slug)
        if not target_page:
            return False
        if target_page == AppState.get_current_page() and slug == st.session_state.get("current_slug"):
            return False
        if AppState.should_ignore_navigation("url"):
            return False

        AppState.set_current_page(target_page, "url", slug=slug)
        return True

    @staticmethod
    def sync_to_query_params() -> None:
        """Ensure the URL reflects the current navigation state."""
        slug = st.session_state.get("current_slug")
        if not slug:
            slug = _REVERSE_SLUG_MAP.get(AppState.get_current_page(), _DEFAULT_SLUG)
            st.session_state.current_slug = slug
        if st.query_params.get("p") != slug:
            st.query_params["p"] = slug

    @staticmethod
    def is_debug_mode() -> bool:
        """Expose the global debug flag."""
        return DEBUG_MODE

    @staticmethod
    def has_active_process() -> bool:
        """Return True when there is data already loaded in this session."""
        ss = st.session_state
        if ss.get("df") is not None:
            return True
        if ss.get("out"):
            return True
        meta = ss.get("meta")
        if isinstance(meta, dict) and any(value not in (None, "", [], {}, False) for value in meta.values()):
            return True
        return False

    @staticmethod
    def reset_process_data() -> None:
        """Clear cached data and LLM artefacts, keeping navigation intact."""
        defaults = {
            "df": None,
            "out": None,
            "erros": {},
            "meta": {},
            "liberar_analise": False,
            "liberar_parecer": False,
            "liberar_lancamentos": False,
            "policy_inputs": None,
            "analise_tab": "Resumo",
            "novo_tab": "Cliente",
        }
        for key, value in defaults.items():
            st.session_state[key] = value
        AppState.drop_cached_process_data()
        st.session_state.pop(_PROCESS_CACHE_KEY, None)
        token = AppState._ensure_client_token()
        _GLOBAL_PROCESS_CACHE.pop(token, None)

    @staticmethod
    def preserve_data_across_pages() -> None:
        """Ensure data persists across page navigation."""
        ss = st.session_state
        token = AppState._ensure_client_token()
        cache = AppState._process_cache()
        global_snapshot = _GLOBAL_PROCESS_CACHE.get(token)
        if global_snapshot:
            if not cache:
                cache.update(copy.deepcopy(global_snapshot))
            else:
                for k, v in global_snapshot.items():
                    cache.setdefault(k, copy.deepcopy(v))

        for flag_key in _PROCESS_FLAG_KEYS:
            if flag_key in ss:
                cache[flag_key] = bool(ss[flag_key])
            elif flag_key in cache:
                # Restaurar todos os flags do cache, inclusive liberar_parecer
                ss[flag_key] = cache[flag_key]

        for key in _PROCESS_DATA_KEYS:
            value = ss.get(key)
            if AppState._has_meaningful_value(value):
                cache[key] = value
                ss.pop(f"_{key}_cleared", None)
            elif key in cache and not ss.get(f"_{key}_cleared", False):
                ss[key] = cache[key]
            elif value is None:
                cache.pop(key, None)

        payload: dict[str, Any] = {}
        for key in _PROCESS_DATA_KEYS + _PROCESS_FLAG_KEYS:
            value = cache.get(key)
            if AppState._has_meaningful_value(value):
                payload[key] = copy.deepcopy(value)

        if ss.get("current_page") != "Novo":
            if cache.get("df") is not None:
                ss["liberar_lancamentos"] = True
            if cache.get("out") is not None:
                ss["liberar_analise"] = True
                # Parecer só é liberado manualmente via botão "Aprovar" em /Análise/Scores
                # NÃO liberar automaticamente aqui

        if payload:
            _GLOBAL_PROCESS_CACHE[token] = payload
        else:
            _GLOBAL_PROCESS_CACHE.pop(token, None)
