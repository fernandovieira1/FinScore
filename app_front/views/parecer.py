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

Este parecer baseia-se em dois instrumentos complementares de avaliação de risco de crédito: o **FinScore** e o **Serasa Score**.

### 2.1 FinScore

O **FinScore** é um índice sintético (escala 0–1000) que avalia a higidez patrimonial, econômica e financeira da empresa a partir de suas demonstrações contábeis recentes. Inspirado em metodologias consagradas como o Altman Z-Score, o FinScore foi desenvolvido especificamente para captar múltiplas dimensões do risco de crédito através de um processo analítico em cinco etapas:

1. **Cálculo de Índices Contábeis**: Extração de 15+ indicadores cobrindo rentabilidade (ROA, ROE, margens), liquidez (corrente, seca, CCL/Ativo), endividamento (alavancagem, cobertura de juros), eficiência operacional (giro do ativo, PMR, PMP) e estrutura de capital.

2. **Padronização Estatística**: Transformação de todos os índices via z-score (média zero, desvio-padrão um) para garantir comparabilidade entre indicadores de diferentes naturezas e escalas.

3. **Redução de Dimensionalidade (PCA)**: Aplicação de Análise de Componentes Principais para condensar a informação em poucos fatores independentes, identificando os padrões mais relevantes e eliminando redundâncias.

4. **Consolidação Temporal**: Agregação de até três exercícios consecutivos com ponderação decrescente (60% para o ano mais recente, 25% para o anterior e 15% para o mais antigo), equilibrando sensibilidade a mudanças recentes e consistência histórica.

5. **Escalonamento e Classificação**: Transformação do escore consolidado para a escala 0–1000 e classificação em faixas interpretativas de risco.

O FinScore é o **indicador primário** deste parecer, pois reflete diretamente a capacidade financeira estrutural da empresa.

**Tabela – Classificação FinScore**

| Faixa de Pontuação | Classificação de Risco | Interpretação |
|-------------------:|:-----------------------|:--------------|
| > 875 | Muito Abaixo do Risco | Perfil financeiro excepcional, risco mínimo |
| 750 – 875 | Levemente Abaixo do Risco | Situação confortável, baixo risco |
| 250 – 750 | Neutro | Situação intermediária, sem sinais claros de excelência ou fragilidade |
| 125 – 250 | Levemente Acima do Risco | Atenção recomendada, sinais de fragilidade |
| < 125 | Muito Acima do Risco | Risco elevado, análise detalhada necessária |

### 2.2 Serasa Score

O **Serasa Score** é um indicador externo de mercado amplamente utilizado no Brasil, que avalia o risco de inadimplência com base no histórico de pagamentos, informações cadastrais e comportamento de crédito da empresa ao longo do tempo. Diferentemente do FinScore, o Serasa não analisa a estrutura financeira interna, mas sim o track record de cumprimento de obrigações.

Neste parecer, o Serasa funciona como **indicador complementar**, útil para identificar divergências entre a capacidade financeira atual (FinScore) e o histórico de comportamento de crédito (Serasa). Divergências significativas podem sinalizar riscos ocultos ou oportunidades mal avaliadas pelo mercado.

**Tabela – Classificação Serasa**

| Faixa de Pontuação | Classificação | Significado |
|-------------------:|:--------------|:------------|
| 851 – 1000 | Excelente | Histórico de crédito exemplar |
| 701 – 850 | Bom | Comportamento de pagamento satisfatório |
| 0 – 400 | Baixo | Histórico comprometido, atenção necessária |
| Sem cadastro | Muito Baixo | Ausência de histórico de crédito |

### 2.3 Dados Contábeis e Índices Financeiros

Embora os dados contábeis brutos e os índices financeiros individuais já estejam sintetizados no FinScore através da metodologia explanada (padronização, PCA e ponderação temporal), eles serão **contextualizados e analisados individualmente** ao longo deste parecer. Essa análise detalhada serve como **critério complementar** fundamental, permitindo:

- Identificar quais dimensões específicas (liquidez, rentabilidade, endividamento, eficiência) mais influenciaram o resultado do FinScore;
- Detectar vulnerabilidades ou pontos fortes que merecem atenção especial, mesmo quando o escore geral é satisfatório;
- Fornecer subsídios objetivos para a definição de covenants e condições de crédito;
- Contextualizar a trajetória histórica da empresa e tendências observadas nos últimos exercícios.

Os índices apresentados nas próximas seções não substituem o FinScore, mas sim o **explicam e enriquecem**, oferecendo uma visão multidimensional que fundamenta a decisão técnica de crédito.

### 2.4 Critérios de Decisão

A decisão de crédito apresentada neste parecer integra múltiplos elementos em uma avaliação holística:

1. **FinScore (Indicador Primário)**: O FinScore é a base da análise, pois condensa de forma objetiva e comparável a saúde financeira estrutural da empresa. Sua classificação em faixas de risco orienta a decisão inicial.

2. **Serasa Score (Validação Cruzada)**: O Serasa complementa o FinScore ao trazer a perspectiva do histórico de crédito e comportamento de pagamento. A convergência entre FinScore e Serasa reforça a confiabilidade da avaliação; divergências significativas demandam investigação qualitativa para distinguir riscos conjunturais de estruturais.

3. **Índices Financeiros Detalhados (Critérios Complementares)**: A análise granular de liquidez, endividamento, rentabilidade e eficiência operacional permite compreender **como** e **por que** a empresa atingiu determinado FinScore, identificando drivers específicos de risco ou solidez.

4. **Contexto Temporal e Setorial**: A ponderação temporal e a consideração das particularidades do setor de atuação contextualizam a análise, evitando interpretações equivocadas de eventos atípicos ou características intrínsecas à atividade empresarial.

**Em síntese**: a decisão final ({decisao_motor}) resulta da **convergência** entre o escore sintético (FinScore), a validação externa (Serasa), a análise detalhada dos fundamentos financeiros (índices contábeis) e a interpretação qualitativa do contexto empresarial. Este parecer apresenta não apenas uma recomendação, mas os **fundamentos técnicos e objetivos** que a sustentam.

---

## 3. Análise Detalhada dos Indicadores

### 3.1 Liquidez

Apresente e interprete:
- Liquidez Corrente
- Liquidez Seca
- CCL/Ativo Total

Comente sobre capacidade de pagamento de curto prazo, eventuais alertas (como liquidez seca negativa) e possíveis causas.

### 3.2 Endividamento e Estrutura de Capital

Analise:
- DL/EBITDA (Alavancagem)
- Passivo/Ativo (Endividamento)
- Cobertura de Juros

Indique se a empresa apresenta equilíbrio de capital e capacidade de pagamento de juros.

### 3.3 Rentabilidade

Avalie:
- ROE (Retorno sobre Patrimônio)
- ROA (Retorno sobre Ativos)
- Margem Líquida
- Margem EBITDA

Comente sobre retorno ao acionista, eficiência na geração de lucros e eventuais margens anômalas (>100%).

### 3.4 Eficiência Operacional

Analise os seguintes indicadores:
- **PMR (Prazo Médio de Recebimento)**: Tempo médio em dias que a empresa leva para receber de seus clientes
- **PMP (Prazo Médio de Pagamento)**: Tempo médio em dias que a empresa leva para pagar seus fornecedores
- **Giro do Ativo**: Eficiência da empresa em gerar receita a partir de seus ativos totais (Receita Total / Ativo Total)

Interprete a gestão do ciclo financeiro: PMR menor que PMP indica folga de caixa operacional; o contrário pode sinalizar pressão de liquidez. O Giro do Ativo elevado sugere boa utilização dos recursos, enquanto valores muito baixos podem indicar ativos ociosos ou subutilizados.

### 3.5 Dados Patrimoniais e de Resultado

Apresente em formato tabular:

| Indicador | Valor |
|-----------|------:|
| Receita Total | [valor] |
| Lucro Líquido | [valor] |
| Ativo Total | [valor] |
| Patrimônio Líquido | [valor] |
| Passivo Total | [valor] |

Finalize com 2–3 frases sobre o porte e desempenho geral.

---

## 4. Análise de Risco e Scoring

### 4.1 FinScore

Explique o valor e a classificação do FinScore. Interprete o significado em termos de solidez patrimonial e risco de inadimplência.

### 4.2 Serasa

Analise o valor e a classificação Serasa, destacando como complementa o FinScore e se sugere atenção adicional.

### 4.3 Síntese de Risco

Compare e concilie FinScore e Serasa, indicando convergências e eventuais tensões entre as avaliações.

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

    dl_ebitda = _safe_float(indices_row.get("Alavancagem"))
    cobertura = _safe_float(indices_row.get("Cobertura de Juros"))

    pi = PolicyInputs(
        finscore_ajustado=finscore_aj,
        dl_ebitda=dl_ebitda,
        cobertura_juros=cobertura,
        serasa_rank=RANK_SERASA.get(cls_ser),
        finscore_rank=RANK_FINSCORE.get(cls_fin),
        flags_qualidade={"dados_incompletos": False},
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
            st.markdown("**Covenants Sugeridos:**")
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
