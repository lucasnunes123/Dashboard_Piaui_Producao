import streamlit as st
from utils.authenticator import login_required, NotAuthenticatedError

try:
    login_required()
except NotAuthenticatedError:
    st.stop()

# Conteúdo da página autenticada
st.title("Área Protegida")
st.write("Este conteúdo está visível apenas para usuários autenticados.")

