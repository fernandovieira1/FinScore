# app_front/views/home.py
import streamlit as st

def render():
    st.header("Bem-vindo ao FinScore")
    st.markdown(
        """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero.
        Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet.
        Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta.

        **IMPORTANTE**: 
        * Versão atual [v. 0.8.20b (ia), de 06/10/2025]. 
        * Por ora, dê preferência para o tema claro do sistema operacional ou navegador.
        * Use com cautela e reporte bugs.
        """,
    )
