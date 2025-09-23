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
    decisao, motivos, covenants = "nao_aprovar", [], []
    fs = pi.finscore_ajustado or 0.0
    cj = pi.cobertura_juros if pi.cobertura_juros is not None else 0.0
    de = pi.dl_ebitda if pi.dl_ebitda is not None else 1e9

    if fs >= 750 and cj >= 2:
        decisao = "aprovar"
    elif 500 <= fs < 750:
        if de <= 3 and cj >= 1.5:
            decisao = "aprovar_com_ressalvas"
            covenants += ["DL/EBITDA<=3", "Cobertura>=1.5", "envio trimestral de DFs"]
        else:
            decisao = "nao_aprovar"

    if pi.serasa_rank and pi.finscore_rank:
        if abs(pi.serasa_rank - pi.finscore_rank) >= 2:
            motivos.append("divergencia com Serasa -> reforcar garantias/monitoramento")

    if pi.flags_qualidade.get("dados_incompletos"):
        motivos.append("dados incompletos: decisao mais conservadora")

    return {"decisao": decisao, "motivos": motivos, "covenants": covenants}
