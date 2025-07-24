import streamlit as st
import pandas as pd
import plotly.express as px
import json
import geopandas as gpd
from utils.data_loader import carregar_dados as load_data

st.set_page_config(page_title="Análise Geográfica", page_icon="🗺️", layout="wide")

# Carregamento dos dados
@st.cache_data
def get_data():
    return load_data()

df = get_data()

# Carregar GeoJSON do Piauí
@st.cache_data
def load_geojson():
    try:
        with open('assets/PI_Municipios_2023.json', encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Arquivo GeoJSON não encontrado. Por favor, adicione o arquivo de mapa do Piauí.")
        return None

geojson_data = load_geojson()

# Título e descrição
st.title("Análise Geográfica - Municípios do Piauí")
st.markdown("Visualização da distribuição geográfica do comércio exterior no estado do Piauí")

# Filtros
col1, col2 = st.columns(2)
with col1:
    ano_selecionado = st.selectbox("Selecione o ano:", options=sorted(df['Ano'].unique()))
with col2:
    fluxo_selecionado = st.selectbox("Tipo de fluxo:", options=df['Fluxo'].unique())

# Filtrar dados
filtered_df = df[(df['Ano'] == ano_selecionado) & (df['Fluxo'] == fluxo_selecionado)]

# Agregar dados por município
municipio_data = filtered_df.groupby('Município')['Valor US$ FOB'].sum().reset_index()

# Mapa coroplético
if geojson_data:
    st.subheader(f"Mapa de Valores Comerciais - {ano_selecionado}")
    
    fig = px.choropleth_mapbox(
        municipio_data,
        geojson=geojson_data,
        locations='Município',
        featureidkey='properties.NM_MUN',
        color='Valor US$ FOB',
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": -7.7, "lon": -42.7},  # Coordenadas aproximadas do Piauí
        opacity=0.7,
        labels={'Valor US$ FOB': 'Valor (US$ FOB)'}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    # Alternativa se não tiver o GeoJSON
    st.subheader("Top Municípios por Valor Comercial")
    
    # Ordenar por valor
    municipio_data = municipio_data.sort_values('Valor US$ FOB', ascending=False)
    
    fig = px.bar(
        municipio_data,
        x='Município',
        y='Valor US$ FOB',
        title=f'Valores Comerciais por Município - {ano_selecionado}',
        labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Município': 'Município'},
        color='Valor US$ FOB',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    st.plotly_chart(fig, use_container_width=True)

# Tabela de dados
st.subheader("Dados por Município")
st.dataframe(municipio_data)