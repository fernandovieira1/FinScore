"""A rejected replacement must never reuse the previous company's data."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import unittest

from app_front.components import session_state
from app_front.views import lancamentos


class RejectedUploadTest(unittest.TestCase):
    def test_rejected_replacement_clears_data_and_disables_calculation(self):
        meta = {"empresa": "TESTE", "anos_rotulos": [2022, 2023, 2024]}
        state = {"meta": meta, "df": object(), "out": {"score": 800},
                 "parecer_gerado": "old", "parecer_pdf": b"old-pdf",
                 "liberar_analise": True, "liberar_parecer": True,
                 "credit_governance": {"old": True}, "_flow_started": True}
        fake = MagicMock()
        fake.session_state = state
        fake.file_uploader.return_value = object()
        fake.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        fake.button.return_value = False
        with patch.object(lancamentos, "st", fake), \
             patch.object(session_state, "st", SimpleNamespace(session_state=state)), \
             patch.object(lancamentos, "ler_planilha", return_value=(None, None, "Formato legado")), \
             patch.object(lancamentos, "_render_cached_data_preview") as preview, \
             patch.object(lancamentos, "_run_finscore_with_timer") as calculate:
            lancamentos._sec_dados()
        self.assertIsNone(state["df"])
        self.assertIsNone(state["out"])
        self.assertIsNone(state["parecer_gerado"])
        self.assertNotIn("parecer_pdf", state)
        self.assertNotIn("credit_governance", state)
        self.assertFalse(state["liberar_analise"])
        self.assertFalse(state["liberar_parecer"])
        self.assertEqual(meta, {"empresa": "TESTE"})
        self.assertTrue(state["_flow_started"])
        fake.button.assert_called_once_with("Calcular FinScore", disabled=True)
        preview.assert_not_called()
        calculate.assert_not_called()

    def test_absent_new_upload_preserves_current_data(self):
        previous = object()
        state = {"df": previous}
        fake = MagicMock()
        fake.session_state = state
        fake.file_uploader.return_value = None
        fake.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        fake.button.return_value = False
        with patch.object(lancamentos, "st", fake), \
             patch.object(lancamentos, "invalidate_imported_data") as invalidate, \
             patch.object(lancamentos, "_render_cached_data_preview") as preview:
            lancamentos._sec_dados()
        invalidate.assert_not_called()
        preview.assert_called_once()
        self.assertIs(state["df"], previous)
        fake.button.assert_called_once_with("Calcular FinScore", disabled=False)


if __name__ == "__main__":
    unittest.main()
