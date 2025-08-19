# app_front/pages/tabelas.py
import streamlit as st

def render():
    ss = st.session_state
    st.header("📄 Tabelas")
    if not ss.out:
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        return

    st.subheader("Índices Contábeis Calculados")
    st.dataframe(ss.out["df_indices"], use_container_width=True)

    st.subheader("Componentes Principais (PCA)")
    st.dataframe(ss.out["df_pca"], use_container_width=True)

    st.subheader("Top 3 Índices por Componente")
    st.dataframe(ss.out["top_indices_df"], use_container_width=True)
