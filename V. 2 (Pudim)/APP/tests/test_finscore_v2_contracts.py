from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from app_front.finscore_v2 import (
    CONTRACT_VERSION,
    ContractError,
    executar_finscore,
    validar_contrato,
)


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class FinScoreV2ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference_data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")

    def test_calculated_result_satisfies_contract(self) -> None:
        result = executar_finscore(self.reference_data, executar_simulacoes=False)

        self.assertIs(validar_contrato(result), result)
        self.assertEqual(result["contrato_versao"], CONTRACT_VERSION)
        self.assertTrue(result["status_qualidade"]["apto_calculo"])
        self.assertIn("finscore_prudencial", result["finscore_observado"])

    def test_blocked_result_satisfies_contract_without_fake_score(self) -> None:
        invalid = self.reference_data.astype(object)
        invalid.loc[0, "p_Ativo_Total"] = "valor inválido"

        result = executar_finscore(invalid, executar_simulacoes=False)

        self.assertIs(validar_contrato(result), result)
        self.assertFalse(result["status_qualidade"]["apto_calculo"])
        self.assertEqual(result["status_qualidade"]["classificacao_uso"], "BLOQUEADO")
        self.assertEqual(result["finscore_observado"], {})
        self.assertTrue(result["df_indices_observados"].empty)

    def test_missing_required_key_is_rejected(self) -> None:
        result = executar_finscore(self.reference_data, executar_simulacoes=False)
        broken = dict(result)
        broken.pop("df_indices_observados")

        with self.assertRaisesRegex(ContractError, "chaves ausentes"):
            validar_contrato(broken)

    def test_wrong_table_type_is_rejected(self) -> None:
        result = executar_finscore(self.reference_data, executar_simulacoes=False)
        broken = dict(result)
        broken["df_qualidade"] = []

        with self.assertRaisesRegex(ContractError, "df_qualidade deve ser"):
            validar_contrato(broken)

    def test_decision_requires_calculation(self) -> None:
        result = executar_finscore(self.reference_data, executar_simulacoes=False)
        broken = dict(result)
        broken["status_qualidade"] = {
            **result["status_qualidade"],
            "apto_calculo": False,
            "apto_decisao": True,
            "classificacao_uso": "BLOQUEADO",
        }
        broken["finscore_observado"] = {}

        with self.assertRaisesRegex(ContractError, "apto_decisao"):
            validar_contrato(broken)


if __name__ == "__main__":
    unittest.main()
