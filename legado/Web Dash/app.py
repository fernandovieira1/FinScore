import pandas as pd
import base64
import io

from script.finscore_core import executar_finscore  # ajuste se o nome for outro

@app.callback(
    Output('process-status', 'children'),
    Output('resultado-dashboard', 'children'),
    Input('process-button', 'n_clicks'),
    State('upload-excel', 'contents'),
    State('link-google-sheets', 'value'),
    prevent_initial_call=True
)
def processar_finscore(n_clicks, excel_contents, google_sheets_link):
    df = None

    try:
        # Caso 1: Upload de Excel
        if excel_contents:
            content_type, content_string = excel_contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_excel(io.BytesIO(decoded))

        # Caso 2: Link do Google Sheets
        elif google_sheets_link:
            try:
                # Extrai a ID da planilha do link
                import re
                match = re.search(r"/d/([a-zA-Z0-9-_]+)", google_sheets_link)
                sheet_id = match.group(1)
                sheet_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'

                df = pd.read_excel(sheet_url)
            except Exception as e:
                return f"Erro ao processar o link do Google Sheets: {str(e)}", None

        if df is None:
            return "Nenhum dado foi carregado. Faça o upload ou cole o link.", None

        # Processa com o FinScore
        resultado = executar_finscore(df)

        # Mostra algo simples por enquanto
        return "FinScore calculado com sucesso!", html.Pre(str(resultado))

    except Exception as e:
        return f"Ocorreu um erro no processamento: {str(e)}", None
