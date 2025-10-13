from __future__ import annotations

import streamlit as st

from . import nav

_FLAG_KEYS = ("_lock_parecer", "_force_parecer", "_DIRECT_TO_PARECER")


class NavigationFlow:
    """Minimal helpers to drive the Novo -> Parecer flow deterministically."""

    @staticmethod
    def reset_navigation_state() -> None:
        for key in _FLAG_KEYS:
            st.session_state.pop(key, None)
        st.session_state.pop("liberar_parecer", None)

    @staticmethod
    def request_lock_parecer() -> None:
        ss = st.session_state
        ss["_lock_parecer"] = True
        ss["_force_parecer"] = True
        ss["_DIRECT_TO_PARECER"] = True
        ss["liberar_parecer"] = True
        nav.force("parecer")
        st.query_params["p"] = "parecer"


