# components/nav.py
from pathlib import Path
import streamlit as st
from components.config import SIDEBAR_MENU, SLUG_MAP, DEBUG_MODE
from components.state_manager import AppState

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOGO = ASSETS / "logo5.png"


def render_sidebar(current_page: str = "Home"):
    """
    Renderiza a barra lateral com dropdown e submenu (HTML <details>/<summary>).
    Retorna a página selecionada (label) quando o usuário clica em um item,
    caso contrário, retorna None.
    """
    client_token = AppState.get_client_token()

    with st.sidebar:
        # Estilos CSS para a sidebar
        st.markdown(
            """
            <style>
            .side-logo { margin-top: -350px !important; padding-top: 0px !important; }
            /* Container do menu */
            .fs-menu { font-family: inherit; }
            .fs-menu a { text-decoration: none; color: #245561; display: block; }
            .fs-menu .item, .fs-menu summary { 
                padding: 10px 12px; border-radius: 0; margin: 0; list-style: none; 
                background: #cdcdcd; color: #245561; cursor: pointer; font-weight: 700;
            }
            .fs-menu .item:hover, .fs-menu summary:hover { background: #e9e9e9; }
            .fs-menu details { background: #cdcdcd; }
            .fs-menu details[open] > summary { background: #d6d6d6; }
            .fs-menu .active { background: #d6d6d6; border-left: 3px solid #9aa0a6; }
            .fs-menu .submenu a { padding: 8px 16px 8px 28px; }
            .fs-menu .item.disabled,
            .fs-menu .submenu a.disabled {
                background: #e4e4e4 !important;
                color: #7a7a7a !important;
                cursor: not-allowed !important;
                pointer-events: none !important;
                opacity: 0.85;
            }
            .fs-menu .item.disabled:hover,
            .fs-menu .submenu a.disabled:hover {
                background: #e4e4e4 !important;
            }
            /* Caret */
            .fs-menu summary { position: relative; }
            .fs-menu summary::marker { display: none; }
            .fs-menu summary::-webkit-details-marker { display: none; }
            .fs-menu summary .caret { position: absolute; right: 10px; transition: transform .2s ease; }
            details[open] > summary .caret { transform: rotate(180deg); }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Logo
        st.markdown('<div class="side-logo">', unsafe_allow_html=True)
        st.image(str(LOGO))
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Determina slug atual a partir do nome da página atual
        reverse_slug_map = {v: k for k, v in SLUG_MAP.items()}
        current_slug = reverse_slug_map.get(current_page, "home")

        liberar_lanc = bool(st.session_state.get("liberar_lancamentos"))
        liberar_analise = bool(st.session_state.get("liberar_analise")) or liberar_lanc
        liberar_parecer = bool(st.session_state.get("liberar_parecer")) or liberar_lanc

        def is_locked(slug: str) -> bool:
            if slug == "lanc":
                return not liberar_lanc
            if slug == "analise":
                return not liberar_analise
            if slug == "parecer":
                return not liberar_parecer
            return False

        # Constrói o HTML do menu com submenus
        def build_menu_html():
            html = ['<nav class="fs-menu">']
            for item in SIDEBAR_MENU:
                label = item["label"]
                slug = item["slug"]
                children = item.get("children", [])

                is_active_top = (current_slug == slug) or any(current_slug == c.get("slug") for c in children)
                open_attr = " open" if is_active_top else ""
                active_cls = " active" if current_slug == slug else ""

                href = f"?p={slug}"
                if client_token:
                    href = f"?p={slug}&sid={client_token}"

                if children:
                    html.append(
                        f'<details{open_attr}><summary class="item{active_cls}">{label}<span class="caret">▾</span></summary>'
                    )
                    for c in children:
                        c_label, c_slug = c["label"], c["slug"]
                        c_active = " active" if current_slug == c_slug else ""
                        child_href = f"?p={c_slug}"
                        if client_token:
                            child_href = f"?p={c_slug}&sid={client_token}"
                        c_locked = is_locked(c_slug) and current_slug != c_slug
                        c_disabled_cls = " disabled" if c_locked else ""
                        c_attrs = ' aria-disabled="true" tabindex="-1"' if c_locked else ""
                        if c_locked:
                            child_href = "#"
                        html.append(
                            f'<div class="submenu"><a class="item{c_active}{c_disabled_cls}" href="{child_href}" target="_self"{c_attrs}>{c_label}</a></div>'
                        )
                    html.append('</details>')
                else:
                    locked = is_locked(slug) and current_slug != slug
                    disabled_cls = " disabled" if locked else ""
                    attrs = ' aria-disabled="true" tabindex="-1"' if locked else ""
                    if locked:
                        href = "#"
                    html.append(f'<a class="item{active_cls}{disabled_cls}" href="{href}" target="_self"{attrs}>{label}</a>')
            html.append('</nav>')
            return "\n".join(html)

        st.markdown(build_menu_html(), unsafe_allow_html=True)

        # Detecta cliques: como usamos links, deixamos a URL conduzir; o AppState
        # fará sync em app.py. Para manter API, checamos se o parâmetro mudou.
        # Se mudou, retornamos o label correspondente (para fluxo atual do app).
        qp = st.query_params.get("p")
        if qp:
            qp = qp[0] if isinstance(qp, list) else qp
            target_label = SLUG_MAP.get(qp)
            if target_label and target_label != current_page:
                return target_label
        return None
            
    return None


# Compatibilidade (evite usar em novo codigo)
from components.config import SIDEBAR_MENU as PAGES

