from __future__ import annotations

import math
import logging
import re
from datetime import datetime
from html import escape
from typing import Any, Dict

import streamlit as st
import streamlit.components.v1 as components

from components import nav
from components.llm_client import (
    MODEL_NAME,
    MODEL_REASONING_EFFORT,
    MODEL_TEMPERATURE,
    ReportGenerationServiceError,
    get_last_usage,
)
from components.navigation_flow import NavigationFlow
from components.parecer_data_schema import ParecerData, RecommendationCode
from components.session_state import clear_flow_state
from components.token_utils import now_ts
from pdf.export_pdf import contar_paginas_pdf, gerar_pdf_parecer
from services.credit_governance import (
    GOVERNANCE_SESSION_KEY,
    GovernanceAction,
    GovernanceSessionState,
    GovernanceStage,
    governance_fingerprint,
    load_or_initialize_governance_state,
    register_analyst_manifestation,
    register_authority_decision,
)
from services.credit_policy import decide_pudim
from services.analysis_dossier import AnalysisDossierStore
from services.parecer_data_builder import (
    build_finscore_recommendation,
    build_parecer_data,
)
from services.parecer_generator import generate_parecer_document


DECISION_ICONS = {
    "aprovar": "✅ Aprovar",
    "nao_aprovar": "❌ Não aprovar",
    "dados_inconsistentes": "⚠️ Dados inconsistentes",
}
GOVERNANCE_LABELS = {
    RecommendationCode.APPROVE: "Aprovar",
    RecommendationCode.DO_NOT_APPROVE: "Não aprovar",
    RecommendationCode.INCONSISTENT_DATA: "Dados inconsistentes",
}
GOVERNANCE_STAGE_LABELS = {
    GovernanceStage.RECOMMENDATION: "Recomendação FinScore",
    GovernanceStage.ANALYST: "Manifestação do analista",
    GovernanceStage.AUTHORITY: "Decisão da alçada",
}
GOVERNANCE_ACTION_LABELS = {
    GovernanceAction.REGISTERED: "registrada",
    GovernanceAction.REPLACED: "substituída",
    GovernanceAction.INVALIDATED: "invalidada",
}

logger = logging.getLogger(__name__)
PARECER_POLICY_SIGNATURE = "three-decisions-finscore-only-v3"
DOSSIER_STORE = AnalysisDossierStore()


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _serasa_record(output: Dict[str, Any]) -> Dict[str, Any]:
    frame = output.get("df_serasa")
    if frame is None or getattr(frame, "empty", True):
        return {}
    return frame.iloc[-1].to_dict()


def _fmt_score(value: Any) -> str:
    number = _number(value)
    return "N/A" if number is None else f"{number:.2f}"


def _fmt_percent(value: Any) -> str:
    number = _number(value)
    return "N/A" if number is None else f"{number:.2%}".replace(".", ",")


def _readable_status(value: Any) -> str:
    text = str(value or "Não informado").replace("_", " ").strip().lower()
    return text[:1].upper() + text[1:]


def _safe_filename(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return clean.strip("_") or "Empresa"


def _cancel_analysis_polling() -> None:
    components.html(
        """
        <script>
        (function(){
            const win = window.parent || window;
            if (win && win.__fsInsightTimer) {
                clearTimeout(win.__fsInsightTimer);
                win.__fsInsightTimer = null;
            }
        })();
        </script>
        """,
        height=0,
    )


def _invalidate_generated_report() -> None:
    for key in (
        "parecer_gerado",
        "parecer_narrativa_estruturada",
        "parecer_contexto_auditavel",
        "parecer_pdf",
        "parecer_pdf_pages",
    ):
        st.session_state.pop(key, None)


def _processed_at(output: Dict[str, Any]) -> Any:
    model = output.get("modelo") if isinstance(output.get("modelo"), dict) else {}
    return model.get("processado_em")


def _processed_datetime(output: Dict[str, Any]) -> datetime:
    value = _processed_at(output)
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))


def _load_governance(
    output: Dict[str, Any],
    meta: Dict[str, Any],
    policy: Dict[str, Any],
) -> GovernanceSessionState:
    recommendation = build_finscore_recommendation(output, policy)
    signature = governance_fingerprint(output, recommendation)
    owner_email = st.session_state.get("finscore_user_email")
    analysis_id = DOSSIER_STORE.ensure_analysis(
        fingerprint=signature,
        processed_at=_processed_datetime(output),
        recommendation_code=recommendation.codigo.value,
        governance_signature=signature,
        meta=meta,
        output=output,
        owner_email=owner_email,
    )
    meta["analise_id"] = analysis_id
    persisted_state = DOSSIER_STORE.load_governance(analysis_id)
    state, reset = load_or_initialize_governance_state(
        persisted_state or st.session_state.get(GOVERNANCE_SESSION_KEY),
        recommendation,
        signature,
        registered_at=_processed_at(output),
    )
    st.session_state[GOVERNANCE_SESSION_KEY] = state.model_dump(mode="json")
    if reset:
        _invalidate_generated_report()

    contract = build_parecer_data(
        output,
        meta,
        policy,
        governance=state.governanca,
    )
    st.session_state["parecer_dados_estruturados"] = contract.model_dump(mode="json")
    st.session_state["parecer_dossie_funcional"] = DOSSIER_STORE.save_contract(
        analysis_id,
        contract,
        state.model_dump(mode="json"),
        actor_email=owner_email,
    )
    if not reset and not st.session_state.get("parecer_gerado"):
        persisted_document = DOSSIER_STORE.load_document(analysis_id)
        if persisted_document:
            st.session_state["parecer_gerado"] = persisted_document
    return state


def _save_governance(
    state: GovernanceSessionState,
    output: Dict[str, Any],
    meta: Dict[str, Any],
    policy: Dict[str, Any],
    notice: str,
) -> None:
    contract = build_parecer_data(
        output,
        meta,
        policy,
        governance=state.governanca,
    )
    st.session_state["parecer_dossie_funcional"] = DOSSIER_STORE.save_contract(
        contract.analise_id,
        contract,
        state.model_dump(mode="json"),
        actor_email=st.session_state.get("finscore_user_email"),
        invalidate_report=True,
    )
    st.session_state[GOVERNANCE_SESSION_KEY] = state.model_dump(mode="json")
    st.session_state["parecer_dados_estruturados"] = contract.model_dump(mode="json")
    _invalidate_generated_report()
    st.session_state["_governance_notice"] = notice


def _governance_position(label: str, decision: Any | None) -> None:
    st.markdown(f"**{label}**")
    if decision is None:
        st.caption("Não registrada")
        return
    st.markdown(GOVERNANCE_LABELS[decision.resultado])
    st.caption(
        f"{decision.responsavel} · {decision.registrado_em.strftime('%d/%m/%Y %H:%M')}"
    )


def _render_governance(
    state: GovernanceSessionState,
    output: Dict[str, Any],
    meta: Dict[str, Any],
    policy: Dict[str, Any],
) -> None:
    governance = state.governanca
    recommendation = governance.recomendacao_finscore
    notice = st.session_state.pop("_governance_notice", None)
    if notice:
        st.success(notice)

    with st.expander("Governança de crédito", expanded=False):
        st.caption(
            "A recomendação FinScore é calculada pelas regras de crédito e não pode ser editada. "
            "A manifestação do analista e a decisão da alçada são posições independentes."
        )
        recommendation_col, analyst_col, authority_col = st.columns(3)
        with recommendation_col:
            st.markdown("**Recomendação FinScore**")
            st.markdown(GOVERNANCE_LABELS[recommendation.codigo])
            st.caption(
                f"Faixa {recommendation.faixa.title()} · "
                f"confiabilidade {_fmt_percent(recommendation.confiabilidade)}"
            )
        with analyst_col:
            _governance_position(
                "Manifestação do analista", governance.manifestacao_analista
            )
        with authority_col:
            _governance_position("Decisão da alçada", governance.decisao_alcada)

        if governance.divergencias:
            st.warning(
                f"Há {len(governance.divergencias)} divergência(s) registrada(s) entre as "
                "posições da governança. As justificativas estão preservadas no histórico."
            )

        analyst_tab, authority_tab, history_tab = st.tabs(
            ["Manifestação do analista", "Decisão da alçada", "Histórico"]
        )
        actor_email = str(st.session_state.get("finscore_user_email") or "").strip()
        responsible = actor_email or "Usuário não identificado"
        analyst_allowed = bool(actor_email)
        authority_allowed = DOSSIER_STORE.can_register_authority(responsible)
        options = list(RecommendationCode)

        with analyst_tab:
            current_analyst = governance.manifestacao_analista
            default_result = (
                current_analyst.resultado if current_analyst else recommendation.codigo
            )
            with st.form(f"governance_analyst_{state.assinatura_analise[:12]}"):
                analyst_result = st.selectbox(
                    "Posição do analista",
                    options,
                    index=options.index(default_result),
                    format_func=lambda item: GOVERNANCE_LABELS[item],
                    disabled=not analyst_allowed,
                )
                analyst_reason = st.text_area(
                    "Fundamentação",
                    value=current_analyst.justificativa if current_analyst else "",
                    placeholder=(
                        "Registre as evidências avaliadas e, se houver divergência, explique "
                        "objetivamente por que a recomendação FinScore não foi acompanhada."
                    ),
                    height=130,
                    disabled=not analyst_allowed,
                )
                st.caption(f"Responsável pelo registro: {responsible}")
                if not analyst_allowed:
                    st.caption(
                        "A manifestação exige identificação do usuário pela camada de acesso "
                        "da instituição."
                    )
                if governance.decisao_alcada is not None:
                    st.caption(
                        "Uma nova manifestação invalidará a decisão de alçada atual e exigirá "
                        "nova deliberação."
                    )
                submit_analyst = st.form_submit_button(
                    "Registrar manifestação",
                    use_container_width=True,
                    disabled=not analyst_allowed,
                )
            if submit_analyst:
                try:
                    updated = register_analyst_manifestation(
                        state,
                        analyst_result,
                        analyst_reason,
                        responsible,
                    )
                    _save_governance(
                        updated,
                        output,
                        meta,
                        policy,
                        "Manifestação do analista registrada.",
                    )
                    st.rerun()
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))

        with authority_tab:
            current_authority = governance.decisao_alcada
            reference_result = (
                governance.manifestacao_analista.resultado
                if governance.manifestacao_analista is not None
                else recommendation.codigo
            )
            default_result = (
                current_authority.resultado if current_authority else reference_result
            )
            with st.form(f"governance_authority_{state.assinatura_analise[:12]}"):
                authority_result = st.selectbox(
                    "Deliberação da alçada",
                    options,
                    index=options.index(default_result),
                    format_func=lambda item: GOVERNANCE_LABELS[item],
                    disabled=not authority_allowed,
                )
                authority_reason = st.text_area(
                    "Fundamentação da decisão",
                    value=current_authority.justificativa if current_authority else "",
                    placeholder=(
                        "Registre o fundamento da deliberação e, se houver divergência, explique "
                        "objetivamente por que a posição anterior não foi acompanhada."
                    ),
                    height=130,
                    disabled=not authority_allowed,
                )
                st.caption(f"Responsável pelo registro: {responsible}")
                if not authority_allowed:
                    st.caption(
                        "O usuário autenticado possui perfil de analista. O registro desta "
                        "deliberação requer perfil de alçada."
                    )
                submit_authority = st.form_submit_button(
                    "Registrar decisão da alçada",
                    use_container_width=True,
                    disabled=not authority_allowed,
                )
            if submit_authority:
                try:
                    updated = register_authority_decision(
                        state,
                        authority_result,
                        authority_reason,
                        responsible,
                    )
                    _save_governance(
                        updated,
                        output,
                        meta,
                        policy,
                        "Decisão da alçada registrada.",
                    )
                    st.rerun()
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))

        with history_tab:
            st.caption(
                "Os registros anteriores não são sobrescritos durante o ciclo da análise."
            )
            for item in reversed(governance.historico):
                stage = GOVERNANCE_STAGE_LABELS[item.etapa]
                action = GOVERNANCE_ACTION_LABELS[item.acao]
                label = GOVERNANCE_LABELS[item.resultado]
                st.markdown(
                    f"**{stage} {action}: {label}**  \n"
                    f"{item.registrado_em.strftime('%d/%m/%Y %H:%M')} · "
                    f"{item.responsavel}  \n"
                    f"{item.justificativa}"
                )

        st.caption(
            "Os registros são arquivados no dossiê da análise. Manifestações e deliberações "
            "ficam vinculadas ao usuário autenticado, à data e ao conteúdo registrado."
        )


def _render_policy_summary(
    output: Dict[str, Any],
    meta: Dict[str, Any],
    policy: Dict[str, Any],
) -> None:
    observed = output.get("finscore_observado") or {}
    status = output.get("status_qualidade") or {}
    serasa = _serasa_record(output)

    st.markdown(
        f"<div style='text-align:center;color:#708090;font-size:1.25rem'>"
        f"{escape(str(meta.get('empresa', 'Empresa')))} | "
        f"{escape(str(meta.get('cnpj', '')))}</div>",
        unsafe_allow_html=True,
    )

    col_score, col_quality, col_serasa, col_decision = st.columns(4)
    col_score.metric("FinScore prudencial", _fmt_score(observed.get("finscore_prudencial")))
    col_score.caption(f"Faixa FinScore: {_readable_status(policy['segmento_politica'])}")
    col_quality.metric("Confiabilidade", _fmt_percent(status.get("indice_confiabilidade")))
    col_quality.caption(_readable_status(status.get("classificacao_uso")))
    col_serasa.metric("Serasa", _fmt_score(serasa.get("serasa_score")))
    col_serasa.caption(_readable_status(serasa.get("status") or "Evidência separada"))
    decision_icon = DECISION_ICONS.get(policy["decisao"], "").split(" ", 1)[0]
    col_decision.markdown(
        f"""
        <div class="finscore-decision-card">
          <div class="finscore-decision-label">Recomendação FinScore</div>
          <div class="finscore-decision-value">{decision_icon} {escape(policy['rotulo'])}</div>
          <div class="finscore-decision-caption">Resultado calculado; não é a decisão da alçada</div>
        </div>
        <style>
          .finscore-decision-label {{ font-size: .875rem; margin-bottom: .35rem; }}
          .finscore-decision-value {{
            font-size: clamp(1.2rem, 2vw, 1.75rem);
            line-height: 1.2;
            min-height: 4.2rem;
            overflow-wrap: anywhere;
          }}
          .finscore-decision-caption {{
            color: #6b7280; font-size: .85rem; line-height: 1.25; margin-top: .4rem;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    decision = policy["decisao"]
    guarantee = policy.get("garantia") or {}
    if decision == "aprovar":
        if guarantee.get("recomendada"):
            st.success(
                "Recomendação: aprovar com garantia. Os sinais que fundamentam a mitigação e as "
                "providências recomendadas estão detalhados abaixo."
            )
        else:
            st.success(
                "Recomendação: aprovar sem indicação de garantia pelos critérios desta análise. "
                "A decisão permanece sujeita à alçada e aos controles usuais da instituição."
            )
    elif decision == "nao_aprovar":
        st.error(
            "Recomendação: não aprovar a operação nas condições atuais. Os motivos e as medidas "
            "necessárias para uma eventual nova análise estão detalhados abaixo."
        )
    else:
        st.warning(
            "Dados inconsistentes ou incompletos: não há informação confiável suficiente para "
            "decidir. Corrija as pendências abaixo e recalcule o FinScore."
        )

    with st.expander(
        "Motivos da recomendação e providências",
        expanded=decision != "aprovar" or bool(guarantee.get("recomendada")),
    ):
        blocking_details = policy.get("bloqueios_detalhados") or []
        if blocking_details:
            st.markdown("### Inconsistências identificadas e como regularizar")
            for index, item in enumerate(blocking_details, 1):
                st.markdown(
                    f"**{index}. {item['titulo']}**  \n"
                    f"**Motivo:** {item['motivo']}  \n"
                    f"**Impacto na análise:** {item['impacto']}  \n"
                    f"**Providência necessária:** {item['providencia']}"
                )
            st.info(
                "Após reunir os documentos e confirmar ou corrigir os valores, atualize os "
                "lançamentos e recalcule o FinScore. A recomendação será reavaliada com os dados revisados."
            )

        detailed_actions = {item.get("providencia") for item in blocking_details}
        other_blockers = [
            item for item in policy.get("bloqueios") or []
            if item not in detailed_actions
        ]
        if decision == "dados_inconsistentes" and other_blockers:
            st.markdown("### Outras pendências que impedem uma recomendação conclusiva")
            st.markdown("\n".join(f"- {item}" for item in other_blockers))

        if decision == "aprovar":
            st.markdown("### Recomendação de garantia")
            st.markdown(str(guarantee.get("justificativa") or "Não aplicável."))

        supplementary = policy.get("evidencias_complementares") or {}
        if supplementary.get("leituras"):
            st.markdown("### Evidências suplementares")
            st.markdown("\n".join(f"- {item}" for item in supplementary["leituras"]))
        if policy.get("fundamentacao"):
            st.markdown("### Elementos considerados na recomendação")
            st.markdown("\n".join(f"- {item}" for item in policy["fundamentacao"]))
        if policy.get("condicoes"):
            remaining_conditions = [
                item for item in policy["condicoes"]
                if item not in detailed_actions
                and item not in set(policy.get("bloqueios") or [])
            ]
            if remaining_conditions:
                title = (
                    "### Condições e monitoramento recomendados"
                    if decision == "aprovar"
                    else "### O que deve ser feito antes de uma nova análise"
                )
                st.markdown(title)
                st.markdown("\n".join(f"- {item}" for item in remaining_conditions))


def _generate_report(
    output: Dict[str, Any],
    meta: Dict[str, Any],
    policy: Dict[str, Any],
    governance_state: GovernanceSessionState,
) -> None:
    with st.status("Preparando parecer técnico...", expanded=True) as status_box:
        st.write("Consolidando os dados contábeis, financeiros e cadastrais.")
        st.write("Elaborando a análise econômico-financeira e a conclusão de crédito.")
        report, narrative, context = generate_parecer_document(
            output,
            meta,
            policy,
            governance=governance_state.governanca.model_dump(mode="json"),
            parecer_data=st.session_state.get("parecer_dados_estruturados"),
        )
        st.write("Verificando a consistência dos resultados e das recomendações.")

        contract = ParecerData.model_validate(
            st.session_state["parecer_dados_estruturados"]
        )
        functional_dossier = DOSSIER_STORE.save_report(
            contract.analise_id,
            contract,
            narrative,
            report,
            {
                "narrativa": context["validacao_narrativa"],
                "documento": context["avaliacao_documento"],
            },
            actor_email=st.session_state.get("finscore_user_email"),
        )
        usage = get_last_usage()
        DOSSIER_STORE.record_technical_telemetry(
            contract.analise_id,
            "parecer_concluido",
            {
                "model": MODEL_NAME,
                "temperature": MODEL_TEMPERATURE,
                "reasoning_effort": MODEL_REASONING_EFFORT,
                "usage_api": usage,
                "timestamp": now_ts(),
            },
        )

        st.session_state["parecer_gerado"] = report
        st.session_state["parecer_narrativa_estruturada"] = narrative.model_dump()
        st.session_state["parecer_dossie_funcional"] = functional_dossier
        st.session_state.pop("parecer_contexto_auditavel", None)
        st.session_state.pop("parecer_pdf", None)
        st.session_state.setdefault("token_usage", []).append(
            {
                "step": "parecer_responses_api",
                "model": MODEL_NAME,
                "temperature": MODEL_TEMPERATURE,
                "reasoning_effort": MODEL_REASONING_EFFORT,
                "usage_api": usage,
                "timestamp": now_ts(),
            }
        )
        status_box.update(label="Parecer técnico concluído.", state="complete")

    NavigationFlow.request_lock_parecer()
    st.session_state["_pending_nav_target"] = "parecer"
    st.rerun()


def _record_generation_failure(meta: Dict[str, Any], error: Exception) -> None:
    """Registra a tentativa sem expor detalhes técnicos na interface funcional."""

    analysis_id = str(meta.get("analise_id") or "")
    if not analysis_id:
        return
    try:
        DOSSIER_STORE.record_technical_telemetry(
            analysis_id,
            "parecer_nao_concluido",
            {
                "error_type": type(error).__name__,
                "model": MODEL_NAME,
                "timestamp": now_ts(),
            },
        )
    except Exception:
        logger.exception("Falha ao registrar a ocorrência técnica do parecer")


def _pdf_metadata(
    output: Dict[str, Any],
    meta: Dict[str, Any],
    policy: Dict[str, Any],
) -> Dict[str, Any]:
    observed = output.get("finscore_observado") or {}
    serasa = _serasa_record(output)
    return {
        "empresa": meta.get("empresa", "Empresa"),
        "cnpj": meta.get("cnpj", "N/A"),
        "data_analise": datetime.now().strftime("%d/%m/%Y"),
        "finscore_ajustado": observed.get("finscore_prudencial"),
        "classificacao_finscore": policy["segmento_politica"],
        "serasa_score": serasa.get("serasa_score"),
        "classificacao_serasa": serasa.get("status") or "Evidência separada",
        "decisao": policy["decisao"],
        "serasa_data": meta.get("serasa_data"),
        "ano_inicial": meta.get("ano_inicial"),
        "ano_final": meta.get("ano_final"),
        "cidade_relatorio": meta.get("cidade_relatorio", "São Paulo (SP)"),
    }


def _render_export(
    output: Dict[str, Any],
    meta: Dict[str, Any],
    policy: Dict[str, Any],
) -> None:
    center = st.columns([1, 1, 1])[1]
    with center:
        if st.button("Preparar PDF", use_container_width=True):
            try:
                with st.spinner("Gerando e conferindo a paginação..."):
                    pdf = gerar_pdf_parecer(
                        conteudo=st.session_state["parecer_gerado"],
                        meta=_pdf_metadata(output, meta, policy),
                        is_markdown=True,
                        min_pages=7,
                        max_pages=14,
                    )
                    pages = contar_paginas_pdf(pdf)
                    analysis_id = str(meta.get("analise_id") or "")
                    if analysis_id:
                        DOSSIER_STORE.record_pdf_export(analysis_id, pdf, pages)
                    st.session_state["parecer_pdf"] = pdf
                    st.session_state["parecer_pdf_pages"] = pages
            except Exception:
                st.session_state.pop("parecer_pdf", None)
                logger.exception("Falha técnica ao preparar o PDF do parecer")
                st.error("Não foi possível preparar o PDF. Encaminhe o evento ao suporte técnico.")

        if st.session_state.get("parecer_pdf"):
            company = _safe_filename(str(meta.get("empresa") or "Empresa"))
            cnpj = _safe_filename(str(meta.get("cnpj") or "CNPJ"))
            pages = st.session_state.get("parecer_pdf_pages")
            st.download_button(
                f"Baixar PDF ({pages} páginas)",
                data=st.session_state["parecer_pdf"],
                file_name=f"Parecer_{company}_{cnpj}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        analysis_id = str(meta.get("analise_id") or "")
        if analysis_id:
            try:
                dossier_json = DOSSIER_STORE.export_functional_json(analysis_id)
            except Exception:
                logger.exception("Falha ao preparar o dossiê funcional")
            else:
                st.download_button(
                    "Baixar dossiê da análise (JSON)",
                    data=dossier_json,
                    file_name=f"Dossie_{_safe_filename(analysis_id)}.json",
                    mime="application/json",
                    use_container_width=True,
                )


def render() -> None:
    session = st.session_state
    _cancel_analysis_polling()
    st.markdown("<h3 style='text-align:center'>📜 Parecer Técnico</h3>", unsafe_allow_html=True)

    if session.get("_parecer_policy_signature") != PARECER_POLICY_SIGNATURE:
        for key in (
            "parecer_gerado",
            "parecer_narrativa_estruturada",
            "parecer_contexto_auditavel",
            "parecer_pdf",
            "parecer_pdf_pages",
        ):
            session.pop(key, None)
        session["_parecer_policy_signature"] = PARECER_POLICY_SIGNATURE

    if not session.get("out"):
        st.info("Calcule o FinScore em **Lançamentos** para liberar o parecer.")
        return

    output = session.out
    meta = session.get("meta", {})
    policy = decide_pudim(output, meta)
    session["policy_inputs"] = policy
    _render_policy_summary(output, meta, policy)
    try:
        governance_state = _load_governance(output, meta, policy)
    except Exception:
        logger.exception("Falha ao validar o estado de governança do parecer")
        st.error(
            "Os registros de governança deste ciclo estão inconsistentes. Inicie um novo ciclo "
            "ou encaminhe o evento ao suporte técnico antes de registrar uma decisão."
        )
        return
    _render_governance(governance_state, output, meta, policy)

    st.divider()
    with st.columns([1, 1, 1])[1]:
        if st.button("Gerar parecer", type="primary", use_container_width=True):
            try:
                _generate_report(output, meta, policy, governance_state)
            except ReportGenerationServiceError as exc:
                _record_generation_failure(meta, exc)
                logger.exception("Falha no serviço de geração do parecer")
                st.error(exc.user_message)
            except Exception as exc:
                _record_generation_failure(meta, exc)
                logger.exception("Falha técnica ao gerar o parecer")
                st.error(
                    "Não foi possível gerar o parecer neste momento. Verifique a conexão e tente "
                    "novamente. Se a falha persistir, encaminhe o horário da tentativa ao suporte."
                )

    if session.get("parecer_gerado"):
        st.divider()
        st.markdown(session["parecer_gerado"], unsafe_allow_html=True)
        st.divider()
        _render_export(output, meta, policy)

        with st.columns([1, 1, 1])[1]:
            if st.button("Iniciar novo ciclo", use_container_width=True):
                clear_flow_state()
                nav.restart()
                st.rerun()
