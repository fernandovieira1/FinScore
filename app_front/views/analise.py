# app_front/views/analise.py
# coding: utf-8
import unicodedata
import streamlit as st

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


def _render_graficos_tab_content():
    df = prepare_graficos_data()
    if df is None:
        st.info("Carregue os dados em **Novo -> Dados** para visualizar os graficos.")
        return

    st.header("1. Dados Contábeis (brutos)")
    st.subheader("1.1 Contas Patrimoniais (Balanço Patrimonial)")
    st.markdown("### • Ativos")
    if not _try_call_plot(
        df,
        ["render_ativos", "render_ativos_grafico", "render_ativo_total", "render_estoques", "render_contas_a_receber"],
    ):
        _todo_placeholder("Ativos")
    st.markdown("### • Passivos")
    if not _try_call_plot(df, ["render_passivos", "render_passivo_total", "render_contas_a_pagar"]):
        _todo_placeholder("Passivos")
    st.markdown("### • Patrimônio Líquido")
    if not _try_call_plot(df, ["render_pl", "render_patrimonio_liquido"]):
        _todo_placeholder("Patrimônio Líquido")
    st.markdown("### • Capital de Giro / Liquidez")
    capital_rendered = render_ativo_passivo_circulante(df)
    if not capital_rendered:
        capital_rendered = _try_call_plot(df, ["render_capital_giro", "render_liquidez_corrente"])
    if not capital_rendered:
        _todo_placeholder("Capital de Giro / Liquidez")

    st.divider()

    st.subheader("1.2 Contas de Resultado (DRE)")
    st.markdown("### • Operacional")
    operacional_rendered = render_receita_total(df)
    if _try_call_plot(df, ["render_custos", "render_depreciacao", "render_amortizacao"]):
        operacional_rendered = True
    if not operacional_rendered:
        _todo_placeholder("Operacional")
    st.markdown("### • Financeiro")
    financeiro_rendered = render_juros_lucro_receita(df)
    if not financeiro_rendered:
        financeiro_rendered = _try_call_plot(df, ["render_despesa_juros"])
    if not financeiro_rendered:
        _todo_placeholder("Financeiro")
    st.markdown("### • Tributos")
    if not _try_call_plot(df, ["render_impostos", "render_despesa_impostos"]):
        _todo_placeholder("Tributos")
    st.markdown("### • Resultado")
    if not _try_call_plot(df, ["render_lucro_liquido", "render_resultado_liquido"]):
        _todo_placeholder("Resultado")

    st.divider()

    st.header("2. Índices Contábeis")
    st.markdown("### • Liquidez")
    if not _try_call_plot(df, ["render_liquidez_indices"]):
        _todo_placeholder("Liquidez")
    st.markdown("### • Endividamento/Estrutura")
    if not _try_call_plot(df, ["render_endividamento_indices"]):
        _todo_placeholder("Endividamento/Estrutura")
    st.markdown("### • Rentabilidade")
    if not _try_call_plot(df, ["render_rentabilidade_indices"]):
        _todo_placeholder("Rentabilidade")
    st.markdown("### • Eficiência Operacional / Ciclo")
    if not _try_call_plot(df, ["render_eficiencia_indices"]):
        _todo_placeholder("Eficiência Operacional / Ciclo")

    st.divider()

    st.header("3. PCA")
    st.markdown("### • Cargas (loadings)")
    if not _try_call_plot(df, ["render_pca_loadings"]):
        _todo_placeholder("Cargas (loadings)")
    st.markdown("### • Variância explicada (explained variance)")
    if not _try_call_plot(df, ["render_pca_variancia"]):
        _todo_placeholder("Variância explicada (explained variance)")
    st.markdown("### • Projeções (scores) por período/empresa")
    if not _try_call_plot(df, ["render_pca_scores"]):
        _todo_placeholder("Projeções (scores) por período/empresa")


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
    if not st.session_state.get("out"):
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        return

    st.header("Dados Contábeis (brutos)")
    st.subheader("1.1 Contas Patrimoniais (Balanço Patrimonial)")
    st.markdown("### • Ativos")
    if not _try_show_table(["table_ativos", "get_ativos_table"]):
        _todo_placeholder("Ativos")
    st.markdown("### • Passivos")
    if not _try_show_table(["table_passivos", "get_passivos_table"]):
        _todo_placeholder("Passivos")
    st.markdown("### • Patrimônio Líquido")
    if not _try_show_table(["table_pl", "get_pl_table", "get_patrimonio_liquido_table"]):
        _todo_placeholder("Patrimônio Líquido")
    st.markdown("### • Capital de Giro / Liquidez")
    if not _try_show_table(["table_capital_giro", "get_ccl_table", "get_liquidez_table"]):
        _todo_placeholder("Capital de Giro / Liquidez")

    st.divider()

    st.subheader("1.2 Contas de Resultado (DRE)")
    st.markdown("### • Operacional")
    if not _try_show_table(["table_operacional", "get_operacional_table", "get_receita_table", "get_custos_table", "get_depreciacao_table", "get_amortizacao_table"]):
        _todo_placeholder("Operacional")
    st.markdown("### • Financeiro")
    if not _try_show_table(["table_financeiro", "get_financeiro_table", "get_despesa_juros_table"]):
        _todo_placeholder("Financeiro")
    st.markdown("### • Tributos")
    if not _try_show_table(["table_impostos", "get_impostos_table", "get_despesa_impostos_table"]):
        _todo_placeholder("Tributos")
    st.markdown("### • Resultado")
    if not _try_show_table(["table_resultado", "get_resultado_liquido_table", "get_lucro_liquido_table"]):
        _todo_placeholder("Resultado")

    st.divider()

    st.header("2. Índices Contábeis")
    st.markdown("### • Liquidez")
    if not _try_show_table(["table_liquidez_indices"]):
        _todo_placeholder("Liquidez")
    st.markdown("### • Endividamento/Estrutura")
    if not _try_show_table(["table_endividamento_indices"]):
        _todo_placeholder("Endividamento/Estrutura")
    st.markdown("### • Rentabilidade")
    if not _try_show_table(["table_rentabilidade_indices"]):
        _todo_placeholder("Rentabilidade")
    st.markdown("### • Eficiência Operacional / Ciclo")
    if not _try_show_table(["table_eficiencia_indices"]):
        _todo_placeholder("Eficiência Operacional / Ciclo")

    st.divider()

    st.header("3. PCA")
    st.markdown("### • Cargas (loadings)")
    if not _try_show_table(["get_pca_loadings_table"]):
        _todo_placeholder("Cargas (loadings)")

    st.markdown("### • Variância explicada (explained variance)")
    if not _try_show_table(["get_pca_variance_table"]):
        _todo_placeholder("Variância explicada (explained variance)")

    st.markdown("### • Projeções (scores) por período/empresa")
    if not _try_show_table(["get_pca_scores_table"]):
        _todo_placeholder("Projeções (scores) por período/empresa")

    st.markdown("### • Destaques de componentes (top indices)")
    if not _try_show_table(["get_top_indices_table"]):
        _todo_placeholder("Destaques de componentes (top indices)")



def render():
    ss = st.session_state
    ss.setdefault("analise_tab", "Resumo")

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

    tab_resumo, tab_graficos, tab_tabelas = st.tabs(["Resumo", "Graficos", "Tabelas"])

    with tab_resumo:
        render_resumo()
    with tab_graficos:
        _render_graficos_tab_content()
    with tab_tabelas:
        _render_tabelas_tab_content()

