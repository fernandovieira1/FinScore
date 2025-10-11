import streamlit as st
import streamlit.components.v1 as components
from datetime import date
from components.state_manager import AppState
from components.config import SLUG_MAP

def _empresa(ss):
    st.markdown("### 🏢 Empresa")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("Nome da Empresa")
        st.markdown(
            f"<h3 style='text-align:left;margin:0;font-size: 140%;'>{ss.meta.get('empresa','-')}</h3>",
            unsafe_allow_html=True,
        )

    with col2:
        st.caption("CNPJ")
        st.markdown(
            f"<h3 style='text-align:left;margin:0;font-size: 140%;'>{ss.meta.get('cnpj','-') or '-'}</h3>",
            unsafe_allow_html=True,
        )

    with col3:
        st.caption("Período")
        ai, af = ss.meta.get("ano_inicial"), ss.meta.get("ano_final")
        periodo = f"{ai} – {af}" if ai and af else "-"
        st.markdown(
            f"<h3 style='text-align:left;margin:0;font-size: 140%;'>{periodo}</h3>",
            unsafe_allow_html=True,
        )

    st.divider()


def _metricas(ss):
    st.markdown("### 📌 Resumo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<p style='margin-bottom:.25rem;'>FinScore Bruto</p>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='margin:.15rem 0 0 0;font-size:140%;'>{ss.out.get('finscore_bruto','-')}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='margin:.25rem 0 0 0;'>{ss.out.get('classificacao_finscore_bruto','(-)')}</p>",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("<p style='margin-bottom:.25rem;'>FinScore Ajustado</p>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='margin:.15rem 0 0 0;font-size:140%;'>{ss.out.get('finscore_ajustado','-')}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='margin:.25rem 0 0 0;'>{ss.out.get('classificacao_finscore','(-)')}</p>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown("<p style='margin-bottom:.25rem;'>Serasa Score</p>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='margin:.15rem 0 0 0;font-size:140%;'>{ss.out.get('serasa','-')}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='margin:.25rem 0 0 0;'>{ss.out.get('classificacao_serasa','(-)')}</p>",
            unsafe_allow_html=True,
        )

    # (sem divider aqui para ficar idêntico ao seu print "certo")


def _datas(ss):
    st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    hoje = date.today().strftime("%d/%m/%Y")
    meta = getattr(ss, "meta", {}) or {}
    serasa_data = meta.get("serasa_data")
    serasa_label = serasa_data if serasa_data else "-"
    with col1:
        st.caption("Data da Análise")
        st.markdown(
            f"<p style='margin:0;font-size:1.25rem;font-weight:600;'>{hoje}</p>",
            unsafe_allow_html=True,
        )
    with col3:
        st.caption("Data de Consulta ao Serasa")
        st.markdown(
            f"<p style='margin:0;font-size:1.25rem;font-weight:600;'>{serasa_label}</p>",
            unsafe_allow_html=True,
        )


def _botao_aprovar(ss):
    """
    Renderiza o botão 'Aprovar' que:
    1) Libera a seção /Parecer
    2) Redireciona automaticamente para /Parecer
    """
    st.markdown("<div style='margin-top:3rem;'></div>", unsafe_allow_html=True)
    
    # Verificar se já foi aprovado
    parecer_liberado = ss.get("liberar_parecer", False)
    
    if parecer_liberado:
        # Mostrar status de aprovação
        st.success("✅ Análise aprovada. A seção **Parecer** está liberada para acesso.")
        return
    
    # Botão centralizado com mesmo estilo dos outros botões
    col = st.columns([3, 2, 3])[1]
    with col:
        # Container com ID próprio para CSS de alta especificidade
        st.markdown('<div id="aprovar-analise-btn">', unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            /* CSS super específico para o botão Aprovar */
            #aprovar-analise-btn .stButton > button,
            #aprovar-analise-btn .stButton > button[data-testid="baseButton-secondary"],
            #aprovar-analise-btn .stButton > button[kind="secondary"],
            #aprovar-analise-btn .stButton > button[data-testid="baseButton-primary"],
            #aprovar-analise-btn .stButton > button[kind="primary"] {
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
            #aprovar-analise-btn .stButton > button:hover {
                background: #43866b !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Aprovar", key="btn_aprovar_analise", help="Liberar seção Parecer"):
            # Liberar a seção Parecer no session_state
            ss["liberar_parecer"] = True
            
            # Salvar no cache também para garantir persistência
            cache = AppState._process_cache()
            cache["liberar_parecer"] = True
            
            # Atualizar estado e URL para avançar no fluxo
            target_page = SLUG_MAP.get("parecer", "Parecer")
            AppState.skip_next_url_sync(
                target_slug="parecer",
                duration=15.0,
                blocked_slugs={"analise", "lanc"},
            )
            AppState.set_current_page(target_page, source="scores_aprovar_btn", slug="parecer")
            AppState.sync_to_query_params()
            st.query_params["p"] = "parecer"
            
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
                            if (t === 'Aprovar'){
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
                const interval = setInterval(() => {
                    if (paint() || tries++ > 50) clearInterval(interval);
                }, 50);
            })();
            </script>
            """,
            height=0,
        )


def render():
    ss = st.session_state

    # Se ainda não processou, apenas orienta
    if not ss.get("out"):
        _empresa(ss)
        st.info("Calcule o FinScore em **Lançamentos → Dados** para liberar o resumo.")
        return

    # Bloco Empresa + Bloco de Métricas (mesmo desenho do print "certo")
    _empresa(ss)
    _metricas(ss)
    _datas(ss)
    
    # Botão Aprovar
    _botao_aprovar(ss)
