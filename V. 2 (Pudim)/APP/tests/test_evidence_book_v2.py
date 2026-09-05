from __future__ import annotations

import copy
from pathlib import Path
import unittest

import pandas as pd
from pydantic import ValidationError

from app_front.components.parecer_data_schema import (
    Finding,
    FindingCategory,
    FindingEvidence,
    FindingNature,
)
from app_front.services.credit_policy import decide_pudim
from app_front.services.evidence_book import build_evidence_book
from app_front.services.finscore_service import run_finscore
from app_front.services.parecer_data_builder import build_parecer_data


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class EvidenceBookV2Test(unittest.TestCase):
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
        cls.contract = build_parecer_data(cls.output, cls.meta, cls.policy)

    def test_builder_attaches_stable_unique_findings(self) -> None:
        first = self.contract.achados
        second = build_evidence_book(self.contract)

        self.assertGreater(len(first), 10)
        self.assertEqual(
            [item.achado_id for item in first],
            [item.achado_id for item in second],
        )
        self.assertEqual(len(first), len({item.achado_id for item in first}))

    def test_every_policy_blocker_has_reason_impact_and_action(self) -> None:
        blockers = [
            item for item in self.contract.achados if item.categoria is FindingCategory.BLOCK
        ]

        self.assertEqual(
            len(blockers),
            len(self.contract.governanca.recomendacao_finscore.bloqueios),
        )
        self.assertTrue(all(item.bloqueia_decisao for item in blockers))
        self.assertTrue(all(item.impacto_credito for item in blockers))
        self.assertTrue(all(item.providencia for item in blockers))

    def test_non_blocking_alerts_remain_non_blocking(self) -> None:
        alerts = [item for item in self.contract.achados if item.achado_id.startswith("ACH-ALT-")]

        self.assertTrue(alerts)
        self.assertTrue(all(item.categoria is FindingCategory.ALERT for item in alerts))
        self.assertTrue(all(not item.bloqueia_decisao for item in alerts))

    def test_score_limiters_reference_note_weight_and_contribution(self) -> None:
        limiters = [
            item for item in self.contract.achados if item.achado_id.startswith("ACH-FIN-LIM-")
        ]

        self.assertTrue(limiters)
        for item in limiters:
            fields = {evidence.campo for evidence in item.evidencias}
            self.assertIn("nota_temporal", fields)
            self.assertIn("peso_no_nucleo", fields)
            self.assertIn("contribuicao_nucleo_pontos", fields)
            self.assertIn("déficit ponderado", item.efeito_metodologico or "")

    def test_scenario_finding_is_explicitly_a_hypothesis(self) -> None:
        finding = next(
            item for item in self.contract.achados if item.achado_id == "ACH-CEN-SEVERO"
        )

        self.assertEqual(finding.natureza, FindingNature.HYPOTHESIS)
        self.assertIn("sem caráter preditivo", finding.efeito_metodologico or "")

    def test_supplementary_diagnostics_do_not_claim_to_change_finscore(self) -> None:
        supplementary = [
            item for item in self.contract.achados if item.achado_id.startswith("ACH-SUP-")
        ]

        self.assertTrue(supplementary)
        self.assertTrue(
            all(
                "não altera" in (item.efeito_metodologico or "").lower()
                or "não são somados" in (item.efeito_metodologico or "").lower()
                for item in supplementary
            )
        )

    def test_non_calculable_supplementary_diagnostic_remains_a_limitation(self) -> None:
        finding = next(
            item
            for item in self.contract.achados
            if item.achado_id == "ACH-SUP-FLEURIET"
        )

        self.assertEqual(finding.categoria, FindingCategory.LIMITATION)
        self.assertIn("não altera", (finding.efeito_metodologico or "").lower())

    def test_non_monotonic_scenario_creates_explicit_finding(self) -> None:
        output = copy.deepcopy(self.output)
        scenario_index = output["df_cenarios_deterministicos"].index[-1]
        output["df_cenarios_deterministicos"].loc[
            scenario_index, "monotonicidade_global"
        ] = False
        output["df_cenarios_deterministicos"].loc[
            scenario_index, "status_monotonicidade"
        ] = "NAO_MONOTONICO"
        contract = build_parecer_data(output, self.meta, self.policy)
        finding = next(
            item
            for item in contract.achados
            if item.achado_id == "ACH-CEN-MONOTONICIDADE"
        )

        self.assertEqual(finding.categoria, FindingCategory.DIVERGENCE)
        self.assertFalse(finding.bloqueia_decisao)

    def test_blocking_finding_requires_block_category_and_action(self) -> None:
        with self.assertRaises(ValidationError):
            Finding(
                achado_id="ACH-INVALIDO",
                categoria=FindingCategory.ALERT,
                natureza=FindingNature.OBSERVED,
                titulo="Achado inválido",
                evidencias=[FindingEvidence(origem="teste", campo="campo", valor=1)],
                impacto_credito="Impacto informado.",
                bloqueia_decisao=True,
            )


if __name__ == "__main__":
    unittest.main()
