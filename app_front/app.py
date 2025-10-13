from pathlib import Path
import sys

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
for path in (str(APP_DIR), str(ROOT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

st.set_page_config(
    page_title="FinScore", 
    layout="wide",
    page_icon=str(APP_DIR / "assets" / "logo_fin1a_fav.png")
)

from components import nav, render_sidebar, render_topbar  # noqa: E402
from components.session_state import ensure_defaults  # noqa: E402
from components.theme import inject_global_css  # noqa: E402

from views import analise as view_analise  # noqa: E402
from views import lancamentos as view_lancamentos  # noqa: E402
from views import parecer as view_parecer  # noqa: E402
from views import novo as view_novo  # noqa: E402
from views import sobre, contato, guia_rapido  # noqa: E402
from views import faq as view_faq  # noqa: E402
from views import glossario as view_glossario  # noqa: E402
from views import home as view_home  # noqa: E402
from views import processo as view_processo  # noqa: E402
from app_front.views import cadastros  # noqa: E402
from app_front.views import estoque  # noqa: E402


def _load_css() -> None:
    css_path = APP_DIR / "styles" / "main.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


_load_css()
inject_global_css()
ensure_defaults()
nav.sync_from_url()


def _enforce_flow() -> None:
    slug = nav.current()
    ss = st.session_state

    if slug == "lanc" and not ss.get("_flow_started"):
        nav.force("novo")
        st.rerun()

    if slug == "analise" and not ss.get("liberar_analise"):
        nav.force("lanc" if ss.get("_flow_started") else "novo")
        st.rerun()

    if slug == "parecer" and not ss.get("liberar_parecer"):
        nav.force("analise" if ss.get("liberar_analise") else "novo")
        st.rerun()


_enforce_flow()

CURRENT_SLUG = nav.current()
TOPBAR_HIGHLIGHTS = {
    "home": "Home",
    "def1": "Estoque",
    "def2": "Cadastros",
    "guia": "Guia Rápido",
}

render_topbar(current_page=TOPBAR_HIGHLIGHTS.get(CURRENT_SLUG))
render_sidebar(CURRENT_SLUG)

ROUTES = {
    "home": view_home.render,
    "proc": view_processo.render,
    "novo": view_novo.render,
    "lanc": view_lancamentos.render,
    "analise": view_analise.render,
    "parecer": view_parecer.render,
    "sobre": sobre.render,
    "contato": contato.render,
    "guia": guia_rapido.render,
    "faq": view_faq.render,
    "glossario": view_glossario.render,
    "def1": estoque.render,
    "def2": cadastros.render,
}

render_function = ROUTES.get(CURRENT_SLUG)
if render_function is None:
    fallback_slug = "home"
    nav.force(fallback_slug)
    render_function = ROUTES[fallback_slug]

render_function()
