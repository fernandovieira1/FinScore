import streamlit as st

def render():
    st.markdown("<h3 style='text-align: left;'>📧 Contato</h3>", unsafe_allow_html=True)
    st.markdown(
        """
        <p style='color: #6c757d;'>Esta é a página de contato.</p>
        """,
        unsafe_allow_html=True
    )
