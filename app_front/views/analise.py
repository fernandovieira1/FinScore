import streamlit as st

# imports RELATIVOS (arquivos no MESMO pacote 'views')
try:
    from .resumo import render as render_resumo
except Exception as e:
    def render_resumo():
        st.error(f"Não foi possível importar 'resumo.py' (render). Detalhe: {e}")

try:
    from .graficos import render as render_graficos
except Exception as e:
    def render_graficos():
        st.error(f"Não foi possível importar 'graficos.py'. Detalhe: {e}")

try:
    from .tabelas import render as render_tabelas
except Exception as e:
    def render_tabelas():
        st.error(f"Não foi possível importar 'tabelas.py'. Detalhe: {e}")

def render():
    ss = st.session_state
    ss.setdefault("analise_tab", "Resumo")

    # CSS para centralizar as abas
    st.markdown(
        """
        <style>
        div[data-testid="stTabs"] > div[role="tablist"],
        div[data-baseweb="tab-list"] {
            display: flex;
            justify-content: center;   /* centraliza as abas */
            gap: 2rem;                 /* espaço entre abas */
        }
        div[data-testid="stTabs"] button[role="tab"],
        div[data-baseweb="tab"] {
            flex: 0 0 auto;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab_resumo, tab_graficos, tab_tabelas = st.tabs(["📊 Resumo", "📈 Gráficos", "📄 Tabelas"])

    with tab_resumo:
        render_resumo()
    with tab_graficos:
        render_graficos()
    with tab_tabelas:
        render_tabelas()
