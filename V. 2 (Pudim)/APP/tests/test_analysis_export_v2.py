from __future__ import annotations

from io import BytesIO
import unittest
from pathlib import Path

import pandas as pd

from app_front.finscore_v2 import executar_finscore
from app_front.services.analysis_export import (
    SHEET_ORDER,
    gerar_planilha_analise,
    nome_arquivo_analise,
)


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"
REFERENCE_EXPORT = (
    APP_DIR.parent
    / "MODELO"
    / "algoritmos"
    / "Versao 12"
    / "resultados_finscore_2.0.13_20260813_0202.xlsx"
)


class AnalysisExportV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.output = executar_finscore(cls.data, executar_simulacoes=False)
        cls.simulated_output = executar_finscore(
            cls.data,
            executar_simulacoes=True,
            numero_simulacoes=100,
            semente=20260723,
        )
        cls.meta = {
            "empresa": "Callamarys Comércio",
            "cnpj": "00.000.000/0000-00",
            "ano_inicial": 2023,
            "ano_final": 2025,
        }

    def test_workbook_matches_reference_sheet_order(self) -> None:
        content = gerar_planilha_analise(self.simulated_output, self.meta)
        workbook = pd.ExcelFile(BytesIO(content), engine="openpyxl")

        self.assertEqual(workbook.sheet_names, SHEET_ORDER)
        self.assertEqual(len(workbook.sheet_names), 33)

    def test_exported_tables_match_engine_contract(self) -> None:
        content = gerar_planilha_analise(self.simulated_output, self.meta)
        workbook = pd.ExcelFile(BytesIO(content), engine="openpyxl")

        accounts = pd.read_excel(workbook, sheet_name="contas_reportadas")
        traceability = pd.read_excel(workbook, sheet_name="rastreabilidade_contas")
        scenarios = pd.read_excel(workbook, sheet_name="cenarios_deterministicos")

        self.assertEqual(accounts["ano"].tolist(), [2023, 2024, 2025])
        self.assertEqual(len(traceability), 63)
        self.assertEqual(scenarios["cenario"].tolist(), ["BASE", "ADVERSO", "SEVERO"])

    def test_summary_contains_model_score_status_and_hashes(self) -> None:
        content = gerar_planilha_analise(self.output, self.meta)
        summary = pd.read_excel(BytesIO(content), sheet_name="resumo_modelo")

        fields = set(summary["campo"])
        self.assertIn("FinScore prudencial final", fields)
        self.assertIn("Classificação de uso", fields)
        self.assertIn("Hash da base reportada", fields)
        version = summary.loc[summary["campo"].eq("Versão"), "valor"].iloc[0]
        self.assertEqual(version, "2.0.14")

    def test_export_does_not_mutate_contract_tables(self) -> None:
        source = self.output["df_contas_reportadas"]
        original = source.copy(deep=True)

        gerar_planilha_analise(self.output, self.meta)

        pd.testing.assert_frame_equal(source, original)

    def test_blocked_result_can_be_exported_for_audit(self) -> None:
        invalid = self.data.astype(object)
        invalid.loc[0, "p_Ativo_Total"] = "valor inválido"
        blocked = executar_finscore(invalid, executar_simulacoes=False)

        content = gerar_planilha_analise(blocked, self.meta)
        quality = pd.read_excel(BytesIO(content), sheet_name="qualidade_dados")
        summary = pd.read_excel(BytesIO(content), sheet_name="resumo_modelo")

        self.assertTrue(quality["bloqueia_calculo"].any())
        usage = summary.loc[summary["campo"].eq("Classificação de uso"), "valor"].iloc[0]
        self.assertEqual(usage, "BLOQUEADO")
        self.assertEqual(len(pd.ExcelFile(BytesIO(content)).sheet_names), 11)

    def test_filename_is_safe_and_identifies_pudim(self) -> None:
        filename = nome_arquivo_analise(self.output, self.meta)

        self.assertRegex(
            filename,
            r"^resultados_finscore_2\.0\.14_callamarys_comercio_\d{8}_\d{4}\.xlsx$",
        )

    def test_schema_matches_the_2_12_reference_workbook(self) -> None:
        content = gerar_planilha_analise(self.simulated_output, self.meta)
        reference = pd.ExcelFile(REFERENCE_EXPORT, engine="openpyxl")
        generated = pd.ExcelFile(BytesIO(content), engine="openpyxl")

        self.assertEqual(generated.sheet_names, reference.sheet_names)
        for sheet in generated.sheet_names:
            expected = pd.read_excel(reference, sheet_name=sheet, nrows=0)
            actual = pd.read_excel(generated, sheet_name=sheet, nrows=0)
            self.assertEqual(list(actual.columns), list(expected.columns), sheet)

    def test_export_canonicalizes_pca_sign_like_reference(self) -> None:
        content = gerar_planilha_analise(self.simulated_output, self.meta)
        reference = pd.read_excel(REFERENCE_EXPORT, sheet_name="cargas_pca")
        generated = pd.read_excel(BytesIO(content), sheet_name="cargas_pca")

        pd.testing.assert_frame_equal(
            generated,
            reference,
            check_dtype=False,
            check_exact=False,
            rtol=1e-10,
            atol=1e-10,
        )


if __name__ == "__main__":
    unittest.main()
