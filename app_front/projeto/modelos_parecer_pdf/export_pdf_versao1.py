"""
Módulo para exportação de pareceres para PDF A4 profissional.

Suporta dois engines:
- Playwright (Chromium): Linux/Mac - Qualidade superior, CSS moderno
- xhtml2pdf (ReportLab): Windows/Fallback - Compatível, mais simples

A escolha do engine é automática baseada na plataforma ou pode ser forçada.
"""

import os
import sys
import platform
import asyncio
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Literal
import markdown_it
from io import BytesIO

# Detectar plataforma
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# Tentar importar ambos os engines
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Engine padrão baseado na plataforma
if IS_WINDOWS:
    DEFAULT_ENGINE = 'xhtml2pdf'
else:
    DEFAULT_ENGINE = 'playwright' if PLAYWRIGHT_AVAILABLE else 'xhtml2pdf'

FOOTER_BRAND = "Assertif Soluções Financeiras"


def get_available_engines() -> list:
    """
    Retorna lista de engines disponíveis.
    
    Returns:
        Lista com nomes dos engines disponíveis
    """
    engines = []
    if PLAYWRIGHT_AVAILABLE:
        engines.append('playwright')
    if XHTML2PDF_AVAILABLE:
        engines.append('xhtml2pdf')
    return engines


def get_engine_info() -> Dict:
    """
    Retorna informações sobre engines disponíveis.
    
    Returns:
        Dicionário com informações dos engines
    """
    return {
        'platform': platform.system(),
        'default_engine': DEFAULT_ENGINE,
        'playwright_available': PLAYWRIGHT_AVAILABLE,
        'xhtml2pdf_available': XHTML2PDF_AVAILABLE,
        'available_engines': get_available_engines()
    }


def _convert_markdown_to_html(markdown_text: str) -> str:
    """
    Converte texto Markdown para HTML usando markdown-it-py.
    
    Args:
        markdown_text: Texto em formato Markdown
        
    Returns:
        HTML renderizado
    """
    md = markdown_it.MarkdownIt()
    html = md.render(markdown_text)
    return html


def _get_css_for_engine(engine: str) -> str:
    """
    Retorna CSS específico para o engine escolhido.
    
    Args:
        engine: 'playwright' ou 'xhtml2pdf'
        
    Returns:
        String com CSS
    """
    if engine == 'playwright':
        # CSS moderno para Playwright (Chromium)
        return """
        @page {
            size: A4;
            margin: 2.4cm 2.3cm 2.8cm 2.3cm;
            
            @top-center {
                content: "";
            }
            
            @bottom-left {
                content: "Assertif Soluções Financeiras";
                font-family: "Source Sans 3", Arial, sans-serif;
                font-size: 9pt;
                color: #999999;
            }
            
            @bottom-right {
                content: counter(page) " / " counter(pages);
                font-family: "Source Sans 3", Arial, sans-serif;
                font-size: 9pt;
                color: #999999;
            }
        }
        """
    else:
        # CSS simples para xhtml2pdf
        return """
        @page {
            size: A4;
            margin: 2.4cm 2.3cm 2.8cm 2.3cm;
        }
        """


def _get_fonts_for_engine(engine: str) -> str:
    """
    Retorna tags de fontes para o engine escolhido.
    
    Args:
        engine: 'playwright' ou 'xhtml2pdf'
        
    Returns:
        String com tags HTML
    """
    if engine == 'playwright':
        # Google Fonts para Playwright
        return """
    <!-- Fontes Google -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
        """
    else:
        # Sem fontes externas para xhtml2pdf
        return ""


def _get_font_families_for_engine(engine: str) -> Dict[str, str]:
    """
    Retorna famílias de fontes para o engine escolhido.
    
    Args:
        engine: 'playwright' ou 'xhtml2pdf'
        
    Returns:
        Dicionário com serif, sans, mono
    """
    if engine == 'playwright':
        return {
            'serif': "'Source Serif 4', 'Times New Roman', serif",
            'sans': "'Source Sans 3', 'Arial', sans-serif",
            'mono': "'JetBrains Mono', 'Courier New', monospace"
        }
    else:
        return {
            'serif': "'Georgia', 'Times New Roman', serif",
            'sans': "'Arial', 'Helvetica', sans-serif",
            'mono': "'Courier New', 'Courier', monospace"
        }


def render_parecer_html(conteudo: str, meta: Dict, is_markdown: bool = True, engine: str = 'xhtml2pdf') -> str:
    """
    Renderiza o conteúdo do parecer em HTML completo com estilos de impressão.
    
    Args:
        conteudo: Corpo do parecer (Markdown ou HTML)
        meta: Dicionário com metadados (empresa, cnpj, data_analise, etc.)
        is_markdown: Se True, converte de Markdown para HTML
        engine: 'playwright' ou 'xhtml2pdf'
        
    Returns:
        HTML completo pronto para impressão
    """
    # Converter Markdown para HTML se necessário
    if is_markdown:
        conteudo_html = _convert_markdown_to_html(conteudo)
    else:
        conteudo_html = conteudo
    
    # Extrair dados do meta
    empresa = meta.get("empresa", "N/A")
    cnpj = meta.get("cnpj", "N/A")
    data_analise = meta.get("data_analise", datetime.now().strftime("%d/%m/%Y"))
    finscore = meta.get("finscore_ajustado", "N/A")
    classificacao_fs = meta.get("classificacao_finscore", "N/A")
    serasa = meta.get("serasa_score", "N/A")
    classificacao_ser = meta.get("classificacao_serasa", "N/A")
    decisao = meta.get("decisao", "N/A")
    
    # Formatar decisão
    decisao_map = {
        "aprovar": "APROVAR",
        "aprovar_com_ressalvas": "APROVAR COM RESSALVAS",
        "nao_aprovar": "NÃO APROVAR"
    }
    decisao_texto = decisao_map.get(decisao, decisao.upper())
    
    # Data por extenso
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    hoje = datetime.now()
    data_extenso = f"{hoje.day} de {meses[hoje.month-1]} de {hoje.year}"
    
    # Obter configurações específicas do engine
    page_css = _get_css_for_engine(engine)
    fonts_html = _get_fonts_for_engine(engine)
    font_families = _get_font_families_for_engine(engine)

    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo_assertif_cab.png"
    if logo_path.exists():
        try:
            logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Logo Assertif" />'
        except Exception:
            logo_html = "<strong>Assertif</strong>"
    else:
        logo_html = "<strong>Assertif</strong>"
    
    # Template HTML completo
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parecer de Crédito - {empresa}</title>
    {fonts_html}
    <style>
        /* ========================================
           CONFIGURAÇÃO DE PÁGINA
           ======================================== */
        {page_css}
        
        /* ========================================
           RESET E BASE
           ======================================== */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html {{
            font-size: 12pt;
        }}
        
        body {{
            font-family: {font_families['serif']};
            color: #2c2c2c;
            line-height: 1.6;
            background: white;
        }}
        
        main {{
            margin-top: 12pt;
        }}
        
        /* ========================================
           TIPOGRAFIA
           ======================================== */
        h1, h2, h3, h4, h5, h6 {{
            font-family: {font_families['sans']};
            font-weight: 700;
            page-break-after: avoid;
            page-break-inside: avoid;
        }}
        
        h1 {{
            font-size: 18pt;
            margin-bottom: 16pt;
            text-align: center;
            color: #111;
        }}
        
        h2 {{
            font-size: 15pt;
            margin-top: 24pt;
            margin-bottom: 10pt;
            color: #4ea4e5;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        h3 {{
            font-size: 13pt;
            margin-top: 16pt;
            margin-bottom: 6pt;
            color: #4ea4e5;
        }}
        
        h4 {{
            font-size: 12pt;
            margin-top: 12pt;
            margin-bottom: 4pt;
            color: #333;
        }}
        
        p {{
            text-align: justify;
            margin: 8pt 0;
            page-break-inside: avoid;
            orphans: 3;
            widows: 3;
        }}
        
        strong {{
            font-weight: 700;
        }}
        
        em {{
            font-style: italic;
        }}
        
        code, pre {{
            font-family: {font_families['mono']};
            font-size: 10pt;
        }}
        
        /* ========================================
           CABEÇALHO DO DOCUMENTO
           ======================================== */
        .documento-hero {{
            margin: 0 0 18pt;
            display: flex;
            flex-direction: column;
            gap: 12pt;
        }}
        
        .documento-hero-logo {{
            text-align: right;
            padding-top: 0;
        }}
        
        .documento-hero-logo img {{
            max-width: 150px;
            width: 100%;
            display: inline-block;
        }}
        
        .documento-hero-banner {{
            background: #1f4e79;
            color: #fff;
            padding: 16pt 12pt;
            text-transform: uppercase;
            letter-spacing: 1px;
            width: 100%;
        }}
        
        .documento-hero-banner .hero-title {{
            font-size: 15pt;
            margin: 0;
            font-weight: 700;
            text-align: center;
        }}
        
        .documento-hero-banner .hero-meta {{
            font-size: 10pt;
            margin: 2pt 0 0;
            font-weight: 600;
            text-align: center;
        }}
        
        .documento-meta {{
            display: none;
        }}
        
        /* ========================================
           TABELAS
           ======================================== */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 14pt 0;
            page-break-inside: avoid;
            font-size: 11pt;
        }}
        
        thead {{
            background: #f2f5fb;
        }}
        
        th, td {{
            border: 1px solid #d8dde8;
            padding: 8pt 10pt;
            text-align: left;
        }}
        
        th {{
            font-weight: 600;
            font-family: 'Source Sans 3', 'Arial', sans-serif;
            color: #1f4e79;
        }}
        
        tr {{
            page-break-inside: avoid;
        }}
        
        /* ========================================
           LISTAS
           ======================================== */
        ul, ol {{
            margin: 8pt 0 8pt 20pt;
        }}
        
        li {{
            margin: 4pt 0;
            page-break-inside: avoid;
        }}
        
        /* ========================================
           CAMPO DE ASSINATURA
           ======================================== */
        .assinaturas {{
            margin-top: 36pt;
            page-break-inside: avoid;
        }}
        
        .assinaturas-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12pt;
            margin-bottom: 18pt;
        }}
        
        .assinaturas-header h3 {{
            margin: 0;
        }}
        
        .assinaturas-header .local-data {{
            text-align: right;
            font-style: italic;
            margin: 0;
            font-size: 11pt;
        }}
        
        .assinatura-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24pt;
            margin-top: 16pt;
        }}
        
        .assinatura-campo {{
            page-break-inside: avoid;
        }}
        
        .assinatura-linha {{
            border-bottom: 1px solid #000;
            height: 60pt;
            margin-bottom: 8pt;
        }}
        
        .assinatura-info {{
            font-size: 10pt;
            line-height: 1.3;
        }}
        
        .assinatura-info strong {{
            display: block;
            margin-bottom: 2pt;
        }}
        
        /* ========================================
           QUEBRAS DE PÁGINA
           ======================================== */
        .page-break {{
            page-break-after: always;
        }}
        
        /* ========================================
           IMPRESSÃO
           ======================================== */
        @media print {{
            body {{
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}
            
            .no-print {{
                display: none !important;
            }}
        }}
        
    </style>
</head>
<body>
    <!-- Cabeçalho do Documento -->
    <header class="documento-hero">
        <div class="documento-hero-logo">{logo_html}</div>
        <div class="documento-hero-banner">
            <p class="hero-title">Parecer Técnico</p>
            <p class="hero-meta">{empresa}</p>
            <p class="hero-meta">CNPJ: {cnpj}</p>
        </div>
    </header>
    
    <!-- Corpo do Parecer -->
    <main>
        {conteudo_html}
    </main>
    
    <!-- Campo de Assinaturas -->
    <section class="assinaturas">
        <div class="assinaturas-header">
            <p class="local-data">São Paulo (SP), {data_extenso}.</p>
        </div>
        
        <div class="assinatura-grid">
            <div class="assinatura-campo">
                <div class="assinatura-linha"></div>
                <div class="assinatura-info">
                    <strong>Nome do Analista</strong>
                    <span>Cargo | CPF: XXX.XXX.XXX-XX</span>
                </div>
            </div>
            
            <div class="assinatura-campo">
                <div class="assinatura-linha"></div>
                <div class="assinatura-info">
                    <strong>Nome do Aprovador</strong>
                    <span>Cargo | CPF: XXX.XXX.XXX-XX</span>
                </div>
            </div>
        </div>
    </section>
</body>
</html>"""
    
    return html


async def _html_to_pdf_playwright_async(html: str) -> bytes:
    """
    Converte HTML para PDF usando Playwright (Chromium).
    Função assíncrona para uso em ambientes Linux/Mac.
    
    Args:
        html: HTML completo para renderizar
        
    Returns:
        Bytes do PDF gerado
    """
    footer_left_text = FOOTER_BRAND

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Definir conteúdo HTML
        await page.set_content(html, wait_until="networkidle")
        
        # Gerar PDF com alta qualidade
        pdf_bytes = await page.pdf(
            format="A4",
            margin={
                "top": "2.4cm",
                "right": "2.3cm",
                "bottom": "2.8cm",
                "left": "2.3cm"
            },
            print_background=True,
            display_header_footer=True,
            header_template="""
                <div style="font-size:0;"></div>
            """,
            footer_template=f"""
                <div style="font-size: 9pt; font-family: 'Source Sans 3', Arial, sans-serif; color: #999999; width: 100%; padding: 6px 40px; display: flex; justify-content: space-between;">
                    <span>{footer_left_text}</span>
                    <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
                </div>
            """
        )
        
        await browser.close()
        return pdf_bytes


def _html_to_pdf_playwright(html: str) -> bytes:
    """
    Wrapper síncrono para Playwright.
    
    Args:
        html: HTML completo para renderizar
        
    Returns:
        Bytes do PDF gerado
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "Playwright não está instalado. "
            "Instale com: pip install playwright && playwright install chromium"
        )
    
    try:
        # Criar novo loop de eventos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            pdf_bytes = loop.run_until_complete(_html_to_pdf_playwright_async(html))
            return pdf_bytes
        finally:
            loop.close()
    except NotImplementedError:
        # Fallback se asyncio não funcionar (Windows + Streamlit)
        raise RuntimeError(
            "Playwright não funciona em Streamlit no Windows. "
            "Use engine='xhtml2pdf' ou execute em Linux."
        )


def _html_to_pdf_xhtml2pdf(html: str) -> bytes:
    """
    Converte HTML para PDF usando xhtml2pdf (pisa).
    Função síncrona compatível com Streamlit em qualquer plataforma.
    
    Args:
        html: HTML completo para renderizar
        
    Returns:
        Bytes do PDF gerado
        
    Raises:
        ImportError: Se xhtml2pdf não estiver instalado
        Exception: Se houver erro na geração do PDF
    """
    if not XHTML2PDF_AVAILABLE:
        raise ImportError(
            "xhtml2pdf não está instalado. "
            "Instale com: pip install xhtml2pdf"
        )
    
    try:
        # Renderizar PDF em memória
        pdf_bytes_io = BytesIO()
        
        # Converter HTML para PDF
        pisa_status = pisa.CreatePDF(
            html,
            dest=pdf_bytes_io,
            encoding='utf-8'
        )
        
        if pisa_status.err:
            raise Exception(f"Erros durante a geração do PDF: {pisa_status.err}")
        
        # Retornar bytes
        pdf_bytes = pdf_bytes_io.getvalue()
        return pdf_bytes
        
    except Exception as e:
        raise Exception(f"Erro ao gerar PDF com xhtml2pdf: {str(e)}") from e


def html_to_pdf_bytes(html: str, engine: Optional[str] = None) -> bytes:
    """
    Converte HTML para PDF usando o engine especificado.
    
    Args:
        html: HTML completo para renderizar
        engine: 'playwright', 'xhtml2pdf' ou None (usa DEFAULT_ENGINE)
        
    Returns:
        Bytes do PDF gerado
        
    Raises:
        ValueError: Se o engine especificado não estiver disponível
        Exception: Se houver erro na geração
    """
    # Usar engine padrão se não especificado
    if engine is None:
        engine = DEFAULT_ENGINE
    
    # Validar engine disponível
    available = get_available_engines()
    if engine not in available:
        raise ValueError(
            f"Engine '{engine}' não disponível. "
            f"Engines disponíveis: {available}. "
            f"Instale o engine necessário."
        )
    
    # Gerar PDF com o engine escolhido
    if engine == 'playwright':
        return _html_to_pdf_playwright(html)
    elif engine == 'xhtml2pdf':
        return _html_to_pdf_xhtml2pdf(html)
    else:
        raise ValueError(f"Engine desconhecido: {engine}")


def gerar_pdf_parecer(
    conteudo: str, 
    meta: Dict, 
    is_markdown: bool = True, 
    engine: Optional[str] = None
) -> bytes:
    """
    Função de alto nível que gera o PDF completo do parecer.
    
    Args:
        conteudo: Corpo do parecer (Markdown ou HTML)
        meta: Dicionário com metadados
        is_markdown: Se True, converte de Markdown para HTML
        engine: 'playwright', 'xhtml2pdf' ou None (auto-detecta)
        
    Returns:
        Bytes do PDF gerado
        
    Raises:
        ValueError: Se o engine não estiver disponível
        Exception: Se houver erro na geração
    """
    # Usar engine padrão se não especificado
    if engine is None:
        engine = DEFAULT_ENGINE
    
    # Renderizar HTML com engine apropriado
    html = render_parecer_html(conteudo, meta, is_markdown, engine=engine)
    
    # Converter para PDF
    pdf_bytes = html_to_pdf_bytes(html, engine=engine)
    
    return pdf_bytes
