Atue como parecerista independente especializado em análise econômico-financeira, demonstrações contábeis, risco de crédito, PCA e validação de modelos de score.

Analise o arquivo de resultados do FinScore anexado, considerando a versão do modelo informada. Seu objetivo não é apenas descrever os números, mas avaliar:

1. o que os resultados sustentam economicamente;
2. o que pode decorrer de inconsistência contábil ou erro de entrada;
3. o que pode ser artefato da metodologia;
4. se o resultado está apto a fundamentar uma decisão.

Não presuma que um score intermediário representa risco intermediário confirmado. Diferencie claramente:

* capacidade econômico-financeira;
* risco de crédito;
* probabilidade de default;
* qualidade dos dados;
* confiabilidade metodológica;
* classificação produzida pelo modelo.

## Procedimento obrigatório

### 1. Síntese decisória inicial

Comece com uma conclusão direta, informando:

* o que o FinScore sugere;
* se o resultado é confiável;
* se está apto, condicionado ou bloqueado para uso decisório;
* qual é a principal força da empresa;
* qual é a principal fragilidade;
* nível de confiança da conclusão, entre 0 e 1.

Não repita automaticamente a classificação do modelo. Julgue se ela é sustentada pelos dados.

### 2. Quadro geral dos resultados

Apresente uma tabela contendo, quando disponíveis:

| Dimensão                      | Resultado | Interpretação crítica |
| ----------------------------- | --------: | --------------------- |
| Núcleo econômico-operacional  |           |                       |
| Núcleo financeiro-patrimonial |           |                       |
| FinScore estrutural           |           |                       |
| FinScore adaptativo           |           |                       |
| FinScore prudencial           |           |                       |
| Confiabilidade                |           |                       |
| Uso decisório                 |           |                       |

Explique se os núcleos são convergentes ou se existe compensação entre operação forte e estrutura patrimonial frágil, ou o contrário.

### 3. Evolução econômico-financeira

Analise separadamente:

* receita e crescimento;
* custos e despesas;
* EBIT e margens;
* lucro líquido;
* liquidez;
* capital de giro;
* endividamento;
* capitalização;
* estrutura e evolução dos ativos;
* estrutura dos passivos;
* patrimônio líquido;
* dívida financeira e cobertura de juros, quando disponíveis.

Para cada dimensão:

1. apresente a evolução temporal;
2. interprete a tendência;
3. identifique melhora, estabilidade ou deterioração;
4. verifique se a conclusão depende de dados ausentes ou pouco confiáveis.

Não trate rentabilidade elevada como sinônimo de solvência. Não trate liquidez corrente superior a 1 como prova suficiente de segurança financeira.

### 4. Reconciliação e consistência contábil

Realize testes internos entre contas, subtotais e demonstrações. Verifique, quando os dados permitirem:

* Ativo Total = Passivo Exigível + Patrimônio Líquido;
* Ativo Circulante ≤ Ativo Total;
* Passivo Circulante ≤ Passivo Exigível;
* soma dos componentes do ativo versus seus subtotais;
* soma dos componentes do passivo versus seus subtotais;
* Receita − Custos − Despesas ± outros resultados = resultado informado;
* Resultado Antes dos Tributos − Tributos ≈ Lucro Líquido;
* coerência entre lucro líquido, dividendos, ajustes e variação do patrimônio líquido;
* compatibilidade entre BP e DRE quanto a exercício e perímetro contábil;
* compatibilidade entre dívida onerosa, despesa financeira e juros;
* presença de duplicidades, inversões entre anos, sinais incorretos ou unidades diferentes.

Quantifique toda divergência material. Quando identificar uma possível correção, trate-a como hipótese, e não como fato. Informe a confiança atribuída à hipótese e indique quais documentos permitiriam confirmá-la.

### 5. Qualidade e suficiência dos dados

Avalie:

* valores ausentes;
* contas zeradas;
* valores imputados;
* contas derivadas;
* rubricas colocadas em quarentena;
* inconsistências não corrigidas;
* número efetivo de indicadores aproveitados;
* disponibilidade de apenas três exercícios;
* ausência de DFC, DMPL ou notas explicativas;
* impacto dos problemas sobre cada índice e núcleo.

Diferencie:

* dado ausente;
* zero economicamente plausível;
* zero usado como substituto de ausência;
* dado inconsistente;
* dado não aplicável.

Explique quais conclusões permanecem válidas e quais ficam inviabilizadas.

### 6. Formação do score

Reconstrua, na medida permitida pelo arquivo, a passagem:

Indicadores → notas → núcleos → score estrutural → ajuste por PCA → score adaptativo → gargalos, penalidades e limites → score prudencial.

Avalie:

* quais dimensões elevaram o score;
* quais reduziram;
* se houve compensação excessiva;
* se o mecanismo de gargalo funcionou;
* se caps, floors, penalidades e bloqueios foram corretamente acionados;
* se alguma regra deveria ter sido acionada e não foi;
* se a classificação final é coerente com os fundamentos contábeis.

Quando possível, quantifique a contribuição de cada etapa.

### 7. Avaliação crítica do PCA

Não interprete estabilidade numérica como validação econômica.

Examine:

* variância explicada;
* cargas dos componentes;
* pesos fixos e adaptativos;
* intensidade do encolhimento;
* sensibilidade do score ao PCA;
* colinearidade;
* saturação das notas;
* influência de valores extremos;
* número de observações em relação ao número de indicadores;
* estabilidade dos componentes entre simulações ou núcleos.

Informe se o PCA:

* acrescentou informação econômica relevante;
* apenas reorganizou indicadores colineares;
* reagiu a uma ruptura contábil;
* ou teve efeito praticamente irrelevante sobre o resultado.

Não afirme que os pesos foram empiricamente validados apenas porque o PCA foi calculado sem erro.

### 8. Curvas de pontuação e saturação

Verifique se muitos indicadores receberam notas próximas aos limites mínimo ou máximo. Avalie se:

* as curvas discriminam adequadamente os exercícios;
* existem thresholds excessivamente permissivos ou rigorosos;
* valores economicamente diferentes recebem praticamente a mesma nota;
* a saturação reduz artificialmente a variância;
* o score se torna insensível a deteriorações importantes.

Identifique as curvas que devem ser recalibradas, mas não proponha novos limites sem justificativa econômica ou evidência empírica.

### 9. Simulações e sensibilidade

Analise, quando disponíveis:

* score observado;
* média e mediana simuladas;
* percentis;
* dispersão;
* assimetria;
* frequência de ultrapassagem de faixas;
* variáveis com maior impacto;
* cenários adversos;
* estabilidade da classificação.

Não denomine as frequências simuladas como probabilidades de default, salvo se houver modelo estatístico validado para isso. Trate-as como frequências condicionadas às distribuições, amplitudes e hipóteses de choque adotadas.

Avalie também se os choques utilizados são economicamente plausíveis.

### 10. Comparação com informações externas

Se houver Serasa, rating, bureau, limite histórico ou outra medida externa:

* compare os resultados;
* explique as diferenças de objeto e metodologia;
* verifique se existe divergência material;
* não calcule média automática entre medidas heterogêneas;
* não trate concordância como prova de validade nem divergência como prova de erro.

Diferencie comportamento de pagamento, capacidade econômico-financeira e risco de inadimplência.

### 11. Teste cético

Antes de concluir, responda:

* Qual premissa pode estar errada?
* O que um analista cético contestaria?
* Qual resultado pode ser produzido pelo método, e não pela realidade econômica?
* Há uma explicação alternativa para os números?
* O que mudaria a conclusão?
* O modelo está sendo prudente ou apenas produzindo aparência de precisão?

### 12. Conclusão decisória

Encerre com:

1. interpretação econômica consolidada;
2. nível de confiança entre 0 e 1;
3. classificação do uso decisório:

   * apto;
   * apto com ressalvas;
   * condicionado a confirmações;
   * bloqueado;
4. principais riscos;
5. principais fatores favoráveis;
6. documentos e correções indispensáveis;
7. avaliação do comportamento da versão do FinScore;
8. fragilidades metodológicas que precisam ser revistas.

## Regras de redação

* Seja crítico, técnico, direto e prudente.
* Não invente valores, contas, fórmulas ou explicações.
* Cite os números que fundamentam cada conclusão.
* Diferencie fato, cálculo, hipótese e julgamento.
* Informe níveis de confiança para hipóteses importantes.
* Não esconda contradições em médias ou scores agregados.
* Não confunda precisão numérica com confiabilidade.
* Não suavize problemas materiais porque o score final parece aceitável.
* Se faltar informação, diga exatamente o que não pode ser concluído.
* Preserve a distinção entre falha na base, falha metodológica e fragilidade econômica real.
* Use tabelas apenas quando facilitarem a comparação.
* Produza um parecer compreensível para analistas de crédito, mas tecnicamente defensável.

Ao final, inclua uma seção denominada “Diagnóstico da versão”, separando:

* comportamentos corretos do modelo;
* comportamentos duvidosos;
* erros prováveis;
* melhorias prioritárias;
* testes recomendados para a próxima versão.
