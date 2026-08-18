"""Apresentação das contas Pudim na aba Dados Contábeis da Análise."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd
import streamlit as st


PRIMARY_LABELS = {
    "p_Caixa_Equivalentes": "Caixa e Equivalentes",
    "p_Contas_Receber_Clientes": "Contas a Receber de Clientes",
    "p_Estoques": "Estoques",
    "p_Ativo_Circulante": "Ativo Circulante",
    "p_Imobilizado_Liquido": "Imobilizado Líquido",
    "p_Ativo_Total": "Ativo Total",
    "p_Fornecedores": "Fornecedores",
    "p_Obrigacoes_Tributarias_CP": "Obrigações Tributárias — Curto Prazo",
    "p_Obrigacoes_Trabalhistas_CP": "Obrigações Trabalhistas — Curto Prazo",
    "p_Passivo_Circulante": "Passivo Circulante",
    "p_Passivo_Nao_Circulante": "Passivo Não Circulante",
    "p_Emprestimos_Financiamentos_CP": "Empréstimos e Financiamentos — Curto Prazo",
    "p_Emprestimos_Financiamentos_LP": "Empréstimos e Financiamentos — Longo Prazo",
    "p_Patrimonio_Liquido": "Patrimônio Líquido",
    "r_Receita_Liquida": "Receita Líquida",
    "r_CMV_CPV_CSV": "CMV / CPV / CSV",
    "r_Resultado_Antes_IR_CSLL": "Resultado Antes de IR/CSLL",
    "r_Lucro_Liquido": "Lucro Líquido",
    "r_Receitas_Financeiras": "Receitas Financeiras",
    "r_Despesa_IR_CSLL": "Despesa de IR/CSLL",
    "r_Despesas_Financeiras": "Despesas Financeiras",
}

WORD_LABELS = {
    "Ativo": "Ativo",
    "Nao": "Não",
    "Circulante": "Circulante",
    "Outros": "Outros",
    "Outras": "Outras",
    "Obrigacoes": "Obrigações",
    "Passivo": "Passivo",
    "Exigivel": "Exigível",
    "Divida": "Dívida",
    "Financeira": "Financeira",
    "Bruta": "Bruta",
    "Liquida": "Líquida",
    "Capital": "Capital",
    "Giro": "Giro",
    "Operacional": "Operacional",
    "Simplificado": "Simplificado",
    "Simplificada": "Simplificada",
    "Necessidade": "Necessidade",
    "Saldo": "Saldo",
    "Tesouraria": "Tesouraria",
    "Lucro": "Lucro",
    "Resultado": "Resultado",
    "Apos": "Após",
    "Impostos": "Impostos",
    "Efeitos": "Efeitos",
    "Tributacao": "Tributação",
    "Medio": "Médio",
}


def formatar_nome_conta(code: str) -> str:
    if code in PRIMARY_LABELS:
        return PRIMARY_LABELS[code]
    text = str(code)
    if text.startswith(("p_", "r_", "d_")):
        text = text[2:]
    words = text.replace("_", " ").title().split()
    label = " ".join(WORD_LABELS.get(word, word) for word in words)
    replacements = {
        "Cmv Cpv Csv": "CMV / CPV / CSV",
        "Ir Csll": "IR/CSLL",
        "Ebit": "EBIT",
        "Ncg": "NCG",
        "Cp": "Curto Prazo",
        "Lp": "Longo Prazo",
    }
    for source, target in replacements.items():
        label = label.replace(source, target)
    return label


def formatar_moeda(value: Any) -> str:
    if pd.isna(value):
        return "Ausente"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"R$ {number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def montar_tabela_contas(
    df: pd.DataFrame | None,
    contas: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Transforma exercícios em colunas e contas em linhas."""
    if df is None or df.empty or "ano" not in df.columns:
        return pd.DataFrame(columns=["Código", "Conta"])
    selected = list(contas) if contas is not None else [
        column for column in df.columns if column != "ano"
    ]
    selected = [column for column in selected if column in df.columns]
    if not selected:
        return pd.DataFrame(columns=["Código", "Conta"])

    work = df[["ano", *selected]].copy()
    work["ano"] = pd.to_numeric(work["ano"], errors="coerce")
    work = work.loc[work["ano"].notna()].sort_values("ano")
    years = [int(year) for year in work["ano"].tolist()]
    transposed = work.set_index("ano")[selected].T
    transposed.columns = [str(year) for year in years]
    transposed.insert(0, "Conta", [formatar_nome_conta(code) for code in transposed.index])
    transposed.insert(0, "Código", transposed.index)
    transposed = transposed.reset_index(drop=True)
    for year in map(str, years):
        transposed[year] = transposed[year].map(formatar_moeda)
    return transposed


def resumir_contas(output: dict[str, Any]) -> dict[str, int]:
    reported = output.get("df_contas_reportadas")
    derived = output.get("df_contas_derivadas")
    trace = output.get("df_rastreabilidade_contas")
    quality = output.get("df_qualidade")
    total = len([column for column in getattr(reported, "columns", []) if column != "ano"])
    missing = (
        int(reported.drop(columns="ano", errors="ignore").isna().sum().sum())
        if isinstance(reported, pd.DataFrame)
        else 0
    )
    changed = (
        int(pd.Series(trace["alterado"]).fillna(False).astype(bool).sum())
        if isinstance(trace, pd.DataFrame) and "alterado" in trace
        else 0
    )
    derived_count = len(
        [column for column in getattr(derived, "columns", []) if str(column).startswith("d_")]
    )
    critical = (
        int(quality["severidade"].eq("CRITICA").sum())
        if isinstance(quality, pd.DataFrame) and "severidade" in quality
        else 0
    )
    return {
        "contas_primarias": total,
        "celulas_ausentes": missing,
        "valores_alterados": changed,
        "contas_derivadas": derived_count,
        "ocorrencias_criticas": critical,
    }


def _show_account_groups(df: pd.DataFrame | None) -> None:
    balance = [code for code in PRIMARY_LABELS if code.startswith("p_")]
    income = [code for code in PRIMARY_LABELS if code.startswith("r_")]
    st.markdown("#### Balanço Patrimonial")
    st.dataframe(
        montar_tabela_contas(df, balance),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("#### Demonstração do Resultado")
    st.dataframe(
        montar_tabela_contas(df, income),
        use_container_width=True,
        hide_index=True,
    )


def _show_audit_table(title: str, table: Any, empty_message: str) -> None:
    st.markdown(f"#### {title}")
    if not isinstance(table, pd.DataFrame) or table.empty:
        st.success(empty_message)
        return
    display = table.copy()
    if "ano" in display.columns:
        # Alertas podem usar anos inteiros e o marcador textual ``SERIE``.
        # Uniformizar evita coerção automática/ruidosa do Arrow no Streamlit.
        display["ano"] = display["ano"].map(
            lambda value: "" if pd.isna(value) else str(value)
        )
    if "conta" in display.columns:
        display.insert(
            display.columns.get_loc("conta") + 1,
            "nome_conta",
            display["conta"].map(formatar_nome_conta),
        )
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_contas_pudim(output: dict[str, Any], meta: dict[str, Any]) -> None:
    reported = output.get("df_contas_reportadas")
    if not isinstance(reported, pd.DataFrame) or reported.empty:
        st.warning("Nenhum dado contábil reportado está disponível.")
        return

    status = output.get("status_qualidade", {})
    reliability = output.get("confiabilidade", {})
    summary = resumir_contas(output)

    st.markdown("<h3 style='text-align:left;'>📖 Contas</h3>", unsafe_allow_html=True)
    st.caption(
        f"{meta.get('empresa') or '-'} · três exercícios · valores em reais. "
        "Ausência de informação não é tratada como zero."
    )
    columns = st.columns(5)
    columns[0].metric("Contas primárias", summary["contas_primarias"])
    columns[1].metric("Células ausentes", summary["celulas_ausentes"])
    columns[2].metric("Valores alterados", summary["valores_alterados"])
    columns[3].metric("Contas derivadas", summary["contas_derivadas"])
    columns[4].metric(
        "Confiabilidade",
        f"{float(reliability.get('indice_confiabilidade', 0)):.1%}",
        str(reliability.get("classificacao_confiabilidade", "-")),
    )

    classification = status.get("classificacao_uso")
    status_text = str(status.get("status") or classification or "Status indisponível")
    if classification == "BLOQUEADO":
        st.error(status_text)
    elif classification == "CALCULADO_COM_ALERTAS":
        st.warning(status_text)
    else:
        st.success(status_text)

    reported_tab, used_tab, derived_tab, audit_tab = st.tabs(
        ["Reportadas", "Usadas no cálculo", "Derivadas", "Qualidade e auditoria"]
    )
    with reported_tab:
        st.caption("Valores exatamente como interpretados na origem, antes de correções controladas.")
        _show_account_groups(reported)
    with used_tab:
        st.caption(
            "Cópia analítica efetivamente usada pelo motor. O original reportado permanece preservado."
        )
        _show_account_groups(output.get("df_contas_analise"))
    with derived_tab:
        derived = output.get("df_contas_derivadas")
        derived_codes = [
            column for column in getattr(derived, "columns", []) if str(column).startswith("d_")
        ]
        table = montar_tabela_contas(derived, derived_codes)
        if table.empty:
            st.info("Contas derivadas indisponíveis porque o gate bloqueou o cálculo.")
        else:
            st.caption("Contas calculadas pelo motor; não são lançamentos da planilha.")
            st.dataframe(table, use_container_width=True, hide_index=True)
    with audit_tab:
        _show_audit_table(
            "Ocorrências de qualidade",
            output.get("df_qualidade"),
            "Nenhuma ocorrência de qualidade registrada.",
        )
        _show_audit_table(
            "Correções e quarentenas",
            output.get("df_correcoes_auditoria"),
            "Nenhuma correção ou quarentena aplicada.",
        )
        _show_audit_table(
            "Alertas de potencial viés",
            output.get("df_alertas_vies"),
            "Nenhum alerta de potencial viés registrado.",
        )
        trace = output.get("df_rastreabilidade_contas")
        with st.expander("Rastreabilidade completa das contas"):
            _show_audit_table(
                "Origem dos valores",
                trace,
                "Rastreabilidade indisponível.",
            )
