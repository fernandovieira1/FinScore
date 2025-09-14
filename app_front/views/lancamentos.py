# app_front/views/lancamentos.py
import streamlit as st
import streamlit.components.v1 as components
from services.io_validation import validar_cliente, ler_planilha, check_minimo
from services.finscore_service import run_finscore

# Rótulos com ícones (ordem fixa na UI)
TAB_LABELS = {"Cliente": "🏢 Cliente", "Dados": "📥 Dados"}
TAB_ORDER = ["Cliente", "Dados"]  # Ordem visual fixa

def _js_select_tab(label_with_icon: str):
    """Força a seleção visual de uma aba do st.tabs sem reordenar a lista."""
    components.html(
        f"""
        <script>
        (function() {{
          const target = `{label_with_icon}`;
          function clickTab() {{
            const btns = window.parent.document.querySelectorAll('button[role="tab"]');
            for (const b of btns) {{
              // Matching mais robusto: usa includes() para ignorar espaços extras
              const txt = (b.innerText || b.textContent || "").trim();
              if (txt.includes(target.replace(/\\s/g, ' ').trim())) {{  // Remove quebras de linha e compara
                b.click();
                return true;
              }}
            }}
            return false;
          }}
          let attempts = 0;
          const iv = setInterval(() => {{
            if (clickTab() || attempts > 30) {{  // Aumentado para 3s de tentativas
              clearInterval(iv);
            }}
            attempts += 1;
          }}, 100);
          // Fallback: tenta uma vez após delay inicial
          setTimeout(clickTab, 200);
        }})();
        </script>
        """,
        height=0,
    )

def _auto_save_cliente():
    ss = st.session_state
    meta = ss.meta.copy()

    # --- FORMULÁRIO CLIENTE ---

    import re
    def mascara_cnpj(valor):
        # Remove tudo que não for dígito
        v = re.sub(r'\D', '', valor)
        # Garante 14 dígitos
        if len(v) < 14:
            return ''
        v = v[:14]
        # Aplica máscara xx.xxx.xxx/xxxx-xx
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:14]}"

    empresa = st.text_input("Nome da Empresa", value=meta.get("empresa", ""), placeholder="Ex.: ACME S.A.")
    cnpj_raw = meta.get("cnpj", "")
    # Aplica máscara ANTES de exibir o campo
    cnpj_default = mascara_cnpj(cnpj_raw)
    cnpj_input = st.text_input("CNPJ", value=cnpj_default, placeholder="00.000.000/0000-00", max_chars=18, key="cnpj_input")
    cnpj = mascara_cnpj(cnpj_input)
    # Aceita apenas 4 dígitos para campo ano
    ai_str = st.text_input("Ano Inicial", value=str(meta.get("ano_inicial", "")), placeholder="YYYY", max_chars=4)
    ai = int(ai_str) if ai_str.isdigit() and len(ai_str) == 4 else None
    # Ano Final é calculado automaticamente
    af = ai + 2 if ai else None
    af_str = str(af) if af else ""
    st.markdown("""
    <style>
    /* Força fundo branco e texto escuro no campo desabilitado, igual aos outros campos */
    input[disabled], input:disabled, .stTextInput input:disabled {
        color: #222 !important;
        background: #fff !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.text_input("Ano Final", value=af_str, placeholder="YYYY", max_chars=4, disabled=True)
    # Serasa Score como float
    serasa_val = meta.get("serasa", "")
    serasa_str = st.text_input(
        "Serasa Score (0–1000)",
        value=str(int(float(serasa_val))) if str(serasa_val).replace(",", ".").replace(" ", "").replace(".0", "").isdigit() else "",
        placeholder="Ex.: 550"
    )
    try:
        serasa = float(int(float(serasa_str.replace(",", ".")))) if serasa_str.strip() else None
    except Exception:
        serasa = None
    # Data de Consulta como DD/MM/YYYY
    serasa_data_raw = str(meta.get("serasa_data", ""))
    import re
    def mascara_data_br(valor):
        # Remove tudo que não for dígito
        v = re.sub(r'\D', '', valor)
        if len(v) < 8:
            return ''
        v = v[:8]
        # Aplica máscara DD/MM/YYYY
        return f"{v[:2]}/{v[2:4]}/{v[4:8]}"
    serasa_data_default = mascara_data_br(serasa_data_raw)
    serasa_data_input = st.text_input("Data de Consulta ao Serasa", value=serasa_data_default, placeholder="DD/MM/YYYY", max_chars=10, key="serasa_data_input")
    def valida_data_br(data):
        if not data:
            return ""
        m = re.match(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}$", data)
        return data if m else ""
    serasa_data = valida_data_br(mascara_data_br(serasa_data_input))

    # Normalização
    empresa = empresa.strip() if empresa else ""
    cnpj = mascara_cnpj(cnpj.strip()) if cnpj else ""

    new_meta = {"empresa": empresa, "cnpj": cnpj, "ano_inicial": ai, "ano_final": af, "serasa": serasa, "serasa_data": serasa_data}
    for k, v in list(new_meta.items()):
        if v is None or v == "":
            new_meta.pop(k)
    ss.meta.update(new_meta)

    pend = validar_cliente(ss.meta)
    if pend:
        st.warning(pend)
    else:
        st.success("Cliente salvo automaticamente.")



def _sec_cliente():
    st.header("Dados do Cliente")
    _auto_save_cliente()
    st.write("")
    st.markdown("""
    <style>
    .stButton>button[data-testid="baseButton-secondary"] {
        background: var(--primary-btn, #5ea68d) !important;
        color: #fff !important;
        font-weight: 600;
        font-size: 1.05rem;
        border-radius: 6px !important;
        padding: 0.7rem 2.2rem !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(16,24,40,0.08);
        transition: background 0.2s;
    }
    .stButton>button[data-testid="baseButton-secondary"]:hover {
        background: #468c6f !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Centralizar o botão
    col = st.columns([3, 2, 3])[1]
    with col:
        if st.button("Enviar Dados"):
            st.session_state["novo_tab"] = "Dados"
            st.session_state["_internal_nav"] = True
            st.rerun()

def _sec_dados():
    # DEBUG: Verificar se há referências a _navigate_to
    if "_navigate_to" in st.session_state:
        st.warning("⚠️ _navigate_to encontrado no session_state. Removendo...")
        del st.session_state["_navigate_to"]
    
    # ... resto do código existente ...
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
        url = st.text_input("Cole o link do Google Sheets (pressione ENTER para ver a prévia)", placeholder="https://docs.google.com/…")
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
        st.session_state.out = None  # Limpa resultados se dados mudaram

    st.write("---")

    st.markdown("""
    <style>
    .stButton>button[data-testid="baseButton-secondary"] {
        background: var(--primary-btn, #5ea68d) !important;
        color: #fff !important;
        font-weight: 600;
        font-size: 1.05rem;
        border-radius: 6px !important;
        padding: 0.7rem 2.2rem !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(16,24,40,0.08);
        transition: background 0.2s;
    }
    .stButton>button[data-testid="baseButton-secondary"]:hover {
        background: #468c6f !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Centralizar o botão
    col = st.columns([3, 2, 3])[1]
    with col:
        if st.button("Calcular FinScore"):
            ss = st.session_state
            pend = validar_cliente(ss.meta)
            if pend:
                st.error(pend)
            elif ss.df is None:
                st.error("Envie os dados contábeis acima antes de calcular.")
            else:
                try:
                    with st.spinner("Calculando FinScore…"):
                        res = run_finscore(ss.df, ss.meta)
                    # Aceita dict ou tupla/lista
                    out = res[0] if isinstance(res, (list, tuple)) else res
                    if not isinstance(out, dict):
                        raise ValueError("Formato de retorno inesperado do run_finscore.")
                    ss.out = out
                    ss["analise_tab"] = "Resumo"  # Abre na aba Resumo
                    ss["liberar_analise"] = True
                    ss["liberar_parecer"] = True
                    # Ativa modo de cálculo (bloqueio retroativo)
                    from components.state_manager import AppState
                    AppState.ativar_modo_calculo()
                    st.success("✅ Processamento concluído.")
                    # === NAVEGAÇÃO DIRETA PARA ANÁLISE ===
                    ss.page = "Análise"
                    st.query_params["p"] = "analise"
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")

def render():
    ss = st.session_state
    # Removido o reset automático de novo_tab para preservar navegação interna (ex.: após 'Iniciar')

    # ===== CSS específico desta view =====
    st.markdown(
        """
        <style>
        /* Centraliza barra de abas desta view */
        div[data-testid="stTabs"] > div[role="tablist"],
        div[data-baseweb="tab-list"] {
            display: flex; justify-content: center;
        }
        div[data-testid="stTabs"] button[role="tab"],
        div[data-baseweb="tab"] { flex: 0 0 auto; }

        /* Garante títulos alinhados à esquerda */
        h1, h2, h3 { text-align: left !important; }

        /* ---- Botões menores e centralizados ---- */
        div.stButton { text-align: center; }
        .stButton > button {
            display: inline-block; margin: .5rem auto; padding: .6rem 1.2rem;
            background: #0074d9; color: #fff; font-weight: 600;
            border: none; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,.15);
            transition: filter .15s ease, transform .02s ease;
        }
        .stButton > button:hover { filter: brightness(.96); }
        .stButton > button:active { transform: translateY(1px); }

        /* ---- Campos do formulário com fundo branco ---- */
        .stTextInput > div > div > input,
        [data-baseweb="select"] > div,
        .stFileUploader > div > div,
        .stTextArea > div > textarea {
            background: #ffffff !important;
            border-radius: 10px;
            border: 1px solid rgba(2,6,23,.12);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Cria abas com ordem fixa e ícones
    labels_with_icons = [TAB_LABELS[name] for name in TAB_ORDER]
    tabs = st.tabs(labels_with_icons)
    tab_dict = {name: tab for name, tab in zip(TAB_ORDER, tabs)}

    # Seleção visual (sem reordenar)
    _js_select_tab(TAB_LABELS.get(ss["novo_tab"], TAB_LABELS["Cliente"]))

    # Render do conteúdo
    with tab_dict["Cliente"]:
        _sec_cliente()
    with tab_dict["Dados"]:
        _sec_dados()