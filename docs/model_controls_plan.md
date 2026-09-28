# Plano incremental — controles propostos, ainda não implementados

Base: `ec1d3dad2`. Esta branch para ao final das fases 1–2. **POLICY_DECISION_REQUIRED** significa decisão institucional pendente, não uma flag já executada em produção.

## Protocolo BEFORE / AFTER desta entrega

| Campo | A01: documentação | A02: baseline versionado | A03: golden tests |
|---|---|---|---|
| BEFORE | Conhecimento distribuído entre código e textos | Casos/testes anteriores sem snapshots completos dos três casos na main integrada | 205 testes legados, incluindo um caso congelado e regressões específicas |
| PROBLEM | Alteração pode atingir matemática/gates sem rastrear dependências | Sem referência versionada ampla para comparar mudanças futuras | Scores isolados não protegem notas, pesos, bloqueios e contrato conjuntamente |
| CATEGORY | OBSERVABILITY | OBSERVABILITY | VALIDATION |
| AFTER | Mapa, riscos, semânticas e pontos de extensão documentados | Snapshots JSON obtidos sem mudar produção, com inputs/hash/configuração/ambiente | Comparação independente contra arquivos congelados, checks de sanidade e integridade |
| CHANGES_SCORE | false | false | false |
| CHANGES_DECISION | false | false | false |
| CHANGES_SCHEMA | false | false: formato da fixture é somente de teste | false |
| BREAKS_COMPATIBILITY | false | false | false |
| RATIONALE | Separar observação de proposta | Fixar comportamento real, inclusive limitações | Detectar regressão sem recalibrar modelo |
| TESTS | Revisão de localização e diff de produção vazio | Hash dos XLSX, integridade da fixture e captura da base | Legados + golden + integração importação/serviço/política/contrato |
| ROLLBACK | Remover docs adicionados | Remover diretório de fixtures e ferramenta de captura | Remover somente os testes/helpers novos; manter testes legados |

O registro acima foi criado antes dos helpers, snapshots e testes novos. Não se introduz `control_rules_version` em produção nesta fase: ainda não há rule set novo.

## Grupos sujeitos à próxima autorização

| Grupo/fases | BEFORE → proposta AFTER | Local exato de extensão | Categoria | Gate e testes previstos |
|---|---|---|---|---|
| Taxonomia (3) | Status parcial → nove estados + provenance e motivo | `core.build_traceability`, `parecer_data_schema.DataPoint/TraceabilityRecord`, `parecer_data_builder._wide_points/_traceability` | OBSERVABILITY | Compatibilidade/versionamento de schema antes de alteração; zero/ausente/quarentena/estimado/ajustado |
| Missingness (4) | Renormalização + intervalo só para dívida → diagnóstico conservador/neutro/favorável por indicador | `core.temporal_indicator_table/calculate_scores`, novo helper diagnóstico externo ao cálculo | VALIDATION | Sem alterar pesos; seis casos A–F; verificar quando muda núcleo/faixa e suggest review |
| Piso de núcleo (5) | Sem piso decisório por EO/FP → simulação configurável, default disabled | `credit_policy.PolicyConfig/decide_pudim`, camada de simulação separada | DECISION_POLICY | POLICY_DECISION_REQUIRED; cinco combinações especificadas; nunca mudar score |
| Estados (6,15) | Três recomendações + gates existentes → estado separado/score_usage | `parecer_data_schema.Governance/FinScoreRecommendation`, builder, view | OBSERVABILITY e, se mudar ação, DECISION_POLICY | Migração aditiva; JNS calculável/não decisória; precedência de bloqueios |
| Caps (7) | Regras/teto/pré-pós já disponíveis → metadados explícitos e revisão opcional | `core.evaluate_prudential_caps` como fonte somente; `parecer_data_builder._caps`, `credit_policy` | OBSERVABILITY + DECISION_POLICY | Flag default disabled; SSA pre-cap 516,06/final 500; cap acionado versus vinculante |
| Hard stops (8) | Flags distribuídas → catálogo versionado com categoria, motivo, saneamento e alçada | `core.validate_correct_and_prepare/detect_material_bias` como fontes; novo catálogo junto de `credit_policy` | VALIDATION + DECISION_POLICY | Regras propostas desabilitadas; inventariar as 12 regras; não duplicar bloqueios legados |
| Soft warnings (9) | Alertas podem afetar Q → coleção explicativa separada | `evidence_book.build_evidence_book`, builder, renderer | OBSERVABILITY/VALIDATION | Provar score, Q e decisão iguais ao acrescentar warning; alçada exige policy |
| Domain gate (10) | Só Springate tem aplicabilidade → domínio principal com fonte documental | `assessment.springate_applicability` apenas como distinção; futura estrutura em contrato/serviço | VALIDATION; bloqueio = DECISION_POLICY | UNKNOWN_DOMAIN sem prova; OUT_OF_DOMAIN só com documento; POLICY_DECISION_REQUIRED |
| Saturação (11) | Alerta agregado de duas ocorrências → raw/transformado/curva/nota/extremo | `core.score_indices`, `_robust_pca_matrix`, `evidence_book` | OBSERVABILITY | Limite/2x/10x; sem mudar curvas e sem inserir warning que penalize Q |
| Denominadores (12) | NaN/sentinels → raw_ratio/status/model_value/motivo separados | `core.safe_div/indices`, builder | OBSERVABILITY/VALIDATION | Sete casos de EBIT/despesa, zero, ausente, inconsistente; sentinels mantidos |
| Cenários (13) | Monotonicidade global → choque/base/resultante/direção por variável | `core.apply_deterministic_scenario/run_deterministic_scenarios`, helper diagnóstico | VALIDATION | Efeito contraintuitivo explicado; não reconstruir cenário automaticamente |
| Sensibilidade (14) | Resumos MC → decomposição descritiva de pequena mudança sob stress material | cenários, caps, temporalidade, contribuições e curvas existentes | VALIDATION | Sem limiares arbitrários: configurar critérios aprovados; stress estável não implica erro |
| Qualidade (16) | Rótulos alternam → “Qualidade informacional” e texto de alcance | `parecer_document._quality_table/_reliability_table`, views | OBSERVABILITY | Manter campos/API; comparar texto/score; revisão de PDF |
| Evidências (17) | Natureza já separada → independência e comparação heurística explícitas | `evidence_book._supplementary_findings`, contrato | OBSERVABILITY | Serasa externo; Springate/Fleuriet derivados; sem média/soma nova |
| Reprodução (18) | Hashes parciais → manifesto de artefato/ambiente/configuração/versões | `analysis_dossier.save_contract/save_report`, builder, export | OBSERVABILITY | Hashes mudam com dado/código/config; seed idêntica reproduz resultados; sem segredos no manifesto |
| Overrides (19) | Manifestações e alçada auditadas → exceção por regra, evidência, autoridade, validade | `credit_governance`, `AnalysisDossierStore._sync_governance` | DECISION_POLICY | POLICY_DECISION_REQUIRED; append-only; sem bypass silencioso; expiração/autoridade/hash |
| Adversariais (20) | Casos legados/golden → `tests/adversarial` com 30 cenários exigidos | testes independentes, fixtures sintéticas | VALIDATION | Matriz 1–30, negativos/ausências/limites/stress/seed/hash; não substituir legado |
| Regressão (21,22) | Baseline desta branch → before/after obrigatório a cada grupo | golden tests novos + suíte existente | VALIDATION | Mobicloud inalterada, SSA matemática igual, JNS bloqueada; diferenças classificadas |
| Parecer (23) | Estrutura atual → blocos visuais separados | `parecer_document`, `views/parecer`, `pdf/export_pdf` | OBSERVABILITY; gate novo = DECISION_POLICY | Três smoke tests de navegador e PDFs após autorização dessa etapa |
| Método/versões (24–26) | Textos e versões existentes → capítulos separados e changelog por grupo | metodologia, constantes de versões, docs | OBSERVABILITY | Sem incrementar methodology_version se matemática não mudou; schema/policy versionados quando mudarem |

Alterar fórmulas, pesos, imputação produtiva, curvas, caps numéricos, PCA, temporalidade, gargalo ou agregação é **QUANTITATIVE_METHOD**, fora desta execução e sujeito a autorização expressa específica. Nenhuma proposta acima exige fazê-lo para iniciar observabilidade/validação.

## Ordem sugerida e decisões pendentes

1. Autorizar taxonomia, metadados e diagnóstico em estrutura aditiva, com plano de compatibilidade.
2. Autorizar missingness, saturação, denominadores, domínio e cenários somente em modo diagnóstico.
3. Definir institucionalmente domínio validado, critérios de materialidade/sensibilidade, piso de núcleo, precedência de estados, política de caps/hard stops e poderes de override. Simular impacto retrospectivo; manter defaults disabled.
4. Autorizar apresentação/manifesto/governança, repetir integração, testes no navegador e revisão dos PDFs.

**Parada obrigatória nesta entrega:** não há implementação das fases 3–30. Os estados/flags/rotinas citados como propostas não devem ser anunciados como disponíveis no app.
