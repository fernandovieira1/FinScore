import streamlit as st

def render():
    st.markdown("<h3 style='text-align: left;'>📟 Cadastros</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        Cadastros de usuários (analistas e gestores) e das empresas clientes.
        
        FASE 2 do projeto (backend).
        """,
    )