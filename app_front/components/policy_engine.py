from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PolicyInputs:
    finscore_ajustado: Optional[float]
    dl_ebitda: Optional[float]
    cobertura_juros: Optional[float]
    serasa_rank: Optional[int]
    finscore_rank: Optional[int]
    flags_qualidade: Dict[str, Any]


def decide(pi: PolicyInputs) -> dict:
    """
    Motor de decisão baseado em:
    1. FinScore como threshold principal de aprovação
    2. Serasa como critério de ressalva (se aprovado mas Serasa baixo)
    3. Índices financeiros detalhados servem para análise crítica na seção de indicadores
    """
    decisao, motivos, covenants = "nao_aprovar", [], []
    fs = pi.finscore_ajustado or 0.0
    serasa_rank = pi.serasa_rank or 4  # 4 = Muito Baixo (default conservador)

    # DECISÃO PRINCIPAL: baseada no FinScore
    if fs > 875:
        # Muito Abaixo do Risco - Aprovação automática
        decisao = "aprovar"
        motivos.append("FinScore excelente (> 875) indica capacidade patrimonial robusta")
        
    elif 750 < fs <= 875:
        # Levemente Abaixo do Risco - Aprovação com possível ressalva por Serasa
        decisao = "aprovar"
        motivos.append("FinScore bom (750-875) indica capacidade patrimonial adequada")
        
    elif 250 <= fs <= 750:
        # Neutro - Aprovação com ressalvas
        decisao = "aprovar_com_ressalvas"
        motivos.append("FinScore neutro (250-750) requer monitoramento adicional")
        covenants += ["Monitoramento trimestral de indicadores", "Envio de DFs atualizadas"]
        
    elif 125 < fs < 250:
        # Levemente Acima do Risco - Não aprovar
        decisao = "nao_aprovar"
        motivos.append("FinScore baixo (125-250) indica fragilidade patrimonial")
        
    else:
        # Muito Acima do Risco - Não aprovar
        decisao = "nao_aprovar"
        motivos.append("FinScore crítico (< 125) indica alta fragilidade patrimonial")

    # CRITÉRIO SERASA: Adiciona ressalvas se aprovado mas Serasa baixo
    if decisao == "aprovar":
        if serasa_rank >= 3:  # Baixo (3) ou Muito Baixo (4)
            decisao = "aprovar_com_ressalvas"
            motivos.append("Serasa Baixo/Muito Baixo requer garantias adicionais e monitoramento de histórico de crédito")
            covenants += ["Garantias reais ou fidejussórias", "Consulta Serasa mensal", "Limite de crédito conservador"]
        elif serasa_rank == 2:  # Bom
            motivos.append("Serasa Bom complementa positivamente a análise patrimonial")

    # Flags de qualidade
    if pi.flags_qualidade.get("dados_incompletos"):
        motivos.append("Dados incompletos: decisão mais conservadora aplicada")
        if decisao == "aprovar":
            decisao = "aprovar_com_ressalvas"
            covenants += ["Completar dados faltantes em 30 dias"]

    return {"decisao": decisao, "motivos": motivos, "covenants": covenants}
