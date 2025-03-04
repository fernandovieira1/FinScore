# %% [markdown]
# <a href="https://colab.research.google.com/github/fernandovieira1/FinScore/blob/main/FINSCORE.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# %% [markdown]
# **# INTRUÇÕES**

# %% [markdown]
# * Antes de iniciar, certifique-se de estar logado na sua conta Google.
# 
# * Um botão azul 'Fazer login', localizado no canto superior direito da tela, aparecerá, se não.
# 
# * Feito isto, basta inserir os dados nas seções abaixo descritas:
#     - 1.1 Cliente
#     - 1.2 Período
#     - 1.3 Lançamento dos dados Contábeis
# 
# * Cada uma das seções mencionadas possui anotações sobre como proceder.
# 
# * Logo após, clique no menu "Ambiente de execução" e em "Executar tudo" (ou CTR + F9), nesta ordem.

# %% [markdown]
# ##### 1. LANÇAMENTO DOS DADOS #####

# %% [markdown]
# ##### 1.1 Cliente

# %% [markdown]
# *--> Insira o nome do cliente/empresa*

# %%
# Cliente
cliente = 'Testes FinScore_Assertif_Empresas FEV-2025.xlsx'

# %% [markdown]
# ##### 1.2 Período

# %% [markdown]
# *--> Insira os anos inicial (a primeira) e final (da última) das demonstrações contábeis que serviram de base para a análise*

# %%
# Ano Inicial
ano_inicial = 2021

# %%
# Ano Final
ano_final = 2023

# %% [markdown]
# ##### 1.3 Lançamento dos dados Contábeis

# %% [markdown]
# *--> Acesse a planilha abaixo (CTRL + click) e insira as informações nas linhas e colunas respectivas*

# %%
# Lance do ano mais recente para o mais antigo
'https://docs.google.com/spreadsheets/d/1-BCv3gjwJ34HZqjWpOQxqXU1q_3s3r33/edit?gid=1575975872#gid=1575975872'

# %% [markdown]
# *--> Agora basta clicar no menu "Ambiente de execução" e em "Executar tudo" (ou CTR + F9), nesta ordem.*

# %% [markdown]
# ##### CONFIGURAÇÃO DO AMBIENTE

# %% [markdown]
# ##### Configuração do ambiente

# %%
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import sys
import subprocess
import importlib.util


# %%
%%capture
# Lista de pacotes necessários
required_packages = ["gspread", "pandas", "gspread_dataframe", "openpyxl"]

# Verificar e instalar pacotes que não estão instalados
def install_missing_packages(packages):
    for package in packages:
        if importlib.util.find_spec(package) is None:
            print(f"⚠ Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
        else:
            print(f"✔ {package} já está instalado")

install_missing_packages(required_packages)

# %%
# Definir o ID da planilha e da aba (worksheet)
sheet_id = "1-BCv3gjwJ34HZqjWpOQxqXU1q_3s3r33"
gid = "1575975872"  # ID da aba específica

# Construir a URL para baixar a planilha como um arquivo Excel (.xlsx)
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&id={sheet_id}&gid={gid}"

# Ler a planilha diretamente no Pandas
df_dados_contabeis = pd.read_excel(url, engine="openpyxl")

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



# %% [markdown]
# ##### Criação de funções

# %%


# %% [markdown]
# ##### Importação dos Dados Contábeis

# %%
## Importar os dados
# - Do mais recente para o mais antigo

# arquivo_dados_contabeis = '/content/dados_contabeis_global.xlsx'
arquivo_dados_contabeis = df_dados_contabeis

# %%
arquivo_dados_contabeis

# %% [markdown]
# ##### Leitura dos Dados Contábeis

# %%
df_dados_contabeis = arquivo_dados_contabeis
print('Dados Contabeis Importados:')
print(df_dados_contabeis)

# %% [markdown]
# ##### 2. PROCESSAMENTO DO MODELO #####

# %% [markdown]
# ##### 2.1 Índices contábeis

# %%
df_indices = calcular_indices_contabeis(df_dados_contabeis).round(2)
print('\nÍndices Contábeis Calculados:')

# %%
if (df_dados_contabeis['Estoques'] == 0).all():
        del df_indices['Liquidez Seca']

# %%
print(df_indices)

# %% [markdown]
# ##### 2.2 Padronização dos índices contábeis

# %%
# Escalar os índices contábeis para o PCA
scaler = StandardScaler()
indices_scaled = scaler.fit_transform(df_indices)
print('\nÍndices Escalados para PCA:')
print(indices_scaled)

# %% [markdown]
# ##### 2.3 Cálculo do PCA

# %%
# Realizar o PCA
pca = PCA()
pca_result = pca.fit_transform(indices_scaled)
print('\nComponentes Principais (PCA):')
print(pca_result)

#relatório


# %% [markdown]
# ##### 2.4 Variância Explicada PCA

# %%
# Variância explicada pelos componentes principais
explained_variance_ratio = pca.explained_variance_ratio_
print('\nVariância Explicada por Componente:')
print(explained_variance_ratio)

#relatório

# %% [markdown]
# ##### 2.5 DataFrame PCA

# %%
# DataFrame com os componentes principais
pca_df = pd.DataFrame(pca_result, columns=[f'PC{i+1}' for i in range(pca_result.shape[1])])
print('\nMatriz de Componentes Principais:')
print(pca_df)

#relatório

# %% [markdown]
# ##### 2.6 Matriz de cargas

# %%
# Obter a matriz de cargas
loadings = pd.DataFrame(
    pca.components_,
    columns=df_indices.columns,
    index=[f'PC{i+1}' for i in range(pca.components_.shape[0])]
)

print('Matriz de Cargas dos Componentes Principais:')
print(loadings)

# Identificar os índices mais significativos para cada PC
print('\nÍndices mais significativos por componente:')
for pc in loadings.index:
    print(f'\n{pc}:')
    print(loadings.loc[pc].abs().sort_values(ascending=False).head(3))  # Top 3 índices mais significativos

#relatório

# %% [markdown]
# ##### 2.7 Escore final

# %%
pca_df.dot(explained_variance_ratio)

# %% [markdown]
# ##### 3. RESULTADOS #####

# %% [markdown]
# ##### 3.1 Valor do Escore Calculado

# %%
# Calcular o escore consolidado com penalização do último ano
# Do mais recente para o mais antigo: 0.5, 0.3, 0.2
pesos = [0.6, 0.25, 0.15]  # Pesos para os três anos
escores_consolidados = round((pca_df.dot(explained_variance_ratio) * pesos).sum(), 2)
print('\nFinscore:')
print(escores_consolidados)

# %% [markdown]
# ##### 3.2 Classificação do Escore

# %%
# Categorizar os escores consolidados
categoria = categorizar_escores_consolidados([escores_consolidados])
print('\nCategoria Final:')
print(categoria)

# %% [markdown]
# ##### 3.3 Valores e Contas Contábeis

# %%
df_dados_contabeis
# Sendo 0 o mais recente e 2 o mais antigo

# %% [markdown]
# ##### 3.4 Índices contábeis

# %%
print(df_indices)
# Sendo 0 o mais recente e 2 o mais antigo


# %% [markdown]
# ##### 4. APRESENTAÇÃO #####

# %% [markdown]
# ##### 4.1 Criação dos dfs

# %%
# Df resultados principais
resultados_df = pd.DataFrame({
    'Métrica': ['Escore Consolidado', 'Categoria Final'],
    'Valor': [escores_consolidados, categoria[0]]
})
resultados_df

# %%
resultados_df.iloc[0, 1]

# %% [markdown]
# ##### 4.2 Tabela Resumo

# %%
import pandas as pd
import matplotlib.pyplot as plt

# --- Ajuste principal: inverter a ordem do df_indices se necessário ---
# Se seu df_indices estiver 2024, 2023, 2022, por exemplo,
# esta linha garante a ordem 2022, 2023, 2024.
df_indices = df_indices.iloc[::-1].reset_index(drop=True)

## FORMATAR PADRÃO BR
# Cópia do df original
df_dados_contabeis_milhoes = df_dados_contabeis.copy()

# Excluindo a coluna 'Ano' antes de realizar as transformações
df_dados_contabeis_milhoes = df_dados_contabeis_milhoes.drop(columns=['Ano'])

# Dividindo os valores das colunas numéricas por 1.000.000
for col in df_dados_contabeis_milhoes.columns:
    df_dados_contabeis_milhoes[col] = df_dados_contabeis_milhoes[col] / 1_000_000

# Formatando os valores para o padrão brasileiro (R$ 1.000.000,00)
df_dados_contabeis_milhoes = df_dados_contabeis_milhoes.applymap(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(x, (int, float)) else x
)

## INSERIR A COLUNA "ANO" NAS TABELAS "Dados Contábeis" e "Índices Financeiros"
anos = [str(ano_inicial), str(ano_inicial + 1), str(ano_final)]  # Convertendo anos para string

# Inserindo a coluna "Ano" como a primeira coluna
df_dados_contabeis_milhoes.insert(0, "Ano", anos)
df_indices.insert(0, "Ano", anos)

## FINSCORE
resultados_df = pd.DataFrame({
    "FINSCORE": ["Valor", "Classificação"],
    "RESULTADO": [resultados_df.iloc[0, 1], resultados_df.iloc[1, 1]]
})

## INSERINDO QUEBRA DE LINHA NOS CABEÇALHOS
df_dados_contabeis_milhoes.columns = [col.replace(" ", "\n") for col in df_dados_contabeis_milhoes.columns]
df_indices.columns = [col.replace(" ", "\n") for col in df_indices.columns]
resultados_df.columns = [col.replace(" ", "\n") for col in resultados_df.columns]

## CABEÇALHO
fig, axs = plt.subplots(nrows=3, figsize=(14, 12))
fig.suptitle(
    f"CÁLCULO FINSCORE - {cliente} - Período base {ano_inicial} - {ano_final}",
    fontsize=14, fontweight="bold"
)

## TABELAS
def add_table(ax, df, title):
    ax.axis("tight")
    ax.axis("off")
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center", loc="center",
        colWidths=[0.12] * len(df.columns)  # Ajustando largura das colunas
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)  # Ajustando escala para melhor legibilidade

    # Aumentando a altura da linha do cabeçalho
    for col in range(len(df.columns)):
        table[(0, col)].set_height(0.3)

    # Destacando o cabeçalho com negrito
    for key, cell in table._cells.items():
        if key[0] == 0:  # Se for a primeira linha (cabeçalho)
            cell.set_fontsize(10)
            cell.set_text_props(weight='bold')

    ax.set_title(title, fontsize=12, fontweight="bold", pad=2)
    ax.title.set_y(0.9)

# Adicionando cada tabela
add_table(axs[0], resultados_df, "FinScore Calculado")
add_table(axs[1], df_dados_contabeis_milhoes, "Dados Contábeis\n(Em Milhões de R$)")
add_table(axs[2], df_indices, "Índices Financeiros")

plt.show()


# %% [markdown]
# #### 5. Prompt IA

# %%
print('\n INÍCIO')
print('=====================================')

print('- Crie um relatório interpretando os resultados dos cálculos feitos neste notebook, utilizando os valores das seguintes variáveis:\n')

print('* Cliente:')
print('-------------------------------')
print(cliente)

print('\n * Período da analise:')
print('-------------------------------')
print(ano_inicial, '-', ano_final)

print('\n * Dados contábeis:')
print('-------------------------------')
print(df_dados_contabeis)

print('\n * Índices Contábeis:')
print('-------------------------------')
print(df_indices)

print('\n - Analise o Cliente com base nos dfs abaixo. Interprete as saídas à vista dos dados contábeis e dos índices contábeis supracitados, contextualizando em termos de capacidade de pagamento, liquidez e resultados operacionais o que os resultados indicam.')

print('\n RESULTADOS PCA')
print('=====================================')

print('\n DF: indices_scaled:')
print('-------------------------------')
print(indices_scaled)

print('\n DF: pca_result:')
print('-------------------------------')
print(pca_result)

print('\n DF: explained_variance_ratio:')
print('-------------------------------')
print(explained_variance_ratio)

print('\n DF: pca_df:')
print('-------------------------------')
print(pca_df)

print('\n DF: loadings:')
print('-------------------------------')
print(loadings)

print('\n Finscore Final')
print('-------------------------------')
print(resultados_df.iloc[0, 1])

print('O Finscore Final é classificado segundo os seguintes critérios')

criterios_escore = """def categorizar_escores_consolidados(escores):
    categorias = []
    for escore in escores:
        if escore > 2:
            categorias.append('Muito Abaixo do Risco')
        elif 1 < escore <= 2:
            categorias.append('Abaixo do Risco')
        elif -1 <= escore <= 1:
            categorias.append('Neutro')
        elif -2 <= escore < -1:
            categorias.append('Acima do Risco')
        else:
            categorias.append('Muito Acima do Risco')
    return categorias
"""

print(criterios_escore)

print('\n Evite termos estatísticos e técnicos, sequer é necessário apresentar os valores relacionados ao PCA, mas cite os valores e contas dos dataframes df_dados_contabeis e df_indices, com a devida explicação (o que a conta ou índice significa), implicação em relação aos resultados e valores citados.')

print('\n Após esta contextualização, com base nos resultados do PCA (RESULTADOS PCA), apresente a tabela resumo citada em 4.2:')

print('\n O importante é você fechar com os valores da variável "escores_consolidados" e "categoria", com a devida interpretação final.')

print('\n FIM')
print('=====================================')



