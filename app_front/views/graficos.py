# app_front/pages/graficos.py
import streamlit as st
import plotly.express as px
import pandas as pd

TITLE_STYLE = {
    "font_size": 20,
    "y": 0.95
}

def _prepare_base_df() -> pd.DataFrame | None:
    """Escolhe a base mais apropriada para os gráficos e padroniza 'ano'."""
    ss = st.session_state
    base = None

    # Preferir a base contábil original (tem as contas pedidas)
    if ss.get("df") is not None:
        base = ss.df
    elif ss.get("out"):
        # fallback: se alguém quiser plotar a partir do resultado
        base = ss.out.get("df_raw")  # só se você tiver salvo isso no backend
        if base is None:
            # sem df_raw, não dá para produzir esses gráficos
            return None

    df = base.copy()

    # Garantir coluna 'ano'
    if "ano" not in df.columns:
        df["ano"] = list(range(len(df), 0, -1))

    # Tentar converter numéricos
    for c in df.columns:
        if c != "ano":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Ordenar pelos anos (mais recente no topo em gráficos horizontais)
    # como 'ano' vem como número/str, garantir ordenação correta
    df = df.sort_values("ano", ascending=False)
    return df


def _bar_h(fig_title: str, tidy_df: pd.DataFrame, x_col: str, y_col: str, color_col: str):
    fig = px.bar(
        tidy_df,
        x=x_col,
        y=y_col,
        color=color_col,
        orientation="h",
        text=x_col,
        barmode="group",
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        title={"text": fig_title, **TITLE_STYLE},
        xaxis=dict(title="", tickformat=",.0f"),
        yaxis_title="",
        legend_title="",
        margin=dict(l=10, r=10, t=50, b=10),
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)


def _bar_v(fig_title: str, df: pd.DataFrame, x_col: str, y_col: str):
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        text=y_col,
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        title={"text": fig_title, **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis=dict(title="", tickformat=",.0f"),
        margin=dict(l=10, r=10, t=50, b=10),
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)


def render():
    st.header("📈 Gráficos")

    df = _prepare_base_df()
    if df is None:
        st.info("Carregue os dados em **Novo → Dados** para visualizar os gráficos.")
        return

    # 1) Ativo e Passivo Circulante (barras horizontais, agrupadas)
    needed_1 = {"p_Ativo_Circulante", "p_Passivo_Circulante"}
    if needed_1.issubset(df.columns):
        tidy1 = df[["ano", "p_Ativo_Circulante", "p_Passivo_Circulante"]].melt(
            id_vars="ano", var_name="Conta", value_name="Valor"
        )
        # rótulos amigáveis
        tidy1["Conta"] = tidy1["Conta"].replace({
            "p_Ativo_Circulante": "Ativo Circulante",
            "p_Passivo_Circulante": "Passivo Circulante",
        })
        _bar_h("Ativo e Passivo Circulante", tidy1, x_col="Valor", y_col="ano", color_col="Conta")
    else:
        miss = ", ".join(sorted(needed_1 - set(df.columns)))
        st.warning(f"Não foi possível montar **Ativo e Passivo Circulante** (faltam: {miss}).")

    st.divider()

    # 2) Receita Total (barras verticais)
    if "r_Receita_Total" in df.columns:
        _bar_v("Receita Total", df, x_col="ano", y_col="r_Receita_Total")
    else:
        st.warning("Não foi possível montar **Receita Total** (coluna ausente: r_Receita_Total).")

    st.divider()

    # 3) Juros, Lucro e Receita Total (barras horizontais empilhadas)
    needed_3 = {"r_Despesa_de_Juros", "r_Lucro_Liquido", "r_Receita_Total"}
    if needed_3.issubset(df.columns):
        tidy3 = df[["ano", "r_Despesa_de_Juros", "r_Lucro_Liquido", "r_Receita_Total"]].melt(
            id_vars="ano", var_name="Conta", value_name="Valor"
        )
        tidy3["Conta"] = tidy3["Conta"].replace({
            "r_Despesa_de_Juros": "Juros (Despesa)",
            "r_Lucro_Liquido": "Lucro Líquido",
            "r_Receita_Total": "Receita Total",
        })
        fig3 = px.bar(
            tidy3,
            x="Valor",
            y="ano",
            color="Conta",
            orientation="h",
            text="Valor",
            barmode="stack",
        )
        fig3.update_traces(texttemplate="%{text:,.0f}", textposition="none")
        fig3.update_layout(
            title={"text": "Juros, Lucro e Receita Total", **TITLE_STYLE},
            xaxis=dict(title="", tickformat=",.0f"),
            yaxis_title="",
            legend_title="",
            margin=dict(l=10, r=10, t=50, b=10),
            height=380,
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        miss = ", ".join(sorted(needed_3 - set(df.columns)))
        st.warning(f"Não foi possível montar **Juros, Lucro e Receita Total** (faltam: {miss}).")
