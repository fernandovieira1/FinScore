# Motor FinScore Pudim 2.0.14

Esta versão mantém os cálculos metodológicos da 2.0.13 e restaura, na 2.0.14,
a exportação auditável integral existente na 2.12. O notebook de referência é
`MODELO/algoritmos/Versao 14/FinScore_V2_14.ipynb`.

## Organização

- `core.py`: funções e constantes extraídas mecanicamente do congelado;
- `engine.py`: orquestração sobre um `pandas.DataFrame` em memória;
- `contracts.py`: contrato público tipado e validação de runtime;
- `__init__.py`: API pública do pacote.

`core.py` é gerado por `APP/scripts/extract_finscore_v2.py`. Não o edite
manualmente. O gerador exclui leitura automática de caminhos, exportação,
`print`, `display`, gráficos e execução automática de simulações/autotestes.

## Uso isolado

```python
import pandas as pd
from finscore_v2 import executar_finscore

dados = pd.read_excel("empresa.xlsx", sheet_name="lancamentos")
resultado = executar_finscore(
    dados,
    serasa_score=700,
    serasa_data="2026-07-23",
    executar_simulacoes=True,
    numero_simulacoes=1000,
    semente=20260723,
)
```

O pacote não depende do Streamlit e não altera o estado de sessão do app.

## Entrada contábil

A fronteira de importação está em `services/io_validation.py` e usa o mesmo
parser do motor. O formato aceito possui a aba `lancamentos`, três exercícios
e as colunas `ano` mais as 21 contas de `core.PRIMARY`.

A importação preserva os valores reportados:

- célula vazia continua `NaN` e não é convertida para zero;
- texto inválido continua disponível para auditoria e gera ocorrência crítica;
- colunas adicionais são ignoradas com aviso;
- planilhas da versão Brigadeiro recebem erro específico;
- a aba `lancamentos` é obrigatória.

O app disponibiliza um modelo vazio gerado por `gerar_modelo_planilha`, com
abas de lançamentos, dicionário e instruções de preenchimento.

## Análise de contas

A aba `Processo → Análise → Dados Contábeis` consome diretamente as tabelas do
contrato e separa:

- contas reportadas, preservadas da origem;
- contas usadas pelo motor após correções controladas;
- contas derivadas, que não são lançamentos da planilha;
- qualidade, correções, alertas de viés e rastreabilidade.

As contas são exibidas nas linhas e os três exercícios nas colunas. `Ausente`
e `R$ 0,00` são representações distintas.

## Tabelas da análise

A aba `Processo → Análise → Tabelas` apresenta exclusivamente DataFrames do
contrato Pudim, organizados em cinco grupos:

- índices observados, notas e motivos de indisponibilidade;
- composição temporal e contribuições ao score;
- diagnóstico, pesos e cargas de PCA separados por núcleo;
- caps, intervalos de incerteza e redundância prudencial;
- cenários determinísticos, Monte Carlo, sensibilidade e amplitudes.

A view não recalcula índices ou scores. Em resultados bloqueados, orienta a
revisão das ocorrências em Dados Contábeis; quando as simulações estão
desabilitadas, preserva os cenários determinísticos e informa a ausência do
Monte Carlo.

## Gráficos da análise

A aba `Processo → Análise → Gráficos` usa apenas contas e resultados do
contrato Pudim. As visualizações são agrupadas em:

- estrutura patrimonial, capital de giro, resultado e dívida;
- mapa de notas observadas e composição temporal;
- núcleos EO/FP, consolidação do FinScore e pesos PCA por núcleo;
- cenários determinísticos e distribuições Monte Carlo independente e
  correlacionada.

Os gráficos não reproduzem fórmulas do motor. Um resultado bloqueado não gera
visualizações analíticas; sem simulações, os cenários determinísticos continuam
visíveis e a ausência do Monte Carlo é informada explicitamente.

## Scores da análise

A aba `Processo → Análise → Scores` substitui os campos Brigadeiro de score
bruto/ajustado pelos resultados nativos do Pudim:

- FinScore prudencial e scores estrutural/adaptativo pós-gargalo;
- núcleos EO e FP em ambos os métodos;
- confiabilidade, status de uso e aptidão para decisão;
- score pré-cap, cap aplicável, divergência e regras acionadas;
- Serasa apresentado separadamente como evidência externa.

Quando o gate bloqueia o cálculo, a aba não exibe scores artificiais e orienta
a revisão das ocorrências em Dados Contábeis.

## Exportação da análise

Ao final de `Processo → Análise`, o expansor `Exportar análise completa`
disponibiliza um arquivo XLSX gerado em memória. Ele reproduz as 33 abas, ordem,
colunas e formatação operacional da exportação 2.12, agora sob a versão 2.0.14.
O download é opcional e não altera os resultados mantidos na sessão.

## Contrato de saída

O retorno é um `FinScoreOutput`, dicionário tipado com versão de contrato
independente da versão metodológica:

- `contrato_versao`: versão da interface (`1.0`);
- `modelo`: versão/hash da metodologia e parâmetros de reprodutibilidade;
- `status_qualidade`: gates de cálculo e decisão;
- `confiabilidade`: índice separado do FinScore;
- `finscore_observado`: scores e núcleos, vazio quando o cálculo é bloqueado;
- tabelas `df_*`: dados, auditoria, índices, PCA, cenários e simulações;
- `df_serasa`: evidência externa, sem média automática com o FinScore.

`executar_finscore` valida o contrato antes de retornar. Integrações também
podem chamar `validar_contrato(resultado)` ao atravessar uma fronteira, como o
serviço que grava o resultado no `session_state`.

O `services/finscore_service.py` é essa fronteira no Streamlit. Ele chama o
motor Pudim e acrescenta apenas aliases temporários necessários enquanto as
views são migradas. Os aliases estão listados em
`resultado["compatibilidade_legado"]`; conceitos sem equivalente metodológico,
como `finscore_bruto` e o antigo `df_pca`, não são fabricados.

Parâmetros operacionais aceitos pelo serviço:

- `FINSCORE_EXECUTAR_SIMULACOES`: `1` ou `0` (padrão `1`);
- `FINSCORE_SIMULACOES`: mínimo 100 quando habilitado (padrão 1000);
- `FINSCORE_SEMENTE`: semente inteira (padrão 20260723).

Invariantes principais:

- bases reportada e analítica contêm exatamente três exercícios;
- resultado bloqueado não recebe score artificial;
- resultado calculado contém índices, notas e consolidação temporal;
- `apto_decisao=True` exige `apto_calculo=True`;
- quando habilitadas, as duas séries de Monte Carlo contêm a quantidade
  solicitada de simulações aceitas.

## Testes

Na pasta `APP`:

```bash
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
```
