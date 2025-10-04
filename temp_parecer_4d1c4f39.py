import math
import json
from typing import Dict, Any, Optional

import streamlit as st

from components.policy_engine import PolicyInputs, decide
from components.llm_client import _invoke_model, MODEL_NAME, MODEL_TEMPERATURE

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
    data["margem_liquida"] = _safe_float(indices_row.get("Margem Liquida"))
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
Você é um analista de crédito experiente. Gere um parecer técnico completo e profissional para análise de crédito.

**EMPRESA:** {empresa} (CNPJ: {cnpj})

**PRÉ-VEREDITO DETERMINÍSTICO (NÃO ALTERE):**
- Decisão: {decisao_motor}
- Motivos: {', '.join(motivos_motor) if motivos_motor else 'Nenhum motivo adicional'}
- Covenants sugeridos: {', '.join(covenants_motor) if covenants_motor else 'Nenhum covenant específico'}

**DADOS DA ANÁLISE FINANCEIRA:**
{dados_formatados}

**INSTRUÇÕES:**
1. Mantenha a decisão do motor ({decisao_motor}) como FINAL e INALTERÁVEL
2. Redija um parecer narrativo estruturado em seções:
   - Resumo Executivo (2-3 parágrafos)
   - Análise dos Indicadores Financeiros (liquidez, endividamento, rentabilidade, eficiência)
   - Análise de Risco (baseado em FinScore e Serasa)
   - Conclusão e Recomendações
3. Use linguagem técnica mas acessível
4. Destaque pontos positivos e negativos de forma equilibrada
5. Justifique a decisão com base nos dados apresentados
6. Se houver covenants, explique sua importância
7. Máximo de 800 palavras
8. Use markdown para formatação (**, ##, -, etc)

**IMPORTANTE:** A decisão final é "{decisao_motor}" e isso NÃO PODE ser alterado pela sua análise.
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
        response = _invoke_model(messages, MODEL_NAME, MODEL_TEMPERATURE)
        return response
    except Exception as e:
        st.error(f"Erro ao gerar parecer: {e}")
        return None


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
