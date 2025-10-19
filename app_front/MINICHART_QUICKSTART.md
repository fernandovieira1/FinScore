# 🎨 Guia Rápido: Minicharts no Parecer

## O que foi implementado?

Agora o parecer gerado em `/Parecer` inclui automaticamente um **gráfico comparativo visual** entre Serasa e FinScore na **seção 4.4 Opinião (Síntese Visual)**.

## Como funciona?

### 1. **Entrada de Dados** (em `/Lançamentos`)
Você insere:
- Dados contábeis (Excel)
- Metadados da empresa (nome, CNPJ, anos)
- **Score Serasa** (campo obrigatório)

### 2. **Processamento** (em `/Análise`)
O sistema calcula:
- FinScore (0-1000)
- Classificação FinScore (Muito Abaixo/Levemente Abaixo/Neutro/etc.)
- Classificação Serasa (Excelente/Bom/Baixo/Muito Baixo)
- Índices financeiros detalhados

### 3. **Geração do Parecer** (em `/Parecer`)
Ao clicar em **"Gerar Parecer"**:

```
📝 IA escreve o parecer completo (seções 1-5)
     ↓
🎨 Sistema gera minichart automaticamente
     ↓
🔗 Minichart é injetado na seção 4.4
     ↓
✅ Parecer final com gráfico embutido
```

### 4. **Resultado**
O parecer exibe um gráfico lado a lado:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   [Gráfico Serasa]     [Gráfico FinScore]         │
│   - 4 barras pastel    - 5 barras pastel          │
│   - Linha do score     - Linha do score           │
│   - Logo Serasa        - Logo FinScore            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Personalização Automática

Os valores das barras se ajustam automaticamente à classificação:

**Exemplo 1: Empresa com perfil sólido**
- Serasa: 850 (Excelente) → Barras: [300, 500, 700, **1000**]
- FinScore: 920 (Muito Abaixo do Risco) → Barras: [125, 250, 750, 875, **1000**]

**Exemplo 2: Empresa com risco elevado**
- Serasa: 320 (Baixo) → Barras: [200, 400, 600, **800**]
- FinScore: 180 (Levemente Acima do Risco) → Barras: [100, 200, 400, 600, **800**]

## Arquivos Importantes

```
app_front/
├── services/
│   ├── chart_renderer.py          ← 🆕 Geração dos gráficos
│   ├── test_chart_renderer.py     ← 🧪 Testes
│   └── CHART_INTEGRATION.md       ← 📚 Documentação técnica
├── views/
│   └── parecer.py                 ← ✏️ Modificado (injeção do chart)
└── assets/
    ├── logo_serasa3.png           ← 🖼️ Logo Serasa
    └── logo_fin1a.png             ← 🖼️ Logo FinScore
```

## Teste Rápido

### Opção 1: Via aplicativo (recomendado)
1. Abra o app: `streamlit run app_front/app.py`
2. Vá em `/Lançamentos` e insira dados de uma empresa
3. Vá em `/Análise` e aguarde processamento
4. Vá em `/Parecer` e clique em "Gerar Parecer"
5. Verifique a seção 4.4 do parecer gerado

### Opção 2: Via script de teste
```bash
cd app_front/services
python test_chart_renderer.py
```

Isso gerará 2 arquivos PNG de exemplo:
- `test_minichart_basic.png`
- `test_minichart_classified.png`

## Formato de Exportação

### No Streamlit (Markdown)
O gráfico é embutido como **base64**:
```markdown
![Comparativo Serasa vs FinScore](data:image/png;base64,iVBORw0KG...)
```

### No PDF (futuro)
Quando exportar para PDF, o gráfico será incluído automaticamente.

## Troubleshooting

### ❌ "Não foi possível gerar o gráfico comparativo"
**Causa:** Faltam dependências ou erro ao carregar dados.

**Solução:**
```bash
pip install matplotlib numpy Pillow
```

### ❌ Gráfico não aparece no parecer
**Verificar:**
1. O score Serasa foi informado em `/Lançamentos`?
2. O FinScore foi calculado em `/Análise`?
3. Há erros no console do Streamlit?

**Debug:**
Verifique `st.session_state["out"]` após análise:
```python
print(st.session_state["out"]["serasa"])
print(st.session_state["out"]["finscore_ajustado"])
print(st.session_state["out"]["classificacao_serasa"])
print(st.session_state["out"]["classificacao_finscore"])
```

### ⚠️ Logos não aparecem
**Causa:** Arquivos PNG não encontrados em `assets/`.

**Solução:** O sistema usa **fallback automático** para texto:
- "Serasa" (em vez do logo)
- "FinScore" (em vez do logo)

Sem problemas para funcionamento, apenas estético.

## Customização

### Alterar cores das barras
Edite em `chart_renderer.py`:
```python
TEAL_PASTEL = ["#BFEDE6", "#A6E4DB", "#8ADBCF", "#6FD2C4"]  # Serasa
BLUE_PASTEL = ["#C8DBF4", "#AECBEE", "#90BAE8", "#78A6DB", "#5F90CE"]  # FinScore
```

### Alterar tamanho do gráfico
Em `gerar_minichart_serasa_finscore()`:
```python
fig, (axL, axR) = plt.subplots(
    1, 2, figsize=(10.0, 3.0), dpi=250  # ← Ajustar aqui
)
```

### Desabilitar gráfico temporariamente
Comente em `parecer.py`, função `_generate_parecer_ia()`:
```python
# response = _inject_minichart(response, analysis_data)
```

## Próximas Melhorias

- [ ] Incluir gráfico no PDF exportado
- [ ] Adicionar gráfico de tendências temporais (evolução dos scores)
- [ ] Permitir download do gráfico separadamente
- [ ] Comparativo setorial (benchmarking)

## Créditos

Baseado no mockup manual `render_minicharts.py` e integrado 
automaticamente no fluxo do app FinScore.

---

📖 **Documentação completa:** `services/CHART_INTEGRATION.md`
