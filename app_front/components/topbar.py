# components/topbar.py
import streamlit as st
import base64
from pathlib import Path
from components.config import TOPBAR_PAGES

def render_topbar(current_page: str | None = None) -> None:
    """Renderiza a barra superior de navegação"""
    # Logo
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    try:
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        logo_src = f"data:image/png;base64,{logo_b64}"
    except Exception:
        logo_src = ""

    def is_active(page: str) -> str:
        return "active" if current_page == page else ""

    st.markdown(
        f"""
        <style>
          :root {{
            --tb-bg:#fff; --tb-fg:#1f2937; --tb-fg-muted:#071700;
            --tb-border: rgba(2,6,23,.10); --tb-hover: rgba(2,6,23,.06);
            --radius:14px;
          }}
          .mm-wrap {{ display:flex; justify-content:flex-start; margin:10px 0; width:100%; }}
          .mm-topbar {{
            width:100%; max-width:none; height:60px; padding:0 18px;
            display:flex; align-items:center; justify-content:space-between;
            background:var(--tb-bg); color:var(--tb-fg);
            border:1px solid var(--tb-border); border-radius:var(--radius);
          }}
          .nav {{ display:flex; align-items:center; gap:16px; margin:0; }}
          .pill-btn, .pill-btn:link, .pill-btn:visited, .pill-btn:active {{
            display:inline-block; padding:6px 10px; border-radius:10px;
            color:var(--tb-fg-muted); font-weight:600; font-size:.92rem; line-height:1;
            border:1px solid transparent; text-decoration:none;
            cursor: pointer;
          }}
          .pill-btn:hover, .pill-btn.active {{
            color:var(--tb-fg); background:var(--tb-hover); border-color:var(--tb-border);
            text-decoration:none;
          }}
          .right {{ display:flex; align-items:center; gap:14px; }}
          .assertif-logo {{ height:22px; display:block; border-radius:4px; }}
          
          /* Estilo para botões sociais e de configuração */
          .social-btn, .theme-btn, .config-btn {{
            display: flex; align-items: center; justify-content: center;
            width: 30px; height: 30px; border-radius: 50%;
            background: transparent;
            border: 1px solid rgba(2,6,23,.10);
            font-size: 14px; cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
          }}
          /* Cores para todos os botões - forçando com máxima especificidade */
          .social-btn,
          .social-btn i,
          .social-btn .fab,
          .social-btn .fas,
          a.social-btn,
          a.social-btn i,
          button.theme-btn,
          button.theme-btn i,
          button.config-btn,
          button.config-btn i {{
            color: #999999 !important;
          }}
          
          .social-btn:hover,
          .social-btn:hover i,
          .social-btn:hover .fab,
          .social-btn:hover .fas,
          a.social-btn:hover,
          a.social-btn:hover i,
          button.theme-btn:hover,
          button.theme-btn:hover i,
          button.config-btn:hover,
          button.config-btn:hover i {{
            background: rgba(2,6,23,.06) !important;
            color: #bcbcbc !important;
          }}
        </style>

        <!-- Link para Font Awesome (ícones) -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        
        <!-- CSS adicional para sobrescrever cores do Font Awesome -->
        <style>
          /* Garantir que os ícones não herdem cores do Font Awesome */
          .fa, .fab, .fas, .far, .fal, .fad, .fak {{
            color: inherit !important;
          }}
        </style>

        <div class="mm-wrap">
          <div class="mm-topbar">
            <nav class="nav">
              <a class="pill-btn {is_active('Home')}" href="?p=home" target="_self">Página Inicial</a>
              <a class="pill-btn {is_active('Estoque')}" href="?p=def1" target="_self">Estoque</a>
              <a class="pill-btn {is_active('Cadastros')}" href="?p=def2" target="_self">Cadastros</a>
              <a class="pill-btn {is_active('Guia Rápido')}" href="?p=guia" target="_self">Guia Rápido</a>
            </nav>
            <div class="right">
              <a href="https://www.facebook.com/assertif/about/" class="social-btn" title="Facebook" target="_blank" rel="noopener noreferrer">
                <i class="fab fa-facebook-f"></i>
              </a>
              <a href="https://www.youtube.com/@grupoassertif" class="social-btn" title="YouTube" target="_blank" rel="noopener noreferrer">
                <i class="fab fa-youtube"></i>
              </a>
              <a href="https://www.linkedin.com/company/grupoassertif" class="social-btn" title="LinkedIn" target="_blank" rel="noopener noreferrer">
                <i class="fab fa-linkedin-in"></i>
              </a>
              <button class="theme-btn" title="Alternar tema">
                <i class="fas fa-moon"></i>
              </button>
              <button class="config-btn" title="Configurações">
                <i class="fas fa-cog"></i>
              </button>
              <img class="assertif-logo" src="{logo_src}" alt="assertif"/>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
