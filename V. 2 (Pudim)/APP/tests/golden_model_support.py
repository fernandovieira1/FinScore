"""Test-only capture/comparison; never imported by the Streamlit application.

Snapshots preserve complete service outputs and the report contract. Only the
engine wall clock is fixed, before execution, to make IDs and audit times stable.
No values, rows, warnings, PCA signs or fields are discarded by serialization.
"""
from __future__ import annotations

import dataclasses
from datetime import date, datetime
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from app_front.finscore_v2 import core, engine
from app_front.services.credit_policy import decide_pudim
from app_front.services.io_validation import ler_planilha
from app_front.services.finscore_service import run_finscore
from app_front.services.parecer_data_builder import build_parecer_data

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
DATA = APP.parent / 'MODELO' / 'dados_teste'
BASE_COMMIT = 'ec1d3dad222186649dc7dafd5d3bb855f24d4e4c'
FIXTURES = Path(__file__).parent / 'fixtures' / 'model_controls_v1'
FIXED_TIME = datetime(2026, 9, 28, 12, 0, 0)
SEED = 20260723
SIMULATIONS = 100  # regression corpus, not a production-default change
CASES = {
    'mobicloud': {
        'file': '5umarket - Mobicloud Tecnologia.xlsx',
        'meta': {'empresa': 'TESTE GOLDEN - MOBICLOUD TECNOLOGIA',
                 'cnpj': '26.590.119/0001-55', 'tipo_empresa': 'Serviços não financeiros'},
    },
    'ssa_mro': {
        'file': '6strumarket - SSA-Miro Solucoes.xlsx',
        'meta': {'empresa': 'TESTE GOLDEN - SSA-MRO SOLUCOES',
                 'cnpj': '26.409.092/0001-51', 'tipo_empresa': 'Serviços não financeiros'},
    },
    'jns': {
        'file': '12Grupo JNP - JNS Seguradora.xlsx',
        'meta': {'empresa': 'TESTE GOLDEN - JNS SEGURADORA',
                 'cnpj': '30.862.594/0001-00', 'tipo_empresa': 'Seguradora'},
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    """Strict JSON with explicit NaN/inf/type/axis information; no rounding."""
    if isinstance(value, pd.DataFrame):
        return {'__kind__': 'dataframe', 'columns': canonical(value.columns.tolist()),
                'index': canonical(value.index.tolist()), 'index_name': value.index.name,
                'dtypes': [str(dtype) for dtype in value.dtypes],
                'data': canonical(list(value.itertuples(index=False, name=None))),
                'attrs': canonical(value.attrs)}
    if isinstance(value, pd.Series):
        return {'__kind__': 'series', 'index': canonical(value.index.tolist()),
                'name': canonical(value.name), 'dtype': str(value.dtype),
                'data': canonical(value.tolist())}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {'__kind__': type(value).__name__, **{
            field.name: canonical(getattr(value, field.name)) for field in dataclasses.fields(value)}}
    if isinstance(value, Enum):
        return canonical(value.value)
    if isinstance(value, (datetime, date)):
        return {'__kind__': type(value).__name__, 'value': value.isoformat()}
    if isinstance(value, np.ndarray):
        return canonical(value.tolist())
    if isinstance(value, np.generic):
        return canonical(value.item())
    if value is pd.NA or value is pd.NaT:
        return {'__kind__': 'missing', 'value': str(value)}
    if isinstance(value, float) and not math.isfinite(value):
        return {'__kind__': 'float', 'value': 'nan' if math.isnan(value) else 'inf' if value > 0 else '-inf'}
    if isinstance(value, dict):
        return {str(key): canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f'Unserialized snapshot type: {type(value).__name__}')


def capture_case(name: str) -> dict:
    spec = CASES[name]
    path = DATA / spec['file']
    data, sheet, error = ler_planilha(path)
    if error or data is None:
        raise AssertionError(f'{name}: import failed: {error}')
    meta = {**spec['meta'], 'ano_inicial': 2023, 'ano_final': 2025,
            'serasa': 500, 'serasa_data': '22/09/2026'}
    input_meta = dict(meta)
    # The clock fixture does not patch finance methods, RNGs, validators or policy.
    previous_time = core.DATA_HORA_PROCESSAMENTO
    previous_base = getattr(core, 'df_contas_analise', None)
    had_base = hasattr(core, 'df_contas_analise')
    try:
        with patch.object(engine, 'datetime', wraps=datetime) as clock:
            clock.now.return_value = FIXED_TIME
            output = run_finscore(data, meta, executar_simulacoes=True,
                                 numero_simulacoes=SIMULATIONS, semente=SEED)
        policy = decide_pudim(output, meta)
        contract = build_parecer_data(output, meta, policy)
        return canonical({
            'case': name,
            'input': {'file': path.relative_to(ROOT).as_posix(), 'sha256': sha256(path),
                      'sheet': sheet, 'metadata': input_meta, 'serasa_is_synthetic': True},
            'execution': {'timestamp_fixture': FIXED_TIME, 'seed': SEED,
                          'simulations_per_approach': SIMULATIONS},
            'output': output,
            'policy': policy,
            'report_contract': contract.model_dump(mode='python'),
        })
    finally:
        core.DATA_HORA_PROCESSAMENTO = previous_time
        if had_base:
            core.df_contas_analise = previous_base
        else:
            core.__dict__.pop('df_contas_analise', None)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True,
                               indent=2, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def differences(expected, actual, path='$', limit=30) -> list[str]:
    """Exact schema/text/order; floats tolerate only 1e-10 relative/absolute.

    At score 1000 this admits at most 1e-7 point, not display-level rounding.
    NaN is tagged and remains distinct from null, economic zero and infinity.
    """
    found = []

    def visit(left, right, where):
        if len(found) >= limit:
            return
        if type(left) is not type(right):
            found.append(f'{where}: type {type(left).__name__} != {type(right).__name__}')
        elif isinstance(left, dict):
            if left.keys() != right.keys():
                found.append(f'{where}: missing={sorted(left.keys()-right.keys())}; added={sorted(right.keys()-left.keys())}')
            for key in sorted(left.keys() & right.keys()):
                visit(left[key], right[key], f'{where}.{key}')
        elif isinstance(left, list):
            if len(left) != len(right):
                found.append(f'{where}: length {len(left)} != {len(right)}')
            for index, (a, b) in enumerate(zip(left, right)):
                visit(a, b, f'{where}[{index}]')
        elif isinstance(left, float):
            if not math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-10):
                found.append(f'{where}: {left!r} != {right!r}')
        elif left != right:
            found.append(f'{where}: {left!r} != {right!r}')

    visit(expected, actual, path)
    return found
