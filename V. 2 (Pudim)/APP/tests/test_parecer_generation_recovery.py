"""Regressões da geração: números referenciados, correção e ressalva de PD."""
from copy import deepcopy
import unittest
from unittest.mock import Mock

from APP.tests import test_parecer_evaluation_v2 as fixtures
from app_front.services.parecer_generator import build_narrative_context, generate_parecer_document
from app_front.services.parecer_validation import ParecerValidationError, validate_parecer_narrative


class ParecerGenerationRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ParecerDocumentEvaluationTest.setUpClass()
        cls.fixture = fixtures.ParecerDocumentEvaluationTest()
        cls.contract = cls.fixture.contract

    def _generate(self, invoke):
        return generate_parecer_document(
            self.fixture.output, self.fixture.meta, self.fixture.policy,
            parecer_data=self.contract, invoke=invoke,
        )

    def test_analyzed_period_passes_in_summary_and_credit_thesis(self):
        narrative = self.fixture._narrative()
        for name in ("sumario_executivo", "tese_credito_governanca"):
            section = getattr(narrative, name)
            section.texto += " A análise abrange o período de 2023 a 2025."
            section.achado_ids = ["ACH-RES-FINSCORE"]
        invoke = Mock(return_value=narrative.model_dump_json())
        _document, generated, context = self._generate(invoke)
        self.assertEqual(invoke.call_count, 1)
        self.assertEqual(generated, narrative)
        self.assertTrue(context["validacao_narrativa"]["valido"])

    def test_temporal_references_use_actual_analyzed_years(self):
        for sentence, expected in (
            ("A análise considera 2023 a 2025.", False),
            ("Os exercícios de 2023, 2024 e 2025 foram analisados.", False),
            ("A série começa em 2023.", False),
            ("A análise considera o período de 2022 a 2025.", True),
            ("O score é 2023 pontos.", True),
            ("A receita foi de R$ 2023.", True),
            ("Em 2023 pontos, haveria aprovação.", True),
            ("A margem foi de 2023%.", True),
            ("O valor é 2023,50.", True),
        ):
            with self.subTest(sentence=sentence):
                narrative = self.fixture._narrative()
                narrative.sumario_executivo.texto += " " + sentence
                narrative.sumario_executivo.achado_ids = ["ACH-RES-FINSCORE"]
                report = validate_parecer_narrative(narrative, self.contract, raise_on_error=False)
                self.assertEqual("NUMERO_SEM_LASTRO" in {i.codigo for i in report.problemas}, expected)

    def test_formatted_evidence_round_trips_without_changing_contract(self):
        original = deepcopy(self.contract.model_dump(mode="json"))
        context = build_narrative_context(self.contract)
        checked = 0
        for finding in context["achados"]:
            for evidence in finding["evidencias"]:
                if "valor_formatado" not in evidence:
                    continue
                with self.subTest(finding=finding["achado_id"], field=evidence["campo"]):
                    narrative = self.fixture._narrative()
                    narrative.sumario_executivo.texto = (
                        "A evidência documentada registra " + evidence["valor_formatado"] + "."
                    )
                    narrative.sumario_executivo.achado_ids = [finding["achado_id"]]
                    report = validate_parecer_narrative(narrative, self.contract, raise_on_error=False)
                    self.assertNotIn("NUMERO_SEM_LASTRO", {issue.codigo for issue in report.problemas})
                    self.assertEqual(evidence["valor_formatado"].endswith("%"),
                                     evidence["unidade"] == "proporcao")
                    checked += 1
        self.assertGreater(checked, 50)
        self.assertEqual(self.contract.model_dump(mode="json"), original)

    def test_numeric_correction_receives_rejected_draft_and_original_evidence(self):
        valid = self.fixture._narrative()
        invalid = valid.model_copy(deep=True)
        invalid.conclusao.texto += " O score é 999,99 pontos."

        def respond(messages, **_kwargs):
            drafts = [item for item in messages if item["role"] == "assistant"]
            if not drafts:
                return invalid.model_dump_json()
            self.assertEqual(drafts[-1]["content"], invalid.model_dump_json())
            self.assertIn("999,99", messages[-1]["content"])
            self.assertIn("conclusao", messages[-1]["content"])
            self.assertIn("valor_formatado", messages[1]["content"])
            return valid.model_dump_json()

        invoke = Mock(side_effect=respond)
        _document, generated, context = self._generate(invoke)
        self.assertEqual(invoke.call_count, 2)
        self.assertEqual(generated, valid)
        self.assertTrue(context["validacao_narrativa"]["valido"])
        self.assertIn("999,99", invalid.conclusao.texto)

    def test_each_retry_receives_most_recent_rejected_draft(self):
        first = self.fixture._narrative()
        first.conclusao.texto += " O score é 999,99 pontos."
        second = self.fixture._narrative()
        second.conclusao.texto += " O score é 998,99 pontos."
        valid = self.fixture._narrative()
        invoke = Mock(side_effect=[first.model_dump_json(), second.model_dump_json(), valid.model_dump_json()])
        self._generate(invoke)
        last_messages = invoke.call_args.args[0]
        drafts = [item["content"] for item in last_messages if item["role"] == "assistant"]
        self.assertEqual(drafts, [second.model_dump_json()])

    def test_unsupported_numbers_still_block_publication_after_retries(self):
        invalid = self.fixture._narrative()
        invalid.conclusao.texto += " O score é 999,99 pontos."
        invoke = Mock(return_value=invalid.model_dump_json())
        with self.assertRaises(ParecerValidationError) as raised:
            self._generate(invoke)
        self.assertEqual(invoke.call_count, 3)
        self.assertIn("NUMERO_SEM_LASTRO", {i.codigo for i in raised.exception.report.problemas})

    def test_explicit_pd_disclaimers_pass_on_first_generation(self):
        for disclaimer in (
            "FinScore não é PD.",
            "FinScore não representa uma probabilidade de inadimplência.",
            "FinScore não deve ser interpretado como probabilidade de default.",
        ):
            with self.subTest(disclaimer=disclaimer):
                narrative = self.fixture._narrative()
                narrative.formacao_finscore.texto += " " + disclaimer
                invoke = Mock(return_value=narrative.model_dump_json())
                _document, generated, context = self._generate(invoke)
                self.assertEqual(invoke.call_count, 1)
                self.assertEqual(generated, narrative)
                self.assertTrue(context["avaliacao_documento"]["valido"])

    def test_pd_equivalence_still_rejected_even_after_disclaimer(self):
        for statement in (
            "FinScore representa a probabilidade de inadimplência.",
            "A PD é expressa pelo FinScore.",
            "FinScore não é PD. Contudo, FinScore equivale à PD.",
        ):
            with self.subTest(statement=statement):
                narrative = self.fixture._narrative()
                narrative.formacao_finscore.texto += " " + statement
                report = validate_parecer_narrative(narrative, self.contract, raise_on_error=False)
                self.assertIn("FINSCORE_COMO_PD", {issue.codigo for issue in report.problemas})


if __name__ == "__main__":
    unittest.main()
