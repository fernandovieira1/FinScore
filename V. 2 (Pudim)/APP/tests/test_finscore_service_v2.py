from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app_front.finscore_v2 import validar_contrato
from app_front.services.finscore_service import run_finscore


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class FinScoreServiceV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference_data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.meta = {
            "empresa": "Callamarys",
            "cnpj": "00.000.000/0000-00",
            "ano_inicial": 2023,
            "ano_final": 2025,
            "serasa": 700,
            "serasa_data": "23/07/2026",
            "serasa_restricao_grave": False,
        }

    def test_service_uses_pudim_contract(self) -> None:
        meta = dict(self.meta)
        result = run_finscore(
            self.reference_data,
            meta,
            executar_simulacoes=False,
        )

        self.assertIs(validar_contrato(result), result)
        self.assertEqual(result["modelo"]["nome"], "Pudim")
        self.assertEqual(result["modelo"]["versao"], "2.0.19")
        self.assertAlmostEqual(
            result["finscore_observado"]["finscore_prudencial"],
            412.2311278076248,
        )
        self.assertEqual(meta["anos_rotulos"], [2023, 2024, 2025])

    def test_transitional_aliases_are_explicit_and_safe(self) -> None:
        result = run_finscore(
            self.reference_data,
            dict(self.meta),
            executar_simulacoes=False,
        )

        self.assertEqual(
            result["finscore_ajustado"],
            result["finscore_observado"]["finscore_prudencial"],
        )
        self.assertEqual(result["classificacao_finscore"], "Calculado com alertas")
        self.assertEqual(result["serasa"], 700)
        self.assertEqual(result["classificacao_serasa"], "Bom")
        self.assertIs(result["df_raw"], result["df_contas_reportadas"])
        self.assertEqual(result["df_indices"]["ano"].tolist(), [2023, 2024, 2025])
        self.assertNotIn("finscore_bruto", result)
        self.assertNotIn("df_pca", result)
        self.assertTrue(result["compatibilidade_legado"]["temporaria"])

    def test_relative_years_are_mapped_before_engine(self) -> None:
        relative = self.reference_data.copy()
        relative["ano"] = [1, 2, 3]
        meta = dict(self.meta)

        result = run_finscore(relative, meta, executar_simulacoes=False)

        self.assertEqual(result["df_contas_reportadas"]["ano"].tolist(), [2023, 2024, 2025])
        self.assertEqual(meta["anos_rotulos"], [2023, 2024, 2025])

    def test_simulation_configuration_can_come_from_environment(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "FINSCORE_EXECUTAR_SIMULACOES": "0",
                "FINSCORE_SIMULACOES": "100",
                "FINSCORE_SEMENTE": "12345",
            },
        ):
            result = run_finscore(self.reference_data, dict(self.meta))

        self.assertEqual(result["modelo"]["numero_simulacoes"], 0)
        self.assertEqual(result["modelo"]["semente"], 12345)
        self.assertTrue(result["df_simulacoes"].empty)

    def test_invalid_simulation_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "pelo menos 100"):
            run_finscore(
                self.reference_data,
                dict(self.meta),
                executar_simulacoes=True,
                numero_simulacoes=99,
            )

    def test_empty_corrections_dataframe_does_not_use_ambiguous_truth_value(self) -> None:
        meta = dict(self.meta)
        meta["correcoes_manuais"] = pd.DataFrame()

        result = run_finscore(
            self.reference_data,
            meta,
            executar_simulacoes=False,
        )

        self.assertEqual(result["modelo"]["nome"], "Pudim")
        self.assertTrue(result["df_correcoes_auditoria"].empty)

    def test_corrections_dataframe_is_converted_to_records(self) -> None:
        meta = dict(self.meta)
        meta["correcoes_manuais"] = pd.DataFrame([
            {
                "ano": 2025,
                "conta": "r_Receitas_Financeiras",
                "valor": 305_878.0,
                "fonte": "Documento de teste",
                "justificativa": "Ajuste documentado para teste de integração.",
                "confirmado": True,
            }
        ])

        result = run_finscore(
            self.reference_data,
            meta,
            executar_simulacoes=False,
        )

        corrections = result["df_correcoes_auditoria"]
        manual = corrections[corrections["etapa"].eq("CORRECAO_MANUAL")]
        self.assertEqual(len(manual), 1)
        self.assertEqual(manual.iloc[0]["conta"], "r_Receitas_Financeiras")


if __name__ == "__main__":
    unittest.main()
