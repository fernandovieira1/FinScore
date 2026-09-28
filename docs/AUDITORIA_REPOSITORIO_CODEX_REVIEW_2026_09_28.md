# Auditoria do repositório de revisão

## Resultado

O branch de trabalho permanece `4_auditoria_baseline_controles`, no commit
`6319cc6348638869cd5470dce444e39c014af33a`. As alterações solicitadas estão
nesse commit. Não foi necessário mesclar código nem substituir arquivos do app.

## Origem da divergência

`.codex-review` é um repositório Git independente dentro do projeto, não um
branch do repositório principal. Seu branch é `1_parecer_rastreavel`.
O commit `6319cc634` incluiu essa pasta como um gitlink (modo `160000`),
apontando para `c23c6f251`, sem configuração correspondente em `.gitmodules`.
O repositório interno está em `c842b160b`; essa diferença produzia a indicação
de modificação no repositório principal.

O repositório interno não tinha alterações locais, arquivos novos não ignorados
ou conflitos pendentes.

## Comparação do código

O único commit do repositório interno ausente por identidade no histórico do
branch de trabalho é `c842b160b` (ajuste das tabelas do PDF). Sua alteração é
idêntica à do commit `46c59817b`, já incorporado no histórico do branch atual:

- `git cherry HEAD c842b160b` indica `- c842b160b` (alteração equivalente já presente).
- Ambos os patches têm o identificador estável
  `28a74cb0f55571c215c40a31bd09ebb31c7e4773`.
- A formatação das tabelas permanece em `app_front/pdf/export_pdf.py`.

Não há mudanças exclusivas de código a recuperar de `.codex-review`.
Os índices Git não contêm entradas em conflito, e a busca nos arquivos Python,
CSS e Markdown do app e dos testes não encontrou marcadores de merge.

## Alterações solicitadas preservadas

- Gráfico de faixas no PDF e classificação em quatro faixas.
- Critérios de aprovação qualificada e explicações na metodologia e no Anexo 1.
- Download padrão “Parecer + Anexo”.
- Melhorias na correção de narrativas e validação das referências temporais.
- Diagnóstico das ocorrências de validação.
- Menu lateral `#E8F9F9` e rodapé `V.2.7.20 (Out/26)`.

## Correção da estrutura Git

- Removido somente o gitlink de `.codex-review` do índice principal.
- Adicionado `/.codex-review/` ao `.gitignore`.
- Pasta interna, arquivos e histórico preservados no disco.
- Nenhum branch criado, excluído ou trocado; nenhum commit ou push efetuado.
- O worktree externo já existente e destacado em `9f16ad4be` foi preservado.

A remoção do gitlink e a regra de ignore estão preparadas no índice para serem
registradas juntas no próximo commit. A pasta interna pode continuar aparecendo
como repositório aberto no editor; isso não representa um branch adicional do projeto.

## Validação final

- Suíte completa: **238 testes aprovados**, em 166,873 segundos.
- Código do app e testes permanecem idênticos ao commit `6319cc634`.
- `git diff --check` e `git diff --cached --check`: sem erros.
- A limpeza do vínculo Git não modificou o código nem os dados da aplicação.
