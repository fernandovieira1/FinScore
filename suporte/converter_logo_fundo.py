"""
Script para converter logos PNG com fundo transparente para fundo sólido.
Uso: python converter_logo_fundo.py
"""
from PIL import Image
import os

def converter_transparente_para_solido(caminho_entrada, caminho_saida=None, cor_fundo=(253, 250, 251)):
    """
    Converte uma imagem PNG com fundo transparente para fundo sólido.
    
    Args:
        caminho_entrada: Caminho do arquivo PNG de entrada
        caminho_saida: Caminho do arquivo PNG de saída (se None, sobrescreve o original)
        cor_fundo: Tupla RGB da cor de fundo (padrão: #FDFAFB = (253, 250, 251))
    """
    print(f"Abrindo: {caminho_entrada}")
    
    # Abrir imagem
    img = Image.open(caminho_entrada)
    
    # Converter para RGBA se necessário
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Criar nova imagem com fundo sólido
    fundo = Image.new('RGB', img.size, cor_fundo)
    
    # Compor o logo sobre o fundo usando o canal alpha
    fundo.paste(img, (0, 0), img)
    
    # Definir caminho de saída
    if caminho_saida is None:
        caminho_saida = caminho_entrada
    
    # Salvar
    fundo.save(caminho_saida, 'PNG')
    print(f"✓ Salvo: {caminho_saida}")
    print(f"  Tamanho: {img.size}")
    print(f"  Cor de fundo: RGB{cor_fundo}")


if __name__ == "__main__":
    # Caminho do logo Serasa
    logo_serasa = r"C:\Users\ferna\OneDrive\Desktop OneDrive\FinScore\app_front\assets\logo_serasa.png"
    
    # Criar backup do original
    backup_path = logo_serasa.replace(".png", "_backup_original.png")
    if not os.path.exists(backup_path):
        img_original = Image.open(logo_serasa)
        img_original.save(backup_path)
        print(f"📦 Backup criado: {backup_path}")
    
    # Converter logo Serasa
    print("\n🔄 Convertendo logo Serasa...")
    converter_transparente_para_solido(
        logo_serasa,
        cor_fundo=(253, 250, 251)  # #FDFAFB
    )
    
    print("\n✅ Conversão concluída!")
    print("O arquivo foi sobrescrito com a versão de fundo sólido.")
    print("Um backup do original foi salvo com sufixo '_backup_original'.")
