"""
Helpers para contagem de tokens e estimativa de custo.
Colocado em app_front/components para fácil importação nas views.
"""
import time
from typing import List, Dict, Optional
import os

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except Exception:
    TIKTOKEN_AVAILABLE = False

# Mapeamento padrão de modelos para encodings tiktoken
MODEL_TO_ENCODING = {
    "gpt-4o": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-4-0613": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-3.5-turbo-0613": "cl100k_base",
}


def _get_encoding_for_model(model: str):
    enc_name = MODEL_TO_ENCODING.get(model, "cl100k_base")
    if not TIKTOKEN_AVAILABLE:
        return None
    try:
        return tiktoken.get_encoding(enc_name)
    except Exception:
        try:
            return tiktoken.encoding_for_model(model)
        except Exception:
            return tiktoken.get_encoding("cl100k_base")


def count_text_tokens(model: str, text: str) -> int:
    """Conta tokens em um texto simples para o modelo especificado."""
    if not text:
        return 0
    if TIKTOKEN_AVAILABLE:
        enc = _get_encoding_for_model(model)
        if enc:
            try:
                return len(enc.encode(text))
            except Exception:
                pass
    # fallback aproximado: ~4 caracteres por token
    return max(1, int(len(text) / 4))


def count_messages_tokens(model: str, messages: List[Dict]) -> int:
    """
    Conta tokens em mensagens no formato chat (lista de dicts com role/name/content).
    Implementação simples compatível com a heurística recomendada pela OpenAI/tiktoken.
    """
    if not messages:
        return 0
    if TIKTOKEN_AVAILABLE:
        enc = _get_encoding_for_model(model)
        if enc is None:
            # fallback para soma dos conteúdos
            return sum(count_text_tokens(model, m.get("content", "")) for m in messages)
        tokens_per_message = 4
        tokens_per_name = -1
        total = 0
        for m in messages:
            total += tokens_per_message
            for k, v in m.items():
                if k == "name":
                    total += tokens_per_name
                total += len(enc.encode(str(v)))
        total += 2
        return total
    # fallback simplificado
    combined = "\n".join((m.get("role", "") + ": " + m.get("content", "") for m in messages))
    return count_text_tokens(model, combined)


def estimate_cost_usd(tokens: int, price_per_1k_usd: float) -> float:
    try:
        return float(tokens) * (float(price_per_1k_usd) / 1000.0)
    except Exception:
        return 0.0


def now_ts() -> int:
    return int(time.time())
