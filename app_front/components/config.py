# components/config.py
"""
Configurações e constantes compartilhadas para evitar dependências circulares
"""

# Mapeamento de slugs para nomes de páginas
SLUG_MAP = {
    "home": "Home",
    "novo": "Novo",
    "def1": "Definir1", 
    "def2": "Definir2",
    "guia": "Guia Rápido", 
    "lanc": "Lançamentos",
    "analise": "Análise",
    "parecer": "Parecer",
    "sobre": "Sobre",
    "contato": "Contato"
}

# Todas as páginas disponíveis na sidebar
SIDEBAR_PAGES = ["Novo", "Lançamentos", "Análise", "Parecer", "Sobre", "Contato"]

# Páginas disponíveis na topbar
TOPBAR_PAGES = ["Home", "Definir1", "Definir2", "Guia Rápido"]

# Configuração de debug
DEBUG_MODE = False