# app.py
from pathlib import Path
import sys
import streamlit as st

# ---------------- path setup ----------------
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
for p in (str(APP_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# --------------- config ---------------
st.set_page_config(page_title="FinScore Dashboard", layout="wide")

# --------------- imports ---------------
from components import AppState, render_sidebar, render_topbar, DEBUG_MODE

# Import das views
from views import analise as view_analise
from views import lancamentos as view_lancamentos
from views import parecer, sobre, contato
from views import guia_rapido
from views import definir1, definir2
from app_front.views import home as view_home

# --------------- tema / css ---------------
st.markdown("""
<style>
:root {
  --bg: #f2f4f5; --card: #ffffff; --text: #1f2937; --muted: #6b7280;
  --accent: #0d47a1; --accent2: #1976d2; --sidebar: #cdcdcd;
  --menu-text: #001733; --primary-btn: #0074d9; --side-logo-top-fix: -38px;
}
header[data-testid="stHeader"] { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
[data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; margin-top: 0 !important; }
#MainMenu { display: none; }
[data-testid="stAppViewContainer"] { background: var(--bg) !important; }
.block-container { padding-top: .5rem; padding-bottom: 2rem; }
.block-container > hr:first-of-type { display: none !important; }
h1, h2, h3 { color: var(--text); letter-spacing: .2px; }
p, li, label, span { color: var(--text); }
.card { 
  background: var(--card); border-radius: 14px; box-shadow: 0 6px 22px rgba(16,24,40,.06), 0 2px 8px rgba(16,24,40,.04);
  padding: 18px 18px 14px; border: 1px solid rgba(2,6,23,.06); margin-bottom: 1rem;
}
.card-title { font-size: 1rem; font-weight: 700; color: var(--text); margin-bottom: .25rem; }
.card-sub { font-size: .82rem; color: var(--muted); margin-top: -2px; }

/* -------- sidebar -------- */
section[data-testid="stSidebar"] > div:first-child { background: #cdcdcd !important; padding-top: 0 !important; }
section[data-testid="stSidebar"] .block-container { padding-top: 0 !important; padding-bottom: .8rem; }
section[data-testid="stSidebar"] .side-logo { 
  height: 110px; display: flex; align-items: center; justify-content: center;
  margin: var(--side-logo-top-fix) 8px 10px; border-bottom: 1px solid #bdbdbd60;
}
section[data-testid="stSidebar"] .side-logo img { 
  display: block !important; margin: 0 auto !important; max-width: 80% !important; height: auto !important;
}
section[data-testid="stSidebar"] .nav-link,
section[data-testid="stSidebar"] .nav-link span,
section[data-testid="stSidebar"] .nav-link i,
section[data-testid="stSidebar"] .icon,
section[data-testid="stSidebar"] .nav-link-selected,
section[data-testid="stSidebar"] .nav-link-selected span,
section[data-testid="stSidebar"] .nav-link-selected i { color: #001733 !important; }
section[data-testid="stSidebar"] .nav-link { 
  background-color: #cdcdcd !important; border-radius: 0 !important; margin: 0 !important; padding: 10px 12px !important;
}
section[data-testid="stSidebar"] .nav-link-selected { 
  background-color: #bdbdbd !important; border-left: 4px solid #8a8a8a !important;
}

/* ocultar o botão de fechar/colapsar a sidebar */
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] [data-testid="baseButton-header"],
section[data-testid="stSidebar"] button[aria-label="Close"],
section[data-testid="stSidebar"] button[aria-label="Fechar"],
section[data-testid="stSidebar"] > div:first-child button {
  display: none !important;
}

hr { border-color: rgba(2,6,23,.08); }
</style>
""", unsafe_allow_html=True)

# --------------- inicialização do estado ---------------
AppState.initialize()

# --------------- definição das rotas ---------------
ROUTES = {
    "Home": view_home.render,
    "Definir1": definir1.render,
    "Definir2": definir2.render,
    "Guia Rápido": guia_rapido.render,
    "Lançamentos": view_lancamentos.render,
    "Análise": view_analise.render,
    "Parecer": parecer.render,
    "Sobre": sobre.render,
    "Contato": contato.render,
}

# --------------- processamento de navegação ---------------

# 1. Sincroniza a partir da URL (prioridade máxima)
url_changed = AppState.sync_from_query_params()

# 2. Renderiza a topbar
render_topbar(current_page=AppState.get_current_page())

# 3. Renderiza a sidebar
sidebar_page = render_sidebar(current_page=AppState.get_current_page())

# 4. Processa navegação da sidebar (prioridade média)
if sidebar_page and sidebar_page in ROUTES:
    if sidebar_page != AppState.get_current_page():
        if not AppState.should_ignore_navigation('sidebar'):
            AppState.set_current_page(sidebar_page, 'sidebar')
            AppState.sync_to_query_params()
            st.rerun()

# 5. Sincroniza para a URL (mantém consistência)
AppState.sync_to_query_params()

# Remove hash da URL (estético)
st.markdown("""
<script>
try {
  if (window.location.hash) {
    history.replaceState('', document.title, window.location.pathname + window.location.search);
  }
} catch(e) {}
</script>
""", unsafe_allow_html=True)

# --------------- renderização da página ---------------
try:
    current_page = AppState.get_current_page()
    render_function = ROUTES.get(current_page, view_home.render)
    render_function()
except Exception as e:
    st.error(f"Erro ao renderizar {current_page}: {str(e)}")
    # Fallback para Home em caso de erro
    AppState.set_current_page("Home", 'error')
    view_home.render()

# --------------- debug info ---------------
if DEBUG_MODE:
    with st.expander("🔧 Debug Info", expanded=False):
        st.write(f"**Página atual:** {AppState.get_current_page()}")
        st.write(f"**Sidebar retornou:** {sidebar_page}")
        st.write(f"**Query param:** {st.query_params.get('p', None)}")
        st.write(f"**Última navegação:** {st.session_state.get('last_navigation_time')}")
        st.write(f"**Fonte:** {st.session_state.get('navigation_source')}")
        st.write(f"**Mudança por URL:** {url_changed}")