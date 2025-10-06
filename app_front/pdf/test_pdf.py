"""
Script de teste rápido para validar a instalação do Playwright e geração de PDF.
"""

import sys
from pathlib import Path

# Adicionar app_front ao path
app_front = Path(__file__).parent.parent
sys.path.insert(0, str(app_front))

def test_imports():
    """Testa se todas as dependências estão instaladas"""
    print("🔍 Testando importações...")
    
    try:
        from xhtml2pdf import pisa
        print("✅ xhtml2pdf importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar xhtml2pdf: {e}")
        return False
    
    try:
        import markdown_it
        print("✅ markdown_it importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar markdown_it: {e}")
        return False
    
    return True


def test_pdf_module():
    """Testa se o módulo PDF funciona"""
    print("\n🔍 Testando módulo PDF...")
    
    try:
        from pdf.export_pdf import gerar_pdf_parecer
        print("✅ Módulo pdf.export_pdf importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar pdf.export_pdf: {e}")
        return False
    
    return True


def test_pdf_generation():
    """Testa geração de PDF simples"""
    print("\n🔍 Testando geração de PDF...")
    
    try:
        from pdf.export_pdf import gerar_pdf_parecer
        
        # Conteúdo de teste
        conteudo_teste = """
# Parecer de Crédito - TESTE

## 1. Informações Gerais
Este é um teste de geração de PDF.

## 2. Análise
Teste de formatação com **negrito** e *itálico*.

### 2.1 Subseção
- Item 1
- Item 2
- Item 3

## 3. Conclusão
PDF gerado com sucesso!
"""
        
        meta_teste = {
            "empresa": "EMPRESA TESTE LTDA",
            "cnpj": "00.000.000/0001-00",
            "data_analise": "01/10/2025",
            "finscore_ajustado": "725.50",
            "classificacao_finscore": "Médio-Alto",
            "serasa_score": "650",
            "classificacao_serasa": "Médio",
            "decisao": "aprovar_com_ressalvas"
        }
        
        print("⏳ Gerando PDF de teste...")
        pdf_bytes = gerar_pdf_parecer(conteudo_teste, meta_teste, is_markdown=True)
        
        print(f"✅ PDF gerado! Tamanho: {len(pdf_bytes)} bytes")
        
        # Salvar arquivo de teste
        output_path = Path(__file__).parent / "teste_output.pdf"
        output_path.write_bytes(pdf_bytes)
        print(f"✅ PDF salvo em: {output_path}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Erro ao gerar PDF: {e}")
        print("\n📋 Traceback completo:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE MÓDULO PDF")
    print("=" * 60)
    
    # Teste 1: Importações
    if not test_imports():
        print("\n❌ Falha no teste de importações. Instale as dependências:")
        print("   pip install xhtml2pdf markdown-it-py")
        sys.exit(1)
    
    # Teste 2: Módulo PDF
    if not test_pdf_module():
        print("\n❌ Falha ao importar módulo PDF")
        sys.exit(1)
    
    # Teste 3: Geração de PDF
    if not test_pdf_generation():
        print("\n❌ Falha ao gerar PDF")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 60)
