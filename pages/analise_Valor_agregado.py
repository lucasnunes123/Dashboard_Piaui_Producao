import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from utils.data_loader import load_data

st.set_page_config(page_title="Análise de Valor Agregado", page_icon="💰", layout="wide")

# Carregamento dos dados
@st.cache_data
def get_data():
    df = load_data()
    # Calcular valor por kg
    df['Valor por kg'] = df['Valor US$ FOB'] / df['Quilograma Líquido'].replace(0, np.nan)
    return df

df = get_data()

# Título e descrição
st.title("Análise de Valor Agregado")
st.markdown("Análise da eficiência e valor agregado das exportações e importações")

# Filtros
col1, col2 = st.columns(2)
with col1:
    ano_selecionado = st.multiselect(
        "Selecione o(s) ano(s):",
        options=sorted(df['Ano'].unique()),
        default=sorted(df['Ano'].unique())
    )
with col2:
    fluxo_selecionado = st.multiselect(
        "Tipo de fluxo:",
        options=df['Fluxo'].unique(),
        default=df['Fluxo'].unique()
    )

# Filtrar dados
filtered_df = df.copy()
if ano_selecionado:
    filtered_df = filtered_df[filtered_df['Ano'].isin(ano_selecionado)]
if fluxo_selecionado:
    filtered_df = filtered_df[filtered_df['Fluxo'].isin(fluxo_selecionado)]

# Remover valores infinitos ou NaN
filtered_df = filtered_df[~filtered_df['Valor por kg'].isna() & ~np.isinf(filtered_df['Valor por kg'])]

# Gráfico de dispersão: Valor vs. Peso
st.subheader("Relação entre Valor e Peso")
fig_scatter = px.scatter(
    filtered_df,
    x='Quilograma Líquido',
    y='Valor US$ FOB',
    color='Município',
    size='Valor US$ FOB',
    hover_name='Município',
    log_x=True,
    log_y=True,
    title='Relação entre Valor US$ FOB e Quilograma Líquido',
    labels={
        'Quilograma Líquido': 'Peso (kg) - escala logarítmica',
        'Valor US$ FOB': 'Valor (US$) - escala logarítmica'
    }
)
st.plotly_chart(fig_scatter, use_container_width=True)

# Top municípios por valor por kg
st.subheader("Municípios com Maior Valor Agregado")

# Calcular valor médio por kg para cada município
valor_por_kg = filtered_df.groupby('Município')['Valor por kg'].mean().reset_index()
valor_por_kg = valor_por_kg.sort_values('Valor por kg', ascending=False).head(15)

fig_valor_kg = px.bar(
    valor_por_kg,
    x='Município',
    y='Valor por kg',
    title='Top 15 Municípios por Valor Médio por kg',
    labels={'Valor por kg': 'Valor Médio (US$/kg)', 'Município': 'Município'},
    color='Valor por kg',
    color_continuous_scale=px.colors.sequential.Plasma
)
st.plotly_chart(fig_valor_kg, use_container_width=True)

# Tabela de dados
st.subheader("Dados Detalhados de Valor Agregado")
st.dataframe(
    filtered_df[['Município', 'Ano', 'Fluxo', 'Valor US$ FOB', 'Quilograma Líquido', 'Valor por kg']]
    .sort_values('Valor por kg', ascending=False)
)