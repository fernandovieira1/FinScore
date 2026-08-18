# PUDIM V3 STANDALONE — LEIAME

Arquivo único e autocontido para comparar, lado a lado, o **motor V2.0.13
oficial** (o seu, intocado) com a **camada V3 do laboratório** (as quatro
correções que ainda se mostraram necessárias). Feito para rodar no seu PC,
sem rede, sem banco de dados e sem nenhum caminho do laboratório.

---

## 1. O que há dentro do arquivo

`pudim_v3_standalone.py` tem três seções:

| Seção | Conteúdo | Origem |
|---|---|---|
| **SEÇÃO 1** | Motor V2.0.13 **verbatim** — extração literal das células de definição do `FinScore_V2_13.ipynb`. Nenhuma linha alterada (verificado byte a byte contra o notebook). | Seu |
| **SEÇÃO 2** | Camada V3: correções #3, #4, #8 e #9, todas implementadas **por fora** do motor (wrappers). O código da SEÇÃO 1 nunca é chamado de forma diferente nem modificado. | Laboratório |
| **SEÇÃO 3** | Executor/comparador: varre a pasta de planilhas, roda os dois fluxos, imprime a tabela e grava o CSV. | Laboratório |

A coluna **V2.0.13** da saída é o seu motor rodando o fluxo determinístico
das células 64–66 do notebook (gate de qualidade → derive → índices → notas
→ scores → caps prudenciais), sem Monte Carlo/Serasa — o mesmo score
prudencial determinístico do notebook. A camada V3 **nunca** altera essa
coluna.

## 2. As quatro correções da camada V3

| # | Correção | Efeito observado na base de calibração |
|---|---|---|
| **#3** | **Gate de materialidade (pré-escoragem).** Empresa abaixo do piso de materialidade (ativo total < R$ 100.000 **ou** receita líquida < R$ 50.000 no último exercício) vira "não classificável" com motivo legível, em vez de receber um número. | *Modo Serviços RH*: 350,00 → N/A (ativo total de R$ 15,76). *Flammers*: receita zero → N/A com motivo. |
| **#4** | **Ausência legítima ≠ nota zero.** Empresa sem passivo não circulante **e** sem dívida financeira de LP tem "composição do endividamento" tratado como não-aplicável (peso redistribuído pela cobertura), em vez de nota 0. | *Fornax* +63,77 · *MegaAdm* +34,44 · *Super-G* +26,29 (B→A) · *Mooven* +16,03 (D→C). |
| **#8** | **Recusa sempre com motivo legível.** Quando o motor devolve NaN sem mensagem, a camada deriva o motivo das coberturas reais do próprio motor. | *Flammers*: "cobertura do núcleo EO 0,25 < 0,70" em vez de NaN mudo. |
| **#9** | **Tolerância de validação unificada.** Identidade contábil Ativo = PC + PNC + PL verificada na entrada com a **mesma** tolerância relativa do motor (`BALANCE_TOLERANCE`) — vira aviso legível na tabela, nunca exceção sem contexto. | Planilha de teste com balanço aberto ganha "AVISO #9" com o valor exato da violação. |

**Itens do V3 antigo que NÃO estão mais aqui** (absorvidos pelo seu
V2.0.13): sandbox de trajetória (a nova regra temporal resolve o teto),
reescala 1000 (o teto teórico nativo agora chega a 1000) e o toggle de teto
de curvas 95→100 (hoje teria efeito *oposto* — reduziria scores — e foi
removido).

## 3. Requisitos

- Python ≥ 3.10
- `pip install pandas numpy openpyxl scikit-learn matplotlib`
  (scikit-learn e matplotlib são importados pelo próprio motor do notebook —
  o mesmo ambiente que já roda o `FinScore_V2_13.ipynb` serve.)

## 4. Como rodar

```bash
python pudim_v3_standalone.py <pasta_com_xlsx>
```

- `<pasta_com_xlsx>`: pasta com as planilhas `.xlsx` das empresas — formato
  de 21 contas + coluna `ano`, na aba **"lancamentos"**. Se omitida, usa a
  pasta atual.
- Planilhas fora desse formato são **ignoradas com aviso** ao final (nada
  quebra).

## 5. Saída

1. **Tabela no terminal**:
   `empresa | score V2.0.13 | faixa | score V3 | faixa | Δ | o que mudou e por quê`
2. **CSV** `comparativo_v213_v3.csv`, gravado dentro da pasta de entrada:
   separador `;`, decimais com vírgula e BOM UTF-8 — abre direto no Excel
   pt-BR, com 4 casas decimais nos scores.
3. **Resumo final**: quantas empresas escoradas, quantas alteradas por cada
   correção, e a lista de arquivos ignorados com o motivo.

## 6. Garantias

- **Motor intocado**: a SEÇÃO 1 é o V2.0.13 literal; os scores oficiais são
  reproduzidos sem mudança (na base de calibração: Callamarys 394,43 ·
  Fornax 854,01 · MegaAdm 845,81 · Mobicloud 897,64 · etc.).
- **Nenhum número inventado**: tudo é computado ao vivo, a cada execução,
  a partir das planilhas apontadas.
- **Diferença nenhuma além das quatro correções**: a coluna V3 é exatamente
  o mesmo fluxo + #3/#4/#8/#9.
- **Sem efeitos colaterais**: o script só grava o CSV de saída (e um
  bootstrap temporário mínimo, apagado logo em seguida, usado apenas para
  satisfazer a guarda de auto-carga da célula 49 do notebook — ele não
  influencia nenhum score).
