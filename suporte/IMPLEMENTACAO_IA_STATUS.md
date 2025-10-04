# Status da Implementação - Integração IA Crítica Assistida

## ✅ CONCLUÍDO

### 1. Componentes Base
- ✅ `components/schemas.py` - Atualizado com campos `acao` e `obs` no `ReviewSchema`
- ✅ `components/llm_client.py` - Atualizado para suportar campo `acao` no JSON de resposta
- ✅ `components/policy_engine.py` - Já existia e está funcional

### 2. Views - Análise
- ✅ Nova aba "Críticas & Curadoria" adicionada em `views/analise.py`
- ✅ Função `_render_criticas_curadoria_tab()` implementada com:
  - Filtro por status (todos/accepted/needs_revision/draft)
  - Listagem formatada de críticas
  - Visualização de insight, riscos e ações
  - Display de observações do analista

### 3. Views - Parecer  
- ✅ `views/parecer.py` - Já implementado com:
  - Integração com `policy_engine`
  - Pré-veredito determinístico
  - Botão para redação final (placeholder)
  - Exposição de `policy_inputs` no session_state

## ⚠️ PENDENTE - CRÍTICO

### 4. Implementação das "Caixinhas de Crítica" nos Artefatos

**IMPORTANTE:** As caixinhas de crítica foram REMOVIDAS anteriormente conforme solicitação do usuário. 
A nova implementação deve ser feita de forma LIMPA e MODULAR.

#### Arquivos que precisam ser modificados:

**A) `views/graficos.py`**
- Adicionar após cada gráfico principal (5-8 artefatos selecionados):
  - Receita, Custos e EBITDA
  - Capital de Giro e Liquidez
  - Indicadores de Liquidez
  - Estrutura de Capital (DL/EBITDA)
  - Indicadores de Rentabilidade
  - Eficiência Operacional
  - PCA - Variância Explicada
  - PCA - Scores

**B) `views/tabelas.py`**
- Adicionar após cada tabela principal:
  - Tabela de Liquidez
  - Tabela de Endividamento/Estrutura
  - Tabela de Rentabilidade
  - Tabela de Eficiência
  - PCA - Loadings
  - PCA - Scores
  - PCA - Top Índices

#### Padrão de Implementação:

```python
# Após renderizar cada artefato principal
from components.llm_client import call_review_llm

# Exemplo para gráfico de Receita
def render_receita_total(df):
    # ... código existente de renderização ...
    
    # NOVA SEÇÃO: Crítica IA (Opcional - ativada por flag)
    if st.session_state.get("enable_ai_review", True):
        _render_artifact_review_box(
            artifact_id="grafico_receita_total",
            title="Receita, Custos e EBITDA",
            df=df,
            key_metrics=["r_Receita_Total", "r_Custos", "r_Lucro_Liquido"]
        )
```

### 5. Helper Function para Caixinhas

Criar função auxiliar em `views/graficos.py` e `views/tabelas.py`:

```python
def _render_artifact_review_box(artifact_id, title, df, key_metrics):
    """
    Renderiza caixinha de crítica IA para um artefato específico.
    
    Args:
        artifact_id: ID único do artefato (ex: "grafico_receita_total")
        title: Título do artefato (ex: "Receita, Custos e EBITDA")
        df: DataFrame com os dados do artefato
        key_metrics: Lista de colunas-chave para incluir no resumo
    """
    ss = st.session_state
    out = ss.get("out", {})
    
    # Construir mini_ctx
    mini_ctx = {
        "empresa": (ss.get("meta") or {}).get("empresa", "N/A"),
        "anos_disponiveis": list(df.get("ano", [])) if df is not None else [],
        "finscore_ajustado": out.get("finscore_ajustado"),
        "classificacao_finscore": out.get("classificacao_finscore"),
        "serasa": out.get("classificacao_serasa"),
    }
    
    # Construir dados_resumo com métricas-chave
    dados_resumo = {}
    if df is not None and not df.empty:
        for metric in key_metrics:
            if metric in df.columns:
                valores = df[metric].dropna()
                if len(valores) > 0:
                    dados_resumo[metric] = {
                        "ultimo": float(valores.iloc[-1]),
                        "media": float(valores.mean()),
                    }
    
    # Construir artifact_meta
    artifact_meta = {
        "artifact_id": artifact_id,
        "title": title,
        "mini_ctx": mini_ctx,
        "dados_resumo": dados_resumo,
        "review_kind": "raw"  # ou "indices" dependendo do tipo
    }
    
    # Salvar metadata
    ss.setdefault("artifacts_meta", {})
    ss.artifacts_meta[artifact_id] = artifact_meta
    
    # Renderizar UI
    st.markdown(f"#### 💬 Crítica da IA — {title}")
    
    col_btn, col_content = st.columns([1, 2])
    
    with col_btn:
        if st.button("🤖 Gerar crítica", key=f"btn_{artifact_id}", help="Analisar este artefato com IA"):
            with st.spinner("Consultando IA..."):
                try:
                    review = call_review_llm(artifact_id, artifact_meta)
                    ss.setdefault("reviews", {})
                    ss.reviews[artifact_id] = review.model_dump()
                    st.success("✅ Crítica gerada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar crítica: {e}")
    
    with col_content:
        if artifact_id in ss.get("reviews", {}):
            rev = ss.reviews[artifact_id]
            
            # Exibir insight
            sinal_emoji = {"positivo": "🟢", "neutro": "🟡", "negativo": "🔴"}.get(rev.get("sinal", "neutro"), "🟡")
            st.markdown(f"{sinal_emoji} **{rev.get('insight', '')}**")
            
            # Exibir riscos e ações em colunas
            if rev.get("riscos") or rev.get("acao"):
                col_risk, col_action = st.columns(2)
                
                with col_risk:
                    if rev.get("riscos"):
                        st.caption("⚠️ Riscos:")
                        for risco in rev.get("riscos", []):
                            st.caption(f"• {risco}")
                
                with col_action:
                    if rev.get("acao"):
                        st.caption("✅ Ações:")
                        for acao in rev.get("acao", []):
                            st.caption(f"• {acao}")
            
            # Botões de ação
            col1, col2, col3, col4 = st.columns(4)
            
            if col1.button("✓ Aceitar", key=f"ok_{artifact_id}", help="Marcar como aceita"):
                rev["status"] = "accepted"
                st.rerun()
            
            if col2.button("⚠ Revisar", key=f"rev_{artifact_id}", help="Marcar para revisão"):
                rev["status"] = "needs_revision"
                st.rerun()
            
            if col3.button("✗ Descartar", key=f"del_{artifact_id}", help="Remover crítica"):
                del ss.reviews[artifact_id]
                st.rerun()
            
            if col4.button("🔄 Regerar", key=f"regen_{artifact_id}", help="Gerar nova crítica"):
                with st.spinner("Regenerando..."):
                    try:
                        review = call_review_llm(artifact_id, artifact_meta)
                        ss.reviews[artifact_id] = review.model_dump()
                        st.success("✅ Crítica regenerada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
            
            # Observação do analista
            with st.expander("📝 Adicionar observação"):
                note_key = f"obs_{artifact_id}"
                obs_value = st.text_area(
                    "Observação do analista:",
                    value=rev.get("obs", ""),
                    key=note_key,
                    height=100
                )
                rev["obs"] = obs_value
```

## 📋 PRÓXIMOS PASSOS

### Opção 1: Implementação Manual
1. Copiar a função `_render_artifact_review_box` acima
2. Adicionar em `views/graficos.py` e `views/tabelas.py`
3. Identificar os 5-8 artefatos principais
4. Adicionar chamada após cada renderização desses artefatos

### Opção 2: Implementação Automatizada (Recomendado)
Criar um decorador ou wrapper que injeta automaticamente a caixinha após funções de render específicas.

## 🎯 CRITÉRIOS DE ACEITE

- [ ] Caixinhas aparecem nos 5-8 artefatos principais
- [ ] Botão "Gerar crítica" funciona e salva em `reviews`
- [ ] Botões Aceitar/Revisar/Descartar funcionam
- [ ] Campo de observação do analista funciona
- [ ] Aba "Críticas & Curadoria" lista corretamente
- [ ] Filtro por status funciona
- [ ] Parecer integra com críticas aceitas
- [ ] `policy_inputs` são expostos corretamente

## ⚙️ CONFIGURAÇÃO

### Variáveis de Ambiente (.env)
```
OPENAI_API_KEY=sk-...
FINSCORE_LLM_MODEL=gpt-4o-mini
FINSCORE_LLM_TEMPERATURE=0.2
```

### Feature Flag (opcional)
Para ativar/desativar críticas IA:
```python
st.session_state["enable_ai_review"] = True  # ou False
```

## 🐛 TROUBLESHOOTING

### Erro: "OPENAI_API_KEY not configured"
- Verificar se `.env` está no diretório correto
- Verificar se a chave está válida

### Críticas não aparecem
- Verificar se `ss.reviews` está sendo inicializado
- Verificar se `artifact_id` é único e consistente

### Botões não funcionam
- Verificar se `st.rerun()` está sendo chamado
- Verificar conflitos de `key` em widgets

## 📚 REFERÊNCIAS

- LangChain: https://python.langchain.com/
- OpenAI API: https://platform.openai.com/docs
- Pydantic: https://docs.pydantic.dev/
