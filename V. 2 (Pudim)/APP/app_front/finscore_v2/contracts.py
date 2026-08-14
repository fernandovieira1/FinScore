"""Contrato público de saída do motor FinScore Pudim.

O contrato usa ``TypedDict`` para preservar a ergonomia de dicionário exigida
pelo Streamlit e um validador de runtime para detectar regressões de integração.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypedDict

import pandas as pd


CONTRACT_VERSION = "1.0"

ClassificationUse = Literal["BLOQUEADO", "CALCULADO_COM_ALERTAS", "CALCULADO"]
DecisionFlag = Literal["SIM", "NAO"]


class ModelMetadata(TypedDict):
    nome: Literal["Pudim"]
    versao: str
    hash_codigo: str
    processado_em: datetime
    semente: int
    numero_simulacoes: int


class QualityStatus(TypedDict, total=False):
    apto_score: bool
    apto_calculo: bool
    apto_decisao: bool
    score_provisorio: bool
    status: str
    ocorrencias_criticas: int
    ocorrencias_aviso: int
    correcoes_aplicadas: int
    correcoes_pendentes_confirmacao: int
    alertas_vies_alto_critico: int
    alertas_bloqueadores_decisao: int
    indice_confiabilidade: float
    classificacao_confiabilidade: str
    classificacao_uso: ClassificationUse


class Reliability(TypedDict):
    indice_confiabilidade: float
    classificacao_confiabilidade: str


class ObservedFinScore(TypedDict, total=False):
    exercicios_prejuizo_liquido: int
    multiplicador_prejuizo_recorrente: float
    cobertura_EO_estrutural: float
    nucleo_EO_estrutural_antes_prejuizo: float
    multiplicador_EO_estrutural: float
    nucleo_EO_estrutural: float
    cobertura_FP_estrutural: float
    nucleo_FP_estrutural_antes_prejuizo: float
    multiplicador_FP_estrutural: float
    nucleo_FP_estrutural: float
    finscore_estrutural: float
    gargalo_estrutural: float
    finscore_estrutural_pos_gargalo: float
    cobertura_EO_adaptativo: float
    nucleo_EO_adaptativo_antes_prejuizo: float
    multiplicador_EO_adaptativo: float
    nucleo_EO_adaptativo: float
    cobertura_FP_adaptativo: float
    nucleo_FP_adaptativo_antes_prejuizo: float
    multiplicador_FP_adaptativo: float
    nucleo_FP_adaptativo: float
    finscore_adaptativo: float
    gargalo_adaptativo: float
    finscore_adaptativo_pos_gargalo: float
    finscore_prudencial_pre_cap: float
    finscore_prudencial: float
    divergencia_modelos: float
    cap_prudencial_aplicavel: float
    indice_confiabilidade: float
    classificacao_confiabilidade: str
    classificacao_uso: ClassificationUse
    natureza_resultado: str
    utilizavel_decisao: DecisionFlag
    faixa_incerteza_inferior: float
    faixa_incerteza_superior: float


class FinScoreOutput(TypedDict):
    contrato_versao: str
    modelo: ModelMetadata
    status_qualidade: QualityStatus
    confiabilidade: Reliability
    finscore_observado: ObservedFinScore
    pca_observado: dict[str, Any]
    resumo_redundancia_fp: dict[str, Any]
    diagnosticos_simulacao: dict[str, Any]
    diagnosticos_simulacao_correlacionada: dict[str, Any]
    hash_dados_reportados: str
    hash_dados_utilizados: str
    df_confiabilidade_componentes: pd.DataFrame
    df_contas_reportadas: pd.DataFrame
    df_contas_analise: pd.DataFrame
    df_relatorio_importacao: pd.DataFrame
    df_qualidade: pd.DataFrame
    df_correcoes_auditoria: pd.DataFrame
    df_rastreabilidade_contas: pd.DataFrame
    df_alertas_vies: pd.DataFrame
    df_contas_derivadas: pd.DataFrame
    df_indices_observados: pd.DataFrame
    df_notas_observadas: pd.DataFrame
    df_motivos_nan: pd.DataFrame
    df_score_temporal: pd.DataFrame
    df_contribuicoes_score: pd.DataFrame
    df_caps_prudenciais: pd.DataFrame
    df_intervalos_incerteza: pd.DataFrame
    df_sensibilidade_redundancia_fp: pd.DataFrame
    df_diagnostico_pca: pd.DataFrame
    df_pesos_pca: pd.DataFrame
    df_cargas_pca: pd.DataFrame
    df_cenarios_deterministicos: pd.DataFrame
    df_simulacoes: pd.DataFrame
    df_simulacoes_independentes: pd.DataFrame
    df_simulacoes_correlacionadas: pd.DataFrame
    df_resumo_simulacoes: pd.DataFrame
    df_sensibilidade: pd.DataFrame
    df_amplitudes: pd.DataFrame
    df_comparacao_monte_carlo: pd.DataFrame
    df_comparacao_aceitos_rejeitados: pd.DataFrame
    df_serasa: pd.DataFrame


DATAFRAME_KEYS = (
    "df_confiabilidade_componentes",
    "df_contas_reportadas",
    "df_contas_analise",
    "df_relatorio_importacao",
    "df_qualidade",
    "df_correcoes_auditoria",
    "df_rastreabilidade_contas",
    "df_alertas_vies",
    "df_contas_derivadas",
    "df_indices_observados",
    "df_notas_observadas",
    "df_motivos_nan",
    "df_score_temporal",
    "df_contribuicoes_score",
    "df_caps_prudenciais",
    "df_intervalos_incerteza",
    "df_sensibilidade_redundancia_fp",
    "df_diagnostico_pca",
    "df_pesos_pca",
    "df_cargas_pca",
    "df_cenarios_deterministicos",
    "df_simulacoes",
    "df_simulacoes_independentes",
    "df_simulacoes_correlacionadas",
    "df_resumo_simulacoes",
    "df_sensibilidade",
    "df_amplitudes",
    "df_comparacao_monte_carlo",
    "df_comparacao_aceitos_rejeitados",
    "df_serasa",
)

DICT_KEYS = (
    "modelo",
    "status_qualidade",
    "confiabilidade",
    "finscore_observado",
    "pca_observado",
    "resumo_redundancia_fp",
    "diagnosticos_simulacao",
    "diagnosticos_simulacao_correlacionada",
)

REQUIRED_STATUS_KEYS = (
    "apto_calculo",
    "apto_decisao",
    "score_provisorio",
    "classificacao_uso",
    "indice_confiabilidade",
)

REQUIRED_OBSERVED_KEYS = (
    "nucleo_EO_estrutural",
    "nucleo_FP_estrutural",
    "finscore_estrutural",
    "finscore_adaptativo",
    "finscore_prudencial_pre_cap",
    "finscore_prudencial",
    "cap_prudencial_aplicavel",
    "classificacao_uso",
    "utilizavel_decisao",
)


class ContractError(ValueError):
    """Indica que a saída do motor não respeita o contrato público."""


def validar_contrato(output: FinScoreOutput | dict[str, Any]) -> FinScoreOutput:
    """Valida forma, tipos básicos e invariantes condicionais da saída."""
    errors: list[str] = []
    required_top_level = {
        "contrato_versao",
        "hash_dados_reportados",
        "hash_dados_utilizados",
        *DICT_KEYS,
        *DATAFRAME_KEYS,
    }
    missing = sorted(required_top_level - output.keys())
    if missing:
        errors.append(f"chaves ausentes: {missing}")

    if output.get("contrato_versao") != CONTRACT_VERSION:
        errors.append(
            "contrato_versao incompatível: "
            f"esperado {CONTRACT_VERSION!r}, recebido {output.get('contrato_versao')!r}"
        )

    for key in DICT_KEYS:
        if key in output and not isinstance(output[key], dict):
            errors.append(f"{key} deve ser dict")
    for key in DATAFRAME_KEYS:
        if key in output and not isinstance(output[key], pd.DataFrame):
            errors.append(f"{key} deve ser pandas.DataFrame")

    model = output.get("modelo", {})
    if isinstance(model, dict):
        for key in (
            "nome",
            "versao",
            "hash_codigo",
            "processado_em",
            "semente",
            "numero_simulacoes",
        ):
            if key not in model:
                errors.append(f"modelo.{key} ausente")
        if model.get("nome") != "Pudim":
            errors.append("modelo.nome deve ser 'Pudim'")
        if "processado_em" in model and not isinstance(model["processado_em"], datetime):
            errors.append("modelo.processado_em deve ser datetime")

    status = output.get("status_qualidade", {})
    if isinstance(status, dict):
        for key in REQUIRED_STATUS_KEYS:
            if key not in status:
                errors.append(f"status_qualidade.{key} ausente")
        classification = status.get("classificacao_uso")
        if classification not in {"BLOQUEADO", "CALCULADO_COM_ALERTAS", "CALCULADO"}:
            errors.append(f"classificacao_uso inválida: {classification!r}")
        if status.get("apto_decisao") and not status.get("apto_calculo"):
            errors.append("apto_decisao não pode ser verdadeiro quando apto_calculo é falso")

    reliability = output.get("confiabilidade", {})
    if isinstance(reliability, dict):
        for key in ("indice_confiabilidade", "classificacao_confiabilidade"):
            if key not in reliability:
                errors.append(f"confiabilidade.{key} ausente")
        value = reliability.get("indice_confiabilidade")
        if isinstance(value, (int, float)) and not 0.0 <= float(value) <= 1.0:
            errors.append("indice_confiabilidade deve estar entre 0 e 1")

    observed = output.get("finscore_observado", {})
    model_ready = bool(status.get("apto_calculo")) if isinstance(status, dict) else False
    if isinstance(observed, dict):
        if model_ready:
            for key in REQUIRED_OBSERVED_KEYS:
                if key not in observed:
                    errors.append(f"finscore_observado.{key} ausente")
        elif observed:
            errors.append("finscore_observado deve ser vazio quando o cálculo está bloqueado")

    reported = output.get("df_contas_reportadas")
    analysis = output.get("df_contas_analise")
    if isinstance(reported, pd.DataFrame) and len(reported) != 3:
        errors.append("df_contas_reportadas deve conter exatamente 3 exercícios")
    if isinstance(analysis, pd.DataFrame) and len(analysis) != 3:
        errors.append("df_contas_analise deve conter exatamente 3 exercícios")

    if model_ready:
        for key in ("df_indices_observados", "df_notas_observadas", "df_score_temporal"):
            table = output.get(key)
            if isinstance(table, pd.DataFrame) and table.empty:
                errors.append(f"{key} não pode ser vazio quando o cálculo foi executado")

    simulations = int(model.get("numero_simulacoes", 0)) if isinstance(model, dict) else 0
    if model_ready and simulations > 0:
        for key in ("df_simulacoes_independentes", "df_simulacoes_correlacionadas"):
            table = output.get(key)
            if isinstance(table, pd.DataFrame) and len(table) != simulations:
                errors.append(f"{key} deve conter {simulations} simulações aceitas")

    if errors:
        raise ContractError("Saída FinScore inválida: " + "; ".join(errors))
    return output  # type: ignore[return-value]
