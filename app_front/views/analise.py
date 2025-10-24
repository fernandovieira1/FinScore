# app_front/views/analise.py
# coding: utf-8
import copy
import html
import json
import math
import os
import statistics
import time
import unicodedata
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from components.llm_client import call_review_llm
from components.navigation_flow import NavigationFlow
from components.schemas import ReviewSchema
from components import nav

# imports RELATIVOS (arquivos no MESMO pacote 'views')
try:
    from .scores import render as render_scores
except Exception as exc:
    _SCORES_IMPORT_ERROR = str(exc)

    def render_scores():
        st.error(f"Nao foi possivel importar 'scores.py' (render). Detalhe: {_SCORES_IMPORT_ERROR}")

try:
    from .graficos import (
        prepare_base_data as prepare_graficos_data,
        render_ativo_passivo_circulante,
        render_receita_total,
        render_juros_lucro_receita,
    )
except Exception as exc:
    _GRAFICOS_IMPORT_ERROR = str(exc)

    def prepare_graficos_data():
        st.error(f"Nao foi possivel importar 'graficos.py'. Detalhe: {_GRAFICOS_IMPORT_ERROR}")
        return None

    def render_ativo_passivo_circulante(_df):
        st.error("Nao foi possivel preparar o grafico de Ativo e Passivo Circulante.")
        return False

    def render_receita_total(_df):
        st.error("Nao foi possivel preparar o grafico de Receita Total.")
        return False

    def render_juros_lucro_receita(_df):
        st.error("Nao foi possivel preparar o grafico de Juros, Lucro e Receita Total.")
        return False

try:
    from .tabelas import (
        get_indices_table,
        get_pca_scores_table,
        get_top_indices_table,
        get_pca_loadings_table,
    )
except Exception as exc:
    _TABELAS_IMPORT_ERROR = str(exc)

    def get_indices_table():
        st.error(f"Nao foi possivel importar 'tabelas.py'. Detalhe: {_TABELAS_IMPORT_ERROR}")
        return None

    def get_pca_scores_table():
        st.error("Nao foi possivel preparar a tabela de scores de PCA.")
        return None

    def get_top_indices_table():
        st.error("Nao foi possivel preparar a tabela de destaques do PCA.")
        return None

    def get_pca_loadings_table():
        st.error("Nao foi possivel preparar a tabela de loadings do PCA.")
        return None


try:
    from . import graficos as _graficos_module
except Exception:
    _graficos_module = None

try:
    from . import tabelas as _tabelas_module
except Exception:
    _tabelas_module = None


_REVIEW_EXECUTOR = ThreadPoolExecutor(max_workers=1)
_INSIGHT_STYLES_FLAG = "_insight_styles_loaded"
_INSIGHT_POLL_INTERVAL_MS = 1500
_INSIGHT_POLL_INTERVAL_SEC = _INSIGHT_POLL_INTERVAL_MS / 1000.0
_INSIGHT_POLL_LAST_KEY = "_insight_last_poll_ts"
_INSIGHT_POLL_FLAG = "_insight_polling_active"

_LLM_CALL_LOCK = threading.Lock()
_LLM_LAST_CALL_TS = [0.0]
_LLM_MIN_GAP = float(os.getenv("FINSCORE_LLM_MIN_GAP", "2.5"))
_LLM_MAX_RETRIES = int(os.getenv("FINSCORE_LLM_MAX_RETRIES", "3"))

_MAX_AUTO_ATTEMPTS = 2


def _on_aprovar():
    NavigationFlow.request_lock_parecer()


def _get_review_tasks() -> Dict[str, Dict[str, Any]]:
    return st.session_state.setdefault("_review_tasks", {})


def _call_review_llm_with_throttle(artifact_id: str, payload: Dict[str, Any]) -> ReviewSchema:
    attempts = 0
    last_error = None
    while attempts < _LLM_MAX_RETRIES:
        attempts += 1
        with _LLM_CALL_LOCK:
            now = time.time()
            wait = _LLM_MIN_GAP - (now - _LLM_LAST_CALL_TS[0])
            if wait > 0:
                time.sleep(wait)
            _LLM_LAST_CALL_TS[0] = time.time()
        try:
            return call_review_llm(artifact_id, payload)
        except Exception as exc:  # handle rate limit fallback
            message = str(exc).lower()
            if 'rate limit' in message or '429' in message:
                backoff = max(_LLM_MIN_GAP, _LLM_MIN_GAP * attempts)
                time.sleep(backoff)
                last_error = exc
                continue
            raise
    raise RuntimeError(f'Falha ao gerar insight apos {_LLM_MAX_RETRIES} tentativas: {last_error}')






def _ensure_insight_polling() -> None:
    # CRÍTICO: Só fazer polling se usuário ESTÁ em /Análise
    # Não fazer rerun automático se usuário navegou para outra página
    if st.query_params.get("p") != "analise":
        return
    
    tasks = _get_review_tasks()
    has_running = any((task or {}).get("status") in ("pending", "running") for task in tasks.values())
    timer_active = st.session_state.get(_INSIGHT_POLL_FLAG, False)

    if has_running:
        st.session_state[_INSIGHT_POLL_FLAG] = True
        st.markdown(
            f"""
            <script>
            if (window.__fsInsightTimer) {{
                clearTimeout(window.__fsInsightTimer);
            }}
            window.__fsInsightTimer = setTimeout(function () {{
                window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:rerun'}}, '*');
            }}, {_INSIGHT_POLL_INTERVAL_MS});
            </script>
            """,
            unsafe_allow_html=True,
        )
        last_ts = float(st.session_state.get(_INSIGHT_POLL_LAST_KEY, 0.0))
        now_ts = time.time()
        if now_ts - last_ts >= _INSIGHT_POLL_INTERVAL_SEC:
            st.session_state[_INSIGHT_POLL_LAST_KEY] = now_ts
            st.experimental_rerun()
    elif timer_active:
        st.session_state.pop(_INSIGHT_POLL_LAST_KEY, None)
        st.session_state[_INSIGHT_POLL_FLAG] = False
        st.markdown(
            """
            <script>
            if (window.__fsInsightTimer) {
                clearTimeout(window.__fsInsightTimer);
                window.__fsInsightTimer = null;
            }
            </script>
            """,
            unsafe_allow_html=True,
        )



def _ensure_insight_styles() -> None:
    if st.session_state.get(_INSIGHT_STYLES_FLAG):
        return
    st.markdown(
        """
        <link
            rel="stylesheet"
            href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
            integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
            crossorigin="anonymous"
        />
        <style>
        .insight-button-wrapper { display: inline-block; }
        .btn-insight {
            display: inline-block;
            padding: 0.45rem 1.4rem;
            border-radius: 0.375rem;
            font-weight: 600;
            border: none;
            color: #ffffff;
            background-color: #adb5bd;
            cursor: not-allowed;
            opacity: 0.65;
            transition: background-color 0.2s ease, transform 0.15s ease;
        }
        .btn-insight.ready {
            background-color: #198754;
            cursor: pointer;
            opacity: 1;
        }
        .btn-insight.ready:hover { background-color: #157347; }
        .btn-insight:focus {
            outline: none;
            box-shadow: 0 0 0 0.25rem rgba(25, 135, 84, 0.25);
        }
        .insight-spinner {
            display: inline-block;
            width: 1rem;
            height: 1rem;
            border-radius: 50%;
            border: 0.16rem solid #0d6efd;
            border-top-color: transparent;
            animation: insight-spin 0.75s linear infinite;
            margin-top: 0.4rem;
        }
        @keyframes insight-spin { to { transform: rotate(360deg); } }
        .insight-status {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.85rem;
            margin-top: 0.35rem;
        }
        .insight-status-error { color: #dc3545; font-weight: 600; }
        .insight-popover .popover-header { font-weight: 600; }
        .insight-popover .popover-body { font-size: 0.9rem; color: #212529; }
        .insight-popover .insight-text { margin-bottom: 0.6rem; }
        .insight-popover .insight-sinal { display: inline-block; margin-bottom: 0.6rem; }
        .insight-popover .badge { font-size: 0.75rem; }
        .insight-popover .badge-positivo { background-color: #198754; }
        .insight-popover .badge-neutro { background-color: #6c757d; }
        .insight-popover .badge-negativo { background-color: #dc3545; }
        .insight-popover .insight-riscos { padding-left: 1rem; margin: 0; }
        .insight-popover .insight-riscos li { font-size: 0.84rem; }
        </style>
        <script>
        (function() {
            const win = window.parent || window;
            if (!win || win.__FS_BOOTSTRAP_INIT__) { return; }
            win.__FS_BOOTSTRAP_INIT__ = true;
            const doc = win.document;
            if (!doc.querySelector('script[data-fs-bootstrap]')) {
                const script = doc.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js';
                script.integrity = 'sha384-HoA5SgdAxeMR5X0xOYe/gkGEXUXMaLLfi5yRvDqxn6VOGGAIv/uGFo9Y8dU5I+4f';
                script.crossOrigin = 'anonymous';
                script.dataset.fsBootstrap = 'true';
                doc.head.appendChild(script);
            }
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.session_state[_INSIGHT_STYLES_FLAG] = True


def _submit_review_task(artifact_id: str, artifact_meta: Dict[str, Any], *, auto: bool = False) -> None:
    payload = copy.deepcopy(artifact_meta)
    tasks = _get_review_tasks()
    previous = tasks.get(artifact_id) or {}
    attempts = int(previous.get("attempts", 0)) + 1
    future = _REVIEW_EXECUTOR.submit(_call_review_llm_with_throttle, artifact_id, payload)
    tasks[artifact_id] = {
        "future": future,
        "status": "pending",
        "started_at": time.time(),
        "attempts": attempts,
        "auto": bool(auto),
    }


def _poll_review_tasks() -> None:
    tasks = _get_review_tasks()
    reviews = st.session_state.setdefault("reviews", {})
    rerun_needed = False

    for artifact_id, task in list(tasks.items()):
        future = task.get("future")
        if not future:
            continue
        if future.done():
            if task.get("status") not in ("completed", "failed"):
                try:
                    review = future.result()
                    if isinstance(review, ReviewSchema):
                        payload = review.model_dump()
                    else:
                        dump = getattr(review, "model_dump", None)
                        payload = dump() if callable(dump) else review
                    if isinstance(payload, ReviewSchema):
                        payload = payload.model_dump()
                    if not isinstance(payload, dict):
                        payload = {"insight": str(payload), "riscos": [], "sinal": "neutro", "status": "draft"}
                    reviews[artifact_id] = payload
                    task["status"] = "completed"
                    task.pop("error", None)
                except Exception as exc:
                    task["status"] = "failed"
                    task["error"] = str(exc)
                task["completed_at"] = time.time()
                task["notified"] = False
        elif task.get("status") == "pending":
            task["status"] = "running"

    for artifact_id, task in tasks.items():
        status = task.get("status")
        if status in ("completed", "failed") and not task.get("notified"):
            if status == "completed":
                st.session_state["_analise_flash_id"] = artifact_id
                st.session_state["_analise_flash_msg"] = "Insight gerado com sucesso."
            else:
                st.session_state["_analise_flash_id"] = artifact_id
                st.session_state["_analise_flash_msg"] = task.get("error") or "Falha ao gerar insight."
            task["notified"] = True
            rerun_needed = True

    if rerun_needed:
        # CRÍTICO: Só força redirect se usuário JÁ ESTÁ em /Análise
        # Não arrancar usuário de outras páginas (ex: /Parecer)
        if st.query_params.get("p") == "analise":
            st.rerun()


def _emit_captions(captions):
    shown = set()
    for text in captions:
        if isinstance(text, str) and text and text not in shown:
            st.caption(text)
            shown.add(text)


def _process_plot_result(result) -> bool:
    captions = []
    success = False

    def _handle(value):
        nonlocal success
        if value is None:
            success = True
            return
        if isinstance(value, bool):
            success = success or value
            return
        if isinstance(value, str):
            captions.append(value)
            success = True
            return
        if isinstance(value, dict):
            caption = value.get("caption")
            if isinstance(caption, str):
                captions.append(caption)
            if "rendered" in value:
                _handle(value["rendered"])
            if "success" in value:
                _handle(value["success"])
            if all(key not in value for key in ("rendered", "success")):
                success = True
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                _handle(item)
            return
        success = True

    _handle(result)
    _emit_captions(captions)
    return success


def _process_table_result(result) -> bool:
    captions = []
    rendered = False

    def _handle(value):
        nonlocal rendered
        if value is None:
            return
        if isinstance(value, bool):
            rendered = rendered or value
            return
        if isinstance(value, str):
            captions.append(value)
            return
        if isinstance(value, dict):
            caption = value.get("caption")
            if isinstance(caption, str):
                captions.append(caption)
            for key in ("df", "dataframe", "data", "table"):
                if key in value:
                    _handle(value[key])
            if "rendered" in value:
                _handle(value["rendered"])
            if "success" in value:
                _handle(value["success"])
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                _handle(item)
            return
        if hasattr(value, "empty") and hasattr(value, "columns"):
            if not getattr(value, "empty", False):
                st.dataframe(value, use_container_width=True, hide_index=True)
                rendered = True
            return
        rendered = True

    _handle(result)
    _emit_captions(captions)
    return rendered


def _try_call_plot(df, name_list) -> bool:
    if df is None or not name_list or _graficos_module is None:
        return False
    for name in name_list:
        func = getattr(_graficos_module, name, None)
        if not callable(func):
            continue
        try:
            result = func(df)
        except Exception as exc:  # noqa: PERF203 - user feedback prioritizado
            st.warning(f"Falha ao renderizar gráfico '{name}': {exc}")
            continue
        if _process_plot_result(result):
            return True
    return False


def _try_show_table(name_list) -> bool:
    if not name_list or _tabelas_module is None:
        return False
    for name in name_list:
        func = getattr(_tabelas_module, name, None)
        if not callable(func):
            continue
        try:
            result = func()
        except Exception as exc:  # noqa: PERF203 - user feedback prioritizado
            st.warning(f"Falha ao carregar tabela '{name}': {exc}")
            continue
        if _process_table_result(result):
            return True
    return False


def _todo_placeholder(nome: str):
    st.info(f"TODO: inserir gráfico/tabela desta subseção ({nome})")


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


def _format_column_name(col_name: str) -> str:
    """
    Formata nome de coluna: remove prefixos p_ ou r_, capitaliza palavras,
    substitui underscore por espaço e corrige ortografia brasileira.
    
    Exemplo: 'p_Patrimonio_Liquido' -> 'Patrimônio Líquido'
             'r_Lucro_Liquido' -> 'Lucro Líquido'
    """
    # Remove prefixos p_ ou r_
    if col_name.startswith(('p_', 'r_')):
        col_name = col_name[2:]
    
    # Substitui underscore por espaço
    col_name = col_name.replace('_', ' ')
    
    # Capitaliza primeira letra de cada palavra
    col_name = col_name.title()
    
    # Dicionário de correções ortográficas para padrão brasileiro
    corrections = {
        'Patrimonio': 'Patrimônio',
        'Liquido': 'Líquido',
        'Liquidez': 'Liquidez',
        'Receita': 'Receita',
        'Circulante': 'Circulante',
        'Passivo': 'Passivo',
        'Ativo': 'Ativo',
        'Lucro': 'Lucro',
        'Imobilizado': 'Imobilizado',
        'Realizavel': 'Realizável',
        'Divida': 'Dívida',
        'Credito': 'Crédito',
        'Debito': 'Débito',
        'Capital': 'Capital',
        'Medio': 'Médio',
        'Periodo': 'Período',
        'Analise': 'Análise',
        'Operacional': 'Operacional',
        'Indice': 'Índice',
        'Indices': 'Índices',
        'Despesa': 'Despesa',
        'Despesas': 'Despesas',
        'Impostos': 'Impostos',
        'Juros': 'Juros',
        'Depreciacao': 'Depreciação',
        'Amortizacao': 'Amortização',
        'Disponivel': 'Disponível',
        'Estoque': 'Estoque',
        'Fornecedor': 'Fornecedor',
        'Fornecedores': 'Fornecedores',
    }
    
    # Aplica correções palavra por palavra
    words = col_name.split()
    corrected_words = [corrections.get(word, word) for word in words]
    
    return ' '.join(corrected_words)


def _format_currency_value(value) -> str:
    """
    Formata valor numérico como moeda brasileira com prefixo R$.
    
    Exemplo: 37531910 -> 'R$ 37.531.910,00'
    """
    if pd.isna(value):
        return '-'
    
    try:
        num_value = float(value)
        # Formata com separador de milhares (.) e decimais (,)
        formatted = f'R$ {num_value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatted
    except (ValueError, TypeError):
        return str(value)


def _split_indices_columns(df) -> dict:
    categories = {
        "Liquidez": [],
        "Endividamento/Estrutura": [],
        "Rentabilidade": [],
        "Eficiência Operacional / Ciclo": [],
    }
    for col in df.columns:
        if col == "Ano":
            continue
        label = _normalize_label(str(col))
        if "liquidez" in label or "ccl" in label:
            categories["Liquidez"].append(col)
        elif "endivid" in label or "alavanc" in label or "imobilizado" in label:
            categories["Endividamento/Estrutura"].append(col)
        elif "margem" in label or "roa" in label or "roe" in label or "ebitda" in label or "lucro" in label:
            categories["Rentabilidade"].append(col)
        elif "giro" in label or "periodo" in label or "cobertura" in label or "ciclo" in label:
            categories["Eficiência Operacional / Ciclo"].append(col)
    return categories




def _to_float(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number



def _format_metric(value: Any, divisor: float = 1.0) -> Any:
    number = _to_float(value)
    if number is None:
        return value
    if not divisor:
        divisor = 1.0
    scaled = number / divisor
    return round(scaled, 2)



def _latest_row_dict(df) -> Optional[Dict[str, Any]]:
    if df is None:
        return None
    if getattr(df, "empty", False):
        return None
    try:
        if "ano" in df.columns:
            data = df.sort_values("ano", ascending=True)
            row = data.iloc[-1]
        elif "Ano" in df.columns:
            data = df.sort_values("Ano", ascending=True)
            row = data.iloc[-1]
        else:
            row = df.iloc[0]
    except Exception:
        try:
            row = df.iloc[0]
        except Exception:
            return None
    to_dict = getattr(row, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return dict(row)





def _series_points(df, column: str) -> list[tuple[Any, float]]:
    if df is None or getattr(df, "empty", False):
        return []
    points: list[tuple[Any, float]] = []
    for _, row in df.iterrows():
        raw_value = row.get(column)
        value = _to_float(raw_value)
        if value is None:
            continue
        year = row.get("Ano") or row.get("ano") or row.get("ano_label")
        if isinstance(year, str):
            digits = ''.join(ch for ch in year if ch.isdigit())
            year = int(digits) if digits else year.strip() or None
        points.append((year, value))
    return points


def _infer_numeric_columns(df, limit: int = 4) -> list[str]:
    if df is None or getattr(df, "empty", False):
        return []
    columns: list[str] = []
    for col in df.columns:
        col_lower = str(col).lower()
        if col_lower in {"ano", "ano_label", "periodo"}:
            continue
        values = []
        for value in df[col]:
            converted = _to_float(value)
            if converted is not None:
                values.append(converted)
        if values:
            columns.append(col)
        if len(columns) >= limit:
            break
    return columns


def _summarize_metrics(
    df,
    columns: list[str],
    rename: Optional[Dict[str, str]] = None,
    divisors: Optional[Dict[str, float] | float] = None,
) -> Dict[str, Any]:
    rename = rename or {}
    summary: Dict[str, Any] = {}
    if df is None or getattr(df, "empty", False):
        return summary
    if not columns:
        return summary

    for col in columns:
        points = _series_points(df, col)
        if not points:
            continue
        divisor = 1.0
        if isinstance(divisors, dict):
            divisor = divisors.get(col, 1.0)
        elif isinstance(divisors, (int, float)) and divisors:
            divisor = float(divisors)
        label = rename.get(col, col)
        series_data: Dict[str, Any] = {}
        for idx, (year, value) in enumerate(points):
            key = str(year if year is not None else idx)
            series_data[key] = _format_metric(value, divisor)

        values_raw = [value for _, value in points]
        latest = values_raw[-1]
        first = values_raw[0]
        mean_value = statistics.fmean(values_raw)
        variation = latest - first
        percentual = 0.0
        if first != 0:
            percentual = (variation / abs(first)) * 100.0

        trend = "estavel"
        if percentual > 5:
            trend = "alta"
        elif percentual < -5:
            trend = "queda"

        try:
            scaled_values = [value / divisor for value in values_raw]
        except Exception:
            scaled_values = values_raw
        min_scaled = min(scaled_values) if scaled_values else 0.0
        max_scaled = max(scaled_values) if scaled_values else 0.0
        amplitude_scaled = max_scaled - min_scaled
        if len(scaled_values) >= 2:
            std_dev_scaled = statistics.pstdev(scaled_values)
            variance_scaled = statistics.pvariance(scaled_values)
        else:
            std_dev_scaled = 0.0
            variance_scaled = 0.0

        stats_block = {
            "media": round(statistics.fmean(scaled_values), 2) if scaled_values else None,
            "min": round(min_scaled, 2) if scaled_values else None,
            "max": round(max_scaled, 2) if scaled_values else None,
            "amplitude": round(amplitude_scaled, 2) if scaled_values else None,
            "desvio_padrao": round(std_dev_scaled, 2),
            "variancia": round(variance_scaled, 4),
        }

        summary[label] = {
            "serie": series_data,
            "ultimo": _format_metric(latest, divisor),
            "media": _format_metric(mean_value, divisor),
            "variacao_absoluta": _format_metric(variation, divisor),
            "variacao_percentual": round(percentual, 2),
            "tendencia": trend,
            "anos": [p[0] for p in points if p[0] is not None],
            "estatisticas": stats_block,
        }
    return summary


def _compute_ebitda_snapshot(row: Dict[str, Any]) -> Optional[float]:
    if not row:
        return None
    lucro = _to_float(row.get("r_Lucro_Liquido"))
    juros = _to_float(row.get("r_Despesa_de_Juros"))
    impostos = _to_float(row.get("r_Despesa_de_Impostos"))
    if lucro is None or juros is None or impostos is None:
        return None
    amort = _to_float(row.get("r_Amortizacao")) or 0.0
    depreciacao = _to_float(row.get("r_Depreciacao")) or 0.0
    return lucro + juros + impostos + amort + depreciacao


def _build_mini_context(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ss = st.session_state
    out = ss.get("out") or {}
    meta = ss.get("meta") or {}
    ctx = {
        "empresa": meta.get("empresa"),
    }
    # Inclui anos disponíveis quando presentes para dar contexto temporal básico
    df_state = ss.get("df")
    if df_state is not None and getattr(df_state, "empty", False) is False and "ano" in df_state.columns:
        try:
            anos = sorted(set(int(a) for a in df_state["ano"].dropna()))
            if anos:
                ctx["anos_disponiveis"] = anos
        except Exception:
            pass
    else:
        df_raw = out.get("df_raw")
        if df_raw is not None and getattr(df_raw, "empty", False) is False and "ano" in getattr(df_raw, "columns", []):
            try:
                anos = sorted(set(int(a) for a in df_raw["ano"].dropna()))
                if anos:
                    ctx["anos_disponiveis"] = anos
            except Exception:
                pass
    if extra:
        ctx.update(extra)
    return {k: v for k, v in ctx.items() if v is not None}







def _filter_existing_columns(df, columns: list[str]) -> list[str]:
    if df is None or getattr(df, "empty", False):
        return []
    return [col for col in columns if col in df.columns]


def _build_tax_summary(df) -> Dict[str, Any]:
    columns = _filter_existing_columns(df, ["r_Despesa_de_Impostos", "r_Receita_Total"])
    summary = _summarize_metrics(
        df,
        columns,
        rename={
            "r_Despesa_de_Impostos": "Despesa de Impostos (mi)",
            "r_Receita_Total": "Receita (mi)",
        },
        divisors={
            "r_Despesa_de_Impostos": 1_000_000,
            "r_Receita_Total": 1_000_000,
        },
    )
    row = _latest_row_dict(df)
    impostos = _to_float(row.get("r_Despesa_de_Impostos")) if row else None
    receita = _to_float(row.get("r_Receita_Total")) if row else None
    if receita not in (None, 0) and impostos is not None:
        summary["Carga Tributaria (%)"] = round((impostos / receita) * 100, 2)
    if not summary:
        summary = {"nota": "Despesa de impostos e efetividade tributaria"}
    else:
        summary.setdefault("nota", "Despesa de impostos e efetividade tributaria")
    return summary


def _build_profit_summary(df) -> Dict[str, Any]:
    columns = _filter_existing_columns(df, ["r_Lucro_Liquido", "r_Receita_Total"])
    summary = _summarize_metrics(
        df,
        columns,
        rename={
            "r_Lucro_Liquido": "Lucro Liquido (mi)",
            "r_Receita_Total": "Receita (mi)",
        },
        divisors={
            "r_Lucro_Liquido": 1_000_000,
            "r_Receita_Total": 1_000_000,
        },
    )
    row = _latest_row_dict(df)
    lucro = _to_float(row.get("r_Lucro_Liquido")) if row else None
    receita = _to_float(row.get("r_Receita_Total")) if row else None
    if receita not in (None, 0) and lucro is not None:
        summary["Margem Liquida (%)"] = round((lucro / receita) * 100, 2)
    if not summary:
        summary = {"nota": "Desempenho do lucro liquido"}
    else:
        summary.setdefault("nota", "Desempenho do lucro liquido")
    return summary


def _collect_indices_summary(indices_df, category: str, note: str) -> Dict[str, Any]:
    if indices_df is None or getattr(indices_df, "empty", False):
        return {"nota": note}
    categories = _split_indices_columns(indices_df)
    columns = categories.get(category)
    if columns is None:
        target = _normalize_label(category)
        for key, values in categories.items():
            if _normalize_label(str(key)) == target:
                columns = values
                break
    if columns is None:
        columns = []
    summary = _summarize_metrics(indices_df, columns)
    if not summary:
        summary = {"nota": note}
    else:
        summary.setdefault("nota", note)
    return summary


def _build_pca_loadings_summary(loadings_df, top_components: int = 3, top_variables: int = 3) -> Dict[str, Any]:
    if loadings_df is None or getattr(loadings_df, "empty", False):
        return {}
    summary: Dict[str, Any] = {}
    try:
        components = list(loadings_df.columns)
    except Exception:
        return summary
    for comp in components[:top_components]:
        try:
            series = loadings_df[comp].abs().sort_values(ascending=False)
        except Exception:
            continue
        entries = []
        for variable in series.index[:top_variables]:
            try:
                raw_value = loadings_df.loc[variable, comp]
                value = _to_float(raw_value)
            except Exception:
                value = None
            entries.append({
                "variavel": str(variable),
                "peso": round(value, 3) if value is not None else value,
            })
        summary[str(comp)] = {"principais": entries}
    if summary:
        summary.setdefault("nota", "Variaveis com maior carga absoluta por componente")
    return summary


def _build_pca_scores_summary(scores_df, max_components: int = 3) -> Dict[str, Any]:
    if scores_df is None or getattr(scores_df, "empty", False):
        return {}
    columns = [col for col in scores_df.columns if str(col).upper().startswith("PC")]
    if not columns:
        return {}
    summary = _summarize_metrics(scores_df, columns[:max_components])
    if summary:
        summary.setdefault("nota", "Scores por componente principal")
    return summary

def _unwrap_table_dataframe(value):
    if value is None:
        return None
    if hasattr(value, "empty") and hasattr(value, "columns"):
        if getattr(value, "empty", False):
            return None
        return value
    if isinstance(value, dict):
        for key in ("df", "dataframe", "data", "table"):
            if key in value:
                df = _unwrap_table_dataframe(value.get(key))
                if df is not None:
                    return df
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            df = _unwrap_table_dataframe(item)
            if df is not None:
                return df
    return None


def _get_table_dataframe(name_list) -> Optional[Any]:
    if not name_list or _tabelas_module is None:
        return None
    for name in name_list:
        func = getattr(_tabelas_module, name, None)
        if not callable(func):
            continue
        try:
            result = func()
        except Exception:
            continue
        df = _unwrap_table_dataframe(result)
        if df is not None:
            return df
    return None


def _register_table_section(
    artifact_id: str,
    title: str,
    name_list,
    note: Optional[str] = None,
    column_filter: Optional[Any] = None,
    rename: Optional[Dict[str, str]] = None,
):
    table_df = _get_table_dataframe(name_list)
    if table_df is None:
        return
    if callable(column_filter):
        columns = column_filter(table_df)
    elif isinstance(column_filter, (list, tuple)):
        columns = list(column_filter)
    else:
        columns = [col for col in table_df.columns if str(col).lower() not in {"ano", "periodo"}]
    if not columns:
        columns = _infer_numeric_columns(table_df)
    _register_artifact(
        artifact_id,
        title,
        df=table_df,
        columns=columns,
        rename=rename,
        note=note or title,
    )


def _register_artifact(
    artifact_id: str,
    title: str,
    df=None,
    columns: Optional[list[str]] = None,
    rename: Optional[Dict[str, str]] = None,
    divisors: Optional[Dict[str, float] | float] = None,
    note: Optional[str] = None,
    extra_ctx: Optional[Dict[str, Any]] = None,
    summary_override: Optional[Dict[str, Any]] = None,
    review_kind: Optional[str] = None,
) -> None:
    summary: Dict[str, Any] = summary_override.copy() if summary_override else {}
    if not summary and df is not None:
        target_columns = columns or _infer_numeric_columns(df)
        summary = _summarize_metrics(df, target_columns, rename=rename, divisors=divisors)
    if not summary:
        summary = {"nota": note or title}
    else:
        summary.setdefault("nota", note or title or title)
    mini_ctx = _build_mini_context(extra_ctx)
    lowered_id = artifact_id.lower()
    if review_kind is None:
        if "indice" in lowered_id or "pca" in lowered_id:
            review_kind = "indices"
        else:
            review_kind = "raw"
    _artifact_box(artifact_id, title, mini_ctx, summary, review_kind)



def _artifact_box(
    artifact_id: str,
    title: str,
    mini_ctx: Dict[str, Any],
    dados_resumo: Dict[str, Any],
    review_kind: str,
) -> None:
    ss = st.session_state
    meta = ss.setdefault("artifacts_meta", {})
    reviews = ss.setdefault("reviews", {})
    tasks = _get_review_tasks()
    flash_id = ss.get("_analise_flash_id")
    flash_msg = ss.get("_analise_flash_msg", "Insight gerado com sucesso.")

    artifact_meta = {
        "title": title,
        "mini_ctx": dict(mini_ctx),
        "dados_resumo": dict(dados_resumo),
        "review_kind": review_kind,
        "artifact_id": artifact_id,
    }
    meta[artifact_id] = artifact_meta

    review_payload = reviews.get(artifact_id)
    has_review = review_payload is not None

    task_state = tasks.get(artifact_id)
    status = task_state.get("status") if task_state else None

    if not has_review:
        should_submit = False
        if task_state is None:
            should_submit = True
        elif status == "failed" and task_state.get("auto"):
            attempts = int(task_state.get("attempts", 0))
            if attempts < _MAX_AUTO_ATTEMPTS:
                should_submit = True
        if should_submit:
            _submit_review_task(artifact_id, artifact_meta, auto=True)
            task_state = tasks.get(artifact_id)
            status = task_state.get("status") if task_state else None

    is_running = status in ("pending", "running")
    has_error = status == "failed"
    error_msg = task_state.get("error") if has_error else None
    review_payload = reviews.get(artifact_id)
    has_review = review_payload is not None

    popover_id = f"insight-popover-{artifact_id}"
    popover_html = "<div class='insight-popover-body'><p class='insight-text'>Insight em processamento...</p></div>"
    if has_error and not is_running:
        popover_html = (
            "<div class='insight-popover-body'><p class='insight-text'>"
            + html.escape(error_msg or "Falha ao gerar insight")
            + "</p></div>"
        )
    elif has_review and review_payload:
        insight_html = html.escape(review_payload.get("insight", ""))
        sinal_value = (review_payload.get("sinal") or "neutro").lower()
        sinal_label = sinal_value.capitalize()
        riscos_list = review_payload.get("riscos") or []
        riscos_items = (
            "".join(f"<li>{html.escape(str(item))}</li>" for item in riscos_list)
            if riscos_list
            else "<li>Sem riscos destacados</li>"
        )
        popover_html = (
            "<div class='insight-popover-body'>"
            f"<p class='insight-text'>{insight_html}</p>"
            f"<span class='badge insight-sinal badge-{sinal_value}'>{html.escape(sinal_label)}</span>"
            f"<ul class='insight-riscos'>{riscos_items}</ul>"
            "</div>"
        )

    popover_json = json.dumps(popover_html)
    btn_ready = has_review and not is_running
    button_class = "btn-insight ready" if btn_ready else "btn-insight"

    button_col, status_col = st.columns([1, 0.2])
    with button_col:
        if flash_id == artifact_id:
            st.success(flash_msg)
            ss.pop("_analise_flash_id", None)
            ss.pop("_analise_flash_msg", None)
        disabled_attr = "" if btn_ready else "disabled"
        if btn_ready:
            data_attrs = (
                ' data-bs-toggle="popover" data-bs-placement="bottom" data-bs-trigger="focus"'
                + ' data-bs-html="true" data-bs-custom-class="insight-popover" data-fs-insight-popover="1"'
            )
        else:
            data_attrs = ' data-fs-insight-popover="1"'
        st.markdown(
            f"""
            <div class="insight-button-wrapper">
                <button type="button" class="{button_class}" id="{popover_id}" {disabled_attr}{data_attrs}>Insight</button>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <script>
            (function() {{
                const win = window.parent || window;
                if (!win) {{ return; }}
                const doc = win.document;
                const btn = doc.getElementById('{popover_id}');
                if (!btn) {{ return; }}
                const ready = {str(btn_ready).lower()};
                const content = {popover_json};
                if (ready) {{
                    btn.removeAttribute('disabled');
                    btn.classList.add('ready');
                    btn.setAttribute('data-bs-toggle', 'popover');
                    btn.setAttribute('data-bs-placement', 'bottom');
                    btn.setAttribute('data-bs-trigger', 'focus');
                    btn.setAttribute('data-bs-html', 'true');
                    btn.setAttribute('data-bs-custom-class', 'insight-popover');
                    btn.setAttribute('data-bs-content', content);
                }} else {{
                    btn.classList.remove('ready');
                    btn.setAttribute('disabled', 'disabled');
                    btn.removeAttribute('data-bs-toggle');
                }}
                const init = () => {{
                    if (!win.bootstrap || !bootstrap.Popover) {{
                        setTimeout(init, 120);
                        return;
                    }}
                    if (ready) {{
                        const instance = bootstrap.Popover.getOrCreateInstance(btn, {{container: 'body', html: true, trigger: 'focus', placement: 'bottom', customClass: 'insight-popover'}});
                        instance.setContent({{'.popover-body': content}});
                    }} else {{
                        const instance = bootstrap.Popover.getInstance(btn);
                        if (instance) {{ instance.dispose(); }}
                    }}
                }};
                init();
            }})();
            </script>
            """,
            unsafe_allow_html=True,
        )

    if is_running:
        status_col.markdown(
            "<div class='insight-status'><span class='insight-spinner'></span><span>Processando...</span></div>",
            unsafe_allow_html=True,
        )
    elif has_error:
        safe_error = html.escape(error_msg or "Falha ao gerar insight")
        status_col.markdown(
            f"<div class='insight-status insight-status-error'>{safe_error}</div>",
            unsafe_allow_html=True,
        )
    else:
        status_col.empty()

    if has_error and not is_running:
        if st.button("Tentar novamente", key=f"retry_{artifact_id}"):
            _submit_review_task(artifact_id, artifact_meta, auto=False)
            st.rerun()

    if not has_review and not is_running and not has_error:
        st.caption("Insight sendo preparado automaticamente. Aguarde alguns instantes.")

    if review_payload:
        st.json({k: v for k, v in review_payload.items() if k != "status"})
        c1, c2, c3 = st.columns(3)
        if c1.button("Aceitar", key=f"ok_{artifact_id}"):
            review_payload["status"] = "accepted"
            st.rerun()
        if c2.button("Revisar", key=f"rev_{artifact_id}"):
            review_payload["status"] = "needs_revision"
            st.rerun()
        if c3.button("Descartar", key=f"del_{artifact_id}"):
            reviews.pop(artifact_id, None)
            st.rerun()

        note_key = f"obs_{artifact_id}"
        obs_value = st.text_area(
            "Observacao do analista",
            value=review_payload.get("obs", ""),
            key=note_key,
        )
        review_payload["obs"] = obs_value

        if st.button("Reprocessar insight", key=f"refresh_{artifact_id}", disabled=is_running):
            _submit_review_task(artifact_id, artifact_meta, auto=False)
            st.rerun()


def _render_graficos_tab_content():
    df = prepare_graficos_data()
    if df is None:
        st.info("Carregue os dados em **Novo -> Dados** para visualizar os gráficos.")
        return

    ss = st.session_state
    out = ss.get("out") or {}
    indices_df = out.get("df_indices")
    row = _latest_row_dict(df)

    st.markdown("<h3 style='text-align: left;'>📔 Demonstrativos Contábeis</h3>", unsafe_allow_html=True)
    st.markdown("#### 🪙 1. Balanço Patrimonial")
    if not _try_call_plot(
        df,
        [
            "render_ativos",
            "render_ativos_grafico",
            "render_ativo_total",
            "render_estoques",
            "render_contas_a_receber",
        ],
    ):
        _todo_placeholder("Ativos")
    if not _try_call_plot(df, ["render_passivos", "render_passivo_total", "render_contas_a_pagar"]):
        _todo_placeholder("Passivos")
    if not _try_call_plot(df, ["render_pl", "render_patrimonio_liquido"]):
        _todo_placeholder("Patrimônio Líquido")
    capital_rendered = render_ativo_passivo_circulante(df)
    if not capital_rendered:
        capital_rendered = _try_call_plot(df, ["render_capital_giro", "render_liquidez_corrente"])
    if not capital_rendered:
        _todo_placeholder("Capital de Giro e Liquidez")

    st.divider()

    st.markdown("#### 🧮 2. Demonstração de Resultado")
    operacional_rendered = render_receita_total(df)
    if _try_call_plot(df, ["render_custos", "render_depreciacao", "render_amortizacao"]):
        operacional_rendered = True
    if not operacional_rendered:
        _todo_placeholder("Operacional")
    financeiro_rendered = render_juros_lucro_receita(df)
    if not financeiro_rendered:
        financeiro_rendered = _try_call_plot(df, ["render_despesa_juros"])
    if not financeiro_rendered:
        _todo_placeholder("Financeiro")
    impostos_rendered = _try_call_plot(df, ["render_impostos", "render_despesa_impostos"])
    if not impostos_rendered:
        _todo_placeholder("Tributos")
    resultado_rendered = _try_call_plot(df, ["render_lucro_liquido", "render_resultado_liquido"])
    if not resultado_rendered:
        _todo_placeholder("Resultado")

    st.divider()

    st.markdown("#### 📊 3. Índices Contábeis")
    liquidez_rendered = _try_call_plot(df, ["render_liquidez_indices"])
    if not liquidez_rendered:
        _todo_placeholder("Liquidez")
    endividamento_rendered = _try_call_plot(df, ["render_endividamento_indices"])
    if not endividamento_rendered:
        _todo_placeholder("Endividamento/Estrutura")
    rentabilidade_rendered = _try_call_plot(df, ["render_rentabilidade_indices"])
    if not rentabilidade_rendered:
        _todo_placeholder("Rentabilidade")
    eficiencia_rendered = _try_call_plot(df, ["render_eficiencia_indices"])
    if not eficiencia_rendered:
        _todo_placeholder("Eficiência Operacional / Ciclo")

    st.divider()

    st.markdown("#### 🧲 4. Componentes Principais (PCA)")
    loadings_rendered = _try_call_plot(df, ["render_pca_loadings"])
    if not loadings_rendered:
        _todo_placeholder("Cargas (loadings)")
    variancia_rendered = _try_call_plot(df, ["render_pca_variancia"])
    if not variancia_rendered:
        _todo_placeholder("Variância explicada (explained variance)")
    scores_rendered = _try_call_plot(df, ["render_pca_scores"])
    if not scores_rendered:
        _todo_placeholder("Projeções (scores) por período/empresa")

def _render_indices_tables(df):
    categories = _split_indices_columns(df)
    for label, columns in categories.items():
        st.markdown(f"### • {label}")
        available = [col for col in columns if col in df.columns]
        if not available:
            _todo_placeholder(label)
            continue
        subset_cols = available
        if "Ano" in df.columns:
            subset_cols = ["Ano"] + available
        st.dataframe(df[subset_cols], use_container_width=True, hide_index=True)



def _render_dados_contabeis_tab_content():
    """Renderiza a aba 'Dados Contábeis' com dados brutos formatados da planilha."""
    ss = st.session_state
    out = ss.get("out")
    
    if not out:
        st.info("Calcule o FinScore em **Novo** para visualizar os dados contábeis.")
        return
    
    df_raw = out.get("df_raw")
    
    if df_raw is None or df_raw.empty:
        st.warning("Nenhum dado contábil disponível.")
        return
    
    # Informações no topo
    st.markdown("<h3 style='text-align: left;'>📖 Contas</h3>", unsafe_allow_html=True)
    
    meta = ss.get("meta", {})
    empresa = meta.get("empresa", "-")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            "<p style='text-align:center;margin-bottom:0.25rem;'>Nome da Empresa</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h3 style='text-align:center;margin:0;font-size: 140%;'>{empresa}</h3>",
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            "<p style='text-align:center;margin-bottom:0.25rem;'>Períodos</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h3 style='text-align:center;margin:0;font-size: 140%;'>{len(df_raw)}</h3>",
            unsafe_allow_html=True,
        )
    
    with col3:
        # Contar colunas numéricas (exceto 'Ano')
        numeric_cols = df_raw.select_dtypes(include=['number']).columns.tolist()
        if 'ano' in [c.lower() for c in df_raw.columns]:
            numeric_cols = [c for c in numeric_cols if c.lower() != 'ano']
        
        st.markdown(
            "<p style='text-align:center;margin-bottom:0.25rem;'>Total de Contas</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h3 style='text-align:center;margin:0;font-size: 140%;'>{len(numeric_cols)}</h3>",
            unsafe_allow_html=True,
        )
    
    st.divider()
    
    # Criar cópia do dataframe para não modificar o original
    df_display = df_raw.copy()
    
    # Limitar a 3 linhas
    df_display = df_display.head(3)
    
    # Formatar nomes das colunas
    df_display.columns = [_format_column_name(col) for col in df_display.columns]
    
    # Identificar colunas numéricas (exceto 'Ano' se existir)
    numeric_cols_display = df_display.select_dtypes(include=['number']).columns.tolist()
    if 'Ano' in numeric_cols_display:
        numeric_cols_display.remove('Ano')
    
    # Formatar coluna Ano (se existir) - sem vírgulas ou pontos
    if 'Ano' in df_display.columns:
        df_display['Ano'] = df_display['Ano'].apply(lambda x: str(int(x)) if pd.notna(x) else '-')
    
    # Formatar valores numéricos como moeda
    for col in numeric_cols_display:
        df_display[col] = df_display[col].apply(_format_currency_value)
    
    # Exibir tabela formatada
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )


def _render_tabelas_tab_content():
    ss = st.session_state
    out = ss.get("out")
    if not out:
        st.info("Calcule o FinScore em **Novo** para visualizar as tabelas.")
        return

    indices_df = out.get("df_indices")
    top_indices_df = out.get("top_indices_df")

    st.markdown("<h3 style='text-align: left;'>📔 Demonstrativos Contábeis</h3>", unsafe_allow_html=True)
    st.markdown("#### 🪙 1. Balanço Patrimonial")
    if not _try_show_table(["table_ativos", "get_ativos_table"]):
        _todo_placeholder("Ativos")
    if not _try_show_table(["table_passivos", "get_passivos_table"]):
        _todo_placeholder("Passivos")
    if not _try_show_table(["table_pl", "get_pl_table", "get_patrimonio_liquido_table"]):
        _todo_placeholder("Patrimonio Liquido")
    if not _try_show_table(["table_capital_giro", "get_ccl_table", "get_liquidez_table"]):
        _todo_placeholder("Capital de Giro / Liquidez")

    st.divider()

    st.markdown("#### 🧮 2. Demonstração de Resultado")
    if not _try_show_table([
        "table_operacional",
        "get_operacional_table",
        "get_receita_table",
        "get_custos_table",
        "get_depreciacao_table",
        "get_amortizacao_table",
    ]):
        _todo_placeholder("Operacional")
    if not _try_show_table(["table_financeiro", "get_financeiro_table", "get_despesa_juros_table"]):
        _todo_placeholder("Financeiro")
    if not _try_show_table(["table_impostos", "get_impostos_table", "get_despesa_impostos_table"]):
        _todo_placeholder("Tributos")
    if not _try_show_table(["table_resultado", "get_resultado_liquido_table", "get_lucro_liquido_table"]):
        _todo_placeholder("Resultado")

    st.divider()

    st.markdown("#### 📊 3. Indices Contábeis")
    liquidez_table = _try_show_table(["table_liquidez_indices"])
    if not liquidez_table:
        _todo_placeholder("Liquidez")
    endividamento_table = _try_show_table(["table_endividamento_indices"])
    if not endividamento_table:
        _todo_placeholder("Endividamento/Estrutura")
    rent_table = _try_show_table(["table_rentabilidade_indices"])
    if not rent_table:
        _todo_placeholder("Rentabilidade")
    eficiencia_table = _try_show_table(["table_eficiencia_indices"])
    if not eficiencia_table:
        _todo_placeholder("Eficiencia Operacional / Ciclo")

    st.divider()

    st.markdown("#### 🧲 4. Componentes Principais (PCA)")
    pca_loadings_table = _try_show_table(["get_pca_loadings_table"])
    if not pca_loadings_table:
        _todo_placeholder("Cargas (loadings)")

    if not _try_show_table(["get_pca_variance_table"]):
        _todo_placeholder("Variancia explicada (explained variance)")

    pca_scores_table = _try_show_table(["get_pca_scores_table"])
    if not pca_scores_table:
        _todo_placeholder("Projecoes (scores) por periodo/empresa")

    st.markdown("### - Destaques de componentes (top indices)")
    top_table = _try_show_table(["get_top_indices_table"])
    if not top_table:
        _todo_placeholder("Destaques de componentes (top indices)")




def render():
    ss = st.session_state
    
    # Flags de navegação são processadas em app.py ANTES de chegar aqui
    
    ss.setdefault("analise_tab", "Scores")
    ss.setdefault("reviews", {})
    ss.setdefault("artifacts_meta", {})

    # Removido: Não force p=analise aqui, pois interfere com navegação de outras páginas
    # A navegação já é controlada pelo app.py e novo módulo de sessão

    _poll_review_tasks()
    _ensure_insight_styles()
    _ensure_insight_polling()

    # CSS para centralizar as abas
    st.markdown(
        """
        <style>
        div[data-testid="stTabs"] > div[role="tablist"],
        div[data-baseweb="tab-list"] {
            display: flex;
            justify-content: center;   /* centraliza as abas */
            gap: 2rem;                 /* espaco entre abas */
        }
        div[data-testid="stTabs"] button[role="tab"],
        div[data-baseweb="tab"] {
            flex: 0 0 auto;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab_dados, tab_graficos, tab_tabelas, tab_scores = st.tabs([
        "Dados Contábeis", 
        "Gráficos", 
        "Tabelas",
        "Scores"
    ])

    with tab_dados:
        _render_dados_contabeis_tab_content()
    with tab_graficos:
        _render_graficos_tab_content()
    with tab_tabelas:
        _render_tabelas_tab_content()
    with tab_scores:
        render_scores()

    if ss.get("out"):
        st.divider()
        col = st.columns([1, 1, 1])[1]
        with col:
            if st.button("Aprovar", key="btn_aprovar_analise", use_container_width=True):
                NavigationFlow.request_lock_parecer()
                st.session_state["_pending_nav_target"] = "parecer"
                st.rerun()
