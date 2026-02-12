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

# --- CAMBIO AQUÍ: LÓGICA PARA SELECCIONAR SOLO 2026 POR DEFECTO ---
opciones_ano = sorted(df['AÑO'].unique())

# Si '2026' existe en los datos, lo usamos por defecto. Si no, usamos todos.
default_ano = ['2026'] if '2026' in opciones_ano else opciones_ano

filtro_ano = st.sidebar.multiselect(
    "Selecciona Año:",
    options=opciones_ano,
    default=default_ano  # <--- Aquí está el cambio clave
)
# ------------------------------------------------------------------

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

# --- 4. GRÁFICOS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Hectáreas por Cultivo y Año")
    if not df_filtered.empty:
        fig_bar = px.bar(
            df_filtered, 
            x="CULTIVO", 
            y="HAS", 
            color="AÑO", 
            barmode="group",
            text_auto='.2s',
            color_discrete_map={'2025': '#95a5a6', '2026': '#3498db'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No hay datos visibles. Intenta seleccionar más filtros.")

with col2:
    st.subheader("💧 Distribución por Red de Riego")
    if not df_filtered.empty:
        fig_pie = px.pie(
            df_filtered, 
            values="HAS", 
            names="RED DE RIEGO", 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("🔄 Impacto Doble Cosecha")
    if not df_filtered.empty:
        df_doble = df_filtered.groupby('DOBLE COSECHA')['HAS'].sum().reset_index()
        fig_doble = px.bar(
            df_doble,
            x='DOBLE COSECHA',
            y='HAS',
            color='DOBLE COSECHA',
            text_auto='.2s'
        )
        st.plotly_chart(fig_doble, use_container_width=True)

with col4:
    st.subheader("📈 Evolución Total")
    if not df_filtered.empty:
        # Agrupamos por año para la línea temporal
        # Nota: Si solo filtras 2026, solo verás un punto.
        df_ano = df_filtered.groupby('AÑO')['HAS'].sum().reset_index()
        fig_line = px.line(
            df_ano,
            x='AÑO',
            y='HAS',
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)

# --- 5. TABLA ---
st.subheader("📋 Datos Detallados")
with st.expander("Ver tabla completa"):
    st.dataframe(df_filtered.style.format({"HAS": "{:.2f}"}), use_container_width=True)
