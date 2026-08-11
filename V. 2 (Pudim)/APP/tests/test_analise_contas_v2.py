from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from app_front.finscore_v2 import executar_finscore
from app_front.views.analise_contas import (
    formatar_moeda,
    formatar_nome_conta,
    montar_tabela_contas,
    resumir_contas,
)


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class AnaliseContasV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.output = executar_finscore(data, executar_simulacoes=False)

    def test_primary_and_derived_labels(self) -> None:
        self.assertEqual(
            formatar_nome_conta("p_Emprestimos_Financiamentos_CP"),
            "Empréstimos e Financiamentos — Curto Prazo",
        )
        self.assertEqual(formatar_nome_conta("d_EBIT"), "EBIT")
        self.assertEqual(
            formatar_nome_conta("d_Divida_Financeira_Liquida"),
            "Dívida Financeira Líquida",
        )

    def test_account_table_has_accounts_in_rows_and_years_in_columns(self) -> None:
        source = self.output["df_contas_reportadas"]
        original = source.copy(deep=True)
        table = montar_tabela_contas(
            source,
            ["p_Caixa_Equivalentes", "p_Obrigacoes_Trabalhistas_CP"],
        )

        self.assertEqual(
            list(table.columns),
            ["Código", "Conta", "2023", "2024", "2025"],
        )
        self.assertEqual(table.iloc[0]["Conta"], "Caixa e Equivalentes")
        self.assertEqual(table.iloc[0]["2023"], "R$ 866.692,17")
        self.assertEqual(table.iloc[1]["2023"], "Ausente")
        pd.testing.assert_frame_equal(source, original)

    def test_summary_uses_contract_tables(self) -> None:
        summary = resumir_contas(self.output)

        self.assertEqual(summary["contas_primarias"], 21)
        self.assertEqual(summary["celulas_ausentes"], 3)
        self.assertEqual(summary["valores_alterados"], 0)
        self.assertEqual(summary["contas_derivadas"], 20)
        self.assertEqual(summary["ocorrencias_criticas"], 0)

    def test_currency_formatter_distinguishes_absence_from_zero(self) -> None:
        self.assertEqual(formatar_moeda(float("nan")), "Ausente")
        self.assertEqual(formatar_moeda(0), "R$ 0,00")
        self.assertEqual(formatar_moeda(-1234.5), "R$ -1.234,50")

    def test_blocked_result_has_no_derived_accounts(self) -> None:
        invalid = self.output["df_contas_reportadas"].astype(object)
        invalid.loc[0, "p_Ativo_Total"] = "valor inválido"
        blocked = executar_finscore(invalid, executar_simulacoes=False)

        summary = resumir_contas(blocked)

        self.assertEqual(blocked["status_qualidade"]["classificacao_uso"], "BLOQUEADO")
        self.assertEqual(summary["contas_derivadas"], 0)
        self.assertGreater(summary["ocorrencias_criticas"], 0)


if __name__ == "__main__":
    unittest.main()
