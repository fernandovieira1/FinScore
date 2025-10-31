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
from string import Template
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
ACCENT_PRIMARY = "#2d4c6a"
ACCENT_SECONDARY = "#7bb0d5"
NEUTRAL_DARK = "#2f2f2f"
NEUTRAL_LIGHT = "#f5f6fa"
BODY_FONT = "'Source Sans 3', 'Helvetica Neue', Arial, sans-serif"
TITLE_FONT = "'Source Serif 4', 'Libre Baskerville', serif"


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
    Ativa extensões necessárias para suportar tabelas e outros
    elementos avançados utilizados no parecer.
    
    Args:
        markdown_text: Texto em formato Markdown
        
    Returns:
        HTML renderizado
    """
    md = (
        markdown_it
        .MarkdownIt("commonmark")
        .enable(["table", "strikethrough"])
    )
    return md.render(markdown_text)


def _get_css_for_engine(engine: str) -> str:
    """
    Retorna CSS específico para o engine escolhido.
    
    Args:
        engine: 'playwright' ou 'xhtml2pdf'
        
    Returns:
        String com CSS
    """
    margin_top = "1.2cm"
    margin_sides = "2cm"
    margin_bottom = "2.5cm"

    if engine == 'playwright':
        # CSS moderno para Playwright (Chromium)
        template = Template(
            """
        @page {
            size: A4;
            margin: $margin_top $margin_sides $margin_bottom $margin_sides;
            @top-center {
                content: element(fs-header);
            }
        }
        @page:first {
            @top-center {
                content: normal;
            }
        }
        """
        )
        return template.substitute(
            margin_top=margin_top,
            margin_sides=margin_sides,
            margin_bottom=margin_bottom,
        )
    else:
        # CSS simples para xhtml2pdf
        template = Template(
            """
        @page {
            size: A4;
            margin: $margin_top $margin_sides $margin_bottom $margin_sides;
        }
        """
        )
        return template.substitute(
            margin_top=margin_top,
            margin_sides=margin_sides,
            margin_bottom=margin_bottom,
        )


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
    def _format_score(value) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "N/A"
        if number.is_integer():
            return f"{number:,.0f}".replace(",", ".")
        return f"{number:,.1f}".replace(",", ".")

    def _format_periodo(meta_dict: Dict) -> tuple[str, str, str]:
        def _safe_int(value):
            try:
                return int(str(value).strip())
            except (TypeError, ValueError, AttributeError):
                return None

        ano_inicial_meta = _safe_int(meta_dict.get("ano_inicial"))
        ano_final_meta = _safe_int(meta_dict.get("ano_final"))

        periodo_resumo = "Período não informado"
        ano_inicial_texto = "Ano inicial não informado"
        ano_final_texto = "Ano final não informado"

        if ano_inicial_meta and ano_final_meta:
            ano_inicial_texto = str(ano_inicial_meta)
            ano_final_texto = str(ano_final_meta)
            if ano_inicial_meta == ano_final_meta:
                periodo_resumo = str(ano_inicial_meta)
            elif ano_final_meta > ano_inicial_meta:
                periodo_resumo = f"{ano_inicial_meta}–{ano_final_meta}"
            else:
                periodo_resumo = f"{ano_inicial_meta}, {ano_final_meta}"
        elif ano_inicial_meta:
            ano_inicial_texto = str(ano_inicial_meta)
            ano_final_texto = "Ano final não informado"
            periodo_resumo = str(ano_inicial_meta)
        elif ano_final_meta:
            ano_final_texto = str(ano_final_meta)
            ano_inicial_texto = "Ano inicial não informado"
            periodo_resumo = str(ano_final_meta)

        return periodo_resumo, ano_inicial_texto, ano_final_texto

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
    classificacao_fs = meta.get("classificacao_finscore", meta.get("classificacao_fs", "N/A"))
    serasa = meta.get("serasa_score", "N/A")
    classificacao_ser = meta.get("classificacao_serasa", meta.get("classificacao_ser", "N/A"))
    decisao = meta.get("decisao", "N/A")
    
    # Formatar decisão (com ícones conforme solicitado)
    decisao_map = {
        "aprovar": "APROVAR",
        "aprovar_com_ressalvas": "APROVAR COM RESSALVAS",
        "nao_aprovar": "NÃO APROVAR"
    }
    # Mapa com ícones para exibição no cabeçalho/PDF
    decisao_icon_map = {
        "aprovar": "✅ APROVAR",
        "aprovar_com_ressalvas": "⚠️ APROVAR COM RESSALVAS",
        "nao_aprovar": "❌ NÃO APROVAR",
    }
    decisao_texto = decisao_icon_map.get(decisao, decisao_map.get(decisao, decisao.upper()))
    
    # Data por extenso
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    hoje = datetime.now()
    data_extenso = f"{hoje.day} de {meses[hoje.month-1]} de {hoje.year}"
    data_relatorio = meta.get("data_analise") or data_extenso
    serasa_data_texto = str(meta.get("serasa_data") or "Consulta não informada")
    cidade_relatorio = meta.get("cidade_relatorio", "São Paulo (SP)")
    periodo_texto, ano_inicial_texto, ano_final_texto = _format_periodo(meta)
    finscore_display = _format_score(meta.get("finscore_ajustado") or meta.get("finscore"))
    serasa_display = _format_score(meta.get("serasa_score") or meta.get("serasa"))
    
    # Obter configurações específicas do engine
    page_css = _get_css_for_engine(engine)
    fonts_html = _get_fonts_for_engine(engine)
    font_families = _get_font_families_for_engine(engine)

    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo_assertif_cab.png"
    if logo_path.exists():
        try:
            logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Logo Assertif" />'
            header_logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Logo Assertif" style="height:18pt;" />'
        except Exception:
            logo_html = "<strong>Assertif</strong>"
            header_logo_html = "<strong>Assertif</strong>"
    else:
        logo_html = "<strong>Assertif</strong>"
        header_logo_html = "<strong>Assertif</strong>"
    
    font_family_mono = font_families['mono']

    # Template HTML completo
    html_template = Template("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parecer de Crédito - $empresa</title>
    $fonts_html
    <style>
        /* ========================================
           CONFIGURAÇÃO DE PÁGINA
           ======================================== */
        $page_css
        
        /* ========================================
           RESET E BASE
           ======================================== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html {
            font-size: 12pt;
        }
        
        body {
            font-family: $BODY_FONT;
            color: $NEUTRAL_DARK;
            line-height: 1.65;
            background: #ffffff;
            padding: 20pt 0 30pt;
        }
        
        main {
            margin-top: 24pt;
        }
        
        /* ========================================
           TIPOGRAFIA
           ======================================== */
        h1, h2, h3, h4, h5, h6 {
            font-family: $TITLE_FONT;
            font-weight: 600;
            page-break-after: avoid;
            page-break-inside: avoid;
        }
        
        h2 {
            font-size: 18pt;
            margin-top: 32pt;
            margin-bottom: 14pt;
            color: $ACCENT_PRIMARY;
            letter-spacing: 0.4pt;
        }
        
        h3 {
            font-size: 14pt;
            margin-top: 20pt;
            margin-bottom: 8pt;
            color: $ACCENT_PRIMARY;
        }
        
        h4 {
            font-size: 12.5pt;
            margin-top: 12pt;
            margin-bottom: 6pt;
            color: $NEUTRAL_DARK;
        }
        
        p {
            text-align: justify;
            margin: 9pt 0;
            page-break-inside: avoid;
            orphans: 3;
            widows: 3;
            font-size: 11pt;
        }
        
        strong {
            font-weight: 700;
        }
        
        em {
            font-style: italic;
        }
        
        code, pre {
            font-family: $font_family_mono;
            font-size: 10pt;
        }
        
        /* ========================================
           CABEÇALHO DO DOCUMENTO
           ======================================== */
        .documento-hero {
            background: linear-gradient(135deg, rgba(45,76,106,0.95), rgba(23,33,54,0.92));
            border-radius: 28px;
            padding: 24pt;
            color: #fff;
            box-shadow: 0 25px 60px rgba(23,33,54,0.35);
        }
        
        .hero-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 24pt;
        }
        
        .hero-text {
            max-width: 70%;
        }
        
        .hero-eyebrow {
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 10pt;
            margin: 0;
            color: rgba(255,255,255,0.75);
        }
        
        .hero-text h1 {
            /* Fonte reduzida para ajustar hierarquia visual no cabeçalho */
            font-size: 20pt;
            margin: 6pt 0 8pt;
            color: #fff;
        }
        
        .hero-subtitle {
            margin: 0;
            font-size: 11pt;
            color: rgba(255,255,255,0.9);
        }
        
        .hero-logo {
            text-align: right;
        }
        
        .hero-logo img {
            max-width: 160px;
            width: 100%;
            display: inline-block;
        }
        
        .documento-meta {
            display: none;
        }

        .print-header-placeholder {
            height: 0;
            overflow: hidden;
        }

        .print-header-content {
            position: running(fs-header);
            font-family: $BODY_FONT;
            font-size: 11pt;
            color: #1f3f5b;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18pt;
            padding: 12px 40px;
            border-bottom: 1px solid #d9e2ef;
        }

        .print-header-content .print-header-logo img {
            height: 18pt;
        }

        .print-header-content .print-header-info {
            text-align: right;
            line-height: 1.45;
        }

        .page-canvas {
            width: 100%;
            margin: 0 auto;
            background: transparent;
            padding: 0;
        }
        
        .page-content {
            background: #ffffff;
            border-radius: 0;
            padding: 0;
        }

        .hero-shell {
            background: linear-gradient(135deg, #f7f9fc 0%, #eef3fb 100%);
            border-radius: 34px;
            padding: 26pt 28pt 28pt;
            margin-bottom: 26pt;
            box-shadow: 0 30px 80px rgba(25,40,75,0.18);
        }
        
        .summary-grid {
            display: grid;
            /* Ajuste: permitir que 4 cards caibam sem extrapolar a margem da página,
               mantendo proporção visual. Min-width reduzido para evitar overflow em A4. */
            grid-template-columns: repeat(4, minmax(170px, 1fr));
            gap: 2pt;
            margin-top: 16pt;
            /* Usar largura total do container e deslocamento interno para alinhar à esquerda */
            width: calc(100% - 48pt);
            margin-left: -24pt; /* alinha com padding interno do hero-shell */
            margin-right: -0pt;
            box-sizing: border-box;
            align-items: stretch;
        }

        .summary-card {
            background: linear-gradient(180deg, #ffffff 0%, #f8f9fc 100%);
            border-radius: 22px;
            padding: 14pt 16pt 16pt;
            box-shadow: 0 28px 60px rgba(32,56,85,0.12);
            border: 1px solid #e6ecf6;
            display: flex;
            flex-direction: column;
            /* Colocar título e valor próximos; helpers (rodapé) serão empurrados ao final */
            justify-content: flex-start;
            min-height: 125px;
        }
        
        .summary-card.highlight {
            background: linear-gradient(135deg, $ACCENT_PRIMARY, #1a2840);
            color: #fff;
            border: none;
        }
        
        .summary-label {
            font-size: 7.2pt;
            text-transform: uppercase;
            letter-spacing: 1.8px;
            margin-bottom: 5pt;
            color: #8892a6;
        }
        
        .summary-card.highlight .summary-label {
            color: rgba(255,255,255,0.7);
        }
        
        .summary-value {
            font-size: 13pt;
            margin: 0 0 4pt;
            font-family: $TITLE_FONT;
            line-height: 1.05;
            color: #1f2434;
        }
        
        .summary-card.highlight .summary-value {
            color: #fff;
        }
        
        .summary-helper {
            margin: 4pt 0 0;
            font-size: 8.6pt;
            color: #768197;
            /* Empurra o helper para o final do card quando houver espaço extra */
            margin-top: auto;
        }
        
        .summary-card.highlight .summary-helper {
            color: rgba(255,255,255,0.85);
        }

        /* Removido ajuste negativo em 'Período Avaliado' para restaurar altura original */
        
        .summary-chip {
            display: inline-block;
            margin-top: 5pt;
            padding: 3pt 10pt;
            border-radius: 999px;
            font-size: 8pt;
            background: rgba(123,176,213,0.22);
            color: $ACCENT_PRIMARY;
            font-weight: 600;
        }
        
        .summary-card.highlight .summary-chip {
            background: rgba(255,255,255,0.18);
            color: #fff;
        }

        @media screen and (max-width: 900px) {
            .summary-grid {
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            }
        }
        
        .content-panel {
            background: transparent;
            border-radius: 0;
            padding: 0;
            box-shadow: none;
            border: none;
            margin-top: 26pt;
        }
        
        .markdown-body h2 {
            font-size: 18pt;
            margin-top: 30pt;
        }
        
        .markdown-body h3 {
            font-size: 14pt;
        }
        
        .markdown-body h4 {
            font-size: 12.5pt;
        }
        
        .markdown-body blockquote {
            border-left: 4px solid $ACCENT_SECONDARY;
            background: #eef5fb;
            padding: 10pt 14pt;
            margin: 12pt 0;
            font-style: italic;
        }
        
        .markdown-body hr {
            border: none;
            border-top: 1px solid #d9dfe8;
            margin: 20pt 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16pt 0;
            page-break-inside: avoid;
            font-size: 10.5pt;
        }
        
        thead {
            background: $ACCENT_PRIMARY;
            color: #fff;
        }
        
        .markdown-body img {
            display: block;
            margin: 16pt auto;
            max-width: 90%;
            height: auto;
        }
        
        th {
            font-weight: 600;
            padding: 8pt 10pt;
            border: none;
        }
        
        td {
            border-bottom: 1px solid #e5e9f0;
            padding: 8pt 10pt;
        }
        
        tr:last-child td {
            border-bottom: none;
        }
        
        ul, ol {
            margin: 10pt 0 10pt 22pt;
        }
        
        li {
            margin: 4pt 0;
            page-break-inside: avoid;
        }
        
        /* ========================================
           CAMPO DE ASSINATURA
           ======================================== */
        .assinaturas {
            margin-top: 36pt;
            page-break-inside: avoid;
            background: #fff;
            border-radius: 20px;
            padding: 22pt 26pt;
            box-shadow: 0 15px 55px rgba(15,23,42,0.08);
            border: 1px solid #e2e7f0;
        }
        
        .assinaturas-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12pt;
            margin-bottom: 18pt;
        }
        
        .assinaturas-header h3 {
            margin: 0;
            color: $ACCENT_PRIMARY;
        }
        
        .assinaturas-header .local-data {
            text-align: right;
            font-style: italic;
            margin: 0;
            font-size: 11pt;
        }
        
        .assinatura-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24pt;
            margin-top: 16pt;
        }
        
        .assinatura-campo {
            page-break-inside: avoid;
        }
        
        .assinatura-linha {
            border-bottom: 1px solid #1f2937;
            height: 60pt;
            margin-bottom: 8pt;
        }
        
        .assinatura-info {
            font-size: 10pt;
            line-height: 1.3;
        }
        
        .assinatura-info strong {
            display: block;
            margin-bottom: 2pt;
        }
        
        /* ========================================
           QUEBRAS DE PÁGINA
           ======================================== */
        .page-break {
            page-break-after: always;
        }
        
        /* ========================================
           IMPRESSÃO
           ======================================== */
        @media print {
            body {
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }
            
            .no-print {
                display: none !important;
            }
        }
        
    </style>
</head>
<body>
    <div class="print-header-placeholder">
        <div class="print-header-content">
            <div class="print-header-logo">$header_logo_html</div>
            <div class="print-header-info">
                <span style="font-weight:700; display:block;">$empresa</span>
                <span style="font-size:10pt; display:block;">CNPJ: $cnpj</span>
            </div>
        </div>
    </div>
    <div class="page-canvas">
    <div class="page-content" style="background:#ffffff;">
    <section class="hero-shell">
    <header class="documento-hero">
        <div class="hero-top">
            <div class="hero-text">
                <p class="hero-eyebrow">Parecer Técnico · FinScore</p>
                <h1>$empresa</h1>
                <p class="hero-subtitle">CNPJ: $cnpj</p>
                <p class="hero-subtitle">Emitido em $data_relatorio</p>
            </div>
            <div class="hero-logo">$logo_html</div>
        </div>
    </header>
    
    <section class="summary-grid">
        <div class="summary-card highlight">
            <p class="summary-label">Decisão</p>
            <p class="summary-value">$decisao_texto</p>
        </div>
        <div class="summary-card">
            <p class="summary-label">FinScore Ajustado</p>
            <p class="summary-value">$finscore_display</p>
            <span class="summary-chip">$classificacao_fs</span>
        </div>
        <div class="summary-card">
            <p class="summary-label">Score Serasa</p>
            <p class="summary-value">$serasa_display</p>
            <span class="summary-chip">$classificacao_ser</span>
            <!-- Consulta date intentionally removed from PDF summary card as requested -->
        </div>
        <div class="summary-card period-card">
            <p class="summary-label">Período Avaliado</p>
            <p class="summary-value">$periodo_texto</p>
        </div>
    </section>
    </section>
    
    <!-- Corpo do Parecer -->
    <main>
        <section class="content-panel markdown-body">
            $conteudo_html
        </section>
    </main>
    
    <!-- Campo de Assinaturas -->
    <section class="assinaturas">
        <div class="assinaturas-header">
            <h3></h3>
            <p class="local-data">$cidade_relatorio, $data_extenso.</p>
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
    </div>
    </div>
</body>
</html>""")

    html = html_template.safe_substitute(
        empresa=empresa,
        fonts_html=fonts_html,
        page_css=page_css,
        BODY_FONT=BODY_FONT,
        NEUTRAL_DARK=NEUTRAL_DARK,
        TITLE_FONT=TITLE_FONT,
        ACCENT_PRIMARY=ACCENT_PRIMARY,
        ACCENT_SECONDARY=ACCENT_SECONDARY,
        font_family_mono=font_family_mono,
        header_logo_html=header_logo_html,
        cnpj=cnpj,
        data_relatorio=data_relatorio,
        logo_html=logo_html,
        decisao_texto=decisao_texto,
        cidade_relatorio=cidade_relatorio,
        finscore_display=finscore_display,
        classificacao_fs=classificacao_fs,
        serasa_display=serasa_display,
        classificacao_ser=classificacao_ser,
        serasa_data_texto=serasa_data_texto,
        periodo_texto=periodo_texto,
        ano_inicial_texto=ano_inicial_texto,
        ano_final_texto=ano_final_texto,
        conteudo_html=conteudo_html,
        data_extenso=data_extenso,
    )
    
    return html


async def _html_to_pdf_playwright_async(html: str, header_html: str) -> bytes:
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
                "top": "1.2cm",
                "right": "2cm",
                "bottom": "2.5cm",
                "left": "2cm"
            },
            print_background=True,
            display_header_footer=True,
            header_template=header_html,
            footer_template=f"""
                <div style="font-size: 9pt; font-family: 'Source Sans 3', Arial, sans-serif; color: #2d3c4f; width: 100%; padding: 8px 40px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #d4dae4; background: #ffffff;">
                    <span style="font-weight:600;">{footer_left_text}</span>
                    <span style="font-size: 8.5pt; color: #556070;">Página <span class="pageNumber"></span> de <span class="totalPages"></span></span>
                </div>
            """
        )
        
        await browser.close()
        return pdf_bytes


def _html_to_pdf_playwright(html: str, header_html: str) -> bytes:
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
            pdf_bytes = loop.run_until_complete(_html_to_pdf_playwright_async(html, header_html))
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


def html_to_pdf_bytes(html: str, engine: Optional[str] = None, header_html: Optional[str] = None) -> bytes:
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
        header_html = header_html or "<div style='font-size:0;'></div>"
        return _html_to_pdf_playwright(html, header_html)
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
