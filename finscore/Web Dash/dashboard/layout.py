from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H2("Dashboard FinScore"),
    html.Div(id='dados-dashboard'),
    dbc.Button('Gerar Parecer com IA', id='generate-report', color='info', className='mt-3')
])
