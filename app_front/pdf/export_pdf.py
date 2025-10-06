"""
Módulo para exportação de pareceres para PDF A4 profissional.
Utiliza xhtml2pdf (pisa) para renderização HTML->PDF com qualidade de impressão.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import markdown_it
from io import BytesIO

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False


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


def render_parecer_html(conteudo: str, meta: Dict, is_markdown: bool = True) -> str:
    """
    Renderiza o conteúdo do parecer em HTML completo com estilos de impressão.
    
    Args:
        conteudo: Corpo do parecer (Markdown ou HTML)
        meta: Dicionário com metadados (empresa, cnpj, data_analise, etc.)
        is_markdown: Se True, converte de Markdown para HTML
        
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
    
    # Template HTML completo
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parecer de Crédito - {empresa}</title>
    
    <style>
        /* ========================================
           CONFIGURAÇÃO DE PÁGINA
           ======================================== */
        @page {{
            size: A4;
            margin: 2.5cm;
        }}
        
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
            font-family: 'Georgia', 'Times New Roman', serif;
            color: #222;
            line-height: 1.5;
            background: white;
        }}
        
        /* ========================================
           TIPOGRAFIA
           ======================================== */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Arial', 'Helvetica', sans-serif;
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
            font-family: 'Courier New', 'Courier', monospace;
            font-size: 10pt;
        }}
        
        /* ========================================
           CABEÇALHO DO DOCUMENTO
           ======================================== */
        .documento-header {{
            text-align: center;
            margin-bottom: 24pt;
            padding-bottom: 12pt;
            border-bottom: 2px solid #444;
        }}
        
        .documento-header h1 {{
            margin-bottom: 8pt;
        }}
        
        .documento-meta {{
            font-size: 10pt;
            color: #555;
            line-height: 1.4;
        }}
        
        .documento-meta p {{
            text-align: center;
            margin: 2pt 0;
        }}
        
        /* ========================================
           RESUMO EXECUTIVO (destaque)
           ======================================== */
        .resumo-executivo {{
            background: #f5f5f5;
            border-left: 4px solid #5ea68d;
            padding: 12pt;
            margin: 16pt 0;
            page-break-inside: avoid;
        }}
        
        .resumo-executivo h3 {{
            margin-top: 0;
            color: #5ea68d;
        }}
        
        .decisao-box {{
            background: white;
            border: 2px solid #444;
            padding: 8pt;
            margin: 8pt 0;
            text-align: center;
            font-weight: 700;
            font-size: 14pt;
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
           CABEÇALHO E RODAPÉ FIXOS
           ======================================== */
        .pdf-header {{
            text-align: center;
            font-size: 9pt;
            color: #666;
            padding: 10pt 0;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20pt;
        }}
        
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
    <!-- Cabeçalho fixo PDF -->
    <div class="pdf-header">
        <strong>Parecer de Crédito - Confidencial</strong>
    </div>
    
    <!-- Cabeçalho do Documento -->
    <header class="documento-header">
        <h1>Parecer de Crédito</h1>
        <div class="documento-meta">
            <p><strong>{empresa}</strong></p>
            <p>CNPJ: {cnpj}</p>
            <p>Data da Análise: {data_analise}</p>
        </div>
    </header>
    
    <!-- Resumo Executivo (destaque) -->
    <section class="resumo-executivo">
        <h3>Resumo Executivo</h3>
        <p><strong>FinScore:</strong> {finscore} ({classificacao_fs})</p>
        <p><strong>Serasa Score:</strong> {serasa} ({classificacao_ser})</p>
        <div class="decisao-box">
            DECISÃO: {decisao_texto}
        </div>
    </section>
    
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


def html_to_pdf_bytes(html: str) -> bytes:
    """
    Converte HTML para PDF usando xhtml2pdf (pisa).
    Função síncrona compatível com Streamlit.
    
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


def gerar_pdf_parecer(conteudo: str, meta: Dict, is_markdown: bool = True) -> bytes:
    """
    Função de alto nível que gera o PDF completo do parecer.
    
    Args:
        conteudo: Corpo do parecer (Markdown ou HTML)
        meta: Dicionário com metadados
        is_markdown: Se True, converte de Markdown para HTML
        
    Returns:
        Bytes do PDF gerado
    """
    # Renderizar HTML
    html = render_parecer_html(conteudo, meta, is_markdown)
    
    # Converter para PDF
    pdf_bytes = html_to_pdf_bytes(html)
    
    return pdf_bytes
