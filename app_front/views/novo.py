# app_front/views/novo.py

import streamlit as st
import streamlit.components.v1 as components
from components.state_manager import AppState
from components.config import SLUG_MAP

def render():
    st.header("Novo Calculo")
    has_active_process = AppState.has_active_process()
    if has_active_process:
        st.warning("Ha um calculo em andamento. Clicar em Iniciar limpara os dados atuais e reiniciara a analise.")


    st.markdown(
        """
Para dar inicio, siga os passos descritos:

1. Apos clicar no botao **[Iniciar]**, logo abaixo, voce sera redirecionado para a secao **"Lancamentos"**.
2. Em lancamentos, na aba **|Cliente|**, preencha as seguintes informacoes:
    * Nome da empresa.
    * CNPJ.
    * Ano Inicial e Ano Final das demonstracoes contabeis.
    * Pontuacao do Serasa.
    * Data de consulta ao Serasa.

   Em seguida, clique no botao **[Enviar Dados]**, localizado no final do formulario.
3. Na aba **|Dados|**, faca o lancamento dos dados contabeis, que podem ser enviados via upload de arquivo, link do Google Sheets ou diretamente na plataforma.
    * Se optar pelo upload de arquivo, certifique-se de que ele esteja no formato correto (.xlsx).
4. Clique em **[Calcular FinScore]**.

A analise sera detalhada na secao **"Analise"** e voce podera visualizar o parecer na secao **"Parecer"**.
*(melhorar esse final)*

        """,
        unsafe_allow_html=True
    )

    st.write("")
    # Botao centralizado com o mesmo estilo do "Calcular FinScore" (verde)
    col = st.columns([3, 2, 3])[1]
    with col:
        # Container com ID proprio para CSS de alta especificidade
        st.markdown('<div id="novo-iniciar-btn">', unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            /* CSS super especifico para o botao Iniciar */
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
        if st.button("Iniciar", key="btn_iniciar", help="Ir para lancamentos"):
            AppState.reset_process_data()
            st.session_state["liberar_lancamentos"] = True
            target_page = SLUG_MAP.get("lanc", "Lancamentos")
            AppState.set_current_page(target_page, source="novo_iniciar_btn", slug="lanc")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        # Fallback robusto: forca a cor via JS se algum tema ainda sobrescrever o CSS
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
