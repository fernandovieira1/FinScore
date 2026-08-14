from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from app_front.finscore_v2 import executar_finscore
from app_front.views.tabelas import TABLE_KEYS, catalogar_tabelas_pudim


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class TabelasV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.output = executar_finscore(data, executar_simulacoes=False)

    def test_catalog_covers_the_pudim_analytical_tables(self) -> None:
        tables = catalogar_tabelas_pudim(self.output)

        self.assertEqual(set(tables), set(TABLE_KEYS))
        self.assertTrue(all(isinstance(table, pd.DataFrame) for table in tables.values()))
        self.assertEqual(len(tables["diagnostico_pca"]), 2)
        self.assertEqual(len(tables["pesos_pca"]), 14)

    def test_indices_and_notes_receive_real_years_and_labels(self) -> None:
        tables = catalogar_tabelas_pudim(self.output)

        self.assertEqual(tables["indices"]["Ano"].tolist(), [2023, 2024, 2025])
        self.assertEqual(tables["notas"]["Ano"].tolist(), [2023, 2024, 2025])
        self.assertIn("Margem Líquida", tables["indices"].columns)
        self.assertIn("Margem Líquida", tables["notas"].columns)
        self.assertIn("Ciclo de Conversão de Caixa (dias)", tables["indices"].columns)
        self.assertIn("NCG Operacional / Ativo", tables["indices"].columns)

    def test_catalog_does_not_mutate_engine_output(self) -> None:
        source = self.output["df_indices_observados"]
        original = source.copy(deep=True)

        tables = catalogar_tabelas_pudim(self.output)
        tables["indices"].iloc[0, 0] = 1900

        pd.testing.assert_frame_equal(source, original)
        self.assertNotIn("ano", source.columns)

    def test_disabled_monte_carlo_keeps_deterministic_scenarios(self) -> None:
        tables = catalogar_tabelas_pudim(self.output)

        self.assertEqual(self.output["modelo"]["numero_simulacoes"], 0)
        self.assertEqual(len(tables["cenarios_deterministicos"]), 3)
        self.assertTrue(tables["resumo_simulacoes"].empty)
        self.assertTrue(tables["comparacao_monte_carlo"].empty)

    def test_blocked_result_has_empty_analytical_tables(self) -> None:
        invalid = self.output["df_contas_reportadas"].astype(object)
        invalid.loc[0, "p_Ativo_Total"] = "valor inválido"
        blocked = executar_finscore(invalid, executar_simulacoes=False)
        tables = catalogar_tabelas_pudim(blocked)

        self.assertFalse(blocked["status_qualidade"]["apto_calculo"])
        self.assertTrue(tables["indices"].empty)
        self.assertTrue(tables["score_temporal"].empty)
        self.assertTrue(tables["diagnostico_pca"].empty)


if __name__ == "__main__":
    unittest.main()
