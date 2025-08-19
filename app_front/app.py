# app_front/app.py
import streamlit as st

# >>> TEM QUE SER A PRIMEIRA CHAMADA DO STREAMLIT <<<
st.set_page_config(page_title="FinScore Dashboard", layout="wide")

import base64
from components.header import render_header
from components.nav import render_sidebar
from views import novo, resumo, tabelas, graficos, parecer, sobre

# ---------------------------
# Estado global (NÃO sobrescrever!)
# ---------------------------
ss = st.session_state
ss.setdefault("meta", {})            # empresa, cnpj, anos, serasa
ss.setdefault("df", None)            # DataFrame contábil
ss.setdefault("out", None)           # saída do processamento FinScore
ss.setdefault("erros", {})           # validações
ss.setdefault("novo_tab", "Início")  # controle programático das "abas" internas de Novo
ss.setdefault("assertif_logo_css", False)  # evita injetar CSS repetido

def _add_logo_assertif(path: str = "assets/logo1.png",
                       *, width_px: int = 140, top_px: int = 16, right_px: int = 40):
    """Exibe o logo da Assertif fixo no canto superior direito, em todas as abas."""
    if ss.assertif_logo_css:
        return
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return  # se o arquivo não existir, só não exibe o logo

    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            top: {top_px}px;
            right: {right_px}px;
            width: {width_px}px;
            height: {int(width_px * 0.285)}px;
            background-image: url("data:image/png;base64,{encoded}");
            background-repeat: no-repeat;
            background-size: contain;
            z-index: 9999;
            pointer-events: none;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    ss.assertif_logo_css = True

# Render padrão + logo
render_header()
_add_logo_assertif()

pagina = render_sidebar()

ROUTES = {
    "Novo": novo.render,
    "Resumo": resumo.render,
    "Tabelas": tabelas.render,
    "Gráficos": graficos.render,
    "Parecer": parecer.render,
    "Sobre": sobre.render,
}

# Chama a página atual
ROUTES[pagina]()
