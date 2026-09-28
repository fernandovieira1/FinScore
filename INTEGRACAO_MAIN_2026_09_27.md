# Integração da branch 3 à main — 27/09/2026

Integração de `3_auditoria_pareceres` (`2f2653dde`) à `main` (`139e7e423`), que já continha a branch 2 pelo PR #7. O merge preserva os dois históricos.

## Conciliação

- Mantidos o layout de tabelas, os três modos de PDF, a aplicabilidade setorial do Springate e as regras de cap da branch 3.
- Preservadas as validações de referências e datas da main, sem reescrita silenciosa de afirmações sem lastro. Respostas inválidas continuam sujeitas ao limite de três tentativas.
- Compatibilizados os parâmetros personalizados de política e os dois formatos de notas: resumo por linha e proveniência por célula. O parecer apresenta notas resumidas; o dossiê conserva os dados integrais.
- Texto de faixas acompanha os limites configurados. Mantidas as reconciliações patrimoniais e a identificação do período efetivamente analisado na capa.
- Atualizada a assinatura de cache do parecer para invalidar documentos de versões anteriores.

## Validação

- Suíte completa: **205 testes, zero falhas, zero erros, zero testes ignorados**, em 128,161 segundos.
- Regressões específicas de compatibilidade repetidas após os ajustes finais: **9 testes aprovados**.
- Sintaxe dos arquivos Python alterados e ausência de conflitos residuais verificadas.
- `git diff --check` sem problemas.

Nesta integração foram executados testes automatizados. Os três smoke tests no navegador e os PDFs no Desktop documentados em `AUDITORIA_PARECERES_2026_09_26.md` correspondem à branch 3 antes deste merge e não foram repetidos nesta etapa.
