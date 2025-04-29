import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Comércio Exterior - Piauí",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    df = pd.read_excel('data/Dados_POR MUNICIPIO_2020_2025.xlsx', sheet_name='Resultado')
    
    # Adicionar colunas calculadas
    df['Valor por kg'] = df['Valor US$ FOB'] / df['Quilograma Líquido'].replace(0, np.nan)
    
    # Converter tipos de dados se necessário
    df['Ano'] = df['Ano'].astype(int)
    
    return df

# Carregar os dados
try:
    df = carregar_dados()
    
    # Obter estatísticas gerais
    total_exportacao = df[df['Fluxo'] == 'Exportação']['Valor US$ FOB'].sum()
    total_importacao = df[df['Fluxo'] == 'Importação']['Valor US$ FOB'].sum()
    saldo_comercial = total_exportacao - total_importacao
    total_paises = df['País'].nunique()
    total_produtos = df['Descrição SH4'].nunique()
    
    # Título e descrição
    st.title("Dashboard de Comércio Exterior - Piauí (2020-2025)")
    st.markdown("""
    Este dashboard apresenta uma análise detalhada dos dados de comércio exterior dos municípios do Piauí 
    entre 2020 e 2025, incluindo exportações e importações, principais produtos, países e municípios.
    """)
    
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
    
    # Filtro de município (top 15 + opção "Outros")
    top_municipios = df.groupby('Município')['Valor US$ FOB'].sum().nlargest(15).index.tolist()
    municipio_selecionado = st.sidebar.multiselect(
        "Selecione o(s) município(s):",
        options=['Todos'] + top_municipios,
    )
    
    # Filtro de país (top 15 + opção "Outros")
    top_paises = df.groupby('País')['Valor US$ FOB'].sum().nlargest(15).index.tolist()
    pais_selecionado = st.sidebar.multiselect(
        "Selecione o(s) país(es):",
        options=['Todos'] + top_paises,
    )
    
    # Filtro de seção
    secoes = sorted(df['Descrição Seção'].unique())
    secao_selecionada = st.sidebar.multiselect(
        "Selecione a(s) seção(ões) de produtos:",
        options=['Todas'] + secoes,
    )
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if ano_selecionado:
        filtered_df = filtered_df[filtered_df['Ano'].isin(ano_selecionado)]
    
    if fluxo_selecionado:
        filtered_df = filtered_df[filtered_df['Fluxo'].isin(fluxo_selecionado)]
    
    if 'Todos' not in municipio_selecionado and municipio_selecionado:
        filtered_df = filtered_df[filtered_df['Município'].isin(municipio_selecionado)]
    
    if 'Todos' not in pais_selecionado and pais_selecionado:
        filtered_df = filtered_df[filtered_df['País'].isin(pais_selecionado)]
    
    if 'Todas' not in secao_selecionada and secao_selecionada:
        filtered_df = filtered_df[filtered_df['Descrição Seção'].isin(secao_selecionada)]
    
    # Verificar se há dados após a filtragem
    if filtered_df.empty:
        st.warning("Não há dados disponíveis para os filtros selecionados. Por favor, ajuste os filtros.")
    else:
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            valor_filtrado = filtered_df['Valor US$ FOB'].sum()
            st.metric("Valor Total (US$)", f"${valor_filtrado:,.2f}")
        
        with col2:
            exp_filtrado = filtered_df[filtered_df['Fluxo'] == 'Exportação']['Valor US$ FOB'].sum()
            imp_filtrado = filtered_df[filtered_df['Fluxo'] == 'Importação']['Valor US$ FOB'].sum()
            saldo_filtrado = exp_filtrado - imp_filtrado
            st.metric("Saldo Comercial (US$)", f"${saldo_filtrado:,.2f}")
        
        with col3:
            peso_filtrado = filtered_df['Quilograma Líquido'].sum()
            st.metric("Volume Total (kg)", f"{peso_filtrado:,.2f}")
        
        with col4:
            if peso_filtrado > 0:
                valor_medio_kg = valor_filtrado / peso_filtrado
                st.metric("Valor Médio (US$/kg)", f"${valor_medio_kg:.2f}")
            else:
                st.metric("Valor Médio (US$/kg)", "N/A")
        
        # Criar abas para organizar as visualizações
        tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral", "Análise Geográfica", "Análise por Produto", "Análise Temporal"])
        
        with tab1:
            st.subheader("Visão Geral do Comércio Exterior")
            
            # Gráfico de barras: Exportação vs Importação por ano
            evolucao_anual = filtered_df.groupby(['Ano', 'Fluxo'])['Valor US$ FOB'].sum().reset_index()
            fig_evolucao = px.bar(
                evolucao_anual,
                x='Ano',
                y='Valor US$ FOB',
                color='Fluxo',
                title='Evolução de Exportações e Importações por Ano',
                labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Ano': 'Ano'},
                barmode='group',
                color_discrete_map={'Exportação': '#2E86C1', 'Importação': '#E74C3C'}
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)
            
            # Gráfico de pizza: Distribuição por fluxo
            dist_fluxo = filtered_df.groupby('Fluxo')['Valor US$ FOB'].sum().reset_index()
            fig_pie_fluxo = px.pie(
                dist_fluxo,
                values='Valor US$ FOB',
                names='Fluxo',
                title='Distribuição por Tipo de Fluxo',
                color='Fluxo',
                color_discrete_map={'Exportação': '#2E86C1', 'Importação': '#E74C3C'}
            )
            
            # Gráfico de pizza: Distribuição por seção
            dist_secao = filtered_df.groupby('Descrição Seção')['Valor US$ FOB'].sum().reset_index()
            dist_secao = dist_secao.sort_values('Valor US$ FOB', ascending=False)
            
            # Limitar a 10 principais seções e agrupar o resto como "Outros"
            if len(dist_secao) > 10:
                top_secoes = dist_secao.head(9)
                outros_valor = dist_secao.iloc[9:]['Valor US$ FOB'].sum()
                outros_df = pd.DataFrame({'Descrição Seção': ['Outras Seções'], 'Valor US$ FOB': [outros_valor]})
                dist_secao = pd.concat([top_secoes, outros_df])
            
            fig_pie_secao = px.pie(
                dist_secao,
                values='Valor US$ FOB',
                names='Descrição Seção',
                title='Distribuição por Seção de Produtos',
                hole=0.4
            )
            
            # Exibir os gráficos de pizza lado a lado
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_pie_fluxo, use_container_width=True)
            with col2:
                st.plotly_chart(fig_pie_secao, use_container_width=True)
        
        with tab2:
            st.subheader("Análise Geográfica")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top 10 municípios
                top_municipios_df = filtered_df.groupby('Município')['Valor US$ FOB'].sum().reset_index()
                top_municipios_df = top_municipios_df.sort_values('Valor US$ FOB', ascending=True).tail(10)
                
                fig_top_municipios = px.bar(
                    top_municipios_df,
                    x='Valor US$ FOB',
                    y='Município',
                    orientation='h',
                    title='Top 10 Municípios por Valor Comercial',
                    labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Município': 'Município'},
                    color='Valor US$ FOB',
                    color_continuous_scale=px.colors.sequential.Blues
                )
                st.plotly_chart(fig_top_municipios, use_container_width=True)
            
            with col2:
                # Top 10 países
                top_paises_df = filtered_df.groupby('País')['Valor US$ FOB'].sum().reset_index()
                top_paises_df = top_paises_df.sort_values('Valor US$ FOB', ascending=True).tail(10)
                
                fig_top_paises = px.bar(
                    top_paises_df,
                    x='Valor US$ FOB',
                    y='País',
                    orientation='h',
                    title='Top 10 Países por Valor Comercial',
                    labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'País': 'País'},
                    color='Valor US$ FOB',
                    color_continuous_scale=px.colors.sequential.Reds
                )
                st.plotly_chart(fig_top_paises, use_container_width=True)
            
            # Mapa de calor: Município x País
            if len(filtered_df['Município'].unique()) <= 20 and len(filtered_df['País'].unique()) <= 20:
                heatmap_data = filtered_df.pivot_table(
                    values='Valor US$ FOB',
                    index='Município',
                    columns='País',
                    aggfunc='sum',
                    fill_value=0
                )
                
                # Selecionar apenas os top municípios e países para o mapa de calor
                top_municipios_heat = filtered_df.groupby('Município')['Valor US$ FOB'].sum().nlargest(10).index
                top_paises_heat = filtered_df.groupby('País')['Valor US$ FOB'].sum().nlargest(10).index
                
                heatmap_data = heatmap_data.loc[
                    heatmap_data.index.isin(top_municipios_heat),
                    heatmap_data.columns.isin(top_paises_heat)
                ]
                
                fig_heatmap = px.imshow(
                    heatmap_data,
                    labels=dict(x="País", y="Município", color="Valor US$ FOB"),
                    title="Mapa de Calor: Relação Município x País",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with tab3:
            st.subheader("Análise por Produto")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top 10 produtos (SH4)
                top_produtos_df = filtered_df.groupby('Descrição SH4')['Valor US$ FOB'].sum().reset_index()
                top_produtos_df = top_produtos_df.sort_values('Valor US$ FOB', ascending=False).head(10)
                
                # Truncar nomes longos de produtos
                top_produtos_df['Descrição SH4 Truncada'] = top_produtos_df['Descrição SH4'].str.slice(0, 50) + '...'
                
                fig_top_produtos = px.bar(
                    top_produtos_df,
                    x='Valor US$ FOB',
                    y='Descrição SH4 Truncada',
                    orientation='h',
                    title='Top 10 Produtos por Valor Comercial',
                    labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Descrição SH4 Truncada': 'Produto'},
                    color='Valor US$ FOB',
                    color_continuous_scale=px.colors.sequential.Greens
                )
                st.plotly_chart(fig_top_produtos, use_container_width=True)
            
            with col2:
                # Valor médio por kg para as principais seções
                valor_por_kg_df = filtered_df.groupby('Descrição Seção')['Valor por kg'].mean().reset_index()
                valor_por_kg_df = valor_por_kg_df.sort_values('Valor por kg', ascending=False).head(10)
                
                # Truncar nomes longos de seções
                valor_por_kg_df['Descrição Seção Truncada'] = valor_por_kg_df['Descrição Seção'].str.slice(0, 50) + '...'
                
                fig_valor_kg = px.bar(
                    valor_por_kg_df,
                    x='Valor por kg',
                    y='Descrição Seção Truncada',
                    orientation='h',
                    title='Valor Médio por kg para as Principais Seções',
                    labels={'Valor por kg': 'Valor Médio (US$/kg)', 'Descrição Seção Truncada': 'Seção'},
                    color='Valor por kg',
                    color_continuous_scale=px.colors.sequential.Oranges
                )
                st.plotly_chart(fig_valor_kg, use_container_width=True)
            
            # Gráfico de dispersão: Valor vs Peso por Seção
            fig_scatter = px.scatter(
                filtered_df,
                x='Quilograma Líquido',
                y='Valor US$ FOB',
                color='Descrição Seção',
                size='Valor US$ FOB',
                hover_name='Descrição SH4',
                log_x=True,
                log_y=True,
                title='Relação entre Valor e Peso por Seção de Produto',
                labels={
                    'Quilograma Líquido': 'Peso (kg) - escala logarítmica',
                    'Valor US$ FOB': 'Valor (US$) - escala logarítmica',
                    'Descrição Seção': 'Seção de Produto'
                }
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with tab4:
            st.subheader("Análise Temporal")
            
            # Evolução temporal por fluxo
            evolucao_temporal = filtered_df.groupby(['Ano', 'Fluxo'])['Valor US$ FOB'].sum().reset_index()
            
            fig_linha_temporal = px.line(
                evolucao_temporal,
                x='Ano',
                y='Valor US$ FOB',
                color='Fluxo',
                title='Evolução Temporal por Tipo de Fluxo',
                labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Ano': 'Ano'},
                markers=True,
                color_discrete_map={'Exportação': '#2E86C1', 'Importação': '#E74C3C'}
            )
            st.plotly_chart(fig_linha_temporal, use_container_width=True)
            
            # Evolução dos principais produtos ao longo do tempo
            top5_produtos = filtered_df.groupby('Descrição SH4')['Valor US$ FOB'].sum().nlargest(5).index
            evolucao_produtos = filtered_df[filtered_df['Descrição SH4'].isin(top5_produtos)]
            evolucao_produtos = evolucao_produtos.groupby(['Ano', 'Descrição SH4'])['Valor US$ FOB'].sum().reset_index()
            
            # Truncar nomes longos de produtos
            evolucao_produtos['Produto Truncado'] = evolucao_produtos['Descrição SH4'].str.slice(0, 30) + '...'
            
            fig_evolucao_produtos = px.line(
                evolucao_produtos,
                x='Ano',
                y='Valor US$ FOB',
                color='Produto Truncado',
                title='Evolução dos 5 Principais Produtos ao Longo do Tempo',
                labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Ano': 'Ano', 'Produto Truncado': 'Produto'},
                markers=True
            )
            st.plotly_chart(fig_evolucao_produtos, use_container_width=True)
            
            # Evolução dos principais países ao longo do tempo
            top5_paises = filtered_df.groupby('País')['Valor US$ FOB'].sum().nlargest(5).index
            evolucao_paises = filtered_df[filtered_df['País'].isin(top5_paises)]
            evolucao_paises = evolucao_paises.groupby(['Ano', 'País'])['Valor US$ FOB'].sum().reset_index()
            
            fig_evolucao_paises = px.line(
                evolucao_paises,
                x='Ano',
                y='Valor US$ FOB',
                color='País',
                title='Evolução dos 5 Principais Países ao Longo do Tempo',
                labels={'Valor US$ FOB': 'Valor (US$ FOB)', 'Ano': 'Ano'},
                markers=True
            )
            st.plotly_chart(fig_evolucao_paises, use_container_width=True)
        
        # Adicionar informações sobre os dados
        st.markdown("---")
        st.markdown(f"""
        **Informações sobre os dados:**
        - Fonte de dados: Comex Stat
        - Período: 2020 a 2025
        - Total de registros: {len(df)}
        - Municípios: {df['Município'].nunique()}
        - Países: {df['País'].nunique()}
        - Produtos (SH4): {df['Descrição SH4'].nunique()}
        - Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """)

except Exception as e:
    st.error(f"Ocorreu um erro ao carregar os dados: {e}")
    st.markdown("""
    Por favor, verifique se o arquivo 'Dados_POR MUNICIPIO_2020_2025.xlsx' está disponível no diretório atual.
    """)
