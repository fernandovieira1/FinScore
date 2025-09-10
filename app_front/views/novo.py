# app_front/views/novo.py
import streamlit as st

def render():
    st.header("🚀 Novo Cálculo FinScore")
    
    st.markdown("""
    ### Bem-vindo ao FinScore!
    
    Aqui você pode iniciar um novo cálculo do seu score financeiro empresarial.
    
    #### 📊 O que é o FinScore?
    O FinScore é uma metodologia proprietária da Assertif que avalia a saúde financeira 
    de empresas através de indicadores contábeis e análises preditivas.
    
    #### 🎯 Como funciona?
    1. **Dados da Empresa**: Insira as informações básicas da sua empresa
    2. **Dados Contábeis**: Forneça os dados financeiros dos últimos anos
    3. **Análise**: Nosso algoritmo processa as informações
    4. **Resultado**: Receba seu FinScore e relatório detalhado
    
    #### 🔍 Principais Benefícios:
    - **Análise Precisa**: Baseada em metodologia científica comprovada
    - **Relatório Completo**: Gráficos, tabelas e insights detalhados
    - **Parecer Técnico**: Análise interpretativa dos resultados
    - **Facilidade de Uso**: Interface intuitiva e amigável
    
    ---
    
    ### 📈 Estatísticas Gerais
    """)
    
    # Área de estatísticas (exemplo)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total de Cálculos",
            value="1,247",
            delta="12"
        )
    
    with col2:
        st.metric(
            label="🏢 Empresas Analisadas", 
            value="892",
            delta="8"
        )
    
    with col3:
        st.metric(
            label="📈 Score Médio",
            value="7.2",
            delta="0.3"
        )
    
    with col4:
        st.metric(
            label="⭐ Satisfação",
            value="4.8/5",
            delta="0.1"
        )
    
    st.markdown("---")
    
    # Área de ações principais
    st.markdown("### 🎬 Ações Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Novo Cálculo", use_container_width=True):
            st.info("🔄 Redirecionando para Lançamentos...")
            # Aqui você pode adicionar lógica para navegar para Lançamentos
    
    with col2:
        if st.button("📊 Ver Último Resultado", use_container_width=True):
            st.info("🔄 Redirecionando para Análise...")
            # Aqui você pode adicionar lógica para navegar para Análise
    
    with col3:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.success("✅ Dados atualizados!")
    
    st.markdown("---")
    
    # Área de informações adicionais
    st.markdown("### 📚 Recursos Úteis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 📖 Documentação
        - [📘 Guia Rápido](/?p=guia) - Como usar o sistema
        - [📊 Metodologia](/?p=sobre) - Entenda nossos cálculos  
        - [❓ FAQ](/?p=sobre) - Perguntas frequentes
        """)
    
    with col2:
        st.markdown("""
        #### 📞 Suporte
        - [💬 Contato](/?p=contato) - Fale conosco
        - [📧 Email](mailto:suporte@assertif.com.br) - suporte@assertif.com.br
        - [📱 WhatsApp](https://wa.me/5511999999999) - (11) 99999-9999
        """)
