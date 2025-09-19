# app_front/services/finscore_service.py
from typing import Dict, List, Optional, Tuple

import pandas as pd

from utils_finscore import executar_finscore


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
    if df is None or not anos_rotulos:
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


def run_finscore(df, meta: Dict):
    """
    Recebe o DataFrame contábil e o dicionário meta (empresa, cnpj, anos, serasa)
    e retorna o dicionário 'resultado' pronto para ir ao session_state['out'].
    """
    nome = meta.get("empresa", "").strip()
    ano_i = int(meta.get("ano_inicial"))
    ano_f = int(meta.get("ano_final"))
    serasa = int(meta.get("serasa", 0))

    df_ajustado, anos_rotulos = ajustar_coluna_ano(df, ano_i, ano_f)
    resultado = executar_finscore(df_ajustado, nome, ano_i, ano_f, serasa)

    anos_para_usar: Optional[List[int]] = anos_rotulos
    if not anos_para_usar:
        meta_rotulos = meta.get("anos_rotulos")
        if isinstance(meta_rotulos, (list, tuple)):
            try:
                anos_para_usar = [int(a) for a in meta_rotulos]
            except Exception:
                anos_para_usar = list(meta_rotulos)

    if anos_para_usar:
        resultado["df_indices"] = _inject_ano_column(resultado.get("df_indices"), anos_para_usar)
        resultado["df_pca"] = _inject_ano_column(resultado.get("df_pca"), anos_para_usar)
        meta["anos_rotulos"] = anos_para_usar

    resultado["df_raw"] = df_ajustado
    return resultado
