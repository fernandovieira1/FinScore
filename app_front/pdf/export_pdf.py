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
            margin: 2.5cm 2.5cm 3cm 2.5cm;
            
            @top-center {
                content: "Parecer de Crédito - Confidencial";
                font-family: Arial, sans-serif;
                font-size: 9pt;
                color: #666;
                padding-bottom: 5pt;
                border-bottom: 1px solid #ddd;
            }
            
            @bottom-left {
                content: "Confidencial – Uso Interno";
                font-family: Arial, sans-serif;
                font-size: 9pt;
                color: #666;
            }
            
            @bottom-right {
                content: "Página " counter(page) " de " counter(pages);
                font-family: Arial, sans-serif;
                font-size: 9pt;
                color: #666;
            }
        }
        """
    else:
        # CSS simples para xhtml2pdf
        return """
        @page {
            size: A4;
            margin: 2.5cm;
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
            color: #222;
            line-height: 1.5;
            background: white;
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
            font-size: 14pt;
            margin-top: 18pt;
            margin-bottom: 8pt;
            color: #111;
            border-bottom: 1px solid #444;
            padding-bottom: 4pt;
        }}
        
        h3 {{
            font-size: 13pt;
            margin-top: 14pt;
            margin-bottom: 6pt;
            color: #111;
        }}
        
        h4 {{
            font-size: 12pt;
            margin-top: 10pt;
            margin-bottom: 4pt;
            color: #333;
        }}
        
        p {{
            text-align: justify;
            margin: 6pt 0;
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
        .documento-header {{
            text-align: center;
            margin: 6pt 0 24pt;
            padding: 18pt 0 14pt;
            border-top: 1.5px solid #d8d8d8;
            border-bottom: 1px solid #c7c7c7;
        }}
        
        .documento-header-logo img {{
            max-width: 180px;
            width: 100%;
            display: block;
            margin: 0 auto 12pt;
        }}
        
        .documento-header-title p {{
            font-family: {font_families['sans']};
            color: #111;
            font-weight: 700;
            margin: 3pt 0;
            text-align: center;
        }}
        
        .documento-header-title .titulo-principal {{
            font-size: 16pt;
        }}
        
        .documento-header-title .titulo-secundario {{
            font-size: 13pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .documento-header-title .titulo-cnpj {{
            font-size: 11pt;
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
            margin: 12pt 0;
            page-break-inside: avoid;
        }}
        
        thead {{
            background: #f0f0f0;
        }}
        
        th, td {{
            border: 1px solid #444;
            padding: 6pt 8pt;
            text-align: left;
        }}
        
        th {{
            font-weight: 600;
            font-family: 'Source Sans 3', 'Arial', sans-serif;
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
        
        .assinaturas h3 {{
            margin-bottom: 16pt;
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
        
        .local-data {{
            margin-top: 24pt;
            text-align: right;
            font-style: italic;
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
        
        /* ========================================
           RODAPÉ FIXO
           ======================================== */
        .pdf-footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            font-size: 9pt;
            color: #666;
            padding: 10pt 0;
            border-top: 1px solid #ddd;
            text-align: center;
            background: white;
        }}
    </style>
</head>
<body>
    <!-- Cabeçalho do Documento -->
    <header class="documento-header">
        <div class="documento-header-logo">{logo_html}</div>
        <div class="documento-header-title">
            <p class="titulo-principal">Parecer de Crédito</p>
            <p class="titulo-secundario">{empresa}</p>
            <p class="titulo-cnpj">CNPJ: {cnpj}</p>
        </div>
    </header>
    
    <!-- Corpo do Parecer -->
    <main>
        {conteudo_html}
    </main>
    
    <!-- Campo de Assinaturas -->
    <section class="assinaturas">
        <h3>5. Assinaturas</h3>
        
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
        
        <div class="local-data">
            <p>Ribeirão Preto (SP), {data_extenso}.</p>
        </div>
    </section>
    
    <!-- Rodapé fixo PDF -->
    <div class="pdf-footer">
        <p>Confidencial – Uso Interno</p>
    </div>
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
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Definir conteúdo HTML
        await page.set_content(html, wait_until="networkidle")
        
        # Gerar PDF com alta qualidade
        pdf_bytes = await page.pdf(
            format="A4",
            margin={
                "top": "2.5cm",
                "right": "2.5cm",
                "bottom": "3cm",
                "left": "2.5cm"
            },
            print_background=True,
            display_header_footer=True,
            header_template="""
                <div style="font-size: 9pt; color: #666; width: 100%; text-align: center; padding: 5px 0;">
                    <span>Parecer de Crédito - Confidencial</span>
                </div>
            """,
            footer_template="""
                <div style="font-size: 9pt; color: #666; width: 100%; padding: 5px 40px; display: flex; justify-content: space-between;">
                    <span>Confidencial – Uso Interno</span>
                    <span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span>
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
