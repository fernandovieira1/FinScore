import streamlit as st
from datetime import date

def _empresa(ss):
    st.markdown("### 🏢 Empresa")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("Nome da Empresa")
        st.markdown(
            f"<h3 style='text-align:left;margin:0;font-size: 140%;'>{ss.meta.get('empresa','-')}</h3>",
            unsafe_allow_html=True,
        )

    with col2:
        st.caption("CNPJ")
        st.markdown(
            f"<h3 style='text-align:left;margin:0;font-size: 140%;'>{ss.meta.get('cnpj','-') or '-'}</h3>",
            unsafe_allow_html=True,
        )

    with col3:
        st.caption("Período")
        ai, af = ss.meta.get("ano_inicial"), ss.meta.get("ano_final")
        periodo = f"{ai} – {af}" if ai and af else "-"
        st.markdown(
            f"<h3 style='text-align:left;margin:0;font-size: 140%;'>{periodo}</h3>",
            unsafe_allow_html=True,
        )

    st.divider()


def _metricas(ss):
    st.markdown("### 📌 Resumo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<p style='margin-bottom:.25rem;'>FinScore Bruto</p>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='margin:.15rem 0 0 0;font-size:140%;'>{ss.out.get('finscore_bruto','-')}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='margin:.25rem 0 0 0;'>{ss.out.get('classificacao_finscore_bruto','(-)')}</p>",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("<p style='margin-bottom:.25rem;'>FinScore Ajustado</p>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='margin:.15rem 0 0 0;font-size:140%;'>{ss.out.get('finscore_ajustado','-')}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='margin:.25rem 0 0 0;'>{ss.out.get('classificacao_finscore','(-)')}</p>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown("<p style='margin-bottom:.25rem;'>Serasa Score</p>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='margin:.15rem 0 0 0;font-size:140%;'>{ss.out.get('serasa','-')}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='margin:.25rem 0 0 0;'>{ss.out.get('classificacao_serasa','(-)')}</p>",
            unsafe_allow_html=True,
        )

    # (sem divider aqui para ficar idêntico ao seu print “certo”)





def _datas(ss):
    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    hoje = date.today().strftime("%d/%m/%Y")
    meta = getattr(ss, "meta", {}) or {}
    serasa_data = meta.get("serasa_data")
    serasa_label = serasa_data if serasa_data else "-"
    with col1:
        st.caption("Data da Analise")
        st.markdown(
            f"<p style='margin:0;font-size:1.25rem;font-weight:600;'>{hoje}</p>",
            unsafe_allow_html=True,
        )
    with col3:
        st.caption("Data de Consulta ao Serasa")
        st.markdown(
            f"<p style='margin:0;font-size:1.25rem;font-weight:600;'>{serasa_label}</p>",
            unsafe_allow_html=True,
        )


def render():
    ss = st.session_state

    # Se ainda não processou, apenas orienta
    if not ss.get("out"):
        _empresa(ss)
        st.info("Calcule o FinScore em **Lançamentos → Dados** para liberar o resumo.")
        return

    # Bloco Empresa + Bloco de Métricas (mesmo desenho do print “certo”)
    _empresa(ss)
    _metricas(ss)
    _datas(ss)
