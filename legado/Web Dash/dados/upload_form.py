from dash import html, dcc
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H2("Lançamento de Dados – FinScore", className="mb-4"),

    # Nome da empresa
    dbc.Label("Nome da Empresa:"),
    dbc.Input(id='cliente', type='text', placeholder="Ex: CARGOBR TRANSPORTES", className="mb-3"),

    # Ano inicial
    dbc.Label("Ano Inicial da Análise:"),
    dbc.Input(id='ano_inicial', type='number', placeholder="Ex: 2021", className="mb-3"),

    # Ano final
    dbc.Label("Ano Final da Análise:"),
    dbc.Input(id='ano_final', type='number', placeholder="Ex: 2023", className="mb-3"),

    # Score Serasa
    dbc.Label("Score do Serasa:"),
    dbc.Input(id='serasa', type='number', placeholder="Ex: 550", className="mb-3"),

    # Link do Google Sheets
    dbc.Label("Link da planilha do Google Sheets:"),
    dbc.Input(id='link_google', type='url', placeholder="Cole o link da planilha aqui", className="mb-4"),

    # Botão de submissão
    dbc.Button("Processar FinScore", id='process-button', color='success', className="mb-3"),

    # Status do processamento
    html.Div(id='process-status', className="mt-2")
], fluid=True)
