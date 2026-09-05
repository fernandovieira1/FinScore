from __future__ import annotations

from pathlib import Path

import streamlit as st


TAB_LABELS = ["🧭 Metodologia", "📚 Glossário", "❓ FAQ"]
METHODOLOGY_PATH = (
    Path(__file__).resolve().parents[1] / "content" / "metodologia_pudim_2_0_20.md"
)


GLOSSARY = {
    "Aprovar": (
        "Recomendação favorável quando o resultado está apto para decisão e o FinScore prudencial "
        "é igual ou superior a 250 pontos. Pode incluir recomendação de garantia e permanece sujeita "
        "à alçada e aos controles cadastrais, jurídicos e de concentração da instituição."
    ),
    "Cap prudencial": (
        "Teto aplicado ao FinScore quando capitalização, endividamento exigível ou cobertura de "
        "juros alcançam condições de fragilidade definidas na metodologia."
    ),
    "Confiabilidade": (
        "Índice separado do FinScore que resume completude, reconciliação, evidência, controle de "
        "correções, plausibilidade e consistência temporal. O limiar de aptidão decisória é 75%."
    ),
    "Covenant": (
        "Obrigação contratual ou gatilho de acompanhamento associado a um risco identificado, como "
        "entrega de demonstrações, manutenção de índices ou revisão antecipada da exposição."
    ),
    "Dados inconsistentes": (
        "Resultado aplicado quando não há informação confiável suficiente para decidir. Exige correção "
        "ou comprovação das pendências e novo cálculo; não representa recusa do risco de crédito."
    ),
    "EO": (
        "Núcleo Econômico-Operacional, formado por crescimento, margens, giro do ativo e ciclo de caixa."
    ),
    "FP": (
        "Núcleo Financeiro-Patrimonial, formado por capitalização, liquidez, capital de giro, dívida, "
        "cobertura de juros e composição do endividamento."
    ),
    "Faixa FinScore": (
        "Leitura dos cortes usados na sensibilidade e na decisão: abaixo de 125; de 125 a 249,99; "
        "de 250 a 499,99; e 500 ou mais. O piso decisório é 250 pontos; a faixa de 250 a 499,99 "
        "aciona avaliação de garantia."
    ),
    "FinScore prudencial": (
        "Menor resultado pós-gargalo entre as abordagens estrutural e adaptativa, após a aplicação "
        "dos caps prudenciais. Varia de 0 a 1.000 pontos."
    ),
    "Fleuriet simplificado": (
        "Diagnóstico de capital de giro baseado em Ativo Circulante Operacional, Passivo Circulante "
        "Operacional, Necessidade de Capital de Giro, Capital de Giro e Saldo de Tesouraria."
    ),
    "Gargalo": (
        "Ajuste que atribui influência explícita ao núcleo mais fraco e limita a compensação de uma "
        "fragilidade financeira por desempenho forte no outro núcleo."
    ),
    "Garantia recomendada": (
        "Mitigador indicado em uma aprovação quando a faixa do FinScore, caps, cenário severo ou "
        "evidências suplementares registram sinais de atenção. O FinScore não presume modalidade, "
        "valor nem percentual de cobertura."
    ),
    "Não aprovar": (
        "Recomendação desfavorável quando há base apta para decisão e o FinScore prudencial é inferior "
        "a 250 pontos. Uma nova análise requer mudança material nos dados e indicadores."
    ),
    "PCA adaptativa": (
        "Diagnóstico de redundância entre indicadores que pode influenciar no máximo 15% dos pesos "
        "quando apresenta estabilidade suficiente."
    ),
    "Resiliência": (
        "Componente temporal que representa estabilidade e capacidade de suportar deterioração nos "
        "exercícios observados."
    ),
    "Restrição grave no Serasa": (
        "Ocorrência externa registrada pelo analista a partir da consulta documental. Permanece "
        "destacada para exame da alçada e pode fundamentar mitigação, sem alterar o FinScore ou, "
        "isoladamente, a categoria de decisão."
    ),
    "Serasa Score": (
        "Evidência externa comparada ao FinScore para identificar direção e intensidade da divergência. "
        "Não é somada, ponderada nem convertida para compor a pontuação."
    ),
    "Springate": (
        "Índice complementar de insolvência calculado por exercício. Resultado inferior a 0,862 indica "
        "sinal de distress no teste, sem alterar a pontuação do FinScore."
    ),
}


FAQ = [
    (
        "Quais são os resultados possíveis da decisão?",
        "Aprovar, Não aprovar e Dados inconsistentes. Aprovar pode incluir ou não recomendação de "
        "garantia. Garantias, covenants e providências não constituem categorias adicionais.",
    ),
    (
        "Qual é a diferença entre Não aprovar e Dados inconsistentes?",
        "Não aprovar pressupõe uma base apta e FinScore inferior a 250 pontos. Dados inconsistentes "
        "indica que os controles ainda não permitem uma conclusão confiável; as pendências devem ser "
        "sanadas e o cálculo refeito.",
    ),
    (
        "Quando a decisão é Aprovar?",
        "Quando o cálculo e o resultado estão aptos para decisão, a confiabilidade alcança pelo menos "
        "75%, não há alerta bloqueador e o FinScore prudencial é igual ou superior a 250 pontos.",
    ),
    (
        "Quando a decisão é Não aprovar?",
        "Quando o resultado está apto para decisão e o FinScore prudencial é inferior a 250 pontos. "
        "O parecer apresenta os componentes de fragilidade e os dados que precisariam mudar para uma "
        "nova análise.",
    ),
    (
        "Quando os dados são considerados inconsistentes?",
        "Quando o FinScore está indisponível, os controles de cálculo falham, o resultado não é "
        "utilizável, a confiabilidade é inferior a 75% ou existem correções e alertas bloqueadores.",
    ),
    (
        "Quando é recomendada garantia?",
        "Quando uma aprovação se situa entre 250 e 499,99 pontos, há cap prudencial, o cenário severo "
        "fica abaixo de 250 ou Serasa, Springate ou Fleuriet registram sinal de atenção. Modalidade, "
        "valor e cobertura dependem da avaliação do colateral e da alçada.",
    ),
    (
        "Serasa, Springate ou Fleuriet mudam a decisão?",
        "Não de forma isolada. São evidências suplementares, sem soma ou média com o FinScore. Elas "
        "qualificam a análise, a recomendação de garantia, os covenants e o exame da alçada.",
    ),
    (
        "O FinScore é uma probabilidade de inadimplência?",
        "Não. Ele sintetiza capacidade econômico-financeira relativa em escala de 0 a 1.000 pontos. "
        "A metodologia não converte a pontuação em probabilidade de inadimplência.",
    ),
    (
        "O que significam os pesos 60%, 25% e 15%?",
        "São pesos do nível atual, da dinâmica temporal e da resiliência. Não são pesos diretos "
        "atribuídos a cada um dos três exercícios.",
    ),
    (
        "A PCA define a pontuação?",
        "Não. Quando estável, sua contribuição é limitada a 15%; pelo menos 85% permanece ancorado "
        "nos pesos estruturais. Se instável, a metodologia preserva os pesos fixos.",
    ),
    (
        "Como são definidos os covenants?",
        "A recomendação aponta os indicadores associados ao risco observado. Limite, periodicidade, "
        "fonte de comprovação, prazo de cura e consequência do descumprimento devem ser definidos pela "
        "instituição; o parecer não cria parâmetros ausentes.",
    ),
    (
        "Um score calculado sempre pode ser usado para decidir?",
        "Não. Aptidão para cálculo e aptidão para decisão são controles distintos. Um FinScore "
        "provisório pode existir enquanto inconsistências documentais impedem seu uso decisório.",
    ),
    (
        "A recomendação substitui a alçada de crédito?",
        "Não. O parecer apoia o julgamento, mas não substitui política formal, alçada, validação "
        "jurídica, análise de concentração, exposição consolidada ou controles regulatórios.",
    ),
    (
        "O que acompanha o parecer?",
        "O documento reúne fontes, controles de qualidade, indicadores, formação do FinScore, cenários, "
        "evidências suplementares, decisão, mitigadores e a metodologia em anexo.",
    ),
]


def render_methodology_section() -> None:
    if not METHODOLOGY_PATH.exists():
        st.error("O conteúdo metodológico não está disponível.")
        return
    content = METHODOLOGY_PATH.read_text(encoding="utf-8")
    st.markdown(content)


def render_glossary_section() -> None:
    st.markdown("<h3 style='text-align:left'>Glossário</h3>", unsafe_allow_html=True)
    st.caption("Termos empregados no cálculo, na decisão e no parecer de crédito.")
    for term, definition in GLOSSARY.items():
        st.markdown(f"**{term}**  \n{definition}")


def render_faq_section() -> None:
    st.markdown("<h3 style='text-align:left'>Questões frequentes</h3>", unsafe_allow_html=True)
    for index, (question, answer) in enumerate(FAQ, 1):
        with st.expander(f"{index}. {question}"):
            st.markdown(answer)


def render() -> None:
    st.markdown("## Sobre o FinScore")
    st.markdown(
        "O FinScore organiza informações contábeis e econômico-financeiras em uma leitura integrada "
        "da capacidade de crédito. A documentação apresenta os conceitos de forma direta e detalha "
        "os parâmetros necessários à análise quantitativa e à revisão independente."
    )
    st.markdown(
        "A pontuação é um componente da análise, não uma decisão isolada. Qualidade dos dados, "
        "evidências suplementares, garantias, covenants e alçada permanecem explicitamente separados."
    )

    tabs = st.tabs(TAB_LABELS)
    with tabs[0]:
        render_methodology_section()
    with tabs[1]:
        render_glossary_section()
    with tabs[2]:
        render_faq_section()
