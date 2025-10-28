import streamlit as st
from streamlit_cookies_manager import CookieManager

# Initialize CookieManager
cookies = CookieManager()

# Display the readiness status
st.write("CookieManager ready:", cookies.ready)

# Test setting and getting a cookie
if cookies.ready:
    cookies['test_cookie'] = 'test_value'
    cookies.sync()
    st.write("Test cookie value:", cookies.get('test_cookie'))
else:
    st.write("CookieManager is not ready. Please check browser settings or initialization.")