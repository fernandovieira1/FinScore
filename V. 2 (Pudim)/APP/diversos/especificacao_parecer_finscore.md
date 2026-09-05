# Especificação funcional do parecer de crédito FinScore

**Versão da especificação:** 1.0  
**Estado:** baseline funcional para implementação  
**Escopo:** parecer de crédito, contrato de informações, governança, redação, renderização e validação  
**Fora do escopo desta versão:** alteração do cálculo do FinScore, dos critérios decisórios ou do conteúdo metodológico

## 1. Finalidade

Esta especificação define o parecer de crédito apoiado pelo FinScore. O documento deve organizar dados contábeis, resultados calculados, qualidade da informação, cenários e evidências suplementares em uma análise clara, reproduzível e verificável.

O FinScore é um suporte quantitativo à análise. A recomendação produzida por suas regras não substitui a manifestação do analista, a política de crédito, os demais instrumentos de governança nem a decisão da alçada competente.

O parecer deve servir simultaneamente a:

1. analistas de crédito e risco;
2. gestores e comitês de crédito;
3. auditorias internas e externas;
4. consultores, estatísticos e economistas encarregados de revisão independente;
5. equipes técnicas responsáveis pela reprodução e manutenção do processo.

## 2. Fontes e autoridade

### 2.1 Fontes examinadas

| Código | Fonte | Função | SHA-256 na consolidação |
|---|---|---|---|
| `FONTE-CALCULO` | `MODELO/algoritmos/Versao 20/FinScore_V2_0_20.ipynb` | Definições e execução do cálculo | `347423c0cc4ea39bd43f927a6670e179e612a1f624e531d7a948bb5b547da74f` |
| `FONTE-METODO` | `APP/app_front/content/metodologia_pudim_2_0_20.md` | Explicação metodológica incorporada ao parecer | `824492f733176967c6c7fd4f8ad6037e74cb74807d221db30a65469e402bbca1` |
| `FONTE-REQUISITOS` | `APP/diversos/prompt parecer finscore.txt` | Requisitos funcionais, editoriais, técnicos e de teste | `7918808e6cbc003e02b04079d8ee68c3a0e921da390f4efa998ad3b4f81221ae` |
| `FONTE-POLITICA` | `APP/app_front/services/credit_policy.py` | Recomendação, mitigadores e encaminhamentos atuais | Conforme a versão do código em execução |
| `FONTE-CONTRATO` | `APP/app_front/finscore_v2/contracts.py` | Contrato público da saída do motor | Versão de contrato registrada na execução |

O arquivo `prompt parecer finscore.txt` permanece preservado como material de origem. Esta especificação passa a ser a referência consolidada para as etapas de aperfeiçoamento do parecer.

### 2.2 Ordem de autoridade

Em caso de divergência, deve ser observada a seguinte ordem:

1. o motor e o contrato do FinScore governam cálculos, dados derivados, indicadores, notas, núcleos, caps, cenários e diagnósticos;
2. a política de crédito aprovada governa a conversão dos resultados em recomendação, garantia e encaminhamentos;
3. as decisões humanas registradas governam manifestação do analista e decisão da alçada;
4. esta especificação governa organização, apresentação, rastreabilidade e redação do parecer;
5. a rotina de redação não pode alterar nenhuma das camadas anteriores.

Qualquer alteração de fórmula, curva, peso, cap, limiar, categoria ou regra decisória exige processo próprio de validação. Não pode ser introduzida por modificação editorial do parecer.

## 3. Separação de responsabilidades

### 3.1 Metodologia FinScore

Compreende exclusivamente a preparação dos dados, os controles de qualidade, os cálculos contábeis, os indicadores, as notas, a composição temporal, os núcleos EO e FP, as abordagens estrutural e adaptativa, o gargalo, os caps prudenciais, o FinScore prudencial, os cenários e as análises de sensibilidade descritas nas fontes metodológicas.

### 3.2 Política de recomendação

Converte o resultado apto em uma das três recomendações permitidas:

1. **Aprovar**;
2. **Não aprovar**;
3. **Dados inconsistentes**.

Os critérios atualmente implementados permanecem como baseline até que haja alteração formal da política. Seus limiares e gatilhos devem possuir versão, origem e vigência próprias, sem serem apresentados como inferência da rotina de redação.

### 3.3 Governança humana

O processo deve preservar separadamente:

| Registro | Responsável | Função |
|---|---|---|
| Recomendação FinScore | Regras determinísticas | Conclusão produzida a partir do cálculo e da política configurada |
| Manifestação do analista | Analista responsável | Julgamento profissional fundamentado, inclusive divergências e informações externas ao escopo do FinScore |
| Decisão da alçada | Autoridade competente | Deliberação institucional final |
| Divergência de governança | Analista ou alçada | Justificativa quando a manifestação ou decisão divergir da recomendação FinScore |

Uma informação posterior não deve sobrescrever a anterior. Todos os registros devem manter autor, data, estado e justificativa.

### 3.4 Redação variável

A redação variável interpreta fatos previamente estruturados. Ela não deve:

- recalcular contas ou indicadores;
- escolher ou alterar a recomendação;
- criar fatos, documentos, valores ou exercícios;
- converter score em probabilidade de inadimplência;
- criar modalidade, cobertura ou valor de garantia;
- criar limite, periodicidade, prazo de cura ou consequência de covenant;
- transformar alerta em bloqueio ou recomendação em decisão institucional;
- ocultar ausência, correção, ressalva ou divergência.

## 4. Vocabulário controlado

### 4.1 Termos públicos preferenciais

| Termo | Uso |
|---|---|
| FinScore prudencial | Pontuação final após as regras prudenciais aplicáveis |
| Recomendação FinScore | Resultado determinístico: Aprovar, Não aprovar ou Dados inconsistentes |
| Manifestação do analista | Posição profissional registrada pelo analista |
| Decisão da alçada | Decisão institucional final |
| Dados reportados | Valores recebidos da fonte de origem |
| Dados utilizados | Valores efetivamente empregados nos cálculos |
| Dados derivados | Valores obtidos por identidade ou fórmula definida |
| Evidência externa | Informação proveniente de fonte distinta das demonstrações; no escopo atual, o Serasa |
| Evidência suplementar | Serasa e diagnósticos auxiliares usados sem integração aritmética ao FinScore |
| Diagnóstico complementar | Springate ou Fleuriet calculado a partir das demonstrações |
| Pendência decisória | Ocorrência que impede o uso do resultado na recomendação |
| Alerta não bloqueador | Ocorrência relevante que não impede, isoladamente, a recomendação |
| Monitoramento recomendado | Indicador ou fato sugerido para acompanhamento, sem obrigação contratual presumida |
| Covenant | Obrigação contratual definida pela instituição, com métrica e consequência documentadas |

### 4.2 Termos restritos ao ambiente técnico

Os termos abaixo não devem aparecer no corpo, nos anexos destinados ao analista nem nas mensagens funcionais do parecer:

- inteligência artificial;
- modelo de linguagem;
- OpenAI ou nome do fornecedor;
- nome ou identificador do modelo de geração;
- prompt;
- temperatura;
- esforço de raciocínio;
- tokens;
- nomes internos de versões do sistema;
- nomes internos de rotinas, classes ou módulos.

Essas informações podem existir em telemetria e registros técnicos de acesso restrito. Não integram o dossiê funcional do analista.

### 4.3 Convenções editoriais

1. O título da metodologia deve ser apenas **Metodologia**.
2. Não utilizar a expressão “metodologia vigente”.
3. A numeração deve ser decimal e sequencial.
4. Não duplicar título de seção e título do conteúdo incorporado.
5. Valores ausentes devem ser apresentados como “Não informado”, “Não disponível” ou “Não calculado”, conforme a natureza.
6. Ausência não deve ser representada como zero.
7. FinScore, Serasa, Springate e Fleuriet não podem ser somados, ponderados ou convertidos entre si.
8. Cenários e frequências de simulação não são previsões nem probabilidades de inadimplência.

## 5. Contrato funcional de informações

### 5.1 Estrutura canônica pretendida

O objeto de auditoria deve, em etapa posterior, seguir esta organização lógica:

```json
{
  "schema_versao": "1.0",
  "analise_id": null,
  "identificacao": {
    "tomador": {},
    "concedente": {},
    "operacao": {},
    "periodos": {
      "cadastral": {},
      "analisado": {},
      "divergencias": []
    }
  },
  "governanca": {
    "recomendacao_finscore": {},
    "manifestacao_analista": null,
    "decisao_alcada": null,
    "divergencias": []
  },
  "dados": {
    "reportados": [],
    "propostos": [],
    "utilizados": [],
    "derivados": [],
    "rastreabilidade": []
  },
  "qualidade": {
    "status": null,
    "confiabilidade": null,
    "componentes": [],
    "alertas": [],
    "bloqueios": [],
    "correcoes": []
  },
  "finscore": {},
  "cenarios": {},
  "evidencias_suplementares": {
    "serasa": {},
    "springate": [],
    "fleuriet": []
  },
  "achados": [],
  "metadados_funcionais": {},
  "metadados_tecnicos_restritos": {}
}
```

O contrato detalhado, os tipos e as validações serão definidos na etapa 2. A presente estrutura fixa apenas a divisão de responsabilidades.

### 5.2 Regras transversais de dados

1. Usar `null` para dado indisponível no contrato estruturado.
2. Manter valores numéricos como números; formatação brasileira pertence ao renderizador.
3. Informar unidade, exercício, fonte e natureza sempre que aplicáveis.
4. Usar listas tipadas para séries anuais, achados, alertas, correções e evidências.
5. Preservar valor reportado, proposto e utilizado em campos distintos.
6. Registrar a regra e a justificativa de toda transformação.
7. Manter o período cadastral separado do período efetivamente analisado.
8. Registrar divergência temporal sem corrigir ou substituir períodos silenciosamente.
9. Não encaminhar para redação campos cadastrais que não sejam necessários à interpretação.
10. Inserir nome, CNPJ e identificação do concedente deterministicamente na renderização.

## 6. Inventário de campos

### 6.1 Campos já disponíveis

| Grupo | Campos ou estruturas | Origem atual | Uso no parecer |
|---|---|---|---|
| Tomador | nome e CNPJ | metadados da sessão | Identificação determinística |
| Período analisado | ano inicial, ano final e exercícios efetivos | sessão e dados utilizados | Escopo e séries temporais |
| Serasa | score, data, restrição grave, divergência | sessão e saída do motor | Evidência externa separada |
| Dados contábeis | reportados, utilizados e derivados | contrato FinScore | Tabelas, qualidade e análise |
| Qualidade | status, aptidão, confiabilidade e componentes | contrato FinScore | Uso decisório e limitações |
| Auditoria | correções, quarentenas, alertas e rastreabilidade | contrato FinScore | Pendências e reprodução |
| Indicadores | índices, notas e motivos não calculáveis | contrato FinScore | Análise temporal e formação dos núcleos |
| FinScore | núcleos, estrutural, adaptativo, gargalo, caps e prudencial | contrato FinScore | Síntese quantitativa |
| Cenários | base, adverso, severo e monotonicidade | contrato FinScore | Estresse e resiliência |
| Simulação | resumos, percentis, sensibilidade e diagnósticos | contrato FinScore | Análise de incerteza, quando válida |
| Diagnósticos | Springate e Fleuriet por exercício | contrato FinScore | Evidências suplementares |
| Recomendação | categoria, fundamentos, bloqueios e mitigadores | política atual | Recomendação FinScore |
| Metadados | processamento, semente, número de simulações e hashes | contrato FinScore | Auditoria funcional ou técnica, conforme classificação |

### 6.2 Campos ainda inexistentes ou incompletos

| Campo | Estado | Origem recomendada | Efeito de ausência |
|---|---|---|---|
| Identificador persistente da análise | Inexistente | Repositório transacional de análises | Impede referência única e histórico completo; não altera o score |
| Concedente: nome e CNPJ | Inexistente | Configuração institucional | Exibir “Não informado” durante transição; não altera o score |
| Natureza da operação | Inexistente | Formulário da operação | Campo contextual opcional; não altera o score |
| Finalidade da operação | Inexistente | Formulário da operação | Campo contextual opcional; não altera o score |
| Valor e moeda | Inexistente | Formulário da operação | Campo contextual opcional; não altera o score nem gera precificação |
| Prazo da operação | Inexistente | Formulário da operação | Campo contextual opcional; não altera o score |
| Período cadastral | Inexistente | Cadastro ou documentação de origem | Registrar ausência ou divergência; não substituir o período calculado |
| Manifestação do analista | Inexistente | Fluxo de governança | Parecer pode ser emitido como análise FinScore, sem manifestação humana registrada |
| Decisão da alçada | Inexistente | Fluxo de governança | Não usar “decisão final” até o registro da alçada |
| Justificativa de divergência | Inexistente | Fluxo de governança | Obrigatória se manifestação ou decisão divergir da recomendação |
| Detalhes da garantia | Inexistente | Avaliação institucional do colateral | Não presumir modalidade, cobertura, valor realizável ou exequibilidade |
| Parâmetros de covenant | Inexistente | Política e instrumento contratual | Tratar apenas como monitoramento recomendado |

Campos contextuais da operação não devem ser promovidos a critérios de consistência ou recomendação sem alteração formal da política.

## 7. Estrutura do parecer

O documento deve seguir esta ordem, sem títulos duplicados:

1. **Identificação da análise e da operação**  
   Tomador, concedente, campos da operação, períodos, data e identificador.

2. **Sumário executivo**  
   Recomendação FinScore, pontuação, aptidão, confiabilidade, principais fundamentos, limitações e indicação de garantia.

3. **Escopo e qualidade da informação**  
   Fontes, exercícios, dados reportados e utilizados, correções, alertas, bloqueios e limitações.

4. **Análise econômico-operacional**  
   Receita, margens, produtividade, ciclo financeiro, trajetória e achados do núcleo EO.

5. **Análise financeira e patrimonial**  
   Capitalização, liquidez, capital de giro, endividamento, serviço da dívida, trajetória e achados do núcleo FP.

6. **Formação e interpretação do FinScore**  
   Núcleos, abordagens, gargalo, contribuições, cobertura informacional, caps e resultado prudencial.

7. **Estresse, sensibilidade e evidências suplementares**  
   Cenários, simulações válidas, Serasa, Springate, Fleuriet e divergências relevantes.

8. **Tese de crédito e posição na governança**  
   Recomendação FinScore, fundamento, garantia, monitoramento, manifestação do analista e decisão da alçada quando disponíveis.

9. **Riscos, diligências e monitoramento**  
   Pontos fortes comprovados, riscos prioritários, validações pendentes e indicadores recomendados para acompanhamento.

10. **Conclusão da análise**  
    Síntese coerente com os dados e indicação explícita de que a decisão institucional compete à alçada.

11. **Anexo 1 — Metodologia**  
    Conteúdo fixo, versionado e carregado de fonte única.

12. **Anexo 2 — Informações da análise**  
    Informações necessárias à reprodução e à auditoria, sem expor tecnologia de redação ou nomes internos.

### 7.1 Extensão e paginação

O parecer completo, incluindo anexos, deve conter de 7 a 14 páginas. A extensão decorre da materialidade das evidências, não de preenchimento textual artificial.

Distribuição indicativa:

- corpo analítico: 4 a 7 páginas;
- metodologia: 3 a 5 páginas;
- informações de auditoria: 1 a 2 páginas.

Se o documento exceder o limite, devem ser reduzidas repetições e detalhes secundários antes de remover evidências materiais. Se ficar abaixo do mínimo, não se deve inventar análise: tabelas auditáveis e explicações metodológicas pertinentes têm precedência sobre expansão retórica.

## 8. Conteúdo fixo, calculado, informado e variável

| Natureza | Exemplos | Responsável | Pode ser alterado pela redação? |
|---|---|---|---|
| Informado | nome, CNPJ, finalidade, valor, prazo, período cadastral | Usuário ou configuração institucional | Não |
| Observado | contas reportadas e Serasa | Fonte de dados | Não |
| Calculado | derivados, índices, notas, núcleos, caps e cenários | Motor FinScore | Não |
| Determinístico | recomendação, bloqueios e gatilhos configurados | Política de recomendação | Não |
| Governança | manifestação e decisão da alçada | Responsável humano | Não |
| Fixo | ressalvas, metodologia e rótulos | Fonte versionada e renderizador | Não |
| Variável | interpretação, síntese e transições textuais | Rotina de redação | Sim, dentro das evidências autorizadas |

Todo conteúdo variável deve referenciar achados estruturados. Dados, tabelas, recomendação, garantia, pendências, metodologia e informações da execução devem ser montados deterministicamente.

## 9. Livro de evidências

Antes da redação, o sistema deve produzir achados com identificador estável no contexto da análise. O formato detalhado será definido na etapa 2, mas cada achado deve conter ao menos:

| Campo | Finalidade |
|---|---|
| `achado_id` | Referência da afirmação no parecer |
| `categoria` | Força, risco, alerta, bloqueio, limitação ou divergência |
| `natureza` | Observado, calculado, derivado, hipótese ou evidência externa |
| `titulo` | Descrição objetiva |
| `evidencias` | Campo, valor, exercício, unidade e origem |
| `efeito_metodologico` | Nota, peso, núcleo, cap ou controle relacionado |
| `impacto_credito` | Consequência analítica sustentada pelos dados |
| `bloqueia_decisao` | Indicação reproduzida do contrato ou da política |
| `providencia` | Saneamento ou diligência, quando aplicável |

Um indicador não pode ser classificado como principal risco apenas por apresentar valor baixo. A classificação deve considerar trajetória, nota, peso, contribuição e efeito efetivo no núcleo ou no FinScore.

## 10. Matriz consolidada de requisitos

Legenda de natureza: `INF` informado, `OBS` observado, `CALC` calculado, `DET` determinístico, `GOV` governança, `FIX` fixo, `VAR` redação variável.

| ID | Requisito | Fonte | Natureza | Destino | Validação de aceite |
|---|---|---|---|---|---|
| `REQ-ID-001` | A análise deve possuir identificador único e imutável | Requisito de auditoria | DET | Corpo e auditoria | Duas análises não compartilham identificador |
| `REQ-ID-002` | Tomador e CNPJ devem ser inseridos deterministicamente | Requisito funcional | INF | Corpo | Texto reproduz exatamente os campos validados |
| `REQ-ID-003` | Concedente deve vir de configuração institucional ou permanecer não informado | Requisito funcional | INF | Corpo | Ausência não cria dado nem bloqueio do FinScore |
| `REQ-ID-004` | Período cadastral e analisado devem permanecer separados | Requisito funcional | INF/CALC | Corpo e auditoria | Divergência é exibida sem substituição silenciosa |
| `REQ-OP-001` | Natureza, finalidade, valor, prazo e moeda são campos contextuais | Requisito funcional | INF | Corpo | Campos ausentes aparecem como não informados |
| `REQ-OP-002` | Campos contextuais não alteram score ou recomendação atual | Diretriz do usuário | DET | Política | Teste prova invariância da recomendação |
| `REQ-DAD-001` | Valores reportados, propostos, utilizados e derivados devem ser distintos | Metodologia | OBS/CALC | Corpo e auditoria | Rastreabilidade preserva cada estágio |
| `REQ-DAD-002` | Dado ausente deve permanecer nulo | Metodologia | OBS | Todos | Nenhuma ausência é convertida em zero |
| `REQ-DAD-003` | Séries devem conter exercício e unidade | Requisito de auditoria | OBS/CALC | Todos | Validador rejeita registro temporal incompleto |
| `REQ-DAD-004` | Correção deve registrar regra, justificativa, confiança e impacto | Metodologia | CALC | Qualidade e auditoria | Registro reproduz campos do contrato |
| `REQ-QUA-001` | Aptidão para cálculo e para recomendação devem ser exibidas separadamente | Metodologia | CALC | Corpo | Os dois estados constam do sumário ou da qualidade |
| `REQ-QUA-002` | Bloqueios devem informar motivo, impacto e saneamento | Diretriz do usuário | DET | Corpo | Todo bloqueio possui os três elementos |
| `REQ-QUA-003` | Alertas não bloqueadores não podem ser apresentados como impedimentos | Metodologia | DET/VAR | Corpo | Texto conserva a classificação de origem |
| `REQ-QUA-004` | Resultado provisório não pode sustentar recomendação decisória | Metodologia | DET | Recomendação | Categoria resultante é Dados inconsistentes |
| `REQ-FIN-001` | FinScore não pode ser apresentado como PD ou rating regulatório | Metodologia | FIX/VAR | Corpo e anexo | Busca de termos e avaliação semântica |
| `REQ-FIN-002` | EO, FP, estrutural, adaptativo, gargalo, caps e prudencial devem permanecer distintos | Metodologia | CALC | Corpo e auditoria | Tabelas usam os campos originais corretos |
| `REQ-FIN-003` | Principais limitadores devem considerar nota, peso e contribuição | Requisito funcional | CALC/VAR | Corpo | Achado referencia efeito metodológico |
| `REQ-CEN-001` | Cenários devem ser tratados como hipóteses, não previsões | Metodologia | CALC/VAR | Corpo | Ressalva e vocabulário compatíveis |
| `REQ-CEN-002` | Monotonicidade deve ser verificada e sua violação explicitada | Metodologia | CALC/DET | Corpo e auditoria | Caso não monotônico gera achado e ressalva |
| `REQ-CEN-003` | Frequência de simulação não pode ser tratada como inadimplência | Metodologia | VAR/FIX | Corpo | Texto não emprega equivalência com PD |
| `REQ-SUP-001` | Serasa deve permanecer separado do FinScore | Metodologia | OBS/CALC | Corpo | Não há soma, média ou conversão |
| `REQ-SUP-002` | Springate e Fleuriet devem ser identificados como diagnósticos derivados | Metodologia | CALC | Corpo | Não são rotulados como fontes externas |
| `REQ-SUP-003` | Evidência suplementar isolada não altera a categoria atual | Política atual | DET | Recomendação | Testes preservam categoria com alteração isolada |
| `REQ-REC-001` | As categorias permitidas são Aprovar, Não aprovar e Dados inconsistentes | Diretriz do usuário | DET | Corpo | Enumeração rejeita qualquer quarta categoria |
| `REQ-REC-002` | A recomendação deve ser calculada antes da redação | Política atual | DET | Todos | Resposta variável não contém campo capaz de alterá-la |
| `REQ-REC-003` | Dados inconsistentes deve explicar ausência de base confiável e saneamento | Diretriz do usuário | DET/VAR | Corpo | Todos os impedimentos aparecem com providência |
| `REQ-REC-004` | Não aprovar deve indicar fundamentos e hipótese de nova análise | Diretriz do usuário | DET/VAR | Corpo | Conclusão não se limita ao rótulo |
| `REQ-REC-005` | Aprovar deve indicar se há recomendação de garantia | Diretriz do usuário | DET | Corpo | Sumário e tese apresentam o mesmo estado |
| `REQ-GOV-001` | Recomendação FinScore não deve ser denominada decisão final da instituição | Diretriz de governança | FIX/VAR | Corpo | Terminologia controlada é respeitada |
| `REQ-GOV-002` | Manifestação do analista e decisão da alçada devem ser campos separados | Diretriz de governança | GOV | Corpo e auditoria | Persistência independente, com autor e data |
| `REQ-GOV-003` | Divergência deve exigir justificativa sem sobrescrever registros | Diretriz de governança | GOV | Auditoria | Histórico conserva todas as posições |
| `REQ-GAR-001` | Garantia recomendada deve possuir gatilhos determinísticos versionados | Política atual | DET | Corpo e auditoria | Cada recomendação referencia regra e evidência |
| `REQ-GAR-002` | Não presumir modalidade, valor, cobertura ou exequibilidade | Diretriz do usuário | DET/VAR | Corpo | Ausência permanece explícita |
| `REQ-COV-001` | Sem parâmetro institucional, usar monitoramento recomendado | Diretriz de governança | DET/VAR | Corpo | Texto não cria obrigação contratual |
| `REQ-COV-002` | Covenant exige métrica, limite, fonte, periodicidade e consequência registrados | Diretriz de governança | INF/GOV | Corpo e auditoria | Ausência de qualquer componente impede rótulo de covenant definido |
| `REQ-NAR-001` | Redação deve usar somente achados autorizados | Requisito de auditoria | VAR | Corpo | Cada seção referencia achados existentes |
| `REQ-NAR-002` | Quantidades de forças, riscos e pendências devem refletir os dados | Diretriz editorial | VAR | Corpo | Listas vazias são permitidas quando justificadas |
| `REQ-NAR-003` | Seções devem ter extensão proporcional à materialidade | Diretriz editorial | VAR | Corpo | Não há mínimo uniforme por seção |
| `REQ-NAR-004` | O texto deve distinguir fato, cálculo, hipótese e interpretação | Requisito funcional | VAR | Corpo | Avaliação semântica em casos de regressão |
| `REQ-NAR-005` | Termos técnicos de geração não podem aparecer no dossiê funcional | Diretriz do usuário | FIX/VAR | Corpo e anexos funcionais | Lista de termos proibidos não é encontrada |
| `REQ-DOC-001` | A metodologia deve ser carregada de uma única fonte versionada | Requisito funcional | FIX | Anexo 1 | Conteúdo e hash correspondem à fonte selecionada |
| `REQ-DOC-002` | Tabelas devem preservar números, anos, unidades e formatação brasileira | Requisito editorial | FIX/CALC | Corpo e anexos | Comparação com o objeto estruturado |
| `REQ-DOC-003` | Gráficos só devem ser incluídos quando melhorarem a interpretação | Requisito editorial | DET | Corpo | Gráfico possui dados, título, unidade, fonte e análise relacionada |
| `REQ-DOC-004` | O documento completo deve ter entre 7 e 14 páginas | Diretriz do usuário | DET | PDF | Contagem realizada no PDF final |
| `REQ-DOC-005` | Extensão não deve ser atingida por conteúdo inventado ou repetitivo | Diretriz editorial | VAR/DET | Corpo | Avaliação de repetição e cobertura material |
| `REQ-AUD-001` | O dossiê deve permitir reprodução com hashes, versões e parâmetros funcionais | Requisito de auditoria | DET | Auditoria | Identificadores correspondem à execução |
| `REQ-AUD-002` | Metadados da tecnologia de redação devem ficar em registro técnico restrito | Diretriz do usuário | DET | Registro interno | Não aparecem no PDF ou JSON funcional |
| `REQ-AUD-003` | Falha da redação não deve apagar cálculo ou contexto preparado | Requisito operacional | DET | Aplicação | Retry usa a mesma análise e mantém os dados |

## 11. Critérios de aceite das próximas etapas

### 11.1 Contrato de informações

- Tipos explícitos e campos sem mapas genéricos nos pontos críticos.
- Validação de `null`, unidade, exercício e enumerações.
- Separação física entre dossiê funcional e telemetria técnica.
- Conversão reproduzível a partir do contrato atual do FinScore.

### 11.2 Síntese e redação

- Todo número narrado existe no objeto de origem.
- Todo risco material referencia ao menos um achado.
- Todos os bloqueios são mencionados com motivo, impacto e providência.
- A recomendação não pode ser alterada pelo texto.
- Ausência legítima de risco, força ou pendência permite lista vazia.
- Não há repetição substancial entre sumário, tese e conclusão.

### 11.3 Documento e auditoria

- Tabelas coincidem com os dados estruturados após arredondamento definido.
- Gráficos preservam exercícios, unidades e fontes.
- Anexo metodológico corresponde integralmente à fonte aprovada.
- PDF contém de 7 a 14 páginas.
- Dossiê funcional não contém termos técnicos restritos.
- Identificador, datas, versões e hashes permitem localizar a execução.

### 11.4 Casos mínimos de regressão

1. recomendação Aprovar sem garantia;
2. recomendação Aprovar com garantia;
3. recomendação Não aprovar;
4. Dados inconsistentes por baixa confiabilidade;
5. Dados inconsistentes por alerta bloqueador;
6. alerta não bloqueador;
7. indicador não calculável;
8. divergência entre período cadastral e período analisado;
9. cenário não monotônico;
10. Serasa mais desfavorável sem mudança isolada de categoria;
11. Springate ou Fleuriet não calculável;
12. ausência de campos contextuais da operação;
13. divergência entre recomendação, analista e alçada;
14. falha do serviço de redação com preservação do dossiê.

## 12. Decisões de negócio pendentes

Estas decisões não impedem a modelagem do contrato, mas devem ser formalizadas antes da conclusão de todas as etapas:

| ID | Decisão | Recomendação de trabalho |
|---|---|---|
| `PEND-001` | Titularidade e aprovação formal dos cortes de 250 e 500 pontos | Registrar como política de recomendação versionada |
| `PEND-002` | Titularidade da regra de confiabilidade mínima de 75% | Manter alinhada ao status de aptidão do motor e documentar a origem |
| `PEND-003` | Fonte oficial de concedente e CNPJ | Configuração institucional administrada, não campo repetido por cliente |
| `PEND-004` | Obrigatoriedade de natureza e finalidade da operação | Manter opcionais até existir política institucional específica |
| `PEND-010` | Política de retenção do dossiê e da telemetria | Definir prazo, acesso, descarte e requisitos regulatórios da instituição |

### 12.1 Decisões consolidadas na implementação

| ID original | Decisão aplicada |
|---|---|
| `PEND-005` | Sequência transacional persistente `FS-AAAA-NNNNNN` |
| `PEND-006` | Reprodução funcional no Anexo 2 e telemetria em tabela restrita separada |
| `PEND-007` | PDF, Markdown e JSON funcional; DOCX permanece fora do escopo atual |
| `PEND-008` | Até dois gráficos comparativos, incluídos somente quando há variação material |
| `PEND-009` | Histórico acrescentado sem sobrescrita, comprovante por hash e perfil específico para alçada |

## 13. Mapeamento para as etapas do projeto

1. **Especificação consolidada:** este documento.
2. **Contrato estruturado:** tipos, validações e adaptador do resultado atual.
3. **Governança:** recomendação, manifestação, alçada e divergências.
4. **Livro de evidências:** geração determinística dos achados.
5. **Schema narrativo:** seções e itens referenciando achados.
6. **Prompt de execução:** instruções enxutas, sem regras duplicadas.
7. **Validação final:** consistência factual, decisória, semântica e editorial.
8. **Documento:** tabelas, gráficos, anexos e paginação.
9. **Persistência:** identificador, histórico, assinaturas e dossiê.
10. **Testes e avaliações:** regressão determinística, qualidade narrativa e revisão especializada.

## 14. Controle de alterações

| Versão | Alteração |
|---|---|
| 1.0 | Consolidação inicial dos requisitos, separação entre metodologia, política, governança e redação, inventário de campos, matriz de requisitos e critérios de aceite |
| 1.1 | Registro das etapas 4 a 10, decisões de documento e persistência, matriz de regressão e protocolo de validação especializada |
