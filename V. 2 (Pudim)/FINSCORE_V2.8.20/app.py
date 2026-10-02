"""Ponto de entrada da distribuição FinScore Pudim.

Execute com: streamlit run app.py
"""

from runpy import run_path
from pathlib import Path


run_path(Path(__file__).resolve().parent / "app_front" / "app.py", run_name="__main__")
