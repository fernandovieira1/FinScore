# app_front/pages/tabelas.py
from __future__ import annotations
from typing import Any

import streamlit as st
import pandas as pd
import numpy as np

from .analise_contas import formatar_nome_conta


MILLION = 1_000_000


def _get_base_df() -> pd.DataFrame | None:
    ss = st.session_state
    base = None
    if ss.get("df") is not None:
        base = ss.df
    elif ss.get("out"):
        base = ss.out.get("df_raw")
        if base is None:
            return None
    if base is None:
        return None
    df = base.copy()
    if "ano" not in df.columns:
        df["ano"] = list(range(len(df), 0, -1))
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["ano"].notna()].copy()
    df["ano"] = df["ano"].astype(int)
    df = df.sort_values("ano", ascending=True).reset_index(drop=True)
    return df


def _ensure_required(df: pd.DataFrame | None, columns: list[str]) -> tuple[bool, set[str]]:
    if df is None:
        return False, set(columns)
    missing = {col for col in columns if col not in df.columns}
    return not missing, missing


def _optional_series(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce").fillna(default)


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return numerator.divide(denominator)


def _currency(series: pd.Series) -> pd.Series:
    return (series / MILLION).round(2)


def _percent(series: pd.Series) -> pd.Series:
    return series.round(2)


def _yoy(series: pd.Series) -> pd.Series:
    return (series.pct_change() * 100).round(2)


def _diff(series: pd.Series) -> pd.Series:
    return series.diff().round(2)


def _cagr(series: pd.Series) -> float:
    series = series.dropna()
    if len(series) <= 1:
        return np.nan
    start, end = series.iloc[0], series.iloc[-1]
    if start <= 0 or end <= 0:
        return np.nan
    periods = len(series) - 1
    try:
        return (end / start) ** (1 / periods) - 1
    except (ZeroDivisionError, ValueError):
        return np.nan


def _compute_ebit_e_ebitda(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    lucro = _optional_series(df, "r_Lucro_Liquido")
    juros = _optional_series(df, "r_Despesa_de_Juros")
    impostos = _optional_series(df, "r_Despesa_de_Impostos")
    amort = _optional_series(df, "r_Amortizacao")
    depr = _optional_series(df, "r_Depreciacao")
    ebit = lucro + juros + impostos
    ebitda = ebit + amort + depr
    return ebit, ebitda


def _compute_liquidez_metricas(df: pd.DataFrame) -> pd.DataFrame:
    ac = _optional_series(df, "p_Ativo_Circulante")
    pc = _optional_series(df, "p_Passivo_Circulante")
    estoques = _optional_series(df, "p_Estoques")
    total = _optional_series(df, "p_Ativo_Total")
    return pd.DataFrame(
        {
            "Ano": df["ano"].astype(int),
            "Liquidez Corrente": _safe_div(ac, pc),
            "Liquidez Seca": _safe_div(ac - estoques, pc),
            "CCL/Ativo": _safe_div(ac - pc, total),
        }
    )


def _compute_endividamento_metricas(df: pd.DataFrame) -> pd.DataFrame:
    ebit, ebitda = _compute_ebit_e_ebitda(df)
    divida_bruta = _optional_series(df, "p_Passivo_Total") - _optional_series(df, "p_Patrimonio_Liquido")
    divida_liquida = divida_bruta - _optional_series(df, "p_Caixa")
    total = _optional_series(df, "p_Ativo_Total")
    return pd.DataFrame(
        {
            "Ano": df["ano"].astype(int),
            "Divida/Ativo": _safe_div(divida_bruta, total),
            "Divida Liquida/EBITDA": _safe_div(divida_liquida, ebitda),
            "PL/Ativo": _safe_div(_optional_series(df, "p_Patrimonio_Liquido"), total),
        }
    )


def _compute_rentabilidade_metricas(df: pd.DataFrame) -> pd.DataFrame:
    _, ebitda = _compute_ebit_e_ebitda(df)
    receita = _optional_series(df, "r_Receita_Total")
    lucro = _optional_series(df, "r_Lucro_Liquido")
    return pd.DataFrame(
        {
            "Ano": df["ano"].astype(int),
            "ROE": _safe_div(lucro, _optional_series(df, "p_Patrimonio_Liquido")) * 100,
            "ROA": _safe_div(lucro, _optional_series(df, "p_Ativo_Total")) * 100,
            "Margem Liquida": _safe_div(lucro, receita) * 100,
            "Margem EBITDA": _safe_div(ebitda, receita) * 100,
        }
    )


def _compute_eficiencia_metricas(df: pd.DataFrame) -> pd.DataFrame:
    ebit, _ = _compute_ebit_e_ebitda(df)
    receita = _optional_series(df, "r_Receita_Total")
    custos = _optional_series(df, "r_Custos")
    contas_receber = _optional_series(df, "p_Contas_a_Receber")
    contas_pagar = _optional_series(df, "p_Contas_a_Pagar")
    ativo = _optional_series(df, "p_Ativo_Total")
    juros = _optional_series(df, "r_Despesa_de_Juros")
    pmr = _safe_div(contas_receber, receita) * 365
    pmp = _safe_div(contas_pagar, custos) * 365
    giro = _safe_div(receita, ativo)
    cobertura = _safe_div(ebit, juros)
    return pd.DataFrame(
        {
            "Ano": df["ano"].astype(int),
            "PMR (dias)": pmr,
            "PMP (dias)": pmp,
            "Giro do Ativo (x)": giro,
            "Cobertura de Juros (x)": cobertura,
        }
    )


def _finalize_table(table: pd.DataFrame | None) -> pd.DataFrame | None:
    if table is None:
        return None
    table = table.copy()
    if "Ano" in table.columns:
        table["Ano"] = table["Ano"].astype(str)
    return table



def _formata_ano(df):
    if df is None:
        return df
    df_display = df.copy()
    if "ano" not in df_display.columns:
        return df_display

    ordenacao = pd.to_numeric(df_display["ano"], errors="coerce")
    df_display = df_display.assign(_ano_ord=ordenacao)
    df_display = df_display.sort_values("_ano_ord", ascending=True, na_position="last")
    df_display = df_display.drop(columns="_ano_ord")
    df_display = df_display.reset_index(drop=True)

    def _fmt(valor, fallback):
        if valor is None:
            return fallback
        try:
            return str(int(float(valor)))
        except (TypeError, ValueError):
            return str(valor)

    df_display["Ano"] = [
        _fmt(valor, str(idx + 1)) for idx, valor in enumerate(df_display["ano"])
    ]
    df_display.drop(columns="ano", inplace=True)
    cols = ["Ano"] + [c for c in df_display.columns if c != "Ano"]
    df_display = df_display[cols]
    return df_display


def table_ativos() -> pd.DataFrame | None:
    df = _get_base_df()
    required = [
        "p_Ativo_Circulante",
        "p_Ativo_Total",
        "p_Caixa",
        "p_Estoques",
        "p_Contas_a_Receber",
    ]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    data = df[["ano", *required]].copy()
    table = pd.DataFrame({"Ano": data["ano"].astype(int)})
    mapping = [
        ("p_Ativo_Circulante", "Ativo Circulante"),
        ("p_Ativo_Total", "Ativo Total"),
        ("p_Caixa", "Caixa"),
        ("p_Estoques", "Estoques"),
        ("p_Contas_a_Receber", "Contas a Receber"),
    ]
    for col, label in mapping:
        table[f"{label} (R$ mi)"] = _currency(data[col])
        table[f"{label} YoY (%)"] = _yoy(data[col])
    return _finalize_table(table)


def table_passivos() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["p_Contas_a_Pagar", "p_Passivo_Circulante", "p_Passivo_Total"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    data = df[["ano", *required]].copy()
    table = pd.DataFrame({"Ano": data["ano"].astype(int)})
    mapping = [
        ("p_Contas_a_Pagar", "Contas a Pagar"),
        ("p_Passivo_Circulante", "Passivo Circulante"),
        ("p_Passivo_Total", "Passivo Total"),
    ]
    for col, label in mapping:
        table[f"{label} (R$ mi)"] = _currency(data[col])
        table[f"{label} YoY (%)"] = _yoy(data[col])
    return _finalize_table(table)


def table_pl() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["p_Patrimonio_Liquido"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    data = df[["ano", "p_Patrimonio_Liquido"]].copy()
    table = pd.DataFrame({"Ano": data["ano"].astype(int)})
    valores = data["p_Patrimonio_Liquido"]
    table["Patrimônio Líquido (R$ mi)"] = _currency(valores)
    table["YoY (%)"] = _yoy(valores)
    cagr = _cagr(valores)
    cagr_pct = round(cagr * 100, 2) if not np.isnan(cagr) else np.nan
    table["CAGR do periodo (%)"] = [cagr_pct] * len(table)
    return _finalize_table(table)


def table_capital_giro() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["p_Ativo_Circulante", "p_Passivo_Circulante"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    data = df[["ano", "p_Ativo_Circulante", "p_Passivo_Circulante"]].copy()
    ativo = data["p_Ativo_Circulante"]
    passivo = data["p_Passivo_Circulante"]
    ccl = ativo - passivo
    table = pd.DataFrame({"Ano": data["ano"].astype(int)})
    table["Ativo Circulante (R$ mi)"] = _currency(ativo)
    table["Ativo Circulante YoY (%)"] = _yoy(ativo)
    table["Passivo Circulante (R$ mi)"] = _currency(passivo)
    table["Passivo Circulante YoY (%)"] = _yoy(passivo)
    table["CCL (R$ mi)"] = _currency(ccl)
    table["CCL YoY (%)"] = _yoy(ccl)
    table["AC/PC (x)"] = _percent(_safe_div(ativo, passivo))
    return _finalize_table(table)


def table_operacional() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["r_Receita_Total", "r_Custos", "r_Lucro_Liquido", "r_Despesa_de_Juros", "r_Despesa_de_Impostos"]
    ok, missing = _ensure_required(df, required)
    if not ok:
        return None
    ebit, ebitda = _compute_ebit_e_ebitda(df)
    receita = _optional_series(df, "r_Receita_Total")
    custos = _optional_series(df, "r_Custos")
    table = pd.DataFrame({"Ano": df["ano"].astype(int)})
    table["Receita Total (R$ mi)"] = _currency(receita)
    table["Receita YoY (%)"] = _yoy(receita)
    table["Custos (R$ mi)"] = _currency(custos)
    table["Custos YoY (%)"] = _yoy(custos)
    table["EBITDA (R$ mi)"] = _currency(ebitda)
    table["EBITDA YoY (%)"] = _yoy(ebitda)
    table["Margem EBITDA (%)"] = _percent(_safe_div(ebitda, receita) * 100)
    return _finalize_table(table)


def table_financeiro() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["r_Despesa_de_Juros", "r_Receita_Total", "r_Lucro_Liquido", "r_Despesa_de_Impostos"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    ebit, _ = _compute_ebit_e_ebitda(df)
    juros = _optional_series(df, "r_Despesa_de_Juros")
    receita = _optional_series(df, "r_Receita_Total")
    table = pd.DataFrame({"Ano": df["ano"].astype(int)})
    table["Despesa de Juros (R$ mi)"] = _currency(juros)
    table["Despesa de Juros YoY (%)"] = _yoy(juros)
    table["Juros/Receita (%)"] = _percent(_safe_div(juros, receita) * 100)
    table["Cobertura de Juros (x)"] = _percent(_safe_div(ebit, juros))
    return _finalize_table(table)


def table_impostos() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["r_Despesa_de_Impostos", "r_Receita_Total"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    impostos = _optional_series(df, "r_Despesa_de_Impostos")
    receita = _optional_series(df, "r_Receita_Total")
    table = pd.DataFrame({"Ano": df["ano"].astype(int)})
    table["Despesa de Impostos (R$ mi)"] = _currency(impostos)
    table["Despesa de Impostos YoY (%)"] = _yoy(impostos)
    table["Carga Tributaria (%)"] = _percent(_safe_div(impostos, receita) * 100)
    return _finalize_table(table)


def table_resultado() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["r_Lucro_Liquido"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    lucro = _optional_series(df, "r_Lucro_Liquido")
    table = pd.DataFrame({"Ano": df["ano"].astype(int)})
    table["Lucro Liquido (R$ mi)"] = _currency(lucro)
    table["Lucro YoY (%)"] = _yoy(lucro)
    cagr = _cagr(lucro)
    cagr_pct = round(cagr * 100, 2) if not np.isnan(cagr) else np.nan
    table["CAGR do periodo (%)"] = [cagr_pct] * len(table)
    return _finalize_table(table)


def table_liquidez_indices() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["p_Ativo_Circulante", "p_Passivo_Circulante", "p_Estoques", "p_Ativo_Total"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    metrics = _compute_liquidez_metricas(df).round(2)
    window = metrics.drop(columns=["Ano"], errors="ignore").tail(min(len(metrics), 5))
    media_values = window.mean(numeric_only=True).round(2)
    media_row = {"Ano": "Media 5 anos"}
    for col in metrics.columns:
        if col == "Ano":
            continue
        media_row[col] = media_values.get(col, np.nan)
    table = pd.concat([metrics, pd.DataFrame([media_row])], ignore_index=True)
    return _finalize_table(table)


def table_endividamento_indices() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["p_Passivo_Total", "p_Patrimonio_Liquido", "p_Caixa", "p_Ativo_Total"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    metrics = _compute_endividamento_metricas(df).round(2)
    window = metrics.drop(columns=["Ano"], errors="ignore").tail(min(len(metrics), 5))
    media_values = window.mean(numeric_only=True).round(2)
    metrics["Benchmark"] = np.nan
    media_row = {"Ano": "Media 5 anos", "Benchmark": np.nan}
    for col in metrics.columns:
        if col in {"Ano", "Benchmark"}:
            continue
        media_row[col] = media_values.get(col, np.nan)
    table = pd.concat([metrics, pd.DataFrame([media_row])], ignore_index=True)
    return _finalize_table(table)


def table_rentabilidade_indices() -> pd.DataFrame | None:
    df = _get_base_df()
    required = ["r_Lucro_Liquido", "r_Receita_Total", "p_Patrimonio_Liquido", "p_Ativo_Total"]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    metrics = _compute_rentabilidade_metricas(df)
    table = pd.DataFrame({"Ano": metrics["Ano"].astype(int)})
    mapping = [
        ("ROE", "ROE (%)"),
        ("ROA", "ROA (%)"),
        ("Margem Liquida", "Margem Liquida (%)"),
        ("Margem EBITDA", "Margem EBITDA (%)"),
    ]
    for col, label in mapping:
        table[label] = _percent(metrics[col])
        table[f"{label} Δ YoY (p.p.)"] = _diff(metrics[col])
    media = table.tail(min(len(table), 5)).mean(numeric_only=True)
    media_dict = {label: media.get(label, np.nan) for _, label in mapping}
    media_row = {"Ano": "Media 5 anos"}
    media_row.update({label: round(media_dict[label], 2) if not np.isnan(media_dict[label]) else np.nan for _, label in mapping})
    for _, label in mapping:
        media_row[f"{label} Δ YoY (p.p.)"] = np.nan
    table = pd.concat([table, pd.DataFrame([media_row])], ignore_index=True)
    return _finalize_table(table)


def table_eficiencia_indices() -> pd.DataFrame | None:
    df = _get_base_df()
    required = [
        "p_Contas_a_Receber",
        "p_Contas_a_Pagar",
        "r_Receita_Total",
        "r_Custos",
        "p_Ativo_Total",
        "r_Despesa_de_Juros",
        "r_Lucro_Liquido",
        "r_Despesa_de_Impostos",
    ]
    ok, _ = _ensure_required(df, required)
    if not ok:
        return None
    metrics = _compute_eficiencia_metricas(df)
    table = pd.DataFrame({"Ano": metrics["Ano"].astype(int)})
    for col in ["PMR (dias)", "PMP (dias)", "Giro do Ativo (x)", "Cobertura de Juros (x)"]:
        table[col] = _percent(metrics[col])
        table[f"{col} Δ YoY"] = _diff(metrics[col])
    media = table.tail(min(len(table), 5)).mean(numeric_only=True)
    media_row = {"Ano": "Media 5 anos"}
    for col in ["PMR (dias)", "PMP (dias)", "Giro do Ativo (x)", "Cobertura de Juros (x)"]:
        val = media.get(col, np.nan)
        media_row[col] = round(val, 2) if not np.isnan(val) else np.nan
        media_row[f"{col} Δ YoY"] = np.nan
    table = pd.concat([table, pd.DataFrame([media_row])], ignore_index=True)
    return _finalize_table(table)

def get_pca_variance_table() -> pd.DataFrame | None:
    out = st.session_state.get("out")
    if not out:
        return None
    variancia = out.get("pca_explained_variance")
    variancia_cum = out.get("pca_explained_variance_cum")
    if not variancia:
        return None
    variancia = np.array(variancia)
    variancia_cum = np.array(variancia_cum if variancia_cum else np.cumsum(variancia))
    componentes = [f"PC{i+1}" for i in range(len(variancia))]
    return pd.DataFrame(
        {
            "Componente": componentes,
            "Variância (%)": np.round(variancia * 100, 2),
            "Acumulada (%)": np.round(variancia_cum * 100, 2),
        }
    )


def get_indices_table() -> pd.DataFrame | None:
    ss = st.session_state
    out = ss.get("out")
    if not out:
        return None
    df_indices = out.get("df_indices")
    if df_indices is None:
        return None
    return _formata_ano(df_indices)

def get_pca_scores_table() -> pd.DataFrame | None:
    ss = st.session_state
    out = ss.get("out")
    if not out:
        return None
    df_pca = out.get("df_pca")
    if df_pca is None:
        return None
    return _formata_ano(df_pca).drop(columns="Ano", errors="ignore")

def get_top_indices_table() -> pd.DataFrame | None:
    ss = st.session_state
    out = ss.get("out")
    if not out:
        return None
    return out.get("top_indices_df")

def get_pca_loadings_table() -> pd.DataFrame | None:
    ss = st.session_state
    out = ss.get("out")
    if not out:
        return None
    return out.get("loadings")

def render():
    ss = st.session_state
    st.header("Tabelas")
    if not ss.out:
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        return

    st.subheader("Índices Contábeis Calculados")
    df_indices = get_indices_table()
    if df_indices is not None:
        st.dataframe(df_indices, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados de índices contábeis para exibir.")

    st.subheader("Componentes Principais (PCA)")
    df_pca = get_pca_scores_table()
    if df_pca is not None:
        st.dataframe(df_pca, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados de scores de PCA para exibir.")

    st.subheader("Top 3 Índices por Componente")
    top_indices_df = get_top_indices_table()
    if top_indices_df is not None:
        st.dataframe(top_indices_df, use_container_width=True, hide_index=True)
    else:
        st.info("Sem destaques de PCA para exibir.")


# Contrato de apresentação da metodologia Pudim 2.0.13. Os DataFrames abaixo
# são apenas copiados e formatados; nenhum índice ou score é recalculado na view.
INDICATOR_LABELS = {
    "crescimento_receita": "Crescimento da Receita",
    "margem_bruta": "Margem Bruta",
    "margem_liquida": "Margem Líquida",
    "margem_ebit": "Margem EBIT",
    "giro_ativo": "Giro do Ativo",
    "capitalizacao": "Capitalização",
    "endividamento_exigivel": "Endividamento Exigível",
    "liquidez_corrente": "Liquidez Corrente",
    "liquidez_seca": "Liquidez Seca",
    "liquidez_imediata": "Liquidez Imediata",
    "ccl_ativo": "CCL / Ativo",
    "divida_liquida_ativo": "Dívida Líquida / Ativo",
    "cobertura_juros": "Cobertura de Juros",
    "composicao_endividamento": "Composição do Endividamento",
}

TABLE_KEYS = {
    "indices": "df_indices_observados",
    "notas": "df_notas_observadas",
    "motivos_indisponibilidade": "df_motivos_nan",
    "score_temporal": "df_score_temporal",
    "contribuicoes": "df_contribuicoes_score",
    "diagnostico_pca": "df_diagnostico_pca",
    "pesos_pca": "df_pesos_pca",
    "cargas_pca": "df_cargas_pca",
    "caps_prudenciais": "df_caps_prudenciais",
    "intervalos_incerteza": "df_intervalos_incerteza",
    "redundancia_fp": "df_sensibilidade_redundancia_fp",
    "cenarios_deterministicos": "df_cenarios_deterministicos",
    "resumo_simulacoes": "df_resumo_simulacoes",
    "comparacao_monte_carlo": "df_comparacao_monte_carlo",
    "sensibilidade": "df_sensibilidade",
    "amplitudes": "df_amplitudes",
    "comparacao_aceitos_rejeitados": "df_comparacao_aceitos_rejeitados",
}


def _copy_table(value: Any) -> pd.DataFrame:
    return value.copy(deep=True) if isinstance(value, pd.DataFrame) else pd.DataFrame()


def _add_year(table: pd.DataFrame, output: dict[str, Any]) -> pd.DataFrame:
    if table.empty or "ano" in table.columns:
        return table
    reported = output.get("df_contas_reportadas")
    if isinstance(reported, pd.DataFrame) and "ano" in reported and len(reported) == len(table):
        table.insert(0, "ano", reported["ano"].to_list())
    return table


def _prepare_display_table(table: pd.DataFrame, output: dict[str, Any]) -> pd.DataFrame:
    result = _add_year(table.copy(deep=True), output)
    if "indicador" in result:
        result["indicador"] = result["indicador"].map(
            lambda value: INDICATOR_LABELS.get(str(value), str(value))
        )
    if "conta" in result:
        result.insert(
            result.columns.get_loc("conta") + 1,
            "nome_conta",
            result["conta"].map(formatar_nome_conta),
        )
    result = result.rename(columns={
        "ano": "Ano", "indicador": "Indicador", "nucleo": "Núcleo",
        "metodo": "Método", "motivo": "Motivo", "dependencias": "Dependências",
    })
    result = result.rename(columns={
        column: INDICATOR_LABELS[column]
        for column in result.columns if column in INDICATOR_LABELS
    })
    numeric = result.select_dtypes(include=["number"]).columns
    result[numeric] = result[numeric].round(4)
    return result


def catalogar_tabelas_pudim(output: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Obtém cópias prontas para exibição sem alterar o contrato do motor."""
    return {
        name: _prepare_display_table(_copy_table(output.get(key)), output)
        for name, key in TABLE_KEYS.items()
    }


def _show_contract_table(title: str, table: pd.DataFrame, empty_message: str) -> None:
    st.markdown(f"#### {title}")
    if table.empty:
        st.info(empty_message)
        return
    st.dataframe(table, use_container_width=True, hide_index=True)


def render_tabelas_pudim(output: dict[str, Any]) -> None:
    """Renderiza somente resultados calculados pelo motor Pudim."""
    status = output.get("status_qualidade", {})
    st.markdown("<h3 style='text-align:left;'>📊 Tabelas — Pudim 2.0.13</h3>", unsafe_allow_html=True)
    st.caption("Resultados auditáveis fornecidos diretamente pelo contrato do motor.")
    if not status.get("apto_calculo", False):
        st.error(
            f"Cálculo bloqueado: {status.get('status', 'dados não aptos para scoring')}. "
            "Revise as ocorrências na aba Dados Contábeis."
        )
        return

    tables = catalogar_tabelas_pudim(output)
    tab_indices, tab_composicao, tab_pca, tab_prudencial, tab_cenarios = st.tabs([
        "Índices e notas", "Composição do score", "PCA",
        "Prudencial", "Cenários e simulações",
    ])
    with tab_indices:
        _show_contract_table("Índices observados", tables["indices"], "Sem índices calculados.")
        _show_contract_table("Notas observadas", tables["notas"], "Sem notas calculadas.")
        _show_contract_table(
            "Indicadores indisponíveis", tables["motivos_indisponibilidade"],
            "Todos os indicadores utilizados estão disponíveis.",
        )
    with tab_composicao:
        _show_contract_table("Score temporal", tables["score_temporal"], "Sem composição temporal.")
        _show_contract_table("Contribuições ao score", tables["contribuicoes"], "Sem contribuições calculadas.")
    with tab_pca:
        _show_contract_table("Diagnóstico por núcleo", tables["diagnostico_pca"], "Sem diagnóstico de PCA.")
        _show_contract_table("Pesos por núcleo", tables["pesos_pca"], "Sem pesos de PCA.")
        _show_contract_table("Cargas por núcleo", tables["cargas_pca"], "Sem cargas de PCA.")
    with tab_prudencial:
        _show_contract_table("Caps prudenciais", tables["caps_prudenciais"], "Nenhum cap prudencial foi registrado.")
        _show_contract_table("Intervalos de incerteza", tables["intervalos_incerteza"], "Sem intervalos de incerteza.")
        _show_contract_table("Redundância do núcleo FP", tables["redundancia_fp"], "Sem análise de redundância.")
    with tab_cenarios:
        _show_contract_table("Cenários determinísticos", tables["cenarios_deterministicos"], "Sem cenários determinísticos.")
        if int(output.get("modelo", {}).get("numero_simulacoes", 0)) == 0:
            st.info("Monte Carlo não foi executado neste cálculo.")
        else:
            _show_contract_table("Resumo das simulações", tables["resumo_simulacoes"], "Sem resumo das simulações.")
            _show_contract_table("Comparação Monte Carlo", tables["comparacao_monte_carlo"], "Sem comparação Monte Carlo.")
            _show_contract_table("Sensibilidade", tables["sensibilidade"], "Sem resultados de sensibilidade.")
            _show_contract_table("Amplitudes", tables["amplitudes"], "Sem amplitudes calculadas.")
            _show_contract_table(
                "Aceitos e rejeitados", tables["comparacao_aceitos_rejeitados"],
                "Sem comparação entre resultados aceitos e rejeitados.",
            )


# A entrada pública desta view passa a usar a metodologia Pudim.
def render():
    output = st.session_state.get("out")
    if not output:
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        return
    render_tabelas_pudim(output)
