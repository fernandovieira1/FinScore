from pathlib import Path
import sys
import streamlit as st
import base64

# ---------------- path setup ----------------
APP_DIR = Path(__file__).resolve().parent          # .../FinScore/app_front
ROOT_DIR = APP_DIR.parent                          # .../FinScore
for p in (str(APP_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# --------------- config ---------------
st.set_page_config(page_title="FinScore Dashboard", layout="wide")

# --------------- tema / css ---------------
st.markdown("""
<style>
:root{
  --bg:#f2f4f5; --card:#ffffff; --text:#1f2937; --muted:#6b7280;
  --accent:#0d47a1; --accent2:#1976d2; --sidebar:#cdcdcd;
  --menu-text:#001733; --primary-btn:#0074d9; --side-logo-top-fix:-38px;
}
header[data-testid="stHeader"]{ display:none !important; }
div[data-testid="stToolbar"]{ display:none !important; }
[data-testid="stAppViewContainer"] > .main{ padding-top:0 !important; margin-top:0 !important; }
#MainMenu{ display:none; }
[data-testid="stAppViewContainer"]{ background: var(--bg) !important; }
.block-container{ padding-top:.5rem; padding-bottom:2rem; }
.block-container > hr:first-of-type{ display:none !important; }
h1,h2,h3{ color:var(--text); letter-spacing:.2px; }
p,li,label,span{ color:var(--text); }
.card{ background:var(--card); border-radius:14px; box-shadow:0 6px 22px rgba(16,24,40,.06), 0 2px 8px rgba(16,24,40,.04);
  padding:18px 18px 14px; border:1px solid rgba(2,6,23,.06); margin-bottom:1rem;}
.card-title{ font-size:1rem; font-weight:700; color:var(--text); margin-bottom:.25rem;}
.card-sub{ font-size:.82rem; color:var(--muted); margin-top:-2px;}
/* sidebar */
section[data-testid="stSidebar"] > div:first-child{ background:#cdcdcd !important; padding-top:0 !important;}
section[data-testid="stSidebar"] .block-container{ padding-top:0 !important; padding-bottom:.8rem;}
section[data-testid="stSidebar"] .side-logo{ height:110px; display:flex; align-items:center; justify-content:center;
  margin:var(--side-logo-top-fix) 8px 10px; border-bottom:1px solid #bdbdbd60;}
section[data-testid="stSidebar"] .side-logo img{ display:block !important; margin:0 auto !important; max-width:80% !important; height:auto !important;}
section[data-testid="stSidebar"] .nav-link,
section[data-testid="stSidebar"] .nav-link span,
section[data-testid="stSidebar"] .nav-link i,
section[data-testid="stSidebar"] .icon,
section[data-testid="stSidebar"] .nav-link-selected,
section[data-testid="stSidebar"] .nav-link-selected span,
section[data-testid="stSidebar"] .nav-link-selected i{ color:#001733 !important;}
section[data-testid="stSidebar"] .nav-link{ background-color:#cdcdcd !important; border-radius:0 !important; margin:0 !important; padding:10px 12px !important;}
section[data-testid="stSidebar"] .nav-link-selected{ background-color:#bdbdbd !important; border-left:4px solid #8a8a8a !important;}
hr{ border-color: rgba(2,6,23,.08); }
</style>
""", unsafe_allow_html=True)

ASSETS = Path(__file__).resolve().parent / "assets"

# --------------- imports das views ---------------
from views import analise as view_analise
from views import lancamentos as view_lancamentos
from views import parecer, sobre, contato
from components.topbar import render_topbar
from components.nav import render_sidebar

# --------------- estado global ---------------
ss = st.session_state
ss.setdefault("meta", {})
ss.setdefault("df", None)
ss.setdefault("out", None)
ss.setdefault("erros", {})
ss.setdefault("novo_tab", "Início")
ss.setdefault("analise_tab", "Resumo")
ss.setdefault("page", "Lançamentos")

# --------------- topbar ---------------
render_topbar()

# --------------- rotas ---------------
ROUTES = {
    "Lançamentos": view_lancamentos.render,
    "Análise": view_analise.render,
    "Parecer": parecer.render,
    "Sobre": sobre.render,
    "Contato": contato.render,
}

pagina_sidebar = render_sidebar(current_page=ss["page"])
if pagina_sidebar in ROUTES and pagina_sidebar != ss["page"]:
    ss["page"] = pagina_sidebar
    st.rerun()

# remove hash de URL de outras views
st.markdown("""
<script>
try{
  if (window.location.hash) {
    history.replaceState('', document.title, window.location.pathname + window.location.search);
  }
}catch(e){}
</script>
""", unsafe_allow_html=True)

def navigate_to(page: str):
    if page in ROUTES:
        ss["page"] = page
        st.rerun()

ss["_navigate_to"] = navigate_to

# --------------- render ---------------
try:
    ROUTES.get(ss.get("page", "Lançamentos"), view_lancamentos.render)()
except Exception as e:
    st.error("Erro ao renderizar a página selecionada.")
    st.exception(e)
