# app_front/components/theme.py
import streamlit as st

# Paleta de cores do tema
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

def get_palette():
    """Retorna a paleta de cores"""
    return PALETTE

def inject_global_css():
    c = get_palette()
    
    st.markdown(
        f"""
        <style>
        /* ====== Layout geral ====== */
        body, [data-testid="stAppViewContainer"], .main {{
            background-color: {c["gray_bg"]} !important;
        }}
        [data-testid="stAppViewContainer"] > .main {{
            background-color: {c["gray_bg"]} !important;
        }}
        section.main > div {{
            background-color: {c["gray_bg"]};
        }}
        h1,h2,h3,h4,h5,h6 {{ color: {c["text"]}; }}
        p, span, div {{ color: {c["text"]}; }}

        /* ====== Sidebar ====== */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {c["blue_dark"]} 0%, {c["blue_darker"]} 100%);
            color: {c["white"]} !important;
            border-right: 1px solid {c["blue_darker"]};
        }}
        
        /* Texto da sidebar - branco */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] button {{
            color: {c["white"]} !important;
        }}
        
        /* Seta do dropdown menu na sidebar - azul escuro #235561 */
        [data-testid="stSidebar"] details summary svg,
        [data-testid="stSidebar"] .streamlit-expanderHeader svg,
        [data-testid="stSidebar"] [data-testid="stExpanderToggleIcon"] svg,
        [data-testid="stSidebar"] details svg,
        [data-testid="stSidebar"] summary svg {{
            fill: #235561 !important;
            color: #235561 !important;
        }}
        [data-testid="stSidebar"] details summary svg *,
        [data-testid="stSidebar"] .streamlit-expanderHeader svg *,
        [data-testid="stSidebar"] [data-testid="stExpanderToggleIcon"] svg * {{
            fill: #235561 !important;
            color: #235561 !important;
        }}

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
        
        /* ====== Estilos adicionais de tema ====== */
        /* Containers e elementos de conteúdo */
        .stMarkdown, .stText {{
            color: {c["text"]};
        }}
        
        /* Inputs e elementos de formulário */
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox > div > div > div,
        .stNumberInput > div > div > input {{
            background-color: {c["white"]};
            color: {c["text"]};
            border-color: {c["gray_border"]};
        }}
        
        /* Dataframes e tabelas */
        .dataframe, [data-testid="stDataFrame"] {{
            background-color: {c["white"]};
            color: {c["text"]};
        }}
        .dataframe thead tr th {{
            background-color: {c["blue_light"]};
            color: {c["text"]};
        }}
        
        /* Métricas */
        [data-testid="stMetricValue"] {{
            color: {c["text"]};
        }}
        [data-testid="stMetricLabel"] {{
            color: {c["muted"]};
        }}
        
        /* Botões */
        .stButton > button {{
            background-color: {c["white"]};
            color: {c["text"]};
            border: 1px solid {c["gray_border"]};
        }}
        .stButton > button:hover {{
            background-color: {c["blue_light"]};
            border-color: {c["blue_dark"]};
        }}
        
        /* Info/Warning/Error/Success boxes */
        .stAlert {{
            background-color: {c["white"]};
            border-color: {c["gray_border"]};
        }}
        
        /* Expanders */
        .streamlit-expanderHeader {{
            background-color: {c["white"]};
            color: {c["text"]};
        }}
        
        /* Code blocks */
        .stCodeBlock, code {{
            background-color: {c["blue_light"]};
            color: {c["text"]};
        }}
        
        /* Plotly charts - modo escuro */
        .js-plotly-plot .plotly .main-svg {{
            background-color: transparent !important;
        }}
        
        /* Dividers */
        hr, .stDivider {{
            border-color: {c["gray_border"]} !important;
        }}
        
        /* Radio buttons e checkboxes */
        .stRadio > label, .stCheckbox > label {{
            color: {c["text"]};
        }}
        
        /* File uploader */
        [data-testid="stFileUploadDropzone"] {{
            background-color: {c["white"]};
            border-color: {c["gray_border"]};
        }}
        [data-testid="stFileUploadDropzoneInstructions"] {{
            color: {c["muted"]};
        }}
        
        /* Sidebar no dark mode - ajuste adicional */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            color: {c["white"]} !important;
        }}
        
        /* Headers e títulos no dark */
        h1, h2, h3, h4, h5, h6 {{
            color: {c["text"]} !important;
        }}
        
        /* Links */
        a {{
            color: {c["blue_dark"]};
        }}
        a:hover {{
            color: {c["blue_darker"]};
        }}
        
        /* Progress bar */
        .stProgress > div > div > div {{
            background-color: {c["blue_dark"]};
        }}
        
        /* Spinner */
        .stSpinner > div {{
            border-top-color: {c["blue_dark"]};
        }}
        
        /* Tooltips */
        [data-testid="stTooltipIcon"] {{
            color: {c["muted"]};
        }}
        
        /* Date input */
        .stDateInput > div > div > input {{
            background-color: {c["white"]};
            color: {c["text"]};
            border-color: {c["gray_border"]};
        }}
        
        /* Time input */
        .stTimeInput > div > div > input {{
            background-color: {c["white"]};
            color: {c["text"]};
            border-color: {c["gray_border"]};
        }}
        
        /* Slider */
        .stSlider > div > div > div {{
            color: {c["text"]};
        }}
        
        /* Caption text */
        .stCaptionContainer, [data-testid="stCaptionContainer"] {{
            color: {c["muted"]};
        }}
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
