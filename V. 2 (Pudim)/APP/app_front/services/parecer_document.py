"""Montagem determinística do documento funcional do parecer."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import re
from html import escape as html_escape
from pathlib import Path
from typing import Any, Iterable

try:  # Execução Streamlit, com app_front no sys.path.
    from components.parecer_data_schema import (
        DataPoint,
        FindingCategory,
        ParecerData,
    )
    from components.parecer_schema import NarrativeItem, ParecerNarrativo
except ModuleNotFoundError:  # Importação como pacote nos testes.
    from app_front.components.parecer_data_schema import (
        DataPoint,
        FindingCategory,
        ParecerData,
    )
    from app_front.components.parecer_schema import NarrativeItem, ParecerNarrativo


METHODOLOGY_PATH = (
    Path(__file__).resolve().parent.parent / "content" / "metodologia_pudim_2_0_20.md"
)

INDICATOR_LABELS = {
    "crescimento_receita": "Crescimento da receita",
    "margem_bruta": "Margem bruta",
    "margem_ebit": "Margem EBIT",
    "margem_liquida": "Margem líquida",
    "giro_ativo": "Giro do ativo",
    "prazo_recebimento_dias": "Prazo de recebimento",
    "prazo_estoques_dias": "Prazo de estoques",
    "prazo_fornecedores_dias": "Prazo de fornecedores",
    "ciclo_conversao_caixa": "Ciclo de conversão de caixa",
    "capitalizacao": "Capitalização",
    "endividamento_exigivel": "Endividamento exigível",
    "liquidez_corrente": "Liquidez corrente",
    "liquidez_seca": "Liquidez seca",
    "ccl_ativo": "CCL / ativo",
    "ncg_operacional_ativo": "NCG operacional / ativo",
    "divida_liquida_ativo": "Dívida líquida / ativo",
    "composicao_endividamento": "Composição do endividamento",
    "cobertura_juros": "Cobertura de juros",
}
ACCOUNT_LABELS = {
    "r_Receita_Liquida": "Receita líquida",
    "r_Lucro_Liquido": "Lucro líquido",
    "p_Ativo_Total": "Ativo total",
    "p_Patrimonio_Liquido": "Patrimônio líquido",
    "d_EBIT": "EBIT",
    "d_Divida_Financeira_Bruta": "Dívida bruta",
    "d_Divida_Financeira_Liquida": "Dívida líquida",
}
ECONOMIC_INDICATORS = (
    "crescimento_receita",
    "margem_bruta",
    "margem_ebit",
    "margem_liquida",
    "giro_ativo",
    "ciclo_conversao_caixa",
)
FINANCIAL_INDICATORS = (
    "capitalizacao",
    "endividamento_exigivel",
    "liquidez_corrente",
    "liquidez_seca",
    "ccl_ativo",
    "ncg_operacional_ativo",
    "divida_liquida_ativo",
    "composicao_endividamento",
    "cobertura_juros",
)


def load_methodology() -> str:
    return METHODOLOGY_PATH.read_text(encoding="utf-8").strip()


def methodology_sha256() -> str:
    return hashlib.sha256(METHODOLOGY_PATH.read_bytes()).hexdigest()


def _md(value: Any) -> str:
    if value in (None, ""):
        return "Não informado"
    return html_escape(str(value)).replace("|", "&#124;").replace("\n", " ")


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_number(value: Any, decimals: int = 2) -> str:
    number = _number(value)
    if number is None:
        return "—"
    return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_value(value: Any, unit: str | None) -> str:
    if value is None:
        return "Não calculado"
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if unit == "BRL":
        return "R$ " + _fmt_number(value, 2)
    if unit == "proporcao":
        number = _number(value)
        return "—" if number is None else _fmt_number(number * 100, 2) + "%"
    if unit == "dias":
        return _fmt_number(value, 1) + " dias"
    if unit in {"pontos", "pontos_0_100", "pontos_0_95"}:
        return _fmt_number(value, 2)
    if unit == "multiplo":
        return _fmt_number(value, 2) + "x"
    if isinstance(value, (int, float)):
        return _fmt_number(value, 2)
    return _md(value)


def _period_label(contract: ParecerData) -> str:
    period = contract.identificacao.periodos.analisado
    return f"{period.inicio} a {period.fim}"


def _split_paragraph(text: str) -> tuple[str, str]:
    """Divide uma análise longa em dois parágrafos sem fracionar frases."""
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
    if len(sentences) < 2:
        return text, text
    midpoint = max(1, len(sentences) // 2)
    return " ".join(sentences[:midpoint]), " ".join(sentences[midpoint:])


def _series_commentary(
    points: Iterable[DataPoint],
    fields: Iterable[str],
    years: list[int],
    labels: dict[str, str],
    *,
    favorable_up: set[str],
    favorable_down: set[str],
) -> tuple[str, str]:
    """Resume variações e ausências diretamente das séries exibidas na tabela."""
    selected = {(item.campo, item.exercicio): item for item in points}
    variations: list[tuple[float, str, int, int, float, float, str | None]] = []
    missing: list[str] = []
    ordered_fields = list(fields)
    for field in ordered_fields:
        absent_years = [
            str(year)
            for year in years
            if selected.get((field, year)) is None
            or _number(selected[(field, year)].valor) is None
        ]
        if absent_years:
            missing.append(f"{labels.get(field, field)} ({', '.join(absent_years)})")
        available = [
            (year, _number(selected[(field, year)].valor), selected[(field, year)].unidade)
            for year in years
            if (field, year) in selected and _number(selected[(field, year)].valor) is not None
        ]
        for (left_year, left, unit), (right_year, right, _right_unit) in zip(
            available, available[1:]
        ):
            if left is None or right is None:
                continue
            # Variação simétrica evita que base quase zero monopolize os destaques.
            scale = max(abs(left), abs(right))
            magnitude = abs(right - left) / scale if scale else 0.0
            variations.append((magnitude, field, left_year, right_year, left, right, unit))

    variations.sort(reverse=True, key=lambda item: item[0])
    highlights = []
    supportive = []
    pressure = []
    highlighted_fields: set[str] = set()
    for _magnitude, field, left_year, right_year, left, right, unit in variations:
        direction = "elevação" if right > left else "redução" if right < left else "estabilidade"
        if unit == "proporcao":
            change_text = f", diferença de {_fmt_number((right - left) * 100)} pontos percentuais"
        elif left > 0 and right >= 0:
            change_text = f", variação de {_fmt_number((right - left) / left * 100)}%"
        else:
            change_text = ", percentual de variação não interpretado por base nula/negativa ou mudança de sinal"
        label = labels.get(field, field.replace("_", " "))
        if field not in highlighted_fields and len(highlights) < 3:
            highlights.append(
                f"{label}, de {_fmt_value(left, unit)} em {left_year} para "
                f"{_fmt_value(right, unit)} em {right_year}{change_text}"
            )
            highlighted_fields.add(field)
        favorable = (right > left and field in favorable_up) or (
            right < left and field in favorable_down
        )
        unfavorable = (right < left and field in favorable_up) or (
            right > left and field in favorable_down
        )
        if favorable and f"{direction} de {label}" not in supportive:
            supportive.append(f"{direction} de {label}")
        elif unfavorable and f"{direction} de {label}" not in pressure:
            pressure.append(f"{direction} de {label}")

    if highlights:
        before = "Movimentos selecionados da série (sem equivaler a ranking de materialidade econômica): " + "; ".join(highlights) + "."
    else:
        before = "A série disponível não apresenta base temporal suficiente para mensurar variações entre exercícios."
    if missing:
        before += " Há ausência ou impossibilidade de cálculo em " + "; ".join(missing[:6]) + "."
    else:
        before += " Não foram identificadas lacunas nas linhas apresentadas nesta tabela."

    strengths = ", ".join(supportive) if supportive else "nenhum vetor favorável isolado suficientemente caracterizado"
    weaknesses = ", ".join(pressure) if pressure else "nenhum fator adverso isolado suficientemente caracterizado"
    after = (
        f"Sob a perspectiva econômico-financeira, constituem vetores de sustentação {strengths}; "
        f"como fatores de pressão, observam-se {weaknesses}. Esses movimentos devem ser avaliados "
        "em conjunto com liquidez, estrutura de capital, geração de resultado e qualidade dos dados. "
        "Uma rubrica pode apresentar movimentos opostos em intervalos distintos; a tabela preserva a trajetória completa."
    )
    return before, after


def _prose_items(prefix: str, values: Iterable[str]) -> str:
    texts = [_md(item).strip().rstrip(".") for item in values if str(item).strip()]
    if not texts:
        return f"{prefix} não registra elemento material adicional."
    return f"{prefix} " + "; ".join(texts) + "."


def _items(values: Iterable[NarrativeItem]) -> str:
    texts = [_md(item.texto) for item in values]
    return "\n".join(f"- {text}" for text in texts) if texts else "- Nenhum item material registrado."


def _plain_items(values: Iterable[str]) -> str:
    texts = [_md(item) for item in values if str(item).strip()]
    return "\n".join(f"- {text}" for text in texts) if texts else "- Nenhum item registrado."


def _series_table(
    points: Iterable[DataPoint],
    fields: Iterable[str],
    years: list[int],
    labels: dict[str, str],
) -> str:
    selected = {(item.campo, item.exercicio): item for item in points}
    lines = [
        "| Indicador | " + " | ".join(str(year) for year in years) + " |",
        "|---|" + "---:|" * len(years),
    ]
    for field in fields:
        row = [labels.get(field, field.replace("_", " "))]
        for year in years:
            point = selected.get((field, year))
            row.append("—" if point is None else _fmt_value(point.valor, point.unidade))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _data_inventory(contract: ParecerData) -> str:
    data = contract.dados
    changed = sum(1 for item in data.rastreabilidade if item.alterado)
    return "\n".join(
        [
            "| Camada de informação | Registros | Observação |",
            "|---|---:|---|",
            f"| Valores reportados | {len(data.reportados)} | Preservados como recebidos |",
            f"| Valores propostos | {len(data.propostos)} | Sem substituição silenciosa |",
            f"| Valores utilizados | {len(data.utilizados)} | Base efetiva do cálculo |",
            f"| Valores derivados | {len(data.derivados)} | Cálculos contábeis intermediários |",
            f"| Índices | {len(data.indices)} | Séries por exercício |",
            f"| Notas | {len(data.notas)} | Séries por exercício |",
            f"| Itens não calculados | {len(data.nao_calculados)} | Ausências preservadas |",
            f"| Valores alterados | {changed} | Identificados na rastreabilidade |",
        ]
    )


def _blocking_details(contract: ParecerData) -> str:
    blockers = contract.governanca.recomendacao_finscore.bloqueios
    if not blockers:
        return "Nenhum bloqueio decisório registrado."
    sections = []
    for index, item in enumerate(blockers, 1):
        sections.append(
            f"**{index}. {_md(item.titulo)}**  \n"
            f"**Motivo:** {_md(item.motivo)}  \n"
            f"**Impacto:** {_md(item.impacto)}  \n"
            f"**Providência:** {_md(item.providencia)}"
        )
    return "\n\n".join(sections)


def _quality_table(contract: ParecerData) -> str:
    quality = contract.qualidade.resumo
    return "\n".join(
        [
            "| Controle | Resultado |",
            "|---|---:|",
            f"| Apto para cálculo | {'Sim' if quality.apto_calculo else 'Não'} |",
            f"| Apto para recomendação | {'Sim' if quality.apto_decisao else 'Não'} |",
            f"| Qualidade dos dados | {_fmt_value(quality.indice_confiabilidade, 'proporcao')} |",
            f"| Classificação da qualidade dos dados | {_md(quality.classificacao_confiabilidade)} |",
            f"| Ocorrências críticas | {quality.ocorrencias_criticas} |",
            f"| Avisos | {quality.ocorrencias_aviso} |",
            f"| Alertas de viés alto/crítico | {quality.alertas_vies_alto_critico} |",
            f"| Alertas bloqueadores | {quality.alertas_bloqueadores_decisao} |",
        ]
    )


def _reliability_table(contract: ParecerData) -> str:
    components = contract.qualidade.componentes_confiabilidade
    if not components:
        return "Decomposição da confiabilidade não disponibilizada nesta execução."
    lines = ["| Componente da confiabilidade | Nota | Peso | Contribuição |",
             "|---|---:|---:|---:|"]
    for item in components:
        lines.append(f"| {_md(item.componente)} | {_fmt_value(item.nota, 'proporcao')} | "
                     f"{_fmt_value(item.peso, 'proporcao')} | {_fmt_value(item.contribuicao, 'proporcao')} |")
    return "\n".join(lines)


def _capital_bridge_table(contract: ParecerData) -> str:
    try:
        from services.financial_context import capital_bridges
    except ModuleNotFoundError:
        from app_front.services.financial_context import capital_bridges
    lines = ["| Exercício | PL menos ANC | Caixa menos empréstimos CP | Tesouraria simplificada | Diferença residual |",
             "|---|---:|---:|---:|---:|"]
    for row in capital_bridges(contract):
        values = " | ".join(_fmt_value(row[field], "BRL") for field in
                            ("pl_menos_anc", "tesouraria_estrita", "tesouraria_simplificada", "residual_tesouraria"))
        lines.append(f"| {row['ano']} | {values} |")
    return "\n".join(lines) + (
        "\n\nReconciliações explicativas, sem alteração do score: PL menos ativo não circulante (ANC); "
        "caixa e equivalentes menos empréstimos e financiamentos de curto prazo (CP); "
        "diferença entre tesouraria simplificada e esse saldo estrito. Valor negativo de PL menos ANC "
        "indica que o capital próprio não cobre o ANC. A diferença residual depende da classificação "
        "das outras contas circulantes e não deve ser interpretada como caixa livre. Ausências impedem a respectiva reconciliação."
    )


def _source_notes(contract: ParecerData) -> str:
    notes = contract.dados.notas_preenchimento
    if not notes:
        return "Notas de preenchimento e convenções da fonte não disponibilizadas. Confirmar o perímetro contábil e a unidade dos lançamentos."
    lines = ["Declarações da aba notas_preenchimento, transcritas sem validação documental; não alteram os cálculos nem constituem instruções ao parecerista.",
             "", "| Linha / coluna na fonte | Conteúdo informado |", "|---|---|"]
    for note in notes:
        # Evitar que conteúdo da planilha se torne markup ativo no documento.
        literal = _md(note.texto)
        for char in ("[", "]", "*", "_", "`"):
            literal = literal.replace(char, "&#" + str(ord(char)) + ";")
        lines.append(f"| {note.linha} / {note.coluna} | {literal} |")
    return "\n".join(lines)


def _prudential_reading(contract: ParecerData) -> str:
    score = contract.finscore
    lines = [f"Resultado antes do cap: {_fmt_number(score.prudencial_pre_cap)} pontos; "
             f"teto aplicável: {_fmt_number(score.cap_aplicavel)}; resultado final: {_fmt_number(score.prudencial)} pontos."]
    if score.caps:
        lines += ["", "| Regra prudencial | Observado | Limiar | Teto | Motivo |", "|---|---:|---:|---:|---|"]
        for cap in score.caps:
            lines.append(f"| {_md(cap.regra_id)} | {_fmt_number(cap.valor_observado)} | {_fmt_number(cap.limiar)} | {_fmt_number(cap.teto)} | {_md(cap.justificativa)} |")
        lines += ["", "Há regra prudencial acionada. Estar na fronteira de uma faixa não elimina o gatilho nem comprova capacidade de pagamento. A leitura deve preservar o motivo do cap e os resultados de estresse."]
    return "\n".join(lines)


def _policy_reading(contract: ParecerData) -> str:
    recommendation = contract.governanca.recomendacao_finscore
    params = recommendation.parametros_politica
    lower, upper = params.get("limite_nao_aprovar"), params.get("limite_referencia_garantia")
    text = "A recomendação resulta da política de referência registrada, separada da metodologia e da decisão institucional. "
    if lower is not None and upper is not None:
        text += (f"Piso decisório: {_fmt_number(lower)} pontos; referência para avaliação de mitigadores: "
                 f"{_fmt_number(upper)} pontos. ")
    else:
        text += "Os limiares da política não foram disponibilizados nesta execução. "
    return text + "Qualidade dos dados controla aptidão de uso e não é evidência de solvência."


def _score_table(contract: ParecerData) -> str:
    score = contract.finscore
    return "\n".join(
        [
            "| Componente | Estrutural | Adaptativo |",
            "|---|---:|---:|",
            f"| Núcleo econômico-operacional | {_fmt_number(score.estrutural.nucleo_eo)} | {_fmt_number(score.adaptativo.nucleo_eo)} |",
            f"| Núcleo financeiro-patrimonial | {_fmt_number(score.estrutural.nucleo_fp)} | {_fmt_number(score.adaptativo.nucleo_fp)} |",
            f"| Composição geométrica | {_fmt_number(score.estrutural.geometrico)} | {_fmt_number(score.adaptativo.geometrico)} |",
            f"| Gargalo | {_fmt_number(score.estrutural.gargalo)} | {_fmt_number(score.adaptativo.gargalo)} |",
            f"| Resultado após gargalo | {_fmt_number(score.estrutural.pos_gargalo)} | {_fmt_number(score.adaptativo.pos_gargalo)} |",
        ]
    )


def _bar_chart(title: str, values: list[tuple[str, float]], source: str) -> str:
    if len(values) < 2 or len({round(value, 8) for _label, value in values}) < 2:
        return ""
    bars = []
    for label, value in values:
        width = max(0.5, min(100.0, value / 10.0))
        bars.append(
            '<div class="chart-row">'
            f'<span class="chart-label">{html_escape(label)}</span>'
            '<span class="chart-track">'
            f'<span class="chart-bar" style="width:{width:.2f}%"></span>'
            "</span>"
            f'<span class="chart-value">{_fmt_number(value)}</span>'
            "</div>"
        )
    return (
        '<figure class="finscore-chart">'
        f'<figcaption>{html_escape(title)} <small>(pontos)</small></figcaption>'
        + "".join(bars)
        + f'<p class="chart-source">Fonte: {html_escape(source)}.</p>'
        + "</figure>"
    )


def _score_chart(contract: ParecerData) -> str:
    score = contract.finscore
    values = [
        ("EO estrutural", score.estrutural.nucleo_eo),
        ("FP estrutural", score.estrutural.nucleo_fp),
        ("EO adaptativo", score.adaptativo.nucleo_eo),
        ("FP adaptativo", score.adaptativo.nucleo_fp),
    ]
    return _bar_chart(
        "Comparação dos núcleos do FinScore",
        [(label, value) for label, value in values if value is not None],
        "Dados processados na análise",
    )


def _scenario_table(contract: ParecerData) -> str:
    scenarios = contract.cenarios.deterministicos
    if not scenarios:
        return "Cenários determinísticos não disponíveis."
    lines = [
        "| Cenário | Status | FinScore | Margem líquida | Financiamento adicional | Monotonicidade |",
        "|---|---|---:|---:|---:|---|",
    ]
    for item in scenarios:
        lines.append(
            f"| {_md(item.nome.title())} | {_md(item.status)} | {_fmt_number(item.finscore_prudencial)} | "
            f"{_fmt_value(item.margem_liquida_ultimo_ano, 'proporcao')} | "
            f"{_fmt_value(item.financiamento_adicional_ultimo_ano, 'BRL')} | "
            f"{_md(item.status_monotonicidade)} |"
        )
    return "\n".join(lines)


def _scenario_chart(contract: ParecerData) -> str:
    values = [
        (item.nome.title(), item.finscore_prudencial)
        for item in contract.cenarios.deterministicos
        if item.finscore_prudencial is not None
    ]
    return _bar_chart(
        "FinScore sob cenários determinísticos",
        [(label, value) for label, value in values if value is not None],
        "Cenários condicionais da análise; não constituem previsão",
    )


def _simulation_table(contract: ParecerData) -> str:
    summaries = contract.cenarios.resumos_simulacao
    if not summaries:
        return "Simulação não executada nesta análise."
    lines = [
        "| Abordagem | Método | Trajetórias | Média | P05 | Mediana | P95 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    limitations: dict[str, str] = {}
    frequencies = []
    for item in summaries:
        diagnostics = [diagnostic for diagnostic in contract.cenarios.diagnosticos
                       if diagnostic.abordagem.strip().casefold() == item.abordagem.strip().casefold()]
        if not diagnostics or any(diagnostic.valida_para_interpretacao is not True for diagnostic in diagnostics):
            details = "; ".join(
                f"{_md(diagnostic.status_rejeicao)}; taxa de rejeição {_fmt_value(diagnostic.taxa_rejeicao, 'proporcao')}"
                for diagnostic in diagnostics
            ) or "diagnóstico de validade não disponibilizado"
            limitations[item.abordagem] = (
                f"Simulação {_md(item.abordagem)} indisponível para interpretação: {details}. "
                "Os resultados numéricos não são apresentados como evidência utilizável."
            )
            continue
        lines.append(
            f"| {_md(item.abordagem)} | {_md(item.metodo)} | {item.numero_trajetorias} | "
            f"{_fmt_number(item.media)} | {_fmt_number(item.p05)} | "
            f"{_fmt_number(item.mediana)} | {_fmt_number(item.p95)} |"
        )
        if item.metodo.strip().casefold() == "prudencial" and item.frequencias:
            values = "; ".join(
                f"abaixo de {_fmt_number(f.corte, 0)} pontos: {_fmt_value(f.frequencia, 'proporcao')}"
                for f in sorted(item.frequencias, key=lambda f: f.corte)
            )
            frequencies.append(f"FinScore prudencial, {_md(item.abordagem)} — {values}.")
    table = "\n".join(lines) if len(lines) > 2 else ""
    frequency_text = (
        "Frequências empíricas das trajetórias aceitas (não são probabilidades de inadimplência): "
        + " ".join(frequencies) if frequencies else ""
    )
    return "\n\n".join([part for part in [table, frequency_text, *limitations.values()] if part])


def _supplementary_table(contract: ParecerData) -> str:
    evidence = contract.evidencias_suplementares
    lines = [
            "| Diagnóstico | Exercício/data | Resultado | Natureza |",
            "|---|---|---|---|",
            f"| Serasa | {_md(evidence.serasa.data_consulta)} | {_fmt_number(evidence.serasa.score)} — {_md(evidence.serasa.status)} | Evidência externa separada |",
        ]
    for item in sorted(evidence.springate, key=lambda item: item.exercicio):
        lines.append(f"| Springate | {item.exercicio} | {_fmt_number(item.score)} — {_md(item.classificacao)} | Diagnóstico derivado |")
    if not evidence.springate:
        lines.append("| Springate | — | Não calculado | Diagnóstico derivado |")
    for item in sorted(evidence.fleuriet, key=lambda item: item.exercicio):
        lines.append(f"| Fleuriet simplificado | {item.exercicio} | {_md(item.diagnostico)} | Diagnóstico derivado |")
    if not evidence.fleuriet:
        lines.append("| Fleuriet simplificado | — | Não calculado | Diagnóstico derivado |")
    return "\n".join(lines)


def _latest_data_point(
    points: Iterable[DataPoint], field: str, year: int
) -> DataPoint | None:
    return next(
        (item for item in points if item.campo == field and item.exercicio == year),
        None,
    )


def _display_point(point: DataPoint | None) -> str:
    return "não calculado" if point is None else _fmt_value(point.valor, point.unidade)


def _supplementary_interpretation(contract: ParecerData) -> str:
    evidence = contract.evidencias_suplementares
    serasa = evidence.serasa
    springate = max(evidence.springate, key=lambda item: item.exercicio) if evidence.springate else None
    fleuriet = max(evidence.fleuriet, key=lambda item: item.exercicio) if evidence.fleuriet else None
    parts = [f"O FinScore prudencial apurado foi de {_fmt_number(contract.finscore.prudencial)} pontos"]
    if serasa.score is not None:
        divergence = (
            f", com divergência de {_fmt_number(serasa.divergencia_pontos)} pontos, "
            f"classificada como {_md(serasa.nivel_divergencia)} e {_md(serasa.direcao)}"
            if serasa.divergencia_pontos is not None
            else ""
        )
        parts.append(
            f"o Serasa registrou {_fmt_number(serasa.score)} pontos{divergence}"
        )
    else:
        parts.append("o score Serasa não foi informado")
    if springate is not None and springate.score is not None:
        parts.append(
            f"o Springate de {springate.exercicio} foi {_fmt_number(springate.score)}, "
            f"classificado como {_md(springate.classificacao)}"
        )
    else:
        parts.append("o Springate não pôde ser calculado")
    if fleuriet is not None:
        parts.append(
            f"a leitura Fleuriet de {fleuriet.exercicio} apresentou NCG de "
            f"{_fmt_value(fleuriet.necessidade_capital_giro, 'BRL')}, capital de giro de "
            f"{_fmt_value(fleuriet.capital_giro, 'BRL')} e saldo de tesouraria de "
            f"{_fmt_value(fleuriet.saldo_tesouraria, 'BRL')}, com diagnóstico "
            f"{_md(fleuriet.diagnostico)}"
        )
    else:
        parts.append("a leitura Fleuriet não pôde ser calculada")
    if serasa.alerta_temporal:
        parts.append(_md(serasa.alerta_temporal) + " A consulta requer confirmação antes do uso")
    return (
        "; ".join(parts)
        + ". A convergência ou divergência entre essas medidas qualifica a análise, mas não altera "
        "aritmeticamente o FinScore: Serasa representa evidência externa, enquanto Springate e "
        "Fleuriet reutilizam as demonstrações contábeis sob critérios diagnósticos próprios."
    )


def _final_considerations(contract: ParecerData) -> str:
    identity = contract.identificacao
    recommendation = contract.governanca.recomendacao_finscore
    quality = contract.qualidade.resumo
    year = identity.periodos.analisado.fim
    accounts = [*contract.dados.utilizados, *contract.dados.derivados]
    indices = contract.dados.indices

    revenue = _latest_data_point(accounts, "r_Receita_Liquida", year)
    profit = _latest_data_point(accounts, "r_Lucro_Liquido", year)
    ebit = _latest_data_point(accounts, "d_EBIT", year)
    assets = _latest_data_point(accounts, "p_Ativo_Total", year)
    equity = _latest_data_point(accounts, "p_Patrimonio_Liquido", year)
    margin = _latest_data_point(indices, "margem_liquida", year)
    capitalization = _latest_data_point(indices, "capitalizacao", year)
    current_liquidity = _latest_data_point(indices, "liquidez_corrente", year)
    net_debt = _latest_data_point(indices, "divida_liquida_ativo", year)
    interest_cover = _latest_data_point(indices, "cobertura_juros", year)

    scenario_parts = []
    for name in ("adverso", "severo"):
        scenario = next((item for item in contract.cenarios.deterministicos if item.nome.lower() == name), None)
        if scenario is None or scenario.finscore_prudencial is None:
            scenario_parts.append(f"O cenário {name} não apresentou FinScore calculável.")
            continue
        part = f"No cenário {name}, o FinScore alcançou {_fmt_number(scenario.finscore_prudencial)} pontos"
        if contract.finscore.prudencial is not None:
            delta = scenario.finscore_prudencial - contract.finscore.prudencial
            part += f", uma diferença de {_fmt_number(delta)} pontos em relação ao observado"
        scenario_parts.append(part + ".")
    scenario_text = " ".join(scenario_parts)
    blockers = recommendation.bloqueios
    blocker_text = (
        f"Foram registrados {len(blockers)} bloqueios: "
        + "; ".join(
            f"{_md(item.titulo)} — {_md(item.motivo).rstrip('.')}. "
            f"Impacto: {_md(item.impacto).rstrip('.')}"
            for item in blockers
        )
        + "."
        if blockers
        else "Não foram registrados bloqueios de qualidade para o uso do FinScore nesta análise."
    )
    provisions = [
        _md(item).rstrip(".")
        for item in recommendation.providencias
        if str(item).strip()
    ]
    provision_intro = (
        "As providências de acompanhamento registradas são"
        if recommendation.codigo.value == "aprovar"
        else "Para nova submissão, devem ser executadas as seguintes providências"
    )
    provision_text = (
        f"{provision_intro}: " + "; ".join(provisions) + "."
        if provisions
        else "Não foram registradas providências adicionais no resultado calculado."
    )
    if recommendation.codigo.value == "aprovar":
        guarantee_text = (
            "A eventual inclusão, modalidade e suficiência de garantias poderão ser avaliadas "
            "pelo gestor e pela alçada competente conforme a estrutura da operação; o FinScore "
            "não determina dispensa automática de garantia."
        )
    elif blockers:
        guarantee_text = (
            f"No resultado **{_md(recommendation.rotulo)}**, a constituição de garantia não sana "
            f"os {len(blockers)} bloqueios registrados nem altera, isoladamente, o FinScore de "
            f"{_fmt_number(contract.finscore.prudencial)} pontos; eventual garantia somente poderá "
            "ser apreciada pelo gestor e pela alçada competente em nova análise."
        )
    else:
        guarantee_text = (
            f"No resultado **{_md(recommendation.rotulo)}**, a constituição de garantia não altera, "
            f"isoladamente, o FinScore de {_fmt_number(contract.finscore.prudencial)} pontos nem os "
            "indicadores econômico-financeiros que fundamentaram a recomendação; eventual garantia "
            "somente poderá ser apreciada pelo gestor e pela alçada competente em nova análise."
        )

    paragraphs = [
        (
            f"Para {_md(identity.tomador.nome)}, no período de {_period_label(contract)}, o FinScore "
            f"prudencial foi {_fmt_number(contract.finscore.prudencial)} pontos, situado na faixa "
            f"{_md(recommendation.faixa)}, com qualidade dos dados de "
            f"{_fmt_value(quality.indice_confiabilidade, 'proporcao')}. O núcleo econômico-operacional "
            f"foi {_fmt_number(contract.finscore.estrutural.nucleo_eo)} pontos na abordagem estrutural "
            f"e {_fmt_number(contract.finscore.adaptativo.nucleo_eo)} na adaptativa; o núcleo "
            f"financeiro-patrimonial foi {_fmt_number(contract.finscore.estrutural.nucleo_fp)} e "
            f"{_fmt_number(contract.finscore.adaptativo.nucleo_fp)} pontos, respectivamente."
        ),
        (
            f"No exercício de {year}, a receita líquida foi {_display_point(revenue)}, o lucro líquido "
            f"foi {_display_point(profit)} e o EBIT foi {_display_point(ebit)}. O ativo total encerrou "
            f"o período em {_display_point(assets)} e o patrimônio líquido em {_display_point(equity)}. "
            "A relação entre geração operacional, resultado líquido e base patrimonial delimita a "
            "capacidade interna de absorver serviço da dívida e oscilações do ciclo financeiro."
        ),
        (
            f"Também em {year}, a margem líquida foi {_display_point(margin)}, a capitalização "
            f"{_display_point(capitalization)}, a liquidez corrente {_display_point(current_liquidity)}, "
            f"a dívida líquida sobre o ativo {_display_point(net_debt)} e a cobertura de juros "
            f"{_display_point(interest_cover)}. Em conjunto, esses indicadores mostram a intensidade "
            "do endividamento, a folga de curto prazo, a sustentação patrimonial e a capacidade de "
            "cobrir despesas financeiras com resultado operacional."
        ),
        _supplementary_interpretation(contract),
        (
            f"{scenario_text} {blocker_text} A recomendação FinScore é **{_md(recommendation.rotulo)}**, "
            f"fundamentada no resultado de {_fmt_number(contract.finscore.prudencial)} pontos e nos "
            f"controles de qualidade descritos. {provision_text} {guarantee_text}"
        ),
        (
            f"A recomendação **{_md(recommendation.rotulo)}** aplica a política registrada ao FinScore de "
            f"{_fmt_number(contract.finscore.prudencial)} pontos e à aptidão informacional. "
            f"A leitura econômica considera a margem líquida de "
            f"{_display_point(margin)}, da capitalização de {_display_point(capitalization)}, da "
            f"liquidez corrente de {_display_point(current_liquidity)}, da dívida líquida sobre o "
            f"ativo de {_display_point(net_debt)} e da cobertura de juros de "
            f"{_display_point(interest_cover)}, todos referidos a {year}. O encaminhamento sujeita-se "
            "à revisão da documentação jurídica e cadastral da operação e à decisão de alçada superior."
        ),
    ]
    return "\n\n".join(paragraphs)


def _material_findings_table(contract: ParecerData) -> str:
    material = [
        item
        for item in contract.achados
        if item.categoria is not FindingCategory.RESULT
    ]
    lines = [
        "| Referência | Categoria | Achado | Efeito ou providência |",
        "|---|---|---|---|",
    ]
    for item in material:
        detail = item.providencia or item.efeito_metodologico or item.impacto_credito
        lines.append(
            f"| {_md(item.achado_id)} | {_md(item.categoria.value.title())} | "
            f"{_md(item.titulo)} | {_md(detail)} |"
        )
    return "\n".join(lines)


def render_structured_parecer(
    narrative: ParecerNarrativo,
    contract: ParecerData,
) -> str:
    identity = contract.identificacao
    operation = identity.operacao
    years = identity.periodos.analisado.exercicios
    recommendation = contract.governanca.recomendacao_finscore
    guarantee = recommendation.garantia
    methodology = load_methodology().replace(
        "## Metodologia", "## Anexo 1 — Metodologia", 1
    )
    guarantee_label = (
        "Avaliação atribuída ao gestor e à alçada competente"
        if guarantee.aplicavel
        else "Não aplicável à recomendação atual"
    )
    prazo = (
        f"{_fmt_number(operation.prazo.valor)} {_md(operation.prazo.unidade)}"
        if operation.prazo
        else "Não informado"
    )
    account_before, account_after = _series_commentary(
        [*contract.dados.utilizados, *contract.dados.derivados],
        ACCOUNT_LABELS,
        years,
        ACCOUNT_LABELS,
        favorable_up={
            "r_Receita_Liquida",
            "r_Lucro_Liquido",
            "p_Patrimonio_Liquido",
            "d_EBIT",
        },
        favorable_down={"d_Divida_Financeira_Bruta", "d_Divida_Financeira_Liquida"},
    )
    indicator_before, indicator_after = _series_commentary(
        contract.dados.indices,
        ECONOMIC_INDICATORS,
        years,
        INDICATOR_LABELS,
        favorable_up={
            "crescimento_receita",
            "margem_bruta",
            "margem_ebit",
            "margem_liquida",
            "giro_ativo",
        },
        favorable_down={"ciclo_conversao_caixa"},
    )
    financial_before, financial_after = _split_paragraph(
        narrative.analise_financeira_patrimonial.texto
    )
    guarantees_text = (
        "A recomendação de garantia decorre dos seguintes sinais: "
        + "; ".join(_md(item) for item in guarantee.motivos)
        + ". Modalidade, cobertura, prazo e suficiência dependem da política institucional e da avaliação da operação."
        if guarantee.recomendada else
        "A ausência de indicação automática de garantia não dispensa sua avaliação institucional. "
        "O parecer não determina modalidade, cobertura ou obrigação contratual."
    )
    final_paragraphs = _final_considerations(contract)
    return f"""<!-- FINSCORE_PARECER -->

# Parecer de Crédito — FinScore

**Identificador da análise:** {_md(contract.analise_id)}  
**Tomador:** {_md(identity.tomador.nome)}  
**CNPJ:** {_md(identity.tomador.cnpj)}  
**Período efetivamente analisado:** {_period_label(contract)}  
**Recomendação FinScore:** {_md(recommendation.rotulo)}

## 1. Identificação, operação e escopo

O presente parecer técnico de análise econômico-financeira e patrimonial examina
**{_md(identity.tomador.nome)}**, inscrita no CNPJ sob nº **{_md(identity.tomador.cnpj)}**,
com base nas informações contábeis e nos resultados FinScore dos exercícios de
{identity.periodos.analisado.inicio} a {identity.periodos.analisado.fim}.
As conclusões apoiam a avaliação humana da capacidade financeira e dos riscos observados.
A recomendação calculada permanece sujeita à política da instituição e à decisão da alçada
competente; a validade jurídica da operação e das garantias exige avaliação própria.

## 2. Sumário executivo

{_md(narrative.sumario_executivo.texto)}

| Controle | Resultado |
|---|---:|
| FinScore | {_fmt_number(contract.finscore.prudencial)} |
| Faixa | {_md(recommendation.faixa)} |
| Apto para recomendação | {'Sim' if recommendation.apto_decisao else 'Não'} |
| Qualidade dos dados | {_fmt_value(recommendation.confiabilidade, 'proporcao')} |
| Recomendação FinScore | {_md(recommendation.rotulo)} |
| Garantia | {guarantee_label} |

### 2.1 Impedimentos e providências

{_blocking_details(contract)}

## 3. Escopo e qualidade da informação

{_md(narrative.escopo_e_qualidade.texto)}

{_quality_table(contract)}

{_reliability_table(contract)}

A confiabilidade mede a qualidade informacional, não a capacidade de pagamento. Os avisos
de validação e os alertas de viés pertencem a controles distintos; ausência de avisos não
significa ausência de alertas. As contribuições acima explicam a composição do índice.

### 3.1 Fontes e convenções informadas

{_source_notes(contract)}

### 3.2 Inventário e rastreabilidade

{_data_inventory(contract)}

O dossiê estruturado conserva integralmente valores reportados, propostos, utilizados e derivados.
As tabelas seguintes apresentam as séries materiais para a leitura do parecer.

## 4. Análise econômico-operacional

{_md(narrative.analise_economico_operacional.texto)}

### 4.1 Contas utilizadas e derivadas

{account_before}

{_series_table([*contract.dados.utilizados, *contract.dados.derivados], ACCOUNT_LABELS, years, ACCOUNT_LABELS)}

{account_after}

### 4.2 Indicadores e trajetória

{indicator_before}

{_series_table(contract.dados.indices, ECONOMIC_INDICATORS, years, INDICATOR_LABELS)}

{indicator_after}

## 5. Análise financeira e patrimonial

{_md(financial_before)}

{_series_table(contract.dados.indices, FINANCIAL_INDICATORS, years, INDICATOR_LABELS)}

{_md(financial_after)}

### 5.1 Cobertura patrimonial e composição da tesouraria

{_capital_bridge_table(contract)}

## 6. Formação e interpretação do FinScore

O FinScore sintetiza, em escala de 0 a 1.000 pontos, os núcleos econômico-operacional e
financeiro-patrimonial. As abordagens estrutural e adaptativa calculam os núcleos com pesos fixos e
com ajuste controlado, respectivamente; a composição geométrica preserva o equilíbrio entre ambos,
e o gargalo atribui maior influência ao núcleo mais fraco. O FinScore prudencial corresponde ao
menor resultado pós-gargalo entre as abordagens, limitado, quando aplicável, por travas prudenciais.
{_policy_reading(contract)}

{_prudential_reading(contract)}

{_score_table(contract)}

{_md(narrative.formacao_finscore.texto)}

### 6.1 Garantias

{guarantees_text}

## 7. Evidências suplementares

Os cenários abaixo são hipóteses condicionais de estresse, sem caráter preditivo.

{_scenario_table(contract)}

{_simulation_table(contract)}

O score Serasa, informado na consulta externa em escala de 0 a 1.000 pontos, não é recalculado a
partir das demonstrações nem integrado ao FinScore. A comparação utiliza a diferença absoluta entre
as pontuações: até 100 pontos, a divergência é baixa e classificada como convergente; acima de 100 e
até 200, é moderada; acima de 200 e até 300, relevante; e, acima de 300, elevada. Nas divergências
superiores a 100 pontos, o sinal da diferença indica se a evidência externa é mais favorável ou mais
desfavorável que o FinScore. O índice Springate é calculado por `1,03 × CCL/Ativo Total + 3,07 × EBIT/Ativo
Total + 0,66 × Resultado antes de IR e CSLL/Passivo Circulante + 0,40 × Receita líquida/Ativo Total`:
resultado inferior a 0,862 sinaliza situação de distress, enquanto valor igual ou superior afasta
esse sinal específico. A leitura Fleuriet calcula `NCG = Ativo Circulante Operacional − Passivo
Circulante Operacional`, `CDG = Passivo Não Circulante + Patrimônio Líquido − Ativo Não Circulante`
e `Saldo de Tesouraria = CDG − NCG`. CDG positivo e saldo não negativo indicam cobertura da
necessidade operacional por fontes permanentes; saldo negativo evidencia dependência de recursos
financeiros de curto prazo; CDG não positivo aponta insuficiência de fontes permanentes.

{_supplementary_table(contract)}

**Limites de interpretação:** A dívida financeira considera os empréstimos e financiamentos
informados nas contas de curto e longo prazo; arrendamentos e mútuos não são incorporados
se não estiverem nesses saldos. Confirmar o perímetro nas notas explicativas antes de concluir
que o endividamento é baixo. A aplicabilidade setorial do Springate não foi validada nesta análise;
seus sinais não devem, isoladamente, sustentar conclusões sobre instituições financeiras ou seguradoras.
O saldo de tesouraria do Fleuriet simplificado inclui resíduos de classificação do circulante;
não equivale necessariamente a caixa livre. Capitalização positiva também não demonstra,
isoladamente, cobertura dos ativos não circulantes pelo patrimônio líquido.

## 8. Considerações finais

{final_paragraphs}

<div class="page-break"></div>

{methodology}

<div class="page-break"></div>

## Anexo 2 — Informações da análise

### 1. Reprodução funcional

| Campo | Valor |
|---|---|
| Identificador | {_md(contract.analise_id)} |
| Processado em | {_md(contract.metadados_funcionais.processado_em.isoformat())} |
| Versão da metodologia | {_md(contract.metadados_funcionais.versao_metodologia)} |
| Versão da estrutura do dossiê | {_md(contract.schema_versao)} |
| Versão da estrutura de resultados | {_md(contract.metadados_funcionais.versao_contrato_motor)} |
| Número de simulações | {contract.metadados_funcionais.numero_simulacoes} |
| Semente de simulação | {contract.metadados_funcionais.semente_simulacao} |
| Hash dos dados reportados | {_md(contract.metadados_tecnicos_restritos.hash_dados_reportados)} |
| Hash dos dados utilizados | {_md(contract.metadados_tecnicos_restritos.hash_dados_utilizados)} |
| Hash da metodologia | {methodology_sha256()} |
| Status de reprodução | Parâmetros e hashes registrados |
""".strip()


__all__ = [
    "load_methodology",
    "methodology_sha256",
    "render_structured_parecer",
]
