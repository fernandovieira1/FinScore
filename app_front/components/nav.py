import streamlit as st
from streamlit_option_menu import option_menu

def render_sidebar():
    with st.sidebar:
        # Logo no topo
        st.image("app_front/assets/logo5.png", use_column_width=True)

        # Menu lateral com blocos azuis
        pagina = option_menu(
            None,
            ["Novo", "Resumo", "Tabelas", "Gráficos", "Parecer", "Sobre"],
            icons=["plus-circle", "bar-chart", "table", "graph-up", "file-earmark-text", "info-circle"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {"background-color": "#0d47a1", "padding": "20px"},
                "icon": {"color": "white", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "10px 0",
                    "color": "white",
                    "border-radius": "10px",
                },
                "nav-link-selected": {"background-color": "#1976d2"},
            },
        )
    return pagina
