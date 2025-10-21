import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração inicial da página
st.set_page_config(layout="wide", page_title="Dashboard Terminal Pesqueiro")

# --- 1. CARREGAMENTO E PRÉ-PROCESSAMENTO DE DADOS ---
@st.cache_data
def load_data(file_path):
    """Carrega, limpa e prepara os dados."""
    df = pd.read_excel(file_path)
    
    # Renomear colunas para facilitar o uso (opcional, mas recomendado)
    df.columns = [
        'Nome', 'Idade', 'Destino_Pescado', 'Arte_Pesca', 'Isca', 'Local_Isca', 
        'Pesca_Noite_Hora', 'Melhor_Pior_Epoca', 'Dias_Pesca_Melhor_Epoca', 
        'Kilos_Medios', 'Rede_Espera', 'Kilos_Mar_Ruim', 'Tempo_Pesca_Horas', 
        'Influencia_Lua_Melhor', 'Peixes_Canal', 'Bichos_Marinhos', 'Local'
    ]
    
    # Limpeza e conversão para números
    # Tenta extrair o valor numérico (assumindo que "X quilos" ou "Y horas" são o formato)
    df['Kilos_Medios_Num'] = df['Kilos_Medios'].str.extract('(\d+)').astype(float).fillna(0)
    df['Kilos_Mar_Ruim_Num'] = df['Kilos_Mar_Ruim'].str.extract('(\d+)').astype(float).fillna(0)
    df['Tempo_Pesca_Horas_Num'] = df['Tempo_Pesca_Horas'].str.extract('(\d+)').astype(float).fillna(0)
    
    # Limpa a coluna 'Dias_Pesca_Melhor_Epoca'
    df['Dias_Pesca_Num'] = df['Dias_Pesca_Melhor_Epoca'].replace('Todos os dias', 7).str.extract('(\d+)').astype(float).fillna(0)
    
    return df

try:
    df = load_data("data/tabela_combinada_final.xlsx")
except FileNotFoundError:
    st.error("Erro: O arquivo 'tabela_combinada_final.xlsx - Sheet1.csv' não foi encontrado. Certifique-se de que ele está no mesmo diretório do script.")
    st.stop()
    
# --- Funções de Análise ---
def get_top_items(series, top_n=5):
    """Conta e retorna os itens mais frequentes de uma coluna que contém múltiplos valores separados por vírgula."""
    all_items = series.dropna().astype(str).str.lower().str.replace('.', '').str.replace('/', ',').str.strip()
    # Expande a lista de itens
    items_list = [item.strip() for sublist in all_items.str.split(',') for item in sublist]
    # Filtra vazios e conta
    counts = pd.Series(items_list).value_counts()
    return counts[counts.index != ''].head(top_n)

# --- 2. LAYOUT DA APLICAÇÃO ---

st.title("🐟 Análise de Dados - Terminal Pesqueiro")
st.markdown("---")

# --- 3. LINHA DE KPIS (KEY PERFORMANCE INDICATORS) ---
col1, col2, col3, col4 = st.columns(4)

# KPI 1: Média de Captura
avg_kilos = df['Kilos_Medios_Num'].mean()
col1.metric(
    label="Média de Captura por Pescador (Kg)", 
    value=f"{avg_kilos:,.1f}", 
    delta=None
)

# KPI 2: Média de Dias de Pesca
avg_days = df['Dias_Pesca_Num'].mean()
col2.metric(
    label="Média de Dias de Pesca na Melhor Época", 
    value=f"{avg_days:.1f} dias", 
    delta=None
)

# KPI 3: Produtividade em Condições Ruins
avg_kilos_ruim = df['Kilos_Mar_Ruim_Num'].mean()
col3.metric(
    label="Média de Captura com Mar Ruim (Kg)", 
    value=f"{avg_kilos_ruim:.1f}", 
    delta=f"{(avg_kilos_ruim / avg_kilos - 1) * 100:.1f}% da média normal", 
    delta_color="inverse"
)

# KPI 4: Tempo médio no mar
avg_time = df['Tempo_Pesca_Horas_Num'].mean()
col4.metric(
    label="Tempo Médio de Pesca (Horas)", 
    value=f"{avg_time:.1f}h", 
    delta=None
)

st.markdown("---")

# --- 4. GRÁFICOS DE MERCADO E ESFORÇO ---

col_g1, col_g2 = st.columns(2)

# Gráfico 1: Destino do Pescado
with col_g1:
    st.subheader("📊 Destino do Pescado")
    
    # Limpa a coluna, agrupando as categorias principais
    destino_counts = df['Destino_Pescado'].str.split(',').explode().str.strip().value_counts().head(5)
    
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    sns.barplot(x=destino_counts.index, y=destino_counts.values, ax=ax1, palette="Blues_d")
    ax1.set_title('Quem Compra o Pescado')
    ax1.set_ylabel('Nº de Citações')
    ax1.set_xlabel('')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig1)

# Gráfico 2: Top Espécies Capturadas
with col_g2:
    st.subheader("🐟 Top 5 Espécies Mais Capturadas (no canal)")
    top_peixes = get_top_items(df['Peixes_Canal'])

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    sns.barplot(x=top_peixes.index, y=top_peixes.values, ax=ax2, palette="viridis")
    ax2.set_title('Espécies mais citadas')
    ax2.set_ylabel('Nº de Citações')
    ax2.set_xlabel('')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig2)

st.markdown("---")

# --- 5. GRÁFICOS DE LOGÍSTICA E INFLUÊNCIA ---
col_l1, col_l2 = st.columns(2)

# Gráfico 3: Distribuição das Artes de Pesca
with col_l1:
    st.subheader("🎣 Artes de Pesca Utilizadas")
    
    # Usa a função para contar as artes de pesca (separadas por vírgula)
    top_artes = get_top_items(df['Arte_Pesca'])

    fig3, ax3 = plt.subplots(figsize=(6, 4))
    ax3.pie(top_artes.values, labels=top_artes.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("Set2"))
    ax3.axis('equal') # Garante que o gráfico de pizza seja um círculo
    ax3.set_title('Proporção das Artes de Pesca')
    st.pyplot(fig3)

# Gráfico 4: Influência da Lua
with col_l2:
    st.subheader("🌙 Influência da Lua")
    
    # Limpa a coluna da lua
    lua_counts = df['Influencia_Lua_Melhor'].str.split(',').explode().str.strip().str.lower().value_counts().head(5)

    fig4, ax4 = plt.subplots(figsize=(6, 4))
    sns.barplot(x=lua_counts.index, y=lua_counts.values, ax=ax4, palette="plasma")
    ax4.set_title('Melhor Lua para Pesca (Citações)')
    ax4.set_ylabel('Nº de Citações')
    ax4.set_xlabel('')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig4)

st.image("assets/luis.png", width=800)


st.markdown("---")
# --- 6. Tabela de Detalhes ---
st.subheader("Tabela de Dados Brutos (Amostra)")
st.dataframe(df[['Nome', 'Local', 'Kilos_Medios_Num', 'Dias_Pesca_Num', 'Destino_Pescado', 'Arte_Pesca']].head(100))