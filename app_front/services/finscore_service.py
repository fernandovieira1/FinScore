# app_front/services/finscore_service.py
from typing import Dict
from utils_finscore import executar_finscore

def run_finscore(df, meta: Dict):
    """
    Recebe o DataFrame contábil e o dicionário meta (empresa, cnpj, anos, serasa)
    e retorna o dicionário 'resultado' pronto para ir ao session_state['out'].
    """
    nome = meta.get("empresa", "").strip()
    ano_i = int(meta.get("ano_inicial"))
    ano_f = int(meta.get("ano_final"))
    serasa = int(meta.get("serasa", 0))

    return executar_finscore(df, nome, ano_i, ano_f, serasa)
