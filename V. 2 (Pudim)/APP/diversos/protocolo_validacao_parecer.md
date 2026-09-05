# Protocolo de validação do parecer de crédito

## 1. Finalidade

Este protocolo orienta a homologação antes da liberação de uma versão do parecer. A revisão
combina testes automatizados, conferência de amostras e manifestação independente das áreas
responsáveis pela metodologia e pela governança de crédito.

## 2. Amostra mínima

A amostra deve abranger os 14 casos registrados em
`APP/tests/parecer_acceptance_matrix.json`, acrescentando pelo menos:

1. uma empresa com três exercícios integralmente preenchidos;
2. uma empresa com ausência material de contas;
3. uma empresa com prejuízo recorrente;
4. uma empresa com diferença relevante entre FinScore e Serasa;
5. uma análise com manifestação do analista divergente;
6. uma análise com decisão de alçada divergente.

Valores, documentos ou identificadores reais devem seguir as regras de acesso e proteção de
dados da instituição.

## 3. Revisões independentes

1. **Crédito:** coerência da tese, clareza dos motivos, providências e alcance da recomendação.
2. **Contabilidade:** contas, derivações, períodos, unidades e conciliações.
3. **Metodologia quantitativa:** curvas, pesos, composição temporal, gargalo, caps, cenários e
   diagnósticos suplementares.
4. **Auditoria ou controles internos:** rastreabilidade, versões, hashes, histórico, autoria,
   segregação do dossiê funcional e integridade dos anexos.
5. **Jurídico e segurança, quando aplicável:** alcance das garantias, registros eletrônicos,
   perfis de acesso, retenção e proteção das informações.

## 4. Critérios de aceite

- a pontuação, a aptidão, a confiabilidade e a recomendação coincidem com o cálculo;
- todos os bloqueios apresentam motivo, impacto e providência;
- alertas informativos não são apresentados como impedimentos;
- nenhum número variável carece de evidência referenciada;
- Serasa permanece separado, e Springate e Fleuriet permanecem diagnósticos suplementares;
- cenários são tratados como hipóteses condicionais, sem caráter preditivo;
- garantia não recebe modalidade, valor ou cobertura não informados;
- posições do FinScore, do analista e da alçada permanecem separadas;
- o anexo metodológico coincide integralmente com a fonte versionada;
- o PDF possui de 7 a 14 páginas e mantém tabelas legíveis;
- o JSON funcional não contém tecnologia de redação ou telemetria operacional;
- falha de redação preserva o cálculo, o contrato estruturado e a ocorrência técnica;
- eventos assinados não podem ser alterados ou substituídos sem novo evento.

## 5. Registro da homologação

Cada revisor registra versão examinada, casos conferidos, ressalvas, evidências da revisão,
data e responsável. A liberação requer ausência de falha crítica e tratamento formal das
ressalvas materiais. Mudanças em dados, fórmulas, curvas, pesos, caps, recomendação, anexos ou
validações exigem nova execução dos testes e nova revisão das áreas afetadas.
