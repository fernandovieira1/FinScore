# PDF Export Module - Hybrid Engine# Exportação PDF - Instruções de Instalação



Este módulo suporta **dois engines** de geração de PDF, com seleção automática baseada na plataforma:## Dependências Necessárias



## 🎭 Engines DisponíveisA funcionalidade de exportação PDF profissional requer as seguintes bibliotecas:



### 1. **Playwright** (Chromium) - Recomendado para Linux/Mac```bash

- ✅ Qualidade superiorpip install playwright jinja2 markdown-it-py

- ✅ CSS moderno completo (Grid, Flexbox, etc.)```

- ✅ Google Fonts funcionam perfeitamente

- ✅ Cabeçalhos/rodapés nativos com numeração## Instalação do Chromium (Playwright)

- ✅ Renderização pixel-perfect

- ⚠️ Requer Chromium (~150MB)Após instalar o Playwright, é necessário instalar o navegador Chromium:

- ❌ Não funciona com Streamlit no Windows

```bash

### 2. **xhtml2pdf** (ReportLab) - Compatível Windowspython -m playwright install chromium

- ✅ 100% Python puro```

- ✅ Multiplataforma

- ✅ Leve e rápido## Estrutura de Arquivos

- ✅ Funciona em qualquer ambiente

- ⚠️ CSS 2.1 limitado```

- ⚠️ Sem fontes externasapp_front/

├── pdf/

## 📦 Instalação│   ├── __init__.py

│   └── export_pdf.py

### Opção 1: Instalar ambos (recomendado)└── views/

```bash    └── parecer.py (integração do botão)

pip install xhtml2pdf playwright markdown-it-py```



# Instalar Chromium (só em Linux/Mac ou para testes)## Uso

python -m playwright install chromium

```A funcionalidade é acionada automaticamente através do botão **"Exportar PDF (A4)"** na seção de Parecer.



### Opção 2: Apenas xhtml2pdf (Windows/mínimo)### Características do PDF gerado:

```bash

pip install xhtml2pdf markdown-it-py- ✅ Formato A4 com margens de 2,5 cm

```- ✅ Tipografia profissional (Source Serif 4 + Source Sans 3)

- ✅ Cabeçalho e rodapé com paginação "Página X de Y"

## 🚀 Uso- ✅ Corpo justificado com hierarquia de títulos

- ✅ Tabelas formatadas para impressão

### Uso básico (auto-detecta plataforma)- ✅ Campo de assinatura com linhas, nomes, cargos e CPF

```python- ✅ Resumo executivo destacado

from pdf.export_pdf import gerar_pdf_parecer- ✅ Quebras de página otimizadas (sem órfãs/viúvas)



pdf_bytes = gerar_pdf_parecer(## Troubleshooting

    conteudo="# Parecer\n\nTexto em Markdown...",

    meta={### Erro: "playwright not found"

        "empresa": "Empresa Exemplo",Execute: `pip install playwright`

        "cnpj": "00.000.000/0001-00",

        "finscore_ajustado": "725.50",### Erro: "Executable doesn't exist"

        ...Execute: `python -m playwright install chromium`

    },

    is_markdown=True### Erro em ambiente de produção (deploy)

)Se o Playwright não funcionar no ambiente de deploy:

```1. Verifique se o ambiente suporta navegadores headless

2. Considere usar um serviço alternativo (WeasyPrint, wkhtmltopdf)

### Forçar engine específico3. Configure variáveis de ambiente específicas para Playwright

```python

# Forçar Playwright (alta qualidade)## Deploy no Streamlit Cloud

pdf_bytes = gerar_pdf_parecer(..., engine='playwright')

Adicione ao arquivo `packages.txt` (na raiz do projeto):

# Forçar xhtml2pdf (compatibilidade)

pdf_bytes = gerar_pdf_parecer(..., engine='xhtml2pdf')```

```chromium

chromium-driver

### Verificar engines disponíveis```

```python

from pdf.export_pdf import get_engine_info, get_available_enginesE no `requirements.txt` mantenha:



info = get_engine_info()```

print(f"Plataforma: {info['platform']}")playwright==1.48.0

print(f"Engine padrão: {info['default_engine']}")jinja2==3.1.4

print(f"Disponíveis: {info['available_engines']}")markdown-it-py==3.0.0

``````



## 🎨 Seleção Automática## Fallback (opcional)



O módulo detecta automaticamente a melhor opção:Caso o Playwright não seja viável, implemente fallback usando:



| Plataforma | Engine Padrão | Motivo |```python

|------------|---------------|--------|# Opção 1: WeasyPrint

| **Windows** | xhtml2pdf | Playwright não funciona com Streamlit |from weasyprint import HTML

| **Linux** | playwright | Melhor qualidade, funciona perfeitamente |pdf = HTML(string=html).write_pdf()

| **Mac** | playwright | Melhor qualidade, funciona perfeitamente |

# Opção 2: pdfkit + wkhtmltopdf

## 🧪 Testesimport pdfkit

pdf = pdfkit.from_string(html, False)

Execute o script de teste para validar ambos engines:```



```bash## Suporte

python app_front/pdf/test_pdf.py

```Para mais informações sobre Playwright:

- Documentação: https://playwright.dev/python/

Resultado esperado:- GitHub: https://github.com/microsoft/playwright-python

```
✅ xhtml2pdf importado com sucesso
✅ playwright importado com sucesso (opcional)
✅ Módulo pdf.export_pdf importado com sucesso

📊 Informações do sistema:
   Plataforma: Windows
   Engine padrão: xhtml2pdf
   Playwright disponível: True
   xhtml2pdf disponível: True
   Engines disponíveis: ['playwright', 'xhtml2pdf']

🔍 Testando geração de PDF com playwright...
✅ PDF gerado! Tamanho: 211346 bytes

🔍 Testando geração de PDF com xhtml2pdf...
✅ PDF gerado! Tamanho: 7075 bytes

✅ TODOS OS TESTES PASSARAM!
```

## ☁️ Deploy no Streamlit Cloud

O Streamlit Cloud usa **Linux**, então o Playwright será usado automaticamente para máxima qualidade.

### Arquivos de configuração:

**requirements.txt:**
```txt
xhtml2pdf==0.2.16
playwright==1.48.0
markdown-it-py==3.0.0
```

**packages.txt:**
```txt
libgbm1
libasound2
```

**.streamlit/install_playwright.sh:**
```bash
#!/bin/bash
python -m playwright install chromium --with-deps
```

## 🔧 Troubleshooting

### Playwright não funciona no Windows com Streamlit
**Esperado!** Use `engine='xhtml2pdf'` ou deixe auto-detectar.

### Erro "Engine não disponível"
Instale o engine necessário:
```bash
pip install xhtml2pdf  # ou
pip install playwright && playwright install chromium
```

### PDF com fontes estranhas
- **Playwright**: Baixa Google Fonts automaticamente
- **xhtml2pdf**: Usa fontes do sistema (Georgia, Arial)

### Chromium muito grande para deploy
Use apenas xhtml2pdf:
```bash
pip uninstall playwright
```

## 📊 Comparação de Qualidade

| Recurso | Playwright | xhtml2pdf |
|---------|------------|-----------|
| Tamanho médio PDF | ~200KB | ~7KB |
| Google Fonts | ✅ | ❌ |
| CSS Grid/Flexbox | ✅ | ❌ |
| Cabeçalho/rodapé | ✅ Nativo | ⚠️ Manual |
| Numeração páginas | ✅ Automática | ❌ |
| Qualidade tipografia | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Compatibilidade | Linux/Mac | Todos |
| Velocidade | Médio | Rápido |

## 🎯 Recomendações

- **Desenvolvimento local (Windows)**: Use xhtml2pdf
- **Produção (Streamlit Cloud)**: Use Playwright (automático)
- **Máxima compatibilidade**: Use apenas xhtml2pdf
- **Máxima qualidade**: Force Playwright em Linux/Mac
