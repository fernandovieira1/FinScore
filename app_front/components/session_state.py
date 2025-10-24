from __future__ import annotations

import copy
import streamlit as st

_DEFAULTS: dict[str, object] = {
    "meta": {},
    "df": None,
    "out": None,
    "erros": {},
    "novo_tab": "Cliente",
    "analise_tab": "Resumo",
    "parecer_gerado": None,
    "liberar_analise": False,
    "liberar_parecer": False,
    "_flow_started": False,
}

_NAV_FLAG_KEYS = ("_lock_parecer", "_force_parecer", "_DIRECT_TO_PARECER", "_button_nav_active")
_TRANSIENT_KEYS = (
    "_review_tasks",
    "_insight_polling_active",
    "_insight_last_poll_ts",
    "_insight_styles_loaded",
)


def _clone_default(value: object) -> object:
    if isinstance(value, (dict, list, set)):
        return copy.deepcopy(value)
    return value


def ensure_defaults() -> None:
    """Guarantee that the session holds the baseline keys used across the flow."""
    ss = st.session_state
    for key, value in _DEFAULTS.items():
        if key not in ss:
            ss[key] = _clone_default(value)
    ss.setdefault("page", "home")
    ss.setdefault("_pending_nav_target", None)
    ss.pop("_DIRECT_TO_PARECER", None)


def clear_flow_state() -> None:
    """Reset calculation data and navigation flags to their baseline values."""
    ss = st.session_state

    for key, value in _DEFAULTS.items():
        ss[key] = _clone_default(value)

    for key in _NAV_FLAG_KEYS:
        ss.pop(key, None)

    for key in _TRANSIENT_KEYS:
        ss.pop(key, None)

    ss.pop("_nav_block_message", None)

    ss["meta"] = {}
    ss["erros"] = {}
    ss["novo_tab"] = "Cliente"
    ss["analise_tab"] = "Resumo"


def reset_for_new_cycle() -> None:
    """Clear calculation artefacts so a fresh cycle can start deterministically."""
    clear_flow_state()
    st.session_state["_flow_started"] = True
