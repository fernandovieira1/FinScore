# app_front/views/graficos.py
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

TITLE_STYLE = {"font_size": 20, "y": 0.95}
LEGEND_STYLE = {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1.0}
MILLION = 1_000_000


def _prepare_base_df() -> pd.DataFrame | None:
    # Escolhe a base mais apropriada para os gráficos e padroniza a coluna 'ano'.
    ss = st.session_state
    base = None

    if ss.get("df") is not None:
        base = ss.df
    elif ss.get("out"):
        base = ss.out.get("df_raw")
        if base is None:
            return None

    df = base.copy()

    if "ano" not in df.columns:
        df["ano"] = list(range(len(df), 0, -1))

    for col in df.columns:
        if col != "ano":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df = df[df["ano"].notna()].copy()
    df["ano"] = df["ano"].astype(int)
    df = df.sort_values("ano", ascending=True)
    df["ano_label"] = df["ano"].astype(str)
    return df


def prepare_base_data() -> pd.DataFrame | None:
    return _prepare_base_df()


def _ensure_columns(df: pd.DataFrame, required: list[str], contexto: str) -> bool:
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.warning(
            f"Nao foi possivel montar **{contexto}** (faltam: {', '.join(sorted(missing))})."
        )
        return False
    return True


def _series(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce").fillna(default)


def _to_millions(series: pd.Series) -> pd.Series:
    return series / MILLION


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return numerator.divide(denominator)



def _apply_year_axis(fig, labels, axis="x"):
    if labels is None:
        return
    ordered = [str(value) for value in dict.fromkeys(labels)]
    if not ordered:
        return
    if axis == "x":
        fig.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=ordered,
            tickmode="array",
            tickvals=ordered,
            ticktext=ordered,
        )
    else:
        fig.update_yaxes(
            type="category",
            categoryorder="array",
            categoryarray=ordered,
            tickmode="array",
            tickvals=ordered,
            ticktext=ordered,
        )


def render_ativos(df: pd.DataFrame) -> bool:
    required = [
        "p_Ativo_Circulante",
        "p_Ativo_Total",
        "p_Caixa",
        "p_Estoques",
        "p_Contas_a_Receber",
    ]
    if not _ensure_columns(df, required, "Evolução dos Ativos"):
        return False

    data = df[["ano_label", *required]].copy()
    for col in required:
        data[col] = _to_millions(data[col])

    fig = go.Figure()
    area_map = {
        "p_Caixa": ("Caixa", "#4cb2a0"),
        "p_Estoques": ("Estoques", "#7cd1b8"),
        "p_Contas_a_Receber": ("Contas a Receber", "#a2d35e"),
    }
    for col, (name, color) in area_map.items():
        fig.add_trace(
            go.Scatter(
                x=data["ano_label"],
                y=data[col],
                name=name,
                mode="lines",
                line=dict(width=0.6, color=color),
                stackgroup="ativos",
                hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=data["ano_label"],
            y=data["p_Ativo_Circulante"],
            name="Ativo Circulante",
            mode="lines+markers",
            line=dict(color="#0b7285", width=3, dash="dot"),
            marker=dict(size=7),
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["ano_label"],
            y=data["p_Ativo_Total"],
            name="Ativo Total",
            mode="lines+markers",
            line=dict(color="#014f86", width=3),
            marker=dict(size=8),
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )

    fig.update_layout(
        title={"text": "Evolução dos Ativos", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="R$ milhões",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=420,
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_passivos(df: pd.DataFrame) -> bool:
    required = ["p_Contas_a_Pagar", "p_Passivo_Circulante", "p_Passivo_Total"]
    if not _ensure_columns(df, required, "Evolução dos Passivos"):
        return False

    data = df[["ano_label", *required]].copy()
    for col in required:
        data[col] = _to_millions(data[col])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["ano_label"],
            y=data["p_Contas_a_Pagar"],
            name="Contas a Pagar",
            mode="lines",
            line=dict(width=0.6, color="#f8961e"),
            stackgroup="passivos",
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["ano_label"],
            y=data["p_Passivo_Circulante"],
            name="Passivo Circulante",
            mode="lines",
            line=dict(width=0.6, color="#f3722c"),
            stackgroup="passivos",
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["ano_label"],
            y=data["p_Passivo_Total"],
            name="Passivo Total",
            mode="lines+markers",
            line=dict(color="#d00000", width=3),
            marker=dict(size=8),
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )

    fig.update_layout(
        title={"text": "Evolução dos Passivos", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="R$ milhões",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=400,
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_pl(df: pd.DataFrame) -> bool:
    required = ["p_Patrimonio_Liquido"]
    if not _ensure_columns(df, required, "Evolução do Patrimônio Líquido"):
        return False

    data = df[["ano_label", "p_Patrimonio_Liquido"]].copy()
    data["p_Patrimonio_Liquido"] = _to_millions(data["p_Patrimonio_Liquido"])

    fig = go.Figure(
        data=[
            go.Scatter(
                x=data["ano_label"],
                y=data["p_Patrimonio_Liquido"],
                mode="lines+markers",
                line=dict(color="#2c6e49", width=3),
                marker=dict(size=8),
                name="Patrimônio Líquido",
                hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title={"text": "Evolução do Patrimônio Líquido", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="R$ milhões",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=360,
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_ativo_passivo_circulante(df: pd.DataFrame) -> bool:
    required = ["p_Ativo_Circulante", "p_Passivo_Circulante"]
    if not _ensure_columns(df, required, "Capital de Giro e Liquidez"):
        return False

    data = df[["ano_label", "p_Ativo_Circulante", "p_Passivo_Circulante"]].copy()
    data["Ativo Circulante"] = _to_millions(data["p_Ativo_Circulante"])
    data["Passivo Circulante"] = _to_millions(data["p_Passivo_Circulante"])
    data["CCL"] = _to_millions(df["p_Ativo_Circulante"] - df["p_Passivo_Circulante"])

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=data["ano_label"],
            y=data["Ativo Circulante"],
            name="Ativo Circulante",
            marker_color="#3a86ff",
            offsetgroup="circulante",
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=data["ano_label"],
            y=data["Passivo Circulante"],
            name="Passivo Circulante",
            marker_color="#ff595e",
            offsetgroup="circulante",
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["ano_label"],
            y=data["CCL"],
            name="CCL (AC-PC)",
            mode="lines+markers",
            line=dict(color="#000000", width=3),
            marker=dict(size=7),
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )

    fig.update_layout(
        title={"text": "Capital de Giro e Liquidez", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="R$ milhoes",
        barmode="group",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=420,
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True

def _compute_ebit_e_ebitda(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    lucro = _series(df, "r_Lucro_Liquido")
    juros = _series(df, "r_Despesa_de_Juros")
    impostos = _series(df, "r_Despesa_de_Impostos")
    amort = _series(df, "r_Amortizacao")
    depr = _series(df, "r_Depreciacao")
    ebit = lucro + juros + impostos
    ebitda = ebit + amort + depr
    return ebit, ebitda


def render_receita_total(df: pd.DataFrame) -> bool:
    required = ["r_Receita_Total", "r_Custos", "r_Lucro_Liquido", "r_Despesa_de_Juros", "r_Despesa_de_Impostos"]
    if not _ensure_columns(df, required, "Receita, Custos e EBITDA"):
        return False

    _, ebitda = _compute_ebit_e_ebitda(df)
    data = pd.DataFrame(
        {
            "ano_label": df["ano_label"],
            "Receita": _to_millions(_series(df, "r_Receita_Total")),
            "Custos": _to_millions(_series(df, "r_Custos")),
            "EBITDA": _to_millions(ebitda),
        }
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=data["ano_label"],
            y=data["Receita"],
            name="Receita Total",
            marker_color="#1d4ed8",
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=data["ano_label"],
            y=-data["Custos"],
            name="Custos",
            marker_color="#f59f9f",
            hovertemplate="Ano %{x}<br>%{(-y):,.2f} R$ mi<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["ano_label"],
            y=data["EBITDA"],
            name="EBITDA",
            mode="lines+markers",
            line=dict(color="#16a34a", width=3),
            marker=dict(size=8),
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        )
    )
    fig.update_layout(
        title={"text": "Receita, Custos e EBITDA", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="R$ milhoes",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=420,
        barmode="relative",
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_juros_lucro_receita(df: pd.DataFrame) -> bool:
    required = ["r_Despesa_de_Juros", "r_Receita_Total", "r_Lucro_Liquido"]
    if not _ensure_columns(df, required, "Custo Financeiro e Resultados"):
        return False

    data = pd.DataFrame(
        {
            "ano_label": df["ano_label"],
            "Despesa de Juros": _to_millions(_series(df, "r_Despesa_de_Juros")),
            "Receita Total": _to_millions(_series(df, "r_Receita_Total")),
            "Lucro Liquido": _to_millions(_series(df, "r_Lucro_Liquido")),
        }
    )

    fig = go.Figure()
    colors = {
        "Despesa de Juros": "#d1495b",
        "Receita Total": "#4361ee",
        "Lucro Liquido": "#2a9d8f",
    }
    for name in ["Despesa de Juros", "Receita Total", "Lucro Liquido"]:
        fig.add_trace(
            go.Scatter(
                x=data["ano_label"],
                y=data[name],
                name=name,
                mode="lines+markers",
                line=dict(color=colors[name], width=3),
                marker=dict(size=7),
                hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
            )
        )
    fig.update_layout(
        title={"text": "Custo Financeiro e Resultados", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="R$ milhoes",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=380,
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_despesa_juros(df: pd.DataFrame) -> bool:
    return render_juros_lucro_receita(df)


def render_impostos(df: pd.DataFrame) -> bool:
    required = ["r_Despesa_de_Impostos", "r_Receita_Total"]
    if not _ensure_columns(df, required, "Despesa de Impostos"):
        return False

    valores = _to_millions(_series(df, "r_Despesa_de_Impostos"))
    receita = _series(df, "r_Receita_Total")
    carga = _safe_div(_series(df, "r_Despesa_de_Impostos"), receita) * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=df["ano_label"],
            y=valores,
            name="Despesa de Impostos",
            marker_color="#9e9e9e",
            hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["ano_label"],
            y=carga,
            name="% sobre Receita",
            mode="lines+markers",
            line=dict(color="#000000", width=3),
            marker=dict(size=7),
            hovertemplate="Ano %{x}<br>%{y:,.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_layout(
        title={"text": "Despesa de Impostos e Efetividade Tributária", **TITLE_STYLE},
        xaxis_title="Ano",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=400,
    )
    _apply_year_axis(fig, df["ano_label"])
    fig.update_yaxes(title_text="R$ milhões", secondary_y=False)
    fig.update_yaxes(title_text="% da Receita", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_lucro_liquido(df: pd.DataFrame) -> bool:
    if not _ensure_columns(df, ["r_Lucro_Liquido"], "Lucro Liquido"):
        return False

    serie = _to_millions(_series(df, "r_Lucro_Liquido"))
    fig = go.Figure(
        data=[
            go.Scatter(
                x=df["ano_label"],
                y=serie,
                name="Lucro Liquido",
                mode="lines+markers",
                line=dict(color="#1a7431", width=3),
                marker=dict(size=8),
                hovertemplate="Ano %{x}<br>%{y:,.2f} R$ mi<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title={"text": "Lucro Liquido", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="R$ milhoes",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=360,
    )
    _apply_year_axis(fig, df["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True

def _compute_liquidez_metricas(df: pd.DataFrame) -> pd.DataFrame:
    ac = _series(df, "p_Ativo_Circulante")
    pc = _series(df, "p_Passivo_Circulante")
    estoques = _series(df, "p_Estoques")
    total = _series(df, "p_Ativo_Total")
    liquidez_corrente = _safe_div(ac, pc)
    liquidez_seca = _safe_div(ac - estoques, pc)
    ccl_ativo = _safe_div(ac - pc, total)
    return pd.DataFrame(
        {
            "ano_label": df["ano_label"],
            "Liquidez Corrente": liquidez_corrente,
            "Liquidez Seca": liquidez_seca,
            "CCL/Ativo": ccl_ativo,
        }
    )


def render_liquidez_indices(df: pd.DataFrame) -> bool:
    required = ["p_Ativo_Circulante", "p_Passivo_Circulante", "p_Estoques", "p_Ativo_Total"]
    if not _ensure_columns(df, required, "Indices de Liquidez"):
        return False

    data = _compute_liquidez_metricas(df)
    fig = go.Figure()
    palette = {
        "Liquidez Corrente": "#1d4ed8",
        "Liquidez Seca": "#0ea5e9",
        "CCL/Ativo": "#10b981",
    }
    for name in ["Liquidez Corrente", "Liquidez Seca", "CCL/Ativo"]:
        fig.add_trace(
            go.Scatter(
                x=data["ano_label"],
                y=data[name],
                name=name,
                mode="lines+markers",
                line=dict(color=palette[name], width=3),
                marker=dict(size=7),
                hovertemplate="Ano %{x}<br>%{y:,.2f}x<extra></extra>",
            )
        )
    fig.update_layout(
        title={"text": "Indicadores de Liquidez", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="Vezes",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=390,
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_capital_giro(df: pd.DataFrame) -> bool:
    return render_ativo_passivo_circulante(df)


def render_liquidez_corrente(df: pd.DataFrame) -> bool:
    return render_liquidez_indices(df)


def render_endividamento_indices(df: pd.DataFrame) -> bool:
    required = ["p_Passivo_Total", "p_Patrimonio_Liquido", "p_Caixa", "p_Ativo_Total"]
    if not _ensure_columns(df, required, "Estrutura de Capital e Alavancagem"):
        return False

    ebit, ebitda = _compute_ebit_e_ebitda(df)
    divida_bruta = _series(df, "p_Passivo_Total") - _series(df, "p_Patrimonio_Liquido")
    divida_liquida = divida_bruta - _series(df, "p_Caixa")
    total = _series(df, "p_Ativo_Total")

    data = pd.DataFrame(
        {
            "ano_label": df["ano_label"],
            "Divida/Ativo": _safe_div(divida_bruta, total),
            "Divida Liquida/EBITDA": _safe_div(divida_liquida, ebitda),
            "PL/Ativo": _safe_div(_series(df, "p_Patrimonio_Liquido"), total),
        }
    )

    fig = go.Figure()
    palette = {
        "Divida/Ativo": "#ef476f",
        "Divida Liquida/EBITDA": "#f3722c",
        "PL/Ativo": "#ffb703",
    }
    for name in ["Divida/Ativo", "Divida Liquida/EBITDA", "PL/Ativo"]:
        fig.add_trace(
            go.Scatter(
                x=data["ano_label"],
                y=data[name],
                name=name,
                mode="lines+markers",
                line=dict(color=palette[name], width=3),
                marker=dict(size=7),
                hovertemplate="Ano %{x}<br>%{y:,.2f}x<extra></extra>",
            )
        )
    fig.update_layout(
        title={"text": "Estrutura de Capital e Alavancagem", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="Vezes",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=390,
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_rentabilidade_indices(df: pd.DataFrame) -> bool:
    required = ["r_Lucro_Liquido", "r_Receita_Total", "p_Patrimonio_Liquido", "p_Ativo_Total"]
    if not _ensure_columns(df, required, "Indicadores de Rentabilidade"):
        return False

    _, ebitda = _compute_ebit_e_ebitda(df)
    receita = _series(df, "r_Receita_Total")
    lucro = _series(df, "r_Lucro_Liquido")

    data = pd.DataFrame(
        {
            "ano_label": df["ano_label"],
            "ROE": _safe_div(lucro, _series(df, "p_Patrimonio_Liquido")) * 100,
            "ROA": _safe_div(lucro, _series(df, "p_Ativo_Total")) * 100,
            "Margem Liquida": _safe_div(lucro, receita) * 100,
            "Margem EBITDA": _safe_div(ebitda, receita) * 100,
        }
    )

    fig = go.Figure()
    palette = {
        "ROE": "#046865",
        "ROA": "#1b9aaa",
        "Margem Liquida": "#2c7da0",
        "Margem EBITDA": "#144552",
    }
    for name in ["ROE", "ROA", "Margem Liquida", "Margem EBITDA"]:
        fig.add_trace(
            go.Scatter(
                x=data["ano_label"],
                y=data[name],
                name=name,
                mode="lines+markers",
                line=dict(color=palette[name], width=3),
                marker=dict(size=7),
                hovertemplate="Ano %{x}<br>%{y:,.2f}%<extra></extra>",
            )
        )
    fig.update_layout(
        title={"text": "Indicadores de Rentabilidade", **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis_title="%",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=410,
    )
    _apply_year_axis(fig, data["ano_label"])
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_eficiencia_indices(df: pd.DataFrame) -> bool:
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
    if not _ensure_columns(df, required, "Eficiencia Operacional e Ciclo"):
        return False

    ebit, _ = _compute_ebit_e_ebitda(df)
    pmr = _safe_div(_series(df, "p_Contas_a_Receber"), _series(df, "r_Receita_Total")) * 365
    pmp = _safe_div(_series(df, "p_Contas_a_Pagar"), _series(df, "r_Custos")) * 365
    giro = _safe_div(_series(df, "r_Receita_Total"), _series(df, "p_Ativo_Total"))
    cobertura = _safe_div(ebit, _series(df, "r_Despesa_de_Juros"))

    tidy = pd.DataFrame(
        {
            "Ano": np.repeat(df["ano_label"].values, 4),
            "Metrica": [
                "PMR (dias)",
                "PMP (dias)",
                "Giro do Ativo (x)",
                "Cobertura de Juros (x)",
            ]
            * len(df),
            "Valor": np.concatenate(
                [pmr.values, pmp.values, giro.values, cobertura.values]
            ),
        }
    )

    tidy.replace([np.inf, -np.inf], np.nan, inplace=True)
    tidy.dropna(subset=["Valor"], inplace=True)
    if tidy.empty:
        st.info("Sem dados suficientes para Eficiência Operacional.")
        return False

    fig = px.bar(
        tidy,
        x="Valor",
        y="Ano",
        color="Metrica",
        orientation="h",
        barmode="group",
        color_discrete_sequence=["#6c757d", "#adb5bd", "#74c0fc", "#4dabf7"],
        hover_data={"Valor": ":.2f"},
    )
    fig.update_layout(
        title={"text": "Eficiencia e Ciclo Operacional", **TITLE_STYLE},
        xaxis_title="Dias / Vezes",
        yaxis_title="Ano",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=420,
    )
    _apply_year_axis(fig, tidy["Ano"], axis="y")
    st.plotly_chart(fig, use_container_width=True)
    return True

def _get_out_dict() -> dict | None:
    ss = st.session_state
    return ss.get("out") if ss.get("out") else None


def render_pca_loadings(df: pd.DataFrame | None = None) -> bool:
    out = _get_out_dict()
    if not out:
        st.info("Calcule o FinScore em **Novo** para visualizar PCA.")
        return False
    loadings = out.get("loadings")
    if loadings is None or getattr(loadings, "empty", True):
        st.info("Sem dados de loadings para exibir.")
        return False

    heatmap_df = loadings.copy()
    fig = px.imshow(
        heatmap_df,
        color_continuous_scale="RdBu",
        aspect="auto",
        labels=dict(x="Componentes", y="Variaveis", color="Peso"),
    )
    fig.update_layout(
        title={"text": "PCA - Cargas (Loadings)", **TITLE_STYLE},
        margin=dict(l=60, r=20, t=60, b=40),
        height=480,
    )
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_pca_variancia(df: pd.DataFrame | None = None) -> bool:
    out = _get_out_dict()
    if not out:
        st.info("Calcule o FinScore em **Novo** para visualizar PCA.")
        return False
    variancia = out.get("pca_explained_variance")
    variancia_cum = out.get("pca_explained_variance_cum")
    if not variancia:
        st.info("Sem dados de variância explicada para exibir.")
        return False

    variancia = np.array(variancia)
    variancia_cum = np.array(variancia_cum if variancia_cum else np.cumsum(variancia))
    componentes = [f"PC{i+1}" for i in range(len(variancia))]
    df_var = pd.DataFrame(
        {
            "Componente": componentes,
            "Variancia (%)": variancia * 100,
            "Acumulada (%)": variancia_cum * 100,
        }
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_var["Componente"],
            y=df_var["Variancia (%)"],
            name="Variancia",
            marker_color="#3a86ff",
            hovertemplate="%{x}<br>%{y:,.2f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_var["Componente"],
            y=df_var["Acumulada (%)"],
            name="Acumulada",
            mode="lines+markers",
            line=dict(color="#000000", width=3),
            marker=dict(size=7),
            hovertemplate="%{x}<br>%{y:,.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title={"text": "PCA - Variancia Explicada", **TITLE_STYLE},
        xaxis_title="Componentes",
        yaxis_title="%",
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)
    return True


def render_pca_scores(df: pd.DataFrame | None = None) -> bool:
    out = _get_out_dict()
    if not out:
        st.info("Calcule o FinScore em **Novo** para visualizar PCA.")
        return False
    df_scores = out.get("df_pca")
    if df_scores is None or getattr(df_scores, "empty", True):
        st.info("Sem dados de scores para exibir.")
        return False

    plot_df = df_scores.copy()
    if "ano" in plot_df.columns:
        plot_df["Ano"] = plot_df["ano"].astype(str)
    else:
        plot_df["Ano"] = plot_df.index.astype(str)

    pcs = [col for col in plot_df.columns if col.startswith("PC")]
    if len(pcs) < 2:
        st.info("PCA possui menos de 2 componentes para graficar.")
        return False

    fig = px.scatter(
        plot_df,
        x=pcs[0],
        y=pcs[1],
        color="Ano",
        hover_data={"Ano": True},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(
        title={"text": "PCA - Projecoes (Scores)", **TITLE_STYLE},
        xaxis_title=pcs[0],
        yaxis_title=pcs[1],
        legend=LEGEND_STYLE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
    return True


__all__ = [
    "prepare_base_data",
    "render_ativo_passivo_circulante",
    "render_receita_total",
    "render_juros_lucro_receita",
    "render_ativos",
    "render_passivos",
    "render_pl",
    "render_capital_giro",
    "render_liquidez_corrente",
    "render_impostos",
    "render_lucro_liquido",
    "render_liquidez_indices",
    "render_endividamento_indices",
    "render_rentabilidade_indices",
    "render_eficiencia_indices",
    "render_pca_loadings",
    "render_pca_variancia",
    "render_pca_scores",
    "render_despesa_juros",
]
