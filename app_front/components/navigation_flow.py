from __future__ import annotations

import streamlit as st

_FLAG_KEYS = ("_lock_parecer", "_force_parecer", "_DIRECT_TO_PARECER")


class NavigationFlow:
    """Minimal helpers to drive the Novo -> Parecer flow deterministically."""

    @staticmethod
    def reset_navigation_state() -> None:
        for key in _FLAG_KEYS:
            st.session_state.pop(key, None)
        st.session_state.pop("liberar_parecer", None)
        st.session_state.pop("_nav_block_message", None)

    @staticmethod
    def request_lock_parecer() -> None:
        ss = st.session_state
        ss.pop("_DIRECT_TO_PARECER", None)
        ss["_lock_parecer"] = True
        ss["liberar_parecer"] = True
