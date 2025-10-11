# components/config.py
"""
Configurações e constantes compartilhadas para evitar dependências circulares
"""

"""
Convenções de navegação
- SLUG_MAP: slug na URL (?p=slug) -> label da página usada no estado/ROUTES
- SIDEBAR_MENU: estrutura hierárquica da sidebar (suporta submenus)
- SIDEBAR_PAGES: compatibilidade legada (apenas topo), mantido para não quebrar imports
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
    "contato": "Contato",
    "proc": "Processo",
    # Extras usados no submenu Sobre
    "faq": "FAQ",
    "glossario": "Glossário",
}

# Estrutura hierárquica do menu lateral (labels devem existir em SLUG_MAP)
# Você pode acrescentar novos grupos/itens seguindo o mesmo padrão.
SIDEBAR_MENU = [
    {
        "label": "Processo",
        "slug": "proc",
        "icon": "diagram-3",
        "children": [
            {"label": "Novo", "slug": "novo"},
            {"label": "Lançamentos", "slug": "lanc"},
            {"label": "Análise", "slug": "analise"},
            {"label": "Parecer", "slug": "parecer"},
        ],
    },
    {"label": "Sobre", "slug": "sobre", "icon": "info-circle", "children": []},
    {"label": "Contato", "slug": "contato", "icon": "envelope", "children": []},
]

# Compat: lista simples apenas com topo (evite usar em novo código)
SIDEBAR_PAGES = [item["label"] for item in SIDEBAR_MENU]

# Páginas disponíveis na topbar
TOPBAR_PAGES = ["Home", "Definir1", "Definir2", "Guia Rápido"]

# Configuração de debug
DEBUG_MODE = True