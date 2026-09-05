"""Contrato estruturado e auditável das informações do parecer FinScore.

O contrato desta unidade não substitui o contrato público do motor. Ele organiza
os dados já calculados para consumo pelas camadas de síntese, governança,
redação e renderização do parecer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
import math
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    field_validator,
    model_validator,
)


PARECER_DATA_SCHEMA_VERSION = "1.0"

FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
NonNegativeFloat = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Score = Annotated[float, Field(ge=0, le=1000, allow_inf_nan=False)]
Ratio = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Year = Annotated[int, Field(ge=1900, le=2200)]
Scalar = StrictBool | StrictInt | FiniteFloat | str


class ContractModel(BaseModel):
    """Base estrita para impedir campos silenciosamente ignorados."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class AvailabilityStatus(str, Enum):
    AVAILABLE = "disponivel"
    UNAVAILABLE = "nao_informado"
    NOT_CALCULATED = "nao_calculado"


class DataNature(str, Enum):
    REPORTED = "reportado"
    PROPOSED = "proposto"
    USED = "utilizado"
    DERIVED = "derivado"
    CALCULATED = "calculado"
    HYPOTHESIS = "hipotese"
    EXTERNAL = "evidencia_externa"


class RecommendationCode(str, Enum):
    APPROVE = "aprovar"
    DO_NOT_APPROVE = "nao_aprovar"
    INCONSISTENT_DATA = "dados_inconsistentes"


class GovernanceStage(str, Enum):
    RECOMMENDATION = "recomendacao_finscore"
    ANALYST = "manifestacao_analista"
    AUTHORITY = "decisao_alcada"


class GovernanceAction(str, Enum):
    REGISTERED = "registrada"
    REPLACED = "substituida"
    INVALIDATED = "invalidada"


RECOMMENDATION_LABELS = {
    RecommendationCode.APPROVE: "Aprovar",
    RecommendationCode.DO_NOT_APPROVE: "Não aprovar",
    RecommendationCode.INCONSISTENT_DATA: "Dados inconsistentes",
}


class FindingCategory(str, Enum):
    RESULT = "resultado"
    STRENGTH = "forca"
    RISK = "risco"
    ALERT = "alerta"
    BLOCK = "bloqueio"
    LIMITATION = "limitacao"
    DIVERGENCE = "divergencia"


class FindingNature(str, Enum):
    OBSERVED = "observado"
    CALCULATED = "calculado"
    DERIVED = "derivado"
    HYPOTHESIS = "hipotese"
    INTERPRETATION = "interpretacao"
    EXTERNAL_EVIDENCE = "evidencia_externa"


class Party(ContractModel):
    nome: str | None = None
    cnpj: str | None = None

    @field_validator("nome", "cnpj", mode="before")
    @classmethod
    def blank_as_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class OperationTerm(ContractModel):
    valor: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    unidade: str


class Operation(ContractModel):
    natureza: str | None = None
    finalidade: str | None = None
    valor: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    prazo: OperationTerm | None = None
    moeda: Annotated[str, Field(min_length=3, max_length=3)] = "BRL"

    @field_validator("moeda")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class PeriodRange(ContractModel):
    inicio: Year | None = None
    fim: Year | None = None
    exercicios: list[Year] = Field(default_factory=list)
    fonte: str | None = None
    status: AvailabilityStatus = AvailabilityStatus.UNAVAILABLE

    @model_validator(mode="after")
    def validate_period(self) -> "PeriodRange":
        if (self.inicio is None) != (self.fim is None):
            raise ValueError("início e fim do período devem ser informados em conjunto")
        if self.inicio is not None and self.fim is not None:
            if self.inicio > self.fim:
                raise ValueError("início do período não pode ser posterior ao fim")
            if self.status is AvailabilityStatus.UNAVAILABLE:
                raise ValueError("período informado não pode ter status não informado")
        if self.exercicios != sorted(set(self.exercicios)):
            raise ValueError("exercícios devem ser únicos e estar em ordem cronológica")
        if self.exercicios:
            if self.inicio != self.exercicios[0] or self.fim != self.exercicios[-1]:
                raise ValueError("início e fim devem coincidir com os exercícios extremos")
        return self


class PeriodDivergence(ContractModel):
    codigo: str
    descricao: str
    impacto: str
    requer_confirmacao: bool = True


class Periods(ContractModel):
    cadastral: PeriodRange
    analisado: PeriodRange
    divergencias: list[PeriodDivergence] = Field(default_factory=list)

    @model_validator(mode="after")
    def analyzed_period_is_required(self) -> "Periods":
        if (
            self.analisado.status is not AvailabilityStatus.AVAILABLE
            or not self.analisado.exercicios
        ):
            raise ValueError("o período efetivamente analisado deve estar disponível")
        return self


class Identification(ContractModel):
    tomador: Party
    concedente: Party
    operacao: Operation
    periodos: Periods


class DataPoint(ContractModel):
    ponto_id: str
    campo: str
    valor: Scalar | None
    exercicio: Year | None = None
    unidade: str | None = None
    fonte: str
    natureza: DataNature
    status: AvailabilityStatus

    @model_validator(mode="after")
    def value_matches_status(self) -> "DataPoint":
        if self.valor is None and self.status is AvailabilityStatus.AVAILABLE:
            raise ValueError("valor ausente não pode ser marcado como disponível")
        if self.valor is not None and self.status is not AvailabilityStatus.AVAILABLE:
            raise ValueError("valor presente deve ser marcado como disponível")
        return self


class TraceabilityRecord(ContractModel):
    registro_id: str
    exercicio: Year
    conta: str
    valor_reportado: Scalar | None = None
    valor_proposto: Scalar | None = None
    valor_utilizado: Scalar | None = None
    alterado: bool
    origem_valor: str
    evento_id: str | None = None


class MissingCalculation(ContractModel):
    exercicio: Year | None = None
    indicador: str
    motivo: str
    dependencias: list[str] = Field(default_factory=list)


class AccountingData(ContractModel):
    reportados: list[DataPoint] = Field(default_factory=list)
    propostos: list[DataPoint] = Field(default_factory=list)
    utilizados: list[DataPoint] = Field(default_factory=list)
    derivados: list[DataPoint] = Field(default_factory=list)
    indices: list[DataPoint] = Field(default_factory=list)
    notas: list[DataPoint] = Field(default_factory=list)
    nao_calculados: list[MissingCalculation] = Field(default_factory=list)
    rastreabilidade: list[TraceabilityRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_points(self) -> "AccountingData":
        for collection_name in (
            "reportados",
            "propostos",
            "utilizados",
            "derivados",
            "indices",
            "notas",
        ):
            collection = getattr(self, collection_name)
            keys = [(item.campo, item.exercicio) for item in collection]
            if len(keys) != len(set(keys)):
                raise ValueError(f"pontos duplicados em {collection_name}")
        return self


class QualitySummary(ContractModel):
    apto_score: bool = False
    apto_calculo: bool
    apto_decisao: bool
    score_provisorio: bool
    status: str
    classificacao_uso: str
    indice_confiabilidade: Ratio | None = None
    classificacao_confiabilidade: str | None = None
    ocorrencias_criticas: int = 0
    ocorrencias_aviso: int = 0
    correcoes_aplicadas: int = 0
    correcoes_pendentes_confirmacao: int = 0
    alertas_vies_alto_critico: int = 0
    alertas_bloqueadores_decisao: int = 0


class ReliabilityComponent(ContractModel):
    componente: str
    nota: Ratio | None = None
    peso: Ratio
    contribuicao: Ratio | None = None


class QualityOccurrence(ContractModel):
    ocorrencia_id: str
    origem: str
    severidade: str
    tipo: str
    conta: str | None = None
    exercicios: list[Year] = Field(default_factory=list)
    detalhe: str
    bloqueia_calculo: bool = False
    bloqueia_decisao: bool = False
    bloqueia_score: bool = False


class BiasAlert(ContractModel):
    alerta_id: str
    severidade: str
    categoria: str
    exercicio: Year | None = None
    conta: str | None = None
    valor_referencia: FiniteFloat | None = None
    valor_observado: FiniteFloat | None = None
    metrica: str | None = None
    limiar: FiniteFloat | None = None
    materialidade_pct_ativo: FiniteFloat | None = None
    risco_vies: str | None = None
    impacto_provavel: str | None = None
    tratamento_modelo: str | None = None
    acao_recomendada: str | None = None
    bloqueia_decisao: bool = False


class CorrectionRecord(ContractModel):
    evento_id: str
    data_hora: datetime | None = None
    etapa: str | None = None
    acao: str
    status_acao: str | None = None
    exercicio: Year | None = None
    conta: str | None = None
    valor_original: FiniteFloat | None = None
    valor_proposto: FiniteFloat | None = None
    valor_utilizado: FiniteFloat | None = None
    delta_absoluto: FiniteFloat | None = None
    delta_percentual: FiniteFloat | None = None
    materialidade_pct_ativo: FiniteFloat | None = None
    regra_id: str | None = None
    regra_descricao: str | None = None
    evidencia: str | None = None
    confianca: Ratio | None = None
    potencial_vies: str | None = None
    indicadores_afetados: list[str] = Field(default_factory=list)
    requer_confirmacao: bool = False
    confirmado: bool = False
    bloqueia_calculo: bool = False
    bloqueia_decisao: bool = False
    fonte: str | None = None
    responsavel: str | None = None


class Quality(ContractModel):
    resumo: QualitySummary
    componentes_confiabilidade: list[ReliabilityComponent] = Field(default_factory=list)
    ocorrencias: list[QualityOccurrence] = Field(default_factory=list)
    alertas: list[BiasAlert] = Field(default_factory=list)
    correcoes: list[CorrectionRecord] = Field(default_factory=list)


class MethodScore(ContractModel):
    nucleo_eo_antes_prejuizo: Score | None = None
    multiplicador_eo: Ratio | None = None
    nucleo_eo: Score | None = None
    cobertura_eo: Ratio | None = None
    nucleo_fp_antes_prejuizo: Score | None = None
    multiplicador_fp: Ratio | None = None
    nucleo_fp: Score | None = None
    cobertura_fp: Ratio | None = None
    geometrico: Score | None = None
    gargalo: Score | None = None
    pos_gargalo: Score | None = None


class TemporalComponent(ContractModel):
    indicador: str
    nivel_atual: Score | None = None
    dinamica_temporal: Score | None = None
    resiliencia: Score | None = None
    nota_temporal: Score | None = None
    cobertura_temporal: Ratio | None = None


class ScoreContribution(ContractModel):
    metodo: str
    nucleo: str
    indicador: str
    nota_temporal: Score | None = None
    peso_no_nucleo: Ratio | None = None
    contribuicao_nucleo_pontos: FiniteFloat | None = None
    cobertura_temporal: Ratio | None = None


class PrudentialCap(ContractModel):
    regra_id: str
    valor_observado: FiniteFloat
    limiar: FiniteFloat
    teto: Score
    justificativa: str


class PcaDiagnostic(ContractModel):
    nucleo: str
    status: str
    variaveis_ativas: int | None = None
    componentes: int | None = None
    variancia_pc1: Ratio | None = None
    variancia_pc2: Ratio | None = None
    participacao_adaptativa: Ratio | None = None
    distancia_l1_media: FiniteFloat | None = None
    similaridade_cosseno_media: Ratio | None = None
    maior_peso_pca_puro: Ratio | None = None
    n_efetivo_pesos: FiniteFloat | None = None
    fonte: str | None = None


class PcaWeight(ContractModel):
    nucleo: str
    indicador: str
    peso_adaptativo: Ratio | None = None
    peso_fixo: Ratio | None = None


class FinScoreData(ContractModel):
    prudencial: Score | None = None
    prudencial_pre_cap: Score | None = None
    estrutural: MethodScore
    adaptativo: MethodScore
    divergencia_metodos: FiniteFloat | None = None
    cap_aplicavel: Score | None = None
    faixa_incerteza_inferior: Score | None = None
    faixa_incerteza_superior: Score | None = None
    exercicios_prejuizo_liquido: int = 0
    multiplicador_prejuizo_recorrente: Ratio | None = None
    natureza_resultado: str | None = None
    utilizavel_decisao: bool
    componentes_temporais: list[TemporalComponent] = Field(default_factory=list)
    contribuicoes: list[ScoreContribution] = Field(default_factory=list)
    caps: list[PrudentialCap] = Field(default_factory=list)
    diagnosticos_pca: list[PcaDiagnostic] = Field(default_factory=list)
    pesos_pca: list[PcaWeight] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_uncertainty_interval(self) -> "FinScoreData":
        if (
            self.faixa_incerteza_inferior is not None
            and self.faixa_incerteza_superior is not None
            and self.faixa_incerteza_inferior > self.faixa_incerteza_superior
        ):
            raise ValueError("faixa de incerteza invertida")
        return self


class DeterministicScenario(ContractModel):
    nome: str
    descricao: str | None = None
    status: str
    flags: list[str] = Field(default_factory=list)
    premissa_excesso_fontes: str | None = None
    financiamento_adicional_ultimo_ano: FiniteFloat | None = None
    excesso_fontes_ultimo_ano: FiniteFloat | None = None
    ativo_residual_ultimo_ano: FiniteFloat | None = None
    vinculo_juros_divida_ultimo_ano: str | None = None
    margem_liquida_ultimo_ano: FiniteFloat | None = None
    nucleo_eo: Score | None = None
    nucleo_fp: Score | None = None
    finscore_prudencial: Score | None = None
    monotonicidade_global: bool | None = None
    status_monotonicidade: str | None = None


class ThresholdFrequency(ContractModel):
    corte: Score
    frequencia: Ratio | None = None


class SimulationSummary(ContractModel):
    abordagem: str
    metodo: str
    numero_trajetorias: int
    observado: Score | None = None
    media: Score | None = None
    mediana: Score | None = None
    moda_estimada: Score | None = None
    desvio_padrao: FiniteFloat | None = None
    minimo: Score | None = None
    p05: Score | None = None
    p10: Score | None = None
    p25: Score | None = None
    p75: Score | None = None
    p90: Score | None = None
    p95: Score | None = None
    maximo: Score | None = None
    frequencias: list[ThresholdFrequency] = Field(default_factory=list)


class SensitivityRecord(ContractModel):
    abordagem: str
    score: str
    conta: str
    correlacao_spearman: FiniteFloat | None = None
    impacto_absoluto: Ratio | None = None


class ShockAmplitude(ContractModel):
    conta: str
    natureza_simulacao: str
    amplitude_declarada: Ratio | None = None
    choque_maximo_observado: NonNegativeFloat | None = None
    dentro_limite_declarado: bool | None = None


class SimulationDiagnostic(ContractModel):
    abordagem: str
    tentativas: int | None = None
    rejeitados: int | None = None
    taxa_rejeicao: Ratio | None = None
    limite_taxa_rejeicao: Ratio | None = None
    status_rejeicao: str | None = None
    valida_para_interpretacao: bool | None = None
    drivers_fora_limite: int | None = None


class MonteCarloComparison(ContractModel):
    metodo: str
    media_independente: Score | None = None
    media_correlacionada: Score | None = None
    delta_media: FiniteFloat | None = None
    mediana_independente: Score | None = None
    mediana_correlacionada: Score | None = None
    delta_mediana: FiniteFloat | None = None
    desvio_independente: FiniteFloat | None = None
    desvio_correlacionado: FiniteFloat | None = None
    p05_independente: Score | None = None
    p05_correlacionado: Score | None = None
    p95_independente: Score | None = None
    p95_correlacionado: Score | None = None
    rejeicao_independente: Ratio | None = None
    rejeicao_correlacionada: Ratio | None = None


class Scenarios(ContractModel):
    deterministicos: list[DeterministicScenario] = Field(default_factory=list)
    resumos_simulacao: list[SimulationSummary] = Field(default_factory=list)
    sensibilidade: list[SensitivityRecord] = Field(default_factory=list)
    amplitudes: list[ShockAmplitude] = Field(default_factory=list)
    diagnosticos: list[SimulationDiagnostic] = Field(default_factory=list)
    comparacao_monte_carlo: list[MonteCarloComparison] = Field(default_factory=list)


class SerasaEvidence(ContractModel):
    score: Score | None = None
    data_consulta: str | None = None
    status: str
    divergencia_pontos: FiniteFloat | None = None
    nivel_divergencia: str | None = None
    direcao: str | None = None
    restricao_grave: bool = False
    cronologia_valida: bool | None = None
    alerta_temporal: str | None = None


class SpringateEvidence(ContractModel):
    exercicio: Year
    componente_a_ccl_at: FiniteFloat | None = None
    componente_b_ebit_at: FiniteFloat | None = None
    componente_c_ebt_pc: FiniteFloat | None = None
    componente_d_receita_at: FiniteFloat | None = None
    score: FiniteFloat | None = None
    classificacao: str
    observacao: str | None = None


class FleurietEvidence(ContractModel):
    exercicio: Year
    ativo_circulante_operacional: FiniteFloat | None = None
    passivo_circulante_operacional: FiniteFloat | None = None
    necessidade_capital_giro: FiniteFloat | None = None
    ativo_nao_circulante: FiniteFloat | None = None
    capital_giro: FiniteFloat | None = None
    saldo_tesouraria: FiniteFloat | None = None
    perfil_sinais: str | None = None
    diagnostico: str


class SupplementaryEvidence(ContractModel):
    serasa: SerasaEvidence
    springate: list[SpringateEvidence] = Field(default_factory=list)
    fleuriet: list[FleurietEvidence] = Field(default_factory=list)


class BlockingReason(ContractModel):
    bloqueio_id: str
    titulo: str
    motivo: str
    impacto: str
    providencia: str
    origem: str


class GuaranteeRecommendation(ContractModel):
    aplicavel: bool
    recomendada: bool
    motivos: list[str] = Field(default_factory=list)
    justificativa: str | None = None
    modalidade: str | None = None
    valor_realizavel: FiniteFloat | None = None
    cobertura_minima: FiniteFloat | None = None
    exequibilidade_juridica: str | None = None

    @model_validator(mode="after")
    def validate_recommendation(self) -> "GuaranteeRecommendation":
        if self.recomendada and not self.aplicavel:
            raise ValueError("garantia não pode ser recomendada quando não aplicável")
        return self


class FinScoreRecommendation(ContractModel):
    codigo: RecommendationCode
    rotulo: str
    regra_id: str
    versao_politica: str
    apto_decisao: bool
    finscore_prudencial: Score | None = None
    faixa: str
    confiabilidade: Ratio | None = None
    fundamentos: list[str] = Field(default_factory=list)
    bloqueios: list[BlockingReason] = Field(default_factory=list)
    providencias: list[str] = Field(default_factory=list)
    garantia: GuaranteeRecommendation

    @model_validator(mode="after")
    def validate_label_and_eligibility(self) -> "FinScoreRecommendation":
        if self.rotulo != RECOMMENDATION_LABELS[self.codigo]:
            raise ValueError("rótulo da recomendação não corresponde ao código")
        if not self.apto_decisao and self.codigo is not RecommendationCode.INCONSISTENT_DATA:
            raise ValueError("resultado não apto deve produzir Dados inconsistentes")
        if self.codigo is RecommendationCode.INCONSISTENT_DATA and not self.bloqueios:
            raise ValueError("Dados inconsistentes exige ao menos um bloqueio estruturado")
        return self


class HumanDecision(ContractModel):
    resultado: RecommendationCode
    justificativa: Annotated[str, Field(min_length=3)]
    responsavel: Annotated[str, Field(min_length=2)]
    registrado_em: datetime


class GovernanceDivergence(ContractModel):
    origem: Literal["recomendacao_finscore", "manifestacao_analista"]
    resultado_origem: RecommendationCode
    destino: Literal["manifestacao_analista", "decisao_alcada"]
    resultado_destino: RecommendationCode
    justificativa: Annotated[str, Field(min_length=3)]
    responsavel: Annotated[str, Field(min_length=2)]
    registrado_em: datetime


class GovernanceAuditEvent(ContractModel):
    evento_id: Annotated[str, Field(min_length=8)]
    etapa: GovernanceStage
    acao: GovernanceAction
    resultado: RecommendationCode
    justificativa: Annotated[str, Field(min_length=3)]
    responsavel: Annotated[str, Field(min_length=2)]
    registrado_em: datetime


class Governance(ContractModel):
    recomendacao_finscore: FinScoreRecommendation
    manifestacao_analista: HumanDecision | None = None
    decisao_alcada: HumanDecision | None = None
    divergencias: list[GovernanceDivergence] = Field(default_factory=list)
    historico: list[GovernanceAuditEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def divergent_decisions_are_justified(self) -> "Governance":
        recommendation = self.recomendacao_finscore.codigo
        analyst = self.manifestacao_analista
        final = self.decisao_alcada
        expected_pairs: set[tuple[str, RecommendationCode, str, RecommendationCode]] = set()
        if analyst is not None and analyst.resultado != recommendation:
            expected_pairs.add(
                ("recomendacao_finscore", recommendation, "manifestacao_analista", analyst.resultado)
            )
        if final is not None:
            origin_name = "manifestacao_analista" if analyst is not None else "recomendacao_finscore"
            origin_result = analyst.resultado if analyst is not None else recommendation
            if final.resultado != origin_result:
                expected_pairs.add(
                    (origin_name, origin_result, "decisao_alcada", final.resultado)
                )
        recorded = {
            (item.origem, item.resultado_origem, item.destino, item.resultado_destino)
            for item in self.divergencias
        }
        missing = expected_pairs - recorded
        if missing:
            raise ValueError("divergência de governança sem justificativa registrada")
        unexpected = recorded - expected_pairs
        if unexpected:
            raise ValueError("registro de divergência não corresponde às posições vigentes")
        if len(recorded) != len(self.divergencias):
            raise ValueError("registro de divergência duplicado")

        event_ids = [item.evento_id for item in self.historico]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("evento de governança duplicado")
        recommendation_events = [
            item
            for item in self.historico
            if item.etapa is GovernanceStage.RECOMMENDATION
        ]
        if recommendation_events:
            if len(recommendation_events) != 1:
                raise ValueError("a recomendação FinScore deve ter um único evento inicial")
            event = recommendation_events[0]
            if (
                self.historico[0] is not event
                or event.acao is not GovernanceAction.REGISTERED
                or event.resultado != recommendation
            ):
                raise ValueError("evento inicial diverge da recomendação FinScore")

        analyst_events = [
            item for item in self.historico if item.etapa is GovernanceStage.ANALYST
        ]
        if analyst is None and analyst_events:
            raise ValueError("histórico contém manifestação sem posição vigente")
        if analyst is not None:
            if not analyst_events:
                raise ValueError("manifestação do analista ausente do histórico")
            latest_analyst = analyst_events[-1]
            if (
                latest_analyst.resultado != analyst.resultado
                or latest_analyst.justificativa != analyst.justificativa
                or latest_analyst.responsavel != analyst.responsavel
                or latest_analyst.registrado_em != analyst.registrado_em
            ):
                raise ValueError("manifestação vigente diverge do histórico")

        authority_events = [
            item for item in self.historico if item.etapa is GovernanceStage.AUTHORITY
        ]
        if final is None and authority_events:
            if authority_events[-1].acao is not GovernanceAction.INVALIDATED:
                raise ValueError("decisão da alçada sem posição vigente ou invalidação")
        if final is not None:
            if not authority_events:
                raise ValueError("decisão da alçada ausente do histórico")
            latest_authority = authority_events[-1]
            if (
                latest_authority.acao is GovernanceAction.INVALIDATED
                or latest_authority.resultado != final.resultado
                or latest_authority.justificativa != final.justificativa
                or latest_authority.responsavel != final.responsavel
                or latest_authority.registrado_em != final.registrado_em
            ):
                raise ValueError("decisão da alçada vigente diverge do histórico")
        return self


class FindingEvidence(ContractModel):
    origem: str
    campo: str
    valor: Scalar | None = None
    exercicio: Year | None = None
    unidade: str | None = None


class Finding(ContractModel):
    achado_id: str
    categoria: FindingCategory
    natureza: FindingNature
    titulo: str
    evidencias: list[FindingEvidence] = Field(default_factory=list)
    efeito_metodologico: str | None = None
    impacto_credito: str | None = None
    bloqueia_decisao: bool = False
    providencia: str | None = None

    @model_validator(mode="after")
    def validate_finding(self) -> "Finding":
        if not self.evidencias:
            raise ValueError("achado deve conter ao menos uma evidência")
        if self.bloqueia_decisao and self.categoria is not FindingCategory.BLOCK:
            raise ValueError("achado bloqueador deve usar a categoria bloqueio")
        if self.categoria is FindingCategory.BLOCK:
            if not self.bloqueia_decisao:
                raise ValueError("categoria bloqueio exige bloqueia_decisao=true")
            if not self.providencia:
                raise ValueError("achado bloqueador exige providência")
        if self.categoria in {
            FindingCategory.RISK,
            FindingCategory.ALERT,
            FindingCategory.BLOCK,
            FindingCategory.DIVERGENCE,
        } and not self.impacto_credito:
            raise ValueError("achado de atenção exige impacto analítico")
        return self


class FunctionalMetadata(ContractModel):
    processado_em: datetime
    numero_simulacoes: int
    semente_simulacao: int
    versao_metodologia: str
    versao_contrato_motor: str
    status_reproducao: str


class RestrictedTechnicalMetadata(ContractModel):
    nome_interno_motor: str | None = None
    versao_codigo: str
    hash_codigo: str
    semente: int
    hash_dados_reportados: str
    hash_dados_utilizados: str
    origem_analise_id: str


class ParecerData(ContractModel):
    schema_versao: str = PARECER_DATA_SCHEMA_VERSION
    analise_id: Annotated[str, Field(min_length=8, max_length=80)]
    identificacao: Identification
    governanca: Governance
    dados: AccountingData
    qualidade: Quality
    finscore: FinScoreData
    cenarios: Scenarios
    evidencias_suplementares: SupplementaryEvidence
    achados: list[Finding] = Field(default_factory=list)
    metadados_funcionais: FunctionalMetadata
    metadados_tecnicos_restritos: RestrictedTechnicalMetadata

    @field_validator("schema_versao")
    @classmethod
    def supported_schema(cls, value: str) -> str:
        if value != PARECER_DATA_SCHEMA_VERSION:
            raise ValueError(
                f"schema_versao incompatível: esperado {PARECER_DATA_SCHEMA_VERSION}"
            )
        return value

    @model_validator(mode="after")
    def validate_cross_section_invariants(self) -> "ParecerData":
        recommendation = self.governanca.recomendacao_finscore
        quality = self.qualidade.resumo

        if recommendation.apto_decisao != quality.apto_decisao:
            raise ValueError("aptidão diverge entre qualidade e recomendação")
        if recommendation.finscore_prudencial != self.finscore.prudencial:
            raise ValueError("FinScore diverge entre cálculo e recomendação")
        if recommendation.confiabilidade != quality.indice_confiabilidade:
            raise ValueError("confiabilidade diverge entre qualidade e recomendação")
        if recommendation.garantia.aplicavel != (
            recommendation.codigo is RecommendationCode.APPROVE
        ):
            raise ValueError("aplicabilidade da garantia diverge da recomendação")
        if self.finscore.utilizavel_decisao != quality.apto_decisao:
            raise ValueError("uso decisório diverge entre FinScore e qualidade")

        analyzed_years = set(self.identificacao.periodos.analisado.exercicios)
        for collection in (
            self.dados.reportados,
            self.dados.utilizados,
            self.dados.derivados,
            self.dados.indices,
            self.dados.notas,
        ):
            if any(item.exercicio not in analyzed_years for item in collection):
                raise ValueError("dado anual fora do período efetivamente analisado")

        if len({item.achado_id for item in self.achados}) != len(self.achados):
            raise ValueError("achado_id duplicado")
        if not math.isfinite(float(self.metadados_funcionais.numero_simulacoes)):
            raise ValueError("número de simulações inválido")
        return self


__all__ = [
    "AvailabilityStatus",
    "DataNature",
    "Finding",
    "FindingCategory",
    "FindingEvidence",
    "FindingNature",
    "Governance",
    "GovernanceAction",
    "GovernanceAuditEvent",
    "GovernanceDivergence",
    "GovernanceStage",
    "HumanDecision",
    "PARECER_DATA_SCHEMA_VERSION",
    "ParecerData",
    "RecommendationCode",
]
