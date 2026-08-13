"""Cria o notebook FinScore 2.0.14 restaurando a exportação auditável 2.12."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V12 = ROOT / "MODELO" / "algoritmos" / "Versao 12" / "FinScore_V2_12-5.ipynb"
V13 = ROOT / "MODELO" / "algoritmos" / "Versao 13" / "FinScore_V2_13.ipynb"
V14_DIR = ROOT / "MODELO" / "algoritmos" / "Versao 14"
V14 = V14_DIR / "FinScore_V2_14.ipynb"


def _source(cell: dict) -> str:
    return "".join(cell.get("source", []))


def _set_source(cell: dict, source: str) -> None:
    cell["source"] = source.splitlines(keepends=True)


def _code_hash(notebook: dict) -> str:
    sources = []
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        if "finscore_editavel" in cell.get("metadata", {}).get("tags", []):
            continue
        source = _source(cell)
        source = re.sub(
            r'(?m)^HASH_CODIGO_MODELO\s*=\s*["\'][0-9a-f_<>-]{16,}["\']',
            'HASH_CODIGO_MODELO = "<NEUTRALIZADO>"',
            source,
        )
        sources.append(source)
    payload = json.dumps(
        sources, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _export_cell(v12: dict) -> dict:
    candidates = [
        cell for cell in v12["cells"]
        if "def export_audit_workbook" in _source(cell)
    ]
    if len(candidates) != 1:
        raise RuntimeError("Célula exportadora 2.12 não encontrada de forma unívoca.")
    cell = deepcopy(candidates[0])
    source = _source(cell)
    old = '''if EXPORTAR_EXCEL:
    export_audit_workbook(ARQUIVO_SAIDA)
    print(f"Resultados salvos em: {ARQUIVO_SAIDA.resolve()}")
else:
    print("Exportação Excel desativada.")
'''
    new = '''if EXPORTAR_EXCEL:
    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    export_audit_workbook(ARQUIVO_SAIDA)
    if not ARQUIVO_SAIDA.is_file() or ARQUIVO_SAIDA.stat().st_size == 0:
        raise IOError(f"A exportação não criou um arquivo válido: {ARQUIVO_SAIDA}")
    PLANILHA_EXPORTADA = True
    print(f"Resultados salvos em: {ARQUIVO_SAIDA.resolve()}")
else:
    PLANILHA_EXPORTADA = False
    print("Exportação Excel desativada.")
'''
    if old not in source:
        raise RuntimeError("Rodapé esperado da exportação 2.12 não encontrado.")
    source = source.replace(old, new)
    export_marker = "def export_audit_workbook(path: Path):\n"
    canonicalizer = '''def _cargas_pca_orientadas_para_exportacao(table):
    """Fixa o sinal arbitrário do PCA: maior carga absoluta fica positiva."""
    result = table.copy()
    if "nucleo" not in result.columns:
        return result
    for nucleo in result["nucleo"].dropna().unique():
        mask = result["nucleo"].eq(nucleo)
        for component in [column for column in result.columns if str(column).startswith("PC")]:
            values = pd.to_numeric(result.loc[mask, component], errors="coerce")
            if values.notna().any() and values.loc[values.abs().idxmax()] < 0:
                result.loc[mask, component] = -values
    return result


'''
    if export_marker not in source:
        raise RuntimeError("Função de exportação 2.12 não encontrada.")
    source = source.replace(export_marker, canonicalizer + export_marker, 1)
    source = source.replace(
        '"cargas_pca": df_cargas_pca,',
        '"cargas_pca": _cargas_pca_orientadas_para_exportacao(df_cargas_pca),',
        1,
    )
    _set_source(cell, source)
    cell["execution_count"] = None
    cell["outputs"] = []
    cell["id"] = "exportacao-auditavel-v214"
    return cell


def build() -> Path:
    v12 = json.loads(V12.read_text(encoding="utf-8"))
    notebook = json.loads(V13.read_text(encoding="utf-8"))

    for cell in notebook["cells"]:
        source = _source(cell)
        source = source.replace("FinScore v2.0.13 — PUDIM", "FinScore v2.0.14 — PUDIM")
        source = source.replace("Versão 2.0.13", "Versão 2.0.14", 1)
        source = source.replace('VERSAO_MODELO = "2.0.13"', 'VERSAO_MODELO = "2.0.14"')
        source = source.replace(
            'NOME_NOTEBOOK_MODELO = "FinScore_V2_13_retificado.ipynb"',
            'NOME_NOTEBOOK_MODELO = "FinScore_V2_14.ipynb"',
        )
        if cell.get("cell_type") == "code" and "## Alterações metodológicas: Versão 2.0.14" in source:
            marker = "### ===============================================\n## Alterações metodológicas: Versão 2.0.14\n### ===============================================\n"
            source = source.replace(
                marker,
                marker + "# 1. Restaura a exportação auditável integral da versão 2.12.\n"
                "# 2. Confirma a criação física do XLSX antes de anunciar sucesso.\n"
                "# 3. Mantém inalteradas as regras de cálculo da versão 2.13.\n",
                1,
            )
        _set_source(cell, source)
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            cell["outputs"] = []

    final_index = next(
        index for index, cell in enumerate(notebook["cells"])
        if "def _formatar_numero_resumo" in _source(cell)
        and "Consulte a planilha para resultados completos" in _source(cell)
    )
    notebook["cells"].insert(final_index, _export_cell(v12))

    final_cell = notebook["cells"][final_index + 1]
    final_source = _source(final_cell).replace(
        "if exportar_excel and arquivo_saida is not None:",
        "if exportar_excel and arquivo_saida is not None and globals().get(\"PLANILHA_EXPORTADA\", False):",
    )
    _set_source(final_cell, final_source)

    placeholder = "0" * 64
    for cell in notebook["cells"]:
        source = re.sub(
            r'(?m)^HASH_CODIGO_MODELO\s*=\s*["\'][0-9a-f]{64}["\']',
            f'HASH_CODIGO_MODELO = "{placeholder}"',
            _source(cell),
        )
        _set_source(cell, source)
    model_hash = _code_hash(notebook)
    for cell in notebook["cells"]:
        _set_source(cell, _source(cell).replace(placeholder, model_hash))

    V14_DIR.mkdir(parents=True, exist_ok=True)
    V14.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    if _code_hash(notebook) != model_hash:
        raise RuntimeError("Hash do notebook 2.14 não é reprodutível.")
    return V14


if __name__ == "__main__":
    print(build())
