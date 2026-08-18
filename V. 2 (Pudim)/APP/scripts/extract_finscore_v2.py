"""Extrai o núcleo metodológico do notebook FinScore Pudim 2.0.20.

O gerador seleciona células por sua função metodológica, não por intervalos de
linhas. Blocos de leitura, apresentação, exportação e execução do notebook são
deliberadamente excluídos.

Execute a partir da pasta APP:

    .venv/bin/python scripts/extract_finscore_v2.py
"""

from __future__ import annotations

import ast
import json
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
SOURCE = (
    APP_DIR.parent
    / "MODELO"
    / "algoritmos"
    / "Versao 20"
    / "FinScore_V2_0_20.ipynb"
)
TARGET = APP_DIR / "app_front" / "finscore_v2" / "core.py"

# Células que contêm exclusivamente parâmetros/estruturas metodológicos.
ASSIGNMENT_CELLS = {
    28, 30, 32, 33, 34, 37, 39, 41, 42, 44, 49, 50, 74,
}
# Células com funções e classes necessárias ao motor e aos autotestes.
DEFINITION_CELLS = {17, 22, 49, 50, 52, 54, 56, 60, 62, 74}

RUNTIME_ASSIGNMENTS = {
    "EXPORTAR_EXCEL",
    "CAMINHO_NOTEBOOK_MODELO",
    "HASH_CODIGO_RECALCULADO",
    "HASH_CODIGO_VERIFICAVEL",
    "STATUS_HASH_CODIGO",
    "df_springate_complementar",
    "df_fleuriet_complementar",
    "status_indices_complementares",
}


def _assigned_names(node: ast.AST) -> set[str]:
    targets = getattr(node, "targets", None)
    if targets is None:
        targets = [getattr(node, "target", None)]
    return {target.id for target in targets if isinstance(target, ast.Name)}


def _nodes_from_cell(index: int, source: str) -> list[ast.stmt]:
    parsed = ast.parse(source, filename=f"{SOURCE}:cell-{index}")
    selected: list[ast.stmt] = []
    for node in parsed.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)) and index <= 62:
            selected.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and index in DEFINITION_CELLS:
            selected.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            names = _assigned_names(node)
            if index == 21 and "VERSAO_MODELO" in names:
                selected.append(node)
            elif index == 22 and names & {"NOME_NOTEBOOK_MODELO", "HASH_CODIGO_MODELO"}:
                selected.append(node)
            elif index in ASSIGNMENT_CELLS and not names & RUNTIME_ASSIGNMENTS:
                selected.append(node)
    return selected


def main() -> None:
    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    body: list[ast.stmt] = []
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code" or index > 74:
            continue
        body.extend(_nodes_from_cell(index, "".join(cell.get("source", []))))

    extracted = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(extracted)
    preamble = '''\
"""Núcleo metodológico FinScore Pudim 2.0.20.

ARQUIVO GERADO. A fonte de verdade é
``MODELO/algoritmos/Versao 20/FinScore_V2_0_20.ipynb``.
Regere com ``scripts/extract_finscore_v2.py`` após uma mudança metodológica.

Este módulo contém somente definições e constantes. Ele não lê arquivos, não
exporta planilhas, não imprime resultados e não executa simulações ao importar.
"""

from __future__ import annotations

'''
    defaults = '''

# Estado neutro necessário pelos autotestes extraídos do notebook.
NUM_SIMULACOES = 1000
SEMENTE = 20260723
EXECUTAR_AUTOTESTES = False
DATA_HORA_PROCESSAMENTO = None
HASH_CODIGO_RECALCULADO = None
HASH_CODIGO_VERIFICAVEL = False
STATUS_HASH_CODIGO = "NAO_VERIFICADO"
MODELO_APTO = False
diagnosticos_simulacao = {}
diagnosticos_simulacao_correlacionada = {}
'''
    TARGET.write_text(preamble + ast.unparse(extracted) + defaults, encoding="utf-8")
    print(f"Gerado: {TARGET}")


if __name__ == "__main__":
    main()
