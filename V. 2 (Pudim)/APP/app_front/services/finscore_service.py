# app_front/services/finscore_service.py
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    from finscore_v2 import FinScoreOutput, executar_finscore, validar_contrato
except ModuleNotFoundError:  # Importação pelo pacote ``app_front`` nos testes.
    from app_front.finscore_v2 import FinScoreOutput, executar_finscore, validar_contrato


DEFAULT_SIMULATIONS = 1000
DEFAULT_SEED = 20260723


def _coerce_int(value: object) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def ajustar_coluna_ano(
    df, ano_inicial: Optional[int], ano_final: Optional[int]
) -> Tuple[object, Optional[List[int]]]:
    if df is None:
        return df, None
    if "ano" not in df.columns:
        return df.copy(), None

    df_adjusted = df.copy()
    anos_series = pd.to_numeric(df_adjusted["ano"], errors="coerce")
    if anos_series.isna().all():
        return df_adjusted, None

    anos_int = anos_series.astype(int)
    anos_lista = anos_int.tolist()

    if anos_int.between(1900, 2100).all():
        df_adjusted["ano"] = anos_lista
        return df_adjusted, anos_lista

    ano_inicial_int = _coerce_int(ano_inicial)
    ano_final_int = _coerce_int(ano_final)
    valores_ordenados = sorted(set(anos_int))
    quantidade = len(valores_ordenados)

    if (
        ano_inicial_int is not None
        and valores_ordenados == list(range(1, quantidade + 1))
    ):
        mapping = {valor: ano_inicial_int + (valor - 1) for valor in valores_ordenados}
        anos_rotulos = [mapping[val] for val in anos_lista]
        df_adjusted["ano"] = anos_rotulos
        return df_adjusted, anos_rotulos

    if (
        ano_final_int is not None
        and valores_ordenados == list(range(1, quantidade + 1))
    ):
        mapping = {valor: ano_final_int - (quantidade - valor) for valor in valores_ordenados}
        anos_rotulos = [mapping[val] for val in anos_lista]
        df_adjusted["ano"] = anos_rotulos
        return df_adjusted, anos_rotulos

    if (
        ano_final_int is not None
        and valores_ordenados == list(range(0, quantidade))
    ):
        mapping = {valor: ano_final_int - valor for valor in valores_ordenados}
        anos_rotulos = [mapping[val] for val in anos_lista]
        df_adjusted["ano"] = anos_rotulos
        return df_adjusted, anos_rotulos

    if ano_inicial_int is not None and ano_final_int is not None:
        try:
            mapping = {valor: ano_inicial_int + idx for idx, valor in enumerate(valores_ordenados)}
            anos_rotulos = [mapping.get(val, ano_inicial_int) for val in anos_lista]
            df_adjusted["ano"] = anos_rotulos
            return df_adjusted, anos_rotulos
        except Exception:
            pass

    return df_adjusted, None


def _inject_ano_column(df, anos_rotulos: Optional[List[int]]):
    if df is None or not anos_rotulos or "ano" in getattr(df, "columns", []):
        return df
    if getattr(df, "empty", True):
        return df
    if len(anos_rotulos) < len(df):
        return df

    df_copy = df.copy()
    try:
        anos_values = [int(a) for a in anos_rotulos[: len(df_copy)]]
    except Exception:
        anos_values = list(anos_rotulos[: len(df_copy)])
    df_copy.insert(0, "ano", anos_values)
    return df_copy


def _coerce_bool(value: object, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "sim", "yes", "on"}:
        return True
    if normalized in {"0", "false", "nao", "não", "no", "off", ""}:
        return False
    raise ValueError(f"{field} deve ser um valor booleano.")


def _normalizar_correcoes_manuais(value: object) -> list[dict[str, Any]]:
    """Normaliza correções sem avaliar DataFrames como booleanos."""
    if value is None:
        return []
    if isinstance(value, pd.DataFrame):
        return [] if value.empty else value.to_dict(orient="records")
    if isinstance(value, (list, tuple)):
        if not all(isinstance(item, dict) for item in value):
            raise ValueError("Cada correção manual deve ser um registro/dicionário.")
        return [dict(item) for item in value]
    raise ValueError(
        "correcoes_manuais deve ser uma lista de registros ou uma tabela."
    )


def _simulation_config(
    executar_simulacoes: Optional[bool],
    numero_simulacoes: Optional[int],
    semente: Optional[int],
) -> tuple[bool, int, int]:
    run = (
        _coerce_bool(
            os.environ.get("FINSCORE_EXECUTAR_SIMULACOES", "1"),
            field="FINSCORE_EXECUTAR_SIMULACOES",
        )
        if executar_simulacoes is None
        else _coerce_bool(
            executar_simulacoes,
            field="executar_simulacoes",
        )
    )
    simulations = int(
        numero_simulacoes
        if numero_simulacoes is not None
        else os.environ.get("FINSCORE_SIMULACOES", DEFAULT_SIMULATIONS)
    )
    seed = int(
        semente
        if semente is not None
        else os.environ.get("FINSCORE_SEMENTE", DEFAULT_SEED)
    )
    if run and simulations < 100:
        raise ValueError("FINSCORE_SIMULACOES deve ser pelo menos 100.")
    return run, simulations, seed


def _classificar_serasa_legado(score: Optional[int]) -> str:
    """Alias visual temporário; o Serasa permanece externo ao FinScore."""
    if score is None:
        return "Não informado"
    if score > 700:
        return "Excelente"
    if score > 500:
        return "Bom"
    if score > 300:
        return "Baixo"
    return "Muito Baixo"


def _status_visual(classificacao_uso: str) -> str:
    return {
        "BLOQUEADO": "Bloqueado pelo gate de qualidade",
        "CALCULADO_COM_ALERTAS": "Calculado com alertas",
        "CALCULADO": "Calculado",
    }.get(classificacao_uso, classificacao_uso)


def _add_transitional_aliases(
    result: FinScoreOutput,
    meta: Dict[str, Any],
) -> dict[str, Any]:
    """Mantém somente aliases seguros até as views migrarem nos itens 5–8."""
    output: dict[str, Any] = result
    observed = result["finscore_observado"]
    status = result["status_qualidade"]
    reported = result["df_contas_reportadas"]
    years = reported["ano"].astype(int).tolist() if "ano" in reported else None

    output["empresa"] = str(meta.get("empresa") or "").strip()
    output["periodo"] = (
        f"{meta.get('ano_inicial')}–{meta.get('ano_final')}"
        if meta.get("ano_inicial") is not None and meta.get("ano_final") is not None
        else ""
    )
    output["df_raw"] = reported
    output["df_indices"] = _inject_ano_column(
        result["df_indices_observados"], years
    )
    output["finscore_ajustado"] = observed.get("finscore_prudencial")
    output["classificacao_finscore"] = _status_visual(
        str(status.get("classificacao_uso", ""))
    )
    serasa = _coerce_int(meta.get("serasa"))
    output["serasa"] = serasa
    output["classificacao_serasa"] = _classificar_serasa_legado(serasa)
    output["compatibilidade_legado"] = {
        "temporaria": True,
        "aliases": [
            "empresa",
            "periodo",
            "df_raw",
            "df_indices",
            "finscore_ajustado",
            "classificacao_finscore",
            "serasa",
            "classificacao_serasa",
        ],
        "nao_fornecidos": [
            "finscore_bruto",
            "df_pca",
            "top_indices_df",
            "loadings",
            "pca_explained_variance",
            "pca_explained_variance_cum",
        ],
    }
    return output


def run_finscore(
    df,
    meta: Dict,
    *,
    executar_simulacoes: Optional[bool] = None,
    numero_simulacoes: Optional[int] = None,
    semente: Optional[int] = None,
) -> dict[str, Any]:
    """
    Recebe o DataFrame contábil e o dicionário meta (empresa, cnpj, anos, serasa)
    e retorna o dicionário 'resultado' pronto para ir ao session_state['out'].
    """
    ano_i = _coerce_int(meta.get("ano_inicial"))
    ano_f = _coerce_int(meta.get("ano_final"))
    if ano_i is None or ano_f is None:
        raise ValueError("Ano inicial e ano final devem ser inteiros válidos.")

    serasa = _coerce_int(meta.get("serasa"))
    if serasa is not None and not 0 <= serasa <= 1000:
        raise ValueError("Serasa deve estar entre 0 e 1000.")
    run_simulations, simulations, seed = _simulation_config(
        executar_simulacoes,
        numero_simulacoes,
        semente,
    )

    df_ajustado, anos_rotulos = ajustar_coluna_ano(df, ano_i, ano_f)
    resultado = executar_finscore(
        df_ajustado,
        serasa_score=serasa,
        serasa_data=str(meta.get("serasa_data") or "") or None,
        serasa_restricao_grave=_coerce_bool(
            meta.get("serasa_restricao_grave", False),
            field="serasa_restricao_grave",
        ),
        correcoes_manuais=_normalizar_correcoes_manuais(
            meta.get("correcoes_manuais")
        ),
        executar_simulacoes=run_simulations,
        numero_simulacoes=simulations,
        semente=seed,
    )
    validar_contrato(resultado)

    anos_para_usar: Optional[List[int]] = anos_rotulos
    if not anos_para_usar:
        meta_rotulos = meta.get("anos_rotulos")
        if isinstance(meta_rotulos, (list, tuple)):
            try:
                anos_para_usar = [int(a) for a in meta_rotulos]
            except Exception:
                anos_para_usar = list(meta_rotulos)

    if anos_para_usar:
        meta["anos_rotulos"] = anos_para_usar

    return _add_transitional_aliases(resultado, meta)
