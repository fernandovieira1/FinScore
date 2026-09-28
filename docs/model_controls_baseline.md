# Baseline e golden tests — FinScore, 28/09/2026

Base: `ec1d3dad222186649dc7dafd5d3bb855f24d4e4c`, a main com a integração das branches 2 e 3. Escopo: fases 1 e 2. Esta entrega não modifica o aplicativo, a metodologia vigente, o contrato persistido ou a política.

## Referências congeladas

Fixtures: [`model_controls_v1`](../V.%202%20%28Pudim%29/APP/tests/fixtures/model_controls_v1/). O [`manifest.json`](../V.%202%20%28Pudim%29/APP/tests/fixtures/model_controls_v1/manifest.json) registra commit, hashes dos três XLSX, hashes dos snapshots, configuração, ambiente e hashes LF-normalizados dos arquivos de produção examinados. É um manifesto **do baseline de testes**; a rotina produtiva `reproduction_manifest()` da fase 18 não foi implementada.

Entradas:

| Caso | XLSX existente em `V. 2 (Pudim)/MODELO/dados_teste` | Tipo declarado na fixture |
|---|---|---|
| Mobicloud | `5umarket - Mobicloud Tecnologia.xlsx` | Serviços não financeiros |
| SSA-MRO | `6strumarket - SSA-Miro Solucoes.xlsx` | Serviços não financeiros |
| JNS | `12Grupo JNP - JNS Seguradora.xlsx` | Seguradora |

Período: 2023–2025. Serasa **sintético**: 500, com data 22/09/2026, para manter a referência usada nos testes anteriores. A classificação setorial é configuração de teste, não validação externa da atividade. As planilhas não foram alteradas nem duplicadas.

Semente: `20260723`, e `20360723` na abordagem correlacionada, conforme o deslocamento existente de 100.000. São **100 trajetórias por abordagem por caso** no corpus de regressão, o mínimo aceito pelo motor. O default de produção continua 1.000. Este baseline não se apresenta como repetição dos smoke tests anteriores de 1.000 trajetórias.

O relógio do engine é fixado **somente no helper de testes**, em `2026-09-28T12:00:00`, antes do processamento, para tornar determinísticos timestamps de auditoria e ID derivado. A fixture não congela RNG por mock, não altera contas, índices, pesos, regras, alertas ou retornos. Todos os resultados financeiros vêm do código de produção inalterado.

## Resultados de referência

Valores abaixo arredondados para leitura; os JSON preservam a precisão recebida do motor.

| Medida | Mobicloud | SSA-MRO | JNS |
|---|---:|---:|---:|
| EO estrutural | 914,858064 | 443,679273 | 333,252357 |
| FP estrutural | 848,893168 | 657,678783 | 445,271343 |
| EO adaptativo | 914,956690 | 462,652764 | 356,040614 |
| FP adaptativo | 841,991235 | 656,278227 | 461,314987 |
| Geométrica estrutural | 881,258623 | 540,183714 | 385,211273 |
| Geométrica adaptativa | 877,716078 | 551,025350 | 405,273823 |
| Pós-gargalo estrutural | 873,167259 | 516,057603 | 372,221544 |
| Pós-gargalo adaptativo | 868,784867 | 528,932203 | 392,965521 |
| Prudencial antes do cap | 868,784867 | 516,057603 | 372,221544 |
| Teto aplicável | 1.000 (sem regra acionada) | 500 | 500 |
| Prudencial final | **868,784867** | **500,000000** | **372,221544** |
| Qualidade informacional | 93,00% | 92,519048% | 88,85% |
| Apto para cálculo | sim | sim | sim |
| Apto para decisão | sim | sim | **não** |
| Alertas de viés, total | 10 | 8 | 7 |
| Alertas de viés bloqueadores | 0 | 0 | **2** |
| Alertas de saturação | 5 | 5 | 1 |
| Recomendação atual | aprovar | aprovar | dados_inconsistentes |
| Faixa atual | 500 OU MAIS | APROVAÇÃO SUJEITA A MITIGADORES | 250 A 499,99 |

Em SSA-MRO e JNS, `CAP-JUROS-1` registra cobertura de −2, limiar 1 e teto 500. Em JNS, o cap está acionado mas não reduz o prudencial pré-cap, que já é 372,22. **Cap acionado não é sinônimo de cap vinculante.**

Em Mobicloud/SSA, saturam margem bruta, capitalização, liquidez corrente, liquidez seca e cobertura de juros. Em JNS, cobertura de juros. O Serasa sintético gera divergência elevada em Mobicloud; os dados não certificam consulta real.

O estado formal `MANDATORY_REVIEW` e o campo `score_usage=NON_DECISIONAL` ainda não existem na política ativa. JNS já tem `utilizavel_decisao=NAO`, `score_provisorio=true` e recomendação bloqueada. Os testes preservam esses nomes existentes; não fingem que a fase 6/15 já foi implementada.

## Cobertura dos snapshots e testes

Cada JSON contém **todo o output do serviço**, inclusive contas, indicadores, notas, componentes temporais, contribuições, pesos/cargas/diagnósticos PCA, caps, cenários, trajetórias Monte Carlo, resumos, rejeições, hashes, rastreabilidade, alertas, evidências suplementares, aliases e configurações. Também contém o retorno integral da política e o contrato estruturado do parecer com seus achados.

Serialização preserva ordem, tipos de tabela, eixos e dtypes. NaN/inf têm tags explícitas e não são confundidos com null ou zero. Não se arredondam valores, não se descartam linhas e não se normaliza sinal de PCA. Comparações numéricas usam tolerância absoluta e relativa de `1e-10` (até `1e-7` ponto no score 1.000); textos, estados, campos, contagens e estrutura são exatos. Ambiente diferente pode exigir análise de divergência numérica, nunca atualização automática da expectativa.

São nove testes novos: três comparações integrais, três verificações semânticas independentes dos valores esperados, integridade dos inputs/fixtures, detecção de mutações de score/política/peso/bloqueio e distinção de ausente/zero/tipos/variação subcentésima. Os testes não importam a rotina de captura para sobrescrever expectativas. A comparação é feita contra arquivos versionados, nunca contra uma segunda chamada usada como expectativa dinâmica.

Não foram criados os 30 adversariais da fase 20 nesta execução; esse trabalho depende da próxima autorização. As mutações do comparador verificam a eficácia dos golden tests e não implantam controles no modelo.

## Reprodução

Na raiz, com Python 3.12 e dependências de `requirements.txt` instaladas:

```powershell
python "V. 2 (Pudim)/APP/scripts/run_model_controls_tests.py" --suite all --output "$env:TEMP/FinScore-model-controls-check"
```

Use `--suite legacy` para os 205 testes existentes e `--suite golden` para os nove novos. O runner resolve imports por caminhos do próprio script, sem depender da pasta atual, e gera log + resumo JSON. Nenhum teste chama a API de redação ou usa a base de dados operacional; testes de persistência existentes usam bancos temporários.

O script `capture_model_controls_baseline.py` é ferramenta de manutenção: exige checkout no commit base e produção sem diferenças, e recusa sobrescrever diretório existente. Para nova metodologia/política autorizada, criar nova versão de baseline por revisão explícita; não “aceitar” regressões regenerando a fixture atual. Os arquivos JSON mantêm LF por `.gitattributes` para preservar hashes também no Windows.

## Execuções

- BEFORE: **205 testes legados aprovados**, 0 falhas, 0 erros, 0 ignorados, 134,919 s. Registro em `baselines/ec1d3dad2/before/`.
- AFTER e comparação before/after: consultar [relatório de validação](model_controls_validation.md), gerado após a execução completa.

Ambiente da captura: Python 3.12.14, Windows 11, NumPy 1.26.4, pandas 2.2.2, SciPy 1.11.4, scikit-learn 1.4.2, Pydantic 2.13.4 e openpyxl 3.1.5. Demais versões constam no manifesto. Não há modificação das dependências do projeto.

## Limites

Os golden tests exercitam importação → serviço → engine → política → contrato/evidências, com MC e cenários. Não são execução no navegador nem comparação de PDFs. A redação remota é não determinística e ficou fora desta captura; o template/PDF permanece intacto e a suíte legada continua verificando geração, validação e renderização com respostas controladas. Esta entrega não gera novos pareceres nem substitui os PDFs já entregues.
