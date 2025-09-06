# app_front/views/sobre.py
import streamlit as st
from pathlib import Path

# rótulos com ícones
TAB_LABELS = ["🧭 Metodologia", "📚 Glossário", "❓ FAQ"]

def _sec_metodologia():
    import pandas as pd

    st.subheader("📶 FinScore")

    # caminho robusto para os assets (independente de onde o app é executado)
    ASSETS_PATH = Path(__file__).resolve().parents[1] / "assets"

    # 1) O que é o FinScore (texto executivo, impessoal)
    st.markdown("""
    O **FinScore** transforma as demonstrações contábeis da empresa em um **número único (0–1000)**
    que resume sua saúde econômico-financeira e risco de crédito. O cálculo combina informações de até
    **três exercícios** e entrega um resultado comparável entre empresas e ao longo do tempo.
    """)

    # 2) Metodologia (texto descritivo com termos técnicos explicados)
    st.markdown("#### 📕 Metodologia")
    st.markdown("""
    A construção do FinScore ocorre em três blocos integrados:

    **a) Índices contábeis.** São extraídos indicadores que cobrem quatro dimensões: **liquidez**
    (capacidade de honrar compromissos de curto prazo), **rentabilidade** (eficiência em gerar lucro),
    **endividamento/alavancagem** (grau de dependência de capital de terceiros e folga para serviço da dívida)
    e **eficiência operacional** (ritmo do ciclo financeiro e uso de ativos para gerar receita).
    Esses índices não são lidos de forma isolada; o interesse é o **conjunto**, pois combinações específicas
    revelam forças e fragilidades.

    **b) Técnicas estatísticas.** Para comparação equilibrada, os índices passam por **padronização (z-score)**,
    que os coloca em uma escala comum (média zero, desvio-padrão um), evitando que um indicador pese mais apenas
    por ter valores naturalmente maiores. Em seguida, emprega-se **PCA (Análise de Componentes Principais)**,
    que organiza informações correlacionadas em poucos **fatores independentes**. Duas noções guiam a leitura:
    **cargas (loadings)**, que indicam a contribuição de cada índice em um fator, e **variância explicada**,
    que mostra quanto do comportamento total aquele fator representa. Na prática, a PCA reduz complexidade e
    destaca **quais índices realmente dirigem** o resultado em cada caso.

    **c) Ponderação temporal.** Para refletir a situação atual sem perder contexto, os escores anuais são
    combinados com pesos **60% (t)**, **25% (t−1)** e **15% (t−2)**. O efeito é valorizar o desempenho recente,
    preservando tendência e reduzindo a influência de anos atípicos.
    """)

    # Fluxograma do cálculo
    fluxograma = ASSETS_PATH / "finscore_pipeline.png"
    if fluxograma.exists():
        st.image(str(fluxograma), use_column_width=True)
    else:
        st.info("Fluxograma não encontrado em assets. Esperado: `finscore_pipeline.png`.")

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

    # 4) Ponderação temporal (texto + imagem)
    st.markdown("#### Ponderação temporal")
    st.markdown("""
    O FinScore utiliza até três exercícios consecutivos para equilibrar **recência** e **consistência histórica**.
    A distribuição de pesos é **60%** para o ano mais recente, **25%** para o ano anterior e **15%** para o ano anterior a esse.
    """)
    pesos_img = ASSETS_PATH / "finscore_pesos_temporais.png"
    if pesos_img.exists():
        st.image(str(pesos_img), use_column_width=False)
        st.caption("Ano t: 60% · Ano t−1: 25% · Ano t−2: 15%")
    else:
        st.info("Gráfico de pesos não encontrado em assets. Esperado: `finscore_pesos_temporais.png`.")

    # 5) Faixas de risco (texto + imagem)
    st.markdown("#### Faixas de risco (FinScore 0–1000)")
    st.markdown("""
    O escore final é convertido para a escala **0–1000** e classificado em faixas de risco predefinidas,
    facilitando a comunicação para decisão de crédito.
    """)
    faixas_img = ASSETS_PATH / "finscore_faixas_risco.png"
    if faixas_img.exists():
        st.image(str(faixas_img), use_column_width=True)
    else:
        st.info("Gráfico de faixas não encontrado em assets. Esperado: `finscore_faixas_risco.png`.")

def _sec_glossario():
    st.subheader("Glossário")
    st.write("Esta é a página de glossário.")
    # TODO: conteúdo do glossário

def _sec_faq():
    st.subheader("FAQ")
    st.write("Esta é a página de FAQ.")
    # TODO: perguntas e respostas

def render():
    # --- CSS desta view: CENTRALIZAR A BARRA DE ABAS ---
    st.markdown(
        """
        <style>
        /* Centraliza o container das abas nesta página */
        div[data-testid="stTabs"] > div[role="tablist"],
        div[data-baseweb="tab-list"]{
            display:flex;
            justify-content:center;
        }
        /* Mantém largura natural dos botões de aba */
        div[data-testid="stTabs"] button[role="tab"],
        div[data-baseweb="tab"]{
            flex: 0 0 auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # abas internas
    tab_met, tab_glos, tab_faq = st.tabs(TAB_LABELS)

    with tab_met:
        _sec_metodologia()

    with tab_glos:
        _sec_glossario()

    with tab_faq:
        _sec_faq()
