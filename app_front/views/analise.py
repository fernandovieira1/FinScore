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
    _todo_placeholder("Ativos")
    st.markdown("### • Passivos")
    _todo_placeholder("Passivos")
    st.markdown("### • Patrimônio Líquido")
    _todo_placeholder("Patrimônio Líquido")
    st.markdown("### • Capital de Giro / Liquidez")
    if not render_ativo_passivo_circulante(df):
        _todo_placeholder("Capital de Giro / Liquidez")

    st.divider()

    st.subheader("1.2 Contas de Resultado (DRE)")
    st.markdown("### • Operacional")
    if not render_receita_total(df):
        _todo_placeholder("Operacional")
    st.markdown("### • Financeiro")
    if not render_juros_lucro_receita(df):
        _todo_placeholder("Financeiro")
    st.markdown("### • Tributos")
    _todo_placeholder("Tributos")
    st.markdown("### • Resultado")
    _todo_placeholder("Resultado")

    st.divider()

    st.header("2. Índices Contábeis")
    st.markdown("### • Liquidez")
    _todo_placeholder("Liquidez")
    st.markdown("### • Endividamento/Estrutura")
    _todo_placeholder("Endividamento/Estrutura")
    st.markdown("### • Rentabilidade")
    _todo_placeholder("Rentabilidade")
    st.markdown("### • Eficiência Operacional / Ciclo")
    _todo_placeholder("Eficiência Operacional / Ciclo")

    st.divider()

    st.header("3. PCA")
    st.markdown("### • Cargas (loadings)")
    _todo_placeholder("Cargas (loadings)")
    st.markdown("### • Variância explicada (explained variance)")
    _todo_placeholder("Variância explicada (explained variance)")
    st.markdown("### • Projeções (scores) por período/empresa")
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
    _todo_placeholder("Ativos")
    st.markdown("### • Passivos")
    _todo_placeholder("Passivos")
    st.markdown("### • Patrimônio Líquido")
    _todo_placeholder("Patrimônio Líquido")
    st.markdown("### • Capital de Giro / Liquidez")
    _todo_placeholder("Capital de Giro / Liquidez")

    st.divider()

    st.subheader("1.2 Contas de Resultado (DRE)")
    st.markdown("### • Operacional")
    _todo_placeholder("Operacional")
    st.markdown("### • Financeiro")
    _todo_placeholder("Financeiro")
    st.markdown("### • Tributos")
    _todo_placeholder("Tributos")
    st.markdown("### • Resultado")
    _todo_placeholder("Resultado")

    st.divider()

    st.header("2. Índices Contábeis")
    indices_df = get_indices_table()
    if indices_df is not None and not indices_df.empty:
        _render_indices_tables(indices_df)
    else:
        st.markdown("### • Liquidez")
        _todo_placeholder("Liquidez")
        st.markdown("### • Endividamento/Estrutura")
        _todo_placeholder("Endividamento/Estrutura")
        st.markdown("### • Rentabilidade")
        _todo_placeholder("Rentabilidade")
        st.markdown("### • Eficiência Operacional / Ciclo")
        _todo_placeholder("Eficiência Operacional / Ciclo")

    st.divider()

    st.header("3. PCA")
    loadings_df = get_pca_loadings_table()
    st.markdown("### • Cargas (loadings)")
    if loadings_df is not None and not loadings_df.empty:
        st.dataframe(loadings_df, use_container_width=True, hide_index=True)
    else:
        _todo_placeholder("Cargas (loadings)")

    st.markdown("### • Variância explicada (explained variance)")
    _todo_placeholder("Variância explicada (explained variance)")

    scores_df = get_pca_scores_table()
    st.markdown("### • Projeções (scores) por período/empresa")
    if scores_df is not None and not scores_df.empty:
        st.dataframe(scores_df, use_container_width=True, hide_index=True)
    else:
        _todo_placeholder("Projeções (scores) por período/empresa")

    top_indices_df = get_top_indices_table()
    if top_indices_df is not None and not top_indices_df.empty:
        st.markdown("### • Destaques de componentes (top indices)")
        st.dataframe(top_indices_df, use_container_width=True, hide_index=True)


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
