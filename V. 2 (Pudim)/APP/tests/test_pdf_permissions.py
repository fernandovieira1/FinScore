from io import BytesIO
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from pypdf.constants import UserAccessPermissions as Permission
from reportlab.pdfgen import canvas

from app_front.pdf import export_pdf


class PdfPermissionsTest(unittest.TestCase):
    def setUp(self):
        buffer = BytesIO()
        document = canvas.Canvas(buffer)
        document.setTitle("Parecer de teste")
        document.drawString(40, 800, "Parecer FinScore - conteudo preservado")
        document.save()
        self.original = buffer.getvalue()

    def assertProtected(self, data):
        reader = PdfReader(BytesIO(data))
        self.assertTrue(reader.is_encrypted)
        self.assertEqual(reader.decrypt(""), 1)  # acesso de leitura, não de proprietário
        permissions = reader.user_access_permissions
        for forbidden in (Permission.MODIFY, Permission.ADD_OR_MODIFY,
                          Permission.FILL_FORM_FIELDS, Permission.ASSEMBLE_DOC):
            self.assertFalse(permissions & forbidden)
        for allowed in (Permission.PRINT, Permission.PRINT_TO_REPRESENTATION,
                        Permission.EXTRACT, Permission.EXTRACT_TEXT_AND_GRAPHICS):
            self.assertTrue(permissions & allowed)
        self.assertEqual(reader.trailer["/Encrypt"]["/V"], 5)
        original = PdfReader(BytesIO(self.original))
        self.assertEqual(reader.pages[0].extract_text(), original.pages[0].extract_text())
        self.assertEqual(reader.pages[0].mediabox, original.pages[0].mediabox)
        self.assertEqual(reader.metadata.title, original.metadata.title)
        self.assertEqual(export_pdf.contar_paginas_pdf(data), 1)

    def test_protection_preserves_reading_printing_and_content(self):
        self.assertProtected(export_pdf._proteger_pdf_contra_edicao(self.original))

    def test_both_engines_return_protected_documents(self):
        for engine in ("playwright", "xhtml2pdf"):
            with self.subTest(engine=engine), patch.object(export_pdf, "render_parecer_html", return_value="html"), patch.object(export_pdf, "html_to_pdf_bytes", return_value=self.original):
                self.assertProtected(export_pdf.gerar_pdf_parecer("texto", {}, engine=engine, min_pages=1))

    def test_fallback_document_is_also_protected(self):
        with patch.object(export_pdf, "DEFAULT_ENGINE", "playwright"), patch.object(export_pdf, "XHTML2PDF_AVAILABLE", True), patch.object(export_pdf, "render_parecer_html", return_value="html"), patch.object(export_pdf, "html_to_pdf_bytes", side_effect=[RuntimeError("engine unavailable"), self.original]):
            self.assertProtected(export_pdf.gerar_pdf_parecer("texto", {}))

    def test_encryption_failure_never_returns_unprotected_document(self):
        with patch.object(export_pdf, "render_parecer_html", return_value="html"), patch.object(export_pdf, "html_to_pdf_bytes", return_value=self.original), patch.object(export_pdf, "_proteger_pdf_contra_edicao", side_effect=RuntimeError("encryption failed")):
            with self.assertRaisesRegex(RuntimeError, "encryption failed"):
                export_pdf.gerar_pdf_parecer("texto", {})
