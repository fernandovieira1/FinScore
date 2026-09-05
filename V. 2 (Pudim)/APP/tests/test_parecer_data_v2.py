from __future__ import annotations

import copy
from datetime import datetime
import json
from pathlib import Path
import unittest

import pandas as pd
from pydantic import ValidationError

from app_front.components.parecer_data_schema import (
    Governance,
    GovernanceAction,
    GovernanceAuditEvent,
    GovernanceDivergence,
    GovernanceStage,
    HumanDecision,
    PARECER_DATA_SCHEMA_VERSION,
    ParecerData,
    RecommendationCode,
)
from app_front.services.credit_policy import decide_pudim
from app_front.services.finscore_service import run_finscore
from app_front.services.parecer_data_builder import build_parecer_data


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class ParecerDataV2Test(unittest.TestCase):
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

    def _build(self, meta: dict | None = None) -> ParecerData:
        return build_parecer_data(self.output, meta or self.meta, self.policy)

    def test_builds_typed_contract_from_current_engine_output(self) -> None:
        contract = self._build()

        self.assertEqual(contract.schema_versao, PARECER_DATA_SCHEMA_VERSION)
        self.assertRegex(contract.analise_id, r"^FS-\d{4}-[A-F0-9]{12}$")
        self.assertEqual(contract.identificacao.periodos.analisado.exercicios, [2023, 2024, 2025])
        self.assertEqual(contract.governanca.recomendacao_finscore.codigo, RecommendationCode.INCONSISTENT_DATA)
        self.assertAlmostEqual(contract.finscore.prudencial or 0.0, 412.2311278076248)
        self.assertEqual(len(contract.dados.reportados), 63)
        self.assertEqual(len(contract.dados.utilizados), 63)
        self.assertEqual(len(contract.dados.rastreabilidade), 63)
        self.assertEqual(len(contract.dados.indices), 54)
        self.assertEqual(len(contract.dados.notas), 45)
        self.assertEqual(len(contract.governanca.recomendacao_finscore.bloqueios), 3)

    def test_missing_values_remain_null_in_json(self) -> None:
        contract = self._build()
        missing = [
            item
            for item in contract.dados.reportados
            if item.campo == "p_Obrigacoes_Trabalhistas_CP"
        ]

        self.assertEqual(len(missing), 3)
        self.assertTrue(all(item.valor is None for item in missing))
        serialized = contract.model_dump_json()
        self.assertNotIn(":NaN", serialized)
        self.assertNotIn(":Infinity", serialized)
        serialized_missing = [
            item
            for item in json.loads(serialized)["dados"]["reportados"]
            if item["campo"] == "p_Obrigacoes_Trabalhistas_CP"
        ]
        self.assertTrue(all(item["valor"] is None for item in serialized_missing))

    def test_cadastral_period_is_separate_and_divergence_is_explicit(self) -> None:
        meta = {
            **self.meta,
            "periodo_cadastral": {"inicio": 2021, "fim": 2023},
        }

        contract = self._build(meta)

        self.assertEqual(contract.identificacao.periodos.cadastral.inicio, 2021)
        self.assertEqual(contract.identificacao.periodos.analisado.inicio, 2023)
        self.assertEqual(len(contract.identificacao.periodos.divergencias), 1)
        self.assertIn(
            "não altera silenciosamente",
            contract.identificacao.periodos.divergencias[0].impacto,
        )

    def test_optional_operation_fields_are_contextual_only(self) -> None:
        enriched_meta = {
            **self.meta,
            "concedente_nome": "Banco Exemplo S.A.",
            "concedente_cnpj": "11.111.111/0001-11",
            "natureza_operacao": "Capital de giro",
            "finalidade_operacao": "Reforço de caixa",
            "valor_operacao": 2_500_000,
            "prazo_operacao": 24,
            "moeda": "brl",
        }

        baseline = self._build()
        enriched = self._build(enriched_meta)

        self.assertEqual(
            enriched.governanca.recomendacao_finscore,
            baseline.governanca.recomendacao_finscore,
        )
        self.assertEqual(enriched.identificacao.operacao.valor, 2_500_000)
        self.assertEqual(enriched.identificacao.operacao.prazo.valor, 24)
        self.assertEqual(enriched.identificacao.operacao.moeda, "BRL")

    def test_analysis_id_is_stable_for_same_execution_and_can_be_informed(self) -> None:
        first = self._build()
        second = self._build()
        informed = self._build({**self.meta, "analise_id": "FS-2026-000001"})

        self.assertEqual(first.analise_id, second.analise_id)
        self.assertEqual(informed.analise_id, "FS-2026-000001")
        self.assertEqual(
            informed.metadados_tecnicos_restritos.origem_analise_id,
            "informado",
        )

    def test_contract_rejects_score_divergence_between_sections(self) -> None:
        payload = self._build().model_dump(mode="json")
        payload["governanca"]["recomendacao_finscore"]["finscore_prudencial"] = 999.0

        with self.assertRaisesRegex(ValidationError, "FinScore diverge"):
            ParecerData.model_validate(payload)

    def test_contract_rejects_non_eligible_approval(self) -> None:
        payload = self._build().model_dump(mode="json")
        recommendation = payload["governanca"]["recomendacao_finscore"]
        recommendation["codigo"] = "aprovar"
        recommendation["rotulo"] = "Aprovar"
        recommendation["garantia"]["aplicavel"] = True

        with self.assertRaisesRegex(ValidationError, "resultado não apto"):
            ParecerData.model_validate(payload)

    def test_human_divergence_requires_audit_record(self) -> None:
        base = self._build().governanca
        analyst = HumanDecision(
            resultado=RecommendationCode.APPROVE,
            justificativa="Informações adicionais avaliadas pelo analista.",
            responsavel="Analista responsável",
            registrado_em=datetime(2026, 9, 4, 10, 0),
        )

        with self.assertRaisesRegex(ValidationError, "sem justificativa"):
            Governance(
                recomendacao_finscore=base.recomendacao_finscore,
                manifestacao_analista=analyst,
            )

        valid = Governance(
            recomendacao_finscore=base.recomendacao_finscore,
            manifestacao_analista=analyst,
            divergencias=[
                GovernanceDivergence(
                    origem="recomendacao_finscore",
                    resultado_origem=RecommendationCode.INCONSISTENT_DATA,
                    destino="manifestacao_analista",
                    resultado_destino=RecommendationCode.APPROVE,
                    justificativa="Foram consideradas informações adicionais documentadas.",
                    responsavel="Analista responsável",
                    registrado_em=datetime(2026, 9, 4, 10, 0),
                )
            ],
            historico=[
                GovernanceAuditEvent(
                    evento_id="GOV-RECOMENDACAO",
                    etapa=GovernanceStage.RECOMMENDATION,
                    acao=GovernanceAction.REGISTERED,
                    resultado=RecommendationCode.INCONSISTENT_DATA,
                    justificativa="Recomendação calculada pelas regras de crédito.",
                    responsavel="FinScore",
                    registrado_em=datetime(2026, 9, 4, 9, 0),
                ),
                GovernanceAuditEvent(
                    evento_id="GOV-ANALISTA",
                    etapa=GovernanceStage.ANALYST,
                    acao=GovernanceAction.REGISTERED,
                    resultado=RecommendationCode.APPROVE,
                    justificativa="Informações adicionais avaliadas pelo analista.",
                    responsavel="Analista responsável",
                    registrado_em=datetime(2026, 9, 4, 10, 0),
                ),
            ],
        )
        self.assertEqual(len(valid.divergencias), 1)

    def test_future_serasa_date_is_preserved_and_flagged(self) -> None:
        output = copy.deepcopy(self.output)
        output["df_serasa"].loc[:, "data_consulta"] = "31/12/2099"
        contract = build_parecer_data(output, self.meta, decide_pudim(output, self.meta))

        serasa = contract.evidencias_suplementares.serasa
        self.assertFalse(serasa.cronologia_valida)
        self.assertEqual(serasa.data_consulta, "31/12/2099")
        self.assertIn("posterior", serasa.alerta_temporal or "")

    def test_functional_metadata_excludes_generation_technology(self) -> None:
        functional = json.dumps(
            self._build().metadados_funcionais.model_dump(mode="json"),
            ensure_ascii=False,
        ).lower()

        for forbidden in ("openai", "gpt", "prompt", "temperatura", "token"):
            self.assertNotIn(forbidden, functional)

    def test_builder_does_not_mutate_engine_dataframes(self) -> None:
        before = self.output["df_contas_reportadas"].copy(deep=True)

        self._build()

        pd.testing.assert_frame_equal(before, self.output["df_contas_reportadas"])

    def test_extra_fields_are_forbidden(self) -> None:
        payload = self._build().model_dump(mode="json")
        payload["campo_desconhecido"] = True

        with self.assertRaises(ValidationError):
            ParecerData.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
