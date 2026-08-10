# Integração do Minichart no Parecer FinScore

## Visão Geral

Este documento descreve a integração automática dos gráficos comparativos (minicharts) Serasa vs FinScore no parecer gerado pela IA, especificamente na seção **4.4 Opinião (Síntese Visual)**.

## Arquivos Criados/Modificados

### 1. `app_front/services/chart_renderer.py` (NOVO)
Módulo responsável pela geração dos minicharts comparativos.

**Principais funções:**
- `gerar_minichart_serasa_finscore()`: Gera o gráfico lado a lado
- `obter_valores_faixas_serasa()`: Retorna valores ilustrativos das faixas Serasa
- `obter_valores_faixas_finscore()`: Retorna valores ilustrativos das faixas FinScore

**Características:**
- Backend não-interativo (`matplotlib.use("Agg")`)
- Paletas de cores pastel (verde-água para Serasa, azul para FinScore)
- Logos automáticos (com fallback para texto)
- Exportação em arquivo PNG ou base64

### 2. `app_front/views/parecer.py` (MODIFICADO)

**Modificações realizadas:**

#### a) Atualização do prompt (seção 4.4 adicionada)
Incluída nova seção no template do parecer:

```markdown
### 4.4 Opinião (Síntese Visual)

**Nota:** Esta subseção será preenchida automaticamente com um gráfico 
comparativo visual dos escores Serasa e FinScore, contextualizando as 
classificações obtidas em 4.1, 4.2 e 4.3.

Em 2-3 frases, sintetize:
- O alinhamento (ou divergência) entre FinScore e Serasa
- Se os resultados confirmam ou contradizem a análise detalhada dos indicadores
- Uma avaliação geral sobre o perfil de risco da empresa
```

#### b) Nova função `_inject_minichart()`
Injeta automaticamente o gráfico gerado após a criação do parecer pela IA.

**Funcionamento:**
1. Extrai scores e classificações de `analysis_data`
2. Gera o minichart em formato base64
3. Procura pela seção `### 4.4` no parecer gerado
4. Insere o gráfico como imagem inline markdown
5. Fallback: se não encontrar 4.4, insere antes da seção 5

#### c) Atualização em `_generate_parecer_ia()`
Adicionada chamada para `_inject_minichart()` após geração do parecer pela IA.

#### d) Correção de campo
Corrigido `analysis_data.get("serasa_score")` → `analysis_data.get("serasa")`
para consistência com o dicionário de dados.

## Fluxo de Execução

```
┌────────────────────────────────────────────────┐
│ Usuário clica em "Gerar Parecer"              │
└────────────────┬───────────────────────────────┘
                 │
                 v
┌────────────────────────────────────────────────┐
│ _extract_analysis_data(out_dict)               │
│ - Extrai finscore_ajustado, classificacao     │
│ - Extrai serasa, classificacao_serasa         │
│ - Extrai índices financeiros                  │
└────────────────┬───────────────────────────────┘
                 │
                 v
┌────────────────────────────────────────────────┐
│ _generate_parecer_ia()                         │
│ 1. Constrói prompt com template completo      │
│ 2. Invoca modelo de IA (GPT/Claude)           │
│ 3. Aplica correções de formatação             │
└────────────────┬───────────────────────────────┘
                 │
                 v
┌────────────────────────────────────────────────┐
│ _inject_minichart()                            │
│ 1. Extrai scores de analysis_data             │
│ 2. Determina valores de faixas               │
│ 3. Gera gráfico (base64)                      │
│ 4. Injeta na seção 4.4                        │
└────────────────┬───────────────────────────────┘
                 │
                 v
┌────────────────────────────────────────────────┐
│ Parecer completo salvo em                      │
│ st.session_state["parecer_gerado"]            │
└────────────────────────────────────────────────┘
```

## Formato do Gráfico

### Layout
- **Dois gráficos lado a lado:** Serasa (esquerda) e FinScore (direita)
- **Resolução:** 10x3 polegadas, 250 DPI
- **Fundo:** `#FDFAFB` (branco levemente pastel)

### Características de cada gráfico
- **Barras:** Sem bordas, cores pastel graduadas
- **Grid:** Linhas horizontais leves (`#EDEFF3`)
- **Score:** Linha pontilhada horizontal (`#7A8596`)
- **Valores:** Exibidos acima de cada barra (8pt, bold)
- **Categorias:** Labels no eixo X (7pt)
- **Logos:** Centralizados abaixo dos gráficos (zoom 0.06)

### Categorias

**Serasa (4 categorias):**
- Muito Baixo
- Baixo
- Bom
- Excelente

**FinScore (5 categorias):**
- M. Acima (Muito Acima do Risco)
- L. Acima (Levemente Acima do Risco)
- Neutro
- L. Abaixo (Levemente Abaixo do Risco)
- M. Abaixo (Muito Abaixo do Risco)

## Valores das Faixas

Os valores ilustrativos das barras são ajustados automaticamente baseados 
na classificação obtida:

### Serasa
- **Excelente/Muito Bom:** `(300, 500, 700, 1000)`
- **Bom:** `(250, 450, 750, 900)`
- **Baixo:** `(200, 400, 600, 800)`
- **Muito Baixo/N/A:** `(150, 300, 500, 700)`

### FinScore
- **Muito Abaixo do Risco:** `(125, 250, 750, 875, 1000)`
- **Levemente Abaixo do Risco:** `(125, 250, 750, 875, 950)`
- **Neutro:** `(125, 250, 500, 750, 875)`
- **Levemente Acima do Risco:** `(100, 200, 400, 600, 800)`
- **Muito Acima do Risco:** `(50, 125, 250, 400, 600)`

## Dependências

```python
# requirements.txt
matplotlib>=3.7.0
numpy>=1.24.0
Pillow>=10.0.0
```

## Testes

Execute o script de teste:

```bash
cd app_front/services
python test_chart_renderer.py
```

**Testes incluídos:**
1. Valores fixos padrão (Serasa 550, FinScore 905)
2. Com classificações automáticas
3. Retorno em formato base64

## Assets Necessários

Os logos devem estar presentes em:
- `app_front/assets/logo_serasa3.png`
- `app_front/assets/logo_fin1a.png`

**Fallback:** Se os logos não forem encontrados, o sistema automaticamente 
usa labels de texto ("Serasa" e "FinScore").

## Exemplo de Uso Manual

```python
from services.chart_renderer import gerar_minichart_serasa_finscore

# Gerar e salvar em arquivo
gerar_minichart_serasa_finscore(
    serasa_score=550,
    finscore_score=905,
    output_path="parecer_grafico.png"
)

# Ou obter em base64 para embed
base64_img = gerar_minichart_serasa_finscore(
    serasa_score=550,
    finscore_score=905,
    return_base64=True
)
```

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'matplotlib'"
**Solução:**
```bash
pip install matplotlib numpy pillow
```

### Erro: "FileNotFoundError: Logo not found"
**Solução:** O sistema automaticamente usa fallback para texto. 
Para usar logos, certifique-se que os arquivos PNG estão em `app_front/assets/`.

### Gráfico não aparece no parecer
**Verificar:**
1. O parecer foi gerado com sucesso?
2. A seção 4.4 existe no prompt?
3. Há mensagens de erro/warning no Streamlit?

**Debug:**
```python
# Adicionar em _inject_minichart():
print(f"Serasa: {serasa_score}, FinScore: {finscore_score}")
print(f"Base64 length: {len(chart_base64)}")
```

## Próximos Passos

- [ ] Adicionar opção de customização de cores via config
- [ ] Permitir ajuste de tamanho/resolução via parâmetros
- [ ] Exportar gráfico separadamente (além do parecer)
- [ ] Adicionar gráfico de tendências temporais
- [ ] Integrar com exportação PDF (inclusão da imagem)

## Referências

- Script original (mockup manual): `render_minicharts.py`
- Documentação Matplotlib: https://matplotlib.org/
 
