import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import hashlib

# Configuração da página
st.set_page_config(layout="wide", page_title="Movimentações Portuárias")

# Função para criar hash de senha
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Função para verificar hash de senha
def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# Credenciais de login (em produção, isso deveria estar em um banco de dados seguro)
# Usuário: fulano, Senha: 123
credentials = {
    "fulano": make_hashes("123")
}

# Função para autenticação
def authenticate(username, password):
    if username in credentials:
        return check_hashes(password, credentials[username])
    return False

# Função para carregar e pré-processar os dados
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
        def convert_excel_duration_to_days(excel_date):
            if pd.isna(excel_date):
                return np.nan
            try:
                if isinstance(excel_date, str):
                    excel_date = pd.to_datetime(excel_date, errors='coerce')
                if pd.api.types.is_datetime64_any_dtype(excel_date):
                    base_date = pd.Timestamp("1899-12-30")
                    delta = excel_date - base_date
                    return delta.total_seconds() / (24 * 60 * 60)
                elif isinstance(excel_date, (int, float)):
                    return excel_date
            except Exception:
                return np.nan
            return np.nan

        df["Tempo de Estada (Dias)"] = df["Tempo de estada"].apply(convert_excel_duration_to_days)

        # 3. Converter colunas de data para datetime
        date_cols = ["ETA", "ETB", "ETS"]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        # 3.1 Calcular Tempo de Estada com base em ETA e ETS
        df["Tempo de Estada Calculado (Dias)"] = (df["ETS"] - df["ETA"]).dt.total_seconds() / (24 * 60 * 60)

        # 4. Limpeza básica de colunas para filtros
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

        if "ETSETB Port Operator" in df.columns:
            df = df.drop(columns=["ETSETB Port Operator"])
        if "Tempo de estada" in df.columns:
            df = df.drop(columns=["Tempo de estada"])

        return df

    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{file_path}' não encontrado.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar ou processar o arquivo Excel: {e}")
        return pd.DataFrame()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

def login_page():
    st.title("🔐 Login - Movimentações Portuárias")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit_button = st.form_submit_button("Entrar")
        if submit_button:
            if authenticate(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.rerun()

def main_dashboard():
    data_path = "data/dd_movexp_2024.xls"
    df_original = load_and_preprocess_data(data_path)

    if df_original.empty:
        st.stop()

    df = df_original.copy()

    col1, col2 = st.columns([10, 2])
    with col1:
        st.title("🚢 Movimentações Portuárias")
        st.markdown(f"Bem-vindo, **{st.session_state['username']}**! Análise interativa das operações e desempenho portuário.")
    with col2:
        st.button("Logout", on_click=logout, type="primary")

    st.sidebar.header("Filtros")

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
            else:
                st.sidebar.warning("Período inválido selecionado. Exibindo todos os dados.")
    else:
        st.sidebar.text("Coluna 'ETB' não disponível para filtro de período.")
        selected_period = None

    def create_multiselect_filter(column_name, label, default=None):
        if column_name in df.columns:
            options = sorted(df[column_name].astype(str).unique().tolist())
            if "Não especificado" in options:
                options.remove("Não especificado")
                options.insert(0, "Não especificado")
            if default is None:
                default = options
            selected_options = st.sidebar.multiselect(label, options, default=default)
            if selected_options != options:
                return df[df[column_name].isin(selected_options)]
        else:
            st.sidebar.text(f"Coluna '{column_name}' não disponível para filtro.")
        return df

    df = create_multiselect_filter("Port", "Porto", default=['Belém'])
    df = create_multiselect_filter("Terminal", "Terminal")
    df = create_multiselect_filter("Berth", "Berço")
    df = create_multiselect_filter("Cargo Type", "Tipo de Carga")
    df = create_multiselect_filter("Charterer Nome", "Armador (Charterer)")
    df = create_multiselect_filter("Inward/Outward Agent", "Agente")
    df = create_multiselect_filter("Vessel", "Navio")

    if st.sidebar.checkbox("Mostrar dados filtrados (primeiras 100 linhas)"):
        st.subheader("Dados Filtrados")
        st.dataframe(df.head(100))

    st.markdown("### Indicadores Chave")

    if df.empty:
        st.warning("Nenhum dado disponível para os filtros selecionados.")
    else:
        avg_tempo_estada = df["Tempo de Estada Calculado (Dias)"].mean()
        st.metric(label="Média de Tempo de Estada (Dias)", value=f"{avg_tempo_estada:.2f}" if not pd.isna(avg_tempo_estada) else "N/D")

        st.markdown("--- ")
        st.markdown("### Visualizações Detalhadas")

        if "Cargo Type" in df.columns and "Qtty" in df.columns:
            st.subheader("Movimentação por Tipo de Carga")
            mov_por_carga = df.groupby("Cargo Type")["Qtty"].sum().sort_values(ascending=False)
            if not mov_por_carga.empty:
                if len(mov_por_carga) <= 5:
                    st.plotly_chart(px.pie(mov_por_carga, values="Qtty", names=mov_por_carga.index, title="Distribuição de Quantidade por Tipo de Carga"), use_container_width=True)
                else:
                    st.bar_chart(mov_por_carga)
            else:
                st.info("Sem dados de movimentação por tipo de carga para os filtros selecionados.")

        if "Berth" in df.columns and "Vessel" in df.columns:
            st.subheader("Número de Navios Atendidos por Berço")
            navios_por_berco = df.groupby("Berth")["Vessel"].nunique().sort_values(ascending=False)
            if not navios_por_berco.empty:
                st.bar_chart(navios_por_berco.head(20))
            else:
                st.info("Sem dados de navios por berço para os filtros selecionados.")

        if "Charterer Nome" in df.columns and "Qtty" in df.columns:
            st.subheader("Desempenho por Armador (Quantidade Total Movimentada)")
            desempenho_armador = df.groupby("Charterer Nome")["Qtty"].sum().sort_values(ascending=False)
            if not desempenho_armador.empty:
                st.bar_chart(desempenho_armador.head(20))
            else:
                st.info("Sem dados de desempenho por armador para os filtros selecionados.")

        if "Origin/Destiny" in df.columns:
            st.subheader("Principais Rotas (Origem/Destino)")
            principais_rotas = df["Origin/Destiny"].value_counts().sort_values(ascending=False)
            if not principais_rotas.empty:
                st.bar_chart(principais_rotas.head(20))
            else:
                st.info("Sem dados de rotas para os filtros selecionados.")


if st.session_state['logged_in']:
    main_dashboard()
else:
    login_page()
