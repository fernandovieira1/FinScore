"""Streamlit overlay for FinScore authentication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import streamlit as st

from app_front.components.auth import authenticate, complete_password_reset, create_user, init_password_reset
from app_front.components.guards import store_session


@dataclass
class AuthState:
    mode: str = "login"  # 'login', 'register', 'reset'
    reset_token: Optional[str] = None


_AUTH_STATE_KEY = "finscore_auth_state"


def _get_state() -> AuthState:
    if _AUTH_STATE_KEY not in st.session_state:
        st.session_state[_AUTH_STATE_KEY] = AuthState()
    return st.session_state[_AUTH_STATE_KEY]


def reset_state() -> None:
    if _AUTH_STATE_KEY in st.session_state:
        del st.session_state[_AUTH_STATE_KEY]


def auth_overlay() -> None:
    """Render the authentication overlay."""

    state = _get_state()

    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(120deg, rgba(15, 32, 62, 0.92), rgba(24, 69, 123, 0.88)) !important;
        }
        section.main > div:first-child {
            width: min(420px, 92vw);
            margin: 8vh auto 0 auto;
            background: #fff;
            border-radius: 1.25rem;
            box-shadow: 0 8px 32px rgba(24, 69, 123, 0.18), 0 1.5px 8px rgba(24, 69, 123, 0.10);
            padding: 2.5rem 2.2rem 2rem 2.2rem;
            color: #0b1f33;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: stretch;
        }
        section.main > div:first-child h3, section.main > div:first-child h2, section.main > div:first-child h1 {
            text-align: center;
            margin-bottom: 1.2rem;
            font-weight: 700;
        }
        section.main > div:first-child .stTextInput > div > div > input,
        section.main > div:first-child .stTextInput input,
        section.main > div:first-child .stTextArea textarea {
            border-radius: 0.7rem !important;
            border: 1.5px solid #bdbdbd !important;
            background: #f8fafc !important;
            font-size: 1.05rem;
            padding: 0.7rem 1rem !important;
        }
        section.main > div:first-child .stButton > button {
            width: 100%;
            border-radius: 0.7rem;
            font-size: 1.08rem;
            font-weight: 600;
            margin-bottom: 0.7rem;
            background: linear-gradient(90deg, #5ea68d 60%, #1976d2 100%) !important;
            color: #fff !important;
            border: none !important;
            box-shadow: 0 2px 8px rgba(24, 69, 123, 0.10);
            transition: background 0.2s;
        }
        section.main > div:first-child .stButton > button:hover {
            background: linear-gradient(90deg, #1976d2 60%, #5ea68d 100%) !important;
        }
        section.main > div:first-child label {
            font-weight: 500;
            margin-bottom: 0.2rem;
        }
        section.main > div:first-child .stCheckbox > label {
            font-size: 1rem;
        }
        section.main > div:first-child .stAlert {
            border-radius: 0.7rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Entrar", key="auth_tab_login", use_container_width=True, type="secondary"):
                state.mode = "login"
        with col2:
            if st.button("Criar conta", key="auth_tab_register", use_container_width=True, type="secondary"):
                state.mode = "register"

        if state.mode == "login":
            _render_login(state)
        elif state.mode == "register":
            _render_register(state)
        else:
            _render_reset(state)

    st.stop()


def _render_login(state: AuthState) -> None:
    st.markdown("### Bem-vindo de volta")
    email = st.text_input("E-mail", key="auth_login_email")
    password = st.text_input("Senha", type="password", key="auth_login_password")
    remember = st.checkbox("Manter sessão ativa", key="auth_login_remember")

    if st.button("Entrar", use_container_width=True, type="primary", key="auth_login_submit"):
        user = authenticate(email, password)
        if user:
            store_session(user, remember=remember)
            st.success("Login realizado com sucesso!")
            st.experimental_rerun()
        else:
            st.error("Credenciais inválidas.")

    if st.button("Esqueci minha senha", use_container_width=True, key="auth_login_reset", type="secondary"):
        state.mode = "reset"
        state.reset_token = None
        st.experimental_rerun()


def _render_register(state: AuthState) -> None:
    st.markdown("### Criar nova conta")

    email = st.text_input("E-mail", key="auth_register_email")
    password = st.text_input(
        "Senha",
        type="password",
        key="auth_register_password",
        max_chars=72,
        help="Máximo 72 caracteres."
    )
    confirm = st.text_input(
        "Confirmar senha",
        type="password",
        key="auth_register_confirm",
        max_chars=72
    )
    # Checar tamanho em bytes
    password_bytes = password.encode('utf-8')
    confirm_bytes = confirm.encode('utf-8')
    if len(password_bytes) > 72:
        st.warning('A senha ultrapassa 72 bytes e será truncada automaticamente. Use menos caracteres especiais ou reduza o tamanho.')
    if len(confirm_bytes) > 72:
        st.warning('A confirmação de senha ultrapassa 72 bytes e será truncada.')
    # Truncar para 72 bytes
    password = password_bytes[:72].decode('utf-8', errors='ignore')
    confirm = confirm_bytes[:72].decode('utf-8', errors='ignore')

    if st.button("Cadastrar", use_container_width=True, type="primary", key="auth_register_submit"):
        if len(password.encode('utf-8')) > 72 or len(confirm.encode('utf-8')) > 72:
            st.error("A senha não pode ter mais que 72 bytes.")
            return
        if not password:
            st.error("A senha não pode ser vazia após truncamento.")
            return
        if password != confirm:
            st.error("As senhas não conferem.")
            return
        try:
            user = create_user(email, password)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))
            return
        store_session(user, remember=False)
        st.success("Conta criada e login realizado!")
        st.experimental_rerun()

    if st.button("Já tenho conta", use_container_width=True, key="auth_register_login"):
        state.mode = "login"
        st.experimental_rerun()


def _render_reset(state: AuthState) -> None:
    st.markdown("### Redefinir senha")
    email = st.text_input("E-mail cadastrado", key="auth_reset_email")

    if state.reset_token:
        token = st.text_input("Token de redefinição", key="auth_reset_token")
        new_password = st.text_input("Nova senha", type="password", key="auth_reset_new_password", max_chars=72, help="Máximo 72 caracteres.")
        confirm = st.text_input("Confirmar nova senha", type="password", key="auth_reset_new_confirm", max_chars=72)

        if st.button("Atualizar senha", use_container_width=True, type="primary", key="auth_reset_submit"):
            if len(new_password) > 72 or len(confirm) > 72:
                st.error("A senha não pode ter mais que 72 caracteres.")
                return
            if new_password != confirm:
                st.error("As senhas não conferem.")
                return
            if complete_password_reset(email, token, new_password):
                st.success("Senha atualizada! Faça login com a nova senha.")
                state.mode = "login"
                state.reset_token = None
                st.experimental_rerun()
            else:
                st.error("Não foi possível redefinir a senha. Verifique o token e tente novamente.")
    else:
        if st.button("Gerar token", use_container_width=True, type="primary", key="auth_reset_generate"):
            token = init_password_reset(email)
            if token:
                state.reset_token = token
                st.info(f"Token gerado: {token}. Informe-o abaixo para redefinir a senha.")
                st.experimental_rerun()
            else:
                st.error("Não foi possível encontrar este e-mail.")

    if st.button("Voltar ao login", use_container_width=True, key="auth_reset_login"):
        state.mode = "login"
        state.reset_token = None
        st.experimental_rerun()
