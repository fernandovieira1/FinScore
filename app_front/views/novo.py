# app_front/views/novo.py

import streamlit as st
from components.state_manager import AppState

def render():
    st.header("Novo Cálculo")

    st.markdown(
        """
Para dar início, siga os passos descritos:

1. Após clicar no botão **[Iniciar]**, logo abaixo, você será redirecionado para a seção **"Lançamentos"**.
2. Em lançamentos, na aba **|Cliente|**, preencha as seguintes informações:
    * Nome da empresa.
    * CNPJ.
    * Ano Inicial e Ano Final das demonstrações contábeis.
    * Pontuação do Serasa.
    * Data de consulta ao Serasa.

   Em seguida, clique no botão **[Enviar Dados]**, localizado no final do formulário.
3. Na aba **|Dados|**, faça o lançamento dos dados contábeis, que podem ser enviados via upload de arquivo, link do Google Sheets ou diretamente na plataforma.
    * Se optar pelo upload de arquivo, certifique-se de que ele esteja no formato correto (.xlsx).
4. Clique **[Calcular FinScore]**.

A análise será detalhada (mexer nessa parte) na seção **"Análise"** e você poderá visualizar o parecer na seção **"Parecer"**.
        """,
        unsafe_allow_html=True
    )

    st.write("")
    # Botão Streamlit centralizado, azul, estilo consistente
    col = st.columns([3, 2, 3])[1]
    with col:
        btn_style = """
        <style>
        div[data-testid='column'] button[kind='secondary'] {
            background: var(--primary-btn, #0074d9) !important;
            color: #fff !important;
            font-weight: 600;
            font-size: 1.1rem;
            border-radius: 6px !important;
            padding: 0.7rem 2.5rem !important;
            border: none !important;
            box-shadow: 0 2px 8px rgba(16,24,40,0.08);
            transition: background 0.2s;
        }
        div[data-testid='column'] button[kind='secondary']:hover {
            background: #005fa3 !important;
        }
        </style>
        """
        st.markdown(btn_style, unsafe_allow_html=True)
        if st.button("Iniciar", key="btn_iniciar", help="Ir para lançamentos"):
            st.session_state["liberar_lancamentos"] = True
            AppState.set_current_page("Lançamentos", source="novo_iniciar_btn")
            st.rerun()
