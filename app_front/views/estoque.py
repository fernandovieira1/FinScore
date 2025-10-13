import streamlit as st

def render():
    st.markdown("<h3 style='text-align: left;'>📦 Estoque</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        Informações sobre a base de dados - processos/propostas cadastradas.
        
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero.
        Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet.
        Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta.
        """,
    )