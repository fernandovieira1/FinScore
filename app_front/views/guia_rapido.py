# app_front/views/guia_rapido.py
import streamlit as st

def render():
    st.header("🚀 Guia Rápido")
    st.markdown("---")
    st.caption("Como usar o FinScore passo a passo.")

    st.markdown(
        """
O FinScore é uma ferramenta de análise financeira que utiliza dados contábeis para gerar um parecer detalhado
sobre a saúde financeira de uma empresa.

Na **barra lateral**, você navega entre as seções do app; e, conforme a seção, **abas centralizadas** na parte superior
indicam o conteúdo correspondente.

### 🟥 Seções disponíveis
- **|Lançamentos|**: onde você insere os dados do cliente e as demonstrações contábeis.
- **|Análise|**: resultados preliminares da análise financeira.
- **|Parecer|**: geração/edição de um parecer em PDF.
- **|Sobre|**: informações sobre o FinScore e seus desenvolvedores.
- **|Contato|**: formulário para dúvidas/sugestões.

As seções **|Análise|** e **|Parecer|** ficam disponíveis **após** o cálculo do FinScore na seção **|Lançamentos|**.

### 🔶 Como lançar os dados
1. Acesse **|Lançamentos| → 📘 Cliente** e preencha *Empresa, CNPJ, Ano Inicial/Final e Serasa*.
2. Vá em **📥 Dados** e forneça as demonstrações via **Excel (.xlsx)** ou **Google Sheets**.
3. Clique em **Calcular FinScore** para processar.

### ☑️ Como analisar e interpretar
Após calcular, consulte **|Análise|** para os resultados e, se desejar, gere/edite o PDF em **|Parecer|**.
        """,
        unsafe_allow_html=False,
    )