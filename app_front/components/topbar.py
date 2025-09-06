# app_front/components/topbar.py
import streamlit as st
import streamlit.components.v1 as components

def render_topbar():
    """
    Topbar estática (sem comportamento nos botões) dentro de um IFRAME.
    Não será capturada em exportações (PDF/Word).
    """
    html = """
    <style>
      :root {
        --tb-bg: rgba(72, 82, 97, .92);
        --tb-fg: #E8EEF7;
        --tb-fg-muted:#B9C3D0;
        --tb-accent:#4da3ff;
        --tb-ring:#9cc7ff;
        --tb-radius: 14px;
      }

      html, body { margin:0; padding:0; }
      body {
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial;
      }

      /* wrapper centralizado e largura delimitada */
      .mm-wrap { display:flex; justify-content:center; margin:10px 0; }
      .mm-topbar {
        max-width: 960px; width: 100%;
        display:flex; align-items:center; justify-content:space-between; gap:14px;
        padding:10px 14px;
        background: var(--tb-bg); color: var(--tb-fg);
        border-radius: var(--tb-radius);
        border: 1px solid rgba(255,255,255,.08);
        box-shadow: none; /* sem sombra */
      }

      .mm-left, .mm-right { display:flex; align-items:center; gap:12px; min-width:0; }

      .brand {
        display:flex; align-items:center; gap:10px; white-space:nowrap;
        font-weight: 800; letter-spacing:.2px;
      }
      .brand .dot {
        width:26px; height:26px; border-radius:8px; background: #5c78f0;
      }

      .nav { display:flex; align-items:center; gap:6px; }

      /* Botões estáticos: span com aparência de botão */
      .pill-btn {
        display:inline-block;
        padding:8px 12px; border-radius:10px;
        color: var(--tb-fg-muted); font-weight:700; font-size:.92rem; line-height:1;
        border: 1px solid transparent; user-select:none;
      }
      .pill-btn:hover { /* apenas visual */
        color: var(--tb-fg);
        background: rgba(255,255,255,.08);
      }

      /* Ícones redondos à direita (apenas visuais) */
      .icon-btn {
        width:32px; height:32px; border-radius:10px; display:grid; place-items:center;
        color: var(--tb-fg); background: rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.14);
        user-select:none;
      }
      .icon-btn:hover { background: rgba(255,255,255,.16); }
      .icon { width:18px; height:18px; display:block; }
    </style>

    <div class="mm-wrap">
      <div class="mm-topbar">
        <div class="mm-left">
          <div class="brand">
            <span class="dot"></span>
            <span>FinScore</span>
          </div>

          <nav class="nav">
            <span class="pill-btn">Início</span>
            <span class="pill-btn">Definir</span>
            <span class="pill-btn">Resultados</span>
            <span class="pill-btn">Parecer</span>
          </nav>
        </div>

        <div class="mm-right">
          <div class="icon-btn" title="Tema claro/escuro">
            <svg class="icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M21 12.8A8.5 8.5 0 1 1 11.2 3a7 7 0 1 0 9.8 9.8Z"
                    stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="icon-btn" title="Configurações">
            <svg class="icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" stroke="currentColor" stroke-width="1.6"/>
              <path d="M19.4 15.5c.2-.6.6-1.2 1-1.6l.2-.2-1.3-2.2-.3.1c-.6.2-1.3.2-1.9 0a6.6 6.6 0 0 0-.9-.3l-.2-.9c-.1-.7-.4-1.3-.8-1.9l-.2-.3L12.9 6l-.2.2c-.5.4-1.2.8-1.9.9l-.9.2-.3.9c-.1.3-.2.6-.3.9-.2.6-.6 1.2-1.2 1.5L7.9 12l-2.3-1.3-.2.2c-.5.5-.8 1.1-1 1.7l-.2.7L5 15l.6.2c.7.2 1.3.5 1.8 1l.5.5.2.8c.1.6.4 1.2.7 1.7l.3.5 2.2-1.2-.1-.2c-.2-.6-.3-1.3-.2-1.9l.2-.9.8-.3c.3-.1.6-.3.9-.5.6-.3 1.3-.5 2-.4l.7.1.2-.6Z"
                    stroke="currentColor" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
    """
    # iframe isolado (não exporta no PDF/Word)
    components.html(html, height=64, scrolling=False)
