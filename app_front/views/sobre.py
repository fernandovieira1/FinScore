# app_front/views/sobre.py
import streamlit as st

# rótulos com ícones
TAB_LABELS = ["🧭 Metodologia", "📚 Glossário", "❓ FAQ"]

def _sec_metodologia():
    import os, pandas as pd
    from pathlib import Path

    st.subheader("FinScore")

    # caminho robusto para os assets (independente de onde o app é executado)
    ASSETS_PATH = Path(__file__).resolve().parents[1] / "assets"

    # 1) O que é o FinScore
    st.markdown("""
    O FinScore transforma as demonstrações contábeis da empresa em um número único (0 a 1000) que resume sua saúde econômico-financeira e risco de crédito.

Ele combina três elementos:

- Índices financeiros clássicos — como liquidez, rentabilidade e endividamento.

- Técnicas estatísticas — que colocam todos os índices na mesma escala e evidenciam os que mais pesam no risco.

- Ponderação temporal — que valoriza o desempenho mais recente (60% do peso), mas sem perder a visão do histórico (25% e 15%).

Em outras palavras, o FinScore funciona como um termômetro de risco: quanto mais alto, menor a probabilidade percebida de problemas financeiros.
    """)

    # 2) Fluxo visual do cálculo
    st.markdown("#### Metodologia")

    st.markdown("""
    O **FinScore** transforma dados contábeis das **três demonstrações contábeis** mais recentes da empresa em um **número único (0–1000)** 
    que resume sua saúde econômico-financeira e risco de crédito. O cálculo combina três etapas principais: 
    **1) índices contábeis, 2) técnicas estatísticas e 3) ponderação temporal**.

    **1) índices contábeis**

    O ponto de partida do FinScore são indicadores extraídos das três últimas demonstrações financeiras que permitem avaliar
    diferentes dimensões da empresa.

    - **Liquidez** (Liquidez Corrente, Liquidez Seca, CCL/Ativo): mede a capacidade de honrar 
      compromissos de curto prazo e sinaliza a folga de caixa.
    - **Rentabilidade** (Margem Líquida, ROA, ROE, Margem EBITDA): indica a eficiência em transformar 
      receita em lucro e o retorno obtido pelos ativos e pelo capital próprio.
    - **Endividamento/Alavancagem** (Dívida/Ativo, Dívida Líquida/EBITDA, Cobertura de Juros): mostra 
      o grau de dependência de recursos de terceiros e a capacidade operacional de sustentar o serviço da dívida.
    - **Eficiência Operacional** (Giro do Ativo, PMR, PMP): avalia a velocidade do ciclo financeiro e o uso dos ativos para gerar receita.

                
    2) **Técnicas estatísticas**
    Esses índices não são avaliados de forma isolada: o FinScore relaciona sinais distintos, destacando 
    combinações que revelam pontos fortes e fragilidades. Para tornar os indicadores comparáveis e extrair padrões relevantes, 
    o FinScore padroniza e reduz a dimensionalidade dos dados, com vistas a otimizar a análise.

    - **A padronização (z-score)** converte todos os índices para uma escala comum (média zero, desvio-padrão um), 
      permitindo comparações equilibradas.
    
    - Já a **análise de componentes principais (PCA)** resume grupos de variáveis correlacionadas em fatores que não se sobrepõem, 
      facilitando a interpretação dos dados, o que é crucial para um modelo de risco. Isto é computado com base em:
        
        - **Cargas (loadings)**: coeficientes que mostram o quanto cada índice influencia cada fator, ajudando a entender quais variáveis mais 
        afetam o risco. As cargas (loadings) representam o grau de influência de cada variável original sobre os fatores extraídos, ou seja: 
        valores mais altos indicam maior contribuição daquela variável para o fator;

        - **Variância explicada**: indica o quanto cada fator consegue representar dos dados originais. Quanto maior essa variância, mais relevante 
        é o fator na composição do escore.

    Esse processo reduz a complexidade ao tempo em que dá mais eficência no cômputo do índice, pois em vez de acompanhar uma lista extensa de 
    índices contábeis, o FinScore sopesa todos eles e escolhe, ao final, trabalhar com os fatores que concentram a essência das informações daquela
    empresa, consoante o contexto dado pelo seu histórico recente.
                """)

    fluxograma = ASSETS_PATH / "finscore_pipeline.png"
    if fluxograma.exists():
        st.image(str(fluxograma), use_column_width=True)
    else:
        st.info("Fluxograma não encontrado em assets. Esperado: `finscore_pipeline.png`.")

    st.markdown("""
    **3) Ponderação temporal**
                
    O modelo também incorpora a evolução no tempo, considerando até três exercícios consecutivos, 
    com pesos diferenciados:

    - **Ano mais recente (t): 60%**
    - **Ano anterior (t−1): 25%**
    - **Dois anos antes (t−2): 15%**

    Essa ponderação valoriza o desempenho atual sem desconsiderar a trajetória. Resultados recentes 
    têm maior influência, mas ainda moderados pelo histórico. O escore final é convertido para a escala 
    de **0 a 1000** e classificado em faixas de risco, o que facilita a leitura e a comunicação em 
    decisões de crédito.
    """)

    # 3) Índices considerados (tabela)
    st.markdown("#### Índices utilizados")
    tabela_csv = ASSETS_PATH / "finscore_indices_formulas.csv"
    if tabela_csv.exists():
        df = pd.read_csv(tabela_csv)
        st.table(df)
        st.download_button(
            "Baixar tabela de índices (CSV)",
            data=tabela_csv.read_bytes(),
            file_name="finscore_indices_formulas.csv",
            mime="text/csv",
        )
    else:
        st.info("Tabela de índices não encontrada em assets. Esperado: `finscore_indices_formulas.csv`.")

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
