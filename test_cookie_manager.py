from streamlit_cookies_manager import CookieManager

# Inicializa o CookieManager
cookies = CookieManager(prefix="finscore")

# Verifica se está pronto
if cookies.ready():
    print("CookieManager está pronto!")
else:
    print("CookieManager ainda não está pronto.")