"""Regressões da navegação quando a emissão de parecer não conclui."""
from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app_front.components import nav


class NavigationFlowTest(unittest.TestCase):
    def test_new_url_can_leave_an_unfinished_cycle_without_clearing_data(self):
        for origin in ("lanc", "analise", "parecer"):
            with self.subTest(origin=origin):
                output = {"finscore_observado": {"finscore_prudencial": 868.78}}
                meta = {"empresa": "Empresa de teste"}
                state = {
                    "page": origin,
                    "_flow_started": True,
                    "liberar_analise": True,
                    "liberar_parecer": True,
                    "parecer_gerado": None,
                    "out": output,
                    "meta": meta,
                }
                query = {"p": "novo"}
                with patch.object(nav, "st", SimpleNamespace(session_state=state, query_params=query)):
                    nav.sync_from_url()

                self.assertEqual(state["page"], "novo")
                self.assertEqual(query["p"], "novo")
                # Só o clique em Iniciar deverá descartar o ciclo anterior.
                self.assertIs(state["out"], output)
                self.assertIs(state["meta"], meta)
                self.assertTrue(state["_flow_started"])
                self.assertNotIn("_nav_block_message", state)

    def test_completed_report_remains_protected_from_new_url(self):
        state = {"page": "parecer", "_lock_parecer": True,
            "parecer_gerado": "Parecer concluído", "parecer_pdf": b"existing-pdf"}
        query = {"p": "novo"}
        with patch.object(nav, "st", SimpleNamespace(session_state=state, query_params=query)):
            nav.sync_from_url()

        self.assertEqual(state["page"], "parecer")
        self.assertEqual(query["p"], "parecer")
        self.assertEqual(state["parecer_gerado"], "Parecer concluído")
        self.assertEqual(state["parecer_pdf"], b"existing-pdf")
        self.assertIn("Iniciar novo ciclo", state["_nav_block_message"])

    def test_new_page_does_not_allow_skipping_to_report(self):
        state = {"page": "novo", "_flow_started": True, "liberar_parecer": True}
        query = {"p": "parecer"}
        with patch.object(nav, "st", SimpleNamespace(session_state=state, query_params=query)):
            nav.sync_from_url()

        self.assertEqual(state["page"], "novo")
        self.assertEqual(query["p"], "novo")


if __name__ == "__main__":
    unittest.main()
