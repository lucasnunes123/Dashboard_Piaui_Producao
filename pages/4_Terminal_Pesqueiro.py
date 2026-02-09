import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuração inicial da página
st.set_page_config(layout="wide", page_title="Dashboard Terminal Pesqueiro")

# CARREGAMENTO E PRÉ-PROCESSAMENTO DE DADOS

@st.cache_data
def load_data(file_path):
    """Carrega, limpa e prepara os dados."""
    df = pd.read_excel(file_path)
    
    df.columns = [
        'Nome', 'Idade', 'Destino_Pescado', 'Arte_Pesca', 'Isca', 'Local_Isca', 
        'Pesca_Noite_Hora', 'Melhor_Pior_Epoca', 'Dias_Pesca_Melhor_Epoca', 
        'Kilos_Medios', 'Rede_Espera', 'Kilos_Mar_Ruim', 'Tempo_Pesca_Horas', 
        'Influencia_Lua_Melhor', 'Peixes_Canal', 'Bichos_Marinhos', 'Local'
    ]
    
    # Extração numérica
    df['Kilos_Medios_Num']   = df['Kilos_Medios'].str.extract('(\d+)').astype(float).fillna(0)
    df['Kilos_Mar_Ruim_Num'] = df['Kilos_Mar_Ruim'].str.extract('(\d+)').astype(float).fillna(0)
    df['Tempo_Pesca_Horas_Num'] = df['Tempo_Pesca_Horas'].str.extract('(\d+)').astype(float).fillna(0)
    df['Dias_Pesca_Num'] = df['Dias_Pesca_Melhor_Epoca'].replace('Todos os dias', '7').str.extract('(\d+)').astype(float).fillna(0)
    
    return df

try:
    df = load_data("data/tabela_combinada_final.xlsx")
except FileNotFoundError:
    st.error("Arquivo 'tabela_combinada_final.xlsx' não encontrado.")
    st.stop()

# Função auxiliar (mantida)
def get_top_items(series, top_n=5):
    all_items = series.dropna().astype(str).str.lower().str.replace('.', '').str.replace('/', ',').str.strip()
    items_list = [item.strip() for sublist in all_items.str.split(',') for item in sublist]
    counts = pd.Series(items_list).value_counts()
    return counts[counts.index != ''].head(top_n).reset_index().rename(columns={'index':'item', 0:'count'})

# ────────────────────────────────────────────────
# LAYOUT
# ────────────────────────────────────────────────

st.title("🐟 Análise de Dados - Terminal Pesqueiro")
st.markdown("---")

# KPIs
col1, col2, col3, col4 = st.columns(4)

avg_kilos     = df['Kilos_Medios_Num'].mean()
avg_days      = df['Dias_Pesca_Num'].mean()
avg_kilos_ruim = df['Kilos_Mar_Ruim_Num'].mean()
avg_time      = df['Tempo_Pesca_Horas_Num'].mean()

col1.metric("Média de Captura por Pescador (Kg)", f"{avg_kilos:,.1f}")
col2.metric("Média de Dias de Pesca na Melhor Época", f"{avg_days:.1f} dias")
col3.metric(
    "Média de Captura com Mar Ruim (Kg)",
    f"{avg_kilos_ruim:.1f}",
    delta=f"{(avg_kilos_ruim / avg_kilos - 1) * 100:.1f}% da média normal" if avg_kilos > 0 else "—",
    delta_color="inverse"
)
col4.metric("Tempo Médio de Pesca (Horas)", f"{avg_time:.1f}h")

st.markdown("---")

# ────────────────────────────────────────────────
# PRIMEIRA LINHA DE GRÁFICOS
# ────────────────────────────────────────────────

col_g1, col_g2 = st.columns(2)

# Gráfico 1: Destino do Pescado (barras horizontais)
with col_g1:
    st.subheader("📊 Destino do Pescado")
    destino = df['Destino_Pescado'].str.split(',').explode().str.strip().value_counts().head(8).reset_index()
    destino.columns = ['Destino', 'Quantidade']
    destino = destino.sort_values(by='Quantidade', ascending=True)
    
    fig1 = px.bar(
        destino,
        x="Quantidade",
        y="Destino",
        orientation='h',
        color="Quantidade",
        color_continuous_scale="blues",
        title="Quem compra o pescado (mais citados)",
        text_auto=True
    )
    fig1.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig1, use_container_width=True)

# Gráfico 2: Top espécies no canal
with col_g2:
    st.subheader("🐟 Top 5 Espécies Mais Capturadas (no canal)")
    top_peixes = get_top_items(df['Peixes_Canal'])
    top_peixes = top_peixes.sort_values(by='count', ascending=True)
    
    fig2 = px.bar(
        top_peixes,
        x="count",
        y="item",
        orientation='h',
        color="count",
        color_continuous_scale="viridis",
        title="Espécies mais citadas",
        text_auto=True
    )
    fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ────────────────────────────────────────────────
# SEGUNDA LINHA DE GRÁFICOS
# ────────────────────────────────────────────────

col_l1, col_l2 = st.columns(2)

# Gráfico 3: Artes de pesca (pizza)
with col_l1:
    st.subheader("🎣 Artes de Pesca Utilizadas")
    top_artes = get_top_items(df['Arte_Pesca'])
    
    fig3 = px.pie(
        top_artes,
        values="count",
        names="item",
        title="Proporção das Artes de Pesca",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig3.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig3, use_container_width=True)

# Gráfico 4: Influência da Lua
with col_l2:
    st.subheader("🌙 Influência da Lua")
    lua = df['Influencia_Lua_Melhor'].str.split(',').explode().str.strip().str.lower().value_counts().head(8).reset_index()
    lua.columns = ['Lua', 'Quantidade']
    
    fig4 = px.bar(
        lua,
        x="Lua",
        y="Quantidade",
        color="Quantidade",
        color_continuous_scale="plasma",
        title="Melhor Lua para Pesca (citações)",
        text_auto=True
    )
    fig4.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig4, use_container_width=True)

# Imagem (mantida)
st.image("assets/luis.png", width=800)

st.markdown("---")

# Tabela final
st.subheader("Tabela de Dados Brutos (Amostra)")
st.dataframe(
    df[['Nome', 'Local', 'Kilos_Medios_Num', 'Dias_Pesca_Num', 'Destino_Pescado', 'Arte_Pesca']]
    .head(100)
    .style.format({
        'Kilos_Medios_Num': '{:.1f}',
        'Dias_Pesca_Num': '{:.0f}'
    })
)