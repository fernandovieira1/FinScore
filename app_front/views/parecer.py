# app_front/pages/parecer.py
import streamlit as st

def render():
    ss = st.session_state
    st.header("📝 Parecer (Fase 2)")
    st.info("Integração futura: OpenAI/LangChain para gerar o parecer e exportar PDF/Word.")
    if ss.out:
        st.caption(f"Contexto: {ss.meta.get('empresa','Empresa')} — {ss.meta['ano_inicial']}–{ss.meta['ano_final']}")
        st.write("• Estrutura proposta do parecer:")
        st.write("- Sumário executivo")
        st.write("- Liquidez, Rentabilidade, Estrutura de Capital, Eficiência, Endividamento")
        st.write("- Conclusão e recomendações")
