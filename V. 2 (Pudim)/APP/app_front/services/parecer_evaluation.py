"""Avaliação determinística do documento montado e de sua cobertura material."""

from __future__ import annotations

from dataclasses import dataclass
import re

try:  # Execução Streamlit, com app_front no sys.path.
    from components.parecer_data_schema import FindingCategory, ParecerData
    from components.parecer_schema import ParecerNarrativo
    from services.parecer_document import load_methodology
    from services.parecer_validation import validate_parecer_narrative
except ModuleNotFoundError:  # Importação como pacote nos testes.
    from app_front.components.parecer_data_schema import FindingCategory, ParecerData
    from app_front.components.parecer_schema import ParecerNarrativo
    from app_front.services.parecer_document import load_methodology
    from app_front.services.parecer_validation import validate_parecer_narrative


BODY_HEADINGS = (
    "## 1. Identificação, operação e escopo",
    "## 2. Sumário executivo",
    "## 3. Escopo e qualidade da informação",
    "## 4. Análise econômico-operacional",
    "## 5. Análise financeira e patrimonial",
    "## 6. Formação e interpretação do FinScore",
    "## 7. Estresse, sensibilidade e evidências suplementares",
    "## 8. Tese de crédito e recomendação",
    "## 9. Riscos, diligências e monitoramento",
    "## 10. Conclusão da análise",
)
FORBIDDEN_DOCUMENT_TERMS = re.compile(
    r"\b(?:IA|OpenAI|GPT(?:-[A-Za-z0-9.]+)?|prompt|Pudim|Brigadeiro|"
    r"intelig[eê]ncia artificial|modelo de linguagem)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class DocumentEvaluationIssue:
    codigo: str
    mensagem: str


@dataclass(frozen=True)
class DocumentEvaluationReport:
    valido: bool
    problemas: tuple[DocumentEvaluationIssue, ...]
    achados_referenciados: int
    achados_materiais: int
    cobertura_material: float
    paginas: int | None


class DocumentEvaluationError(ValueError):
    def __init__(self, report: DocumentEvaluationReport):
        self.report = report
        super().__init__(
            "documento reprovado na avaliação: "
            + "; ".join(item.mensagem for item in report.problemas[:5])
        )


def evaluate_parecer_document(
    narrative: ParecerNarrativo,
    contract: ParecerData,
    document: str,
    *,
    routes: dict[str, list[str]] | None = None,
    pages: int | None = None,
    raise_on_error: bool = True,
) -> DocumentEvaluationReport:
    issues: list[DocumentEvaluationIssue] = []
    narrative_validation = validate_parecer_narrative(
        narrative,
        contract,
        routes=routes,
        raise_on_error=False,
    )
    if not narrative_validation.valido:
        issues.append(
            DocumentEvaluationIssue(
                "NARRATIVA_INVALIDA",
                "a narrativa não passou pelas validações factual e editorial",
            )
        )

    for heading in BODY_HEADINGS:
        if document.count(heading) != 1:
            issues.append(
                DocumentEvaluationIssue(
                    "ESTRUTURA_INVALIDA",
                    f"a seção {heading.removeprefix('## ')} deve ocorrer uma única vez",
                )
            )
    if document.count("## Anexo 1 — Metodologia") != 1:
        issues.append(
            DocumentEvaluationIssue("ANEXO_METODOLOGIA", "anexo metodológico ausente ou duplicado")
        )
    if document.count("## Anexo 2 — Informações da análise") != 1:
        issues.append(
            DocumentEvaluationIssue("ANEXO_REPRODUCAO", "anexo de reprodução ausente ou duplicado")
        )

    expected_methodology = load_methodology().replace(
        "## Metodologia", "## Anexo 1 — Metodologia", 1
    )
    if expected_methodology not in document:
        issues.append(
            DocumentEvaluationIssue(
                "METODOLOGIA_DIVERGENTE",
                "o anexo não corresponde integralmente à fonte metodológica versionada",
            )
        )
    if FORBIDDEN_DOCUMENT_TERMS.search(document):
        issues.append(
            DocumentEvaluationIssue(
                "TERMO_TECNICO_RESTRITO",
                "o documento funcional contém referência à tecnologia de redação",
            )
        )

    chart_count = document.count('<figure class="finscore-chart">')
    if chart_count:
        if document.count("<figcaption>") != chart_count:
            issues.append(DocumentEvaluationIssue("GRAFICO_SEM_TITULO", "gráfico sem título"))
        if document.count('class="chart-source"') != chart_count:
            issues.append(DocumentEvaluationIssue("GRAFICO_SEM_FONTE", "gráfico sem fonte"))
        if any(
            not fragment.strip()
            for fragment in re.findall(r'<span class="chart-value">(.*?)</span>', document)
        ):
            issues.append(DocumentEvaluationIssue("GRAFICO_SEM_VALOR", "gráfico sem valor exibido"))

    years = contract.identificacao.periodos.analisado.exercicios
    if any(str(year) not in document for year in years):
        issues.append(
            DocumentEvaluationIssue(
                "PERIODO_OMITIDO", "um exercício do período analisado não consta do documento"
            )
        )
    if pages is not None and not 7 <= pages <= 14:
        issues.append(
            DocumentEvaluationIssue(
                "PAGINACAO_INVALIDA",
                f"o PDF contém {pages} páginas; a faixa aceita é de 7 a 14",
            )
        )

    referenced = narrative.referenced_finding_ids()
    material = {
        item.achado_id
        for item in contract.achados
        if item.categoria is not FindingCategory.RESULT
    }
    blocker_ids = {
        item.achado_id
        for item in contract.achados
        if item.categoria is FindingCategory.BLOCK
    }
    if not blocker_ids.issubset(referenced):
        issues.append(
            DocumentEvaluationIssue(
                "BLOQUEIO_SEM_COBERTURA", "nem todos os bloqueios são citados pela narrativa"
            )
        )
    covered = len(material & referenced)
    coverage = covered / len(material) if material else 1.0
    report = DocumentEvaluationReport(
        valido=not issues,
        problemas=tuple(issues),
        achados_referenciados=len(referenced),
        achados_materiais=len(material),
        cobertura_material=coverage,
        paginas=pages,
    )
    if raise_on_error and not report.valido:
        raise DocumentEvaluationError(report)
    return report


__all__ = [
    "BODY_HEADINGS",
    "DocumentEvaluationError",
    "DocumentEvaluationIssue",
    "DocumentEvaluationReport",
    "evaluate_parecer_document",
]
