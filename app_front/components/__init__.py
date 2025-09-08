# components/__init__.py
"""
Package initialization for components
"""
from .config import SLUG_MAP, SIDEBAR_PAGES, TOPBAR_PAGES, DEBUG_MODE
from .state_manager import AppState
from .nav import render_sidebar
from .topbar import render_topbar

# Aliases para compatibilidade
PAGES = SIDEBAR_PAGES