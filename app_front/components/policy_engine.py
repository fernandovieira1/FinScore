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
    # Dados adicionais para motivos detalhados
    serasa_score: Optional[float] = None
    classificacao_finscore: Optional[str] = None
    classificacao_serasa: Optional[str] = None
    # Índices para crítica
    liquidez_corrente: Optional[float] = None
    liquidez_seca: Optional[float] = None
    roe: Optional[float] = None
    margem_liquida: Optional[float] = None
    margem_ebitda: Optional[float] = None
    endividamento: Optional[float] = None


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
    serasa_score = pi.serasa_score or 0.0
    
    # DECISÃO PRINCIPAL: baseada no FinScore
    if fs > 875:
        # Muito Abaixo do Risco - Aprovação automática
        decisao = "aprovar"
        motivos.append(f"**FinScore**: {pi.classificacao_finscore or 'Muito Abaixo do Risco'} ({fs:.0f} pontos) — capacidade patrimonial robusta")
        
    elif 750 < fs <= 875:
        # Levemente Abaixo do Risco - Aprovação com possível ressalva por Serasa
        decisao = "aprovar"
        motivos.append(f"**FinScore**: {pi.classificacao_finscore or 'Levemente Abaixo do Risco'} ({fs:.0f} pontos) — capacidade patrimonial adequada")
        
    elif 250 <= fs <= 750:
        # Neutro - Aprovação com ressalvas
        decisao = "aprovar_com_ressalvas"
        motivos.append(f"**FinScore**: {pi.classificacao_finscore or 'Neutro'} ({fs:.0f} pontos) — situação intermediária que requer monitoramento")
        covenants += ["Monitoramento trimestral de indicadores", "Envio de DFs atualizadas"]
        
    elif 125 < fs < 250:
        # Levemente Acima do Risco - Não aprovar
        decisao = "nao_aprovar"
        motivos.append(f"**FinScore**: {pi.classificacao_finscore or 'Levemente Acima do Risco'} ({fs:.0f} pontos) — fragilidade patrimonial")
        
    else:
        # Muito Acima do Risco - Não aprovar
        decisao = "nao_aprovar"
        motivos.append(f"**FinScore**: {pi.classificacao_finscore or 'Muito Acima do Risco'} ({fs:.0f} pontos) — fragilidade patrimonial crítica")

    # CRITÉRIO SERASA: Adiciona ressalvas se aprovado mas Serasa baixo
    if decisao == "aprovar":
        if serasa_rank >= 3:  # Baixo (3) ou Muito Baixo (4)
            decisao = "aprovar_com_ressalvas"
            motivos.append(f"**Serasa Score**: {pi.classificacao_serasa or 'Baixo/Muito Baixo'} ({serasa_score:.0f} pontos) — histórico de crédito comprometido exige garantias adicionais")
            covenants += ["Garantias reais ou fidejussórias", "Consulta Serasa mensal", "Limite de crédito conservador"]
        elif serasa_rank == 2:  # Bom
            motivos.append(f"**Serasa Score**: {pi.classificacao_serasa or 'Bom'} ({serasa_score:.0f} pontos) — histórico de crédito satisfatório")
        else:  # Excelente
            motivos.append(f"**Serasa Score**: {pi.classificacao_serasa or 'Excelente'} ({serasa_score:.0f} pontos) — histórico de crédito exemplar")
    else:
        # Para não aprovar, ainda mostrar o Serasa
        motivos.append(f"**Serasa Score**: {pi.classificacao_serasa or 'N/A'} ({serasa_score:.0f} pontos)")

    # CRÍTICA BASEADA NOS INDICADORES FINANCEIROS (3º bullet)
    critica_indicadores = _gerar_critica_indicadores(pi, decisao)
    if critica_indicadores:
        motivos.append(critica_indicadores)

    # Flags de qualidade
    if pi.flags_qualidade.get("dados_incompletos"):
        motivos.append("⚠️ Dados incompletos: decisão mais conservadora aplicada")
        if decisao == "aprovar":
            decisao = "aprovar_com_ressalvas"
            covenants += ["Completar dados faltantes em 30 dias"]

    return {"decisao": decisao, "motivos": motivos, "covenants": covenants}


def _gerar_critica_indicadores(pi: PolicyInputs, decisao: str) -> str:
    """
    Gera crítica com base nos indicadores conforme a decisão:
    - Aprovar: enfatizar pontos positivos
    - Aprovar com ressalvas: equilibrar pontos bons e ruins
    - Não aprovar: enfatizar pontos negativos
    """
    pontos_positivos = []
    pontos_negativos = []
    
    # Analisar liquidez
    if pi.liquidez_corrente is not None:
        if pi.liquidez_corrente >= 1.5:
            pontos_positivos.append("liquidez confortável")
        elif pi.liquidez_corrente < 1.0:
            pontos_negativos.append("liquidez comprometida")
    
    # Analisar rentabilidade
    if pi.margem_liquida is not None:
        if pi.margem_liquida >= 0.05:  # >= 5%
            pontos_positivos.append("rentabilidade adequada")
        elif pi.margem_liquida < 0.02:  # < 2%
            pontos_negativos.append("margens apertadas")
    
    if pi.roe is not None:
        if pi.roe >= 0.12:  # >= 12%
            pontos_positivos.append("retorno sobre patrimônio satisfatório")
        elif pi.roe < 0.05:  # < 5%
            pontos_negativos.append("baixo retorno aos sócios")
    
    # Analisar endividamento
    if pi.endividamento is not None:
        if pi.endividamento <= 0.60:  # <= 60%
            pontos_positivos.append("estrutura de capital equilibrada")
        elif pi.endividamento > 0.75:  # > 75%
            pontos_negativos.append("endividamento elevado")
    
    if pi.dl_ebitda is not None:
        if pi.dl_ebitda <= 2.5:
            pontos_positivos.append("alavancagem controlada")
        elif pi.dl_ebitda > 4.0:
            pontos_negativos.append("alavancagem excessiva")
    
    # Montar a crítica conforme a decisão
    if decisao == "aprovar":
        if pontos_positivos:
            return f"**Indicadores**: Apresenta {', '.join(pontos_positivos[:3])}"
        else:
            return "**Indicadores**: Fundamentos financeiros dentro dos padrões aceitáveis"
    
    elif decisao == "aprovar_com_ressalvas":
        partes = []
        if pontos_positivos:
            partes.append(f"pontos fortes ({', '.join(pontos_positivos[:2])})")
        if pontos_negativos:
            partes.append(f"pontos de atenção ({', '.join(pontos_negativos[:2])})")
        
        if partes:
            return f"**Indicadores**: {' mas '.join(partes)}"
        else:
            return "**Indicadores**: Situação mista que demanda monitoramento"
    
    else:  # nao_aprovar
        if pontos_negativos:
            return f"**Indicadores**: Apresenta {', '.join(pontos_negativos[:3])}"
        else:
            return "**Indicadores**: Fundamentos financeiros abaixo dos padrões mínimos"
