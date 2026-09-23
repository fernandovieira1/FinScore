"""Reconciliações explicativas do parecer; não participam do score nem dos gates."""
from __future__ import annotations

import math


def capital_bridges(contract) -> list[dict]:
    points = {(p.campo, p.exercicio): p.valor
              for p in [*contract.dados.utilizados, *contract.dados.derivados]}

    def number(field, year):
        value = points.get((field, year))
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value) if math.isfinite(value) else None

    def difference(left, right):
        return None if left is None or right is None else left - right

    result = []
    fleuriet = {item.exercicio: item for item in contract.evidencias_suplementares.fleuriet}
    for year in contract.identificacao.periodos.analisado.exercicios:
        equity = number("p_Patrimonio_Liquido", year)
        noncurrent = number("d_Ativo_Nao_Circulante", year)
        cash = number("p_Caixa_Equivalentes", year)
        loans = number("p_Emprestimos_Financiamentos_CP", year)
        strict = difference(cash, loans)
        item = fleuriet.get(year)
        treasury = item.saldo_tesouraria if item is not None else None
        result.append({"ano": year, "patrimonio_liquido": equity, "ativo_nao_circulante": noncurrent,
                       "pl_menos_anc": difference(equity, noncurrent), "caixa": cash,
                       "emprestimos_cp": loans, "tesouraria_estrita": strict,
                       "tesouraria_simplificada": treasury,
                       "residual_tesouraria": difference(treasury, strict)})
    return result
