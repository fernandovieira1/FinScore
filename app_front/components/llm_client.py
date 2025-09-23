from typing import Any, Dict
import json
import os

from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from .schemas import ReviewSchema


def _get_llm(model: str = "gpt-4o-mini", temperature: float = 0.2) -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)


REVIEW_SYSTEM = (
    "Voce e um analista de credito. Avalie um artefato (grafico ou tabela) "
    "em no maximo 120 palavras e retorne APENAS um JSON com as chaves: "
    '{"insight":"...", "riscos":["..."], "acao":["..."], "sinal":"positivo|neutro|negativo"}'
)


def build_prompt(artifact_title: str, mini_ctx: Dict[str, Any], dados_resumo: Dict[str, Any]) -> str:
    return (
        f"Contexto resumido: {mini_ctx}\n"
        f"Artefato: {artifact_title}\n"
        f"Dados-chave: {dados_resumo}\n"
        "Tarefa: Em ate 120 palavras, avalie SINAL, CONSISTENCIA e RISCO.\n"
        'Saida JSON: {"insight":"...", "riscos":["..."], "acao":["..."], "sinal":"positivo|neutro|negativo"}'
    )


def call_review_llm(artifact_title: str, mini_ctx: Dict[str, Any], dados_resumo: Dict[str, Any]) -> ReviewSchema:
    llm = _get_llm()
    prompt = build_prompt(artifact_title, mini_ctx, dados_resumo)
    messages = [
        {"role": "system", "content": REVIEW_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    response = llm.invoke(messages)
    text = getattr(response, "content", None) or str(response)

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
