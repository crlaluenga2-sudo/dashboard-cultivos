import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Cultivos",
    page_icon="🚜",
    layout="wide"
)

st.title("🚜 Dashboard de Gestión de Cultivos")
st.markdown("---")

# --- 1. CARGA DE DATOS AUTOMÁTICA ---
@st.cache_data
def cargar_datos():
    archivo = 'datos.csv'  # Asegúrate de que tu archivo en GitHub se llame así
    
    try:
        df = pd.read_csv(archivo)
    except FileNotFoundError:
        st.error(f"⚠️ No se encuentra el archivo '{archivo}'.")
        return None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

    # Limpieza básica
    df.columns = df.columns.str.strip()
    
    # CONVERSIÓN DE DATOS
    def clean_currency(x):
        if isinstance(x, str):
            return float(x.replace(',', '.').replace('"', ''))
        return float(x)
    
    if 'HAS' in df.columns:
        df['HAS'] = df['HAS'].apply(clean_currency)
    
    if 'AÑO' in df.columns:
        df['AÑO'] = df['AÑO'].astype(str)
    
    cols_texto = ['CULTIVO', 'RED DE RIEGO', 'DOBLE COSECHA']
    for col in cols_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()
            df[col] = df[col].replace({'NAN': 'SIN DEFINIR', 'NAM': 'SIN DEFINIR'})

    return df

df = cargar_datos()

if df is None:
    st.stop()

# --- 2. BARRA LATERAL DE FILTROS ---
st.sidebar.header("🔍 Filtros")

# Filtro Año (Solo 2026 por defecto)
opciones_ano = sorted(df['AÑO'].unique())
default_ano = ['2026'] if '2026' in opciones_ano else opciones_ano

filtro_ano = st.sidebar.multiselect(
    "Selecciona Año:",
    options=opciones_ano,
    default=default_ano
)

# Filtro Red de Riego
filtro_red = st.sidebar.multiselect(
    "Red de Riego:",
    options=sorted(df['RED DE RIEGO'].unique()),
    default=sorted(df['RED DE RIEGO'].unique())
)

# Filtro Cultivo
filtro_cultivo = st.sidebar.multiselect(
    "Cultivo:",
    options=sorted(df['CULTIVO'].unique()),
    default=sorted(df['CULTIVO'].unique())
)

# Filtro Doble Cosecha
filtro_doble = st.sidebar.multiselect(
    "Doble Cosecha:",
    options=sorted(df['DOBLE COSECHA'].unique()),
    default=sorted(df['DOBLE COSECHA'].unique())
)

# APLICAR FILTROS
df_filtered = df.query(
    "`AÑO` == @filtro_ano & `RED DE RIEGO` == @filtro_red & `CULTIVO` == @filtro_cultivo & `DOBLE COSECHA` == @filtro_doble"
)

# --- 3. INDICADORES (KPIs) ---
total_has = df_filtered['HAS'].sum()
num_parcelas = df_filtered.shape[0]

c1, c2, c3 = st.columns(3)
c1.metric("Total Hectáreas", f"{total_has:,.2f} ha")
c2.metric("Nº de Registros", num_parcelas)
c3.metric("Cultivos Distintos", df_filtered['CULTIVO'].nunique())

st.markdown("---")

# --- CONFIGURACIÓN GRÁFICA COMÚN ---
# Esta configuración desactiva la interactividad para todos los gráficos
config_estatica = {'staticPlot': True}

# --- 4. GRÁFICOS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Hectáreas por Cultivo y Año")
    if not df_filtered.empty:
        # Agrupamos para sumar hectáreas por cultivo/año antes de graficar
        # Esto asegura que la etiqueta muestre el total y no valores superpuestos
        df_agrupado = df_filtered.groupby(['CULTIVO', 'AÑO'])['HAS'].sum().reset_index()
        
        fig_bar = px.bar(
            df_agrupado, 
            x="CULTIVO", 
            y="HAS", 
            color="AÑO",
