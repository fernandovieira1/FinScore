# Revisão de rastreabilidade do parecer — 22/09/2026

Base examinada: `5ebfd87fe44131b079e082c0e20fb56eee969810` (main remoto).
Branch: `codex/parecer-rastreavel`.

## Problemas corrigidos

- As tabelas e os achados buscavam `d_Divida_Bruta` e `d_Divida_Liquida`, enquanto o motor fornece `d_Divida_Financeira_Bruta` e `d_Divida_Financeira_Liquida`. O mapeamento agora usa o contrato real: zero continua zero e dívida líquida negativa continua negativa. A linha inexistente `r_Receita_Total` foi retirada; não foi criada uma fórmula substituta.
- A introdução atribuía análise jurídica e contraparte fixa sem evidência. Agora delimita análise econômico-financeira e patrimonial, tomador e período efetivos, e remete a decisão à alçada humana.
- Os três maiores movimentos podiam repetir a mesma rubrica e omitir toda pressão adversa. Destaques detalhados agora usam rubricas distintas; forças e pressões são examinadas sobre toda a série e deduplicadas separadamente.
- O livro de evidências só incluía o cenário severo. Inclui agora adverso e severo, com origem, valor base e diferença individual; dados ausentes não são convertidos em zero. A conclusão e a tabela mostram os dois cenários.
- Springate e Fleuriet eram limitados ao exercício final. A tabela e os achados conservam todos os exercícios em ordem cronológica. Springate sem score passa a limitação, em vez de força.
- A tolerância numérica de 0,011 em proporções admitia diferenças relevantes; o fator relativo também crescia com os montantes. Agora a tolerância corresponde ao arredondamento de duas casas da unidade exibida. Percentuais exigem evidências em proporção; anos, moeda e pontos não os autorizam.
- A qualidade exibe separadamente alertas de viés e avisos, com nota, peso e contribuição de cada componente da confiabilidade. Resultados de cenários e simulações disponíveis voltam ao corpo do documento.
- O exportador Windows normaliza sinais de menos e setas para equivalentes legíveis nas fontes básicas, somente na renderização HTML.

## Fontes e invariantes

Foram examinados APP, contrato estruturado, motor extraído, metodologia versionada, testes e origem do extrator em `MODELO/algoritmos/Versao 20/FinScore_V2_0_20.ipynb`. As quatro páginas do PDF local de críticas foram lidas visualmente. O PDF/email foi tratado como referência de revisão.

Esta alteração não muda contas de entrada, fórmulas do motor, curvas, pesos, caps, corte decisório nem a fonte metodológica. O documento é suporte à análise humana; não concede crédito. A classificação favorável de um movimento continua dependendo da orientação definida pelo modelo, e não prova causalidade nem materialidade econômica.

## Evidências de teste

- Suíte completa: 147 testes e 5 subtestes aprovados. Após as últimas inclusões de tabelas/conclusão, nova execução das suítes afetadas de parecer, avaliação, evidências e precisão.
- Casos novos: adverso 495 e severo 395 com base 500; cenário ausente versus zero; estabilidade versus deterioração; percentual pequeno negativo versus zero; arredondamento; montante elevado; troca indevida de unidade; trajetória de recuperação; diagnóstico ausente; forças extremas coexistindo com pressões.
- Comparação real de documentos usando os mesmos dados e narrativa controlada: Callamarys (412,2311278076248) e Mobicloud (868,7848667885734). Springate/Fleuriet passaram de uma para três linhas anuais em ambos; alegação jurídica removida; cenário adverso rastreável.
- Smoke de exportação Windows: PDF de 10 páginas, renderizado e inspecionado visualmente. As tabelas de dívidas, confiabilidade e cenários estão presentes. Não foi executada geração paga com serviço externo de redação: os testes usam narrativa controlada para isolar a montagem e os controles factuais.
- `git diff --check` sem erros.

Ambiente: Python 3.12 e dependências instaladas em diretório local excluído do Git. Os testes usaram versões disponíveis no ambiente de revisão, não uma reprodução exata de todas as versões de produção; a homologação no ambiente fixado em requirements.txt continua necessária. As comparações, scripts e PDF de QA estão em `review-output/`, excluído do commit.

## Pontos que ainda exigem trabalho/homologação

Esta revisão não encerra todas as críticas do email. Permanecem para validação específica: importação e uso das notas de preenchimento; perímetro de dívida incluindo arrendamentos/mútuos; aplicabilidade setorial do Springate; decomposição residual do Fleuriet; abrangência e materialidade dos alertas de variação; política parametrizável e interpretação do cap na fronteira de faixa. Alterar essas convenções exige critérios explícitos e regressão metodológica, não apenas edição da narrativa.

A correspondência de números e IDs ainda não é prova semântica completa de associação entre conta, valor e exercício dentro de uma frase. A reconciliação automática existente pode remover frases e procurar evidências por número; os testes não substituem revisão humana do conteúdo gerado. Datas também precisam de validação factual própria: não são verificadas por este comparador numérico.

## Publicação

Não houve merge ou deploy. Push e PR dependem de autenticação GitHub utilizável neste ambiente: o helper de credenciais ficou aguardando; execução sem helper confirmou ausência de Username; navegador abriu desconectado. Nenhuma credencial foi impressa ou solicitada em texto. A branch e o commit local permitem retomar a publicação após login.
