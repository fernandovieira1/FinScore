# app_front/components/topbar.py
import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path

def render_topbar():
    """
    Topbar branca, altura e espaçamentos refinados.
    Botões à esquerda; ícones (FB, X, IG, YT, lua) + logo Assertif à direita.
    Render em iframe para não sair no PDF/Word.
    """
    MAX_WIDTH = 1060  # largura visual equilibrada

    # Logo local (app_front/assets/logo.png)
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    try:
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")
        logo_src = f"data:image/png;base64,{logo_b64}"
    except Exception:
        logo_src = ""

    html = f"""
    <style>
      :root {{
        --tb-bg: #ffffff;
        --tb-fg: #1f2937;
        --tb-fg-muted:#071700; \* Cor dos botões *\
        --tb-border: rgba(2,6,23,.10);
        --tb-hover: rgba(2,6,23,.06);
        --radius: 14px;
      }}

      html, body {{ margin:0; padding:0; }}
      body {{
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial;
      }}

      .mm-wrap {{ display:flex; justify-content:center; margin:10px 0; }}

      .mm-topbar {{
        width:100%;
        max-width:{MAX_WIDTH}px;
        height:60px;                 /* altura fixa elegante */
        padding:0 18px;              /* só lateral */
        display:flex; align-items:center; justify-content:space-between;
        background:var(--tb-bg); color:var(--tb-fg);
        border:1px solid var(--tb-border);
        border-radius:var(--radius);
        box-shadow:none;             /* mantendo sem sombra */
      }}

      /* esquerda: nav */
      .nav {{
        display:flex; align-items:center; gap:16px; margin:0;
      }}
      .pill-btn {{
        display:inline-block;
        padding:6px 10px;            /* mais enxuto */
        border-radius:10px;
        color:var(--tb-fg-muted);
        font-weight:600;             /* menos pesado */
        font-size:.92rem;
        line-height:1;
        border:1px solid transparent;
        user-select:none;
      }}
      .pill-btn:hover {{
        color:var(--tb-fg);
        background:var(--tb-hover);
        border-color:var(--tb-border);
      }}

      /* direita: ícones + logo */
      .right {{ display:flex; align-items:center; gap:14px; }}
      .icons {{ display:flex; align-items:center; gap:12px; }}
      .ic {{
        width:18px; height:18px;
        display:block; color:#374151;
        opacity:.85; transition:opacity .15s ease, transform .05s ease;
      }}
      .ic:hover {{ opacity:1; transform:translateY(-1px); }}

      .assertif-logo {{ height:22px; display:block; border-radius:4px; }}
    </style>

    <div class="mm-wrap">
      <div class="mm-topbar">
        <nav class="nav">
          <span class="pill-btn">Início</span>
          <span class="pill-btn">Definir1</span>
          <span class="pill-btn">Definir2</span>
          <span class="pill-btn">Definir3</span>
        </nav>

        <div class="right">
          <div class="icons" aria-label="social icons">
            <!-- Facebook -->
            <svg class="ic" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M13.5 21v-7h2.6l.4-3H13.5V9.1c0-.9.3-1.5 1.6-1.5h1.6V5.1C16.3 5 15.4 5 14.4 5 12 5 10.5 6.3 10.5 8.8V11H8v3h2.5v7h3Z" fill="currentColor"/>
            </svg>
            <!-- X / Twitter -->
            <svg class="ic" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M3 3h3.3l6 7.6L16.7 3H21l-7.2 9.1L21 21h-3.3l-6.3-7.9L7.3 21H3l7.5-9.2L3 3Z" fill="currentColor"/>
            </svg>
            <!-- Instagram -->
            <svg class="ic" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="4" y="4" width="16" height="16" rx="4" stroke="currentColor" stroke-width="2"/>
              <circle cx="12" cy="12" r="3.5" stroke="currentColor" stroke-width="2"/>
              <circle cx="17" cy="7" r="1.2" fill="currentColor"/>
            </svg>
            <!-- YouTube -->
            <svg class="ic" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M22 12c0-2.2-.3-3.7-.7-4.4-.4-.8-1-1.3-1.8-1.5C17.9 5.6 12 5.6 12 5.6s-5.9 0-7.5.5c-.8.2-1.4.7-1.8 1.5C2.3 8.3 2 9.8 2 12s.3 3.7.7 4.4c.4.8 1 1.3 1.8 1.5 1.6.5 7.5.5 7.5.5s5.9 0 7.5-.5c.8-.2 1.4-.7 1.8-1.5.4-.7.7-2.2.7-4.4Z" fill="currentColor"/>
              <path d="M10 9.75v4.5L15 12l-5-2.25Z" fill="#fff"/>
            </svg>
            <!-- Lua / Tema -->
            <svg class="ic" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M20.2 14.9A8.5 8.5 0 1 1 9.1 3.8a7 7 0 1 0 11.1 11.1Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>

          <img class="assertif-logo" src="{logo_src}" alt="assertif" />
        </div>
      </div>
    </div>
    """
    components.html(html, height=68, scrolling=False)  # 60px + folga
