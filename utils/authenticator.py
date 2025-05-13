import streamlit as st
import streamlit_authenticator as stauth

class NotAuthenticatedError(Exception):
    pass

def login_required():
    """
    Protege a página exigindo autenticação. Interrompe a execução se o login falhar.
    """
    # Usuários e senhas simples (use hash em produção)
    names = ["Admin", "Usuário"]
    usernames = ["admin", "usuario"]
    passwords = ["1234", "senha"]  # Senhas em texto puro aqui (hash recomendável)

    hashed_passwords = stauth.Hasher(passwords).generate()

    authenticator = stauth.Authenticate(
        names,
        usernames,
        hashed_passwords,
        "meu_cookie",      # Nome do cookie
        "minha_chave",     # Chave secreta para o cookie
        cookie_expiry_days=1
    )

    name, auth_status, username = authenticator.login("Login", "main")

    if auth_status is None:
        st.warning("Por favor, insira suas credenciais.")
        raise NotAuthenticatedError()
    elif auth_status is False:
        st.error("Usuário ou senha inválidos.")
        raise NotAuthenticatedError()
    elif auth_status:
        # Exibe logout na barra lateral
        authenticator.logout("Sair", "sidebar")
        st.sidebar.success(f"Logado como: {name}")
