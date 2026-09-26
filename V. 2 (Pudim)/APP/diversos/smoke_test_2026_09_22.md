# Revisão e smoke tests de 22 de setembro de 2026

Base remota conferida: `5ebfd87fe44131b079e082c0e20fb56eee969810`.
Alterações anteriores revisadas: `9351fc5`.
Branch local numerada: `1_parecer_rastreavel`.

A revisão corrigiu duas falhas na apresentação das evidências: estatísticas de
simulação sem validade explícita deixaram de ser exibidas como utilizáveis, e
cenários com monotonicidade reprovada passaram a registrar limitação sem inferir
resiliência. A suíte completa passou com 152 testes e 13 subtestes, em 122,87 s.

O inventário usou o importador real do Streamlit nos arquivos de
`V. 2 (Pudim)/MODELO/dados_teste`: 48 arquivos físicos, 10 ZIPs íntegros e 191
membros internos. As 35 ocorrências aceitas pelo importador correspondem a 18
entradas únicas; 17 são duplicatas dentro dos ZIPs.

Dos 18 arquivos aceitos, 15 concluíram motor, simulações e contrato estruturado;
dois falharam; um depende de mapear os exercícios posicionais 1, 2, 3 para anos
de calendário. O smoke usou 100 simulações por abordagem e semente 20260723,
em processos isolados. Não substitui a execução padrão de 1000 trajetórias.

- T006, `15Log Road Transporte Rodoviario.xlsx`: residual negativo de 3.921 no
  passivo circulante de 2022 interrompe a reconstrução nas simulações. Sem
  simulações, o cálculo diagnóstico conclui; o fluxo completo continua reprovado.
- T015, `7ornax - Flammers Participacoes.xlsx`: cenários BASE, ADVERSO e SEVERO
  retornam NaN e a validação lança RuntimeError, também sem simulações.
- T024, `DADOS_V2_PUDIM_bp-dre4.xlsx`: não foi atribuído calendário arbitrário.

Nos 15 sucessos técnicos, a política retornou sete vezes `Aprovar` e oito vezes
`Dados inconsistentes`. Sucesso técnico não equivale a liberação de crédito.
O código do motor que lança as duas falhas não mudou em relação à base remota.

AppTest executou o entrypoint real: 10 rotas renderizaram; 15 telas de parecer
preservaram o contrato e apresentaram erro controlado ao acionar a geração sem
serviço configurado; dois testes do botão Calcular FinScore mostraram os erros
reais do motor de forma controlada. Foi usado SQLite de teste. Os dois últimos
testes utilizaram cadastro sintético declarado apenas para alcançar o tratamento
de exceção, sem produzir texto ou PDF. Não houve mock do serviço de redação.

Nenhum PDF final foi gerado: falta configuração do serviço de redação no checkout.
Serasa e data de consulta reais também não estão comprovados nos arquivos, e a
interface exige esses campos. Os PDFs controlados de verificações anteriores do
exportador não foram entregues como pareceres deste lote.

Evidências e scripts completos foram mantidos em
`review-output/smoke-20260922` (ignorado pelo Git), e a documentação DOCX será
salva no Desktop. O ambiente isolado usou dependências instaladas para o teste,
incluindo Streamlit 1.64.0, pandas 3.0.6 e NumPy 2.5.3; não representa uma
reprodução integral de dependências fixadas de implantação.
