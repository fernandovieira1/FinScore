from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from app_front.finscore_v2 import executar_autotestes, executar_finscore
from app_front.finscore_v2 import core


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class FinScoreV2EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference_data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")

    def test_reference_case_matches_frozen_script(self) -> None:
        result = executar_finscore(
            self.reference_data,
            serasa_score=700,
            serasa_data="2026-07-23",
            executar_simulacoes=False,
        )
        observed = result["finscore_observado"]

        self.assertAlmostEqual(observed["finscore_prudencial"], 394.4314699700764)
        self.assertAlmostEqual(
            result["confiabilidade"]["indice_confiabilidade"],
            0.9180952380952381,
        )
        self.assertEqual(
            result["status_qualidade"]["classificacao_uso"],
            "CALCULADO_COM_ALERTAS",
        )
        self.assertEqual(observed["cap_prudencial_aplicavel"], 500.0)
        self.assertEqual(observed["utilizavel_decisao"], "NAO")

    def test_blank_accounting_value_remains_nan(self) -> None:
        result = executar_finscore(
            self.reference_data,
            executar_simulacoes=False,
        )
        values = result["df_contas_reportadas"]["p_Obrigacoes_Trabalhistas_CP"]
        self.assertTrue(values.map(np.isnan).all())
        report = result["df_relatorio_importacao"]
        self.assertTrue(
            (
                (report["tipo"] == "ausencia")
                & (report["conta"] == "p_Obrigacoes_Trabalhistas_CP")
            ).any()
        )

    def test_missing_column_is_rejected(self) -> None:
        invalid = self.reference_data.drop(columns=[core.PRIMARY[0]])
        with self.assertRaisesRegex(ValueError, "Colunas ausentes"):
            executar_finscore(invalid, executar_simulacoes=False)

    def test_requires_exactly_three_exercises(self) -> None:
        with self.assertRaisesRegex(ValueError, "3 exercícios"):
            executar_finscore(
                self.reference_data.iloc[:2],
                executar_simulacoes=False,
            )

    def test_methodological_self_tests_pass(self) -> None:
        tests = executar_autotestes()
        self.assertEqual(len(tests), 32)
        self.assertTrue(tests["status"].eq("PASSOU").all())

    def test_seeded_monte_carlo_matches_frozen_script(self) -> None:
        result = executar_finscore(
            self.reference_data,
            serasa_score=700,
            serasa_data="2026-07-23",
            executar_simulacoes=True,
            numero_simulacoes=100,
            semente=20260723,
        )
        comparison = result["df_comparacao_monte_carlo"].set_index("metodo")

        self.assertAlmostEqual(
            comparison.loc["prudencial", "media_independente"],
            391.8849,
            places=4,
        )
        self.assertAlmostEqual(
            comparison.loc["prudencial", "media_correlacionada"],
            394.5015,
            places=4,
        )
        self.assertAlmostEqual(
            comparison.loc["estrutural", "mediana_independente"],
            424.3239,
            places=4,
        )
        self.assertEqual(len(result["df_simulacoes_independentes"]), 100)
        self.assertEqual(len(result["df_simulacoes_correlacionadas"]), 100)


if __name__ == "__main__":
    unittest.main()
