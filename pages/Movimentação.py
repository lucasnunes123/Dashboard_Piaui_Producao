import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuração da página
st.set_page_config(layout="wide", page_title="Dashboard de Movimentações Portuárias")

@st.cache_data
def load_and_preprocess_data(file_path):
    """Carrega e pré-processa os dados do arquivo Excel."""
    try:
        xls_file = pd.ExcelFile(file_path)
        if not xls_file.sheet_names:
            st.error("Erro: O arquivo Excel não contém planilhas.")
            return pd.DataFrame()
        
        df = xls_file.parse(xls_file.sheet_names[0])

        # --- Pré-processamento --- 
        # 1. Tratar "Type of Operation"
        type_of_operation_map = {1.0: "Exportação", 2.0: "Importação"}
        df["Type of Operation"] = df["Type of Operation"].map(type_of_operation_map).fillna("Não especificado")

        # 2. Converter "Tempo de estada" para dias numéricos
        # A data base do Excel para cálculo de dias pode variar, mas geralmente é 1899-12-30
        # Se a coluna já for timedelta, esta conversão pode não ser necessária ou ser diferente.
        # A inspeção mostrou datas como "1900-01-03 00:00:00", o que sugere que é um offset da data base.
        def convert_excel_duration_to_days(excel_date):
            if pd.isna(excel_date):
                return np.nan
            try:
                # Se for string, tenta converter para datetime
                if isinstance(excel_date, str):
                    excel_date = pd.to_datetime(excel_date, errors='coerce')
                
                # Se for datetime, calcula a diferença da data base do Excel
                if pd.api.types.is_datetime64_any_dtype(excel_date):
                    base_date = pd.Timestamp("1899-12-30")
                    # Adicionamos um pequeno delta para evitar problemas de precisão em algumas conversões
                    # e garantimos que o resultado seja em dias.
                    delta = excel_date - base_date
                    return delta.total_seconds() / (24 * 60 * 60) # Convertendo para dias
                # Se já for numérico (pode acontecer se o Excel já interpretou como número de dias)
                elif isinstance(excel_date, (int, float)):
                    return excel_date
            except Exception:
                return np.nan # Retorna NaN se a conversão falhar
            return np.nan

        df["Tempo de Estada (Dias)"] = df["Tempo de estada"].apply(convert_excel_duration_to_days)
        
        # 3. Converter colunas de data para datetime
        date_cols = ["ETA", "ETB", "ETS"]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        # 4. Limpeza básica de colunas para filtros (exemplo)
        cols_to_clean_fillna = {
            "Port": "Não especificado",
            "Terminal": "Não especificado",
            "Berth": "Não especificado",
            "Cargo Type": "Não especificado",
            "Charterer Nome": "Não especificado",
            "Inward/Outward Agent": "Não especificado",
            "Vessel": "Não especificado",
            "Origin/Destiny": "Não especificado"
        }
        for col, fill_value in cols_to_clean_fillna.items():
            if col in df.columns:
                df[col] = df[col].astype(str).fillna(fill_value).str.strip()
                df[col] = df[col].replace(['nan', 'NaN', 'NAN', 'None', ''], fill_value)
            else:
                st.warning(f"Coluna {col} não encontrada no DataFrame para limpeza.")

        # Remover a coluna "ETSETB Port Operator" conforme solicitado
        if "ETSETB Port Operator" in df.columns:
            df = df.drop(columns=["ETSETB Port Operator"])
        if "Tempo de estada" in df.columns: # Coluna original
             df = df.drop(columns=["Tempo de estada"])

        return df

    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{file_path}' não encontrado.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar ou processar o arquivo Excel: {e}")
        return pd.DataFrame()

# --- Carregar Dados --- 
data_path = "data/dd_movexp_2024.xls"
df_original = load_and_preprocess_data(data_path)

if df_original.empty:
    st.stop()

df = df_original.copy() # Trabalhar com uma cópia para os filtros

# --- Título do Dashboard --- 
st.title("🚢 Dashboard de Movimentações Portuárias")
st.markdown("Análise interativa das operações e desempenho portuário.")

# --- Barra Lateral de Filtros --- 
st.sidebar.header("Filtros")

# Filtro de Período (usando ETB como referência, pode ser ajustado)
if 'ETB' in df.columns and not df['ETB'].isnull().all():
    min_date = df["ETB"].min()
    max_date = df["ETB"].max()
    if pd.isna(min_date) or pd.isna(max_date):
        st.sidebar.warning("Não foi possível determinar o período para o filtro de data (ETB).")
        selected_period = None
    else:
        selected_period = st.sidebar.date_input(
            "Selecione o Período (ETB):",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )
        if len(selected_period) == 2:
            df = df[(df["ETB"] >= pd.to_datetime(selected_period[0])) & (df["ETB"] <= pd.to_datetime(selected_period[1]))]
        else: # Caso o usuário desfaça a seleção ou algo dê errado
            st.sidebar.warning("Período inválido selecionado. Exibindo todos os dados.")
else:
    st.sidebar.text("Coluna 'ETB' não disponível para filtro de período.")
    selected_period = None

def create_multiselect_filter(column_name, label):
    if column_name in df.columns:
        options = sorted(df[column_name].astype(str).unique().tolist())
        if "Não especificado" in options:
             options.remove("Não especificado")
             options.insert(0, "Não especificado") # Coloca no topo
        
        selected_options = st.sidebar.multiselect(label, options, default=options)
        if selected_options != options: # Se o usuário mudou a seleção padrão (todos)
             return df[df[column_name].isin(selected_options)]
    else:
        st.sidebar.text(f"Coluna '{column_name}' não disponível para filtro.")
    return df

df = create_multiselect_filter("Port", "Porto")
df = create_multiselect_filter("Terminal", "Terminal")
df = create_multiselect_filter("Berth", "Berço")
df = create_multiselect_filter("Cargo Type", "Tipo de Carga")
df = create_multiselect_filter("Charterer Nome", "Armador (Charterer)")
df = create_multiselect_filter("Inward/Outward Agent", "Agente")
df = create_multiselect_filter("Vessel", "Navio")

# --- Exibição dos Dados Filtrados (Opcional, para depuração) ---
if st.sidebar.checkbox("Mostrar dados filtrados (primeiras 100 linhas)"):
    st.subheader("Dados Filtrados")
    st.dataframe(df.head(100))

# --- Layout Principal para Indicadores --- 
st.markdown("### Indicadores Chave")

# Placeholder para os indicadores
if df.empty:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
else:
    # Indicador 1: Média do Tempo de Estada
    avg_tempo_estada = df["Tempo de Estada (Dias)"].mean()
    st.metric(label="Média de Tempo de Estada (Dias)", value=f"{avg_tempo_estada:.2f}" if not pd.isna(avg_tempo_estada) else "N/D")

    # Outros indicadores serão adicionados aqui
    # ... (Desempenho por Armador/Agente, Principais Rotas, etc.)

    st.markdown("--- ")
    st.markdown("### Visualizações Detalhadas")

    # Placeholder para gráficos
    # Gráfico 1: Movimentação por Tipo de Carga
    if "Cargo Type" in df.columns and "Qtty" in df.columns:
        st.subheader("Movimentação por Tipo de Carga")
        mov_por_carga = df.groupby("Cargo Type")["Qtty"].sum().sort_values(ascending=False)
        if not mov_por_carga.empty:
            if len(mov_por_carga) <= 5: # Usar pizza para poucas categorias
                st.plotly_chart(px.pie(mov_por_carga, values="Qtty", names=mov_por_carga.index, title="Distribuição de Quantidade por Tipo de Carga"), use_container_width=True)
            else:
                st.bar_chart(mov_por_carga)
        else:
            st.info("Sem dados de movimentação por tipo de carga para os filtros selecionados.")
    
    # Gráfico 2: Número de Navios Atendidos por Berço
    if "Berth" in df.columns and "Vessel" in df.columns:
        st.subheader("Número de Navios Atendidos por Berço")
        navios_por_berco = df.groupby("Berth")["Vessel"].nunique().sort_values(ascending=False)
        if not navios_por_berco.empty:
            st.bar_chart(navios_por_berco.head(20)) # Mostrar top 20 para não poluir
        else:
            st.info("Sem dados de navios por berço para os filtros selecionados.")

    # Gráfico 3: Desempenho por Armador (Charterer Nome) - Ex: Qtty total
    if "Charterer Nome" in df.columns and "Qtty" in df.columns:
        st.subheader("Desempenho por Armador (Quantidade Total Movimentada)")
        desempenho_armador = df.groupby("Charterer Nome")["Qtty"].sum().sort_values(ascending=False)
        if not desempenho_armador.empty:
            st.bar_chart(desempenho_armador.head(20)) # Top 20
        else:
            st.info("Sem dados de desempenho por armador para os filtros selecionados.")

    # Gráfico 4: Principais Rotas (Origem/Destino)
    if "Origin/Destiny" in df.columns:
        st.subheader("Principais Rotas (Origem/Destino)")
        # Contagem de ocorrências da coluna "Region\n Origin/Destiny"
        principais_rotas = df["Origin/Destiny"].value_counts().sort_values(ascending=False)
        if not principais_rotas.empty:
            st.bar_chart(principais_rotas.head(20)) # Top 20
        else:
            st.info("Sem dados de rotas para os filtros selecionados.")

# Adicionar import para plotly express se for usar gráficos de pizza mais elaborados

# Nota: Este é um script inicial. Mais indicadores e visualizações serão adicionados.
# A lógica de conversão do "Tempo de estada" pode precisar de ajuste fino dependendo da natureza exata dos dados.
# A limpeza de dados também pode ser mais extensa.


