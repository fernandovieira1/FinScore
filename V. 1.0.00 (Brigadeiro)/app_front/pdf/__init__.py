"""
Módulo de exportação de pareceres para PDF.
"""

from .export_pdf import gerar_pdf_parecer, render_parecer_html, html_to_pdf_bytes

__all__ = ['gerar_pdf_parecer', 'render_parecer_html', 'html_to_pdf_bytes']
