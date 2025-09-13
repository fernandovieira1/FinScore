# components/nav.py
from pathlib import Path
import streamlit as st
from components.config import SIDEBAR_MENU, SLUG_MAP, DEBUG_MODE

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOGO = ASSETS / "logo5.png"

def render_sidebar(current_page: str = "Home"):
    """
    Renderiza a barra lateral com dropdown e submenu (HTML <details>/<summary>).
    Retorna a página selecionada (label) quando o usuário clica em um item,
    caso contrário, retorna None.
    """
    with st.sidebar:
        # Estilos CSS para a sidebar
        st.markdown(
            """
            <style>
            .side-logo { margin-top: -350px !important; padding-top: 0px !important; }
            /* Container do menu */
            .fs-menu { font-family: inherit; }
            .fs-menu a { text-decoration: none; color: #001733; display: block; }
            .fs-menu .item, .fs-menu summary { 
                padding: 10px 12px; border-radius: 0; margin: 0; list-style: none; 
                background: #cdcdcd; color: #001733; cursor: pointer; 
            }
            .fs-menu .item:hover, .fs-menu summary:hover { background: #e9e9e9; }
            .fs-menu details { background: #cdcdcd; }
            .fs-menu details[open] > summary { background: #d6d6d6; }
            .fs-menu .active { background: #d6d6d6; border-left: 3px solid #9aa0a6; }
            .fs-menu .submenu a { padding: 8px 16px 8px 28px; }
            /* Caret */
            .fs-menu summary { position: relative; }
            .fs-menu summary::marker { display: none; }
            .fs-menu summary::-webkit-details-marker { display: none; }
            .fs-menu summary .caret { position: absolute; right: 10px; transition: transform .2s ease; }
            details[open] > summary .caret { transform: rotate(180deg); }
            /* Negrito para seções específicas */
            .fs-menu .bold { font-weight: bold; }
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

        # Constrói o HTML do menu com submenus
        def build_menu_html():
            html = ['<nav class="fs-menu">']
            bold_sections = {"Processo", "Sobre", "Contato"}
            for item in SIDEBAR_MENU:
                label = item["label"]
                slug = item["slug"]
                children = item.get("children", [])

                is_active_top = (current_slug == slug) or any(current_slug == c.get("slug") for c in children)
                open_attr = " open" if is_active_top else ""
                active_cls = " active" if current_slug == slug else ""
                bold_cls = " bold" if label in bold_sections else ""

                if children:
                    html.append(
                        f'<details{open_attr}><summary class="item{active_cls}{bold_cls}">{label}<span class="caret">▾</span></summary>'
                    )
                    for c in children:
                        c_label, c_slug = c["label"], c["slug"]
                        c_active = " active" if current_slug == c_slug else ""
                        html.append(f'<div class="submenu"><a class="item{c_active}" href="?p={c_slug}" target="_self">{c_label}</a></div>')
                    html.append('</details>')
                else:
                    html.append(f'<a class="item{active_cls}{bold_cls}" href="?p={slug}" target="_self">{label}</a>')
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

# Mantém compatibilidade com imports existentes (evite usar)
from components.config import SIDEBAR_MENU as PAGES