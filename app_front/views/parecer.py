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
    data["pmr"] = _safe_float(indices_row.get("PMR (dias)"))
    data["pmp"] = _safe_float(indices_row.get("PMP (dias)"))
    data["giro_ativo"] = _safe_float(indices_row.get("Giro do Ativo (x)"))
    
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
Você é um analista de crédito sênior com 15+ anos de experiência em avaliação de risco corporativo.
Sua tarefa é redigir um parecer técnico profissional baseado nos dados financeiros e na decisão determinística fornecida.

**CONTEXTO DA ANÁLISE:**
Empresa: {empresa}
CNPJ: {cnpj}

**PRÉ-VEREDITO (INALTERÁVEL):**
Decisão: {decisao_motor}
Motivos: {', '.join(motivos_motor) if motivos_motor else 'Nenhum motivo específico'}
Covenants sugeridos: {', '.join(covenants_motor) if covenants_motor else 'Nenhum covenant'}

**METODOLOGIA DE CLASSIFICAÇÃO:**

FinScore - Faixas de Risco:
• Muito Abaixo do Risco: > 875 pontos (risco mínimo)
• Levemente Abaixo do Risco: 750-875 pontos (risco controlado)
• Neutro: 250-750 pontos (risco moderado)
• Levemente Acima do Risco: 125-250 pontos (risco elevado)
• Muito Acima do Risco: < 125 pontos (risco crítico)

Serasa - Classificação de Crédito:
• Excelente: 851-1000 pontos
• Bom: 701-850 pontos
• Baixo: 0-400 pontos
• Muito Baixo: sem cadastro ou dados insuficientes

Critérios de Decisão:
1. FinScore = indicador PRIMÁRIO (define aprovação/reprovação)
2. Serasa = complementar (pode adicionar ressalvas)
3. DL/EBITDA ≤ 3,0x (meta de endividamento saudável)
4. Cobertura de Juros ≥ 1,5x (capacidade mínima de pagamento)

**DADOS FINANCEIROS COMPLETOS:**
{dados_formatados}

**ESTRUTURA OBRIGATÓRIA DO PARECER:**

## 1. Introdução
Breve contextualização da empresa e objetivo da análise (2-3 frases).

## 2. Resumo Executivo
Visão geral da situação financeira e patrimonial da empresa, destacando:
- Classificação FinScore e Serasa
- Principal conclusão sobre capacidade de pagamento
- Recomendação de crédito (2-3 parágrafos)

## 3. Metodologia

Este parecer utiliza dois sistemas complementares de avaliação de risco de crédito:

**FinScore** é o score proprietário principal, calculado através de análise multivariada (PCA) de 15+ indicadores financeiros, resultando em uma pontuação que classifica o risco da empresa em 5 faixas:

| Faixa de Pontuação | Classificação de Risco |
|-------------------|------------------------|
| > 875 | Muito Abaixo do Risco |
| 750 - 875 | Levemente Abaixo do Risco |
| 250 - 750 | Neutro |
| 125 - 250 | Levemente Acima do Risco |
| < 125 | Muito Acima do Risco |

**Serasa Score** é o indicador de mercado utilizado como complemento, refletindo o comportamento de crédito da empresa no mercado brasileiro:

| Faixa de Pontuação | Classificação |
|-------------------|---------------|
| 851 - 1000 | Excelente |
| 701 - 850 | Bom |
| 0 - 400 | Baixo |
| Sem cadastro | Muito Baixo |

**Critério de Decisão:** O FinScore é o indicador primário para aprovação ou reprovação de crédito. O Serasa complementa a análise e pode adicionar ressalvas (covenants) quando indicar risco adicional, mesmo com FinScore aprovando.

## 4. Análise Detalhada dos Indicadores

### 4.1 Indicadores de Liquidez
Analise TODOS os índices disponíveis:
- Liquidez Corrente, Liquidez Seca, Liquidez Imediata
- CCL/Ativo Total
- Interprete se a empresa tem capacidade de honrar obrigações de curto prazo

### 4.2 Indicadores de Endividamento e Estrutura de Capital
Analise TODOS os índices disponíveis:
- Alavancagem (DL/EBITDA)
- Endividamento (Passivo/Ativo)
- Cobertura de Juros (EBITDA/Despesas Financeiras)
- Composição do Endividamento
- Avalie se a estrutura de capital é saudável

### 4.3 Indicadores de Rentabilidade
Analise TODOS os índices disponíveis:
- ROE (Retorno sobre Patrimônio)
- ROA (Retorno sobre Ativos)
- Margem Líquida
- Margem EBITDA
- Avalie a capacidade de geração de lucro

### 4.4 Indicadores de Eficiência Operacional
Analise TODOS os índices disponíveis:
- PMR (Prazo Médio de Recebimento)
- PMP (Prazo Médio de Pagamento)
- PME (Prazo Médio de Estocagem)
- Giro do Ativo
- Ciclo Operacional e Ciclo Financeiro
- Avalie a eficiência da gestão operacional

### 4.5 Dados Patrimoniais e de Resultado
Mencione valores absolutos quando disponíveis:
- Receita Total
- Lucro Líquido
- EBITDA
- Ativo Total
- Patrimônio Líquido
- Passivo Total
- Contextualize o porte e evolução da empresa

## 5. Análise de Risco e Scoring

### 5.1 FinScore
- Valor obtido: [mencionar pontuação exata]
- Classificação: [mencionar faixa]
- Interpretação detalhada do que significa esse score

### 5.2 Serasa
- Valor obtido: [mencionar pontuação exata]
- Classificação: [mencionar faixa]
- Como complementa a análise do FinScore

### 5.3 Síntese de Risco
Consolidação dos dois scores e o que indicam sobre o risco de crédito.

## 6. Considerações Finais
- Reitere a decisão: {decisao_motor}
- Justificativa técnica final baseada nos dados
- Se houver covenants, explique em detalhes cada um e sua importância
- Recomendações adicionais (ex: monitoramento, condições especiais)

**DIRETRIZES DE REDAÇÃO:**
✓ Use linguagem técnica mas acessível
✓ Seja objetivo e direto
✓ Sempre justifique com números e fatos dos dados fornecidos
✓ Destaque tanto pontos positivos quanto negativos
✓ CITE valores exatos dos índices (não generalize)
✓ Mencione TODOS os índices presentes nos dados
✓ Use percentuais para margens e retornos (ex: 15% em vez de 0,15)
✓ Use "x vezes" para múltiplos (ex: 2,5x em vez de 2,5)
✓ Máximo 1000 palavras
✓ Formatação markdown: use ##, **, - para estruturar

**REGRA FUNDAMENTAL:**
A decisão "{decisao_motor}" é FINAL e IMUTÁVEL.
Você NÃO decide - você REDIGE e JUSTIFICA a decisão já tomada.
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
    st.subheader("📋 Pré-Veredito (Motor Determinístico)")
    
    col1, col2 = st.columns([1, 2])
    
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
    
    # Dados chave usados na decisão
    with st.expander("📊 Ver dados-chave da decisão"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("FinScore Ajustado", f"{finscore_aj:.0f}" if finscore_aj else "N/A")
            st.caption(cls_fin or "N/A")
        with col_b:
            st.metric("DL/EBITDA", f"{dl_ebitda:.2f}x" if dl_ebitda else "N/A")
            st.caption("Meta: ≤ 3.0x")
        with col_c:
            st.metric("Cobertura Juros", f"{cobertura:.2f}x" if cobertura else "N/A")
            st.caption("Meta: ≥ 1.5x")

    st.divider()

    # ========================================
    # SEÇÃO 2: GERAÇÃO DO PARECER NARRATIVO
    # ========================================
    st.subheader("📝 Parecer Técnico Completo")
    
    st.markdown("""
    O parecer narrativo consolida:
    - ✅ Decisão determinística (inalterável)
    - 📊 Análise de todos os indicadores financeiros
    - 📈 Dados de gráficos e tabelas
    - 🎯 Comparação FinScore vs Serasa
    - 💡 Recomendações e justificativas
    """)
    
    # Botão para gerar parecer
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        gerar = st.button("🤖 Gerar Parecer IA", use_container_width=True, type="primary")
    
    with col_btn2:
        if "parecer_gerado" in ss:
            if st.button("🔄 Regenerar", use_container_width=True):
                gerar = True
                del ss["parecer_gerado"]
    
    if gerar:
        with st.spinner("🤖 Analisando dados e gerando parecer técnico..."):
            # Extrair dados consolidados
            analysis_data = _extract_analysis_data(o)
            
            # Gerar parecer
            parecer = _generate_parecer_ia(
                decisao_motor=resultado["decisao"],
                motivos_motor=resultado.get("motivos", []),
                covenants_motor=resultado.get("covenants", []),
                analysis_data=analysis_data,
                meta_cliente=meta
            )
            
            if parecer:
                ss["parecer_gerado"] = parecer
                st.success("✅ Parecer gerado com sucesso!")
                st.rerun()
    
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
