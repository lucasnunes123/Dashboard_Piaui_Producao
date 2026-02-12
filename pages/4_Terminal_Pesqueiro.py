import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import base64

# Configuração da página
st.set_page_config(layout="wide", page_title="Dashboard Terminal Pesqueiro")

def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded_string.decode()}");
        background-attachment: fixed;
        background-size: contain;
        background-repeat: no-repeat;
        background-position: 170% 0%;
    }}
    
    /* fundo levemente transparente aos blocos de conteúdo */

    [data-testid="stVerticalBlock"] > div {{
        background-color: rgba(255, 255, 255, 0.8); 
        border-radius: 10px;
        padding: 10px;
    }}
    </style>

    """, # Note: em versões novas use unsafe_allow_html=True
    unsafe_allow_html=True
    )

# Chame a função com o caminho da sua imagem
add_bg_from_local('assets/TP/logo_rede_A.png')

# ------------------------ Imagem terminal ---------------------------
image_path = "assets/TP/TPLC_Horizontal.jpg"

with open(image_path, "rb") as img_file:
    base64_img = base64.b64encode(img_file.read()).decode()

st.markdown(f"""
    <style>
        [data-testid="stSidebar"]::before {{
            content: "";
            display: block;
            background-image: url("data:image/png;base64,{base64_img}");
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            height: 120px;
            margin: 20px 10px;
        }}
    </style>
""", unsafe_allow_html=True)

# ─── CARREGAMENTO E PRÉ-PROCESSAMENTO ────────────────────────────────────────
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    
    df.columns = [
        'Nome', 'Idade', 'Destino_Pescado', 'Arte_Pesca', 'Isca', 'Local_Isca', 
        'Pesca_Noite_Hora', 'Melhor_Pior_Epoca', 'Dias_Pesca_Melhor_Epoca', 
        'Kilos_Medios', 'Rede_Espera', 'Kilos_Mar_Ruim', 'Tempo_Pesca_Horas', 
        'Influencia_Lua_Melhor', 'Peixes_Canal', 'Bichos_Marinhos', 'Local'
    ]
    
    # Conversões numéricas
    df['Idade'] = pd.to_numeric(df['Idade'], errors='coerce')
    df['Kilos_Medios_Num']   = df['Kilos_Medios'].str.extract('(\d+)').astype(float).fillna(0)
    df['Kilos_Mar_Ruim_Num'] = df['Kilos_Mar_Ruim'].str.extract('(\d+)').astype(float).fillna(0)
    df['Tempo_Pesca_Horas_Num'] = df['Tempo_Pesca_Horas'].str.extract('(\d+)').astype(float).fillna(0)
    df['Dias_Pesca_Num'] = df['Dias_Pesca_Melhor_Epoca'].replace('Todos os dias', '7').str.extract('(\d+)').astype(float).fillna(0)
    
    # Coluna auxiliar: pesca noturna?
    df['Pesca_Noturna'] = df['Pesca_Noite_Hora'].str.contains('Sim', case=False, na=False)
    
    return df

try:
    df = load_data("data/tabela_combinada_final.xlsx")
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# ─── FILTRO GLOBAL ───────────────────────────────────────────────────────────
st.sidebar.header("Filtros")
locais_disponiveis = ["Todos"] + sorted(df['Local'].dropna().unique().tolist())
local_selecionado = st.sidebar.selectbox("Local / Associação", locais_disponiveis)

if local_selecionado != "Todos":
    df_filtrado = df[df['Local'] == local_selecionado].copy()
else:
    df_filtrado = df.copy()

# ─── FUNÇÃO AUXILIAR ────────────────────────────────────────────
def get_top_items(series, top_n=6):
    all_items = series.dropna().astype(str).str.lower().str.replace(r'[./]', ',', regex=True).str.strip()
    items_list = [item.strip() for sublist in all_items.str.split(',') for item in sublist if item.strip()]
    counts = pd.Series(items_list).value_counts().head(top_n)
    return counts.reset_index().rename(columns={'index':'item', 0:'count'})

# ─── KPIs ────────────────────────────────────────────────────────────────────
st.title("🐟 DADOS PESQUEIROS PIAUI")
st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)

avg_kilos     = df_filtrado['Kilos_Medios_Num'].mean()
avg_days      = df_filtrado['Dias_Pesca_Num'].mean()
avg_kilos_ruim = df_filtrado['Kilos_Mar_Ruim_Num'].mean()
avg_time      = df_filtrado['Tempo_Pesca_Horas_Num'].mean()
avg_idade     = df_filtrado['Idade'].mean()

col1.metric("Média Captura (kg)",     f"{avg_kilos:.1f}")
col2.metric("Dias/semana (melhor época)", f"{avg_days:.1f}")
col3.metric("Captura mar ruim (kg)",  f"{avg_kilos_ruim:.1f}",
            delta=f"{(avg_kilos_ruim / avg_kilos * 100 - 100):+.1f}%" if avg_kilos > 0 else "—")
col4.metric("Tempo médio no mar",     f"{avg_time:.1f} h")
col5.metric("Idade média",            f"{avg_idade:.1f} anos" if not pd.isna(avg_idade) else "—")

st.markdown("---")

# ─── PRIMEIRA LINHA ──────────────────────────────────────────────────────────
col_g1, col_g2, col_g3 = st.columns(3)

# 1. Destino do pescado
with col_g1:
    st.subheader("📊 Quem compra o pescado")
    destino = df_filtrado['Destino_Pescado'].str.split(',').explode().str.strip().value_counts().head(8).reset_index()
    destino = destino.sort_values('count', ascending=True)
    destino.columns = ['Destino', 'Quantidade']
    fig1 = px.bar(destino, x="Quantidade", y="Destino", orientation='h',
                  color="Quantidade", color_continuous_scale="blues",
                  text_auto=True, title="Mais citados")
    fig1.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig1, use_container_width=True)

# 2. Top espécies no canal
with col_g2:
    st.subheader("🐟 Top espécies (canal)")
    top_peixes = get_top_items(df_filtrado['Peixes_Canal'])
    top_peixes = top_peixes.sort_values('count', ascending=True)
    fig2 = px.bar(top_peixes, x="count", y="item", orientation='h',
                  color="count", color_continuous_scale="viridis",
                  text_auto=True, title="Mais citadas")
    fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig2, use_container_width=True)

# 3. Histograma idade dos pescadores
with col_g3:
    st.subheader("👤 Distribuição de Idade")
    fig_idade = px.histogram(df_filtrado, x="Idade", nbins=15,
                             title="Histograma de Idades",
                             color_discrete_sequence=["#636EFA"])
    fig_idade.update_layout(xaxis_title="Idade (anos)", yaxis_title="Quantidade", bargap=0.1)
    st.plotly_chart(fig_idade, use_container_width=True)

st.markdown("---")

# ─── SEGUNDA LINHA ───────────────────────────────────────────────────────────
col_l1, col_l2, col_l3 = st.columns(3)

# Artes de pesca
with col_l1:
    st.subheader("🎣 Artes de Pesca")
    top_artes = get_top_items(df_filtrado['Arte_Pesca'])
    fig3 = px.pie(top_artes, values="count", names="item",
                  title="Proporção das Artes", hole=0.4,
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig3.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig3, use_container_width=True)

# Influência da Lua
with col_l2:
    st.subheader("🌙 Melhor Lua")
    lua = df_filtrado['Influencia_Lua_Melhor'].str.split(',').explode().str.strip().str.lower().value_counts().head(8).reset_index()
    lua.columns = ['Lua', 'Quantidade']
    fig4 = px.bar(lua, x="Lua", y="Quantidade", color="Quantidade",
                  color_continuous_scale="plasma", text_auto=True)
    fig4.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig4, use_container_width=True)

# Top Iscas
with col_l3:
    st.subheader("🪝 Top Iscas Utilizadas")
    top_isca = get_top_items(df_filtrado['Isca'])
    top_isca = top_isca.sort_values('count', ascending=True)
    fig_isca = px.bar(top_isca, x="count", y="item", orientation='h',
                      color="count", color_continuous_scale="greens",
                      text_auto=True, title="Mais citadas")
    fig_isca.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_isca, use_container_width=True)

st.markdown("---")

# ─── TERCEIRA LINHA ──────────────────────────────────────────────────────────
col_a1, col_a2 = st.columns(2)

# Pesca noturna
with col_a1:
    st.subheader("🌙 Pesca Noturna")
    prop_noturna = df_filtrado['Pesca_Noturna'].mean() * 100
    fig_noturna = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = prop_noturna,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "% que pesca à noite"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "#AB63FA"},
            'steps' : [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "gray"}],
            'threshold' : {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': prop_noturna}}))
    fig_noturna.update_layout(height=250, margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig_noturna, use_container_width=True)

# Animais marinhos observados
with col_a2:
    st.subheader("🐢 Animais Marinhos Observados")
    animais = df_filtrado['Bichos_Marinhos'].str.lower().str.contains('tartaruga|peixe-boi|boto|golfinho|tubarao|aruaná', na=False)
    contagem_animais = animais.value_counts().reset_index()
    contagem_animais.columns = ['Visto', 'Quantidade']
    contagem_animais['Visto'] = contagem_animais['Visto'].map({True: 'Sim', False: 'Não/Não citado'})
    
    fig_anim = px.pie(contagem_animais, values='Quantidade', names='Visto',
                      title="Pelo menos um animal marinho citado?",
                      color_discrete_sequence=["#EF553B", "#00CC96"])
    fig_anim.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_anim, use_container_width=True)

st.markdown("---")

# Carrosel imagens
tab1, tab2, tab3 = st.tabs(["Imagem A", "Imagem B", "Imagem C"])

with tab1:
    st.image("assets/TP/CSL/1.jpg")
with tab2:
    st.image("assets/TP/CSL/2.jpg")
with tab3:
    st.image("assets/TP/CSL/3.jpg")


# Tabela final
st.subheader("Dados Brutos (amostra filtrada)")
st.dataframe(
    df_filtrado[['Nome', 'Local', 'Idade', 'Kilos_Medios_Num', 'Dias_Pesca_Num', 
                 'Destino_Pescado', 'Arte_Pesca', 'Isca']]
    .head(150)
    .style.format(precision=1)
)

# Rodapé
st.markdown("---")
st.caption("Dashboard construído com base nas entrevistas realizadas pela Cia. Portos e hidrovias do Piaui.")