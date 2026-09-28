"""Faixas quantitativas, elegibilidade prudencial e apresentação, sem recalibrar o motor."""
from __future__ import annotations

import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd
from matplotlib.figure import Figure
from pydantic import ValidationError

from app_front.components.parecer_data_schema import FinScoreRecommendation
from app_front.pdf.export_pdf import _render_finscore_band_chart, render_parecer_html
from app_front.services.credit_policy import PolicyConfig, _score_band, decide_pudim, finscore_bands
from app_front.services.parecer_data_builder import build_finscore_recommendation
from app_front.services.parecer_document import load_methodology
from app_front.services.parecer_validation import _validate_semantics
from app_front.views.sobre import METHODOLOGY_PATH, render_methodology_section


BOUNDARIES = (
    (0, "Risco elevado", "#c64747", "nao_aprovar"),
    (249.99, "Risco elevado", "#c64747", "nao_aprovar"),
    (250, "Risco relevante", "#c58a16", "aprovar"),
    (499.99, "Risco relevante", "#c58a16", "aprovar"),
    (500, "Risco aceitável", "#3276b5", "aprovar"),
    (749.99, "Risco aceitável", "#3276b5", "aprovar"),
    (750, "Risco reduzido", "#26836b", "aprovar"),
    (1000, "Risco reduzido", "#26836b", "aprovar"),
)


def eligible_output(score=824, quality=0.95, caps=(), severe=None):
    return {
        "status_qualidade": {"apto_calculo": True, "apto_decisao": True,
                            "classificacao_uso": "CALCULADO", "indice_confiabilidade": quality},
        "finscore_observado": {"finscore_prudencial": score, "utilizavel_decisao": "SIM"},
        "df_caps_prudenciais": pd.DataFrame(
            [{"cap": cap, "justificativa": "Cap acionado"} for cap in caps],
            columns=["cap", "justificativa"]),
        "df_cenarios_deterministicos": pd.DataFrame(
            [{"cenario": "SEVERO", "finscore_prudencial": severe}]),
    }


class CreditPolicyBandsV4Test(unittest.TestCase):
    def test_exact_score_boundaries_preserve_numeric_result_and_base_decision(self):
        for score, label, _color, decision in BOUNDARIES:
            with self.subTest(score=score):
                result = decide_pudim(eligible_output(score), {})
                self.assertEqual(result["finscore_prudencial"], score)
                self.assertEqual(result["segmento_politica"], label)
                self.assertEqual(result["decisao"], decision)
                self.assertEqual(result["rotulo"] == "Aprovação qualificada", score >= 750)
                self.assertEqual(result["garantia"]["recomendada"], 250 <= score < 500)

    def test_quality_boundaries_do_not_make_90_percent_a_general_block(self):
        for score in (249.99, 500, 824):
            for quality in (None, 0.7499, 0.75, 0.8999, 0.90, 0.95):
                with self.subTest(score=score, quality=quality):
                    result = decide_pudim(eligible_output(score, quality), {})
                    blocked = quality is None or quality < 0.75
                    expected = "dados_inconsistentes" if blocked else "nao_aprovar" if score < 250 else "aprovar"
                    self.assertEqual(result["decisao"], expected)
                    self.assertEqual(result["rotulo"] == "Aprovação qualificada",
                                     score >= 750 and quality is not None and quality >= 0.90)
                    self.assertEqual(result["segmento_politica"], _score_band(score, PolicyConfig()))

    def test_any_active_cap_prevents_qualification_without_changing_score_or_band(self):
        for score, caps in ((500, (500,)), (749.99, ()), (780, (800,)), (824, (900,)), (824, ())):
            with self.subTest(score=score, caps=caps):
                result = decide_pudim(eligible_output(score, caps=caps), {})
                self.assertEqual(result["finscore_prudencial"], score)
                self.assertEqual(result["segmento_politica"], _score_band(score, PolicyConfig()))
                self.assertEqual(result["rotulo"] == "Aprovação qualificada", score >= 750 and not caps)
                self.assertEqual(result["garantia"]["recomendada"], bool(caps))

    def test_score_and_quality_blocks_always_take_precedence(self):
        cases = (("apto_calculo", False), ("apto_decisao", False), ("classificacao_uso", "BLOQUEADO"))
        for key, value in cases:
            output = eligible_output(1000)
            output["status_qualidade"][key] = value
            with self.subTest(key=key):
                self.assertEqual(decide_pudim(output, {})["decisao"], "dados_inconsistentes")
        output = eligible_output(1000)
        output["finscore_observado"]["utilizavel_decisao"] = "NAO"
        self.assertEqual(decide_pudim(output, {})["decisao"], "dados_inconsistentes")

    def test_unavailable_scores_remain_uncalculable(self):
        for score in (None, float("nan"), float("inf")):
            result = decide_pudim(eligible_output(score), {})
            self.assertIsNone(result["finscore_prudencial"])
            self.assertEqual(result["segmento_politica"], "NÃO CALCULÁVEL")
            self.assertEqual(result["decisao"], "dados_inconsistentes")

    def test_only_existing_severe_stress_cut_prevents_qualification(self):
        for severe, qualified in ((249.99, False), (250, True), (600, True), (None, True)):
            with self.subTest(severe=severe):
                result = decide_pudim(eligible_output(severe=severe), {})
                self.assertEqual(result["rotulo"] == "Aprovação qualificada", qualified)
                self.assertEqual(result["segmento_politica"], "Risco reduzido")
                self.assertEqual(result["garantia"]["recomendada"], not qualified)

    def test_supplementary_evidence_does_not_downgrade_band_or_qualification(self):
        frames = {
            "df_serasa": {"serasa_score": 100, "restricao_grave": True},
            "df_springate_complementar": {"classificacao": "SINAL DE DISTRESS", "springate_S": 0.2},
            "df_fleuriet_complementar": {"diagnostico": "Dependência de financiamento de curto prazo"},
        }
        for name, row in frames.items():
            with self.subTest(evidence=name):
                output = eligible_output()
                output[name] = pd.DataFrame([row])
                result = decide_pudim(output, {})
                self.assertEqual(result["segmento_politica"], "Risco reduzido")
                self.assertEqual(result["rotulo"], "Aprovação qualificada")
                self.assertTrue(result["garantia"]["recomendada"])

    def test_policy_does_not_mutate_engine_output(self):
        output = eligible_output(caps=(900,), severe=200)
        before = copy.deepcopy(output)
        decide_pudim(output, {})
        for key, value in output.items():
            if isinstance(value, pd.DataFrame):
                pd.testing.assert_frame_equal(before[key], value, check_exact=True)
            else:
                self.assertEqual(before[key], value)

    def test_configured_thresholds_and_legacy_labels_are_preserved(self):
        config = PolicyConfig(limite_nao_aprovar=300, limite_referencia_garantia=600,
                              limite_aprovacao_qualificada=800, confiabilidade_minima_qualificada=0.95)
        self.assertEqual(_score_band(550, config), "Risco relevante")
        self.assertEqual(_score_band(780, config), "Risco aceitável")
        self.assertEqual(decide_pudim(eligible_output(824, 0.90), {}, config)["rotulo"], "Aprovar")
        legacy = PolicyConfig(rotulos_faixas={"500 OU MAIS": "Faixa institucional alta"})
        self.assertEqual(_score_band(650, legacy), "Faixa institucional alta")
        self.assertEqual(_score_band(824, legacy), "Faixa institucional alta")

    def test_qualified_label_round_trips_without_new_decision_code(self):
        output = eligible_output()
        recommendation = build_finscore_recommendation(output, decide_pudim(output, {}))
        self.assertEqual(recommendation.codigo.value, "aprovar")
        self.assertEqual(recommendation.rotulo, "Aprovação qualificada")
        self.assertEqual(FinScoreRecommendation.model_validate_json(recommendation.model_dump_json()), recommendation)
        for field, value in (("confiabilidade", 0.89), ("finscore_prudencial", 749.99)):
            payload = recommendation.model_dump()
            payload[field] = value
            with self.assertRaises(ValidationError):
                FinScoreRecommendation.model_validate(payload)

    def test_graph_colors_and_marker_follow_quantitative_boundaries_even_with_caps(self):
        captured = []
        def capture(figure, stream, **kwargs):
            captured.append(figure.axes[0])
            stream.write(b"chart-test")
        with patch.object(Figure, "savefig", capture):
            for score, label, color, _decision in BOUNDARIES:
                with self.subTest(score=score):
                    _render_finscore_band_chart({"finscore_ajustado": score, "cap_acionado_ate_500": True})
                    axes = captured[-1]
                    self.assertEqual(axes.lines[-1].get_color(), color)
                    self.assertEqual(axes.lines[-1].get_xdata()[0], score)
                    self.assertEqual([patch.get_width() for patch in axes.patches[::2]], [250] * 4)
                    self.assertTrue(any(label in text.get_text() for text in axes.texts))
            _render_finscore_band_chart({"finscore_ajustado": None})
            self.assertFalse(captured[-1].lines)

    def test_narrative_cannot_grant_qualification_to_an_ineligible_result(self):
        from APP.tests.test_parecer_pudim_v2 import _narrative
        narrative = _narrative()
        narrative.conclusao.texto = "A recomendação FinScore é Aprovação qualificada."
        for quality, rejected in ((0.89, True), (0.90, False)):
            output = eligible_output(quality=quality)
            recommendation = build_finscore_recommendation(output, decide_pudim(output, {}))
            contract = SimpleNamespace(governanca=SimpleNamespace(recomendacao_finscore=recommendation))
            issues = _validate_semantics(narrative, contract)
            self.assertEqual("RECOMENDACAO_DIVERGENTE" in {item.codigo for item in issues}, rejected)

    def test_pdf_separates_classification_and_recommendation_and_preserves_zero(self):
        for engine in ("xhtml2pdf", "playwright"):
            html = render_parecer_html("Corpo", {"finscore_ajustado": 824, "decisao": "aprovar",
                                      "recomendacao_finscore": "Aprovação qualificada"}, engine=engine)
            self.assertIn("Recomendação FinScore:</strong> Aprovação qualificada", html)
            self.assertIn("Risco reduzido", html)
            self.assertLess(html.index('class="finscore-band-chart"'), html.index('<section class="summary-grid">'))
            zero = render_parecer_html("Corpo", {"finscore_ajustado": 0}, engine=engine)
            self.assertIn('<p class="summary-value">0,00</p>', zero)

    def test_app_methodology_and_annex_share_the_same_band_explanation(self):
        content = load_methodology()
        self.assertEqual(content, METHODOLOGY_PATH.read_text(encoding="utf-8").strip())
        for _start, _end, label, _color in finscore_bands():
            self.assertIn(label, content)
        self.assertIn("75% e menos de 90%", content)
        self.assertIn("nenhum cap prudencial acionado", content)
        with patch("app_front.views.sobre.st.markdown") as markdown:
            render_methodology_section()
            self.assertEqual(markdown.call_args.args[0].strip(), content)


if __name__ == "__main__":
    unittest.main()
