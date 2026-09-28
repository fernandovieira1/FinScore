# Changelog — baseline de controles v1

28/09/2026 · base `ec1d3dad2` · branch `4_auditoria_baseline_controles`.

| Alteração | Categoria | Motivação/impacto | Score alterado? | Decisão alterada? | Schema produtivo alterado? | Validação | Rollback |
|---|---|---|---|---|---|---|---|
| Mapa arquitetural e semânticas | OBSERVABILITY | Localizar responsabilidades, dependências e riscos antes de controles novos | não | não | não | Inspeção do caminho ativo e referências | Remover docs novos |
| Plano incremental/protocolo | OBSERVABILITY | Registrar BEFORE/AFTER e gates institucionais | não | não | não | Escopo limitado às fases 1–2 | Remover docs novos |
| Corpus `model_controls_v1` | OBSERVABILITY | Fixar outputs atuais dos três casos, inputs, hashes e ambiente | não | não | não; JSON é fixture de teste | Integridade e recaptura pela suíte | Remover fixtures novas |
| Nove golden tests | VALIDATION | Detectar regressão em matemática, contratos, alertas e decisão | não | não | não | 9/9 passaram; 205 legados preservados | Remover helper/teste novo |
| Captura protegida e runner | VALIDATION | Evitar overwrite de expectativa e permitir execução portátil | não | não | não | Captura na base e execução completa 214/214 | Remover scripts novos |

Versão adicionada: somente `baseline_version=1.0`, interna ao corpus de teste. `methodology_version`, `decision_policy_version`, schemas e assinaturas do app não foram alterados. Nenhum rule set de produção novo foi criado.

## Arquivos adicionados e justificativas

| Arquivo/pasta | Justificativa |
|---|---|
| `docs/model_controls_audit.md` | Auditoria exigida na fase 1; mapa, semânticas e riscos |
| `docs/model_controls_plan.md` | Protocolo BEFORE/AFTER e classificação/localização das propostas futuras |
| `docs/model_controls_baseline.md` | Entradas, parâmetros, resultados, escopo e reprodução da fase 2 |
| `docs/model_controls_validation.md` | Relatório before/after e limites da validação |
| `docs/model_controls_changelog.md` | Mudanças, categorias, impactos e rollback |
| `docs/baselines/ec1d3dad2/before/legacy.json` e `legacy.log` | Evidência da suíte antes das adições |
| `docs/baselines/ec1d3dad2/after/all.json` e `all.log` | Evidência da suíte completa após as adições |
| `docs/baselines/ec1d3dad2/after/golden.json` e `golden.log` | Reteste dos nove golden após normalização das quebras de linha dos snapshots |
| `V. 2 (Pudim)/APP/tests/golden_model_support.py` | Captura test-only e comparação sem arredondar/mutar produção |
| `V. 2 (Pudim)/APP/tests/test_model_controls_golden.py` | Golden tests e checks independentes/mutações do comparador |
| `V. 2 (Pudim)/APP/tests/fixtures/model_controls_v1/mobicloud.json` | Snapshot integral Mobicloud |
| `V. 2 (Pudim)/APP/tests/fixtures/model_controls_v1/ssa_mro.json` | Snapshot integral SSA-MRO |
| `V. 2 (Pudim)/APP/tests/fixtures/model_controls_v1/jns.json` | Snapshot integral JNS |
| `V. 2 (Pudim)/APP/tests/fixtures/model_controls_v1/manifest.json` | Proveniência, hashes e ambiente do corpus |
| `V. 2 (Pudim)/APP/tests/fixtures/model_controls_v1/.gitattributes` | Garantir LF nos JSON e estabilidade dos hashes entre plataformas |
| `V. 2 (Pudim)/APP/scripts/capture_model_controls_baseline.py` | Captura explícita na base e recusa de overwrite |
| `V. 2 (Pudim)/APP/scripts/run_model_controls_tests.py` | Execução legacy/golden/all com logs e resumo JSON |

Não há arquivos existentes de produção ou testes legados modificados. Nenhum arquivo de configuração secreta, banco operacional, parecer PDF ou notebook foi alterado. As fases seguintes não foram implementadas.
