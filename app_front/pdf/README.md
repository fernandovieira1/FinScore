# Exportação PDF - Instruções de Instalação

## Dependências Necessárias

A funcionalidade de exportação PDF profissional requer as seguintes bibliotecas:

```bash
pip install playwright jinja2 markdown-it-py
```

## Instalação do Chromium (Playwright)

Após instalar o Playwright, é necessário instalar o navegador Chromium:

```bash
python -m playwright install chromium
```

## Estrutura de Arquivos

```
app_front/
├── pdf/
│   ├── __init__.py
│   └── export_pdf.py
└── views/
    └── parecer.py (integração do botão)
```

## Uso

A funcionalidade é acionada automaticamente através do botão **"Exportar PDF (A4)"** na seção de Parecer.

### Características do PDF gerado:

- ✅ Formato A4 com margens de 2,5 cm
- ✅ Tipografia profissional (Source Serif 4 + Source Sans 3)
- ✅ Cabeçalho e rodapé com paginação "Página X de Y"
- ✅ Corpo justificado com hierarquia de títulos
- ✅ Tabelas formatadas para impressão
- ✅ Campo de assinatura com linhas, nomes, cargos e CPF
- ✅ Resumo executivo destacado
- ✅ Quebras de página otimizadas (sem órfãs/viúvas)

## Troubleshooting

### Erro: "playwright not found"
Execute: `pip install playwright`

### Erro: "Executable doesn't exist"
Execute: `python -m playwright install chromium`

### Erro em ambiente de produção (deploy)
Se o Playwright não funcionar no ambiente de deploy:
1. Verifique se o ambiente suporta navegadores headless
2. Considere usar um serviço alternativo (WeasyPrint, wkhtmltopdf)
3. Configure variáveis de ambiente específicas para Playwright

## Deploy no Streamlit Cloud

Adicione ao arquivo `packages.txt` (na raiz do projeto):

```
chromium
chromium-driver
```

E no `requirements.txt` mantenha:

```
playwright==1.48.0
jinja2==3.1.4
markdown-it-py==3.0.0
```

## Fallback (opcional)

Caso o Playwright não seja viável, implemente fallback usando:

```python
# Opção 1: WeasyPrint
from weasyprint import HTML
pdf = HTML(string=html).write_pdf()

# Opção 2: pdfkit + wkhtmltopdf
import pdfkit
pdf = pdfkit.from_string(html, False)
```

## Suporte

Para mais informações sobre Playwright:
- Documentação: https://playwright.dev/python/
- GitHub: https://github.com/microsoft/playwright-python
