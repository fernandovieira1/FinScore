from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from app_front.finscore_v2 import executar_finscore
from app_front.views.graficos_pudim import (
    construir_figura_cenarios,
    construir_figura_monte_carlo,
    construir_figura_notas,
    construir_figura_nucleos,
    construir_figura_pesos_pca,
    construir_figura_temporal,
    construir_figuras_contabeis,
)


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class GraficosV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.output = executar_finscore(data, executar_simulacoes=False)

    def test_account_figures_use_pudim_accounts_and_real_years(self) -> None:
        figures = construir_figuras_contabeis(self.output)

        self.assertEqual(set(figures), {"estrutura", "liquidez", "resultado", "divida"})
        self.assertEqual(len(figures["estrutura"].data), 3)
        self.assertEqual(list(figures["estrutura"].data[0].x), ["2023", "2024", "2025"])
        self.assertEqual(figures["estrutura"].data[0].name, "Ativo Total")

    def test_indicator_figures_use_observed_notes_and_temporal_scores(self) -> None:
        notes = construir_figura_notas(self.output)
        temporal = construir_figura_temporal(self.output)

        self.assertEqual(len(notes.data), 1)
        self.assertEqual(list(notes.data[0].x), ["2023", "2024", "2025"])
        self.assertIn("Margem Bruta", list(notes.data[0].y))
        self.assertEqual(len(temporal.data), 4)
        self.assertEqual(temporal.data[-1].name, "Nota temporal")

    def test_model_figures_separate_nuclei_and_pca_weights(self) -> None:
        nuclei = construir_figura_nucleos(self.output)
        weights = construir_figura_pesos_pca(self.output)

        self.assertEqual([trace.name for trace in nuclei.data], ["Estrutural", "Adaptativo"])
        self.assertEqual([trace.name for trace in weights.data], ["Núcleo EO", "Núcleo FP"])
        self.assertEqual(len(weights.data[0].x), 6)
        self.assertEqual(len(weights.data[1].x), 8)

    def test_deterministic_scenarios_remain_without_monte_carlo(self) -> None:
        scenarios = construir_figura_cenarios(self.output)
        monte_carlo = construir_figura_monte_carlo(self.output)

        self.assertEqual(len(scenarios.data), 3)
        self.assertEqual(list(scenarios.data[0].x), ["BASE", "ADVERSO", "SEVERO"])
        self.assertEqual(len(monte_carlo.data), 0)

    def test_monte_carlo_figure_accepts_both_simulation_models(self) -> None:
        synthetic = dict(self.output)
        synthetic["df_simulacoes_independentes"] = pd.DataFrame(
            {"finscore_prudencial": [400.0, 410.0]}
        )
        synthetic["df_simulacoes_correlacionadas"] = pd.DataFrame(
            {"finscore_prudencial": [390.0, 420.0]}
        )

        figure = construir_figura_monte_carlo(synthetic)

        self.assertEqual([trace.name for trace in figure.data], ["Independente", "Correlacionado"])

    def test_figure_builders_do_not_mutate_contract_tables(self) -> None:
        source = self.output["df_notas_observadas"]
        original = source.copy(deep=True)

        construir_figura_notas(self.output)
        construir_figura_temporal(self.output)
        construir_figura_pesos_pca(self.output)

        pd.testing.assert_frame_equal(source, original)


if __name__ == "__main__":
    unittest.main()
