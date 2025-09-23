import math

import streamlit as st

from components.policy_engine import PolicyInputs, decide

RANK_SERASA = {"Excelente": 1, "Bom": 2, "Baixo": 3, "Muito Baixo": 4}
RANK_FINSCORE = {
    "Muito Abaixo do Risco": 1,
    "Levemente Abaixo do Risco": 2,
    "Neutro": 3,
    "Levemente Acima do Risco": 4,
    "Muito Acima do Risco": 5,
}


def _safe_float(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _latest_indices_row(out_dict):
    df = out_dict.get("df_indices") if out_dict else None
    if df is None or getattr(df, "empty", True):
        return {}
    try:
        return df.iloc[0].to_dict()
    except Exception:
        return {}


def render():
    ss = st.session_state
    st.header("Parecer")

    if not ss.get("out"):
        st.info("Calcule o FinScore em **Novo** para liberar o parecer.")
        return

    o = ss.out
    indices_row = _latest_indices_row(o)

    finscore_aj = o.get("finscore_ajustado")
    cls_fin = o.get("classificacao_finscore")
    cls_ser = o.get("classificacao_serasa")

    dl_ebitda = _safe_float(indices_row.get("Alavancagem"))
    cobertura = _safe_float(indices_row.get("Cobertura de Juros"))

    pi = PolicyInputs(
        finscore_ajustado=finscore_aj,
        dl_ebitda=dl_ebitda,
        cobertura_juros=cobertura,
        serasa_rank=RANK_SERASA.get(cls_ser),
        finscore_rank=RANK_FINSCORE.get(cls_fin),
        flags_qualidade={"dados_incompletos": False},
    )
    ss["policy_inputs"] = {
        "finscore_ajustado": pi.finscore_ajustado,
        "dl_ebitda": pi.dl_ebitda,
        "cobertura_juros": pi.cobertura_juros,
        "serasa_rank": pi.serasa_rank,
        "finscore_rank": pi.finscore_rank,
        "flags_qualidade": pi.flags_qualidade,
    }

    resultado = decide(pi)

    st.subheader("Pre-veredito")
    st.metric("Decisao", resultado["decisao"])
    st.write("Motivos:", resultado["motivos"])
    st.write("Covenants:", resultado["covenants"])

    st.divider()
    st.subheader("Gerar Parecer Final (IA)")
    if st.button("Redigir Parecer"):
        accepted = {
            key: value
            for key, value in (ss.get("reviews") or {}).items()
            if value.get("status") == "accepted"
        }
        st.write("Criticas aceitas:", list(accepted.keys()))
        st.success(
            "Parecer gerado (placeholder). Aqui, chame o LLM apenas para redacao, nunca para decidir."
        )
