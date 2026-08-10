from __future__ import annotations
import streamlit as st

def render():
    st.markdown("<h3 style='text-align: left;'>📦 Estoque de Propostas</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        <p style='color: #6c757d;'>
        Informações sobre a base de dados - processos/propostas cadastradas.
        <br><br>
        FASE 2 do projeto (backend).
        </p>
        """,
        unsafe_allow_html=True
    )
