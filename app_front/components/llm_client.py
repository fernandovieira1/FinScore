from typing import Any, Dict, List, Optional, Tuple
import json
import logging
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()

_env_candidates = [
    Path(__file__).resolve().parent.parent / '.env',
    Path(__file__).resolve().parent / '.env',
]
for _env_path in _env_candidates:
    try:
        if _env_path.is_file():
            load_dotenv(_env_path, override=False)
    except Exception:
        pass

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
) -> List[Tuple[str, Any]]:
    metrics: List[Tuple[str, Any]] = []
    for nome, info in dados_resumo.items():
        if len(metrics) >= 3:
            break
        valor = None
        if isinstance(info, dict):
            valor = info.get('ultimo')
            if valor is None:
                valor = info.get('valor')
        elif isinstance(info, (int, float)):
            valor = info
        if valor in (None, '', []):
            continue
        metrics.append((str(nome), valor))
    if not metrics and dados_resumo.get('nota'):
        metrics.append(('nota', dados_resumo['nota']))
    return metrics

def build_prompt(artifact_id: str, artifact_meta: Dict[str, Any]) -> str:
    title = artifact_meta.get('title')
    mini_ctx = artifact_meta.get('mini_ctx', {})
    dados_resumo = artifact_meta.get('dados_resumo', {})
    metrics_payload = _prepare_metrics_payload(dados_resumo, artifact_meta.get('review_kind', 'raw'))
    metrics_dict = {nome: valor for nome, valor in metrics_payload}
    metrics_text = json.dumps(metrics_dict, ensure_ascii=False, separators=(',', ':'))
    minimal_ctx = {key: mini_ctx[key] for key in ('empresa', 'anos_disponiveis') if key in mini_ctx}
    ctx_text = json.dumps(minimal_ctx, ensure_ascii=False) if minimal_ctx else 'null'

    instructions = f"""
Analise as metrics do artefato '{title}' e escreva um paragrafo curto (ate 25 palavras) com a visao principal do analista.
Classifique o parecer como positivo, neutro ou negativo, retornando apenas JSON no formato {{\"insight\": str, \"riscos\": list[str], \"sinal\": str}}.
Considere as metricas: {metrics_text} e o contexto basico: {ctx_text}.
"""

    return instructions.strip()



REVIEW_SYSTEM = (
    "Voce e um analista de credito. Responda SEMPRE com um unico JSON {\"insight\": str, \"riscos\": [str], \"acao\": [str], \"sinal\": \"positivo|neutro|negativo\"}. "
    "O campo 'insight' deve ser uma frase curta e objetiva (max 120 palavras). Use 'riscos' para alertas diretos, 'acao' para recomendacoes praticas (ambos podem ficar vazios) e 'sinal' deve resumir a visao final. Nao escreva nada fora do JSON."
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
        payload = {"insight": text.strip(), "riscos": [], "acao": [], "sinal": "neutro"}

    # Normalizar campo acao/acoes
    if "acoes" in payload and "acao" not in payload:
        payload["acao"] = payload.pop("acoes")
    elif "acao" not in payload:
        payload["acao"] = []

    try:
        return ReviewSchema(**payload)
    except ValidationError:
        fallback = {"insight": str(payload)[:400], "riscos": [], "acao": [], "sinal": "neutro"}
        return ReviewSchema(**fallback)