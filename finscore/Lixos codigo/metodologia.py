# app_front/views/metodologia.py
import streamlit as st
import pandas as pd
import os

ASSETS_PATH = os.path.join("app_front", "assets")

def show():
    st.title("Metodologia do FinScore")

    # =======================
    # 1. O que é o FinScore
    # =======================
    st.markdown("""
    O **FinScore** é um índice que resume a saúde econômico-financeira da empresa
    em um único número, de **0 a 1000**.  

    Ele combina três elementos:
    - **Índices financeiros clássicos** (liquidez, rentabilidade, endividamento, prazos).  
    - **Técnicas estatísticas** para dar peso correto a cada índice.  
    - **Ponderação temporal**, que privilegia o desempenho mais recente.
    """)

    # =======================
    # 2. Como funciona o cálculo
    # =======================
    st.subheader("Fluxo do cálculo")
    st.image(os.path.join(ASSETS_PATH, "finscore_pipeline.png"), use_column_width=True)

    st.markdown("""
    **Passo 1. Entram os balanços e DREs**  
    Usamos até 3 anos de informações contábeis.  

    **Passo 2. Cálculo de índices financeiros**  
    São métricas conhecidas de liquidez, margem, retorno, alavancagem etc.  

    **Passo 3. Padronização estatística**  
    Aqui entra o conceito de **z-score**: transformar todos os índices para uma escala
    comparável (média = 0, desvio = 1). Isso evita que um indicador "pese" mais apenas
    por ter números naturalmente maiores.  

    **Passo 4. Identificação de fatores principais**  
    Usamos a técnica de **PCA (Análise de Componentes Principais)**, que cria fatores
    (ou “componentes”) que concentram as principais variações nos dados.  
    - Cada componente é uma combinação dos índices originais.  
    - Os pesos de cada índice nesses componentes são chamados **loadings**.  
    - O quanto cada componente explica dos dados é a **variância explicada**.  

    **Passo 5. Consolidação ao longo do tempo**  
    Cada ano gera um escore. Para o FinScore final, fazemos uma média ponderada:  
    - Ano mais recente: **60%**  
    - Ano anterior: **25%**  
    - Dois anos antes: **15%**

    **Passo 6. Escala 0–1000 e classificação**  
    O escore é convertido para 0–1000 e enquadrado em faixas de risco.
    """)

    # =======================
    # 3. Índices considerados
    # =======================
    st.subheader("Índices utilizados")
    df = pd.read_csv(os.path.join(ASSETS_PATH, "finscore_indices_formulas.csv"))
    st.table(df)

    # =======================
    # 4. Pesos temporais
    # =======================
    st.subheader("Ponderação temporal")
    st.image(os.path.join(ASSETS_PATH, "finscore_pesos_temporais.png"), use_column_width=False)

    # =======================
    # 5. Faixas de risco
    # =======================
    st.subheader("Faixas de risco")
    st.image(os.path.join(ASSETS_PATH, "finscore_faixas_risco.png"), use_column_width=True)

    st.markdown("""
    - **0–125:** Muito Arriscado  
    - **126–250:** Levemente Arriscado  
    - **251–750:** Neutro  
    - **751–875:** Levemente Sólido  
    - **>875:** Muito Sólido  
    """)

    # =======================
    # 6. Limites e governança
    # =======================
    st.subheader("Limites e governança")
    st.markdown("""
    - **Qualidade dos dados**: o modelo depende da consistência dos balanços.  
    - **Dados extremos ou faltantes**: podem distorcer o cálculo; o sistema aplica
      regras automáticas para suavizar, mas recomenda-se auditoria.  
    - **Contexto setorial**: alguns índices podem pesar mais em determinados setores;
      por isso, a PCA ajusta dinamicamente os pesos.  
    - **Versionamento**: cada rodada de cálculo registra versão do modelo (ex.: v9.7),
      garantindo rastreabilidade e comparabilidade ao longo do tempo.
    """)
