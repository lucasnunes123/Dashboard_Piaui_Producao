import streamlit as st
import base64

st.title("Boletim Comercial Trimestral")

# Lê o arquivo PDF e converte para base64
with open("assets/boletim.pdf", "rb") as f:
    base64_pdf = base64.b64encode(f.read()).decode('utf-8')



with open("assets/boletim.pdf", "rb") as f:
    pdf_data = f.read()

st.image("assets/bol2.jpg", width=300)

st.download_button(label="📄 Baixar PDF",
                   data=pdf_data,
                   file_name="meuarquivo.pdf",
                   mime="application/pdf")

# Exibe o PDF
pdf_display = f"""
<div style="display: flex; justify-content: left;">
    <iframe src="data:application/pdf;base64,{base64_pdf}" 
            width="900" height="700" type="application/pdf">
    </iframe>
</div>
"""

st.markdown(pdf_display, unsafe_allow_html=True)