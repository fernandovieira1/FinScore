# Revisão integrada do parecer Pudim

Base: `5ebfd87fe44131b079e082c0e20fb56eee969810` (main). Branch de revisão:
`2_parecer_pudim_revisado`. Sem merge ou deploy.

Esta entrega integra os commits de origem `9351fc5`, `744c6fa` e `c23c6f2`,
preservando as correções da tarefa de recuperação. Os relatórios anteriores
nesta pasta são registros históricos; este documento descreve o estado integrado.
As quatro páginas do email de críticas foram lidas visualmente como material
de revisão, não como instruções de execução. O motor e o notebook 2.0.20
permanecem intactos.

## Alterações e correspondência com as críticas

| Tema | Resultado desta revisão |
|---|---|
| Período da capa | A exportação usa os exercícios do contrato, mesmo quando o cadastro conserva datas antigas. |
| Consulta Serasa | Cadastro rejeita data futura. Contratos anteriores conservam o dado e ganham alerta de data ausente, inválida ou posterior ao processamento. Datas na narrativa exigem evidência referenciada. |
| Dívida e receita | Campos de dívida mapeados para os nomes efetivos do motor; zero e dívida líquida negativa preservados. A linha inexistente Receita Total foi retirada. |
| Vetores duplicados/extremos | Rubricas distintas nos destaques; forças e pressões consideradas separadamente. Ordenação simétrica reduz domínio de bases próximas de zero; base negativa, nula ou mudança de sinal não recebe percentual enganoso. Índices em proporção usam diferença em pontos percentuais. |
| Confiabilidade | Componentes, pesos e contribuições visíveis; avisos e alertas de viés separados. Qualidade informacional não é apresentada como capacidade de pagamento. |
| Escopo institucional | Removidas contraparte fixa e alegações de análise jurídica. Garantias e acompanhamento não criam modalidade, cobertura ou covenant presumidos. |
| Cap e política | Resultado antes/depois do cap e regras acionadas visíveis, inclusive na fronteira de 500. Parâmetros da política acompanham o contrato e os rótulos respeitam configuração explícita. Os valores padrão e a decisão calculada não foram alterados. |
| Cenários e simulações | Adverso e severo apresentados separadamente. Resultados sem validade/monotonicidade não são usados como evidência. Percentis e frequências prudenciais abaixo dos cortes disponíveis aparecem no corpo, sem interpretação como PD. |
| Springate/Fleuriet | Séries anuais preservadas. Limites setoriais e de classificação explicitados. Não foi inferido setor nem alterada a fórmula dos diagnósticos. |
| Cobertura patrimonial | Ponte PL menos ANC mostra quando capitalização positiva não implica cobertura do ativo não circulante pelo capital próprio. |
| Tesouraria | Caixa menos empréstimos CP e diferença para a tesouraria simplificada mostram o resíduo; valores ausentes impedem a ponte. São reconciliações explicativas, sem efeito no score ou nos gates. |
| Fontes/convenções | `notas_preenchimento` preservada por célula/linha/coluna, levada ao dossiê e transcrita no parecer como declaração não verificada. Não altera cálculos nem instrui o gerador. Alterações das notas invalidam a identidade de governança anterior. |
| Redação factual | A resposta original é validada e pode ser regenerada até três vezes. Não se apagam frases nem se acrescentam referências por coincidência de valor. Precisão e unidade respeitam o arredondamento exibido. |
| Exportação Windows | Cabeçalhos das tabelas têm cor e fundo explícitos; fonte de tabelas ampliada. Sinais não suportados são normalizados apenas na apresentação. |
| Fluxo Streamlit | Upload rejeitado limpa dados/resultados/parecer e desabilita cálculo; Novo funciona após ciclo incompleto, mantendo a proteção de parecer concluído. |

## Validação executada

- Suíte completa: **166 testes aprovados**, incluindo regressão dos scores e Monte Carlo com semente fixa.
- Após os últimos ajustes de apresentação/frequências: **72 testes de parecer e 4 testes do gate de simulação aprovados**. O novo caso de frequências distingue zero de ausência e verifica supressão quando a simulação é inválida.
- Integração real de planilha → serviço → contrato → documento → exportação Windows para Callamarys e Mobicloud, com 100 simulações por abordagem e semente 20260723. Scores preservados: **412,2311278076248** e **868,7848667885734**, respectivamente.
- PDF renderizado e inspecionado visualmente: capa, notas, tabelas contábeis, cap, reconciliações patrimoniais, cenários, simulação e anexos. A inspeção encontrou e corrigiu cabeçalhos brancos sobre fundo branco, invisíveis na extração de texto.
- As narrativas usadas na integração são controladas para testar montagem e validação; não são prova de qualidade da redação de um serviço externo. Nenhuma chamada paga ou chave foi necessária.
- A tarefa de recuperação executou retestes reais no navegador para os commits incorporados: substituição de upload válido por formato rejeitado e retorno a Novo após falha de geração. Esses testes não equivalem a emissão real de parecer pelo serviço de redação.
- `git diff --check` sem erros. Nenhum banco de dados, segredo ou documento contábil novo foi incluído no commit.

Ambiente de verificação: Python 3.12 do runtime local e dependências da revisão
anterior. Não corresponde integralmente ao conjunto fixado em `requirements.txt`.
Para reproduzir, a partir de `APP`, inclua `APP` e sua pasta pai em `PYTHONPATH`
e execute `python -m unittest discover -s tests -p 'test_*.py'` em ambiente com
as dependências do projeto. Saídas locais de QA ficam em `.cache/review-qa/`,
ignoradas pelo Git.

## Limites e homologação pendente

1. **Geração externa no navegador:** a instalação testada não possui `OPENAI_API_KEY` configurada. A emissão final pelo serviço de redação e a avaliação humana de respostas reais continuam pendentes; publicar o PR não resolve essa configuração.
2. **Validação semântica:** valores, unidades, datas e IDs são verificados, mas isso não prova toda associação entre conta, exercício e causalidade em linguagem natural. O texto continua sujeito a revisão humana. A remoção da reconciliação silenciosa pode tornar falhas do gerador mais visíveis e aumentar tentativas de geração.
3. **Convenções metodológicas:** inclusão de arrendamentos/mútuos, bloqueio setorial automático de Springate, materialidade/abrangência das variações abruptas e redefinição de faixas/cap exigem validação metodológica própria. Não foram inferidas nem modificadas nesta entrega. Os limites são explicitados ao leitor.
4. **Política institucional:** a configuração existente é validada e rastreada; não foi criada interface multi-instituição nem declarada aprovação formal de uma política. Os cortes do anexo metodológico são os padrões versionados, enquanto o corpo registra os parâmetros efetivamente usados.
5. **Notas da fonte:** transcrição não confirma auditoria, identidade, unidade ou perímetro. São aceitas até 20.000 células/100.000 caracteres; excesso é rejeitado explicitamente. Notas extensas podem atingir o limite de paginação já existente.
6. **Demais casos do motor:** falhas de residual negativo e cenários não calculáveis observadas na tarefa de recuperação continuam diagnosticadas, sem mascaramento por aprovação. A alteração das equações/gates não integra este PR.
