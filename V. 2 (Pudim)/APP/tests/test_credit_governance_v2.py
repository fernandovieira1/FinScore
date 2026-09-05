from __future__ import annotations

from datetime import datetime
from pathlib import Path
import unittest

import pandas as pd

from app_front.components.parecer_data_schema import RecommendationCode
from app_front.services.credit_governance import (
    GovernanceAction,
    GovernanceSessionState,
    GovernanceStage,
    governance_fingerprint,
    initialize_governance_state,
    load_or_initialize_governance_state,
    register_analyst_manifestation,
    register_authority_decision,
)
from app_front.services.credit_policy import decide_pudim
from app_front.services.finscore_service import run_finscore
from app_front.services.parecer_data_builder import (
    build_finscore_recommendation,
    build_parecer_data,
)


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class CreditGovernanceV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.meta = {
            "empresa": "Callamarys",
            "cnpj": "00.000.000/0000-00",
            "ano_inicial": 2023,
            "ano_final": 2025,
            "serasa": 700,
            "serasa_data": "23/07/2026",
            "serasa_restricao_grave": False,
        }
        cls.output = run_finscore(data, dict(cls.meta), executar_simulacoes=False)
        cls.policy = decide_pudim(cls.output, cls.meta)
        cls.recommendation = build_finscore_recommendation(cls.output, cls.policy)
        cls.signature = governance_fingerprint(cls.output, cls.recommendation)

    def _state(self) -> GovernanceSessionState:
        return initialize_governance_state(
            self.recommendation,
            self.signature,
            registered_at=datetime(2026, 9, 4, 10, 0),
        )

    def test_initial_state_has_only_immutable_finscore_recommendation(self) -> None:
        state = self._state()

        self.assertEqual(
            state.governanca.recomendacao_finscore,
            self.recommendation,
        )
        self.assertIsNone(state.governanca.manifestacao_analista)
        self.assertIsNone(state.governanca.decisao_alcada)
        self.assertEqual(
            state.governanca.historico[0].etapa,
            GovernanceStage.RECOMMENDATION,
        )

    def test_analyst_divergence_is_registered_without_changing_recommendation(self) -> None:
        state = register_analyst_manifestation(
            self._state(),
            RecommendationCode.APPROVE,
            "Documentos adicionais foram conferidos e sustentam a posição favorável.",
            "analista@instituicao.test",
            registered_at=datetime(2026, 9, 4, 11, 0),
        )

        self.assertEqual(state.governanca.recomendacao_finscore, self.recommendation)
        self.assertEqual(
            state.governanca.manifestacao_analista.resultado,
            RecommendationCode.APPROVE,
        )
        self.assertEqual(len(state.governanca.divergencias), 1)
        self.assertEqual(
            state.governanca.divergencias[0].origem,
            GovernanceStage.RECOMMENDATION.value,
        )

    def test_equal_analyst_position_does_not_create_divergence(self) -> None:
        state = register_analyst_manifestation(
            self._state(),
            self.recommendation.codigo,
            "A documentação examinada confirma os fundamentos da recomendação calculada.",
            "analista@instituicao.test",
        )

        self.assertEqual(state.governanca.divergencias, [])

    def test_short_justification_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "ao menos 20 caracteres"):
            register_analyst_manifestation(
                self._state(),
                self.recommendation.codigo,
                "Concordo.",
                "analista@instituicao.test",
            )

    def test_authority_divergence_uses_analyst_as_immediate_origin(self) -> None:
        analyst_state = register_analyst_manifestation(
            self._state(),
            RecommendationCode.APPROVE,
            "Os documentos complementares permitem manifestação favorável do analista.",
            "analista@instituicao.test",
        )
        final_state = register_authority_decision(
            analyst_state,
            RecommendationCode.DO_NOT_APPROVE,
            "A alçada considerou a concentração consolidada incompatível com o limite interno.",
            "alcada@instituicao.test",
        )

        authority_divergence = final_state.governanca.divergencias[-1]
        self.assertEqual(
            authority_divergence.origem,
            GovernanceStage.ANALYST.value,
        )
        self.assertEqual(
            authority_divergence.destino,
            GovernanceStage.AUTHORITY.value,
        )

    def test_new_analyst_manifestation_invalidates_current_authority_decision(self) -> None:
        analyst_state = register_analyst_manifestation(
            self._state(),
            self.recommendation.codigo,
            "A manifestação acompanha os dados e controles apresentados nesta análise.",
            "analista@instituicao.test",
        )
        final_state = register_authority_decision(
            analyst_state,
            self.recommendation.codigo,
            "A alçada acompanha a manifestação e os fundamentos documentados no parecer.",
            "alcada@instituicao.test",
        )
        revised_state = register_analyst_manifestation(
            final_state,
            RecommendationCode.APPROVE,
            "Novos documentos alteraram a avaliação profissional anteriormente registrada.",
            "analista@instituicao.test",
        )

        self.assertIsNone(revised_state.governanca.decisao_alcada)
        self.assertEqual(
            revised_state.governanca.historico[-1].acao,
            GovernanceAction.INVALIDATED,
        )
        self.assertEqual(
            revised_state.governanca.historico[-1].etapa,
            GovernanceStage.AUTHORITY,
        )

    def test_new_analysis_starts_a_separate_governance_state(self) -> None:
        previous = register_analyst_manifestation(
            self._state(),
            self.recommendation.codigo,
            "A posição acompanha integralmente a recomendação e seus fundamentos.",
            "analista@instituicao.test",
        )

        loaded, reset = load_or_initialize_governance_state(
            previous.model_dump(mode="json"),
            self.recommendation,
            "a" * 64,
        )

        self.assertTrue(reset)
        self.assertIsNone(loaded.governanca.manifestacao_analista)
        self.assertEqual(len(loaded.governanca.historico), 1)

    def test_state_survives_json_compatible_round_trip(self) -> None:
        state = register_analyst_manifestation(
            self._state(),
            self.recommendation.codigo,
            "A posição acompanha integralmente a recomendação e seus fundamentos.",
            "analista@instituicao.test",
        )

        loaded, reset = load_or_initialize_governance_state(
            state.model_dump(mode="json"),
            self.recommendation,
            self.signature,
        )

        self.assertFalse(reset)
        self.assertEqual(loaded, state)

    def test_structured_contract_accepts_governance_but_rejects_changed_recommendation(self) -> None:
        state = register_analyst_manifestation(
            self._state(),
            self.recommendation.codigo,
            "A manifestação confirma a análise dos dados contábeis e financeiros.",
            "analista@instituicao.test",
        )
        contract = build_parecer_data(
            self.output,
            self.meta,
            self.policy,
            governance=state.governanca,
        )
        tampered = state.governanca.model_dump(mode="json")
        tampered["recomendacao_finscore"]["regra_id"] = "REGRA-ALTERADA"

        self.assertIsNotNone(contract.governanca.manifestacao_analista)
        self.assertEqual(len(contract.governanca.historico), 2)
        with self.assertRaisesRegex(ValueError, "tenta alterar"):
            build_parecer_data(
                self.output,
                self.meta,
                self.policy,
                governance=tampered,
            )


if __name__ == "__main__":
    unittest.main()
