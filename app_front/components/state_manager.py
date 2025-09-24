# components/state_manager.py
"""Centralized state manager for the FinScore Streamlit app."""

from __future__ import annotations

import time
from typing import Optional

import streamlit as st

from components.config import SLUG_MAP, DEBUG_MODE

_REVERSE_SLUG_MAP = {label: slug for slug, label in SLUG_MAP.items()}
_DEFAULT_SLUG = "home"
_DEFAULT_PAGE = SLUG_MAP.get(_DEFAULT_SLUG, "Home")


class AppState:
    """Utility helpers to manage shared Streamlit session state."""

    @staticmethod
    def initialize() -> None:
        """Populate default keys the first time the app runs."""
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

        st.session_state.previous_page = previous
        st.session_state.current_page = page_name
        st.session_state.current_slug = slug
        st.session_state.navigation_source = source
        st.session_state.last_navigation_time = time.time()

        if DEBUG_MODE:
            print(f"[AppState] page change: {previous} -> {page_name} (source={source}, slug={slug})")

    @staticmethod
    def should_ignore_navigation(source: str) -> bool:
        """Throttle competing navigation events triggered in quick succession."""
        current_time = time.time()
        last_time = st.session_state.get("last_navigation_time", 0.0)
        last_source = st.session_state.get("navigation_source")
        return current_time - last_time < 0.3 and last_source and last_source != source

    @staticmethod
    def sync_from_query_params() -> bool:
        """Copy navigation state from the URL query parameters."""
        page_param = st.query_params.get("p")
        if not page_param:
            return False

        slug = page_param[0] if isinstance(page_param, list) else page_param
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
        for transient_key in ("reviews", "artifacts_meta"):
            st.session_state.pop(transient_key, None)
