# Auditoria dos controles do FinScore — fases 1 e 2

Data: 28/09/2026. Base auditada: `ec1d3dad222186649dc7dafd5d3bb855f24d4e4c` (`main`, integração das branches 2 e 3). Branch de trabalho: `4_auditoria_baseline_controles`.

Esta entrega executa **somente as fases 1 e 2** da instrução recebida. A inspeção abaixo precedeu a criação dos testes. Não autoriza novas regras, recalibração, alteração de schemas ou alteração do parecer. Um golden test preserva o comportamento observado; **não certifica validade econômica nem corrige os riscos encontrados**.

## Mapa da arquitetura

Os caminhos da tabela são relativos a `V. 2 (Pudim)/APP/app_front/`. Linhas referem-se ao commit base. Risco: A = alto (resultado, contrato ou governança), M = médio (diagnóstico/apresentação), B = baixo (isolado em testes/documentação).

| Área | Arquivo:linha e função/classe | Responsabilidade | Dependências | Consumidores | Risco |
|---|---|---|---|---|---|
| Entrada | `views/lancamentos.py:352` `_sec_dados` | Upload XLSX, prévia, execução e sessão | io_validation, finscore_service, session_state | fluxo Streamlit | A |
| Cadastro | `services/io_validation.py:43` `validar_cliente` | Cadastro, período, Serasa e cronologia | assessment, pandas | lançamentos | A |
| Importação | `services/io_validation.py:181` `ler_planilha`; `validar_dataframe_importado:101` | Aba lancamentos, 21 contas, notas e relatório de importação | openpyxl, engine | serviço e UI | A |
| Adaptação da UI | `services/finscore_service.py:237` `run_finscore`; `ajustar_coluna_ano:26` | Períodos, contexto, parâmetros, aliases legados | engine, contracts, assessment | lançamentos e testes | A |
| Parser | `finscore_v2/engine.py:15` `preparar_dados_contabeis`; `core.py:148` `parse_accounting_value` | Três exercícios, conversão, ausências/erros | pandas, numpy | engine e importação | A |
| Correção e validação | `finscore_v2/core.py:224` `validate_correct_and_prepare` | Identidades, sinais, subtotais, correções e quarentena | constantes e dados reportados | engine | A |
| Proveniência | `finscore_v2/core.py:394` `build_traceability` | Reportado, usado, regra, status de correção | relatório de correções | contrato, dossiê | A |
| Derivação | `finscore_v2/core.py:549` `derive` | Contas derivadas, EBIT, capital de giro, dívida, médias | contas analíticas | índices e diagnósticos | A |
| Indicadores | `finscore_v2/core.py:582` `indices`; `safe_div:137` | Razões e tratamento de denominadores | contas derivadas | curvas, PCA, cenários | A |
| Curvas/notas | `finscore_v2/core.py:130` `ANCHORS`; `score_indices:612` | Interpolação e extremos 0–95 | índices | temporalidade | A |
| Saturação | `finscore_v2/core.py:437` `detect_material_bias` | Duas observações no extremo geram SATURACAO_CURVA | índices e notas | qualidade, evidências | A |
| Temporalidade | `finscore_v2/core.py:633` `temporal_indicator_table` | Nível 60%, dinâmica 25%, resiliência 15%, cobertura | notas anuais | calculate_scores | A |
| Pesos estruturais | `finscore_v2/core.py:127` `FIXED_WEIGHTS`; `_normalized_fixed_weights:629` | Pesos por EO/FP | NUCLEI | composição | A |
| PCA | `finscore_v2/core.py:853` `_robust_pca_matrix`; `pca_profile:889` | Orientação, imputação estatística, escala robusta, estabilidade e fallback | sklearn/numpy | abordagem adaptativa | A |
| Composição | `finscore_v2/core.py:675` `calculate_scores` | EO/FP estrutural e adaptativo; renormalização; prejuízo recorrente | notas temporais, perfis PCA | score observado e cenários | A |
| Geométrica/gargalo | `finscore_v2/core.py:661` `_geometric_nucleus_score`; `calculate_scores:675` | Geométrica EO/FP 50/50; 75% geométrica + 25% menor núcleo | núcleos | prudencial pré-cap | A |
| Prudencial e caps | `finscore_v2/core.py:728` `evaluate_prudential_caps`; `engine.py:153` `executar_finscore` | Mínimo entre abordagens; menor teto aplicável | último exercício | política, relatório | A |
| Ausências | `finscore_v2/core.py:621` `explain_missing_indices`; `missing_debt_classification_interval:759` | Motivos NaN e intervalo parcial para dívida desconhecida | base/perfis | contrato e exportação | M |
| Redundância | `finscore_v2/core.py:783` `analyze_fp_redundancy` | Comparação explicativa capitalização/endividamento | temporal, índices | diagnóstico | M |
| Qualidade | `finscore_v2/core.py:510` `calculate_reliability`; `engine.py:85` `_atualizar_status_qualidade` | Q separado do score; gates de cálculo/decisão | qualidade, correções, alertas | política e contrato | A |
| Alertas/bloqueios | `finscore_v2/core.py:437` `detect_material_bias`; `synchronize_quality_taxonomy:498` | Viés, DRE, extremos, ausências, flags | dados, correções | qualidade/política | A |
| Cenários | `finscore_v2/core.py:131` `SCENARIO_DEFINITIONS`; `apply_deterministic_scenario:1230`, `run_deterministic_scenarios:1267` | Choques, reconstrução, teste de monotonicidade | perfis congelados, funding/juros | tabelas, evidências | A |
| Reconstrução | `finscore_v2/core.py:1021` `_linked_financial_expense`; `reconcile_funding_balance:1035` | Juros/dívida, recursos CP/LP, residual não líquido | contas e premissas | cenários e Monte Carlo | A |
| Simulações | `finscore_v2/core.py:1171` `run_sensitivity`; `simulate_trajectory:1091` | Semente, rejeição, limites, trajetórias independentes/correlacionadas | RNG, perfis, accounting_flags | engine | A |
| Estatísticas | `finscore_v2/core.py:1292` `descriptive`; `sensitivity_ranking:1319` | Percentis, frequências, correlações de sensibilidade | trajetórias | contrato e gráficos | M |
| Springate | `finscore_v2/core.py:1470` `calcular_springate`; `assessment.py:22` `springate_applicability` | Diagnóstico derivado e aplicabilidade declarada | tipo/CNAE, contas | evidências | M |
| Fleuriet | `finscore_v2/core.py:1515` `calcular_fleuriet_simplificado` | NCG, CDG, T, tesouraria estrita e resíduo | contas | evidências | M |
| Serasa | `finscore_v2/core.py:823` `assess_external_credit` | Evidência externa, divergência absoluta sem integração | score e consulta declarada | política/evidências | M |
| Faixas/recomendação | `services/credit_policy.py:11` `PolicyConfig`; `_score_band:66`; `decide_pudim:269` | Três recomendações, cap/faixa, garantias e encaminhamentos | output validado | parecer e governança | A |
| Contrato do motor | `finscore_v2/contracts.py:208` `validar_contrato` | Chaves/tipos públicos, contrato 1.0 | TypedDict/DataFrames | serviço | A |
| Contrato do parecer | `components/parecer_data_schema.py:820` `ParecerData`; `services/parecer_data_builder.py:1089` `build_parecer_data` | Contrato estrito 1.0, estados, metadados, dados utilizados | engine/política | evidências, parecer, dossiê | A |
| Evidências | `services/evidence_book.py:777` `build_evidence_book` | Achados vinculados à fonte, naturezas e limitações | contrato; financial_context | contexto narrativo | M |
| Governança | `services/credit_governance.py:134` `initialize_governance_state`; `register_analyst_manifestation:265`; `register_authority_decision:332` | Recomendação, manifestação e alçada distintas; histórico | schemas/fingerprint | UI e store | A |
| Geração | `services/parecer_generator.py` `generate_parecer_document`, `generate_variable_narrative` | Contexto estruturado e até três tentativas | llm_client, contrato, validadores | view parecer | A |
| Validação textual | `services/parecer_validation.py:494` `validate_parecer_narrative`; `parecer_evaluation.py` `evaluate_parecer_document` | Lastro de números/datas/IDs, semântica, cobertura | evidências e schema narrativo | gerador | A |
| Apresentação | `services/parecer_document.py:796` `render_structured_parecer`; `select_report_content:761` | Corpo fixo, narrativa validada, metodologia e três modos | contrato, metodologia | PDF/dossiê | M |
| PDF | `pdf/export_pdf.py:1260` `gerar_pdf_parecer` | HTML, engines PDF, tabelas e paginação | renderer, xhtml2pdf/Playwright | download e store | M |
| Dossiê | `services/analysis_dossier.py:131` `AnalysisDossierStore` | ID institucional, contrato, documento, histórico, telemetria separada | SQLAlchemy, models, governança | UI/exportação | A |
| Hashes | `core.py:175` `dataframe_sha256`; `parecer_document.py:91` `methodology_sha256`; `credit_governance.py:110` `governance_fingerprint` | Hash de dados, texto metodológico, estado e eventos | pandas/hashlib | reprodução e invalidação | A |
| Exportação | `services/analysis_export.py:182` `montar_abas_exportacao` | Abas técnicas, configuração, hashes e PCA com sinal canônico | output e autotestes | download XLSX | M |
| Logs | `components/llm_client.py`, `views/parecer.py:357` `_record_generation_failure`; `AnalysisDossierStore.record_technical_telemetry:349` | Erros técnicos e telemetria fora do parecer | logging/DB | suporte e auditoria | M |
| Testes atuais | `../tests/test_*.py`; `core.py:1341` `run_self_tests` | Unidade, contratos, governança, integração, relatório, comparação congelada | unittest/mocks/DB temporário | desenvolvimento | B |

Fluxo principal: XLSX → importação → serviço → engine/core → contrato e política → governança/evidências → gerador/validação → documento → PDF/dossiê. `components/policy_engine.py` contém regras legadas diferentes; a busca de imports no app ativo aponta para `services/credit_policy.py`. Não usar o módulo legado como ponto de extensão sem verificar seus consumidores.

## Semânticas, imputações e limites existentes

| Mecanismo | Comportamento observado | Efeito/limite |
|---|---|---|
| Entrada ausente | Vazio, hífen, N/A e NaN viram NaN; erro textual distinto gera bloqueio | Não vira zero na importação; texto original numérico é normalizado antes da rastreabilidade |
| Conversão numérica | `parse_accounting_value` remove caracteres e interpreta separadores | Strings ambíguas merecem validação de formato; por exemplo uma vírgula com três casas pode ser tratada como milhar |
| Não finito | Valores numéricos infinitos são convertidos em NaN; `safe_div` troca ±inf por NaN | `pct_change` do crescimento não usa safe_div: saída infinita pode chegar à curva. Registrar risco, não corrigir nesta etapa |
| Zero por correção | R-BAL-001 substitui por zero a única rubrica cuja retirada fecha o balanço | Correção automática **existente**, auditada, pendente de confirmação e bloqueadora de decisão; não confundir com ausência→zero |
| Inferência | R-BAL-002 preenche única parcela ausente de AT=PC+PNC+PL | Auditada, não validada documentalmente; bloqueio decisório preservado |
| Quarentena | Componentes incompatíveis com subtotal ficam NaN na base analítica | Origem e motivo preservados; cálculo pode continuar provisório |
| Derivação | Soma aritmética CP+LP mantém NaN se um termo falta | `_known_sum`/somatórios de reconstrução usam apenas parcelas conhecidas, com significado de soma parcial |
| Denominador | `safe_div` suprime `abs(denominador) <= 1e-9 × max(mediana absoluta,1)` | Valor não calculável continua NaN; limiar é legado quantitativo |
| Cobertura de juros | Despesa zero + EBIT positivo → 10; zero + EBIT negativo → −2; ambos zero → NaN | 10/−2 são valores convencionais do modelo, não quocientes matemáticos; origem não tem status estruturado exclusivo |
| Notas/curvas | `np.interp`, extremos fixos; NaN restabelecido explicitamente | Limites 0–95; não há extrapolação, extremos comprimem diferenças |
| Temporalidade | Nível/dinâmica/resiliência; pesos dos componentes disponíveis renormalizados | Ausência recente difere de ausência histórica; cobertura registra perda mas não mede ganho potencial por ausência |
| Núcleos | Cobertura ponderada mínima 0,70; pesos ativos renormalizados | Ausência de indicador ruim pode melhorar nota condicional. Não existe teste geral missingness_sensitivity_test |
| PCA | Mediana somente na matriz estatística; MAD→IQR→desvio padrão; clipping ±3 | Não imputa conta na base; fallback estrutural por insuficiência/instabilidade; 85/15 somente se aceito |
| Floors | Geométrica com núcleo <=0 →0; qualidade com floors de plausibilidade 0,40 e temporalidade 0,50 | Floors pertencem a camadas distintas; não são qualidade de crédito |
| Caps | Último ano; menor cap acionado; default 1000 sem regra | Teto acionado pode não reduzir score quando pré-cap já está abaixo do teto |
| Dívida ausente | Intervalo favorável zero / conservador subtotal integral | Apenas cópias diagnósticas; não substitui base observada; não cobre todos os indicadores |
| Cenários | Resíduos/taxas/amplitudes recebem clipping; gaps/excessos NaN recebem zero intermediário | Juros sem vínculo suficiente usam despesa histórica × choque; razão de receita inválida usa fator 1. Registrar explicitamente antes de qualquer revisão |
| Financiamento | Ausente em dívida + adição observável pode gerar saldo parcial; sem adição mantém ausência | É limite inferior, não confirmação de dívida total conhecida |
| Rejeição MC | Até 40 tentativas por trajetória; taxa >25% invalida interpretação | `accounting_flags` usa comparação/fillna(False); indefinição de score também rejeita. Ausência não é prova de consistência |
| Não aplicável | Springate possui classificação textual própria | Não há taxonomia unificada dos nove estados proposta na fase 3 |
| Não calculável/inconsistente | Enum do parecer distingue disponível/não informado/não calculado; flags de bloqueio separadas | NaN agrega causas; fontes/correções explicam parte delas. Não promover o enum novo nesta entrega |
| Defaults | Serviço usa simulação padrão/seed; período tem adaptador; política ausente usa PolicyConfig | Alguns `get/or` são conservadores (BLOQUEADO); módulo legado usa ausência→0 e não é a política ativa |
| Qualidade | Evidência documental=1 se não há correção pendente; materialidade NaN tratada como 0 no componente de correções | Esse índice não comprova documento assinado nem qualidade de crédito; alertas afetam Q e, via gate, podem afetar recomendação |

## Riscos e mistura de responsabilidades

1. **R01 — ausência favorável, potencial:** renormalização está comprovada no código; não foi executada nesta etapa a matriz adversarial da fase 4. Registrar impacto e destino dos pesos antes de propor qualquer penalização.
2. **R02 — validação também decisória:** `detect_material_bias` emite flags e `calculate_reliability` conta alertas altos/críticos. Adicionar um warning nessa coleção pode baixar Q e bloquear decisão. Novos warnings puramente explicativos devem ficar separados até desenho aprovado.
3. **R03 — cálculo também valida/corrige:** `validate_correct_and_prepare` modifica uma cópia analítica, infere identidades e coloca contas em quarentena. Não substituir regras existentes por hard stops genéricos sem equivalência e migração.
4. **R04 — cap e recomendação:** a política já trata faixa no cap <= referência, mas conserva `decisao=aprovar` com mitigadores. `MANDATORY_REVIEW` não existe como novo estado. Instituição deve aprovar sua semântica e flag; score 500 não vira 499,99.
5. **R05 — sentinels e falsa precisão:** juros zero pode representar 10/−2 na curva. Sem raw_ratio/calculation_status próprios, leitor pode interpretar valor convencional como razão observada.
6. **R06 — domínio:** não foi localizada documentação de validação setorial do **FinScore principal** nos arquivos Markdown/Python examinados de V2. A restrição de Springate não prova exclusão de seguradoras/bancos/holdings do FinScore. Proposta futura: UNKNOWN_DOMAIN até evidência documental; nunca marcar OUT_OF_DOMAIN apenas pelo setor.
7. **R07 — cenários:** a monotonicidade agregada é obrigatória e lança RuntimeError; isso não prova direção econômica de cada variável. EBIT negativo multiplicado por fator de margem menor pode ficar menos negativo. Diagnosticar por variável antes de alterar choque/reconstrução.
8. **R08 — baixa sensibilidade:** curvas, caps, temporalidade e gargalo podem comprimir impacto. Não existe decomposição geral que atribua a estabilidade do score a esses efeitos; score estável não prova resiliência.
9. **R09 — Serasa:** comparação absoluta por cortes 100/200/300 existe; não foi encontrada validação empírica que torne escalas equivalentes. Tratar proposta de HEURISTIC_COMPARISON como observabilidade, sem remover regra. Serasa de 500 nos casos de teste é **sintético**, não consulta real.
10. **R10 — reprodutibilidade:** hash_codigo do motor é constante ligada ao notebook, não hash integral do app atual. Versões motor/parecer/dossiê são separadas, mas não há manifest completo de ambiente/artefato/git; adicionar apenas em fase autorizada. Dados de tempo e globals do core exigem cuidado com concorrência (cada chamada da UI cria seu executor).
11. **R11 — apresentação:** parecer e UI já separam parcialmente qualidade e recomendação, porém ainda usam “Confiabilidade” e exibem score técnico em casos bloqueados. Reordenar headline e padronizar rótulo é fase 15/16/23, não modificação permitida agora.
12. **R12 — versões/compatibilidade:** schemas do motor, parecer, governança e dossiê continuam 1.0 apesar de campos opcionais adicionados em versões anteriores. Não incrementar metodologia por alteração documental futura; planejar migração/aditividade antes de novos campos.
13. **R13 — política configurável:** `cap_acionado_ate_500` compara com o limite configurado, que pode não ser 500. O nome legado não deve ser interpretado literalmente fora do default; preservar compatibilidade e propor metadado explícito.
14. **R14 — validação de software versus modelo:** três casos e autotestes confirmam implementação, não poder preditivo, calibração de PD, imparcialidade setorial ou aprovação institucional. Corpus adversarial e validação empírica permanecem pendentes.

## Pontos para controles futuros

Ver [plano incremental](model_controls_plan.md): cada grupo aponta local de extensão, categoria, aprovação e testes. Nesta branch, somente arquivos de documentação, infraestrutura de teste e fixtures serão adicionados. Nenhum consumidor de produção importa os golden tests.

## Evidências e limites

O baseline executável e o relatório before/after estão em [model_controls_baseline.md](model_controls_baseline.md). A revisão abrange o caminho ativo Pudim e os arquivos de documentação/testes indicados, não uma auditoria de todos os notebooks históricos ou uma validação externa setorial. Os riscos potenciais acima não são todos falhas reproduzidas; cada item identifica seu limite de evidência.
