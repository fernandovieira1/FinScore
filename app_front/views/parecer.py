import math
import json
from typing import Dict, Any, Optional

import streamlit as st

from components.policy_engine import PolicyInputs, decide
from components.llm_client import _invoke_model, MODEL_NAME

# Usar temperatura 0 para máxima determinism e reduzir erros ortográficos
PARECER_TEMPERATURE = 0.0

RANK_SERASA = {"Excelente": 1, "Bom": 2, "Baixo": 3, "Muito Baixo": 4}
RANK_FINSCORE = {
    "Muito Abaixo do Risco": 1,
    "Levemente Abaixo do Risco": 2,
    "Neutro": 3,
    "Levemente Acima do Risco": 4,
    "Muito Acima do Risco": 5,
}


def _safe_float(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _latest_indices_row(out_dict):
    df = out_dict.get("df_indices") if out_dict else None
    if df is None or getattr(df, "empty", True):
        return {}
    try:
        return df.iloc[0].to_dict()
    except Exception:
        return {}


def _extract_analysis_data(out_dict) -> Dict[str, Any]:
    """
    Extrai dados consolidados de gráficos e tabelas para o parecer.
    """
    indices_row = _latest_indices_row(out_dict)
    df_raw = out_dict.get("df_raw")
    
    # Dados básicos
    data = {
        "finscore_bruto": out_dict.get("finscore_bruto"),
        "finscore_ajustado": out_dict.get("finscore_ajustado"),
        "classificacao_finscore": out_dict.get("classificacao_finscore"),
        "serasa": out_dict.get("serasa"),
        "classificacao_serasa": out_dict.get("classificacao_serasa"),
    }
    
    # Índices chave de liquidez
    data["liquidez_corrente"] = _safe_float(indices_row.get("Liquidez Corrente"))
    data["liquidez_seca"] = _safe_float(indices_row.get("Liquidez Seca"))
    data["ccl_ativo"] = _safe_float(indices_row.get("CCL/Ativo Total"))
    
    # Índices de estrutura/endividamento
    data["alavancagem"] = _safe_float(indices_row.get("Alavancagem"))  # DL/EBITDA
    data["endividamento"] = _safe_float(indices_row.get("Endividamento"))
    data["cobertura_juros"] = _safe_float(indices_row.get("Cobertura de Juros"))
    
    # Índices de rentabilidade
    data["roe"] = _safe_float(indices_row.get("ROE"))
    data["roa"] = _safe_float(indices_row.get("ROA"))
    data["margem_liquida"] = _safe_float(indices_row.get("Margem Líquida"))
    data["margem_ebitda"] = _safe_float(indices_row.get("Margem EBITDA"))
    
    # Índices de eficiência
    data["pmr"] = _safe_float(indices_row.get("Período Médio de Recebimento"))
    data["pmp"] = _safe_float(indices_row.get("Período Médio de Pagamento"))
    data["giro_ativo"] = _safe_float(indices_row.get("Giro do Ativo"))
    
    # Dados patrimoniais (último ano disponível)
    if df_raw is not None and not df_raw.empty:
        try:
            ultimo_ano = df_raw.iloc[-1]
            data["receita_total"] = _safe_float(ultimo_ano.get("r_Receita_Total"))
            data["lucro_liquido"] = _safe_float(ultimo_ano.get("r_Lucro_Liquido"))
            data["ativo_total"] = _safe_float(ultimo_ano.get("p_Ativo_Total"))
            data["patrimonio_liquido"] = _safe_float(ultimo_ano.get("p_Patrimonio_Liquido"))
            data["passivo_total"] = _safe_float(ultimo_ano.get("p_Passivo_Total"))
        except Exception:
            pass
    
    # PCA (se disponível)
    data["pca_variancia_pc1"] = out_dict.get("pca_explained_variance", [None])[0] if out_dict.get("pca_explained_variance") else None
    
    return data


def _build_parecer_prompt(
    decisao_motor: str,
    motivos_motor: list,
    covenants_motor: list,
    analysis_data: Dict[str, Any],
    meta_cliente: Dict[str, Any]
) -> str:
    """
    Constrói o prompt para a IA gerar o parecer narrativo.
    """
    empresa = meta_cliente.get("empresa", "N/A")
    cnpj = meta_cliente.get("cnpj", "N/A")
    
    # Formatar dados para o prompt
    dados_formatados = json.dumps(analysis_data, ensure_ascii=False, indent=2, default=str)
    
    prompt = f"""
Você é um analista de crédito sênior. Redija um parecer financeiro técnico, claro e analítico em **Markdown puro** (sem HTML).

**DADOS DA EMPRESA:**
- Empresa: {empresa}
- CNPJ: {cnpj}

**DECISÃO DETERMINÍSTICA (INALTERÁVEL):**
- Decisão: {decisao_motor}
- Motivos: {', '.join(motivos_motor) if motivos_motor else 'Nenhum motivo específico'}
- Covenants: {', '.join(covenants_motor) if covenants_motor else 'Nenhum covenant'}

**DADOS FINANCEIROS:**
{dados_formatados}

**ESTRUTURA OBRIGATÓRIA (siga exatamente):**

## 1. Introdução

**Primeiro parágrafo:** Apresente a empresa ({empresa}, CNPJ {cnpj}) e o objetivo do parecer: avaliar sua capacidade de crédito com base nos indicadores financeiros e no FinScore.

**Segundo parágrafo (Síntese Executiva):** Em 5–8 linhas, apresente:
- Destaques principais: FinScore e Serasa (valores e classificações)
- Pontos fortes e eventuais fragilidades identificadas
- Conclusão direta sobre a decisão de crédito ({decisao_motor}), com justificativa objetiva
- Indicação se há ou não covenants necessários

**Terceiro parágrafo (Estrutura do Parecer):** Descreva brevemente como este parecer está organizado, explicando que as próximas seções abordarão: (i) a metodologia do FinScore e Serasa; (ii) a análise detalhada dos indicadores financeiros por categoria (liquidez, endividamento, rentabilidade e eficiência); (iii) a análise de risco e scoring; e (iv) as considerações finais com recomendações e covenants, se aplicáveis.

---

## 2. Metodologia

A decisão de crédito apresentada neste parecer não se baseia em impressões subjetivas ou análises superficiais, mas sim em uma **avaliação técnica estruturada** que combina dois instrumentos complementares: o **FinScore** (um índice proprietário baseado em dados contábeis) e o **Serasa Score** (um indicador externo de mercado baseado em histórico de crédito). A seguir, detalhamos como cada um desses instrumentos funciona, o que medem e como se integram para formar uma visão holística do risco de crédito.

### 2.1 FinScore

O **FinScore** é um índice sintético que condensa, em um único número (escala de 0 a 1000), a saúde financeira da empresa. Pense nele como um "raio-X quantitativo" que captura simultaneamente a capacidade de pagar contas, a eficiência em gerar lucros, o equilíbrio entre dívidas e capital próprio, e a produtividade dos ativos. Inspirado em metodologias consagradas internacionalmente (como o Altman Z-Score), o FinScore foi desenvolvido para oferecer uma avaliação objetiva e comparável do risco de inadimplência.

**Como o FinScore é calculado (5 etapas):**

1. **Cálculo de Índices Contábeis**: A partir das demonstrações financeiras da empresa (balanço patrimonial e demonstração de resultados), são extraídos mais de 15 indicadores que cobrem quatro dimensões críticas:
   - **Rentabilidade**: ROE (retorno sobre patrimônio), ROA (retorno sobre ativos), Margem Líquida, Margem EBITDA
   - **Liquidez**: Liquidez Corrente, Liquidez Seca, Capital Circulante Líquido / Ativo Total
   - **Endividamento**: Dívida Líquida / EBITDA, Passivo / Ativo, Cobertura de Juros
   - **Eficiência Operacional**: Giro do Ativo, Prazo Médio de Recebimento (PMR), Prazo Médio de Pagamento (PMP)

2. **Padronização Estatística**: Como esses indicadores possuem escalas diferentes (alguns são percentuais, outros múltiplos, outros dias), eles são padronizados (transformados em z-scores) para que possam ser comparados objetivamente. Isso garante que um indicador de liquidez tenha o mesmo "peso matemático" que um indicador de rentabilidade.

3. **Redução de Dimensionalidade (PCA)**: Com mais de 15 indicadores, há muita informação — mas também redundância (por exemplo, ROE e ROA medem coisas parecidas). A Análise de Componentes Principais (PCA) identifica os **padrões fundamentais** que realmente importam, eliminando ruído e consolidando a informação em poucos fatores independentes.

4. **Consolidação Temporal**: Para evitar que um único ano atípico (seja excepcionalmente bom ou ruim) distorça a avaliação, o FinScore considera até três exercícios consecutivos, mas com pesos diferentes: 60% para o ano mais recente, 25% para o ano anterior e 15% para o mais antigo. Isso equilibra a sensibilidade a mudanças recentes com a estabilidade histórica.

5. **Escalonamento e Classificação**: O resultado final é transformado para a escala 0–1000 e classificado em faixas de risco. Quanto maior o FinScore, menor o risco de inadimplência.

**Por que o FinScore é o indicador primário?** Porque ele reflete a **capacidade financeira estrutural** da empresa — ou seja, se ela tem recursos, gera lucro e está equilibrada financeiramente. Empresas com FinScore elevado tendem a atravessar crises com mais resiliência; empresas com FinScore baixo são vulneráveis a choques de receita ou custos.

**Tabela – Classificação FinScore**

| Faixa de Pontuação | Classificação de Risco | Interpretação |
|-------------------:|:-----------------------|:--------------|
| > 875 | Muito Abaixo do Risco | Perfil financeiro excepcional, risco mínimo |
| 750 – 875 | Levemente Abaixo do Risco | Situação confortável, baixo risco |
| 250 – 750 | Neutro | Situação intermediária, sem sinais claros de excelência ou fragilidade |
| 125 – 250 | Levemente Acima do Risco | Atenção recomendada, sinais de fragilidade |
| < 125 | Muito Acima do Risco | Risco elevado, análise detalhada necessária |

**Exemplo prático:** Uma empresa com FinScore de 820 está na faixa "Levemente Abaixo do Risco", indicando que seus fundamentos financeiros são sólidos, mas não excepcionais. Isso se traduz, na prática, em baixa probabilidade de inadimplência, desde que não haja choques externos severos ou erros graves de gestão.

### 2.2 Serasa Score

O **Serasa Score** é um indicador externo amplamente utilizado no mercado brasileiro. Diferentemente do FinScore, que analisa **o que a empresa é** (sua estrutura financeira interna), o Serasa avalia **como a empresa se comporta** em suas relações de crédito: ela paga em dia? Tem protestos ou negativações? Honrou compromissos passados?

O Serasa não tem acesso às demonstrações financeiras detalhadas da empresa; em vez disso, ele coleta informações de bureaus de crédito, bancos, fornecedores e registros públicos (cartórios, tribunais, etc.). Com base nesse histórico de comportamento, o Serasa atribui uma pontuação de 0 a 1000 que estima a probabilidade de inadimplência nos próximos meses.

**Por que o Serasa é complementar?** Porque ele captura aspectos que o FinScore não consegue ver diretamente. Por exemplo: uma empresa pode ter demonstrações financeiras razoáveis (FinScore neutro), mas histórico de atrasos recorrentes (Serasa baixo), sinalizando problemas de gestão de caixa ou falta de compromisso com credores. Por outro lado, uma empresa pode ter FinScore elevado mas Serasa médio se passou por dificuldades no passado que já foram superadas — nesse caso, a convergência entre os escores reforça a avaliação positiva.

**Tabela – Classificação Serasa**

| Faixa de Pontuação | Classificação | Significado |
|-------------------:|:--------------|:------------|
| 851 – 1000 | Excelente | Histórico de crédito exemplar, paga em dia, sem restrições |
| 701 – 850 | Bom | Comportamento de pagamento satisfatório, baixo risco |
| 0 – 400 | Baixo | Histórico comprometido, atenção necessária (atrasos, negativações) |
| Sem cadastro | Muito Baixo | Ausência de histórico de crédito (empresa nova ou sem relacionamento bancário) |

**Exemplo prático:** Uma empresa com Serasa de 780 está na faixa "Bom", indicando que, historicamente, ela honra seus compromissos. Isso reforça a confiança de que, mesmo em momentos de aperto, ela priorizará o pagamento de credores.

### 2.3 Dados Contábeis e Índices Financeiros

Embora o FinScore já condense mais de 15 indicadores em um único número, **a análise detalhada de cada indicador individualmente** é essencial para compreender **como** e **por que** a empresa atingiu aquele escore. Pense no FinScore como o "diagnóstico geral" e nos índices individuais como os "exames específicos" que explicam o diagnóstico.

**Por que detalhar os índices se eles já estão no FinScore?**

1. **Identificar drivers de risco**: O FinScore pode estar baixo, mas é fundamental saber **qual dimensão** está puxando o escore para baixo. É a liquidez? A rentabilidade? O endividamento? Cada dimensão exige estratégias de mitigação diferentes.

2. **Detectar vulnerabilidades ocultas**: Uma empresa pode ter FinScore razoável, mas apresentar liquidez crítica — um risco que merece atenção imediata, mesmo que o escore geral seja aceitável.

3. **Definir covenants personalizados**: Se a análise detalhada revelar que o endividamento está crescendo rapidamente, um covenant limitando novas dívidas faz sentido. Se a rentabilidade está caindo, um covenant exigindo margem mínima pode ser apropriado.

4. **Compreender tendências**: Dois exercícios com os mesmos índices podem resultar em escores semelhantes, mas se um está melhorando e o outro piorando, as implicações são radicalmente diferentes. A análise temporal identifica trajetórias.

Em síntese: os índices detalhados não substituem o FinScore, mas o **explicam e enriquecem**, oferecendo uma visão granular que fundamenta não apenas a decisão de crédito, mas também as condições e covenants necessários para mitigar riscos específicos.

### 2.4 Critérios de Decisão

A decisão de crédito apresentada neste parecer **não** se baseia em um único número isolado, mas sim na **convergência de múltiplas evidências** analisadas de forma integrada. Trata-se de uma avaliação holística que equilibra dados quantitativos objetivos (escores, índices) com interpretação qualitativa (contexto setorial, tendências temporais, particularidades da empresa). A seguir, explicamos como cada elemento contribui para a decisão final.

**1. FinScore (Indicador Primário)**

O FinScore é a **âncora** da análise. Ele sintetiza, de forma objetiva e estatisticamente rigorosa, a saúde financeira estrutural da empresa. Sua classificação em faixas de risco (Muito Abaixo do Risco, Neutro, Muito Acima do Risco, etc.) orienta a decisão inicial: empresas com FinScore elevado (>750) tendem a ser aprovadas; empresas com FinScore baixo (<250) tendem a ser reprovadas ou aprovadas com condições restritivas.

**Por que o FinScore é o indicador primário?** Porque ele é construído sobre dados contábeis auditados (ou auditáveis), reflete capacidade financeira real, e permite comparação objetiva entre empresas de diferentes portes e setores.

**2. Serasa Score (Validação Cruzada)**

O Serasa complementa o FinScore ao trazer a perspectiva do **histórico de comportamento de crédito**. Enquanto o FinScore diz "a empresa tem capacidade de pagar", o Serasa diz "a empresa costuma pagar". A convergência entre FinScore e Serasa reforça a confiabilidade da avaliação: se ambos são elevados, a aprovação é mais segura. Divergências significativas demandam investigação qualitativa:

- **FinScore alto + Serasa baixo**: Pode indicar inadimplência recente já superada (capacidade recuperada, mas histórico ainda manchado) → Aprovação com ressalvas e covenants.
- **FinScore baixo + Serasa alto**: Pode indicar deterioração financeira recente não captada pelo Serasa (que é retroativo) → Atenção redobrada, possível reprovação.

**3. Índices Financeiros Detalhados (Critérios Complementares)**

A análise granular de liquidez, endividamento, rentabilidade e eficiência operacional permite compreender **o que está por trás do FinScore**. Dois exemplos práticos:

- Uma empresa pode ter FinScore neutro (500 pontos), mas liquidez crítica (Liquidez Corrente < 1,0) → Risco de insolvência de curto prazo, mesmo com escore geral aceitável → Necessário covenant de manutenção de liquidez mínima.
- Uma empresa pode ter FinScore razoável (600 pontos), mas rentabilidade em queda livre (Margem Líquida caindo de 10% para 2% em dois anos) → Trajetória insustentável → Necessário monitoramento trimestral e covenant de margem mínima.

Os índices detalhados também permitem personalizar covenants: se o problema é endividamento crescente, limita-se novas dívidas; se o problema é liquidez, exige-se manutenção de índices mínimos.

**4. Contexto Temporal e Setorial (Interpretação Qualitativa)**

Números não existem no vácuo. A ponderação temporal (60% ano recente, 25% anterior, 15% mais antigo) já está embutida no FinScore, mas a análise qualitativa considera:

- **Tendências**: Uma empresa com FinScore 400 em crescimento (300 → 350 → 400) é menos arriscada que uma com FinScore 400 em queda (600 → 500 → 400).
- **Sazonalidade**: Empresas de setores sazonais (turismo, agronegócio) podem ter índices voláteis que não refletem risco estrutural.
- **Eventos atípicos**: Prejuízos isolados por investimentos estratégicos (abertura de filial, compra de ativo) diferem de prejuízos recorrentes por ineficiência operacional.

**Síntese da Lógica Decisória:**

A decisão final ({decisao_motor}) resulta da **convergência** entre:
- O escore sintético (FinScore) → capacidade financeira estrutural
- A validação externa (Serasa) → histórico de comportamento de crédito
- A análise detalhada dos fundamentos financeiros (índices) → drivers específicos de risco
- A interpretação qualitativa do contexto (tendências, setor, eventos atípicos) → nuances que números isolados não captam

Este parecer apresenta não apenas uma recomendação, mas os **fundamentos técnicos, objetivos e rastreáveis** que a sustentam. A decisão pode ser revisitada, auditada ou contestada — e em todos os casos, os critérios estão claros e documentados.

---

## 3. Análise Detalhada dos Indicadores

Nesta seção, os indicadores financeiros da empresa são examinados em profundidade, organizados por dimensão de análise. Cada categoria de indicadores revela aspectos distintos, mas complementares, da saúde financeira: a capacidade de honrar compromissos de curto prazo (liquidez), o equilíbrio entre capital próprio e de terceiros (endividamento), a eficiência em gerar lucros (rentabilidade), a produtividade operacional (eficiência) e o porte empresarial (dados patrimoniais). A análise detalhada desses indicadores permite compreender **não apenas** os escores sintéticos (FinScore e Serasa), **mas também** os drivers específicos que moldam o perfil de risco da empresa e fundamentam a decisão de crédito.

### 3.1 Liquidez

A liquidez mede a capacidade da empresa de cumprir suas obrigações financeiras de curto prazo sem comprometer suas operações. É um dos pilares fundamentais da análise de crédito, pois indica se a empresa dispõe de recursos suficientes para pagar fornecedores, salários, impostos e parcelas de empréstimos nos próximos meses.

**Indicadores analisados:**
- **Liquidez Corrente**: Quanto de ativo circulante (caixa, contas a receber, estoques) a empresa possui para cada R$ 1,00 de dívida de curto prazo. Um valor acima de 1,0 indica folga; valores próximos de 1,0 sugerem aperto financeiro.
- **Liquidez Seca**: Similar à Liquidez Corrente, mas exclui os estoques (que podem demorar para serem convertidos em dinheiro). É um teste mais rigoroso de solvência imediata.
- **CCL/Ativo Total**: O Capital Circulante Líquido (CCL) representa a diferença entre ativos e passivos circulantes. Quando expresso como proporção do Ativo Total, indica quanto da estrutura patrimonial está disponível para financiar o giro operacional.

**Contexto e implicações práticas:**
Apresente os valores dos três indicadores e **interprete-os em linguagem acessível**. Por exemplo: se a Liquidez Corrente for 2,5, explique que "a empresa possui R$ 2,50 de recursos de curto prazo para cada R$ 1,00 de dívida de curto prazo, o que proporciona uma margem de segurança confortável para enfrentar imprevistos ou quedas temporárias de receita". Se a Liquidez Seca for inferior à Corrente, comente o impacto da dependência de estoques. Se houver deterioração ao longo do tempo, alerte sobre aperto de caixa crescente e possível necessidade de reforço de capital de giro.

### 3.2 Endividamento e Estrutura de Capital

O endividamento revela como a empresa financia suas operações e investimentos: com recursos próprios (patrimônio líquido) ou com capital de terceiros (empréstimos, financiamentos, fornecedores). Um equilíbrio saudável reduz o risco financeiro; endividamento excessivo aumenta a vulnerabilidade a crises de liquidez e eleva o custo de capital.

**Indicadores analisados:**
- **DL/EBITDA (Dívida Líquida sobre EBITDA)**: Mede quantos anos de geração de caixa operacional (EBITDA) seriam necessários para quitar a dívida líquida. Valores acima de 3,0–3,5x geralmente sinalizam alavancagem elevada.
- **Passivo/Ativo (Endividamento Total)**: Percentual do ativo financiado por terceiros. Valores acima de 60–70% indicam dependência significativa de capital externo.
- **Cobertura de Juros**: Quantas vezes o EBITDA cobre as despesas financeiras. Valores abaixo de 2,0x sugerem dificuldade para pagar juros sem comprometer o caixa operacional.

**Contexto e implicações práticas:**
Apresente os valores e **explique suas consequências reais**. Por exemplo: se DL/EBITDA for 4,5x, contextualize que "a empresa precisaria de mais de quatro anos de geração de caixa operacional, mantido o nível atual, para quitar suas dívidas líquidas — um prazo que pode se tornar crítico caso haja retração de receitas ou aumento de custos financeiros". Se a Cobertura de Juros for baixa, alerte que "despesas financeiras consomem parcela significativa do caixa gerado, reduzindo a capacidade de investir em crescimento ou distribuir lucros". Comente também sobre a evolução temporal: aumento de endividamento pode indicar expansão planejada ou deterioração financeira — o contexto importa.

### 3.3 Rentabilidade

A rentabilidade avalia a capacidade da empresa de gerar lucro a partir de suas receitas, ativos e capital investido. É o motor de sustentabilidade no longo prazo: empresas consistentemente rentáveis geram caixa para reinvestir, pagar dívidas e remunerar sócios. Baixa rentabilidade ou prejuízos recorrentes são sinais de alerta crítico.

**Indicadores analisados:**
- **ROE (Retorno sobre Patrimônio Líquido)**: Quanto de lucro a empresa gera para cada R$ 1,00 investido pelos sócios. ROE elevado atrai investidores; ROE negativo indica destruição de valor.
- **ROA (Retorno sobre Ativos)**: Eficiência em gerar lucro com os ativos totais (independentemente de como foram financiados). Útil para comparar empresas de diferentes estruturas de capital.
- **Margem Líquida**: Percentual da receita que se transforma em lucro líquido após todos os custos, despesas e impostos. Margens baixas (<5%) indicam pouca resiliência a variações de custo ou receita.
- **Margem EBITDA**: Percentual da receita que se transforma em caixa operacional (antes de juros, impostos, depreciação e amortização). Reflete eficiência operacional pura.

**Contexto e implicações práticas:**
Apresente os valores e **traduza-os em termos concretos**. Por exemplo: se o ROE for 18%, explique que "os sócios obtêm um retorno de 18% ao ano sobre o capital investido, superior à taxa de juros de mercado e indicativo de que o negócio remunera adequadamente o risco assumido". Se a Margem Líquida for 3%, contextualize que "para cada R$ 100,00 de receita, apenas R$ 3,00 chegam ao bolso dos sócios após pagar todos os custos — uma margem apertada que deixa pouca margem para erros operacionais ou aumentos de custos". Identifique tendências: margens crescentes sugerem ganho de eficiência; margens declinantes podem antecipar problemas de competitividade ou gestão de custos.

### 3.4 Eficiência Operacional

A eficiência operacional mede quão bem a empresa gerencia seu ciclo de caixa e seus ativos para gerar receita. Empresas eficientes recebem rápido, pagam devagar e extraem o máximo de receita de cada real investido em ativos — comportamento que fortalece a liquidez e reduz necessidade de capital de giro.

**Indicadores analisados:**
- **PMR (Prazo Médio de Recebimento)**: Quantos dias, em média, a empresa leva para receber de seus clientes após realizar uma venda. PMR elevado (>60–90 dias) indica concessão de prazos longos ou inadimplência, comprometendo o caixa.
- **PMP (Prazo Médio de Pagamento)**: Quantos dias, em média, a empresa leva para pagar seus fornecedores. PMP elevado pode indicar poder de negociação ou, negativamente, dificuldades de caixa que forçam atrasos.
- **Giro do Ativo**: Quantas vezes ao ano a empresa "gira" seu ativo total em receita (Receita Total / Ativo Total). Giro elevado indica uso eficiente dos ativos; giro baixo sugere ociosidade ou ativos improdutivos.

**Contexto e implicações práticas:**
Apresente os valores e **interprete-os de forma integrada**. Por exemplo: se PMR for 45 dias e PMP for 60 dias, explique que "a empresa consegue uma folga de 15 dias no ciclo financeiro — recebe de clientes antes de pagar fornecedores, o que reduz a necessidade de capital de giro e melhora a liquidez". Se o cenário for inverso (PMR > PMP), alerte que "a empresa precisa financiar o ciclo operacional com recursos próprios ou empréstimos, pressionando o caixa". Se o Giro do Ativo for baixo (<0,5x), comente que "a empresa gera pouca receita em relação ao volume de ativos, sugerindo capacidade ociosa ou ativos não produtivos (como estoques excessivos ou imobilizado subutilizado)". Avalie também a evolução: PMR crescente pode indicar inadimplência ou perda de poder de barganha; PMP declinante pode sinalizar pressão de credores.

### 3.5 Dados Patrimoniais e de Resultado

Para contextualizar os índices analisados, é fundamental compreender o porte e a estrutura financeira da empresa em valores absolutos.

**Principais indicadores:**

| Indicador | Valor |
|-----------|------:|
| Receita Total | [valor] |
| Lucro Líquido | [valor] |
| Ativo Total | [valor] |
| Patrimônio Líquido | [valor] |
| Passivo Total | [valor] |

**Contexto e implicações práticas:**
Apresente a tabela e, em seguida, **contextualize o porte e desempenho** em 3–4 frases. Por exemplo: "A empresa apresenta porte médio/grande, com receita anual de R$ X milhões e base patrimonial de R$ Y milhões. O lucro líquido de R$ Z indica rentabilidade positiva, mas representa apenas X% da receita, o que sugere margens operacionais apertadas. O patrimônio líquido de R$ W (aproximadamente X% do ativo total) confere certo grau de solidez patrimonial, mas o passivo elevado (R$ P) exige atenção à capacidade de pagamento e custos financeiros." Se houver crescimento ou retração significativa entre os anos, comente sobre a trajetória e suas possíveis causas (expansão, crise, inadimplência, etc.).

---

## 4. Resultados

Escreva um parágrafo introdutório (sem subtítulo) apresentando esta seção. Explique que aqui serão analisados os resultados da avaliação quantitativa: o FinScore e o Serasa Score. Contextualize que esses escores, conforme detalhado na Metodologia, serão agora interpretados considerando os dados contábeis e índices financeiros específicos da empresa. Mencione também que serão identificados riscos operacionais relevantes que possam demandar covenants.

### 4.1 FinScore

Apresente e interprete o valor do FinScore e sua classificação de risco.

Em seguida, **valide esse resultado** analisando os dados contábeis e índices financeiros que sustentam (ou não) o escore obtido:
- Relacione o FinScore com os índices de **liquidez** (Liquidez Corrente, Seca, CCL/Ativo Total)
- Relacione com os índices de **rentabilidade** (ROE, ROA, Margem Líquida, Margem EBITDA)
- Relacione com os índices de **endividamento** (DL/EBITDA, Passivo/Ativo, Cobertura de Juros)
- Relacione com os índices de **eficiência operacional** (Giro do Ativo, PMR, PMP)

Explique se os fundamentos financeiros confirmam o FinScore ou se há divergências que merecem atenção.

### 4.2 Serasa

Apresente e interprete o Serasa Score e sua classificação.

Em seguida, **contextualize esse resultado** com os indicadores financeiros da empresa:
- Compare o Serasa com os índices de liquidez e capacidade de pagamento
- Relacione com o nível de endividamento e estrutura patrimonial
- Analise a coerência entre rentabilidade atual e histórico de crédito
- Avalie se há **convergência ou divergência** entre FinScore e Serasa, e o que isso significa

Conclua indicando se o Serasa reforça a avaliação do FinScore ou se apresenta alertas adicionais.

### 4.3 Riscos da Operação

Analise os dados contábeis e índices financeiros observando tanto os **valores atuais** quanto as **tendências ao longo do tempo** (evolução entre os anos analisados).

Identifique e discuta:
- **Riscos estruturais detectados**: liquidez em queda, endividamento crescente, rentabilidade declinante, piora na eficiência operacional, etc.
- **Covenants recomendados** (se aplicável): limites de DL/EBITDA, manutenção de índices mínimos de liquidez ou cobertura de juros, envio periódico de demonstrações, restrições a dividendos ou novos endividamentos, etc.
- **Indicadores críticos para monitoramento**: liste 3-5 índices que devem ser acompanhados continuamente e justifique cada escolha

Conclua avaliando se a operação apresenta riscos mitigáveis, riscos estruturais preocupantes, ou solidez suficiente para dispensar cláusulas restritivas mais rígidas.

---

## 5. Considerações Finais

- Apresente a **decisão final**: {decisao_motor}
- Justifique em 3–4 bullets os principais fundamentos da decisão
- Mencione se há **covenants** (ex.: limites de endividamento, envio de balanços trimestrais)
- Acrescente uma **recomendação de monitoramento** contínuo, se aplicável

---

**DIRETRIZES:**
✓ Markdown puro (sem HTML)
✓ Linguagem técnica, clara e analítica
✓ Transições suaves entre seções
✓ Use valores EXATOS dos dados fornecidos
✓ Percentuais: 15% (não 0,15)
✓ Múltiplos: 2,5x (não 2,5)
✓ Máximo 1000 palavras
✓ A decisão {decisao_motor} é FINAL e INALTERÁVEL
"""
    return prompt.strip()


def _generate_parecer_ia(
    decisao_motor: str,
    motivos_motor: list,
    covenants_motor: list,
    analysis_data: Dict[str, Any],
    meta_cliente: Dict[str, Any]
) -> Optional[str]:
    """
    Gera o parecer narrativo usando IA.
    """
    system_prompt = (
        "Você é um analista de crédito sênior. Escreva pareceres técnicos objetivos e bem estruturados. "
        "NUNCA altere a decisão determinística fornecida. Seu papel é apenas REDIGIR e JUSTIFICAR, não DECIDIR."
    )
    
    user_prompt = _build_parecer_prompt(
        decisao_motor, motivos_motor, covenants_motor, analysis_data, meta_cliente
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = _invoke_model(messages, MODEL_NAME, PARECER_TEMPERATURE)
        response = _fix_formatting_issues(response)
        return response
    except Exception as e:
        st.error(f"Erro ao gerar parecer: {e}")
        return None


def _fix_formatting_issues(text: str) -> str:
    """
    Pós-processamento MINIMALISTA: apenas correções essenciais comprovadas.
    Temperatura 0 já reduz drasticamente erros ortográficos.
    """
    import re
    import unicodedata

    # 1) Normalização Unicode
    text = unicodedata.normalize('NFC', text)
    
    # 2) Remover caracteres invisíveis
    invisibles = ['\u200B', '\u200C', '\u200D', '\u2060', '\uFEFF', '\u00AD']
    for ch in invisibles:
        text = text.replace(ch, '')
    text = text.replace('\u00A0', ' ')
    
    # 3) Corrigir numeração de seções: vírgula -> ponto em títulos markdown
    text = re.sub(r'^(#{2,3}\s+)(\d+),(\d+)(\s+)', r'\1\2.\3\4', text, flags=re.MULTILINE)
    
    # 4) Correções monetárias
    # "R 0.83" ou "R 210" -> "R$ 0,83" ou "R$ 210"
    text = re.sub(r'\bR\s+(\d+[.,]?\d*)', r'R$ \1', text)
    text = re.sub(r'R\$(?!\s)', r'R$ ', text)
    
    # 5) Converter ponto decimal para vírgula (padrão BR)
    # Processar linha por linha para NÃO afetar títulos markdown
    lines = text.split('\n')
    result_lines = []
    for line in lines:
        if line.strip().startswith('#'):
            # Linhas com # (títulos) mantêm pontos na numeração
            result_lines.append(line)
        else:
            # Outras linhas: converter ponto para vírgula em decimais
            result_lines.append(re.sub(r'(\d+)\.(\d+)', r'\1,\2', line))
    text = '\n'.join(result_lines)
    
    # 6) Escapar $ para evitar MathJax
    text = re.sub(r'(?<!\\)\$', r'\\$', text)
    
    # 5) Espaços múltiplos
    text = re.sub(r'([^\n]) {2,}', r'\1 ', text)
    
    # 6) Espaços antes de pontuação
    text = re.sub(r' +([,.;:!?])', r'\1', text)
    
    return text


def render():
    ss = st.session_state
    st.header("Parecer de Crédito")

    if not ss.get("out"):
        st.info("Calcule o FinScore em **Lançamentos** para liberar o parecer.")
        return

    o = ss.out
    meta = ss.get("meta", {})
    indices_row = _latest_indices_row(o)

    finscore_aj = o.get("finscore_ajustado")
    cls_fin = o.get("classificacao_finscore")
    cls_ser = o.get("classificacao_serasa")
    serasa_score = o.get("serasa")

    dl_ebitda = _safe_float(indices_row.get("Alavancagem"))
    cobertura = _safe_float(indices_row.get("Cobertura de Juros"))
    liquidez_corrente = _safe_float(indices_row.get("Liquidez Corrente"))
    liquidez_seca = _safe_float(indices_row.get("Liquidez Seca"))
    roe = _safe_float(indices_row.get("ROE"))
    margem_liquida = _safe_float(indices_row.get("Margem Líquida"))
    margem_ebitda = _safe_float(indices_row.get("Margem EBITDA"))
    endividamento = _safe_float(indices_row.get("Endividamento"))

    pi = PolicyInputs(
        finscore_ajustado=finscore_aj,
        dl_ebitda=dl_ebitda,
        cobertura_juros=cobertura,
        serasa_rank=RANK_SERASA.get(cls_ser),
        finscore_rank=RANK_FINSCORE.get(cls_fin),
        flags_qualidade={"dados_incompletos": False},
        serasa_score=serasa_score,
        classificacao_finscore=cls_fin,
        classificacao_serasa=cls_ser,
        liquidez_corrente=liquidez_corrente,
        liquidez_seca=liquidez_seca,
        roe=roe,
        margem_liquida=margem_liquida,
        margem_ebitda=margem_ebitda,
        endividamento=endividamento,
    )
    
    ss["policy_inputs"] = {
        "finscore_ajustado": pi.finscore_ajustado,
        "dl_ebitda": pi.dl_ebitda,
        "cobertura_juros": pi.cobertura_juros,
        "serasa_rank": pi.serasa_rank,
        "finscore_rank": pi.finscore_rank,
        "flags_qualidade": pi.flags_qualidade,
    }

    resultado = decide(pi)

    # ========================================
    # SEÇÃO 1: PRÉ-VEREDITO DETERMINÍSTICO
    # ========================================
   
    col1, col2 = st.columns([2, 1])
    
    with col1:
        decisao_label = {
            "aprovar": "✅ Aprovar",
            "aprovar_com_ressalvas": "⚠️ Aprovar com Ressalvas",
            "nao_aprovar": "❌ Não Aprovar"
        }.get(resultado["decisao"], resultado["decisao"])
        
        st.metric("Decisão Final", decisao_label)
    
    with col2:
        if resultado.get("motivos"):
            st.markdown("**Motivos:**")
            for motivo in resultado["motivos"]:
                st.markdown(f"- {motivo}")
        
        if resultado.get("covenants"):
            st.markdown("**Salvaguardas a serem sopesadas:**")
            for covenant in resultado["covenants"]:
                st.markdown(f"- 📌 {covenant}")

    st.divider()

    # ========================================
    # SEÇÃO 2: GERAÇÃO DO PARECER NARRATIVO
    # ========================================
    
    # Botão para gerar parecer - centralizado
    col_left, col_center, col_right = st.columns([1, 1, 1])
    
    with col_center:
        gerar = st.button("Gerar Parecer IA", use_container_width=True, type="primary")
    
    if gerar:
        # Criar barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Etapa 1: Extrair dados
            status_text.text("🔄 Extraindo dados consolidados...")
            progress_bar.progress(30)
            analysis_data = _extract_analysis_data(o)
            
            # Etapa 2: Gerar parecer
            status_text.text("🤖 Gerando parecer técnico com IA...")
            progress_bar.progress(60)
            parecer = _generate_parecer_ia(
                decisao_motor=resultado["decisao"],
                motivos_motor=resultado.get("motivos", []),
                covenants_motor=resultado.get("covenants", []),
                analysis_data=analysis_data,
                meta_cliente=meta
            )
            
            # Etapa 3: Finalizar
            progress_bar.progress(100)
            status_text.text("✅ Parecer gerado com sucesso!")
            
            if parecer:
                ss["parecer_gerado"] = parecer
                # Limpar componentes de progresso após breve pausa
                import time
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                st.rerun()
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Erro ao gerar parecer: {e}")
    
    # Exibir parecer se já foi gerado
    if "parecer_gerado" in ss:
        st.divider()
        
        # Container para o parecer com fundo destacado
        with st.container():
            st.markdown(ss["parecer_gerado"])
        
        st.divider()
        
        # Ações pós-geração
        col_action1, col_action2, col_action3 = st.columns(3)
        
        with col_action1:
            if st.button("💾 Exportar PDF", use_container_width=True, disabled=True):
                st.info("Funcionalidade em desenvolvimento")
        
        with col_action2:
            if st.button("📧 Enviar por Email", use_container_width=True, disabled=True):
                st.info("Funcionalidade em desenvolvimento")
        
        with col_action3:
            if st.button("📋 Copiar Texto", use_container_width=True):
                st.code(ss["parecer_gerado"], language=None)
                st.caption("Use Ctrl+A e Ctrl+C para copiar")
