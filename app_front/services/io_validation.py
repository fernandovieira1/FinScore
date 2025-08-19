# app_front/services/io_validation.py
from typing import Any, Dict, Tuple, Optional
import pandas as pd
import streamlit as st

def validar_cliente(meta: Dict[str, Any]) -> Dict[str, str]:
    e: Dict[str, str] = {}
    if not meta.get("empresa"): e["empresa"] = "Informe o nome da empresa."
    try:
        ai, af = int(meta.get("ano_inicial")), int(meta.get("ano_final"))
        if ai > af: e["anos"] = "Ano Inicial não pode ser maior que Ano Final."
        if ai < 2000 or af > 2100: e["faixa"] = "Anos entre 2000 e 2100."
    except Exception:
        e["anos"] = "Anos inválidos."
    try:
        s = int(meta.get("serasa"))
        if not (0 <= s <= 1000): raise ValueError
    except Exception:
        e["serasa"] = "Serasa deve estar entre 0 e 1000."
    return e

def _sheet_name_case_insensitive(xls: pd.ExcelFile, wanted: str) -> Optional[str]:
    for s in xls.sheet_names:
        if s.lower() == wanted.lower():
            return s
    return None

def ler_planilha(upload_or_url) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[str]]:
    try:
        xls = pd.ExcelFile(upload_or_url)
        aba = _sheet_name_case_insensitive(xls, "lancamentos") or xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=aba)
        return df, aba, None
    except Exception as e:
        return None, None, str(e)

def check_minimo(df: pd.DataFrame) -> Dict[str, list]:
    req_bp = ["p_Ativo_Total", "p_Patrimonio_Liquido"]
    req_dre = ["r_Lucro_Liquido", "r_Receita_Total"]
    cols_low = [c.lower() for c in df.columns]
    falta_bp = [c for c in req_bp if c.lower() not in cols_low]
    falta_dre = [c for c in req_dre if c.lower() not in cols_low]
    return {"BP_faltando": falta_bp, "DRE_faltando": falta_dre}
