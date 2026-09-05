from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import unittest

import pandas as pd
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app_front.components.parecer_data_schema import FindingCategory
from app_front.components.parecer_schema import ParecerNarrativo
from app_front.services.analysis_dossier import AnalysisDossierStore
from app_front.services.credit_governance import (
    governance_fingerprint,
    initialize_governance_state,
    register_analyst_manifestation,
    register_authority_decision,
)
from app_front.services.credit_policy import decide_pudim
from app_front.services.db import Base
from app_front.services.finscore_service import run_finscore
from app_front.services.models import (
    AnalysisDossier,
    GovernanceEventRecord,
    GovernanceSignatureRecord,
    TechnicalTelemetryRecord,
)
from app_front.services.parecer_data_builder import (
    build_finscore_recommendation,
    build_parecer_data,
)
from app_front.services.parecer_document import render_structured_parecer
from app_front.services.parecer_generator import build_narrative_context
from APP.tests.test_parecer_validation_v2 import SECTION_TEXTS


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class AnalysisDossierStoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.base_meta = {
            "empresa": "Callamarys",
            "cnpj": "00.000.000/0000-00",
            "ano_inicial": 2023,
            "ano_final": 2025,
            "serasa": 700,
            "serasa_data": "23/07/2026",
            "serasa_restricao_grave": False,
        }
        cls.output = run_finscore(data, dict(cls.base_meta), executar_simulacoes=False)
        cls.policy = decide_pudim(cls.output, cls.base_meta)
        cls.recommendation = build_finscore_recommendation(cls.output, cls.policy)
        cls.fingerprint = governance_fingerprint(cls.output, cls.recommendation)

    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(engine, "connect")
        def _foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, expire_on_commit=False)
        self.store = AnalysisDossierStore(self.Session, initialize_schema=False)

    def _create(self):
        meta = dict(self.base_meta)
        raw_processed = self.output["modelo"]["processado_em"]
        processed = (
            raw_processed
            if isinstance(raw_processed, datetime)
            else datetime.fromisoformat(str(raw_processed))
        )
        analysis_id = self.store.ensure_analysis(
            fingerprint=self.fingerprint,
            processed_at=processed,
            recommendation_code=self.recommendation.codigo.value,
            governance_signature=self.fingerprint,
            meta=meta,
            output=self.output,
            owner_email="analista@instituicao.test",
        )
        meta["analise_id"] = analysis_id
        state = initialize_governance_state(
            self.recommendation,
            self.fingerprint,
            registered_at=processed,
        )
        contract = build_parecer_data(
            self.output,
            meta,
            self.policy,
            governance=state.governanca,
        )
        self.store.save_contract(
            analysis_id,
            contract,
            state.model_dump(mode="json"),
            actor_email="analista@instituicao.test",
        )
        return meta, state, contract

    def test_transactional_identifier_is_stable_and_sequential(self) -> None:
        meta, _state, _contract = self._create()
        raw_processed = self.output["modelo"]["processado_em"]
        processed = (
            raw_processed
            if isinstance(raw_processed, datetime)
            else datetime.fromisoformat(str(raw_processed))
        )
        same = self.store.ensure_analysis(
            fingerprint=self.fingerprint,
            processed_at=processed,
            recommendation_code=self.recommendation.codigo.value,
            governance_signature=self.fingerprint,
            meta=meta,
            output=self.output,
            owner_email="analista@instituicao.test",
        )
        second = self.store.ensure_analysis(
            fingerprint="B" * 64,
            processed_at=processed,
            recommendation_code=self.recommendation.codigo.value,
            governance_signature="B" * 64,
            meta=meta,
            output=self.output,
            owner_email="analista@instituicao.test",
        )

        self.assertEqual(same, meta["analise_id"])
        self.assertRegex(same, r"^FS-\d{4}-000001$")
        self.assertRegex(second, r"^FS-\d{4}-000002$")

    def test_functional_export_excludes_restricted_technical_metadata(self) -> None:
        meta, _state, _contract = self._create()
        exported = self.store.export_functional_json(meta["analise_id"])
        payload = json.loads(exported)
        serialized = exported.decode("utf-8")

        self.assertEqual(payload["analise_id"], meta["analise_id"])
        self.assertIn("contrato", payload)
        self.assertNotIn("metadados_tecnicos_restritos", serialized)
        self.assertNotIn("OpenAI", serialized)
        self.assertNotIn("gpt-", serialized.lower())

    def test_governance_events_are_append_only_and_signed(self) -> None:
        meta, state, _contract = self._create()
        updated = register_analyst_manifestation(
            state,
            self.recommendation.codigo,
            "A manifestação acompanha os elementos documentados na análise.",
            "analista@instituicao.test",
        )
        contract = build_parecer_data(
            self.output, meta, self.policy, governance=updated.governanca
        )
        self.store.save_contract(
            meta["analise_id"],
            contract,
            updated.model_dump(mode="json"),
            actor_email="analista@instituicao.test",
            invalidate_report=True,
        )

        with self.Session() as session:
            self.assertEqual(
                session.scalar(select(func.count()).select_from(GovernanceEventRecord)), 2
            )
            self.assertEqual(
                session.scalar(select(func.count()).select_from(GovernanceSignatureRecord)), 1
            )

        altered = updated.model_dump(mode="json")
        altered["governanca"]["manifestacao_analista"]["justificativa"] += " Alterada."
        altered["governanca"]["historico"][-1]["justificativa"] += " Alterada."
        altered_state = type(updated).model_validate(altered)
        altered_contract = build_parecer_data(
            self.output, meta, self.policy, governance=altered_state.governanca
        )
        with self.assertRaisesRegex(ValueError, "foi alterado"):
            self.store.save_contract(
                meta["analise_id"],
                altered_contract,
                altered_state.model_dump(mode="json"),
                actor_email="analista@instituicao.test",
            )

    def test_authority_decision_requires_authority_role(self) -> None:
        meta, state, _contract = self._create()
        authority = register_authority_decision(
            state,
            self.recommendation.codigo,
            "A alçada acompanha os fundamentos e controles registrados.",
            "gestor@instituicao.test",
        )
        contract = build_parecer_data(
            self.output, meta, self.policy, governance=authority.governanca
        )
        with self.assertRaisesRegex(PermissionError, "perfil de alçada"):
            self.store.save_contract(
                meta["analise_id"],
                contract,
                authority.model_dump(mode="json"),
                actor_email="gestor@instituicao.test",
            )

        self.store.grant_role("gestor@instituicao.test", "alcada")
        self.store.save_contract(
            meta["analise_id"],
            contract,
            authority.model_dump(mode="json"),
            actor_email="gestor@instituicao.test",
        )
        with self.Session() as session:
            record = session.scalar(select(AnalysisDossier))
            signatures = session.scalar(
                select(func.count()).select_from(GovernanceSignatureRecord)
            )
        self.assertEqual(record.status, "decisao_registrada")
        self.assertEqual(signatures, 1)

    def test_failed_report_attempt_preserves_contract_and_records_telemetry(self) -> None:
        meta, _state, _contract = self._create()
        self.store.record_technical_telemetry(
            meta["analise_id"],
            "parecer_nao_concluido",
            {"error_type": "ServiceUnavailable", "model": "restricted-model"},
        )
        functional = json.loads(self.store.export_functional_json(meta["analise_id"]))
        with self.Session() as session:
            telemetry = session.scalar(
                select(func.count()).select_from(TechnicalTelemetryRecord)
            )

        self.assertIn("contrato", functional)
        self.assertNotIn("documento", functional)
        self.assertEqual(telemetry, 1)

    def test_validated_report_is_persisted_and_recovered(self) -> None:
        meta, _state, contract = self._create()
        context = build_narrative_context(contract)
        payload = {
            name: {
                "texto": text,
                "achado_ids": context["roteiro_achados"][name][:1],
            }
            for name, text in SECTION_TEXTS.items()
        }
        blockers = [
            item.achado_id
            for item in contract.achados
            if item.categoria is FindingCategory.BLOCK
        ]
        payload["escopo_e_qualidade"]["achado_ids"] = list(
            dict.fromkeys([*payload["escopo_e_qualidade"]["achado_ids"], *blockers])
        )
        payload.update(
            pontos_fortes=[],
            riscos_prioritarios=[],
            validacoes_pendentes=[],
            recomendacoes_monitoramento=[],
        )
        narrative = ParecerNarrativo.model_validate(payload)
        document = render_structured_parecer(narrative, contract)

        dossier = self.store.save_report(
            meta["analise_id"],
            contract,
            narrative,
            document,
            {"narrativa": {"valido": True}, "documento": {"valido": True}},
            actor_email="analista@instituicao.test",
        )

        self.assertEqual(self.store.load_document(meta["analise_id"]), document)
        self.assertEqual(dossier["documento"]["conteudo"], document)
        with self.Session() as session:
            record = session.scalar(select(AnalysisDossier))
        self.assertEqual(record.status, "parecer_validado")
        self.assertEqual(record.document_hash, dossier["documento"]["sha256"])


if __name__ == "__main__":
    unittest.main()
