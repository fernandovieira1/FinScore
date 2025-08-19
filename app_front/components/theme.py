# app_front/components/theme.py
import streamlit as st

PALETTE = {
    "blue_dark":   "#0b5ea8",  # primário
    "blue_darker": "#084a86",
    "blue_light":  "#e8f2fb",
    "gray_bg":     "#f5f7fb",
    "gray_border": "#e6eaf0",
    "text":        "#111827",
    "muted":       "#6b7280",
    "white":       "#ffffff",
    "cherry":      "#c81e1e",
    "amber":       "#b45309",
    "green":       "#15803d",
}

def inject_global_css():
    c = PALETTE
    st.markdown(
        f"""
        <style>
        /* ====== Layout geral ====== */
        body, [data-testid="stAppViewContainer"] {{
            background: {c["gray_bg"]};
        }}
        h1,h2,h3,h4,h5,h6 {{ color: {c["text"]}; }}

        /* ====== Sidebar ====== */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {c["blue_dark"]} 0%, {c["blue_darker"]} 100%);
            color: {c["white"]} !important;
            border-right: 1px solid {c["blue_darker"]};
        }}
        [data-testid="stSidebar"] * {{ color: {c["white"]} !important; }}

        /* Cards / blocos brancos */
        .card {{
            background: {c["white"]};
            border: 1px solid {c["gray_border"]};
            border-radius: 14px;
            padding: 16px 18px;
        }}

        /* ====== Tabs ====== */
        .stTabs [data-baseweb="tab-list"] button {{
            color: {c["muted"]};
        }}
        .stTabs [data-baseweb="tab"] [role="tab"] {{
            border-bottom: 2px solid transparent;
        }}
        .stTabs [aria-selected="true"] {{
            border-bottom: 2px solid {c["blue_dark"]} !important;
            color: {c["text"]} !important;
        }}

        /* ====== Logo sobreposto ====== */
        #brand-logo {{
            position: fixed;
            top: 10px; left: 12px;
            z-index: 1000;
            display: flex; align-items: center; gap: 8px;
        }}
        #brand-logo img {{ height: 42px; width: auto; }}
        #brand-logo .brand-text {{ color: {c["white"]}; font-weight: 700; }}

        /* ====== Pequenos acentos de cor ====== */
        .accent-cherry {{ color: {c["cherry"]}; }}
        .accent-amber  {{ color: {c["amber"]};  }}
        .accent-green  {{ color: {c["green"]};  }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_logo_overlay(path="assets/logo.png", text=""):
    # Mostra o logo sobre a sidebar (canto superior esquerdo)
    st.markdown(
        f"""
        <div id="brand-logo">
            <img src="{path}" alt="logo">
            {'<span class="brand-text">'+text+'</span>' if text else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
