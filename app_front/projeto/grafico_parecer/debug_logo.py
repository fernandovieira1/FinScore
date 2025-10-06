"""
Script para debugar o logo Serasa e descobrir o problema.
"""
from PIL import Image

# Caminho do logo
logo_path = r"C:\Users\ferna\OneDrive\Desktop OneDrive\FinScore\app_front\assets\logo_serasa.png"

print("Analisando logo Serasa...")
print("=" * 60)

# Abrir e analisar
img = Image.open(logo_path)

print(f"Modo da imagem: {img.mode}")
print(f"Tamanho: {img.size}")
print(f"Formato: {img.format}")

# Verificar se tem canal alpha
if img.mode in ('RGBA', 'LA', 'PA'):
    print("⚠️  A imagem AINDA tem canal alpha (transparência)")
    
    # Verificar se realmente tem pixels transparentes
    if img.mode == 'RGBA':
        alpha = img.split()[3]  # Canal alpha
        bbox = alpha.getbbox()
        if bbox:
            min_alpha = min(alpha.getdata())
            max_alpha = max(alpha.getdata())
            print(f"Canal alpha - Min: {min_alpha}, Max: {max_alpha}")
            if min_alpha < 255:
                print("⚠️  Existem pixels com transparência!")
else:
    print("✓ A imagem NÃO tem canal alpha (fundo sólido)")

# Tentar salvar uma versão forçadamente RGB
print("\n" + "=" * 60)
print("Tentando forçar conversão para RGB...")

img_rgb = img.convert('RGB')
output_path = r"C:\Users\ferna\OneDrive\Desktop OneDrive\FinScore\app_front\assets\logo_serasa_forcado.png"
img_rgb.save(output_path, 'PNG')

print(f"✓ Salvo versão RGB em: logo_serasa_forcado.png")
print(f"Modo da nova imagem: {img_rgb.mode}")
