import streamlit as st
import base64



col1, col2 = st.columns(2)

with col1:
    st.title("Boletim")
    # Lê o arquivo PDF e converte para base64
    with open("assets/boletim.pdf", "rb") as f: 
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')


    with open("assets/boletim.pdf", "rb") as f:
        pdf_data = f.read()

    st.image("assets/bol2.png", width=300)

    st.download_button(label="📄 Baixar PDF",
                    data=pdf_data,
                    file_name="meuarquivo.pdf",
                    mime="application/pdf")

with col2:
    st.title("Resumo do Boletim")
    st.image("assets/TP/die.png", width=400)

st.title("Principais pontos de desembarques do estado do Piauí")
st.image("assets/TP/pontos.png", use_container_width=True)