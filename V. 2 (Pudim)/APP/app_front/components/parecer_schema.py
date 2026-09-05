"""Contrato da interpretação variável do parecer de crédito."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


FINDING_ID_PATTERN = re.compile(r"^ACH-[A-Z0-9][A-Z0-9-]*$")


class NarrativeContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class NarrativeSection(NarrativeContractModel):
    texto: str = Field(
        min_length=40,
        description="Interpretação técnica em prosa, sem título e sem repetir tabelas.",
    )
    achado_ids: list[str] = Field(
        min_length=1,
        max_length=12,
        description="Achados do livro de evidências que sustentam toda a seção.",
    )

    @field_validator("achado_ids")
    @classmethod
    def validate_finding_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("achado_ids duplicados na seção")
        if any(not FINDING_ID_PATTERN.fullmatch(value) for value in values):
            raise ValueError("achado_id possui formato inválido")
        return values


class NarrativeItem(NarrativeContractModel):
    texto: str = Field(
        min_length=12,
        description="Item objetivo e verificável, sem marcador Markdown.",
    )
    achado_ids: list[str] = Field(
        min_length=1,
        max_length=6,
        description="Achados que sustentam especificamente este item.",
    )

    @field_validator("achado_ids")
    @classmethod
    def validate_finding_ids(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("achado_ids duplicados no item")
        if any(not FINDING_ID_PATTERN.fullmatch(value) for value in values):
            raise ValueError("achado_id possui formato inválido")
        return values


class ParecerNarrativo(NarrativeContractModel):
    """Interpretação organizada; fatos e posições permanecem determinísticos."""

    sumario_executivo: NarrativeSection = Field(
        description="Síntese da recomendação, materialidade e limitações principais."
    )
    escopo_e_qualidade: NarrativeSection = Field(
        description="Escopo temporal, qualidade, confiabilidade, correções e limitações."
    )
    analise_economico_operacional: NarrativeSection = Field(
        description="Trajetória de receita, margens, produtividade e ciclo financeiro."
    )
    analise_financeira_patrimonial: NarrativeSection = Field(
        description="Capitalização, liquidez, capital de giro, dívida e serviço financeiro."
    )
    formacao_finscore: NarrativeSection = Field(
        description="Núcleos, métodos, gargalo, contribuições, cobertura e caps."
    )
    estresse_e_evidencias: NarrativeSection = Field(
        description="Cenários, simulação válida e evidências suplementares separadas."
    )
    tese_credito_governanca: NarrativeSection = Field(
        description="Tese de crédito, garantia recomendada e posições registradas."
    )
    riscos_diligencias_monitoramento: NarrativeSection = Field(
        description="Síntese das prioridades, diligências e acompanhamento proporcional."
    )
    conclusao: NarrativeSection = Field(
        description="Conclusão coerente com a recomendação e a governança registrada."
    )
    pontos_fortes: list[NarrativeItem] = Field(
        default_factory=list,
        max_length=8,
        description="Forças materiais efetivamente sustentadas; pode ser vazio.",
    )
    riscos_prioritarios: list[NarrativeItem] = Field(
        default_factory=list,
        max_length=10,
        description="Riscos materiais efetivamente sustentados; pode ser vazio.",
    )
    validacoes_pendentes: list[NarrativeItem] = Field(
        default_factory=list,
        max_length=12,
        description="Diligências sustentadas por bloqueios ou limitações; pode ser vazio.",
    )
    recomendacoes_monitoramento: list[NarrativeItem] = Field(
        default_factory=list,
        max_length=10,
        description="Acompanhamentos sem inventar covenant, limite ou periodicidade.",
    )

    @model_validator(mode="after")
    def validate_proportional_substance(self) -> "ParecerNarrativo":
        sections = (
            self.sumario_executivo,
            self.escopo_e_qualidade,
            self.analise_economico_operacional,
            self.analise_financeira_patrimonial,
            self.formacao_finscore,
            self.estresse_e_evidencias,
            self.tese_credito_governanca,
            self.riscos_diligencias_monitoramento,
            self.conclusao,
        )
        total_words = sum(len(section.texto.split()) for section in sections)
        if total_words < 450:
            raise ValueError("corpo narrativo insuficiente para cobrir as evidências materiais")
        if total_words > 1_800:
            raise ValueError("corpo narrativo excede o limite editorial")
        return self

    def referenced_finding_ids(self) -> set[str]:
        result: set[str] = set()
        for name in (
            "sumario_executivo",
            "escopo_e_qualidade",
            "analise_economico_operacional",
            "analise_financeira_patrimonial",
            "formacao_finscore",
            "estresse_e_evidencias",
            "tese_credito_governanca",
            "riscos_diligencias_monitoramento",
            "conclusao",
        ):
            result.update(getattr(self, name).achado_ids)
        for name in (
            "pontos_fortes",
            "riscos_prioritarios",
            "validacoes_pendentes",
            "recomendacoes_monitoramento",
        ):
            for item in getattr(self, name):
                result.update(item.achado_ids)
        return result


__all__ = ["NarrativeItem", "NarrativeSection", "ParecerNarrativo"]
