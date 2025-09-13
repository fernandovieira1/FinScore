# app_front/utils_finscore.py
## Biblioteca de funções para cálculo do FinScore
### Baseado em metodologia do 9.7 (finscore\v9\FINSCORE_v9.7.ipynb), adaptado para o app
#### Autor: Fernando Vieira
import numpy as np
import pandas as pd
"""
Nota: As dependências do scikit-learn são importadas dentro da função executar_finscore
para evitar falhas na importação do módulo quando o app é iniciado com o Python errado.
"""

# ---------------------------
# 1) Índices contábeis
# ---------------------------
def calcular_indices_contabeis(df: pd.DataFrame) -> pd.DataFrame:
    idx = {}

    # RENTABILIDADE
    idx['Margem Líquida'] = df['r_Lucro_Liquido'] / df['r_Receita_Total']
    idx['ROA']             = df['r_Lucro_Liquido'] / df['p_Ativo_Total']
    idx['ROE']             = df['r_Lucro_Liquido'] / df['p_Patrimonio_Liquido']

    # EBITDA e Margem
    ebit  = df['r_Lucro_Liquido'] + df['r_Despesa_de_Juros'] + df['r_Despesa_de_Impostos']
    amort = df.get('r_Amortizacao', pd.Series(0, index=df.index)).fillna(0)
    depr  = df.get('r_Depreciacao', pd.Series(0, index=df.index)).fillna(0)
    ebitda = ebit + amort + depr
    idx['EBITDA']        = ebitda
    idx['Margem EBITDA'] = ebitda / df['r_Receita_Total']

    # Alavancagem / Endividamento
    df = df.copy()
    df['p_Divida_Bruta']  = df['p_Passivo_Total'] - df['p_Patrimonio_Liquido']
    df['p_Divida_Liquida'] = df['p_Divida_Bruta'] - df['p_Caixa']
    idx['Alavancagem']   = df['p_Divida_Liquida'] / ebitda
    idx['Endividamento'] = df['p_Divida_Bruta'] / df['p_Ativo_Total']

    # Estrutura de Capital
    df['p_Imobilizado'] = df['p_Ativo_Total'] - df['p_Ativo_Circulante']
    idx['Imobilizado/Ativo'] = df['p_Imobilizado'] / df['p_Ativo_Total']

    # Cobertura de Juros
    idx['Cobertura de Juros'] = ebit / df['r_Despesa_de_Juros']

    # Eficiência e Ciclo
    idx['Giro do Ativo']                 = df['r_Receita_Total'] / df['p_Ativo_Total']
    idx['Período Médio de Recebimento'] = df['p_Contas_a_Receber'] / df['r_Receita_Total'] * 365
    idx['Período Médio de Pagamento']   = df['p_Contas_a_Pagar']   / df['r_Custos']        * 365

    # Liquidez
    idx['Liquidez Corrente'] = df['p_Ativo_Circulante'] / df['p_Passivo_Circulante']
    idx['Liquidez Seca']     = (df['p_Ativo_Circulante'] - df['p_Estoques']) / df['p_Passivo_Circulante']
    idx['CCL/Ativo Total']   = (df['p_Ativo_Circulante'] - df['p_Passivo_Circulante']) / df['p_Ativo_Total']

    df_indices = pd.DataFrame(idx)
    df_indices.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df_indices.round(2)

# ---------------------------
# 2) Classificadores
# ---------------------------
def classificar_finscore_ajustado(valor: float) -> str:
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

def classificar_serasa(score: int) -> str:
    if score > 700:
        return 'Excelente'
    elif score > 500:
        return 'Bom'
    elif score > 300:
        return 'Baixo'
    else:
        return 'Muito Baixo'

def classificar_finscore_bruto(valor: float) -> str:
    if valor > 1.5:
        return 'Muito Abaixo do Risco'
    elif 1.0 < valor <= 1.5:
        return 'Levemente Abaixo do Risco'
    elif -1.0 <= valor <= 1.0:
        return 'Neutro'
    elif -1.5 < valor < -1.0:
        return 'Levemente Acima do Risco'
    else:
        return 'Muito Acima do Risco'

# ---------------------------
# 3) Principal
# ---------------------------
def executar_finscore(
    df_dados_contabeis: pd.DataFrame,
    nome_empresa: str,
    ano_inicial: int,
    ano_final: int,
    serasa_score: int
) -> dict:

    # (opcional) garantir ordem: mais recente -> mais antigo
    df_dc = df_dados_contabeis.copy()
    if 'ano' in df_dc.columns:
        # na 9.7 o "0" é o mais recente; manter 0,1,2...
        df_dc = df_dc.sort_values('ano', ascending=True).reset_index(drop=True)

    # Índices
    df_indices = calcular_indices_contabeis(df_dc)

    # Se todos os estoques são 0, remover Liquidez Seca do PCA
    if (df_dc['p_Estoques'] == 0).all():
        df_indices.drop('Liquidez Seca', axis=1, inplace=True, errors='ignore')

    # Padronização e PCA (imports tardios para evitar crash ao iniciar o app sem sklearn)
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA
    except Exception as e:
        raise ImportError(
            "scikit-learn não está disponível no ambiente atual. "
            "Execute o app com a venv do projeto (.venv) ou instale as dependências: "
            "pip install -r requirements.txt"
        ) from e

    scaler = StandardScaler()
    X = scaler.fit_transform(df_indices.fillna(0))       # robusto a eventuais NaNs
    pca = PCA()
    Z = pca.fit_transform(X)

    explained = pca.explained_variance_ratio_
    pca_df = pd.DataFrame(Z, columns=[f'PC{i+1}' for i in range(Z.shape[1])])

    # Loadings e "top 3"
    loadings = pd.DataFrame(
        pca.components_,
        columns=df_indices.columns,
        index=[f'PC{i+1}' for i in range(pca.components_.shape[0])]
    )
    top_indices_df = pd.DataFrame([
        {
            'PC': pc,
            'Indice 1': top.index[0], 'Peso 1': round(top.values[0], 3),
            'Indice 2': top.index[1], 'Peso 2': round(top.values[1], 3),
            'Indice 3': top.index[2], 'Peso 3': round(top.values[2], 3),
        }
        for pc, top in {
            pc: loadings.loc[pc].abs().sort_values(ascending=False).head(3)
            for pc in loadings.index
        }.items()
    ])

    # === FINSCORE BRUTO (como na 9.7) ===
    # 1) um score por ano: combinação dos PCs ponderados pela variância explicada
    scores_por_ano = pca_df.dot(explained)  # shape = (n_anos,)
    # 2) pesos do mais recente para o mais antigo
    w = np.array([0.6, 0.25, 0.15], dtype=float)
    if len(scores_por_ano) < len(w):
        w = w[:len(scores_por_ano)]
    elif len(scores_por_ano) > len(w):
        w = np.pad(w, (0, len(scores_por_ano) - len(w)), constant_values=0.0)
    finscore_bruto = round(float((scores_por_ano.values * w).sum()), 2)

    # === FINSCORE AJUSTADO (0..1000) ===
    finscore_ajustado = round(min(((finscore_bruto + 2) / 4) * 1000, 1000), 2)

    return {
        "empresa": nome_empresa,
        "periodo": f"{ano_inicial}–{ano_final}",
        "finscore_bruto": finscore_bruto,
        "classificacao_finscore_bruto": classificar_finscore_bruto(finscore_bruto),
        "finscore_ajustado": finscore_ajustado,
        "classificacao_finscore": classificar_finscore_ajustado(finscore_ajustado),
        "serasa": int(serasa_score),
        "classificacao_serasa": classificar_serasa(int(serasa_score)),
        "df_indices": df_indices,
        "df_pca": pca_df,
        "top_indices_df": top_indices_df,
        "loadings": loadings,
    }
