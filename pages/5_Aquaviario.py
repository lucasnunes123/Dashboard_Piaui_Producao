import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard Pesca TPLC", layout="wide")

# 1. Carregamento e Limpeza Básica
@st.cache_data
def load_data():
    df = pd.read_excel("data/DiagnosticoTPLC.xlsx")
    
    # Limpeza básica de strings
    cols_texto = df.select_dtypes(include=['object']).columns
    for col in cols_texto:
        df[col] = df[col].str.strip().str.upper()
    
    return df

df = load_data()

# --- SIDEBAR (Filtros) ---
st.sidebar.header("Filtros")
comunidade = st.sidebar.multiselect(
    "Selecione a Comunidade",
    options=df["Comunidade"].unique(),
    default=df["Comunidade"].unique()
)

genero = st.sidebar.multiselect(
    "Gênero",
    options=df["Genero"].unique(),
    default=df["Genero"].unique()
)

# Aplicando os filtros
df_filtered = df[(df["Comunidade"].isin(comunidade)) & (df["Genero"].isin(genero))]

# --- DASHBOARD PRINCIPAL ---
st.title("📊 Diagnóstico da Atividade Pesqueira")
st.markdown(f"Exibindo dados de **{len(df_filtered)}** pescadores entrevistados.")

# Linha 1: Métricas e Perfil
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribuição por Idade")
    fig_idade = px.pie(df_filtered, names='Idade', hole=0.4, 
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_idade, use_container_width=True)

with col2:
    st.subheader("Renda Mensal Familiar")
    # Ordenando manualmente as categorias de renda para o gráfico fazer sentido
    ordem_renda = ["ATE 500,00", "DE 501,00 A 1.000,00", "DE 1.001,00 A 2.000,00", "MAIS DE 2.001,00"]
    fig_renda = px.bar(df_filtered, x='Renda_mensal_total_familia', 
                       category_orders={"Renda_mensal_total_familia": ordem_renda},
                       color_discrete_sequence=['#2E8B57'])
    st.plotly_chart(fig_renda, use_container_width=True)

# Linha 2: Análise de Espécies (Onde usamos o Explode)
st.divider()
st.subheader("📍 Top Espécies Capturadas")

# Tratamento para colunas com múltiplos valores (separados por ;)
especies_series = df_filtered['Especies_importantes_captrura'].dropna().str.split(';').explode()
df_especies = especies_series.value_counts().reset_index()
df_especies.columns = ['Espécie', 'Contagem']

fig_especies = px.bar(df_especies.head(10), x='Contagem', y='Espécie', 
                      orientation='h', color='Contagem',
                      color_continuous_scale='Viridis')
st.plotly_chart(fig_especies, use_container_width=True)

# Linha 3: Artes de Pesca e Problemas
col3, col4 = st.columns(2)

with col3:
    st.subheader("Artes de Pesca Utilizadas")
    artes_series = df_filtered['Arte_pesca'].dropna().str.split(';').explode()
    df_artes = artes_series.value_counts().reset_index()
    fig_artes = px.funnel(df_artes, x='count', y='Arte_pesca')
    st.plotly_chart(fig_artes, use_container_width=True)

with col4:
    st.subheader("Principais Fatores Prejudiciais")
    fatores_series = df_filtered['Fatores_prejudicam_pesca'].dropna().str.split(';').explode()
    df_fatores = fatores_series.value_counts().reset_index()
    fig_fatores = px.treemap(df_fatores, path=['Fatores_prejudicam_pesca'], values='count')
    st.plotly_chart(fig_fatores, use_container_width=True)

# Visualização da Tabela
if st.checkbox("Mostrar dados brutos"):
    st.dataframe(df_filtered)