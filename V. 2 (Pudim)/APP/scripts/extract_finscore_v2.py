"""Extrai o núcleo metodológico do script congelado FinScore 2.0.13.

O gerador mantém funções, classes e constantes metodológicas, mas descarta os
blocos de execução do notebook (leitura de caminho, prints, gráficos e exportação).
Execute a partir da pasta APP:

    .venv/bin/python scripts/extract_finscore_v2.py
"""

from __future__ import annotations

import ast
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
SOURCE = APP_DIR / "diversos" / "FinScoreV12.3.py"
TARGET = APP_DIR / "app_front" / "finscore_v2" / "core.py"

RUNTIME_ASSIGNMENTS = {
    "CAMINHO_PLANILHA",
    "ABA_DADOS",
    "EXPORTAR_EXCEL",
    "CAMINHO_NOTEBOOK_MODELO",
    "HASH_CODIGO_RECALCULADO",
    "HASH_CODIGO_VERIFICAVEL",
    "STATUS_HASH_CODIGO",
    "DATA_HORA_PROCESSAMENTO",
    "ARQUIVO_SAIDA",
    "NUM_SIMULACOES",
    "SEMENTE",
    "EXECUTAR_AUTOTESTES",
}


def _assigned_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    targets = getattr(node, "targets", None)
    if targets is None:
        target = getattr(node, "target", None)
        targets = [target] if target is not None else []
    for target in targets:
        if isinstance(target, ast.Name):
            names.add(target.id)
    return names


def _keep(node: ast.AST) -> bool:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return node.lineno <= 754
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        return 167 <= node.lineno <= 3490
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        if not 188 <= node.lineno <= 1660:
            return False
        return not (_assigned_names(node) & RUNTIME_ASSIGNMENTS)
    if isinstance(node, (ast.Assert, ast.For)):
        return 734 <= node.lineno <= 740
    return False


def main() -> None:
    source_text = SOURCE.read_text(encoding="utf-8")
    parsed = ast.parse(source_text, filename=str(SOURCE))
    body = [node for node in parsed.body if _keep(node)]
    extracted = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(extracted)

    preamble = '''\
"""Núcleo metodológico FinScore Pudim 2.0.13.

ARQUIVO GERADO. A fonte de verdade é ``diversos/FinScoreV12.3.py``.
Regere com ``scripts/extract_finscore_v2.py`` após uma mudança metodológica.

Este módulo contém somente definições e constantes. Ele não lê arquivos, não
exporta planilhas, não imprime resultados e não executa simulações ao importar.
"""

from __future__ import annotations

'''
    defaults = '''

# Estado neutro necessário pelos autotestes herdados do script congelado.
NUM_SIMULACOES = 1000
SEMENTE = 20260723
EXECUTAR_AUTOTESTES = False
HASH_CODIGO_RECALCULADO = None
HASH_CODIGO_VERIFICAVEL = False
STATUS_HASH_CODIGO = "NAO_VERIFICADO"
MODELO_APTO = False
diagnosticos_simulacao = {}
diagnosticos_simulacao_correlacionada = {}
'''
    TARGET.write_text(
        preamble + ast.unparse(extracted) + defaults,
        encoding="utf-8",
    )
    print(f"Gerado: {TARGET}")


if __name__ == "__main__":
    main()
