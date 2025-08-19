import streamlit as st
from services.io_validation import validar_cliente, ler_planilha, check_minimo
from services.finscore_service import run_finscore

TABS = ["Início", "Cliente", "Dados"]

def _pill_nav():
    """Pílulas de navegação (sub-abas) controladas por session_state."""
    ss = st.session_state
    current = ss.get("novo_tab", "Início")
    idx = TABS.index(current) if current in TABS else 0
    choice = st.radio(
        "nav",
        TABS,
        index=idx,
        horizontal=True,
        label_visibility="collapsed",
        key="novo_tab_radio",
    )
    # Sincroniza o valor da radio com o estado global
    if choice != current:
        ss["novo_tab"] = choice
    st.write("")  # pequeno espaçamento

def _auto_save_cliente():
    """Lê os campos da seção 'Cliente' e salva em ss.meta sem precisar de botão."""
    ss = st.session_state
    meta = ss.meta.copy()

    empresa = st.text_input("Nome da Empresa", value=meta.get("empresa", ""), placeholder="Ex.: ACME S.A.")
    cnpj    = st.text_input("CNPJ (opcional)", value=meta.get("cnpj", ""), placeholder="00.000.000/0000-00")
    ai_str  = st.text_input("Ano Inicial", value=str(meta.get("ano_inicial", "")), placeholder="AAAA")
    af_str  = st.text_input("Ano Final",   value=str(meta.get("ano_final", "")),   placeholder="AAAA")
    serasa_str = st.text_input("Serasa Score (0–1000)", value=str(meta.get("serasa", "")), placeholder="Ex.: 550")

    # Normalização leve
    empresa = empresa.strip()
    cnpj = cnpj.strip()
    ai = int(ai_str) if ai_str.strip().isdigit() else None
    af = int(af_str) if af_str.strip().isdigit() else None
    serasa = int(serasa_str) if serasa_str.strip().isdigit() else None

    # Salva somente o que foi digitado
    new_meta = {
        "empresa": empresa,
        "cnpj": cnpj,
        "ano_inicial": ai,
        "ano_final": af,
        "serasa": serasa,
    }
    # Remove chaves com None para não “apagar” o que já estava válido
    for k, v in list(new_meta.items()):
        if v is None or v == "":
            new_meta.pop(k)

    # Atualiza o estado global com o que veio preenchido
    ss.meta.update(new_meta)

    # Mensagens de validação informativas
    pend = validar_cliente(ss.meta)
    if pend:
        st.warning(pend)
    else:
        st.success("Cliente salvo automaticamente.")

def _sec_inicio():
    st.header("Bem‑vindo ao FinScore")
    st.markdown(
        """
        **Fluxo de uso**
        1) Aba **Cliente** → informe empresa, período e Serasa.  
        2) Aba **Dados** → envie o Excel (prioriza `lancamentos`).  
        3) Use **Resumo/Tabelas/Gráficos** para visualizar resultados.  
        4) Gere o **Parecer** (PDF/Word) na aba correspondente.
        """
    )
    st.write("")
    # Botão que pula para "Cliente"
    if st.button("Iniciar", use_container_width=True):
        st.session_state["novo_tab"] = "Cliente"
        st.rerun()

def _sec_cliente():
    st.header("Dados do Cliente")
    _auto_save_cliente()
    st.write("")
    # Botão que pula para "Dados"
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
        # Salva no estado (sem botão)
        st.session_state.df = df.copy()
        chec = check_minimo(st.session_state.df)
        if chec["BP_faltando"] or chec["DRE_faltando"]:
            st.warning("🔎 Checagem de campos mínimos (informativa):")
            st.write({"Ausentes BP": chec["BP_faltando"], "Ausentes DRE": chec["DRE_faltando"]})
        st.success("✅ Dados contábeis salvos.")
        st.session_state.out = None

    st.write("---")

    # Botão Calcular FinScore (verde)
    st.markdown(
        """
        <style>
        div.stButton > button:first-child{
            background:#1f7a34!important; color:white!important; font-weight:600;
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
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

def render():
    _pill_nav()
    tab = st.session_state.get("novo_tab", "Início")
    if tab == "Início":
        _sec_inicio()
    elif tab == "Cliente":
        _sec_cliente()
    else:
        _sec_dados()
