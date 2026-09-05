"""Adaptador do contrato do motor para o contrato estruturado do parecer."""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import math
import re
from typing import Any, Iterable

import numpy as np
import pandas as pd

try:  # Execução Streamlit, com app_front no sys.path.
    from components.parecer_data_schema import (
        AccountingData,
        AvailabilityStatus,
        BiasAlert,
        BlockingReason,
        CorrectionRecord,
        DataNature,
        DataPoint,
        DeterministicScenario,
        FinScoreData,
        FinScoreRecommendation,
        FleurietEvidence,
        FunctionalMetadata,
        Governance,
        GuaranteeRecommendation,
        Identification,
        MethodScore,
        MissingCalculation,
        MonteCarloComparison,
        Operation,
        OperationTerm,
        PARECER_DATA_SCHEMA_VERSION,
        ParecerData,
        Party,
        PcaDiagnostic,
        PcaWeight,
        PeriodDivergence,
        PeriodRange,
        Periods,
        Quality,
        QualityOccurrence,
        QualitySummary,
        RecommendationCode,
        ReliabilityComponent,
        RestrictedTechnicalMetadata,
        Scenarios,
        ScoreContribution,
        SensitivityRecord,
        SerasaEvidence,
        ShockAmplitude,
        SimulationDiagnostic,
        SimulationSummary,
        SpringateEvidence,
        SupplementaryEvidence,
        TemporalComponent,
        ThresholdFrequency,
        TraceabilityRecord,
        PrudentialCap,
    )
    from services.credit_policy import decide_pudim
except ModuleNotFoundError:  # Importação como pacote nos testes.
    from app_front.components.parecer_data_schema import (
        AccountingData,
        AvailabilityStatus,
        BiasAlert,
        BlockingReason,
        CorrectionRecord,
        DataNature,
        DataPoint,
        DeterministicScenario,
        FinScoreData,
        FinScoreRecommendation,
        FleurietEvidence,
        FunctionalMetadata,
        Governance,
        GuaranteeRecommendation,
        Identification,
        MethodScore,
        MissingCalculation,
        MonteCarloComparison,
        Operation,
        OperationTerm,
        PARECER_DATA_SCHEMA_VERSION,
        ParecerData,
        Party,
        PcaDiagnostic,
        PcaWeight,
        PeriodDivergence,
        PeriodRange,
        Periods,
        Quality,
        QualityOccurrence,
        QualitySummary,
        RecommendationCode,
        ReliabilityComponent,
        RestrictedTechnicalMetadata,
        Scenarios,
        ScoreContribution,
        SensitivityRecord,
        SerasaEvidence,
        ShockAmplitude,
        SimulationDiagnostic,
        SimulationSummary,
        SpringateEvidence,
        SupplementaryEvidence,
        TemporalComponent,
        ThresholdFrequency,
        TraceabilityRecord,
        PrudentialCap,
    )
    from app_front.services.credit_policy import decide_pudim


PARECER_POLICY_VERSION = "three-decisions-finscore-only-v2"

PERCENT_INDICATORS = {
    "crescimento_receita",
    "margem_bruta",
    "margem_ebit",
    "margem_liquida",
    "capitalizacao",
    "endividamento_exigivel",
    "ccl_ativo",
    "ncg_operacional_ativo",
    "divida_liquida_ativo",
    "composicao_endividamento",
}
DAY_INDICATORS = {
    "prazo_recebimento_dias",
    "prazo_estoques_dias",
    "prazo_fornecedores_dias",
    "ciclo_conversao_caixa",
}


def _missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return isinstance(result, (bool, np.bool_)) and bool(result)


def _scalar(value: Any) -> bool | int | float | str | None:
    if _missing(value):
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return pd.Timestamp(value).isoformat()
    return str(value).strip()


def _number(value: Any) -> float | None:
    cleaned = _scalar(value)
    if cleaned is None or isinstance(cleaned, bool):
        return None
    try:
        number = float(cleaned)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _ratio(value: Any) -> float | None:
    """Normaliza apenas resíduos numéricos de ponto flutuante nos limites 0 e 1."""

    number = _number(value)
    if number is None:
        return None
    if -1e-12 <= number < 0:
        return 0.0
    if 1 < number <= 1 + 1e-12:
        return 1.0
    return number


def _integer(value: Any) -> int | None:
    number = _number(value)
    return None if number is None else int(number)


def _boolean(value: Any, default: bool = False) -> bool:
    if _missing(value):
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "sim", "s", "true", "verdadeiro"}
    return bool(value)


def _text(value: Any, default: str = "") -> str:
    cleaned = _scalar(value)
    return default if cleaned is None else str(cleaned)


def _string_list(value: Any) -> list[str]:
    if _missing(value):
        return []
    if isinstance(value, (list, tuple, set, np.ndarray, pd.Series)):
        return [text for item in value if (text := _text(item))]
    return [item.strip() for item in re.split(r"[;,|]", str(value)) if item.strip()]


def _years_from_value(value: Any) -> list[int]:
    if isinstance(value, (list, tuple, set, np.ndarray, pd.Series)):
        candidates = value
    else:
        candidates = re.findall(r"\b(?:19|20|21)\d{2}\b", _text(value))
    years = sorted({year for item in candidates if (year := _integer(item)) is not None})
    return [year for year in years if 1900 <= year <= 2200]


def _records(frame: Any) -> list[dict[str, Any]]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []
    return frame.to_dict(orient="records")


def _actual_years(output: dict[str, Any], meta: dict[str, Any]) -> list[int]:
    for key in ("df_contas_analise", "df_contas_reportadas"):
        frame = output.get(key)
        if isinstance(frame, pd.DataFrame) and not frame.empty and "ano" in frame:
            years = _years_from_value(frame["ano"].tolist())
            if years:
                return years
    configured = meta.get("anos_rotulos")
    years = _years_from_value(configured)
    if years:
        return years
    start, end = _integer(meta.get("ano_inicial")), _integer(meta.get("ano_final"))
    if start is not None and end is not None and start <= end:
        return list(range(start, end + 1))
    raise ValueError("não foi possível identificar o período efetivamente analisado")


def _parse_period(value: Any, *, source: str) -> PeriodRange:
    start: int | None = None
    end: int | None = None
    if isinstance(value, dict):
        start = _integer(value.get("inicio"))
        end = _integer(value.get("fim"))
    elif isinstance(value, (list, tuple)) and len(value) >= 2:
        start, end = _integer(value[0]), _integer(value[1])
    elif not _missing(value):
        years = _years_from_value(value)
        if years:
            start, end = years[0], years[-1]
    if start is None and end is None:
        return PeriodRange(fonte=source, status=AvailabilityStatus.UNAVAILABLE)
    if start is None or end is None:
        raise ValueError("período cadastral deve conter início e fim")
    return PeriodRange(
        inicio=start,
        fim=end,
        exercicios=list(range(start, end + 1)),
        fonte=source,
        status=AvailabilityStatus.AVAILABLE,
    )


def _periods(output: dict[str, Any], meta: dict[str, Any]) -> Periods:
    years = _actual_years(output, meta)
    analyzed = PeriodRange(
        inicio=years[0],
        fim=years[-1],
        exercicios=years,
        fonte="df_contas_analise",
        status=AvailabilityStatus.AVAILABLE,
    )
    cadastral_value = meta.get("periodo_cadastral")
    if cadastral_value is None and (
        meta.get("periodo_cadastral_inicio") is not None
        or meta.get("periodo_cadastral_fim") is not None
    ):
        cadastral_value = {
            "inicio": meta.get("periodo_cadastral_inicio"),
            "fim": meta.get("periodo_cadastral_fim"),
        }
    cadastral = _parse_period(cadastral_value, source="cadastro")
    divergences: list[PeriodDivergence] = []
    if cadastral.status is AvailabilityStatus.AVAILABLE and (
        cadastral.inicio != analyzed.inicio or cadastral.fim != analyzed.fim
    ):
        divergences.append(
            PeriodDivergence(
                codigo="PERIODO_CADASTRAL_DIVERGENTE",
                descricao=(
                    f"O período cadastral de {cadastral.inicio} a {cadastral.fim} difere "
                    f"do período efetivamente analisado de {analyzed.inicio} a {analyzed.fim}."
                ),
                impacto=(
                    "A divergência deve ser confirmada documentalmente e não altera "
                    "silenciosamente os exercícios utilizados no cálculo."
                ),
            )
        )
    return Periods(cadastral=cadastral, analisado=analyzed, divergencias=divergences)


def _optional_nonnegative(value: Any, *, field: str) -> float | None:
    if _missing(value):
        return None
    number = _number(value)
    if number is None or number < 0:
        raise ValueError(f"{field} deve ser numérico e não negativo")
    return number


def _operation(meta: dict[str, Any]) -> Operation:
    raw_term = meta.get("prazo_operacao", meta.get("prazo_meses"))
    term: OperationTerm | None = None
    if isinstance(raw_term, dict):
        number = _number(raw_term.get("valor"))
        unit = _text(raw_term.get("unidade"), "meses")
        if number is not None:
            term = OperationTerm(valor=number, unidade=unit)
    elif not _missing(raw_term):
        number = _number(raw_term)
        if number is None or number <= 0:
            raise ValueError("prazo da operação deve ser numérico e positivo")
        term = OperationTerm(valor=number, unidade=_text(meta.get("prazo_unidade"), "meses"))
    return Operation(
        natureza=_scalar(meta.get("natureza_operacao")),
        finalidade=_scalar(meta.get("finalidade_operacao")),
        valor=_optional_nonnegative(meta.get("valor_operacao", meta.get("valor_solicitado")), field="valor da operação"),
        prazo=term,
        moeda=_text(meta.get("moeda"), "BRL"),
    )


def _identification(output: dict[str, Any], meta: dict[str, Any]) -> Identification:
    return Identification(
        tomador=Party(nome=meta.get("empresa"), cnpj=meta.get("cnpj")),
        concedente=Party(
            nome=meta.get("concedente_nome"),
            cnpj=meta.get("concedente_cnpj"),
        ),
        operacao=_operation(meta),
        periodos=_periods(output, meta),
    )


def _unit_for_indicator(name: str) -> str:
    if name in PERCENT_INDICATORS:
        return "proporcao"
    if name in DAY_INDICATORS:
        return "dias"
    return "multiplo"


def _wide_points(
    frame: Any,
    *,
    point_prefix: str,
    nature: DataNature,
    source: str,
    years: list[int],
    only_prefix: str | None = None,
    default_unit: str | None = None,
    indicator_units: bool = False,
    missing_status: AvailabilityStatus = AvailabilityStatus.UNAVAILABLE,
) -> list[DataPoint]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []
    result: list[DataPoint] = []
    for position, record in enumerate(frame.to_dict(orient="records")):
        year = _integer(record.get("ano"))
        if year is None and position < len(years):
            year = years[position]
        if year is None:
            raise ValueError(f"registro sem exercício em {source}")
        for field, raw_value in record.items():
            if field == "ano" or (only_prefix is not None and not str(field).startswith(only_prefix)):
                continue
            value = _scalar(raw_value)
            status = AvailabilityStatus.AVAILABLE if value is not None else missing_status
            unit = _unit_for_indicator(str(field)) if indicator_units else default_unit
            result.append(
                DataPoint(
                    ponto_id=f"{point_prefix}-{year}-{field}",
                    campo=str(field),
                    valor=value,
                    exercicio=year,
                    unidade=unit,
                    fonte=source,
                    natureza=nature,
                    status=status,
                )
            )
    return result


def _corrections(output: dict[str, Any]) -> list[CorrectionRecord]:
    result: list[CorrectionRecord] = []
    for index, record in enumerate(_records(output.get("df_correcoes_auditoria")), 1):
        raw_date = record.get("data_hora")
        parsed_date = None if _missing(raw_date) else pd.Timestamp(raw_date).to_pydatetime()
        result.append(
            CorrectionRecord(
                evento_id=_text(record.get("evento_id"), f"COR-{index:04d}"),
                data_hora=parsed_date,
                etapa=_scalar(record.get("etapa")),
                acao=_text(record.get("acao"), "correcao_registrada"),
                status_acao=_scalar(record.get("status_acao")),
                exercicio=_integer(record.get("ano")),
                conta=_scalar(record.get("conta")),
                valor_original=_number(record.get("valor_original")),
                valor_proposto=_number(record.get("valor_proposto")),
                valor_utilizado=_number(record.get("valor_utilizado")),
                delta_absoluto=_number(record.get("delta_absoluto")),
                delta_percentual=_number(record.get("delta_percentual")),
                materialidade_pct_ativo=_number(record.get("materialidade_pct_ativo")),
                regra_id=_scalar(record.get("regra_id")),
                regra_descricao=_scalar(record.get("regra_descricao")),
                evidencia=_scalar(record.get("evidencia")),
                confianca=_ratio(record.get("confianca")),
                potencial_vies=_scalar(record.get("potencial_vies")),
                indicadores_afetados=_string_list(record.get("indicadores_afetados")),
                requer_confirmacao=_boolean(record.get("requer_confirmacao")),
                confirmado=_boolean(record.get("confirmado")),
                bloqueia_calculo=_boolean(record.get("bloqueia_calculo")),
                bloqueia_decisao=_boolean(record.get("bloqueia_decisao")),
                fonte=_scalar(record.get("fonte")),
                responsavel=_scalar(record.get("responsavel")),
            )
        )
    return result


def _proposed_points(corrections: Iterable[CorrectionRecord]) -> list[DataPoint]:
    latest: dict[tuple[str, int | None], CorrectionRecord] = {}
    for correction in corrections:
        if correction.conta and correction.valor_proposto is not None:
            latest[(correction.conta, correction.exercicio)] = correction
    return [
        DataPoint(
            ponto_id=f"PROP-{year or 'SEM-ANO'}-{account}",
            campo=account,
            valor=correction.valor_proposto,
            exercicio=year,
            unidade="BRL",
            fonte=f"correcao:{correction.evento_id}",
            natureza=DataNature.PROPOSED,
            status=AvailabilityStatus.AVAILABLE,
        )
        for (account, year), correction in latest.items()
    ]


def _traceability(output: dict[str, Any], corrections: list[CorrectionRecord]) -> list[TraceabilityRecord]:
    proposed = {
        (item.conta, item.exercicio): item.valor_proposto
        for item in corrections
        if item.conta and item.valor_proposto is not None
    }
    result: list[TraceabilityRecord] = []
    for index, record in enumerate(_records(output.get("df_rastreabilidade_contas")), 1):
        year = _integer(record.get("ano"))
        account = _text(record.get("conta"))
        if year is None or not account:
            raise ValueError("rastreabilidade contém registro sem ano ou conta")
        result.append(
            TraceabilityRecord(
                registro_id=f"RAST-{index:04d}",
                exercicio=year,
                conta=account,
                valor_reportado=_scalar(record.get("valor_reportado")),
                valor_proposto=proposed.get((account, year)),
                valor_utilizado=_scalar(record.get("valor_utilizado")),
                alterado=_boolean(record.get("alterado")),
                origem_valor=_text(record.get("origem_valor"), "NAO_INFORMADA"),
                evento_id=_scalar(record.get("evento_id")),
            )
        )
    return result


def _missing_calculations(output: dict[str, Any]) -> list[MissingCalculation]:
    return [
        MissingCalculation(
            exercicio=_integer(record.get("ano")),
            indicador=_text(record.get("indicador"), "indicador_nao_identificado"),
            motivo=_text(record.get("motivo"), "dependência indisponível"),
            dependencias=_string_list(record.get("dependencias")),
        )
        for record in _records(output.get("df_motivos_nan"))
    ]


def _accounting_data(output: dict[str, Any], years: list[int]) -> AccountingData:
    corrections = _corrections(output)
    return AccountingData(
        reportados=_wide_points(
            output.get("df_contas_reportadas"),
            point_prefix="REP",
            nature=DataNature.REPORTED,
            source="df_contas_reportadas",
            years=years,
            default_unit="BRL",
        ),
        propostos=_proposed_points(corrections),
        utilizados=_wide_points(
            output.get("df_contas_analise"),
            point_prefix="USO",
            nature=DataNature.USED,
            source="df_contas_analise",
            years=years,
            default_unit="BRL",
        ),
        derivados=_wide_points(
            output.get("df_contas_derivadas"),
            point_prefix="DER",
            nature=DataNature.DERIVED,
            source="df_contas_derivadas",
            years=years,
            only_prefix="d_",
            default_unit="BRL",
        ),
        indices=_wide_points(
            output.get("df_indices_observados"),
            point_prefix="IND",
            nature=DataNature.CALCULATED,
            source="df_indices_observados",
            years=years,
            indicator_units=True,
            missing_status=AvailabilityStatus.NOT_CALCULATED,
        ),
        notas=_wide_points(
            output.get("df_notas_observadas"),
            point_prefix="NOTA",
            nature=DataNature.CALCULATED,
            source="df_notas_observadas",
            years=years,
            default_unit="pontos_0_95",
            missing_status=AvailabilityStatus.NOT_CALCULATED,
        ),
        nao_calculados=_missing_calculations(output),
        rastreabilidade=_traceability(output, corrections),
    )


def _quality_occurrences(output: dict[str, Any]) -> list[QualityOccurrence]:
    result: list[QualityOccurrence] = []
    for source, prefix in (("df_relatorio_importacao", "IMP"), ("df_qualidade", "QUA")):
        for index, record in enumerate(_records(output.get(source)), 1):
            result.append(
                QualityOccurrence(
                    ocorrencia_id=f"{prefix}-{index:04d}",
                    origem=source,
                    severidade=_text(record.get("severidade"), "INFORMATIVA"),
                    tipo=_text(record.get("tipo"), "ocorrencia"),
                    conta=_scalar(record.get("conta")),
                    exercicios=_years_from_value(record.get("exercicios")),
                    detalhe=_text(record.get("detalhe"), "Ocorrência sem detalhe."),
                    bloqueia_calculo=_boolean(record.get("bloqueia_calculo")),
                    bloqueia_decisao=_boolean(record.get("bloqueia_decisao")),
                    bloqueia_score=_boolean(record.get("bloqueia_score")),
                )
            )
    return result


def _bias_alerts(output: dict[str, Any]) -> list[BiasAlert]:
    return [
        BiasAlert(
            alerta_id=_text(record.get("alerta_id"), f"ALT-{index:04d}"),
            severidade=_text(record.get("severidade"), "INFORMATIVA"),
            categoria=_text(record.get("categoria"), "NAO_CLASSIFICADA"),
            exercicio=_integer(record.get("ano")),
            conta=_scalar(record.get("conta")),
            valor_referencia=_number(record.get("valor_referencia")),
            valor_observado=_number(record.get("valor_observado")),
            metrica=_scalar(record.get("metrica")),
            limiar=_number(record.get("limiar")),
            materialidade_pct_ativo=_number(record.get("materialidade_pct_ativo")),
            risco_vies=_scalar(record.get("risco_vies")),
            impacto_provavel=_scalar(record.get("impacto_provavel")),
            tratamento_modelo=_scalar(record.get("tratamento_modelo")),
            acao_recomendada=_scalar(record.get("acao_recomendada")),
            bloqueia_decisao=_boolean(record.get("bloqueia_decisao")),
        )
        for index, record in enumerate(_records(output.get("df_alertas_vies")), 1)
    ]


def _quality(output: dict[str, Any]) -> Quality:
    status = output.get("status_qualidade") if isinstance(output.get("status_qualidade"), dict) else {}
    components = [
        ReliabilityComponent(
            componente=_text(record.get("componente"), "nao_identificado"),
            nota=_ratio(record.get("nota_0_1")),
            peso=_ratio(record.get("peso")) or 0.0,
            contribuicao=_ratio(record.get("contribuicao")),
        )
        for record in _records(output.get("df_confiabilidade_componentes"))
    ]
    return Quality(
        resumo=QualitySummary(
            apto_score=_boolean(status.get("apto_score")),
            apto_calculo=_boolean(status.get("apto_calculo")),
            apto_decisao=_boolean(status.get("apto_decisao")),
            score_provisorio=_boolean(status.get("score_provisorio")),
            status=_text(status.get("status"), "NAO_INFORMADO"),
            classificacao_uso=_text(status.get("classificacao_uso"), "BLOQUEADO"),
            indice_confiabilidade=_ratio(status.get("indice_confiabilidade")),
            classificacao_confiabilidade=_scalar(status.get("classificacao_confiabilidade")),
            ocorrencias_criticas=_integer(status.get("ocorrencias_criticas")) or 0,
            ocorrencias_aviso=_integer(status.get("ocorrencias_aviso")) or 0,
            correcoes_aplicadas=_integer(status.get("correcoes_aplicadas")) or 0,
            correcoes_pendentes_confirmacao=_integer(status.get("correcoes_pendentes_confirmacao")) or 0,
            alertas_vies_alto_critico=_integer(status.get("alertas_vies_alto_critico")) or 0,
            alertas_bloqueadores_decisao=_integer(status.get("alertas_bloqueadores_decisao")) or 0,
        ),
        componentes_confiabilidade=components,
        ocorrencias=_quality_occurrences(output),
        alertas=_bias_alerts(output),
        correcoes=_corrections(output),
    )


def _method_score(observed: dict[str, Any], method: str) -> MethodScore:
    return MethodScore(
        nucleo_eo_antes_prejuizo=_number(observed.get(f"nucleo_EO_{method}_antes_prejuizo")),
        multiplicador_eo=_ratio(observed.get(f"multiplicador_EO_{method}")),
        nucleo_eo=_number(observed.get(f"nucleo_EO_{method}")),
        cobertura_eo=_ratio(observed.get(f"cobertura_EO_{method}")),
        nucleo_fp_antes_prejuizo=_number(observed.get(f"nucleo_FP_{method}_antes_prejuizo")),
        multiplicador_fp=_ratio(observed.get(f"multiplicador_FP_{method}")),
        nucleo_fp=_number(observed.get(f"nucleo_FP_{method}")),
        cobertura_fp=_ratio(observed.get(f"cobertura_FP_{method}")),
        geometrico=_number(observed.get(f"finscore_{method}")),
        gargalo=_number(observed.get(f"gargalo_{method}")),
        pos_gargalo=_number(observed.get(f"finscore_{method}_pos_gargalo")),
    )


def _temporal_components(output: dict[str, Any]) -> list[TemporalComponent]:
    return [
        TemporalComponent(
            indicador=_text(record.get("indicador"), "nao_identificado"),
            nivel_atual=_number(record.get("nivel_atual")),
            dinamica_temporal=_number(record.get("dinamica_temporal")),
            resiliencia=_number(record.get("resiliencia")),
            nota_temporal=_number(record.get("nota_temporal")),
            cobertura_temporal=_ratio(record.get("cobertura_temporal")),
        )
        for record in _records(output.get("df_score_temporal"))
    ]


def _score_contributions(output: dict[str, Any]) -> list[ScoreContribution]:
    return [
        ScoreContribution(
            metodo=_text(record.get("metodo"), "nao_identificado"),
            nucleo=_text(record.get("nucleo"), "nao_identificado"),
            indicador=_text(record.get("indicador"), "nao_identificado"),
            nota_temporal=_number(record.get("nota_temporal")),
            peso_no_nucleo=_ratio(record.get("peso_no_nucleo")),
            contribuicao_nucleo_pontos=_number(record.get("contribuicao_nucleo_pontos")),
            cobertura_temporal=_ratio(record.get("cobertura_temporal")),
        )
        for record in _records(output.get("df_contribuicoes_score"))
    ]


def _caps(output: dict[str, Any]) -> list[PrudentialCap]:
    return [
        PrudentialCap(
            regra_id=_text(record.get("regra"), f"CAP-{index:04d}"),
            valor_observado=_number(record.get("valor_observado")),
            limiar=_number(record.get("limiar")),
            teto=_number(record.get("cap")),
            justificativa=_text(record.get("justificativa"), "Cap prudencial acionado."),
        )
        for index, record in enumerate(_records(output.get("df_caps_prudenciais")), 1)
    ]


def _pca_diagnostics(output: dict[str, Any]) -> list[PcaDiagnostic]:
    return [
        PcaDiagnostic(
            nucleo=_text(record.get("nucleo"), "nao_identificado"),
            status=_text(record.get("status_pca"), "NAO_INFORMADO"),
            variaveis_ativas=_integer(record.get("variaveis_ativas")),
            componentes=_integer(record.get("componentes")),
            variancia_pc1=_ratio(record.get("variancia_pc1")),
            variancia_pc2=_ratio(record.get("variancia_pc2")),
            participacao_adaptativa=_ratio(record.get("participacao_adaptativa")),
            distancia_l1_media=_number(record.get("distancia_l1_media")),
            similaridade_cosseno_media=_ratio(record.get("similaridade_cosseno_media")),
            maior_peso_pca_puro=_ratio(record.get("maior_peso_pca_puro")),
            n_efetivo_pesos=_number(record.get("n_efetivo_pesos")),
            fonte=_scalar(record.get("fonte_pca")),
        )
        for record in _records(output.get("df_diagnostico_pca"))
    ]


def _pca_weights(output: dict[str, Any]) -> list[PcaWeight]:
    return [
        PcaWeight(
            nucleo=_text(record.get("nucleo"), "nao_identificado"),
            indicador=_text(record.get("indicador"), "nao_identificado"),
            peso_adaptativo=_ratio(record.get("peso_adaptativo")),
            peso_fixo=_ratio(record.get("peso_fixo")),
        )
        for record in _records(output.get("df_pesos_pca"))
    ]


def _finscore(output: dict[str, Any]) -> FinScoreData:
    observed = output.get("finscore_observado") if isinstance(output.get("finscore_observado"), dict) else {}
    return FinScoreData(
        prudencial=_number(observed.get("finscore_prudencial")),
        prudencial_pre_cap=_number(observed.get("finscore_prudencial_pre_cap")),
        estrutural=_method_score(observed, "estrutural"),
        adaptativo=_method_score(observed, "adaptativo"),
        divergencia_metodos=_number(observed.get("divergencia_modelos")),
        cap_aplicavel=_number(observed.get("cap_prudencial_aplicavel")),
        faixa_incerteza_inferior=_number(observed.get("faixa_incerteza_inferior")),
        faixa_incerteza_superior=_number(observed.get("faixa_incerteza_superior")),
        exercicios_prejuizo_liquido=_integer(observed.get("exercicios_prejuizo_liquido")) or 0,
        multiplicador_prejuizo_recorrente=_ratio(observed.get("multiplicador_prejuizo_recorrente")),
        natureza_resultado=_scalar(observed.get("natureza_resultado")),
        utilizavel_decisao=_text(observed.get("utilizavel_decisao")).upper() == "SIM",
        componentes_temporais=_temporal_components(output),
        contribuicoes=_score_contributions(output),
        caps=_caps(output),
        diagnosticos_pca=_pca_diagnostics(output),
        pesos_pca=_pca_weights(output),
    )


def _deterministic_scenarios(output: dict[str, Any]) -> list[DeterministicScenario]:
    return [
        DeterministicScenario(
            nome=_text(record.get("cenario"), f"CENARIO-{index:02d}"),
            descricao=_scalar(record.get("descricao")),
            status=_text(record.get("status"), "NAO_INFORMADO"),
            flags=_string_list(record.get("flags")),
            premissa_excesso_fontes=_scalar(record.get("premissa_excesso_fontes")),
            financiamento_adicional_ultimo_ano=_number(record.get("financiamento_adicional_ultimo_ano")),
            excesso_fontes_ultimo_ano=_number(record.get("excesso_fontes_ultimo_ano")),
            ativo_residual_ultimo_ano=_number(record.get("ativo_residual_ultimo_ano")),
            vinculo_juros_divida_ultimo_ano=_scalar(record.get("vinculo_juros_divida_ultimo_ano")),
            margem_liquida_ultimo_ano=_number(record.get("margem_liquida_ultimo_ano")),
            nucleo_eo=_number(record.get("nucleo_EO_estrutural")),
            nucleo_fp=_number(record.get("nucleo_FP_estrutural")),
            finscore_prudencial=_number(record.get("finscore_prudencial")),
            monotonicidade_global=(
                None if _missing(record.get("monotonicidade_global"))
                else _boolean(record.get("monotonicidade_global"))
            ),
            status_monotonicidade=_scalar(record.get("status_monotonicidade")),
        )
        for index, record in enumerate(_records(output.get("df_cenarios_deterministicos")), 1)
    ]


def _simulation_summaries(output: dict[str, Any]) -> list[SimulationSummary]:
    result: list[SimulationSummary] = []
    for record in _records(output.get("df_resumo_simulacoes")):
        frequencies: list[ThresholdFrequency] = []
        for field, value in record.items():
            match = re.fullmatch(r"freq_abaixo_(\d+(?:\.\d+)?)", str(field))
            if match:
                frequencies.append(
                    ThresholdFrequency(corte=float(match.group(1)), frequencia=_ratio(value))
                )
        result.append(
            SimulationSummary(
                abordagem=_text(record.get("abordagem"), "nao_informada"),
                metodo=_text(record.get("metodo"), "nao_informado"),
                numero_trajetorias=_integer(record.get("n")) or 0,
                observado=_number(record.get("observado")),
                media=_number(record.get("media")),
                mediana=_number(record.get("mediana")),
                moda_estimada=_number(record.get("moda_estimada")),
                desvio_padrao=_number(record.get("desvio_padrao")),
                minimo=_number(record.get("minimo")),
                p05=_number(record.get("p05")),
                p10=_number(record.get("p10")),
                p25=_number(record.get("p25")),
                p75=_number(record.get("p75")),
                p90=_number(record.get("p90")),
                p95=_number(record.get("p95")),
                maximo=_number(record.get("maximo")),
                frequencias=frequencies,
            )
        )
    return result


def _sensitivity(output: dict[str, Any]) -> list[SensitivityRecord]:
    return [
        SensitivityRecord(
            abordagem=_text(record.get("abordagem"), "nao_informada"),
            score=_text(record.get("score"), "nao_informado"),
            conta=_text(record.get("conta"), "nao_informada"),
            correlacao_spearman=_number(record.get("correlacao_spearman")),
            impacto_absoluto=_ratio(record.get("impacto_absoluto")),
        )
        for record in _records(output.get("df_sensibilidade"))
    ]


def _amplitudes(output: dict[str, Any]) -> list[ShockAmplitude]:
    return [
        ShockAmplitude(
            conta=_text(record.get("conta"), "nao_informada"),
            natureza_simulacao=_text(record.get("natureza_simulacao"), "nao_informada"),
            amplitude_declarada=_ratio(record.get("amplitude_declarada")),
            choque_maximo_observado=_number(record.get("choque_maximo_observado")),
            dentro_limite_declarado=(
                None if _missing(record.get("dentro_limite_declarado"))
                else _boolean(record.get("dentro_limite_declarado"))
            ),
        )
        for record in _records(output.get("df_amplitudes"))
    ]


def _simulation_diagnostic(raw: Any, fallback: str) -> SimulationDiagnostic | None:
    if not isinstance(raw, dict) or not raw:
        return None
    return SimulationDiagnostic(
        abordagem=_text(raw.get("abordagem"), fallback),
        tentativas=_integer(raw.get("tentativas")),
        rejeitados=_integer(raw.get("rejeitados")),
        taxa_rejeicao=_ratio(raw.get("taxa_rejeicao")),
        limite_taxa_rejeicao=_ratio(raw.get("limite_taxa_rejeicao")),
        status_rejeicao=_scalar(raw.get("status_rejeicao")),
        valida_para_interpretacao=(
            None if _missing(raw.get("valida_para_interpretacao"))
            else _boolean(raw.get("valida_para_interpretacao"))
        ),
        drivers_fora_limite=_integer(raw.get("drivers_fora_limite")),
    )


def _monte_carlo_comparison(output: dict[str, Any]) -> list[MonteCarloComparison]:
    fields = (
        "media_independente", "media_correlacionada", "delta_media",
        "mediana_independente", "mediana_correlacionada", "delta_mediana",
        "desvio_independente", "desvio_correlacionado", "p05_independente",
        "p05_correlacionado", "p95_independente", "p95_correlacionado",
        "rejeicao_independente", "rejeicao_correlacionada",
    )
    result = []
    for record in _records(output.get("df_comparacao_monte_carlo")):
        values = {field: _number(record.get(field)) for field in fields}
        result.append(
            MonteCarloComparison(
                metodo=_text(record.get("metodo"), "nao_informado"),
                **values,
            )
        )
    return result


def _scenarios(output: dict[str, Any]) -> Scenarios:
    diagnostics = [
        item for item in (
            _simulation_diagnostic(output.get("diagnosticos_simulacao"), "independente"),
            _simulation_diagnostic(
                output.get("diagnosticos_simulacao_correlacionada"), "correlacionado"
            ),
        ) if item is not None
    ]
    return Scenarios(
        deterministicos=_deterministic_scenarios(output),
        resumos_simulacao=_simulation_summaries(output),
        sensibilidade=_sensitivity(output),
        amplitudes=_amplitudes(output),
        diagnosticos=diagnostics,
        comparacao_monte_carlo=_monte_carlo_comparison(output),
    )


def _parse_consultation_date(value: Any) -> date | None:
    if _missing(value):
        return None
    text = _text(value)
    for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], pattern).date()
        except ValueError:
            continue
    return None


def _supplementary_evidence(output: dict[str, Any], processed_at: datetime) -> SupplementaryEvidence:
    serasa_records = _records(output.get("df_serasa"))
    serasa = serasa_records[-1] if serasa_records else {}
    consultation_date = _parse_consultation_date(serasa.get("data_consulta"))
    chronology = None if consultation_date is None else consultation_date <= processed_at.date()
    temporal_alert = None
    if chronology is False:
        temporal_alert = (
            "A data da consulta ao Serasa é posterior à data de processamento e requer validação."
        )
    springate = [
        SpringateEvidence(
            exercicio=_integer(record.get("ano")),
            componente_a_ccl_at=_number(record.get("A_CCL_AT")),
            componente_b_ebit_at=_number(record.get("B_EBIT_AT")),
            componente_c_ebt_pc=_number(record.get("C_EBT_PC")),
            componente_d_receita_at=_number(record.get("D_RECEITA_AT")),
            score=_number(record.get("springate_S")),
            classificacao=_text(record.get("classificacao"), "NÃO CALCULÁVEL"),
            observacao=_scalar(record.get("observacao")),
        )
        for record in _records(output.get("df_springate_complementar"))
        if _integer(record.get("ano")) is not None
    ]
    fleuriet = [
        FleurietEvidence(
            exercicio=_integer(record.get("ano")),
            ativo_circulante_operacional=_number(record.get("ACO_s")),
            passivo_circulante_operacional=_number(record.get("PCO_s")),
            necessidade_capital_giro=_number(record.get("NCG_s")),
            ativo_nao_circulante=_number(record.get("ANC")),
            capital_giro=_number(record.get("CDG")),
            saldo_tesouraria=_number(record.get("ST_s")),
            perfil_sinais=_scalar(record.get("perfil_sinais")),
            diagnostico=_text(record.get("diagnostico"), "NÃO CALCULÁVEL"),
        )
        for record in _records(output.get("df_fleuriet_complementar"))
        if _integer(record.get("ano")) is not None
    ]
    return SupplementaryEvidence(
        serasa=SerasaEvidence(
            score=_number(serasa.get("serasa_score")),
            data_consulta=_scalar(serasa.get("data_consulta")),
            status=_text(serasa.get("status"), "AUSENTE"),
            divergencia_pontos=_number(serasa.get("divergencia_pontos")),
            nivel_divergencia=_scalar(serasa.get("nivel_divergencia")),
            direcao=_scalar(serasa.get("direcao")),
            restricao_grave=_boolean(serasa.get("restricao_grave")),
            cronologia_valida=chronology,
            alerta_temporal=temporal_alert,
        ),
        springate=springate,
        fleuriet=fleuriet,
    )


def _blocking_reasons(policy: dict[str, Any]) -> list[BlockingReason]:
    details = policy.get("bloqueios_detalhados")
    details = details if isinstance(details, list) else []
    result = [
        BlockingReason(
            bloqueio_id=f"BLOQ-{index:03d}",
            titulo=_text(item.get("titulo"), "Pendência decisória"),
            motivo=_text(item.get("motivo"), "O resultado não está apto para decisão."),
            impacto=_text(item.get("impacto"), "Impede o uso decisório do resultado."),
            providencia=_text(item.get("providencia"), "Sanar a pendência e recalcular o FinScore."),
            origem="politica_credito:bloqueios_detalhados",
        )
        for index, item in enumerate(details, 1)
        if isinstance(item, dict)
    ]
    if not result:
        raw_blockers = policy.get("bloqueios")
        raw_blockers = raw_blockers if isinstance(raw_blockers, list) else []
        result = [
            BlockingReason(
                bloqueio_id=f"BLOQ-{index:03d}",
                titulo="Pendência decisória",
                motivo=_text(reason, "O resultado não está apto para decisão."),
                impacto="Não há informação confiável suficiente para emitir recomendação decisória.",
                providencia="Sanar a pendência indicada, reenviar os dados e recalcular o FinScore.",
                origem="politica_credito:bloqueios",
            )
            for index, reason in enumerate(raw_blockers, 1)
        ]
    return result


def build_finscore_recommendation(
    output: dict[str, Any], policy: dict[str, Any]
) -> FinScoreRecommendation:
    """Materializa a recomendação calculada, sem posições humanas.

    A recomendação retornada por esta função é a referência imutável do fluxo
    de governança. Manifestação do analista e decisão da alçada são registradas
    separadamente e nunca alteram este objeto.
    """

    quality = output.get("status_qualidade") if isinstance(output.get("status_qualidade"), dict) else {}
    guarantee = policy.get("garantia") if isinstance(policy.get("garantia"), dict) else {}
    code = RecommendationCode(_text(policy.get("decisao")))
    return FinScoreRecommendation(
        codigo=code,
        rotulo=_text(policy.get("rotulo")),
        regra_id="POL-REC-001",
        versao_politica=PARECER_POLICY_VERSION,
        apto_decisao=_boolean(quality.get("apto_decisao")),
        finscore_prudencial=_number(policy.get("finscore_prudencial")),
        faixa=_text(policy.get("segmento_politica"), "NÃO CALCULÁVEL"),
        confiabilidade=_ratio(policy.get("confiabilidade")),
        fundamentos=[_text(item) for item in policy.get("fundamentacao", []) if _text(item)],
        bloqueios=_blocking_reasons(policy),
        providencias=[_text(item) for item in policy.get("condicoes", []) if _text(item)],
        garantia=GuaranteeRecommendation(
            aplicavel=_boolean(guarantee.get("aplicavel")),
            recomendada=_boolean(guarantee.get("recomendada")),
            motivos=[_text(item) for item in guarantee.get("motivos", []) if _text(item)],
            justificativa=_scalar(guarantee.get("justificativa")),
            cobertura_minima=_number(guarantee.get("cobertura_minima")),
        ),
    )


def _governance(
    output: dict[str, Any],
    policy: dict[str, Any],
    governance: Governance | dict[str, Any] | None,
) -> Governance:
    recommendation = build_finscore_recommendation(output, policy)
    if governance is None:
        return Governance(recomendacao_finscore=recommendation)

    selected = Governance.model_validate(governance)
    if selected.recomendacao_finscore != recommendation:
        raise ValueError(
            "a governança informada tenta alterar a recomendação FinScore da análise"
        )
    return selected


def _processed_at(output: dict[str, Any]) -> datetime:
    model = output.get("modelo") if isinstance(output.get("modelo"), dict) else {}
    value = model.get("processado_em")
    if isinstance(value, datetime):
        return value
    if not _missing(value):
        return pd.Timestamp(value).to_pydatetime()
    raise ValueError("data de processamento ausente no contrato do motor")


def _analysis_id(
    output: dict[str, Any], meta: dict[str, Any], processed_at: datetime
) -> tuple[str, str]:
    informed = _text(meta.get("analise_id"))
    if informed:
        return informed, "informado"
    basis = {
        "cnpj": _text(meta.get("cnpj")),
        "processado_em": processed_at.isoformat(),
        "hash_reportado": _text(output.get("hash_dados_reportados")),
        "hash_utilizado": _text(output.get("hash_dados_utilizados")),
    }
    digest = hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12].upper()
    return f"FS-{processed_at.year}-{digest}", "derivado_da_execucao"


def build_parecer_data(
    output: dict[str, Any],
    meta: dict[str, Any],
    policy: dict[str, Any] | None = None,
    governance: Governance | dict[str, Any] | None = None,
) -> ParecerData:
    """Constrói e valida o contrato do parecer sem modificar as entradas.

    A função não calcula indicadores, não altera a recomendação e não produz
    texto narrativo. O identificador derivado é transitório até a etapa de
    persistência fornecer a sequência institucional definitiva.
    """

    if not isinstance(output, dict):
        raise TypeError("output deve ser um dicionário do contrato FinScore")
    if not isinstance(meta, dict):
        raise TypeError("meta deve ser um dicionário")

    selected_policy = decide_pudim(output, meta) if policy is None else policy
    if not isinstance(selected_policy, dict):
        raise TypeError("policy deve ser um dicionário")

    processed_at = _processed_at(output)
    analysis_id, id_origin = _analysis_id(output, meta, processed_at)
    identification = _identification(output, meta)
    years = identification.periodos.analisado.exercicios
    model = output.get("modelo") if isinstance(output.get("modelo"), dict) else {}
    model_version = _text(model.get("versao"))

    contract = ParecerData(
        schema_versao=PARECER_DATA_SCHEMA_VERSION,
        analise_id=analysis_id,
        identificacao=identification,
        governanca=_governance(output, selected_policy, governance),
        dados=_accounting_data(output, years),
        qualidade=_quality(output),
        finscore=_finscore(output),
        cenarios=_scenarios(output),
        evidencias_suplementares=_supplementary_evidence(output, processed_at),
        achados=[],
        metadados_funcionais=FunctionalMetadata(
            processado_em=processed_at,
            numero_simulacoes=_integer(model.get("numero_simulacoes")) or 0,
            semente_simulacao=_integer(model.get("semente")) or 0,
            versao_metodologia=model_version,
            versao_contrato_motor=_text(output.get("contrato_versao")),
            status_reproducao="PARAMETROS_E_HASHES_REGISTRADOS",
        ),
        metadados_tecnicos_restritos=RestrictedTechnicalMetadata(
            nome_interno_motor=_scalar(model.get("nome")),
            versao_codigo=model_version,
            hash_codigo=_text(model.get("hash_codigo")),
            semente=_integer(model.get("semente")) or 0,
            hash_dados_reportados=_text(output.get("hash_dados_reportados")),
            hash_dados_utilizados=_text(output.get("hash_dados_utilizados")),
            origem_analise_id=id_origin,
        ),
    )
    try:
        from services.evidence_book import attach_evidence_book
    except ModuleNotFoundError:
        from app_front.services.evidence_book import attach_evidence_book
    return attach_evidence_book(contract)


__all__ = [
    "PARECER_POLICY_VERSION",
    "build_finscore_recommendation",
    "build_parecer_data",
]
