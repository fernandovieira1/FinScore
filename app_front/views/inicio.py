# app_front/views/inicio.py
import streamlit as st

def render():
    st.header("Bem-vindo ao FinScore")
    st.markdown(
        """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero.
        Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet.
        Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta.
        """,
    )
