# app.py
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# Importa os layouts modulares
from dados.upload_form import layout as input_layout
from dashboard.layout import layout as output_layout
from parecer.ia_report import layout as report_layout

# Inicialização
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Layout da Página 1 - Login
login_layout = dbc.Container([
    html.H2("Login - FinScore"),
    dbc.Input(id='username', placeholder='Usuário', type='text', className='mb-2'),
    dbc.Input(id='password', placeholder='Senha', type='password', className='mb-2'),
    dbc.Button('Entrar', id='login-button', color='primary'),
    html.Div(id='login-message', className='text-danger mt-2')
])

# App Layout principal com roteamento
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Roteamento entre páginas
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/dados':
        return input_layout
    elif pathname == '/dashboard':
        return output_layout
    elif pathname == '/parecer':
        return report_layout
    else:
        return login_layout

# Autenticação simples
@app.callback(
    Output('login-message', 'children'),
    Output('url', 'pathname'),
    Input('login-button', 'n_clicks'),
    State('username', 'value'),
    State('password', 'value'),
    prevent_initial_call=True
)
def login(n_clicks, username, password):
    if username == 'admin' and password == '123':
        return '', '/dados'
    return 'Usuário ou senha inválidos', dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)
