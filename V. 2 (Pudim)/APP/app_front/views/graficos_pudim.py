"""Visualizações do contrato FinScore Pudim.

Este módulo não calcula indicadores ou scores. Ele apenas seleciona e apresenta
valores já produzidos pelo motor.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .tabelas import INDICATOR_LABELS


COLORS = ["#0b7285", "#2f9e44", "#f08c00", "#c92a2a", "#7048e8"]


def _frame(output: dict[str, Any], key: str) -> pd.DataFrame:
    value = output.get(key)
    return value.copy(deep=True) if isinstance(value, pd.DataFrame) else pd.DataFrame()


def _years(output: dict[str, Any], length: int) -> list[str]:
    source = _frame(output, "df_contas_reportadas")
    if "ano" in source and len(source) == length:
        return source["ano"].map(lambda value: str(int(value))).tolist()
    return [str(index + 1) for index in range(length)]


def _line_figure(
    source: pd.DataFrame,
    series: dict[str, str],
    title: str,
    yaxis_title: str = "R$ milhões",
    scale: float = 1_000_000,
) -> go.Figure:
    fig = go.Figure()
    if source.empty or "ano" not in source:
        return fig
    years = source["ano"].map(lambda value: str(int(value)))
    for index, (column, label) in enumerate(series.items()):
        if column not in source:
            continue
        values = pd.to_numeric(source[column], errors="coerce") / scale
        fig.add_trace(go.Scatter(
            x=years,
            y=values,
            name=label,
            mode="lines+markers",
            line={"width": 3, "color": COLORS[index % len(COLORS)]},
            marker={"size": 8},
            hovertemplate=f"%{{x}}<br>{label}: %{{y:,.2f}}<extra></extra>",
        ))
    fig.update_layout(
        title=title,
        xaxis_title="Exercício",
        yaxis_title=yaxis_title,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12},
        height=410,
        margin={"l": 20, "r": 20, "t": 75, "b": 20},
    )
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=list(years))
    return fig


def construir_figuras_contabeis(output: dict[str, Any]) -> dict[str, go.Figure]:
    """Constrói séries contábeis usando somente contas do contrato Pudim."""
    accounts = _frame(output, "df_contas_derivadas")
    return {
        "estrutura": _line_figure(accounts, {
            "p_Ativo_Total": "Ativo Total",
            "d_Passivo_Exigivel_Total": "Passivo Exigível",
            "p_Patrimonio_Liquido": "Patrimônio Líquido",
        }, "Estrutura patrimonial"),
        "liquidez": _line_figure(accounts, {
            "p_Ativo_Circulante": "Ativo Circulante",
            "p_Passivo_Circulante": "Passivo Circulante",
            "d_Capital_Circulante_Liquido": "Capital Circulante Líquido",
        }, "Capital de giro"),
        "resultado": _line_figure(accounts, {
            "r_Receita_Liquida": "Receita Líquida",
            "d_EBIT": "EBIT",
            "r_Lucro_Liquido": "Lucro Líquido",
        }, "Receita e resultados"),
        "divida": _line_figure(accounts, {
            "d_Divida_Financeira_Bruta": "Dívida Financeira Bruta",
            "d_Divida_Financeira_Liquida": "Dívida Financeira Líquida",
            "r_Despesas_Financeiras": "Despesas Financeiras",
        }, "Dívida e despesas financeiras"),
    }


def construir_figura_notas(output: dict[str, Any]) -> go.Figure:
    notes = _frame(output, "df_notas_observadas")
    fig = go.Figure()
    if notes.empty:
        return fig
    labels = [INDICATOR_LABELS.get(column, column.replace("_", " ").title()) for column in notes]
    values = notes.apply(pd.to_numeric, errors="coerce").T
    fig.add_trace(go.Heatmap(
        z=values.to_numpy(),
        x=_years(output, len(notes)),
        y=labels,
        zmin=0,
        zmax=100,
        colorscale="RdYlGn",
        colorbar={"title": "Nota"},
        hovertemplate="%{y}<br>%{x}: %{z:.1f}<extra></extra>",
    ))
    fig.update_layout(
        title="Notas dos indicadores por exercício",
        xaxis_title="Exercício",
        height=560,
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    return fig


def construir_figura_temporal(output: dict[str, Any]) -> go.Figure:
    scores = _frame(output, "df_score_temporal")
    fig = go.Figure()
    if scores.empty:
        return fig
    labels = scores["indicador"].map(lambda value: INDICATOR_LABELS.get(str(value), str(value)))
    for column, label, color in (
        ("nivel_atual", "Nível atual", "#1971c2"),
        ("dinamica_temporal", "Dinâmica temporal", "#f08c00"),
        ("resiliencia", "Resiliência", "#2f9e44"),
        ("nota_temporal", "Nota temporal", "#7048e8"),
    ):
        fig.add_trace(go.Bar(
            x=labels,
            y=pd.to_numeric(scores[column], errors="coerce"),
            name=label,
            marker_color=color,
        ))
    fig.update_layout(
        title="Composição temporal dos indicadores",
        barmode="group",
        yaxis={"title": "Nota", "range": [0, 100]},
        xaxis={"tickangle": -35},
        legend={"orientation": "h", "y": 1.12},
        height=520,
        margin={"l": 20, "r": 20, "t": 75, "b": 140},
    )
    return fig


def construir_figura_pesos_pca(output: dict[str, Any]) -> go.Figure:
    weights = _frame(output, "df_pesos_pca")
    fig = go.Figure()
    if weights.empty:
        return fig
    labels = weights["indicador"].map(lambda value: INDICATOR_LABELS.get(str(value), str(value)))
    for nucleus, color in (("EO", "#1971c2"), ("FP", "#e8590c")):
        mask = weights["nucleo"].eq(nucleus)
        fig.add_trace(go.Bar(
            x=labels[mask],
            y=pd.to_numeric(weights.loc[mask, "peso_adaptativo"], errors="coerce") * 100,
            name=f"Núcleo {nucleus}",
            marker_color=color,
        ))
    fig.update_layout(
        title="Pesos adaptativos do PCA por núcleo",
        yaxis_title="Peso (%)",
        xaxis={"tickangle": -35},
        legend={"orientation": "h", "y": 1.12},
        height=500,
        margin={"l": 20, "r": 20, "t": 75, "b": 140},
    )
    return fig


def construir_figura_nucleos(output: dict[str, Any]) -> go.Figure:
    score = output.get("finscore_observado", {})
    fig = go.Figure()
    if not score:
        return fig
    categories = ["EO", "FP", "FinScore pós-gargalo"]
    fig.add_trace(go.Bar(
        x=categories,
        y=[score.get("nucleo_EO_estrutural"), score.get("nucleo_FP_estrutural"), score.get("finscore_estrutural_pos_gargalo")],
        name="Estrutural",
        marker_color="#1971c2",
    ))
    fig.add_trace(go.Bar(
        x=categories,
        y=[score.get("nucleo_EO_adaptativo"), score.get("nucleo_FP_adaptativo"), score.get("finscore_adaptativo_pos_gargalo")],
        name="Adaptativo",
        marker_color="#7048e8",
    ))
    cap = score.get("cap_prudencial_aplicavel")
    if cap is not None:
        fig.add_hline(y=float(cap), line_dash="dash", line_color="#c92a2a", annotation_text="Cap prudencial")
    fig.update_layout(
        title="Núcleos e consolidação do FinScore",
        barmode="group",
        yaxis={"title": "Pontos", "range": [0, 1000]},
        legend={"orientation": "h", "y": 1.12},
        height=430,
        margin={"l": 20, "r": 20, "t": 75, "b": 20},
    )
    return fig


def construir_figura_cenarios(output: dict[str, Any]) -> go.Figure:
    scenarios = _frame(output, "df_cenarios_deterministicos")
    fig = go.Figure()
    required = {"cenario", "finscore_prudencial", "nucleo_EO_adaptativo", "nucleo_FP_adaptativo"}
    if scenarios.empty or not required.issubset(scenarios.columns):
        return fig
    for column, label, color in (
        ("nucleo_EO_adaptativo", "Núcleo EO", "#1971c2"),
        ("nucleo_FP_adaptativo", "Núcleo FP", "#e8590c"),
        ("finscore_prudencial", "FinScore prudencial", "#2f9e44"),
    ):
        fig.add_trace(go.Bar(
            x=scenarios["cenario"],
            y=pd.to_numeric(scenarios[column], errors="coerce"),
            name=label,
            marker_color=color,
        ))
    fig.update_layout(
        title="Cenários determinísticos",
        barmode="group",
        yaxis={"title": "Pontos", "range": [0, 1000]},
        legend={"orientation": "h", "y": 1.12},
        height=430,
        margin={"l": 20, "r": 20, "t": 75, "b": 20},
    )
    return fig


def construir_figura_monte_carlo(output: dict[str, Any]) -> go.Figure:
    fig = go.Figure()
    for key, label, color in (
        ("df_simulacoes_independentes", "Independente", "#1971c2"),
        ("df_simulacoes_correlacionadas", "Correlacionado", "#e8590c"),
    ):
        simulations = _frame(output, key)
        if "finscore_prudencial" not in simulations:
            continue
        fig.add_trace(go.Histogram(
            x=pd.to_numeric(simulations["finscore_prudencial"], errors="coerce"),
            name=label,
            marker_color=color,
            opacity=0.65,
            nbinsx=30,
        ))
    if fig.data:
        fig.update_layout(
            title="Distribuição Monte Carlo do FinScore prudencial",
            barmode="overlay",
            xaxis_title="FinScore prudencial",
            yaxis_title="Frequência",
            legend={"orientation": "h", "y": 1.12},
            height=430,
            margin={"l": 20, "r": 20, "t": 75, "b": 20},
        )
    return fig


def _show_figure(fig: go.Figure, empty_message: str) -> None:
    if not fig.data:
        st.info(empty_message)
        return
    st.plotly_chart(fig, use_container_width=True)


def render_graficos_pudim(output: dict[str, Any]) -> None:
    """Renderiza os gráficos oficiais da etapa de análise Pudim."""
    status = output.get("status_qualidade", {})
    st.markdown("<h3 style='text-align:left;'>📈 Gráficos</h3>", unsafe_allow_html=True)
    st.caption("Visualizações de dados e resultados fornecidos pelo contrato do motor.")
    if not status.get("apto_calculo", False):
        st.error(
            f"Cálculo bloqueado: {status.get('status', 'dados não aptos para scoring')}. "
            "Revise as ocorrências na aba Dados Contábeis."
        )
        return

    tab_contas, tab_indicadores, tab_modelo, tab_cenarios = st.tabs([
        "Contas", "Indicadores", "Modelo e PCA", "Cenários",
    ])
    with tab_contas:
        for figure in construir_figuras_contabeis(output).values():
            _show_figure(figure, "Sem dados contábeis suficientes para este gráfico.")
    with tab_indicadores:
        _show_figure(construir_figura_notas(output), "Sem notas observadas para exibir.")
        _show_figure(construir_figura_temporal(output), "Sem composição temporal para exibir.")
    with tab_modelo:
        _show_figure(construir_figura_nucleos(output), "Sem consolidação do FinScore para exibir.")
        _show_figure(construir_figura_pesos_pca(output), "Sem pesos PCA para exibir.")
    with tab_cenarios:
        _show_figure(construir_figura_cenarios(output), "Sem cenários determinísticos para exibir.")
        monte_carlo = construir_figura_monte_carlo(output)
        if int(output.get("modelo", {}).get("numero_simulacoes", 0)) == 0:
            st.info("Monte Carlo não foi executado neste cálculo.")
        else:
            _show_figure(monte_carlo, "Sem resultados Monte Carlo para exibir.")
