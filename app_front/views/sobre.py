# app_front/pages/sobre.py
import streamlit as st

def render():
    st.header("ℹ️ Sobre este App")
    st.markdown(
        """
        **FinScore** — painel para análise financeira automatizada.

        **Como usar**  
        1) **Novo** → preencha **Cliente** e **Dados** e execute o cálculo.  
        2) Explore **Resumo**, **Tabelas** e **Gráficos**.  
        3) Na Fase 2, gere o **Parecer** (PDF/Word).
        """
    )
