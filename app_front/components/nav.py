# components/nav.py
from pathlib import Path
import streamlit as st
from components.config import SIDEBAR_MENU, SLUG_MAP, DEBUG_MODE
from components.state_manager import AppState

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOGO = ASSETS / "logo5.png"


def render_sidebar(current_page: str = "Home"):
    """
    Sidebar sem links HTML (que causam reload total).
    Usa widgets nativos para preservar st.session_state ao navegar.

    Retorna None: aplica navegacao via AppState + st.rerun.
    """
    with st.sidebar:
        # Logo
        try:
            st.image(str(LOGO))
        except Exception:
            pass

        # Slug/pagina atual
        reverse_slug_map = {v: k for k, v in SLUG_MAP.items()}
        current_slug = reverse_slug_map.get(current_page, "home")

        # Permissoes
        ss = st.session_state
        lanc_enabled = ss.get("liberar_lancamentos", False)
        analise_enabled = ss.get("liberar_analise", False)
        parecer_enabled = ss.get("liberar_parecer", False)

        # Menu hierarquico
        for item in SIDEBAR_MENU:
            label = item["label"]
            slug = item["slug"]
            children = item.get("children", [])

            if children:
                expanded = (current_slug == slug) or any(current_slug == c.get("slug") for c in children)
                with st.expander(label, expanded=expanded):
                    for c in children:
                        c_label, c_slug = c["label"], c["slug"]
                        disabled = (
                            (c_slug == "lanc" and not lanc_enabled) or
                            (c_slug == "analise" and not analise_enabled) or
                            (c_slug == "parecer" and not parecer_enabled)
                        )
                        if st.button(c_label, key=f"side_{c_slug}", disabled=disabled, use_container_width=True):
                            AppState.set_current_page(SLUG_MAP.get(c_slug, c_label), "sidebar", slug=c_slug)
                            AppState.sync_to_query_params()
                            st.rerun()
            else:
                if st.button(label, key=f"side_{slug}", use_container_width=True):
                    AppState.set_current_page(SLUG_MAP.get(slug, label), "sidebar", slug=slug)
                    AppState.sync_to_query_params()
                    st.rerun()

        return None
    return None


# Compatibilidade (evite usar em novo codigo)
from components.config import SIDEBAR_MENU as PAGES

