# app_front/views/sobre.py
import streamlit as st
from pathlib import Path

# rótulos com ícones
TAB_LABELS = ["🧭 Metodologia", "📚 Glossário", "❓ FAQ"]

def _sec_metodologia():
    import pandas as pd

    st.subheader("FinScore")

    st.markdown("""
    O **FinScore** é um índice sintético (0–1000) que busca deduzir a higidez patrimonial, econômica, financeira 
                e o risco de crédito de uma empresa, a partir da análise quantitativa de suas demonstrações 
                contábeis recentes. O método foi desenhado para ser objetivo, comparável entre empresas e sensível
                 a mudanças de tendência, consoante a variância temporal dos dados.
    """)

    st.markdown("#### Metodologia")
    st.markdown("""
    O cálculo do FinScore é composto pelas seguintes etapas:

    **1. Cálculo dos Índices Contábeis**  
    A partir dos dados brutos das demonstrações, são extraídos indicadores que cobrem dimensões essenciais:
    - **Rentabilidade** (ex: Margem Líquida, ROA, ROE, Margem EBITDA);
    - **Alavancagem e Endividamento** (ex: Alavancagem, Endividamento, Cobertura de Juros);
    - **Estrutura de Capital** (ex: Imobilizado/Ativo);
    - **Eficiência Operacional** (ex: Giro do Ativo, Períodos Médios de Recebimento e Pagamento);
    - **Liquidez** (ex: Liquidez Corrente, Liquidez Seca, CCL/Ativo Total).
    Esses índices são calculados para até três exercícios consecutivos, permitindo captar evolução e consistência.

    **2. Padronização Estatística**  
    Para garantir comparabilidade, todos os índices são padronizados via z-score (média zero, desvio-padrão um), evitando distorções por escalas distintas.

    **3. Redução de Dimensionalidade (PCA)**  
    Utiliza-se a Análise de Componentes Principais (PCA) para condensar a informação dos índices em poucos fatores independentes (componentes principais). Cada componente é uma combinação linear dos índices originais, e sua importância é medida pela variância explicada. Os loadings (cargas) indicam o peso de cada índice em cada componente, permitindo interpretar quais fatores mais influenciam o resultado.

    **4. Consolidação Temporal**  
    O FinScore considera até três anos, atribuindo maior peso ao desempenho mais recente. Os escores anuais (obtidos pela combinação dos componentes principais ponderados pela variância explicada) são agregados de forma decrescente do mais recente ao mais antigo, refletindo tanto a situação atual quanto a tendência histórica.

    **5. Escalonamento e Classificação**  
    O escore consolidado é transformado para a escala 0–1000, onde valores mais altos indicam menor risco. O resultado é classificado em faixas interpretativas, facilitando a comunicação e a tomada de decisão:
    - Muito Abaixo do Risco;
    - Levemente Abaixo do Risco;
    - Neutro;
    - Levemente Acima do Risco;
    - Muito Acima do Risco.

    **Interpretação dos Resultados**  
    - **FinScore próximo de 1000:** Empresa com perfil financeiro robusto, baixo risco de crédito e boa performance recente.
    - **FinScore intermediário (250–750):** Situação neutra, sem sinais claros de risco elevado ou excelência.
    - **FinScore próximo de 0:** Indica fragilidades relevantes, alto risco de crédito ou deterioração recente.
    A análise dos índices e dos principais componentes permite identificar quais dimensões (liquidez, rentabilidade, endividamento, eficiência) mais impactaram o resultado, apoiando diagnósticos e recomendações.
    """)

    # 3) Índices considerados (tabela)
    st.markdown("#### Índices utilizados")
    st.markdown("""
    Os índices abaixo são calculados a partir das demonstrações contábeis e representam diferentes dimensões da saúde financeira da empresa. Cada índice contribui de forma específica para o diagnóstico, permitindo uma análise multifacetada do risco e da performance.
    """)
    ASSETS_PATH = Path(__file__).resolve().parents[1] / "assets"
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
        st.markdown("""
        **Como interpretar:**
        - Índices de rentabilidade altos sugerem boa geração de lucro.
        - Índices de liquidez elevados indicam maior capacidade de honrar compromissos de curto prazo.
        - Alavancagem e endividamento devem ser analisados em conjunto com a cobertura de juros e a estrutura de capital.
        - Eficiência operacional e prazos ajudam a entender o ciclo financeiro e a gestão de ativos.
        A análise integrada desses índices permite identificar pontos fortes e vulnerabilidades específicas da empresa.
        """)
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
        st.image(str(pesos_img), use_column_width=False, width=550)
        st.caption("Ano t: 60% · Ano t−1: 25% · Ano t−2: 15%")
    else:
        st.info("Gráfico de pesos não encontrado em assets. Esperado: `finscore_pesos_temporais.png`.")

    # 5) Faixas de risco (tabela explicativa)
    st.markdown("#### Faixas de risco (FinScore 0–1000)")
    st.markdown("""
    Após o cálculo, o FinScore é convertido para a escala de 0 a 1000 e classificado em faixas que facilitam a comunicação do risco de crédito. Cada faixa representa um perfil de risco distinto, auxiliando na tomada de decisão e na comparação entre empresas.
    """)
    import pandas as pd
    faixas = [
        {"Faixa": "Muito Abaixo do Risco", "Intervalo": "> 875", "Descrição": "Perfil financeiro excepcional, risco mínimo."},
        {"Faixa": "Levemente Abaixo do Risco", "Intervalo": "751 – 875", "Descrição": "Situação confortável, baixo risco."},
        {"Faixa": "Neutro", "Intervalo": "250 – 750", "Descrição": "Situação intermediária, sem sinais claros de risco elevado ou excelência."},
        {"Faixa": "Levemente Acima do Risco", "Intervalo": "126 – 249", "Descrição": "Atenção: sinais de fragilidade financeira."},
        {"Faixa": "Muito Acima do Risco", "Intervalo": "≤ 125", "Descrição": "Risco elevado, recomenda-se análise detalhada."},
    ]
    st.table(pd.DataFrame(faixas))
    st.markdown("""
    **Como interpretar:**
    - Empresas classificadas como **Muito Abaixo do Risco** apresentam excelente robustez financeira e baixíssima probabilidade de inadimplência.
    - **Levemente Abaixo do Risco** indica conforto, mas recomenda-se monitoramento.
    - **Neutro** sugere situação estável, mas sem garantias de excelência ou risco iminente.
    - **Levemente Acima do Risco** e **Muito Acima do Risco** demandam atenção, podendo indicar problemas estruturais ou conjunturais.
    A classificação deve ser sempre analisada em conjunto com os índices detalhados e o contexto do setor.
    """)

def _sec_glossario():
    st.subheader("Glossário")
    st.markdown("""
* **Alavancagem:** Relação entre o capital de terceiros (dívidas) e o capital próprio da empresa. Alta alavancagem pode indicar maior risco financeiro, mas também potencial de retorno.

* **Análise de Componentes Principais (PCA):** Técnica estatística de redução de dimensionalidade que transforma um conjunto de variáveis correlacionadas em um conjunto menor de fatores independentes (componentes principais), preservando a maior parte da variância dos dados.

* **CCL/Ativo Total:** Índice que mede a proporção do Capital Circulante Líquido em relação ao Ativo Total, indicando folga financeira de curto prazo.

* **Cobertura de Juros:** Capacidade da empresa de pagar suas despesas financeiras com o resultado operacional (EBIT). Valores baixos sugerem risco de inadimplência.

* **Eficiência Operacional:** Grau de aproveitamento dos ativos e da gestão dos ciclos financeiros (ex: Giro do Ativo, PMR, PMP) para geração de receita.

* **Endividamento:** Proporção do passivo total em relação ao ativo total, indicando o grau de dependência de capital de terceiros.

* **Escalonamento:** Processo de transformação do escore bruto para uma escala padronizada (0–1000), facilitando a comparação e interpretação dos resultados.

* **Estrutura de Capital:** Composição do financiamento da empresa entre capital próprio e de terceiros, incluindo o peso do ativo imobilizado.

* **Faixas de Risco:** Categorias interpretativas do FinScore, que agrupam empresas conforme o perfil de risco de crédito.

* **Giro do Ativo:** Mede a eficiência da empresa em gerar receita a partir de seus ativos totais.

* **Imobilizado/Ativo:** Proporção do ativo imobilizado em relação ao ativo total, indicando o grau de investimento em ativos fixos.

* **Índices Contábeis:** Indicadores extraídos das demonstrações financeiras que refletem diferentes dimensões da saúde econômico-financeira da empresa.

* **Liquidez Corrente:** Capacidade de a empresa honrar obrigações de curto prazo com seus ativos circulantes.

* **Liquidez Seca:** Similar à liquidez corrente, mas desconsidera estoques, oferecendo visão mais conservadora da liquidez.

* **Margem EBITDA:** Percentual da receita operacional que sobra após despesas operacionais, antes de juros, impostos, depreciação e amortização.

* **Margem Líquida:** Percentual do lucro líquido em relação à receita total, indicando rentabilidade final da empresa.

* **Padronização (z-score):** Transformação dos índices para uma escala comum (média zero, desvio-padrão um), permitindo comparabilidade entre diferentes indicadores.

* **Período Médio de Pagamento (PMP):** Tempo médio (em dias) que a empresa leva para pagar seus fornecedores.

* **Período Médio de Recebimento (PMR):** Tempo médio (em dias) que a empresa leva para receber de seus clientes.

* **Ponderação Temporal:** Processo de atribuir pesos diferentes aos anos analisados, valorizando mais o desempenho recente na composição do FinScore.

* **Rentabilidade:** Capacidade da empresa de gerar lucro a partir de suas receitas e ativos (ex: Margem Líquida, ROA, ROE).

* **ROA (Return on Assets):** Retorno sobre o ativo total, mede a eficiência da empresa em gerar lucro com seus ativos.

* **ROE (Return on Equity):** Retorno sobre o patrimônio líquido, mede a rentabilidade do capital próprio investido.
    """)

def _sec_faq():
    st.subheader("FAQ")
    st.markdown("*Perguntas Frequentes sobre o FinScore e sua aplicação na análise de crédito*")

    faqs = [
        ("O que é o FinScore e como ele difere de outros escores de crédito?",
         "O FinScore é um índice sintético (0–1000) que resume a saúde econômico-financeira da empresa a partir de suas demonstrações contábeis recentes, utilizando técnicas estatísticas avançadas (padronização, PCA e ponderação temporal). Diferente de escores tradicionais, como o Serasa, que se baseiam em histórico de pagamentos e informações cadastrais, o FinScore foca na estrutura e performance financeira real da empresa, permitindo uma análise complementar e mais profunda do risco de crédito."),
        ("Como a metodologia do FinScore transforma dados contábeis em um escore objetivo?",
         "Os dados contábeis são convertidos em diversos índices financeiros, que são padronizados e sintetizados por meio de PCA, reduzindo a complexidade e destacando os fatores mais relevantes. O resultado é consolidado ao longo de até três anos, com maior peso para o desempenho recente, e escalonado para a faixa 0–1000, facilitando a comparação entre empresas e períodos."),
        ("Por que usar padronização e PCA?",
         "A padronização garante que todos os índices tenham o mesmo peso inicial, evitando distorções por escalas diferentes. O PCA permite identificar padrões e fatores-chave, reduzindo o risco de interpretações equivocadas por correlações ocultas entre os índices."),
        ("Como interpretar as faixas de risco do FinScore?",
         "As faixas vão de 'Muito Abaixo do Risco' (excelente robustez financeira) até 'Muito Acima do Risco' (alto risco). Empresas nas faixas mais baixas devem ser analisadas com cautela, pois podem apresentar fragilidades estruturais ou conjunturais. A classificação serve como um alerta, mas deve ser sempre contextualizada com os índices detalhados e o setor de atuação."),
        ("Como o FinScore pode ser usado junto ao escore Serasa?",
         "O FinScore e o Serasa são complementares: enquanto o Serasa reflete o histórico de crédito e comportamento de pagamentos, o FinScore revela a real capacidade financeira da empresa. Divergências entre eles podem indicar situações de risco oculto (ex: bom Serasa, mas FinScore baixo) ou oportunidades (ex: FinScore alto, mas histórico de crédito ruim por eventos pontuais)."),
        ("Como um analista deve usar o FinScore na concessão de crédito?",
         "O analista deve considerar o FinScore como um filtro inicial e um guia para aprofundar a análise. Empresas com FinScore baixo exigem investigação detalhada dos índices que puxaram o resultado para baixo. Já empresas com FinScore alto, mas Serasa baixo, podem merecer uma análise qualitativa para identificar se o risco é conjuntural ou estrutural. O cruzamento dos dois escores, aliado ao contexto do setor e à experiência do analista, permite decisões mais seguras e fundamentadas."),
        ("Quais oportunidades de negócio podem ser identificadas com o FinScore?",
         "Além de mitigar riscos, o FinScore pode revelar empresas subavaliadas pelo mercado tradicional, mas com fundamentos sólidos, abrindo espaço para concessão de crédito diferenciada, renegociação de condições ou oferta de produtos financeiros customizados."),
        ("O que fazer se os índices contábeis apresentarem sinais contraditórios?",
         "O FinScore sintetiza múltiplos índices, mas o analista deve sempre investigar casos de divergência (ex: alta liquidez, mas baixa rentabilidade). A análise detalhada dos componentes principais e dos índices individuais é fundamental para entender a real situação da empresa."),
        ("O FinScore pode ser usado para monitoramento contínuo?",
         "Sim. O acompanhamento periódico do FinScore permite identificar tendências de melhora ou deterioração, antecipando riscos e oportunidades antes que se reflitam no histórico de crédito tradicional."),
        ("Como justificar uma decisão de crédito baseada no FinScore?",
         "O FinScore oferece transparência metodológica: cada resultado pode ser decomposto nos índices e fatores que o compõem, permitindo justificar decisões com base em dados objetivos e rastreáveis, o que é fundamental para governança e compliance."),
        ("O FinScore pode ser aplicado a empresas de todos os portes e setores?",
         "Sim, desde que as demonstrações contábeis estejam disponíveis e minimamente padronizadas. Recomenda-se, porém, considerar particularidades setoriais e adaptar a análise qualitativa conforme o contexto."),
        ("Quais são as limitações do FinScore?",
         "O FinScore depende da qualidade e integridade das informações contábeis. Empresas com dados inconsistentes, defasados ou manipulados podem ter escores distorcidos. Além disso, eventos extraordinários recentes podem não ser totalmente captados."),
        ("Como o FinScore lida com empresas em crescimento acelerado ou em crise?",
         "O uso de múltiplos anos e a ponderação temporal ajudam a suavizar efeitos de anos atípicos, mas o analista deve sempre investigar variações abruptas e buscar explicações qualitativas para mudanças bruscas no escore."),
        ("O FinScore pode ser auditado ou validado externamente?",
         "Sim. Toda a metodologia é transparente e os cálculos podem ser reproduzidos a partir dos dados e fórmulas apresentados, facilitando auditorias e validações por terceiros."),
        ("Como o FinScore pode apoiar políticas de crédito mais justas e inclusivas?",
         "Ao focar em fundamentos financeiros e não apenas em histórico de crédito, o FinScore pode identificar empresas com potencial, mas que foram penalizadas por eventos pontuais ou falta de histórico, promovendo inclusão financeira responsável."),
        ("O FinScore pode ser integrado a sistemas automatizados de decisão de crédito?",
         "Sim, a estrutura do FinScore permite integração via API ou processamento em lote, facilitando a automação de políticas de crédito e monitoramento de carteiras."),
        ("Como o FinScore trata empresas com poucos anos de histórico contábil?",
         "O cálculo se adapta ao número de anos disponíveis (até três), ajustando os pesos conforme a quantidade de períodos informados, sem comprometer a comparabilidade."),
        ("O FinScore pode ser manipulado por práticas contábeis agressivas?",
         "Embora a metodologia seja robusta, práticas contábeis agressivas ou criativas podem distorcer os índices. Por isso, recomenda-se sempre análise crítica dos dados e, se necessário, ajustes qualitativos."),
        ("Como o FinScore pode ser usado em conjunto com análise qualitativa?",
         "O FinScore deve ser visto como ponto de partida. A análise qualitativa (governança, mercado, gestão, eventos recentes) complementa e enriquece a avaliação, reduzindo riscos de decisões baseadas apenas em números."),
        ("O FinScore pode ser utilizado para renegociação de dívidas ou revisão de limites de crédito?",
         "Sim. Mudanças positivas no FinScore podem embasar renegociações, concessão de melhores condições ou revisão de limites, enquanto deteriorações sinalizam necessidade de revisão de exposição e acompanhamento mais próximo."),
    ]

    for i, (pergunta, resposta) in enumerate(faqs, 1):
        with st.expander(f"**{i}. {pergunta}**"):
            st.markdown(resposta)

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