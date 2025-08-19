# app_front/components/header.py
import streamlit as st
from components.theme import inject_global_css, render_logo_overlay

LOGO_PATH = "assets/logo.png"

def render_header():
    # estilos globais + logo fixo sobre a sidebar
    inject_global_css()
    render_logo_overlay(LOGO_PATH)  # se quiser: render_logo_overlay(LOGO_PATH, "ASSERTIF")

    # Linha divisória opcional (pode até tirar se quiser tudo mais limpo)
    st.write("---")
