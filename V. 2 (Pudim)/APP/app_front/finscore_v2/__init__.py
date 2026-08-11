"""API reutilizável do motor FinScore Pudim."""

from .contracts import CONTRACT_VERSION, ContractError, FinScoreOutput, validar_contrato
from .engine import executar_finscore, executar_autotestes, preparar_dados_contabeis

__all__ = [
    "CONTRACT_VERSION",
    "ContractError",
    "FinScoreOutput",
    "executar_finscore",
    "executar_autotestes",
    "preparar_dados_contabeis",
    "validar_contrato",
]
