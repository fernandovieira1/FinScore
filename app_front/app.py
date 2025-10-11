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
st.set_page_config(page_title="FinScore", layout="wide")

# --------------- imports ---------------
from app_front.views import estoque
from components import AppState, render_sidebar, render_topbar, DEBUG_MODE
from components.config import TOPBAR_PAGES, SIDEBAR_PAGES
from components.theme import inject_global_css

# Import das views
from views import analise as view_analise
from views import lancamentos as view_lancamentos
from views import parecer, sobre, contato
from views import guia_rapido
from views import faq as view_faq
from views import glossario as view_glossario
from app_front.views import cadastros
from views import home as view_home
from views import novo as view_novo
from views import processo as view_processo

# --------------- carregar CSS externo ---------------
def load_css():
    # O CSS está na pasta styles dentro de app_front
    css_path = APP_DIR / "styles" / "main.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.warning("Arquivo CSS não encontrado. Usando estilo padrão.")

# --------------- tema / css ---------------
load_css()
inject_global_css()

# --------------- inicialização do estado ---------------
AppState.initialize()

# Preserva os dados ao navegar entre as páginas
AppState.preserve_data_across_pages()

# --------------- definição das rotas ---------------
ROUTES = {
    "Home": view_home.render,
    "Processo": view_processo.render,     # <-- NOVO
    "Novo": view_novo.render,
    "Definir1": estoque.render,
    "Definir2": cadastros.render,
    "Guia Rápido": guia_rapido.render,
    "FAQ": view_faq.render,
    "Glossário": view_glossario.render,
    "Lançamentos": view_lancamentos.render,
    "Análise": view_analise.render,
    "Parecer": parecer.render,
    "Sobre": sobre.render,
    "Contato": contato.render,
}

# --------------- processamento de navegação ---------------

# 1. Suprime navegação automática para 'analise' se _lock_parecer estiver ativo
if st.session_state.get("_lock_parecer") or st.session_state.get("current_page") == "Parecer":
    # Garante que a página permaneça em 'Parecer' após rerun e força URL
    AppState.set_current_page("Parecer", source="lock_parecer", slug="parecer")
    AppState.sync_to_query_params()
    st.query_params["p"] = "parecer"
    # Bloqueia navegação da sidebar por 2 segundos
    AppState.skip_next_url_sync(target_slug="parecer", duration=2.0, blocked_slugs={"lanc", "analise"})
    st.session_state.pop("_lock_parecer", None)
else:
    # 1. Sincroniza a partir da URL normalmente
    url_changed = AppState.sync_from_query_params()

# 2. Renderiza a topbar
render_topbar(current_page=AppState.get_current_page())

# 3. Renderiza a sidebar
sidebar_page = render_sidebar(current_page=AppState.get_current_page())

# 4. Processa navegação da sidebar
if sidebar_page and sidebar_page in ROUTES:
    current_page = AppState.get_current_page()
    print(f"[DEBUG] app.py: sidebar_page={sidebar_page}, current_page={current_page}")
    if sidebar_page != current_page:
        if not AppState.should_ignore_navigation('sidebar'):
            print(f"[DEBUG] app.py: Navegação permitida para {sidebar_page}")
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

