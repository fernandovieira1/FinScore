"""Governança da recomendação FinScore e das posições humanas.

Esta camada não recalcula o FinScore e não aplica critérios de crédito. Ela
mantém a recomendação calculada como referência imutável e registra, em campos
independentes, a manifestação do analista e a decisão da alçada.

O histórico desta unidade é mantido durante o ciclo corrente. Identificador
institucional, persistência, assinaturas e permissões serão tratados na camada
de dossiê persistente.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

try:  # Execução Streamlit, com app_front no sys.path.
    from components.parecer_data_schema import (
        FinScoreRecommendation,
        Governance,
        GovernanceAction,
        GovernanceAuditEvent,
        GovernanceDivergence,
        GovernanceStage,
        HumanDecision,
        RecommendationCode,
    )
except ModuleNotFoundError:  # Importação como pacote nos testes.
    from app_front.components.parecer_data_schema import (
        FinScoreRecommendation,
        Governance,
        GovernanceAction,
        GovernanceAuditEvent,
        GovernanceDivergence,
        GovernanceStage,
        HumanDecision,
        RecommendationCode,
    )


GOVERNANCE_STATE_VERSION = "1.0"
GOVERNANCE_SESSION_KEY = "credit_governance"
MIN_JUSTIFICATION_LENGTH = 20
LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


class GovernanceSessionState(BaseModel):
    """Estado transitório versionado, serializável e validado da governança."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    versao: str = GOVERNANCE_STATE_VERSION
    assinatura_analise: str = Field(min_length=64, max_length=64)
    governanca: Governance

    @model_validator(mode="after")
    def validate_state(self) -> "GovernanceSessionState":
        if self.versao != GOVERNANCE_STATE_VERSION:
            raise ValueError("versão incompatível do estado de governança")
        return self


def _now() -> datetime:
    return datetime.now(LOCAL_TIMEZONE)


def _as_datetime(value: Any | None) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or LOCAL_TIMEZONE)
    if value is not None:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            return parsed.replace(tzinfo=parsed.tzinfo or LOCAL_TIMEZONE)
        except ValueError:
            pass
    return _now()


def _event(
    *,
    stage: GovernanceStage,
    action: GovernanceAction,
    result: RecommendationCode,
    justification: str,
    responsible: str,
    registered_at: datetime,
) -> GovernanceAuditEvent:
    return GovernanceAuditEvent(
        evento_id=f"GOV-{uuid4().hex.upper()}",
        etapa=stage,
        acao=action,
        resultado=result,
        justificativa=justification,
        responsavel=responsible,
        registrado_em=registered_at,
    )


def governance_fingerprint(
    output: dict[str, Any], recommendation: FinScoreRecommendation
) -> str:
    """Identifica a execução e impede que posições migrem entre análises."""

    model = output.get("modelo") if isinstance(output.get("modelo"), dict) else {}
    basis = {
        "hash_dados_reportados": output.get("hash_dados_reportados"),
        "hash_dados_utilizados": output.get("hash_dados_utilizados"),
        "processado_em": model.get("processado_em"),
        "recomendacao": recommendation.model_dump(mode="json"),
    }
    serialized = json.dumps(
        basis,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def initialize_governance_state(
    recommendation: FinScoreRecommendation,
    signature: str,
    *,
    registered_at: datetime | str | None = None,
) -> GovernanceSessionState:
    timestamp = _as_datetime(registered_at)
    justification = (
        "; ".join(recommendation.fundamentos[:2])
        or "Recomendação registrada conforme as regras de crédito aplicáveis ao FinScore."
    )
    history = (
        _event(
            stage=GovernanceStage.RECOMMENDATION,
            action=GovernanceAction.REGISTERED,
            result=recommendation.codigo,
            justification=justification,
            responsible="FinScore",
            registered_at=timestamp,
        ),
    )
    return GovernanceSessionState(
        assinatura_analise=signature,
        governanca=Governance(
            recomendacao_finscore=recommendation,
            historico=list(history),
        ),
    )


def load_or_initialize_governance_state(
    raw_state: GovernanceSessionState | dict[str, Any] | None,
    recommendation: FinScoreRecommendation,
    signature: str,
    *,
    registered_at: datetime | str | None = None,
) -> tuple[GovernanceSessionState, bool]:
    """Carrega o estado atual ou inicia outro quando a análise mudou.

    Retorna ``(estado, reiniciado)``. Estado inválido da mesma análise gera
    erro, para não encobrir uma adulteração ou corrupção da trilha.
    """

    if raw_state is None:
        return (
            initialize_governance_state(
                recommendation, signature, registered_at=registered_at
            ),
            True,
        )

    try:
        state = GovernanceSessionState.model_validate(raw_state)
    except Exception as exc:
        raise ValueError("estado de governança inválido") from exc

    if state.assinatura_analise != signature:
        return (
            initialize_governance_state(
                recommendation, signature, registered_at=registered_at
            ),
            True,
        )
    if state.governanca.recomendacao_finscore != recommendation:
        raise ValueError("a recomendação FinScore registrada foi alterada")
    return state, False


def _validated_result(value: RecommendationCode | str) -> RecommendationCode:
    try:
        return RecommendationCode(value)
    except ValueError as exc:
        raise ValueError("resultado de governança inválido") from exc


def _validated_justification(value: str) -> str:
    result = str(value or "").strip()
    if len(result) < MIN_JUSTIFICATION_LENGTH:
        raise ValueError(
            f"informe uma fundamentação com ao menos {MIN_JUSTIFICATION_LENGTH} caracteres"
        )
    return result


def _validated_responsible(value: str) -> str:
    result = str(value or "").strip()
    if len(result) < 2:
        raise ValueError("responsável pelo registro não identificado")
    return result


def _current_divergences(
    recommendation: FinScoreRecommendation,
    analyst: HumanDecision | None,
    authority: HumanDecision | None,
) -> list[GovernanceDivergence]:
    result: list[GovernanceDivergence] = []
    if analyst is not None and analyst.resultado != recommendation.codigo:
        result.append(
            GovernanceDivergence(
                origem=GovernanceStage.RECOMMENDATION.value,
                resultado_origem=recommendation.codigo,
                destino=GovernanceStage.ANALYST.value,
                resultado_destino=analyst.resultado,
                justificativa=analyst.justificativa,
                responsavel=analyst.responsavel,
                registrado_em=analyst.registrado_em,
            )
        )
    if authority is not None:
        origin_stage = (
            GovernanceStage.ANALYST.value
            if analyst is not None
            else GovernanceStage.RECOMMENDATION.value
        )
        origin_result = analyst.resultado if analyst is not None else recommendation.codigo
        if authority.resultado != origin_result:
            result.append(
                GovernanceDivergence(
                    origem=origin_stage,
                    resultado_origem=origin_result,
                    destino=GovernanceStage.AUTHORITY.value,
                    resultado_destino=authority.resultado,
                    justificativa=authority.justificativa,
                    responsavel=authority.responsavel,
                    registrado_em=authority.registrado_em,
                )
            )
    return result


def register_analyst_manifestation(
    state: GovernanceSessionState,
    result: RecommendationCode | str,
    justification: str,
    responsible: str,
    *,
    registered_at: datetime | None = None,
) -> GovernanceSessionState:
    """Registra nova manifestação e invalida decisão de alçada anterior."""

    selected_result = _validated_result(result)
    rationale = _validated_justification(justification)
    actor = _validated_responsible(responsible)
    timestamp = registered_at or _now()
    current = state.governanca
    analyst = HumanDecision(
        resultado=selected_result,
        justificativa=rationale,
        responsavel=actor,
        registrado_em=timestamp,
    )
    action = (
        GovernanceAction.REPLACED
        if current.manifestacao_analista is not None
        else GovernanceAction.REGISTERED
    )
    events = [
        *current.historico,
        _event(
            stage=GovernanceStage.ANALYST,
            action=action,
            result=selected_result,
            justification=rationale,
            responsible=actor,
            registered_at=timestamp,
        ),
    ]
    if current.decisao_alcada is not None:
        events.append(
            _event(
                stage=GovernanceStage.AUTHORITY,
                action=GovernanceAction.INVALIDATED,
                result=current.decisao_alcada.resultado,
                justification=(
                    "Registro invalidado porque houve nova manifestação do analista; "
                    "a alçada deve deliberar novamente."
                ),
                responsible="Fluxo de governança",
                registered_at=timestamp,
            )
        )

    governance = Governance(
        recomendacao_finscore=current.recomendacao_finscore,
        manifestacao_analista=analyst,
        decisao_alcada=None,
        divergencias=_current_divergences(
            current.recomendacao_finscore, analyst, None
        ),
        historico=events,
    )
    return GovernanceSessionState(
        assinatura_analise=state.assinatura_analise,
        governanca=governance,
    )


def register_authority_decision(
    state: GovernanceSessionState,
    result: RecommendationCode | str,
    justification: str,
    responsible: str,
    *,
    registered_at: datetime | None = None,
) -> GovernanceSessionState:
    """Registra a decisão da alçada sem sobrescrever as posições anteriores."""

    selected_result = _validated_result(result)
    rationale = _validated_justification(justification)
    actor = _validated_responsible(responsible)
    timestamp = registered_at or _now()
    current = state.governanca
    authority = HumanDecision(
        resultado=selected_result,
        justificativa=rationale,
        responsavel=actor,
        registrado_em=timestamp,
    )
    action = (
        GovernanceAction.REPLACED
        if current.decisao_alcada is not None
        else GovernanceAction.REGISTERED
    )
    event = _event(
        stage=GovernanceStage.AUTHORITY,
        action=action,
        result=selected_result,
        justification=rationale,
        responsible=actor,
        registered_at=timestamp,
    )
    governance = Governance(
        recomendacao_finscore=current.recomendacao_finscore,
        manifestacao_analista=current.manifestacao_analista,
        decisao_alcada=authority,
        divergencias=_current_divergences(
            current.recomendacao_finscore,
            current.manifestacao_analista,
            authority,
        ),
        historico=[*current.historico, event],
    )
    return GovernanceSessionState(
        assinatura_analise=state.assinatura_analise,
        governanca=governance,
    )


__all__ = [
    "GOVERNANCE_SESSION_KEY",
    "GOVERNANCE_STATE_VERSION",
    "GovernanceAction",
    "GovernanceAuditEvent",
    "GovernanceSessionState",
    "GovernanceStage",
    "governance_fingerprint",
    "initialize_governance_state",
    "load_or_initialize_governance_state",
    "register_analyst_manifestation",
    "register_authority_decision",
]
