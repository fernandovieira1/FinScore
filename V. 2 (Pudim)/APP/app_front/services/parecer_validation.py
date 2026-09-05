"""Validação factual, decisória, semântica e editorial do parecer."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
import unicodedata
from typing import Iterable

try:  # Execução Streamlit, com app_front no sys.path.
    from components.parecer_data_schema import (
        Finding,
        FindingCategory,
        ParecerData,
        RecommendationCode,
    )
    from components.parecer_schema import NarrativeItem, NarrativeSection, ParecerNarrativo
except ModuleNotFoundError:  # Importação como pacote nos testes.
    from app_front.components.parecer_data_schema import (
        Finding,
        FindingCategory,
        ParecerData,
        RecommendationCode,
    )
    from app_front.components.parecer_schema import (
        NarrativeItem,
        NarrativeSection,
        ParecerNarrativo,
    )


SECTION_NAMES = (
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
ITEM_COLLECTIONS = (
    "pontos_fortes",
    "riscos_prioritarios",
    "validacoes_pendentes",
    "recomendacoes_monitoramento",
)
NUMBER_PATTERN = re.compile(
    r"(?<![\w-])-?\d{1,3}(?:\.\d{3})*(?:,\d+)?%?|(?<![\w-])-?\d+(?:[.,]\d+)?%?"
)
FORBIDDEN_TERMS = {
    "inteligência artificial": "tecnologia de geração",
    "modelo de linguagem": "tecnologia de geração",
    "openai": "fornecedor técnico",
    "prompt": "processo técnico",
    "automação": "processo técnico",
    "pudim": "nome interno",
    "brigadeiro": "nome interno",
}


@dataclass(frozen=True)
class ValidationIssue:
    codigo: str
    local: str
    mensagem: str


@dataclass(frozen=True)
class ParecerValidationReport:
    valido: bool
    problemas: tuple[ValidationIssue, ...]
    numeros_verificados: int
    referencias_verificadas: int


class ParecerValidationError(ValueError):
    def __init__(self, report: ParecerValidationReport):
        self.report = report
        summary = "; ".join(
            f"{item.local}: {item.mensagem}" for item in report.problemas[:5]
        )
        super().__init__("parecer reprovado na validação: " + summary)


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _finding_map(contract: ParecerData) -> dict[str, Finding]:
    return {item.achado_id: item for item in contract.achados}


def _iter_text_blocks(
    narrative: ParecerNarrativo,
) -> Iterable[tuple[str, str, list[str]]]:
    for name in SECTION_NAMES:
        section: NarrativeSection = getattr(narrative, name)
        yield name, section.texto, section.achado_ids
    for collection_name in ITEM_COLLECTIONS:
        collection: list[NarrativeItem] = getattr(narrative, collection_name)
        for index, item in enumerate(collection, 1):
            yield f"{collection_name}[{index}]", item.texto, item.achado_ids


def _parse_number(token: str) -> tuple[float | None, bool]:
    percent = token.endswith("%")
    text = token.rstrip("%")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    elif re.fullmatch(r"-?\d{1,3}\.\d{3}", text):
        # 1.000 é mais frequentemente milhar em português; 0.xxx permanece decimal.
        if not text.startswith(("0.", "-0.")):
            text = text.replace(".", "")
    try:
        value = float(text)
    except ValueError:
        return None, percent
    return (value if math.isfinite(value) else None), percent


def _authorized_numbers(findings: Iterable[Finding]) -> list[float]:
    values: list[float] = []
    for finding in findings:
        for evidence in finding.evidencias:
            if evidence.exercicio is not None:
                values.append(float(evidence.exercicio))
            value = evidence.valor
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            number = float(value)
            if math.isfinite(number):
                values.append(number)
    return values


def _matches_authorized(value: float, percent: bool, authorized: list[float]) -> bool:
    candidates = [value / 100.0, value] if percent else [value]
    for candidate in candidates:
        for reference in authorized:
            tolerance = max(0.011, abs(reference) * 0.0015)
            if abs(candidate - reference) <= tolerance:
                return True
    return False


def _validate_references(
    narrative: ParecerNarrativo,
    contract: ParecerData,
    routes: dict[str, list[str]] | None,
) -> tuple[list[ValidationIssue], int]:
    issues: list[ValidationIssue] = []
    finding_map = _finding_map(contract)
    references = 0
    all_referenced: set[str] = set()
    for local, _text, finding_ids in _iter_text_blocks(narrative):
        references += len(finding_ids)
        all_referenced.update(finding_ids)
        unknown = [identifier for identifier in finding_ids if identifier not in finding_map]
        if unknown:
            issues.append(
                ValidationIssue(
                    "REF_INEXISTENTE",
                    local,
                    "referência a achado inexistente: " + ", ".join(unknown),
                )
            )
        if routes and local in SECTION_NAMES:
            suggested = set(routes.get(local) or [])
            if suggested and not suggested.intersection(finding_ids):
                issues.append(
                    ValidationIssue(
                        "REF_FORA_ROTEIRO",
                        local,
                        "a seção não referencia nenhum achado previsto em seu roteiro",
                    )
                )

    blocking = {
        item.achado_id
        for item in contract.achados
        if item.categoria is FindingCategory.BLOCK
    }
    missing_blockers = blocking - all_referenced
    if missing_blockers:
        issues.append(
            ValidationIssue(
                "BLOQUEIO_OMITIDO",
                "parecer",
                "bloqueios não referenciados: " + ", ".join(sorted(missing_blockers)),
            )
        )
    return issues, references


def _validate_item_categories(
    narrative: ParecerNarrativo,
    contract: ParecerData,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    findings = _finding_map(contract)
    allowed = {
        "pontos_fortes": {FindingCategory.STRENGTH},
        "riscos_prioritarios": {
            FindingCategory.RISK,
            FindingCategory.ALERT,
            FindingCategory.BLOCK,
            FindingCategory.DIVERGENCE,
        },
        "validacoes_pendentes": {
            FindingCategory.BLOCK,
            FindingCategory.LIMITATION,
            FindingCategory.ALERT,
            FindingCategory.DIVERGENCE,
        },
        "recomendacoes_monitoramento": {
            FindingCategory.RISK,
            FindingCategory.ALERT,
            FindingCategory.LIMITATION,
            FindingCategory.DIVERGENCE,
        },
    }
    for collection_name, allowed_categories in allowed.items():
        for index, item in enumerate(getattr(narrative, collection_name), 1):
            categories = {
                findings[identifier].categoria
                for identifier in item.achado_ids
                if identifier in findings
            }
            if categories and not categories.intersection(allowed_categories):
                issues.append(
                    ValidationIssue(
                        "CATEGORIA_INCOMPATIVEL",
                        f"{collection_name}[{index}]",
                        "as referências não sustentam a natureza do item",
                    )
                )
    return issues


def _validate_numbers(
    narrative: ParecerNarrativo,
    contract: ParecerData,
) -> tuple[list[ValidationIssue], int]:
    issues: list[ValidationIssue] = []
    finding_map = _finding_map(contract)
    verified = 0
    for local, text, finding_ids in _iter_text_blocks(narrative):
        authorized = _authorized_numbers(
            finding_map[identifier]
            for identifier in finding_ids
            if identifier in finding_map
        )
        for token in NUMBER_PATTERN.findall(text):
            value, percent = _parse_number(token)
            if value is None:
                continue
            verified += 1
            if not _matches_authorized(value, percent, authorized):
                issues.append(
                    ValidationIssue(
                        "NUMERO_SEM_LASTRO",
                        local,
                        f"o número {token} não consta nas evidências referenciadas",
                    )
                )
    return issues, verified


def _validate_semantics(
    narrative: ParecerNarrativo,
    contract: ParecerData,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    blocks = list(_iter_text_blocks(narrative))
    combined = "\n".join(text for _local, text, _ids in blocks)
    normalized = _plain(combined)
    for term, nature in FORBIDDEN_TERMS.items():
        if _plain(term) in normalized:
            issues.append(
                ValidationIssue("TERMO_RESTRITO", "parecer", f"menção indevida a {nature}: {term}")
            )
    if re.search(r"decis[aã]o\s+final|recomenda[cç][aã]o\s+final", combined, re.IGNORECASE):
        issues.append(
            ValidationIssue(
                "GOVERNANCA_CONFUNDIDA",
                "parecer",
                "a recomendação FinScore foi confundida com decisão final",
            )
        )
    if re.search(
        r"finscore.{0,45}(?:pd|probabilidade de (?:default|inadimpl[eê]ncia))|"
        r"(?:pd|probabilidade de (?:default|inadimpl[eê]ncia)).{0,45}finscore",
        combined,
        re.IGNORECASE | re.DOTALL,
    ):
        issues.append(
            ValidationIssue("FINSCORE_COMO_PD", "parecer", "FinScore foi apresentado como PD")
        )
    if re.search(
        r"(?:monte carlo|simula[cç][aã]o).{0,55}(?:probabilidade|chance).{0,35}(?:default|inadimpl)",
        combined,
        re.IGNORECASE | re.DOTALL,
    ):
        issues.append(
            ValidationIssue(
                "SIMULACAO_COMO_PD",
                "parecer",
                "frequência de simulação foi tratada como inadimplência",
            )
        )
    if re.search(r"cen[aá]rio.{0,35}(?:previs[aã]o|proje[cç][aã]o certa)", combined, re.IGNORECASE):
        issues.append(
            ValidationIssue("CENARIO_PREDITIVO", "parecer", "cenário foi tratado como previsão")
        )
    if re.search(r"\bcovenants?\b", combined, re.IGNORECASE):
        issues.append(
            ValidationIssue(
                "COVENANT_NAO_PARAMETRIZADO",
                "parecer",
                "foi definido covenant sem parâmetros institucionais completos",
            )
        )
    guarantee = contract.governanca.recomendacao_finscore.garantia
    if guarantee.cobertura_minima is None and re.search(
        r"garantia.{0,60}\d+(?:[.,]\d+)?%", combined, re.IGNORECASE | re.DOTALL
    ):
        issues.append(
            ValidationIssue(
                "COBERTURA_INVENTADA",
                "parecer",
                "foi atribuída cobertura percentual de garantia sem dado informado",
            )
        )

    recommendation = contract.governanca.recomendacao_finscore.codigo
    labels = {
        RecommendationCode.APPROVE: r"aprovar",
        RecommendationCode.DO_NOT_APPROVE: r"n[aã]o aprovar",
        RecommendationCode.INCONSISTENT_DATA: r"dados inconsistentes",
    }
    explicit = re.findall(
        r"recomenda[cç][aã]o\s+(?:finscore\s+)?(?:é|permanece|foi|:)\s*"
        r"(aprovar|n[aã]o aprovar|dados inconsistentes)",
        combined,
        re.IGNORECASE,
    )
    expected = re.compile(labels[recommendation], re.IGNORECASE)
    if any(not expected.fullmatch(value.strip()) for value in explicit):
        issues.append(
            ValidationIssue(
                "RECOMENDACAO_DIVERGENTE",
                "parecer",
                "o texto altera a recomendação FinScore registrada",
            )
        )
    return issues


def _word_set(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-záàâãéêíóôõúç]{4,}", text.lower())
        if word not in {"para", "como", "pela", "pelos", "entre", "sobre", "esta", "este"}
    }


def _validate_editorial(narrative: ParecerNarrativo) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    sections = [(name, getattr(narrative, name).texto) for name in SECTION_NAMES]
    for name, text in sections:
        if re.search(r"(?m)^\s*(?:#{1,6}\s|[-*]\s|\|.+\|)", text):
            issues.append(
                ValidationIssue(
                    "MARKDOWN_INTERNO",
                    name,
                    "a seção contém título, lista ou tabela que pertence ao renderizador",
                )
            )
    for index, (left_name, left_text) in enumerate(sections):
        left = _word_set(left_text)
        if len(left) < 20:
            continue
        for right_name, right_text in sections[index + 1 :]:
            right = _word_set(right_text)
            union = left | right
            similarity = len(left & right) / len(union) if union else 0.0
            if similarity >= 0.82:
                issues.append(
                    ValidationIssue(
                        "REPETICAO_MATERIAL",
                        f"{left_name}/{right_name}",
                        f"similaridade lexical excessiva ({similarity:.0%})",
                    )
                )
    for collection_name in ITEM_COLLECTIONS:
        for index, item in enumerate(getattr(narrative, collection_name), 1):
            if "\n" in item.texto or re.match(r"\s*[-*]", item.texto):
                issues.append(
                    ValidationIssue(
                        "ITEM_FORMATADO",
                        f"{collection_name}[{index}]",
                        "o item deve conter apenas texto simples",
                    )
                )
    return issues


def validate_parecer_narrative(
    narrative: ParecerNarrativo,
    contract: ParecerData,
    *,
    routes: dict[str, list[str]] | None = None,
    raise_on_error: bool = True,
) -> ParecerValidationReport:
    issues, reference_count = _validate_references(narrative, contract, routes)
    issues.extend(_validate_item_categories(narrative, contract))
    number_issues, number_count = _validate_numbers(narrative, contract)
    issues.extend(number_issues)
    issues.extend(_validate_semantics(narrative, contract))
    issues.extend(_validate_editorial(narrative))
    report = ParecerValidationReport(
        valido=not issues,
        problemas=tuple(issues),
        numeros_verificados=number_count,
        referencias_verificadas=reference_count,
    )
    if raise_on_error and not report.valido:
        raise ParecerValidationError(report)
    return report


__all__ = [
    "ParecerValidationError",
    "ParecerValidationReport",
    "ValidationIssue",
    "validate_parecer_narrative",
]
