# app_front/components/topbar.py
import streamlit as st
import base64
from pathlib import Path

def render_topbar(current_page: str | None = None) -> None:
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

          /* container da topbar ocupa toda a largura da área de conteúdo */
          .mm-wrap {{
            display:flex;
            justify-content:flex-start;   /* nada de centralizar */
            margin:10px 0;
            width:100%;
          }}

          /* barra em largura total (alinha com a margem do texto) */
          .mm-topbar {{
            width:100%;
            max-width:none;               /* remove limite de 1060px */
            height:60px;
            padding:0 18px;
            display:flex; align-items:center; justify-content:space-between;
            background:var(--tb-bg); color:var(--tb-fg);
            border:1px solid var(--tb-border);
            border-radius:var(--radius);
          }}

          .nav {{ display:flex; align-items:center; gap:16px; margin:0; }}

          .pill-btn,
          .pill-btn:link,
          .pill-btn:visited,
          .pill-btn:active {{
            display:inline-block; padding:6px 10px; border-radius:10px;
            color:var(--tb-fg-muted); font-weight:600; font-size:.92rem; line-height:1;
            border:1px solid transparent; text-decoration:none;
          }}
          .pill-btn:hover,
          .pill-btn.active {{
            color:var(--tb-fg); background:var(--tb-hover); border-color:var(--tb-border);
            text-decoration:none;
          }}

          .right {{ display:flex; align-items:center; gap:14px; }}
          .assertif-logo {{ height:22px; display:block; border-radius:4px; }}
        </style>

        <div class="mm-wrap">
          <div class="mm-topbar">
            <nav class="nav">
              <a class="pill-btn {is_active("Página Inicial")}"        href="?p=home" target="_self">Página Inicial</a>
              <a class="pill-btn"                              href="?p=lanc" target="_self">Definir1</a>
              <a class="pill-btn"                              href="?p=lanc" target="_self">Definir2</a>
              <a class="pill-btn {is_active("Guia Rápido")}"   href="?p=guia" target="_self">Guia Rápido</a>
            </nav>
            <div class="right">
              <img class="assertif-logo" src="{logo_src}" alt="assertif"/>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
