from __future__ import annotations

import unittest
from io import BytesIO
from pathlib import Path

import pandas as pd

from app_front.finscore_v2.core import PRIMARY
from app_front.services.io_validation import (
    EXPECTED_COLUMNS,
    gerar_modelo_planilha,
    ler_planilha,
    obter_colunas_extras,
    obter_relatorio_importacao,
    validar_cliente,
    validar_dataframe_importado,
)


APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR.parent / "MODELO" / "dados_teste"


def workbook_bytes(df: pd.DataFrame, sheet_name: str = "lancamentos") -> BytesIO:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    buffer.seek(0)
    return buffer


class IOValidationV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference_path = DATA_DIR / "1Callamarys.xlsx"
        cls.reference_data = pd.read_excel(cls.reference_path, sheet_name="lancamentos")

    def test_reference_workbook_is_accepted_losslessly(self) -> None:
        data, sheet, error = ler_planilha(self.reference_path)

        self.assertIsNone(error)
        self.assertEqual(sheet, "lancamentos")
        self.assertEqual(list(data.columns), list(EXPECTED_COLUMNS))
        self.assertTrue(data["p_Obrigacoes_Trabalhistas_CP"].isna().all())
        report = obter_relatorio_importacao(data)
        self.assertTrue((report["tipo"] == "ausencia").any())

    def test_invalid_text_is_reported_and_preserved(self) -> None:
        raw = self.reference_data.astype(object)
        raw.loc[0, "p_Ativo_Total"] = "não é número"

        data, report = validar_dataframe_importado(raw)

        self.assertEqual(data.loc[0, "p_Ativo_Total"], "não é número")
        critical = report[report["severidade"].eq("CRITICA")]
        self.assertEqual(critical.iloc[0]["conta"], "p_Ativo_Total")
        self.assertTrue(bool(critical.iloc[0]["bloqueia_calculo"]))

    def test_brigadeiro_workbook_has_specific_error(self) -> None:
        data, sheet, error = ler_planilha(DATA_DIR / "DADOS_TESTE_FS.xlsx")

        self.assertIsNone(data)
        self.assertIsNone(sheet)
        self.assertIn("versão 1 (Brigadeiro)", error)

    def test_lancamentos_sheet_is_required(self) -> None:
        data, sheet, error = ler_planilha(
            workbook_bytes(self.reference_data, sheet_name="dados")
        )

        self.assertIsNone(data)
        self.assertIsNone(sheet)
        self.assertIn("deve conter a aba 'lancamentos'", error)

    def test_extra_columns_are_ignored_and_reported(self) -> None:
        raw = self.reference_data.copy()
        raw["observacao_livre"] = ["a", "b", "c"]

        data, _ = validar_dataframe_importado(raw)

        self.assertNotIn("observacao_livre", data.columns)
        self.assertEqual(obter_colunas_extras(data), ["observacao_livre"])

    def test_column_names_are_case_sensitive_with_actionable_error(self) -> None:
        raw = self.reference_data.rename(columns={PRIMARY[0]: PRIMARY[0].lower()})

        with self.assertRaisesRegex(ValueError, "maiúsculas/minúsculas"):
            validar_dataframe_importado(raw)

    def test_template_has_expected_sheets_columns_and_years(self) -> None:
        content = gerar_modelo_planilha((2024, 2025, 2026))
        workbook = pd.ExcelFile(BytesIO(content), engine="openpyxl")
        data = pd.read_excel(workbook, sheet_name="lancamentos")

        self.assertEqual(
            workbook.sheet_names,
            ["lancamentos", "dicionario", "notas_preenchimento"],
        )
        self.assertEqual(list(data.columns), list(EXPECTED_COLUMNS))
        self.assertEqual(data["ano"].tolist(), [2024, 2025, 2026])

    def test_client_rejects_impossible_date(self) -> None:
        meta = {
            "empresa": "Empresa",
            "cnpj": "00.000.000/0000-00",
            "ano_inicial": 2023,
            "ano_final": 2025,
            "serasa": 700,
            "serasa_data": "31/02/2026",
        }

        errors = validar_cliente(meta)

        self.assertIn("serasa_data", errors)


if __name__ == "__main__":
    unittest.main()
