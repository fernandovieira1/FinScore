import math
import json
import time
import uuid
import base64
from typing import Dict, Any, Optional

import streamlit as st
import streamlit.components.v1 as components
import requests
import os

from components.policy_engine import PolicyInputs, decide
from components.llm_client import _invoke_model, MODEL_NAME, get_last_usage
from components.token_utils import (
    count_messages_tokens,
    count_text_tokens,
    estimate_cost_usd,
    now_ts,
)
from components.navigation_flow import NavigationFlow
from components.session_state import clear_flow_state
from components import nav

# Usar temperatura 0 para máxima determinismo e reduzir erros ortográficos
PARECER_TEMPERATURE = 0.0

RANK_SERASA = {"Excelente": 1, "Bom": 2, "Baixo": 3, "Muito Baixo": 4}
RANK_FINSCORE = {
    "Muito Abaixo do Risco": 1,
    "Levemente Abaixo do Risco": 2,
    "Neutro": 3,
    "Levemente Acima do Risco": 4,
    "Muito Acima do Risco": 5,
}


def _format_metric(value, decimals: int = 2, suffix: str = "") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError, AttributeError):
        return "N/A"
    formatted = f"{number:.{decimals}f}"
    if suffix:
        formatted = f"{formatted}{suffix}"
    return formatted


def _format_currency(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError, AttributeError):
        return "N/A"
    return f"R$ {number:,.0f}".replace(",", ".")


def _safe_float(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _safe_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _expected_intro_paragraphs(meta_cliente: Dict[str, Any]) -> tuple[str, str]:
    empresa = meta_cliente.get("empresa", "N/A")
    cnpj = meta_cliente.get("cnpj", "N/A")

    ano_inicial_meta = _safe_int(meta_cliente.get("ano_inicial"))
    ano_final_meta = _safe_int(meta_cliente.get("ano_final"))

    anos_disponiveis: list[int] = []
    if ano_inicial_meta is not None and ano_final_meta is not None:
        if ano_final_meta >= ano_inicial_meta:
            anos_disponiveis = list(range(ano_inicial_meta, ano_final_meta + 1))
        else:
            anos_disponiveis = [ano_inicial_meta, ano_final_meta]
    elif ano_inicial_meta is not None:
        anos_disponiveis = [ano_inicial_meta]
    elif ano_final_meta is not None:
        anos_disponiveis = [ano_final_meta]

    anos_texto = ", ".join(str(ano) for ano in anos_disponiveis) if anos_disponiveis else "N/A"
    serasa_data_texto = str(meta_cliente.get("serasa_data") or "N/A").strip() or "N/A"

    paragrafo1 = (
        f"Trata-se de análise da situação econômica, contábil e patrimonial da empresa {empresa}, "
        f"CNPJ {cnpj}, para fins de análise de riscos e oportunidades em operação de crédito."
    )

    paragrafo2 = (
        "Foram utilizados como fontes de informações as demonstrações contábeis referentes aos anos "
        f"{anos_texto}, que serviram para cálculo e análise do FinScore, conforme metodologia detalhada "
        "adiante, bem como o score Serasa, consultado em "
        f"{serasa_data_texto}."
    )

    return paragrafo1, paragrafo2


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

    # Incluir CSVs brutos para garantir que o prompt receba todos os valores
    try:
        df_indices_full = out_dict.get("df_indices")
        if df_indices_full is not None and getattr(df_indices_full, "empty", True) is False:
            # exportar sem índice e com ponto decimal padrão
            data["df_indices_csv"] = df_indices_full.to_csv(index=False, float_format='%.6f')
        else:
            data["df_indices_csv"] = None
    except Exception:
        data["df_indices_csv"] = None

    try:
        if df_raw is not None and not df_raw.empty:
            data["df_raw_csv"] = df_raw.to_csv(index=False)
        else:
            data["df_raw_csv"] = None
    except Exception:
        data["df_raw_csv"] = None

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
    intro_paragrafo1, intro_paragrafo2 = _expected_intro_paragraphs(meta_cliente)
    
    # Extrair dados para variáveis no prompt
    finscore_ajustado = analysis_data.get("finscore_ajustado", "N/A")
    classificacao_finscore = analysis_data.get("classificacao_finscore", "N/A")
    serasa_score = analysis_data.get("serasa", "N/A")  # Corrigido: era "serasa_score"
    classificacao_serasa = analysis_data.get("classificacao_serasa", "N/A")
    covenants_texto = ', '.join(covenants_motor) if covenants_motor else 'Nenhum covenant específico'
    
    # Formatar dados para o prompt
    dados_formatados = json.dumps(analysis_data, ensure_ascii=False, indent=2, default=str)

    # Incluir CSVs brutos explicitamente no prompt para garantir uso dos valores exatos
    df_indices_csv = analysis_data.get("df_indices_csv")
    df_raw_csv = analysis_data.get("df_raw_csv")

    csv_section = ""
    if df_indices_csv:
        # Limitar tamanho se muito grande — aqui adicionamos completo para garantir precisão
        csv_section += "\n**DADOS BRUTOS (CSV) - ÍNDICES CONTÁBEIS**\n\n```csv\n" + df_indices_csv + "\n```\n"
    if df_raw_csv:
        csv_section += "\n**DADOS BRUTOS (CSV) - DADOS CONTÁBEIS (LINHA POR ANO)**\n\n```csv\n" + df_raw_csv + "\n```\n"

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

ATENÇÃO: abaixo seguem os arquivos CSV com os valores brutos e os índices calculados (linha por ano). Utilize esses CSVs EXATAMENTE como fonte factual ao redigir a seção 3 (Análise Detalhada dos Indicadores). Reproduza os números literais quando pedir valores ou comparar anos.

{csv_section}

**ESTRUTURA OBRIGATÓRIA (siga exatamente):**

## 1. Introdução

**Primeiro parágrafo (copie exatamente o texto abaixo e mantenha-o como um parágrafo isolado, sem conectores adicionais):**
{intro_paragrafo1}

**Segundo parágrafo (copie exatamente o texto abaixo e mantenha-o como um parágrafo isolado, separado por linha em branco):**
{intro_paragrafo2}

**Terceiro parágrafo (Estrutura do Parecer – escreva em um parágrafo separado):** Descreva brevemente como este parecer está organizado, explicando que as próximas seções abordarão: (i) a metodologia do FinScore e Serasa; (ii) a análise detalhada dos indicadores financeiros por categoria (liquidez, endividamento, rentabilidade e eficiência); (iii) a análise de risco e scoring; e (iv) as considerações finais com recomendações e salvaguardas (garantias reais, fianças, seguros etc), se aplicáveis.

---

## 2. Metodologia

Este parecer fundamenta-se em uma **avaliação técnica estruturada** que combina dois instrumentos complementares: o **FinScore** (índice proprietário baseado em dados contábeis) e o **Serasa Score** (indicador externo de histórico de crédito).

### 2.1 FinScore

O **FinScore** (escala 0–1000) sintetiza a saúde financeira da empresa, capturando capacidade de pagamento, eficiência, endividamento e produtividade dos ativos. Inspirado no Altman Z-Score, oferece avaliação objetiva do risco de inadimplência.

**Cálculo (5 etapas):**

1. **Índices Contábeis**: Extração de diversos indicadores (rentabilidade, liquidez, endividamento, eficiência) das demonstrações financeiras.
2. **Padronização**: Transformação em z-scores para comparação objetiva entre dimensões.
3. **PCA**: Redução de dimensionalidade eliminando redundâncias.
4. **Consolidação Temporal**: Pesos 60% (ano recente), 25% (anterior), 15% (mais antigo).
5. **Escalonamento**: Resultado convertido para escala 0–1000 e classificado em faixas de risco.

**Tabela – Classificação FinScore**

| Faixa de Pontuação | Classificação de Risco | Interpretação |
|-------------------:|:-----------------------|:--------------|
| > 875 | Muito Abaixo do Risco | Perfil financeiro excepcional, risco mínimo |
| 750 – 875 | Levemente Abaixo do Risco | Situação confortável, baixo risco |
| 250 – 750 | Neutro | Situação intermediária, sem sinais claros de excelência ou fragilidade |
| 125 – 250 | Levemente Acima do Risco | Atenção recomendada, sinais de fragilidade |
| < 125 | Muito Acima do Risco | Risco elevado, análise detalhada necessária |

O FinScore reflete a **capacidade estrutural** da empresa: recursos, lucratividade e equilíbrio financeiro. Empresas com escore elevado demonstram maior resiliência a crises; escores baixos indicam vulnerabilidade a choques externos.

### 2.2 Serasa Score

O **Serasa Score** (0–1000) avalia **comportamento de crédito**: pagamentos em dia, protestos, negativações e histórico com credores. Complementa o FinScore ao capturar aspectos comportamentais não visíveis nas demonstrações contábeis.

**Tabela – Classificação Serasa**

| Faixa de Pontuação | Classificação | Significado |
|-------------------:|:--------------|:------------|
| 851 – 1000 | Excelente | Histórico de crédito exemplar, paga em dia, sem restrições |
| 701 – 850 | Bom | Comportamento de pagamento satisfatório, baixo risco |
| 0 – 400 | Baixo | Histórico comprometido, atenção necessária (atrasos, negativações) |
| Sem cadastro | Muito Baixo | Ausência de histórico de crédito (empresa nova ou sem relacionamento bancário) |

A convergência entre FinScore e Serasa reforça a avaliação. Divergências significativas demandam análise qualitativa adicional para compreender inconsistências entre capacidade financeira e histórico de pagamento.

### 2.3 Dados Contábeis e Índices Financeiros

De forma complementar, a análise contextualizada e detalhada dos índices que compõem o FinScore permite:

1. **Identificar fatores de risco**: A identificação precisa de qual dimensão financeira (liquidez, rentabilidade ou endividamento) exerce impacto negativo no escore permite direcionar ações corretivas específicas e priorizadas, otimizando recursos e reduzindo o custo de capital ao mitigar os pontos críticos que mais deterioram a avaliação de crédito.
2. **Detectar vulnerabilidades ocultas**: A identificação de riscos específicos, mesmo quando o escore geral aparenta solidez, possibilita antecipar problemas latentes que poderiam se materializar em crises futuras, garantindo maior segurança operacional sem sacrificar oportunidades de rentabilizar o negócio ou comprometer a concessão de crédito.
3. **Sugestão de garantias de crédito**: A elaboração de cláusulas contratuais (salvaguardas) customizadas e alinhadas aos riscos específicos identificados estabelece gatilhos de alerta precoce e mecanismos de proteção proporcionais ao perfil real do tomador, equilibrando proteção institucional com condições comercialmente viáveis.
4. **Compreender tendências**: A análise da trajetória temporal dos indicadores financeiros revela se a empresa está em ciclo de fortalecimento ou deterioração, permitindo decisões proativas de renovação, aumento de garantias ou encerramento de exposição antes que reversões negativas se consolidem em perdas efetivas.

Os índices detalhados não substituem o FinScore, mas o **explicam e fundamentam**, oferecendo visão granular que sustenta decisões e eventuais salvaguardas adicionais.

### 2.4 Critérios de Decisão

A decisão final resulta da **convergência** entre:

**1. FinScore (Indicador Primário)**: Âncora da análise, orienta decisão inicial baseada em capacidade financeira estrutural.

**2. Serasa Score (Validação Cruzada)**: Valida histórico de comportamento de crédito. Divergências entre FinScore e Serasa demandam investigação qualitativa.

**3. Índices Detalhados**: A análise granular permite identificar riscos e personalizar salvaguardas.

**4. Contexto Qualitativo**: Tendências temporais, sazonalidade setorial e eventos atípicos complementam a análise quantitativa.

A decisão ({decisao_motor}) fundamenta-se em critérios técnicos, objetivos e auditáveis, garantindo transparência e rastreabilidade da avaliação.

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

Escreva um parágrafo introdutório (sem subtítulo) apresentando esta seção. Explique que aqui serão analisados os resultados da avaliação quantitativa: o FinScore e o Serasa Score. Contextualize que esses escores, conforme detalhado na Metodologia, serão agora interpretados considerando os dados contábeis e índices financeiros específicos da empresa. Mencione também que serão identificados riscos operacionais relevantes que possam demandar salvaguardas adicionais.

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
- **Salvaguardas contratuais recomendadas** (se aplicável): limites de DL/EBITDA, manutenção de índices mínimos de liquidez ou cobertura de juros, envio periódico de demonstrações, restrições a dividendos ou novos endividamentos, etc.
- **Indicadores críticos para monitoramento**: liste 3-5 índices que devem ser acompanhados continuamente e justifique cada escolha

Conclua avaliando se a operação apresenta riscos mitigáveis, riscos estruturais preocupantes, ou solidez suficiente para dispensar cláusulas restritivas mais rígidas.

### 4.4 Opinião (Síntese Visual)

**Parágrafo inicial (Síntese Executiva Visual):** Antes do gráfico, redija 5–8 linhas apresentando os valores e classificações de FinScore e Serasa, os principais pontos fortes e fragilidades identificados, a decisão de crédito ({decisao_motor}) com justificativa objetiva e se há salvaguardas necessários. Esta síntese substitui o antigo parágrafo-resumo da Introdução e deve servir como leitura prévia ao gráfico.

**Parágrafo posterior (Comentário Analítico):** Em 2-3 frases, sintetize:
- O alinhamento (ou divergência) entre FinScore e Serasa
- Se os resultados confirmam ou contradizem a análise detalhada dos indicadores
- Uma avaliação geral sobre o perfil de risco da empresa

---

## 5. Considerações Finais

**Primeiro parágrafo (Síntese da Análise Detalhada):** Resuma em 3-4 linhas os principais achados da seção "3. Análise Detalhada dos Indicadores", destacando os pontos mais relevantes identificados nas categorias de liquidez, endividamento, rentabilidade e eficiência. Mencione quais indicadores demonstraram maior solidez ou fragilidade.

**Segundo parágrafo (Síntese dos Resultados - Pontos Fortes e Fragilidades):** Com base na análise da seção "4. Resultados", identifique e resuma:
- **Aspectos positivos**: Quais indicadores, dimensões ou escores demonstraram desempenho satisfatório ou acima da média? (ex: liquidez confortável, rentabilidade consistente, Serasa elevado, FinScore sólido)
- **Aspectos de atenção**: Quais indicadores ou dimensões apresentaram fragilidades, deterioração temporal ou riscos que justificam monitoramento? (ex: endividamento crescente, margens declinantes, liquidez apertada)
- **Ponderação geral**: Como o equilíbrio entre pontos fortes e fragilidades fundamenta a decisão de crédito ({decisao_motor}) e os covenants (salvaguardas) recomendados?

Este parágrafo deve consolidar os comentários específicos da seção 4 em uma visão integrada, permitindo ao leitor compreender rapidamente o "saldo" da análise (se predominam aspectos positivos, negativos, ou se há equilíbrio com ressalvas).

**Terceiro parágrafo (Decisão Final e Recomendações):** 
- Reafirme formalmente a **decisão final**: {decisao_motor}
- Repita os valores e classificações: FinScore {finscore_ajustado} ({classificacao_finscore}) e Serasa {serasa_score} ({classificacao_serasa})
- Liste as **salvaguardas/covenants recomendados** (se aplicável): {covenants_texto}
- Conclua com uma recomendação de monitoramento contínuo, se pertinente

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
✓ Em cada seção ou tópico, finalize com um parágrafo iniciado por conjunção conclusiva (ex: “Em suma”, “Em resumo”, “Portanto”, “Logo”, “Destarte”)
"""
    return prompt.strip()


def _generate_fake_parecer(
    decisao_motor: str,
    motivos_motor: list,
    covenants_motor: list,
    analysis_data: Dict[str, Any],
    meta_cliente: Dict[str, Any]
) -> str:
    empresa = meta_cliente.get("empresa", "Empresa")
    cnpj = meta_cliente.get("cnpj", "N/A")
    intro1, intro2 = _expected_intro_paragraphs(meta_cliente)
    intro3 = (
        "Este parecer foi produzido no modo de contingência para permitir testes da interface e do PDF "
        "quando o serviço de IA estiver temporariamente indisponível."
    )
    intro_estrutura = (
        "A seguir, o documento apresenta a metodologia aplicada (FinScore e Serasa), a análise detalhada "
        "dos indicadores financeiros por categoria, os resultados consolidados com avaliação de riscos e, "
        "por fim, as considerações finais com recomendações e eventuais covenants."
    )

    finscore_ajustado = _format_metric(analysis_data.get("finscore_ajustado"))
    classificacao_finscore = analysis_data.get("classificacao_finscore", "N/A")
    serasa_score = _format_metric(analysis_data.get("serasa"), decimals=0)
    classificacao_serasa = analysis_data.get("classificacao_serasa", "N/A")

    indicadores = [
        ("Liquidez", "Liquidez Corrente", _format_metric(analysis_data.get("liquidez_corrente"))),
        ("Liquidez", "Liquidez Seca", _format_metric(analysis_data.get("liquidez_seca"))),
        ("Estrutura", "Endividamento", _format_metric(analysis_data.get("endividamento"))),
        ("Estrutura", "Alavancagem (DL/EBITDA)", _format_metric(analysis_data.get("alavancagem"))),
        ("Rentabilidade", "ROE", _format_metric(analysis_data.get("roe"), suffix="%")),
        ("Rentabilidade", "ROA", _format_metric(analysis_data.get("roa"), suffix="%")),
        ("Margens", "Margem Líquida", _format_metric(analysis_data.get("margem_liquida"), suffix="%")),
        ("Margens", "Margem EBITDA", _format_metric(analysis_data.get("margem_ebitda"), suffix="%")),
        ("Eficiência", "PMR (dias)", _format_metric(analysis_data.get("pmr"), decimals=0)),
        ("Eficiência", "PMP (dias)", _format_metric(analysis_data.get("pmp"), decimals=0)),
        ("Eficiência", "Giro do Ativo", _format_metric(analysis_data.get("giro_ativo"))),
    ]

    motivos_md = "\n".join(f"- {motivo}" for motivo in motivos_motor) if motivos_motor else "- Motor determinístico não forneceu motivos detalhados."
    covenants_md = ", ".join(covenants_motor) if covenants_motor else "Monitoramento trimestral dos indicadores de liquidez e alavancagem."

    liquidez_corrente = indicadores[0][2]
    liquidez_seca = indicadores[1][2]
    ccl_ativo = _format_metric(analysis_data.get("ccl_ativo"))
    endividamento = indicadores[2][2]
    alavancagem = indicadores[3][2]
    cobertura_juros = _format_metric(analysis_data.get("cobertura_juros"))
    roe = indicadores[4][2]
    roa = indicadores[5][2]
    margem_liquida = indicadores[6][2]
    margem_ebitda = indicadores[7][2]
    pmr = indicadores[8][2]
    pmp = indicadores[9][2]
    giro_ativo = indicadores[10][2]

    receita_total = _format_currency(analysis_data.get("receita_total"))
    lucro_liquido = _format_currency(analysis_data.get("lucro_liquido"))
    ativo_total = _format_currency(analysis_data.get("ativo_total"))
    patrimonio_liquido = _format_currency(analysis_data.get("patrimonio_liquido"))
    passivo_total = _format_currency(analysis_data.get("passivo_total"))

    dados_patrimoniais_table = (
        "| Indicador | Valor |\n"
        "|-----------|------:|\n"
        f"| Receita Total | {receita_total} |\n"
        f"| Lucro Líquido | {lucro_liquido} |\n"
        f"| Ativo Total | {ativo_total} |\n"
        f"| Patrimônio Líquido | {patrimonio_liquido} |\n"
        f"| Passivo Total | {passivo_total} |\n"
    )

    indicadores_monitoramento = "\n".join(
        [
            f"- Liquidez Corrente em {liquidez_corrente} para acompanhar eventual aperto de caixa.",
            f"- Alavancagem em {alavancagem}x para evitar degradação da cobertura de serviço da dívida.",
            f"- Margem EBITDA em {margem_ebitda} para medir geração operacional.",
            f"- PMR em {pmr} dias e PMP em {pmp} dias para monitorar o ciclo financeiro.",
            f"- Cobertura de juros em {cobertura_juros} para assegurar folga frente a custos financeiros.",
        ]
    )

    fake_text = f"""
> ⚠️ Parecer simulado para desenvolvimento. Utilize apenas para validar layout, navegação e exportação em PDF.

## 1. Introdução

{intro1}

{intro2}

{intro3}

{intro_estrutura}

---

## 2. Metodologia

Este parecer fundamenta-se em uma **avaliação técnica estruturada** que combina dois instrumentos complementares: o **FinScore** (índice proprietário baseado em dados contábeis) e o **Serasa Score** (indicador externo de histórico de crédito).

### 2.1 FinScore

O **FinScore** (escala 0–1000) sintetiza a saúde financeira da empresa, capturando capacidade de pagamento, eficiência, endividamento e produtividade dos ativos. Inspirado no Altman Z-Score, oferece avaliação objetiva do risco de inadimplência.

**Cálculo (5 etapas):**

1. **Índices Contábeis**: Extração de 15+ indicadores (rentabilidade, liquidez, endividamento, eficiência) das demonstrações financeiras.
2. **Padronização**: Transformação em z-scores para comparação objetiva entre dimensões.
3. **PCA**: Redução de dimensionalidade eliminando redundâncias.
4. **Consolidação Temporal**: Pesos 60% (ano recente), 25% (anterior), 15% (mais antigo).
5. **Escalonamento**: Resultado convertido para escala 0–1000 e classificado em faixas de risco.

**Tabela – Classificação FinScore**

| Faixa de Pontuação | Classificação de Risco | Interpretação |
|-------------------:|:-----------------------|:--------------|
| > 875 | Muito Abaixo do Risco | Perfil financeiro excepcional, risco mínimo |
| 750 – 875 | Levemente Abaixo do Risco | Situação confortável, baixo risco |
| 250 – 750 | Neutro | Situação intermediária, sem sinais claros de excelência ou fragilidade |
| 125 – 250 | Levemente Acima do Risco | Atenção recomendada, sinais de fragilidade |
| < 125 | Muito Acima do Risco | Risco elevado, análise detalhada necessária |

### 2.2 Serasa Score

O **Serasa Score** (0–1000) avalia **comportamento de crédito**: pagamentos em dia, protestos, negativações e histórico com credores. Complementa o FinScore ao capturar aspectos comportamentais não visíveis nas demonstrações contábeis.

**Tabela – Classificação Serasa**

| Faixa de Pontuação | Classificação | Significado |
|-------------------:|:--------------|:------------|
| 851 – 1000 | Excelente | Histórico de crédito exemplar, paga em dia, sem restrições |
| 701 – 850 | Bom | Comportamento de pagamento satisfatório, baixo risco |
| 0 – 400 | Baixo | Histórico comprometido, atenção necessária (atrasos, negativações) |
| Sem cadastro | Muito Baixo | Ausência de histórico de crédito (empresa nova ou sem relacionamento bancário) |

A convergência entre FinScore e Serasa reforça a avaliação. Divergências significativas demandam análise qualitativa adicional para compreender inconsistências entre capacidade financeira e histórico de pagamento.

### 2.3 Dados Contábeis e Índices Financeiros

De forma complementar, a análise contextualizada e detalhada dos índices que compõem o FinScore permite identificar fatores de risco, detectar vulnerabilidades ocultas, desenhar covenants proporcionais e compreender tendências temporais. Os índices não substituem o FinScore: **explicam e fundamentam** o escore consolidado.

### 2.4 Critérios de Decisão

A decisão final resulta da convergência entre FinScore ({finscore_ajustado}), Serasa ({serasa_score}), indicadores detalhados e contexto qualitativo. Essa combinação garante transparência, rastreabilidade e aderência às políticas de crédito.

---

## 3. Análise Detalhada dos Indicadores

Esta seção disseca os indicadores financeiros nas dimensões de liquidez, endividamento, rentabilidade, eficiência e porte patrimonial. Os valores servem como base factual para a conclusão expressa na decisão {decisao_motor}.

### 3.1 Liquidez

**Indicadores analisados:** Liquidez Corrente ({liquidez_corrente}), Liquidez Seca ({liquidez_seca}) e CCL/Ativo Total ({ccl_ativo}).

**Contexto e implicações práticas:** Os valores apontam como a empresa equilibra ativos e passivos de curto prazo. Portanto, a combinação atual indica que a companhia dispõe de {liquidez_corrente} em recursos circulantes para cada unidade de dívida imediata, enquanto a liquidez seca de {liquidez_seca} revela o colchão disponível sem estoques. O CCL equivalente a {ccl_ativo} do ativo total confirma se há capital próprio sustentando o giro e orienta a necessidade (ou não) de capital de giro adicional.

### 3.2 Endividamento e Estrutura de Capital

**Indicadores analisados:** Endividamento total ({endividamento}), Alavancagem DL/EBITDA ({alavancagem}) e Cobertura de Juros ({cobertura_juros}).

**Contexto e implicações práticas:** A relação dívida/ativo em {endividamento} sinaliza a dependência de capital de terceiros. A alavancagem de {alavancagem}x indica quantos anos de EBITDA seriam necessários para amortizar a dívida líquida, enquanto a cobertura de juros em {cobertura_juros} vezes demonstra a folga operacional frente às despesas financeiras. Logo, a análise conjunta mostra se a empresa suporta novas linhas ou se precisa de covenants restritivos.

### 3.3 Rentabilidade

**Indicadores analisados:** ROE ({roe}), ROA ({roa}), Margem Líquida ({margem_liquida}) e Margem EBITDA ({margem_ebitda}).

**Contexto e implicações práticas:** Os retornos sobre patrimônio e ativos, combinados às margens, indicam capacidade de geração de caixa e remuneração dos sócios. Em resumo, os percentuais atuais ilustram se o negócio remunera adequadamente o risco e se possui elasticidade para absorver oscilações de custos ou receita.

### 3.4 Eficiência Operacional

**Indicadores analisados:** PMR ({pmr} dias), PMP ({pmp} dias) e Giro do Ativo ({giro_ativo}).

**Contexto e implicações práticas:** O PMR revela a velocidade de recebimento, o PMP sinaliza o poder de negociação com fornecedores e o giro do ativo mostra a produtividade dos investimentos. Logo, o ciclo financeiro resultante ({pmr} vs {pmp}) indica se a empresa financia clientes com capital próprio ou se consegue gerar folga de caixa.

### 3.5 Dados Patrimoniais e de Resultado

**Principais indicadores:**

{dados_patrimoniais_table}

**Contexto e implicações práticas:** A tabela evidencia o porte do negócio em termos de receita e base patrimonial. Portanto, a leitura conjunta dos valores demonstra se a estrutura é compatível com o nível de endividamento atual e quais amortecedores patrimoniais existem para suportar choques.

---

## 4. Resultados

Esta seção consolida os escores quantitativos e interpreta como FinScore e Serasa traduzem os dados analisados anteriormente, destacando riscos que podem demandar salvaguardas contratuais.

### 4.1 FinScore

O FinScore ajustado de **{finscore_ajustado} ({classificacao_finscore})** reflete a combinação dos indicadores avaliados. Logo, o resultado confirma que a situação financeira descrita nas seções de liquidez, estrutura, rentabilidade e eficiência sustenta o patamar atual de risco e orienta a manutenção/ajuste de limites.

### 4.2 Serasa

O Serasa Score de **{serasa_score} ({classificacao_serasa})** complementa a análise ao capturar o histórico de pagamentos. Em resumo, o comportamento externo está alinhado à leitura contábil, reforçando (ou relativizando) o FinScore conforme a proximidade entre as classificações.

### 4.3 Riscos da Operação

{motivos_md}

**Covenants sugeridos:** {covenants_md}

**Indicadores críticos para monitoramento:**
{indicadores_monitoramento}

Portanto, a decisão determinística **{decisao_motor.upper()}** permanece aderente às evidências e pode ser acompanhada pelos gatilhos listados.

### 4.4 Opinião (Síntese Visual)

Esta subseção reserva espaço para o gráfico comparativo entre FinScore e Serasa. Utilize-o para comunicar visualmente o equilíbrio de risco, mantendo a fundamentação descrita nas etapas anteriores.

---

## 5. Considerações Finais

**Síntese da análise detalhada:** As leituras de liquidez ({liquidez_corrente}/{liquidez_seca}), estrutura ({endividamento}, {alavancagem}), rentabilidade ({roe}, {margem_liquida}) e eficiência ({pmr} dias vs {pmp} dias) formam o núcleo da avaliação e explicam a decisão {decisao_motor}.

**Aspectos positivos e pontos de atenção:** Pontos fortes incluem a combinação entre FinScore {finscore_ajustado} e Serasa {serasa_score}, além da produtividade indicada pelo giro {giro_ativo}. Entre as fragilidades, acompanhe alavancagem ({alavancagem}) e margem EBITDA ({margem_ebitda}) para evitar deterioração. Portanto, o saldo é equilibrado com viés {classificacao_finscore}.

**Decisão final e recomendações:** Reitera-se a decisão **{decisao_motor}**, respaldada pelos escores (FinScore {finscore_ajustado} / Serasa {serasa_score}) e pelos motivos determinísticos. Recomenda-se manter os covenants: {covenants_md}. Logo, monitore periodicamente os indicadores destacados enquanto o serviço de IA não retorna, substituindo este texto pelo parecer definitivo assim que possível.
"""

    return fake_text.strip()


def _generate_parecer_ia(
    decisao_motor: str,
    motivos_motor: list,
    covenants_motor: list,
    analysis_data: Dict[str, Any],
    meta_cliente: Dict[str, Any]
) -> Optional[str]:
    """
    Gera o parecer narrativo usando IA e injeta o minichart na seção 4.4.
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
    
    # --- Token counting (estimativa) antes do envio ---
    try:
        price_per_1k = float(os.getenv("FINSCORE_PRICE_PER_1K_USD", "0.03"))
    except Exception:
        price_per_1k = 0.03

    try:
        prompt_tokens = int(count_messages_tokens(MODEL_NAME, messages))
    except Exception:
        prompt_tokens = int(count_text_tokens(MODEL_NAME, user_prompt))

    st.session_state.setdefault("token_usage", []).append({
        "step": "parecer_prompt",
        "model": MODEL_NAME,
        "prompt_tokens_est": int(prompt_tokens),
        "price_per_1k_usd": float(price_per_1k),
        "timestamp": now_ts(),
    })

    try:
        response_text = _invoke_model(messages, MODEL_NAME, PARECER_TEMPERATURE)
    except requests.exceptions.HTTPError as http_err:  # type: ignore[attr-defined]
        status_code = http_err.response.status_code if http_err.response is not None else None
        if status_code == 429:
            st.warning("Limite da API de IA atingido. Gerando parecer simulado para testes...")
            response_text = _generate_fake_parecer(
                decisao_motor,
                motivos_motor,
                covenants_motor,
                analysis_data,
                meta_cliente,
            )
        else:
            st.error(f"Erro ao gerar parecer: {http_err}")
            return None
    except Exception as e:
        st.error(f"Erro ao gerar parecer: {e}")
        return None

    response_text = _fix_formatting_issues(response_text, meta_cliente)
    response_text = _inject_minichart(response_text, analysis_data)

    # Preferir 'usage' retornado pela API quando disponível (mais preciso)
    usage = None
    try:
        usage = get_last_usage()
    except Exception:
        usage = None

    response_tokens = 0
    prompt_tokens_final = prompt_tokens
    if usage and isinstance(usage, dict):
        # API pode retornar 'prompt_tokens', 'completion_tokens' e 'total_tokens'
        api_prompt = usage.get("prompt_tokens")
        api_completion = usage.get("completion_tokens")
        api_total = usage.get("total_tokens")

        if api_prompt is not None:
            prompt_tokens_final = int(api_prompt)
        if api_completion is not None:
            response_tokens = int(api_completion)
        elif api_total is not None:
            # fallback: total - prompt
            try:
                response_tokens = int(api_total) - int(prompt_tokens_final)
            except Exception:
                response_tokens = 0
    else:
        # Fallback: contar localmente a resposta
        try:
            response_tokens = int(count_text_tokens(MODEL_NAME, response_text))
        except Exception:
            response_tokens = 0

    total_tokens = int(prompt_tokens_final) + int(response_tokens)
    cost = estimate_cost_usd(total_tokens, price_per_1k)

    st.session_state.setdefault("token_usage", []).append({
        "step": "parecer_result",
        "model": MODEL_NAME,
        "prompt_tokens": int(prompt_tokens_final),
        "response_tokens": int(response_tokens),
        "total_tokens": int(total_tokens),
        "cost_usd": float(cost),
        "usage_api": usage,
        "timestamp": now_ts(),
    })

    # Persistir uma cópia do token_usage em arquivo para investigação/admin (evita perda por rerun)
    try:
        token_list = st.session_state.get("token_usage", [])
        token_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".last_token_usage.json"))
        with open(token_file, "w", encoding="utf-8") as _tf:
            json.dump(token_list, _tf, ensure_ascii=False, indent=2)
    except Exception:
        # Não falhar o fluxo por causa do log/persistência
        pass

    return response_text


def _inject_minichart(parecer: str, analysis_data: Dict[str, Any]) -> str:
    """
    Injeta o minichart visual comparativo na seção 4.4 do parecer.
    """
    import re
    from services.chart_renderer import (
        gerar_minichart_serasa_finscore,
        obter_valores_faixas_serasa,
        obter_valores_faixas_finscore
    )
    
    try:
        # Extrair valores
        serasa_score = analysis_data.get("serasa", 0)
        finscore_score = analysis_data.get("finscore_ajustado", 0)
        cls_serasa = analysis_data.get("classificacao_serasa", "N/A")
        cls_finscore = analysis_data.get("classificacao_finscore", "N/A")
        
        # Obter valores das faixas baseado nas classificações
        serasa_vals = obter_valores_faixas_serasa(cls_serasa)
        finscore_vals = obter_valores_faixas_finscore(cls_finscore)
        
        # Gerar minichart em base64
        chart_base64 = gerar_minichart_serasa_finscore(
            serasa_score=float(serasa_score),
            finscore_score=float(finscore_score),
            serasa_vals=serasa_vals,
            finscore_vals=finscore_vals,
            return_base64=True
        )
        
        # Construir markdown com imagem embutida
        chart_markdown = f"\n\n![Comparativo Serasa vs FinScore](data:image/png;base64,{chart_base64})\n\n"
        
        # Procurar pela seção 4.4 e injetar o gráfico logo após o título
        # Padrão: ### 4.4 Opinião (Síntese Visual)
        pattern = r'(###\s+4\.4\s+Opinião\s*\(Síntese Visual\).*?\n\n)'
        
        def replacer(match):
            return match.group(1) + chart_markdown
        
        parecer_modificado = re.sub(pattern, replacer, parecer, count=1, flags=re.DOTALL)
        
        # Se não encontrou o padrão, adicionar antes da seção 5
        if parecer_modificado == parecer:
            pattern_secao5 = r'(##\s+5\.\s+Considerações Finais)'
            fallback_chart = f"\n\n### 4.4 Opinião (Síntese Visual)\n\n{chart_markdown}\n"
            parecer_modificado = re.sub(pattern_secao5, fallback_chart + r'\1', parecer, count=1)
        
        return parecer_modificado
        
    except Exception as e:
        st.warning(f"Não foi possível gerar o gráfico comparativo: {e}")
        return parecer

        return None


def _ensure_concluding_connectors(text: str) -> str:
    """
    Garante que o último parágrafo de cada seção/tópico se inicie com uma
    conjunção conclusiva ou locução equivalente.
    """
    import re

    connectors = [
        "Em suma",
        "Em resumo",
        "Portanto",
        "Logo",
        "Destarte",
        "Assim",
        "Dessa forma",
        "Consequentemente",
        "Por conseguinte",
        "Deste modo",
    ]
    connectors_lower = [c.casefold() for c in connectors]
    connector_index = 0

    def next_connector() -> str:
        nonlocal connector_index
        connector = connectors[connector_index % len(connectors)]
        connector_index += 1
        return connector

    def lowercase_first_alpha(sentence: str) -> str:
        for idx, ch in enumerate(sentence):
            if ch.isalpha():
                return sentence[:idx] + ch.lower() + sentence[idx + 1 :]
        return sentence

    lines = text.split("\n")
    heading_indexes = [idx for idx, line in enumerate(lines) if line.strip().startswith("#")]
    heading_indexes.append(len(lines))

    for i in range(len(heading_indexes) - 1):
        start = heading_indexes[i]
        end = heading_indexes[i + 1]
        if end - start <= 1:
            continue

        section = lines[start + 1:end]
        paragraphs = []
        cursor = 0

        while cursor < len(section):
            if section[cursor].strip() == "":
                cursor += 1
                continue

            para_start = cursor
            while cursor < len(section) and section[cursor].strip() != "":
                cursor += 1
            para_end = cursor
            paragraphs.append((para_start, para_end))

        for para_start, para_end in reversed(paragraphs):
            first_line = section[para_start]
            stripped = first_line.lstrip()
            if not stripped:
                continue
            if stripped.startswith(("!", "|", "```")):
                continue
            if stripped[0] in "-*+>":
                continue
            if re.match(r"^\d+[.)]", stripped):
                continue

            lowered = stripped.casefold()
            if any(lowered.startswith(conn) for conn in connectors_lower):
                break

            leading = first_line[: len(first_line) - len(stripped)]
            connector = next_connector()
            new_sentence = lowercase_first_alpha(stripped)
            section[para_start] = f"{leading}{connector}, {new_sentence}"
            break

        lines[start + 1:end] = section

    return "\n".join(lines)


def _enforce_intro_paragraphs(text: str, meta_cliente: Optional[Dict[str, Any]]) -> str:
    import re

    if not meta_cliente:
        return text

    p1, p2 = _expected_intro_paragraphs(meta_cliente)
    pattern = r"(##\s+1\.\s+Introdução\s+)(.*?)(\n##\s+2\.)"
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return text

    body = match.group(2)
    paragraphs = [seg.strip() for seg in re.split(r"\n\s*\n", body) if seg.strip()]
    remaining = paragraphs[2:] if len(paragraphs) > 2 else []
    if not remaining:
        remaining = [
            "Este parecer está organizado nas próximas seções: (i) a metodologia do FinScore e Serasa; "
            "(ii) a análise detalhada dos indicadores financeiros por categoria; (iii) a análise de risco e scoring; "
            "e (iv) as considerações finais com recomendações e covenants."
        ]

    new_body_parts = [p1, p2] + remaining
    new_body = "\n\n".join(new_body_parts).strip()

    suffix = text[match.end(2):]
    prefix = text[:match.start(2)]

    if not suffix.startswith("\n"):
        new_body = new_body + "\n\n"
    else:
        new_body = new_body + "\n"

    return prefix + new_body + suffix


def _fix_formatting_issues(text: str, meta_cliente: Optional[Dict[str, Any]] = None) -> str:
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

    text = _enforce_intro_paragraphs(text, meta_cliente)
    
    return _ensure_concluding_connectors(text)


def render():
    ss = st.session_state

    # Flags de navegacao sao processadas em app.py ANTES de chegar aqui

    # Forca cancelamento de timers de polling remanescentes da pagina de Analise
    components.html(
        """
        <script>
        (function(){
            const win = window.parent || window;
            if (!win) { return; }
            if (win.__fsInsightTimer) {
                clearTimeout(win.__fsInsightTimer);
                win.__fsInsightTimer = null;
            }
        })();
        </script>
        """,
        height=0,
    )

    # CSS específico para barra de progresso desta view (aplicado uma única vez)
    if not ss.get("_parecer_progress_css"):
        st.markdown(
            """
            <style>
            .parecer-progress {
                margin: 1.25rem 0 0.75rem 0 !important;
            }
            .parecer-progress-track {
                position: relative;
                width: 100%;
                font-size: clamp(1.6rem, 2.8vw, 2.05rem);
                height: 1em;
                border-radius: 999px;
                background: #ffffff;
                border: 1px solid #e0e7ff;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.08);
                overflow: hidden;
            }
            .parecer-progress-fill {
                display: block;
                height: 100%;
                border-radius: inherit;
                background: linear-gradient(90deg, #0f9d58, #34c759);
                transition: width .45s ease-in-out;
                position: relative;
            }
            .parecer-progress-fill::after {
                content: "";
                position: absolute;
                inset: 0;
                background: linear-gradient(120deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.45) 50%, rgba(255,255,255,0) 100%);
                animation: parecer-sheen 1.6s ease-in-out infinite;
                border-radius: inherit;
            }
            .parecer-progress-label {
                position: absolute;
                inset: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.46em;
                color: #0f5132;
                font-weight: 700;
                letter-spacing: 0.02em;
            }
            @keyframes parecer-sheen {
                0% { transform: translateX(-150%); }
                100% { transform: translateX(150%); }
            }
            .parecer-progress-message p {
                margin: 0.15rem 0 0 0;
                color: #6b7280;
                font-weight: 600;
                font-style: italic;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        ss["_parecer_progress_css"] = True

    st.markdown("<h3 style='text-align: center;'>📜 Parecer Técnico</h3>", unsafe_allow_html=True)

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
    
    # Empresa/CNPJ centralizado
    empresa = meta.get("empresa", "Empresa")
    cnpj = meta.get("cnpj", "")
    st.markdown(
        f"<div style='text-align: center;'><span style='font-size: 1.5rem; color: #708090; font-weight: 400;'>{empresa} | {cnpj}</span></div>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Header em duas colunas com estrutura de tabela
    col1, col2 = st.columns([2, 1], gap="large")
    
    # Preparar valores
    finscore_val = f"{finscore_aj:.2f}" if finscore_aj is not None else "N/A"
    serasa_val = f"{serasa_score:.0f}" if serasa_score is not None else "N/A"
    decisao_label = {
        "aprovar": "✅ Aprovar",
        "aprovar_com_ressalvas": "⚠️ Aprovar com Ressalvas",
        "nao_aprovar": "❌ Não Aprovar"
    }.get(resultado["decisao"], resultado["decisao"])
    
    # Críticas
    if finscore_aj is not None:
        if cls_fin == "Muito Abaixo do Risco":
            critica_finscore = "Indicadores patrimoniais, econômicos e contábeis sugerem desempenho significativamente superior ao benchmark do setor."
        elif cls_fin == "Levemente Abaixo do Risco":
            critica_finscore = "Dados fornecidos apontam para desempenho levemente acima da média setorial em múltiplos indicadores."
        elif cls_fin == "Neutro":
            critica_finscore = "Indicadores apresentam-se consistentes com o esperado para empresas comparáveis do setor."
        elif cls_fin == "Levemente Acima do Risco":
            critica_finscore = "Há indícios de desempenho abaixo da média setorial, sugerindo necessidade de monitoramento."
        else:
            critica_finscore = "Indicadores sugerem desempenho significativamente inferior ao benchmark, com possíveis fragilidades estruturais."
    else:
        critica_finscore = "Dados insuficientes para análise do FinScore."
    
    if serasa_score is not None:
        if cls_ser == "Excelente":
            critica_serasa = "Pontuação indica histórico consistente com baixa probabilidade de inadimplência no horizonte de análise."
        elif cls_ser == "Bom":
            critica_serasa = "Pontuação sugere comportamento de crédito dentro de parâmetros aceitáveis, com risco moderado."
        elif cls_ser == "Baixo":
            critica_serasa = "Pontuação aponta para possíveis restrições no histórico, indicando maior probabilidade de inadimplência."
        else:
            critica_serasa = "Pontuação sugere histórico com restrições relevantes, compatível com risco elevado de inadimplência."
    else:
        critica_serasa = "Dados de Serasa não disponíveis."
    
    if resultado["decisao"] == "aprovar":
        critica_decisao = "Dados analisados indicam perfil de risco compatível com aprovação, dentro dos parâmetros estabelecidos."
    elif resultado["decisao"] == "aprovar_com_ressalvas":
        critica_decisao = "Perfil sugere aprovação condicional, com recomendação de cláusulas restritivas e acompanhamento periódico."
    else:
        critica_decisao = "Indicadores analisados sugerem perfil de risco incompatível com os critérios de aprovação vigentes."
    
    # Renderizar em formato de tabela HTML para alinhamento perfeito
    st.markdown(f"""
    <style>
        .parecer-table {{ 
            background: #f5f7fb !important; 
            border: 0 !important;
            border-spacing: 0 !important;
        }}
        .parecer-table tr {{ 
            background: #f5f7fb !important; 
            border: 0 !important;
        }}
        .parecer-table td {{ 
            background: #f5f7fb !important; 
            border: 0 !important;
            border-top: 0 !important;
            border-bottom: 0 !important;
            border-left: 0 !important;
            border-right: 0 !important;
        }}
    </style>
    <table class="parecer-table" style="width: 100%; border-collapse: collapse; background: #f5f7fb !important; border: 0 !important;">
        <tr style="border: 0 !important; background: #f5f7fb !important;">
            <td style="width: 60%; vertical-align: top; padding: 12px 0; border: 0 !important; background: #f5f7fb !important;">
                <strong>FinScore:</strong><br>
                {finscore_val} ({cls_fin or 'N/A'})
            </td>
            <td style="width: 40%; vertical-align: top; padding: 12px 0; border: 0 !important; background: #f5f7fb !important;">
                {critica_finscore}
            </td>
        </tr>
        <tr style="border: 0 !important; background: #f5f7fb !important;">
            <td style="vertical-align: top; padding: 12px 0; border: 0 !important; background: #f5f7fb !important;">
                <strong>Serasa:</strong><br>
                {serasa_val} ({cls_ser or 'N/A'})
            </td>
            <td style="vertical-align: top; padding: 12px 0; border: 0 !important; background: #f5f7fb !important;">
                {critica_serasa}
            </td>
        </tr>
        <tr style="border: 0 !important; background: #f5f7fb !important;">
            <td style="vertical-align: top; padding: 12px 0; border: 0 !important; background: #f5f7fb !important;">
                <strong>Decisão Final:</strong><br>
                {decisao_label}
            </td>
            <td style="vertical-align: top; padding: 12px 0; border: 0 !important; background: #f5f7fb !important;">
                {critica_decisao}
            </td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

    st.divider()

    # ========================================
    # SEÇÃO 2: GERAÇÃO DO PARECER NARRATIVO
    # ========================================
    
    # Botão para gerar parecer - centralizado
    col_left, col_center, col_right = st.columns([1, 1, 1])
    
    with col_center:
        gerar = st.button("Gerar Parecer", use_container_width=True, type="primary")
    
    if gerar:
        # Criar barra de progresso customizada
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            progress_visual = st.empty()
            status_text = st.empty()

        def _render_progress_bar(percent: int) -> None:
            bounded = max(0, min(100, percent))
            progress_visual.markdown(
                f"""
                <div class="parecer-progress">
                    <div class="parecer-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{bounded}" aria-valuetext="{bounded}% concluído">
                        <span class="parecer-progress-fill" style="width:{bounded}%;"></span>
                        <span class="parecer-progress-label">{bounded}%</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        def update_progress(pct: int, message: str) -> None:
            bounded = max(0, min(100, pct))
            _render_progress_bar(bounded)
            status_text.markdown(f"<div class='parecer-progress-message'><p><em>{message}</em></p></div>", unsafe_allow_html=True)

        update_progress(4, "⚙️ Preparando ambiente para geração do parecer...")
        time.sleep(0.35)
        
        try:
            # Etapas iniciais (feedback adicional para reduzir ansiedade)
            pre_steps = [
                (12, "📁 Inicializando pipeline de análise..."),
                (22, "🧮 Validando dados contábeis e metadados..."),
                (32, "🔗 Carregando estruturas auxiliares..."),
            ]
            for pct, message in pre_steps:
                update_progress(pct, message)
                time.sleep(0.4)

            # Etapa 1: Extrair dados
            update_progress(44, "🔎 Extraindo dados consolidados...")
            analysis_data = _extract_analysis_data(o)
            time.sleep(0.4)

            # Etapa intermediária (motor determinístico)
            update_progress(58, "🧠 Aplicando motor de políticas e regras de crédito...")
            time.sleep(0.4)

            # Etapa 2: Gerar parecer
            progresso_base = "🤖 Gerando narrativa da análise econômica, contábil e patrimonial da empresa..."
            update_progress(74, progresso_base)

            parecer = _generate_parecer_ia(
                decisao_motor=resultado["decisao"],
                motivos_motor=resultado.get("motivos", []),
                covenants_motor=resultado.get("covenants", []),
                analysis_data=analysis_data,
                meta_cliente=meta
            )

            # Etapa 3: Finalizar
            update_progress(88, "📝 Finalizando formatação e salvando resultado...")
            time.sleep(0.4)

            if parecer:
                ss["parecer_gerado"] = parecer
                # Expor token_usage para inspeção rápida no console do navegador
                try:
                    import json as _json
                    token_js = _json.dumps(st.session_state.get("token_usage", []), ensure_ascii=False)
                    st.markdown(f"<pre id='token-usage-debug' style='display:none'>{token_js}</pre>", unsafe_allow_html=True)
                except Exception:
                    pass
                # Atualiza 100% ANTES de limpar placeholders (evita erro 'setIn' em elementos removidos)
                try:
                    update_progress(100, "✅ Parecer gerado com sucesso!")
                except Exception:
                    # Se a barra já foi removida por algum motivo, ignorar
                    pass
                # Limpar componentes de progresso após breve pausa
                time.sleep(0.3)
                progress_placeholder.empty()
                status_text.empty()
                # Travar navegacao em /Parecer apos rerun
                NavigationFlow.request_lock_parecer()
                st.session_state["_pending_nav_target"] = "parecer"
                st.rerun()
            else:
                update_progress(100, "⚠️ Não foi possível gerar o parecer automaticamente.")
                st.warning("Não recebemos resposta do modelo de IA. Tente novamente em instantes.")
        except Exception as e:
            progress_placeholder.empty()
            status_text.empty()
            st.error(f"Erro ao gerar parecer: {e}")
    
    # Exibir parecer se já foi gerado
    if ss.get("parecer_gerado"):
        st.divider()
        
        # Container para o parecer com fundo destacado
        with st.container():
            st.markdown(ss["parecer_gerado"])
        
        st.divider()
        
        # Ações pós-geração
        col_left, col_center, col_right = st.columns([1, 1, 1])
        
        with col_center:
            try:
                import sys
                import os
                # Adicionar o diretório app_front ao path se necessário
                app_front_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if app_front_dir not in sys.path:
                    sys.path.insert(0, app_front_dir)
                
                from pdf.export_pdf import gerar_pdf_parecer
                pdf_disponivel = True
                
            except ImportError as e:
                pdf_disponivel = False
                import_error = str(e)
            
            if st.button("📃 Exportar PDF", use_container_width=True, disabled=not pdf_disponivel):
                if pdf_disponivel:
                    try:
                        with st.spinner("Gerando PDF profissional..."):
                            # Preparar metadados
                            pdf_meta = {
                                "empresa": meta.get("empresa", "Empresa"),
                                "cnpj": meta.get("cnpj", "N/A"),
                                "data_analise": meta.get("serasa_data", ""),
                                "finscore_ajustado": f"{finscore_aj:.2f}" if finscore_aj is not None else "N/A",
                                "classificacao_finscore": cls_fin or "N/A",
                                "serasa_score": f"{serasa_score:.0f}" if serasa_score is not None else "N/A",
                                "classificacao_serasa": cls_ser or "N/A",
                                "decisao": resultado["decisao"],
                                "serasa_data": meta.get("serasa_data"),
                                "ano_inicial": meta.get("ano_inicial"),
                                "ano_final": meta.get("ano_final"),
                                "cidade_relatorio": meta.get("cidade_relatorio", "São Paulo (SP)")
                            }
                            
                            # Gerar PDF (engine auto-detectado baseado na plataforma)
                            pdf_bytes = gerar_pdf_parecer(
                                conteudo=ss["parecer_gerado"],
                                meta=pdf_meta,
                                is_markdown=True
                                # engine=None detecta automaticamente:
                                # Windows → xhtml2pdf
                                # Linux/Mac → playwright (se disponível)
                            )
                            
                            # Nome do arquivo
                            empresa_safe = meta.get("empresa", "Empresa").replace(" ", "_")
                            pdf_filename = f"Parecer_{empresa_safe}_{meta.get('cnpj', 'CNPJ').replace('.', '').replace('/', '').replace('-', '')}.pdf"
                            
                            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                            components.html(
                                f"""
                                <html>
                                <body>
                                <script>
                                (function() {{
                                    const link = document.createElement('a');
                                    link.href = 'data:application/pdf;base64,{b64_pdf}';
                                    link.download = '{pdf_filename}';
                                    link.style.display = 'none';
                                    document.body.appendChild(link);
                                    link.click();
                                    setTimeout(() => document.body.removeChild(link), 1000);
                                }})();
                                </script>
                                </body>
                                </html>
                                """,
                                height=0,
                                width=0,
                            )
                            st.success("PDF gerado com sucesso!")
                    except Exception as e:
                        import traceback
                        st.error(f"Erro ao gerar PDF: {str(e)}")
                        with st.expander("🔍 Detalhes do erro"):
                            st.code(traceback.format_exc())
                        st.info("💡 **Soluções comuns:**\n" + 
                                "1. Certifique-se que o Chromium está instalado: `python -m playwright install chromium`\n" +
                                "2. Reinicie o app Streamlit\n" +
                                "3. Verifique se o ambiente virtual está ativo")
                else:
                    if 'import_error' in locals():
                        st.warning(f"Módulo PDF não disponível: {import_error}")
                    st.info("📦 **Instale as dependências:**\n\n1. `pip install playwright jinja2 markdown-it-py`\n2. `python -m playwright install chromium`")
        restart_col = st.columns([1, 1, 1])[1]
        with restart_col:
            if st.button("Iniciar novo ciclo", key="btn_novo_ciclo_parecer", use_container_width=True):
                clear_flow_state()
                nav.restart()
                st.rerun()
