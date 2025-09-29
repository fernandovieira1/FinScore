from typing import Any, Dict, List, Optional
import json
import logging
import os
import unicodedata
from dataclasses import dataclass

import requests
from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()

from .schemas import ReviewSchema

logger = logging.getLogger(__name__)


@dataclass
class _SimpleMessage:
    content: str


def _maybe_get_langchain_client(model: str, temperature: float):
    # LangChain client disabled: environment lacks compatible dependencies.
    return None


def _call_openai_rest(messages, model: str, temperature: float) -> _SimpleMessage:
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

    response = requests.post(endpoint, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - API drift
        raise RuntimeError(f"Unexpected OpenAI response: {data}") from exc
    return _SimpleMessage(content=content)


def _invoke_model(messages, model: str, temperature: float) -> str:
    _maybe_get_langchain_client(model, temperature)  # noop (mantido para compatibilidade futura)

    tried_models: List[str] = []
    last_exc: Exception | None = None
    candidates = [model] + [fallback for fallback in MODEL_FALLBACKS if fallback and fallback != model]

    for candidate in candidates:
        tried_models.append(candidate)
        try:
            response = _call_openai_rest(messages, model=candidate, temperature=temperature)
            if candidate != model:
                logger.info("LLM fallback: usando modelo %s (preferido: %s)", candidate, model)
            return response.content
        except requests.exceptions.HTTPError as exc:  # type: ignore[attr-defined]
            status = exc.response.status_code if exc.response is not None else None
            if status in (400, 404):
                logger.warning("Modelo %s indisponivel (%s). Tentando proxima opcao.", candidate, status)
                last_exc = exc
                continue
            logger.error("Falha HTTP ao consultar modelo %s: %s", candidate, exc)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Falha ao consultar modelo %s: %s", candidate, exc)
            last_exc = exc
            break

    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"Nao foi possivel invocar nenhum modelo: {tried_models}")


MODEL_NAME = os.getenv("FINSCORE_LLM_MODEL", "gpt-4o-mini")
MODEL_TEMPERATURE = float(os.getenv("FINSCORE_LLM_TEMPERATURE", "0.1"))
MODEL_FALLBACKS = [
    model for model in (
        os.getenv("FINSCORE_LLM_FALLBACK1", "gpt-4o-mini"),
        os.getenv("FINSCORE_LLM_FALLBACK2", "gpt-4o"),
        os.getenv("FINSCORE_LLM_FALLBACK3", "gpt-4.1-mini"),
    )
    if model
]


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
        snapshot = {
            "nome": nome,
            "ultimo": info.get("ultimo"),
            "tendencia": info.get("tendencia"),
            "variacao_percentual": info.get("variacao_percentual"),
        }
        if review_kind == "indices":
            normalized = _normalize_label(str(nome))
            metadata = INDEX_METADATA.get(normalized, {})
            if metadata.get("grupo"):
                snapshot["grupo"] = metadata["grupo"]
            if metadata.get("formula"):
                snapshot["formula"] = metadata["formula"]
        metrics.append({k: v for k, v in snapshot.items() if v not in (None, "")})
    return metrics


def build_prompt(artifact_id: str, artifact_meta: Dict[str, Any]) -> str:
    review_kind = artifact_meta.get("review_kind", "raw")
    title = artifact_meta.get("title")
    mini_ctx = artifact_meta.get("mini_ctx", {})
    dados_resumo = artifact_meta.get("dados_resumo", {})
    metrics_payload = _prepare_metrics_payload(dados_resumo, review_kind)
    metrics_text = json.dumps(metrics_payload, ensure_ascii=False, separators=(",", ":"))
    minimal_ctx = {key: mini_ctx[key] for key in ("empresa", "anos_disponiveis") if key in mini_ctx}
    ctx_text = json.dumps(minimal_ctx, ensure_ascii=False)

    if review_kind == "indices":
        instructions = f"""
Analise rapida dos indices do artefato \"{title}\".
Contexto: {ctx_text}
Resumo em JSON: {metrics_text}

Escreva UMA frase (ate 25 palavras) explicando o comportamento dominante dos indices e o impacto no risco; cite apenas um numero essencial, se preciso.
Defina `sinal` como \"positivo\", \"neutro\" ou \"negativo\" coerente com a frase.
Preencha `riscos` com no maximo um alerta objetivo; deixe a lista vazia se nao houver alerta imediato.

Retorne apenas {{\"insight\": str, \"riscos\": list[str], \"sinal\": str}}.
"""
    else:
        instructions = f"""
Analise rapida das contas do artefato \"{title}\".
Contexto: {ctx_text}
Resumo em JSON: {metrics_text}

Escreva UMA frase (ate 25 palavras) descrevendo o movimento principal das contas e suas implicacoes; cite um numero chave somente se indispensavel.
Defina `sinal` como \"positivo\", \"neutro\" ou \"negativo\" coerente com a frase.
Preencha `riscos` com no maximo um alerta objetivo; deixe a lista vazia se nao houver alerta imediato.

Retorne apenas {{\"insight\": str, \"riscos\": list[str], \"sinal\": str}}.
"""


    return instructions.strip()


REVIEW_SYSTEM = (
    "Voce e um analista de credito. Responda SEMPRE com um unico JSON {\"insight\": str, \"riscos\": [str], \"sinal\": \"positivo|neutro|negativo\"}. "
    "O campo 'insight' deve ser uma frase curta e objetiva. Use 'riscos' apenas para alertas diretos (pode ficar vazio) e 'sinal' deve resumir a visao final. Nao escreva nada fora do JSON."
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
            "sinal": "neutro",
        }
        return ReviewSchema(**fallback_payload)

    try:
        start = text.find("{")
        end = text.rfind("}")
        candidate = text[start : end + 1]
        payload = json.loads(candidate)
    except Exception:
        payload = {"insight": text.strip(), "riscos": [], "sinal": "neutro"}

    payload.pop("acoes", None)
    payload.pop("acao", None)

    try:
        return ReviewSchema(**payload)
    except ValidationError:
        fallback = {"insight": str(payload)[:400], "riscos": [], "sinal": "neutro"}
        return ReviewSchema(**fallback)
