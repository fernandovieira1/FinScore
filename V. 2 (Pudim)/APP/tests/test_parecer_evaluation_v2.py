from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd

from app_front.components.parecer_data_schema import FindingCategory
from app_front.components.parecer_schema import ParecerNarrativo
from app_front.pdf.export_pdf import contar_paginas_pdf, gerar_pdf_parecer
from app_front.services.credit_policy import decide_pudim
from app_front.services.finscore_service import run_finscore
from app_front.services.parecer_data_builder import build_parecer_data
from app_front.services.parecer_document import _bar_chart, render_structured_parecer
from app_front.services.parecer_evaluation import (
    BODY_HEADINGS,
    evaluate_parecer_document,
)
from app_front.services.parecer_generator import build_narrative_context
from app_front.services.parecer_generator import generate_parecer_document
from APP.tests.test_parecer_validation_v2 import SECTION_TEXTS


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


class ParecerDocumentEvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        data = pd.read_excel(REFERENCE_XLSX, sheet_name="lancamentos")
        cls.meta = {
            "empresa": "Callamarys",
            "cnpj": "00.000.000/0000-00",
            "ano_inicial": 2023,
            "ano_final": 2025,
            "serasa": 700,
            "serasa_data": "23/07/2026",
        }
        cls.output = run_finscore(data, dict(cls.meta), executar_simulacoes=False)
        cls.policy = decide_pudim(cls.output, cls.meta)
        cls.contract = build_parecer_data(cls.output, cls.meta, cls.policy)
        cls.context = build_narrative_context(cls.contract)

    def _narrative(self) -> ParecerNarrativo:
        routes = self.context["roteiro_achados"]
        payload = {
            name: {"texto": text, "achado_ids": routes[name][:1]}
            for name, text in SECTION_TEXTS.items()
        }
        blockers = [
            item.achado_id
            for item in self.contract.achados
            if item.categoria is FindingCategory.BLOCK
        ]
        payload["escopo_e_qualidade"]["achado_ids"] = list(
            dict.fromkeys([*payload["escopo_e_qualidade"]["achado_ids"], *blockers])
        )
        payload.update(
            pontos_fortes=[],
            riscos_prioritarios=[],
            validacoes_pendentes=[],
            recomendacoes_monitoramento=[],
        )
        return ParecerNarrativo.model_validate(payload)

    def test_complete_document_passes_deterministic_evaluation(self) -> None:
        narrative = self._narrative()
        document = render_structured_parecer(narrative, self.contract)
        report = evaluate_parecer_document(
            narrative,
            self.contract,
            document,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertTrue(report.valido, report.problemas)
        self.assertGreater(report.achados_referenciados, 0)
        self.assertTrue(all(document.count(item) == 1 for item in BODY_HEADINGS))

    def test_end_to_end_pipeline_accepts_a_grounded_structured_response(self) -> None:
        narrative = self._narrative()

        document, generated, context = generate_parecer_document(
            self.output,
            self.meta,
            self.policy,
            parecer_data=self.contract,
            invoke=lambda *_args, **_kwargs: narrative.model_dump_json(),
        )

        self.assertEqual(generated, narrative)
        self.assertTrue(context["validacao_narrativa"]["valido"])
        self.assertTrue(context["avaliacao_documento"]["valido"])
        self.assertIn("## 10. Conclusão da análise", document)

    def test_methodology_tampering_is_rejected(self) -> None:
        narrative = self._narrative()
        document = render_structured_parecer(narrative, self.contract).replace(
            "O FinScore sintetiza", "O índice sintetiza", 1
        )
        report = evaluate_parecer_document(
            narrative, self.contract, document, raise_on_error=False
        )

        self.assertIn("METODOLOGIA_DIVERGENTE", {item.codigo for item in report.problemas})

    def test_generation_technology_term_is_rejected_from_document(self) -> None:
        narrative = self._narrative()
        document = render_structured_parecer(narrative, self.contract) + "\nOpenAI"
        report = evaluate_parecer_document(
            narrative, self.contract, document, raise_on_error=False
        )

        self.assertIn("TERMO_TECNICO_RESTRITO", {item.codigo for item in report.problemas})

    def test_page_range_is_enforced(self) -> None:
        narrative = self._narrative()
        document = render_structured_parecer(narrative, self.contract)
        report = evaluate_parecer_document(
            narrative, self.contract, document, pages=6, raise_on_error=False
        )

        self.assertIn("PAGINACAO_INVALIDA", {item.codigo for item in report.problemas})

    def test_chart_is_omitted_when_comparison_has_no_material_variation(self) -> None:
        self.assertEqual(
            _bar_chart("Comparação", [("A", 500.0), ("B", 500.0)], "Fonte"),
            "",
        )
        chart = _bar_chart("Comparação", [("A", 400.0), ("B", 500.0)], "Fonte")
        self.assertIn("<figcaption>", chart)
        self.assertIn("chart-source", chart)

    def test_reference_pdf_stays_within_seven_to_fourteen_pages(self) -> None:
        narrative = self._narrative()
        document = render_structured_parecer(narrative, self.contract)
        pdf = gerar_pdf_parecer(
            document,
            {
                "empresa": "Callamarys",
                "cnpj": "00.000.000/0000-00",
                "finscore_ajustado": self.contract.finscore.prudencial,
                "decisao": self.policy["decisao"],
                "ano_inicial": 2023,
                "ano_final": 2025,
            },
            engine="xhtml2pdf",
            min_pages=7,
            max_pages=14,
        )
        pages = contar_paginas_pdf(pdf)

        self.assertGreaterEqual(pages, 7)
        self.assertLessEqual(pages, 14)


if __name__ == "__main__":
    unittest.main()
