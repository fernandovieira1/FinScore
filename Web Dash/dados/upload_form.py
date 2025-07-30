from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H2("Lançamento de Dados"),
    dbc.Input(id='nome-empresa', placeholder='Nome da empresa', type='text', className='mb-2'),
    dbc.Input(id='periodo', placeholder='Período (ex: 2021-2023)', type='text', className='mb-2'),
    dbc.Button('Processar FinScore', id='process-button', color='success'),
    html.Div(id='process-status', className='mt-2')
])
