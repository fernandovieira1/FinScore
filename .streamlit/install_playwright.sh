#!/bin/bash
# Script para instalar Chromium do Playwright no Streamlit Cloud
# Este script é executado automaticamente durante o deploy

echo "🚀 Instalando Chromium para Playwright..."
python -m playwright install chromium --with-deps

echo "✅ Chromium instalado com sucesso!"
