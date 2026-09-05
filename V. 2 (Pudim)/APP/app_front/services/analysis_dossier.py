"""Persistência do dossiê funcional e da trilha de governança do parecer.

O JSON funcional é deliberadamente separado da telemetria operacional. Eventos
de governança são somente acrescentados; manifestações e decisões registradas
recebem um comprovante eletrônico vinculado ao conteúdo e ao usuário autenticado.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from typing import Any, Callable, Iterator

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:  # Execução Streamlit, com app_front no sys.path.
    from components.parecer_data_schema import (
        GovernanceAction,
        GovernanceStage,
        ParecerData,
    )
    from components.parecer_schema import ParecerNarrativo
    from services.db import SessionLocal, init_db
    from services.models import (
        AnalysisDossier,
        CreditRoleAssignment,
        GovernanceEventRecord,
        GovernanceSignatureRecord,
        TechnicalTelemetryRecord,
    )
    from services.parecer_document import methodology_sha256
except ModuleNotFoundError:  # Importação como pacote nos testes.
    from app_front.components.parecer_data_schema import (
        GovernanceAction,
        GovernanceStage,
        ParecerData,
    )
    from app_front.components.parecer_schema import ParecerNarrativo
    from app_front.services.db import SessionLocal, init_db
    from app_front.services.models import (
        AnalysisDossier,
        CreditRoleAssignment,
        GovernanceEventRecord,
        GovernanceSignatureRecord,
        TechnicalTelemetryRecord,
    )
    from app_front.services.parecer_document import methodology_sha256


DOSSIER_VERSION = "1.0"
STATUS_DRAFT = "em_elaboracao"
STATUS_REPORT = "parecer_validado"
STATUS_ANALYST = "manifestacao_registrada"
STATUS_AUTHORITY = "decisao_registrada"
ALLOWED_CREDIT_ROLES = frozenset({"analista", "alcada", "administrador"})

_FORBIDDEN_FUNCTIONAL_TEXT = re.compile(
    r"\b(?:IA|OpenAI|GPT(?:-[A-Za-z0-9.]+)?|prompt|Pudim|Brigadeiro|"
    r"intelig[eê]ncia artificial|modelo de linguagem)\b",
    flags=re.IGNORECASE,
)
_FORBIDDEN_FUNCTIONAL_KEYS = frozenset(
    {
        "metadados_tecnicos_restritos",
        "provider",
        "model",
        "prompt",
        "temperature",
        "reasoning_effort",
        "token_usage",
    }
)


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _email(value: str | None) -> str | None:
    result = str(value or "").strip().lower()
    return result or None


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _configured_emails(variable: str) -> set[str]:
    return {
        item.strip().lower()
        for item in os.getenv(variable, "").split(",")
        if item.strip()
    }


def _validate_functional_payload(value: Any, path: str = "dossie") -> None:
    """Impede que informações da tecnologia de redação migrem ao dossiê."""

    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in _FORBIDDEN_FUNCTIONAL_KEYS:
                raise ValueError(f"campo técnico restrito no dossiê funcional: {path}.{key}")
            _validate_functional_payload(nested, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _validate_functional_payload(nested, f"{path}[{index}]")
        return
    if isinstance(value, str) and _FORBIDDEN_FUNCTIONAL_TEXT.search(value):
        raise ValueError(f"termo técnico restrito no dossiê funcional: {path}")


class AnalysisDossierStore:
    """Repositório transacional para análises e registros de governança."""

    def __init__(
        self,
        session_factory: Callable[[], Session] = SessionLocal,
        *,
        initialize_schema: bool = True,
    ) -> None:
        self._session_factory = session_factory
        if initialize_schema and session_factory is SessionLocal:
            init_db()

    @contextmanager
    def _session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ensure_analysis(
        self,
        *,
        fingerprint: str,
        processed_at: datetime,
        recommendation_code: str,
        governance_signature: str,
        meta: dict[str, Any],
        output: dict[str, Any],
        owner_email: str | None,
    ) -> str:
        """Obtém ou cria o identificador imutável ``FS-AAAA-NNNNNN``."""

        with self._session() as session:
            current = session.execute(
                select(AnalysisDossier).where(
                    AnalysisDossier.analysis_fingerprint == fingerprint
                )
            ).scalar_one_or_none()
            if current is not None:
                return current.analysis_id

            year = int(processed_at.year)
            sequence = session.execute(
                text(
                    "INSERT INTO analysis_sequences (year, last_value) VALUES (:year, 1) "
                    "ON CONFLICT(year) DO UPDATE SET last_value = last_value + 1 "
                    "RETURNING last_value"
                ),
                {"year": year},
            ).scalar_one()
            analysis_id = f"FS-{year}-{int(sequence):06d}"
            record = AnalysisDossier(
                analysis_id=analysis_id,
                analysis_fingerprint=fingerprint,
                owner_email=_email(owner_email),
                tomador_nome=str(meta.get("empresa") or "").strip() or None,
                tomador_cnpj=str(meta.get("cnpj") or "").strip() or None,
                status=STATUS_DRAFT,
                schema_version=DOSSIER_VERSION,
                recommendation_code=str(recommendation_code),
                methodology_hash=methodology_sha256(),
                reported_data_hash=str(output.get("hash_dados_reportados") or "") or None,
                used_data_hash=str(output.get("hash_dados_utilizados") or "") or None,
                governance_signature=governance_signature,
                functional_dossier_json="{}",
            )
            session.add(record)
            try:
                session.flush()
            except IntegrityError:
                # Concorrência sobre a mesma impressão digital: preserva o registro vencedor.
                session.rollback()
                current = session.execute(
                    select(AnalysisDossier).where(
                        AnalysisDossier.analysis_fingerprint == fingerprint
                    )
                ).scalar_one_or_none()
                if current is None:
                    raise
                return current.analysis_id
            return analysis_id

    def load_governance(self, analysis_id: str) -> dict[str, Any] | None:
        with self._session() as session:
            record = self._record(session, analysis_id)
            return json.loads(record.governance_json) if record.governance_json else None

    def load_document(self, analysis_id: str) -> str | None:
        """Recupera o parecer validado da mesma análise, quando existente."""

        with self._session() as session:
            return self._record(session, analysis_id).document_markdown

    def roles_for(self, email: str | None) -> frozenset[str]:
        normalized = _email(email)
        if normalized is None:
            return frozenset()
        with self._session() as session:
            return self._roles_for_session(session, normalized)

    def can_register_authority(self, email: str | None) -> bool:
        return bool(self.roles_for(email) & {"alcada", "administrador"})

    def grant_role(self, email: str, role: str) -> None:
        normalized = _email(email)
        selected = str(role or "").strip().lower()
        if normalized is None or selected not in ALLOWED_CREDIT_ROLES:
            raise ValueError("usuário ou perfil de crédito inválido")
        with self._session() as session:
            existing = session.execute(
                select(CreditRoleAssignment).where(
                    CreditRoleAssignment.email == normalized,
                    CreditRoleAssignment.role == selected,
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(CreditRoleAssignment(email=normalized, role=selected))

    def save_contract(
        self,
        analysis_id: str,
        contract: ParecerData,
        governance_state: dict[str, Any],
        *,
        actor_email: str | None,
        invalidate_report: bool = False,
    ) -> dict[str, Any]:
        functional_contract = contract.model_dump(
            mode="json", exclude={"metadados_tecnicos_restritos"}
        )
        with self._session() as session:
            record = self._record(session, analysis_id)
            current = json.loads(record.functional_dossier_json or "{}")
            dossier = {
                "dossie_versao": DOSSIER_VERSION,
                "analise_id": analysis_id,
                "contrato": functional_contract,
                "integridade": {
                    "hash_metodologia": methodology_sha256(),
                    "hash_dados_reportados": record.reported_data_hash,
                    "hash_dados_utilizados": record.used_data_hash,
                },
            }
            if not invalidate_report:
                for key in ("narrativa", "documento", "validacao"):
                    if key in current:
                        dossier[key] = current[key]
            _validate_functional_payload(dossier)
            record.functional_dossier_json = _json(dossier)
            record.governance_json = _json(governance_state)
            record.recommendation_code = contract.governanca.recomendacao_finscore.codigo.value
            if invalidate_report:
                record.document_markdown = None
                record.document_hash = None
            self._sync_governance(
                session,
                record,
                contract,
                actor_email=actor_email,
            )
            record.status = self._status(contract, report_saved=not invalidate_report and bool(record.document_hash))
            session.add(record)
            return dossier

    def save_report(
        self,
        analysis_id: str,
        contract: ParecerData,
        narrative: ParecerNarrativo,
        document_markdown: str,
        validation: dict[str, Any],
        *,
        actor_email: str | None,
    ) -> dict[str, Any]:
        functional_contract = contract.model_dump(
            mode="json", exclude={"metadados_tecnicos_restritos"}
        )
        dossier = {
            "dossie_versao": DOSSIER_VERSION,
            "analise_id": analysis_id,
            "contrato": functional_contract,
            "narrativa": narrative.model_dump(mode="json"),
            "documento": {
                "formato": "markdown",
                "sha256": _sha256(document_markdown),
                "conteudo": document_markdown,
            },
            "validacao": validation,
            "integridade": {
                "hash_metodologia": methodology_sha256(),
                "hash_dados_reportados": contract.metadados_tecnicos_restritos.hash_dados_reportados,
                "hash_dados_utilizados": contract.metadados_tecnicos_restritos.hash_dados_utilizados,
            },
        }
        _validate_functional_payload(dossier)
        with self._session() as session:
            record = self._record(session, analysis_id)
            self._sync_governance(session, record, contract, actor_email=actor_email)
            record.functional_dossier_json = _json(dossier)
            record.governance_json = _json(
                {
                    "versao": "1.0",
                    "assinatura_analise": record.governance_signature,
                    "governanca": contract.governanca.model_dump(mode="json"),
                }
            )
            record.document_markdown = document_markdown
            record.document_hash = dossier["documento"]["sha256"]
            record.status = self._status(contract, report_saved=True)
            session.add(record)
        return dossier

    def record_technical_telemetry(
        self,
        analysis_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        serialized = _json(payload)
        with self._session() as session:
            record = self._record(session, analysis_id)
            session.add(
                TechnicalTelemetryRecord(
                    analysis_dossier_id=record.id,
                    event_type=str(event_type)[:48],
                    payload_json=serialized,
                    payload_hash=_sha256(serialized),
                )
            )

    def record_pdf_export(self, analysis_id: str, pdf_bytes: bytes, pages: int) -> None:
        if not 7 <= int(pages) <= 14:
            raise ValueError("PDF fora da faixa de 7 a 14 páginas")
        with self._session() as session:
            record = self._record(session, analysis_id)
            dossier = json.loads(record.functional_dossier_json)
            document = dossier.setdefault("documento", {})
            document["pdf"] = {
                "sha256": hashlib.sha256(pdf_bytes).hexdigest(),
                "paginas": int(pages),
            }
            _validate_functional_payload(dossier)
            record.functional_dossier_json = _json(dossier)
            session.add(record)

    def export_functional_json(self, analysis_id: str) -> bytes:
        with self._session() as session:
            record = self._record(session, analysis_id)
            payload = json.loads(record.functional_dossier_json)
        _validate_functional_payload(payload)
        return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    @staticmethod
    def _record(session: Session, analysis_id: str) -> AnalysisDossier:
        record = session.execute(
            select(AnalysisDossier).where(AnalysisDossier.analysis_id == analysis_id)
        ).scalar_one_or_none()
        if record is None:
            raise ValueError("análise persistente não localizada")
        return record

    def _sync_governance(
        self,
        session: Session,
        record: AnalysisDossier,
        contract: ParecerData,
        *,
        actor_email: str | None,
    ) -> None:
        normalized_actor = _email(actor_email)
        existing = {
            item.event_id: item
            for item in session.execute(
                select(GovernanceEventRecord).where(
                    GovernanceEventRecord.analysis_dossier_id == record.id
                )
            ).scalars()
        }
        for order, event in enumerate(contract.governanca.historico, 1):
            payload = event.model_dump(mode="json")
            event_hash = _sha256(_json(payload))
            if event.evento_id in existing:
                if existing[event.evento_id].event_hash != event_hash:
                    raise ValueError("evento de governança persistido foi alterado")
                continue

            human_event = (
                event.etapa in {GovernanceStage.ANALYST, GovernanceStage.AUTHORITY}
                and event.acao in {GovernanceAction.REGISTERED, GovernanceAction.REPLACED}
            )
            if human_event:
                if normalized_actor is None or _email(event.responsavel) != normalized_actor:
                    raise PermissionError("o registro deve pertencer ao usuário autenticado")
                if (
                    event.etapa is GovernanceStage.AUTHORITY
                    and not (
                        self._roles_for_session(session, normalized_actor)
                        & {"alcada", "administrador"}
                    )
                ):
                    raise PermissionError("usuário sem perfil de alçada")

            session.add(
                GovernanceEventRecord(
                    analysis_dossier_id=record.id,
                    event_id=event.evento_id,
                    event_order=order,
                    stage=event.etapa.value,
                    action=event.acao.value,
                    result=event.resultado.value,
                    justification=event.justificativa,
                    responsible=event.responsavel,
                    registered_at=_naive_utc(event.registrado_em),
                    event_hash=event_hash,
                )
            )
            if human_event:
                role = "alcada" if event.etapa is GovernanceStage.AUTHORITY else "analista"
                session.add(
                    GovernanceSignatureRecord(
                        analysis_dossier_id=record.id,
                        event_id=event.evento_id,
                        signer_email=normalized_actor,
                        signer_role=role,
                        signed_at=_naive_utc(event.registrado_em),
                        signed_content_hash=event_hash,
                    )
                )

    @staticmethod
    def _status(contract: ParecerData, *, report_saved: bool) -> str:
        if contract.governanca.decisao_alcada is not None:
            return STATUS_AUTHORITY
        if contract.governanca.manifestacao_analista is not None:
            return STATUS_ANALYST
        return STATUS_REPORT if report_saved else STATUS_DRAFT

    @staticmethod
    def _roles_for_session(session: Session, normalized_email: str) -> frozenset[str]:
        roles = {"analista"}
        if normalized_email in _configured_emails("FINSCORE_AUTHORITY_EMAILS"):
            roles.add("alcada")
        if normalized_email in _configured_emails("FINSCORE_ADMIN_EMAILS"):
            roles.update({"alcada", "administrador"})
        stored = session.execute(
            select(CreditRoleAssignment.role).where(
                CreditRoleAssignment.email == normalized_email
            )
        ).scalars()
        roles.update(role for role in stored if role in ALLOWED_CREDIT_ROLES)
        return frozenset(roles)


__all__ = [
    "ALLOWED_CREDIT_ROLES",
    "AnalysisDossierStore",
    "DOSSIER_VERSION",
    "STATUS_ANALYST",
    "STATUS_AUTHORITY",
    "STATUS_DRAFT",
    "STATUS_REPORT",
]
