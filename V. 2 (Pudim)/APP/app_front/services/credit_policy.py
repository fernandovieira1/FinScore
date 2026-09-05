from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict

import pandas as pd


@dataclass(frozen=True)
class PolicyConfig:
    """Cortes da camada decisória aplicados somente ao FinScore calculado."""

    limite_nao_aprovar: float = 250.0
    limite_referencia_garantia: float = 500.0
    confiabilidade_minima_modelo: float = 0.75


DECISION_LABELS = {
    "aprovar": "Aprovar",
    "nao_aprovar": "Não aprovar",
    "dados_inconsistentes": "Dados inconsistentes",
}


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _flag_is_true(value: Any) -> bool:
    if value is None:
        return False
    try:
        if bool(pd.isna(value)):
            return False
    except (TypeError, ValueError):
        pass
    if isinstance(value, str):
        return value.strip().lower() in {"1", "sim", "s", "true", "verdadeiro"}
    return bool(value)


def _fmt_score(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _last_record(frame: Any) -> Dict[str, Any]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return {}
    return frame.iloc[-1].to_dict()


def _score_band(score: float | None, config: PolicyConfig) -> str:
    if score is None:
        return "NÃO CALCULÁVEL"
    if score < config.limite_nao_aprovar:
        return "ABAIXO DE 250"
    if score < config.limite_referencia_garantia:
        return "250 A 499,99"
    return "500 OU MAIS"


def _fmt_alert_value(value: Any, metric: str) -> str:
    number = _number(value)
    if number is None:
        return "não informado"
    if "/ ativo" in metric.lower() or "percent" in metric.lower():
        return f"{number:.2%}".replace(".", ",")
    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _blocking_alerts(output: Dict[str, Any]) -> list[Dict[str, str]]:
    frame = output.get("df_alertas_vies")
    if not isinstance(frame, pd.DataFrame) or frame.empty or "bloqueia_decisao" not in frame:
        return []
    result: list[Dict[str, str]] = []
    for record in frame.loc[frame["bloqueia_decisao"].eq(True)].to_dict(orient="records"):
        metric = str(record.get("metrica") or record.get("conta") or "Indicador")
        year = str(record.get("ano") or "período analisado")
        observed = _fmt_alert_value(record.get("valor_observado"), metric)
        reference = _fmt_alert_value(record.get("valor_referencia"), metric)
        result.append(
            {
                "titulo": f"{metric} — {year}",
                "motivo": f"O valor observado foi {observed}; o parâmetro de validação é {reference}.",
                "impacto": str(record.get("impacto_provavel") or "Exige validação documental."),
                "providencia": str(
                    record.get("acao_recomendada")
                    or "Confirmar o dado e anexar os documentos comprobatórios."
                ),
            }
        )
    return result


def _quality_blocking_events(output: Dict[str, Any]) -> list[Dict[str, str]]:
    frame = output.get("df_qualidade")
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []
    decision_mask = frame.get(
        "bloqueia_decisao", pd.Series(False, index=frame.index)
    ).eq(True)
    calculation_mask = frame.get(
        "bloqueia_calculo", pd.Series(False, index=frame.index)
    ).eq(True)
    result: list[Dict[str, str]] = []
    for record in frame.loc[decision_mask | calculation_mask].to_dict(orient="records"):
        issue_type = str(record.get("tipo") or "inconsistência").replace("_", " ")
        account = str(record.get("conta") or "dados contábeis")
        years = str(record.get("exercicios") or "período analisado")
        result.append(
            {
                "titulo": f"{issue_type.capitalize()} — {account} ({years})",
                "motivo": str(
                    record.get("detalhe")
                    or "O controle de qualidade não foi atendido."
                ),
                "impacto": (
                    "Impede o cálculo e a decisão de crédito."
                    if bool(record.get("bloqueia_calculo"))
                    else "Impede o uso do resultado na decisão de crédito."
                ),
                "providencia": (
                    "Corrigir ou confirmar o valor na demonstração de origem, reenviar os dados e "
                    "recalcular o FinScore."
                ),
            }
        )
    return result


def _audit_blocking_events(output: Dict[str, Any]) -> list[Dict[str, str]]:
    frame = output.get("df_correcoes_auditoria")
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []
    decision_mask = frame.get(
        "bloqueia_decisao", pd.Series(False, index=frame.index)
    ).eq(True)
    calculation_mask = frame.get(
        "bloqueia_calculo", pd.Series(False, index=frame.index)
    ).eq(True)
    result: list[Dict[str, str]] = []
    for record in frame.loc[decision_mask | calculation_mask].to_dict(orient="records"):
        action = str(record.get("acao") or "ajuste pendente").replace("_", " ")
        account = str(record.get("conta") or "dado contábil")
        year = str(record.get("ano") or "período analisado")
        result.append(
            {
                "titulo": f"{action.capitalize()} — {account} ({year})",
                "motivo": str(
                    record.get("evidencia")
                    or record.get("regra_descricao")
                    or "Ajuste pendente."
                ),
                "impacto": "O dado ajustado ainda não pode sustentar a decisão de crédito.",
                "providencia": (
                    "Validar o ajuste em demonstração assinada ou nota explicativa, registrar a "
                    "confirmação responsável e recalcular o FinScore."
                ),
            }
        )
    return result


def _all_blocking_details(output: Dict[str, Any]) -> list[Dict[str, str]]:
    items = [
        *_quality_blocking_events(output),
        *_audit_blocking_events(output),
        *_blocking_alerts(output),
    ]
    unique: list[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["titulo"], item["motivo"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _severe_scenario_score(output: Dict[str, Any]) -> float | None:
    scenarios = output.get("df_cenarios_deterministicos")
    if not isinstance(scenarios, pd.DataFrame) or scenarios.empty:
        return None
    rows = scenarios[scenarios["cenario"].astype(str).str.upper().eq("SEVERO")]
    return None if rows.empty else _number(rows.iloc[-1].get("finscore_prudencial"))


def _supplementary_evidence(output: Dict[str, Any]) -> Dict[str, Any]:
    """Organiza Serasa, Springate e Fleuriet sem integrá-los ao FinScore."""

    readings: list[str] = []
    attention: list[str] = []

    serasa = _last_record(output.get("df_serasa"))
    serasa_score = _number(serasa.get("serasa_score"))
    if serasa_score is None:
        readings.append("Serasa Score não informado; evidência externa indisponível.")
    else:
        direction = str(serasa.get("direcao") or "sem classificação de divergência")
        level = str(serasa.get("nivel_divergencia") or "não calculado")
        readings.append(
            f"Serasa Score de {_fmt_score(serasa_score)} pontos; comparação com o FinScore: "
            f"{direction}, com divergência {level}."
        )
        if direction == "evidência externa mais desfavorável" and level in {
            "relevante",
            "elevada",
        }:
            attention.append(
                "Serasa materialmente mais desfavorável que o FinScore."
            )
    if _flag_is_true(serasa.get("restricao_grave")):
        attention.append("Restrição grave registrada na consulta ao Serasa.")

    springate = _last_record(output.get("df_springate_complementar"))
    springate_class = str(springate.get("classificacao") or "NÃO CALCULÁVEL")
    springate_score = _number(springate.get("springate_S"))
    readings.append(
        "Springate: "
        + (f"{springate_score:.3f} — " if springate_score is not None else "")
        + springate_class.lower().replace("_", " ")
        + "."
    )
    if springate_class == "SINAL DE DISTRESS":
        attention.append("Springate com sinal de distress no exercício mais recente.")

    fleuriet = _last_record(output.get("df_fleuriet_complementar"))
    fleuriet_diagnostic = str(
        fleuriet.get("diagnostico") or "diagnóstico não calculável"
    )
    readings.append("Fleuriet simplificado: " + fleuriet_diagnostic + ".")
    if any(
        marker in fleuriet_diagnostic.lower()
        for marker in (
            "dependência de financiamento de curto prazo",
            "fontes permanentes insuficientes",
            "estrutura atípica",
        )
    ):
        attention.append("Fleuriet indica fragilidade na estrutura de capital de giro.")

    return {
        "serasa": serasa,
        "springate": springate,
        "fleuriet": fleuriet,
        "leituras": readings,
        "sinais_atencao": list(dict.fromkeys(attention)),
        "natureza": (
            "Evidências complementares: não são somadas ao FinScore e não alteram, isoladamente, "
            "a categoria de decisão."
        ),
    }


def decide_pudim(
    output: Dict[str, Any],
    meta: Dict[str, Any],
    config: PolicyConfig | None = None,
) -> Dict[str, Any]:
    """Decisão baseada no FinScore; Serasa, Springate e Fleuriet são suplementares."""

    del meta  # A decisão não depende de parâmetros comerciais não disponíveis no modelo.
    cfg = config or PolicyConfig()
    status = output.get("status_qualidade") or {}
    observed = output.get("finscore_observado") or {}
    score = _number(observed.get("finscore_prudencial"))
    reliability = _number(status.get("indice_confiabilidade"))
    score_band = _score_band(score, cfg)
    blocking_details = _all_blocking_details(output)
    supplementary = _supplementary_evidence(output)

    reasons: list[str] = []
    conditions: list[str] = []
    blocking: list[str] = []

    if score is None:
        blocking.append("FinScore prudencial indisponível.")
    else:
        reasons.append(
            f"FinScore prudencial de {_fmt_score(score)} pontos, na faixa {score_band.lower()}."
        )

    classification = str(status.get("classificacao_uso") or "BLOQUEADO")
    if not status.get("apto_calculo") or classification == "BLOQUEADO":
        blocking.append("Os dados contábeis não passaram pelos controles mínimos de cálculo.")
    if not status.get("apto_decisao") or observed.get("utilizavel_decisao") != "SIM":
        blocking.append(
            "O resultado não está apto para decisão até sanar os alertas bloqueadores."
        )
    if reliability is None:
        blocking.append("Índice de qualidade dos dados indisponível.")
    elif reliability < cfg.confiabilidade_minima_modelo:
        blocking.append(
            "Qualidade dos dados inferior ao limiar metodológico de "
            + f"{cfg.confiabilidade_minima_modelo:.0%}".replace(".", ",")
            + "."
        )
    else:
        reasons.append(
            "Qualidade dos dados de " + f"{reliability:.2%}".replace(".", ",") + "."
        )

    blockers = int(_number(status.get("alertas_bloqueadores_decisao")) or 0)
    if blockers:
        noun = "alerta" if blockers == 1 else "alertas"
        reasons.append(f"Há {blockers} {noun} que bloqueiam a decisão.")
    if blocking_details:
        conditions.extend(item["providencia"] for item in blocking_details)

    caps = output.get("df_caps_prudenciais")
    cap_reasons: list[str] = []
    if isinstance(caps, pd.DataFrame) and not caps.empty:
        cap_reasons = [str(value) for value in caps["justificativa"].dropna().tolist()]
        reasons.extend("Regra prudencial acionada: " + value for value in cap_reasons)

    severe = _severe_scenario_score(output)
    if severe is not None and score is not None:
        reasons.append(
            f"No cenário severo, o FinScore chega a {_fmt_score(severe)} "
            f"({_fmt_score(severe - score)} pontos frente ao observado)."
        )

    if blocking:
        decision = "dados_inconsistentes"
    elif score is not None and score < cfg.limite_nao_aprovar:
        decision = "nao_aprovar"
        reasons.append(
            f"O FinScore está abaixo do piso decisório de {cfg.limite_nao_aprovar:.0f} pontos."
        )
        conditions.append(
            "Realizar nova análise após mudança material da situação econômico-financeira e "
            "apresentação de demonstrações atualizadas."
        )
    else:
        decision = "aprovar"
        reasons.append(
            f"O FinScore atende ao piso decisório de {cfg.limite_nao_aprovar:.0f} pontos."
        )

    guarantee_reasons: list[str] = []
    if decision == "aprovar" and score is not None:
        if score < cfg.limite_referencia_garantia:
            guarantee_reasons.append(
                "FinScore entre 250 e 499,99 pontos."
            )
        if cap_reasons:
            guarantee_reasons.append("Existência de cap prudencial acionado.")
        if severe is not None and severe < cfg.limite_nao_aprovar:
            guarantee_reasons.append(
                "FinScore abaixo de 250 pontos no cenário severo."
            )
        guarantee_reasons.extend(supplementary["sinais_atencao"])

    guarantee_reasons = list(dict.fromkeys(guarantee_reasons))
    guarantee_recommended = bool(guarantee_reasons)
    guarantee: Dict[str, Any] = {
        "aplicavel": decision == "aprovar",
        "recomendada": guarantee_recommended,
        "cobertura_minima": None,
        "motivos": guarantee_reasons,
        "justificativa": None,
    }
    if decision == "aprovar" and guarantee_recommended:
        guarantee["justificativa"] = (
            "Recomenda-se garantia como mitigador dos sinais identificados: "
            + " ".join(guarantee_reasons)
            + " A modalidade, o valor realizável e a cobertura devem ser definidos após a "
            "avaliação do colateral; o sistema não presume percentual de cobertura."
        )
        conditions.append(
            "Avaliar modalidade, valor realizável, cobertura e exequibilidade jurídica da garantia."
        )
    elif decision == "aprovar":
        guarantee["justificativa"] = (
            "Os resultados disponíveis não acionam recomendação de garantia pelos critérios desta análise."
        )

    attention_text = " ".join(supplementary["sinais_atencao"]).lower()
    if decision == "aprovar" and "springate" in attention_text:
        conditions.append(
            "Definir covenant de acompanhamento do Springate, do EBIT e do capital circulante líquido."
        )
    if decision == "aprovar" and "fleuriet" in attention_text:
        conditions.append(
            "Definir covenant de acompanhamento da NCG, do CDG e do saldo de tesouraria."
        )
    if decision == "aprovar" and "serasa" in attention_text:
        conditions.append(
            "Atualizar a consulta ao Serasa e documentar as divergências antes da contratação."
        )
    cap_text = " ".join(cap_reasons).lower()
    if decision == "aprovar" and "capitalização" in cap_text:
        conditions.append(
            "Definir covenant de acompanhamento da capitalização e do patrimônio líquido."
        )
    if decision == "aprovar" and (
        "passivo exigível" in cap_text or "endividamento" in cap_text
    ):
        conditions.append(
            "Definir covenant de acompanhamento do endividamento exigível e de sua composição."
        )
    if decision == "aprovar" and (
        "cobertura de juros" in cap_text or "ebit" in cap_text
    ):
        conditions.append(
            "Definir covenant de acompanhamento do EBIT e da cobertura de juros."
        )
    if decision == "aprovar" and severe is not None and severe < cfg.limite_nao_aprovar:
        conditions.append(
            "Recalcular os cenários de estresse nas revisões da exposição e registrar deteriorações "
            "materiais para reavaliação."
        )

    return {
        "decisao": decision,
        "rotulo": DECISION_LABELS[decision],
        "segmento_politica": score_band,
        "finscore_prudencial": score,
        "confiabilidade": reliability,
        "fundamentacao": list(dict.fromkeys(reasons)),
        "bloqueios": list(dict.fromkeys(blocking)),
        "bloqueios_detalhados": blocking_details,
        "condicoes": list(dict.fromkeys(conditions)),
        "garantia": guarantee,
        "evidencias_complementares": supplementary,
        "parametros_politica": asdict(cfg),
        "avisos_metodologicos": [
            "A decisão utiliza o FinScore prudencial e seus controles de qualidade.",
            "Serasa, Springate e Fleuriet são evidências complementares e não são somados ao FinScore.",
            "Garantias e covenants são recomendações de mitigação; não criam uma quarta decisão.",
        ],
    }
