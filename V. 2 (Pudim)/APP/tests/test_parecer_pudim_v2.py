from __future__ import annotations

import copy
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pypdf import PdfWriter

from app_front.components.llm_client import (
    MODEL_NAME,
    MODEL_REASONING_EFFORT,
    MODEL_TEMPERATURE,
    _call_openai_responses_structured,
    _strict_json_schema,
)
from app_front.components.parecer_schema import ParecerNarrativo
from app_front.pdf.export_pdf import contar_paginas_pdf
from app_front.services.credit_governance import (
    governance_fingerprint,
    initialize_governance_state,
    register_analyst_manifestation,
    register_authority_decision,
)
from app_front.services.credit_policy import decide_pudim
from app_front.services.finscore_service import run_finscore
from app_front.services.parecer_data_builder import build_finscore_recommendation
from app_front.services.parecer_generator import (
    _narrative_json_schema,
    build_parecer_context,
    render_parecer_document,
)


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"
NARRATIVE_FIELDS = (
    "sumario_executivo",
    "escopo_e_qualidade",
    "analise_economico_operacional",
    "analise_financeira_patrimonial",
    "formacao_finscore",
    "estresse_e_evidencias",
    "tese_credito_governanca",
    "riscos_diligencias_monitoramento",
    "conclusao",
)


def _narrative() -> ParecerNarrativo:
    text = (
        "A análise utiliza exclusivamente os fatos do contexto, distingue o dado observado do "
        "cálculo e preserva a decisão determinística. As limitações permanecem explícitas e "
        "nenhuma ausência é convertida em estimativa. O julgamento considera capacidade, "
        "resiliência, qualidade documental e sinais suplementares, sempre subordinado aos "
        "controles metodológicos. "
    ) * 2
    section = {"texto": text, "achado_ids": ["ACH-CEN-SEVERO"]}

    def item(value: str) -> dict:
        return {"texto": value, "achado_ids": ["ACH-CEN-SEVERO"]}

    return ParecerNarrativo(
        **{field: section for field in NARRATIVE_FIELDS},
        pontos_fortes=[item("Força documentada no conjunto analisado.")],
        riscos_prioritarios=[item("Risco documentado no conjunto analisado.")],
        validacoes_pendentes=[item("Validação documental indicada pelos achados.")],
        recomendacoes_monitoramento=[item("Monitoramento recomendado conforme os achados.")],
    )


class ParecerPudimV2Test(unittest.TestCase):
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
            "serasa_restricao_grave": False,
        }
        cls.output = run_finscore(data, dict(cls.meta), executar_simulacoes=False)

    def _eligible_output(self, score: float) -> dict:
        output = copy.deepcopy(self.output)
        output["status_qualidade"].update(
            {
                "apto_calculo": True,
                "apto_decisao": True,
                "classificacao_uso": "CALCULADO",
                "indice_confiabilidade": 0.918,
                "alertas_bloqueadores_decisao": 0,
            }
        )
        output["finscore_observado"].update(
            {"finscore_prudencial": score, "utilizavel_decisao": "SIM"}
        )
        for name in (
            "df_alertas_vies",
            "df_caps_prudenciais",
            "df_qualidade",
            "df_correcoes_auditoria",
        ):
            frame = output.get(name)
            if isinstance(frame, pd.DataFrame):
                output[name] = frame.iloc[0:0]
        return output

    def test_configuration_uses_requested_model_and_low_variability(self) -> None:
        self.assertEqual(MODEL_NAME, "gpt-5.6-sol")
        self.assertEqual(MODEL_TEMPERATURE, 0.2)
        self.assertEqual(MODEL_REASONING_EFFORT, "high")

    def test_native_quality_gate_prevents_automatic_approval(self) -> None:
        policy = decide_pudim(self.output, self.meta)

        self.assertEqual(policy["decisao"], "dados_inconsistentes")
        self.assertTrue(policy["bloqueios"])
        self.assertEqual(len(policy["bloqueios_detalhados"]), 3)
        self.assertTrue(all(item["motivo"] for item in policy["bloqueios_detalhados"]))
        self.assertTrue(all(item["providencia"] for item in policy["bloqueios_detalhados"]))
        self.assertNotIn("economia_operacao", policy)

    def test_missing_score_suspends_instead_of_simulating_a_decline(self) -> None:
        output = copy.deepcopy(self.output)
        output["finscore_observado"] = {}
        output["status_qualidade"].update(
            {"apto_calculo": False, "apto_decisao": False, "classificacao_uso": "BLOQUEADO"}
        )

        policy = decide_pudim(output, self.meta)

        self.assertEqual(policy["decisao"], "dados_inconsistentes")
        self.assertIsNone(policy["finscore_prudencial"])

    def test_eligible_score_approves_without_commercial_inputs(self) -> None:
        output = self._eligible_output(800.0)
        policy = decide_pudim(output, self.meta)

        self.assertEqual(policy["decisao"], "aprovar")
        self.assertFalse(policy["garantia"]["recomendada"])
        self.assertNotIn("economia_operacao", policy)

    def test_commercial_metadata_does_not_affect_the_decision(self) -> None:
        output = self._eligible_output(800.0)
        baseline = decide_pudim(output, self.meta)
        legacy_metadata = {
            **self.meta,
            "taxa_juros_anual": 0.01,
            "custo_captacao_anual": 0.99,
            "pd_institucional_anual": 0.99,
        }

        with_legacy_metadata = decide_pudim(output, legacy_metadata)

        self.assertEqual(with_legacy_metadata["decisao"], baseline["decisao"])
        self.assertEqual(with_legacy_metadata["garantia"], baseline["garantia"])

    def test_restricted_approval_recommends_guarantee(self) -> None:
        output = self._eligible_output(412.23)
        policy = decide_pudim(output, self.meta)

        self.assertEqual(policy["decisao"], "aprovar")
        self.assertTrue(policy["garantia"]["recomendada"])
        self.assertIsNone(policy["garantia"]["cobertura_minima"])

    def test_supplementary_distress_recommends_guarantee_without_veto(self) -> None:
        output = self._eligible_output(650.0)
        last_index = output["df_springate_complementar"].index[-1]
        output["df_springate_complementar"].loc[last_index, "classificacao"] = (
            "SINAL DE DISTRESS"
        )
        policy = decide_pudim(output, self.meta)

        self.assertEqual(policy["decisao"], "aprovar")
        self.assertTrue(policy["garantia"]["recomendada"])
        self.assertTrue(any("Springate" in item for item in policy["condicoes"]))

    def test_severe_serasa_restriction_is_supplementary_not_an_automatic_veto(self) -> None:
        output = self._eligible_output(650.0)
        output["df_serasa"].loc[:, "restricao_grave"] = True

        policy = decide_pudim(output, self.meta)

        self.assertEqual(policy["decisao"], "aprovar")
        self.assertTrue(policy["garantia"]["recomendada"])

    def test_eligible_score_below_250_is_not_approved(self) -> None:
        policy = decide_pudim(self._eligible_output(249.99), self.meta)

        self.assertEqual(policy["decisao"], "nao_aprovar")

    def test_reliability_below_native_threshold_is_inconsistent(self) -> None:
        output = self._eligible_output(650.0)
        output["status_qualidade"]["indice_confiabilidade"] = 0.749

        policy = decide_pudim(output, self.meta)

        self.assertEqual(policy["decisao"], "dados_inconsistentes")

    def test_report_has_fixed_methodology_and_audit_annex(self) -> None:
        policy = decide_pudim(self.output, self.meta)
        context = build_parecer_context(self.output, self.meta, policy)
        document = render_parecer_document(_narrative(), context)

        self.assertIn("Anexo 1 — Metodologia", document)
        self.assertIn("Anexo 2 — Informações da análise", document)
        self.assertIn("2023", document)
        self.assertGreater(len(document.split()), 3_000)

    def test_report_omits_governance_positions_and_keeps_institutional_caveat(self) -> None:
        policy = decide_pudim(self.output, self.meta)
        recommendation = build_finscore_recommendation(self.output, policy)
        state = initialize_governance_state(
            recommendation,
            governance_fingerprint(self.output, recommendation),
        )
        state = register_analyst_manifestation(
            state,
            recommendation.codigo,
            "A manifestação acompanha os fundamentos documentados e os controles de qualidade.",
            "analista@instituicao.test",
        )
        state = register_authority_decision(
            state,
            "nao_aprovar",
            "A alçada considerou outros elementos de governança e deliberou pela não aprovação.",
            "alcada@instituicao.test",
        )
        context = build_parecer_context(
            self.output,
            self.meta,
            policy,
            governance=state.governanca.model_dump(mode="json"),
        )
        document = render_parecer_document(_narrative(), context)

        self.assertIn("**Recomendação FinScore:**", document)
        self.assertNotIn("| Manifestação do analista |", document)
        self.assertNotIn("| Decisão da alçada |", document)
        self.assertNotIn("governança", document.lower())
        self.assertEqual(document.count("decisão de alçada superior"), 1)

    def test_nested_pandas_diagnostics_are_serialized_without_boolean_evaluation(self) -> None:
        output = copy.deepcopy(self.output)
        output["diagnosticos_simulacao"] = {
            "tabela": pd.DataFrame([{"cenario": "base", "valor": 1.0}]),
            "serie": pd.Series({"aceitos": 10, "rejeitados": 2}),
        }
        policy = decide_pudim(output, self.meta)

        context = build_parecer_context(output, self.meta, policy)

        self.assertEqual(
            context["diagnosticos_simulacao"]["tabela"],
            [{"cenario": "base", "valor": 1.0}],
        )
        self.assertEqual(
            context["diagnosticos_simulacao"]["serie"],
            {"aceitos": 10, "rejeitados": 2},
        )

    def test_analyst_report_does_not_expose_generation_technology(self) -> None:
        policy = decide_pudim(self.output, self.meta)
        context = build_parecer_context(self.output, self.meta, policy)
        document = render_parecer_document(_narrative(), context).lower()

        for forbidden in (
            "inteligência artificial",
            "modelo de linguagem",
            "openai",
            "temperatura do modelo",
            "versão do prompt",
            "pudim",
            "brigadeiro",
            "hash do código",
        ):
            self.assertNotIn(forbidden, document)

    def test_methodology_documents_only_the_three_decisions(self) -> None:
        methodology = (
            APP_DIR / "app_front" / "content" / "metodologia_pudim_2_0_20.md"
        ).read_text(encoding="utf-8")

        for expected in ("**Aprovar**", "**Não aprovar**", "**Dados inconsistentes**"):
            self.assertIn(expected, methodology)
        for obsolete in (
            "Aprovar com condições",
            "Condicionar à validação",
            "Suspender até validação",
        ):
            self.assertNotIn(obsolete, methodology)
        self.assertIn("confiabilidade inferior a 75%", methodology)
        self.assertIn("Springate", methodology)
        self.assertIn("Fleuriet", methodology)
        self.assertIn("não presume percentual de cobertura", methodology)
        for unsupported in (
            "PD institucional",
            "custo de captação",
            "taxa de recuperação",
            "retorno mínimo",
            "120%",
            "confiabilidade inferior a 80%",
        ):
            self.assertNotIn(unsupported, methodology)
        self.assertTrue(methodology.startswith("## Metodologia"))
        self.assertNotIn("vigente", methodology.lower())
        self.assertNotRegex(methodology, r"(?m)^###\s+[A-Z]\.\d+")

    def test_responses_api_payload_is_structured_and_not_stored(self) -> None:
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "output": [
                        {"content": [{"type": "output_text", "text": '{"ok":true}'}]}
                    ],
                    "usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
                }

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}), patch(
            "app_front.components.llm_client.requests.post", return_value=FakeResponse()
        ) as post:
            response = _call_openai_responses_structured(
                [{"role": "user", "content": "teste"}],
                model="gpt-5.6-sol",
                temperature=0.2,
                reasoning_effort="high",
                schema_name="test_schema",
                json_schema={
                    "type": "object",
                    "properties": {"ok": {"type": "boolean"}},
                    "required": ["ok"],
                    "additionalProperties": False,
                },
            )

        payload = post.call_args.kwargs["json"]
        self.assertEqual(response.content, '{"ok":true}')
        self.assertEqual(post.call_args.args[0], "https://api.openai.com/v1/responses")
        self.assertFalse(payload["store"])
        self.assertEqual(payload["model"], "gpt-5.6-sol")
        self.assertNotIn("temperature", payload)
        self.assertTrue(payload["text"]["format"]["strict"])

    def test_strict_schema_requires_all_declared_fields_recursively(self) -> None:
        source = {
            "type": "object",
            "properties": {
                "obrigatorio": {"type": "string"},
                "itens": {
                    "type": "array",
                    "default": [],
                    "items": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string"},
                            "referencias": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "secao": {"$ref": "#/$defs/Secao", "description": "Texto narrativo"},
            },
            "required": ["obrigatorio"],
        }

        normalized = _strict_json_schema(source)

        self.assertEqual(normalized["required"], ["obrigatorio", "itens", "secao"])
        self.assertFalse(normalized["additionalProperties"])
        self.assertNotIn("default", normalized["properties"]["itens"])
        self.assertEqual(normalized["properties"]["secao"], {"$ref": "#/$defs/Secao"})
        item_schema = normalized["properties"]["itens"]["items"]
        self.assertEqual(item_schema["required"], ["texto", "referencias"])
        self.assertFalse(item_schema["additionalProperties"])
        self.assertEqual(source["required"], ["obrigatorio"])

    def test_narrative_schema_accepts_only_findings_from_the_evidence_book(self) -> None:
        allowed = ["ACH-RES-FINSCORE", "ACH-CEN-SEVERO", "ACH-CEN-SEVERO"]

        schema = _narrative_json_schema(allowed)

        expected = ["ACH-RES-FINSCORE", "ACH-CEN-SEVERO"]
        for definition in ("NarrativeSection", "NarrativeItem"):
            items = schema["$defs"][definition]["properties"]["achado_ids"]["items"]
            self.assertEqual(items, {"type": "string", "enum": expected})

        with self.assertRaisesRegex(ValueError, "não contém achados"):
            _narrative_json_schema([])

    def test_pdf_page_counter(self) -> None:
        writer = PdfWriter()
        for _ in range(7):
            writer.add_blank_page(width=595, height=842)
        stream = io.BytesIO()
        writer.write(stream)
        self.assertEqual(contar_paginas_pdf(stream.getvalue()), 7)


if __name__ == "__main__":
    unittest.main()
