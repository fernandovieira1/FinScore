from pathlib import Path
import streamlit as st
import base64

# 1) Config inicial (uma única vez)
st.set_page_config(page_title="FinScore Dashboard", layout="wide")

# ======= TEMA / ESTILO =======
st.markdown("""
<style>
:root{
  --bg:#f2f4f5;
  --card:#ffffff;
  --text:#1f2937;
  --muted:#6b7280;
  --accent:#0d47a1;
  --accent2:#1976d2;
  --sidebar:#cdcdcd;            /* cor da barra lateral */
  --menu-text:#001733;          /* cor dos textos/ícones do menu lateral */
  --primary-btn:#0a66c2;        /* cor do botão "Iniciar" */

  /* offset fino p/ grudar o logo no topo da sidebar */
  --side-logo-top-fix:-38px;    /* + sobe / - desce */
}

/* ===== Esconde a barra superior (inclui "Deploy") ===== */
header[data-testid="stHeader"]{ display:none; }
#MainMenu{ display:none; }  /* fallback p/ versões antigas */

/* ===== Fundo e espaçamentos do conteúdo ===== */
[data-testid="stAppViewContainer"]{
  background: var(--bg) !important;
}
.block-container{
  padding-top: 0.5rem;  /* alinhado ao topo/nível do logo da sidebar */
  padding-bottom: 2rem;
}

/* Tipografia */
h1,h2,h3{ color:var(--text); letter-spacing:.2px; }
p,li,label,span{ color:var(--text); }

/* Cards reutilizáveis */
.card{
  background: var(--card);
  border-radius: 14px;
  box-shadow: 0 6px 22px rgba(16,24,40,.06), 0 2px 8px rgba(16,24,40,.04);
  padding: 18px 18px 14px 18px;
  border: 1px solid rgba(2,6,23,.06);
  margin-bottom: 1rem;
}
.card-title{ font-size: 1rem; font-weight:700; color:var(--text); margin-bottom:.25rem; }
.card-sub{ font-size: .82rem; color:var(--muted); margin-top:-2px; }

/* ===== Botão principal (ex.: "Iniciar") ===== */
.stButton > button{
  width: min(260px, 100%);
  display: block;
  margin: .35rem auto 0 auto;
  background: var(--primary-btn);
  color:#fff; border:0; border-radius:12px;
  padding:.65rem 1rem; font-weight:700;
  box-shadow: 0 6px 14px rgba(0,0,0,.15);
  transition: filter .15s ease, transform .02s ease;
}
.stButton > button:hover{ filter:brightness(.96); }
.stButton > button:active{ transform: translateY(1px); }

/* ===== Inputs ===== */
.stTextInput>div>div>input,
[data-baseweb="select"]>div,
.stFileUploader>div>div{
  background:#fff; border-radius:10px; border:1px solid rgba(2,6,23,.12);
}
.stRadio>div{ gap:1.2rem; }

/* ===== Sidebar #cdcdcd ===== */
section[data-testid="stSidebar"] > div:first-child{
  background: var(--sidebar) !important;
  padding-top: 0 !important;
}
section[data-testid="stSidebar"] .block-container{
  padding-top: 0 !important;
  padding-bottom: .8rem;
}

/* ===== Logo da sidebar ===== */
section[data-testid="stSidebar"] .side-logo{
  height: 110px;
  display:flex;
  align-items:center;     /* centraliza vertical */
  justify-content:center; /* centraliza horizontal */
  margin: var(--side-logo-top-fix) 8px 10px 8px;
  border-bottom: 1px solid #bdbdbd60;
}
section[data-testid="stSidebar"] .side-logo img{
  display:block !important;
  margin:0 auto !important;
  max-width:80% !important;
  height:auto !important;
}

/* ===== Cores do menu lateral ===== */
section[data-testid="stSidebar"] .nav-link,
section[data-testid="stSidebar"] .nav-link span,
section[data-testid="stSidebar"] .nav-link i,
section[data-testid="stSidebar"] .icon,
section[data-testid="stSidebar"] .nav-link-selected,
section[data-testid="stSidebar"] .nav-link-selected span,
section[data-testid="stSidebar"] .nav-link-selected i{
  color: var(--menu-text) !important;
}
section[data-testid="stSidebar"] .nav-link{
  background-color: var(--sidebar) !important;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 10px 12px !important;
}
section[data-testid="stSidebar"] .nav-link-selected{
  background-color: #bdbdbd !important;
  border-left: 4px solid #8a8a8a !important;
}

/* HR suave */
hr{ border-color: rgba(2,6,23,.08); }
</style>
""", unsafe_allow_html=True)
# ======= fim do estilo =======

ASSETS = Path(__file__).resolve().parent / "assets"

from components.header import render_header
from components.nav import render_sidebar
from views import novo, resumo, tabelas, graficos, parecer, sobre

# ---------------------------
# Estado global
# ---------------------------
ss = st.session_state
ss.setdefault("meta", {})
ss.setdefault("df", None)
ss.setdefault("out", None)
ss.setdefault("erros", {})
ss.setdefault("novo_tab", "Início")
# ss.setdefault("assertif_logo_css", False)  # <- não precisamos mais desse guard

def _add_logo_assertif(path: Path = ASSETS / "logo.png",
                       *, width_px: int = 112, top_px: int = 15, right_px: int = 16):
    """
    Injeta SEMPRE o selo ASSERTIF no canto superior direito
    (precisa rodar a cada rerun/aba).
    """
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

# Render padrão + selo (a cada rerun)
render_header()
_add_logo_assertif()

# Sidebar + rotas (mantidas)
pagina = render_sidebar()

ROUTES = {
    "Novo": novo.render,
    "Resumo": resumo.render,
    "Tabelas": tabelas.render,
    "Gráficos": graficos.render,
    "Parecer": parecer.render,
    "Sobre": sobre.render,
}
ROUTES[pagina]()