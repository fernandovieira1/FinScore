from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SinalType = Literal["positivo", "neutro", "negativo"]
StatusType = Literal["draft", "accepted", "needs_revision"]


class ReviewSchema(BaseModel):
    insight: str = Field(..., description="Resumo objetivo do que o artefato mostra")
    riscos: List[str] = Field(default_factory=list, description="Riscos relevantes")
    sinal: SinalType = "neutro"
    status: StatusType = "draft"

    class Config:
        populate_by_name = True
        extra = "ignore"


class PolicyInputs(BaseModel):
    finscore_ajustado: Optional[float] = None
    dl_ebitda: Optional[float] = None
    cobertura_juros: Optional[float] = None
    serasa_rank: Optional[int] = None
    finscore_rank: Optional[int] = None
    flags_qualidade: Dict[str, Any] = Field(default_factory=dict)
