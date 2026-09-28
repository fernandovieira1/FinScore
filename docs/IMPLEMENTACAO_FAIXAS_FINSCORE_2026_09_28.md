# Faixas e aprovação qualificada do FinScore

Data: 28/09/2026. Escopo: classificação, política de aprovação e apresentação. Metodologia quantitativa mantida em **2.0.20**.

## A. Diagnóstico inicial

Os caminhos abaixo partem de `V. 2 (Pudim)/APP/app_front/`.

| Responsabilidade | Arquivo e função existentes |
|---|---|
| Faixas e limites | `services/credit_policy.py`: `PolicyConfig` e `_score_band` |
| Cores e gráfico no PDF | `pdf/export_pdf.py`: `_render_finscore_band_chart` |
| Recomendação, precedência e mitigadores | `services/credit_policy.py`: `decide_pudim` |
| Gatilhos e valores dos caps | `finscore_v2/core.py`: `evaluate_prudential_caps`; aplicação em `finscore_v2/engine.py`: `executar_finscore` |
| Bloqueios de qualidade e aptidão | `finscore_v2/engine.py`: `_atualizar_status_qualidade`; leitura pela política em `decide_pudim` |
| Índice de qualidade dos dados | `finscore_v2/core.py`: `calculate_reliability` |
| Contrato, texto e PDF do parecer | `services/parecer_data_builder.py`, `components/parecer_data_schema.py`, `services/parecer_document.py` e `pdf/export_pdf.py` |
| Anexo 1 e Metodologia do app | Ambos leem `content/metodologia_pudim_2_0_20.md`; renderização por `render_structured_parecer` e `views/sobre.py:render_methodology_section` |
| Regressões existentes | `tests/test_parecer_pudim_v2.py`, `test_parecer_audit_v3.py`, `test_parecer_context_review.py`, `test_model_controls_golden.py` e demais testes do motor, parecer, exportação e governança |

A política anterior tinha cortes em 250 e 500. Um cap de até 500 podia substituir o rótulo da faixa por uma ressalva. A mudança separa a classificação quantitativa dessa ressalva, preservando o score e as regras de garantia.

## B. Alterações realizadas

| Arquivo | Função/componente | Alteração e motivo |
|---|---|---|
| `services/credit_policy.py` | `PolicyConfig`, `_score_band`, `finscore_bands`, `decide_pudim` | Fonte comum de quatro faixas e cores; parâmetros de 750 pontos e IQD de 90%; qualificação condicionada aos controles. Mantidos os códigos `aprovar`, `nao_aprovar` e `dados_inconsistentes`. |
| `pdf/export_pdf.py` | `_render_finscore_band_chart`, `render_parecer_html` | Quatro regiões, marcador e cor exclusivamente quantitativos; rótulo efetivo da recomendação no cabeçalho. Zero permanece `0,00` na apresentação, sem ser confundido com ausência. |
| `views/parecer.py` | `_render_policy_summary`, `_pdf_metadata` | Classificação separada do status; repasse da recomendação efetiva ao PDF; mensagens de garantia preservadas. |
| `views/scores.py` | `_render_score_principal` | Exibição da classificação quantitativa junto ao resultado. |
| `components/parecer_data_schema.py` | `FinScoreRecommendation`, `ParecerData` | Aceita o rótulo qualificado dentro de `aprovar`; valida elegibilidade e rejeita contratos qualificados com cap ou estresse restritivo. Contratos anteriores continuam legíveis. |
| `services/parecer_data_builder.py` | `PARECER_POLICY_VERSION` | Identificador da política atualizado para `three-decisions-finscore-only-v4-qualified-approval`. Versão do motor preservada. |
| `services/evidence_book.py` | `_result_findings` | Registra faixa e rótulo como evidências para sustentar a narrativa. |
| `services/parecer_validation.py` | `_validate_semantics` | Reconhece aprovação qualificada e rejeita sua atribuição textual a resultado não elegível. |
| `services/parecer_document.py` | `_policy_reading` | Explica a separação entre faixa, cap e recomendação; apresenta os requisitos e os motivos de elegibilidade já produzidos pela política. |
| `content/metodologia_pudim_2_0_20.md` | Seções 10, 11, 15 e 17 | Atualiza as tabelas, inclui explicação intuitiva e exemplos, esclarece IQD de 75% versus 90% e a precedência dos controles. Conteúdo compartilhado pelo Anexo 1 e pela tela Metodologia. |
| `views/sobre.py` | Glossário e FAQ | Alinha as definições às quatro faixas e explica por que um score verde pode não receber aprovação qualificada. |
| `tests/test_credit_policy_bands_v4.py` | 14 testes novos | Limites, qualidade, caps, controles, estresse, evidências complementares, gráfico, contrato, narrativa e conteúdo compartilhado. |
| `tests/test_model_controls_golden.py` | Comparação integral e dois testes novos | Aplica somente o delta esperado da política na comparação, sem regravar os snapshots; verifica leitura histórica e rejeição de adulteração de cap/estresse. |
| `tests/test_parecer_audit_v3.py` | Testes de faixa e cap | Atualiza os rótulos esperados; mantém as verificações de mitigadores e precedência. |
| `tests/test_parecer_context_review.py` | Limites configurados | Espera a nova classificação e mantém os cortes institucionais configurados. |
| `tests/test_parecer_pudim_v2.py` | Documentação da decisão | Confere a qualificação de Aprovar e os requisitos de qualidade sem remover os códigos anteriores. |

### Comportamento entregue

| Score prudencial | Faixa / cor | Recomendação-base, com dados aptos |
|---|---|---|
| 0 até menos de 250 | Risco elevado / vermelho | Não aprovar |
| 250 até menos de 500 | Risco relevante / amarelo | Aprovar, com garantia/mitigadores recomendados |
| 500 até menos de 750 | Risco aceitável / azul | Aprovar |
| 750 até 1.000 | Risco reduzido / verde | Aprovação qualificada, se elegível; caso contrário, regras anteriores de aprovação ou bloqueio |

A qualificação exige score de pelo menos 750, IQD de pelo menos 90%, aptidão decisória, ausência de bloqueios e de qualquer cap acionado. Também reutiliza o sinal já existente de cenário severo inferior ao piso de 250 pontos. Não foi criado novo cenário nem limiar de estresse. Ausência desse resultado não é convertida em zero ou em novo bloqueio.

IQD ausente ou inferior a 75% continua bloqueando a decisão. IQD de 75% a menos de 90% apenas impede a qualificação máxima, sem invalidar o score por esse motivo. Serasa, Springate e Fleuriet continuam podendo motivar garantias e acompanhamento, sem mudar automaticamente a faixa ou vetar isoladamente a qualificação.

## C. Preservação metodológica

Permaneceram inalterados o cálculo do FinScore e do FinScore prudencial, indicadores e fórmulas, normalizações, âncoras, pesos, PCA, componente adaptativo, ponderação temporal, gargalos, cálculo e gatilhos dos caps, cálculo e componentes do IQD, bloqueios de qualidade, tratamento de ausências e inconsistências, cenários, simulações, testes de estresse, Serasa, Springate e Fleuriet.

Nenhum arquivo de `app_front/finscore_v2/` foi modificado. Não houve troca de biblioteca, alteração de dependência, migração de banco ou novo esquema de versionamento. O identificador metodológico continua em 2.0.20; apenas o identificador já existente da política foi atualizado.

As comparações de referência mantêm o output integral do motor, os cálculos intermediários, pesos, caps, qualidade e simulações. Os snapshots e seus hashes foram preservados.

| Caso de referência | FinScore antes e depois | Apresentação atual |
|---|---:|---|
| Mobicloud | 868,7848667885734 | Risco reduzido; aprovação qualificada, com ressalvas complementares mantidas |
| SSA-MRO | 500,00 | Risco aceitável; Aprovar, com cap e mitigadores preservados |
| JNS | 372,22, arredondado para exibição | Risco relevante; Dados inconsistentes preservado |

## D. Testes e verificação

- Antes: suíte existente completa, **214 testes aprovados**.
- Depois: suíte completa, **230 testes aprovados**, em 163,146 segundos; **nenhuma falha ou erro final**.
- Foram acrescentados 16 testes: 14 na nova suíte e dois de compatibilidade/controle nos testes de referência.
- Fronteiras verificadas: 0; 249,99; 250; 499,99; 500; 749,99; 750; 1.000.
- Qualidade: ausente, abaixo de 75%, exatamente 75%, entre 75% e 90%, exatamente 90% e acima de 90%.
- Caps: ausência, cap de 500, caps acima de 750 e manutenção da cor quantitativa com ressalvas.
- Estresse: 249,99, 250, resultado favorável e resultado ausente, sem modificar o modelo de cenários.
- Evidências complementares: preservação da faixa e da qualificação; recomendação de garantia mantida.
- Documentos: PDFs completos de teste em xhtml2pdf e Playwright, com inspeção visual do gráfico e das tabelas; respectivamente 13 e 11 páginas no caso utilizado.
- Verificação de `git diff --check` sem erros.

As cinco falhas da primeira regressão após a mudança correspondiam a expectativas da política/texto anterior. Foram atualizadas somente as expectativas autorizadas; a comparação do motor não foi relaxada. Em seguida, dois testes novos precisaram converter o marcador de datetime dos snapshots para o formato aceito pelo contrato. Essa correção ficou restrita à preparação dos testes.

Comando de execução a partir da raiz do repositório, usando o Python do ambiente da aplicação:

```powershell
$env:PYTHONPATH = (Resolve-Path 'V. 2 (Pudim)/APP').Path + ';' + (Resolve-Path 'V. 2 (Pudim)').Path
& 'V. 2 (Pudim)/APP/.venv/Scripts/python.exe' -m unittest discover -s 'V. 2 (Pudim)/APP/tests' -v
```

## E. Resumo do diff

São 11 arquivos de aplicação/conteúdo, cinco arquivos de teste (um novo) e este relatório. As mudanças se concentram nas quatro faixas, elegibilidade da aprovação qualificada, apresentação e explicação. Não houve alteração no motor quantitativo, nos fixtures históricos, nas dependências ou nos controles humanos de aprovação/override.

O gráfico usa a mesma definição central de faixas da política. O conteúdo metodológico continua único para app e Anexo 1. A terminologia consolidada `Aprovar` com garantia foi mantida para a faixa intermediária.

## F. Limites e riscos residuais

- Integrações devem continuar usando o código decisório estável. O rótulo textual de uma aprovação elegível passa a ser `Aprovação qualificada`.
- Configurações institucionais continuam suportadas. O novo limite de qualificação precisa ser maior que a referência de garantia, e sua exigência de qualidade não pode ser menor que a geral; configurações incompatíveis são rejeitadas explicitamente.
- Documentos históricos e snapshots não são reescritos. Um novo PDF é necessário para exibir a política atual.
- A ausência de cenário severo não cria impedimento novo. Qualquer exigência futura de disponibilidade do estresse deve ser especificada e validada separadamente.
- A paginação varia entre os dois geradores existentes. A inclusão da explicação amplia o anexo, mantendo os testes de paginação do caso de referência.
- Os logs mantêm avisos preexistentes de NumPy e de fechamento de arquivos de teste. Não foram feitos ajustes fora do escopo para eliminá-los.
