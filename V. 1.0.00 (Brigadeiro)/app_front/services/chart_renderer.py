# app_front/services/chart_renderer.py
"""
Módulo para renderização de minicharts comparativos Serasa vs FinScore.
Gera gráficos de barras lado a lado com logos, valores e classificações.
"""

import os
import io
import base64
from typing import Tuple, Optional

import matplotlib
matplotlib.use("Agg")  # Backend não-interativo

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

# Paletas pastel
TEAL_PASTEL = ["#BFEDE6", "#A6E4DB", "#8ADBCF", "#6FD2C4"]          # Serasa (verde-água)
BLUE_PASTEL = ["#C8DBF4", "#AECBEE", "#90BAE8", "#78A6DB", "#5F90CE"]  # FinScore (azuis)

# Diretório de assets
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
LOGO_SERASA = os.path.join(ASSETS_DIR, "logo_serasa3.png")
LOGO_FINSCORE = os.path.join(ASSETS_DIR, "logo_fin1a.png")


def _draw_minichart(ax, categories, values, colors, score,
                   font_x=7, font_value=8, grid_color="#EDEFF3",
                   score_color="#7A8596"):
    """
    Mini bar chart:
      - barras partem do eixo x (sem bordas)
      - linha pontilhada no 'score'
      - valores pequenos acima das barras
      - sem spines e sem ticks no eixo y
    """
    x = np.arange(len(categories))
    ymax = max(max(values), float(score)) * 1.15

    # Barras (sem borda)
    ax.bar(x, values, width=0.55, color=colors[:len(values)],
           edgecolor="none", linewidth=0.0, zorder=3)

    # Grid leve
    ax.grid(axis="y", color=grid_color, linestyle="-", linewidth=1, zorder=0)

    # Linha do resultado (pontilhada)
    ax.axhline(score, linestyle="--", color=score_color, linewidth=1.2, zorder=5)

    # Rótulos de valor
    for i, v in enumerate(values):
        ax.text(i, v + ymax*0.03, f"{v:.0f}", ha="center", va="bottom",
                fontsize=font_value, color="#8A8F99", fontweight="bold", zorder=5)

    # Eixo x
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=font_x, color="#1E2A3A")
    ax.set_ylim(0, ymax)
    ax.set_yticks([])

    # Sem bordas
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_facecolor("#FDFAFB")


def _compose_logo_on_bg(path, bg_rgb=(253, 250, 251)):
    """
    Carrega um PNG (possivelmente com alpha), compõe sobre um fundo RGB 
    e retorna uma imagem RGB pronta para uso no Matplotlib.
    """
    if not os.path.exists(path):
        return None
    
    logo = Image.open(path)
    # Garantir RGBA para composição correta
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')
    # Criar fundo em RGBA com alpha 255
    bg_rgba = Image.new('RGBA', logo.size, (bg_rgb[0], bg_rgb[1], bg_rgb[2], 255))
    composed = Image.alpha_composite(bg_rgba, logo)
    return composed.convert('RGB')


def gerar_minichart_serasa_finscore(
    serasa_score: float,
    finscore_score: float,
    serasa_vals: Tuple[float, float, float, float] = (300, 500, 700, 1000),
    finscore_vals: Tuple[float, float, float, float, float] = (125, 250, 750, 875, 1000),
    return_base64: bool = False,
    output_path: Optional[str] = None
) -> str:
    """
    Gera imagem comparativa lado a lado dos minicharts Serasa e FinScore.
    
    Args:
        serasa_score: Pontuação Serasa (0-1000)
        finscore_score: Pontuação FinScore (0-1000)
        serasa_vals: Valores de referência das 4 categorias Serasa
        finscore_vals: Valores de referência das 5 categorias FinScore
        return_base64: Se True, retorna string base64 da imagem
        output_path: Se fornecido, salva a imagem neste caminho
    
    Returns:
        Caminho do arquivo salvo, string base64 ou string vazia em caso de erro
    """
    # Categorias
    serasa_cats = ["Muito\nBaixo", "Baixo", "Bom", "Excelente"]
    finscore_cats = ["M.\nAcima", "L.\nAcima", "Neutro", "L.\nAbaixo", "M.\nAbaixo"]

    # Dois eixos lado a lado, bem próximos
    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(10.0, 3.0), dpi=250, gridspec_kw=dict(wspace=0.06)
    )
    fig.patch.set_facecolor("#FDFAFB")
    fig.patch.set_alpha(1.0)

    # Desenho dos minicharts
    _draw_minichart(axL, serasa_cats, serasa_vals, TEAL_PASTEL, score=serasa_score)
    _draw_minichart(axR, finscore_cats, finscore_vals, BLUE_PASTEL, score=finscore_score)

    # Margens
    plt.subplots_adjust(left=0.06, right=0.99, top=0.92, bottom=0.30, wspace=0.06)

    # Logos embaixo dos gráficos (centralizados e pequenos)
    try:
        logo_serasa_rgb = _compose_logo_on_bg(LOGO_SERASA)
        logo_finscore_rgb = _compose_logo_on_bg(LOGO_FINSCORE)
        
        if logo_serasa_rgb and logo_finscore_rgb:
            imagebox_serasa = OffsetImage(logo_serasa_rgb, zoom=0.06)
            boxL = axL.get_position()
            # Posição em coordenadas da figura (60px para a esquerda, 20px para baixo)
            offset_x = 60 / (fig.get_figwidth() * fig.dpi)
            offset_y = 20 / (fig.get_figheight() * fig.dpi)
            ab_serasa = AnnotationBbox(
                imagebox_serasa, 
                xy=(boxL.x0 + boxL.width/2 - offset_x, boxL.y0 - 0.10 - offset_y),
                xycoords='figure fraction',
                frameon=False,
                box_alignment=(0.5, 1.0)
            )
            fig.add_artist(ab_serasa)

            imagebox_finscore = OffsetImage(logo_finscore_rgb, zoom=0.06)
            boxR = axR.get_position()
            ab_finscore = AnnotationBbox(
                imagebox_finscore,
                xy=(boxR.x0 + boxR.width/2 - offset_x, boxR.y0 - 0.10 - offset_y),
                xycoords='figure fraction',
                frameon=False,
                box_alignment=(0.5, 1.0)
            )
            fig.add_artist(ab_finscore)
        else:
            # Fallback para texto
            _add_text_fallback(fig, axL, axR)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar os logos: {e}")
        _add_text_fallback(fig, axL, axR)

    # Retornar em diferentes formatos
    if return_base64:
        # Salvar em buffer e converter para base64
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches="tight", 
                   facecolor=fig.get_facecolor(), edgecolor='none', 
                   transparent=False)
        buf.seek(0)
        
        # Garantir RGB (sem alpha)
        im_final = Image.open(buf)
        if im_final.mode == 'RGBA':
            im_final = im_final.convert('RGB')
        
        buf_rgb = io.BytesIO()
        im_final.save(buf_rgb, format='PNG')
        buf_rgb.seek(0)
        
        plt.close(fig)
        return base64.b64encode(buf_rgb.read()).decode('utf-8')
    
    elif output_path:
        # Salvar em arquivo
        fig.savefig(output_path, bbox_inches="tight", 
                   facecolor=fig.get_facecolor(), edgecolor='none', 
                   transparent=False)
        
        # Pós-processamento: garantir RGB
        try:
            im_final = Image.open(output_path)
            if im_final.mode == 'RGBA':
                im_final = im_final.convert('RGB')
                im_final.save(output_path)
        except Exception as e:
            print(f"Aviso ao converter PNG final para RGB: {e}")
        
        plt.close(fig)
        return output_path
    
    else:
        # Salvar em buffer temporário e retornar base64
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches="tight",
                   facecolor=fig.get_facecolor(), edgecolor='none',
                   transparent=False)
        buf.seek(0)
        plt.close(fig)
        return base64.b64encode(buf.read()).decode('utf-8')


def _add_text_fallback(fig, axL, axR):
    """Adiciona labels de texto quando os logos não estão disponíveis"""
    fig.canvas.draw()
    boxL = axL.get_position()
    boxR = axR.get_position()
    fig.text(boxL.x0 + boxL.width/2, boxL.y0 - 0.10, "Serasa",
             ha="center", va="top", fontsize=10, color="#303030")
    fig.text(boxR.x0 + boxR.width/2, boxR.y0 - 0.10, "FinScore",
             ha="center", va="top", fontsize=10, fontweight="bold", color="#303030")


def obter_valores_faixas_serasa(classificacao: str) -> Tuple[float, float, float, float]:
    """
    Retorna valores ilustrativos das faixas Serasa baseado na classificação.
    """
    # Valores padrão (ajustados para melhor visualização)
    if classificacao in ["Excelente", "Muito Bom"]:
        return (300, 500, 700, 1000)
    elif classificacao == "Bom":
        return (250, 450, 750, 900)
    elif classificacao == "Baixo":
        return (200, 400, 600, 800)
    else:  # Muito Baixo ou N/A
        return (150, 300, 500, 700)


def obter_valores_faixas_finscore(classificacao: str) -> Tuple[float, float, float, float, float]:
    """
    Retorna valores ilustrativos das faixas FinScore baseado na classificação.
    """
    # Valores padrão alinhados com a metodologia
    if classificacao == "Muito Abaixo do Risco":
        return (125, 250, 750, 875, 1000)
    elif classificacao == "Levemente Abaixo do Risco":
        return (125, 250, 750, 875, 950)
    elif classificacao == "Neutro":
        return (125, 250, 500, 750, 875)
    elif classificacao == "Levemente Acima do Risco":
        return (100, 200, 400, 600, 800)
    else:  # Muito Acima do Risco
        return (50, 125, 250, 400, 600)
