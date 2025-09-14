# app_front/views/novo.py

import streamlit as st
import streamlit.components.v1 as components
from components.state_manager import AppState

def render():
    st.header("Novo Cálculo")

    st.markdown(
        """
Para dar início, siga os passos descritos:

1. Após clicar no botão **[Iniciar]**, logo abaixo, você será redirecionado para a seção **"Lançamentos"**.
2. Em lançamentos, na aba **|Cliente|**, preencha as seguintes informações:
    * Nome da empresa.
    * CNPJ.
    * Ano Inicial e Ano Final das demonstrações contábeis.
    * Pontuação do Serasa.
    * Data de consulta ao Serasa.

   Em seguida, clique no botão **[Enviar Dados]**, localizado no final do formulário.
3. Na aba **|Dados|**, faça o lançamento dos dados contábeis, que podem ser enviados via upload de arquivo, link do Google Sheets ou diretamente na plataforma.
    * Se optar pelo upload de arquivo, certifique-se de que ele esteja no formato correto (.xlsx).
4. Clique em **[Calcular FinScore]**.

A análise será detalhada na seção **"Análise"** e você poderá visualizar o parecer na seção **"Parecer"**.
*(melhorar esse final)*

        """,
        unsafe_allow_html=True
    )

    st.write("")
    # Botão centralizado com o mesmo estilo do "Calcular FinScore" (verde)
    col = st.columns([3, 2, 3])[1]
    with col:
        # Container com ID próprio para CSS de alta especificidade
        st.markdown('<div id="novo-iniciar-btn">', unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            /* CSS super específico para o botão Iniciar */
            #novo-iniciar-btn .stButton > button,
            #novo-iniciar-btn .stButton > button[data-testid="baseButton-secondary"],
            #novo-iniciar-btn .stButton > button[kind="secondary"],
            #novo-iniciar-btn .stButton > button[data-testid="baseButton-primary"],
            #novo-iniciar-btn .stButton > button[kind="primary"] {
                background: #5ea68d !important;
                color: #fff !important;
                font-weight: 600;
                font-size: 1.05rem;
                border-radius: 6px !important;
                padding: 0.7rem 2.2rem !important;
                border: none !important;
                box-shadow: 0 2px 8px rgba(16,24,40,0.08);
                transition: background 0.2s;
            }
            #novo-iniciar-btn .stButton > button:hover {
                background: #43866b !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Iniciar", key="btn_iniciar", help="Ir para lançamentos"):
            st.session_state["liberar_lancamentos"] = True
            AppState.set_current_page("Lançamentos", source="novo_iniciar_btn")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        # Fallback robusto: força a cor via JS se algum tema ainda sobrescrever o CSS
        components.html(
                """
                <script>
                (function(){
                    function paint(){
                        try{
                            const btns = window.parent.document.querySelectorAll('button');
                            for (const b of btns){
                                const t = (b.innerText || b.textContent || '').trim();
                                if (t === 'Iniciar'){
                                    b.style.background = '#5ea68d';
                                    b.style.color = '#ffffff';
                                    b.style.border = 'none';
                                    b.style.borderRadius = '6px';
                                    b.style.boxShadow = '0 2px 8px rgba(16,24,40,0.08)';
                                    b.onmouseenter = () => b.style.background = '#43866b';
                                    b.onmouseleave = () => b.style.background = '#5ea68d';
                                    return true;
                                }
                            }
                        } catch(e){}
                        return false;
                    }
                    let tries = 0;
                    const iv = setInterval(()=>{ if(paint() || tries++ > 25){ clearInterval(iv); } }, 120);
                    setTimeout(paint, 0);
                })();
                </script>
                """,
                height=0,
        )
