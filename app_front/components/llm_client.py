from typing import Any, Dict
import json
import logging
import os
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


def build_prompt(artifact_title: str, mini_ctx: Dict[str, Any], dados_resumo: Dict[str, Any]) -> str:
    return (
        f"Contexto resumido: {mini_ctx}\n"
        f"Artefato: {artifact_title}\n"
        f"Dados-chave: {dados_resumo}\n"
        "Tarefa: Em ate 120 palavras, avalie SINAL, CONSISTENCIA e RISCO.\n"
        'Saida JSON: {"insight":"...", "riscos":["..."], "acao":["..."], "sinal":"positivo|neutro|negativo"}'
    )


REVIEW_SYSTEM = (
    "Voce e um analista de credito. Avalie um artefato (grafico ou tabela) "
    "em no maximo 120 palavras e retorne APENAS um JSON com as chaves: "
    '{"insight":"...", "riscos":["..."], "acao":["..."], "sinal":"positivo|neutro|negativo"}'
)


def call_review_llm(artifact_title: str, mini_ctx: Dict[str, Any], dados_resumo: Dict[str, Any]) -> ReviewSchema:
    messages = [
        {"role": "system", "content": REVIEW_SYSTEM},
        {"role": "user", "content": build_prompt(artifact_title, mini_ctx, dados_resumo)},
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
