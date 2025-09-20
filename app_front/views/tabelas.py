# app_front/pages/tabelas.py
import streamlit as st
import pandas as pd


def _formata_ano(df):
    if df is None:
        return df
    df_display = df.copy()
    if "ano" not in df_display.columns:
        return df_display

    ordenacao = pd.to_numeric(df_display["ano"], errors="coerce")
    df_display = df_display.assign(_ano_ord=ordenacao)
    df_display = df_display.sort_values("_ano_ord", ascending=True, na_position="last")
    df_display = df_display.drop(columns="_ano_ord")
    df_display = df_display.reset_index(drop=True)

    def _fmt(valor, fallback):
        if valor is None:
            return fallback
        try:
            return str(int(float(valor)))
        except (TypeError, ValueError):
            return str(valor)

    df_display["Ano"] = [
        _fmt(valor, str(idx + 1)) for idx, valor in enumerate(df_display["ano"])
    ]
    df_display.drop(columns="ano", inplace=True)
    cols = ["Ano"] + [c for c in df_display.columns if c != "Ano"]
    df_display = df_display[cols]
    return df_display

def render():
    ss = st.session_state
    st.header("📄 Tabelas")
    if not ss.out:
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        return

    st.subheader("Índices Contábeis Calculados")
    df_indices = _formata_ano(ss.out["df_indices"])
    st.dataframe(df_indices, use_container_width=True, hide_index=True)

    st.subheader("Componentes Principais (PCA)")
    df_pca = _formata_ano(ss.out["df_pca"]).drop(columns="Ano", errors="ignore")
    st.dataframe(df_pca, use_container_width=True, hide_index=True)

    st.subheader("Top 3 Índices por Componente")
    st.dataframe(ss.out["top_indices_df"], use_container_width=True, hide_index=True)
