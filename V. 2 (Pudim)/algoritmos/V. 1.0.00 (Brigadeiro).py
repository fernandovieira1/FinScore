# %%
# Versão de testes
# V. 095 - Nova classificação do Score, testes IA e Uso de GPU
# Dados aproveitados v. 09x


# %% [markdown]
# ##### 0. CONFIGURAÇÃO DO AMBIENTE

# %% [markdown]
# 0.1 Configuração do ambiente

# %%
## Criar ambiente (bash)
# conda create -n tensorflow-env python=3.8xx   
# conda activate tensorflow-env
# conda install -c conda-forge tensorflow


# %%
# !conda install -c conda-forge tensorflow

# %%
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# %% [markdown]
# 0.2 Criação de funções

# %%
# Função para calcular os índices contábeis
def calcular_indices_contabeis(df):
    indices = {}
    
    indices['Liquidez Corrente'] = df['Ativo Circulante'] / df['Passivo Circulante']
    # Ativo Circulante: BP
    # Passivo Circulante: BP
    # => A liquidez corrente mede a capacidade da empresa de pagar suas obrigações de curto prazo.

    indices['Liquidez Seca'] = (df['Ativo Circulante'] - df['Estoques']) / df['Passivo Circulante']
    # Ativo Circulante: BP
    # Estoque: BP
    # Passivo Circulante: BP
    # => A liquidez seca é uma medida de liquidez que desconsidera o estoque da empresa.

    indices['Margem Líquida'] = df['Lucro Líquido'] / df['Receita Total']
    # Lucro Líquido: DRE
    # Receita Total: DRE
    # => A margem líquida mede a porcentagem de lucro líquido que a empresa gera para cada real de receita.

    indices['ROA'] = df['Lucro Líquido'] / df['Ativo Total']
    # Lucro Líquido: DRE
    # Ativo Total: BP
    # => O retorno sobre ativos (ROA) mede a eficiência da empresa em gerar lucro a partir de seus ativos.

    indices['ROE'] = df['Lucro Líquido'] / df['Patrimônio Líquido']
    # Lucro Líquido: DRE
    # Patrimônio Líquido: BP
    # => O retorno sobre o patrimônio líquido (ROE) mede a eficiência da empresa em gerar lucro a partir de seu patrimônio líquido.

    indices['Endividamento'] = df['Passivo Total'] / df['Ativo Total']
    # Passivo Total: BP
    # Ativo Total: BP
    # => O endividamento mede a proporção de dívidas da empresa em relação ao total de ativos.

    indices['Cobertura de Juros'] = df['EBIT'] / df['Despesa de Juros']
    # EBIT: DRE (Lucro antes de juros e impostos)
    # Despesa de Juros: DRE
    # => A cobertura de juros mede a capacidade da empresa de pagar seus juros com seu lucro antes de juros e impostos.
    # => Reflete a capacidade de gerar resultados com suas atividades principais
    
    indices['Giro do Ativo'] = df['Receita Total'] / df['Ativo Total']
    # Ativo Total: BP
    # Receita Total: DRE
    # => O giro do ativo mede a eficiência da empresa em gerar receita a partir de seus ativos.

    indices['Período Médio de Recebimento'] = df['Contas a Receber'] / df['Receita Total'] * 365
    # Contas a Receber: BP
    # Receita Total: DRE
    # => O período médio de recebimento mede o tempo médio que a empresa leva para receber suas vendas.

    indices['Período Médio de Pagamento'] = df['Contas a Pagar'] / df['Custos'] * 365
    # Contas a Pagar: BP
    # Custos: DRE
    # => O período médio de pagamento mede o tempo médio que a empresa leva para pagar seus custos.

    return pd.DataFrame(indices)

# Função para categorizar escores consolidados
def categorizar_escores_consolidados(escores):
    categorias = []
    for escore in escores:
        if escore > 2:
            categorias.append("Muito Abaixo do Risco")
        elif 1 < escore <= 2:
            categorias.append("Abaixo do Risco")
        elif -1 <= escore <= 1:
            categorias.append("Neutro")
        elif -2 <= escore < -1:
            categorias.append("Acima do Risco")
        else:
            categorias.append("Muito Acima do Risco")
    return categorias

# %% [markdown]
# **Passo 1**

# %% [markdown]
# *Lançamento dos dados pelo funcionário (analista, economiário, escriturário)*

# %% [markdown]
# ##### 1. LANÇAMENTO DOS DADOS #####

# %%
# Importar os dados do Excel
# Do mais recente para o mais antigo
df_dados_contabeis = pd.read_excel('dados_contabeis_global.xlsx')  # Insira o nome correto do arquivo
print("Dados Contabeis Importados:")
print(df_dados_contabeis)

# %% [markdown]
# **Passo 2**

# %% [markdown]
# *Cálculo do modelo Finscore 5A*

# %% [markdown]
# ##### 2. PROCESSAMENTO DO MODELO #####

# %% [markdown]
# 2.1 Índices contábeis

# %%
# Calcular os índices contábeis
df_indices = calcular_indices_contabeis(df_dados_contabeis)
print("\nÍndices Contábeis Calculados:")
print(df_indices)

#relatório

# %% [markdown]
# 2.2 Padronização dos índices contábeis

# %%
# Escalar os índices contábeis para o PCA
scaler = StandardScaler()
indices_scaled = scaler.fit_transform(df_indices)
print("\nÍndices Escalados para PCA:")
print(indices_scaled)

# %% [markdown]
# 2.3 Cálculo do PCA

# %%
# Realizar o PCA
pca = PCA()
pca_result = pca.fit_transform(indices_scaled)
print("\nComponentes Principais (PCA):")
print(pca_result)

#relatório


# %% [markdown]
# 2.4 Variância Explicada PCA

# %%
# Variância explicada pelos componentes principais
explained_variance_ratio = pca.explained_variance_ratio_
print("\nVariância Explicada por Componente:")
print(explained_variance_ratio)

#relatório

# %% [markdown]
# 2.5 DataFrame PCA

# %%
# DataFrame com os componentes principais
pca_df = pd.DataFrame(pca_result, columns=[f"PC{i+1}" for i in range(pca_result.shape[1])])
print("\nMatriz de Componentes Principais:")
print(pca_df)

#relatório

# %% [markdown]
# 2.6 Matriz de cargas

# %%
# Obter a matriz de cargas
loadings = pd.DataFrame(
    pca.components_,
    columns=df_indices.columns,
    index=[f"PC{i+1}" for i in range(pca.components_.shape[0])]
)

print("Matriz de Cargas dos Componentes Principais:")
print(loadings)

# Identificar os índices mais significativos para cada PC
print("\nÍndices mais significativos por componente:")
for pc in loadings.index:
    print(f"\n{pc}:")
    print(loadings.loc[pc].abs().sort_values(ascending=False).head(3))  # Top 3 índices mais significativos

#relatório

# %% [markdown]
# 2.6 Escore final

# %%
pca_df.dot(explained_variance_ratio)

# %%
print(df_dados_contabeis)

# %%
# Calcular o escore consolidado com penalização do último ano
# Do mais recente para o mais antigo: 0.5, 0.3, 0.2
pesos = [0.5, 0.3, 0.2]  # Pesos para os três anos
escores_consolidados = (pca_df.dot(explained_variance_ratio) * pesos).sum()
print("\nEscore Consolidado:")
print(escores_consolidados)

# Categorizar os escores consolidados
categoria = categorizar_escores_consolidados([escores_consolidados])
print("\nCategoria Final:")
print(categoria)

#relatório


