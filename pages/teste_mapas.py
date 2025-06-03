import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(layout="wide")

st.title("Mapa dos Portos do Brasil - Fluxo de Movimentação")

# Carregar dados
file = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])

if file is not None:
    df = pd.read_excel(file, sheet_name='Folha1')

    # Limpar espaços nos nomes das colunas
    df.columns = df.columns.str.strip()

    # Verificar se a coluna 'Region' existe
    if 'Region' in df.columns:
        # Filtrar Brasil
        df_brasil = df[df['Region'].str.contains('Brazil', case=False, na=False)]
    else:
        st.error("A coluna 'Region' não foi encontrada no arquivo. Verifique o nome correto.")
        st.stop()

    # Agrupar por porto
    df_grouped = df_brasil.groupby('Port').agg({'Qtty': 'sum'}).reset_index()

    # Obter coordenadas dos portos
    geolocator = Nominatim(user_agent="geoapi")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    latitudes = []
    longitudes = []

    with st.spinner('Obtendo coordenadas dos portos...'):
        for port in df_grouped['Port']:
            location = geocode(f"{port}, Brazil")
            if location:
                latitudes.append(location.latitude)
                longitudes.append(location.longitude)
            else:
                latitudes.append(None)
                longitudes.append(None)

    df_grouped['lat'] = latitudes
    df_grouped['lon'] = longitudes

    # Remover portos sem coordenadas
    df_grouped = df_grouped.dropna(subset=['lat', 'lon'])

    # Criar o mapa
    fig = px.scatter_mapbox(
        df_grouped,
        lat="lat",
        lon="lon",
        size="Qtty",
        color="Port",
        hover_name="Port",
        hover_data={"Qtty": True, "lat": False, "lon": False},
        size_max=50,
        zoom=3,
        mapbox_style="carto-positron",
        title="Portos do Brasil - Movimentação"
    )

    st.plotly_chart(fig, use_container_width=True)

