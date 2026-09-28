# Auditoria dos pareceres FinScore — 26/09/2026

## Base preservada

Branch de trabalho: `3_auditoria_pareceres`, criada na raiz do repositório. A base é o commit local `c23c6f251afafda23f91e8585947981fd7f6f381`, acrescido do ajuste de exportação PDF que estava sem commit na cópia `.codex-review` e que produziu os 16 pareceres anteriores. Esse ajuste foi preservado no commit `46c59817b`. Não se utilizou a branch remota 2 como base.

O SHA-256 do exportador preservado é `3DD5D39975DB5C3BC504ACA1F6B6D9ADBA5D48EDEE06CD815B99A544BB42A7C6`. A cópia anterior e os documentos do Desktop foram preservados.

## Auditoria antes da implementação

A faixa superior era escolhida somente pelo score final, embora a política de garantias já considerasse caps. Não existia classificação setorial estruturada para Springate. O Fleuriet não distinguia tesouraria estrita. As frequências de Monte Carlo já eram calculadas, porém omitidas do parecer. As notas da planilha eram ignoradas. A validação cadastral verificava formato, mas não impedia data futura do Serasa. A conclusão ainda usava qualidade como mérito econômico e repetia evidências suplementares. O anexo metodológico era obrigatório na exportação.

Os problemas concentram-se em regra decisória, validação, diagnósticos auxiliares e apresentação. Não foi necessário recalibrar a metodologia quantitativa principal.

## 1. Arquivos alterados

Caminhos relativos à raiz; os módulos abaixo estão em `V. 2 (Pudim)/APP/`.

| Arquivo | Alteração |
|---|---|
| `app_front/pdf/export_pdf.py` | Preservação do ajuste de layout usado nos 16 PDFs anteriores, em commit separado da auditoria. |
| `app_front/finscore_v2/assessment.py` | Aplicabilidade setorial, tipos de empresa, datas Serasa, perímetro da dívida e extensão desativada. |
| `app_front/finscore_v2/core.py` | Centralização das variações, Springate condicionado e diagnósticos adicionais de Fleuriet. |
| `app_front/finscore_v2/engine.py` | Validação temporal e passagem do contexto setorial. |
| `app_front/services/finscore_service.py` | Propagação de setor, notas da planilha e perímetro da dívida. |
| `app_front/services/io_validation.py` | Data futura rejeitada e parser da aba opcional de notas. |
| `app_front/services/analysis_dossier.py` | Registro de PDFs curtos ou completos, com identificação do formato exportado. |
| `app_front/views/lancamentos.py` | Cadastro explícito do tipo de empresa. |
| `app_front/services/credit_policy.py` | Enquadramento com cap e configuração de rótulos, garantias e texto institucional. |
| `app_front/components/parecer_data_schema.py` | Campos opcionais de fontes, contexto, tesouraria e política; compatibilidade com contratos históricos. |
| `app_front/services/parecer_data_builder.py` | Conversão dos novos campos para o contrato rastreável. |
| `app_front/services/evidence_book.py` | Mensagem externa de saturação sem instruções de desenvolvimento. |
| `app_front/services/parecer_generator.py` | Regras de redação, bloqueio de data Serasa futura e nova tentativa limitada para resposta estruturada inválida. |
| `app_front/services/parecer_validation.py` | Rejeição de mensagens internas e qualidade apresentada como mérito de aprovação. |
| `app_front/services/parecer_document.py` | Frequências, fontes, dívida, Fleuriet, Springate, conclusão e três níveis de documento. |
| `app_front/views/parecer.py` | Escolha de conteúdo do PDF, com invalidação do cache ao mudar o formato. |
| `app_front/content/metodologia_pudim_2_0_20.md` | Regras complementares e documentação explícita do universo de variações. |
| `tests/test_parecer_audit_v3.py` | 34 testes novos dos comportamentos corrigidos. |
| `tests/test_parecer_evaluation_v2.py` | Evidência completa na seção 7, sem repetição na conclusão; dois testes das novas tentativas de redação estruturada. |
| `tests/test_parecer_pudim_v2.py` | Verificação da ressalva institucional na redação corrigida para dados inconsistentes. |
| `tests/test_analysis_dossier_v2.py` | Dois testes de gravação de PDFs curtos, completos e vazios. |
| `AUDITORIA_PARECERES_2026_09_26.md` (raiz) | Este relatório. |

## 2. Problemas corrigidos

| Bloco | Status | Implementação | Camada | Risco de regressão |
|---|---|---|---|---|
| 1 — Cap de 500 | Corrigido | Cap acionado de até 500 impede a faixa superior; score permanece intacto. Recusa e bloqueios continuam prevalecendo. | Decisão | Baixo |
| 2 — Springate | Corrigido | Função central usa tipo/CNAE estruturados. Setor incompatível ou não confirmado recebe NÃO APLICÁVEL. | Diagnóstico/validação | Médio: cadastro antigo sem setor exige confirmação |
| 3 — Dívida | Corrigido | Perímetro explícito no parecer; contas adicionais previstas em configuração desativada. | Apresentação/arquitetura | Baixo |
| 4 — Fleuriet | Corrigido | Mantém NCG, CDG e T; adiciona T estrito, resíduo e alerta de 1% do ativo total. | Diagnóstico | Baixo |
| 5 — Qualidade | Corrigido | Gate informacional separado do mérito; resultado bloqueado não recebe conclusão econômica de aprovação. | Decisão/redação | Baixo |
| 6 — Variações | Corrigido | Função central, seis contas documentadas, tratamento de zeros/sinais/bases frágeis e contagem legada preservada. | Diagnóstico/documentação | Baixo |
| 7 — Saturação | Corrigido | Parecer comunica limitação de diferenciação; instrução de revisão de âncoras fica fora do documento. | Apresentação/validação | Baixo |
| 8 — Monte Carlo | Corrigido | Frequências prudenciais <500, <250 e <125 apresentadas somente se a simulação é válida para interpretação. | Apresentação | Baixo |
| 9 — Fontes | Corrigido | Parser aceita uma coluna ou linhas de chave/valor; seleção compacta no PDF e linhas integrais no contrato/dossiê. | Importação/rastreabilidade | Baixo |
| 10 — Redundância | Corrigido | Evidências completas na seção 7; conclusão usa referência e síntese. Frase única não é duplicada ao dividir parágrafos. | Apresentação | Baixo |
| 11 — Anexos | Corrigido | Parecer principal (padrão), parecer com anexo técnico ou anexo separado; metadados preservados. | Exportação | Baixo |
| 12 — Serasa | Corrigido | Cadastro, cálculo e nova geração rejeitam data posterior à análise. | Validação | Baixo |
| 13 — Contratante | Corrigido | Recomendação identificada como padrão; rótulos, texto e orientação de garantias configuráveis no serviço. | Decisão/apresentação | Baixo |
| 14 — Regressão | Corrigido | Suíte existente e novos testes, comparação exata dos 16 casos e três fluxos reais no navegador. | Verificação | Baixo |

## 3. Alterações metodológicas e decisórias

**Nenhuma regra quantitativa principal foi alterada.** Pesos, âncoras, PCA, composição 85/15, gargalo, núcleos, score bruto, score prudencial e Monte Carlo permanecem com a metodologia anterior.

Mudanças intencionais:

1. A faixa decisória considera a existência de cap acionado ≤500. Não se subtrai 0,01 do score.
2. Springate deixa de emitir diagnóstico quando a aplicabilidade não está confirmada. Sua fórmula continua igual nos setores aplicáveis. Isso também remove um sinal suplementar de garantia que anteriormente poderia ser inadequado.
3. T estrito e resíduo são diagnósticos novos. O limiar reutiliza `LIMIAR_MATERIALIDADE = 0,01` sobre ativo total, já existente. Não se adotou um limiar novo de 10% do ativo circulante. Não há penalização adicional.
4. Data Serasa futura passa a bloquear novos cálculos/pareceres. Documentos históricos continuam rastreáveis.

Variações: universo de ativo total, PL, contas a receber, caixa, empréstimos CP e despesas financeiras; nenhum índice integra essa regra de penalização. A regra congelada é `abs(atual/anterior − 1) >= 0,5`, com valores finitos e `abs(anterior) > 1e-12`. Mudança de sinal/base frágil recebe diagnóstico sem percentual enganoso. Zero → valor não nulo não recebe nova penalização. A medida absoluta sobre ativo total é informativa. A documentação técnica detalha cada caso.

## 4. Testes

### Automatizados

- Base anterior: 157 testes existentes aprovados.
- Versão corrigida: 157 existentes + 38 novos = **195 testes aprovados; zero falhas, zero erros e zero testes ignorados** na execução final.
- Duas expectativas textuais antigas foram atualizadas para os comportamentos solicitados: remover repetição da evidência Serasa e manter a ressalva institucional sem apresentar dados bloqueados como mérito de aprovação.
- Regressão de 16 empresas: igualdade exata de todos os campos anteriores, exceto os horários de processamento/auditoria e o Springate cuja aplicabilidade foi alterada intencionalmente. As nove colunas originais de Fleuriet também permaneceram iguais. Novas colunas são adicionais.
- Monte Carlo: comparação reproduzível com 100 trajetórias nos casos Mobicloud, SSA-MRO e JNS, mesma semente `20260723`; saídas anteriores e atuais iguais. A suíte também compara resultados com o script quantitativo congelado.
- O exportador PDF original continua com o mesmo hash utilizado nos 16 PDFs anteriores.
- Os smoke tests identificaram duas falhas de integração corrigidas durante esta rodada: o dossiê ainda recusava PDFs com menos de sete páginas; e a resposta de redação com referências duplicadas interrompia o fluxo sem nova tentativa. O registro agora aceita os três formatos e rejeita documentos vazios. Erros estruturais da redação entram nas mesmas três tentativas limitadas, sem afrouxar a validação. Quatro testes novos cobrem esses casos.

### Três smoke tests no navegador

Execução real: `streamlit run app.py`, na pasta `V. 2 (Pudim)/APP/app_front`, com a branch 3. Cadastro, upload de XLSX, cálculo, revisão, geração e download feitos nos controles do app. Serasa 500 e consulta de 22/09/2026 são valores sintéticos de teste, não consultas reais. Exercícios: 2023–2025.

| Caso | Arquivo original | Foco | Resultado |
|---|---|---|---|
| T013 — Mobicloud | `5umarket - Mobicloud Tecnologia.xlsx` | Perfil sem bloqueadores; tipo serviços não financeiros | Passou: score 868,78; qualidade 93%; zero bloqueadores; PDF final de 5 páginas baixado. |
| T014 — SSA-MRO | `6strumarket - SSA-Miro Solucoes.xlsx` | Cap prudencial 500 e enquadramento com mitigadores | Passou: score pré-cap 516,06 → 500,00; qualidade 92,52%; zero bloqueadores; faixa APROVAÇÃO SUJEITA A MITIGADORES; PDF final de 5 páginas baixado. |
| T003 — JNS Seguradora | `12Grupo JNP - JNS Seguradora.xlsx` | Springate não aplicável e preservação dos bloqueios informacionais | Passou: score 372,22; qualidade 88,85%; dois bloqueadores; Springate NÃO APLICÁVEL; parecer Dados inconsistentes; PDF de 6 páginas baixado. |

Sucesso técnico do fluxo e emissão de PDF não equivalem à aprovação de crédito. O teste da seguradora deve preservar a recomendação de dados inconsistentes quando houver bloqueadores.

Todos os três cálculos da interface executaram 1.000 trajetórias por abordagem. IDs dos dossiês locais: Mobicloud `FS-2026-000008`, SSA-MRO `FS-2026-000009`, JNS `FS-2026-000010`.

Também foi verificada na interface a exportação separada do anexo técnico de Mobicloud: 8 páginas, com invalidação correta do PDF anterior ao trocar o formato. Os três pareceres principais passaram por extração de texto, renderização das 16 páginas e revisão visual: sem cortes de conteúdo ou sobreposições observados. Foram conferidos score, faixa, fontes, tesouraria estrita, frequências de simulação, exceção do cap e manutenção dos bloqueios da seguradora.

### Arquivos finais no Desktop

Pasta: `C:/Users/ferna/Desktop/FinScore_branch_3_testes_2026_09_26/`.

| Arquivo | Páginas | SHA-256 |
|---|---:|---|
| `1_Mobicloud.pdf` | 5 | `a129216f78d1a0364330549f4cc43e3d3b657cff02d36bf3ef8a96624c031829` |
| `2_SSA_MRO.pdf` | 5 | `23fe85648dea8abaf5b11b907f74a36456fdac3c3657dc67fabf5fad120d781c` |
| `3_JNS_Seguradora.pdf` | 6 | `2f14751e5213c5a18f5aacf196a0224469fd74c1b3e42a1dab4f14a41bb83ec2` |

Os PDFs foram baixados pelos botões do Streamlit e copiados sem alteração para o Desktop. A pasta também contém este relatório e o manifesto de verificação.

Encerramento: abas e dois servidores temporários fechados. O banco usado nos testes foi preservado localmente em `finscore_auth_after.db`, na pasta de evidências. O banco original foi restaurado e seu SHA-256 confirmado: `B11002C3290127AD4C1BE60507E26E3E3EA296FD25215E8A0DDF3189402336D8`; o Git não registra alteração nele.

A revisão visual/textual também identificou e corrigiu uma frase fixa que descrevia a faixa superior sem a exceção do cap. Os documentos foram regenerados pelo app após a correção. Durante a atualização de módulos com sessões simultâneas, uma sessão apresentou `KeyError: views.analise`; o comando Rerun da interface recuperou a sessão, sem refazer ou alterar os cálculos. O erro não apareceu na execução estável do fluxo final.

## 5. Pendências e limites

- A classificação setorial depende do cadastro do analista; não há enriquecimento externo automático. CNAE pode ser recebido pelo serviço, enquanto a interface oferece o tipo de empresa.
- A configuração por contratante está preparada no serviço `PolicyConfig`; não foi criada uma tela administrativa nova.
- A extensão da dívida está deliberadamente desativada e não passa a somar arrendamentos/mútuos automaticamente.
- As notas de preenchimento são declarações da planilha, sem validação documental automática. O PDF limita a seleção a seis linhas relevantes e 700 caracteres por linha; o conteúdo integral permanece rastreável.
- Diagnósticos de simulação reprovados no controle de validade não têm suas frequências exibidas como evidência utilizável.
- Não se reexecutaram todos os 48 arquivos no navegador nesta rodada: o escopo solicitado foi três smoke tests após a implementação. Os 16 casos foram comparados no motor e a suíte automatizada cobre casos sintéticos de bloqueios/ausências/inconsistências.
- Os logs e artefatos locais de verificação estão em `.codex-review/review-output/audit-20260926/`; dependências, chave de API e bancos de teste não integram o commit.
