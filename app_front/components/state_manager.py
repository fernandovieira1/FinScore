# components/state_manager.py
import streamlit as st
from typing import Optional
import time
from components.config import SLUG_MAP, DEBUG_MODE

class AppState:
    """Gerenciador centralizado de estado para o aplicativo FinScore"""
    
    @staticmethod
    def initialize():
        """Inicializa todos os estados necessários"""
        if 'app_initialized' not in st.session_state:
            # Estado de navegação
            st.session_state.current_page = "Home"
            st.session_state.previous_page = None
            
            # Estado de dados
            st.session_state.df = None
            st.session_state.out = None
            st.session_state.erros = {}
            st.session_state.meta = {}
            
            # Estado de abas
            st.session_state.novo_tab = "Início"
            st.session_state.analise_tab = "Resumo"
            
            # Controle de navegação
            st.session_state.last_navigation_time = 0
            st.session_state.navigation_source = None
            
            # Modo de cálculo ativo - bloqueio retroativo
            st.session_state.calculo_ativo = False
            
            st.session_state.app_initialized = True
    
    @staticmethod
    def get_current_page() -> str:
        """Retorna a página atual"""
        return st.session_state.get('current_page', 'Home')
    
    @staticmethod
    def get_previous_page() -> Optional[str]:
        """Retorna a página anterior"""
        return st.session_state.get('previous_page')
    
    @staticmethod
    def set_current_page(page_name: str, source: str = 'unknown'):
        """
        Define a página atual com controle de origem
        """
        previous = st.session_state.get('current_page')
        st.session_state.previous_page = previous
        st.session_state.current_page = page_name
        st.session_state.navigation_source = source
        st.session_state.last_navigation_time = time.time()
        
        if DEBUG_MODE:
            print(f"Página alterada: {previous} -> {page_name} (fonte: {source})")
    
    @staticmethod
    def should_ignore_navigation(source: str) -> bool:
        """
        Verifica se deve ignorar navegação baseado no tempo
        para prevenir conflitos entre sidebar, topbar and URL
        """
        current_time = time.time()
        last_time = st.session_state.get('last_navigation_time', 0)
        last_source = st.session_state.get('navigation_source')
        
        # Ignora navegações muito rápidas de fontes diferentes
        if (current_time - last_time < 0.3 and 
            last_source and last_source != source):
            return True
        return False
    
    @staticmethod
    def sync_from_query_params() -> bool:
        """Sincroniza o estado a partir dos query parameters"""
        query_params = st.query_params
        page_param = query_params.get("p")
        
        if page_param:
            page_param = page_param[0] if isinstance(page_param, list) else page_param
            target_page = SLUG_MAP.get(page_param)
            
            if target_page and target_page != AppState.get_current_page():
                if not AppState.should_ignore_navigation('url'):
                    # Verifica popup antes de navegar
                    if AppState.check_calculo_popup(target_page):
                        # Não muda a página se houver popup
                        return False
                    AppState.set_current_page(target_page, 'url')
                    return True
        return False
    
    @staticmethod
    def sync_to_query_params():
        """Sincroniza os query parameters com o estado atual"""
        reverse_slug_map = {v: k for k, v in SLUG_MAP.items()}
        current_slug = reverse_slug_map.get(AppState.get_current_page(), "home")
        
        if st.query_params.get("p") != current_slug:
            st.query_params["p"] = current_slug
    
    @staticmethod
    def ativar_modo_calculo():
        """Ativa o modo de cálculo ativo (bloqueio retroativo)"""
        st.session_state.calculo_ativo = True
        
    @staticmethod
    def desativar_modo_calculo():
        """Desativa o modo de cálculo ativo"""
        st.session_state.calculo_ativo = False
        
    @staticmethod
    def is_calculo_ativo() -> bool:
        """Verifica se o modo de cálculo está ativo"""
        return st.session_state.get('calculo_ativo', False)
    
    @staticmethod
    def check_calculo_popup(target_page: str) -> bool:
        """
        Verifica se deve mostrar popup de aviso para mudança de seção
        durante cálculo ativo. Retorna True se deve mostrar popup.
        """
        if not AppState.is_calculo_ativo():
            return False
            
        # Páginas permitidas durante cálculo ativo (sem popup)
        paginas_permitidas = ["Análise", "Parecer", "Sobre"]
        
        return target_page not in paginas_permitidas
    
    @staticmethod
    def is_debug_mode() -> bool:
        """Verifica modo debug"""
        return DEBUG_MODE