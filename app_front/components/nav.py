# components/nav.py
from pathlib import Path
import streamlit as st
from components.config import SIDEBAR_MENU, SLUG_MAP, DEBUG_MODE
from components.state_manager import AppState

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOGO = ASSETS / "logo_fin1a.png"


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
            .side-logo { margin-top: 0 !important; padding-top: 0 !important; }
            /* Container do menu */
            .fs-menu { font-family: inherit; }
            .fs-menu a { text-decoration: none; color: #245561; display: block; }
            .fs-menu .item, .fs-menu summary { 
                padding: 10px 12px; border-radius: 0; margin: 0; list-style: none; 
                background: #cdcdcd; color: #245561; cursor: pointer; font-weight: 700;
            }
            .fs-menu .item:hover, .fs-menu summary:hover { background: #cdcdcd; }
            .fs-menu details { background: #cdcdcd; }
            .fs-menu details[open] > summary { background: #cdcdcd; }
            .fs-menu .active { background: #cdcdcd; border-left: 3px solid #9aa0a6; }
            .fs-menu .submenu a { padding: 8px 16px 8px 28px; }
            .fs-menu .item.disabled,
            .fs-menu .submenu a.disabled {
                background: #cdcdcd !important;
                color: #7a7a7a !important;
                cursor: not-allowed !important;
                pointer-events: none !important;
                opacity: 0.85;
            }
            .fs-menu .item.disabled:hover,
            .fs-menu .submenu a.disabled:hover {
                background: #cdcdcd !important;
            }
            /* Caret */
            .fs-menu summary { position: relative; }
            .fs-menu summary::marker { display: none; }
            .fs-menu summary::-webkit-details-marker { display: none; }
            .fs-menu summary .caret { position: absolute; right: 10px; transition: transform .2s ease; color: #235561 !important; }
            details[open] > summary .caret { transform: rotate(180deg); }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <script>
            (function() {
                const win = window.parent || window;
                if (!win || win.__FS_SIDEBAR_RESIZER_INIT__) { return; }
                win.__FS_SIDEBAR_RESIZER_INIT__ = true;
                const doc = win.document;

                const getVarPx = (name, fallback) => {
                    try {
                        const value = getComputedStyle(doc.documentElement).getPropertyValue(name).trim();
                        const parsed = parseFloat(value.replace('px', ''));
                        return Number.isFinite(parsed) ? parsed : fallback;
                    } catch (e) {
                        return fallback;
                    }
                };

                const MIN = getVarPx('--fs-sidebar-min', 220);
                const MAX = getVarPx('--fs-sidebar-max', 547);
                const DEF = getVarPx('--fs-sidebar-default', 274);
                const state = win.__FS_SIDEBAR_RESIZER_STATE__ || { width: DEF };
                win.__FS_SIDEBAR_RESIZER_STATE__ = state;

                const clampWidth = (value) => Math.min(MAX, Math.max(MIN, value));

                const applyWidth = (sidebar, value) => {
                    const target = clampWidth(value || state.width || DEF);
                    state.width = target;
                    sidebar.style.setProperty('--fs-sidebar-width', `${target}px`);
                };

                const ensureResizer = () => {
                    const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
                    if (!sidebar) { return; }

                    applyWidth(sidebar, state.width);

                    if (sidebar.querySelector('.fs-sidebar-resizer')) { return; }

                    const resizer = doc.createElement('div');
                    resizer.className = 'fs-sidebar-resizer';
                    sidebar.appendChild(resizer);

                    let dragging = false;
                    let startX = 0;
                    let startWidth = state.width || DEF;

                    const onMouseDown = (event) => {
                        dragging = true;
                        resizer.classList.add('active');
                        startX = event.clientX;
                        const currentWidth = parseFloat(getComputedStyle(sidebar).width);
                        startWidth = Number.isFinite(currentWidth) ? currentWidth : state.width || DEF;
                        event.preventDefault();
                    };

                    const onMouseMove = (event) => {
                        if (!dragging) { return; }
                        const delta = event.clientX - startX;
                        const newWidth = clampWidth(startWidth + delta);
                        sidebar.style.setProperty('--fs-sidebar-width', `${newWidth}px`);
                        state.width = newWidth;
                    };

                    const stopDrag = () => {
                        if (!dragging) { return; }
                        dragging = false;
                        resizer.classList.remove('active');
                        sidebar.style.setProperty('--fs-sidebar-width', `${state.width}px`);
                    };

                    resizer.addEventListener('mousedown', onMouseDown);
                    doc.addEventListener('mousemove', onMouseMove);
                    doc.addEventListener('mouseup', stopDrag);
                    doc.addEventListener('mouseleave', stopDrag);

                    const attrObserver = new MutationObserver(() => {
                        const expanded = sidebar.getAttribute('aria-expanded');
                        if (expanded !== 'false') {
                            applyWidth(sidebar, state.width);
                        }
                    });
                    attrObserver.observe(sidebar, { attributes: true, attributeFilter: ['aria-expanded'] });
                };

                const mo = new MutationObserver(() => ensureResizer());
                mo.observe(doc.body, { childList: true, subtree: true });

                ensureResizer();
            })();
            </script>
            """,
            unsafe_allow_html=True,
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
        # Parecer só é liberado quando o usuário clicar no botão "Aprovar" em /Análise/Scores
        liberar_parecer = bool(st.session_state.get("liberar_parecer"))

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
        if AppState.consume_sidebar_skip():
            qp = None
        else:
            qp = st.query_params.get("p")
        if qp:
            qp = qp[0] if isinstance(qp, list) else qp
            target_label = SLUG_MAP.get(qp)
            if target_label and target_label != current_page:
                if AppState.is_slug_blocked(qp):
                    return None
                AppState.clear_nav_lock()
                return target_label
        return None
            
    return None


# Compatibilidade (evite usar em novo codigo)
from components.config import SIDEBAR_MENU as PAGES

