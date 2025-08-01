import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def calcular_indices_contabeis(df):
    indices = {}

    # RENTABILIDADE
    indices['Margem Líquida'] = df['r_Lucro_Liquido'] / df['r_Receita_Total']
    indices['ROA'] = df['r_Lucro_Liquido'] / df['p_Ativo_Total']
    indices['ROE'] = df['r_Lucro_Liquido'] / df['p_Patrimonio_Liquido']

    # EBITDA e Margem
    ebit = df['r_Lucro_Liquido'] + df['r_Despesa_de_Juros'] + df['r_Despesa_de_Impostos']
    amort = df.get('r_Amortizacao', 0).fillna(0)
    depr = df.get('r_Depreciacao', 0).fillna(0)
    ebitda = ebit + amort + depr
    indices['EBITDA'] = ebitda
    indices['Margem EBITDA'] = ebitda / df['r_Receita_Total']

    # Alavancagem e Endividamento
    df['p_Divida_Bruta'] = df['p_Passivo_Total'] - df['p_Patrimonio_Liquido']
    df['p_Divida_Liquida'] = df['p_Divida_Bruta'] - df['p_Caixa']
    indices['Alavancagem'] = df['p_Divida_Liquida'] / ebitda
    indices['Endividamento'] = df['p_Divida_Bruta'] / df['p_Ativo_Total']

    # Estrutura de Capital
    df['p_Imobilizado'] = df['p_Ativo_Total'] - df['p_Ativo_Circulante']
    indices['Imobilizado/Ativo'] = df['p_Imobilizado'] / df['p_Ativo_Total']

    # Cobertura de Juros
    indices['Cobertura de Juros'] = ebit / df['r_Despesa_de_Juros']

    # Eficiência e Ciclo
    indices['Giro do Ativo'] = df['r_Receita_Total'] / df['p_Ativo_Total']
    indices['Período Médio de Recebimento'] = df['p_Contas_a_Receber'] / df['r_Receita_Total'] * 365
    indices['Período Médio de Pagamento'] = df['p_Contas_a_Pagar'] / df['r_Custos'] * 365

    # Liquidez
    indices['Liquidez Corrente'] = df['p_Ativo_Circulante'] / df['p_Passivo_Circulante']
    indices['Liquidez Seca'] = (df['p_Ativo_Circulante'] - df['p_Estoques']) / df['p_Passivo_Circulante']
    indices['CCL/Ativo Total'] = (df['p_Ativo_Circulante'] - df['p_Passivo_Circulante']) / df['p_Ativo_Total']

    df_indices = pd.DataFrame(indices)
    df_indices.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df_indices

def executar_finscore(df_dados_contabeis, nome_empresa, ano_inicial, ano_final, serasa_score):
    df_indices = calcular_indices_contabeis(df_dados_contabeis).round(2)
    if (df_dados_contabeis['p_Estoques'] == 0).all():
        df_indices.drop('Liquidez Seca', axis=1, inplace=True, errors='ignore')

    # Padronizar os índices
    scaler = StandardScaler()
    indices_scaled = scaler.fit_transform(df_indices)

    # PCA
    pca = PCA()
    pca_result = pca.fit_transform(indices_scaled)
    explained_variance_ratio = pca.explained_variance_ratio_

    # Matriz de componentes principais
    pca_df = pd.DataFrame(pca_result, columns=[f'PC{i+1}' for i in range(pca_result.shape[1])])

    # Matriz de cargas e top 3 índices por componente
    loadings = pd.DataFrame(
        pca.components_,
        columns=df_indices.columns,
        index=[f'PC{i+1}' for i in range(pca.components_.shape[0])]
    )

    top_indices_df = pd.DataFrame([
        {
            'PC': pc,
            'Indice 1': top.index[0],
            'Peso 1': round(top.values[0], 3),
            'Indice 2': top.index[1],
            'Peso 2': round(top.values[1], 3),
            'Indice 3': top.index[2],
            'Peso 3': round(top.values[2], 3)
        }
        for pc, top in {
            pc: loadings.loc[pc].abs().sort_values(ascending=False).head(3)
            for pc in loadings.index
        }.items()
    ])

    # Cálculo do FinScore Bruto
    pesos = [0.6, 0.25, 0.15]
    finscore_bruto = round((pca_df.dot(explained_variance_ratio) * pesos).sum(), 2)

    # FinScore Ajustado
    finscore_ajustado = round(min(((finscore_bruto + 2)/4)*1000, 1000), 2)

    # Classificações
    def classificar_finscore(valor):
        if valor > 875:
            return 'Muito Abaixo do Risco'
        elif 750 < valor <= 875:
            return 'Levemente Abaixo do Risco'
        elif 250 <= valor <= 750:
            return 'Neutro'
        elif 125 < valor < 250:
            return 'Levemente Acima do Risco'
        else:
            return 'Muito Acima do Risco'

    def classificar_serasa(score):
        if score > 700:
            return 'Excelente'
        elif score > 500:
            return 'Bom'
        elif score > 300:
            return 'Baixo'
        else:
            return 'Muito Baixo'

    resultado = {
        "empresa": nome_empresa,
        "periodo": f"{ano_inicial}–{ano_final}",
        "finscore_bruto": finscore_bruto,
        "finscore_ajustado": finscore_ajustado,
        "classificacao_finscore": classificar_finscore(finscore_ajustado),
        "serasa": serasa_score,
        "classificacao_serasa": classificar_serasa(serasa_score),
        "df_indices": df_indices,
        "df_pca": pca_df,
        "top_indices_df": top_indices_df,
        "loadings": loadings
    }

    return resultado
