# app_front/views/analise.py
# coding: utf-8
import unicodedata
import math
import statistics
from typing import Any, Dict, Optional

import streamlit as st

from components.llm_client import call_review_llm
from components.schemas import ReviewSchema
from components.state_manager import AppState
from components.config import SLUG_MAP

# imports RELATIVOS (arquivos no MESMO pacote 'views')
try:
    from .scores import render as render_scores
except Exception as e:
    def render_scores():
        st.error(f"Nao foi possivel importar 'scores.py' (render). Detalhe: {e}")

try:
    from .graficos import (
        prepare_base_data as prepare_graficos_data,
        render_ativo_passivo_circulante,
        render_receita_total,
        render_juros_lucro_receita,
    )
except Exception as e:
    def prepare_graficos_data():
        st.error(f"Nao foi possivel importar 'graficos.py'. Detalhe: {e}")
        return None

    def render_ativo_passivo_circulante(_df):
        st.error("Nao foi possivel preparar o grafico de Ativo e Passivo Circulante.")
        return False

    def render_receita_total(_df):
        st.error("Nao foi possivel preparar o grafico de Receita Total.")
        return False

    def render_juros_lucro_receita(_df):
        st.error("Nao foi possivel preparar o grafico de Juros, Lucro e Receita Total.")
        return False

try:
    from .tabelas import (
        get_indices_table,
        get_pca_scores_table,
        get_top_indices_table,
        get_pca_loadings_table,
    )
except Exception as e:
    def get_indices_table():
        st.error(f"Nao foi possivel importar 'tabelas.py'. Detalhe: {e}")
        return None

    def get_pca_scores_table():
        st.error("Nao foi possivel preparar a tabela de scores de PCA.")
        return None

    def get_top_indices_table():
        st.error("Nao foi possivel preparar a tabela de destaques do PCA.")
        return None

    def get_pca_loadings_table():
        st.error("Nao foi possivel preparar a tabela de loadings do PCA.")
        return None


try:
    from . import graficos as _graficos_module
except Exception:
    _graficos_module = None

try:
    from . import tabelas as _tabelas_module
except Exception:
    _tabelas_module = None


def _emit_captions(captions):
    shown = set()
    for text in captions:
        if isinstance(text, str) and text and text not in shown:
            st.caption(text)
            shown.add(text)


def _process_plot_result(result) -> bool:
    captions = []
    success = False

    def _handle(value):
        nonlocal success
        if value is None:
            success = True
            return
        if isinstance(value, bool):
            success = success or value
            return
        if isinstance(value, str):
            captions.append(value)
            success = True
            return
        if isinstance(value, dict):
            caption = value.get("caption")
            if isinstance(caption, str):
                captions.append(caption)
            if "rendered" in value:
                _handle(value["rendered"])
            if "success" in value:
                _handle(value["success"])
            if all(key not in value for key in ("rendered", "success")):
                success = True
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                _handle(item)
            return
        success = True

    _handle(result)
    _emit_captions(captions)
    return success


def _process_table_result(result) -> bool:
    captions = []
    rendered = False

    def _handle(value):
        nonlocal rendered
        if value is None:
            return
        if isinstance(value, bool):
            rendered = rendered or value
            return
        if isinstance(value, str):
            captions.append(value)
            return
        if isinstance(value, dict):
            caption = value.get("caption")
            if isinstance(caption, str):
                captions.append(caption)
            for key in ("df", "dataframe", "data", "table"):
                if key in value:
                    _handle(value[key])
            if "rendered" in value:
                _handle(value["rendered"])
            if "success" in value:
                _handle(value["success"])
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                _handle(item)
            return
        if hasattr(value, "empty") and hasattr(value, "columns"):
            if not getattr(value, "empty", False):
                st.dataframe(value, use_container_width=True, hide_index=True)
                rendered = True
            return
        rendered = True

    _handle(result)
    _emit_captions(captions)
    return rendered


def _try_call_plot(df, name_list) -> bool:
    if df is None or not name_list or _graficos_module is None:
        return False
    for name in name_list:
        func = getattr(_graficos_module, name, None)
        if not callable(func):
            continue
        try:
            result = func(df)
        except Exception as exc:  # noqa: PERF203 - user feedback prioritizado
            st.warning(f"Falha ao renderizar grafico '{name}': {exc}")
            continue
        if _process_plot_result(result):
            return True
    return False


def _try_show_table(name_list) -> bool:
    if not name_list or _tabelas_module is None:
        return False
    for name in name_list:
        func = getattr(_tabelas_module, name, None)
        if not callable(func):
            continue
        try:
            result = func()
        except Exception as exc:  # noqa: PERF203 - user feedback prioritizado
            st.warning(f"Falha ao carregar tabela '{name}': {exc}")
            continue
        if _process_table_result(result):
            return True
    return False


def _todo_placeholder(nome: str):
    st.info(f"TODO: inserir gráfico/tabela desta subseção ({nome})")


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


def _split_indices_columns(df) -> dict:
    categories = {
        "Liquidez": [],
        "Endividamento/Estrutura": [],
        "Rentabilidade": [],
        "Eficiência Operacional / Ciclo": [],
    }
    for col in df.columns:
        if col == "Ano":
            continue
        label = _normalize_label(str(col))
        if "liquidez" in label or "ccl" in label:
            categories["Liquidez"].append(col)
        elif "endivid" in label or "alavanc" in label or "imobilizado" in label:
            categories["Endividamento/Estrutura"].append(col)
        elif "margem" in label or "roa" in label or "roe" in label or "ebitda" in label or "lucro" in label:
            categories["Rentabilidade"].append(col)
        elif "giro" in label or "periodo" in label or "cobertura" in label or "ciclo" in label:
            categories["Eficiência Operacional / Ciclo"].append(col)
    return categories




def _to_float(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number



def _format_metric(value: Any, divisor: float = 1.0) -> Any:
    number = _to_float(value)
    if number is None:
        return value
    if not divisor:
        divisor = 1.0
    scaled = number / divisor
    return round(scaled, 2)



def _latest_row_dict(df) -> Optional[Dict[str, Any]]:
    if df is None:
        return None
    if getattr(df, "empty", False):
        return None
    try:
        if "ano" in df.columns:
            data = df.sort_values("ano", ascending=True)
            row = data.iloc[-1]
        elif "Ano" in df.columns:
            data = df.sort_values("Ano", ascending=True)
            row = data.iloc[-1]
        else:
            row = df.iloc[0]
    except Exception:
        try:
            row = df.iloc[0]
        except Exception:
            return None
    to_dict = getattr(row, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return dict(row)





def _series_points(df, column: str) -> list[tuple[Any, float]]:
    if df is None or getattr(df, "empty", False):
        return []
    points: list[tuple[Any, float]] = []
    for _, row in df.iterrows():
        raw_value = row.get(column)
        value = _to_float(raw_value)
        if value is None:
            continue
        year = row.get("Ano") or row.get("ano") or row.get("ano_label")
        if isinstance(year, str):
            digits = ''.join(ch for ch in year if ch.isdigit())
            year = int(digits) if digits else year.strip() or None
        points.append((year, value))
    return points


def _infer_numeric_columns(df, limit: int = 4) -> list[str]:
    if df is None or getattr(df, "empty", False):
        return []
    columns: list[str] = []
    for col in df.columns:
        col_lower = str(col).lower()
        if col_lower in {"ano", "ano_label", "periodo"}:
            continue
        values = []
        for value in df[col]:
            converted = _to_float(value)
            if converted is not None:
                values.append(converted)
        if values:
            columns.append(col)
        if len(columns) >= limit:
            break
    return columns


def _summarize_metrics(
    df,
    columns: list[str],
    rename: Optional[Dict[str, str]] = None,
    divisors: Optional[Dict[str, float] | float] = None,
) -> Dict[str, Any]:
    rename = rename or {}
    summary: Dict[str, Any] = {}
    if df is None or getattr(df, "empty", False):
        return summary
    if not columns:
        return summary

    for col in columns:
        points = _series_points(df, col)
        if not points:
            continue
        divisor = 1.0
        if isinstance(divisors, dict):
            divisor = divisors.get(col, 1.0)
        elif isinstance(divisors, (int, float)) and divisors:
            divisor = float(divisors)
        label = rename.get(col, col)
        series_data: Dict[str, Any] = {}
        for idx, (year, value) in enumerate(points):
            key = str(year if year is not None else idx)
            series_data[key] = _format_metric(value, divisor)

        values_raw = [value for _, value in points]
        latest = values_raw[-1]
        first = values_raw[0]
        mean_value = statistics.fmean(values_raw)
        variation = latest - first
        percentual = 0.0
        if first != 0:
            percentual = (variation / abs(first)) * 100.0

        trend = "estavel"
        if percentual > 5:
            trend = "alta"
        elif percentual < -5:
            trend = "queda"

        try:
            scaled_values = [value / divisor for value in values_raw]
        except Exception:
            scaled_values = values_raw
        min_scaled = min(scaled_values) if scaled_values else 0.0
        max_scaled = max(scaled_values) if scaled_values else 0.0
        amplitude_scaled = max_scaled - min_scaled
        if len(scaled_values) >= 2:
            std_dev_scaled = statistics.pstdev(scaled_values)
            variance_scaled = statistics.pvariance(scaled_values)
        else:
            std_dev_scaled = 0.0
            variance_scaled = 0.0

        stats_block = {
            "media": round(statistics.fmean(scaled_values), 2) if scaled_values else None,
            "min": round(min_scaled, 2) if scaled_values else None,
            "max": round(max_scaled, 2) if scaled_values else None,
            "amplitude": round(amplitude_scaled, 2) if scaled_values else None,
            "desvio_padrao": round(std_dev_scaled, 2),
            "variancia": round(variance_scaled, 4),
        }

        summary[label] = {
            "serie": series_data,
            "ultimo": _format_metric(latest, divisor),
            "media": _format_metric(mean_value, divisor),
            "variacao_absoluta": _format_metric(variation, divisor),
            "variacao_percentual": round(percentual, 2),
            "tendencia": trend,
            "anos": [p[0] for p in points if p[0] is not None],
            "estatisticas": stats_block,
        }
    return summary


def _compute_ebitda_snapshot(row: Dict[str, Any]) -> Optional[float]:
    if not row:
        return None
    lucro = _to_float(row.get("r_Lucro_Liquido"))
    juros = _to_float(row.get("r_Despesa_de_Juros"))
    impostos = _to_float(row.get("r_Despesa_de_Impostos"))
    if lucro is None or juros is None or impostos is None:
        return None
    amort = _to_float(row.get("r_Amortizacao")) or 0.0
    depreciacao = _to_float(row.get("r_Depreciacao")) or 0.0
    return lucro + juros + impostos + amort + depreciacao


def _build_mini_context(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ss = st.session_state
    out = ss.get("out") or {}
    meta = ss.get("meta") or {}
    ctx = {
        "empresa": meta.get("empresa"),
    }
    # Inclui anos disponíveis quando presentes para dar contexto temporal básico
    df_state = ss.get("df")
    if df_state is not None and getattr(df_state, "empty", False) is False and "ano" in df_state.columns:
        try:
            anos = sorted(set(int(a) for a in df_state["ano"].dropna()))
            if anos:
                ctx["anos_disponiveis"] = anos
        except Exception:
            pass
    else:
        df_raw = out.get("df_raw")
        if df_raw is not None and getattr(df_raw, "empty", False) is False and "ano" in getattr(df_raw, "columns", []):
            try:
                anos = sorted(set(int(a) for a in df_raw["ano"].dropna()))
                if anos:
                    ctx["anos_disponiveis"] = anos
            except Exception:
                pass
    if extra:
        ctx.update(extra)
    return {k: v for k, v in ctx.items() if v is not None}







def _filter_existing_columns(df, columns: list[str]) -> list[str]:
    if df is None or getattr(df, "empty", False):
        return []
    return [col for col in columns if col in df.columns]


def _build_tax_summary(df) -> Dict[str, Any]:
    columns = _filter_existing_columns(df, ["r_Despesa_de_Impostos", "r_Receita_Total"])
    summary = _summarize_metrics(
        df,
        columns,
        rename={
            "r_Despesa_de_Impostos": "Despesa de Impostos (mi)",
            "r_Receita_Total": "Receita (mi)",
        },
        divisors={
            "r_Despesa_de_Impostos": 1_000_000,
            "r_Receita_Total": 1_000_000,
        },
    )
    row = _latest_row_dict(df)
    impostos = _to_float(row.get("r_Despesa_de_Impostos")) if row else None
    receita = _to_float(row.get("r_Receita_Total")) if row else None
    if receita not in (None, 0) and impostos is not None:
        summary["Carga Tributaria (%)"] = round((impostos / receita) * 100, 2)
    if not summary:
        summary = {"nota": "Despesa de impostos e efetividade tributaria"}
    else:
        summary.setdefault("nota", "Despesa de impostos e efetividade tributaria")
    return summary


def _build_profit_summary(df) -> Dict[str, Any]:
    columns = _filter_existing_columns(df, ["r_Lucro_Liquido", "r_Receita_Total"])
    summary = _summarize_metrics(
        df,
        columns,
        rename={
            "r_Lucro_Liquido": "Lucro Liquido (mi)",
            "r_Receita_Total": "Receita (mi)",
        },
        divisors={
            "r_Lucro_Liquido": 1_000_000,
            "r_Receita_Total": 1_000_000,
        },
    )
    row = _latest_row_dict(df)
    lucro = _to_float(row.get("r_Lucro_Liquido")) if row else None
    receita = _to_float(row.get("r_Receita_Total")) if row else None
    if receita not in (None, 0) and lucro is not None:
        summary["Margem Liquida (%)"] = round((lucro / receita) * 100, 2)
    if not summary:
        summary = {"nota": "Desempenho do lucro liquido"}
    else:
        summary.setdefault("nota", "Desempenho do lucro liquido")
    return summary


def _collect_indices_summary(indices_df, category: str, note: str) -> Dict[str, Any]:
    if indices_df is None or getattr(indices_df, "empty", False):
        return {"nota": note}
    categories = _split_indices_columns(indices_df)
    columns = categories.get(category)
    if columns is None:
        target = _normalize_label(category)
        for key, values in categories.items():
            if _normalize_label(str(key)) == target:
                columns = values
                break
    if columns is None:
        columns = []
    summary = _summarize_metrics(indices_df, columns)
    if not summary:
        summary = {"nota": note}
    else:
        summary.setdefault("nota", note)
    return summary


def _build_pca_loadings_summary(loadings_df, top_components: int = 3, top_variables: int = 3) -> Dict[str, Any]:
    if loadings_df is None or getattr(loadings_df, "empty", False):
        return {}
    summary: Dict[str, Any] = {}
    try:
        components = list(loadings_df.columns)
    except Exception:
        return summary
    for comp in components[:top_components]:
        try:
            series = loadings_df[comp].abs().sort_values(ascending=False)
        except Exception:
            continue
        entries = []
        for variable in series.index[:top_variables]:
            try:
                raw_value = loadings_df.loc[variable, comp]
                value = _to_float(raw_value)
            except Exception:
                value = None
            entries.append({
                "variavel": str(variable),
                "peso": round(value, 3) if value is not None else value,
            })
        summary[str(comp)] = {"principais": entries}
    if summary:
        summary.setdefault("nota", "Variaveis com maior carga absoluta por componente")
    return summary


def _build_pca_scores_summary(scores_df, max_components: int = 3) -> Dict[str, Any]:
    if scores_df is None or getattr(scores_df, "empty", False):
        return {}
    columns = [col for col in scores_df.columns if str(col).upper().startswith("PC")]
    if not columns:
        return {}
    summary = _summarize_metrics(scores_df, columns[:max_components])
    if summary:
        summary.setdefault("nota", "Scores por componente principal")
    return summary

def _unwrap_table_dataframe(value):
    if value is None:
        return None
    if hasattr(value, "empty") and hasattr(value, "columns"):
        if getattr(value, "empty", False):
            return None
        return value
    if isinstance(value, dict):
        for key in ("df", "dataframe", "data", "table"):
            if key in value:
                df = _unwrap_table_dataframe(value.get(key))
                if df is not None:
                    return df
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            df = _unwrap_table_dataframe(item)
            if df is not None:
                return df
    return None


def _get_table_dataframe(name_list) -> Optional[Any]:
    if not name_list or _tabelas_module is None:
        return None
    for name in name_list:
        func = getattr(_tabelas_module, name, None)
        if not callable(func):
            continue
        try:
            result = func()
        except Exception:
            continue
        df = _unwrap_table_dataframe(result)
        if df is not None:
            return df
    return None


def _register_table_section(
    artifact_id: str,
    title: str,
    name_list,
    note: Optional[str] = None,
    column_filter: Optional[Any] = None,
    rename: Optional[Dict[str, str]] = None,
):
    table_df = _get_table_dataframe(name_list)
    if table_df is None:
        return
    if callable(column_filter):
        columns = column_filter(table_df)
    elif isinstance(column_filter, (list, tuple)):
        columns = list(column_filter)
    else:
        columns = [col for col in table_df.columns if str(col).lower() not in {"ano", "periodo"}]
    if not columns:
        columns = _infer_numeric_columns(table_df)
    _register_artifact(
        artifact_id,
        title,
        df=table_df,
        columns=columns,
        rename=rename,
        note=note or title,
    )


def _register_artifact(
    artifact_id: str,
    title: str,
    df=None,
    columns: Optional[list[str]] = None,
    rename: Optional[Dict[str, str]] = None,
    divisors: Optional[Dict[str, float] | float] = None,
    note: Optional[str] = None,
    extra_ctx: Optional[Dict[str, Any]] = None,
    summary_override: Optional[Dict[str, Any]] = None,
    review_kind: Optional[str] = None,
) -> None:
    summary: Dict[str, Any] = summary_override.copy() if summary_override else {}
    if not summary and df is not None:
        target_columns = columns or _infer_numeric_columns(df)
        summary = _summarize_metrics(df, target_columns, rename=rename, divisors=divisors)
    if not summary:
        summary = {"nota": note or title}
    else:
        summary.setdefault("nota", note or title or title)
    mini_ctx = _build_mini_context(extra_ctx)
    lowered_id = artifact_id.lower()
    if review_kind is None:
        if "indice" in lowered_id or "pca" in lowered_id:
            review_kind = "indices"
        else:
            review_kind = "raw"
    _artifact_box(artifact_id, title, mini_ctx, summary, review_kind)


def _artifact_box(
    artifact_id: str,
    title: str,
    mini_ctx: Dict[str, Any],
    dados_resumo: Dict[str, Any],
    review_kind: str,
) -> None:
    ss = st.session_state
    meta = ss.setdefault("artifacts_meta", {})
    reviews = ss.setdefault("reviews", {})
    meta[artifact_id] = {
        "title": title,
        "mini_ctx": dict(mini_ctx),
        "dados_resumo": dict(dados_resumo),
        "review_kind": review_kind,
        "artifact_id": artifact_id,
    }
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("Gerar critica da IA", key=f"btn_{artifact_id}"):
            with st.spinner("Gerando critica da IA..."):
                artifact_meta = meta[artifact_id]
                review: ReviewSchema = call_review_llm(artifact_id, artifact_meta)
            reviews[artifact_id] = review.model_dump()
            AppState.set_current_page(
                SLUG_MAP.get("analise", "Análise"),
                "analise_artifact",
                slug="analise",
            )
            AppState.sync_to_query_params()
            st.success("Critica gerada com sucesso.")
    with col_b:
        if artifact_id in reviews:
            rev = reviews[artifact_id]
            st.json({k: v for k, v in rev.items() if k != "status"})
            c1, c2, c3 = st.columns(3)
            if c1.button("Aceitar", key=f"ok_{artifact_id}"):
                rev["status"] = "accepted"
                st.rerun()
            if c2.button("Revisar", key=f"rev_{artifact_id}"):
                rev["status"] = "needs_revision"
                st.rerun()
            if c3.button("Descartar", key=f"del_{artifact_id}"):
                del reviews[artifact_id]
                st.rerun()
            note_key = f"obs_{artifact_id}"
            obs_value = st.text_area(
                "Observacao do analista",
                value=rev.get("obs", ""),
                key=note_key,
            )
            reviews[artifact_id]["obs"] = obs_value


def _render_graficos_tab_content():
    df = prepare_graficos_data()
    if df is None:
        st.info("Carregue os dados em **Novo -> Dados** para visualizar os graficos.")
        return

    ss = st.session_state
    out = ss.get("out") or {}
    indices_df = out.get("df_indices")
    row = _latest_row_dict(df)

    st.header("1. Dados Contabeis (brutos)")
    st.subheader("1.1 Contas Patrimoniais (Balanco Patrimonial)")
    st.markdown("### - Ativos")
    if not _try_call_plot(
        df,
        [
            "render_ativos",
            "render_ativos_grafico",
            "render_ativo_total",
            "render_estoques",
            "render_contas_a_receber",
        ],
    ):
        _todo_placeholder("Ativos")
    else:
        _register_artifact(
            "grafico_ativos",
            "Grafico - Ativos",
            df=df,
            columns=[
                "p_Ativo_Circulante",
                "p_Ativo_Total",
                "p_Caixa",
                "p_Estoques",
                "p_Contas_a_Receber",
            ],
            divisors={
                "p_Ativo_Circulante": 1_000_000,
                "p_Ativo_Total": 1_000_000,
                "p_Caixa": 1_000_000,
                "p_Estoques": 1_000_000,
                "p_Contas_a_Receber": 1_000_000,
            },
            note="Evolucao dos ativos (R$ mi)",
        )
    st.markdown("### - Passivos")
    if not _try_call_plot(df, ["render_passivos", "render_passivo_total", "render_contas_a_pagar"]):
        _todo_placeholder("Passivos")
    else:
        _register_artifact(
            "grafico_passivos",
            "Grafico - Passivos",
            df=df,
            columns=["p_Contas_a_Pagar", "p_Passivo_Circulante", "p_Passivo_Total"],
            divisors={
                "p_Contas_a_Pagar": 1_000_000,
                "p_Passivo_Circulante": 1_000_000,
                "p_Passivo_Total": 1_000_000,
            },
            note="Evolucao dos passivos (R$ mi)",
        )
    st.markdown("### - Patrimonio Liquido")
    if not _try_call_plot(df, ["render_pl", "render_patrimonio_liquido"]):
        _todo_placeholder("Patrimonio Liquido")
    else:
        _register_artifact(
            "grafico_patrimonio_liquido",
            "Grafico - Patrimonio Liquido",
            df=df,
            columns=["p_Patrimonio_Liquido"],
            divisors={"p_Patrimonio_Liquido": 1_000_000},
            note="Patrimonio liquido em R$ mi",
        )
    st.markdown("### - Capital de Giro e Liquidez")
    capital_rendered = render_ativo_passivo_circulante(df)
    if not capital_rendered:
        capital_rendered = _try_call_plot(df, ["render_capital_giro", "render_liquidez_corrente"])
    if not capital_rendered:
        _todo_placeholder("Capital de Giro e Liquidez")
    else:
        _register_artifact(
            "grafico_capital_giro",
            "Grafico - Capital de Giro e Liquidez",
            df=df,
            columns=["p_Ativo_Circulante", "p_Passivo_Circulante", "p_Estoques", "p_Ativo_Total"],
            divisors={
                "p_Ativo_Circulante": 1_000_000,
                "p_Passivo_Circulante": 1_000_000,
                "p_Estoques": 1_000_000,
                "p_Ativo_Total": 1_000_000,
            },
            note="Capital de giro e liquidez (R$ mi)",
        )

    st.divider()

    st.subheader("1.2 Contas de Resultado (DRE)")
    st.markdown("### - Operacional")
    operacional_rendered = render_receita_total(df)
    if _try_call_plot(df, ["render_custos", "render_depreciacao", "render_amortizacao"]):
        operacional_rendered = True
    if not operacional_rendered:
        _todo_placeholder("Operacional")
    else:
        dados_resumo = _summarize_metrics(
            df,
            ["r_Receita_Total", "r_Custos", "r_Lucro_Liquido"],
            rename={
                "r_Receita_Total": "Receita (mi)",
                "r_Custos": "Custos (mi)",
                "r_Lucro_Liquido": "Lucro (mi)",
            },
            divisors={
                "r_Receita_Total": 1_000_000,
                "r_Custos": 1_000_000,
                "r_Lucro_Liquido": 1_000_000,
            },
        )
        ebitda = _compute_ebitda_snapshot(row)
        if ebitda is not None:
            dados_resumo["EBITDA (mi)"] = _format_metric(ebitda, 1_000_000)
        dados_resumo.setdefault("nota", "Receita, Custos e EBITDA em R$ mi")
        _artifact_box(
            "grafico_receita_total",
            "Receita, Custos e EBITDA",
            _build_mini_context(),
            dados_resumo,
            "raw",
        )
    st.markdown("### - Financeiro")
    financeiro_rendered = render_juros_lucro_receita(df)
    if not financeiro_rendered:
        financeiro_rendered = _try_call_plot(df, ["render_despesa_juros"])
    if not financeiro_rendered:
        _todo_placeholder("Financeiro")
    else:
        row = _latest_row_dict(df)
        dados_resumo = _summarize_metrics(
            df,
            ["r_Despesa_de_Juros", "r_Lucro_Liquido", "r_Receita_Total"],
            rename={
                "r_Despesa_de_Juros": "Juros (mi)",
                "r_Lucro_Liquido": "Lucro (mi)",
                "r_Receita_Total": "Receita (mi)",
            },
            divisors={
                "r_Despesa_de_Juros": 1_000_000,
                "r_Lucro_Liquido": 1_000_000,
                "r_Receita_Total": 1_000_000,
            },
        )
        indices_row = _latest_row_dict(indices_df)
        cobertura = _to_float(indices_row.get("Cobertura de Juros")) if indices_row else None
        if cobertura is not None:
            dados_resumo["Cobertura (x)"] = round(cobertura, 2)
        dados_resumo.setdefault("nota", "Fluxo financeiro e cobertura")
        _artifact_box(
            "grafico_financeiro",
            "Fluxo Financeiro e Cobertura",
            _build_mini_context(),
            dados_resumo,
            "raw",
        )
    st.markdown("### - Tributos")
    impostos_rendered = _try_call_plot(df, ["render_impostos", "render_despesa_impostos"])
    if not impostos_rendered:
        _todo_placeholder("Tributos")
    else:
        dados_resumo = _build_tax_summary(df)
        _artifact_box(
            "grafico_impostos",
            "Despesa de Impostos e Efetividade Tributaria",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Resultado")
    resultado_rendered = _try_call_plot(df, ["render_lucro_liquido", "render_resultado_liquido"])
    if not resultado_rendered:
        _todo_placeholder("Resultado")
    else:
        dados_resumo = _build_profit_summary(df)
        _artifact_box(
            "grafico_lucro_liquido",
            "Lucro Liquido",
            _build_mini_context(),
            dados_resumo,
            "raw",
        )

    st.divider()

    st.header("2. Indices Contabeis")
    st.markdown("### - Liquidez")
    liquidez_rendered = _try_call_plot(df, ["render_liquidez_indices"])
    if not liquidez_rendered:
        _todo_placeholder("Liquidez")
    else:
        dados_resumo = _summarize_metrics(
            indices_df,
            ["Liquidez Corrente", "Liquidez Seca", "CCL/Ativo Total"],
            rename={
                "Liquidez Corrente": "Liquidez Corrente (x)",
                "Liquidez Seca": "Liquidez Seca (x)",
                "CCL/Ativo Total": "CCL/Ativo (x)",
            },
        )
        dados_resumo.setdefault("nota", "Indicadores de liquidez (vezes)")
        _artifact_box(
            "grafico_liquidez_indices",
            "Indicadores de Liquidez",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Endividamento/Estrutura")
    endividamento_rendered = _try_call_plot(df, ["render_endividamento_indices"])
    if not endividamento_rendered:
        _todo_placeholder("Endividamento/Estrutura")
    else:
        dados_resumo = _summarize_metrics(
            indices_df,
            ["Alavancagem", "Endividamento", "Cobertura de Juros"],
            rename={
                "Alavancagem": "DL/EBITDA (x)",
                "Endividamento": "Divida/Ativo (x)",
                "Cobertura de Juros": "Cobertura de Juros (x)",
            },
        )
        dados_resumo.setdefault("nota", "Estrutura de capital (vezes)")
        _artifact_box(
            "grafico_endividamento_indices",
            "Estrutura de Capital e Alavancagem",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Rentabilidade")
    rentabilidade_rendered = _try_call_plot(df, ["render_rentabilidade_indices"])
    if not rentabilidade_rendered:
        _todo_placeholder("Rentabilidade")
    else:
        dados_resumo = _collect_indices_summary(indices_df, "Rentabilidade", "Indicadores de rentabilidade")
        _artifact_box(
            "grafico_rentabilidade_indices",
            "Indicadores de Rentabilidade",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Eficiencia Operacional / Ciclo")
    eficiencia_rendered = _try_call_plot(df, ["render_eficiencia_indices"])
    if not eficiencia_rendered:
        _todo_placeholder("Eficiencia Operacional / Ciclo")
    else:
        dados_resumo = _collect_indices_summary(
            indices_df,
            "Eficiencia Operacional / Ciclo",
            "Indicadores de eficiencia operacional",
        )
        _artifact_box(
            "grafico_eficiencia_indices",
            "Eficiencia e Ciclo Operacional",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )

    st.divider()

    st.header("3. PCA")
    st.markdown("### - Cargas (loadings)")
    loadings_rendered = _try_call_plot(df, ["render_pca_loadings"])
    if not loadings_rendered:
        _todo_placeholder("Cargas (loadings)")
    else:
        loadings_df = (out or {}).get("loadings") if isinstance(out, dict) else None
        dados_resumo = _build_pca_loadings_summary(loadings_df)
        if not dados_resumo:
            dados_resumo = {"nota": "Resumo das cargas nao disponivel"}
        _artifact_box(
            "grafico_pca_loadings",
            "PCA - Cargas (Loadings)",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Variancia explicada (explained variance)")
    variancia_rendered = _try_call_plot(df, ["render_pca_variancia"])
    if not variancia_rendered:
        _todo_placeholder("Variancia explicada (explained variance)")
    else:
        variancias = out.get("pca_explained_variance") or []
        dados_resumo = {f"PC{i + 1}": round(valor * 100, 2) for i, valor in enumerate(variancias[:3])}
        dados_resumo.setdefault("nota", "Variancia explicada (%)")
        _artifact_box(
            "grafico_pca_variancia",
            "PCA - Variancia Explicada",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Projecoes (scores) por periodo/empresa")
    scores_rendered = _try_call_plot(df, ["render_pca_scores"])
    if not scores_rendered:
        _todo_placeholder("Projecoes (scores) por periodo/empresa")
    else:
        scores_df = (out or {}).get("df_pca") if isinstance(out, dict) else None
        dados_resumo = _build_pca_scores_summary(scores_df)
        if not dados_resumo:
            dados_resumo = {"nota": "Resumo dos scores nao disponivel"}
        _artifact_box(
            "grafico_pca_scores",
            "PCA - Projecoes (Scores)",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )

def _render_indices_tables(df):
    categories = _split_indices_columns(df)
    for label, columns in categories.items():
        st.markdown(f"### • {label}")
        available = [col for col in columns if col in df.columns]
        if not available:
            _todo_placeholder(label)
            continue
        subset_cols = available
        if "Ano" in df.columns:
            subset_cols = ["Ano"] + available
        st.dataframe(df[subset_cols], use_container_width=True, hide_index=True)



def _render_tabelas_tab_content():
    ss = st.session_state
    out = ss.get("out")
    if not out:
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        return

    indices_df = out.get("df_indices")
    top_indices_df = out.get("top_indices_df")

    st.header("Dados Contabeis (brutos)")
    st.subheader("1.1 Contas Patrimoniais (Balanco Patrimonial)")
    st.markdown("### - Ativos")
    if not _try_show_table(["table_ativos", "get_ativos_table"]):
        _todo_placeholder("Ativos")
    else:
        _register_table_section(
            "tabela_ativos",
            "Tabela - Ativos",
            ["table_ativos", "get_ativos_table"],
            note="Evolucao dos ativos (R$ mi) e variacao anual",
        )
    st.markdown("### - Passivos")
    if not _try_show_table(["table_passivos", "get_passivos_table"]):
        _todo_placeholder("Passivos")
    else:
        _register_table_section(
            "tabela_passivos",
            "Tabela - Passivos",
            ["table_passivos", "get_passivos_table"],
            note="Evolucao dos passivos (R$ mi) e variacao anual",
        )
    st.markdown("### - Patrimonio Liquido")
    if not _try_show_table(["table_pl", "get_pl_table", "get_patrimonio_liquido_table"]):
        _todo_placeholder("Patrimonio Liquido")
    else:
        _register_table_section(
            "tabela_pl",
            "Tabela - Patrimonio Liquido",
            ["table_pl", "get_pl_table", "get_patrimonio_liquido_table"],
            note="Patrimonio liquido e variacoes anuais",
        )
    st.markdown("### - Capital de Giro / Liquidez")
    if not _try_show_table(["table_capital_giro", "get_ccl_table", "get_liquidez_table"]):
        _todo_placeholder("Capital de Giro / Liquidez")
    else:
        _register_table_section(
            "tabela_capital_giro_base",
            "Tabela - Capital de Giro / Liquidez",
            ["table_capital_giro", "get_ccl_table", "get_liquidez_table"],
            note="Capital de giro, CCL e liquidez",
        )

    st.divider()

    st.subheader("1.2 Contas de Resultado (DRE)")
    st.markdown("### - Operacional")
    if not _try_show_table([
        "table_operacional",
        "get_operacional_table",
        "get_receita_table",
        "get_custos_table",
        "get_depreciacao_table",
        "get_amortizacao_table",
    ]):
        _todo_placeholder("Operacional")
    else:
        _register_table_section(
            "tabela_operacional",
            "Tabela - Operacional",
            [
                "table_operacional",
                "get_operacional_table",
                "get_receita_table",
                "get_custos_table",
                "get_depreciacao_table",
                "get_amortizacao_table",
            ],
            note="Receita, custos e itens operacionais",
        )
    st.markdown("### - Financeiro")
    if not _try_show_table(["table_financeiro", "get_financeiro_table", "get_despesa_juros_table"]):
        _todo_placeholder("Financeiro")
    else:
        _register_table_section(
            "tabela_financeiro",
            "Tabela - Financeiro",
            ["table_financeiro", "get_financeiro_table", "get_despesa_juros_table"],
            note="Fluxo financeiro e despesas de juros",
        )
    st.markdown("### - Tributos")
    if not _try_show_table(["table_impostos", "get_impostos_table", "get_despesa_impostos_table"]):
        _todo_placeholder("Tributos")
    else:
        _register_table_section(
            "tabela_tributos",
            "Tabela - Tributos",
            ["table_impostos", "get_impostos_table", "get_despesa_impostos_table"],
            note="Despesa de impostos e efetividade",
        )
    st.markdown("### - Resultado")
    if not _try_show_table(["table_resultado", "get_resultado_liquido_table", "get_lucro_liquido_table"]):
        _todo_placeholder("Resultado")
    else:
        _register_table_section(
            "tabela_resultado",
            "Tabela - Resultado",
            ["table_resultado", "get_resultado_liquido_table", "get_lucro_liquido_table"],
            note="Indicadores de resultado e lucro",
        )

    st.divider()

    st.header("2. Indices Contabeis")
    st.markdown("### - Liquidez")
    liquidez_table = _try_show_table(["table_liquidez_indices"])
    if not liquidez_table:
        _todo_placeholder("Liquidez")
    else:
        dados_resumo = _summarize_metrics(
            indices_df,
            ["Liquidez Corrente", "Liquidez Seca", "CCL/Ativo Total"],
            rename={
                "Liquidez Corrente": "Liquidez Corrente (x)",
                "Liquidez Seca": "Liquidez Seca (x)",
                "CCL/Ativo Total": "CCL/Ativo (x)",
            },
        )
        dados_resumo.setdefault("nota", "Tabela de liquidez (vezes)")
        _artifact_box(
            "tabela_liquidez_indices",
            "Tabela - Indicadores de Liquidez",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Endividamento/Estrutura")
    endividamento_table = _try_show_table(["table_endividamento_indices"])
    if not endividamento_table:
        _todo_placeholder("Endividamento/Estrutura")
    else:
        dados_resumo = _summarize_metrics(
            indices_df,
            ["Alavancagem", "Endividamento", "Cobertura de Juros"],
            rename={
                "Alavancagem": "DL/EBITDA (x)",
                "Endividamento": "Divida/Ativo (x)",
                "Cobertura de Juros": "Cobertura de Juros (x)",
            },
        )
        dados_resumo.setdefault("nota", "Tabela de estrutura de capital (vezes)")
        _artifact_box(
            "tabela_endividamento_indices",
            "Tabela - Estrutura de Capital",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Rentabilidade")
    rent_table = _try_show_table(["table_rentabilidade_indices"])
    if not rent_table:
        _todo_placeholder("Rentabilidade")
    else:
        dados_resumo = _collect_indices_summary(
            indices_df,
            "Rentabilidade",
            "Tabela de indicadores de rentabilidade",
        )
        _artifact_box(
            "tabela_rentabilidade_indices",
            "Tabela - Indicadores de Rentabilidade",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )
    st.markdown("### - Eficiencia Operacional / Ciclo")
    eficiencia_table = _try_show_table(["table_eficiencia_indices"])
    if not eficiencia_table:
        _todo_placeholder("Eficiencia Operacional / Ciclo")
    else:
        dados_resumo = _collect_indices_summary(
            indices_df,
            "Eficiencia Operacional / Ciclo",
            "Tabela de eficiencia operacional",
        )
        _artifact_box(
            "tabela_eficiencia_indices",
            "Tabela - Eficiencia Operacional",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )

    st.divider()

    st.header("3. PCA")
    st.markdown("### - Cargas (loadings)")
    pca_loadings_table = _try_show_table(["get_pca_loadings_table"])
    if not pca_loadings_table:
        _todo_placeholder("Cargas (loadings)")
    else:
        loadings_df = out.get("loadings") if isinstance(out, dict) else None
        dados_resumo = _build_pca_loadings_summary(loadings_df)
        if not dados_resumo:
            dados_resumo = {"nota": "Resumo das cargas nao disponivel"}
        _artifact_box(
            "tabela_pca_loadings",
            "Tabela - PCA Loadings",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )

    st.markdown("### - Variancia explicada (explained variance)")
    if not _try_show_table(["get_pca_variance_table"]):
        _todo_placeholder("Variancia explicada (explained variance)")

    st.markdown("### - Projecoes (scores) por periodo/empresa")
    pca_scores_table = _try_show_table(["get_pca_scores_table"])
    if not pca_scores_table:
        _todo_placeholder("Projecoes (scores) por periodo/empresa")
    else:
        scores_df = out.get("df_pca") if isinstance(out, dict) else None
        dados_resumo = _build_pca_scores_summary(scores_df)
        if not dados_resumo:
            dados_resumo = {"nota": "Resumo dos scores nao disponivel"}
        _artifact_box(
            "tabela_pca_scores",
            "Tabela - PCA Scores",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )

    st.markdown("### - Destaques de componentes (top indices)")
    top_table = _try_show_table(["get_top_indices_table"])
    if not top_table:
        _todo_placeholder("Destaques de componentes (top indices)")
    else:
        row = _latest_row_dict(top_indices_df)
        dados_resumo = {}
        if row:
            dados_resumo["PC"] = row.get("PC")
            for idx in range(1, 4):
                indice = row.get(f"Indice {idx}")
                peso = _to_float(row.get(f"Peso {idx}"))
                if indice:
                    dados_resumo[f"Indice {idx}"] = indice
                if peso is not None:
                    dados_resumo[f"Peso {idx}"] = round(peso, 3)
        dados_resumo.setdefault("nota", "Top indices por componente principal")
        _artifact_box(
            "tabela_top_indices",
            "Tabela - PCA Top Indices",
            _build_mini_context(),
            dados_resumo,
            "indices",
        )




def render():
    ss = st.session_state
    ss.setdefault("analise_tab", "Scores")
    ss.setdefault("reviews", {})
    ss.setdefault("artifacts_meta", {})

    # CSS para centralizar as abas
    st.markdown(
        """
        <style>
        div[data-testid="stTabs"] > div[role="tablist"],
        div[data-baseweb="tab-list"] {
            display: flex;
            justify-content: center;   /* centraliza as abas */
            gap: 2rem;                 /* espaco entre abas */
        }
        div[data-testid="stTabs"] button[role="tab"],
        div[data-baseweb="tab"] {
            flex: 0 0 auto;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab_scores, tab_graficos, tab_tabelas = st.tabs(["Scores", "Gráficos", "Tabelas"])

    with tab_scores:
        render_scores()
    with tab_graficos:
        _render_graficos_tab_content()
    with tab_tabelas:
        _render_tabelas_tab_content()

