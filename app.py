import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data, get_summary_stats

# Configuração da página
st.set_page_config(
    page_title="Dashboard Comercial - Municípios do Piauí",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregamento dos dados
@st.cache_data
def get_data():
    return load_data()

df = get_data()
stats = get_summary_stats(df)

# Sidebar para filtros
st.sidebar.title("Filtros")

# Filtro de ano
anos = sorted(df['Ano'].unique())
ano_selecionado = st.sidebar.multiselect(
    "Selecione o(s) ano(s):",
    options=anos,
    default=anos
)

# Filtro de fluxo
fluxo_selecionado = st.sidebar.multiselect(
    "Tipo de fluxo:",
    options=df['Fluxo'].unique(),
    default=df['Fluxo'].unique()
)

# Filtro de município
todos_municipios = sorted(df['Município'].unique())
municipio_selecionado = st.sidebar.multiselect(
    "Selecione o(s) município(s):",
    options=todos_municipios,
    default=[]
)

# Aplicar filtros
filtered_df = df.copy()
if ano_selecionado:
    filtered_df = filtered_df[filtered_df['Ano'].isin(ano_selecionado)]
if fluxo_selecionado:
    filtered_df = filtered_df[filtered_df['Fluxo'].isin(fluxo_selecionado)]
if municipio_selecionado:
    filtered_df = filtered_df[filtered_df['Município'].isin(municipio_selecionado)]

# Título principal
st.title("Dashboard Comercial - Municípios do Piauí")
st.markdown("Análise de dados de exportação e importação dos municípios do Piauí (2020-2025)")

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Exportação (US$)", f"${stats['total_exportacao']:,.2f}")
with col2:
    st.metric("Total Importação (US$)", f"${stats['total_importacao']:,.2f}")
with col3:
    st.metric("Saldo Comercial (US$)", f"${stats['saldo_comercial']:,.2f}")
with col4:
    st.metric("Municípios", stats['total_municipios'])

# Gráfico de evolução temporal
st.subheader("Evolução do Comércio Exterior ao Longo do Tempo")

# Agregação por ano e fluxo
evolucao_temporal = filtered_df.groupby(['Ano', 'Fluxo'])['Valor US$ FOB'].sum().reset_index()

fig_evolucao = px.line(
    evolucao_temporal, 
    x='Ano', 
    y='Valor US$ FOB',
    color='Fluxo',
    title='Evolução dos Valores de Exportação e Importação',
    labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Ano': 'Ano'},
    markers=True
)
st.plotly_chart(fig_evolucao, use_container_width=True)

# Top 10 municípios
st.subheader("Top 10 Municípios por Valor Comercial")

top_municipios = filtered_df.groupby('Município')['Valor US$ FOB'].sum().reset_index()
top_municipios = top_municipios.sort_values('Valor US$ FOB', ascending=False).head(10)

fig_top_municipios = px.bar(
    top_municipios,
    x='Município',
    y='Valor US$ FOB',
    title='Top 10 Municípios por Valor Comercial',
    labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Município': 'Município'},
    color='Valor US$ FOB',
    color_continuous_scale=px.colors.sequential.Viridis
)
st.plotly_chart(fig_top_municipios, use_container_width=True)

# Tabela de dados
st.subheader("Dados Detalhados")
st.dataframe(filtered_df)