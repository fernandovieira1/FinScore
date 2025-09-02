from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOGO = ASSETS / "logo5.png"

def render_sidebar():
    with st.sidebar:
        # Logo centralizado automaticamente (CSS .side-logo cuida do alinhamento)
        st.markdown('<div class="side-logo">', unsafe_allow_html=True)
        st.image(str(LOGO))  # sem width fixo -> CSS limita a 80% e centraliza
        st.markdown('</div>', unsafe_allow_html=True)

        # Menu integrado na cor da sidebar
        pagina = option_menu(
            None,
            ["Novo", "Resumo", "Tabelas", "Gráficos", "Parecer", "Sobre"],
            icons=["plus-circle", "bar-chart", "table", "graph-up", "file-earmark-text", "info-circle"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {
                    "background-color": "#cdcdcd",
                    "padding": "0px",
                    "border-radius": "0px",
                },
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
                "nav-link-selected": {
                    "background-color": "#bdbdbd",
                    "color": "#001733",
                    "border-left": "4px solid #8a8a8a",
                },
            },
        )
    return pagina
