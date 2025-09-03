# app_front/views/sobre.py
import streamlit as st

# rótulos com ícones
TAB_LABELS = ["🧭 Metodologia", "📚 Glossário", "❓ FAQ"]

def _sec_metodologia():
    st.subheader("Metodologia")
    st.write("Esta é a página de metodologia.")
    # TODO: coloque aqui o conteúdo real da metodologia
    # (tabelas, imagens, markdowns etc.)

def _sec_glossario():
    st.subheader("Glossário")
    st.write("Esta é a página de glossário.")
    # TODO: conteúdo do glossário

def _sec_faq():
    st.subheader("FAQ")
    st.write("Esta é a página de FAQ.")
    # TODO: perguntas e respostas

def render():
    st.header("Sobre")

    # abas internas
    tab_met, tab_glos, tab_faq = st.tabs(TAB_LABELS)

    with tab_met:
        _sec_metodologia()

    with tab_glos:
        _sec_glossario()

    with tab_faq:
        _sec_faq()
