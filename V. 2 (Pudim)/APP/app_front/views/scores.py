"""Resumo dos resultados FinScore Pudim."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(number) else number


def formatar_pontos(value: Any) -> str:
    number = _number(value)
    return "—" if number is None else f"{number:.2f}"


def formatar_pontos_consolidado(value: Any) -> str:
    """Formata os resultados consolidados com duas casas decimais."""
    number = _number(value)
    return "—" if number is None else f"{number:.2f}"


def formatar_percentual(value: Any) -> str:
    number = _number(value)
    return "—" if number is None else f"{number:.2%}"


def resumir_scores(output: dict[str, Any]) -> dict[str, Any]:
    """Extrai o resumo exclusivamente dos campos públicos do contrato Pudim."""
    status = dict(output.get("status_qualidade", {}))
    score = dict(output.get("finscore_observado", {}))
    model = dict(output.get("modelo", {}))
    serasa_table = output.get("df_serasa")
    serasa = (
        serasa_table.iloc[0].to_dict()
        if isinstance(serasa_table, pd.DataFrame) and not serasa_table.empty
        else {}
    )
    caps = output.get("df_caps_prudenciais")
    active_caps = caps.copy(deep=True) if isinstance(caps, pd.DataFrame) else pd.DataFrame()
    return {
        "bloqueado": not bool(status.get("apto_calculo", False)),
        "status": status.get("status", "STATUS INDISPONÍVEL"),
        "classificacao_uso": status.get("classificacao_uso", "—"),
        "apto_decisao": bool(status.get("apto_decisao", False)),
        "score_provisorio": bool(status.get("score_provisorio", False)),
        "finscore_prudencial": score.get("finscore_prudencial"),
        "finscore_pre_cap": score.get("finscore_prudencial_pre_cap"),
        "estrutural": score.get("finscore_estrutural_pos_gargalo"),
        "adaptativo": score.get("finscore_adaptativo_pos_gargalo"),
        "eo_estrutural": score.get("nucleo_EO_estrutural"),
        "fp_estrutural": score.get("nucleo_FP_estrutural"),
        "eo_adaptativo": score.get("nucleo_EO_adaptativo"),
        "fp_adaptativo": score.get("nucleo_FP_adaptativo"),
        "exercicios_prejuizo": score.get("exercicios_prejuizo_liquido"),
        "multiplicador_prejuizo": score.get("multiplicador_prejuizo_recorrente"),
        "eo_estrutural_antes_prejuizo": score.get(
            "nucleo_EO_estrutural_antes_prejuizo"
        ),
        "divergencia_modelos": score.get("divergencia_modelos"),
        "cap_aplicavel": score.get("cap_prudencial_aplicavel"),
        "intervalo_inferior": score.get("faixa_incerteza_inferior"),
        "intervalo_superior": score.get("faixa_incerteza_superior"),
        "confiabilidade": status.get("indice_confiabilidade"),
        "classificacao_confiabilidade": status.get("classificacao_confiabilidade", "—"),
        "alertas_bloqueadores": int(status.get("alertas_bloqueadores_decisao", 0)),
        "ocorrencias_criticas": int(status.get("ocorrencias_criticas", 0)),
        "modelo": f"{model.get('nome', 'Pudim')} {model.get('versao', '')}".strip(),
        "processado_em": model.get("processado_em"),
        "numero_simulacoes": int(model.get("numero_simulacoes", 0)),
        "serasa": serasa,
        "caps": active_caps,
    }


def _empresa(meta: dict[str, Any]) -> None:
    st.markdown("### 🏢 Empresa")
    columns = st.columns(3)
    columns[0].metric("Nome da empresa", meta.get("empresa") or "—")
    columns[1].metric("CNPJ", meta.get("cnpj") or "—")
    initial, final = meta.get("ano_inicial"), meta.get("ano_final")
    columns[2].metric("Período", f"{initial} – {final}" if initial and final else "—")


def _status_banner(summary: dict[str, Any]) -> None:
    message = str(summary["status"]).replace("_", " ")
    if summary["bloqueado"]:
        st.error(f"Resultado bloqueado — {message}")
    elif summary["apto_decisao"]:
        st.success(message)
    else:
        st.warning(message)
        st.caption(
            "O score foi calculado, mas não está liberado para decisão enquanto "
            "persistirem alertas prudenciais ou documentais."
        )


def _render_score_principal(summary: dict[str, Any]) -> None:
    st.markdown("### 📌 Resultado consolidado")
    columns = st.columns(4)
    columns[0].metric(
        "FinScore prudencial",
        formatar_pontos_consolidado(summary["finscore_prudencial"]),
    )
    columns[1].metric(
        "Estrutural pós-gargalo",
        formatar_pontos_consolidado(summary["estrutural"]),
    )
    columns[2].metric(
        "Adaptativo pós-gargalo",
        formatar_pontos_consolidado(summary["adaptativo"]),
    )
    columns[3].metric(
        "Confiabilidade",
        formatar_percentual(summary["confiabilidade"]),
        str(summary["classificacao_confiabilidade"]),
    )
    st.caption(
        "Escala de 0 a 1000 pontos. O FinScore prudencial incorpora gargalo e caps "
        "definidos pela metodologia; confiabilidade é apresentada separadamente."
    )


def _render_nucleos(summary: dict[str, Any]) -> None:
    st.markdown("### Núcleos da avaliação")
    columns = st.columns(4)
    columns[0].metric("EO estrutural", formatar_pontos(summary["eo_estrutural"]))
    columns[1].metric("FP estrutural", formatar_pontos(summary["fp_estrutural"]))
    columns[2].metric("EO adaptativo", formatar_pontos(summary["eo_adaptativo"]))
    columns[3].metric("FP adaptativo", formatar_pontos(summary["fp_adaptativo"]))
    loss_years = _number(summary["exercicios_prejuizo"])
    multiplier = _number(summary["multiplicador_prejuizo"])
    if loss_years is not None and multiplier is not None and multiplier < 1.0:
        st.warning(
            "Penalidade por prejuízo recorrente aplicada ao núcleo EO: "
            f"{int(loss_years)} exercícios com prejuízo; multiplicador "
            f"{multiplier:.0%}. EO estrutural antes da penalidade: "
            f"{formatar_pontos(summary['eo_estrutural_antes_prejuizo'])}."
        )


def _render_prudencial(summary: dict[str, Any]) -> None:
    st.markdown("### Controle prudencial")
    columns = st.columns(4)
    columns[0].metric("Score antes do cap", formatar_pontos(summary["finscore_pre_cap"]))
    columns[1].metric("Cap aplicável", formatar_pontos(summary["cap_aplicavel"]))
    columns[2].metric("Divergência dos modelos", formatar_pontos(summary["divergencia_modelos"]))
    columns[3].metric("Alertas bloqueadores", str(summary["alertas_bloqueadores"]))

    lower, upper = summary["intervalo_inferior"], summary["intervalo_superior"]
    if _number(lower) is not None and _number(upper) is not None:
        st.caption(f"Faixa de incerteza: {formatar_pontos(lower)} a {formatar_pontos(upper)} pontos.")

    caps = summary["caps"]
    if isinstance(caps, pd.DataFrame) and not caps.empty:
        with st.expander(f"Regras prudenciais acionadas ({len(caps)})"):
            for row in caps.itertuples(index=False):
                st.markdown(f"- **{row.regra}** — cap {formatar_pontos(row.cap)}: {row.justificativa}")


def _render_serasa(summary: dict[str, Any]) -> None:
    st.markdown("### Evidência externa — Serasa")
    serasa = summary["serasa"]
    if not serasa:
        st.info("Nenhuma evidência Serasa foi vinculada a este cálculo.")
        return
    columns = st.columns(4)
    columns[0].metric("Serasa Score", formatar_pontos(serasa.get("serasa_score")))
    columns[1].metric("Data da consulta", serasa.get("data_consulta") or "—")
    columns[2].metric("Divergência", formatar_pontos(serasa.get("divergencia_pontos")))
    columns[3].metric("Nível", str(serasa.get("nivel_divergencia") or "—").title())
    direction = serasa.get("direcao")
    if direction:
        st.caption(f"Leitura comparativa: {direction}. O Serasa não é somado ao FinScore.")
    if bool(serasa.get("restricao_grave", False)):
        st.error("A consulta registra restrição grave, tratada como evidência externa relevante.")


def _render_processamento(summary: dict[str, Any]) -> None:
    processed = summary["processado_em"]
    if isinstance(processed, datetime):
        processed_label = processed.strftime("%d/%m/%Y %H:%M:%S")
    else:
        processed_label = "—"
    st.caption(
        f"Modelo {summary['modelo']} · processado em {processed_label} · "
        f"simulações: {summary['numero_simulacoes']}."
    )


def render_scores_pudim(output: dict[str, Any], meta: dict[str, Any]) -> None:
    summary = resumir_scores(output)
    _empresa(meta)
    _status_banner(summary)
    if summary["bloqueado"]:
        columns = st.columns(3)
        columns[0].metric("Ocorrências críticas", str(summary["ocorrencias_criticas"]))
        columns[1].metric("Confiabilidade", formatar_percentual(summary["confiabilidade"]))
        columns[2].metric("Classificação de uso", str(summary["classificacao_uso"]))
        st.info("Revise as ocorrências na aba Dados Contábeis antes de recalcular.")
        _render_processamento(summary)
        return

    _render_score_principal(summary)
    _render_nucleos(summary)
    _render_prudencial(summary)
    _render_serasa(summary)
    _render_processamento(summary)


def render() -> None:
    ss = st.session_state
    output = ss.get("out")
    meta = ss.get("meta", {})
    if not output:
        _empresa(meta)
        st.info("Calcule o FinScore em **Lançamentos → Dados** para liberar o resumo.")
        return
    render_scores_pudim(output, meta)
