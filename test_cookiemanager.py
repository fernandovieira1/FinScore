import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config(page_title="Teste CookieManager", layout="centered")

st.title("Teste Mínimo do CookieManager")

cookies = EncryptedCookieManager(password="teste-cookie-secret")

cm_ready = cookies.ready()
st.info(f"CookieManager ready: {cm_ready}")

if not cm_ready:
    st.warning("CookieManager ainda não está pronto. Recarregue a página e permita cookies no navegador.")
    st.stop()
else:
    st.success("CookieManager está pronto! Você pode usar cookies normalmente.")
    st.write("Cookies atuais:", cookies.get_all())
