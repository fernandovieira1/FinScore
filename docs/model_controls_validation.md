# Validação BEFORE / AFTER — fases 1 e 2

Base: `ec1d3dad222186649dc7dafd5d3bb855f24d4e4c`. Branch: `4_auditoria_baseline_controles`. Data: 28/09/2026.

## Execuções registradas

| Rodada | Testes | Falhas | Erros | Ignorados | Duração |
|---|---:|---:|---:|---:|---:|
| BEFORE: suíte existente, sem golden tests adicionados | 205 | 0 | 0 | 0 | 134,919 s |
| AFTER: suíte existente + golden tests | 214 | 0 | 0 | 0 | 154,922 s |
| Golden repetidos após normalização LF dos arquivos JSON | 9 | 0 | 0 | 0 | 52,485 s |

Registros: [BEFORE JSON](baselines/ec1d3dad2/before/legacy.json), [BEFORE log](baselines/ec1d3dad2/before/legacy.log), [AFTER JSON](baselines/ec1d3dad2/after/all.json), [AFTER log](baselines/ec1d3dad2/after/all.log). Os 39 autotestes metodológicos também permanecem cobertos pela suíte legada. Scripts demonstrativos de gráficos/PDF fora de `APP/tests` não são contabilizados como testes dessa suíte.

Reteste final de portabilidade: [golden JSON](baselines/ec1d3dad2/after/golden.json) e [golden log](baselines/ec1d3dad2/after/golden.log). A normalização alterou somente quebras de linha e hashes dos arquivos de fixture, sem alterar valores JSON.

## Comparação dos três casos

As colunas BEFORE vêm dos arquivos congelados no commit base; AFTER foi recalculado pela suíte. “Preservado” significa que o teste integral passou com tolerância absoluta/relativa 1e-10 para floats e comparação exata para estrutura/texto/estados. Valores da tabela arredondados somente para leitura.

| Item | Mobicloud BEFORE → AFTER | SSA-MRO BEFORE → AFTER | JNS BEFORE → AFTER |
|---|---|---|---|
| Score prudencial | 868,784867 → 868,784867 | 500 → 500 | 372,221544 → 372,221544 |
| Score pré-cap | 868,784867 → igual | 516,057603 → igual | 372,221544 → igual |
| Núcleos estrutural/adaptativo | Todos preservados | Todos preservados | Todos preservados |
| Notas por exercício e temporais | Preservadas | Preservadas | Preservadas |
| Pesos, cargas, diagnósticos PCA | Preservados | Preservados | Preservados |
| Composição/gargalo | Preservados | Preservados | Preservados |
| Caps | Nenhum acionado; default 1.000 preservado | CAP-JUROS-1, 500 preservado | CAP-JUROS-1, 500 preservado, sem reduzir score |
| Recomendação | aprovar → aprovar | aprovar → aprovar | dados_inconsistentes → dados_inconsistentes |
| Estado legado | CALCULADO → igual | CALCULADO → igual | CALCULADO_COM_ALERTAS → igual |
| Apto cálculo / decisão | sim / sim → igual | sim / sim → igual | sim / não → igual |
| Alertas bloqueadores | 0 → 0 | 0 → 0 | 2 → 2 |
| Alertas de viés | 10 → 10 | 8 → 8 | 7 → 7 |
| Ocorrências de aviso de qualidade | 0 → 0 | 2 → 2 | 0 → 0 |
| Saturação | 5 indicadores → iguais | 5 indicadores → iguais | 1 indicador → igual |
| Cenários/MC/contrato/evidências | Preservados | Preservados | Preservados |

Não foi criado novo estado decisório. A nomenclatura, a recomendação de mitigadores e os bloqueios já existentes permanecem registrados nos snapshots. Os dois bloqueadores de JNS vêm dos alertas de viés; contagem de ocorrências críticas de qualidade não é a mesma contagem.

## Verificação de não regressão e eficácia

- Os três golden tests comparam todo o output do serviço, política e contrato contra expectativas persistidas; não recalculam a expectativa dentro do teste.
- Verificações independentes exigem os scores conhecidos, o cap da SSA e o bloqueio da JNS.
- Mutações deliberadas em **cópias das fixtures**, de score, peso, recomendação e bloqueio, são detectadas. O teste também diferencia zero, null, NaN, booleano e alteração de 0,0001 ponto.
- Integridade SHA-256 dos XLSX e snapshots passou. Mesma seed gerou a mesma saída dentro da tolerância. A suíte legada mantém seu teste específico de Monte Carlo contra resultado congelado.
- O diff de `APP/app_front` e `requirements.txt` frente ao commit base está vazio. Nenhum teste legado foi editado ou removido.
- O relógio fixo é exclusivo da captura/comparação de testes. O app continua usando seu relógio normal e default de 1.000 simulações.
- Houve RuntimeWarnings de NumPy para médias de séries vazias em casos legados; não foram suprimidos ou convertidos em alteração de comportamento. Não houve falha ou erro de teste.

## Riscos residuais e próximos gates

Os riscos R01–R14 estão em [model_controls_audit.md](model_controls_audit.md). Aprovação da suíte não resolve, por si só, favorecimento por ausência, domínio não documentado, semântica dos sentinels, explicabilidade de stress ou equivalência das escalas FinScore/Serasa. Nenhuma nova penalização, revisão obrigatória ou restrição setorial foi ativada.

O [plano incremental](model_controls_plan.md) classifica os próximos controles e identifica os pontos de extensão. Permanecem **POLICY_DECISION_REQUIRED**: domínio institucionalmente aceito, piso por núcleo, revisão obrigatória por cap, catálogo/precedência dos novos hard stops, critérios novos de materialidade e sensibilidade, e autoridade/validade dos overrides. Qualquer mudança quantitativa exige autorização específica adicional.

**Fases 1–2 concluídas. Fases 3–30 aguardam autorização do usuário, conforme a instrução final do prompt.**
