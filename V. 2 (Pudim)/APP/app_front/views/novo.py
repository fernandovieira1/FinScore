from __future__ import annotations
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
    ss = st.session_state
    if ss.get("_lock_parecer") and ss.get("parecer_gerado"):
        st.warning(
            "⚠️ Um parecer está atualmente armazenado em cache. Ao clicar em "
            "'Iniciar' um novo ciclo será iniciado e todos os dados lançados "
            "até o momento serão descartados."
        )
    st.markdown("<h3 style='text-align: center;'>📃 Novo Cálculo</h3>", unsafe_allow_html=True)
    st.markdown(
        """
Para dar início, siga os passos descritos:

1. Após clicar no botão **[Iniciar]**, logo abaixo, você será redirecionado para a seção **"Lançamentos"**.
2. Em lançamentos, na aba **|Cliente|**, preencha as seguintes informações:
    * Nome da empresa.
    * CNPJ.
        * Ano Inicial das demonstrações contábeis.
    * O valor e data da consulta ao Serasa do cliente..

   Em seguida, clique no botão **[Enviar Dados]**, localizado no final do formulário.
3. Na aba **|Dados|**, faça o lançamento dos dados contábeis, que podem ser enviados via upload de arquivo, link do Google Sheets ou diretamente na plataforma.
    * Se optar pelo upload de arquivo, certifique-se de que ele esteja no formato correto (.xlsx).
4. Clique em **[Calcular FinScore]**.
5. Avalie os resultados preliminares apresentados e emita o Parecer Técnico na seção **"Parecer"**, após aprovar sua emissão, em **"Análise"**.

Além de ser gerado e visualizado na seção própria, o Parecer poderá ser exportado e feito seu download.
        """
    )

    _, col_button, _ = st.columns([1, 1, 1])
    with col_button:
        st.button("Iniciar", key="btn_iniciar_novo_calculo", on_click=_on_iniciar, use_container_width=True)
