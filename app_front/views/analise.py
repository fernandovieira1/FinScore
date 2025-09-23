# app_front/views/analise.py
# coding: utf-8
import unicodedata
import math
from typing import Any, Dict, Optional

import streamlit as st

from components.llm_client import call_review_llm
from components.schemas import ReviewSchema

# imports RELATIVOS (arquivos no MESMO pacote 'views')
try:
    from .resumo import render as render_resumo
except Exception as e:
    def render_resumo():
        st.error(f"Nao foi possivel importar 'resumo.py' (render). Detalhe: {e}")

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



def _summarize_metrics(
    df,
    columns: list[str],
    rename: Optional[Dict[str, str]] = None,
    divisors: Optional[Dict[str, float] | float] = None,
) -> Dict[str, Any]:
    rename = rename or {}
    summary: Dict[str, Any] = {}
    row = _latest_row_dict(df)
    if not row:
        return summary
    for col in columns:
        if col not in row:
            continue
        divisor = 1.0
        if isinstance(divisors, dict):
            divisor = divisors.get(col, 1.0)
        elif isinstance(divisors, (int, float)) and divisors:
            divisor = float(divisors)
        summary[rename.get(col, col)] = _format_metric(row[col], divisor)
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
        "finscore": out.get("finscore_ajustado"),
        "serasa": out.get("serasa"),
        "rating": out.get("classificacao_finscore"),
    }
    if extra:
        ctx.update(extra)
    return {k: v for k, v in ctx.items() if v is not None}



def _artifact_box(artifact_id: str, title: str, mini_ctx: Dict[str, Any], dados_resumo: Dict[str, Any]):
    ss = st.session_state
    meta = ss.setdefault("artifacts_meta", {})
    reviews = ss.setdefault("reviews", {})
    meta[artifact_id] = {
        "title": title,
        "mini_ctx": dict(mini_ctx),
        "dados_resumo": dict(dados_resumo),
    }
    st.markdown(f"#### 💬 Critica da IA — {title}")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("Gerar critica da IA", key=f"btn_{artifact_id}"):
            review: ReviewSchema = call_review_llm(title, mini_ctx, dados_resumo)
            reviews[artifact_id] = review.model_dump()
            st.experimental_rerun()
    with col_b:
        if artifact_id in reviews:
            rev = reviews[artifact_id]
            st.json({k: v for k, v in rev.items() if k != "status"})
            c1, c2, c3 = st.columns(3)
            if c1.button("Aceitar", key=f"ok_{artifact_id}"):
                rev["status"] = "accepted"
                st.experimental_rerun()
            if c2.button("Revisar", key=f"rev_{artifact_id}"):
                rev["status"] = "needs_revision"
                st.experimental_rerun()
            if c3.button("Descartar", key=f"del_{artifact_id}"):
                del reviews[artifact_id]
                st.experimental_rerun()
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
    st.markdown("### - Passivos")
    if not _try_call_plot(df, ["render_passivos", "render_passivo_total", "render_contas_a_pagar"]):
        _todo_placeholder("Passivos")
    st.markdown("### - Patrimonio Liquido")
    if not _try_call_plot(df, ["render_pl", "render_patrimonio_liquido"]):
        _todo_placeholder("Patrimonio Liquido")
    st.markdown("### - Capital de Giro e Liquidez")
    capital_rendered = render_ativo_passivo_circulante(df)
    if not capital_rendered:
        capital_rendered = _try_call_plot(df, ["render_capital_giro", "render_liquidez_corrente"])
    if not capital_rendered:
        _todo_placeholder("Capital de Giro e Liquidez")

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
        )
    st.markdown("### - Tributos")
    if not _try_call_plot(df, ["render_impostos", "render_despesa_impostos"]):
        _todo_placeholder("Tributos")
    st.markdown("### - Resultado")
    if not _try_call_plot(df, ["render_lucro_liquido", "render_resultado_liquido"]):
        _todo_placeholder("Resultado")

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
        )
    st.markdown("### - Rentabilidade")
    if not _try_call_plot(df, ["render_rentabilidade_indices"]):
        _todo_placeholder("Rentabilidade")
    st.markdown("### - Eficiencia Operacional / Ciclo")
    if not _try_call_plot(df, ["render_eficiencia_indices"]):
        _todo_placeholder("Eficiencia Operacional / Ciclo")

    st.divider()

    st.header("3. PCA")
    st.markdown("### - Cargas (loadings)")
    if not _try_call_plot(df, ["render_pca_loadings"]):
        _todo_placeholder("Cargas (loadings)")
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
        )
    st.markdown("### - Projecoes (scores) por periodo/empresa")
    if not _try_call_plot(df, ["render_pca_scores"]):
        _todo_placeholder("Projecoes (scores) por periodo/empresa")

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
    st.markdown("### - Passivos")
    if not _try_show_table(["table_passivos", "get_passivos_table"]):
        _todo_placeholder("Passivos")
    st.markdown("### - Patrimonio Liquido")
    if not _try_show_table(["table_pl", "get_pl_table", "get_patrimonio_liquido_table"]):
        _todo_placeholder("Patrimonio Liquido")
    st.markdown("### - Capital de Giro / Liquidez")
    if not _try_show_table(["table_capital_giro", "get_ccl_table", "get_liquidez_table"]):
        _todo_placeholder("Capital de Giro / Liquidez")

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
    st.markdown("### - Financeiro")
    if not _try_show_table(["table_financeiro", "get_financeiro_table", "get_despesa_juros_table"]):
        _todo_placeholder("Financeiro")
    st.markdown("### - Tributos")
    if not _try_show_table(["table_impostos", "get_impostos_table", "get_despesa_impostos_table"]):
        _todo_placeholder("Tributos")
    st.markdown("### - Resultado")
    if not _try_show_table(["table_resultado", "get_resultado_liquido_table", "get_lucro_liquido_table"]):
        _todo_placeholder("Resultado")

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
        )
    st.markdown("### - Rentabilidade")
    if not _try_show_table(["table_rentabilidade_indices"]):
        _todo_placeholder("Rentabilidade")
    st.markdown("### - Eficiencia Operacional / Ciclo")
    if not _try_show_table(["table_eficiencia_indices"]):
        _todo_placeholder("Eficiencia Operacional / Ciclo")

    st.divider()

    st.header("3. PCA")
    st.markdown("### - Cargas (loadings)")
    if not _try_show_table(["get_pca_loadings_table"]):
        _todo_placeholder("Cargas (loadings)")

    st.markdown("### - Variancia explicada (explained variance)")
    if not _try_show_table(["get_pca_variance_table"]):
        _todo_placeholder("Variancia explicada (explained variance)")

    st.markdown("### - Projecoes (scores) por periodo/empresa")
    if not _try_show_table(["get_pca_scores_table"]):
        _todo_placeholder("Projecoes (scores) por periodo/empresa")

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
        )




def render():
    ss = st.session_state
    ss.setdefault("analise_tab", "Resumo")
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

    tab_resumo, tab_graficos, tab_tabelas = st.tabs(["Resumo", "Gráficos", "Tabelas"])

    with tab_resumo:
        render_resumo()
    with tab_graficos:
        _render_graficos_tab_content()
    with tab_tabelas:
        _render_tabelas_tab_content()

