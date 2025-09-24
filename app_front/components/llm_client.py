from typing import Any, Dict, List, Optional
import json
import logging
import os
import unicodedata
from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()

from .schemas import ReviewSchema

logger = logging.getLogger(__name__)


@dataclass
class _SimpleMessage:
    content: str


def _maybe_get_langchain_client(model: str, temperature: float):
    try:
        from langchain_openai import ChatOpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.info("langchain_openai not available: %s", exc)
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY missing; cannot build ChatOpenAI client")
        return None

    try:
        return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)
    except TypeError as exc:
        if "proxies" in str(exc):
            logger.warning("ChatOpenAI rejected proxies argument; falling back to REST")
            return None
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("ChatOpenAI initialization failed: %s", exc)
        return None


def _call_openai_rest(messages, model: str, temperature: float) -> _SimpleMessage:
    import requests

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    endpoint = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - API drift
        raise RuntimeError(f"Unexpected OpenAI response: {data}") from exc
    return _SimpleMessage(content=content)


def _invoke_model(messages, model: str, temperature: float) -> str:
    client = _maybe_get_langchain_client(model, temperature)
    if client is not None:
        try:
            result = client.invoke(messages)
            return getattr(result, "content", None) or str(result)
        except TypeError as exc:
            if "proxies" not in str(exc):
                raise
            logger.warning("ChatOpenAI invoke failed due to proxies: %s", exc)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("ChatOpenAI invocation failed: %s", exc)
    fallback = _call_openai_rest(messages, model=model, temperature=temperature)
    return fallback.content


MODEL_NAME = "gpt-4o-mini"
MODEL_TEMPERATURE = 0.2


INDEX_CATALOG: List[Dict[str, str]] = [
    {
        "grupo": "Liquidez",
        "indice": "Liquidez Corrente",
        "formula": "Ativo Circulante / Passivo Circulante",
    },
    {
        "grupo": "Liquidez",
        "indice": "Liquidez Seca",
        "formula": "(Ativo Circulante − Estoques) / Passivo Circulante",
    },
    {
        "grupo": "Rentabilidade",
        "indice": "Margem Líquida",
        "formula": "Lucro Líquido / Receita",
    },
    {
        "grupo": "Rentabilidade",
        "indice": "ROA",
        "formula": "Lucro Líquido / Ativo Total",
    },
    {
        "grupo": "Rentabilidade",
        "indice": "ROE",
        "formula": "Lucro Líquido / Patrimônio Líquido",
    },
    {
        "grupo": "Estrutura",
        "indice": "Endividamento",
        "formula": "Dívida Bruta / Ativo Total",
    },
    {
        "grupo": "Estrutura",
        "indice": "Imobilizado/Ativo",
        "formula": "Ativo Imobilizado / Ativo Total",
    },
    {
        "grupo": "Cobertura",
        "indice": "Cobertura de Juros",
        "formula": "EBIT / Despesa de Juros",
    },
    {
        "grupo": "Eficiência",
        "indice": "Giro do Ativo",
        "formula": "Receita / Ativo Total",
    },
    {
        "grupo": "Prazos",
        "indice": "PMR",
        "formula": "Contas a Receber / Receita × 365",
    },
    {
        "grupo": "Prazos",
        "indice": "PMP",
        "formula": "Contas a Pagar / Custos × 365",
    },
    {
        "grupo": "Liquidez",
        "indice": "CCL/Ativo Total",
        "formula": "(Ativo Circulante − Passivo Circulante) / Ativo Total",
    },
    {
        "grupo": "Estrutura",
        "indice": "DL/EBITDA",
        "formula": "Dívida Líquida / EBITDA",
    },
]


def _normalize_label(value: str) -> str:
    cleaned = unicodedata.normalize("NFKD", value)
    cleaned = cleaned.encode("ascii", "ignore").decode("ascii")
    for ch in "()[]":
        cleaned = cleaned.replace(ch, " ")
    cleaned = cleaned.replace("/", " ").replace("-", " ")
    cleaned = cleaned.replace("×", " ")
    return " ".join(cleaned.lower().split())


INDEX_METADATA: Dict[str, Dict[str, str]] = {}
for item in INDEX_CATALOG:
    key = _normalize_label(item["indice"])
    INDEX_METADATA[key] = {
        "grupo": item["grupo"],
        "indice": item["indice"],
        "formula": item["formula"],
    }

# Synonyms/simplifications for labels usados na UI
INDEX_METADATA["ccl ativo"] = INDEX_METADATA.get(_normalize_label("CCL/Ativo Total"), {})
INDEX_METADATA["liquidez corrente x"] = INDEX_METADATA.get(_normalize_label("Liquidez Corrente"), {})
INDEX_METADATA["liquidez seca x"] = INDEX_METADATA.get(_normalize_label("Liquidez Seca"), {})
INDEX_METADATA["ccl ativo x"] = INDEX_METADATA.get(_normalize_label("CCL/Ativo Total"), {})
INDEX_METADATA["cobertura x"] = INDEX_METADATA.get(_normalize_label("Cobertura de Juros"), {})
INDEX_METADATA["divida ativo x"] = INDEX_METADATA.get(_normalize_label("Endividamento"), {})
INDEX_METADATA["dl ebitda x"] = INDEX_METADATA.get(_normalize_label("DL/EBITDA"), {})


def _prepare_metrics_payload(
    dados_resumo: Dict[str, Any],
    review_kind: str,
) -> List[Dict[str, Any]]:
    metrics: List[Dict[str, Any]] = []
    for nome, info in dados_resumo.items():
        if not isinstance(info, dict):
            continue
        if "serie" not in info:
            continue
        normalized = _normalize_label(str(nome))
        metadata = INDEX_METADATA.get(normalized, {})
        metrics.append(
            {
                "nome": nome,
                "grupo": metadata.get("grupo") if review_kind == "indices" else None,
                "formula": metadata.get("formula") if review_kind == "indices" else None,
                "serie": info.get("serie"),
                "estatisticas": info.get("estatisticas"),
                "ultimo": info.get("ultimo"),
                "media": info.get("media"),
                "variacao_percentual": info.get("variacao_percentual"),
                "variacao_absoluta": info.get("variacao_absoluta"),
                "tendencia": info.get("tendencia"),
                "anos": info.get("anos"),
            }
        )
    return metrics


def build_prompt(artifact_id: str, artifact_meta: Dict[str, Any]) -> str:
    review_kind = artifact_meta.get("review_kind", "raw")
    title = artifact_meta.get("title")
    mini_ctx = artifact_meta.get("mini_ctx", {})
    dados_resumo = artifact_meta.get("dados_resumo", {})
    metrics_payload = _prepare_metrics_payload(dados_resumo, review_kind)
    metrics_text = json.dumps(metrics_payload, ensure_ascii=False, indent=2)
    ctx_text = json.dumps(mini_ctx, ensure_ascii=False, indent=2)

    if review_kind == "indices":
        catalog_text = json.dumps(INDEX_CATALOG, ensure_ascii=False, indent=2)
        instructions = f"""
Você é um especialista em análise financeira e contábil. Sua tarefa é interpretar profundamente os índices contábeis fornecidos, considerando três dimensões de análise.

Contexto do artefato: {title}
Contexto adicional: {ctx_text}

CATÁLOGO DE ÍNDICES (grupo, nome, fórmula):
{catalog_text}

DADOS FORNECIDOS (séries anuais, estatísticas e metadados por índice em JSON):
{metrics_text}

INSTRUÇÕES ESPECÍFICAS PARA A ANÁLISE:
1. ANÁLISE INDIVIDUAL POR ANO:
   - Para cada índice em cada ano, interprete qualitativamente o resultado numérico.
   - Contextualize o significado do valor obtido e cite explicitamente o número usado.
   - Classifique cada valor como "excelente", "bom", "regular", "ruim" ou "crítico" com base em parâmetros teóricos/setoriais.

2. ANÁLISE DE TENDÊNCIA TEMPORAL:
   - Identifique a direção da evolução entre os anos (aumento, diminuição ou estabilidade).
   - Informe a variação percentual entre o primeiro e o último ano disponível.
   - Avalie se a tendência é positiva, negativa ou neutra para a saúde financeira.
   - Destaque pontos de virada relevantes.

3. ANÁLISE ESTATÍSTICA DESCRITIVA:
   - Utilize os valores fornecidos em "estatísticas" (média, amplitude, desvio padrão, variância, mínimo, máximo) para comentar estabilidade e dispersão.
   - Relacione volatilidade com previsibilidade do indicador.

FORMATO DE SAÍDA EXIGIDO (coloque o relatório completo dentro do campo "insight" do JSON final):
Para cada índice, siga o layout:
"[Nome do Índice] - [Fórmula]"
- "Análise Anual Individual":
  - "20XX: [valor] → [interpretação qualitativa citando o número e a classificação]"
- "Tendência Temporal": descrição com variação percentual e classificação da tendência (positiva/negativa/estável).
- "Estatística Descritiva":
  * "Média: [valor] → [interpretação]"
  * "Dispersão: amplitude de [valor] entre [min] e [max]"
  * "Desvio Padrão" e "Variância" com leitura sobre volatilidade.

REQUISITOS:
- Use terminologia técnica com explicações claras.
- Contextualize cada índice dentro de seu grupo.
- Destaque inter-relações relevantes entre índices.
- Cite sempre os números que embasam cada afirmação.
- NÃO utilize informações de Serasa ou FinScore.

INSTRUÇÕES PARA O JSON DE SAÍDA:
- Retorne apenas um JSON com as chaves {{"insight": str, "riscos": list[str], "acoes": list[str], "sinal": str}}.
- Coloque o relatório completo acima no campo "insight".
- "riscos" deve listar até três riscos práticos identificados.
- "acoes" deve listar recomendações acionáveis.
- "sinal" deve ser "positivo", "neutro" ou "negativo", refletindo a visão geral.
"""
    else:
        instructions = f"""
Você é um especialista em análise contábil focado em dados brutos (valores absolutos e séries históricas). Analise o artefato "{title}" considerando as contas apresentadas.

Contexto adicional: {ctx_text}
DADOS FORNECIDOS (séries e estatísticas em JSON):
{metrics_text}

INSTRUÇÕES:
1. Para cada conta, descreva os níveis por ano, comparando valores e percentuais de variação (quando disponíveis). Cite explicitamente os números.
2. Identifique tendências (crescimento, queda, estabilidade) e explique possíveis implicações financeiras.
3. Use as estatísticas (média, amplitude, desvio padrão, variância) para avaliar a estabilidade.
4. Relacione contas entre si quando houver interdependência (ex.: Ativo vs Passivo).

FORMATO DO RELATÓRIO (coloque tudo no campo "insight" do JSON final):
- Para cada conta, apresente subtópicos com: panorama anual, tendência consolidada e leitura estatística (média, amplitude, volatilidade).
- Termine com um parágrafo síntese destacando implicações operacionais.

REQUISITOS:
- Cite sempre os valores numéricos.
- Explique termos técnicos de forma objetiva.
- Não utilize referências a Serasa ou FinScore.

JSON DE SAÍDA:
- Retorne apenas um JSON com as chaves {{"insight": str, "riscos": list[str], "acoes": list[str], "sinal": str}}.
- "insight" deve conter o relatório completo formatado.
- "riscos" traga até três riscos relevantes.
- "acoes" liste recomendações concretas.
- "sinal" deve refletir a visão geral (positivo, neutro ou negativo).
"""

    return instructions.strip()


REVIEW_SYSTEM = (
    "Você é um analista de crédito e risco financeiro. Responda SEMPRE com um único JSON contendo as chaves "
    '{"insight": str, "riscos": [str], "acoes": [str], "sinal": "positivo|neutro|negativo"}. '
    "O campo 'insight' deve trazer o relatório completo no formato exigido pelo usuário. Os campos 'riscos' e 'acoes' "
    "devem ser listas de strings e 'sinal' um resumo categórico da visão final. Nunca inclua texto fora do JSON."
)


def call_review_llm(artifact_id: str, artifact_meta: Dict[str, Any]) -> ReviewSchema:
    messages = [
        {"role": "system", "content": REVIEW_SYSTEM},
        {"role": "user", "content": build_prompt(artifact_id, artifact_meta)},
    ]

    try:
        text = _invoke_model(messages, MODEL_NAME, MODEL_TEMPERATURE)
    except Exception as exc:
        logger.error("Falha ao consultar LLM: %s", exc)
        fallback_payload = {
            "insight": f"Nao foi possivel gerar a analise automatica: {exc}",
            "riscos": [],
            "acoes": [],
            "sinal": "neutro",
        }
        return ReviewSchema(**fallback_payload)

    try:
        start = text.find("{")
        end = text.rfind("}")
        candidate = text[start : end + 1]
        payload = json.loads(candidate)
    except Exception:
        payload = {"insight": text.strip(), "riscos": [], "acoes": [], "sinal": "neutro"}

    if "acoes" not in payload and "acao" in payload:
        payload["acoes"] = payload.pop("acao")

    try:
        return ReviewSchema(**payload)
    except ValidationError:
        fallback = {"insight": str(payload)[:400], "riscos": [], "acoes": [], "sinal": "neutro"}
        return ReviewSchema(**fallback)
