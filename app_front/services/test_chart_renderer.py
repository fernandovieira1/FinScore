# test_chart_renderer.py
"""
Script de teste para o módulo chart_renderer.
Testa a geração dos minicharts comparativos Serasa vs FinScore.
"""

import os
import sys

# Adicionar o diretório app_front ao path
app_front_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_front_dir not in sys.path:
    sys.path.insert(0, app_front_dir)

from services.chart_renderer import (
    gerar_minichart_serasa_finscore,
    obter_valores_faixas_serasa,
    obter_valores_faixas_finscore
)


def test_basic():
    """Teste básico com valores fixos"""
    print("🧪 Teste 1: Valores fixos padrão")
    
    serasa_score = 550
    finscore_score = 905
    
    print(f"  Serasa: {serasa_score}")
    print(f"  FinScore: {finscore_score}")
    
    # Gerar e salvar
    output_path = "test_minichart_basic.png"
    result = gerar_minichart_serasa_finscore(
        serasa_score=serasa_score,
        finscore_score=finscore_score,
        output_path=output_path
    )
    
    if os.path.exists(output_path):
        print(f"  ✅ Arquivo gerado: {output_path}")
    else:
        print(f"  ❌ Falha ao gerar arquivo")


def test_with_classifications():
    """Teste com classificações automáticas"""
    print("\n🧪 Teste 2: Com classificações automáticas")
    
    serasa_score = 820
    finscore_score = 650
    cls_serasa = "Bom"
    cls_finscore = "Neutro"
    
    print(f"  Serasa: {serasa_score} ({cls_serasa})")
    print(f"  FinScore: {finscore_score} ({cls_finscore})")
    
    # Obter valores das faixas
    serasa_vals = obter_valores_faixas_serasa(cls_serasa)
    finscore_vals = obter_valores_faixas_finscore(cls_finscore)
    
    print(f"  Faixas Serasa: {serasa_vals}")
    print(f"  Faixas FinScore: {finscore_vals}")
    
    # Gerar e salvar
    output_path = "test_minichart_classified.png"
    result = gerar_minichart_serasa_finscore(
        serasa_score=serasa_score,
        finscore_score=finscore_score,
        serasa_vals=serasa_vals,
        finscore_vals=finscore_vals,
        output_path=output_path
    )
    
    if os.path.exists(output_path):
        print(f"  ✅ Arquivo gerado: {output_path}")
    else:
        print(f"  ❌ Falha ao gerar arquivo")


def test_base64():
    """Teste com retorno em base64"""
    print("\n🧪 Teste 3: Retorno em base64")
    
    serasa_score = 300
    finscore_score = 180
    
    print(f"  Serasa: {serasa_score}")
    print(f"  FinScore: {finscore_score}")
    
    # Gerar em base64
    base64_str = gerar_minichart_serasa_finscore(
        serasa_score=serasa_score,
        finscore_score=finscore_score,
        return_base64=True
    )
    
    if base64_str and len(base64_str) > 0:
        print(f"  ✅ Base64 gerado ({len(base64_str)} caracteres)")
        print(f"  Preview: {base64_str[:50]}...")
    else:
        print(f"  ❌ Falha ao gerar base64")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO MÓDULO CHART_RENDERER")
    print("=" * 60)
    
    try:
        test_basic()
        test_with_classifications()
        test_base64()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\n❌ ERRO: Dependências não instaladas")
        print(f"   {e}")
        print("\n📦 Instale as dependências:")
        print("   pip install matplotlib numpy pillow")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
