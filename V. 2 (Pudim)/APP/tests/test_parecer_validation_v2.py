from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd

from app_front.components.parecer_data_schema import FindingCategory
from app_front.components.parecer_schema import ParecerNarrativo
from app_front.services.credit_policy import decide_pudim
from app_front.services.finscore_service import run_finscore
from app_front.services.parecer_data_builder import build_parecer_data
from app_front.services.parecer_generator import build_narrative_context
from app_front.services.parecer_validation import (
    NUMBER_PATTERN,
    reconcile_narrative_numbers,
    validate_parecer_narrative,
)


APP_DIR = Path(__file__).resolve().parents[1]
REFERENCE_XLSX = APP_DIR.parent / "MODELO" / "dados_teste" / "1Callamarys.xlsx"


SECTION_TEXTS = {
    "sumario_executivo": "A síntese reúne os elementos materiais da recomendação, ponderando capacidade financeira, qualidade informacional, limitações documentais e medidas de saneamento. O resultado deve ser lido como suporte quantitativo à análise de crédito, preservando as ressalvas registradas. Os aspectos favoráveis não eliminam fragilidades, e cada conclusão permanece vinculada às evidências identificadas no dossiê.",
    "escopo_e_qualidade": "O escopo considera os exercícios efetivamente processados e distingue informações recebidas, valores utilizados e cálculos derivados. As ocorrências de qualidade permanecem visíveis, sem converter ausências em zero ou promover estimativas. A confiabilidade condiciona o uso analítico, enquanto bloqueios, alertas e limitações recebem tratamento proporcional à sua origem e ao efeito documentado no resultado.",
    "analise_economico_operacional": "A dimensão econômico-operacional é examinada pela trajetória de receitas, margens, produtividade e ciclo financeiro. A leitura combina nível atual, dinâmica temporal, resiliência, nota e contribuição, evitando conclusões baseadas em indicador isolado. Tendências favoráveis e pressões operacionais são ponderadas pelo efeito efetivo no núcleo, com atenção à recorrência dos resultados e à consistência entre exercícios.",
    "analise_financeira_patrimonial": "A dimensão financeira e patrimonial integra capitalização, liquidez, capital de giro, endividamento e cobertura financeira. A interpretação observa simultaneamente trajetória, cobertura informacional e contribuição para o núcleo. Fragilidades patrimoniais são relacionadas aos controles prudenciais acionados, enquanto sinais relativos de liquidez são mantidos em perspectiva, sem criar cortes externos ou parâmetros não fornecidos.",
    "formacao_finscore": "A formação do FinScore preserva a separação entre núcleos, abordagens estrutural e adaptativa, gargalo e resultado prudencial. Notas temporais e pesos explicam as contribuições observadas, e os limitadores são identificados pela distância ponderada em relação à contribuição possível. Controles prudenciais permanecem explícitos, sem converter a pontuação em probabilidade de inadimplência ou classificação regulatória.",
    "estresse_e_evidencias": "Os cenários oferecem hipóteses condicionais para avaliar sensibilidade e resiliência, sem constituir previsão. A comparação entre base e estresse conserva premissas e validade registradas. Serasa permanece evidência externa separada, enquanto Springate e Fleuriet funcionam como diagnósticos derivados suplementares. Divergências são apresentadas para leitura conjunta e não modificam isoladamente a recomendação calculada.",
    "tese_credito_governanca": "A tese de crédito articula recomendação, fundamentos quantitativos, limitações e mitigadores disponíveis. A indicação de garantia conserva apenas o alcance efetivamente registrado, sem presumir modalidade, cobertura ou exequibilidade. As providências recomendadas permanecem vinculadas aos riscos e às evidências documentadas na análise.",
    "riscos_diligencias_monitoramento": "As prioridades de risco decorrem dos achados materiais e de seus efeitos comprovados, não de referências genéricas. As diligências respondem diretamente às limitações e bloqueios, indicando o saneamento necessário. O monitoramento acompanha indicadores relacionados às fragilidades observadas, mas não cria obrigação contratual, limite, periodicidade ou consequência que não tenham sido formalmente definidos pela instituição credora.",
    "conclusao": "A conclusão consolida os resultados sem alterar a recomendação. Forças relativas, limitadores, qualidade informacional e comportamento sob estresse são ponderados conforme as evidências. Pendências permanecem acompanhadas das providências cabíveis. O parecer encerra a análise preservando rastreabilidade, prudência e clareza sobre o alcance do FinScore. A documentação permite revisar os fundamentos empregados e localizar cada suporte factual relevante.",
}


class ParecerValidationV2Test(unittest.TestCase):
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
        cls.contract = build_parecer_data(
            cls.output,
            cls.meta,
            decide_pudim(cls.output, cls.meta),
        )
        cls.context = build_narrative_context(cls.contract)

    def _payload(self) -> dict:
        routes = self.context["roteiro_achados"]
        blockers = [
            item.achado_id
            for item in self.contract.achados
            if item.categoria is FindingCategory.BLOCK
        ]
        strengths = [
            item.achado_id
            for item in self.contract.achados
            if item.categoria is FindingCategory.STRENGTH
        ]
        risks = [
            item.achado_id
            for item in self.contract.achados
            if item.categoria is FindingCategory.RISK
        ]
        payload = {
            name: {"texto": text, "achado_ids": routes[name][:1]}
            for name, text in SECTION_TEXTS.items()
        }
        payload["escopo_e_qualidade"]["achado_ids"] = list(
            dict.fromkeys([*payload["escopo_e_qualidade"]["achado_ids"], *blockers])
        )
        payload.update(
            {
                "pontos_fortes": [
                    {"texto": "Contribuição relativa favorável documentada.", "achado_ids": strengths[:1]}
                ],
                "riscos_prioritarios": [
                    {"texto": "Limitador material identificado no núcleo.", "achado_ids": risks[:1]}
                ],
                "validacoes_pendentes": [
                    {"texto": "Saneamento documental requerido para nova avaliação.", "achado_ids": blockers}
                ],
                "recomendacoes_monitoramento": [
                    {"texto": "Acompanhar o limitador conforme as evidências registradas.", "achado_ids": risks[:1]}
                ],
            }
        )
        return payload

    def _narrative(self) -> ParecerNarrativo:
        return ParecerNarrativo.model_validate(self._payload())

    def test_valid_narrative_passes_all_layers(self) -> None:
        report = validate_parecer_narrative(
            self._narrative(),
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertTrue(report.valido, report.problemas)
        self.assertGreater(report.referencias_verificadas, 9)

    def test_unknown_finding_reference_is_rejected(self) -> None:
        payload = self._payload()
        payload["conclusao"]["achado_ids"] = ["ACH-INEXISTENTE"]
        report = validate_parecer_narrative(
            ParecerNarrativo.model_validate(payload),
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertIn("REF_INEXISTENTE", {item.codigo for item in report.problemas})

    def test_number_without_referenced_evidence_is_rejected(self) -> None:
        payload = self._payload()
        payload["conclusao"]["texto"] += " O resultado alternativo seria 999,99 pontos."
        report = validate_parecer_narrative(
            ParecerNarrativo.model_validate(payload),
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertIn("NUMERO_SEM_LASTRO", {item.codigo for item in report.problemas})

    def test_unsubstantiated_numeric_sentence_is_removed_before_release(self) -> None:
        payload = self._payload()
        payload["conclusao"]["texto"] += " O resultado alternativo seria 999,99 pontos."

        revised = reconcile_narrative_numbers(
            ParecerNarrativo.model_validate(payload), self.contract
        )
        report = validate_parecer_narrative(
            revised,
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertNotIn("999,99", revised.conclusao.texto)
        self.assertNotIn("NUMERO_SEM_LASTRO", {item.codigo for item in report.problemas})

    def test_section_receives_neutral_text_if_its_only_number_is_unsupported(self) -> None:
        payload = self._payload()
        payload["conclusao"]["texto"] = (
            "A estimativa alternativa, considerada sem evidência documental, sem reconciliação "
            "contábil, sem confirmação cadastral e sem suporte nos achados materiais, seria de "
            "999,99 pontos, embora a análise exija prudência, rastreabilidade, coerência temporal, "
            "fundamentação econômico-financeira e associação direta entre cada afirmação e sua "
            "respectiva fonte registrada no dossiê desta operação de crédito empresarial."
        )

        revised = reconcile_narrative_numbers(
            ParecerNarrativo.model_validate(payload), self.contract
        )
        report = validate_parecer_narrative(
            revised,
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertNotIn("999,99", revised.conclusao.texto)
        self.assertNotIn("NUMERO_SEM_LASTRO", {item.codigo for item in report.problemas})

    def test_date_is_not_decomposed_into_unsupported_financial_numbers(self) -> None:
        payload = self._payload()
        payload["estresse_e_evidencias"]["texto"] += " A consulta ocorreu em 12/09/2026."
        report = validate_parecer_narrative(
            ParecerNarrativo.model_validate(payload),
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertNotIn("NUMERO_SEM_LASTRO", {item.codigo for item in report.problemas})

    def test_number_tokenizer_preserves_complete_years_and_formatted_values(self) -> None:
        text = "Exercícios 2023, 2024 e 2025; saldo de 294.105,39 e margem de -0,02%."

        self.assertEqual(
            NUMBER_PATTERN.findall(text),
            ["2023", "2024", "2025", "294.105,39", "-0,02%"],
        )

    def test_final_decision_wording_is_rejected(self) -> None:
        payload = self._payload()
        payload["conclusao"]["texto"] += " Esta é a decisão final."
        report = validate_parecer_narrative(
            ParecerNarrativo.model_validate(payload),
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertIn("GOVERNANCA_CONFUNDIDA", {item.codigo for item in report.problemas})

    def test_scenario_disclaimer_is_not_mistaken_for_a_prediction(self) -> None:
        payload = self._payload()
        payload["estresse_e_evidencias"]["texto"] += (
            " O cenário não representa uma previsão e permanece como hipótese condicional."
        )
        report = validate_parecer_narrative(
            ParecerNarrativo.model_validate(payload),
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertNotIn("CENARIO_PREDITIVO", {item.codigo for item in report.problemas})

    def test_score_percentage_near_guarantee_is_not_read_as_coverage(self) -> None:
        payload = self._payload()
        payload["tese_credito_governanca"]["texto"] += (
            " A garantia é avaliada em conjunto com a qualidade de 91,81%, sem definir cobertura."
        )
        report = validate_parecer_narrative(
            ParecerNarrativo.model_validate(payload),
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertNotIn("COBERTURA_INVENTADA", {item.codigo for item in report.problemas})

    def test_material_repetition_is_rejected(self) -> None:
        payload = self._payload()
        payload["conclusao"]["texto"] = payload["sumario_executivo"]["texto"]
        report = validate_parecer_narrative(
            ParecerNarrativo.model_validate(payload),
            self.contract,
            routes=self.context["roteiro_achados"],
            raise_on_error=False,
        )

        self.assertIn("REPETICAO_MATERIAL", {item.codigo for item in report.problemas})


if __name__ == "__main__":
    unittest.main()
