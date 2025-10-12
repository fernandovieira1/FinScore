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
Para dar início, siga os passos descritos:

1. Após clicar no botão **[Iniciar]**, logo abaixo, você será redirecionado para a seção **"Lançamentos"**.
2. Em lançamentos, na aba **|Cliente|**, preencha as seguintes informações:
    * Nome da empresa.
    * CNPJ.
        * Ano Inicial e Ano Final das demonstrações contábeis.

   Em seguida, clique no botão **[Enviar Dados]**, localizado no final do formulário.
3. Na aba **|Dados|**, faça o lançamento dos dados contábeis, que podem ser enviados via upload de arquivo, link do Google Sheets ou diretamente na plataforma.
    * Se optar pelo upload de arquivo, certifique-se de que ele esteja no formato correto (.xlsx).
4. Clique em **[Calcular FinScore]**.
5. Avalie os resultados preliminares apresentados e emita o parecer técnico na seção **"Parecer"** após clicar no botão **[Aprovar]**.

A análise será detalhada na seção **"Análise"** e você poderá visualizar o parecer na seção **"Parecer"**.
        """
    )

    _, col_button, _ = st.columns((1, 1, 1))
    col_button.button("Iniciar", key="btn_iniciar_novo_calculo", on_click=_on_iniciar)
