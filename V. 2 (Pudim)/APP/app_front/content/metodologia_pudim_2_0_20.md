## Metodologia

O FinScore sintetiza a capacidade econômico-financeira de empresas em uma escala de 0 a 1.000 pontos. A leitura combina desempenho econômico-operacional, estrutura financeira e patrimonial, evolução em três exercícios, qualidade da informação e resposta a cenários de estresse. Quanto maior a pontuação, mais favorável é a capacidade relativa observada para suportar obrigações financeiras.

A pontuação não é uma probabilidade de inadimplência, um rating regulatório ou uma estimativa direta de perda esperada. A decisão de crédito considera o FinScore prudencial, a aptidão do resultado e, de forma suplementar, Serasa, Springate e Fleuriet. Garantias, covenants e alçada permanecem separados do cálculo da pontuação.

### 1. Escopo e sequência de cálculo

O cálculo segue uma sequência reproduzível:

1. importação de 21 contas primárias para três exercícios;
2. validação contábil, reconciliação e registro de correções ou quarentenas;
3. cálculo das contas derivadas e dos indicadores econômico-financeiros;
4. transformação dos indicadores em notas por curvas com âncoras explícitas;
5. composição temporal de nível atual, dinâmica e resiliência;
6. formação dos núcleos Econômico-Operacional (EO) e Financeiro-Patrimonial (FP);
7. cálculo estrutural e cálculo adaptativo, com controle de estabilidade estatística;
8. combinação dos núcleos, aplicação do gargalo e dos caps prudenciais;
9. execução dos cenários determinísticos e das análises de sensibilidade;
10. cálculo separado da confiabilidade e aplicação das regras de decisão de crédito.

Cada camada conserva sua função. Contas reportadas, valores utilizados, indicadores, notas, FinScore, confiabilidade e decisão são apresentados separadamente. Uma correção não substitui silenciosamente o valor de origem; uma evidência externa não altera a pontuação; uma condição contratual não cria uma categoria adicional de decisão.

### 2. Dados de entrada e rastreabilidade

São exigidos três exercícios identificados por anos inteiros, positivos e não duplicados. A ordenação é cronológica. Períodos não consecutivos geram aviso, pois podem reduzir a comparabilidade da trajetória. Ausências permanecem como valores ausentes e não são convertidas em zero.

As contas primárias são:

| Grupo | Contas |
|---|---|
| Ativo | caixa e equivalentes; contas a receber de clientes; estoques; ativo circulante; imobilizado líquido; ativo total |
| Passivo e patrimônio líquido | fornecedores; obrigações tributárias de curto prazo; obrigações trabalhistas de curto prazo; passivo circulante; passivo não circulante; empréstimos e financiamentos de curto e longo prazo; patrimônio líquido |
| Resultado | receita líquida; CMV/CPV/CSV; resultado antes de IR/CSLL; lucro líquido; receitas financeiras; despesa de IR/CSLL; despesas financeiras |

O valor textual que não possa ser convertido em número bloqueia cálculo e decisão. A trilha de auditoria registra, por exercício e conta, o valor reportado, o valor proposto, o valor utilizado, a variação absoluta e relativa, a materialidade sobre o ativo, a regra aplicada, a evidência, a confiança, os indicadores afetados, a necessidade de confirmação e o responsável.

### 3. Integridade contábil, correções e alertas

A identidade principal é:

`Ativo Total = Passivo Circulante + Passivo Não Circulante + Patrimônio Líquido`

A tolerância de fechamento corresponde a 0,5% do Ativo Total. Também são verificados sinais incompatíveis com a natureza das contas, Ativo Total não positivo, subtotais inferiores à soma de seus componentes e Ativo Total inferior ao Ativo Circulante acrescido do Imobilizado Líquido.

Uma única parcela ausente da identidade patrimonial pode ser inferida quando as demais estão presentes e o resultado respeita as restrições de sinal. A confiança mínima para aplicação automática é 90%; as inferências previstas alcançam 99%. Uma rubrica isolada que, retirada, reconcilie inequivocamente o balanço pode ser ajustada a zero com confiança de 97%. Essas ocorrências permanecem sujeitas a confirmação documental e bloqueiam a decisão enquanto pendentes.

Alterações iguais ou superiores a 1% do Ativo Total são materiais para o controle de correções. Potencial de viés alto é identificado a partir de 5% do Ativo Total. Conflitos sem solução unívoca levam as rubricas envolvidas à quarentena; não há escolha automática do valor mais conveniente.

Entre os alertas bloqueadores estão balanço não reconciliado, conta com sinal inválido, correção material sem confirmação, patrimônio líquido inferior a 5% do ativo, índice extremo que comprometa a comparabilidade, DRE não reconciliada e ausência integral de contas essenciais, como CMV/CPV/CSV ou empréstimos de longo prazo. Variações anuais de 50% ou mais e saturação reiterada de curva são sinalizadas para análise, mas não bloqueiam isoladamente a decisão.

O FinScore provisório pode ser calculado quando os controles matemáticos são satisfeitos, embora persistam pendências documentais. Nesse caso, a pontuação serve para diagnóstico e não para deliberação.

### 4. Indicadores econômico-financeiros

O núcleo EO mede crescimento, rentabilidade, produtividade dos ativos e ciclo financeiro. O núcleo FP mede capitalização, liquidez, capital de giro, dívida e capacidade de serviço financeiro.

| Núcleo | Indicador | Definição de cálculo |
|---|---|---|
| EO | Crescimento da receita | `Receita(t) / Receita(t-1) - 1` |
| EO | Margem bruta | `(Receita Líquida - CMV/CPV/CSV) / Receita Líquida` |
| EO | Margem EBIT | `EBIT / Receita Líquida` |
| EO | Margem líquida | `Lucro Líquido / Receita Líquida` |
| EO | Giro do ativo | `Receita Líquida / Ativo Total médio` |
| EO | Ciclo de conversão de caixa | prazo médio de recebimento + prazo médio de estoques − prazo médio de fornecedores |
| FP | Capitalização | `Patrimônio Líquido / Ativo Total` |
| FP | Liquidez corrente | `Ativo Circulante / Passivo Circulante` |
| FP | Liquidez seca | `(Ativo Circulante - Estoques) / Passivo Circulante` |
| FP | CCL sobre o ativo | `(Ativo Circulante - Passivo Circulante) / Ativo Total` |
| FP | NCG operacional sobre o ativo | `(Clientes + Estoques - Fornecedores) / Ativo Total` |
| FP | Dívida líquida sobre o ativo | `(Empréstimos CP + Empréstimos LP - Caixa) / Ativo Total` |
| FP | Cobertura de juros | `EBIT / Despesas Financeiras` |
| FP | Composição do endividamento | `Passivo Circulante / (Passivo Circulante + Passivo Não Circulante)` |

O EBIT é reconstruído como resultado antes de IR/CSLL mais despesas financeiras menos receitas financeiras. Os prazos médios usam saldos médios de clientes, estoques e fornecedores e base anual de 365 dias. O primeiro exercício não recebe valores artificiais para medidas que dependem do período anterior.

O endividamento exigível, calculado por `(Passivo Circulante + Passivo Não Circulante) / Ativo Total`, permanece como diagnóstico e insumo dos caps, sem peso direto no núcleo FP. Essa separação reduz dupla contagem com capitalização e demais indicadores de dívida.

Quando a despesa financeira é zero, a cobertura recebe teto econômico de 10 vezes se o EBIT for positivo e valor de referência de −2 se o EBIT for negativo. A despesa financeira é tratada como proxy de juros e deve ser confirmada quando contiver componentes não associados ao custo da dívida.

### 5. Curvas de pontuação

Cada indicador é convertido por interpolação linear entre âncoras. As curvas variam de 0 a 95 pontos; valores além das extremidades recebem a nota da extremidade correspondente. A nota de 95 é posteriormente normalizada para 100 na composição temporal. O limite evita que um único indicador saturado domine a análise.

Valores percentuais são apresentados abaixo em porcentagem; múltiplos e dias mantêm suas unidades naturais. Cada par tem a forma `valor do indicador → nota`.

| Indicador | Âncoras da curva |
|---|---|
| Crescimento da receita | −30%→0; 0%→45; 10%→70; 25%→90; 50%→95 |
| Margem bruta | −10%→0; 0%→10; 15%→45; 30%→75; 50%→95 |
| Margem EBIT | −20%→0; 0%→35; 10%→70; 20%→90; 35%→95 |
| Margem líquida | −20%→0; 0%→35; 7%→70; 15%→90; 25%→95 |
| Giro do ativo | 0x→0; 0,30x→25; 0,70x→60; 1,20x→85; 2,00x→95; 5,00x→95 |
| Ciclo de conversão de caixa | −60 dias→95; 0→90; 30→75; 60→55; 90→35; 150→10; 240→0 |
| Capitalização | −20%→0; 0%→5; 5%→20; 15%→50; 30%→80; 50%→95 |
| Liquidez corrente | 0x→0; 0,70x→10; 1,00x→45; 1,30x→70; 1,80x→95; 4,00x→95 |
| Liquidez seca | 0x→0; 0,50x→10; 0,80x→40; 1,10x→70; 1,50x→95; 3,00x→95 |
| CCL sobre o ativo | −50%→0; −10%→15; 0%→45; 10%→65; 25%→85; 50%→95 |
| NCG operacional sobre o ativo | −30%→95; −10%→85; 0%→70; 10%→50; 25%→20; 50%→0 |
| Dívida líquida sobre o ativo | −30%→95; 0%→90; 20%→70; 40%→35; 70%→0 |
| Composição do endividamento | 0%→95; 30%→80; 50%→55; 75%→25; 100%→0 |
| Cobertura de juros | −2x→0; 0x→5; 1x→25; 2x→55; 4x→80; 10x→95; 50x→95 |

A curva diagnóstica do endividamento exigível utiliza 0%→95; 30%→85; 50%→60; 70%→30; 100%→0; 150%→0. Esse indicador não compõe diretamente os pesos do FP.

### 6. Composição temporal

Para cada indicador, a série de três exercícios é resumida por três componentes:

| Componente | Peso | Leitura |
|---|---:|---|
| Nível atual | 60% | nota do exercício mais recente, normalizada de 0–95 para 0–100 |
| Dinâmica temporal | 25% | nível atual acrescido de metade da mudança entre a primeira e a última nota válida, com limite de 0 a 100 |
| Resiliência | 15% | pior nota válida da série, normalizada para 0–100 |

Os percentuais são pesos de componentes analíticos, não pesos diretos dos três anos. Dinâmica e resiliência exigem pelo menos duas observações válidas. Um componente indisponível não vira zero: o peso disponível é renormalizado para a nota condicional e a perda de cobertura permanece registrada.

Cada núcleo requer cobertura informacional ponderada mínima de 70%. Abaixo desse piso, o núcleo e o FinScore ficam indisponíveis. Acima do piso, os pesos dos indicadores válidos são normalizados sem criar dados para os ausentes.

### 7. Pesos estruturais dos núcleos

Os pesos estruturais somam 100% dentro de cada núcleo.

| Núcleo EO | Peso | Núcleo FP | Peso |
|---|---:|---|---:|
| Crescimento da receita | 10% | Capitalização | 25% |
| Margem bruta | 10% | Liquidez corrente | 10% |
| Margem EBIT | 30% | Liquidez seca | 10% |
| Margem líquida | 20% | CCL sobre o ativo | 10% |
| Giro do ativo | 20% | NCG operacional sobre o ativo | 10% |
| Ciclo de conversão de caixa | 10% | Dívida líquida sobre o ativo | 10% |
|  |  | Cobertura de juros | 15% |
|  |  | Composição do endividamento | 10% |

Os pesos mantêm maior participação para geração operacional no EO e capitalização no FP. Margem EBIT, margem líquida e cobertura de juros conectam capacidade operacional à geração de recursos e ao serviço da dívida; liquidez e capital de giro registram a pressão de curto prazo; dívida líquida e composição capturam alavancagem e concentração de vencimentos.

### 8. Componente adaptativo e estabilidade estatística

O cálculo adaptativo examina a estrutura conjunta dos indicadores por análise de componentes principais. Antes da estimação, os indicadores são orientados para que valores maiores representem melhor condição, imputados pela mediana apenas na matriz estatística e padronizados de forma robusta por mediana e desvio absoluto mediano. Quando necessário, utilizam-se intervalo interquartil ou desvio-padrão como escala. Os valores padronizados são limitados a ±3.

São exigidas ao menos três variáveis ativas por núcleo, cada uma com pelo menos duas observações e variabilidade não nula. A estimação considera até dois componentes principais. A importância de cada variável combina o valor absoluto das cargas com a proporção de variância explicada.

A estabilidade é testada em 160 perturbações com desvio de 0,05 e semente reproduzível. A adaptação somente é aceita quando, simultaneamente:

- a distância L1 média entre pesos é igual ou inferior a 0,25;
- a similaridade média de cosseno é igual ou superior a 0,90;
- nenhum peso puro da análise de componentes principais supera 50%.

Quando os critérios são atendidos, os pesos finais combinam 85% dos pesos estruturais e 15% dos pesos adaptativos. Quando há insuficiência, instabilidade ou concentração, o cálculo adaptativo recua integralmente para os pesos estruturais. Com três exercícios, a parcela adaptativa funciona como ajuste controlado de redundância, não como calibração autônoma de risco.

### 9. Formação do FinScore prudencial

As notas temporais são agregadas pelos pesos ativos de cada núcleo e multiplicadas por 10, resultando em EO e FP na escala de 0 a 1.000.

Prejuízos líquidos recorrentes reduzem o núcleo EO:

| Exercícios com margem líquida negativa | Multiplicador do EO |
|---:|---:|
| 0 ou 1 | 1,00 |
| 2 | 0,95 |
| 3 | 0,90 |

Em cada abordagem, estrutural e adaptativa, EO e FP são combinados por média geométrica com participações iguais:

`G = 1.000 × (EO / 1.000)^0,5 × (FP / 1.000)^0,5`

Se um núcleo for zero, o resultado geométrico é zero. Em seguida, o núcleo mais fraco atua como gargalo:

`Resultado pós-gargalo = 75% × G + 25% × mínimo(EO, FP)`

O FinScore prudencial antes dos caps é o menor resultado pós-gargalo entre as abordagens estrutural e adaptativa. A regra mantém visível a fragilidade de um núcleo e impede que a abordagem mais favorável seja selecionada isoladamente.

### 10. Caps prudenciais e faixas de leitura

Os caps são tetos, não descontos fixos. Quando mais de uma regra é acionada, prevalece o menor teto.

| Condição observada no exercício mais recente | Teto do FinScore |
|---|---:|
| Patrimônio líquido negativo | 350 |
| Capitalização inferior a 2% | 500 |
| Capitalização de 2% a menos de 5% | 650 |
| Endividamento exigível igual ou superior a 100% do ativo | 500 |
| Endividamento exigível de 95% a menos de 100% do ativo | 650 |
| Cobertura de juros inferior a 1 vez | 500 |

Os cortes de 125, 250 e 500 pontos integram a análise de sensibilidade. Na camada decisória, 250 pontos funciona como piso de aprovação e 500 pontos como referência para avaliar a necessidade de garantia:

| FinScore | Faixa |
|---:|---|
| abaixo de 125 | Abaixo do primeiro corte de sensibilidade |
| de 125 a 249,99 | Abaixo do piso decisório |
| de 250 a 499,99 | Aprovação sujeita à avaliação de mitigadores |
| 500 ou mais | Sem recomendação de garantia apenas pela faixa |

Essas faixas não são probabilidades de inadimplência nem ratings regulatórios. O resultado **Dados inconsistentes** prevalece sempre que o próprio cálculo estiver marcado como não utilizável para decisão.

### 11. Confiabilidade da informação

A confiabilidade é um índice normativo de completude, reconciliação, evidência, controle de correções, plausibilidade e consistência temporal. Ela varia de 0 a 100%, permanece separada do FinScore e não representa probabilidade estatística.

`Q = 25%C + 20%R + 20%E + 15%K + 15%P + 5%T`

| Componente | Peso | Regra de cálculo |
|---|---:|---|
| Completude (C) | 25% | proporção preenchida das 21 contas nos três exercícios |
| Reconciliação (R) | 20% | `máx(0; 1 − 0,40 × falhas de balanço − 0,15 × falhas de DRE)` |
| Evidência documental (E) | 20% | proporção confirmada das correções pendentes; 100% se não houver pendência |
| Controle de correções (K) | 15% | `exp(−4 × materialidade acumulada das correções)` |
| Plausibilidade (P) | 15% | `máx(0,40; 1 − 0,03 × alertas de viés alto ou crítico)` |
| Consistência temporal (T) | 5% | `máx(0,50; 1 − 0,10 × variações abruptas)` |

A classificação é Alta a partir de 90%, Razoável de 75% a 89,99%, Provisória de 60% a 74,99% e Insuficiente para decisão abaixo de 60%. O limiar de aptidão decisória é 75%, em conjunto com os demais controles de qualidade e alertas bloqueadores. Não há piso adicional de confiabilidade na camada de decisão.

### 12. Cenários determinísticos

Os cenários aplicam choques reproduzíveis sobre o último conjunto de demonstrações. Percentuais negativos representam redução; percentuais positivos representam aumento.

| Variável | Base | Adverso | Severo |
|---|---:|---:|---:|
| Receita líquida | 0% | −10% | −25% |
| Margem EBIT | 0% | −20% | −40% |
| Contas a receber | 0% | +15% | +30% |
| Estoques | 0% | +10% | +20% |
| Caixa | 0% | −15% | −30% |
| Taxa/custo de juros | 0% | +25% | +60% |
| Dívida | 0% | +10% | +25% |
| Patrimônio líquido | 0% | −10% | −25% |
| Passivo circulante total | 0% | +8% | +18% |
| Passivo não circulante total | 0% | +5% | +12% |

O cenário preserva identidades contábeis, reconstrói resultado, impostos e margens e vincula despesa financeira à dívida média e ao choque de taxa quando há abertura suficiente. Dívida histórica parcialmente observável é tratada como limite inferior; informação ausente não é transformada em dívida zero. Necessidades adicionais de financiamento são distribuídas em 70% no curto prazo e 30% no longo prazo. Excesso de fontes é alocado em ativo residual não líquido, evitando melhora artificial de liquidez por aumento automático de caixa.

A ordem esperada é Base maior ou igual a Adverso, que deve ser maior ou igual a Severo. Quebra de monotonicidade é sinal de revisão das premissas ou da reconstrução contábil.

### 13. Simulação e sensibilidade

A análise de sensibilidade utiliza, por padrão, 1.000 trajetórias e semente reproduzível. A amplitude de cada conta parte da maior variação anual absoluta observada e é limitada ao intervalo de 5% a 35%. São avaliadas abordagens com choques independentes e correlacionados, com persistência temporal comum de 60% e persistência idiossincrática de 25%.

Trajetórias que violam identidades contábeis, sinais, subtotais ou definição do score são rejeitadas. O processo admite até 40 tentativas por trajetória requerida e monitora taxa de rejeição de 25% como limite de qualidade da simulação. São apurados percentis, dispersão, diferenças entre trajetórias aceitas e rejeitadas, choques máximos e frequências abaixo de 125, 250 e 500 pontos.

Uma frequência simulada abaixo de determinado corte é condicionada às amplitudes, correlações e regras de reconstrução. Ela mede sensibilidade do FinScore e não deve ser interpretada como PD.

### 14. Evidências complementares

O Serasa permanece separado do cálculo. A pontuação externa é comparada ao FinScore para identificar convergência ou divergência, mas não há soma, média ou conversão automática. A marcação de restrição grave é feita pelo analista com base na consulta documental, permanece destacada no parecer e requer exame explícito pela alçada; isoladamente, não altera o FinScore nem a categoria de decisão.

O índice Springate é calculado por exercício como contraste de insolvência:

`S = 1,03 × (CCL/AT) + 3,07 × (EBIT/AT) + 0,66 × (Resultado antes de IR/CSLL/PC) + 0,40 × (Receita/AT)`

Resultado inferior a 0,862 sinaliza distress; resultado igual ou superior indica ausência desse sinal no teste. Componente ausente ou denominador materialmente nulo torna o índice não calculável. O Springate não altera o FinScore.

A leitura Fleuriet é simplificada conforme a abertura de contas disponível:

- `ACO = Clientes + Estoques`;
- `PCO = Fornecedores + Obrigações tributárias CP + Obrigações trabalhistas CP`;
- `NCG = ACO − PCO`;
- `CDG = Passivo Não Circulante + Patrimônio Líquido − Ativo Não Circulante`;
- `Saldo de Tesouraria = CDG − NCG`.

CDG positivo com saldo de tesouraria não negativo indica cobertura da NCG por fontes permanentes. CDG positivo, NCG positiva e saldo negativo indicam dependência de financiamento de curto prazo. CDG não positivo indica insuficiência de fontes permanentes para o ativo não circulante. Essa leitura também não altera pontuação, pesos, gargalo, caps ou simulações.

### 15. Critérios de decisão de crédito

A decisão utiliza o FinScore prudencial e o status de aptidão produzido pelos controles de qualidade. Serasa, Springate e Fleuriet são evidências suplementares: não são somados à pontuação e não criam um quarto resultado.

| Resultado | Critérios | Efeito e encaminhamento |
|---|---|---|
| **Dados inconsistentes** | FinScore indisponível; base não apta para cálculo; resultado provisório ou não utilizável; confiabilidade inferior a 75%; correção pendente; ou alerta bloqueador. | Não há base suficiente para aprovar ou recusar a operação. O parecer discrimina cada pendência, seu impacto e a correção necessária. A análise deve ser refeita após o saneamento. |
| **Não aprovar** | Resultado apto para decisão e FinScore prudencial inferior a 250 pontos. | A capacidade econômico-financeira ficou abaixo do piso decisório. Nova análise depende de mudança material nas demonstrações e nos indicadores que formam a pontuação. |
| **Aprovar** | Resultado apto para decisão e FinScore prudencial igual ou superior a 250 pontos. | Recomendação favorável, com ou sem garantia, sujeita à alçada, formalização e controles cadastrais e jurídicos da instituição. |

A camada decisória converte a pontuação e a aptidão nas três categorias acima. O piso de 250 pontos coincide com um dos cortes empregados na análise de sensibilidade. Os diagnósticos complementares qualificam a recomendação de garantia, os covenants e a análise da alçada, sem substituir o FinScore como eixo principal.

### 16. Evidências suplementares, garantias e covenants

O score Serasa é comparado ao FinScore sem integração aritmética. Divergências de até 100 pontos são classificadas como baixas; de mais de 100 a 200, moderadas; de mais de 200 a 300, relevantes; e acima de 300, elevadas. A direção informa se a evidência externa é mais favorável ou mais desfavorável. Restrição grave registrada na consulta permanece destacada para exame da alçada.

Springate e Fleuriet utilizam as mesmas demonstrações que alimentam o FinScore. Springate inferior a 0,862 registra sinal de distress. Na leitura Fleuriet, dependência de financiamento de curto prazo, insuficiência de fontes permanentes ou estrutura atípica são sinais de atenção sobre o capital de giro. Resultado não calculável permanece como ausência de evidência complementar, sem bloquear por si só o FinScore.

A recomendação de garantia é acionada quando uma aprovação apresenta pelo menos um dos seguintes sinais observáveis:

- FinScore entre 250 e 499,99 pontos;
- cap prudencial acionado;
- FinScore inferior a 250 no cenário severo;
- Serasa materialmente mais desfavorável, restrição grave registrada, Springate com sinal de distress ou fragilidade indicada pelo Fleuriet.

O sistema não presume percentual de cobertura nem valor de garantia. Modalidade, valor realizável, cobertura e exequibilidade jurídica devem ser definidos pela alçada após avaliação do colateral. Na ausência dos sinais acima, a aprovação é apresentada sem recomendação de garantia decorrente desta análise.

Os covenants decorrem dos indicadores que originaram a ressalva. Sinal de distress direciona o acompanhamento do Springate, EBIT e capital circulante líquido; fragilidade Fleuriet direciona NCG, CDG e saldo de tesouraria; caps direcionam capitalização, endividamento exigível ou cobertura de juros; divergência no Serasa direciona atualização da consulta e revisão pela alçada. O parecer não cria limites numéricos ou periodicidades sem base na política da instituição.

### 17. Conteúdo e leitura do parecer

O parecer apresenta identificação, fontes, qualidade dos dados, indicadores, formação do FinScore, caps, cenários, sensibilidade, Serasa, Springate, Fleuriet, decisão, garantias, riscos, diligências e monitoramento. A metodologia acompanha o documento em anexo. O conjunto é dimensionado para 7 a 14 páginas, conforme a quantidade de evidências e ocorrências materiais.

Fatos observados, valores calculados, premissas e conclusões permanecem distinguíveis. Todo motivo impeditivo deve ser associado ao efeito analítico e à ação de saneamento. Alertas informativos permanecem visíveis sem serem apresentados como impedimentos. A redação não altera valores, regras, bloqueios ou decisão.

Antes da contratação, a alçada confirma demonstrações, perímetro contábil, eventos extraordinários, exposição consolidada, grupo econômico, restrições externas, documentação, garantias e concentração. Alterações em contas, curvas, pesos, caps, limiares de confiabilidade ou critérios de decisão requerem registro de versão, validação independente e aprovação de governança.
