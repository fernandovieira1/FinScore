import streamlit as st

def render():
    st.markdown("<h3 style='text-align: left;'>📦 Estoque de Propostas</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        Informações sobre a base de dados - processos/propostas cadastradas.
        
        FASE 2 do projeto (backend).
        """,
    )