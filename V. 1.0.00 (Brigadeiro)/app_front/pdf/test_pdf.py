"""
Script de teste rápido para validar engines de PDF e geração de pareceres.
Testa tanto xhtml2pdf quanto Playwright (se disponível).
"""

import sys
from pathlib import Path

# Adicionar app_front ao path
app_front = Path(__file__).parent.parent
sys.path.insert(0, str(app_front))


def test_imports():
    """Testa se as dependências estão instaladas"""
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
    
    # Playwright é opcional
    try:
        from playwright.async_api import async_playwright
        print("✅ playwright importado com sucesso (opcional)")
    except ImportError:
        print("⚠️  playwright não disponível (opcional - só funciona em Linux/Mac)")
    
    return True


def test_pdf_module():
    """Testa se o módulo PDF funciona"""
    print("\n🔍 Testando módulo PDF...")
    
    try:
        from pdf.export_pdf import gerar_pdf_parecer, get_engine_info, get_available_engines
        print("✅ Módulo pdf.export_pdf importado com sucesso")
        
        # Mostrar informações dos engines
        info = get_engine_info()
        print(f"\n📊 Informações do sistema:")
        print(f"   Plataforma: {info['platform']}")
        print(f"   Engine padrão: {info['default_engine']}")
        print(f"   Playwright disponível: {info['playwright_available']}")
        print(f"   xhtml2pdf disponível: {info['xhtml2pdf_available']}")
        print(f"   Engines disponíveis: {info['available_engines']}")
        
    except ImportError as e:
        print(f"❌ Erro ao importar pdf.export_pdf: {e}")
        return False
    
    return True


def test_pdf_generation(engine='xhtml2pdf'):
    """Testa geração de PDF com engine específico"""
    print(f"\n🔍 Testando geração de PDF com {engine}...")
    
    try:
        from pdf.export_pdf import gerar_pdf_parecer
        
        # Conteúdo de teste
        conteudo_teste = f"""
# Parecer de Crédito - TESTE

## 1. Informações Gerais
Este é um teste de geração de PDF com **{engine}**.

## 2. Análise Financeira
Teste de formatação com:
- **Negrito**
- *Itálico*
- `Código`

### 2.1 Indicadores
| Indicador | Valor | Classificação |
|-----------|-------|---------------|
| FinScore  | 725.5 | Médio-Alto    |
| Serasa    | 650   | Médio         |

## 3. Decisão
**APROVAR COM RESSALVAS**

## 4. Considerações Finais
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

### 4.1 Recomendações
1. Monitorar fluxo de caixa
2. Revisar garantias
3. Estabelecer covenants

## 5. Conclusão
Parecer favorável com ressalvas técnicas mencionadas.
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
        
        print(f"⏳ Gerando PDF com {engine}...")
        pdf_bytes = gerar_pdf_parecer(
            conteudo_teste, 
            meta_teste, 
            is_markdown=True,
            engine=engine
        )
        
        print(f"✅ PDF gerado! Tamanho: {len(pdf_bytes)} bytes")
        
        # Salvar arquivo de teste
        output_path = Path(__file__).parent / f"teste_output_{engine}.pdf"
        output_path.write_bytes(pdf_bytes)
        print(f"✅ PDF salvo em: {output_path}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Erro ao gerar PDF com {engine}: {e}")
        print("\n📋 Traceback completo:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE MÓDULO PDF - MULTI-ENGINE")
    print("=" * 60)
    
    # Teste 1: Importações
    if not test_imports():
        print("\n❌ Falha no teste de importações. Instale as dependências:")
        print("   pip install xhtml2pdf markdown-it-py")
        print("   pip install playwright && playwright install chromium  # opcional")
        sys.exit(1)
    
    # Teste 2: Módulo PDF
    if not test_pdf_module():
        print("\n❌ Falha ao importar módulo PDF")
        sys.exit(1)
    
    # Teste 3: Geração de PDF com engines disponíveis
    from pdf.export_pdf import get_available_engines
    
    engines = get_available_engines()
    all_passed = True
    
    for engine in engines:
        if not test_pdf_generation(engine):
            print(f"\n⚠️  Falha no teste com {engine}")
            all_passed = False
        else:
            print(f"\n✅ Teste com {engine} passou!")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)
