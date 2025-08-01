import streamlit as st
import plotly.express as px
import pandas as pd

def mostrar_dashboard(df_indices, df_pca, top_indices_df):
    st.header("📈 Dashboard Interativo")

    # Garantir que a coluna 'ano' está presente
    if 'ano' not in df_indices.columns:
        df_indices = df_indices.copy()
        df_indices['ano'] = list(range(len(df_indices), 0, -1))  # fallback

    # 📊 Gráfico 1 – Evolução de Índices Financeiros
    st.subheader("📌 Evolução de Índices Financeiros")
    indice_escolhido = st.selectbox("Selecione um índice:", df_indices.drop(columns=['ano']).columns)
    fig1 = px.line(df_indices, x='ano', y=indice_escolhido,
                   markers=True,
                   title=f"Evolução do índice: {indice_escolhido}")
    fig1.update_layout(xaxis_title="Ano", yaxis_title=indice_escolhido)
    st.plotly_chart(fig1, use_container_width=True)

    # 📈 Gráfico 2 – Variância Explicada (Scree Plot do PCA)
    st.subheader("🔍 Variância Explicada pelos Componentes (PCA)")
    variancia = df_pca.var(axis=0)
    total = variancia.sum()
    componentes = [f"PC{i+1}" for i in range(len(variancia))]
    df_variancia = pd.DataFrame({
        "Componente": componentes,
        "Variância Explicada (%)": round((variancia / total) * 100, 2)
    })
    fig2 = px.bar(df_variancia, x="Componente", y="Variância Explicada (%)", text="Variância Explicada (%)")
    fig2.update_traces(textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

    # 📌 Gráfico 3 – Top 3 Índices por Componente
    st.subheader("🌟 Índices Mais Relevantes por Componente Principal")
    df_melt = top_indices_df.melt(id_vars="PC", value_vars=["Indice 1", "Indice 2", "Indice 3"],
                                  var_name="Ordem", value_name="Índice")
    pesos = top_indices_df.melt(id_vars="PC", value_vars=["Peso 1", "Peso 2", "Peso 3"],
                                var_name="Ordem", value_name="Peso")
    df_plot = pd.concat([df_melt[["PC", "Índice"]], pesos["Peso"]], axis=1)
    df_plot.rename(columns={"PC": "Componente"}, inplace=True)
    df_plot["Peso Absoluto"] = abs(df_plot["Peso"])

    fig3 = px.bar(df_plot, x="Índice", y="Peso Absoluto", color="Componente", barmode="group")
    st.plotly_chart(fig3, use_container_width=True)
