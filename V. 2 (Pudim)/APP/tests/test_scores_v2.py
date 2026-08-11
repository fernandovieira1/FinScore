from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from app_front.finscore_v2 import executar_finscore
from app_front.services.finscore_service import run_finscore
from app_front.views.scores import formatar_percentual, formatar_pontos, resumir_scores


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class ScoresV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.meta = {
            "empresa": "Callamarys",
            "cnpj": "00.000.000/0000-00",
            "ano_inicial": 2023,
            "ano_final": 2025,
            "serasa": 700,
            "serasa_data": "23/07/2026",
            "serasa_restricao_grave": False,
        }
        cls.output = run_finscore(
            cls.data,
            dict(cls.meta),
            executar_simulacoes=False,
        )

    def test_summary_uses_native_pudim_scores(self) -> None:
        summary = resumir_scores(self.output)
        observed = self.output["finscore_observado"]

        self.assertFalse(summary["bloqueado"])
        self.assertEqual(summary["finscore_prudencial"], observed["finscore_prudencial"])
        self.assertEqual(summary["estrutural"], observed["finscore_estrutural_pos_gargalo"])
        self.assertEqual(summary["adaptativo"], observed["finscore_adaptativo_pos_gargalo"])
        self.assertEqual(summary["eo_estrutural"], observed["nucleo_EO_estrutural"])
        self.assertEqual(summary["fp_adaptativo"], observed["nucleo_FP_adaptativo"])

    def test_quality_and_prudential_controls_are_preserved(self) -> None:
        summary = resumir_scores(self.output)

        self.assertTrue(summary["score_provisorio"])
        self.assertFalse(summary["apto_decisao"])
        self.assertEqual(summary["classificacao_uso"], "CALCULADO_COM_ALERTAS")
        self.assertEqual(summary["alertas_bloqueadores"], 3)
        self.assertEqual(len(summary["caps"]), 3)
        self.assertAlmostEqual(summary["confiabilidade"], 0.9180952380952381)

    def test_serasa_remains_separate_external_evidence(self) -> None:
        summary = resumir_scores(self.output)

        self.assertEqual(summary["serasa"]["serasa_score"], 700)
        self.assertEqual(summary["serasa"]["status"], "ANALISAR_CONJUNTAMENTE")
        self.assertTrue(pd.isna(summary["serasa"]["score_integrado"]))
        self.assertAlmostEqual(
            summary["serasa"]["divergencia_pontos"],
            700 - summary["finscore_prudencial"],
        )

    def test_blocked_result_does_not_expose_artificial_scores(self) -> None:
        invalid = self.data.astype(object)
        invalid.loc[0, "p_Ativo_Total"] = "valor inválido"
        blocked = executar_finscore(invalid, executar_simulacoes=False)

        summary = resumir_scores(blocked)

        self.assertTrue(summary["bloqueado"])
        self.assertIsNone(summary["finscore_prudencial"])
        self.assertIsNone(summary["estrutural"])
        self.assertGreater(summary["ocorrencias_criticas"], 0)

    def test_formatters_distinguish_missing_zero_and_percentage(self) -> None:
        self.assertEqual(formatar_pontos(None), "—")
        self.assertEqual(formatar_pontos(float("nan")), "—")
        self.assertEqual(formatar_pontos(0), "0.0")
        self.assertEqual(formatar_percentual(0.918), "91.8%")

    def test_summary_does_not_mutate_contract_tables(self) -> None:
        caps = self.output["df_caps_prudenciais"]
        original = caps.copy(deep=True)

        summary = resumir_scores(self.output)
        summary["caps"].iloc[0, 0] = "alterado"

        pd.testing.assert_frame_equal(caps, original)


if __name__ == "__main__":
    unittest.main()
