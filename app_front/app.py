# app_front/app.py
import inspect
import unicodedata
from typing import Any, Dict

import pandas as pd
import streamlit as st

from utils_finscore import executar_finscore        # cálculo
from dashboard_finscore import mostrar_dashboard    # visualização

st.set_page_config(page_title="FinScore Dashboard", layout="wide")

# ---------- Estado ----------
ss = st.session_state
ss.setdefault("meta", {})
ss.setdefault("df_dict", {})
ss.setdefault("out", None)
ss.setdefault("erros", {})

# ---------- Utilidades ----------
REQUIRED_COLS = [
    # DRE
    "r_Lucro_Liquido", "r_Receita_Total", "r_Despesa_de_Juros",
    "r_Despesa_de_Impostos", "r_Custos",
    # BP
    "p_Ativo_Total", "p_Patrimonio_Liquido", "p_Passivo_Total", "p_Caixa",
    "p_Ativo_Circulante", "p_Passivo_Circulante", "p_Contas_a_Receber",
    "p_Contas_a_Pagar", "p_Estoques",
]

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes: strip, remove acentos, troca espaços por _; padroniza coluna 'ano'."""
    df = df.copy()
    new_cols = []
    for c in df.columns:
        c2 = str(c).strip()
        c2 = _strip_accents(c2)
        c2 = c2.replace(" ", "_")
        new_cols.append(c2)
    df.columns = new_cols
    # padroniza 'Ano' -> 'ano'
    if "ano" not in df.columns and "Ano" in df.columns:
        df = df.rename(columns={"Ano": "ano"})
    return df

def _require_cols(df: pd.DataFrame) -> None:
    faltantes = [c for c in REQUIRED_COLS if c not in df.columns]
    if faltantes:
        raise KeyError(
            "Colunas obrigatórias ausentes: " + ", ".join(faltantes) +
            ". Dica: ajuste os cabeçalhos na planilha ou inclua uma etapa de mapeamento."
        )

def validar_cliente(meta: Dict[str, Any]) -> Dict[str, str]:
    e: Dict[str, str] = {}
    if not meta.get("empresa"):
        e["empresa"] = "Informe o nome da empresa."

    ai = meta.get("ano_inicial")
    af = meta.get("ano_final")
    if ai is None or af is None:
        e["anos"] = "Informe Ano Inicial e Ano Final."
    else:
        try:
            ai, af = int(ai), int(af)
            if ai > af:
                e["ordem"] = "Ano Inicial não pode ser maior que Ano Final."
            if ai < 2000 or af > 2100:
                e["faixa"] = "Anos devem estar entre 2000 e 2100."
            if (af - ai + 1) > 10:
                e["janela" ] = "Selecione no máximo 10 anos para manter performance."
        except Exception:
            e["anos"] = "Anos devem ser números inteiros válidos."

    try:
        s = int(meta.get("serasa"))
    except Exception:
        s = None
    if s is None or not (0 <= s <= 1000):
        e["serasa"] = "Serasa deve estar entre 0 e 1000."

    return e

def validar_dados(df_dict: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    """
    Aceita dois formatos:
      (A) Abas 'BP' e 'DRE' já separadas.
      (B) Uma aba única com colunas p_* (BP) e/ou r_* (DRE).
    """
    e: Dict[str, str] = {}

    # Caso clássico BP/DRE
    if "BP" in df_dict and "DRE" in df_dict:
        if df_dict["BP"].empty:
            e["BP"] = "A aba “BP” está vazia."
        if df_dict["DRE"].empty:
            e["DRE"] = "A aba “DRE” está vazia."
        return e

    # Formato compacto: apenas uma aba
    if len(df_dict) == 1:
        nome, df = next(iter(df_dict.items()))
        cols_lower = [str(c).lower() for c in df.columns]
        tem_p = any(c.startswith("p_") for c in cols_lower)
        tem_r = any(c.startswith("r_") for c in cols_lower)
        if not (tem_p or tem_r):
            e["schema"] = f'A aba “{nome}” não tem colunas iniciando com "p_" (BP) nem "r_" (DRE).'
        return e

    if "BP" not in df_dict:
        e["BP"] = 'Falta a aba “BP”.'
    if "DRE" not in df_dict:
        e["DRE"] = 'Falta a aba “DRE”.'
    return e

def _normalizar_col_ano(df: pd.DataFrame) -> pd.DataFrame:
    if "ano" not in df.columns and "Ano" in df.columns:
        df = df.rename(columns={"Ano": "ano"})
    return df

def _unificar_df(df_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Retorna um único DataFrame com colunas p_* e r_*.
    - Se vier BP/DRE: faz merge por 'ano' (obrigatório).
    - Se vier uma aba já com p_*/r_*: retorna a própria aba.
    """
    if "BP" in df_dict and "DRE" in df_dict:
        df_bp  = _norm_cols(_normalizar_col_ano(df_dict["BP"].copy()))
        df_dre = _norm_cols(_normalizar_col_ano(df_dict["DRE"].copy()))
        if "ano" not in df_bp.columns or "ano" not in df_dre.columns:
            raise KeyError("Para unir BP e DRE é necessária a coluna 'ano' em ambas as abas.")
        # evita duplicidade de coluna 'ano' no merge
        overlap = [c for c in df_bp.columns if c in df_dre.columns and c != "ano"]
        df_dre = df_dre.drop(columns=overlap, errors="ignore")
        df = pd.merge(df_bp, df_dre, on="ano", how="inner")
        return df

    if len(df_dict) == 1:
        _, df = next(iter(df_dict.items()))
        return _norm_cols(_normalizar_col_ano(df.copy()))

    # fallback: concatena tudo e confia nos prefixos
    frames = []
    for _, df in df_dict.items():
        frames.append(_norm_cols(_normalizar_col_ano(df.copy())))
    if not frames:
        raise ValueError("Nenhuma aba contábil válida encontrada.")
    df = frames[0]
    for extra in frames[1:]:
        overlap = [c for c in extra.columns if c in df.columns and c != "ano"]
        extra = extra.drop(columns=overlap, errors="ignore")
        if "ano" in extra.columns and "ano" in df.columns:
            df = pd.merge(df, extra, on="ano", how="outer")
        else:
            df = pd.concat([df, extra], axis=1)
    return df

def _executar_finscore_compat(df_dict: Dict[str, pd.DataFrame], meta: Dict[str, Any]):
    """
    Constrói o DataFrame unificado e chama a assinatura atual do executar_finscore:
        executar_finscore(df_total, nome_empresa, ano_inicial, ano_final, serasa_score)
    Mantém diagnóstico de assinaturas alternativas apenas se necessário.
    """
    df_total = _unificar_df(df_dict)
    _require_cols(df_total)  # valida colunas obrigatórias

    empresa = meta.get("empresa", "")
    ai = int(meta.get("ano_inicial"))
    af = int(meta.get("ano_final"))
    ser = int(meta.get("serasa"))

    # Tenta a assinatura atual (prioritária)
    try:
        return executar_finscore(df_total, empresa, ai, af, ser)
    except TypeError:
        # Compat: tenta variações antigas se existir outra implementação no seu ambiente
        attempts = []
        try:
            return executar_finscore(df_total, ai, af, ser)
        except TypeError as e:
            attempts.append(f"[df, ai, af, ser] {e}")
        try:
            return executar_finscore(df_total, ai, af)
        except TypeError as e:
            attempts.append(f"[df, ai, af] {e}")
        try:
            return executar_finscore(df_dict=df_total, ano_inicial=ai, ano_final=af, serasa_score=ser)
        except TypeError as e:
            attempts.append(f"[kwargs] {e}")

        try:
            sig = str(inspect.signature(executar_finscore))
        except Exception:
            sig = "indisponível"
        raise TypeError(
            "Nenhuma assinatura de executar_finscore compatível com este app.\n"
            f"Assinatura detectada: {sig}\n"
            "Tentativas: " + " | ".join(attempts)
        )

# ---------- Abas ----------
tab0, tab1, tab2, tab3 = st.tabs(["🏁 Início", "🧾 Cliente", "📂 Dados", "📊 Resultados"])

with tab0:
    st.header("Bem‑vindo ao FinScore")
    st.markdown(
        "- **Cliente:** cadastre nome, CNPJ, período (Ano Inicial/Final) e Serasa.\n"
        "- **Dados:** envie o Excel (ou link do Sheets).\n"
        "- **Resultados:** calcule e visualize índices, PCA e FinScore."
    )
    st.info("Dica: as abas não ‘bloqueiam’ navegação, mas só exibimos os resultados quando as validações passam.")

with tab1:
    st.header("Dados do Cliente")
    c1, c2 = st.columns([2, 1])

    with c1:
        empresa = st.text_input("Nome da Empresa", value=ss.meta.get("empresa", ""))
        cnpj = st.text_input("CNPJ (opcional)", value=ss.meta.get("cnpj", ""))
        ano_inicial = st.number_input("Ano Inicial", min_value=2000, max_value=2100,
                                      value=int(ss.meta.get("ano_inicial", 2021)), step=1)
        ano_final   = st.number_input("Ano Final",   min_value=2000, max_value=2100,
                                      value=int(ss.meta.get("ano_final", 2023)), step=1)

    with c2:
        serasa = st.number_input("Serasa Score (0–1000)", 0, 1000, value=int(ss.meta.get("serasa", 550)))
        serasa_data = st.date_input("Data do Serasa (opcional)", value=ss.meta.get("serasa_data", None))

    if st.button("Salvar dados do cliente", use_container_width=True):
        ss.meta.update({
            "empresa": empresa.strip(),
            "cnpj": cnpj.strip(),
            "ano_inicial": int(ano_inicial),
            "ano_final": int(ano_final),
            "serasa": int(serasa),
            "serasa_data": str(serasa_data) if serasa_data else None
        })

        ss.erros = validar_cliente(ss.meta)
        if ss.erros:
            for v in ss.erros.values():
                st.error(v)
        else:
            ss.meta["anos"] = list(range(ss.meta["ano_inicial"], ss.meta["ano_final"] + 1))
            st.success(
                f"✅ Cliente salvo e validado. Período: "
                f"{ss.meta['ano_inicial']}–{ss.meta['ano_final']} "
                f"({len(ss.meta['anos'])} ano(s))."
            )
            ss.out = None  # força recálculo

with tab2:
    st.header("Dados Contábeis")
    modo = st.radio("Fonte dos dados", ["Upload de Excel (.xlsx)", "Link do Google Sheets"], horizontal=True)
    df_dict: Dict[str, pd.DataFrame] = {}

    if modo.startswith("Upload"):
        up = st.file_uploader("Envie o arquivo", type=["xlsx"])
        if up:
            try:
                xls = pd.ExcelFile(up)
                bruto = {aba: _norm_cols(pd.read_excel(xls, aba)) for aba in xls.sheet_names}

                if "BP" in bruto and "DRE" in bruto:
                    df_dict = {"BP": _normalizar_col_ano(bruto["BP"]), "DRE": _normalizar_col_ano(bruto["DRE"])}
                    st.success("✅ Abas BP e DRE detectadas.")
                elif len(bruto) == 1:
                    nome, df = next(iter(bruto.items()))
                    cols = list(df.columns)
                    cols_lower = [str(c).lower() for c in cols]

                    bp_cols  = ["ano"] + [c for c, cl in zip(cols, cols_lower) if cl.startswith("p_")]
                    dre_cols = ["ano"] + [c for c, cl in zip(cols, cols_lower) if cl.startswith("r_")]

                    df_bp  = df[[c for c in bp_cols  if c in df.columns]].copy()
                    df_dre = df[[c for c in dre_cols if c in df.columns]].copy()

                    if not df_bp.empty:
                        df_dict["BP"] = df_bp
                        st.success(f"✅ Convertida a aba “{nome}” → “BP” ({len(df_bp.columns)-1} colunas p_*)")
                    if not df_dre.empty:
                        df_dict["DRE"] = df_dre
                        st.success(f"✅ Convertida a aba “{nome}” → “DRE” ({len(df_dre.columns)-1} colunas r_*)")

                    if "BP" not in df_dict and "DRE" not in df_dict:
                        st.error(f'Aba “{nome}” sem colunas com prefixo "p_" ou "r_".')
                else:
                    df_dict = {k: _normalizar_col_ano(v.copy()) for k, v in bruto.items()}
                    st.info("ℹ️ Múltiplas abas lidas. Se não houver BP/DRE, o validador indicará o que falta.")

                if df_dict:
                    first = next(iter(df_dict.values()))
                    st.caption("Prévia da primeira aba reconhecida:")
                    st.dataframe(first.head(), use_container_width=True)

            except Exception as e:
                st.error(f"Erro ao ler Excel: {e}")

    else:
        url = st.text_input("Cole o link do Google Sheets (compartilhável)")
        if url:
            st.info("Integração com Sheets pode ser adicionada aqui (gspread/Sheets API).")

    if st.button("Salvar dados contábeis", use_container_width=True):
        ss.df_dict = df_dict
        ss.erros = validar_dados(ss.df_dict)
        if ss.erros:
            for v in ss.erros.values():
                st.error(v)
        else:
            st.success("✅ Dados contábeis salvos e validados.")
            ss.out = None

with tab3:
    st.header("Resultados")

    falta_cli = validar_cliente(ss.meta)
    falta_xls = validar_dados(ss.df_dict) if ss.df_dict else {"dados": "Envie e salve os dados contábeis na aba 📂 Dados."}

    if falta_cli or falta_xls:
        st.warning("Complete e valide as abas **Cliente** e **Dados** para habilitar o cálculo.")
        if falta_cli:
            st.write("➡️ Pendências em **Cliente**:"); st.write(falta_cli)
        if falta_xls:
            st.write("➡️ Pendências em **Dados**:"); st.write(falta_xls)
        st.stop()

    st.caption(
        f"Período analisado: {ss.meta['ano_inicial']}–{ss.meta['ano_final']} "
        f"({len(ss.meta['anos'])} ano(s))"
    )

    if st.button("Calcular FinScore", type="primary"):
        with st.spinner("Calculando FinScore…"):
            try:
                ss.out = _executar_finscore_compat(ss.df_dict, ss.meta)
                st.success("✅ Processamento concluído.")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

    if ss.out:
        # A assinatura atual de utils_finscore.py retorna:
        # "finscore_bruto", "finscore_ajustado", "classificacao_finscore",
        # "serasa", "classificacao_serasa", "df_indices", "df_pca", "top_indices_df", ...
        c1, c2, c3 = st.columns(3)
        c1.metric("FinScore Ajustado", f"{ss.out['finscore_ajustado']}")
        c2.metric("Classificação", ss.out["classificacao_finscore"])
        c3.metric("Serasa Score", f"{ss.out['serasa']} ({ss.out['classificacao_serasa']})")

        st.divider()
        st.subheader("📊 Índices Contábeis Calculados")
        st.dataframe(ss.out["df_indices"])

        st.subheader("🔎 Componentes Principais (PCA)")
        st.dataframe(ss.out["df_pca"])

        st.subheader("🌟 Destaques por Componente Principal")
        st.dataframe(ss.out["top_indices_df"])

        # Dashboard interativo
        mostrar_dashboard(
            ss.out["df_indices"],
            ss.out["df_pca"],
            ss.out["top_indices_df"]
        )

        # Download opcional dos índices
        if "df_indices" in ss.out:
            st.download_button(
                "Baixar índices (CSV)",
                ss.out["df_indices"].to_csv(index=False).encode("utf-8"),
                file_name=f"indices_{ss.meta.get('empresa','empresa')}.csv"
            )
