"""Livro determinístico de evidências para o parecer de crédito."""

from __future__ import annotations

from collections import defaultdict
import math
import re
from statistics import mean
from typing import Iterable

try:  # Execução Streamlit, com app_front no sys.path.
    from components.parecer_data_schema import (
        Finding,
        FindingCategory,
        FindingEvidence,
        FindingNature,
        ParecerData,
        ScoreContribution,
    )
except ModuleNotFoundError:  # Importação como pacote nos testes.
    from app_front.components.parecer_data_schema import (
        Finding,
        FindingCategory,
        FindingEvidence,
        FindingNature,
        ParecerData,
        ScoreContribution,
    )


INDICATOR_LABELS = {
    "crescimento_receita": "Crescimento da receita",
    "margem_bruta": "Margem bruta",
    "margem_ebit": "Margem EBIT",
    "margem_liquida": "Margem líquida",
    "giro_ativo": "Giro do ativo",
    "ciclo_conversao_caixa": "Ciclo de conversão de caixa",
    "capitalizacao": "Capitalização",
    "liquidez_corrente": "Liquidez corrente",
    "liquidez_seca": "Liquidez seca",
    "ccl_ativo": "Capital circulante líquido sobre o ativo",
    "ncg_operacional_ativo": "Necessidade de capital de giro sobre o ativo",
    "divida_liquida_ativo": "Dívida líquida sobre o ativo",
    "cobertura_juros": "Cobertura de juros",
    "composicao_endividamento": "Composição do endividamento",
    "penalidade_prejuizo_recorrente": "Penalidade por prejuízo recorrente",
}

ACCOUNT_LABELS = {
    "r_Receita_Liquida": "Receita líquida",
    "r_Receita_Total": "Receita total",
    "r_Lucro_Liquido": "Lucro líquido",
    "p_Ativo_Total": "Ativo total",
    "p_Patrimonio_Liquido": "Patrimônio líquido",
    "d_Divida_Bruta": "Dívida bruta",
    "d_Divida_Liquida": "Dívida líquida",
    "d_EBIT": "EBIT",
}


def _slug(value: object, limit: int = 44) -> str:
    text = re.sub(r"[^A-Z0-9]+", "-", str(value or "").upper()).strip("-")
    return (text or "SEM-ID")[:limit].rstrip("-")


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _evidence(
    origin: str,
    field: str,
    value: object = None,
    *,
    year: int | None = None,
    unit: str | None = None,
) -> FindingEvidence:
    return FindingEvidence(
        origem=origin,
        campo=field,
        valor=value,
        exercicio=year,
        unidade=unit,
    )


def _blocking_findings(contract: ParecerData) -> list[Finding]:
    result: list[Finding] = []
    for blocker in contract.governanca.recomendacao_finscore.bloqueios:
        result.append(
            Finding(
                achado_id=f"ACH-BLOQ-{_slug(blocker.bloqueio_id)}",
                categoria=FindingCategory.BLOCK,
                natureza=FindingNature.CALCULATED,
                titulo=blocker.titulo,
                evidencias=[
                    _evidence(blocker.origem, "motivo", blocker.motivo),
                    _evidence(blocker.origem, "impacto", blocker.impacto),
                ],
                efeito_metodologico="Impede o uso decisório do resultado calculado.",
                impacto_credito=blocker.impacto,
                bloqueia_decisao=True,
                providencia=blocker.providencia,
            )
        )
    return result


def _result_findings(contract: ParecerData) -> list[Finding]:
    quality = contract.qualidade.resumo
    recommendation = contract.governanca.recomendacao_finscore
    result = [
        Finding(
            achado_id="ACH-RES-QUALIDADE",
            categoria=FindingCategory.RESULT,
            natureza=FindingNature.CALCULATED,
            titulo="Qualidade e aptidão da informação",
            evidencias=[
                _evidence("qualidade.resumo", "apto_calculo", quality.apto_calculo),
                _evidence("qualidade.resumo", "apto_decisao", quality.apto_decisao),
                _evidence("qualidade.resumo", "indice_confiabilidade", quality.indice_confiabilidade, unit="proporcao"),
                _evidence("qualidade.resumo", "classificacao_confiabilidade", quality.classificacao_confiabilidade),
                _evidence("qualidade.resumo", "classificacao_uso", quality.classificacao_uso),
            ],
            efeito_metodologico="Controla o uso do resultado e preserva a separação entre cálculo e aptidão decisória.",
            impacto_credito="Define a extensão em que o resultado pode sustentar a recomendação FinScore.",
        ),
        Finding(
            achado_id="ACH-RES-FINSCORE",
            categoria=FindingCategory.RESULT,
            natureza=FindingNature.CALCULATED,
            titulo="Formação e resultado prudencial do FinScore",
            evidencias=[
                _evidence("finscore", "prudencial", contract.finscore.prudencial, unit="pontos"),
                _evidence("finscore", "prudencial_pre_cap", contract.finscore.prudencial_pre_cap, unit="pontos"),
                _evidence("finscore.estrutural", "nucleo_eo", contract.finscore.estrutural.nucleo_eo, unit="pontos"),
                _evidence("finscore.estrutural", "nucleo_fp", contract.finscore.estrutural.nucleo_fp, unit="pontos"),
                _evidence("finscore.estrutural", "pos_gargalo", contract.finscore.estrutural.pos_gargalo, unit="pontos"),
                _evidence("finscore.adaptativo", "nucleo_eo", contract.finscore.adaptativo.nucleo_eo, unit="pontos"),
                _evidence("finscore.adaptativo", "nucleo_fp", contract.finscore.adaptativo.nucleo_fp, unit="pontos"),
                _evidence("finscore.adaptativo", "pos_gargalo", contract.finscore.adaptativo.pos_gargalo, unit="pontos"),
                _evidence("governanca.recomendacao_finscore", "codigo", recommendation.codigo.value),
                _evidence("governanca.recomendacao_finscore", "garantia_recomendada", recommendation.garantia.recomendada),
            ],
            efeito_metodologico="Mantém núcleos, métodos, gargalo, caps e recomendação como grandezas distintas.",
            impacto_credito="Consolida o suporte quantitativo à análise sem representar PD ou rating regulatório.",
        ),
    ]

    notes = {(item.campo, item.exercicio): item for item in contract.dados.notas}
    temporal = {item.indicador: item for item in contract.finscore.componentes_temporais}
    for indicator in sorted({item.campo for item in contract.dados.indices}):
        points = sorted(
            [item for item in contract.dados.indices if item.campo == indicator],
            key=lambda item: item.exercicio or 0,
        )
        evidences: list[FindingEvidence] = []
        for point in points:
            evidences.append(
                _evidence(
                    point.fonte,
                    indicator,
                    point.valor,
                    year=point.exercicio,
                    unit=point.unidade,
                )
            )
            note = notes.get((indicator, point.exercicio))
            if note is not None:
                evidences.append(
                    _evidence(
                        note.fonte,
                        f"nota_{indicator}",
                        note.valor,
                        year=note.exercicio,
                        unit=note.unidade,
                    )
                )
        component = temporal.get(indicator)
        if component is not None:
            evidences.extend(
                [
                    _evidence("finscore.componentes_temporais", "nota_temporal", component.nota_temporal, unit="pontos_0_100"),
                    _evidence("finscore.componentes_temporais", "cobertura_temporal", component.cobertura_temporal, unit="proporcao"),
                ]
            )
        result.append(
            Finding(
                achado_id=f"ACH-RES-IND-{_slug(indicator)}",
                categoria=FindingCategory.RESULT,
                natureza=FindingNature.CALCULATED,
                titulo=f"Trajetória calculada: {INDICATOR_LABELS.get(indicator, indicator.replace('_', ' '))}",
                evidencias=evidences,
                efeito_metodologico="Série de índice, notas anuais e síntese temporal preservadas por exercício.",
                impacto_credito="Disponibiliza a trajetória para interpretação conjunta, sem corte decisório adicional.",
            )
        )

    account_points = [*contract.dados.utilizados, *contract.dados.derivados]
    for account, label in ACCOUNT_LABELS.items():
        points = sorted(
            [item for item in account_points if item.campo == account],
            key=lambda item: item.exercicio or 0,
        )
        if not points:
            continue
        result.append(
            Finding(
                achado_id=f"ACH-RES-CONTA-{_slug(account)}",
                categoria=FindingCategory.RESULT,
                natureza=(
                    FindingNature.DERIVED
                    if account.startswith("d_")
                    else FindingNature.OBSERVED
                ),
                titulo=f"Trajetória contábil: {label}",
                evidencias=[
                    _evidence(
                        point.fonte,
                        point.campo,
                        point.valor,
                        year=point.exercicio,
                        unit=point.unidade,
                    )
                    for point in points
                ],
                efeito_metodologico="Série preservada nos valores efetivamente utilizados no cálculo.",
                impacto_credito="Oferece contexto de porte e trajetória para a leitura dos índices calculados.",
            )
        )
    return result


def _quality_findings(contract: ParecerData) -> list[Finding]:
    result: list[Finding] = []
    for occurrence in contract.qualidade.ocorrencias:
        if occurrence.bloqueia_decisao or occurrence.bloqueia_calculo:
            continue
        years = occurrence.exercicios or [None]
        result.append(
            Finding(
                achado_id=f"ACH-LIM-{_slug(occurrence.ocorrencia_id)}",
                categoria=FindingCategory.LIMITATION,
                natureza=FindingNature.OBSERVED,
                titulo=f"Limitação informacional: {occurrence.tipo.replace('_', ' ')}",
                evidencias=[
                    _evidence(
                        occurrence.origem,
                        occurrence.conta or occurrence.tipo,
                        occurrence.detalhe,
                        year=year,
                    )
                    for year in years
                ],
                efeito_metodologico=(
                    "Ocorrência preservada sem conversão de ausência em zero; "
                    "não bloqueia isoladamente o cálculo ou a recomendação."
                ),
                impacto_credito=(
                    "Limita a abrangência da leitura da conta indicada, sem constituir "
                    "impedimento decisório isolado."
                ),
                providencia="Obter a informação na fonte contábil, quando disponível.",
            )
        )

    for alert in contract.qualidade.alertas:
        if alert.bloqueia_decisao:
            continue
        field = alert.metrica or alert.conta or alert.categoria
        evidence = [
            _evidence(
                f"qualidade.alertas:{alert.alerta_id}",
                field,
                alert.valor_observado,
                year=alert.exercicio,
            )
        ]
        if alert.valor_referencia is not None:
            evidence.append(
                _evidence(
                    f"qualidade.alertas:{alert.alerta_id}",
                    "valor_referencia",
                    alert.valor_referencia,
                    year=alert.exercicio,
                )
            )
        result.append(
            Finding(
                achado_id=f"ACH-ALT-{_slug(alert.alerta_id)}",
                categoria=FindingCategory.ALERT,
                natureza=FindingNature.OBSERVED,
                titulo=(alert.metrica or alert.conta or alert.categoria).replace("_", " "),
                evidencias=evidence,
                efeito_metodologico=alert.tratamento_modelo,
                impacto_credito=(
                    alert.impacto_provavel
                    or "O alerta requer leitura conjunta, mas não bloqueia isoladamente a recomendação."
                ),
                providencia=alert.acao_recomendada,
            )
        )

    for correction in contract.qualidade.correcoes:
        if not correction.requer_confirmacao or correction.confirmado:
            continue
        result.append(
            Finding(
                achado_id=f"ACH-COR-{_slug(correction.evento_id)}",
                categoria=(
                    FindingCategory.BLOCK
                    if correction.bloqueia_decisao or correction.bloqueia_calculo
                    else FindingCategory.LIMITATION
                ),
                natureza=FindingNature.DERIVED,
                titulo=f"Confirmação pendente: {correction.conta or correction.acao}",
                evidencias=[
                    _evidence(
                        f"qualidade.correcoes:{correction.evento_id}",
                        "valor_original",
                        correction.valor_original,
                        year=correction.exercicio,
                        unit="BRL",
                    ),
                    _evidence(
                        f"qualidade.correcoes:{correction.evento_id}",
                        "valor_utilizado",
                        correction.valor_utilizado,
                        year=correction.exercicio,
                        unit="BRL",
                    ),
                ],
                efeito_metodologico=correction.regra_descricao,
                impacto_credito=(
                    "O tratamento ainda depende de confirmação documental e deve ser lido "
                    "com a restrição indicada no registro de auditoria."
                ),
                bloqueia_decisao=correction.bloqueia_decisao or correction.bloqueia_calculo,
                providencia="Confirmar o tratamento com a documentação contábil de origem.",
            )
        )
    return result


def _missing_calculation_findings(contract: ParecerData) -> list[Finding]:
    result: list[Finding] = []
    ordered = sorted(
        contract.dados.nao_calculados,
        key=lambda item: (item.indicador, item.exercicio or 0, item.motivo),
    )
    for index, missing in enumerate(ordered, 1):
        result.append(
            Finding(
                achado_id=f"ACH-NCAL-{index:03d}-{_slug(missing.indicador, 28)}",
                categoria=FindingCategory.LIMITATION,
                natureza=FindingNature.CALCULATED,
                titulo=f"Indicador não calculado: {missing.indicador.replace('_', ' ')}",
                evidencias=[
                    _evidence(
                        "dados.nao_calculados",
                        missing.indicador,
                        None,
                        year=missing.exercicio,
                    )
                ],
                efeito_metodologico=missing.motivo,
                impacto_credito=(
                    "O indicador não integra a interpretação quantitativa enquanto suas "
                    "dependências permanecerem indisponíveis."
                ),
                providencia=(
                    "Disponibilizar e validar: " + ", ".join(missing.dependencias)
                    if missing.dependencias
                    else "Disponibilizar os dados requeridos e recalcular o FinScore."
                ),
            )
        )
    return result


def _contribution_evidence(items: Iterable[ScoreContribution]) -> list[FindingEvidence]:
    result: list[FindingEvidence] = []
    for item in sorted(items, key=lambda value: value.metodo):
        origin = f"finscore.contribuicoes:{item.metodo}:{item.nucleo}"
        result.extend(
            [
                _evidence(origin, "nota_temporal", item.nota_temporal, unit="pontos_0_100"),
                _evidence(origin, "peso_no_nucleo", item.peso_no_nucleo, unit="proporcao"),
                _evidence(
                    origin,
                    "contribuicao_nucleo_pontos",
                    item.contribuicao_nucleo_pontos,
                    unit="pontos",
                ),
            ]
        )
    return result


def _score_findings(contract: ParecerData) -> list[Finding]:
    grouped: dict[tuple[str, str], list[ScoreContribution]] = defaultdict(list)
    for item in contract.finscore.contribuicoes:
        grouped[(item.nucleo.upper(), item.indicador)].append(item)

    result: list[Finding] = []
    by_core: dict[str, list[tuple[str, list[ScoreContribution], float, float, float]]] = defaultdict(list)
    for (core, indicator), items in grouped.items():
        notes = [value for item in items if (value := _number(item.nota_temporal)) is not None]
        weights = [value for item in items if (value := _number(item.peso_no_nucleo)) is not None]
        contributions = [
            value
            for item in items
            if (value := _number(item.contribuicao_nucleo_pontos)) is not None
        ]
        if not notes:
            continue
        average_note = mean(notes)
        maximum_weight = max(weights, default=0.0)
        average_contribution = mean(contributions) if contributions else 0.0
        opportunity_gap = max(0.0, 100.0 - average_note) * maximum_weight
        by_core[core].append(
            (indicator, items, average_note, average_contribution, opportunity_gap)
        )

    for core, candidates in sorted(by_core.items()):
        regular = [item for item in candidates if item[0] != "penalidade_prejuizo_recorrente"]
        limiters = sorted(regular, key=lambda item: (-item[4], item[0]))[:2]
        limiter_names = {item[0] for item in limiters if item[4] > 0}
        for indicator, items, note, contribution, gap in limiters:
            if gap <= 0:
                continue
            result.append(
                Finding(
                    achado_id=f"ACH-FIN-LIM-{core}-{_slug(indicator)}",
                    categoria=FindingCategory.RISK,
                    natureza=FindingNature.CALCULATED,
                    titulo=f"Limitador relativo do núcleo {core}: {INDICATOR_LABELS.get(indicator, indicator)}",
                    evidencias=_contribution_evidence(items),
                    efeito_metodologico=(
                        f"Nota temporal média de {note:.2f}, contribuição média de "
                        f"{contribution:.2f} ponto(s) e déficit ponderado relativo de {gap:.2f}."
                    ),
                    impacto_credito=(
                        f"Entre os componentes disponíveis do núcleo {core}, o indicador apresenta "
                        "uma das maiores distâncias ponderadas em relação à contribuição máxima."
                    ),
                )
            )

        strengths = sorted(
            [item for item in regular if item[0] not in limiter_names],
            key=lambda item: (-item[3], item[0]),
        )[:2]
        for indicator, items, note, contribution, _gap in strengths:
            result.append(
                Finding(
                    achado_id=f"ACH-FIN-FOR-{core}-{_slug(indicator)}",
                    categoria=FindingCategory.STRENGTH,
                    natureza=FindingNature.CALCULATED,
                    titulo=f"Contribuição relativa ao núcleo {core}: {INDICATOR_LABELS.get(indicator, indicator)}",
                    evidencias=_contribution_evidence(items),
                    efeito_metodologico=(
                        f"Nota temporal média de {note:.2f} e contribuição média de "
                        f"{contribution:.2f} ponto(s)."
                    ),
                    impacto_credito=(
                        f"O indicador figura entre as maiores contribuições observadas no núcleo {core}; "
                        "a classificação é relativa ao conjunto analisado, não um corte externo."
                    ),
                )
            )

    penalty = grouped.get(("EO", "penalidade_prejuizo_recorrente"), [])
    if penalty:
        contributions = [
            value
            for item in penalty
            if (value := _number(item.contribuicao_nucleo_pontos)) is not None
        ]
        if contributions and min(contributions) < 0:
            result.append(
                Finding(
                    achado_id="ACH-FIN-PREJUIZO-RECORRENTE",
                    categoria=FindingCategory.RISK,
                    natureza=FindingNature.CALCULATED,
                    titulo="Penalidade por prejuízo recorrente",
                    evidencias=_contribution_evidence(penalty),
                    efeito_metodologico=(
                        f"Multiplicador prudencial aplicado: "
                        f"{contract.finscore.multiplicador_prejuizo_recorrente}."
                    ),
                    impacto_credito="A recorrência de prejuízos reduz o núcleo econômico-operacional.",
                )
            )

    for cap in contract.finscore.caps:
        result.append(
            Finding(
                achado_id=f"ACH-CAP-{_slug(cap.regra_id)}",
                categoria=FindingCategory.RISK,
                natureza=FindingNature.CALCULATED,
                titulo=cap.justificativa,
                evidencias=[
                    _evidence(f"finscore.caps:{cap.regra_id}", "valor_observado", cap.valor_observado),
                    _evidence(f"finscore.caps:{cap.regra_id}", "limiar", cap.limiar),
                    _evidence(f"finscore.caps:{cap.regra_id}", "teto", cap.teto, unit="pontos"),
                ],
                efeito_metodologico=f"Teto prudencial de {cap.teto:.2f} pontos.",
                impacto_credito="O controle limita o FinScore prudencial conforme a regra registrada.",
            )
        )
    return result


def _scenario_findings(contract: ParecerData) -> list[Finding]:
    result: list[Finding] = []
    scenarios = {item.nome.upper(): item for item in contract.cenarios.deterministicos}
    base = scenarios.get("BASE")
    severe = scenarios.get("SEVERO")
    if base and severe and base.finscore_prudencial is not None and severe.finscore_prudencial is not None:
        delta = severe.finscore_prudencial - base.finscore_prudencial
        result.append(
            Finding(
                achado_id="ACH-CEN-SEVERO",
                categoria=FindingCategory.ALERT if delta < 0 else FindingCategory.STRENGTH,
                natureza=FindingNature.HYPOTHESIS,
                titulo="Sensibilidade do FinScore no cenário severo",
                evidencias=[
                    _evidence("cenarios.deterministicos:BASE", "finscore_prudencial", base.finscore_prudencial, unit="pontos"),
                    _evidence("cenarios.deterministicos:SEVERO", "finscore_prudencial", severe.finscore_prudencial, unit="pontos"),
                    _evidence("cenarios.deterministicos:SEVERO", "delta_frente_base", delta, unit="pontos"),
                ],
                efeito_metodologico="Comparação entre hipóteses determinísticas, sem caráter preditivo.",
                impacto_credito=(
                    "O cenário severo reduz o resultado e evidencia sensibilidade às premissas de estresse."
                    if delta < 0
                    else "O resultado não se deteriora sob as premissas severas registradas."
                ),
            )
        )

    invalid_monotonicity = [
        item
        for item in contract.cenarios.deterministicos
        if item.monotonicidade_global is False
        or "NAO" in str(item.status_monotonicidade or "").upper()
    ]
    if invalid_monotonicity:
        result.append(
            Finding(
                achado_id="ACH-CEN-MONOTONICIDADE",
                categoria=FindingCategory.DIVERGENCE,
                natureza=FindingNature.HYPOTHESIS,
                titulo="Monotonicidade dos cenários não atendida",
                evidencias=[
                    _evidence(
                        f"cenarios.deterministicos:{item.nome}",
                        "status_monotonicidade",
                        item.status_monotonicidade or item.monotonicidade_global,
                    )
                    for item in invalid_monotonicity
                ],
                efeito_metodologico="A ordenação esperada entre base, adverso e severo requer revisão.",
                impacto_credito="A leitura comparativa dos cenários fica limitada até a validação das premissas.",
                providencia="Revisar premissas, vínculos contábeis e consistência dos cenários.",
            )
        )

    invalid_diagnostics = [
        item for item in contract.cenarios.diagnosticos if item.valida_para_interpretacao is False
    ]
    if invalid_diagnostics:
        result.append(
            Finding(
                achado_id="ACH-SIM-INVALIDA",
                categoria=FindingCategory.LIMITATION,
                natureza=FindingNature.HYPOTHESIS,
                titulo="Simulação indisponível para interpretação",
                evidencias=[
                    _evidence(
                        f"cenarios.diagnosticos:{item.abordagem}",
                        "taxa_rejeicao",
                        item.taxa_rejeicao,
                        unit="proporcao",
                    )
                    for item in invalid_diagnostics
                ],
                efeito_metodologico="Os resultados da simulação não devem sustentar inferências no parecer.",
                impacto_credito="A análise permanece apoiada nos dados observados e cenários determinísticos válidos.",
                providencia="Revisar os diagnósticos da simulação antes de utilizá-la.",
            )
        )
    return result


def _supplementary_findings(contract: ParecerData) -> list[Finding]:
    result: list[Finding] = []
    serasa = contract.evidencias_suplementares.serasa
    if serasa.score is None:
        result.append(
            Finding(
                achado_id="ACH-SUP-SERASA-AUSENTE",
                categoria=FindingCategory.LIMITATION,
                natureza=FindingNature.EXTERNAL_EVIDENCE,
                titulo="Serasa Score não informado",
                evidencias=[_evidence("evidencias_suplementares.serasa", "score", None)],
                efeito_metodologico="A evidência externa permanece separada e não altera o FinScore.",
                impacto_credito="A comparação externa de comportamento de crédito não está disponível.",
                providencia="Obter consulta válida, se exigida pela governança da instituição.",
            )
        )
    elif str(serasa.nivel_divergencia or "").lower() in {"relevante", "elevada"}:
        result.append(
            Finding(
                achado_id="ACH-SUP-SERASA-DIVERGENCIA",
                categoria=FindingCategory.DIVERGENCE,
                natureza=FindingNature.EXTERNAL_EVIDENCE,
                titulo="Divergência relevante entre FinScore e Serasa",
                evidencias=[
                    _evidence("evidencias_suplementares.serasa", "score", serasa.score, unit="pontos"),
                    _evidence("evidencias_suplementares.serasa", "divergencia_pontos", serasa.divergencia_pontos, unit="pontos"),
                    _evidence("evidencias_suplementares.serasa", "direcao", serasa.direcao),
                ],
                efeito_metodologico="Comparação suplementar; os resultados não são somados nem convertidos entre si.",
                impacto_credito="A divergência requer interpretação conjunta sem alterar isoladamente a recomendação FinScore.",
            )
        )
    if serasa.cronologia_valida is False:
        result.append(
            Finding(
                achado_id="ACH-SUP-SERASA-DATA",
                categoria=FindingCategory.ALERT,
                natureza=FindingNature.EXTERNAL_EVIDENCE,
                titulo="Data da consulta ao Serasa requer validação",
                evidencias=[
                    _evidence("evidencias_suplementares.serasa", "data_consulta", serasa.data_consulta)
                ],
                efeito_metodologico="A cronologia da evidência externa não foi validada.",
                impacto_credito="A consulta não deve sustentar conclusão até a confirmação de sua data.",
                providencia="Confirmar a data da consulta e atualizar a evidência, se necessário.",
            )
        )

    if contract.evidencias_suplementares.springate:
        latest = max(contract.evidencias_suplementares.springate, key=lambda item: item.exercicio)
        distress = "DISTRESS" in latest.classificacao.upper() and "SEM" not in latest.classificacao.upper()
        result.append(
            Finding(
                achado_id="ACH-SUP-SPRINGATE",
                categoria=FindingCategory.RISK if distress else FindingCategory.STRENGTH,
                natureza=FindingNature.DERIVED,
                titulo=f"Springate: {latest.classificacao.lower()}",
                evidencias=[
                    _evidence("evidencias_suplementares.springate", "score", latest.score, year=latest.exercicio),
                    _evidence("evidencias_suplementares.springate", "classificacao", latest.classificacao, year=latest.exercicio),
                ],
                efeito_metodologico="Diagnóstico derivado e suplementar; não altera o FinScore.",
                impacto_credito=(
                    "O diagnóstico indica sinal suplementar de dificuldade financeira."
                    if distress
                    else "O diagnóstico não apresenta sinal de distress no exercício mais recente."
                ),
            )
        )

    if contract.evidencias_suplementares.fleuriet:
        latest = max(contract.evidencias_suplementares.fleuriet, key=lambda item: item.exercicio)
        not_calculated = "NÃO CALCULÁVEL" in latest.diagnostico.upper()
        result.append(
            Finding(
                achado_id="ACH-SUP-FLEURIET",
                categoria=FindingCategory.LIMITATION if not_calculated else FindingCategory.ALERT,
                natureza=FindingNature.DERIVED,
                titulo=f"Fleuriet simplificado: {latest.diagnostico.lower()}",
                evidencias=[
                    _evidence("evidencias_suplementares.fleuriet", "capital_giro", latest.capital_giro, year=latest.exercicio, unit="BRL"),
                    _evidence("evidencias_suplementares.fleuriet", "necessidade_capital_giro", latest.necessidade_capital_giro, year=latest.exercicio, unit="BRL"),
                    _evidence("evidencias_suplementares.fleuriet", "diagnostico", latest.diagnostico, year=latest.exercicio),
                ],
                efeito_metodologico="Diagnóstico derivado e suplementar; não altera o FinScore.",
                impacto_credito=(
                    "A estrutura dinâmica de capital de giro não pôde ser concluída."
                    if not_calculated
                    else "O diagnóstico complementa a leitura da estrutura de capital de giro."
                ),
                providencia=(
                    "Completar as contas operacionais necessárias ao diagnóstico."
                    if not_calculated
                    else None
                ),
            )
        )
    return result


def _period_findings(contract: ParecerData) -> list[Finding]:
    cadastral = contract.identificacao.periodos.cadastral
    analyzed = contract.identificacao.periodos.analisado
    cadastral_label = (
        f"{cadastral.inicio}–{cadastral.fim}"
        if cadastral.inicio is not None and cadastral.fim is not None
        else None
    )
    analyzed_label = f"{analyzed.inicio}–{analyzed.fim}"
    return [
        Finding(
            achado_id=f"ACH-PER-{index:03d}",
            categoria=FindingCategory.DIVERGENCE,
            natureza=FindingNature.OBSERVED,
            titulo="Divergência entre período cadastral e período analisado",
            evidencias=[
                _evidence("identificacao.periodos", "periodo_cadastral", cadastral_label),
                _evidence("identificacao.periodos", "periodo_analisado", analyzed_label),
                _evidence("identificacao.periodos", "descricao_divergencia", item.descricao),
            ],
            efeito_metodologico="O cálculo conserva exclusivamente os exercícios efetivamente utilizados.",
            impacto_credito=item.impacto,
            providencia="Confirmar o escopo temporal documental e manter os períodos separados.",
        )
        for index, item in enumerate(contract.identificacao.periodos.divergencias, 1)
    ]


def _governance_findings(contract: ParecerData) -> list[Finding]:
    governance = contract.governanca
    recommendation = governance.recomendacao_finscore
    evidences = [
        _evidence("governanca.recomendacao_finscore", "resultado", recommendation.codigo.value)
    ]
    if governance.manifestacao_analista is not None:
        evidences.append(
            _evidence(
                "governanca.manifestacao_analista",
                "resultado",
                governance.manifestacao_analista.resultado.value,
            )
        )
    if governance.decisao_alcada is not None:
        evidences.append(
            _evidence(
                "governanca.decisao_alcada",
                "resultado",
                governance.decisao_alcada.resultado.value,
            )
        )
    result = [
        Finding(
            achado_id="ACH-GOV-POSICOES",
            categoria=FindingCategory.RESULT,
            natureza=FindingNature.INTERPRETATION,
            titulo="Posições registradas na governança de crédito",
            evidencias=evidences,
            efeito_metodologico="A recomendação FinScore não substitui a manifestação do analista nem a decisão da alçada.",
            impacto_credito="Cada posição conserva autoria, data e fundamentação em registro separado.",
        )
    ]
    for index, divergence in enumerate(governance.divergencias, 1):
        result.append(
            Finding(
                achado_id=f"ACH-GOV-DIV-{index:03d}",
                categoria=FindingCategory.DIVERGENCE,
                natureza=FindingNature.INTERPRETATION,
                titulo="Divergência entre posições da governança",
                evidencias=[
                    _evidence(f"governanca.divergencias:{index}", divergence.origem, divergence.resultado_origem.value),
                    _evidence(f"governanca.divergencias:{index}", divergence.destino, divergence.resultado_destino.value),
                    _evidence(f"governanca.divergencias:{index}", "justificativa", divergence.justificativa),
                ],
                efeito_metodologico="A divergência não altera retroativamente a recomendação calculada.",
                impacto_credito="A posição posterior deve ser lida com a justificativa e a responsabilidade registradas.",
            )
        )
    return result


def build_evidence_book(contract: ParecerData) -> list[Finding]:
    """Gera achados somente a partir do contrato validado, sem alterar decisões."""

    findings = [
        *_result_findings(contract),
        *_blocking_findings(contract),
        *_quality_findings(contract),
        *_missing_calculation_findings(contract),
        *_score_findings(contract),
        *_scenario_findings(contract),
        *_supplementary_findings(contract),
        *_period_findings(contract),
        *_governance_findings(contract),
    ]
    identifiers = [item.achado_id for item in findings]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("livro de evidências produziu identificadores duplicados")
    return findings


def attach_evidence_book(contract: ParecerData) -> ParecerData:
    payload = contract.model_dump(mode="python")
    payload["achados"] = [item.model_dump(mode="python") for item in build_evidence_book(contract)]
    return ParecerData.model_validate(payload)


__all__ = ["attach_evidence_book", "build_evidence_book"]
