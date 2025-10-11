import streamlit as st
import streamlit.components.v1 as components

def render():
    # --- CARROSSEL (use components.html em vez de st.markdown) ---
    components.html("""
    <style>
      .carousel-container{
        width:100%; height:280px; overflow:hidden; position:relative;
        border-radius:10px; box-shadow:0 6px 18px rgba(0,0,0,.1);
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial, sans-serif;
      }
      .carousel-slide{
        position:absolute; inset:0; opacity:0; transition:opacity 0.8s ease-in-out;
        background-size:cover; background-position:center; display:flex; align-items:center;
      }
      .carousel-slide.active{ opacity:1; }
      .carousel-text{
        color:#fff; padding:40px; max-width:700px; margin-left:20px;
        background:linear-gradient(90deg, rgba(0,0,0,.65) 0%, rgba(0,0,0,.25) 60%, rgba(0,0,0,0) 100%);
        border-radius:10px;
      }
      .carousel-text h1{ margin:0 0 6px 0; font-size:2rem; color:#fff; }
      .carousel-text p{ margin:0 0 14px 0; font-size:1.05rem; opacity:.92; }
      .carousel-text a{
        display:inline-block; padding:8px 18px; border:1px solid rgba(255,255,255,.9);
        border-radius:999px; color:#fff; text-decoration:none; font-weight:600;
      }
      .carousel-dots{ position:absolute; bottom:12px; left:50%; transform:translateX(-50%); display:flex; gap:6px; }
      .carousel-dots span{ font-size:1rem; color:rgba(255,255,255,.6); }
      .carousel-dots span.active{ color:#fff; }
    </style>

    <div class="carousel-container" id="finscore-carousel">
      <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1600&q=80');">
        <div class="carousel-text">
          <h1>FinScore</h1>
          <p>Índice técnico 0–1000 a partir de indicadores, z-score e PCA — claro, confiável e exportável.</p>
          <a href="?p=processo">Começar agora</a>
        </div>
      </div>

      <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1556157382-97eda2d62296?auto=format&fit=crop&w=1600&q=80');">
        <div class="carousel-text">
          <h1>Do dado ao parecer</h1>
          <p>Importe planilha, calcule índices e gere parecer técnico padronizado.</p>
          <a href="?p=analise">Ver análise</a>
        </div>
      </div>

      <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1600&q=80');">
        <div class="carousel-text">
          <h1>Ponderação temporal</h1>
          <p>O ano mais recente pesa mais (60/25/15) para refletir a fotografia atual do negócio.</p>
          <a href="?p=sobre">Saiba mais</a>
        </div>
      </div>

      <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1600&q=80');">
        <div class="carousel-text">
          <h1>Leitura executiva</h1>
          <p>Gráfico de faixas, KPIs e narrativa padronizada para auditoria e compliance.</p>
          <a href="?p=parecer">Gerar parecer</a>
        </div>
      </div>

      <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1600&q=80');">
        <div class="carousel-text">
          <h1>Privacidade e controle</h1>
          <p>Boas práticas LGPD, processamento privado e versionamento de saídas.</p>
          <a href="?p=faq">FAQ / Suporte</a>
        </div>
      </div>

      <div class="carousel-dots">
        <span>●</span><span>●</span><span>●</span><span>●</span><span>●</span>
      </div>
    </div>

    <script>
      const slides = document.querySelectorAll('.carousel-slide');
      const dots = document.querySelectorAll('.carousel-dots span');
      let i = 0;
      function show(n){
        slides.forEach((s,idx)=>s.classList.toggle('active', idx===n));
        dots.forEach((d,idx)=>d.classList.toggle('active', idx===n));
      }
      show(i);
      setInterval(()=>{
        i = (i+1)%slides.length;
        show(i);
      }, 2000);
    </script>
    """, height=320, scrolling=False)

    # --- a seguir, mantenha o resto da sua home (cards/expanders etc.) ---
    st.divider()
    st.markdown("### 📦 Funcionalidades principais")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Importar dados")
        st.markdown("Carregue planilhas Google ou Excel e valide automaticamente os períodos e contas.")
    with c2:
        st.markdown("#### Calcular índices")
        st.markdown("Liquidez, rentabilidade, alavancagem e eficiência com padronização z-score e PCA.")
    with c3:
        st.markdown("#### Gerar parecer")
        st.markdown("Obtenha FinScore 0–1000 e relatório técnico pronto para auditoria e decisão de crédito.")
