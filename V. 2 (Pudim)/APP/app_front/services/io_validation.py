"""Importação e validação de entradas do fluxo FinScore Pudim."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional, Tuple

import pandas as pd

try:
    from finscore_v2 import preparar_dados_contabeis
    from finscore_v2.core import PRIMARY, QUALITY_COLUMNS
except ModuleNotFoundError:  # Importação pelo pacote ``app_front`` nos testes.
    from app_front.finscore_v2 import preparar_dados_contabeis
    from app_front.finscore_v2.core import PRIMARY, QUALITY_COLUMNS


SHEET_NAME = "lancamentos"
EXPECTED_COLUMNS = ("ano", *PRIMARY)
IMPORT_REPORT_ATTR = "finscore_import_report"
EXTRA_COLUMNS_ATTR = "finscore_extra_columns"

BRIGADEIRO_COLUMNS = {
    "p_Caixa",
    "p_Contas_a_Receber",
    "p_Contas_a_Pagar",
    "p_Passivo_Total",
    "r_Receita_Total",
    "r_Custos",
    "r_Despesa_de_Impostos",
    "r_Despesa_de_Juros",
}


def validar_cliente(meta: Dict[str, Any]) -> Dict[str, str]:
    errors: Dict[str, str] = {}
    if not str(meta.get("empresa") or "").strip():
        errors["empresa"] = "Informe o nome da empresa."
    if not str(meta.get("cnpj") or "").strip():
        errors["cnpj"] = "Informe o CNPJ."

    try:
        initial_year = int(meta.get("ano_inicial"))
        final_year = int(meta.get("ano_final"))
        if initial_year > final_year:
            errors["anos"] = "Ano inicial não pode ser maior que ano final."
        elif final_year - initial_year != 2:
            errors["anos"] = "O Pudim exige exatamente três exercícios consecutivos."
        if initial_year < 2000 or final_year > 2100:
            errors["faixa"] = "Informe anos entre 2000 e 2100."
    except (TypeError, ValueError):
        errors["anos"] = "Anos inválidos."

    try:
        serasa = int(meta.get("serasa"))
        if not 0 <= serasa <= 1000:
            raise ValueError
    except (TypeError, ValueError):
        errors["serasa"] = "Serasa deve estar entre 0 e 1000."

    date_text = str(meta.get("serasa_data") or "").strip()
    try:
        datetime.strptime(date_text, "%d/%m/%Y")
    except ValueError:
        errors["serasa_data"] = "Informe uma data de consulta válida em DD/MM/AAAA."
    return errors


def _sheet_name_case_insensitive(xls: pd.ExcelFile, wanted: str) -> Optional[str]:
    for sheet in xls.sheet_names:
        if str(sheet).strip().casefold() == wanted.casefold():
            return sheet
    return None


def _normalize_column_labels(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]
    duplicates = normalized.columns[normalized.columns.duplicated()].tolist()
    if duplicates:
        raise ValueError(f"Há colunas duplicadas na aba {SHEET_NAME}: {duplicates}")
    return normalized


def _detect_brigadeiro(columns: set[str]) -> bool:
    return len(columns & BRIGADEIRO_COLUMNS) >= 4


def validar_dataframe_importado(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida esquema e células sem alterar os valores originais retornados."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError(f"A aba {SHEET_NAME} está vazia.")

    source = _normalize_column_labels(df)
    columns = set(source.columns)
    missing = [column for column in EXPECTED_COLUMNS if column not in columns]
    if missing:
        if _detect_brigadeiro(columns):
            raise ValueError(
                "A planilha usa o formato da versão 1 (Brigadeiro). "
                "Envie uma planilha no formato Pudim 2.0.13 com as 21 contas primárias."
            )
        casefold_map = {column.casefold(): column for column in source.columns}
        case_mismatches = [
            f"{casefold_map[column.casefold()]} → {column}"
            for column in missing
            if column.casefold() in casefold_map
        ]
        detail = f" Diferenças de maiúsculas/minúsculas: {case_mismatches}." if case_mismatches else ""
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}.{detail}")

    extra = [column for column in source.columns if column not in EXPECTED_COLUMNS]
    original = source.loc[:, EXPECTED_COLUMNS].copy()

    # Executa o mesmo parser usado pelo motor apenas para diagnóstico. O
    # DataFrame devolvido continua sendo ``original`` e preserva textos/NaN.
    _, report = preparar_dados_contabeis(original)
    # ``DataFrame.attrs`` é propagado pelo pandas. Guardar outro DataFrame aqui
    # quebra operações como ``melt``/``concat``, que comparam attrs usando ``==``.
    original.attrs[IMPORT_REPORT_ATTR] = report.to_dict(orient="records")
    original.attrs[EXTRA_COLUMNS_ATTR] = extra
    return original, report


def obter_relatorio_importacao(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    report = df.attrs.get(IMPORT_REPORT_ATTR)
    if isinstance(report, pd.DataFrame):  # Compatibilidade com sessões antigas.
        return report.copy()
    if isinstance(report, list):
        return pd.DataFrame(report, columns=QUALITY_COLUMNS)
    return pd.DataFrame(columns=QUALITY_COLUMNS)


def obter_colunas_extras(df: pd.DataFrame | None) -> list[str]:
    if df is None:
        return []
    value = df.attrs.get(EXTRA_COLUMNS_ATTR, [])
    return list(value) if isinstance(value, (list, tuple)) else []


def ler_planilha(
    upload_or_url,
) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[str]]:
    """Lê exclusivamente a aba ``lancamentos`` e preserva dados reportados."""
    try:
        source = upload_or_url
        if hasattr(upload_or_url, "getvalue"):
            source = BytesIO(upload_or_url.getvalue())

        workbook = pd.ExcelFile(source, engine="openpyxl")
        sheet = _sheet_name_case_insensitive(workbook, SHEET_NAME)
        if sheet is None:
            raise ValueError(
                f"A planilha deve conter a aba '{SHEET_NAME}'. "
                f"Abas encontradas: {workbook.sheet_names}"
            )
        raw = pd.read_excel(workbook, sheet_name=sheet, engine="openpyxl")
        validated, _ = validar_dataframe_importado(raw)
        return validated, sheet, None
    except ImportError:
        return (
            None,
            None,
            "Dependência 'openpyxl' ausente. Instale as dependências do projeto.",
        )
    except Exception as error:
        return None, None, str(error)


def check_minimo(df: pd.DataFrame) -> Dict[str, list]:
    """Compatibilidade temporária com a view, agora cobrindo todo o Pudim."""
    columns = set(df.columns) if isinstance(df, pd.DataFrame) else set()
    missing = [column for column in EXPECTED_COLUMNS if column not in columns]
    return {
        "BP_faltando": [column for column in missing if column.startswith("p_")],
        "DRE_faltando": [column for column in missing if column.startswith("r_")],
        "colunas_faltantes": missing,
    }


def gerar_modelo_planilha(anos: tuple[int, int, int] | None = None) -> bytes:
    """Gera um arquivo Pudim vazio, sem dados de qualquer empresa real."""
    years = anos or (2023, 2024, 2025)
    if len(years) != 3:
        raise ValueError("O modelo deve conter exatamente três exercícios.")

    data = pd.DataFrame({"ano": years})
    for column in PRIMARY:
        data[column] = pd.NA
    dictionary = pd.DataFrame(
        {
            "conta": PRIMARY,
            "grupo": ["Balanço Patrimonial" if item.startswith("p_") else "DRE" for item in PRIMARY],
            "observacao": "Preencher valor reportado; deixar vazio quando ausente. Não substituir ausência por zero.",
        }
    )
    instructions = pd.DataFrame(
        {
            "instrucoes": [
                "Use exatamente a aba e as colunas fornecidas.",
                "Informe três exercícios consecutivos.",
                "Despesas e custos devem ser informados em valor absoluto.",
                "Somente patrimônio líquido, resultado antes de IR/CSLL e lucro líquido podem ser negativos.",
                "Célula vazia significa informação ausente; zero significa valor conhecido igual a zero.",
            ]
        }
    )
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        dictionary.to_excel(writer, sheet_name="dicionario", index=False)
        instructions.to_excel(writer, sheet_name="notas_preenchimento", index=False)
    return buffer.getvalue()
