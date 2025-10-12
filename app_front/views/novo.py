import streamlit as st

from components import nav
from components.session_state import reset_for_new_cycle

_NAV_KEYS = ("_lock_parecer", "_force_parecer", "_DIRECT_TO_PARECER", "liberar_parecer", "_button_nav_active")


def _reset_nav_flags() -> None:
    for key in _NAV_KEYS:
        st.session_state.pop(key, None)


def _on_iniciar() -> None:
    reset_for_new_cycle()
    _reset_nav_flags()
    if not nav.go("lanc"):
        nav.force("lanc")


def render() -> None:
    st.header("Novo Cálculo")
    st.markdown(
        """
Para iniciar um novo ciclo do FinScore siga a sequência abaixo:

1. Clique em **Iniciar** para ir à etapa **Lançamentos**.
2. Cadastre o cliente e informe o intervalo de anos da análise.
3. Envie os dados contábeis (upload ou Google Sheets) e pressione **Calcular FinScore**.
4. Revise os resultados em **Análise** e finalize em **Parecer**.
        """
    )

    st.button("Iniciar", key="btn_iniciar_novo_calculo", on_click=_on_iniciar)
