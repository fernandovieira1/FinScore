# app_front/views/resultados.py
import streamlit as st
import pandas as pd
import plotly.express as px

# (opcional) dashboard de evolução, se você já tiver esse módulo
try:
    from dashboard_finscore import mostrar_dashboard
except Exception:
    mostrar_dashboard = None

# ======================
# Helpers (vindos do graficos.py)
# ======================
TITLE_STYLE = {"font_size": 20, "y": 0.95}

def _prepare_base_df() -> pd.DataFrame | None:
    """Escolhe a base mais apropriada para os gráficos e padroniza 'ano'."""
    ss = st.session_state
    base = None

    # Preferir a base contábil original (tem as contas pedidas)
    if ss.get("df") is not None:
        base = ss.df
    elif ss.get("out"):
        base = ss.out.get("df_raw")  # só se você tiver salvo isso no backend
        if base is None:
            return None

    df = base.copy()

    # Garantir coluna 'ano'
    if "ano" not in df.columns:
        df["ano"] = list(range(len(df), 0, -1))

    # Tentar converter numéricos
    for c in df.columns:
        if c != "ano":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.sort_values("ano", ascending=False)
    return df

def _bar_h(fig_title: str, tidy_df: pd.DataFrame, x_col: str, y_col: str, color_col: str):
    fig = px.bar(
        tidy_df, x=x_col, y=y_col, color=color_col,
        orientation="h", text=x_col, barmode="group",
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
    fig = px.bar(df, x=x_col, y=y_col, text=y_col)
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        title={"text": fig_title, **TITLE_STYLE},
        xaxis_title="Ano",
        yaxis=dict(title="", tickformat=",.0f"),
        margin=dict(l=10, r=10, t=50, b=10),
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- Cabeçalho reutilizável (título + empresa) ----------
def _render_header_empresa():
    ss = st.session_state
    
    st.subheader("🏢 Empresa")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("Nome:")
        st.markdown(
            f"<h3 style='text-align:left;'>{ss.meta.get('empresa', '-')}</h3>",
            unsafe_allow_html=True
        )

    with col2:
        st.caption("CNPJ:")
        st.markdown(
            f"<h3 style='text-align:left;'>{ss.meta.get('cnpj', '-') or '-'}</h3>",
            unsafe_allow_html=True
        )

    with col3:
        st.caption("Período:")
        ai = ss.meta.get("ano_inicial", "-")
        af = ss.meta.get("ano_final", "-")
        periodo = f"{ai} – {af}" if ai and af else "-"
        st.markdown(
            f"<h3 style='text-align:left;'>{periodo}</h3>",
            unsafe_allow_html=True
        )

    st.divider()

# ======================
# Página
# ======================
def render():
    ss = st.session_state

    # Se não houver saída, mostra header e mensagem (sem abas)
    if not ss.get("out"):
        _render_header_empresa()
        st.info("Calcule o FinScore em **Novo** para liberar os resultados.")
        return

    # -------- Abas nativas (estilo original) ACIMA do título --------
    tab_resumo, tab_graficos, tab_tabelas = st.tabs(["📊 Resumo", "📈 Gráficos", "📄 Tabelas"])

    # ====== Aba: Resumo ======
    with tab_resumo:
        _render_header_empresa()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("<p style='text-align:left; color:black; font-size:0.9em;'>FinScore Bruto:</p>", unsafe_allow_html=True)
            st.markdown(
                f"<h3 style='text-align:left;'>{ss.out.get('finscore_bruto', '-')}</h3>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<p style='text-align:left;'>{ss.out.get('classificacao_finscore_bruto', '(-)')}</p>",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown("<p style='text-align:left; color:black; font-size:0.9em;'>FinScore Ajustado:</p>", unsafe_allow_html=True)
            st.markdown(
                f"<h3 style='text-align:left;'>{ss.out.get('finscore_ajustado', '-')}</h3>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<p style='text-align:left;'>{ss.out.get('classificacao_finscore', '(-)')}</p>",
                unsafe_allow_html=True
            )

        with col3:
            st.markdown("<p style='text-align:left; color:black; font-size:0.9em;'>Serasa Score:</p>", unsafe_allow_html=True)
            st.markdown(
                f"<h3 style='text-align:left;'>{ss.out.get('serasa', '-')}</h3>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<p style='text-align:left;'>{ss.out.get('classificacao_serasa', '(-)')}</p>",
                unsafe_allow_html=True
            )

        st.write("")

        df_indices = ss.out.get("df_indices")
        if mostrar_dashboard and df_indices is not None:
            try:
                mostrar_dashboard(df_indices)
            except Exception as e:
                st.warning(f"Não foi possível renderizar o dashboard padrão ({e}).")

    # ====== Aba: Gráficos ======
    with tab_graficos:
        _render_header_empresa()

        df_base = _prepare_base_df()
        if df_base is None:
            st.info("Carregue os dados em **Novo → Dados** para visualizar os gráficos.")
        else:
            # 1) Ativo e Passivo Circulante
            needed_1 = {"p_Ativo_Circulante", "p_Passivo_Circulante"}
            if needed_1.issubset(df_base.columns):
                tidy1 = df_base[["ano", "p_Ativo_Circulante", "p_Passivo_Circulante"]].melt(
                    id_vars="ano", var_name="Conta", value_name="Valor"
                )
                tidy1["Conta"] = tidy1["Conta"].replace({
                    "p_Ativo_Circulante": "Ativo Circulante",
                    "p_Passivo_Circulante": "Passivo Circulante",
                })
                _bar_h("Ativo e Passivo Circulante", tidy1, x_col="Valor", y_col="ano", color_col="Conta")
            else:
                miss = ", ".join(sorted(needed_1 - set(df_base.columns)))
                st.warning(f"Não foi possível montar **Ativo e Passivo Circulante** (faltam: {miss}).")

            st.divider()

            # 2) Receita Total
            if "r_Receita_Total" in df_base.columns:
                _bar_v("Receita Total", df_base, x_col="ano", y_col="r_Receita_Total")
            else:
                st.warning("Não foi possível montar **Receita Total** (coluna ausente: r_Receita_Total).")

            st.divider()

            # 3) Juros, Lucro e Receita Total
            needed_3 = {"r_Despesa_de_Juros", "r_Lucro_Liquido", "r_Receita_Total"}
            if needed_3.issubset(df_base.columns):
                tidy3 = df_base[["ano", "r_Despesa_de_Juros", "r_Lucro_Liquido", "r_Receita_Total"]].melt(
                    id_vars="ano", var_name="Conta", value_name="Valor"
                )
                tidy3["Conta"] = tidy3["Conta"].replace({
                    "r_Despesa_de_Juros": "Juros (Despesa)",
                    "r_Lucro_Liquido": "Lucro Líquido",
                    "r_Receita_Total": "Receita Total",
                })
                fig3 = px.bar(
                    tidy3, x="Valor", y="ano", color="Conta",
                    orientation="h", text="Valor", barmode="stack",
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
                miss = ", ".join(sorted(needed_3 - set(df_base.columns)))
                st.warning(f"Não foi possível montar **Juros, Lucro e Receita Total** (faltam: {miss}).")

    # ====== Aba: Tabelas ======
    with tab_tabelas:
        _render_header_empresa()

        st.markdown("**Índices Contábeis Calculados**")
        if ss.out.get("df_indices") is not None:
            st.dataframe(ss.out["df_indices"], use_container_width=True)
        else:
            st.info("Sem `df_indices` para exibir.")

        st.markdown("**Componentes Principais (PCA)**")
        if ss.out.get("df_pca") is not None:
            st.dataframe(ss.out["df_pca"], use_container_width=True)
        else:
            st.info("Sem `df_pca` para exibir.")

        st.markdown("**Top 3 Índices por Componente**")
        if ss.out.get("top_indices_df") is not None:
            st.dataframe(ss.out["top_indices_df"], use_container_width=True)
        else:
            st.info("Sem `top_indices_df` para exibir.")
