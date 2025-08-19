import streamlit as st
from dashboard_finscore import mostrar_dashboard

def render():
    ss = st.session_state

    # ======================
    # Seção Empresa (apenas leitura)
    # ======================
    st.header("🏢 Empresa")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Nome da Empresa")
        st.markdown(
            f"<h3 style='text-align:center;'>{ss.meta.get('empresa', '-')}</h3>",
            unsafe_allow_html=True
        )

    with col2:
        st.subheader("CNPJ")
        st.markdown(
            f"<h3 style='text-align:center;'>{ss.meta.get('cnpj', '-') or '-'}</h3>",
            unsafe_allow_html=True
        )

    with col3:
        st.subheader("Período")
        ai = ss.meta.get("ano_inicial", "-")
        af = ss.meta.get("ano_final", "-")
        periodo = f"{ai} – {af}" if ai and af else "-"
        st.markdown(
            f"<h3 style='text-align:center;'>{periodo}</h3>",
            unsafe_allow_html=True
        )

    st.divider()

    # ======================
    # Seção Resumo
    # ======================
    st.header("📊 Resumo (Dashboard)")
    if not ss.out:
        st.info("Calcule o FinScore em **Novo** para liberar o dashboard.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("FinScore Bruto")
        st.markdown(f"<h3 style='text-align:center;'>{ss.out.get('finscore_bruto', '-')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>{ss.out.get('classificacao_finscore_bruto', '(-)')}</p>", unsafe_allow_html=True)

    with col2:
        st.subheader("FinScore Ajustado")
        st.markdown(f"<h3 style='text-align:center;'>{ss.out.get('finscore_ajustado', '-')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>{ss.out.get('classificacao_finscore', '(-)')}</p>", unsafe_allow_html=True)

    with col3:
        st.subheader("Serasa Score")
        st.markdown(f"<h3 style='text-align:center;'>{ss.out.get('serasa', '-')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>{ss.out.get('classificacao_serasa', '(-)')}</p>", unsafe_allow_html=True)

    st.divider()

    # Dashboard: só df_indices
    if "df_indices" in ss.out and ss.out["df_indices"] is not None:
        mostrar_dashboard(ss.out["df_indices"])
    else:
        st.info("Sem dados de índices para exibir o gráfico de evolução.")
