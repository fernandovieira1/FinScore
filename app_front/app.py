# app_front/app.py
import streamlit as st
import pandas as pd
from typing import Any

from utils_finscore import executar_finscore
from dashboard_finscore import mostrar_dashboard

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
st.set_page_config(page_title="FinScore Dashboard", layout="wide")
LOGO_PATH = "assets/logo.png"  # coloque seu arquivo aqui (ou mude o caminho)

# ---------------------------------------------------------
# Estado
# ---------------------------------------------------------
ss = st.session_state
ss.setdefault("meta", {})
ss.setdefault("df", None)        # df contábil
ss.setdefault("out", None)       # resultado do executar_finscore
ss.setdefault("erros", {})

# ---------------------------------------------------------
# Header com logo
# ---------------------------------------------------------
def header():
    col_logo, col_title, col_spacer = st.columns([0.9, 3, 1])
    with col_logo:
        try:
            st.image(LOGO_PATH, use_container_width=True)
        except Exception:
            st.write("")  # sem logo
    with col_title:
        st.markdown(
            """
            <div style="padding-top:8px">
                <h1 style="margin-bottom:0">FINSCORE</h1>
                <p style="color:#6b7280;margin-top:4px">Análise Financeira Automatizada</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

header()
st.write("---")

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _validar_cliente(meta: dict[str, Any]) -> dict[str, str]:
    e: dict[str, str] = {}
    if not meta.get("empresa"):
        e["empresa"] = "Informe o nome da empresa."
    try:
        ai, af = int(meta.get("ano_inicial")), int(meta.get("ano_final"))
        if ai > af:
            e["anos"] = "Ano Inicial não pode ser maior que Ano Final."
        if ai < 2000 or af > 2100:
            e["faixa"] = "Anos devem estar entre 2000 e 2100."
    except Exception:
        e["anos"] = "Anos inválidos."
    try:
        s = int(meta.get("serasa"))
        if not (0 <= s <= 1000):
            raise ValueError
    except Exception:
        e["serasa"] = "Serasa deve estar entre 0 e 1000."
    return e

def _sheet_name_case_insensitive(xls: pd.ExcelFile, wanted: str) -> str | None:
    for s in xls.sheet_names:
        if s.lower() == wanted.lower():
            return s
    return None

def _ler_planilha(upload_or_url) -> tuple[pd.DataFrame | None, str | None, str | None]:
    """Lê Excel; se houver 'lancamentos', prioriza. Retorna (df, aba, erro)."""
    try:
        xls = pd.ExcelFile(upload_or_url)
        aba = _sheet_name_case_insensitive(xls, "lancamentos") or xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=aba)
        return df, aba, None
    except Exception as e:
        return None, None, str(e)

def _check_minimo(df: pd.DataFrame) -> dict[str, list[str]]:
    req_bp = ["p_Ativo_Total", "p_Patrimonio_Liquido"]
    req_dre = ["r_Lucro_Liquido", "r_Receita_Total"]
    cols_low = [c.lower() for c in df.columns]
    falta_bp = [c for c in req_bp if c.lower() not in cols_low]
    falta_dre = [c for c in req_dre if c.lower() not in cols_low]
    return {"BP_faltando": falta_bp, "DRE_faltando": falta_dre}

# ---------------------------------------------------------
# Sidebar com ícones
# ---------------------------------------------------------
def menu_sidebar() -> str:
    try:
        from streamlit_option_menu import option_menu
        with st.sidebar:
            st.markdown("### Navegação")
            choice = option_menu(
                None,
                ["Novo", "Resumo", "Tabelas", "Gráficos", "Parecer", "Sobre"],
                icons=["plus-circle", "speedometer", "table", "bar-chart", "file-earmark-text", "info-circle"],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#0b5ea8"},
                    "icon": {"color": "white", "font-size": "18px"},
                    "nav-link": {
                        "font-size": "16px",
                        "text-align": "left",
                        "margin": "0px",
                        "color": "white",
                    },
                    "nav-link-selected": {"background-color": "#084a86"},
                },
            )
        return choice
    except Exception:
        # fallback sem dependência, com emojis
        return st.sidebar.radio(
            "Navegação",
            ("Novo", "Resumo", "Tabelas", "Gráficos", "Parecer", "Sobre"),
            index=0,
            format_func=lambda x: {
                "Novo": "🆕 Novo",
                "Resumo": "📊 Resumo",
                "Tabelas": "📄 Tabelas",
                "Gráficos": "📈 Gráficos",
                "Parecer": "📝 Parecer",
                "Sobre": "ℹ️ Sobre",
            }[x],
        )

pagina = menu_sidebar()

# ===========================================================
# NOVO  (Início / Cliente / Dados)
# ===========================================================
if pagina == "Novo":
    tab0, tab1, tab2 = st.tabs(["🏁 Início", "🧾 Cliente", "📂 Dados"])

    with tab0:
        st.header("Bem‑vindo ao FinScore")
        st.markdown(
            """
            **Fluxo de uso**
            1) Aba **Cliente** → informe empresa, período e Serasa.  
            2) Aba **Dados** → envie o Excel (prioriza aba `lancamentos`).  
            3) Vá para **Resumo/Tabelas/Gráficos** para visualizar resultados.
            """
        )

    with tab1:
        st.header("Dados do Cliente")
        c1, c2 = st.columns([2, 1])
        with c1:
            empresa = st.text_input("Nome da Empresa", value=ss.meta.get("empresa", ""))
            cnpj = st.text_input("CNPJ (opcional)", value=ss.meta.get("cnpj", ""))
            ano_inicial = st.number_input("Ano Inicial", min_value=2000, max_value=2100,
                                          value=int(ss.meta.get("ano_inicial", 2021)), step=1)
            ano_final = st.number_input("Ano Final", min_value=2000, max_value=2100,
                                        value=int(ss.meta.get("ano_final", 2023)), step=1)
        with c2:
            serasa = st.number_input("Serasa Score (0–1000)", min_value=0, max_value=1000,
                                     value=int(ss.meta.get("serasa", 550)), step=1)

        if st.button("Salvar dados do cliente", use_container_width=True):
            ss.meta.update({
                "empresa": empresa.strip(),
                "cnpj": cnpj.strip(),
                "ano_inicial": int(ano_inicial),
                "ano_final": int(ano_final),
                "serasa": int(serasa),
            })
            ss.erros = _validar_cliente(ss.meta)
            if ss.erros:
                for v in ss.erros.values():
                    st.error(v)
            else:
                st.success(f"✅ Cliente salvo. Período: {ss.meta['ano_inicial']}–{ss.meta['ano_final']}.")
                ss.out = None

    with tab2:
        st.header("Dados Contábeis")
        modo = st.radio("Como deseja fornecer os dados contábeis?",
                        ["Upload de arquivo Excel", "Link do Google Sheets"], horizontal=True)

        df, aba, erro = None, None, None
        if modo == "Upload de arquivo Excel":
            up = st.file_uploader("Envie o arquivo (.xlsx)", type=["xlsx"])
            if up:
                df, aba, erro = _ler_planilha(up)
        else:
            url = st.text_input("Cole o link compartilhável do Google Sheets")
            if url:
                try:
                    sheet_id = url.split("/d/")[1].split("/")[0]
                    gid = url.split("gid=")[-1].split("&")[0] if "gid=" in url else "0"
                    export = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&id={sheet_id}&gid={gid}"
                    df, aba, erro = _ler_planilha(export)
                except Exception as e:
                    erro = str(e)

        if erro:
            st.error(f"Erro ao ler a planilha: {erro}")

        if df is not None:
            st.success(f"✅ Dados carregados (aba: {aba}).")
            st.caption("Prévia:")
            st.dataframe(df.head(), use_container_width=True)

        if st.button("Salvar dados contábeis", use_container_width=True):
            if df is None:
                st.error("Envie um arquivo ou link válido antes de salvar.")
            else:
                ss.df = df.copy()
                chec = _check_minimo(ss.df)
                if chec["BP_faltando"] or chec["DRE_faltando"]:
                    st.warning("🔎 Checagem de campos mínimos (informativa):")
                    st.write({"Ausentes BP": chec["BP_faltando"], "Ausentes DRE": chec["DRE_faltando"]})
                st.success("✅ Dados contábeis salvos.")
                ss.out = None

    st.divider()
    if st.button("Calcular FinScore (rápido)", type="primary"):
        pend_cli = _validar_cliente(ss.meta)
        if pend_cli:
            st.error(pend_cli)
        elif ss.df is None:
            st.error("Envie e salve os dados contábeis na aba **Dados**.")
        else:
            try:
                ss.out = executar_finscore(
                    ss.df,
                    ss.meta.get("empresa") or "Empresa",
                    int(ss.meta["ano_inicial"]),
                    int(ss.meta["ano_final"]),
                    int(ss.meta["serasa"]),
                )
                st.success("✅ Processamento concluído.")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

# ===========================================================
# RESUMO (Dashboard)
# ===========================================================
elif pagina == "Resumo":
    st.header("📊 Resumo (Dashboard)")
    if not ss.out:
        st.info("Calcule o FinScore em **Novo** para liberar o dashboard.")
        st.stop()

    c1, c2 = st.columns(2)
    c1.metric("FinScore Ajustado", f"{ss.out['finscore_ajustado']}")
    c2.metric("Classificação", ss.out["classificacao_finscore"])
    st.metric("Serasa Score", f"{ss.out['serasa']} ({ss.out['classificacao_serasa']})")
    st.caption(f"Empresa: {ss.meta.get('empresa','-')} | Período: {ss.meta['ano_inicial']}–{ss.meta['ano_final']}")

    st.divider()
    mostrar_dashboard(
        ss.out["df_indices"],
        ss.out["df_pca"],
        ss.out["top_indices_df"],
    )

# ===========================================================
# TABELAS (somente tabelas)
# ===========================================================
elif pagina == "Tabelas":
    st.header("📄 Tabelas")
    if not ss.out:
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        st.stop()

    st.subheader("Índices Contábeis Calculados")
    st.dataframe(ss.out["df_indices"], use_container_width=True)

    st.subheader("Componentes Principais (PCA)")
    st.dataframe(ss.out["df_pca"], use_container_width=True)

    st.subheader("Top 3 Índices por Componente")
    st.dataframe(ss.out["top_indices_df"], use_container_width=True)

# ===========================================================
# GRÁFICOS
# ===========================================================
elif pagina == "Gráficos":
    st.header("📈 Gráficos")
    if not ss.out:
        st.info("Calcule o FinScore em **Novo** para visualizar os gráficos.")
        st.stop()

    mostrar_dashboard(
        ss.out["df_indices"],
        ss.out["df_pca"],
        ss.out["top_indices_df"],
    )

# ===========================================================
# PARECER
# ===========================================================
elif pagina == "Parecer":
    st.header("📝 Parecer (Fase 2)")
    st.info("Integração futura: OpenAI/LangChain para gerar o parecer e exportar PDF/Word.")
    if ss.out:
        st.caption(f"Contexto: {ss.meta.get('empresa','Empresa')} — {ss.meta['ano_inicial']}–{ss.meta['ano_final']}")
        st.write("• Estrutura proposta do parecer:")
        st.write("- Sumário executivo")
        st.write("- Liquidez, Rentabilidade, Estrutura de Capital, Eficiência, Endividamento")
        st.write("- Conclusão e recomendações")

# ===========================================================
# SOBRE
# ===========================================================
elif pagina == "Sobre":
    st.header("ℹ️ Sobre este App")
    st.markdown(
        """
        **FinScore** — painel para análise financeira automatizada.  
        **Como usar**  
        1) **Novo** → preencha **Cliente** e **Dados** e execute o cálculo.  
        2) Explore **Resumo**, **Tabelas** e **Gráficos**.  
        3) Na Fase 2, gere o **Parecer** (PDF/Word).
        """
    )
