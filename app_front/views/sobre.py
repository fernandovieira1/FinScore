# app_front/views/sobre.py
from __future__ import annotations
import streamlit as st
from pathlib import Path

# rótulos com ícones
TAB_LABELS = ["🧭 Metodologia", "📚 Glossário", "❓ FAQ"]

def _sec_metodologia():
    import pandas as pd

    st.markdown("<h3 style='text-align: left;'>🛞 Metodologia</h3>", unsafe_allow_html=True)
    st.markdown("""
O FinScore é um índice sintético (0–1000) que busca deduzir a higidez patrimonial, econômica, financeira e o risco de crédito de uma empresa, a partir da análise quantitativa de suas demonstrações contábeis recentes. O método foi desenhado para ser objetivo, comparável entre empresas e sensível a mudanças de tendência, consoante a variância temporal dos dados.

O cálculo do FinScore segue uma abordagem inspirada em metodologias consagradas de análise de crédito e avaliação de risco, como Altman Z-Score (Altman, 1968) e modelos de escore estatístico, adaptando-as à realidade brasileira e à disponibilidade de dados contábeis. O processo é dividido em cinco etapas principais, que garantem robustez, comparabilidade e sensibilidade ao contexto econômico das empresas analisadas.
    """)

    # 1. Metodologia (5 passos)
    st.markdown("### 1. Etapas do Cálculo do FinScore")
    st.markdown("""
O cálculo do FinScore é composto por cinco etapas sequenciais, cada uma com papel fundamental para garantir a qualidade e a utilidade do índice. A seguir, detalhamos cada passo:
    """)

    st.markdown("**(i) Cálculo dos Índices Contábeis**  ")
    st.markdown("""
A partir dos dados brutos das demonstrações, são extraídos indicadores que cobrem dimensões essenciais:

- **Rentabilidade** (ex: Margem Líquida, ROA, ROE, Margem EBITDA);
- **Alavancagem e Endividamento** (ex: Alavancagem, Endividamento, Cobertura de Juros);
- **Estrutura de Capital** (ex: Imobilizado/Ativo);
- **Eficiência Operacional** (ex: Giro do Ativo, Períodos Médios de Recebimento e Pagamento);
- **Liquidez** (ex: Liquidez Corrente, Liquidez Seca, CCL/Ativo Total).

Esses índices são calculados para até três exercícios consecutivos, permitindo captar evolução e consistência.
    """)

    st.markdown("**(ii) Padronização Estatística**  ")
    st.markdown("""
Para garantir comparabilidade, todos os índices são padronizados via z-score (média zero, desvio-padrão um), evitando distorções por escalas distintas. Essa etapa é fundamental para que indicadores de diferentes naturezas possam ser combinados de forma justa.
    """)

    st.markdown("**(iii) Redução de Dimensionalidade (PCA)**  ")
    st.markdown("""
Utiliza-se a Análise de Componentes Principais (PCA) para condensar a informação dos índices em poucos fatores independentes (componentes principais). Cada componente é uma combinação linear dos índices originais, e sua importância é medida pela variância explicada. Os loadings (cargas) indicam o peso de cada índice em cada componente, permitindo interpretar quais fatores mais influenciam o resultado.
    """)

    st.markdown("**(iv) Consolidação Temporal**  ")
    st.markdown("""
O FinScore considera até três anos, atribuindo maior peso ao desempenho mais recente. Os escores anuais (obtidos pela combinação dos componentes principais ponderados pela variância explicada) são agregados de forma decrescente do mais recente ao mais antigo, refletindo tanto a situação atual quanto a tendência histórica.
    """)

    st.markdown("**(v) Escalonamento e Classificação**  ")
    st.markdown("""
O escore consolidado é transformado para a escala 0–1000, onde valores mais altos indicam menor risco. O resultado é classificado em faixas interpretativas, facilitando a comunicação e a tomada de decisão.
    """)

    st.markdown("Essas etapas, em conjunto, garantem que o FinScore seja um índice robusto, transparente e adaptável a diferentes contextos empresariais.")

    # 2. Índices utilizados
    st.markdown("### 2. Índices utilizados")
    st.markdown("""
Os índices utilizados no cálculo do FinScore foram selecionados por sua relevância na literatura de análise financeira e sua capacidade de captar diferentes dimensões do risco de crédito. Eles abrangem rentabilidade, liquidez, alavancagem, eficiência operacional e estrutura de capital.
    """)
    ASSETS_PATH = Path(__file__).resolve().parents[1] / "assets"
    tabela_csv = ASSETS_PATH / "finscore_indices_formulas.csv"
    if tabela_csv.exists():
        df = pd.read_csv(tabela_csv)
        st.table(df)
        st.markdown("""
        A análise integrada desses índices permite identificar pontos fortes e vulnerabilidades específicas da empresa, apoiando diagnósticos mais precisos e decisões de crédito fundamentadas.
        """)
    else:
        st.info("Tabela de índices não encontrada em assets. Esperado: `finscore_indices_formulas.csv`.")

    # 3. Interpretação dos Resultados (faixas de risco)
    st.markdown("### 3. Interpretação dos Resultados")
    st.markdown("""
O FinScore, após ser calculado e escalonado, é classificado em faixas que facilitam a comunicação do risco de crédito. Cada faixa representa um perfil de risco distinto, auxiliando na tomada de decisão e na comparação entre empresas.
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

    # 4. Ponderação temporal
    st.markdown("### 4. Ponderação temporal")
    st.markdown("""
O FinScore utiliza até três exercícios consecutivos para equilibrar recência e consistência histórica. A distribuição de pesos é 60% para o ano mais recente, 25% para o ano anterior e 15% para o ano anterior a esse.
    """)
    pesos_img = ASSETS_PATH / "finscore_pesos_temporais.png"
    if pesos_img.exists():
        st.image(str(pesos_img), use_column_width=False, width=550)
        st.caption("Ano t: 60% · Ano t−1: 25% · Ano t−2: 15%")
    else:
        st.info("Gráfico de pesos não encontrado em assets. Esperado: `finscore_pesos_temporais.png`.")
    st.markdown("""
Essa ponderação permite que o FinScore seja sensível a mudanças recentes, sem perder de vista a trajetória histórica da empresa.
    """)

def _sec_glossario():
    st.markdown("<h3 style='text-align: left;'>📇 Glossário</h3>", unsafe_allow_html=True)
    # Dicionário do glossário (A-Z)
    glossario = {
        "A": [
            ("Alavancagem", "Relação entre o capital de terceiros (dívidas) e o capital próprio da empresa. Alta alavancagem pode indicar maior risco financeiro, mas também potencial de retorno."),
            ("Ativo Circulante", "Recursos que a empresa espera converter em dinheiro ou consumir no prazo de um ano (caixa, contas a receber, estoques)."),
            ("Ativo Imobilizado", "Bens tangíveis de longo prazo da empresa, como máquinas, equipamentos, veículos e imóveis."),
            ("Ativo Total", "Conjunto de todos os recursos controlados pela empresa, incluindo circulante, realizável a longo prazo e permanente."),
        ],
        "B": [
            ("BNDES", "Banco Nacional de Desenvolvimento Econômico e Social, instituição financeira pública brasileira de fomento."),
        ],
        "C": [
            ("Capital Circulante Líquido (CCL)", "Diferença entre o ativo circulante e o passivo circulante, indicando a folga financeira de curto prazo."),
            ("CCL/Ativo Total", "Índice que mede a proporção do Capital Circulante Líquido em relação ao Ativo Total, indicando folga financeira de curto prazo."),
            ("Cobertura de Juros", "Capacidade da empresa de pagar suas despesas financeiras com o resultado operacional (EBIT). Valores baixos sugerem risco de inadimplência."),
            ("Componentes Principais", "Fatores estatísticos derivados do PCA que representam combinações lineares das variáveis originais, ordenados por importância."),
            ("Contas a Pagar", "Obrigações da empresa com fornecedores e credores, registradas no passivo circulante."),
            ("Contas a Receber", "Valores que a empresa tem a receber de clientes por vendas realizadas a prazo."),
            ("Custos", "Gastos diretamente relacionados à produção de bens ou prestação de serviços (matéria-prima, mão de obra, etc.)."),
        ],
        "D": [
            ("Demonstrações Contábeis", "Relatórios financeiros obrigatórios que evidenciam a situação patrimonial e financeira da empresa."),
            ("Desvio-padrão", "Medida estatística de dispersão que indica quão distantes os valores estão da média."),
            ("Despesas Financeiras", "Custos relacionados a empréstimos, financiamentos e outras operações de crédito."),
        ],
        "E": [
            ("EBIT", "Earnings Before Interest and Taxes - Lucro antes de juros e impostos, medindo a performance operacional."),
            ("EBITDA", "Earnings Before Interest, Taxes, Depreciation and Amortization - Lucro operacional antes de juros, impostos, depreciação e amortização."),
            ("Eficiência Operacional", "Grau de aproveitamento dos ativos e da gestão dos ciclos financeiros (ex: Giro do Ativo, PMR, PMP) para geração de receita."),
            ("Endividamento", "Proporção do passivo total em relação ao ativo total, indicando o grau de dependência de capital de terceiros."),
            ("Escalonamento", "Processo de transformação do escore bruto para uma escala padronizada (0–1000), facilitando a comparação e interpretação dos resultados."),
            ("Escore", "O mesmo que Score, mas em português."),
            ("Estoques", "Mercadorias, produtos acabados, matérias-primas e produtos em elaboração mantidos pela empresa."),
            ("Estrutura de Capital", "Composição do financiamento da empresa entre capital próprio e de terceiros, incluindo o peso do ativo imobilizado."),
        ],
        "F": [
            ("Faixas de Risco", "Categorias interpretativas do FinScore, que agrupam empresas conforme o perfil de risco de crédito."),
            ("Fornecedores", "Empresas que vendem bens ou serviços à organização, gerando contas a pagar."),
        ],
        "G": [
            ("Giro do Ativo", "Mede a eficiência da empresa em gerar receita a partir de seus ativos totais."),
            ("Governança", "Conjunto de práticas e controles para direção e monitoramento de uma empresa."),
        ],
        "H": [
            ("Histórico de Crédito", "Registro do comportamento de pagamento de uma empresa ao longo do tempo."),
        ],
        "I": [
            ("Imobilizado/Ativo", "Proporção do ativo imobilizado em relação ao ativo total, indicando o grau de investimento em ativos fixos."),
            ("Inadimplência", "Situação de não cumprimento de obrigações financeiras dentro do prazo estabelecido."),
            ("Índices Contábeis", "Indicadores extraídos das demonstrações financeiras que refletem diferentes dimensões da saúde econômico-financeira da empresa."),
        ],
        "J": [
            ("Juros", "Remuneração cobrada pelo uso de capital de terceiros em empréstimos e financiamentos."),
        ],
        "K": [],
        "L": [
            ("Liquidez Corrente", "Capacidade de a empresa honrar obrigações de curto prazo com seus ativos circulantes."),
            ("Liquidez Seca", "Similar à liquidez corrente, mas desconsidera estoques, oferecendo visão mais conservadora da liquidez."),
            ("Loadings", "Coeficientes que indicam o peso de cada variável original nos componentes principais do PCA."),
            ("Lucro Líquido", "Resultado final da empresa após deduzir todos os custos, despesas e impostos da receita."),
        ],
        "M": [
            ("Margem EBITDA", "Percentual da receita operacional que sobra após despesas operacionais, antes de juros, impostos, depreciação e amortização."),
            ("Margem Líquida", "Percentual do lucro líquido em relação à receita total, indicando rentabilidade final da empresa."),
            ("Média", "Valor central de um conjunto de dados, calculado pela soma dividida pelo número de observações."),
        ],
        "N": [],
        "O": [
            ("Obrigações", "Compromissos financeiros que a empresa deve cumprir, registrados no passivo."),
        ],
        "P": [
            ("Padronização (z-score)", "Transformação dos índices para uma escala comum (média zero, desvio-padrão um), permitindo comparabilidade entre diferentes indicadores."),
            ("Passivo Circulante", "Obrigações da empresa que devem ser pagas no prazo de um ano (fornecedores, empréstimos de curto prazo, impostos)."),
            ("Passivo Total", "Conjunto de todas as obrigações da empresa, incluindo circulante e não circulante."),
            ("Patrimônio Líquido", "Recursos próprios da empresa, representando a diferença entre ativo total e passivo total."),
            ("Período Médio de Pagamento (PMP)", "Tempo médio (em dias) que a empresa leva para pagar seus fornecedores."),
            ("Período Médio de Recebimento (PMR)", "Tempo médio (em dias) que a empresa leva para receber de seus clientes."),
            ("Ponderação Temporal", "Processo de atribuir pesos diferentes aos anos analisados, valorizando mais o desempenho recente na composição do FinScore."),
        ],
        "Q": [],
        "R": [
            ("Receita", "Valor total das vendas ou prestação de serviços da empresa em determinado período."),
            ("Rentabilidade", "Capacidade da empresa de gerar lucro a partir de suas receitas e ativos (ex: Margem Líquida, ROA, ROE)."),
            ("Resultado Operacional", "Lucro ou prejuízo gerado pelas atividades principais da empresa, antes de considerar aspectos financeiros."),
            ("ROA (Return on Assets)", "Retorno sobre o ativo total, mede a eficiência da empresa em gerar lucro com seus ativos."),
            ("ROE (Return on Equity)", "Retorno sobre o patrimônio líquido, mede a rentabilidade do capital próprio investido."),
        ],
        "S": [
            ("Serasa", "Empresa brasileira de análise e informações para decisões de crédito e apoio a negócios; Escore de crédito amplamente utilizado no Brasil para avaliar o risco de inadimplência de empresas e indivíduos."),
            ("Score", "Índice numérico que representa a avaliação de risco de crédito de uma empresa ou indivíduo. Raiz inglesa da palavra Escore."),
            ("Setor de Atuação", "Segmento econômico em que a empresa opera, influenciando seus riscos e oportunidades."),
            ("Soluções Financeiras", "Produtos e serviços oferecidos por instituições financeiras para atender às necessidades das empresas."),
        ],
        "T": [],
        "U": [],
        "V": [
            ("Variância Explicada", "Medida estatística que indica quanto da variabilidade dos dados é capturada por cada componente principal."),
        ],
        "W": [],
        "X": [],
        "Y": [],
        "Z": [
            ("Z-Score", "Medida estatística que indica quantos desvios-padrão um valor está distante da média, usado na padronização."),
        ],
    }

    letras = [chr(i) for i in range(ord("A"), ord("Z") + 1)]

    st.markdown("""
    <style>
    .glossario-barra {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 8px;
        margin: 0 auto 18px auto;
        padding: 8px 0 4px 0;
        max-width: 700px;
        font-family: inherit;
        font-size: 1rem;
    }
    .glossario-letra {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 5px;
        background: #eaf7f1;
        color: #5ea68d !important;
        font-weight: bold;
        text-decoration: none;
        font-size: 1rem;
        transition: background 0.2s, color 0.2s;
        line-height: 1.6;
        margin: 0;
        font-family: inherit;
        border: 1px solid #5ea68d22;
        box-shadow: none;
    }
    .glossario-letra:hover {
        background: #5ea68d;
        color: #fff !important;
    }
    .glossario-letra.desabilitada {
        background: #f2f2f2;
        color: #bdbdbd;
        pointer-events: none;
        cursor: default;
        border: 1px solid #e0e0e0;
    }
    html {
        scroll-behavior: smooth;
    }
    #topo {
        position: relative;
        top: -80px;
        padding-top: 80px;
    }
    .glossario-voltar {
        display: inline-block;
        margin-top: 8px;
        font-size: 0.95em;
        color: #5ea68d;
        text-decoration: underline;
        cursor: pointer;
        transition: color 0.2s;
    }
    .glossario-voltar:hover {
        color: #388e6c;
    }
    .glossario-letra-titulo {
        font-size: 1.5em;
        font-weight: bold;
        margin-top: 32px;
        margin-bottom: 10px;
        color: #5ea68d;
    }
    </style>
    """, unsafe_allow_html=True)

    # Barra de letras A–Z
    barra_html = '<div class="glossario-barra" id="topo">'
    for letra in letras:
        if glossario.get(letra) and len(glossario[letra]) > 0:
            barra_html += f'<a class="glossario-letra" href="#{letra}">{letra}</a>'
        else:
            barra_html += f'<span class="glossario-letra desabilitada">{letra}</span>'
    barra_html += '</div>'
    st.markdown(barra_html, unsafe_allow_html=True)

    # Seções do glossário
    for letra in letras:
        termos = glossario.get(letra, [])
        if termos:
            st.markdown(f'<div id="{letra}"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="glossario-letra-titulo">{letra}</div>', unsafe_allow_html=True)
            for termo, definicao in termos:
                st.markdown(f'**{termo}**<br><span style="color:#444;">{definicao}</span>', unsafe_allow_html=True)
            st.markdown(
                '<a href="#topo" class="glossario-voltar">↑ voltar ao topo</a>',
                unsafe_allow_html=True
            )

def _sec_faq():

    st.markdown("""
    <style>
    /* Remove qualquer borda e sombra dos expanders do FAQ em todos os temas */
    div[data-testid="stExpander"],
    div[data-testid="stExpander"] *,
    div[data-testid="stExpander"] > div,
    div[data-testid="stExpander"] .st-emotion-cache-1v0mbdj,
    div[data-testid="stExpander"] .st-emotion-cache-1v0mbdj * {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: left;'>🛣️ Questões mais frequentes</h3>", unsafe_allow_html=True)

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
