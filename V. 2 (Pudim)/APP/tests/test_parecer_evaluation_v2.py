from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd

from app_front.components.parecer_data_schema import FindingCategory
from app_front.components.parecer_schema import ParecerNarrativo
from app_front.pdf.export_pdf import contar_paginas_pdf, gerar_pdf_parecer, render_parecer_html
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
        self.assertIn("## 8. Considerações finais", document)

    def test_document_uses_the_consolidated_requested_structure(self) -> None:
        document = render_structured_parecer(self._narrative(), self.contract)

        self.assertIn("O presente parecer técnico-jurídico", document)
        self.assertIn("**Callamarys**", document)
        self.assertIn("referentes aos anos de 2023 a\n2025", document)
        self.assertNotIn("| Concedente |", document)
        self.assertIn("### 6.1 Garantias", document)
        self.assertNotIn("### 6.1 Caps prudenciais", document)
        self.assertNotIn("Comparação dos núcleos do FinScore", document)
        self.assertNotIn("### 2. Livro de evidências materiais", document)
        self.assertIn("## 7. Evidências suplementares", document)
        self.assertNotIn("### 7.1 Cenários determinísticos", document)
        self.assertNotIn("### 7.2 Simulação", document)
        self.assertNotIn("### 7.3 Evidências suplementares", document)
        self.assertNotIn("## 9. Riscos, diligências e monitoramento", document)
        self.assertNotIn("## 10. Conclusão da análise", document)
        self.assertEqual(document.count("## 8. Considerações finais"), 1)
        self.assertIn("Receita líquida/Ativo Total", document)
        self.assertNotIn("aprovar sem garantia", document.lower())

    def test_final_considerations_are_quantitatively_grounded(self) -> None:
        document = render_structured_parecer(self._narrative(), self.contract)
        final_section = document.split("## 8. Considerações finais", 1)[1].split(
            '<div class="page-break"></div>', 1
        )[0]

        self.assertIn("R$ 141.317.648,87", final_section)
        self.assertIn("margem líquida foi -1,86%", final_section)
        self.assertIn("o Serasa registrou 700,00 pontos", final_section)
        self.assertIn("No cenário severo", final_section)
        self.assertIn("PL / Ativo Total — 2023", final_section)
        self.assertIn("Para nova submissão", final_section)

    def test_pdf_header_has_requested_fields_and_no_classification_chips(self) -> None:
        document = render_structured_parecer(self._narrative(), self.contract)
        html = render_parecer_html(
            document,
            {
                "analise_id": "FS-2026-000003",
                "empresa": "Callamarys",
                "cnpj": "00.000.000/0000-00",
                "finscore_ajustado": 914.864,
                "classificacao_finscore": "500 ou mais",
                "serasa_score": 700,
                "classificacao_serasa": "ANALISAR CONJUNTAMENTE",
                "decisao": "aprovar",
                "ano_inicial": 2023,
                "ano_final": 2025,
            },
            engine="xhtml2pdf",
        )

        self.assertIn("Identificador da análise:</strong> FS-2026-000003", html)
        self.assertIn("Período efetivamente analisado:</strong> 2023 a 2025", html)
        self.assertIn("914,86", html)
        self.assertNotIn('alt="Assertif"', html)
        playwright_html = render_parecer_html(
            document,
            {
                "analise_id": "FS-2026-000003",
                "empresa": "Callamarys",
                "cnpj": "00.000.000/0000-00",
                "decisao": "aprovar",
                "ano_inicial": 2023,
                "ano_final": 2025,
            },
            engine="playwright",
        )
        self.assertIn('template id="pdf-header-template"', playwright_html)
        self.assertEqual(playwright_html.count('alt="Assertif"'), 1)
        caput = html.split("<!-- Corpo do Parecer -->", 1)[0]
        self.assertNotIn(">500 ou mais<", caput)
        self.assertNotIn(">ANALISAR CONJUNTAMENTE<", caput)
        self.assertEqual(html.count("Parecer de Crédito — FinScore"), 0)

    def test_methodology_tampering_is_rejected(self) -> None:
        narrative = self._narrative()
        document = render_structured_parecer(narrative, self.contract).replace(
            "A pontuação não é uma probabilidade", "A medida não é uma probabilidade", 1
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
        from io import BytesIO
        from pypdf import PdfReader

        rendered_pages = PdfReader(BytesIO(pdf)).pages
        self.assertTrue(all(len(list(page.images)) >= 1 for page in rendered_pages))


if __name__ == "__main__":
    unittest.main()
