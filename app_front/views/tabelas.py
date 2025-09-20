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

def get_indices_table() -> pd.DataFrame | None:
    ss = st.session_state
    out = ss.get("out")
    if not out:
        return None
    df_indices = out.get("df_indices")
    if df_indices is None:
        return None
    return _formata_ano(df_indices)

def get_pca_scores_table() -> pd.DataFrame | None:
    ss = st.session_state
    out = ss.get("out")
    if not out:
        return None
    df_pca = out.get("df_pca")
    if df_pca is None:
        return None
    return _formata_ano(df_pca).drop(columns="Ano", errors="ignore")

def get_top_indices_table() -> pd.DataFrame | None:
    ss = st.session_state
    out = ss.get("out")
    if not out:
        return None
    return out.get("top_indices_df")

def get_pca_loadings_table() -> pd.DataFrame | None:
    ss = st.session_state
    out = ss.get("out")
    if not out:
        return None
    return out.get("loadings")

def render():
    ss = st.session_state
    st.header("Tabelas")
    if not ss.out:
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        return

    st.subheader("Indices Contabeis Calculados")
    df_indices = get_indices_table()
    if df_indices is not None:
        st.dataframe(df_indices, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados de indices contabeis para exibir.")

    st.subheader("Componentes Principais (PCA)")
    df_pca = get_pca_scores_table()
    if df_pca is not None:
        st.dataframe(df_pca, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados de scores de PCA para exibir.")

    st.subheader("Top 3 Indices por Componente")
    top_indices_df = get_top_indices_table()
    if top_indices_df is not None:
        st.dataframe(top_indices_df, use_container_width=True, hide_index=True)
    else:
        st.info("Sem destaques de PCA para exibir.")
