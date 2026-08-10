import streamlit as st
import plotly.express as px
import pandas as pd

def mostrar_dashboard(df_indices):
    # Garantir coluna 'ano' (se não vier do seu processo)
    if "ano" not in df_indices.columns:
        df_indices = df_indices.copy()
        df_indices["ano"] = list(range(len(df_indices), 0, -1))

    st.subheader("📌 Evolução de Índices Financeiros")

    # Seleciona apenas colunas numéricas (exceto 'ano')
    num_cols = [c for c in df_indices.columns if c != "ano" and pd.api.types.is_numeric_dtype(df_indices[c])]
    if not num_cols:
        st.info("Sem índices numéricos disponíveis.")
        return

    indice_escolhido = st.selectbox("Selecione um índice:", num_cols)
    fig = px.line(
        df_indices,
        x="ano",
        y=indice_escolhido,
        markers=True,
        title=f"Evolução do índice: {indice_escolhido}"
    )
    fig.update_layout(xaxis_title="Ano", yaxis_title=indice_escolhido)
    st.plotly_chart(fig, use_container_width=True)
