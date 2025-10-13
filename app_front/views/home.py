import streamlit as st

# HTML do carrossel renderizado no DOM principal (sem iframe)
HTML_CAROUSEL = """
<style>
  .carousel-container{
    width:100%; height:280px; overflow:hidden; position:relative;
    border-radius:10px; box-shadow:0 6px 18px rgba(0,0,0,.1);
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial, sans-serif;
  }
  .carousel-slide{
    position:absolute; inset:0; opacity:0; visibility:hidden; transition:opacity 0.8s ease-in-out;
    background-size:cover; background-position:center; display:flex; align-items:center;
    animation: fade 16s infinite;
  }
  .carousel-text{
    color:#fff !important; padding:40px; max-width:700px; margin-left:20px;
    background:linear-gradient(90deg, rgba(0,0,0,.65) 0%, rgba(0,0,0,.25) 60%, rgba(0,0,0,0) 100%);
    border-radius:10px;
  }
  .carousel-text h1{ margin:0 0 6px 0; font-size:2rem; color:#fff !important; }
  .carousel-text p{ margin:0 0 14px 0; font-size:1.05rem; opacity:.92; color:#fff !important; }
  .carousel-text a{
    display:inline-block; padding:8px 18px; border:1px solid rgba(255,255,255,.9);
    border-radius:999px; color:#fff !important; text-decoration:none; font-weight:600;
    cursor:pointer; transition:all 0.3s ease;
  }
  .carousel-text a:hover{
    background:rgba(255,255,255,.1); transform:translateY(-1px);
  }
  .carousel-dots{ position:absolute; bottom:12px; left:50%; transform:translateX(-50%); display:flex; gap:6px; }
  .carousel-dots span{ font-size:1rem; color:#fff !important; }

  /* Anima\u00e7\u00e3o CSS para rotacionar slides sem JS */
  @keyframes fade {
    0%, 20% { opacity: 1; visibility: visible; }
    25%, 100% { opacity: 0; visibility: hidden; }
  }
  /* Atrasos por slide (4 slides, ciclo 16s) */
  #finscore-carousel > .carousel-slide:nth-child(1) { animation-delay: 0s; }
  #finscore-carousel > .carousel-slide:nth-child(2) { animation-delay: 4s; }
  #finscore-carousel > .carousel-slide:nth-child(3) { animation-delay: 8s; }
  #finscore-carousel > .carousel-slide:nth-child(4) { animation-delay: 12s; }

  /* Dots sempre brancos, sem anima\u00e7\u00e3o de cor */
  .carousel-dots span { animation: none !important; }
</style>

<div class="carousel-container" id="finscore-carousel">
  <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1600&q=80');">
    <div class="carousel-text">
      <h1>FinScore</h1>
      <p>Avalie riscos e oportunidades com base em dados financeiros.</p>
  <!-- Link configurado para navegar na mesma aba -->
  <a href="?p=guia" target="_self">Conhe\u00e7a a metodologia</a>
    </div>
  </div>

  <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1454165205744-3b78555e5572?auto=format&fit=crop&w=1600&q=80');">
    <div class="carousel-text">
      <h1>Do dado ao parecer</h1>
      <p>Materialize sua an\u00e1lise em um parecer t\u00e9cnico</p>
  <!-- Link configurado para navegar na mesma aba -->
  <a href="?p=novo" target="_self">Iniciar uma nova an\u00e1lise</a>
    </div>
  </div>

  <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1600&q=80');">
    <div class="carousel-text">
      <h1>Metodologia consistente</h1>
    <p>Dados cont\u00e1beis transformados em informa\u00e7\u00e3o econ\u00f4mica, financeira e patrimonial</p>
  <!-- Link configurado para navegar na mesma aba -->
  <a href="?p=sobre" target="_self">Como funciona</a>
    </div>
  </div>

  <div class="carousel-slide" style="background-image:url('https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1600&q=80');">
    <div class="carousel-text">
      <h1>Suporte e contato</h1>
      <p>Precisa de ajuda na implanta\u00e7\u00e3o ou integra\u00e7\u00e3o? Fale com a gente.</p>
  <!-- Link configurado para navegar na mesma aba -->
  <a href="?p=contato" target="_self">Fale conosco</a>
    </div>
  </div>

  <div class="carousel-dots">
    <span>&bull;</span>
    <span>&bull;</span>
    <span>&bull;</span>
    <span>&bull;</span>
  </div>
</div>
"""


def render() -> None:
  # --- CARROSSEL (sem iframe; links navegam no app principal) ---
  st.markdown(HTML_CAROUSEL, unsafe_allow_html=True)

  # --- Conte\u00fado adicional ---
  st.divider()
  st.markdown("<h3 style='text-align: center;'>&#128200; Avalie seu cliente</h3>", unsafe_allow_html=True)

  c1, c2, c3 = st.columns(3)
  with c1:
      st.markdown("#### Insira os dados")
      st.markdown(
          "Carregue (via planilhas) ou lance (manualmente) os dados e valide automaticamente os per\u00edodos e contas."
      )
  with c2:
      st.markdown("#### C\u00e1lculo dos \u00edndices")
      st.markdown(
          "Conhecidos os dados, \u00edndices como Liquidez, rentabilidade, alavancagem e outros s\u00e3o calculados."
      )
  with c3:
      st.markdown("#### Parecer t\u00e9cnico")
      st.markdown(
          "Obtenha FinScore 0-1000 e relat\u00f3rio t\u00e9cnico pronto para auditoria e decis\u00e3o de cr\u00e9dito."
      )
