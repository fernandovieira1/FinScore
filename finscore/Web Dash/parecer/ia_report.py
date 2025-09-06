from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H2("Parecer Automático IA"),
    html.Div(id='ia-report'),
    dbc.Button('Exportar para Word', id='export-button', color='secondary', className='mt-3')
])
