# components/nav.py
from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu
from components.config import SIDEBAR_PAGES, DEBUG_MODE

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOGO = ASSETS / "logo5.png"

def render_sidebar(current_page: str = "Home"):
    """
    Renderiza a barra lateral de navegação
    Retorna a página selecionada ou None se não houver mudança
    """
    with st.sidebar:
        # Estilos CSS para a sidebar
        st.markdown(
            """
            <style>
            .side-logo {
                margin-top: -350px !important;
                padding-top: 0px !important;
            }
            .nav-link:hover {
                background-color: #e9e9e9 !important;
                cursor: pointer !important;
            }
            .nav-link {
                cursor: pointer !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Logo
        st.markdown('<div class="side-logo">', unsafe_allow_html=True)
        st.image(str(LOGO))
        st.markdown('</div>', unsafe_allow_html=True)

        # Posiciona a seleção no item correspondente à página atual
        try:
            default_idx = SIDEBAR_PAGES.index(current_page)
        except ValueError:
            default_idx = 0  # Fallback para "Home"

        # Menu de navegação
        pagina_selecionada = option_menu(
            None,
            SIDEBAR_PAGES,
            icons=["house", "plus-circle", "graph-up", "file-earmark-text", "info-circle", "envelope"],
            menu_icon="cast",
            default_index=default_idx,
            orientation="vertical",
            styles={
                "container": {
                    "background-color": "#cdcdcd", 
                    "padding": "0px", 
                    "border-radius": "0px"
                },
                "icon": {
                    "color": "#001733", 
                    "font-size": "18px"
                },
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0",
                    "padding": "10px 12px",
                    "color": "#001733",
                    "background-color": "#cdcdcd",
                    "border-radius": "0px",
                    "cursor": "pointer",
                },
                "nav-link-selected": {
                    "background-color": "#d6d6d6",
                    "color": "#001733",
                    "border-left": "3px solid #9aa0a6",
                },
            },
        )
        
        # Debug info
        if DEBUG_MODE:
            st.write(f"📌 Sidebar: {pagina_selecionada}")
            
    return pagina_selecionada

# components/nav.py (adicione no final do arquivo)

# Mantém compatibilidade com imports existentes
from components.config import SIDEBAR_PAGES as PAGES