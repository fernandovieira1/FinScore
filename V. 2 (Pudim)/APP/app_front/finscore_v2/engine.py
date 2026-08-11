"""Orquestração sem efeitos colaterais do FinScore Pudim 2.0.13."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from . import core
from .contracts import CONTRACT_VERSION, FinScoreOutput, validar_contrato


def preparar_dados_contabeis(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica ao DataFrame em memória as mesmas regras de ``load_raw_data``."""
    if not isinstance(raw, pd.DataFrame):
        raise TypeError("Os dados contábeis devem ser fornecidos em um DataFrame.")

    required = ["ano", *core.PRIMARY]
    missing = [column for column in required if column not in raw.columns]
    if missing:
        raise ValueError(f"Colunas ausentes nos dados contábeis: {missing}")

    source = raw[required].dropna(how="all", subset=core.PRIMARY).copy()
    if len(source) != 3:
        raise ValueError(
            f"Os dados devem ter 3 exercícios preenchidos; encontrei {len(source)}."
        )

    year_numeric = pd.to_numeric(source["ano"], errors="coerce")
    invalid_year = year_numeric.isna() | (year_numeric <= 0) | (year_numeric % 1 != 0)
    if invalid_year.any():
        rows = (source.index[invalid_year] + 2).tolist()
        raise ValueError(
            f"Exercício/ano deve ser inteiro positivo. Linhas inválidas: {rows}"
        )
    source["ano"] = year_numeric.astype(int)
    if source["ano"].duplicated().any():
        years = source.loc[source["ano"].duplicated(keep=False), "ano"].tolist()
        raise ValueError(f"Há exercícios duplicados: {years}")
    source = source.sort_values("ano").reset_index(drop=True)

    report: list[dict[str, Any]] = []
    for column in core.PRIMARY:
        original = source[column].copy()
        converted = original.map(core.parse_accounting_value)
        blank = original.map(core._is_blank_accounting_value)
        invalid = converted.isna() & ~blank
        absent = converted.isna() & blank
        if invalid.any():
            report.append(
                {
                    "severidade": "CRITICA",
                    "tipo": "erro_conversao",
                    "conta": column,
                    "exercicios": ", ".join(source.loc[invalid, "ano"].astype(str)),
                    "detalhe": "Valor textual não pôde ser convertido; revisar a origem.",
                    "bloqueia_calculo": True,
                    "bloqueia_decisao": True,
                    "bloqueia_score": True,
                }
            )
        if absent.any():
            report.append(
                {
                    "severidade": "AVISO",
                    "tipo": "ausencia",
                    "conta": column,
                    "exercicios": ", ".join(source.loc[absent, "ano"].astype(str)),
                    "detalhe": "Informação ausente preservada como NaN; não equivale a zero.",
                    "bloqueia_calculo": False,
                    "bloqueia_decisao": False,
                    "bloqueia_score": False,
                }
            )
        source[column] = converted

    return source, pd.DataFrame(report, columns=core.QUALITY_COLUMNS)


def _atualizar_status_qualidade(
    status: dict[str, Any],
    confiabilidade: dict[str, Any],
    alertas: pd.DataFrame,
) -> tuple[dict[str, Any], float]:
    status = dict(status)
    bloqueadores = int(alertas["bloqueia_decisao"].sum()) if not alertas.empty else 0
    q_observado = float(confiabilidade["indice_confiabilidade"])
    status["apto_decisao"] = bool(
        status["apto_calculo"]
        and status["apto_decisao"]
        and bloqueadores == 0
        and q_observado >= 0.75
    )
    status["score_provisorio"] = bool(
        status["apto_calculo"] and not status["apto_decisao"]
    )
    status["indice_confiabilidade"] = q_observado
    status["classificacao_confiabilidade"] = confiabilidade[
        "classificacao_confiabilidade"
    ]
    status["alertas_bloqueadores_decisao"] = bloqueadores
    status["classificacao_uso"] = (
        "BLOQUEADO"
        if not status["apto_calculo"]
        else "CALCULADO_COM_ALERTAS"
        if not status["apto_decisao"]
        else "CALCULADO"
    )
    status["status"] = (
        "NAO APTA PARA SCORING"
        if not status["apto_calculo"]
        else "FINSCORE CALCULADO COM ALERTAS PRUDENCIAIS E DOCUMENTAIS"
        if not status["apto_decisao"]
        else "FINSCORE CALCULADO SEM ALERTAS MATERIAIS"
    )
    return status, q_observado


def _diagnosticos_pca(
    profiles: dict[str, core.PCAProfile],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    diagnostics_rows: list[dict[str, Any]] = []
    weight_rows: list[dict[str, Any]] = []
    loading_rows: list[dict[str, Any]] = []
    for nucleus, profile in profiles.items():
        diagnostics_rows.append({"nucleo": nucleus, **profile.diagnostics})
        fixed = core._normalized_fixed_weights(core.NUCLEI[nucleus])
        for indicator, weight in profile.weights.items():
            weight_rows.append(
                {
                    "nucleo": nucleus,
                    "indicador": indicator,
                    "peso_adaptativo": weight,
                    "peso_fixo": fixed[indicator],
                }
            )
        if not profile.loadings.empty:
            local = profile.loadings.reset_index().rename(columns={"index": "indicador"})
            local.insert(0, "nucleo", nucleus)
            loading_rows.extend(local.to_dict("records"))
    return (
        pd.DataFrame(diagnostics_rows),
        pd.DataFrame(weight_rows),
        pd.DataFrame(loading_rows),
    )


def executar_finscore(
    dados: pd.DataFrame,
    *,
    serasa_score: float | int | None = None,
    serasa_data: str | None = None,
    serasa_restricao_grave: bool = False,
    correcoes_manuais: list[dict[str, Any]] | None = None,
    executar_simulacoes: bool = True,
    numero_simulacoes: int = 1000,
    semente: int = 20260723,
) -> FinScoreOutput:
    """Executa integralmente a metodologia 2.0.13 sobre dados em memória."""
    if executar_simulacoes and numero_simulacoes < 100:
        raise ValueError("Use ao menos 100 simulações.")

    processed_at = datetime.now()
    core.DATA_HORA_PROCESSAMENTO = processed_at
    reported, import_report = preparar_dados_contabeis(dados)
    analysis, quality, corrections, status = core.validate_correct_and_prepare(
        reported,
        import_report,
        correcoes_manuais or [],
    )
    traceability = core.build_traceability(reported, analysis, corrections)
    alerts = core.detect_material_bias(reported, analysis, corrections)
    status["alertas_vies_alto_critico"] = (
        int(alerts["risco_vies"].isin(["ALTO", "CRITICO"]).sum())
        if not alerts.empty
        else 0
    )
    quality = core.synchronize_quality_taxonomy(quality, alerts)
    reliability_components, reliability = core.calculate_reliability(
        reported, quality, corrections, alerts
    )
    status, q_observed = _atualizar_status_qualidade(status, reliability, alerts)

    result: dict[str, Any] = {
        "contrato_versao": CONTRACT_VERSION,
        "modelo": {
            "nome": "Pudim",
            "versao": core.VERSAO_MODELO,
            "hash_codigo": core.HASH_CODIGO_MODELO,
            "processado_em": processed_at,
            "semente": int(semente),
            "numero_simulacoes": int(numero_simulacoes) if executar_simulacoes else 0,
        },
        "status_qualidade": status,
        "confiabilidade": reliability,
        "df_confiabilidade_componentes": reliability_components,
        "df_contas_reportadas": reported,
        "df_contas_analise": analysis,
        "df_relatorio_importacao": import_report,
        "df_qualidade": quality,
        "df_correcoes_auditoria": corrections,
        "df_rastreabilidade_contas": traceability,
        "df_alertas_vies": alerts,
        "hash_dados_reportados": core.dataframe_sha256(reported),
        "hash_dados_utilizados": core.dataframe_sha256(analysis),
    }

    model_ready = bool(status["apto_calculo"])
    # A função congelada ``explain_missing_indices`` consulta esta tabela por
    # nome global. Mantemos a compatibilidade aqui sem expor estado ao chamador.
    core.df_contas_analise = analysis
    profiles: dict[str, core.PCAProfile] = {}
    observed: dict[str, Any] = {}
    derived = pd.DataFrame()
    indicators = pd.DataFrame()
    notes = pd.DataFrame()
    missing_reasons = pd.DataFrame()
    temporal_scores = pd.DataFrame()
    contributions = pd.DataFrame()
    caps = pd.DataFrame()
    uncertainty = pd.DataFrame()
    redundancy = pd.DataFrame()
    redundancy_summary: dict[str, Any] = {}
    pca_diagnostics = pd.DataFrame()
    pca_weights = pd.DataFrame()
    pca_loadings = pd.DataFrame()

    if model_ready:
        derived = core.derive(analysis)
        indicators = core.indices(derived)
        notes = core.score_indices(indicators)
        missing_reasons = core.explain_missing_indices(indicators)
        observed, profiles, temporal_scores, contributions = core.calculate_scores(
            indicators, notes
        )
        applicable_cap, caps = core.evaluate_prudential_caps(indicators, analysis)
        observed["cap_prudencial_aplicavel"] = applicable_cap
        observed["finscore_prudencial"] = min(
            observed["finscore_prudencial_pre_cap"], applicable_cap
        )
        observed.update(reliability)
        observed["classificacao_uso"] = status["classificacao_uso"]
        observed["natureza_resultado"] = (
            "EXPLORATORIO_QUALIDADE_INSUFICIENTE"
            if q_observed < 0.60
            else "PROVISORIO_CORRECOES_OU_ALERTAS_PENDENTES"
            if not status["apto_decisao"]
            else "DECISORIO_NA_POLITICA_ATUAL"
        )
        observed["utilizavel_decisao"] = "SIM" if status["apto_decisao"] else "NAO"
        redundancy, redundancy_summary = core.analyze_fp_redundancy(
            temporal_scores, indicators, analysis
        )
        uncertainty = core.missing_debt_classification_interval(analysis, profiles)
        if not uncertainty.empty:
            observed["faixa_incerteza_inferior"] = float(
                uncertainty["finscore_prudencial"].min()
            )
            observed["faixa_incerteza_superior"] = float(
                uncertainty["finscore_prudencial"].max()
            )
        else:
            observed["faixa_incerteza_inferior"] = observed["finscore_prudencial"]
            observed["faixa_incerteza_superior"] = observed["finscore_prudencial"]
        pca_diagnostics, pca_weights, pca_loadings = _diagnosticos_pca(profiles)

    result.update(
        {
            "finscore_observado": observed,
            "pca_observado": profiles,
            "df_contas_derivadas": derived,
            "df_indices_observados": indicators,
            "df_notas_observadas": notes,
            "df_motivos_nan": missing_reasons,
            "df_score_temporal": temporal_scores,
            "df_contribuicoes_score": contributions,
            "df_caps_prudenciais": caps,
            "df_intervalos_incerteza": uncertainty,
            "df_sensibilidade_redundancia_fp": redundancy,
            "resumo_redundancia_fp": redundancy_summary,
            "df_diagnostico_pca": pca_diagnostics,
            "df_pesos_pca": pca_weights,
            "df_cargas_pca": pca_loadings,
        }
    )

    scenarios = pd.DataFrame()
    independent = pd.DataFrame()
    correlated = pd.DataFrame()
    simulation_summary = pd.DataFrame()
    sensitivity = pd.DataFrame()
    amplitudes = pd.DataFrame()
    monte_carlo_comparison = pd.DataFrame()
    accepted_rejected = pd.DataFrame()
    independent_diagnostics: dict[str, Any] = {}
    correlated_diagnostics: dict[str, Any] = {}

    if model_ready:
        scenarios = core.run_deterministic_scenarios(analysis, profiles)
        if executar_simulacoes:
            independent, independent_diagnostics = core.run_sensitivity(
                analysis, numero_simulacoes, semente, profiles, "independente"
            )
            correlated, correlated_diagnostics = core.run_sensitivity(
                analysis, numero_simulacoes, semente + 100_000, profiles, "correlacionado"
            )
            simulation_summary = pd.concat(
                [
                    core.descriptive(independent, observed).assign(abordagem="independente"),
                    core.descriptive(correlated, observed).assign(abordagem="correlacionado"),
                ],
                ignore_index=True,
            )
            sensitivity = pd.concat(
                [
                    core.sensitivity_ranking(independent).assign(abordagem="independente"),
                    core.sensitivity_ranking(correlated).assign(abordagem="correlacionado"),
                ],
                ignore_index=True,
            )
            amplitudes = independent_diagnostics["limites_choques"].copy()
            monte_carlo_comparison = core.compare_monte_carlo_approaches(
                independent,
                independent_diagnostics,
                correlated,
                correlated_diagnostics,
            )
            comparisons = []
            for approach, diagnostics in (
                ("independente", independent_diagnostics),
                ("correlacionado", correlated_diagnostics),
            ):
                table = diagnostics["comparacao_aceitos_rejeitados"].copy()
                table.insert(0, "abordagem", approach)
                comparisons.append(table)
            accepted_rejected = pd.concat(comparisons, ignore_index=True)

    serasa = core.assess_external_credit(
        observed.get("finscore_prudencial", np.nan),
        serasa_score,
        serasa_data,
        serasa_restricao_grave,
    )
    result.update(
        {
            "df_cenarios_deterministicos": scenarios,
            "df_simulacoes": independent,
            "df_simulacoes_independentes": independent,
            "df_simulacoes_correlacionadas": correlated,
            "df_resumo_simulacoes": simulation_summary,
            "df_sensibilidade": sensitivity,
            "df_amplitudes": amplitudes,
            "df_comparacao_monte_carlo": monte_carlo_comparison,
            "df_comparacao_aceitos_rejeitados": accepted_rejected,
            "diagnosticos_simulacao": independent_diagnostics,
            "diagnosticos_simulacao_correlacionada": correlated_diagnostics,
            "df_serasa": serasa,
        }
    )
    return validar_contrato(result)


def executar_autotestes() -> pd.DataFrame:
    """Executa a bateria metodológica herdada sem depender do Streamlit."""
    core.MODELO_APTO = False
    core.diagnosticos_simulacao = {}
    core.diagnosticos_simulacao_correlacionada = {}
    tests = core.run_self_tests()
    failures = tests.loc[tests["status"].ne("PASSOU")]
    if not failures.empty:
        description = "; ".join(
            f"{row.teste}: {row.detalhe or 'sem detalhe'}"
            for row in failures.itertuples(index=False)
        )
        raise AssertionError(f"Autoteste(s) com falha: {description}")
    return tests
