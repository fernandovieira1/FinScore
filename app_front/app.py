import streamlit as st
import pandas as pd
from utils_finscore import executar_finscore
from dashboard_finscore import mostrar_dashboard

st.set_page_config(page_title="FinScore Dashboard", layout="wide")

st.title("📊 FinScore - Análise Financeira Automatizada")

#### 1. Dados do Cliente
st.header("1️⃣ Dados do Cliente")
nome_empresa = st.text_input("Nome da Empresa")
cnpj = st.text_input("CNPJ (opcional)")
ano_inicial = st.number_input("Ano Inicial", min_value=2000, max_value=2100, value=2021)
ano_final = st.number_input("Ano Final", min_value=2000, max_value=2100, value=2023)
serasa_score = st.number_input("Serasa Score", min_value=0, max_value=1000, value=550)

#### 2. Upload ou Link dos Dados Contábeis
st.header("2️⃣ Dados Contábeis")

opcao_entrada = st.radio("Como deseja fornecer os dados contábeis?", ["Upload de arquivo Excel", "Link do Google Sheets"])

df_contabil = None

if opcao_entrada == "Upload de arquivo Excel":
    uploaded_file = st.file_uploader("Faça o upload do arquivo Excel (.xlsx)", type=["xlsx"])
    if uploaded_file is not None:
        try:
            df_contabil = pd.read_excel(uploaded_file, engine='openpyxl')
            st.success("✅ Dados carregados com sucesso.")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

elif opcao_entrada == "Link do Google Sheets":
    link_planilha = st.text_input("Cole aqui o link compartilhável da planilha (formato de edição)")

    if link_planilha:
        try:
            # Extração do sheet_id
            sheet_id = link_planilha.split("/d/")[1].split("/")[0]

            # Extração do gid (se houver)
            if "gid=" in link_planilha:
                gid = link_planilha.split("gid=")[-1].split("&")[0]
            else:
                gid = "0"

            # Construção do link de exportação correto
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&id={sheet_id}&gid={gid}"

            df_contabil = pd.read_excel(url, engine='openpyxl')
            st.success("✅ Dados carregados com sucesso a partir do Google Sheets.")
        except Exception as e:
            st.error(f"Erro ao acessar a planilha: {e}")

#### 3. Visualizar Dados Carregados
if df_contabil is not None:
    st.header("📋 Pré-visualização dos Dados Contábeis")
    st.dataframe(df_contabil)

    st.info("⚙️ Pronto para executar o cálculo do FinScore.")

    if st.button("Calcular FinScore"):
        resultado = executar_finscore(df_contabil, nome_empresa, ano_inicial, ano_final, serasa_score)
        
        st.success(f"✅ FinScore Ajustado: {resultado['finscore_ajustado']} ({resultado['classificacao_finscore']})")
        st.success(f"📈 Serasa Score: {resultado['serasa']} ({resultado['classificacao_serasa']})")

        st.subheader("📊 Índices Contábeis Calculados")
        st.dataframe(resultado['df_indices'])

        st.subheader("🔎 Componentes Principais (PCA)")
        st.dataframe(resultado['df_pca'])

        st.subheader("🌟 Destaques por Componente Principal")
        st.dataframe(resultado['top_indices_df'])

        # ✅ Mostrar os gráficos interativos
        mostrar_dashboard(
            resultado["df_indices"],
            resultado["df_pca"],
            resultado["top_indices_df"]
        )



