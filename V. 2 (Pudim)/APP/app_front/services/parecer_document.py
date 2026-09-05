"""Montagem determinística do documento funcional do parecer."""

from __future__ import annotations

from collections import defaultdict
import hashlib
from html import escape as html_escape
from pathlib import Path
from typing import Any, Iterable

try:  # Execução Streamlit, com app_front no sys.path.
    from components.parecer_data_schema import (
        DataPoint,
        FindingCategory,
        ParecerData,
        RecommendationCode,
    )
    from components.parecer_schema import NarrativeItem, ParecerNarrativo
except ModuleNotFoundError:  # Importação como pacote nos testes.
    from app_front.components.parecer_data_schema import (
        DataPoint,
        FindingCategory,
        ParecerData,
        RecommendationCode,
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
    "r_Receita_Total": "Receita total",
    "r_Lucro_Liquido": "Lucro líquido",
    "p_Ativo_Total": "Ativo total",
    "p_Patrimonio_Liquido": "Patrimônio líquido",
    "d_EBIT": "EBIT",
    "d_Divida_Bruta": "Dívida bruta",
    "d_Divida_Liquida": "Dívida líquida",
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


def _result_label(value: RecommendationCode | str | None) -> str:
    raw = value.value if isinstance(value, RecommendationCode) else str(value or "")
    return {
        "aprovar": "Aprovar",
        "nao_aprovar": "Não aprovar",
        "dados_inconsistentes": "Dados inconsistentes",
    }.get(raw, "Não registrado")


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
            f"| Confiabilidade | {_fmt_value(quality.indice_confiabilidade, 'proporcao')} |",
            f"| Classificação de confiabilidade | {_md(quality.classificacao_confiabilidade)} |",
            f"| Ocorrências críticas | {quality.ocorrencias_criticas} |",
            f"| Avisos | {quality.ocorrencias_aviso} |",
            f"| Alertas bloqueadores | {quality.alertas_bloqueadores_decisao} |",
        ]
    )


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
    for item in summaries:
        lines.append(
            f"| {_md(item.abordagem)} | {_md(item.metodo)} | {item.numero_trajetorias} | "
            f"{_fmt_number(item.media)} | {_fmt_number(item.p05)} | "
            f"{_fmt_number(item.mediana)} | {_fmt_number(item.p95)} |"
        )
    return "\n".join(lines)


def _supplementary_table(contract: ParecerData) -> str:
    evidence = contract.evidencias_suplementares
    springate = max(evidence.springate, key=lambda item: item.exercicio) if evidence.springate else None
    fleuriet = max(evidence.fleuriet, key=lambda item: item.exercicio) if evidence.fleuriet else None
    return "\n".join(
        [
            "| Diagnóstico | Exercício/data | Resultado | Natureza |",
            "|---|---|---|---|",
            f"| Serasa | {_md(evidence.serasa.data_consulta)} | {_fmt_number(evidence.serasa.score)} — {_md(evidence.serasa.status)} | Evidência externa separada |",
            f"| Springate | {springate.exercicio if springate else '—'} | "
            f"{(_fmt_number(springate.score) + ' — ' + _md(springate.classificacao)) if springate else 'Não calculado'} | Diagnóstico derivado |",
            f"| Fleuriet simplificado | {fleuriet.exercicio if fleuriet else '—'} | "
            f"{_md(fleuriet.diagnostico) if fleuriet else 'Não calculado'} | Diagnóstico derivado |",
        ]
    )


def _governance_table(contract: ParecerData) -> str:
    governance = contract.governanca
    analyst = governance.manifestacao_analista
    authority = governance.decisao_alcada
    lines = [
        "| Posição | Resultado | Responsável | Registro |",
        "|---|---|---|---|",
        f"| Recomendação FinScore | {_result_label(governance.recomendacao_finscore.codigo)} | Regras de crédito | {_md(contract.metadados_funcionais.processado_em.isoformat())} |",
        f"| Manifestação do analista | {_result_label(analyst.resultado if analyst else None)} | {_md(analyst.responsavel if analyst else None)} | {_md(analyst.registrado_em.isoformat() if analyst else None)} |",
        f"| Decisão da alçada | {_result_label(authority.resultado if authority else None)} | {_md(authority.responsavel if authority else None)} | {_md(authority.registrado_em.isoformat() if authority else None)} |",
    ]
    if analyst:
        lines.extend(["", f"**Fundamentação do analista:** {_md(analyst.justificativa)}"])
    if authority:
        lines.extend(["", f"**Fundamentação da alçada:** {_md(authority.justificativa)}"])
    if governance.divergencias:
        lines.extend(["", "**Divergências registradas:**"])
        lines.extend(
            f"- {_md(item.origem.replace('_', ' ').title())} → "
            f"{_md(item.destino.replace('_', ' ').title())}: {_md(item.justificativa)}"
            for item in governance.divergencias
        )
    return "\n".join(lines)


def _caps_table(contract: ParecerData) -> str:
    if not contract.finscore.caps:
        return "Nenhum cap prudencial acionado."
    lines = [
        "| Regra | Valor observado | Limiar | Teto | Fundamentação |",
        "|---|---:|---:|---:|---|",
    ]
    for item in contract.finscore.caps:
        lines.append(
            f"| {_md(item.regra_id)} | {_fmt_number(item.valor_observado, 4)} | "
            f"{_fmt_number(item.limiar, 4)} | {_fmt_number(item.teto)} | {_md(item.justificativa)} |"
        )
    return "\n".join(lines)


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
        "Recomendada, com detalhes sujeitos à avaliação institucional"
        if guarantee.recomendada
        else "Sem recomendação automática"
        if guarantee.aplicavel
        else "Não aplicável à recomendação atual"
    )
    prazo = (
        f"{_fmt_number(operation.prazo.valor)} {_md(operation.prazo.unidade)}"
        if operation.prazo
        else "Não informado"
    )
    return f"""<!-- FINSCORE_PARECER -->

# Parecer de Crédito — FinScore

**Identificador da análise:** {_md(contract.analise_id)}  
**Tomador:** {_md(identity.tomador.nome)}  
**CNPJ:** {_md(identity.tomador.cnpj)}  
**Período efetivamente analisado:** {_period_label(contract)}  
**Recomendação FinScore:** {_md(recommendation.rotulo)}

> O FinScore oferece suporte quantitativo à análise de crédito e não substitui a manifestação
> profissional nem a decisão da alçada competente. Dados observados, cálculos, hipóteses,
> diagnósticos suplementares e posições de governança permanecem separados.

## 1. Identificação, operação e escopo

| Campo | Informação |
|---|---|
| Concedente | {_md(identity.concedente.nome)} |
| CNPJ do concedente | {_md(identity.concedente.cnpj)} |
| Natureza da operação | {_md(operation.natureza)} |
| Finalidade | {_md(operation.finalidade)} |
| Valor | {_fmt_value(operation.valor, operation.moeda) if operation.valor is not None else 'Não informado'} |
| Prazo | {prazo} |
| Moeda | {_md(operation.moeda)} |
| Período cadastral | {_md(identity.periodos.cadastral.inicio)} a {_md(identity.periodos.cadastral.fim)} |
| Período analisado | {_period_label(contract)} |

O parecer organiza identificação e escopo, qualidade da informação, análise econômico-operacional,
estrutura financeira e patrimonial, formação do FinScore, estresse, evidências suplementares,
governança, riscos e conclusão. A metodologia e as informações de reprodução constam dos anexos.

## 2. Sumário executivo

{_md(narrative.sumario_executivo.texto)}

| Controle | Resultado |
|---|---:|
| FinScore prudencial | {_fmt_number(contract.finscore.prudencial)} |
| Faixa | {_md(recommendation.faixa)} |
| Apto para recomendação | {'Sim' if recommendation.apto_decisao else 'Não'} |
| Confiabilidade | {_fmt_value(recommendation.confiabilidade, 'proporcao')} |
| Recomendação FinScore | {_md(recommendation.rotulo)} |
| Garantia | {guarantee_label} |

### 2.1 Impedimentos e providências

{_blocking_details(contract)}

## 3. Escopo e qualidade da informação

{_md(narrative.escopo_e_qualidade.texto)}

{_quality_table(contract)}

### 3.1 Inventário e rastreabilidade

{_data_inventory(contract)}

O dossiê estruturado conserva integralmente valores reportados, propostos, utilizados e derivados.
As tabelas seguintes apresentam as séries materiais para a leitura do parecer.

## 4. Análise econômico-operacional

{_md(narrative.analise_economico_operacional.texto)}

### 4.1 Contas utilizadas e derivadas

{_series_table([*contract.dados.utilizados, *contract.dados.derivados], ACCOUNT_LABELS, years, ACCOUNT_LABELS)}

### 4.2 Indicadores e trajetória

{_series_table(contract.dados.indices, ECONOMIC_INDICATORS, years, INDICATOR_LABELS)}

## 5. Análise financeira e patrimonial

{_md(narrative.analise_financeira_patrimonial.texto)}

{_series_table(contract.dados.indices, FINANCIAL_INDICATORS, years, INDICATOR_LABELS)}

## 6. Formação e interpretação do FinScore

{_md(narrative.formacao_finscore.texto)}

{_score_table(contract)}

{_score_chart(contract)}

### 6.1 Caps prudenciais

{_caps_table(contract)}

FinScore não representa probabilidade de inadimplência nem rating regulatório. Núcleos, métodos,
gargalo, caps e resultado prudencial possuem funções próprias e não devem ser confundidos.

## 7. Estresse, sensibilidade e evidências suplementares

{_md(narrative.estresse_e_evidencias.texto)}

### 7.1 Cenários determinísticos

{_scenario_table(contract)}

{_scenario_chart(contract)}

Os cenários são hipóteses condicionais, não previsões. Frequências de simulação não equivalem a
probabilidade de inadimplência.

### 7.2 Simulação

{_simulation_table(contract)}

### 7.3 Evidências suplementares

{_supplementary_table(contract)}

Serasa não é somado ao FinScore. Springate e Fleuriet são diagnósticos derivados e suplementares.

## 8. Tese de crédito e governança

{_md(narrative.tese_credito_governanca.texto)}

### 8.1 Fundamentação da recomendação

{_plain_items(recommendation.fundamentos)}

### 8.2 Garantia e monitoramento

{_md(guarantee.justificativa)}

{_plain_items(recommendation.providencias)}

Na ausência de parâmetros institucionais completos, as medidas são apresentadas como monitoramento
ou diligência recomendada, e não como covenant contratual definido.

### 8.3 Posições registradas

{_governance_table(contract)}

## 9. Riscos, diligências e monitoramento

{_md(narrative.riscos_diligencias_monitoramento.texto)}

### 9.1 Pontos fortes comprovados

{_items(narrative.pontos_fortes)}

### 9.2 Riscos prioritários

{_items(narrative.riscos_prioritarios)}

### 9.3 Validações pendentes

{_items(narrative.validacoes_pendentes)}

### 9.4 Monitoramento recomendado

{_items(narrative.recomendacoes_monitoramento)}

## 10. Conclusão da análise

{_md(narrative.conclusao.texto)}

**Recomendação FinScore: {_md(recommendation.rotulo)}.** A decisão institucional compete à alçada
e somente é reconhecida neste parecer quando houver registro próprio na governança.

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

### 2. Livro de evidências materiais

{_material_findings_table(contract)}
""".strip()


__all__ = [
    "load_methodology",
    "methodology_sha256",
    "render_structured_parecer",
]
