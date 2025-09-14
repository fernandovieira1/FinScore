# app_front/views/processo.py
import streamlit as st

from . import novo as v_novo
from . import lancamentos as v_lanc
from . import analise as v_ana
from . import parecer as v_par

PAGES = {
    "Novo": getattr(v_novo, "render", v_novo.render),
    "Lançamentos": getattr(v_lanc, "render", v_lanc.render),
    "Análise": getattr(v_ana, "render", v_ana.render),
    "Parecer": getattr(v_par, "render", v_par.render),
}

def _default_index():
    sel = st.session_state.get("processo_choice")
    if sel in PAGES:
        return list(PAGES.keys()).index(sel)
    return 0

def render():
    choice = st.session_state.get("processo_choice")
    if choice is None or choice not in PAGES:
        choice = list(PAGES.keys())[0]

    if not st.session_state.get("processo_dropdown_rendered"):
        with st.sidebar:
            st.selectbox(
                "Etapa do processo",                # label real para evitar warning
                list(PAGES.keys()),
                index=_default_index(),
                key="processo_choice",
                label_visibility="collapsed",       # continua invisível
            )
        print(f"[DEBUG processo.py] Dropdown desenhado na sidebar.")

    print(f"[DEBUG processo.py] Navegação permitida para {choice}")
    PAGES[choice]()
