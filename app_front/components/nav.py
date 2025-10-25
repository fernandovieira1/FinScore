from __future__ import annotations

from pathlib import Path

import streamlit as st

from .config import SIDEBAR_MENU, SLUG_MAP

_FLOWS = ("novo", "lanc", "analise", "parecer")
_FORWARD_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "novo": ("lanc",),
    "lanc": ("analise",),
    "analise": ("parecer",),
    "parecer": tuple(),
}

_ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
_LOGO_PATH = _ASSETS_DIR / "logo_fin1a.png"


def _is_flow_step(slug: str) -> bool:
    return slug in _FLOWS


def current(default: str = "home") -> str:
    """Return the current slug registered in the session."""
    return st.session_state.setdefault("page", default)


def _set(target: str) -> None:
    st.session_state["page"] = target
    st.query_params["p"] = target


def _can_enter_flow_step(target: str) -> bool:
    if target == "lanc":
        return bool(st.session_state.get("_flow_started"))
    if target == "analise":
        return bool(st.session_state.get("liberar_analise"))
    if target == "parecer":
        return bool(st.session_state.get("liberar_parecer"))
    return True


def go(target: str) -> bool:
    """
    Attempt to move to the given target respecting the FinScore forward flow.
    Returns True when the transition happened.
    """
    target = target or "home"
    origin = current()
    ss = st.session_state

    if ss.get("_lock_parecer") and target in {"novo", "lanc"}:
        if target == "novo":
            ss["_nav_block_message"] = (
                "⚠️ Um parecer já foi gerado e permanece em cache. "
                "Usar o botão 'Iniciar' na seção Novo reiniciará o processo e apagará os dados atuais. "
                "Se desejar começar de novo, utilize o botão 'Iniciar novo ciclo' ao final do parecer."
            )
        else:
            ss["_nav_block_message"] = (
                "⚠️ Os lançamentos ficam protegidos após a geração do parecer. "
                "Inicie um novo ciclo para editar ou reenviar os dados contábeis."
            )
        return False

    if ss.get("_lock_parecer") and origin == "parecer" and target == "analise":
        _set(target)
        return True

    if target == origin:
        _set(target)
        return True

    if _is_flow_step(origin) and _is_flow_step(target):
        allowed = _FORWARD_TRANSITIONS.get(origin, ())
        if target not in allowed:
            return False
        if not _can_enter_flow_step(target):
            return False
        _set(target)
        return True

    if _is_flow_step(target) and not _can_enter_flow_step(target):
        return False

    _set(target)
    return True


def force(target: str) -> None:
    """Force the session to the target slug."""
    _set(target)


def restart() -> None:
    """Reset the flow to the first step."""
    _set("novo")


def sync_from_url() -> None:
    """Synchronise query parameter ?p= with the internal session slug."""
    ss = st.session_state
    qp_value = st.query_params.get("p")
    if isinstance(qp_value, list):
        qp_value = qp_value[-1] if qp_value else None

    if "page" not in ss:
        ss["page"] = qp_value or "home"
        if not qp_value:
            st.query_params["p"] = ss["page"]
        return

    current_slug = ss["page"]

    if qp_value and qp_value != current_slug:
        if not go(qp_value):
            st.query_params["p"] = current_slug
    elif not qp_value:
        st.query_params["p"] = current_slug


def render_sidebar(current_slug: str) -> None:
    """
    Render the sidebar menu preserving the original FinScore appearance.
    Navigation is driven by URL parameters; this helper only builds the HTML.
    """
    liberar_lanc = bool(st.session_state.get("_flow_started"))
    liberar_analise = bool(st.session_state.get("liberar_analise"))
    liberar_parecer = bool(st.session_state.get("liberar_parecer"))

    def is_locked(slug: str) -> bool:
        if slug == "lanc":
            return not liberar_lanc
        if slug == "analise":
            return not liberar_analise
        if slug == "parecer":
            return not liberar_parecer
        return False

    with st.sidebar:
        st.markdown(
            """
            <style>
            .side-logo { margin-top: 0 !important; padding-top: 0 !important; }
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
            .fs-menu summary { position: relative; }
            .fs-menu summary::marker { display: none; }
            .fs-menu summary::-webkit-details-marker { display: none; }
            .fs-menu summary .caret {
                position: absolute;
                right: 10px;
                transition: transform .2s ease;
                color: #235561 !important;
                
                display: inline-block;
            }
            details[open] > summary .caret { transform: rotate(-90deg); }
            </style>
            """,
            unsafe_allow_html=True,
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
                        applyWidth(sidebar, startWidth + delta);
                    };

                    const stopDrag = () => {
                        if (!dragging) { return; }
                        dragging = false;
                        resizer.classList.remove('active');
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

                const observer = new MutationObserver(() => ensureResizer());
                observer.observe(doc.body, { childList: true, subtree: true });

                ensureResizer();
            })();
            </script>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="side-logo">', unsafe_allow_html=True)
        if _LOGO_PATH.exists():
            st.image(str(_LOGO_PATH))
        st.markdown('</div>', unsafe_allow_html=True)

        def build_menu_html() -> str:
            html: list[str] = ['<nav class="fs-menu">']
            for item in SIDEBAR_MENU:
                label = item["label"]
                slug = item["slug"]
                children = item.get("children", [])

                is_active_top = (current_slug == slug) or any(current_slug == c.get("slug") for c in children)
                open_attr = " open" if is_active_top else ""
                active_cls = " active" if current_slug == slug else ""
                href = f"?p={slug}"

                if children:
                    html.append(
                        f'<details{open_attr}><summary class="item{active_cls}">{label}<span class="caret">◂</span></summary>'
                    )
                    for child in children:
                        c_label, c_slug = child["label"], child["slug"]
                        c_active = " active" if current_slug == c_slug else ""
                        child_href = f"?p={c_slug}"
                        locked = is_locked(c_slug) and current_slug != c_slug
                        c_disabled_cls = " disabled" if locked else ""
                        c_attrs = ' aria-disabled="true" tabindex="-1"' if locked else ""
                        if locked:
                            child_href = "#"
                        html.append(
                            f'<div class="submenu"><a class="item{c_active}{c_disabled_cls}" href="{child_href}" target="_self"{c_attrs}>{c_label}</a></div>'
                        )
                    html.append("</details>")
                else:
                    locked = is_locked(slug) and current_slug != slug
                    disabled_cls = " disabled" if locked else ""
                    attrs = ' aria-disabled="true" tabindex="-1"' if locked else ""
                    if locked:
                        href = "#"
                    html.append(
                        f'<a class="item{active_cls}{disabled_cls}" href="{href}" target="_self"{attrs}>{label}</a>'
                    )
            html.append("</nav>")
            return "\n".join(html)

        st.markdown(build_menu_html(), unsafe_allow_html=True)
