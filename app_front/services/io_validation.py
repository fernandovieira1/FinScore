# app_front/services/io_validation.py
from typing import Any, Dict, Tuple, Optional
import pandas as pd
import numpy as np
import streamlit as st
from io import BytesIO
import re

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


def _limpar_valor_numerico(valor):
    """
    Limpa e converte valores para float, tratando diversos formatos incorretos.
    
    Exemplos:
    - "Rs 20" -> 20.0
    - "R$ 1.234,56" -> 1234.56
    - "1,234.56" -> 1234.56
    - "  " -> 0.0
    - "" -> 0.0
    - None -> 0.0
    """
    # Se já é numérico, retorna como float
    if isinstance(valor, (int, float)):
        if pd.isna(valor) or np.isnan(valor) or np.isinf(valor):
            return 0.0
        return float(valor)
    
    # Se não é string, tenta converter
    if not isinstance(valor, str):
        try:
            val = float(valor)
            if pd.isna(val) or np.isnan(val) or np.isinf(val):
                return 0.0
            return val
        except (ValueError, TypeError):
            return 0.0
    
    # Limpa string
    valor_limpo = str(valor).strip()
    
    # Se vazio, retorna 0
    if not valor_limpo:
        return 0.0
    
    # Remove prefixos comuns de moeda (R$, Rs, $, etc)
    valor_limpo = re.sub(r'^[Rr][Ss]?\$?\s*', '', valor_limpo)
    valor_limpo = re.sub(r'^\$\s*', '', valor_limpo)
    
    # Remove espaços
    valor_limpo = valor_limpo.replace(' ', '')
    
    # Detecta formato brasileiro (1.234,56) vs inglês (1,234.56)
    # Se tem ponto antes de vírgula, é formato brasileiro
    if '.' in valor_limpo and ',' in valor_limpo:
        idx_ponto = valor_limpo.rfind('.')
        idx_virgula = valor_limpo.rfind(',')
        
        if idx_ponto < idx_virgula:
            # Formato brasileiro: 1.234,56
            valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
        else:
            # Formato inglês: 1,234.56
            valor_limpo = valor_limpo.replace(',', '')
    elif ',' in valor_limpo:
        # Só tem vírgula, assume formato brasileiro
        valor_limpo = valor_limpo.replace(',', '.')
    # Se só tem ponto, mantém como está (formato inglês)
    
    # Remove outros caracteres não numéricos (exceto ponto e sinal negativo)
    valor_limpo = re.sub(r'[^\d.\-]', '', valor_limpo)
    
    # Tenta converter para float
    try:
        resultado = float(valor_limpo)
        if pd.isna(resultado) or np.isnan(resultado) or np.isinf(resultado):
            return 0.0
        return resultado
    except (ValueError, TypeError):
        return 0.0


def _padronizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame importado:
    - Converte colunas numéricas para float
    - Preenche valores faltantes com 0
    - Limpa typos e formatos incorretos
    - Preserva coluna 'ano' sem alteração
    """
    if df is None or df.empty:
        return df
    
    df_limpo = df.copy()
    
    # Identifica coluna de ano (case insensitive)
    col_ano = None
    for col in df_limpo.columns:
        if str(col).lower() == 'ano':
            col_ano = col
            break
    
    # Para cada coluna (exceto ano)
    for col in df_limpo.columns:
        # Preserva coluna ano
        if col == col_ano:
            # Garante que ano é inteiro
            try:
                df_limpo[col] = pd.to_numeric(df_limpo[col], errors='coerce').fillna(0).astype(int)
            except:
                pass
            continue
        
        # Para outras colunas, aplica limpeza e conversão para float
        try:
            # Aplica limpeza em cada valor
            df_limpo[col] = df_limpo[col].apply(_limpar_valor_numerico)
            # Garante tipo float
            df_limpo[col] = df_limpo[col].astype(float)
        except Exception:
            # Se falhar, tenta conversão direta
            try:
                df_limpo[col] = pd.to_numeric(df_limpo[col], errors='coerce').fillna(0.0)
            except:
                pass
    
    return df_limpo

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
        
        # Aplica padronização e limpeza automática dos dados
        df_limpo = _padronizar_dataframe(df)
        
        return df_limpo, aba, None
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
