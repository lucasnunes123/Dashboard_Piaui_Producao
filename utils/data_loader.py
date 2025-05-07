# utils/data_loader.py
import pandas as pd
import numpy as np

def carregar_dados():
    df = pd.read_excel('data/Dados_POR MUNICIPIO_2020_2025.xlsx', sheet_name='Resultado')
    
    # Adicionar colunas calculadas
    df['Valor por kg'] = df['Valor US$ FOB'] / df['Quilograma Líquido'].replace(0, np.nan)
    
    # Converter tipos de dados se necessário
    df['Ano'] = df['Ano'].astype(int)
    
    return df

def get_summary_stats(df):
    """Retorna estatísticas resumidas dos dados."""
    stats = {
        'total_exportacao': df[df['Fluxo'] == 'Exportação']['Valor US$ FOB'].sum(),
        'total_importacao': df[df['Fluxo'] == 'Importação']['Valor US$ FOB'].sum(),
        'saldo_comercial': df[df['Fluxo'] == 'Exportação']['Valor US$ FOB'].sum() - 
                          df[df['Fluxo'] == 'Importação']['Valor US$ FOB'].sum(),
        'total_municipios': df['Município'].nunique(),
        'anos_disponiveis': sorted(df['Ano'].unique())
    }
    return stats