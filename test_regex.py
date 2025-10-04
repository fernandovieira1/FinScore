import re

text = """### 4,1 Indicadores de Liquidez
Valor: 0.83
ROE: 0,15
### 5,2 Serasa
Score: 550"""

print("TEXTO ORIGINAL:")
print(text)
print("\n" + "="*50 + "\n")

# Passo 1: Corrigir vírgulas em títulos markdown
text = re.sub(r'^(#{2,3}\s+)(\d+),(\d+)(\s+)', r'\1\2.\3\4', text, flags=re.MULTILINE)

print("APÓS CORREÇÃO DE TÍTULOS:")
print(text)
print("\n" + "="*50 + "\n")

# Passo 2: Converter pontos em decimais (linha por linha, SEM títulos)
lines = text.split('\n')
result = []
for line in lines:
    if line.strip().startswith('#'):
        # Linhas com # não convertem ponto para vírgula
        result.append(line)
    else:
        # Outras linhas convertem ponto para vírgula
        result.append(re.sub(r'(\d+)\.(\d+)', r'\1,\2', line))

final_text = '\n'.join(result)

print("RESULTADO FINAL:")
print(final_text)
