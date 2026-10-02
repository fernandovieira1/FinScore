# Notas da versão — FinScore V. 2.8.20 (Pudim)

Comparativo com a V.1 (Brigadeiro). Esta distribuição reúne a base mais recente presente na branch `main` e foi preparada para execução local independente.

## Motor de análise

- Inclusão do pacote `finscore_v2`, que separa contratos, avaliação, núcleo de cálculo e motor de execução.
- Ampliação da análise econômico-patrimonial, com novos controles de aptidão e confiabilidade e tratamento prudencial do FinScore.
- Inclusão de análises de contas, tabelas e gráficos específicos da versão Pudim.
- Evolução das validações de entrada e dos lançamentos, incluindo maior rastreabilidade dos dados usados no cálculo.
- Serasa, Springate e Fleuriet passam a ser evidências suplementares: não são somados ao score nem se tornam veto automático isolado.

## Alterações e inovações do modelo matemático, estatístico e lógico

### Estrutura matemática do score

- O modelo Pudim organiza a análise em dois núcleos explícitos: **EO** (econômico-operacional) e **FP** (financeiro-patrimonial). EO mede crescimento, margens, giro e ciclo de caixa; FP mede capitalização, liquidez, capital de giro, necessidade de capital de giro, dívida, cobertura de juros e perfil de vencimento.
- Cada indicador passa por curvas de pontuação com âncoras econômicas e interpolação linear, limitadas a 0–95 pontos e normalizadas na composição. Isso evita que um único índice extremo sature ou domine o resultado.
- A pontuação de cada indicador deixa de ser somente uma leitura pontual: combina nível atual (60%), dinâmica da série (25%) e resiliência — pior observação válida (15%). A V.2 exige três exercícios e preserva indisponibilidades; valor ausente não é tratado como zero e os pesos válidos são renormalizados.
- A cobertura informacional ponderada mínima de 70% por núcleo tornou-se um gate matemático. Abaixo desse piso, o núcleo e o FinScore ficam indisponíveis em vez de receberem um score artificial.
- A consolidação dos núcleos usa média geométrica de EO e FP e depois um mecanismo de gargalo: 75% do resultado geométrico mais 25% do núcleo mais fraco. O FinScore prudencial seleciona o menor resultado entre a abordagem estrutural e a adaptativa, impedindo que a alternativa mais favorável prevaleça isoladamente.
- Há penalidade transparente para recorrência de margem líquida negativa e caps prudenciais — prevalece o menor teto aplicável — para patrimônio líquido negativo, baixa capitalização, endividamento elevado e cobertura de juros insuficiente.

### Inovação estatística e robustez

- A V.2 inclui um componente adaptativo por análise de componentes principais (PCA), separado por núcleo. Os dados estatísticos são orientados para que maior valor represente melhor condição, imputados pela mediana somente na matriz estatística, padronizados de forma robusta e limitados a ±3 desvios.
- A adaptação é deliberadamente conservadora: requer pelo menos três variáveis ativas, observações suficientes e variabilidade. Examina até dois componentes principais e aceita pesos adaptativos apenas após 160 perturbações reproduzíveis atenderem simultaneamente limites de distância L1, similaridade de cosseno e concentração máxima de peso.
- Quando aprovada, a PCA contribui apenas 15% dos pesos finais, preservando 85% dos pesos estruturais. Com dados insuficientes, instabilidade ou concentração excessiva, o modelo recua integralmente aos pesos estruturais. Assim, a inovação estatística reduz redundância sem transformar a série curta de três exercícios em calibração autônoma de risco.
- Foram adicionados cenários determinísticos (base, adverso e severo), com reconstrução das identidades contábeis, e simulações Monte Carlo independente e correlacionada. O padrão é de 1.000 trajetórias, semente reproduzível, filtros de validade contábil e análise de percentis, dispersão e frequência abaixo de cortes de sensibilidade.
- Os resultados de simulação são medidas de sensibilidade condicionadas às premissas, não probabilidade de inadimplência (PD) nem rating regulatório.

### Lógica de qualidade e decisão

- A V.2 separa **FinScore** de **confiabilidade da informação**. O índice de confiabilidade considera completude, reconciliação, evidência documental, controle de correções, plausibilidade e consistência temporal; ele não altera a pontuação matemática e não é uma probabilidade estatística.
- A decisão só pode usar resultado apto: controles de qualidade, bloqueios, cobertura mínima e confiabilidade são verificados antes da recomendação. Resultado provisório pode servir para diagnóstico, mas não para deliberação.
- As evidências externas passam a ter papéis lógicos delimitados: Serasa é comparado sem média automática; Springate e Fleuriet são contrastes diagnósticos. Nenhum deles altera diretamente pesos, score, gargalo, caps ou simulações.
- A saída passa a ser contratada e auditável: inclui versão/metodologia, parâmetros de reprodutibilidade, status de qualidade, confiabilidade, scores observados, tabelas de auditoria, pesos, caps, cenários e simulações. Resultados bloqueados permanecem explicitamente sem score fabricado.

## Parecer de crédito e IA

- Novo fluxo estruturado para geração, validação, avaliação e renderização de pareceres.
- Integração com Responses API da OpenAI por HTTP, Structured Outputs, `store: false` e configuração por `.env`.
- Decisões padronizadas em `aprovar`, `nao_aprovar` e `dados_inconsistentes`; recomendação de garantia é mantida separada da decisão.
- Livro de evidências, contexto financeiro, dossiê de análise e documento de parecer passam a ser artefatos próprios.
- Exportação de PDF reforçada, com suporte a Playwright/Chromium e mecanismo alternativo.

## Governança, persistência e segurança

- Inclusão da política de crédito e do fluxo de governança com etapa de analista e etapa de alçada.
- Persistência local de dossiês, manifestações, deliberações e telemetria em SQLite, identificada por `FS-AAAA-NNNNNN`.
- Configuração de alçadas e administradores por `FINSCORE_AUTHORITY_EMAILS` e `FINSCORE_ADMIN_EMAILS`.
- Sem expurgo automático de dossiês ou telemetria: a instituição deve definir retenção e rotina de descarte antes da produção.
- Variáveis sensíveis foram externalizadas para `.env`; esta entrega não contém chave OpenAI, banco de dados, cache de tokens ou ambientes virtuais.

## Interface e documentação

- Atualizações de navegação, cabeçalho, barra superior, estado de sessão e tema visual.
- Nova metodologia versionada em `app_front/content/metodologia_pudim_2_0_20.md`.
- README refeito para instalação local em Python 3.12, configuração segura da chave, execução pelo comando `streamlit run app.py` e preparação da exportação PDF.

## Adaptações desta distribuição

- Criado `app.py` na raiz como ponto de entrada, mantendo o código da aplicação em `app_front/`.
- Dependências centralizadas e fixadas em `requirements.txt`.
- Criado `.gitignore` para impedir que chave, banco local, cache e ambiente virtual sejam enviados ao repositório.
- Removidos da entrega arquivos de teste, bytecode pré-existente, credenciais e artefatos de execução que não são necessários para iniciar o aplicativo. O SQLite distribuído contém apenas o esquema vazio, sem dados operacionais.
- Corrigidas três diretivas `from __future__ import annotations` indevidamente inseridas dentro de funções dos módulos de autenticação; o conjunto distribuído passa pela compilação integral em Python 3.12.

FinScore — Versão 2.8.20 (Pudim), outubro de 2026.
----------------------------------------------------

Modelo matemático e Aplicativo desenvolvido por FSV (fernandodvieira@usp.br)

Assertif - Todos os direitos reservados
