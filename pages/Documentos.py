import streamlit as st
import base64

st.title("Boletim Comercial Trimestral")

# Lê o arquivo PDF e converte para base64
with open("assets/boletim.pdf", "rb") as f:
    base64_pdf = base64.b64encode(f.read()).decode('utf-8')



with open("assets/boletim.pdf", "rb") as f:
    pdf_data = f.read()

st.image("assets/bol2.jpg", width=300)

st.markdown(
    """
    <div style="text-align: left;">
        <img src="http://localhost:8501/media/5e6ca2d8904aa2de2697fabfa2efb2caf2d956b01615ac3f5d2a48f9.jpg" width="300">
    </div>
    """,
    unsafe_allow_html=True
)

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