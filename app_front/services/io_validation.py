# app_front/services/io_validation.py
from typing import Any, Dict, Tuple, Optional
import pandas as pd
import streamlit as st
from io import BytesIO

def validar_cliente(meta: Dict[str, Any]) -> Dict[str, str]:
    e: Dict[str, str] = {}
    if not meta.get("empresa") or not str(meta.get("empresa")).strip():
        e["empresa"] = "Informe o nome da empresa."
    if not meta.get("cnpj") or not str(meta.get("cnpj")).strip():
        e["cnpj"] = "Informe o CNPJ."
    ai_raw = meta.get("ano_inicial")
    af_raw = meta.get("ano_final")
    try:
        ai = int(ai_raw) if ai_raw is not None and str(ai_raw).isdigit() else None
        af = int(af_raw) if af_raw is not None and str(af_raw).isdigit() else None
        if ai is None or af is None:
            raise ValueError
        if ai > af:
            e["anos"] = "Ano Inicial não pode ser maior que Ano Final."
        if ai < 2000 or af > 2100:
            e["faixa"] = "Anos entre 2000 e 2100."
    except Exception:
        e["anos"] = "Anos inválidos."
    s_raw = meta.get("serasa")
    try:
        s = int(s_raw) if s_raw is not None and str(s_raw).strip().isdigit() else None
        if s is None or not (0 <= s <= 1000):
            raise ValueError
    except Exception:
        e["serasa"] = "Serasa deve estar entre 0 e 1000."
    if not meta.get("serasa_data") or not str(meta.get("serasa_data")).strip():
        e["serasa_data"] = "Informe a data de consulta ao Serasa."
    return e

def _sheet_name_case_insensitive(xls: pd.ExcelFile, wanted: str) -> Optional[str]:
    for s in xls.sheet_names:
        if s.lower() == wanted.lower():
            return s
    return None

def ler_planilha(upload_or_url) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[str]]:
    """
    Lê uma planilha Excel, priorizando o engine 'openpyxl' (xlsx).
    Retorna (df, aba_lida, erro_str)
    """
    try:
        # Aceita tanto bytes (upload do Streamlit) quanto caminho/arquivo.
        src = upload_or_url
        if hasattr(upload_or_url, "getvalue"):
            # st.file_uploader retorna um UploadedFile -> usar bytes
            src = BytesIO(upload_or_url.getvalue())

        # Força engine 'openpyxl' para .xlsx
        xls = pd.ExcelFile(src, engine="openpyxl")
        aba = _sheet_name_case_insensitive(xls, "lancamentos") or xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=aba, engine="openpyxl")
        return df, aba, None
    except ImportError as e:
        # Dependência não encontrada no ambiente em execução
        msg = (
            "Dependência 'openpyxl' não encontrada no ambiente ativo. "
            "Certifique-se de executar o app com o Python da sua venv e que o pacote esteja instalado.\n"
            "Dica: ative a venv e rode: python -m pip install openpyxl"
        )
        return None, None, msg
    except Exception as e:
        # Erros genéricos de leitura
        est = str(e)
        if "Missing optional dependency 'openpyxl'" in est:
            msg = (
                "Dependência 'openpyxl' ausente. Instale-a e execute o app pelo mesmo ambiente Python.\n"
                "Ex.: ativar venv e rodar: python -m streamlit run app_front/app.py"
            )
            return None, None, msg
        return None, None, est

def check_minimo(df: pd.DataFrame) -> Dict[str, list]:
    req_bp = ["p_Ativo_Total", "p_Patrimonio_Liquido"]
    req_dre = ["r_Lucro_Liquido", "r_Receita_Total"]
    cols_low = [c.lower() for c in df.columns]
    falta_bp = [c for c in req_bp if c.lower() not in cols_low]
    falta_dre = [c for c in req_dre if c.lower() not in cols_low]
    return {"BP_faltando": falta_bp, "DRE_faltando": falta_dre}
