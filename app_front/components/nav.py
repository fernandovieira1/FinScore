from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOGO = ASSETS / "logo5.png"

# TODAS as páginas disponíveis na sidebar
PAGES = ["Lançamentos", "Análise", "Parecer", "Sobre", "Contato"]

def render_sidebar(current_page: str = "Home"):
    with st.sidebar:
        # hover mais claro nos itens
        st.markdown(
            """
            <style>
            .side-logo {
                margin-top: -350px !important;
                padding-top: 0px !important;
            }
            /* suaviza o hover dos itens do option_menu */
            .nav-link:hover{
                background-color: #e9e9e9 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="side-logo">', unsafe_allow_html=True)
        st.image(str(LOGO))
        st.markdown('</div>', unsafe_allow_html=True)

        # posiciona a seleção no item correspondente à página atual
        try:
            default_idx = PAGES.index(current_page)
        except ValueError:
            default_idx = 0  # Fallback para "Home"

        pagina = option_menu(
            None,
            PAGES,
            icons=["house", "plus-circle", "graph-up", "file-earmark-text", "book", "info-circle", "envelope"],
            menu_icon="cast",
            default_index=default_idx,
            orientation="vertical",
            styles={
                "container": {"background-color": "#cdcdcd", "padding": "0px", "border-radius": "0px"},
                "icon": {"color": "#001733", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0",
                    "padding": "10px 12px",
                    "color": "#001733",
                    "background-color": "#cdcdcd",
                    "border-radius": "0px",
                },
                # seleção mais clara e sutil
                "nav-link-selected": {
                    "background-color": "#d6d6d6",
                    "color": "#001733",
                    "border-left": "3px solid #9aa0a6",
                },
            },
        )
    return pagina