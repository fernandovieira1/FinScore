"""Regressões independentes do motor para evidências e precisão editorial."""
import unittest
from types import SimpleNamespace

from app_front.components.parecer_data_schema import (
    DeterministicScenario, Finding, FindingCategory, FindingEvidence, FindingNature,
    SerasaEvidence, SpringateEvidence, FleurietEvidence, SupplementaryEvidence,
)
from app_front.services.evidence_book import _scenario_findings, _supplementary_findings
from app_front.services.parecer_document import _supplementary_table, _series_commentary
from app_front.services.parecer_validation import _authorized_numbers, _matches_authorized


class TraceabilityRegressionTest(unittest.TestCase):
    def test_large_favorable_changes_do_not_hide_pressure_or_repeat_drivers(self):
        points = [SimpleNamespace(campo=field, exercicio=year, valor=value, unidade="BRL")
            for field, values in (("lucro", [1, 40, 1600]), ("receita", [100, 90, 80]))
            for year, value in zip((2023, 2024, 2025), values)]
        before, after = _series_commentary(points, ["lucro", "receita"],
            [2023, 2024, 2025], {"lucro": "Lucro", "receita": "Receita"},
            favorable_up={"lucro", "receita"}, favorable_down=set())
        self.assertEqual(after.count("elevação de Lucro"), 1)
        self.assertEqual(after.count("redução de Receita"), 1)
        self.assertIn("Receita", before)

    def supplementary(self, last_score=.71):
        return SimpleNamespace(evidencias_suplementares=SupplementaryEvidence(
            serasa=SerasaEvidence(status="Não informado"),
            springate=[SpringateEvidence(exercicio=year, score=score,
                classificacao="Não calculável" if score is None else "Distress")
                for year, score in ((2025, last_score), (2023, -.22), (2024, .42))],
            fleuriet=[FleurietEvidence(exercicio=year, capital_giro=100,
                necessidade_capital_giro=ncg, saldo_tesouraria=100-ncg,
                diagnostico="Dependência de curto prazo" if ncg > 100 else "NCG coberta")
                for year, ncg in ((2025, 90), (2023, 120), (2024, 110))],
        ))

    def test_diagnostic_table_and_evidence_preserve_recovery_history(self):
        contract = self.supplementary()
        table = _supplementary_table(contract)
        self.assertLess(table.index("Springate | 2023"), table.index("Springate | 2025"))
        self.assertIn("Fleuriet simplificado | 2023 | Dependência de curto prazo", table)
        self.assertIn("Fleuriet simplificado | 2025 | NCG coberta", table)
        findings = {f.achado_id: f for f in _supplementary_findings(contract)}
        for identifier in ("ACH-SUP-SPRINGATE", "ACH-SUP-FLEURIET"):
            self.assertEqual({e.exercicio for e in findings[identifier].evidencias}, {2023, 2024, 2025})

    def test_unavailable_springate_is_never_a_strength(self):
        findings = {f.achado_id: f for f in _supplementary_findings(self.supplementary(None))}
        self.assertEqual(findings["ACH-SUP-SPRINGATE"].categoria, FindingCategory.LIMITATION)
        self.assertIn("indisponível", findings["ACH-SUP-SPRINGATE"].impacto_credito)

    def scenarios(self, base, adverse, severe):
        contract = SimpleNamespace(cenarios=SimpleNamespace(
            deterministicos=[DeterministicScenario(nome=name, status="OK", finscore_prudencial=value)
                for name, value in zip(("BASE", "ADVERSO", "SEVERO"), (base, adverse, severe))],
            diagnosticos=[],
        ))
        return {item.achado_id: item for item in _scenario_findings(contract)}

    def test_both_stresses_have_independent_evidence(self):
        findings = self.scenarios(500, 495, 395)
        self.assertEqual(set(findings), {"ACH-CEN-ADVERSO", "ACH-CEN-SEVERO"})
        for name, score, delta in (("ADVERSO", 495, -5), ("SEVERO", 395, -105)):
            item = findings[f"ACH-CEN-{name}"]
            self.assertEqual(item.categoria, FindingCategory.ALERT)
            self.assertEqual([e.valor for e in item.evidencias], [500, score, delta])
            self.assertEqual(item.evidencias[1].origem, f"cenarios.deterministicos:{name}")
            self.assertEqual(item.natureza, FindingNature.HYPOTHESIS)

    def test_missing_stress_is_not_zero(self):
        findings = self.scenarios(500, None, 0)
        self.assertNotIn("ACH-CEN-ADVERSO", findings)
        self.assertEqual(findings["ACH-CEN-SEVERO"].evidencias[1].valor, 0)
        self.assertEqual(self.scenarios(None, 495, 395), {})

    def test_flat_and_deteriorating_stresses_remain_distinct(self):
        findings = self.scenarios(500, 500, 395)
        self.assertEqual(findings["ACH-CEN-ADVERSO"].evidencias[-1].valor, 0)
        self.assertEqual(findings["ACH-CEN-SEVERO"].categoria, FindingCategory.ALERT)

    def test_failed_monotonicity_never_supports_resilience(self):
        for flag, status in ((False, None), (None, "FALHOU"),
                (None, "NÃO ATENDIDA"), (None, "NAO_ATENDIDA"),
                (True, "Não atendida")):
            with self.subTest(flag=flag, status=status):
                scenarios = [DeterministicScenario(nome=name, status="OK",
                    finscore_prudencial=value) for name, value in
                    (("BASE", 500), ("ADVERSO", 550), ("SEVERO", 450))]
                # Um único registro de reprovação já limita a comparação global.
                scenarios[1] = scenarios[1].model_copy(update={
                    "monotonicidade_global": flag, "status_monotonicidade": status})
                contract = SimpleNamespace(cenarios=SimpleNamespace(
                    deterministicos=scenarios, diagnosticos=[]))
                findings = {item.achado_id: item for item in _scenario_findings(contract)}
                self.assertEqual(findings["ACH-CEN-MONOTONICIDADE"].categoria,
                    FindingCategory.DIVERGENCE)
                for name, delta in (("ADVERSO", 50), ("SEVERO", -50)):
                    finding = findings[f"ACH-CEN-{name}"]
                    self.assertEqual(finding.categoria, FindingCategory.LIMITATION)
                    self.assertEqual(finding.evidencias[-1].valor, delta)
                    self.assertIn("não sustenta inferência de resiliência", finding.impacto_credito)

    def test_valid_flat_stress_keeps_strength(self):
        scenarios = [DeterministicScenario(nome=name, status="OK",
            finscore_prudencial=value, monotonicidade_global=True,
            status_monotonicidade="PASSOU") for name, value in
            (("BASE", 500), ("ADVERSO", 500), ("SEVERO", 450))]
        contract = SimpleNamespace(cenarios=SimpleNamespace(
            deterministicos=scenarios, diagnosticos=[]))
        findings = {item.achado_id: item for item in _scenario_findings(contract)}
        self.assertNotIn("ACH-CEN-MONOTONICIDADE", findings)
        self.assertEqual(findings["ACH-CEN-ADVERSO"].categoria, FindingCategory.STRENGTH)
        self.assertEqual(findings["ACH-CEN-SEVERO"].categoria, FindingCategory.ALERT)

    def test_percentage_rounding_does_not_erase_sign_or_small_values(self):
        for displayed, evidence, expected in ((0.3, 0, False), (-0.02, 0, False),
                (0.3, .003, True), (7.57, .07571, True), (7.57, .0758, False)):
            with self.subTest(displayed=displayed, evidence=evidence):
                self.assertEqual(_matches_authorized(displayed, True, [evidence]), expected)

    def test_large_amounts_do_not_have_large_rounding_allowance(self):
        self.assertFalse(_matches_authorized(1001000, False, [1000000]))
        self.assertTrue(_matches_authorized(294105.39, False, [294105.394]))

    def test_percentage_cannot_borrow_score_amount_or_year(self):
        finding = Finding(achado_id="ACH-TEST", categoria=FindingCategory.RESULT,
            natureza=FindingNature.HYPOTHESIS, titulo="Evidências de unidades distintas",
            evidencias=[FindingEvidence(origem="test", campo=unit, valor=value,
                unidade=unit, exercicio=2025) for unit, value in
                (("pontos", 93), ("BRL", .93), ("proporcao", .5))])
        allowed = _authorized_numbers([finding], percent=True)
        self.assertEqual(allowed, [.5])
        self.assertFalse(_matches_authorized(93, True, allowed))
        self.assertTrue(_matches_authorized(50, True, allowed))


if __name__ == "__main__":
    unittest.main()
