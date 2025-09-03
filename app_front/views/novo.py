# app_front/views/novo.py
import streamlit as st
import streamlit.components.v1 as components
from services.io_validation import validar_cliente, ler_planilha, check_minimo
from services.finscore_service import run_finscore

# Rótulos com ícones (ordem fixa na UI)
TAB_LABELS = {
    "Início": "🏁 Início",
    "Cliente": "🏢 Cliente",
    "Dados": "📥 Dados",
}
TAB_ORDER = ["Início", "Cliente", "Dados"]  # ordem visual fixa


def _js_select_tab(label_with_icon: str):
    """
    Força a seleção visual de uma aba do st.tabs sem reordenar a lista.
    Usa um pequeno script JS que procura o rótulo e dispara um click.
    """
    components.html(
        f"""
        <script>
        (function() {{
          const target = `{label_with_icon}`;
          function clickTab() {{
            // Os tabs do Streamlit são botões; vamos varrer por aria-controls
            const btns = window.parent.document.querySelectorAll('button[role="tab"]');
            for (const b of btns) {{
              const txt = (b.innerText || b.textContent || "").trim();
              if (txt === target) {{
                b.click();
                return true;
              }}
            }}
            return false;
          }}
          // tenta algumas vezes até o DOM carregar
          let attempts = 0;
          const iv = setInterval(() => {{
            attempts += 1;
            if (clickTab() || attempts > 20) clearInterval(iv);
          }}, 100);
        }})();
        </script>
        """,
        height=0,
    )


def _auto_save_cliente():
    ss = st.session_state
    meta = ss.meta.copy()

    empresa = st.text_input("Nome da Empresa", value=meta.get("empresa", ""), placeholder="Ex.: ACME S.A.")
    cnpj    = st.text_input("CNPJ (opcional)", value=meta.get("cnpj", ""), placeholder="00.000.000/0000-00")
    ai_str  = st.text_input("Ano Inicial", value=str(meta.get("ano_inicial", "")), placeholder="AAAA")
    af_str  = st.text_input("Ano Final",   value=str(meta.get("ano_final", "")),   placeholder="AAAA")
    serasa_str = st.text_input("Serasa Score (0–1000)", value=str(meta.get("serasa", "")), placeholder="Ex.: 550")

    empresa = empresa.strip()
    cnpj = cnpj.strip()
    ai = int(ai_str) if ai_str.strip().isdigit() else None
    af = int(af_str) if af_str.strip().isdigit() else None
    serasa = int(serasa_str) if serasa_str.strip().isdigit() else None

    new_meta = {"empresa": empresa, "cnpj": cnpj, "ano_inicial": ai, "ano_final": af, "serasa": serasa}
    for k, v in list(new_meta.items()):
        if v is None or v == "":
            new_meta.pop(k)
    ss.meta.update(new_meta)

    pend = validar_cliente(ss.meta)
    if pend:
        st.warning(pend)
    else:
        st.success("Cliente salvo automaticamente.")


def _sec_inicio():
    st.header("Bem-vindo ao FinScore")
    st.markdown(
        """
        **Fluxo de uso**
        1) Aba **Cliente** → informe empresa, período e Serasa.  
        2) Aba **Dados** → envie o Excel (prioriza `lancamentos`).  
        3) Use **Resultados** para visualizar resultados.  
        4) Gere o **Parecer** (PDF/Word) na aba correspondente.
        """
    )
    st.write("")
    if st.button("Iniciar", use_container_width=True):
        st.session_state["novo_tab"] = "Cliente"  # estado lógico
        st.rerun()  # após o rerun, o JS seleciona visualmente a aba


def _sec_cliente():
    st.header("Dados do Cliente")
    _auto_save_cliente()
    st.write("")
    if st.button("Enviar Dados", use_container_width=True):
        st.session_state["novo_tab"] = "Dados"
        st.rerun()


def _sec_dados():
    st.header("Dados Contábeis")
    modo = st.radio(
        "Como deseja fornecer os dados contábeis?",
        ["Upload de arquivo Excel", "Link do Google Sheets"],
        horizontal=True,
    )

    df, aba, erro = None, None, None
    if modo == "Upload de arquivo Excel":
        up = st.file_uploader("Envie o arquivo (.xlsx)", type=["xlsx"])
        if up:
            df, aba, erro = ler_planilha(up)
    else:
        url = st.text_input("Cole o link compartilhável do Google Sheets", placeholder="https://docs.google.com/…")
        if url:
            try:
                sid = url.split("/d/")[1].split("/")[0]
                gid = url.split("gid=")[-1].split("&")[0] if "gid=" in url else "0"
                export = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx&id={sid}&gid={gid}"
                df, aba, erro = ler_planilha(export)
            except Exception as e:
                erro = str(e)

    if erro:
        st.error(f"Erro ao ler a planilha: {erro}")

    if df is not None:
        st.success(f"✅ Dados carregados (aba: {aba}).")
        st.caption("Prévia:")
        st.dataframe(df.head(), use_container_width=True)
        st.session_state.df = df.copy()
        chec = check_minimo(st.session_state.df)
        if chec["BP_faltando"] or chec["DRE_faltando"]:
            st.warning("🔎 Checagem de campos mínimos (informativa):")
            st.write({"Ausentes BP": chec["BP_faltando"], "Ausentes DRE": chec["DRE_faltando"]})
        st.success("✅ Dados contábeis salvos.")
        st.session_state.out = None  # limpa resultados se dados mudaram

    st.write("---")

    st.markdown(
        """
        <style>
        div.stButton > button:first-child{
            background:#0074d9!important; color:white!important; font-weight:600;
            border:none!important; border-radius:8px; height:48px;
        }
        div.stButton > button:first-child:hover{ filter:brightness(1.05); }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Calcular FinScore", use_container_width=True):
        ss = st.session_state
        pend = validar_cliente(ss.meta)
        if pend:
            st.error(pend)
        elif ss.df is None:
            st.error("Envie os dados contábeis acima antes de calcular.")
        else:
            try:
                with st.spinner("Calculando FinScore…"):
                    ss.out = run_finscore(ss.df, ss.meta)
                st.success("✅ Processamento concluído.")
                ss["page"] = "Resultados"
                st.rerun()
            except Exception as e:
                st.error(f"Erro no processamento: {e}")


def render():
    ss = st.session_state
    ss.setdefault("novo_tab", "Início")  # estado lógico da aba

    # Cria abas com ordem fixa e ícones
    labels_with_icons = [TAB_LABELS[name] for name in TAB_ORDER]
    tabs = st.tabs(labels_with_icons)
    tab_dict = {name: tab for name, tab in zip(TAB_ORDER, tabs)}

    # Seleção visual (sem reordenar): após o rerun, o JS clica na aba certa
    _js_select_tab(TAB_LABELS.get(ss["novo_tab"], TAB_LABELS["Início"]))

    # Render do conteúdo (cada aba sempre no mesmo lugar)
    with tab_dict["Início"]:
        _sec_inicio()
    with tab_dict["Cliente"]:
        _sec_cliente()
    with tab_dict["Dados"]:
        _sec_dados()
