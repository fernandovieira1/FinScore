from types import SimpleNamespace
import unittest

from app_front.components.parecer_data_schema import SimulationSummary, SimulationDiagnostic
from app_front.services.parecer_document import _simulation_table


class SimulationReportGateTest(unittest.TestCase):
    def contract(self, valid, include_diagnostic=True):
        diagnostic = SimulationDiagnostic(abordagem="independente", valida_para_interpretacao=valid,
            taxa_rejeicao=.9, status_rejeicao="REPROVADA" if not valid else "APROVADA")
        summary = SimulationSummary(abordagem="independente", metodo="estrutural", numero_trajetorias=1000,
            media=812.34, mediana=810, p05=750, p95=860)
        return SimpleNamespace(cenarios=SimpleNamespace(resumos_simulacao=[summary],
            diagnosticos=[diagnostic] if include_diagnostic else []))

    def test_invalid_and_unknown_diagnostics_hide_numbers(self):
        for valid, exists in ((False, True), (None, True), (True, False)):
            with self.subTest(valid=valid, exists=exists):
                text = _simulation_table(self.contract(valid, exists))
                self.assertNotIn("812,34", text)
                self.assertIn("indisponível para interpretação", text)

    def test_valid_diagnostic_retains_summary(self):
        self.assertIn("812,34", _simulation_table(self.contract(True)))

    def test_other_approach_cannot_authorize_summary(self):
        contract = self.contract(True)
        contract.cenarios.diagnosticos[0].abordagem = "correlacionada"
        self.assertNotIn("812,34", _simulation_table(contract))


if __name__ == "__main__":
    unittest.main()
